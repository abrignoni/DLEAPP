"""Pin the rows in scripts/artifacts/windowsTimeServiceOperational.py.

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

from scripts.artifacts import windowsTimeServiceOperational as timesvc  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Time-Service%4Operational.evtx'
UTC = datetime.timezone.utc
SERVER = 'time.example.org,0x9 (ntp.m|0x9|10.0.0.5:123->203.0.113.7:123)'


def record(record_id, event_id, fields, user='S-1-5-19'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Time-Service" '
           f'Guid="{{06edcfeb-0fd0-4e53-acca-a6f8bbf81bcb}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="700" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-Time-Service/Operational</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


def time_set(record_id, new='2023-01-03T17:29:35.499Z', old='2023-01-03T17:29:31.25Z'):
    return record(record_id, '261', [('NewTime', new), ('OldTime', old), ('TickCount', '123456')])


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=UTC)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class UtcTimeTest(unittest.TestCase):
    def test_a_time_text_is_read_as_utc_with_three_digits_of_milliseconds(self):
        self.assertEqual(timesvc.utc_time('2023-01-03T17:29:35.499Z'),
                         datetime.datetime(2023, 1, 3, 17, 29, 35, 499000, tzinfo=UTC))

    def test_fewer_digits_are_milliseconds_written_without_leading_zeros_and_none_is_a_whole_second(self):
        self.assertEqual(timesvc.utc_time('2023-01-03T17:29:35.5Z'), datetime.datetime(2023, 1, 3, 17, 29, 35, 5000, tzinfo=UTC))
        self.assertEqual(timesvc.utc_time('2023-01-03T17:29:35.45Z'), datetime.datetime(2023, 1, 3, 17, 29, 35, 45000, tzinfo=UTC))
        self.assertEqual(timesvc.utc_time('2023-01-03T17:29:35.0Z'), datetime.datetime(2023, 1, 3, 17, 29, 35, tzinfo=UTC))
        self.assertEqual(timesvc.utc_time('2023-01-03T17:29:35.050Z'), datetime.datetime(2023, 1, 3, 17, 29, 35, 50000, tzinfo=UTC))
        self.assertEqual(timesvc.utc_time('2001-12-31T00:00:09Z'), datetime.datetime(2001, 12, 31, 0, 0, 9, tzinfo=UTC))

    def test_other_texts_are_not_times(self):
        for text in ('', '2023-01-03 17:29:35.5Z', '2023-01-03T17:29:35.5', '2023-01-03T17:29:35.5+00:00', '2023-13-03T17:29:35Z',
                     '2023-02-30T17:29:35Z', '2023-01-03T24:29:35Z', '2023-01-03T17:29:35.1234Z', '2023-01-03T17:29:35.0123Z',
                     'x2023-01-03T17:29:35Z',
                     '2023-01-03T17:29:35Zx', '2023-01-03T17:29:35.Z', '23-01-03T17:29:35Z'):
            self.assertIsNone(timesvc.utc_time(text), text)


class RowTest(unittest.TestCase):
    def test_a_time_set_record_has_both_times_and_the_tick_count_among_the_other_fields(self):
        self.assertEqual(timesvc.time_service_row(time_set('7')),
                         (TIME, datetime.datetime(2023, 1, 3, 17, 29, 35, 499000, tzinfo=UTC),
                          datetime.datetime(2023, 1, 3, 17, 29, 31, 25000, tzinfo=UTC), '261',
                          'W32time service has set the system time to %1(UTC).', '', '', '', 'TickCount: 123456', 'S-1-5-19',
                          '7', 'LAB-PC'))

    def test_a_time_field_that_does_not_read_as_a_time_is_blank_and_kept_among_the_other_fields(self):
        row = timesvc.time_service_row(time_set('8', new='soon', old=''))
        self.assertEqual(row[1:3], ('', ''))
        self.assertEqual(row[8], 'NewTime: soon | TickCount: 123456')
        row = timesvc.time_service_row(time_set('9', new='2023-01-03T17:29:35Z', old='1601'))
        self.assertEqual(row[1:3], (datetime.datetime(2023, 1, 3, 17, 29, 35, tzinfo=UTC), ''))
        self.assertEqual(row[8], 'OldTime: 1601 | TickCount: 123456')

    def test_white_space_around_a_time_text_is_not_part_of_it(self):
        row = timesvc.time_service_row(time_set('10', new=' 2023-01-03T17:29:35.499Z\n',
                                                     old='\t2023-01-03T17:29:31.25Z '))
        self.assertEqual(row[1:3], (datetime.datetime(2023, 1, 3, 17, 29, 35, 499000, tzinfo=UTC),
                                    datetime.datetime(2023, 1, 3, 17, 29, 31, 25000, tzinfo=UTC)))
        self.assertEqual(row[8], 'TickCount: 123456')

    def test_the_source_and_server_fields_have_their_columns(self):
        fields = [('AllNtpServers', f' {SERVER}; '), ('ChosenReferenceNtpServer', SERVER + ' (RefID:0x1)'), ('TickCount', '5'),
                  ('IFTSTMP', '1')]
        row = timesvc.time_service_row(record('10', '259', fields))
        self.assertEqual(row[1:9], ('', '', '259', 'NTP Client provider periodic status:', '', SERVER + ';',
                                    SERVER + ' (RefID:0x1)', 'TickCount: 5 | IFTSTMP: 1'))
        row = timesvc.time_service_row(record('11', '265', [('TimeSource', SERVER), ('TimeSourceRefId', '0x1'),
                                                             ('LocalStratumNumber', '4'), ('TickCount', '6')]))
        self.assertEqual(row[5:9], (SERVER, '', '', 'TimeSourceRefId: 0x1 | LocalStratumNumber: 4 | TickCount: 6'))

    def test_other_fields_are_listed_in_record_order_without_the_empty_ones_and_keep_inner_line_breaks(self):
        fields = [('TimeProviders', 'NtpClient (Local)\nEnabled: 1'), ('Blank', '   '), ('Empty', ''), ('Configuration', 'a:  1'),
                  ('TickCount', ' 9\n')]
        row = timesvc.time_service_row(record('12', '263', fields, user=''))
        self.assertEqual(row[4], 'W32time Service configuration parameters have been updated.')
        self.assertEqual(row[8], 'TimeProviders: NtpClient (Local)\nEnabled: 1 | Configuration: a:  1 | TickCount: 9')
        self.assertEqual(row[9], '')

    def test_an_event_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(timesvc.time_service_row(record('13', '267', []))[1:9],
                         ('', '', '267', 'NTP provider is receiving timestamps from the network stack.', '', '', '', ''))
        row = timesvc.time_service_row(record('14', '9999', [('Extra', 'kept')]))
        self.assertEqual((row[3], row[4], row[8]), ('9999', '', 'Extra: kept'))

    def test_the_table_holds_the_twenty_two_events_of_the_operational_channel(self):
        self.assertEqual(timesvc._EVENTS, {  # pylint: disable=protected-access
            '257': 'W32time service has started at %1 (UTC), System Tick Count %2.',
            '258': 'W32time service is stopping at %1 (UTC), System Tick Count %2 with return code: %3',
            '259': 'NTP Client provider periodic status:',
            '260': 'W32time Service periodic configuration and status message',
            '261': 'W32time service has set the system time to %1(UTC).',
            '262': 'W32time service has adjusted the system clock rate by %1 PPM and the new nominal clock rate is %2.',
            '263': 'W32time Service configuration parameters have been updated.',
            '264': 'NTP Client observed a change peer reachability.',
            '265': ('The time service is now synchronizing the system time with the reference time source %1 with '
                    'reference id %2.'),
            '266': 'W32time Service received notification to rediscover its time sources and/or resynchronize time.',
            '267': 'NTP provider is receiving timestamps from the network stack.',
            '268': ('NTP provider is not receiving any timestamps from the network stack, which may result in lowered '
                    'time sync accuracy.'),
            '272': 'Leap second configuration:',
            '273': 'A leap second will be %1 at %2 UTC (%3 local time).',
            '274': 'The time provider %4 has signaled a leap second should be %1 at %2 UTC (%3 local time).',
            '275': 'Per configuration, W32time service attempted to add a leap second %1 UTC to local settings.',
            '276': 'The local system data indicates that a leap second will be %1 at %2 UTC (%3 local time).',
            '279': 'W32time could not update the local system time data on leap seconds.',
            '281': 'The local system clock requires a frequency correction of approximately %1 parts per million (PPM).',
            '282': ('The local system clock required an average frequency correction of %1 parts per million (PPM) '
                    'over the past %2 minutes.'),
            '283': 'Inconsistent timekeeping or a time jump has been detected.',
            '284': 'Secure time message: %1',
        })


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [time_set('23'), record('21', '266', [('ReasonCode', '0')]), time_set('22'), record('24', '9999', [])]
        with mock.patch.object(timesvc, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = timesvc.timeServiceOperationalEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Time-Service%4Operational.evtx',
                                       'Time Service Operational Events', provider='Microsoft-Windows-Time-Service')
        self.assertEqual([(row[10], row[3]) for row in rows], [('23', '261'), ('21', '266'), ('22', '261'), ('24', '9999')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), ('New Time (UTC)', 'datetime'),
                                   ('Old Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Time Source', 'NTP Servers',
                                   'Reference NTP Server', 'Other Fields', 'User SID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(timesvc, 'read_event_records', return_value=([time_set('1')], [LOG, LOG + '.copy'])):
            self.assertEqual(timesvc.timeServiceOperationalEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(timesvc, 'read_event_records', return_value=([], [])):
            self.assertEqual(timesvc.timeServiceOperationalEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
