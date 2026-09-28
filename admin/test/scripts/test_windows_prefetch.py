"""Pin where Prefetch reads the run count in the two version 30 file information variants."""
import pathlib
import struct
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsPrefetch
# pylint: enable=wrong-import-position


def scca(metrics_offset, run_count_at, run_count, other=0):
    """A decompressed version 30 image: the 84-byte file header, then file information whose
    first field is the file metrics array offset. No files or volumes are listed."""
    data = bytearray(400)
    struct.pack_into('<I', data, 0, 30)
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


if __name__ == '__main__':
    unittest.main()
