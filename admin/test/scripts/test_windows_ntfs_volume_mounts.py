"""Pin the rows in scripts/artifacts/windowsNtfsVolumeMounts.py.

The records are built from XML of the shape python-evtx renders for the events (made-up values); the expected rows
are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsNtfsVolumeMounts as mounts  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Ntfs%4Operational.evtx'
TIME = datetime.datetime(2023, 1, 6, 3, 36, 3, 548039, tzinfo=datetime.timezone.utc)
V1 = [('VolumeCorrelationId', '{11111111-2222-3333-4444-555555555555}'), ('VolumeIdLength', '2'), ('VolumeId', 'D:'),
      ('VolumeLabelLength', '10'), ('VolumeLabel', 'New Volume'), ('DeviceNameLength', '23'),
      ('DeviceName', '\\Device\\HarddiskVolume9'), ('DeviceGuid', '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}'),
      ('VendorIdLength', '8'), ('VendorId', 'MAKER'), ('ProductIdLength', '4'), ('ProductId', 'M1 '),
      ('ProductRevisionLength', '4'), ('ProductRevision', 'R1'), ('DeviceSerialNumberLength', '8'),
      ('DeviceSerialNumber', 'SN000001'), ('BusType', '7'), ('AdapterSerialNumberLength', '0'), ('AdapterSerialNumber', ''),
      ('Vcb', '0xffff000000000000')]


def record(record_id, event_id, fields, version='1'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Ntfs" '
           f'Guid="{{3ff37a1c-a68d-4d6e-8c9b-f79e8b16c482}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>4</Level><TimeCreated SystemTime="2023-01-06 03:36:03.548039+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Correlation></Correlation>'
           f'<Execution ProcessID="4" ThreadID="8"></Execution><Channel>Microsoft-Windows-Ntfs/Operational</Channel>'
           f'<Computer>LAB-PC</Computer><Security></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_mount_names_the_volume_and_its_device(self):
        row = mounts.mount_row(record('7', '4', V1 + [('MountDurationUs', '3374000'), ('MountDuration', '3 s')]))
        self.assertEqual(row, (TIME, '4', 'The NTFS volume has been successfully mounted.', 'D:', 'New Volume', 'MAKER', 'M1',
                               'R1', 'SN000001', '7', '', '', '', '', '3 s', '', '\\Device\\HarddiskVolume9',
                               '{11111111-2222-3333-4444-555555555555}', '', '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}', '7', 'LAB-PC'))

    def test_a_dismount_carries_its_process_and_reason(self):
        row = mounts.mount_row(record('8', '300', V1 + [('ProcessId', '4'), ('ProcessName', 'System'),
                                                        ('DismountReason', 'Surprise removal')]))
        self.assertEqual(row[1:3], ('300', 'NTFS volume dismount has started.'))
        self.assertEqual(row[11:15], ('4', 'System', 'Surprise removal', ''))

    def test_a_version_0_mount_failure_reads_its_volume_name_guid_and_error(self):
        row = mounts.mount_row(record('9', '305', [('Error', '0xc0210000'), ('VolumeGuid', '{54aeb569-0000-0000-0000-010000000000}'),
                                                   ('VolumeNameLength', '2'), ('VolumeName', 'E:')], version='0'))
        self.assertEqual(row[2:4], ('NTFS failed to mount the volume.', 'E:'))
        self.assertEqual(row[4:11], ('', '', '', '', '', '', ''))
        self.assertEqual((row[15], row[17], row[18]), ('0xc0210000', '', '{54aeb569-0000-0000-0000-010000000000}'))

    def test_the_four_events(self):
        self.assertEqual(sorted(mounts._EVENTS, key=int), ['4', '300', '303', '305'])  # pylint: disable=protected-access
        self.assertEqual(mounts._EVENTS['303'], 'The NTFS volume has successfully dismounted.')  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_four_events_of_the_provider(self):
        with mock.patch.object(mounts, 'read_event_records', return_value=([record('3', '303', V1)], [LOG])) as reader:
            headers, rows, source = mounts.ntfsVolumeMounts.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Ntfs%4Operational.evtx', 'NTFS Volume Mounts',
                                       event_ids={'4', '300', '303', '305'}, provider='Microsoft-Windows-Ntfs')
        self.assertEqual(source, LOG)
        self.assertEqual(len(headers), 22)
        self.assertEqual(headers[0], ('Event Time (UTC)', 'datetime'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(rows[0][20], '3')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(mounts, 'read_event_records', return_value=([], [])):
            self.assertEqual(mounts.ntfsVolumeMounts.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
