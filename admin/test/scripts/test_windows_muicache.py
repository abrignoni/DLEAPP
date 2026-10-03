"""Pin the MUICache reader in scripts/artifacts/windowsMuiCache.py.

The hive is stood in for by small objects that answer the python-registry calls the reader makes; the expected rows
are written out.
"""
import datetime
import pathlib
import re
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsMuiCache as mui  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

# The fixtures put each hive under a vol<N> folder; match it as a whole path segment, since the
# temporary folder above it can contain the letters vol.
_VOLUME = re.compile(r'[\\/]vol(?=\d)')

UTC = datetime.timezone.utc
WRITTEN = datetime.datetime(2020, 9, 19, 1, 8, 25, 387016)
WHEN = WRITTEN.replace(tzinfo=UTC)
MUICACHE = 'Local Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache'


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, values=(), written=WRITTEN):
        self._values = [_Value(name, data) for name, data in values]
        self._written = written

    def values(self):
        return self._values

    def timestamp(self):
        return self._written


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return 'vol' + _VOLUME.split(path, maxsplit=1)[1]


VALUES = [('LangID', b'\t\x04'),
          ('D:\\setup64.exe.FriendlyAppName', 'Installation launcher'),
          ('D:\\setup64.exe.ApplicationCompany', 'Example, Inc.'),
          ('C:\\Windows\\system32\\shell32.dll.ApplicationCompany', 'Example Corporation'),
          ('C:\\Tools\\only name.exe.FriendlyAppName', 'Only Name'),
          ('C:\\Windows\\system32\\shell32.dll.FriendlyAppName', 'Shell Common Dll')]


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class MuiRowsTest(unittest.TestCase):
    def test_the_two_values_of_a_path_make_one_row_in_the_order_first_named(self):
        rows, skipped = mui.mui_rows(_Key(VALUES), 'alice')
        self.assertEqual(rows, [(WHEN, 'alice', 'D:\\setup64.exe', 'Installation launcher', 'Example, Inc.'),
                                (WHEN, 'alice', 'C:\\Windows\\system32\\shell32.dll', 'Shell Common Dll',
                                 'Example Corporation'),
                                (WHEN, 'alice', 'C:\\Tools\\only name.exe', 'Only Name', '')])
        self.assertEqual(skipped, 1)

    def test_a_suffix_is_matched_without_case_and_the_path_keeps_its_own(self):
        rows, skipped = mui.mui_rows(_Key([('C:\\A\\App.EXE.friendlyappname', 'App'),
                                           ('C:\\A\\App.EXE.APPLICATIONCOMPANY', 'Maker')]), 'bob')
        self.assertEqual((rows, skipped), ([(WHEN, 'bob', 'C:\\A\\App.EXE', 'App', 'Maker')], 0))

    def test_two_spellings_of_one_path_stay_two_rows(self):
        rows, _skipped = mui.mui_rows(_Key([('C:\\Windows\\System32\\x.dll.FriendlyAppName', 'X'),
                                            ('C:\\Windows\\system32\\x.dll.FriendlyAppName', 'X')]), 'bob')
        self.assertEqual([row[2] for row in rows], ['C:\\Windows\\System32\\x.dll', 'C:\\Windows\\system32\\x.dll'])

    def test_a_value_named_only_for_a_suffix_or_for_neither_is_skipped(self):
        rows, skipped = mui.mui_rows(_Key([('.FriendlyAppName', 'nothing before it'), ('LangID', b'\t\x04'),
                                           ('C:\\a.exe.Other', 'x'), ('C:\\a.exe.FriendlyAppName.old', 'not at the end')]),
                                     'bob')
        self.assertEqual((rows, skipped), ([], 4))

    def test_data_that_is_not_text_is_shown_through_str_and_none_is_blank(self):
        rows, _skipped = mui.mui_rows(_Key([('C:\\a.exe.FriendlyAppName', 7), ('C:\\a.exe.ApplicationCompany', None)]),
                                      'bob')
        self.assertEqual(rows, [(WHEN, 'bob', 'C:\\a.exe', '7', '')])


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.paths = []
        for name in ('vol1/Users/alice/AppData/Local/Microsoft/Windows/UsrClass.dat',
                     'vol1/Users/bob/AppData/Local/Microsoft/Windows/usrClass.dat',
                     'vol1/Users/carol/AppData/Local/Microsoft/Windows/UsrClass.dat',
                     'vol1/Users/alice/AppData/Local/Microsoft/Windows/UsrClass.dat.LOG1',
                     'vol1/Users/alice/NTUSER.DAT'):
            # the staged path sits under the examiner's own Users folder, as a report folder often does
            path = pathlib.Path(folder.name, 'Users', 'examiner', 'report', 'data', name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            self.paths.append(str(path))
        self.alice, self.bob, self.carol = self.paths[0], self.paths[1], self.paths[2]

    def run_artifact(self, hives):
        def opener(path, _context=None):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(mui, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(mui, 'logfunc', side_effect=logged.append):
            result = mui.muiCache.__wrapped__(_Context(self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def test_each_user_hive_gives_its_own_rows_under_the_user_folder_name(self):
        later = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
        hives = {self.alice: _Hive({MUICACHE: _Key(VALUES[:3])}),
                 self.bob: _Hive({MUICACHE: _Key(VALUES[4:5], later)}), self.carol: _Hive({})}
        (headers, rows, source), opened, logged = self.run_artifact(hives)
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'User', 'Program', 'Friendly App Name',
                                   'Company'))
        self.assertEqual(rows, [(WHEN, 'alice', 'D:\\setup64.exe', 'Installation launcher', 'Example, Inc.'),
                                (later.replace(tzinfo=UTC), 'bob', 'C:\\Tools\\only name.exe', 'Only Name', '')])
        self.assertEqual(opened, [self.alice, self.bob, self.carol])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol]))
        self.assertEqual(logged, ['MUICache: 1 value(s) of vol1/Users/alice/AppData/Local/Microsoft/Windows/UsrClass.dat '
                                  'are not named for a friendly name or a company and are not reported'])

    def test_an_unreadable_hive_is_logged_by_its_path_in_the_extraction_and_skipped(self):
        hives = {self.alice: ValueError('bad header'), self.bob: _Hive({MUICACHE: _Key(VALUES[1:3])}),
                 self.carol: _Hive({})}
        (_headers, rows, source), _opened, logged = self.run_artifact(hives)
        self.assertEqual([row[1:3] for row in rows], [('bob', 'D:\\setup64.exe')])
        self.assertEqual(source, self.bob + '\n' + self.carol)
        self.assertEqual(logged, ['MUICache: could not read vol1/Users/alice/AppData/Local/Microsoft/Windows/'
                                  'UsrClass.dat: bad header'])

    def test_without_python_registry_nothing_is_read(self):
        with mock.patch.object(mui, 'Registry', None), mock.patch.object(mui, 'logfunc') as log, \
                mock.patch.object(mui, 'open_hive') as opened:
            _headers, rows, source = mui.muiCache.__wrapped__(_Context(self.paths))
        self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
