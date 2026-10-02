"""Pin the rows in scripts/artifacts/windowsEventLogServiceEvents.py.

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

from scripts.artifacts import windowsEventLogServiceEvents as service  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
SECURITY = '/case/data/vol1/Windows/System32/winevt/Logs/Security.evtx'
SYSTEM = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'


def record(record_id, event_id, fields, version='0', channel='Security', user=''):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Eventlog" '
           f'Guid="{{fc65ddd8-d6ef-4962-83d5-6e5cfe9ce148}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1200" ThreadID="8"></Execution>'
           f'<Channel>{channel}</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), SECURITY if channel == 'Security' else SYSTEM)


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [SECURITY, SYSTEM]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_the_service_shutting_down_has_no_fields(self):
        self.assertEqual(service.service_row(record('7', '1100', [])),
                         (TIME, 'Security', '1100', 'The event logging service has shut down.', '', '', '7', 'LAB-PC'))

    def test_fields_are_listed_by_name_in_record_order_without_the_empty_ones(self):
        fields = [('PubID', 'Example  Provider'), ('EventID', ' 4688 '), ('Blank', '   '), ('Empty', ''), ('ErrorCode', '2147942405')]
        row = service.service_row(record('8', '1108', fields))
        self.assertEqual(row[3], 'The event logging service encountered an error while processing an incoming event '
                                 'published from %3.')
        self.assertEqual(row[4], 'PubID: Example  Provider | EventID: 4688 | ErrorCode: 2147942405')

    def test_the_text_follows_the_record_version_and_is_blank_for_a_version_the_table_lacks(self):
        fields = [('ErrorCode', '5'), ('ChannelPath', 'Example/Operational'), ('NewLogFilePath', 'C:\\x.evtx')]
        old = service.service_row(record('9', '27', fields, channel='System'))
        new = service.service_row(record('10', '27', fields, version='1', channel='System', user='S-1-5-19'))
        self.assertTrue(old[3].endswith('while opening log file for channel %2.'))
        self.assertTrue(new[3].endswith('while opening log file for channel %2 at %3.'))
        self.assertEqual((old[1], new[1], new[5]), ('System', 'System', 'S-1-5-19'))
        self.assertEqual(service.service_row(record('11', '1100', [], version='3'))[3], '')
        self.assertEqual(service.service_row(record('12', '9999', [('Extra', 'kept')]))[3:5], ('', 'Extra: kept'))

    def test_the_table_has_no_log_cleared_event(self):
        self.assertEqual(len(service._EVENTS), 25)  # pylint: disable=protected-access
        self.assertFalse({'1102', '104'} & {key[0] for key in service._EVENTS})  # pylint: disable=protected-access
        self.assertEqual(service._EVENTS[('1104', '0')], 'The security log is now full.')  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def test_both_logs_are_read_for_the_provider_in_record_order_and_the_log_cleared_events_are_left_out(self):
        security = ([record('23', '1100', []), record('21', '1102', []), record('22', '1101', [('Reason', '0')])], [SECURITY])
        system = ([record('5', '104', [], channel='System'), record('4', '6000', [('Channel', 'Example')], channel='System'),
                   record('3', '9999', [], channel='System')], [SYSTEM])
        with mock.patch.object(service, 'read_event_records', side_effect=[security, system]) as reader:
            headers, rows, source = service.eventLogServiceEvents.__wrapped__(_Context())
        self.assertEqual(reader.call_args_list, [mock.call(mock.ANY, 'security.evtx', 'Event Log Service Events', provider='Microsoft-Windows-Eventlog'),
                                                 mock.call(mock.ANY, 'system.evtx', 'Event Log Service Events', provider='Microsoft-Windows-Eventlog')])
        self.assertEqual([(row[1], row[6], row[2]) for row in rows], [('Security', '23', '1100'), ('Security', '22', '1101'), ('System', '4', '6000'),
                                                                       ('System', '3', '9999')])
        self.assertEqual(source, SECURITY + '\n' + SYSTEM)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Log', 'Event ID', 'Event', 'Fields', 'User SID', 'Record ID',
                                   'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(service, 'read_event_records', return_value=([], [])):
            self.assertEqual(service.eventLogServiceEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
