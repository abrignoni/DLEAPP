"""Pin scripts/artifacts/macosTextReplacements.py: the CloudKit record fields and the home-Library guard."""
# pylint: disable=protected-access
import pathlib
import plistlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosTextReplacements as MODULE  # pylint: disable=wrong-import-position

EPOCH_2001 = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _archive(ctime=None, mtime=None, device=None):
    """A keyed archive shaped like a CloudKit record's system fields: the fields sit at $top.
    Every value is invented."""
    objects = ['$null', {'$classname': 'NSDate', '$classes': ['NSDate', 'NSObject']}]
    top = {'KnownToServer': True, 'Permission': 1}
    for key, seconds in (('RecordCtime', ctime), ('RecordMtime', mtime)):
        if seconds is not None:
            objects.append({'NS.time': seconds, '$class': plistlib.UID(1)})
            top[key] = plistlib.UID(len(objects) - 1)
        else:
            top[key] = plistlib.UID(0)
    if device is not None:
        objects.append(device)
        top['ModifiedByDevice'] = plistlib.UID(len(objects) - 1)
    return plistlib.dumps({'$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': top,
                           '$objects': objects}, fmt=plistlib.PlistFormat.FMT_BINARY)


def _seconds(value):
    return round((value - EPOCH_2001).total_seconds(), 3)


class RecordFieldsTest(unittest.TestCase):
    def test_times_and_device_come_from_top(self):
        created, modified, device = MODULE._record_fields(_archive(700000000.25, 700000100.5, 'Test Device'))
        self.assertEqual((_seconds(created), _seconds(modified), device), (700000000.25, 700000100.5, 'Test Device'))

    def test_null_entries_are_blank(self):
        self.assertEqual(MODULE._record_fields(_archive()), ('', '', ''))

    def test_absent_or_unreadable_blob_is_blank(self):
        for blob in (None, b'', b'not a plist', plistlib.dumps({'a': 1}, fmt=plistlib.PlistFormat.FMT_BINARY)):
            self.assertEqual(MODULE._record_fields(blob), ('', '', ''))


class HomeLibraryTest(unittest.TestCase):
    def test_home_libraries_are_read(self):
        for path in ('Users/alice/Library/KeyboardServices/TextReplacements.db',
                     'System/Volumes/Data/Users/alice/Library/KeyboardServices/TextReplacements.db',
                     'private/var/root/Library/KeyboardServices/TextReplacements.db'):
            self.assertTrue(MODULE._in_a_home_library(path), path)

    def test_nested_library_is_not_read(self):
        self.assertFalse(MODULE._in_a_home_library(
            'Users/alice/Library/Containers/com.example/Data/Library/KeyboardServices/TextReplacements.db'))


if __name__ == '__main__':
    unittest.main()
