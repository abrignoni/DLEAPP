"""Pin the rows in scripts/artifacts/windowsTimeServiceEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up host names and addresses from
the documentation ranges); the expected rows are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsTimeServiceEvents as wts  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'
SOURCE = 'time.example.com,0x9 (ntp.m|0x9|0.0.0.0:123->192.0.2.7:123)'


def record(when, record_id, event_id, fields):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Time-Service" '
           f'Guid="{{06edcfeb-0fd0-4e53-acca-a6f8bbf81bcb}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1000" ThreadID="2000"></Execution>'
           f'<Channel>System</Channel><Computer>LAB-PC</Computer><Security UserID="S-1-5-19"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
E34 = 'The time service has detected that the system time needs to be changed'
E35 = 'The time service is now synchronizing the system time with the time source'
E37 = 'The time provider NtpClient is currently receiving valid time data'
E52 = 'The time service has set the time with offset'
E129 = 'NtpClient was unable to set a domain peer to use as a time source because of discovery error'
E134 = 'NtpClient was unable to set a manual peer to use as a time source because of DNS resolution error'
E158 = 'The time provider has indicated that the current hardware and operating environment is not supported and has stopped'


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_synchronizing_record_carries_its_source_reference_id_and_stratum(self):
        fields = [('TimeSource', SOURCE), ('TimeSourceRefId', '857771315'), ('CurrentStratumNumber', '3')]
        self.assertEqual(wts.time_service_row(record(WHEN, '11', '35', fields)),
                         (TIME, '35', E35, SOURCE, '857771315', '3', '', '', '', '', '11', 'LAB-PC'))

    def test_a_receiving_record_carries_only_its_source(self):
        self.assertEqual(wts.time_service_row(record(WHEN, '12', '37', [('TimeSource', SOURCE)])),
                         (TIME, '37', E37, SOURCE, '', '', '', '', '', '', '12', 'LAB-PC'))

    def test_a_change_too_large_record_carries_both_numbers_of_seconds_and_its_source(self):
        fields = [('SystemTimeChangeSeconds', '86400'), ('MaxSystemTimeChangeSeconds', '54000'), ('TimeSource', SOURCE)]
        self.assertEqual(wts.time_service_row(record(WHEN, '13', '34', fields)),
                         (TIME, '34', E34, SOURCE, '', '', '86400', '54000', '', '', '13', 'LAB-PC'))

    def test_a_time_set_record_carries_its_offset(self):
        self.assertEqual(wts.time_service_row(record(WHEN, '14', '52', [('TimeOffsetSeconds', '-7200')])),
                         (TIME, '52', E52, '', '', '', '-7200', '', '', '', '14', 'LAB-PC'))

    def test_the_seconds_column_takes_only_the_field_of_its_own_event(self):
        both = [('SystemTimeChangeSeconds', '5'), ('TimeOffsetSeconds', '9'), ('TimeSource', SOURCE)]
        self.assertEqual(wts.time_service_row(record(WHEN, '15', '34', both))[6], '5')
        self.assertEqual(wts.time_service_row(record(WHEN, '15', '52', both))[6], '9')
        self.assertEqual(wts.time_service_row(record(WHEN, '15', '35', both))[6], '')

    def test_the_peer_errors_carry_the_error_the_retry_minutes_and_for_134_the_peer(self):
        fields = [('ErrorMessage', 'No such host is known. (0x80072AF9)'), ('RetryMinutes', '15'),
                  ('DomainPeer', 'time.example.com,0x9')]
        self.assertEqual(wts.time_service_row(record(WHEN, '16', '134', fields)),
                         (TIME, '134', E134, 'time.example.com,0x9', '', '', '', '',
                          'No such host is known. (0x80072AF9)', '15', '16', 'LAB-PC'))
        self.assertEqual(wts.time_service_row(record(WHEN, '17', '129', fields[:2] + [('TimeSource', 'x')])),
                         (TIME, '129', E129, '', '', '', '', '', 'No such host is known. (0x80072AF9)', '15', '17',
                          'LAB-PC'))

    def test_a_provider_stopped_record_names_the_provider(self):
        fields = [('TimeProvider', 'ExampleTimeProvider'), ('TimeSource', 'not this'), ('DomainPeer', 'nor this')]
        self.assertEqual(wts.time_service_row(record(WHEN, '18', '158', fields)),
                         (TIME, '158', E158, 'ExampleTimeProvider', '', '', '', '', '', '', '18', 'LAB-PC'))

    def test_the_source_column_takes_only_the_field_of_its_own_event(self):
        fields = [('TimeProvider', 'P'), ('TimeSource', 'S'), ('DomainPeer', 'D')]
        events = ('34', '35', '37', '52', '129', '134', '158')
        self.assertEqual([wts.time_service_row(record(WHEN, '19', e, fields))[3] for e in events],
                         ['S', 'S', 'S', '', '', 'D', 'P'])

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(wts.time_service_row(record(WHEN, '20', '35', [])),
                         (TIME, '35', E35, '', '', '', '', '', '', '', '20', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_seven_events_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '37', [('TimeSource', SOURCE)]), record(WHEN, '21', '52', [('TimeOffsetSeconds', '3')]),
                  record(WHEN, '23', '158', [('TimeProvider', 'P')])], [LOG])
        with mock.patch.object(wts, 'read_event_records', return_value=found) as reader:
            headers, rows, source = wts.windowsTimeServiceEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'Windows Time Service Events',
                                       event_ids={'34', '35', '37', '52', '129', '134', '158'},
                                       provider='Microsoft-Windows-Time-Service')
        self.assertEqual([(row[10], row[1]) for row in rows], [('22', '37'), ('21', '52'), ('23', '158')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Source, Peer or Provider',
                                   'Reference ID (as stored)', 'Stratum', 'Seconds', 'Limit Seconds', 'Error',
                                   'Retry Minutes', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        with mock.patch.object(wts, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(wts.windowsTimeServiceEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(wts, 'read_event_records', return_value=([], [])):
            self.assertEqual(wts.windowsTimeServiceEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
