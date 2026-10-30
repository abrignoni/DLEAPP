"""Pin how scripts/artifacts/macosSafariFavicons.py reads icon_info.timestamp. Values are invented."""
# pylint: disable=protected-access
import pathlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosSafariFavicons as fav  # pylint: disable=wrong-import-position


class TimeTest(unittest.TestCase):
    def test_cocoa_seconds(self):
        self.assertEqual(fav._time(700000000), datetime(2023, 3, 8, 20, 26, 40, tzinfo=timezone.utc))

    def test_unix_seconds_above_the_limit(self):
        self.assertEqual(fav._time(1700000000), datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc))

    def test_absent_or_not_positive(self):
        for value in (None, 0, -1, 'x', True):
            self.assertEqual(fav._time(value), '')


if __name__ == '__main__':
    unittest.main()
