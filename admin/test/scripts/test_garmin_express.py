"""Pin the Garmin Express readers in scripts/artifacts/garminExpress.py.

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
from scripts.artifacts import garminExpress  # pylint: disable=wrong-import-position

DEVICE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Device xmlns="http://www.garmin.com/xmlschemas/GarminDevice/v2">
  <Model><PartNumber>000-T0000-00</PartNumber><SoftwareVersion>1234</SoftwareVersion>
    <Description>Test Watch 1</Description></Model>
  <Id>1111111111</Id>
</Device>'''


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class GarminExpressTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target in (garminExpress, macos_plists):
            patcher = patch.object(target, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)
        express = self.root/'Users'/'tester'/'Library'/'Application Support'/'Garmin'/'Express'
        self.device = express/'RegisteredDevices'/'folder-name'
        self.device.mkdir(parents=True)
        self.files = [self.device/'GarminDevice.xml', self.device/'AdditionalInfo.plist',
                      self.device/'CompletedUploadsV2_FIT_TYPE_4.plist',
                      self.device/'CompletedUploadsV2_FIT_TYPE_32.plist',
                      self.device/'CompletedUploadsV2_ErrorShutdownReports.plist',
                      express/'AccountDictionaryDatastore.plist']
        self.files[0].write_text(DEVICE_XML, encoding='utf-8')
        self.files[1].write_bytes(plistlib.dumps({
            'last_connect_sync': 1767225600.5, 'device_serial_number': 'TESTSERIAL',
            'friendly_name': 'Test Watch', 'registration_email': 'tester@example.invalid',
            'auto_backup': True, 'last_update_check_firmware': datetime(2026, 1, 1, 0, 0, 1)}))
        self.files[2].write_bytes(plistlib.dumps(['A0000001.FIT', 'A0000002.FIT']))
        self.files[3].write_bytes(plistlib.dumps([]))
        self.files[4].write_bytes(plistlib.dumps(['REPORT.TXT']))
        self.files[5].write_bytes(plistlib.dumps({'999': ['1111111111'], '888': ['2222222222']}))

    def run_artifact(self, func, files=None):
        return func.__wrapped__(Context(self.root, self.files if files is None else files))

    def test_device_row(self):
        headers, rows, _source = self.run_artifact(garminExpress.garminExpressDevices)
        self.assertEqual(len(rows), 1)
        row = dict(zip([h[0] if isinstance(h, tuple) else h for h in headers], rows[0]))
        self.assertEqual(row['Last Connect Sync (UTC)'],
                         datetime(2026, 1, 1, 0, 0, 0, 500000, tzinfo=timezone.utc))
        self.assertEqual(row['Last Firmware Check (UTC)'],
                         datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc))
        self.assertEqual((row['Model'], row['Part Number'], row['Software Version'], row['Unit ID']),
                         ('Test Watch 1', '000-T0000-00', '1234', '1111111111'))
        self.assertEqual((row['Serial Number'], row['Auto Backup'], row['Account Keys']),
                         ('TESTSERIAL', 'Yes', '999'))
        self.assertEqual((row['Uploads Recorded'], row['User']), (3, 'tester'))

    def test_upload_rows_name_their_list_and_fit_type(self):
        _headers, rows, _source = self.run_artifact(garminExpress.garminExpressUploads)
        self.assertEqual([r[:4] for r in rows], [
            ('REPORT.TXT', 'ErrorShutdownReports', '', ''),
            ('A0000001.FIT', 'FIT_TYPE_4', '4', 'activity'),
            ('A0000002.FIT', 'FIT_TYPE_4', '4', 'activity')])
        self.assertEqual(rows[1][4:], ('Test Watch 1', '1111111111', 'TESTSERIAL', 'tester'))

    def test_unit_id_falls_back_to_folder_and_bad_xml_is_logged(self):
        self.files[0].write_text('<Device', encoding='utf-8')
        _headers, rows, _source = self.run_artifact(garminExpress.garminExpressDevices)
        self.assertEqual((rows[0][3], rows[0][6], rows[0][13]), ('', 'folder-name', ''))
        self.assertTrue(any('could not read GarminDevice.xml' in m for m in self.logged))

    def test_files_below_a_device_folder_are_not_read(self):
        deeper = self.device/'PendingSyncUploads'/'CompletedUploadsV2_FIT_TYPE_4.plist'
        deeper.parent.mkdir()
        deeper.write_bytes(plistlib.dumps(['B0000001.FIT']))
        _headers, rows, _source = self.run_artifact(garminExpress.garminExpressUploads,
                                                    self.files + [deeper])
        self.assertNotIn('B0000001.FIT', [r[0] for r in rows])

    def test_evidence_is_unchanged(self):
        before = [f.read_bytes() for f in self.files]
        self.run_artifact(garminExpress.garminExpressDevices)
        self.run_artifact(garminExpress.garminExpressUploads)
        self.assertEqual(before, [f.read_bytes() for f in self.files])


if __name__ == '__main__':
    unittest.main()
