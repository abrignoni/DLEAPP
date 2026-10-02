"""Pin the rows in scripts/artifacts/windowsDpapiEvents.py.

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

from scripts.artifacts import windowsDpapiEvents as dpapi  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Crypto-DPAPI%4Operational.evtx'
GUID = '{0a1b2c3d-1111-2222-3333-444455556666}'
AREA = 'C:\\Users\\lab\\AppData\\Roaming\\Microsoft\\Protect\\S-1-5-21-1-2-3-1001\\'


def record(record_id, event_id, fields, user='S-1-5-18'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Crypto-DPAPI" '
           f'Guid="{{89fe8f40-cdce-464e-8217-15ef97d4c7c3}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="700" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-Crypto-DPAPI/Operational</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


def created(record_id):
    return record(record_id, '1', [('MasterKeyGUID', GUID), ('UserStorage', AREA)])


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_created_master_key_has_its_guid_and_storage_area(self):
        self.assertEqual(dpapi.dpapi_row(created('7')),
                         (TIME, '1', 'DPAPI created Master key.', GUID, AREA, '', '', '', '', 'S-1-5-18', '7', 'LAB-PC'))

    def test_a_found_credential_key_has_its_identifier_and_the_account(self):
        fields = [('CredKeyIdentifier', 'QUJDRA=='), ('UserName', 'lab'), ('UserSid', 'S-1-5-21-1-2-3-1001')]
        self.assertEqual(dpapi.dpapi_row(record('8', '12289', fields))[1:10],
                         ('12289', 'DPAPI found credential key.', '', '', 'QUJDRA==', 'lab', 'S-1-5-21-1-2-3-1001', '', 'S-1-5-18'))

    def test_fields_without_a_column_are_listed_in_record_order_without_the_empty_ones(self):
        fields = [('MasterKeyGUID', GUID), ('EncryptCredKey', 'k  1'), ('Blank', '   '), ('Empty', ''), ('EncryptCredID', ' {c} ')]
        row = dpapi.dpapi_row(record('9', '8200', fields))
        self.assertEqual(row[2], "Master key's record successfully logged to Diagnostic file.")
        self.assertEqual(row[3:9], (GUID, '', '', '', '', 'EncryptCredKey: k  1 | EncryptCredID: {c}'))

    def test_white_space_at_either_end_of_a_value_is_removed_and_a_record_with_no_user_has_a_blank_user(self):
        row = dpapi.dpapi_row(record('10', '1', [('MasterKeyGUID', f' {GUID}\n'), ('UserStorage', f'{AREA} ')], user=''))
        self.assertEqual(row[3:5], (GUID, AREA))
        self.assertEqual(row[9], '')

    def test_an_event_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(dpapi.dpapi_row(record('11', '12290', []))[2:9], ('Credential key does not exist.', '', '', '', '', '', ''))
        row = dpapi.dpapi_row(record('12', '9999', [('Extra', 'kept')]))
        self.assertEqual((row[1], row[2], row[8]), ('9999', '', 'Extra: kept'))

    def test_the_table_holds_the_twenty_events_of_the_operational_channel(self):
        events = dpapi._EVENTS  # pylint: disable=protected-access
        self.assertEqual(sorted(events, key=int), ['1', '2', '3', '4', '5', '8196'] + [str(n) for n in range(8198, 8208)]
                         + ['12289', '12290', '16386', '16387'])
        self.assertEqual(events['2'], 'DPAPI deleted Master key.')
        self.assertEqual(events['4'], 'Password Change triggered.')
        self.assertEqual(events['8198'], 'DPAPI Unprotect failed .')
        self.assertEqual(events['16386'], events['16387'])


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [created('23'), record('21', '12290', []), created('22'), record('24', '9999', [])]
        with mock.patch.object(dpapi, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = dpapi.dpapiEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Crypto-DPAPI%4Operational.evtx', 'DPAPI Events',
                                       provider='Microsoft-Windows-Crypto-DPAPI')
        self.assertEqual([(row[10], row[1]) for row in rows], [('23', '1'), ('21', '12290'), ('22', '1'), ('24', '9999')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Master Key GUID', 'User Storage Area',
                                   'Credential Key Identifier', 'Credential User Name', 'Credential User SID', 'Other Fields',
                                   'User SID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(dpapi, 'read_event_records', return_value=([created('1')], [LOG, LOG + '.copy'])):
            self.assertEqual(dpapi.dpapiEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(dpapi, 'read_event_records', return_value=([], [])):
            self.assertEqual(dpapi.dpapiEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
