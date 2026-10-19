"""Pin how USB Storage Devices (scripts/artifacts/windowsUsbDevices.py) reads its dates.

Device properties are built in both layouts seen on real hives: Windows 8 and later keep the
data in the property sub-key's default value, with the property type in the value type;
Windows 7 names the sub-key with eight hex digits and keeps a sub-key 00000000 holding Type
and Data values.
"""
import datetime
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsUsbDevices as ud
from scripts.windows_registry import Registry
# pylint: enable=wrong-import-position

DATES = '{83da6326-97a6-4088-9453-a1923f573b29}'
WHEN = datetime.datetime(2015, 3, 23, 18, 31, 11, 356000, tzinfo=datetime.timezone.utc)


def filetime(when):
    delta = when - datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)
    return struct.pack('<Q', (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10)


class _Value:
    def __init__(self, name, data, kind=3):
        self._name, self._data, self._kind = name, data, kind

    def name(self):
        return self._name

    def raw_data(self):
        return self._data

    def value_type(self):
        return self._kind


class _Key:
    def __init__(self, name, values=(), subkeys=()):
        self._name, self._values, self._subkeys = name, list(values), list(subkeys)

    def name(self):
        return self._name

    def values(self):
        return self._values

    def value(self, name):
        for value in self._values:
            if value.name() == name:
                return value
        raise Registry.RegistryValueNotFoundException(name)

    def subkeys(self):
        return self._subkeys

    def subkey(self, name):
        for key in self._subkeys:
            if key.name() == name:
                return key
        raise Registry.RegistryKeyNotFoundException(name)


def instance(*nodes):
    return _Key('SERIAL', subkeys=[_Key('Properties', subkeys=[_Key(DATES, subkeys=list(nodes))])])


def new_layout(name, data, kind=0x10):
    return _Key(name, values=[_Value('(default)', data, kind)])


def win7_layout(name, data, kind=0x10):
    return _Key(name, subkeys=[_Key('00000000', values=[_Value('Type', struct.pack('<I', kind)),
                                                        _Value('Data', data)])])


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class Dates(unittest.TestCase):
    def test_windows_8_and_later_layout(self):
        self.assertEqual(ud._property_filetime(instance(new_layout('0065', filetime(WHEN))), '0065'),  # pylint: disable=protected-access
                         WHEN)

    def test_windows_7_layout(self):
        self.assertEqual(ud._property_filetime(instance(win7_layout('00000065', filetime(WHEN))), '0065'),  # pylint: disable=protected-access
                         WHEN)

    def test_another_type_or_no_property_is_blank(self):
        for node in (new_layout('0065', filetime(WHEN), 0x12), win7_layout('00000065', filetime(WHEN), 0x12),
                     new_layout('0066', filetime(WHEN))):
            self.assertEqual(ud._property_filetime(instance(node), '0065'), '')  # pylint: disable=protected-access
        self.assertEqual(ud._property_filetime(_Key('SERIAL'), '0065'), '')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
