"""Pin the 7-Zip History artifact (scripts/artifacts/windows7ZipHistory.py).

The hive is stood in for by small objects that answer the python-registry calls the reader makes. The lists have
the layout 7-Zip 25.01 wrote on windows11_arm_7zip_known_20261010: UTF-16 strings, each ended by a zero.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windows7ZipHistory as sz
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
T1, T2, T3 = (datetime.datetime(2026, 10, 10, 18, 49, s) for s in (7, 13, 21))


def packed(*strings):
    return b''.join((s + '\0').encode('utf-16-le') for s in strings)


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data

    def raw_data(self):
        return self._data


class _Key:
    def __init__(self, values, written):
        self._values, self._written = values, written

    def values(self):
        return [_Value(name, data) for name, data in self._values.items()]

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
    'Software\\7-Zip\\Compression': _Key({'Level': 5, 'ArcHistory': packed('C:\\known\\one.7z', 'D:\\old.zip')}, T1),
    'Software\\7-Zip\\Extraction': _Key({'PATHHISTORY': packed('C:\\known\\out1\\'), 'ShowPassword': 0}, T2),
    'Software\\7-Zip\\FM': _Key({'FolderHistory': packed('C:\\known\\', '', 'C:\\caf\u00e9\\'), 'CopyHistory': b'',
                                 'FolderShortcuts': packed('E:\\'), 'PanelPath0': 'C:\\known\\', 'PanelPath1': '',
                                 'Panels': b'\x01\x00', 'ListMode': 771, 'PanelPathX': 7}, T3),
})
W1, W2, W3 = (t.replace(tzinfo=UTC) for t in (T1, T2, T3))
ROWS = [(W1, 'Add to Archive: archive paths', 1, 'C:\\known\\one.7z', 'Compression\\ArcHistory'),
        (W1, 'Add to Archive: archive paths', 2, 'D:\\old.zip', 'Compression\\ArcHistory'),
        (W2, 'Extract: destination folders', 1, 'C:\\known\\out1\\', 'Extraction\\PATHHISTORY'),
        (W3, 'File Manager: folder history', 1, 'C:\\known\\', 'FM\\FolderHistory'),
        (W3, 'File Manager: folder history', 2, '', 'FM\\FolderHistory'),
        (W3, 'File Manager: folder history', 3, 'C:\\caf\u00e9\\', 'FM\\FolderHistory'),
        (W3, 'File Manager: folder shortcuts', 1, 'E:\\', 'FM\\FolderShortcuts'),
        (W3, 'File Manager: panel path', '', 'C:\\known\\', 'FM\\PanelPath0'),
        (W3, 'File Manager: panel path', '', '', 'FM\\PanelPath1')]


class Lists(unittest.TestCase):
    def test_strings(self):
        self.assertEqual(sz.list_strings(packed('a', '', 'b c')), (['a', '', 'b c'], 0))
        self.assertEqual(sz.list_strings(b''), ([], 0))
        self.assertEqual(sz.list_strings(packed('')), ([''], 0))

    def test_what_follows_the_last_terminator_is_not_read(self):
        self.assertEqual(sz.list_strings(packed('a') + 'tail'.encode('utf-16-le')), (['a'], 4))
        self.assertEqual(sz.list_strings('none'.encode('utf-16-le')), ([], 4))

    def test_an_odd_number_of_bytes_is_refused(self):
        self.assertEqual(sz.list_strings(packed('a') + b'\x00'), (None, 0))

    def test_a_zero_byte_inside_a_unit_is_no_terminator(self):
        self.assertEqual(sz.list_strings('\u0100\u0001'.encode('utf-16-le') + b'\x00\x00'), (['\u0100\u0001'], 0))

    def test_an_unpaired_surrogate(self):
        self.assertEqual(sz.list_strings(b'\x00\xd8\x00\x00'), (['\\x00\\xd8'], 0))


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Rows(unittest.TestCase):
    def test_a_hive(self):
        counts = Counter()
        self.assertEqual(sz.history_rows(HIVE, counts), ROWS)
        self.assertEqual(counts, {})

    def test_damaged_lists_are_counted(self):
        counts = Counter()
        hive = _Hive({'Software\\7-Zip\\Compression': _Key({'ArcHistory': b'\x41\x00\x00'}, T1),
                      'Software\\7-Zip\\FM': _Key({'CopyHistory': packed('C:\\x\\') + 'yz'.encode('utf-16-le')}, T3)})
        self.assertEqual(sz.history_rows(hive, counts),
                         [(W3, 'File Manager: copy destinations', 1, 'C:\\x\\', 'FM\\CopyHistory')])
        self.assertEqual(counts, {'lists that are not whole 16-bit units, not read': 1,
                                  '16-bit units after the last terminator of a list, not read': 2})

    def test_no_7zip_key(self):
        self.assertEqual(sz.history_rows(_Hive({}), Counter()), [])

    def test_processor(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        by_path = {}
        other = _Hive({'Software\\7-Zip\\Extraction': _Key({'PathHistory': packed('Z:\\out\\')}, T2)})
        for user, hive in (('a', HIVE), ('ab', None), ('b', _Hive({})), ('c', other)):
            path = pathlib.Path(folder.name, 'C', 'Users', user, 'NTUSER.DAT')
            path.parent.mkdir(parents=True)
            path.write_bytes(b'')
            by_path[str(path)] = hive

        def opened(path, _context=None):
            if by_path[path] is None:
                raise ValueError('not a hive')
            return by_path[path]

        context = mock.Mock()
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, folder.name).replace(os.sep, '/')
        with mock.patch.object(sz, 'found_hives', return_value=sorted(by_path, reverse=True)), \
                mock.patch.object(sz, 'open_hive', side_effect=opened), mock.patch.object(sz, 'logfunc') as log:
            headers, rows, located = sz.sevenZipHistory.__wrapped__(context)
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), 'List', 'Position', 'Path', 'Value', 'User',
                                   'Source File'))
        self.assertEqual(rows, [row + ('a', 'C/Users/a/NTUSER.DAT') for row in ROWS]
                         + [(W2, 'Extract: destination folders', 1, 'Z:\\out\\', 'Extraction\\PathHistory', 'c',
                             'C/Users/c/NTUSER.DAT')])
        self.assertEqual(located, '\n'.join(str(pathlib.Path(folder.name, 'C', 'Users', user, 'NTUSER.DAT'))
                                            for user in ('a', 'c')))
        log.assert_called_once()
        self.assertIn('could not read C/Users/ab/NTUSER.DAT: not a hive', log.call_args[0][0])

    def test_no_library(self):
        with mock.patch.object(sz, 'Registry', None), mock.patch.object(sz, 'logfunc') as log:
            self.assertEqual(sz.sevenZipHistory.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
