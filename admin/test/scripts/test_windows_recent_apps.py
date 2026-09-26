"""Pin the value handling in scripts/artifacts/windowsRecentApps.py.

LastAccessedTime is a FILETIME (100 ns intervals since 1601-01-01 UTC); the expected
datetime below is derived from Unix time, 11644473600 seconds after 1601.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsRecentApps as recent  # pylint: disable=wrong-import-position


class ValueTest(unittest.TestCase):
    def test_time(self):
        # 131668295035470000 is Unix 1522355903.547, 2018-03-29 20:38:23.547 UTC.
        self.assertEqual(recent._time(131668295035470000),  # pylint: disable=protected-access
                         datetime(2018, 3, 29, 20, 38, 23, 547000, tzinfo=timezone.utc))
        self.assertEqual(recent._time(0), '')  # pylint: disable=protected-access
        self.assertEqual(recent._time('x'), '')  # pylint: disable=protected-access

    def test_count_and_text(self):
        self.assertEqual(recent._count(26), 26)  # pylint: disable=protected-access
        self.assertEqual(recent._count(True), '')  # pylint: disable=protected-access
        self.assertEqual(recent._count(None), '')  # pylint: disable=protected-access
        self.assertEqual(recent._text('Chrome'), 'Chrome')  # pylint: disable=protected-access
        self.assertEqual(recent._text(b'x'), '')  # pylint: disable=protected-access


class _Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class HiveFilterTest(unittest.TestCase):
    def test_non_hive_files_and_directories_are_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'Users', 'someone')
            os.makedirs(folder)
            other = os.path.join(folder, 'notes.txt')
            with open(other, 'w', encoding='utf-8') as handle:
                handle.write('x')
            rows = list(recent.recent_apps(_Context(root, [other, folder]), 'test'))
        self.assertEqual(rows, [])


if __name__ == '__main__':
    unittest.main()
