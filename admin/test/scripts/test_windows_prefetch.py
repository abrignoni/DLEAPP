"""Pin where Prefetch reads the run count in the two version 30 file information variants, which SCCA
versions the reader takes, and its reading of uncompressed version 17, 23 and 26 files against values
Eric Zimmerman's Prefetch tests assert for them (admin/test/data/prefetch/README.md)."""
import gzip
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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
        info = windowsPrefetch._parse_scca(scca(304, 208, 12, other=3), 30)  # pylint: disable=protected-access
        self.assertEqual(info['run_count'], 12)
        self.assertEqual(info.get('metrics_offset'), 304)

    def test_variant_2_keeps_the_run_count_at_200(self):
        info = windowsPrefetch._parse_scca(scca(296, 200, 12, other=3), 30)  # pylint: disable=protected-access
        self.assertEqual(info['run_count'], 12)
        self.assertEqual(info.get('metrics_offset'), 296)

    def test_an_unknown_layout_leaves_the_run_count_blank_and_says_so(self):
        info = windowsPrefetch._parse_scca(scca(280, None, 0, other=5), 30)  # pylint: disable=protected-access
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
        for version in (25, 29, 32):
            with self.subTest(version=version):
                parsed, logged = self.read({'OLD.EXE-00000001.pf': scca(296, 200, 12, version=version)})
                self.assertEqual(parsed, [])
                self.assertEqual(logged, [f'Prefetch: OLD.EXE-00000001.pf SCCA version {version} not supported, skipped'])


DATA = REPO_ROOT / 'admin' / 'test' / 'data' / 'prefetch'
MST = timezone(timedelta(hours=-7))


class UncompressedVersionTest(unittest.TestCase):
    """Values Eric Zimmerman's TestVersion17, 23 and 26 tests assert for these three files, for the fields this module reports."""
    CASES = {
        'Win2k3_CMD.EXE-087B4001.pf.gz': dict(
            version=17, executable='CMD.EXE', run_count=3,
            last_run=datetime(2016, 1, 15, 16, 1, 40, 875000, tzinfo=MST),
            volume=('\\DEVICE\\HARDDISKVOLUME1', '64BB3469', datetime(2016, 1, 15, 8, 45, 15, 890625, tzinfo=MST)),
            files=16, file3='\\DEVICE\\HARDDISKVOLUME1\\WINDOWS\\SYSTEM32\\LOCALE.NLS'),
        'Win7_CALC.EXE-77FDF17F.pf.gz': dict(
            version=23, executable='CALC.EXE', run_count=2,
            last_run=datetime(2016, 1, 16, 13, 27, 1, 196750, tzinfo=MST),
            volume=('\\DEVICE\\HARDDISKVOLUME2', '88008C2F', datetime(2016, 1, 16, 14, 15, 18, 109375, tzinfo=MST)),
            files=None, file3=None),
        'Win8x__CMD.EXE-4A81B364.pf.gz': dict(
            version=26, executable='CMD.EXE', run_count=2,
            last_run=datetime(2016, 1, 16, 14, 25, 41, 534117, tzinfo=MST),
            volume=('\\DEVICE\\HARDDISKVOLUME2', 'A26E529A', None),
            files=None, file3=None),
    }

    def test_the_values_the_reference_tests_assert(self):
        for name, want in self.CASES.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                with gzip.open(DATA / name, 'rb') as packed, open(os.path.join(folder, name[:-3]), 'wb') as out:
                    out.write(packed.read())
                with mock.patch.object(windowsPrefetch, 'logfunc') as log:
                    parsed = list(windowsPrefetch._parsed_prefetch(_Context(folder), 'Prefetch'))  # pylint: disable=protected-access
                self.assertEqual(log.call_args_list, [])
                info = parsed[0][2]
                self.assertEqual((info['version'], info['executable'], info['run_count']),
                                 (want['version'], want['executable'], want['run_count']))
                self.assertEqual(info['run_times'][0], want['last_run'])
                self.assertEqual(info['volumes'][0][:2], want['volume'][:2])
                if want['volume'][2]:
                    self.assertEqual(info['volumes'][0][2], want['volume'][2])
                if want['files']:
                    self.assertEqual((len(info['files']), info['files'][3]), (want['files'], want['file3']))

    def test_versions_17_and_23_keep_one_run_time(self):
        for name in ('Win2k3_CMD.EXE-087B4001.pf.gz', 'Win7_CALC.EXE-77FDF17F.pf.gz'):
            with gzip.open(DATA / name, 'rb') as packed:
                data = packed.read()
            info = windowsPrefetch._parse_scca(data, struct.unpack_from('<I', data, 0)[0])  # pylint: disable=protected-access
            self.assertEqual(len(info['run_times']), 1, name)

    def test_filetimes_are_cut_to_whole_microseconds_without_float_error(self):
        # 2016-01-15 15:45:15.8906250 UTC as a FILETIME; a float division gives .890624.
        self.assertEqual(windowsPrefetch._filetime(130973463158906250),  # pylint: disable=protected-access
                         datetime(2016, 1, 15, 15, 45, 15, 890625, tzinfo=timezone.utc))


if __name__ == '__main__':
    unittest.main()
