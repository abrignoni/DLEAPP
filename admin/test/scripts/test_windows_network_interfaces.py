"""Pin the lease columns of windowsNetworkInterfaces in scripts/artifacts/windowsSystemInfo.py.

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

from scripts.artifacts import windowsSystemInfo as system_info  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
WRITTEN = datetime.datetime(2020, 9, 18, 21, 40, 22)
OBTAINED = 1600400000
TERMINATES = 1600401800
INTERFACES = 'ControlSet001\\Services\\Tcpip\\Parameters\\Interfaces'


class _Value:
    def __init__(self, data):
        self._data = data

    def value(self):
        return self._data


class _Key:
    def __init__(self, name='', values=None, subkeys=()):
        self._name = name
        self._values = values or {}
        self._subkeys = list(subkeys)

    def name(self):
        return self._name

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(self._values[name])

    def subkeys(self):
        return self._subkeys

    @staticmethod
    def timestamp():
        return WRITTEN


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


class _Context:
    @staticmethod
    def get_relative_path(path):
        return 'vol' + path.split('vol', 1)[1]


def lease(**values):
    return dict(values, LeaseObtainedTime=OBTAINED, LeaseTerminatesTime=TERMINATES, Lease=1800)


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class LeaseColumnTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        path = pathlib.Path(folder.name, 'vol1/Windows/System32/config/SYSTEM')
        path.parent.mkdir(parents=True)
        path.write_bytes(b'')
        self.path = str(path)

    def rows(self, *interfaces):
        hive = _Hive({INTERFACES: _Key(subkeys=interfaces)})
        with mock.patch.object(system_info, 'found_hives', return_value=[self.path]), \
                mock.patch.object(system_info, 'open_hive', return_value=hive), \
                mock.patch.object(system_info, 'logfunc') as log:
            headers, rows, source = system_info.windowsNetworkInterfaces.__wrapped__(_Context())
        self.assertEqual(headers[:2], (('Lease Obtained (UTC)', 'datetime'), ('Lease Terminates (UTC)', 'datetime')))
        self.assertEqual(source, self.path)
        log.assert_not_called()
        return {row[11]: row for row in rows}

    def test_a_static_interface_whose_key_holds_lease_values_reports_them(self):
        row = self.rows(_Key('{static}', lease(EnableDHCP=0, IPAddress=['10.0.0.5', ''])))['{static}']
        self.assertEqual(row[:5], (datetime.datetime(2020, 9, 18, 3, 33, 20, tzinfo=UTC),
                                   datetime.datetime(2020, 9, 18, 4, 3, 20, tzinfo=UTC), '', 'No', '10.0.0.5'))

    def test_a_static_interface_without_lease_values_has_blank_lease_columns(self):
        row = self.rows(_Key('{static}', {'EnableDHCP': 0, 'IPAddress': ['10.0.0.5']}))['{static}']
        self.assertEqual(row[:5], ('', '', '', 'No', '10.0.0.5'))

    def test_a_dhcp_interface_reports_its_lease_and_dhcp_address(self):
        row = self.rows(_Key('{dhcp}', lease(EnableDHCP=1, DhcpIPAddress='192.168.1.20')))['{dhcp}']
        self.assertEqual(row[:5], (datetime.datetime(2020, 9, 18, 3, 33, 20, tzinfo=UTC),
                                   datetime.datetime(2020, 9, 18, 4, 3, 20, tzinfo=UTC), '', 'Yes', '192.168.1.20'))

    def test_an_interface_with_no_address_is_not_reported(self):
        self.assertEqual(self.rows(_Key('{none}', lease(EnableDHCP=1)), _Key('{empty}')), {})


if __name__ == '__main__':
    unittest.main()
