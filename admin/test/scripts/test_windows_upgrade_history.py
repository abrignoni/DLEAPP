"""Pin the Upgrade History (Source OS) artifact (scripts/artifacts/windowsUpgradeHistory.py).

The hive is stood in for by small objects that answer the python-registry calls the reader makes. The first key has
the value names and types of the Source OS key on pc_mus_001_win11; the owner, product ID and second key are made up.
"""
import datetime
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsUpgradeHistory as uh
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
T1 = datetime.datetime(2022, 11, 23, 0, 29, 7)
T2 = datetime.datetime(2024, 1, 2, 3, 4, 5)
FIRST = 'Source OS (Updated on 11/22/2022 19:09:57)'
SECOND = 'source os (updated on 2.1.2024 03:00:00)'


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=None, subkeys=(), written=T1):
        self._name, self._values, self._subkeys, self._written = name, values or {}, list(subkeys), written

    def name(self):
        return self._name

    def values(self):
        return [_Value(name, data) for name, data in self._values.items()]

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


HIVE = _Hive({'Setup': _Key(subkeys=[
    _Key('Pid', {'Pid': 'x'}),
    _Key(FIRST, {'ProductName': 'Windows 10 Home', 'DisplayVersion': '22H2', 'ReleaseId': '2009', 'CurrentBuild': '19045',
                 'UBR': 2006, 'EditionID': 'Core', 'RegisteredOwner': 'made-up owner', 'RegisteredOrganization': '',
                 'ProductId': '00000-00000-00000-AAAAA', 'SystemRoot': 'C:\\Windows', 'InstallDate': 1668183044,
                 'InstallTime': 133126566444793368, 'DigitalProductId': b'\x01\x02', 'PathName': 'C:\\Windows'}),
    _Key(SECOND, {'productname': 'Windows 8.1', 'INSTALLDATE': 'not a number', 'ProductId': b'\x00'}, written=T2),
    _Key('Source OS', {'ProductName': 'no time in the name'}),
    _Key('Upgrade', {'DownlevelBuildNumber': '10.0.19045'})])})
ROWS = [
    (datetime.datetime(2022, 11, 11, 16, 10, 44, tzinfo=UTC), datetime.datetime(2022, 11, 11, 16, 10, 44, 479336, tzinfo=UTC),
     '11/22/2022 19:09:57', T1.replace(tzinfo=UTC), 'Windows 10 Home', '22H2', '2009', '19045', 2006, 'Core',
     'made-up owner', '', '00000-00000-00000-AAAAA', 'C:\\Windows', 'Setup\\' + FIRST),
    ('', '', '2.1.2024 03:00:00', T2.replace(tzinfo=UTC), 'Windows 8.1', '', '', '', '', '', '', '', '', '',
     'Setup\\' + SECOND)]


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Rows(unittest.TestCase):
    def test_a_hive(self):
        self.assertEqual(uh.source_os_rows(HIVE), ROWS)

    def test_no_setup_key(self):
        self.assertEqual(uh.source_os_rows(_Hive({})), [])

    def test_processor(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        by_path = {}
        for name, hive in (('a', HIVE), ('ab', None), ('b', _Hive({'Setup': _Key()})), ('c', HIVE)):
            path = pathlib.Path(folder.name, name, 'Windows', 'System32', 'config', 'SYSTEM')
            path.parent.mkdir(parents=True)
            path.write_bytes(b'')
            by_path[str(path)] = hive

        def opened(path, _context=None):
            if by_path[path] is None:
                raise ValueError('not a hive')
            return by_path[path]

        context = mock.Mock()
        context.get_relative_path.side_effect = lambda p: pathlib.Path(p).relative_to(folder.name).as_posix()
        with mock.patch.object(uh, 'found_hives', return_value=sorted(by_path, reverse=True)), \
                mock.patch.object(uh, 'open_hive', side_effect=opened), mock.patch.object(uh, 'logfunc') as log:
            headers, rows, located = uh.windowsUpgradeHistory.__wrapped__(context)
        self.assertEqual(len(headers), 16)
        self.assertEqual(headers[:4], (('Install Date (UTC)', 'datetime'), ('Install Time (UTC)', 'datetime'),
                                       'Updated On (Key Name)', ('Key Last Written (UTC)', 'datetime')))
        self.assertEqual(rows, [row + (f'{name}/Windows/System32/config/SYSTEM',) for name in ('a', 'c') for row in ROWS])
        self.assertEqual(located, '\n'.join(str(pathlib.Path(folder.name, name, 'Windows', 'System32', 'config', 'SYSTEM'))
                                            for name in ('a', 'c')))
        log.assert_called_once()
        self.assertIn('could not read ab/Windows/System32/config/SYSTEM: not a hive', log.call_args[0][0])

    def test_no_library(self):
        with mock.patch.object(uh, 'Registry', None), mock.patch.object(uh, 'logfunc') as log:
            self.assertEqual(uh.windowsUpgradeHistory.__wrapped__(mock.Mock())[1:], ([], ''))
        log.assert_called_once()


if __name__ == '__main__':
    unittest.main()
