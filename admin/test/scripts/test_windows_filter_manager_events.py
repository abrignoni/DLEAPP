"""Pin the rows in scripts/artifacts/windowsFilterManagerEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up filter and volume names); the
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

from scripts.artifacts import windowsFilterManagerEvents as flt  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'


def record(when, record_id, event_id, fields, provider='Microsoft-Windows-FilterManager'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{f3c5e28e-63f6-49c7-a204-e48a1bc4b09d}}">'
           f'</Provider><EventID>{event_id}</EventID><Version>0</Version><Level>4</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="4" ThreadID="8"></Execution><Channel>System</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-18"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
FILTER = [('FinalStatus', '0x00000000'), ('DeviceVersionMajor', '10'), ('DeviceVersionMinor', '3'),
          ('DeviceNameLength', '9'), ('DeviceName', 'ExampleFs'), ('DeviceTime', '2041-01-31 00:18:31+00:00')]
VOLUME = [('FinalStatus', '0xc03a001c'), ('ExtraStringLength', '23'), ('ExtraString', '\\Device\\HarddiskVolume9')]


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_filter_loaded_record(self):
        self.assertEqual(flt.filter_row(record(WHEN, '11', '6', FILTER)),
                         (TIME, '6', 'File System Filter has successfully loaded and registered with Filter Manager',
                          'ExampleFs', '10.3', '2041-01-31 00:18:31+00:00', '', '0x00000000', '11', 'LAB-PC'))

    def test_a_volume_record_has_no_filter_columns(self):
        self.assertEqual(flt.filter_row(record(WHEN, '12', '3', VOLUME)),
                         (TIME, '3', 'Filter Manager failed to attach to volume', '', '', '',
                          '\\Device\\HarddiskVolume9', '0xc03a001c', '12', 'LAB-PC'))

    def test_a_record_with_filter_and_volume_fields_fills_both(self):
        row = flt.filter_row(record(WHEN, '13', '4', FILTER + VOLUME[1:]))
        self.assertEqual(row[1:8], ('4', 'File System Filter failed to attach to volume', 'ExampleFs', '10.3',
                                    '2041-01-31 00:18:31+00:00', '\\Device\\HarddiskVolume9', '0x00000000'))

    def test_every_event_id_has_its_own_text(self):
        expected = {
            '1': 'File System Filter unloaded successfully',
            '2': 'Name caching for File System Filters has been disabled on volume',
            '3': 'Filter Manager failed to attach to volume',
            '4': 'File System Filter failed to attach to volume',
            '5': 'File System Filter failed to register with Filter Manager',
            '6': 'File System Filter has successfully loaded and registered with Filter Manager',
            '7': 'File System Filter failed to start filtering',
            '8': 'Filter Manager successfully attached to volume',
            '9': 'Filter Manager failed to attach to file system control device object (CDO)',
            '10': 'Filter Manager successfully attached to file system',
        }
        for event_id, text in expected.items():
            self.assertEqual(flt.filter_row(record(WHEN, '14', event_id, []))[1:3], (event_id, text))

    def test_the_version_is_major_dot_minor_and_blank_when_neither_is_stored(self):
        self.assertEqual(flt.filter_version(record(WHEN, '15', '6', FILTER)), '10.3')
        zero = [('DeviceVersionMajor', '0'), ('DeviceVersionMinor', '0')]
        self.assertEqual(flt.filter_version(record(WHEN, '15', '6', zero)), '0.0')
        self.assertEqual(flt.filter_version(record(WHEN, '15', '6', [('DeviceVersionMajor', '2')])), '2.')
        self.assertEqual(flt.filter_version(record(WHEN, '15', '6', [('DeviceVersionMinor', '7')])), '.7')
        self.assertEqual(flt.filter_version(record(WHEN, '15', '3', VOLUME)), '')

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(flt.filter_row(record(WHEN, '16', '1', [])),
                         (TIME, '1', 'File System Filter unloaded successfully', '', '', '', '', '', '16', 'LAB-PC'))

    def test_the_length_fields_are_not_used(self):
        fields = [('DeviceNameLength', '3'), ('DeviceName', 'ExampleFs'), ('ExtraStringLength', '2'), ('ExtraString', 'NTFS')]
        self.assertEqual(flt.filter_row(record(WHEN, '17', '4', fields))[3:8], ('ExampleFs', '', '', 'NTFS', ''))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_events_1_to_10_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '6', FILTER), record(WHEN, '21', '3', VOLUME), record(WHEN, '23', '1', FILTER)], [LOG])
        with mock.patch.object(flt, 'read_event_records', return_value=found) as reader:
            headers, rows, source = flt.fileSystemFilterEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'File System Filter Events',
                                       event_ids={'1', '2', '3', '4', '5', '6', '7', '8', '9', '10'},
                                       provider='Microsoft-Windows-FilterManager')
        self.assertEqual([(row[8], row[1]) for row in rows], [('22', '6'), ('21', '3'), ('23', '1')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Filter Name',
                                   'Filter Version', 'Filter Time (as stored)', 'Volume or File System',
                                   'Final Status (as stored)', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        with mock.patch.object(flt, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(flt.fileSystemFilterEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(flt, 'read_event_records', return_value=([], [])):
            self.assertEqual(flt.fileSystemFilterEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
