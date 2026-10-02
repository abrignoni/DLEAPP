"""Pin the rows in scripts/artifacts/windowsRdpCoreEvents.py and the Activity ID the shared event reader keeps.

The records are built from XML of the shape python-evtx renders for the events (made-up addresses and names); the
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

from scripts.artifacts import windowsRdpCoreEvents as rdp  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = ('/case/data/vol1/Windows/System32/winevt/Logs/'
       'Microsoft-Windows-RemoteDesktopServices-RdpCoreTS%4Operational.evtx')
ACTIVITY = '{11111111-2222-3333-4444-555555555555}'
OTHER = '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}'


def record(when, record_id, event_id, fields, activity=ACTIVITY, correlation=True):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    link = f'<Correlation ActivityID="{activity}" RelatedActivityID=""></Correlation>' if correlation else ''
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-RemoteDesktopServices-RdpCoreTS" '
           f'Guid="{{1139c61b-b549-4251-8ed3-27250a1edec8}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID>{link}<Execution ProcessID="520" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-RemoteDesktopServices-RdpCoreTS/Operational</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-20"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
ACCEPTED = 'The server accepted a new connection from client'


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class EventRecordTest(unittest.TestCase):
    def test_the_activity_id_is_kept_as_rendered_and_is_blank_when_the_record_has_none(self):
        self.assertEqual(record(WHEN, '1', '131', []).activity_id, ACTIVITY)
        self.assertEqual(record(WHEN, '1', '131', [], activity='').activity_id, '')
        self.assertEqual(record(WHEN, '1', '131', [], correlation=False).activity_id, '')
        self.assertEqual(EventRecord(ElementTree.fromstring(f'<Event xmlns="{NS}"></Event>')).activity_id, '')


class RowTest(unittest.TestCase):
    def test_an_accepted_connection_carries_the_address_and_the_connection_type_as_stored(self):
        self.assertEqual(rdp.connection_row(record(WHEN, '11', '131', [('ConnType', 'TCP'), ('ClientIP', '192.0.2.10:50001')])),
                         (TIME, '131', ACCEPTED, '192.0.2.10:50001', 'TCP', '', '', '', '', '', ACTIVITY, '11', 'LAB-PC'))
        row = rdp.connection_row(record(WHEN, '12', '131', [('ConnType', 'UDP'), ('ClientIP', '[192.0.2.10]:50002')],
                                        activity=OTHER))
        self.assertEqual(row[3:5] + row[10:11], ('[192.0.2.10]:50002', 'UDP', OTHER))

    def test_the_connection_name_and_the_session_come_from_65_and_66(self):
        self.assertEqual(rdp.connection_row(record(WHEN, '13', '65', [('ConnectionName', 'RDP-Tcp#4')])),
                         (TIME, '65', 'Connection created', '', '', 'RDP-Tcp#4', '', '', '', '', ACTIVITY, '13', 'LAB-PC'))
        self.assertEqual(rdp.connection_row(record(WHEN, '14', '66', [('ConnectionName', 'RDP-Tcp#4'), ('SessionID', '7')])),
                         (TIME, '66', 'The connection was assigned to session', '', '', 'RDP-Tcp#4', '7', '', '', '', ACTIVITY,
                          '14', 'LAB-PC'))

    def test_the_timezone_the_reason_and_the_end_of_the_connection(self):
        self.assertEqual(rdp.connection_row(record(WHEN, '15', '104', [('TimezoneBiasHour', '[-8]')])),
                         (TIME, '104', 'Client timezone hour from UTC', '', '', '', '', '', '[-8]', '', ACTIVITY, '15', 'LAB-PC'))
        self.assertEqual(rdp.connection_row(record(WHEN, '16', '103', [('ReasonCode', '12')])),
                         (TIME, '103', 'The disconnect reason is', '', '', '', '', '12', '', '', ACTIVITY, '16', 'LAB-PC'))
        self.assertEqual(rdp.connection_row(record(WHEN, '17', '102', [])),
                         (TIME, '102', 'The server has terminated main RDP connection with the client', '', '', '', '', '', '',
                          '', ACTIVITY, '17', 'LAB-PC'))

    def test_139_and_140_take_the_address_from_ipstring_and_139_its_result_code(self):
        row = rdp.connection_row(record(WHEN, '18', '139', [('ResultCode', '0x80090304'), ('IPString', '192.0.2.44')]))
        self.assertEqual(row[2:11], ('The server security layer detected an error in the protocol stream and the client has '
                                     'been disconnected', '192.0.2.44', '', '', '', '', '', '0x80090304', ACTIVITY))
        row = rdp.connection_row(record(WHEN, '19', '140', [('IPString', '192.0.2.45')]))
        self.assertEqual(row[2:11], ('A connection from the client computer failed because the user name or password is not '
                                     'correct', '192.0.2.45', '', '', '', '', '', '', ACTIVITY))

    def test_an_address_field_of_another_event_is_not_used(self):
        row = rdp.connection_row(record(WHEN, '20', '65', [('ConnectionName', 'RDP-Tcp#4'), ('ClientIP', '192.0.2.99:1'),
                                                           ('IPString', '192.0.2.98')]))
        self.assertEqual(row[3], '')
        row = rdp.connection_row(record(WHEN, '21', '131', [('ConnType', 'TCP'), ('IPString', '192.0.2.98')]))
        self.assertEqual(row[3], '')
        row = rdp.connection_row(record(WHEN, '22', '140', [('ClientIP', '192.0.2.99:1')]))
        self.assertEqual(row[3], '')

    def test_white_space_at_either_end_of_a_value_is_removed(self):
        row = rdp.connection_row(record(WHEN, '23', '131', [('ConnType', ' TCP '), ('ClientIP', ' 192.0.2.10:50001 ')]))
        self.assertEqual(row[3:5], ('192.0.2.10:50001', 'TCP'))

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(rdp.connection_row(record(WHEN, '24', '131', [], correlation=False)),
                         (TIME, '131', ACCEPTED, '', '', '', '', '', '', '', '', '24', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_eight_events_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '131', []), record(WHEN, '21', '65', []), record(WHEN, '23', '140', [])], [LOG])
        with mock.patch.object(rdp, 'read_event_records', return_value=found) as reader:
            headers, rows, source = rdp.rdpCoreConnectionEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-remotedesktopservices-rdpcorets%4operational.evtx',
                                       'Remote Desktop Core Connection Events',
                                       event_ids={'65', '66', '102', '103', '104', '131', '139', '140'},
                                       provider='Microsoft-Windows-RemoteDesktopServices-RdpCoreTS')
        self.assertEqual([(row[11], row[1]) for row in rows], [('22', '131'), ('21', '65'), ('23', '140')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Client Address (as stored)',
                                   'Connection Type', 'Connection Name', 'Session ID', 'Reason Code (as stored)',
                                   'Client Timezone (as stored)', 'Result Code (as stored)', 'Activity ID', 'Record ID',
                                   'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        with mock.patch.object(rdp, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(rdp.rdpCoreConnectionEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(rdp, 'read_event_records', return_value=([], [])):
            self.assertEqual(rdp.rdpCoreConnectionEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
