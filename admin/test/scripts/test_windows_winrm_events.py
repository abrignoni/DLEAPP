"""Pin the rows in scripts/artifacts/windowsWinRmEvents.py.

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

from scripts.artifacts import windowsWinRmEvents as winrm  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-WinRM%4Operational.evtx'
ACTIVITY = '{0a1b2c3d-1111-2222-3333-444455556666}'
RELATED = '{ffffffff-1111-2222-3333-444455556666}'


def record(record_id, event_id, fields, user='S-1-5-18', activity=ACTIVITY, pid='4321'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    correlation = (f'<Correlation ActivityID="{activity}" RelatedActivityID="{RELATED}"></Correlation>' if activity
                   else '<Correlation></Correlation>')
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-WinRM" '
           f'Guid="{{a7975c8f-ac13-49f1-87da-5a984a4ab417}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID>{correlation}'
           f'<Execution ProcessID="{pid}" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-WinRM/Operational</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_session_being_created_has_its_connection_and_the_record_ids(self):
        row = winrm.winrm_row(record('7', '6', [('connection', 'host.example/wsman?PSVersion=5.1')], user='S-1-5-21-1-2-3-1001'))
        self.assertEqual(row, (TIME, '6', 'Creating WSMan Session.', 'connection: host.example/wsman?PSVersion=5.1', ACTIVITY,
                               RELATED, '4321', 'S-1-5-21-1-2-3-1001', '7', 'LAB-PC'))

    def test_fields_are_listed_by_name_in_record_order_without_the_empty_ones(self):
        fields = [('resourceUri', ' http://x/y '), ('Blank', '   '), ('Empty', ''), ('operationName', 'Get  it\n')]
        row = winrm.winrm_row(record('8', '145', fields))
        self.assertEqual(row[2], 'WSMan operation %1 started with resourceUri %2')
        self.assertEqual(row[3], 'resourceUri: http://x/y | operationName: Get  it')

    def test_the_related_activity_id_follows_the_activity_id(self):
        self.assertEqual(winrm.winrm_row(record('9', '254', []))[2:7], ('Activity Transfer', '', ACTIVITY, RELATED, '4321'))

    def test_a_record_with_no_activity_and_no_user_has_blank_cells(self):
        row = winrm.winrm_row(record('10', '208', [], user='', activity='', pid='88'))
        self.assertEqual(row[2:8], ('The Winrm service is starting', '', '', '', '88', ''))

    def test_an_event_whose_message_is_a_placeholder_and_an_event_id_outside_the_table(self):
        self.assertEqual(winrm.winrm_row(record('11', '161', [('authFailureMessage', 'no')]))[2:4], ('%1', 'authFailureMessage: no'))
        row = winrm.winrm_row(record('12', '9999', [('Extra', 'kept')]))
        self.assertEqual((row[1], row[2], row[3]), ('9999', '', 'Extra: kept'))

    def test_the_table_holds_the_seventy_four_events_of_the_operational_channel(self):
        events = winrm._EVENTS  # pylint: disable=protected-access
        self.assertEqual(len(events), 74)
        self.assertEqual((min(events, key=int), max(events, key=int)), ('2', '254'))
        self.assertEqual(events['8'], 'Closing WSMan Session')
        self.assertEqual(events['91'], 'Creating WSMan shell on server with ResourceUri: %1')
        self.assertEqual(events['142'], 'WSMan operation %1 failed, error code %2')
        self.assertEqual(events['224'], '%1')
        self.assertNotIn('255', events)


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '145', [('operationName', 'Get')]), record('21', '254', []), record('22', '142', []),
                   record('24', '9999', [])]
        with mock.patch.object(winrm, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = winrm.winRmEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-WinRM%4Operational.evtx', 'WinRM Events',
                                       provider='Microsoft-Windows-WinRM')
        self.assertEqual([(row[8], row[1]) for row in rows], [('23', '145'), ('21', '254'), ('22', '142'), ('24', '9999')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Fields', 'Activity ID',
                                   'Related Activity ID', 'Process ID', 'User SID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(winrm, 'read_event_records', return_value=([record('1', '8', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(winrm.winRmEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(winrm, 'read_event_records', return_value=([], [])):
            self.assertEqual(winrm.winRmEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
