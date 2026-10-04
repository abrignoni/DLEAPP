"""Pin where Prefetch reads the run count in the two version 30 file information variants, and which SCCA
versions the reader takes."""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsPrefetch
# pylint: enable=wrong-import-position


def scca(metrics_offset, run_count_at, run_count, other=0, version=30):
    """A decompressed SCCA image: the 84-byte file header, then file information whose
    first field is the file metrics array offset. No files or volumes are listed."""
    data = bytearray(400)
    struct.pack_into('<I', data, 0, version)
    data[4:8] = b'SCCA'
    data[16:16 + len('KNOWN.EXE') * 2] = 'KNOWN.EXE'.encode('utf-16-le')
    struct.pack_into('<I', data, 84, metrics_offset)
    struct.pack_into('<Q', data, 128, 132500000000000000)  # one run time, in 2020
    for offset in (200, 208):
        struct.pack_into('<I', data, offset, other)
    if run_count_at is not None:
        struct.pack_into('<I', data, run_count_at, run_count)
    return bytes(data)


class RunCountTest(unittest.TestCase):
    def test_variant_1_keeps_the_run_count_at_208(self):
        info = windowsPrefetch._parse_scca_v30(scca(304, 208, 12, other=3))  # pylint: disable=protected-access
        self.assertEqual(info['run_count'], 12)
        self.assertEqual(info.get('metrics_offset'), 304)

    def test_variant_2_keeps_the_run_count_at_200(self):
        info = windowsPrefetch._parse_scca_v30(scca(296, 200, 12, other=3))  # pylint: disable=protected-access
        self.assertEqual(info['run_count'], 12)
        self.assertEqual(info.get('metrics_offset'), 296)

    def test_an_unknown_layout_leaves_the_run_count_blank_and_says_so(self):
        info = windowsPrefetch._parse_scca_v30(scca(280, None, 0, other=5))  # pylint: disable=protected-access
        self.assertEqual(info['run_count'], '')

        class Context:  # pylint: disable=too-few-public-methods
            pass
        with mock.patch.object(windowsPrefetch, '_parsed_prefetch',
                               return_value=[('x/KNOWN.EXE-00000000.pf', 'KNOWN.EXE-00000000.pf', info)]), \
                mock.patch.object(windowsPrefetch, 'logfunc') as log:
            _headers, rows, _source = windowsPrefetch.prefetch.__wrapped__(Context())
        self.assertEqual(rows[0][2], '')
        self.assertIn('file metrics offset 280', log.call_args.args[0])


def mam(image):
    """A .pf file around a decompressed image of at most one 64 KiB block: the MAM header, then Xpress Huffman with
    every byte a literal. Each of the 256 literal symbols gets an 8-bit code, so a byte's code is the byte itself, and
    the 16-bit words the decoder reads are stored low byte first."""
    assert len(image) <= 65536
    padded = image + bytes(len(image) % 2) + bytes(4)
    words = b''.join(bytes((padded[i + 1], padded[i])) for i in range(0, len(padded), 2))
    return b'MAM\x04' + struct.pack('<I', len(image)) + bytes([0x88]) * 128 + bytes(128) + words


class _Context:
    def __init__(self, folder):
        self.folder = folder

    def get_files_found(self):
        return sorted(os.path.join(self.folder, name) for name in os.listdir(self.folder))

    def get_relative_path(self, path):
        return os.path.relpath(path, self.folder)


class VersionTest(unittest.TestCase):
    def read(self, images):
        with tempfile.TemporaryDirectory() as folder:
            for name, image in images.items():
                with open(os.path.join(folder, name), 'wb') as handle:
                    handle.write(mam(image))
            with mock.patch.object(windowsPrefetch, 'logfunc') as log:
                parsed = list(windowsPrefetch._parsed_prefetch(_Context(folder), 'Prefetch'))  # pylint: disable=protected-access
        return parsed, [call.args[0] for call in log.call_args_list]

    def test_the_test_file_decompresses_to_the_image_it_was_made_from(self):
        image = scca(296, 200, 12)
        packed = mam(image)
        self.assertEqual(windowsPrefetch._decompress_xpress_huffman(packed[8:], len(image)), image)  # pylint: disable=protected-access

    def test_version_31_is_read_with_the_version_30_variant_2_layout(self):
        parsed, logged = self.read({'KNOWN.EXE-0000000B.pf': scca(296, 200, 12, other=3, version=31)})
        self.assertEqual([(source, name) for source, name, _info in parsed], [('KNOWN.EXE-0000000B.pf',) * 2])
        self.assertEqual((parsed[0][2]['executable'], parsed[0][2]['run_count'], len(parsed[0][2]['run_times'])),
                         ('KNOWN.EXE', 12, 1))
        self.assertEqual(logged, [])

    def test_version_30_is_still_read(self):
        parsed, logged = self.read({'KNOWN.EXE-0000000A.pf': scca(304, 208, 7, other=3)})
        self.assertEqual((len(parsed), parsed[0][2]['run_count'], logged), (1, 7, []))

    def test_another_version_is_skipped_and_named_in_the_run_log(self):
        for version in (26, 29, 32):
            with self.subTest(version=version):
                parsed, logged = self.read({'OLD.EXE-00000001.pf': scca(296, 200, 12, version=version)})
                self.assertEqual(parsed, [])
                self.assertEqual(logged, [f'Prefetch: OLD.EXE-00000001.pf SCCA version {version} not supported, skipped'])


if __name__ == '__main__':
    unittest.main()
