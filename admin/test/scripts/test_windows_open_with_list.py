"""Pin the Open With list reader in scripts/artifacts/windowsOpenWithList.py.

The hive is stood in for by small objects that answer the python-registry calls the reader makes; the expected rows
are written out.
"""
import datetime
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsOpenWithList as openwith  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
PICKED = datetime.datetime(2021, 3, 4, 5, 6, 7, 800)
LATER = datetime.datetime(2022, 1, 2, 3, 4, 5, 6)
EXTS = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts'
HEADERS = (('Key Last Written (UTC)', 'datetime'), 'User', 'Extension', 'Order', 'Value', 'Program')


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=(), subkeys=(), written=PICKED):
        self._name = name
        self._values = [_Value(n, d) for n, d in values]
        self._subkeys = list(subkeys)
        self._written = written

    def name(self):
        return self._name

    def values(self):
        return self._values

    def subkeys(self):
        return self._subkeys

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
        return 'vol' + path.split('vol', 1)[1]


def _list(values, name='OpenWithList', written=PICKED):
    return _Key(name, values, written=written)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ListRowsTest(unittest.TestCase):
    def test_values_come_in_the_order_the_mru_list_gives_with_the_key_time(self):
        key = _list([('a', 'NOTEPAD.EXE'), ('MRUList', 'cab'), ('b', 'HxD.exe'), ('c', 'Vendor.App_8w!App')])
        self.assertEqual(openwith.list_rows(key, 'alice', '.TXT'), ([
            (PICKED.replace(tzinfo=UTC), 'alice', '.TXT', 1, 'c', 'Vendor.App_8w!App'),
            (PICKED.replace(tzinfo=UTC), 'alice', '.TXT', 2, 'a', 'NOTEPAD.EXE'),
            (PICKED.replace(tzinfo=UTC), 'alice', '.TXT', 3, 'b', 'HxD.exe')], []))

    def test_a_value_the_list_does_not_name_has_a_blank_order_and_comes_last_in_key_order(self):
        key = _list([('z', 'last.exe'), ('b', 'two.exe'), ('MRUList', 'a'), ('a', 'one.exe')])
        rows, missing = openwith.list_rows(key, 'u', '.x')
        self.assertEqual([row[3:] for row in rows], [(1, 'a', 'one.exe'), ('', 'z', 'last.exe'), ('', 'b', 'two.exe')])
        self.assertEqual(missing, [])

    def test_a_name_with_no_value_is_returned_once_and_keeps_its_position_and_a_repeat_is_used_once(self):
        key = _list([('MRUList', 'bzabqzqa'), ('a', 'one.exe'), ('b', 'two.exe')])
        rows, missing = openwith.list_rows(key, 'u', '.x')
        self.assertEqual([row[3:] for row in rows], [(1, 'b', 'two.exe'), (3, 'a', 'one.exe')])
        self.assertEqual(missing, ['z', 'q'])

    def test_the_list_name_is_matched_without_case_and_the_value_names_with_it(self):
        key = _list([('mrulist', 'aA'), ('A', 'upper.exe'), ('a', 'lower.exe')])
        rows, missing = openwith.list_rows(key, 'u', '.x')
        self.assertEqual([row[3:] for row in rows], [(1, 'a', 'lower.exe'), (2, 'A', 'upper.exe')])
        self.assertEqual(missing, [])

    def test_values_that_are_not_text_are_left_out_and_a_list_that_is_not_text_orders_nothing(self):
        key = _list([('MRUList', b'ab'), ('a', 'one.exe'), ('b', 7), ('c', b'\x00')])
        rows, missing = openwith.list_rows(key, 'u', '.x')
        self.assertEqual([row[3:] for row in rows], [('', 'a', 'one.exe')])
        self.assertEqual(missing, [])

    def test_a_key_with_no_value_or_only_the_list_gives_no_row(self):
        self.assertEqual(openwith.list_rows(_list([]), 'u', '.x'), ([], []))
        self.assertEqual(openwith.list_rows(_list([('MRUList', 'a')]), 'u', '.x'), ([], ['a']))

    def test_a_key_with_no_time_has_a_blank_time(self):
        rows, _missing = openwith.list_rows(_list([('a', 'x.exe')], written=None), 'u', '.x')
        self.assertEqual(rows, [('', 'u', '.x', '', 'a', 'x.exe')])


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ExtensionRowsTest(unittest.TestCase):
    def test_every_open_with_list_key_is_read_under_its_extension_name_and_other_subkeys_are_not(self):
        fileexts = _Key('FileExts', subkeys=[
            _Key('.png', subkeys=[_Key('OpenWithProgids', [('PhotoViewer', b'')]), _list([('a', 'paint.exe'), ('MRUList', 'ba'), ('b', 'photos.exe')]),
                                  _Key('UserChoice', [('ProgId', 'x'), ('MRUList', 'a'), ('a', 'no.exe')])]),
            _Key('.empty', subkeys=[_list([])]),
            _Key('.LOG', subkeys=[_list([('MRUList', 'ba'), ('a', 'one.exe')], name='openwithlist', written=LATER)]),
            _Key('.other', subkeys=[_list([('a', 'no.exe')], name='OpenWithList2'), _list([('a', 'no.exe')], name='XOpenWithList')]),
            _list([('a', 'no.exe')])])
        rows, missing = openwith.extension_rows(fileexts, 'bob')
        self.assertEqual(rows, [(PICKED.replace(tzinfo=UTC), 'bob', '.png', 1, 'b', 'photos.exe'),
                                (PICKED.replace(tzinfo=UTC), 'bob', '.png', 2, 'a', 'paint.exe'),
                                (LATER.replace(tzinfo=UTC), 'bob', '.LOG', 2, 'a', 'one.exe')])
        self.assertEqual(missing, 1)

    def test_missing_names_are_counted_over_every_key(self):
        fileexts = _Key(subkeys=[_Key('.a', subkeys=[_list([('MRUList', 'xy')])]), _Key('.b', subkeys=[_list([('MRUList', 'z')])])])
        self.assertEqual(openwith.extension_rows(fileexts, 'u'), ([], 3))


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.paths = []
        for name in ('vol1/Users/alice/NTUSER.DAT', 'vol1/Users/bob/NTUSER.DAT', 'vol1/Users/carol/NTUSER.DAT',
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
        with mock.patch.object(openwith, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(openwith, 'logfunc', side_effect=logged.append):
            result = openwith.openWithList.__wrapped__(_Context(self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_each_user_hive_is_read_under_the_user_folder_name_and_a_missing_name_is_logged(self):
        hives = {self.alice: _Hive({EXTS: _Key(subkeys=[_Key('.txt', subkeys=[_list([('MRUList', 'ab'), ('b', 'HxD.exe')])]),
                                                        _Key('.asc', subkeys=[_list([('a', 'kleo.exe')])])])}),
                 self.bob: _Hive({EXTS: _Key(subkeys=[_Key('.pdf', subkeys=[_list([('MRUList', 'a'), ('a', 'reader.exe')], written=LATER)])])}),
                 self.carol: _Hive({})}
        (headers, rows, source), opened, logged = self.run_artifact(hives)
        self.assertEqual(headers, HEADERS)
        self.assertEqual(rows, [(PICKED.replace(tzinfo=UTC), 'alice', '.txt', 2, 'b', 'HxD.exe'),
                                (PICKED.replace(tzinfo=UTC), 'alice', '.asc', '', 'a', 'kleo.exe'),
                                (LATER.replace(tzinfo=UTC), 'bob', '.pdf', 1, 'a', 'reader.exe')])
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(opened, [self.alice, self.bob, self.carol])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol]))
        self.assertEqual(logged, ['Open With List: MRUList values of vol1/Users/alice/NTUSER.DAT list 1 value name(s) their key '
                                  'does not hold'])

    @unittest.skipIf(Registry is None, 'python-registry is not installed')
    def test_an_unreadable_hive_is_logged_by_its_path_in_the_extraction_and_skipped(self):
        broken = _Key(subkeys=[_Key('.pdf', subkeys=[_list([('a', 'x.exe')], written='not a time')])])
        hives = {self.alice: ValueError('bad header'),
                 self.bob: _Hive({EXTS: _Key(subkeys=[_Key('.txt', subkeys=[_list([('a', 'one.exe')])])])}),
                 self.carol: _Hive({EXTS: broken})}
        (_headers, rows, source), _opened, logged = self.run_artifact(hives)
        self.assertEqual([(row[1], row[2], row[5]) for row in rows], [('bob', '.txt', 'one.exe')])
        self.assertEqual(source, self.bob)
        self.assertEqual(logged[0], 'Open With List: could not read vol1/Users/alice/NTUSER.DAT: bad header')
        self.assertTrue(logged[1].startswith('Open With List: could not read vol1/Users/carol/NTUSER.DAT: '))
        self.assertEqual(len(logged), 2)

    def test_without_python_registry_nothing_is_read_and_the_run_log_says_so(self):
        logged = []
        with mock.patch.object(openwith, 'Registry', None), mock.patch.object(openwith, 'open_hive') as opened, \
                mock.patch.object(openwith, 'logfunc', side_effect=logged.append):
            headers, rows, source = openwith.openWithList.__wrapped__(_Context(self.paths))
        self.assertEqual((headers, rows, source), (HEADERS, [], ''))
        opened.assert_not_called()
        self.assertEqual(logged, ['Open With List: the python-registry package is not installed'])


if __name__ == '__main__':
    unittest.main()
