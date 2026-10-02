"""Pin the rows in scripts/artifacts/windowsStorageClassPnpEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up device names and values);
the expected rows and the whole Event ID table are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsStorageClassPnpEvents as classpnp  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Storage-ClassPnP%4Operational.evtx'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
GUID = '{0A1B2C3D-1111-2222-3333-444455556666}'
DEVICE = [('DeviceGUID', GUID), ('DeviceNumber', '2'), ('Vendor', 'ACME    '), ('Model', 'Pocket Drive    '),
          ('FirmwareVersion', '1.00'), ('SerialNumber', ' 0123456789ABCDEF ')]


def record(record_id, event_id, fields, user='S-1-5-18'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-StorDiag" '
           f'Guid="{{f5d05b38-80a6-4653-825d-c414e4ab3c68}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>1</Version><Level>2</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-Storage-ClassPnP/Operational</Channel><Computer>LAB-PC</Computer>{security}'
           f'</System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_failed_request_record_has_the_device_columns_and_its_other_fields_in_record_order(self):
        fields = DEVICE + [('IrpStatus', ' 0xc000009d  '), ('IoctlControlCode', '0x2d1400')]
        self.assertEqual(classpnp.class_pnp_row(record('7', '504', fields)),
                         (TIME, '504', 'Completing a failed IOCTL request.', '2', 'ACME', 'Pocket Drive', '0123456789ABCDEF',
                          '1.00', f'DeviceGUID: {GUID} | IrpStatus: 0xc000009d | IoctlControlCode: 0x2d1400', 'S-1-5-18',
                          '7', 'LAB-PC'))

    def test_the_device_columns_follow_their_own_order_whatever_the_record_order(self):
        fields = [('SerialNumber', 'S'), ('FirmwareVersion', 'F'), ('Model', 'M'), ('Vendor', 'V'), ('DeviceNumber', 'N'), ('LBA', '9')]
        row = classpnp.class_pnp_row(record('8', '502', fields, user=''))
        self.assertEqual(row[3:10], ('N', 'V', 'M', 'S', 'F', 'LBA: 9', ''))

    def test_a_record_without_the_device_fields_has_blank_device_columns(self):
        fields = [('DeviceGUID', GUID), ('Status', '0xc0000010'), ('InputBufferLength', '8'), ('DeviceNumber', '0'), ('Blank', '  '),
                  ('Empty', ''), ('Text', 'a\nb  c')]
        row = classpnp.class_pnp_row(record('9', '512', fields))
        self.assertEqual(row[2:9], ('Get Storage Firmware Information', '0', '', '', '', '',
                                    f'DeviceGUID: {GUID} | Status: 0xc0000010 | InputBufferLength: 8 | Text: a\nb  c'))

    def test_an_event_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(classpnp.class_pnp_row(record('10', '500', []))[2:9],
                         ('Completing a failed upper level read request.', '', '', '', '', '', ''))
        row = classpnp.class_pnp_row(record('11', '9999', [('Extra', 'kept'), ('Vendor', 'NULL')]))
        self.assertEqual((row[1], row[2], row[4], row[8]), ('9999', '', 'NULL', 'Extra: kept'))

    def test_the_table_holds_the_events_of_the_operational_channel(self):
        self.assertEqual(classpnp._EVENTS, {  # pylint: disable=protected-access
            '500': 'Completing a failed upper level read request.',
            '501': 'Completing a failed upper level write request.',
            '502': 'Completing a failed upper level paging read request.',
            '503': 'Completing a failed upper level paging write request.',
            '504': 'Completing a failed IOCTL request.',
            '505': 'Completing a failed Read SCSI SRB request',
            '506': 'Completing a failed Write SCSI SRB request',
            '507': 'Completing a failed non-ReadWrite SCSI SRB request',
            '508': 'Completing a failed Non-SCSI SRB request',
            '509': 'Completing a failed PNP request.',
            '510': 'Completing a failed Power request.',
            '511': 'Completing a failed WMI request',
            '512': 'Get Storage Firmware Information',
            '513': 'Download Storage Firmware',
            '514': 'Activate New Storage Firmware',
            '515': 'Query Device Telemetry',
            '516': 'Failed to process zone command asynchronously',
            '517': 'Read capacity failed with SMR device',
            '518': 'Zone count mismatch',
            '519': 'Retrieve zone information failed',
            '520': 'Query Command Duration Limit support and its Mode Page',
            '521': 'Query Command Duration Limit Mode Page failed',
            '522': 'Set Command Duration Limit Mode Page failed',
            '523': 'Read capacity failed',
        })


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Number', 'Vendor', 'Model', 'Serial Number',
               'Firmware Version', 'Other Fields', 'User SID', 'Record ID', 'Computer')

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '504', DEVICE), record('21', '512', [('DeviceNumber', '1')]), record('22', '504', DEVICE),
                   record('24', '9999', [])]
        with mock.patch.object(classpnp, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = classpnp.storageClassPnpEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Storage-ClassPnP%4Operational.evtx', 'Storage ClassPnP Events',
                                       provider='Microsoft-Windows-StorDiag')
        self.assertEqual([(row[10], row[1], row[3], row[6]) for row in rows], [
            ('23', '504', '2', '0123456789ABCDEF'), ('21', '512', '1', ''), ('22', '504', '2', '0123456789ABCDEF'), ('24', '9999', '', '')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(classpnp, 'read_event_records', return_value=([record('1', '504', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(classpnp.storageClassPnpEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(classpnp, 'read_event_records', return_value=([], [])):
            self.assertEqual(classpnp.storageClassPnpEvents.__wrapped__(_Context()), (self.HEADERS, [], ''))


if __name__ == '__main__':
    unittest.main()
