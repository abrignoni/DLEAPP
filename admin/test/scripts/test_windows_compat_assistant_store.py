"""Pin the Compatibility Assistant Store reader in scripts/artifacts/windowsCompatAssistantStore.py.

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

from scripts.artifacts import windowsCompatAssistantStore as store  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

# The fixtures put each hive under a vol<N> folder; match it as a whole path segment, since the
# temporary folder above it can contain the letters vol.
_VOLUME = re.compile(r'[\\/]vol(?=\d)')

UTC = datetime.timezone.utc
WRITTEN = datetime.datetime(2020, 9, 19, 5, 9, 56, 145644)
STORE = ('Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Compatibility Assistant\\Store')


class _Value:
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class _Key:
    def __init__(self, names=(), written=WRITTEN):
        self._values = [_Value(name) for name in names]
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


NAMES = ['SIGN.MEDIA=11692A28 Imager\\Imager.exe', 'c:\\users\\alice\\downloads\\Mixed Case.EXE',
         'C:\\Program Files\\Tool\\Tool.exe', '\\\\server\\share\\setup.exe']


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class StoreRowsTest(unittest.TestCase):
    def test_one_row_per_value_with_the_name_as_stored_and_the_key_time(self):
        self.assertEqual(store.store_rows(_Key(NAMES), 'alice'),
                         [(WRITTEN.replace(tzinfo=UTC), 'alice', name) for name in NAMES])

    def test_a_key_with_no_values_gives_no_rows(self):
        self.assertEqual(store.store_rows(_Key(), 'alice'), [])


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.paths = []
        for name in ('vol1/Users/alice/NTUSER.DAT', 'vol1/Users/bob/ntuser.dat', 'vol1/Users/carol/NTUSER.DAT',
                     'vol1/Users/alice/NTUSER.DAT.LOG1', 'vol1/Users/alice/AppData/Local/Microsoft/Windows/UsrClass.dat'):
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
        with mock.patch.object(store, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(store, 'logfunc', side_effect=logged.append):
            result = store.compatibilityAssistantStore.__wrapped__(_Context(self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def test_each_user_hive_gives_its_own_rows_under_the_user_folder_name(self):
        later = datetime.datetime(2021, 1, 2, 3, 4, 5, 6)
        hives = {self.alice: _Hive({STORE: _Key(NAMES[:2])}), self.bob: _Hive({STORE: _Key(NAMES[2:], later)}),
                 self.carol: _Hive({})}
        (headers, rows, source), opened, logged = self.run_artifact(hives)
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'User', 'Program'))
        self.assertEqual(rows, [(WRITTEN.replace(tzinfo=UTC), 'alice', NAMES[0]),
                                (WRITTEN.replace(tzinfo=UTC), 'alice', NAMES[1]),
                                (later.replace(tzinfo=UTC), 'bob', NAMES[2]), (later.replace(tzinfo=UTC), 'bob', NAMES[3])])
        self.assertEqual(opened, [self.alice, self.bob, self.carol])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol]))
        self.assertEqual(logged, [])

    def test_an_unreadable_hive_is_logged_by_its_path_in_the_extraction_and_skipped(self):
        hives = {self.alice: ValueError('bad header'), self.bob: _Hive({STORE: _Key(NAMES[:1])}), self.carol: _Hive({})}
        (_headers, rows, source), _opened, logged = self.run_artifact(hives)
        self.assertEqual([row[1:] for row in rows], [('bob', NAMES[0])])
        self.assertEqual(source, self.bob + '\n' + self.carol)
        self.assertEqual(logged, ['Compatibility Assistant Store: could not read vol1/Users/alice/NTUSER.DAT: bad header'])

    def test_without_python_registry_nothing_is_read(self):
        with mock.patch.object(store, 'Registry', None), mock.patch.object(store, 'logfunc') as log, \
                mock.patch.object(store, 'open_hive') as opened:
            _headers, rows, source = store.compatibilityAssistantStore.__wrapped__(_Context(self.paths))
        self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
