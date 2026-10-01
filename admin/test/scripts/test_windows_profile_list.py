"""Pin the ProfileList reader in scripts/artifacts/windowsProfileList.py.

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

from scripts.artifacts import windowsProfileList as profiles  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
WRITTEN = datetime.datetime(2023, 2, 22, 23, 46, 5, 406186)
LOAD = datetime.datetime(2023, 2, 22, 23, 37, 4, 976245, tzinfo=UTC)
UNLOAD = datetime.datetime(2023, 2, 22, 23, 46, 5, 406186, tzinfo=UTC)


def halves(moment):
    """The High and Low halves of the FILETIME of an aware UTC time."""
    since = moment - datetime.datetime(1601, 1, 1, tzinfo=UTC)
    ticks = ((since.days * 86400 + since.seconds) * 1000000 + since.microseconds) * 10
    return ticks >> 32, ticks & 0xFFFFFFFF


class _Value:
    def __init__(self, data):
        self._data = data

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=None, subkeys=(), written=WRITTEN):
        self._name = name
        self._values = values or {}
        self._subkeys = list(subkeys)
        self._written = written

    def name(self):
        return self._name

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(self._values[name])

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


SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
PROFILE_LIST = 'Microsoft\\Windows NT\\CurrentVersion\\ProfileList'


def user_profile(load=LOAD, unload=UNLOAD, **more):
    values = {'ProfileImagePath': 'C:\\Users\\alice', 'State': 0, 'Flags': 0, 'FullProfile': 1}
    for name, moment in (('LocalProfileLoadTime', load), ('LocalProfileUnloadTime', unload)):
        if moment is not None:
            values[name + 'High'], values[name + 'Low'] = halves(moment)
    values.update(more)
    return _Key(SID, values)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ProfileRowTest(unittest.TestCase):
    def test_each_column_carries_its_own_value(self):
        self.assertEqual(profiles.profile_row(user_profile()),
                         (WRITTEN.replace(tzinfo=UTC), LOAD, UNLOAD, SID, 'C:\\Users\\alice', 0))

    def test_load_and_unload_are_not_swapped_and_keep_their_microseconds(self):
        later = datetime.datetime(2023, 3, 1, 8, 0, 0, 123456, tzinfo=UTC)
        row = profiles.profile_row(user_profile(load=later, unload=UNLOAD))
        self.assertEqual((row[1], row[2]), (later, UNLOAD))

    def test_a_profile_without_the_time_values_has_blank_times(self):
        system = {'ProfileImagePath': '%systemroot%\\system32\\config\\systemprofile', 'State': 0, 'Flags': 12}
        row = profiles.profile_row(_Key('S-1-5-18', system))
        self.assertEqual(row, (WRITTEN.replace(tzinfo=UTC), '', '', 'S-1-5-18',
                               '%systemroot%\\system32\\config\\systemprofile', 0))

    def test_a_zero_time_or_one_missing_half_is_blank(self):
        zero = user_profile(load=None, unload=None, LocalProfileLoadTimeHigh=0, LocalProfileLoadTimeLow=0,
                            LocalProfileUnloadTimeHigh=halves(UNLOAD)[0])
        self.assertEqual(profiles.profile_row(zero)[1:3], ('', ''))

    def test_the_older_profile_load_time_values_are_not_read(self):
        high, low = halves(LOAD)
        older = user_profile(load=None, unload=None, ProfileLoadTimeHigh=high, ProfileLoadTimeLow=low)
        row = profiles.profile_row(older)
        self.assertEqual(row[1:3], ('', ''))

    def test_a_stored_state_is_kept_as_a_number_and_an_absent_one_is_blank(self):
        self.assertEqual(profiles.profile_row(user_profile(State=772))[5], 772)
        self.assertEqual(profiles.profile_row(_Key(SID, {}))[4:], ('', ''))

    def test_split_filetime(self):
        high, low = halves(LOAD)
        key = _Key('x', {'THigh': high, 'TLow': low, 'TextHigh': '1', 'TextLow': 2, 'HalfLow': low, 'OtherHigh': high})
        self.assertEqual(profiles.split_filetime(key, 'T'), LOAD)
        self.assertEqual(profiles.split_filetime(key, 'Half'), '')
        self.assertEqual(profiles.split_filetime(key, 'Other'), '')
        self.assertEqual(profiles.split_filetime(_Key('x', {'BigHigh': 0xFFFFFFFF, 'BigLow': 0}), 'Big'), '')
        self.assertEqual(profiles.split_filetime(key, 'Text'), '')
        self.assertEqual(profiles.split_filetime(key, 'Absent'), '')


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.paths = []
        for name in ('vol1/Windows/System32/config/SOFTWARE', 'vol2/Windows/System32/config/software',
                     'vol1/Windows/System32/config/SOFTWARE.LOG1', 'vol1/Windows/System32/config/SYSTEM'):
            path = pathlib.Path(folder.name, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            self.paths.append(str(path))
        self.one, self.two = self.paths[0], self.paths[1]

    def run_artifact(self, hives):
        def opener(path, _context=None):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(profiles, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(profiles, 'logfunc', side_effect=logged.append):
            result = profiles.userProfileList.__wrapped__(_Context(self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def test_one_row_per_subkey_from_each_software_hive(self):
        system = _Key('S-1-5-18', {'ProfileImagePath': 'sys', 'State': 0})
        hive = _Hive({PROFILE_LIST: _Key(values={'ProfilesDirectory': '%SystemDrive%\\Users'},
                                         subkeys=[system, user_profile()])})
        other = _Hive({PROFILE_LIST: _Key(subkeys=[user_profile(State=772)])})
        (headers, rows, source), opened, logged = self.run_artifact({self.one: hive, self.two: other})
        self.assertEqual(headers, (('Key Last Written (UTC)', 'datetime'), ('Profile Load Time (UTC)', 'datetime'),
                                   ('Profile Unload Time (UTC)', 'datetime'), 'SID', 'Profile Path',
                                   'State (as stored)'))
        self.assertEqual([(r[3], r[5]) for r in rows], [('S-1-5-18', 0), (SID, 0), (SID, 772)])
        self.assertEqual(opened, [self.one, self.two])
        self.assertEqual(source, self.one + '\n' + self.two)
        self.assertEqual(logged, [])

    def test_a_hive_without_the_key_is_named_and_logged_and_an_unreadable_one_is_skipped(self):
        (_headers, rows, source), _opened, logged = self.run_artifact({self.one: ValueError('bad header'),
                                                                      self.two: _Hive({})})
        self.assertEqual((rows, source), ([], self.two))
        self.assertEqual(logged, [
            'User Profile List: could not read vol1/Windows/System32/config/SOFTWARE: bad header',
            'User Profile List: vol2/Windows/System32/config/software has no ProfileList key'])

    def test_without_python_registry_nothing_is_read(self):
        with mock.patch.object(profiles, 'Registry', None), mock.patch.object(profiles, 'logfunc') as log, \
                mock.patch.object(profiles, 'open_hive') as opened:
            _headers, rows, source = profiles.userProfileList.__wrapped__(_Context(self.paths))
        self.assertEqual((rows, source), ([], ''))
        opened.assert_not_called()
        self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
