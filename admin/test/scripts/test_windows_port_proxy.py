"""Pin the Port Proxy Rules artifact (scripts/artifacts/windowsPortProxy.py).

The registry is a stand-in for the key objects regfprobe returns, laid out as netsh wrote it on a
Windows 11 lab VM; the addresses are documentation ranges.
"""
import datetime
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsPortProxy as pp
# pylint: enable=wrong-import-position

STAMP = datetime.datetime(2026, 11, 16, 3, 32, 40, tzinfo=datetime.timezone.utc)


class Value:  # pylint: disable=too-few-public-methods
    def __init__(self, name, value):
        self._n, self._v = name, value

    def name(self):
        return self._n

    def value(self):
        return self._v


class Key:
    def __init__(self, name, subkeys=(), values=(), stamp=None):
        self._name, self._sub, self._values, self._stamp = name, list(subkeys), list(values), stamp

    def name(self):
        return self._name

    def subkeys(self):
        return self._sub

    def values(self):
        return self._values

    def timestamp(self):
        return self._stamp

    def value(self, name):
        for value in self._values:
            if value.name() == name:
                return value
        raise pp.Registry.RegistryValueNotFoundException(name)


class Reg:
    def __init__(self, keys, root):
        self.keys, self._root = keys, root

    def root(self):
        return self._root

    def open(self, path):
        if path not in self.keys:
            raise pp.Registry.RegistryKeyNotFoundException(path)
        return self.keys[path]


def build():
    tcp4 = Key('tcp', values=[Value('127.0.0.1/18080', '192.0.2.10/80'), Value('*/18081', '2001:db8::1/8081')],
               stamp=STAMP)
    proxy1 = Key('PortProxy', [Key('v4tov4', [tcp4]), Key('v4tov6', [])])
    proxy2 = Key('PortProxy', [Key('v6tov6', [Key('tcp', values=[Value('::/9', 'noslash')], stamp=STAMP)])])
    select = Key('Select', values=[Value('Current', 1)])
    root = Key('ROOT', [Key('ControlSet001'), Key('ControlSet002'), select, Key('Software')])
    return Reg({'ControlSet001\\Services\\PortProxy': proxy1, 'ControlSet002\\Services\\PortProxy': proxy2,
                'Select': select}, root)


class Rows(unittest.TestCase):
    def test_rows(self):
        self.assertEqual(pp.portproxy_rows(build()), [
            (STAMP, 'v4tov4', 'tcp', '127.0.0.1', '18080', '192.0.2.10', '80', 'ControlSet001', 'Yes'),
            (STAMP, 'v4tov4', 'tcp', '*', '18081', '2001:db8::1', '8081', 'ControlSet001', 'Yes'),
            (STAMP, 'v6tov6', 'tcp', '::', '9', 'noslash', '', 'ControlSet002', 'No')])

    def test_split_and_text(self):
        self.assertEqual(pp._split('a:b::1/443'), ('a:b::1', '443'))  # pylint: disable=protected-access
        self.assertEqual(pp._text(b'\x01'), '01')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
