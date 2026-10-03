"""Pin the rows in scripts/artifacts/windowsNtfsDeletionSummaries.py.

The records are built from XML of the shape python-evtx renders for the event (made-up values); the expected rows
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

from scripts.artifacts import windowsNtfsDeletionSummaries as dels  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Ntfs%4Operational.evtx'
TIME = datetime.datetime(2020, 9, 19, 4, 13, 28, 120456, tzinfo=datetime.timezone.utc)
VOLUME = '{26f70db0-0000-1111-2222-4cb89f106ac5}'
COMMON = [('VolumeCorrelationId', VOLUME), ('VolumeNameLength', '2'), ('VolumeName', 'C:'), ('IsBootVolume', 'True')]


def record(record_id, fields):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Ntfs" '
           f'Guid="{{3ff37a1c-a68d-4d6e-8c9b-f79e8b16c482}}"></Provider><EventID>151</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2020-09-19 04:13:28.120456+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Correlation></Correlation>'
           f'<Execution ProcessID="4" ThreadID="8"></Execution><Channel>Microsoft-Windows-Ntfs/Operational</Channel>'
           f'<Computer>LAB-PC</Computer><Security></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_build_19041_record_names_one_process_and_its_count(self):
        row = dels.deletion_row(record('40', COMMON + [('SecondsElapsed', '3604'), ('TotalCountDeleteFile', '8247'),
                                                       ('TotalCountDeleteFileLogged', '8247'), ('ProcessName', 'MicrosoftEdge.'),
                                                       ('CountDeleteFile', '12')]))
        self.assertEqual(row, (TIME, '3604', '8247', '8247', 'MicrosoftEdge.', '12', '', '', '', '', '', '', '',
                               'C:', 'True', VOLUME, '40', 'LAB-PC'))

    def test_a_build_22621_record_carries_the_counts_per_known_folder(self):
        folders = [('CountDeletesInDesktopArray', '9'), ('CountDeletesInDocumentsArray', '1'), ('CountDeletesInDownloadsArray', '2'),
                   ('CountDeletesInMusicArray', '3'), ('CountDeletesInPicturesArray', '4'), ('CountDeletesInVideosArray', '5'),
                   ('CountDeletesInOtherArray', '6')]
        row = dels.deletion_row(record('7', COMMON + [('SecondsElapsed', '3602'), ('TotalCountDeleteFile', '30'),
                                                      ('TotalCountDeleteFileLogged', '29'), ('ProcessNamesArray', 'qemu-system-x8')] + folders))
        self.assertEqual(row, (TIME, '3602', '30', '29', 'qemu-system-x8', '', '9', '1', '2', '3', '4', '5', '6',
                               'C:', 'True', VOLUME, '7', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_151_of_the_provider(self):
        with mock.patch.object(dels, 'read_event_records', return_value=([record('9', COMMON)], [LOG])) as reader:
            headers, rows, source = dels.ntfsDeletionSummaries.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Ntfs%4Operational.evtx', 'NTFS File Deletion Summaries',
                                       event_ids={'151'}, provider='Microsoft-Windows-Ntfs')
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Period (seconds)', 'Files Deleted', 'Deletions With A Process Name',
                                   'Process Names', 'Deleted By The Process', 'Desktop', 'Documents', 'Downloads', 'Music', 'Pictures',
                                   'Videos', 'Other', 'Volume Name', 'Is Boot Volume', 'Volume ID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(dels, 'read_event_records', return_value=([], [])):
            self.assertEqual(dels.ntfsDeletionSummaries.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
