"""Pin the rows in scripts/artifacts/windowsNtfsUsnJournalEvents.py.

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

from scripts.artifacts import windowsNtfsUsnJournalEvents as usn  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Ntfs%4Operational.evtx'
TIME = datetime.datetime(2020, 9, 18, 5, 41, 8, 814125, tzinfo=datetime.timezone.utc)
VOLUME = '{26f70db0-0000-1111-2222-4cb89f106ac5}'


def record(record_id, event_id, fields):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Ntfs" '
           f'Guid="{{3ff37a1c-a68d-4d6e-8c9b-f79e8b16c482}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2020-09-18 05:41:08.814125+00:00">'
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
    def test_a_journal_created_on_build_19041(self):
        row = usn.journal_row(record('1', '500', [('ProcessName', 'System'), ('VolumeCorrelationId', VOLUME), ('VolumeNameLength', '2'),
                                                  ('VolumeName', 'C:'), ('MaximumSize', '0x0000000000400000'),
                                                  ('AllocationDelta', '0x0000000000100000')]))
        self.assertEqual(row, (TIME, '500', 'A process has created a USN journal on a volume.', 'System', 'C:', '',
                               '0x0000000000400000', '0x0000000000100000', '', VOLUME, '1', 'LAB-PC'))

    def test_a_journal_deleted_on_build_22621_names_its_journal_and_usn(self):
        row = usn.journal_row(record('28', '501', [('ProcessName', 'SearchIndexer.'), ('VolumeCorrelationId', VOLUME), ('VolumeNameLength', '2'),
                                                   ('VolumeName', 'C:'), ('JournalId', '0x01d8f5e7e67636d0'), ('CurrentUsn', '0x0000000000000000')]))
        self.assertEqual(row[2:10], ('A process has deleted a USN journal on a volume.', 'SearchIndexer.', 'C:', '0x01d8f5e7e67636d0', '', '',
                                     '0x0000000000000000', VOLUME))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_500_and_501_of_the_provider(self):
        with mock.patch.object(usn, 'read_event_records', return_value=([record('9', '501', [('ProcessName', 'x')])], [LOG])) as reader:
            headers, rows, source = usn.ntfsUsnJournalEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Ntfs%4Operational.evtx', 'NTFS USN Journal Events',
                                       event_ids={'500', '501'}, provider='Microsoft-Windows-Ntfs')
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Process Name', 'Volume Name', 'Journal ID',
                                   'Maximum Size', 'Allocation Delta', 'Current USN', 'Volume ID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(usn, 'read_event_records', return_value=([], [])):
            self.assertEqual(usn.ntfsUsnJournalEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
