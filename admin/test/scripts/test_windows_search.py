"""Pin how the Windows Search artifact finds its SystemIndex_PropertyStore columns."""
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsSearch
# pylint: enable=wrong-import-position

# The numbers one tested index gives these properties (lonewolf_win10's Windows.edb),
# which differ from the numbers another index gives the same properties.
NUMBERED = {
    'System_ItemNameDisplay': '4424-System_ItemNameDisplay',
    'System_ItemPathDisplay': '4428-System_ItemPathDisplay',
    'System_ItemUrl': '33-System_ItemUrl',
    'System_ItemTypeText': '5-System_ItemTypeText',
    'System_KindText': '4438-System_KindText',
    'System_Size': '13F-System_Size',
    'System_Search_GatherTime': '4612F-System_Search_GatherTime',
    'System_DateModified': '15F-System_DateModified',
    'System_DateCreated': '16F-System_DateCreated',
    'System_DateAccessed': '17F-System_DateAccessed',
}


class FakeWalk(list):
    """TableRows as the artifact uses it: iterable, with a summary of what it skipped."""

    @staticmethod
    def summary():
        return ''


class FakeDatabase:
    def __init__(self, names, rows=()):
        self._ESENT_DB__tables = {  # pylint: disable=invalid-name
            b'SystemIndex_PropertyStore': {'Columns': {c.encode(): {} for c in names}}}
        self.rows = rows

    def mountDB(self):  # pylint: disable=invalid-name
        pass

    def close(self):
        pass


def columns(**replace):
    names = dict(NUMBERED)
    names.update(replace)
    return ['WorkID'] + [c for c in names.values() if c]


class PropertyColumnTest(unittest.TestCase):
    def test_each_property_is_found_whatever_its_number(self):
        with mock.patch.object(windowsSearch, 'logfunc') as log:
            found = windowsSearch._property_columns(FakeDatabase(columns()))  # pylint: disable=protected-access
        self.assertEqual(found, NUMBERED)
        log.assert_not_called()

    def test_a_missing_property_is_left_out_and_logged(self):
        with mock.patch.object(windowsSearch, 'logfunc') as log:
            found = windowsSearch._property_columns(  # pylint: disable=protected-access
                FakeDatabase(columns(System_KindText=None)), 'Windows Search', 'x/Windows.edb')
        self.assertNotIn('System_KindText', found)
        self.assertIn('x/Windows.edb has no column for System_KindText', log.call_args.args[0])

    def test_a_property_two_columns_carry_is_not_guessed(self):
        names = columns() + ['4600-System_ItemNameDisplay']
        with mock.patch.object(windowsSearch, 'logfunc') as log:
            found = windowsSearch._property_columns(FakeDatabase(names))  # pylint: disable=protected-access
        self.assertNotIn('System_ItemNameDisplay', found)
        self.assertIn('has 2 columns for System_ItemNameDisplay', log.call_args.args[0])

    def test_rows_are_read_from_the_numbered_columns(self):
        stored = {b'WorkID': 7, NUMBERED['System_ItemNameDisplay'].encode(): 'report.docx',
                  NUMBERED['System_ItemPathDisplay'].encode(): 'C:\\Users\\u\\report.docx',
                  NUMBERED['System_KindText'].encode(): 'document',
                  NUMBERED['System_ItemTypeText'].encode(): 'Microsoft Word Document',
                  # an 8-byte FILETIME, stored as ASCII hex like the reader returns a binary column
                  NUMBERED['System_Search_GatherTime'].encode(): b'00e0a8b7f63fd601'}
        database = FakeDatabase(columns())
        with mock.patch.object(windowsSearch.ese_rows, 'ESEDatabase', return_value=database), \
                mock.patch.object(windowsSearch.ese_rows, 'TableRows', return_value=FakeWalk([stored])), \
                mock.patch.object(windowsSearch, 'logfunc'):
            rows = windowsSearch._read_property_store('Windows.edb')  # pylint: disable=protected-access
        self.assertEqual(len(rows), 1)
        gather, _modified, _created, _accessed, name, path, _url, kind_type, kind, _size, work_id = rows[0]
        self.assertEqual((name, path, kind_type, kind, work_id),
                         ('report.docx', 'C:\\Users\\u\\report.docx', 'Microsoft Word Document', 'document', 7))
        self.assertEqual(gather.year, 2020)

    def test_the_resolved_columns_are_read_from_the_long_value_tree(self):
        database = FakeDatabase(columns())
        with mock.patch.object(windowsSearch.ese_rows, 'ESEDatabase', return_value=database), \
                mock.patch.object(windowsSearch.ese_rows, 'TableRows', return_value=FakeWalk()) as walk, \
                mock.patch.object(windowsSearch, 'logfunc'):
            windowsSearch._read_property_store('Windows.edb')  # pylint: disable=protected-access
        self.assertEqual(walk.call_args.kwargs['long_value_columns'], set(NUMBERED.values()))


if __name__ == '__main__':
    unittest.main()
