"""Pin the rows in scripts/artifacts/windowsNcsiEvents.py.

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

from scripts.artifacts import windowsNcsiEvents as ncsi  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-NCSI%4Operational.evtx'
GUID = '{0a1b2c3d-1111-2222-3333-444455556666}'
TEXT_4042 = 'Capability change on %1 (%2 Family: %3 Capability: %4 ChangeReason: %5)'


def record(record_id, event_id, fields, user='S-1-5-20'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-NCSI" '
           f'Guid="{{314de49f-ce63-4779-ba2b-d616f6963a88}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1200" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-NCSI/Operational</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


def change(record_id, family='1', capability='2', reason='4', previous='0'):
    return record(record_id, '4042', [('InterfaceGuid', GUID), ('IfLuid', '19985273102270464'), ('Family', family),
                                      ('Capability', capability), ('CapabilityChangeReason', reason),
                                      ('PreviousCapability', previous)])


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_capability_change_has_its_six_fields_under_their_columns(self):
        self.assertEqual(ncsi.connectivity_row(change('7', family='1', capability='2', reason='4', previous='0')),
                         (TIME, '4042', TEXT_4042, GUID, '19985273102270464', '1', '2', '0', '4', '', 'S-1-5-20', '7', 'LAB-PC'))

    def test_the_numbers_are_shown_as_stored_with_no_name(self):
        row = ncsi.connectivity_row(change('8', family='0', capability='1', reason='13', previous='2'))
        self.assertEqual(row[5:9], ('0', '1', '2', '13'))

    def test_white_space_at_either_end_of_a_value_is_removed_and_a_record_with_no_user_has_a_blank_user(self):
        row = ncsi.connectivity_row(record('9', '4042', [('InterfaceGuid', f' {GUID} '), ('IfLuid', '5\n'), ('Family', ' 0')], user=''))
        self.assertEqual(row[3:10], (GUID, '5', '0', '', '', '', ''))
        self.assertEqual(row[10], '')

    def test_another_event_keeps_the_shared_columns_and_lists_its_other_fields_in_record_order(self):
        fields = [('IfLuid', '5'), ('ProbePath', 'p  q'), ('InterfaceGuid', GUID), ('ErrorCode', ' 7 '), ('Blank', '   '),
                  ('Empty', ''), ('ErrorString', 'x')]
        row = ncsi.connectivity_row(record('10', '4012', fields))
        self.assertEqual(row[1:3], ('4012', 'Inside/Outside probe failed for interface %1.'))
        self.assertEqual(row[3:9], (GUID, '5', '', '', '', ''))
        self.assertEqual(row[9], 'ProbePath: p  q | ErrorCode: 7 | ErrorString: x')

    def test_an_event_id_outside_the_table_has_a_blank_event_and_keeps_its_fields(self):
        row = ncsi.connectivity_row(record('11', '9999', [('Extra', 'kept')]))
        self.assertEqual((row[1], row[2], row[9]), ('9999', '', 'Extra: kept'))

    def test_the_table_holds_the_seven_events_of_the_operational_channel(self):
        events = ncsi._EVENTS  # pylint: disable=protected-access
        self.assertEqual(sorted(events), ['4009', '4010', '4011', '4012', '4028', '4038', '4042'])
        self.assertEqual(events['4042'], TEXT_4042)
        self.assertEqual(events['4011'], 'Windows Firewall Group Policy settings have been updated.')
        self.assertEqual(events['4028'], 'Inside/Outside detection is suspect')


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [change('23'), record('21', '4038', [('IfLuid', '5'), ('Family', '0')]), change('22', capability='0'),
                   record('24', '9999', [])]
        with mock.patch.object(ncsi, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = ncsi.networkConnectivityEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-NCSI%4Operational.evtx', 'Network Connectivity Status Events',
                                       provider='Microsoft-Windows-NCSI')
        self.assertEqual([(row[11], row[1]) for row in rows], [('23', '4042'), ('21', '4038'), ('22', '4042'), ('24', '9999')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Interface GUID', 'Interface LUID',
                                   'Family', 'Capability', 'Previous Capability', 'Change Reason', 'Other Fields', 'User SID',
                                   'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(ncsi, 'read_event_records', return_value=([change('1')], [LOG, LOG + '.copy'])):
            self.assertEqual(ncsi.networkConnectivityEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(ncsi, 'read_event_records', return_value=([], [])):
            self.assertEqual(ncsi.networkConnectivityEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
