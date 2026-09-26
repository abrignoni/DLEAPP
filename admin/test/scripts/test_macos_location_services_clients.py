"""Pin the entry rows of scripts/artifacts/macosLocationServicesClients.py."""
import pathlib
import sys
import unittest
from datetime import datetime, timezone

_EPOCH_2001 = datetime(2001, 1, 1, tzinfo=timezone.utc)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosLocationServicesClients as loc  # pylint: disable=wrong-import-position

HEADERS = ('Started', 'Stopped', 'Client', 'Bundle ID', 'Bundle Path', 'Executable', 'Authorized',
           'Registered', 'Whitelisted', 'System Service', 'Requirement', 'Other Keys')

_STARTED = datetime(2021, 2, 19, 19, 14, 43, 500000, tzinfo=timezone.utc)


class StoredTextTest(unittest.TestCase):
    def test_values(self):
        self.assertEqual(loc.stored_text(True), 'Yes')
        self.assertEqual(loc.stored_text(False), 'No')
        self.assertEqual(loc.stored_text(b'\x01\xab'), '01ab')
        self.assertEqual(loc.stored_text({'b': b'\x02', 'a': [1]}), '{"a": [1], "b": "02"}')
        self.assertEqual(loc.stored_text(None), '')
        self.assertEqual(loc.stored_text(3000.0), '3000.0')


class ClientRowTest(unittest.TestCase):
    def test_a_big_sur_style_entry(self):
        row = dict(zip(HEADERS, loc.client_row('com.apple.Maps', {
            'BundleId': 'com.apple.Maps', 'Authorized': True, 'Whitelisted': False,
            'Registered': '/System/Applications/Maps.app/Contents/MacOS/Maps',
            'LocationTimeStarted': (_STARTED - _EPOCH_2001).total_seconds(),
            'LocationDesiredAccuracy': 3000.0,
            'BatchEnabled': False})))
        self.assertEqual(row['Started'], _STARTED)
        self.assertEqual(row['Stopped'], '')
        self.assertEqual((row['Client'], row['Bundle ID'], row['Authorized'], row['Whitelisted']),
                         ('com.apple.Maps', 'com.apple.Maps', 'Yes', 'No'))
        self.assertEqual(row['Registered'], '/System/Applications/Maps.app/Contents/MacOS/Maps')
        self.assertEqual(row['Other Keys'], 'LocationDesiredAccuracy: 3000.0 | BatchEnabled: No')

    def test_a_newer_entry_keeps_unread_keys(self):
        row = dict(zip(HEADERS, loc.client_row('root:p/System/Library/X.bundle:', {
            'BundlePath': '/System/Library/X.bundle', 'isSystemService': True,
            'ClientStorageToken': b'\x00\xff', 'SubIdentities': ['a']})))
        self.assertEqual((row['Started'], row['Authorized'], row['System Service']), ('', '', 'Yes'))
        self.assertEqual(row['Other Keys'], 'ClientStorageToken: 00ff | SubIdentities: ["a"]')


if __name__ == '__main__':
    unittest.main()
