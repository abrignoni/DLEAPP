"""Pin the Winlogon Operational rows in scripts/artifacts/windowsWinlogonEvents.py.

The records are built from XML of the shape python-evtx renders for the four events (made-up SID and names); the
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

from scripts.artifacts import windowsWinlogonEvents as winlogon  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol/Windows/System32/winevt/Logs/Microsoft-Windows-Winlogon%4Operational.evtx'
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
TIME = datetime.datetime(2026, 10, 4, 0, 22, 7, 570671, tzinfo=datetime.timezone.utc)


def record(event_id, record_id, fields, user=SID):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Winlogon" '
           f'Guid="{{dbe9b383-7cf3-4331-91cc-a3cb16a3b538}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2026-10-04 00:22:07.570671+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Correlation></Correlation>'
           f'<Execution ProcessID="812" ThreadID="4720"></Execution>'
           f'<Channel>Microsoft-Windows-Winlogon/Operational</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="{user}"></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class OperationalRowTest(unittest.TestCase):
    def test_a_subscriber_beginning_a_notification_event(self):
        row = winlogon.operational_row(record('811', '2621', [('Event', '4'), ('SubscriberName', 'Sens')]))
        self.assertEqual(row, (TIME, '811', 'A notification subscriber began handling a notification event', '4',
                               'Sens', '', SID, '812', '2621', 'LAB-PC'))

    def test_a_subscriber_finishing_a_notification_event(self):
        row = winlogon.operational_row(record('812', '2644', [('Event', '5'), ('SubscriberName', 'TermSrv')]))
        self.assertEqual(row, (TIME, '812', 'A notification subscriber finished handling a notification event', '5',
                               'TermSrv', '', SID, '812', '2644', 'LAB-PC'))

    def test_authentication_stopped_carries_its_result_and_no_notification(self):
        row = winlogon.operational_row(record('2', '9', [('Win32Status', '1326')], user='S-1-5-18'))
        self.assertEqual(row, (TIME, '2', 'Authentication stopped', '', '', '1326', 'S-1-5-18', '812', '9', 'LAB-PC'))

    def test_authentication_started_has_no_event_data(self):
        row = winlogon.operational_row(record('1', '8', []))
        self.assertEqual(row, (TIME, '1', 'Authentication started', '', '', '', SID, '812', '8', 'LAB-PC'))


class OperationalArtifactTest(unittest.TestCase):
    def test_the_operational_log_is_read_for_its_four_events(self):
        records = [record('811', '1', [('Event', '4'), ('SubscriberName', 'Sens')])]
        with mock.patch.object(winlogon, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = winlogon.winlogonOperational.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Winlogon%4Operational.evtx', 'Winlogon Operational Events',
                                       event_ids={'1', '2', '811', '812'}, provider='Microsoft-Windows-Winlogon')
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Notification Event (as stored)',
                                   'Subscriber', 'Result (as stored)', 'User SID', 'Process ID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(winlogon, 'read_event_records', return_value=([], [])):
            self.assertEqual(winlogon.winlogonOperational.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
