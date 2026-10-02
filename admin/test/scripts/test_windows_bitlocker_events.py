"""Pin the rows in scripts/artifacts/windowsBitLockerEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up volumes and GUIDs); the
expected rows are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsBitLockerEvents as bitlocker  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
MANAGEMENT_LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-BitLocker%4BitLocker Management.evtx'
SYSTEM_LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'
API = 'Microsoft-Windows-BitLocker-API'
DRIVER = 'Microsoft-Windows-BitLocker-Driver'


def record(provider, record_id, event_id, fields, user='S-1-5-21-1-2-3-1001', unnamed=()):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    data += ''.join(f'<Data>{value}</Data>' for value in unnamed)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{00000000-0000-0000-0000-000000000001}}">'
           f'</Provider><EventID>{event_id}</EventID><Version>0</Version><Level>4</Level>'
           f'<TimeCreated SystemTime="2023-02-22 20:44:18.500000+00:00"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1000" ThreadID="2000"></Execution>'
           f'<Channel>Example</Channel><Computer>LAB-PC</Computer><Security UserID="{user}"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), MANAGEMENT_LOG if provider == API else SYSTEM_LOG)


TIME = datetime.datetime(2023, 2, 22, 20, 44, 18, 500000, tzinfo=datetime.timezone.utc)
ID_GUID = '{11111111-2222-3333-4444-555555555555}'
PROTECTOR = '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}'
VOLUME = '\\\\?\\Volume{01234567-0000-0000-0000-010000000000}'
BASE = [('IdentificationGUID', ID_GUID), ('VolumeName', VOLUME), ('VolumeMountPoint', 'X:')]
SID = 'S-1-5-21-1-2-3-1001'


class _Context:
    @staticmethod
    def get_files_found():
        return [MANAGEMENT_LOG, SYSTEM_LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class ManagementRowTest(unittest.TestCase):
    def test_encryption_started_carries_the_volume_and_the_algorithm_number(self):
        self.assertEqual(bitlocker.management_row(record(API, '5', '768', BASE + [('AlgorithmType', '32772')])),
                         (TIME, '768', 'BitLocker encryption was started for volume %3 using %4 algorithm.', 'X:', VOLUME,
                          ID_GUID, '', '', '32772', '', '', SID, '5', 'LAB-PC'))

    def test_a_protector_record_carries_its_guid_and_type_as_stored(self):
        fields = BASE + [('ProtectorGUID', PROTECTOR), ('ProtectorType', '0x00000008')]
        self.assertEqual(bitlocker.management_row(record(API, '6', '775', fields)),
                         (TIME, '775', 'A BitLocker key protector was created.', 'X:', VOLUME, ID_GUID, PROTECTOR,
                          '0x00000008', '', '', '', SID, '6', 'LAB-PC'))
        self.assertEqual(bitlocker.management_row(record(API, '7', '782', fields))[2],
                         'The BitLocker protected volume %3 was unlocked.')

    def test_an_error_code_has_its_column_and_a_field_without_one_goes_to_other_fields(self):
        row = bitlocker.management_row(record(API, '8', '812', [('VariableName', 'SecureBoot'), ('ErrorCode', '-2147024894')]))
        self.assertEqual(row[2], "BitLocker cannot use Secure Boot for integrity because the UEFI variable '%1' could not be read.")
        self.assertEqual(row[3:11], ('', '', '', '', '', '', '-2147024894', 'VariableName: SecureBoot'))

    def test_other_fields_keeps_record_order_joins_with_a_bar_and_leaves_out_empty_and_shown_fields(self):
        fields = [('JsonRequestId', 'abc'), ('VolumeMountPoint', 'X:'), ('JsonTime', ''), ('JsonErrorCode', '500'),
                  ('JsonSubCode', ' sub '), ('JsonMessage', '   '), ('ErrorCode', '5')]
        row = bitlocker.management_row(record(API, '9', '847', fields))
        self.assertEqual(row[10], 'JsonRequestId: abc | JsonErrorCode: 500 | JsonSubCode: sub')
        self.assertEqual((row[3], row[9]), ('X:', '5'))

    def test_white_space_at_either_end_of_a_value_is_removed_and_inner_line_breaks_stay(self):
        row = bitlocker.management_row(record(API, '10', '4122', [('LocalizedText', '\nISA Bridge:\n\tPCI\\VEN_0000\n')]))
        self.assertEqual(row[10], 'LocalizedText: ISA Bridge:\n\tPCI\\VEN_0000')
        self.assertTrue(row[2].startswith('The following DMA (Direct Memory Access) capable devices are not declared'))
        self.assertTrue(row[2].endswith('BitLocker automatic device encryption: %1'))
        self.assertEqual(bitlocker.management_row(record(API, '11', '768', [('VolumeMountPoint', ' X: ')]))[3], 'X:')

    def test_a_record_with_no_fields_keeps_its_time_user_and_text(self):
        self.assertEqual(bitlocker.management_row(record(API, '12', '810', [], user='S-1-5-18')),
                         (TIME, '810', 'BitLocker cannot use Secure Boot for integrity because it is disabled.', '', '', '',
                          '', '', '', '', '', 'S-1-5-18', '12', 'LAB-PC'))

    def test_an_event_id_outside_the_table_has_a_blank_event_and_keeps_its_fields(self):
        row = bitlocker.management_row(record(API, '13', '9999', BASE + [('Extra', 'kept')]))
        self.assertEqual((row[1], row[2], row[3], row[10]), ('9999', '', 'X:', 'Extra: kept'))

    def test_a_data_item_without_a_name_is_not_shown(self):
        row = bitlocker.management_row(record(API, '14', '780', BASE, unnamed=('loose',)))
        self.assertNotIn('loose', ' '.join(str(cell) for cell in row))

    def test_the_table_holds_the_management_events_and_none_of_the_driver_events(self):
        self.assertEqual(len(bitlocker._MANAGEMENT_EVENTS), 122)  # pylint: disable=protected-access
        self.assertEqual(bitlocker._MANAGEMENT_EVENTS['796'],  # pylint: disable=protected-access
                         'BitLocker Drive Encryption is using software-based encryption to protect volume %3.')
        self.assertNotIn('24660', bitlocker._MANAGEMENT_EVENTS)  # pylint: disable=protected-access


class DriverRowTest(unittest.TestCase):
    def test_a_sweep_record_carries_the_volume_the_error_code_and_the_write_phase(self):
        fields = [('ErrorCode', '0x00000000'), ('Volume', 'X:'), ('WritePhase', '0x00000001')]
        self.assertEqual(bitlocker.driver_row(record(DRIVER, '21', '24667', fields, user='S-1-5-18')),
                         (TIME, '24667', 'BitLocker finalization sweep completed for volume %2.', 'X:', '0x00000000',
                          '0x00000001', '', '', '', '', '21', 'LAB-PC'))

    def test_a_restart_record_carries_both_guids_and_the_flags(self):
        fields = [('ErrorCode', '0xC0210000'), ('Volume', ''), ('WritePhase', '0x00000000'), ('VolumeGUID', ID_GUID),
                  ('OptionalGUID', PROTECTOR), ('Flags', '0x00000002')]
        self.assertEqual(bitlocker.driver_row(record(DRIVER, '22', '24652', fields)),
                         (TIME, '24652', 'A recovery password was used to start Windows.', '', '0xC0210000', '0x00000000',
                          ID_GUID, PROTECTOR, '0x00000002', '', '22', 'LAB-PC'))

    def test_the_metadata_fields_go_to_other_fields_in_record_order(self):
        fields = [('ErrorCode', '0x00000000'), ('Volume', 'X:'), ('Offset', '4096'), ('Length', '65536'), ('Copy', '1'),
                  ('TotalCopies', '3'), ('SlabSize', '0')]
        row = bitlocker.driver_row(record(DRIVER, '23', '24696', fields))
        self.assertEqual(row[2], 'Successfully created metadata file.')
        self.assertEqual(row[9], 'Offset: 4096 | Length: 65536 | Copy: 1 | TotalCopies: 3 | SlabSize: 0')
        self.assertEqual(row[3:9], ('X:', '0x00000000', '', '', '', ''))

    def test_the_driver_row_has_no_user_column_and_an_unknown_event_is_blank(self):
        row = bitlocker.driver_row(record(DRIVER, '24', '30000', [('Volume', 'X:')]))
        self.assertEqual(len(row), 12)
        self.assertEqual((row[2], row[3]), ('', 'X:'))
        padded = [('ErrorCode', ' 0x00000000 '), ('Volume', ' X: '), ('WritePhase', '\n0x00000001')]
        self.assertEqual(bitlocker.driver_row(record(DRIVER, '25', '24660', padded))[3:6], ('X:', '0x00000000', '0x00000001'))
        self.assertNotIn(SID, row)

    def test_the_table_holds_the_driver_events_and_none_of_the_management_events(self):
        self.assertEqual(len(bitlocker._DRIVER_EVENTS), 127)  # pylint: disable=protected-access
        self.assertEqual(bitlocker._DRIVER_EVENTS['24580'], 'Decryption of volume %2 started.')  # pylint: disable=protected-access
        self.assertNotIn('768', bitlocker._DRIVER_EVENTS)  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def test_the_management_log_is_read_for_every_record_of_the_api_provider_in_file_order(self):
        found = ([record(API, '32', '775', BASE), record(API, '31', '768', BASE), record(API, '33', '9999', [])], [MANAGEMENT_LOG])
        with mock.patch.object(bitlocker, 'read_event_records', return_value=found) as reader:
            headers, rows, source = bitlocker.bitLockerManagementEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-bitlocker%4bitlocker management.evtx',
                                       'BitLocker Management Events', provider='Microsoft-Windows-BitLocker-API')
        self.assertEqual([(row[12], row[1]) for row in rows], [('32', '775'), ('31', '768'), ('33', '9999')])
        self.assertEqual(source, MANAGEMENT_LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Volume Mount Point', 'Volume Name',
                                   'Identification GUID', 'Protector GUID', 'Protector Type (as stored)',
                                   'Algorithm Type (as stored)', 'Error Code (as stored)', 'Other Fields', 'User SID',
                                   'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_the_system_log_is_read_for_every_record_of_the_driver_provider_in_file_order(self):
        found = ([record(DRIVER, '42', '24667', []), record(DRIVER, '41', '24660', []), record(DRIVER, '43', '30000', [])], [SYSTEM_LOG])
        with mock.patch.object(bitlocker, 'read_event_records', return_value=found) as reader:
            headers, rows, source = bitlocker.bitLockerDriverEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'BitLocker Driver Events',
                                       provider='Microsoft-Windows-BitLocker-Driver')
        self.assertEqual([(row[10], row[1]) for row in rows], [('42', '24667'), ('41', '24660'), ('43', '30000')])
        self.assertEqual(source, SYSTEM_LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Volume', 'Error Code (as stored)',
                                   'Write Phase (as stored)', 'Volume GUID', 'Optional GUID', 'Flags (as stored)',
                                   'Other Fields', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = SYSTEM_LOG.replace('vol1', 'vol2')
        for function in (bitlocker.bitLockerManagementEvents, bitlocker.bitLockerDriverEvents):
            with mock.patch.object(bitlocker, 'read_event_records', return_value=([], [SYSTEM_LOG, other])):
                self.assertEqual(function.__wrapped__(_Context())[1:], ([], SYSTEM_LOG + '\n' + other))
            with mock.patch.object(bitlocker, 'read_event_records', return_value=([], [])):
                self.assertEqual(function.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
