"""Pin the 7-Zip artifact (scripts/artifacts/windowsSevenZip.py).

The hive is stood in for by small objects that answer the python-registry calls the reader makes; the values are
made up (no real account names or paths).
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsSevenZip as sz
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
TR = datetime.datetime(2026, 10, 10, 1, 0, 0, tzinfo=UTC)
TC = datetime.datetime(2026, 10, 10, 2, 0, 0, tzinfo=UTC)
TE = datetime.datetime(2026, 10, 10, 3, 0, 0, tzinfo=UTC)
TF = datetime.datetime(2026, 10, 10, 4, 0, 0, tzinfo=UTC)


def hist(*paths):
    return ''.join(p + '\x00' for p in paths).encode('utf-16-le')


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, values, written):
        self._values, self._written = values, written

    def values(self):
        return [_Value(n, d) for n, d in self._values.items()]

    def timestamp(self):
        return self._written


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


HIVE = _Hive({
    'Software\\7-Zip': _Key({'Path': 'C:\\Program Files\\7-Zip\\', 'Path64': 'C:\\Program Files\\7-Zip\\'}, TR),
    'Software\\7-Zip\\Compression': _Key({'Archiver': 'zip', 'Level': 9, 'EncryptHeaders': 0, 'ShowPassword': 1,
                                          'ArcHistory': hist('C:\\a.7z', 'D:\\b.7z')}, TC),
    'Software\\7-Zip\\Extraction': _Key({'ShowPassword': 0, 'PathHistory': hist('C:\\out\\')}, TE),
    'Software\\7-Zip\\FM': _Key({'PanelPath0': 'C:\\x\\', 'PanelPath1': '',
                                 'FolderHistory': hist('C:\\f1\\', '\\\\srv\\share\\'),
                                 'CopyHistory': hist('E:\\')}, TF),
})
REL = 'a/Users/tester/NTUSER.DAT'
ROWS = [
    (TR, 'Install', 'Path', 'C:\\Program Files\\7-Zip\\', 'tester', REL),
    (TR, 'Install', 'Path64', 'C:\\Program Files\\7-Zip\\', 'tester', REL),
    (TC, 'Compression', 'Archiver', 'zip', 'tester', REL),
    (TC, 'Compression', 'Level', '9', 'tester', REL),
    (TC, 'Compression', 'EncryptHeaders', '0', 'tester', REL),
    (TC, 'Compression', 'ShowPassword', '1', 'tester', REL),
    (TE, 'Extraction', 'ShowPassword', '0', 'tester', REL),
    (TF, 'File Manager', 'PanelPath0', 'C:\\x\\', 'tester', REL),
    (TF, 'File Manager', 'PanelPath1', '', 'tester', REL),
    (TC, 'Archive history', 'ArcHistory #1', 'C:\\a.7z', 'tester', REL),
    (TC, 'Archive history', 'ArcHistory #2', 'D:\\b.7z', 'tester', REL),
    (TE, 'Extraction history', 'PathHistory #1', 'C:\\out\\', 'tester', REL),
    (TF, 'Folder history', 'FolderHistory #1', 'C:\\f1\\', 'tester', REL),
    (TF, 'Folder history', 'FolderHistory #2', '\\\\srv\\share\\', 'tester', REL),
    (TF, 'Copy history', 'CopyHistory #1', 'E:\\', 'tester', REL),
]


class SevenZip(unittest.TestCase):
    def test_history_paths(self):
        self.assertEqual(sz.history_paths(hist('C:\\a.7z', 'D:\\b.7z')), ['C:\\a.7z', 'D:\\b.7z'])
        self.assertEqual(sz.history_paths(b''), [])
        self.assertEqual(sz.history_paths(None), [])

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_rows(self):
        self.assertEqual(sz.seven_zip_rows(HIVE, REL), ROWS)

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_no_seven_zip_key(self):
        self.assertEqual(sz.seven_zip_rows(_Hive({}), REL), [])

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_processor(self):
        by_path = {'a/Users/tester/NTUSER.DAT': HIVE, 'b/Users/none/NTUSER.DAT': _Hive({})}
        context = mock.Mock()
        context.get_relative_path.side_effect = lambda p: p
        with mock.patch.object(sz, 'found_hives', return_value=sorted(by_path)), \
                mock.patch.object(sz, 'open_hive', side_effect=lambda p, _c=None: by_path[p]), \
                mock.patch.object(sz, 'logfunc'):
            headers, rows, located = sz.windowsSevenZip.__wrapped__(context)
        self.assertEqual(headers[0], ('Key Last Written (UTC)', 'datetime'))
        self.assertEqual(rows, ROWS)                         # only the hive with the key contributes
        self.assertEqual(located, 'a/Users/tester/NTUSER.DAT')  # the empty hive is not listed

    def test_no_library(self):
        with mock.patch.object(sz, 'Registry', None), mock.patch.object(sz, 'logfunc') as log:
            self.assertEqual(sz.windowsSevenZip.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
