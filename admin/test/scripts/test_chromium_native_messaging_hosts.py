"""Pin the Chromium native messaging artifacts (scripts/artifacts/chromiumNativeMessagingHosts.py).

Manifest values are made up in the documented layout. The registry test builds no hive: it feeds
the row builder a stand-in for the key objects regfprobe returns.
"""
import datetime
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import chromiumNativeMessagingHosts as nm
# pylint: enable=wrong-import-position


class FakeValue:  # pylint: disable=too-few-public-methods
    def __init__(self, name, value):
        self._n, self._v = name, value

    def name(self):
        return self._n

    def value(self):
        return self._v


class FakeKey:
    def __init__(self, name, subkeys=(), values=(), stamp=None):
        self._name, self._sub, self._values = name, list(subkeys), list(values)
        self._stamp = stamp

    def name(self):
        return self._name

    def subkeys(self):
        return self._sub

    def values(self):
        return self._values

    def timestamp(self):
        return self._stamp


class FakeReg:  # pylint: disable=too-few-public-methods
    def __init__(self, keys):
        self.keys = keys

    def open(self, path):
        if path not in self.keys:
            raise nm.Registry.RegistryKeyNotFoundException(path)
        return self.keys[path]


class Registry(unittest.TestCase):
    def test_rows_from_both_browsers_and_views(self):
        stamp = datetime.datetime(2026, 11, 16, 3, 30, 55, tzinfo=datetime.timezone.utc)
        host = FakeKey('com.lab.h', values=[FakeValue('(default)', 'C:\\x\\m.json')], stamp=stamp)
        other = FakeKey('com.lab.empty', values=[], stamp=stamp)
        reg = FakeReg({
            'Software\\Google\\Chrome\\NativeMessagingHosts': FakeKey('n', [host, other]),
            'Software\\Wow6432Node\\Chromium\\NativeMessagingHosts': FakeKey('n', [host])})
        rows = nm._registry_rows(reg, nm._NTUSER_ROOTS, 'User', 'a', 'rel')  # pylint: disable=protected-access
        self.assertEqual(rows, [
            (stamp, 'com.lab.h', 'C:\\x\\m.json', 'Software\\Google\\Chrome\\NativeMessagingHosts', 'User', 'a', 'rel'),
            (stamp, 'com.lab.empty', '', 'Software\\Google\\Chrome\\NativeMessagingHosts', 'User', 'a', 'rel'),
            (stamp, 'com.lab.h', 'C:\\x\\m.json', 'Software\\Wow6432Node\\Chromium\\NativeMessagingHosts', 'User', 'a',
             'rel')])

    def test_software_roots(self):
        reg = FakeReg({'WOW6432Node\\Google\\Chrome\\NativeMessagingHosts':
                       FakeKey('n', [FakeKey('h', values=[FakeValue('', 'p')])])})
        rows = nm._registry_rows(reg, nm._SOFTWARE_ROOTS, 'Machine', '', 'rel')  # pylint: disable=protected-access
        self.assertEqual([(r[1], r[2], r[3]) for r in rows], [('h', 'p', 'WOW6432Node\\Google\\Chrome\\NativeMessagingHosts')])


class Manifests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write(self, rel, data):
        path = os.path.join(self.folder.name, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(data if isinstance(data, str) else json.dumps(data))
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(nm, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'):
            result = nm.chromiumNativeMessagingManifests.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_manifest_rows(self):
        one = self.write('Users/a/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.x.json',
                         {'name': 'com.x', 'description': 'd', 'path': '/bin/x', 'type': 'stdio',
                          'allowed_origins': ['chrome-extension://a/', 'chrome-extension://b/']})
        two = self.write('etc/opt/chrome/native-messaging-hosts/com.y.json',
                         {'name': 'com.y', 'path': '/bin/y', 'allowed_extensions': ['y@example.invalid']})
        skip = self.write('Users/a/other/com.z.json', {'name': 'com.z'})
        (headers, rows, _), _ = self.run_artifact([one, two, skip])
        self.assertEqual(len(headers), 6)
        self.assertEqual(sorted(r[0] for r in rows), ['com.x', 'com.y'])
        by = {r[0]: r for r in rows}
        self.assertEqual(by['com.x'][4], 'chrome-extension://a/\nchrome-extension://b/')
        self.assertEqual(by['com.y'][4], '')
        self.assertEqual(nm._text(b'\x00\x01'), '0001')  # pylint: disable=protected-access

    def test_broken_manifest_is_logged(self):
        path = self.write('p/NativeMessagingHosts/a.json', '{"name": ')
        (_, rows, located), log = self.run_artifact([path])
        self.assertEqual((rows, located), ([], ''))
        self.assertTrue(any('could not be read' in m for m in log))

    def test_paths(self):
        import fnmatch  # pylint: disable=import-outside-toplevel
        paths = nm.__artifacts_v2__['chromiumNativeMessagingManifests']['paths']
        for good in ('root/Users/a/Library/Application Support/Google/Chrome/NativeMessagingHosts/a.json',
                     'root/etc/chromium/native-messaging-hosts/a.json'):
            self.assertTrue(any(fnmatch.fnmatchcase(good, p) for p in paths), good)


if __name__ == '__main__':
    unittest.main()
