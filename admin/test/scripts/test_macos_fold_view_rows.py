"""Pin how rows read from several volume views of one file are reported.

A Mac logical extraction can hold one file at the root, under System/Volumes/Data/ and
under System/Volumes/Update/mnt1/. When those copies differ in bytes every copy is read,
and a record more than one copy holds must be reported once, with every file that held
it named, while a record only one copy holds is kept.

Every value below is authored for the test; none comes from a real device, and every
expected value is written out here, never read back from the code under test.
"""
import pathlib
import plistlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosInstallHistory  # pylint: disable=wrong-import-position
from scripts.macos_plists import fold_view_rows  # pylint: disable=wrong-import-position

ROOT = 'Users/someone/Library/store.db'
DATA = 'System/Volumes/Data/Users/someone/Library/store.db'
MNT1 = 'System/Volumes/Update/mnt1/Users/someone/Library/store.db'
OTHER = 'Users/another/Library/store.db'


class FoldViewRowsTest(unittest.TestCase):

    def test_a_record_three_views_hold_is_reported_once_and_names_each_file(self):
        rows = [('a', 1, ROOT), ('a', 1, DATA), ('a', 1, MNT1)]
        self.assertEqual(fold_view_rows(rows), [('a', 1, ROOT + '\n' + DATA + '\n' + MNT1)])

    def test_a_record_only_one_view_holds_is_kept(self):
        rows = [('a', 1, ROOT), ('a', 1, DATA), ('newer', 2, DATA)]
        self.assertEqual(fold_view_rows(rows),
                         [('a', 1, ROOT + '\n' + DATA), ('newer', 2, DATA)])

    def test_a_record_one_file_holds_twice_stays_twice(self):
        rows = [('a', 1, ROOT), ('a', 1, ROOT), ('a', 1, DATA)]
        both = ROOT + '\n' + DATA
        self.assertEqual(fold_view_rows(rows), [('a', 1, both), ('a', 1, both)])

    def test_the_later_view_holding_more_copies_decides_the_count(self):
        rows = [('a', 1, ROOT), ('a', 1, DATA), ('a', 1, DATA), ('a', 1, DATA)]
        both = ROOT + '\n' + DATA
        self.assertEqual(fold_view_rows(rows), [('a', 1, both)] * 3)

    def test_files_at_different_paths_are_never_folded(self):
        rows = [('a', 1, ROOT), ('a', 1, OTHER)]
        self.assertEqual(fold_view_rows(rows), rows)

    def test_a_difference_in_any_value_keeps_both_rows(self):
        rows = [('a', 1, ROOT), ('a', 2, DATA)]
        self.assertEqual(fold_view_rows(rows), rows)

    def test_rows_from_one_file_come_back_unchanged_and_in_order(self):
        rows = [('b', 2, ROOT), ('a', 1, ROOT), ('b', 2, ROOT), ('c', 3, ROOT)]
        self.assertEqual(fold_view_rows(rows), rows)

    def test_no_rows(self):
        self.assertEqual(fold_view_rows([]), [])


class Context:
    def __init__(self, base, files):
        self.base, self.files = base, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.base).as_posix()


def _entry(day, name):
    return {'date': datetime(2026, 3, day, 12, 0, 0), 'displayName': name,
            'displayVersion': '1.0', 'processName': 'installer'}


class InstallHistoryAcrossViewsTest(unittest.TestCase):

    def test_two_views_that_differ_report_the_union(self):
        receipts = 'Library/Receipts/InstallHistory.plist'
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(macosInstallHistory, 'logfunc', lambda *_: None):
            base = pathlib.Path(directory)
            older = base/receipts
            newer = base/'System/Volumes/Data'/receipts
            for path, entries in ((older, [_entry(1, 'First'), _entry(2, 'Second')]),
                                  (newer, [_entry(1, 'First'), _entry(2, 'Second'),
                                           _entry(3, 'Third')])):
                path.parent.mkdir(parents=True)
                path.write_bytes(plistlib.dumps(entries))
            self.assertNotEqual(older.read_bytes(), newer.read_bytes())
            _headers, rows, source = macosInstallHistory.macosInstallHistory.__wrapped__(
                Context(base, [older, newer]))
        both = receipts + '\n' + 'System/Volumes/Data/' + receipts
        self.assertEqual([(row[0], row[1], row[-1]) for row in rows], [
            (datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc), 'First', both),
            (datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc), 'Second', both),
            (datetime(2026, 3, 3, 12, 0, 0, tzinfo=timezone.utc), 'Third',
             'System/Volumes/Data/' + receipts)])
        self.assertEqual(len(source.split('\n')), 2)


if __name__ == '__main__':
    unittest.main()
