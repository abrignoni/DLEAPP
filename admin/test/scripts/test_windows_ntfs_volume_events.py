"""Pin the rows in scripts/artifacts/windowsNtfsVolumeEvents.py.

The records are built from XML of the shape python-evtx renders for the event (made-up volume names); the expected rows
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

from scripts.artifacts import windowsNtfsVolumeEvents as ntfs  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'


def record(when, record_id, fields, level='4'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Ntfs" Guid="{{3ff37a1c-a68d-4d6e-8c9b-f79e8b16c482}}">'
           f'</Provider><EventID>98</EventID><Version>0</Version><Level>{level}</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="4" ThreadID="8"></Execution><Channel>System</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-18"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
LETTER = [('DriveName', 'Q:'), ('DeviceName', '\\Device\\HarddiskVolume9'), ('CorruptionActionState', '0')]
GUID = [('DriveName', '\\\\?\\Volume{01234567-89ab-cdef-0123-456789abcdef}'), ('DeviceName', '\\Device\\HarddiskVolume12'),
        ('CorruptionActionState', '3')]


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_drive_letter_record(self):
        self.assertEqual(ntfs.volume_row(record(WHEN, '11', LETTER)),
                         (TIME, 'Q:', '\\Device\\HarddiskVolume9', '0', '11', 'LAB-PC'))

    def test_a_volume_guid_record_keeps_its_name_and_state_as_stored(self):
        self.assertEqual(ntfs.volume_row(record(WHEN, '12', GUID, level='2')),
                         (TIME, '\\\\?\\Volume{01234567-89ab-cdef-0123-456789abcdef}', '\\Device\\HarddiskVolume12', '3', '12',
                          'LAB-PC'))

    def test_a_drive_name_of_question_marks_is_kept(self):
        fields = [('DriveName', '??'), ('DeviceName', '\\Device\\HarddiskVolumeShadowCopy4'), ('CorruptionActionState', '0')]
        self.assertEqual(ntfs.volume_row(record(WHEN, '13', fields))[1:4], ('??', '\\Device\\HarddiskVolumeShadowCopy4', '0'))

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(ntfs.volume_row(record(WHEN, '14', [])), (TIME, '', '', '', '14', 'LAB-PC'))

    def test_a_state_that_is_not_a_number_is_kept_as_stored(self):
        fields = [('DriveName', 'Q:'), ('DeviceName', 'x'), ('CorruptionActionState', '0x10')]
        self.assertEqual(ntfs.volume_row(record(WHEN, '15', fields))[3], '0x10')


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_event_98_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', LETTER), record(WHEN, '21', GUID, level='2'), record(WHEN, '23', LETTER)], [LOG])
        with mock.patch.object(ntfs, 'read_event_records', return_value=found) as reader:
            headers, rows, source = ntfs.ntfsVolumeStateEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'NTFS Volume State Events', event_ids={'98'},
                                       provider='Microsoft-Windows-Ntfs')
        self.assertEqual([(row[4], row[3]) for row in rows], [('22', '0'), ('21', '3'), ('23', '0')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Drive Name', 'Device Name',
                                   'Corruption Action State (as stored)', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        with mock.patch.object(ntfs, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(ntfs.ntfsVolumeStateEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(ntfs, 'read_event_records', return_value=([], [])):
            self.assertEqual(ntfs.ntfsVolumeStateEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
