"""Pin the rows in scripts/artifacts/windowsSmbServerEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up names and addresses); the
expected rows are written out. In the tested logs 551, 1001, 1016, 1017 and 1020 are UserData holding an EventData
element and 4000 is plain EventData; both shapes are built here.
"""
import base64
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsSmbServerEvents as smb  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOGS = '/case/data/vol1/Windows/System32/winevt/Logs/'
SECURITY = LOGS + 'Microsoft-Windows-SMBServer%4Security.evtx'
OPERATIONAL = LOGS + 'Microsoft-Windows-SMBServer%4Operational.evtx'


def b64(hexadecimal):
    return base64.b64encode(bytes.fromhex(hexadecimal)).decode()


# family 2, port 49934 (C30E), 192.0.2.7, then eight zero bytes
V4 = b64('0200' + 'c30e' + 'c0000207' + '00' * 8)
# family 23, port 52695 (CDD7), flow 0, ::1, scope 0
V6 = b64('1700' + 'cdd7' + '00000000' + '00' * 15 + '01' + '00000000')


def record(when, record_id, event_id, fields, version='0', channel='Security', user_data=True,
           provider='Microsoft-Windows-SMBServer'):
    data = ''.join(f'<{name}>{value}</{name}>' if user_data else f'<Data Name="{name}">{value}</Data>'
                   for name, value in fields)
    body = (f'<UserData><EventData xmlns="http://manifests.microsoft.com/win/2004/08/windows/eventlog">{data}'
            f'</EventData></UserData>') if user_data else f'<EventData>{data}</EventData>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" '
           f'Guid="{{d48ce617-33a2-4bc3-a5c7-11aa4f29619e}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>2</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-SMBServer/{channel}</Channel><Computer>LAB-SRV</Computer>'
           f'<Security UserID="S-1-5-18"></Security></System>{body}</Event>')
    return EventRecord(ElementTree.fromstring(xml), SECURITY)


