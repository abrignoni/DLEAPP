"""Pin the rows in scripts/artifacts/windowsUpdateClientEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up updates); the expected rows
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

from scripts.artifacts import windowsUpdateClientEvents as updates  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'
TITLE = '2023-02 Cumulative Update for Example OS (KB0000001)'
UPDATE = '{0a1b2c3d-0000-4000-8000-00000000000a}'
SERVICE = '{0f0e0d0c-0000-4000-8000-00000000000b}'


def record(event_id, when, record_id, fields, source=LOG, provider='Microsoft-Windows-WindowsUpdateClient'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{945a8954-c147-4acd-923f-40c45405a658}}">'
           f'</Provider><EventID>{event_id}</EventID><Version>1</Version><Level>4</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="1000" ThreadID="2000"></Execution><Channel>System</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-18"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


BASE = [('updateTitle', TITLE), ('updateGuid', UPDATE), ('updateRevisionNumber', '201')]
WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = utc(2023, 2, 20, 22, 16, 15, 500000)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_download_and_an_installation_started(self):
        self.assertEqual(updates.update_row(record('44', WHEN, '7', BASE)),
                         (TIME, '44', 'Windows Update started downloading an update', TITLE, UPDATE, '201', '', '', '7',
                          'LAB-PC'))
        self.assertEqual(updates.update_row(record('43', WHEN, '8', BASE)),
                         (TIME, '43', 'Installation Started', TITLE, UPDATE, '201', '', '', '8', 'LAB-PC'))

    def test_an_installation_that_succeeded_and_one_that_failed(self):
        done = BASE + [('serviceGuid', SERVICE)]
        self.assertEqual(updates.update_row(record('19', WHEN, '9', done)),
                         (TIME, '19', 'Installation Successful', TITLE, UPDATE, '201', SERVICE, '', '9', 'LAB-PC'))
        failed = [('errorCode', '0x80073d02')] + done
        self.assertEqual(updates.update_row(record('20', WHEN, '10', failed)),
                         (TIME, '20', 'Installation Failure', TITLE, UPDATE, '201', SERVICE, '0x80073d02', '10', 'LAB-PC'))

    def test_an_uninstallation_that_succeeded(self):
        done = BASE + [('serviceGuid', SERVICE)]
        self.assertEqual(updates.update_row(record('23', WHEN, '11', done)),
                         (TIME, '23', 'Uninstallation Successful', TITLE, UPDATE, '201', SERVICE, '', '11', 'LAB-PC'))

    def test_a_failed_uninstallation_takes_its_title_from_the_updatelist_field(self):
        fields = [('errorCode', '0x80070002'), ('updatelist', TITLE), ('updateGuid', UPDATE),
                  ('updateRevisionNumber', '201'), ('serviceGuid', SERVICE)]
        self.assertEqual(updates.update_row(record('24', WHEN, '12', fields)),
                         (TIME, '24', 'Uninstallation Failure', TITLE, UPDATE, '201', SERVICE, '0x80070002', '12',
                          'LAB-PC'))
        both = fields + [('updateTitle', 'another title')]
        self.assertEqual(updates.update_row(record('24', WHEN, '12', both))[3], TITLE)

    def test_only_event_24_reads_the_updatelist_field(self):
        fields = [('updatelist', 'a list'), ('updateGuid', UPDATE), ('updateRevisionNumber', '201')]
        for event_id in ('19', '20', '23', '43', '44'):
            self.assertEqual(updates.update_row(record(event_id, WHEN, '13', fields))[3], '', event_id)

    def test_each_field_lands_in_its_own_column(self):
        fields = [('errorCode', 'e'), ('updateTitle', 't'), ('updateGuid', 'g'), ('updateRevisionNumber', 'r'),
                  ('serviceGuid', 's')]
        self.assertEqual(updates.update_row(record('20', WHEN, '14', fields))[3:], ('t', 'g', 'r', 's', 'e', '14', 'LAB-PC'))

    def test_a_value_keeps_its_case_and_inner_spacing_and_loses_white_space_at_its_ends(self):
        fields = [('updateTitle', ' 9ABCDEFGHIJK-Example.App  for  x64 '), ('updateGuid', UPDATE.upper()),
                  ('updateRevisionNumber', '001')]
        row = updates.update_row(record('44', WHEN, '15', fields))
        self.assertEqual(row[3:6], ('9ABCDEFGHIJK-Example.App  for  x64', UPDATE.upper(), '001'))

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(updates.update_row(record('19', '2020-09-18 05:41:31.000000+00:00', '16', [])),
                         (utc(2020, 9, 18, 5, 41, 31), '19', 'Installation Successful', '', '', '', '', '', '16', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_six_events_of_the_provider_and_rows_keep_file_order(self):
        found = ([record('43', WHEN, '8', BASE), record('19', WHEN, '9', BASE), record('44', WHEN, '7', BASE)], [LOG])
        with mock.patch.object(updates, 'read_event_records', return_value=found) as reader:
            headers, rows, source = updates.windowsUpdateClientEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'Windows Update Client Events',
                                       event_ids={'19', '20', '23', '24', '43', '44'},
                                       provider='Microsoft-Windows-WindowsUpdateClient')
        self.assertEqual([row[1] for row in rows], ['43', '19', '44'])
        self.assertEqual([row[8] for row in rows], ['8', '9', '7'])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Update Title', 'Update ID',
                                   'Revision Number', 'Service ID', 'Error Code (as stored)', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        with mock.patch.object(updates, 'read_event_records', return_value=([record('44', WHEN, '7', BASE)], [LOG, other])):
            self.assertEqual(updates.windowsUpdateClientEvents.__wrapped__(_Context())[2], LOG + '\n' + other)
        with mock.patch.object(updates, 'read_event_records', return_value=([], [])):
            self.assertEqual(updates.windowsUpdateClientEvents.__wrapped__(_Context())[1:], ([], ''))

    def test_the_event_words(self):
        self.assertEqual(updates._EVENTS, {  # pylint: disable=protected-access
            '19': 'Installation Successful', '20': 'Installation Failure', '23': 'Uninstallation Successful',
            '24': 'Uninstallation Failure', '43': 'Installation Started',
            '44': 'Windows Update started downloading an update'})


if __name__ == '__main__':
    unittest.main()
