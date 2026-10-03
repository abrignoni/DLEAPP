"""Pin the rows in scripts/artifacts/windowsLiveIdEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up values); the expected rows
and the whole Event ID table are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree
from xml.sax.saxutils import escape

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsLiveIdEvents as live  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-LiveId%4Operational.evtx'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
USER = 'S-1-5-21-1-2-3-1001'


def record(record_id, event_id, fields, user=USER):
    data = ''.join(f'<Data Name="{name}">{escape(value)}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-LiveId" '
           f'Guid="{{05f02597-fe85-4e67-8542-69567ab8fd4f}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-LiveId/Operational</Channel><Computer>LAB-PC</Computer>{security}'
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
    def test_a_token_record_fills_the_token_columns(self):
        fields = [('ResourceURI', ' https://example.test/service '), ('Created', '2023-01-03 12:29:35'),
                  ('Expires', '2023-01-04 12:29:35'), ('TokenType', 'urn:passport:compact'), ('AuthRequired', '0'),
                  ('RequestStatus', '0'), ('HasFlowUrl', 'False'), ('HasAuthUrl', 'False'), ('HasEndAuthUrl', 'False')]
        self.assertEqual(live.live_id_row(record('7', '6117', fields)),
                         (TIME, '6117', 'Acquired Service token.', 'https://example.test/service', '2023-01-03 12:29:35',
                          '2023-01-04 12:29:35', 'urn:passport:compact', '0', '', '', '', '',
                          'AuthRequired: 0 | HasFlowUrl: False | HasAuthUrl: False | HasEndAuthUrl: False',
                          USER, '7', 'LAB-PC'))

    def test_an_account_error_record_has_the_cid_and_the_error_code(self):
        fields = [('RequestType', '1'), ('cid', '0123456789abcdef'), ('ErrorCode', '2147776685'), ('MachineEnvironment', 'production')]
        row = live.live_id_row(record('8', '6114', fields))
        self.assertEqual(row[2], "SOAP Request of type %1 for user CID '%2' in %4 environment received the following error "
                                 'code from the Microsoft Account server: %3.')
        self.assertEqual(row[3:13], ('', '', '', '', '', '0123456789abcdef', '', '2147776685', '',
                                     'RequestType: 1 | MachineEnvironment: production'))

    def test_a_soap_body_has_its_own_column_and_function_errors_fill_theirs(self):
        body = '<s:Envelope><s:Body>*</s:Body></s:Envelope>'
        row = live.live_id_row(record('9', '6115', [('Value', f'  {body}\n')], user=''))
        self.assertEqual((row[2], row[11], row[12], row[13]), ('## SOAP Request: %1', body, '', ''))
        row = live.live_id_row(record('10', '6113', [('FunctionName', 'WLIDCreateContext'), ('ErrorCode', '2147780713')]))
        self.assertEqual(row[9:13], ('WLIDCreateContext', '2147780713', '', ''))

    def test_other_fields_keep_record_order_and_skip_blank_values(self):
        fields = [('Operation', 'Service started'), ('Blank', '  '), ('Details', ' padded '), ('Status', '0x00000000|')]
        row = live.live_id_row(record('11', '2024', fields))
        self.assertEqual((row[2], row[12]), ('Operation: %1', 'Operation: Service started | Details: padded | Status: 0x00000000|'))

    def test_an_event_id_outside_the_table_has_no_event_text(self):
        self.assertEqual(live.live_id_row(record('12', '9999', []))[2], '')

    def test_the_table_holds_the_events_of_the_operational_channel(self):
        self.assertEqual(live._EVENTS, {  # pylint: disable=protected-access
            '1021': 'SignOutUser_RegistryOpenOrReadFailure.',
            '1022': 'SignOutUser_RegistryWriteFailure.',
            '2023': 'Operation: %1',
            '2024': 'Operation: %1',
            '2025': 'WLIDSvc service failed to start.',
            '2028': 'ErrorVerifier in function %1 encountered unexpected error code (%2).',
            '6113': 'RPC call to function %1 returned the following error code: %2.',
            '6114': "SOAP Request of type %1 for user CID '%2' in %4 environment received the following "
                    'error code from the Microsoft Account server: %3.',
            '6115': '## SOAP Request: %1',
            '6116': '## SOAP Response: %1',
            '6117': 'Acquired Service token.',
        })


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Resource URI', 'Token Created (as stored)',
               'Token Expires (as stored)', 'Token Type', 'Request Status (as stored)', 'Account CID', 'Function Name',
               'Error Code (as stored)', 'SOAP Body (as stored)', 'Other Fields', 'User SID', 'Record ID', 'Computer')

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '6117', [('ResourceURI', 'B')]), record('21', '2024', [('Operation', 'x')]),
                   record('22', '6114', [('cid', 'c')]), record('24', '9999', [])]
        with mock.patch.object(live, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = live.liveIdEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-LiveId%4Operational.evtx', 'Microsoft Account (LiveId) Events',
                                       provider='Microsoft-Windows-LiveId')
        self.assertEqual([(row[14], row[1], row[3], row[8]) for row in rows],
                         [('23', '6117', 'B', ''), ('21', '2024', '', ''), ('22', '6114', '', 'c'), ('24', '9999', '', '')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(live, 'read_event_records', return_value=([record('1', '2024', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(live.liveIdEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(live, 'read_event_records', return_value=([], [])):
            self.assertEqual(live.liveIdEvents.__wrapped__(_Context()), (self.HEADERS, [], ''))


if __name__ == '__main__':
    unittest.main()
