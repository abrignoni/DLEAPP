"""Pin the mapped network drive readers in scripts/artifacts/windowsMappedDrives.py.

The hive is stood in for by small objects that answer the python-registry calls the readers make; the expected rows
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

from scripts.artifacts import windowsMappedDrives as drives  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

# The fixtures put each hive under a vol<N> folder; match it as a whole path segment, since the
# temporary folder above it can contain the letters vol.
_VOLUME = re.compile(r'[\\/]vol(?=\d)')

UTC = datetime.timezone.utc
MAPPED = datetime.datetime(2021, 3, 4, 5, 6, 7, 800)
RESTORED = datetime.datetime(2021, 3, 4, 5, 13, 30, 900)
OTHER = datetime.datetime(2022, 1, 2, 3, 4, 5, 6)
MRU = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Map Network Drive MRU'
DRIVE_HEADERS = (('Key Last Written (UTC)', 'datetime'), ('Network Key Last Written (UTC)', 'datetime'), 'User',
                 'Drive', 'Remote Path', 'User Name', 'Provider Name', 'Provider Type', 'Connection Type',
                 'Defer Flags', 'Connect Flags')
MRU_HEADERS = (('Key Last Written (UTC)', 'datetime'), 'User', 'Order', 'Value', 'Share')


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=(), subkeys=(), written=MAPPED):
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
        return 'vol' + _VOLUME.split(path, maxsplit=1)[1]


def _z_drive():
    return _Key('Z', [('RemotePath', '\\\\fileserver\\projects'), ('UserName', 0),
                      ('ProviderName', 'Microsoft Windows Network'), ('ProviderType', 131072),
                      ('ConnectionType', 1), ('ConnectFlags', 0), ('DeferFlags', 4),
                      ('UseOptions', b'DefC\x00\x01')], written=RESTORED)


def _y_drive():
    # a second drive: a stored account name, value names in another case, and values the key lacks
    return _Key('Y', [('remotepath', '\\\\nas\\media'), ('USERNAME', 'LAB\\alice'), ('Extra', 'ignored')],
                written=OTHER)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class DriveRowsTest(unittest.TestCase):
    def test_one_row_per_drive_key_with_both_times_and_the_values_as_stored(self):
        network = _Key('Network', subkeys=[_z_drive(), _y_drive()], written=MAPPED)
        self.assertEqual(drives.drive_rows(network, 'alice'), [
            (RESTORED.replace(tzinfo=UTC), MAPPED.replace(tzinfo=UTC), 'alice', 'Z', '\\\\fileserver\\projects', 0,
             'Microsoft Windows Network', 131072, 1, 4, 0),
            (OTHER.replace(tzinfo=UTC), MAPPED.replace(tzinfo=UTC), 'alice', 'Y', '\\\\nas\\media', 'LAB\\alice',
             '', '', '', '', ''),
        ])

    def test_binary_data_is_left_out_even_under_a_reported_name(self):
        network = _Key('Network', subkeys=[_Key('X', [('RemotePath', b'\\\\a\\b'), ('DeferFlags', 4)])])
        self.assertEqual(drives.drive_rows(network, 'bob')[0][4:], ('', '', '', '', '', 4, ''))

    def test_a_network_key_with_no_subkeys_gives_no_rows(self):
        self.assertEqual(drives.drive_rows(_Key('Network', values=[('RemotePath', 'x')]), 'alice'), [])


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class MruRowsTest(unittest.TestCase):
    def test_rows_follow_mrulist_and_an_unlisted_value_follows_with_a_blank_order(self):
        key = _Key(values=[('a', '\\\\old\\share'), ('MRUList', 'cba'), ('b', '\\\\mid\\share'),
                           ('c', '\\\\new\\share'), ('d', '\\\\unlisted\\share')])
        rows, missing = drives.mru_rows(key, 'alice')
        written = MAPPED.replace(tzinfo=UTC)
        self.assertEqual(rows, [(written, 'alice', 1, 'c', '\\\\new\\share'), (written, 'alice', 2, 'b', '\\\\mid\\share'),
                                (written, 'alice', 3, 'a', '\\\\old\\share'),
                                (written, 'alice', '', 'd', '\\\\unlisted\\share')])
        self.assertEqual(missing, [])

    def test_a_listed_name_the_key_does_not_hold_is_returned_and_keeps_its_position(self):
        rows, missing = drives.mru_rows(_Key(values=[('mrulist', 'xa'), ('a', '\\\\s\\one')]), 'bob')
        self.assertEqual([row[2:] for row in rows], [(2, 'a', '\\\\s\\one')])
        self.assertEqual(missing, ['x'])

    def test_without_mrulist_every_order_is_blank_and_data_that_is_not_text_is_left_out(self):
        rows, missing = drives.mru_rows(_Key(values=[('a', '\\\\s\\one'), ('b', b'\\\\s\\two'), ('c', 7)]), 'bob')
        self.assertEqual([row[2:] for row in rows], [('', 'a', '\\\\s\\one')])
        self.assertEqual(missing, [])

    def test_an_mrulist_that_is_not_text_is_read_as_no_order(self):
        rows, missing = drives.mru_rows(_Key(values=[('MRUList', b'a\x00'), ('a', '\\\\s\\one')]), 'bob')
        self.assertEqual([row[2:] for row in rows], [('', 'a', '\\\\s\\one')])
        self.assertEqual(missing, [])

    def test_a_value_name_keeps_its_stored_case_and_is_matched_as_stored(self):
        rows, missing = drives.mru_rows(_Key(values=[('MRUList', 'Ba'), ('B', '\\\\s\\one'), ('A', '\\\\s\\two')]), 'bob')
        self.assertEqual([row[2:] for row in rows], [(1, 'B', '\\\\s\\one'), ('', 'A', '\\\\s\\two')])
        self.assertEqual(missing, ['a'])

    def test_a_name_mrulist_repeats_is_used_once_and_is_not_counted_as_missing(self):
        rows, missing = drives.mru_rows(_Key(values=[('MRUList', 'abaxx'), ('a', '\\\\s\\one'), ('b', '\\\\s\\two')]), 'bob')
        self.assertEqual([row[2:] for row in rows], [(1, 'a', '\\\\s\\one'), (2, 'b', '\\\\s\\two')])
        self.assertEqual(missing, ['x'])


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

    def run_artifact(self, function, hives):
        def opener(path, _context=None):
            hive = hives[path]
            if isinstance(hive, Exception):
                raise hive
            return hive
        logged = []
        with mock.patch.object(drives, 'open_hive', side_effect=opener) as opened, \
                mock.patch.object(drives, 'logfunc', side_effect=logged.append):
            result = function.__wrapped__(_Context(self.paths))
        return result, [c.args[0] for c in opened.call_args_list], logged

    def test_drives_come_from_each_user_hive_under_the_user_folder_name(self):
        hives = {self.alice: _Hive({'Network': _Key('Network', subkeys=[_z_drive()]), MRU: _Key(values=[('a', 'x')])}),
                 self.bob: _Hive({'Network': _Key('Network', subkeys=[_y_drive()], written=OTHER)}),
                 self.carol: _Hive({})}
        (headers, rows, source), opened, logged = self.run_artifact(drives.mappedNetworkDrives, hives)
        self.assertEqual(headers, DRIVE_HEADERS)
        self.assertEqual([row[:4] for row in rows],
                         [(RESTORED.replace(tzinfo=UTC), MAPPED.replace(tzinfo=UTC), 'alice', 'Z'),
                          (OTHER.replace(tzinfo=UTC), OTHER.replace(tzinfo=UTC), 'bob', 'Y')])
        self.assertEqual(opened, [self.alice, self.bob, self.carol])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol]))
        self.assertEqual(logged, [])

    def test_the_mru_comes_from_its_own_key_and_a_missing_name_is_logged_by_the_path_in_the_extraction(self):
        hives = {self.alice: _Hive({'Network': _Key('Network', subkeys=[_z_drive()]),
                                    MRU: _Key(values=[('MRUList', 'cba'), ('a', '\\\\s\\one')], written=OTHER)}),
                 self.bob: _Hive({MRU: _Key(values=[('MRUList', 'a'), ('a', '\\\\s\\two')])}), self.carol: _Hive({})}
        (headers, rows, source), _opened, logged = self.run_artifact(drives.mapNetworkDriveMru, hives)
        self.assertEqual(headers, MRU_HEADERS)
        self.assertEqual(rows, [(OTHER.replace(tzinfo=UTC), 'alice', 3, 'a', '\\\\s\\one'),
                                (MAPPED.replace(tzinfo=UTC), 'bob', 1, 'a', '\\\\s\\two')])
        self.assertEqual(source, '\n'.join([self.alice, self.bob, self.carol]))
        self.assertEqual(logged, ['Map Network Drive MRU: MRUList of vol1/Users/alice/NTUSER.DAT lists 2 value name(s) '
                                  'the key does not hold'])

    def test_an_unreadable_hive_is_logged_by_its_path_in_the_extraction_and_skipped(self):
        hives = {self.alice: ValueError('bad header'), self.bob: _Hive({'Network': _Key('Network', subkeys=[_y_drive()])}),
                 self.carol: _Hive({})}
        (_headers, rows, source), _opened, logged = self.run_artifact(drives.mappedNetworkDrives, hives)
        self.assertEqual([row[2:4] for row in rows], [('bob', 'Y')])
        self.assertEqual(source, self.bob + '\n' + self.carol)
        self.assertEqual(logged, ['Mapped Network Drives: could not read vol1/Users/alice/NTUSER.DAT: bad header'])
        (_headers, rows, source), _opened, logged = self.run_artifact(drives.mapNetworkDriveMru, hives)
        self.assertEqual((rows, source), ([], self.bob + '\n' + self.carol))
        self.assertEqual(logged, ['Map Network Drive MRU: could not read vol1/Users/alice/NTUSER.DAT: bad header'])

    def test_without_python_registry_nothing_is_read(self):
        for function in (drives.mappedNetworkDrives, drives.mapNetworkDriveMru):
            with mock.patch.object(drives, 'Registry', None), mock.patch.object(drives, 'logfunc') as log, \
                    mock.patch.object(drives, 'open_hive') as opened:
                _headers, rows, source = function.__wrapped__(_Context(self.paths))
            self.assertEqual((rows, source), ([], ''))
            opened.assert_not_called()
            self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
