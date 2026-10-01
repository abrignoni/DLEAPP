"""Pin the Winlogon notification rows in scripts/artifacts/windowsWinlogonEvents.py.

The records are built from XML of the shape python-evtx renders for the two events (made-up SID and names); the
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
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'


def record(event_id, when, record_id, fields, source='/case/data/vol/Windows/System32/winevt/Logs/System.evtx',
           provider='Microsoft-Windows-Winlogon'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{dbe9b383-7cf3-4331-91cc-a3cb16a3b538}}">'
           f'</Provider><EventID Qualifiers="">{event_id}</EventID><Version>0</Version><Level>4</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="692" ThreadID="4720"></Execution><Channel>System</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-18"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


LOGON = record('7001', '2023-02-22 23:37:04.970000+00:00', '1401', [('TSId', '1'), ('UserSid', SID)])
LOGOFF = record('7002', '2023-02-22 23:46:05.400000+00:00', '1440', [('TSId', '2'), ('UserSid', SID)])


class NotificationRowTest(unittest.TestCase):
    def test_a_logon_notification(self):
        self.assertEqual(winlogon.notification_row(LOGON),
                         (utc(2023, 2, 22, 23, 37, 4, 970000), '7001', 'User logon notification', SID, '1', '1401',
                          'LAB-PC'))

    def test_a_logoff_notification(self):
        self.assertEqual(winlogon.notification_row(LOGOFF),
                         (utc(2023, 2, 22, 23, 46, 5, 400000), '7002', 'User logoff notification', SID, '2', '1440',
                          'LAB-PC'))

    def test_the_user_is_the_event_data_field_and_not_the_header_user(self):
        self.assertNotIn('S-1-5-18', winlogon.notification_row(LOGON))

    def test_a_record_without_the_fields_keeps_its_time_and_event(self):
        bare = record('7002', '2023-02-22 23:46:05.400000+00:00', '7', [])
        self.assertEqual(winlogon.notification_row(bare),
                         (utc(2023, 2, 22, 23, 46, 5, 400000), '7002', 'User logoff notification', '', '', '7',
                          'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, records, sources):
        with mock.patch.object(winlogon, 'read_event_records', return_value=(records, sources)) as reader:
            result = winlogon.winlogonNotifications.__wrapped__(mock.sentinel.context)
        return result, reader

    def test_the_log_the_event_ids_and_the_provider_asked_for(self):
        _result, reader = self.run_artifact([], [])
        reader.assert_called_once_with(mock.sentinel.context, 'System.evtx', 'Winlogon Logon and Logoff Notifications',
                                       event_ids={'7001', '7002'}, provider='Microsoft-Windows-Winlogon')

    def test_one_row_per_record_in_the_order_read_and_every_log_read_is_a_source(self):
        (headers, rows, source), _reader = self.run_artifact([LOGOFF, LOGON], ['/case/data/a/System.evtx',
                                                                               '/case/data/b/System.evtx'])
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User SID', 'Session',
                                   'Record ID', 'Computer'))
        self.assertEqual([(row[1], row[5]) for row in rows], [('7002', '1440'), ('7001', '1401')])
        self.assertEqual(source, '/case/data/a/System.evtx\n/case/data/b/System.evtx')

    def test_no_records_gives_no_rows_and_still_names_the_log_read(self):
        (_headers, rows, source), _reader = self.run_artifact([], ['/case/data/a/System.evtx'])
        self.assertEqual((rows, source), ([], '/case/data/a/System.evtx'))

    def test_no_log_gives_no_source(self):
        (_headers, rows, source), _reader = self.run_artifact([], [])
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
