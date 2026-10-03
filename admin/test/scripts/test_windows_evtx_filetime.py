"""Pin the exact FILETIME conversion scripts/windows_evtx.py gives python-evtx."""
import pathlib
import struct
import sys
import unittest
from datetime import datetime, timedelta, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import Evtx.BinaryParser as evtx_binary  # noqa: E402  pylint: disable=wrong-import-position

from scripts import windows_evtx  # noqa: E402  pylint: disable=wrong-import-position

EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
# 2021-04-22 08:51:04.8515183 UTC as a stored count; the float conversion renders it as .851519.
STORED = ((datetime(2021, 4, 22, 8, 51, 4, 851518, tzinfo=timezone.utc) - EPOCH) // timedelta(microseconds=1)) * 10 + 3


def exact(qword):
    return EPOCH + timedelta(microseconds=qword // 10)


class ExactFiletimeTest(unittest.TestCase):
    def test_installed_once(self):
        self.assertTrue(evtx_binary.parse_filetime.dleapp_exact)
        windows_evtx._install_exact_filetime()  # pylint: disable=protected-access
        self.assertFalse(getattr(evtx_binary.parse_filetime.original, 'dleapp_exact', False))

    def test_count_is_cut_to_whole_microseconds(self):
        self.assertEqual(evtx_binary.parse_filetime(STORED), datetime(2021, 4, 22, 8, 51, 4, 851518, tzinfo=timezone.utc))
        self.assertEqual(evtx_binary.parse_filetime(STORED + 6), exact(STORED))
        self.assertEqual(evtx_binary.parse_filetime(116444736000000000), datetime(1970, 1, 1, tzinfo=timezone.utc))
        # 0.9 and 1.9 microseconds past 1601: cut, not rounded
        self.assertEqual(evtx_binary.parse_filetime(9), EPOCH)
        self.assertEqual(evtx_binary.parse_filetime(19), EPOCH + timedelta(microseconds=1))

    def test_the_float_conversion_is_off_where_the_exact_one_is_not(self):
        self.assertNotEqual(evtx_binary.parse_filetime.original(STORED), exact(STORED))

    def test_zero_and_out_of_range_give_python_evtx_minimum(self):
        self.assertEqual(evtx_binary.parse_filetime(0), datetime.min)
        self.assertEqual(evtx_binary.parse_filetime(2 ** 64 - 1), datetime.min)

    def test_a_naive_original_gives_naive_results(self):
        saved = evtx_binary.parse_filetime
        try:
            evtx_binary.parse_filetime = lambda qword: datetime(1970, 1, 1)
            windows_evtx._install_exact_filetime()  # pylint: disable=protected-access
            self.assertEqual(evtx_binary.parse_filetime(STORED), exact(STORED).replace(tzinfo=None))
        finally:
            evtx_binary.parse_filetime = saved

    def test_python_evtx_reads_a_stored_filetime_through_it(self):
        block = evtx_binary.Block(struct.pack('<Q', STORED), 0)
        self.assertEqual(block.unpack_filetime(0), exact(STORED))


if __name__ == '__main__':
    unittest.main()
