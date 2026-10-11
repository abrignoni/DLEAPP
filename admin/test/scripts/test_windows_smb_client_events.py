"""Pin the rows in scripts/artifacts/windowsSmbClientEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up names and addresses); the
expected rows are written out.
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

from scripts.artifacts import windowsSmbClientEvents as smb  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-SmbClient%4Connectivity.evtx'


def b64(hexadecimal):
    return base64.b64encode(bytes.fromhex(hexadecimal)).decode()


# family 2, port 445 (01BD), 192.0.2.7, then eight zero bytes
V4 = b64('0200' + '01bd' + 'c0000207' + '00' * 8)
# family 23 (17 00), port 443 (01BB), flow 0, 2001:db8::9, scope 0
V6 = b64('1700' + '01bb' + '00000000' + '20010db8000000000000000000000009' + '00000000')


def record(when, record_id, event_id, fields, version='0'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-SMBClient" '
           f'Guid="{{988c59c5-0a1c-45b6-a555-0c62276e327d}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>2</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-SmbClient/Connectivity</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="S-1-5-18"></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2026-10-11 05:24:32.108000+00:00'
TIME = datetime.datetime(2026, 10, 11, 5, 24, 32, 108000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class SocketAddressTest(unittest.TestCase):
    def test_ipv4_and_ipv6(self):
        self.assertEqual(smb.socket_address(V4), '192.0.2.7:445')
        self.assertEqual(smb.socket_address(V6), '[2001:db8::9]:443')
        self.assertEqual(smb.socket_address(b64('0200' + 'ff01' + '7f000001')), '127.0.0.1:65281')

    def test_nothing_recorded(self):
        self.assertEqual(smb.socket_address(''), '')
        self.assertEqual(smb.socket_address(b64('00' * 16)), '')

    def test_other_content_is_kept_as_stored(self):
        for text in ('not base64!', V4[:4] + '!' + V4[4:], b64('0200' + '01bd' + 'c00002'), b64('1700' + '01bb' + '00' * 18 + '01'),
                     b64('0002' + '01bd' + 'c0000207'), b64('0100' + '01bd' + 'c0000207' + '00' * 8), 'AgAB'):
            self.assertEqual(smb.socket_address(text), text)


class RowTest(unittest.TestCase):
    def test_a_name_that_could_not_be_resolved(self):
        fields = [('Reason', '1'), ('Status', '3221226021'), ('ServerNameLength', '9'), ('ServerName', ' lab-host ')]
        self.assertEqual(smb.smb_row(record(WHEN, '11', '30800', fields)),
                         (TIME, '30800', 'The server name cannot be resolved', 'lab-host', '', '', '',
                          '0xC0000225 (3221226021)', '1', '', '', '', '', '', '0', '11', 'LAB-PC'))

    def test_a_failed_connection_with_both_addresses(self):
        fields = [('Reason', '4'), ('Status', '3221225653'), ('ServerName', '192.0.2.7'), ('AddressLength', '16'),
                  ('RemoteAddress', V4), ('LocalAddress', V6), ('InstanceName', '\\Device\\LanmanRedirector'),
                  ('ConnectionType', '1')]
        self.assertEqual(smb.smb_row(record(WHEN, '12', '30803', fields, '3')),
                         (TIME, '30803', 'Failed to establish a network connection', '192.0.2.7', '192.0.2.7:445',
                          '[2001:db8::9]:443', '1', '0xC00000B5 (3221225653)', '4', '', '', '', '',
                          '\\Device\\LanmanRedirector', '3', '12', 'LAB-PC'))

    def test_the_older_address_field_name(self):
        fields = [('Status', '0'), ('SessionId', '70368744177665'), ('TreeId', '5'), ('ServerName', '\\192.0.2.7\\C$'),
                  ('Address', V4), ('ConnectionType', '1'), ('SigningUsed', 'True'), ('EncryptionUsed', 'False')]
        self.assertEqual(smb.smb_row(record(WHEN, '13', '30833', fields)),
                         (TIME, '30833', '', '\\192.0.2.7\\C$', '192.0.2.7:445', '', '1', '0x00000000 (0)', '',
                          '70368744177665', '5', 'True', 'False', '', '0', '13', 'LAB-PC'))

    def test_remote_address_is_used_before_address_and_a_text_status_is_kept(self):
        fields = [('ServerName', 'srv'), ('RemoteAddress', V6), ('Address', V4), ('LocalAddress', ''),
                  ('Status', '0x00000000')]
        row = smb.smb_row(record(WHEN, '14', '30830', fields, '2'))
        self.assertEqual(row[2:8], ('The SMB redirector selected the connection initiated with the following parameters',
                                    'srv', '[2001:db8::9]:443', '', '', '0x00000000'))

    def test_only_the_server_name_field_gives_the_name(self):
        self.assertEqual(smb.smb_row(record(WHEN, '16', '30800', [('Name', 'interface'), ('ShareName', 'share')]))[3], '')

    def test_every_event_has_a_label_except_30833(self):
        self.assertEqual({key for key, value in smb._EVENTS.items() if not value}, {'30833'})  # pylint: disable=protected-access
        for event_id in smb._EVENTS:  # pylint: disable=protected-access
            self.assertEqual(smb.smb_row(record(WHEN, '15', event_id, []))[1:3],
                             (event_id, smb._EVENTS[event_id]))  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_events_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '30830', []), record(WHEN, '21', '30800', [])], [LOG])
        with mock.patch.object(smb, 'read_event_records', return_value=found) as reader:
            headers, rows, source = smb.smbClientConnectionEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-smbclient%4connectivity.evtx',
                                       'SMB Client Connection Events',
                                       event_ids={'30800', '30803', '30804', '30805', '30806', '30807', '30808', '30828',
                                                  '30829', '30830', '30833'},
                                       provider='Microsoft-Windows-SMBClient')
        self.assertEqual([(row[15], row[1]) for row in rows], [('22', '30830'), ('21', '30800')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Server or Share Name',
                                   'Server Address', 'Client Address', 'Connection Type (as stored)', 'Status',
                                   'Reason (as stored)', 'Session ID (as stored)', 'Tree ID (as stored)', 'Signing Used',
                                   'Encryption Used', 'Instance Name', 'Event Version', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        with mock.patch.object(smb, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(smb.smbClientConnectionEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(smb, 'read_event_records', return_value=([], [])):
            self.assertEqual(smb.smbClientConnectionEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
