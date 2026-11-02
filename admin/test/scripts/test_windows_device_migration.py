"""Pin the Device Migration artifact (scripts/artifacts/windowsUpgradeHistory.py).

The hive is stood in for by small objects that answer the python-registry calls the reader makes. The value names and
types are those of the DeviceMigration keys on pc_mus_001_win11; the device names and values are made up.
"""
import datetime
import pathlib
import struct
import sys
import unittest
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsUpgradeHistory as uh
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
WRITTEN = datetime.datetime(2022, 11, 23, 0, 28, 20)
# 2022-11-20 12:00:00 UTC as a FILETIME
GONE_AT = datetime.datetime(2022, 11, 20, 12, 0, tzinfo=UTC)
FILETIME = struct.pack('<Q', int((GONE_AT - datetime.datetime(1601, 1, 1, tzinfo=UTC)).total_seconds()) * 10_000_000)
SETUP = 'Setup\\Upgrade\\PnP\\CurrentControlSet\\Control\\DeviceMigration\\Devices'


class _Value:
    def __init__(self, name, data):
        self._name, self._data = name, data

    def name(self):
        return self._name

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=None, subkeys=(), written=WRITTEN):
        self._name, self._values, self._subkeys, self._written = name, values or {}, list(subkeys), written

    def name(self):
        return self._name

    def values(self):
        return [_Value(name, data) for name, data in self._values.items()]

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(name, self._values[name])

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

    def root(self):
        names = sorted({path.split('\\')[0] for path in self._keys})
        return _Key(subkeys=[_Key(name) for name in names])


def _tree(*instances):
    """A Devices key holding instances given as (enumerator, device, instance, values)."""
    enumerators = {}
    for enumerator, device, instance, values in instances:
        enumerators.setdefault(enumerator, {}).setdefault(device, []).append(
            _Key(instance, values, subkeys=[_Key('Properties', {'x': 1})]))
    return _Key(subkeys=[_Key(e, subkeys=[_Key(d, subkeys=i) for d, i in devices.items()])
                         for e, devices in enumerators.items()])


GONE = {'Present': 0, 'LastPresentDate': FILETIME, 'BusDeviceDesc': 'made-up monitor', 'MatchingDeviceId': 'monitor\\x',
        'ClassGuid': '{4d36e96e-e325-11ce-bfc1-08002be10318}', 'DriverInfName': 'monitor.inf',
        'Capabilities': 148, 'HardwareIds': ['MONITOR\\X']}
HERE = {'Present': 1, 'MatchingDeviceId': 'pci\\ven_8086', 'ClassGuid': '{x}', 'DriverInfName': 'machine.inf',
        'LocationInfo': 'PCI bus 0, device 2, function 0'}


def _hive(enum=True):
    keys = {
        SETUP: _tree(('DISPLAY', 'ABC0001', '4&1&0&UID0', GONE), ('PCI', 'VEN_8086&DEV_1234', '3&2&0&10', HERE)),
        'ControlSet001\\Control\\DeviceMigration\\Devices': _tree(('DISPLAY', 'ABC0001', '4&1&0&UID0', GONE)),
        'ControlSet002\\Control\\DeviceMigration\\Devices': _tree(('USB', 'VID_0000&PID_0000', 'made-up', {})),
        'Select': _Key(values={'Current': 2}),
    }
    if enum:
        keys['ControlSet002\\Enum'] = _tree(('pci', 'ven_8086&dev_1234', '3&2&0&10', {}))
        keys['ControlSet001\\Enum'] = _tree(('DISPLAY', 'ABC0001', '4&1&0&UID0', {}))
    return _Hive(keys)


class DeviceMigrationRowsTest(unittest.TestCase):
    def test_every_copy_gives_its_own_rows_and_enum_is_the_current_control_sets(self):
        problems = Counter()
        rows = uh.device_migration_rows(_hive(), problems)
        written = WRITTEN.replace(tzinfo=UTC)
        self.assertEqual(rows, [
            (GONE_AT, written, 0, 'DISPLAY\\ABC0001\\4&1&0&UID0', 'no', 'made-up monitor', 'monitor\\x',
             '{4d36e96e-e325-11ce-bfc1-08002be10318}', 'monitor.inf', '', SETUP + '\\DISPLAY\\ABC0001\\4&1&0&UID0'),
            ('', written, 1, 'PCI\\VEN_8086&DEV_1234\\3&2&0&10', 'yes', '', 'pci\\ven_8086', '{x}', 'machine.inf',
             'PCI bus 0, device 2, function 0', SETUP + '\\PCI\\VEN_8086&DEV_1234\\3&2&0&10'),
            (GONE_AT, written, 0, 'DISPLAY\\ABC0001\\4&1&0&UID0', 'no', 'made-up monitor', 'monitor\\x',
             '{4d36e96e-e325-11ce-bfc1-08002be10318}', 'monitor.inf', '',
             'ControlSet001\\Control\\DeviceMigration\\Devices\\DISPLAY\\ABC0001\\4&1&0&UID0'),
            ('', written, '', 'USB\\VID_0000&PID_0000\\made-up', 'no', '', '', '', '', '',
             'ControlSet002\\Control\\DeviceMigration\\Devices\\USB\\VID_0000&PID_0000\\made-up'),
        ])
        self.assertEqual(problems, Counter())

    def test_a_last_present_date_of_another_size_is_blank_and_counted(self):
        values = dict(GONE, LastPresentDate=FILETIME + b'\x00')
        hive = _Hive({SETUP: _tree(('DISPLAY', 'A', '1', values)), 'Select': _Key(values={'Current': 1})})
        problems = Counter()
        rows = uh.device_migration_rows(hive, problems)
        self.assertEqual((len(rows), rows[0][0], rows[0][2]), (1, '', 0))
        self.assertEqual(problems, {'LastPresentDate values that are not eight bytes, left blank': 1})

    def test_without_an_enum_key_every_instance_is_no(self):
        rows = uh.device_migration_rows(_hive(enum=False), Counter())
        self.assertEqual([row[4] for row in rows], ['no'] * 4)

    def test_a_hive_without_device_migration_gives_no_rows(self):
        hive = _Hive({'Select': _Key(values={'Current': 1}), 'ControlSet001\\Enum': _tree(('PCI', 'A', '1', {}))})
        self.assertEqual(uh.device_migration_rows(hive, Counter()), [])


if __name__ == '__main__':
    unittest.main()
