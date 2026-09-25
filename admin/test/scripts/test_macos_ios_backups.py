"""Pin the iOS device backup readers in scripts/artifacts/macosIosBackups.py.

Every value below is authored for the test; none comes from a real device.
"""
import pathlib
import plistlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import macosIosBackups  # pylint: disable=wrong-import-position

UDID = '00000000-0000TESTDEVICE'
BACKUP_TIME = datetime(2026, 1, 2, 3, 4, 5)


def _metadata(name, purchased='2025-06-07T08:09:10Z'):
    return plistlib.dumps({
        'itemName': name, 'bundleShortVersionString': '1.2', 'bundleVersion': '12',
        'artistName': 'Example Seller', 'genre': 'Utilities', 'itemId': 42,
        'storefrontCountryCode': 'us', 'sourceApp': 'com.apple.AppStore',
        'is-purchased-redownload': True, 'is-auto-download': False, 'isFactoryInstall': False,
        'com.apple.iTunesStore.downloadInfo': {
            'purchaseDate': purchased,
            'accountInfo': {'AppleID': 'tester@example.invalid', 'DSPersonID': 1001,
                            'PurchaserID': 1001, 'DownloaderID': 0, 'FamilyID': 0,
                            'AltDSID': 'alt-test'}}})


class Context:
    """The two calls the artifacts make, over a temporary tree."""

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class BackupReadersTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target in (macosIosBackups, macos_plists):
            patcher = patch.object(target, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.folder = self.root/'Users'/'tester'/'Library'/'Application Support'/'MobileSync'/'Backup'/UDID
        self.folder.mkdir(parents=True)
        self.info = self.folder/'Info.plist'
        self.info.write_bytes(plistlib.dumps({
            'Device Name': 'Test Phone', 'Display Name': 'Test Phone', 'Product Type': 'iPhone0,0',
            'Product Name': 'iPhone', 'Product Version': '1.0', 'Build Version': '1A1',
            'Serial Number': 'TESTSERIAL', 'Unique Identifier': UDID, 'Target Identifier': UDID,
            'IMEI': '000000000000000', 'Phone Number': '+0 000 0000000',
            'Last Backup Date': BACKUP_TIME, 'macOS Version': '99.0',
            'Installed Applications': ['com.example.alpha', 'com.example.only-listed'],
            'Applications': {'com.example.alpha': {'iTunesMetadata': _metadata('Alpha')},
                             'com.example.broken': {'iTunesMetadata': b'not a plist'}}}))
        (self.folder/'Manifest.plist').write_bytes(plistlib.dumps({
            'IsEncrypted': True, 'WasPasscodeSet': False, 'Date': BACKUP_TIME}))
        self.deeper = self.folder/'Snapshot'/'Info.plist'
        self.deeper.parent.mkdir()
        self.deeper.write_bytes(self.info.read_bytes())

    def run_artifact(self, func, files):
        return func.__wrapped__(Context(self.root, files))

    def test_one_row_per_backup_folder(self):
        files = [self.info, self.folder/'Manifest.plist', self.deeper]
        headers, rows, source = self.run_artifact(macosIosBackups.macosIosBackups, files)
        self.assertEqual(len(rows), 1)
        row = dict(zip([h[0] if isinstance(h, tuple) else h for h in headers], rows[0]))
        self.assertEqual(row['Last Backup Date (UTC)'],
                         datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
        self.assertEqual(row['Status Date (UTC)'], '')
        self.assertEqual((row['Device Name'], row['Serial Number'], row['Unique Identifier']),
                         ('Test Phone', 'TESTSERIAL', UDID))
        self.assertEqual((row['Encrypted'], row['Passcode Set'], row['Full Backup']),
                         ('Yes', 'No', ''))
        self.assertEqual(row['Applications Listed'], 3)
        self.assertEqual(row['User'], 'tester')
        self.assertTrue(row['Backup Folder'].endswith('MobileSync/Backup/' + UDID))
        self.assertEqual(source.split('\n'), [str(self.info), str(self.folder/'Manifest.plist')])
        self.assertIn('iOS Device Backups: no readable Status.plist in '
                      + row['Backup Folder'], self.logged)
        self.assertTrue(any('deeper inside a backup folder' in m for m in self.logged))

    def test_one_row_per_listed_or_described_app(self):
        _headers, rows, _source = self.run_artifact(macosIosBackups.macosIosBackupApps,
                                                    [self.info, self.deeper])
        by_id = {r[2]: r for r in rows}
        self.assertEqual(sorted(by_id), ['com.example.alpha', 'com.example.broken',
                                         'com.example.only-listed'])
        alpha = by_id['com.example.alpha']
        self.assertEqual(alpha[0], datetime(2025, 6, 7, 8, 9, 10, tzinfo=timezone.utc))
        self.assertEqual(alpha[1], 'Alpha')
        self.assertEqual(alpha[7:13], ('tester@example.invalid', '1001', '1001', '0', '0', 'alt-test'))
        self.assertEqual(alpha[13:16], ('Yes', 'No', 'No'))
        self.assertEqual(alpha[19], 'Installed Applications, Applications')
        self.assertEqual(by_id['com.example.only-listed'][19], 'Installed Applications')
        self.assertEqual(by_id['com.example.only-listed'][:2], ('', ''))
        self.assertEqual(by_id['com.example.broken'][19], 'Applications')
        self.assertIn('iOS Device Backup Applications: iTunesMetadata not read for '
                      'com.example.broken', self.logged)

    def test_unreadable_purchase_date_is_blank_and_logged(self):
        plist = plistlib.loads(self.info.read_bytes())
        plist['Applications']['com.example.alpha']['iTunesMetadata'] = _metadata('Alpha', 'soon')
        self.info.write_bytes(plistlib.dumps(plist))
        _headers, rows, _source = self.run_artifact(macosIosBackups.macosIosBackupApps, [self.info])
        self.assertEqual({r[2]: r[0] for r in rows}['com.example.alpha'], '')
        self.assertIn('iOS Device Backup Applications: purchaseDate not read for '
                      'com.example.alpha', self.logged)

    def test_home_folder_acquisition_has_blank_user(self):
        home = self.root/'Users'/'tester'
        context = Context(home, [self.info])
        _headers, rows, _source = macosIosBackups.macosIosBackups.__wrapped__(context)
        self.assertEqual(rows[0][-1], '')

    def test_evidence_is_unchanged(self):
        before = self.info.read_bytes()
        self.run_artifact(macosIosBackups.macosIosBackups, [self.info])
        self.run_artifact(macosIosBackups.macosIosBackupApps, [self.info])
        self.assertEqual(before, self.info.read_bytes())


if __name__ == '__main__':
    unittest.main()