WHEN = '2026-10-17 05:24:32.108000+00:00'
TIME = datetime.datetime(2026, 10, 17, 5, 24, 32, 108000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [SECURITY, OPERATIONAL]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_failed_session_authentication(self):
        fields = [('SessionGUID', '{00000000-0000-0000-0000-000000000001}'), ('Status', '0xc000006d'),
                  ('TranslatedStatus', '0xc000006d'), ('ClientAddressLength', '128'), ('ClientAddress', V4),
                  ('SessionId', '0x0000000000000001'), ('UserNameLength', '0'), ('UserName', ''),
                  ('ClientNameLength', '22'), ('ClientName', '\\\\192.0.2.7'), ('SPN', 'cifs/lab-srv'),
                  ('ReasonCode', '0')]
        self.assertEqual(smb.smb_server_row(record(WHEN, '11', '551', fields, '3')),
                         (TIME, '551', 'SMB Session Authentication Failure', '\\\\192.0.2.7', '192.0.2.7:49934', '',
                          '', '', '', '', '0x0000000000000001', '0xc000006d', '0xc000006d',
                          'Microsoft-Windows-SMBServer/Security', '3', '11', 'LAB-SRV'))

    def test_a_slow_file_operation_names_the_user_share_and_file(self):
        fields = [('Command', '5'), ('SessionId', '0x0000000000000002'), ('UserName', 'LAB\\user'),
                  ('ClientName', '\\\\192.0.2.7'), ('ClientAddress', V4), ('ShareName', '\\\\*\\data'),
                  ('FileName', 'folder\\file.txt'), ('Duration', '15000'), ('Threshold', '15000')]
        self.assertEqual(smb.smb_server_row(record(WHEN, '12', '1020', fields, '1', 'Operational')),
                         (TIME, '1020', 'File system operation has taken longer than expected', '\\\\192.0.2.7',
                          '192.0.2.7:49934', 'LAB\\user', '', '\\\\*\\data', '', 'folder\\file.txt',
                          '0x0000000000000002', '', '', 'Microsoft-Windows-SMBServer/Operational', '1', '12',
                          'LAB-SRV'))

    def test_the_other_field_spellings(self):
        fields = [('FileName', 'f.txt'), ('UserName', 'user'), ('ComputerName', 'LAB-PC'), ('ShareName', 'data'),
                  ('SessionID', '0x3'), ('Status', '3221225506'), ('DomainName', 'LAB'), ('SharePath', 'C:\\data')]
        row = smb.smb_server_row(record(WHEN, '13', '658', fields, '0', 'Operational'))
        self.assertEqual(row[2:13], ('File handle for file "%8\\%2" was invalidated by user %4 from computer %6',
                                     'LAB-PC', '', 'user', 'LAB', 'data', 'C:\\data', 'f.txt', '0x3',
                                     '0xC0000022 (3221225506)', ''))
        both = [('ClientName', 'client'), ('ComputerName', 'computer'), ('SessionId', '1'), ('SessionID', '2')]
        self.assertEqual(smb.smb_server_row(record(WHEN, '14', '1003', both, '1'))[3:11:7], ('client', '1'))

    def test_4000_in_plain_event_data_has_no_event_text(self):
        fields = [('ShareNameLength', '5'), ('ShareName', 'IPC$'), ('ClientAddressLength', '28'),
                  ('ClientAddress', V6), ('ClientName', '\\\\[::1]'), ('SessionId', '35184372088833'),
                  ('TreeId', '1'), ('SigningUsed', 'true'), ('EncyptionUsed', 'false')]
        self.assertEqual(smb.smb_server_row(record(WHEN, '15', '4000', fields, '0', 'Connectivity', False)),
                         (TIME, '4000', '', '\\\\[::1]', '[::1]:52695', '', '', 'IPC$', '', '', '35184372088833',
                          '', '', 'Microsoft-Windows-SMBServer/Connectivity', '0', '15', 'LAB-SRV'))

    def test_a_record_with_no_fields_and_a_version_the_table_lacks(self):
        self.assertEqual(smb.smb_server_row(record(WHEN, '16', '1001', [], '1', 'Operational'))[1:4],
                         ('1001', 'A client attempted to access the server using SMB1 and was rejected because SMB1 '
                                  'file sharing support is disabled or has been uninstalled', ''))
        self.assertEqual(smb.smb_server_row(record(WHEN, '17', '551', [], '9'))[1:3], ('551', ''))

    def test_the_event_table(self):
        self.assertEqual(smb._EVENT_IDS,  # pylint: disable=protected-access
                         {'551', '658', '1000', '1001', '1003', '1004', '1005', '1006', '1007', '1009', '1015', '1016',
                          '1017', '1020', '1046', '1054', '1061', '1906', '3000', '3002', '3021', '3022', '3023',
                          '4000'})
        self.assertTrue(all(label and not label.endswith('.') for label in smb._EVENTS.values()))  # pylint: disable=protected-access
        self.assertNotIn('1012', smb._EVENT_IDS)  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def test_each_log_is_read_for_the_events_of_the_provider_in_log_order(self):
        calls = []

        def fake_read(_context, file_name, label, event_ids=None, provider=None):
            calls.append((file_name, label, event_ids, provider))
            if file_name.endswith('security.evtx'):
                return [record(WHEN, '22', '551', [], '3'), record(WHEN, '21', '551', [], '3')], [SECURITY]
            if file_name.endswith('operational.evtx'):
                return [record(WHEN, '5', '1017', [('ShareName', 'data')], '0', 'Operational')], [OPERATIONAL]
            return [], []

        with mock.patch.object(smb, 'read_event_records', side_effect=fake_read):
            headers, rows, source = smb.smbServerClientEvents.__wrapped__(_Context())
        self.assertEqual([call[0] for call in calls],
                         ['microsoft-windows-smbserver%4operational.evtx', 'microsoft-windows-smbserver%4security.evtx',
                          'microsoft-windows-smbserver%4audit.evtx', 'microsoft-windows-smbserver%4connectivity.evtx'])
        self.assertTrue(all(call[1:] == ('SMB Server Client Events', smb._EVENT_IDS,  # pylint: disable=protected-access
                                         'Microsoft-Windows-SMBServer') for call in calls))
        self.assertEqual([(row[15], row[1]) for row in rows], [('5', '1017'), ('22', '551'), ('21', '551')])
        self.assertEqual(source, OPERATIONAL + '\n' + SECURITY)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Client Name',
                                   'Client Address', 'User Name', 'Domain Name', 'Share Name', 'Share Path',
                                   'File Name', 'Session ID (as stored)', 'Status', 'Translated Status', 'Channel',
                                   'Event Version', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_no_log_gives_no_rows_and_no_source(self):
        with mock.patch.object(smb, 'read_event_records', return_value=([], [])):
            self.assertEqual(smb.smbServerClientEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
