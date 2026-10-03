"""Pin the rows in scripts/artifacts/windowsUpdateOperationalEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up update titles and values);
the expected rows and the whole Event ID table are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsUpdateOperationalEvents as wuop  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-WindowsUpdateClient%4Operational.evtx'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
UPDATE = '{0a1b2c3d-1111-2222-3333-444455556666}'
SERVICE = '{11111111-2222-3333-4444-555555555555}'


def record(record_id, event_id, fields, user='S-1-5-18'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-WindowsUpdateClient" '
           f'Guid="{{945a8954-c147-4acd-923f-40c45405a658}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>1</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-WindowsUpdateClient/Operational</Channel><Computer>LAB-PC</Computer>{security}'
           f'</System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_download_record_has_the_title_the_update_id_and_the_revision(self):
        fields = [('updateTitle', ' Sample Update (KB0000001) '), ('updateGuid', UPDATE), ('updateRevisionNumber', ' 200 ')]
        self.assertEqual(wuop.update_row(record('7', '41', fields)),
                         (TIME, '41', 'An update was downloaded.', 'Sample Update (KB0000001)', UPDATE, '200', '', '', '', '',
                          'S-1-5-18', '7', 'LAB-PC'))

    def test_a_scan_record_has_the_count_and_the_service(self):
        row = wuop.update_row(record('8', '26', [('updateCount', '3'), ('serviceGuid', SERVICE)], user=''))
        self.assertEqual(row[1:], ('26', 'Windows Update successfully found %1 updates.', '', '', '', SERVICE, '3', '', '', '', '8', 'LAB-PC'))

    def test_the_shown_columns_follow_their_own_order_whatever_the_record_order(self):
        fields = [('errorCode', 'E'), ('serviceGuid', 'S'), ('updateCount', 'C'), ('updateRevisionNumber', 'R'), ('updateGuid', 'G'),
                  ('updateTitle', 'T')]
        self.assertEqual(wuop.update_row(record('9', '31', fields))[3:10], ('T', 'G', 'R', 'S', 'C', 'E', ''))

    def test_other_fields_are_listed_in_record_order_without_the_empty_ones(self):
        fields = [('hc_stateid', '2'), ('restartDate', ''), ('restartTime', ' 0 '), ('Blank', '  '), ('Text', 'a\nb  c')]
        row = wuop.update_row(record('10', '42', fields))
        self.assertEqual(row[2:10], ('There has been a change in the health of Windows Update.', '', '', '', '', '', '',
                                     'hc_stateid: 2 | restartTime: 0 | Text: a\nb  c'))

    def test_a_record_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(wuop.update_row(record('11', '29', []))[2:10], ('Windows Update lost connectivity.', '', '', '', '', '', '', ''))
        row = wuop.update_row(record('12', '9999', [('Extra', 'kept'), ('updateTitle', 'T')]))
        self.assertEqual((row[1], row[2], row[3], row[9]), ('9999', '', 'T', 'Extra: kept'))

    def test_the_table_holds_the_events_of_the_operational_channel(self):
        self.assertEqual(wuop._EVENTS, {  # pylint: disable=protected-access
            '25': 'Windows Update failed to check for updates with error %1.',
            '26': 'Windows Update successfully found %1 updates.',
            '29': 'Windows Update lost connectivity.',
            '30': 'Windows Update established connectivity.',
            '31': 'Windows Update failed to download an update.',
            '34': 'The Windows Update Client Core component failed to install a self-update with error %1.',
            '35': 'The Windows Update Client Auxillary component failed to install a self-update with error %1.',
            '36': 'The Windows Update Client Core component was successfully updated from version %1 to version %2.',
            '37': 'The Windows Update Client Auxillary was successfully updated from version %1 to version %2.',
            '38': 'Windows Update received a service stop request.',
            '39': 'Windows Update received a service shutdown request.',
            '40': 'An update was detected.',
            '41': 'An update was downloaded.',
            '42': 'There has been a change in the health of Windows Update.',
        })


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Update Title', 'Update ID', 'Revision Number', 'Service ID',
               'Update Count', 'Error Code (as stored)', 'Other Fields', 'User SID', 'Record ID', 'Computer')

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '41', [('updateTitle', 'B')]), record('21', '26', [('updateCount', '1')]), record('22', '41', [('updateTitle', 'A')]),
                   record('24', '9999', [])]
        with mock.patch.object(wuop, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = wuop.windowsUpdateOperationalEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-WindowsUpdateClient%4Operational.evtx', 'Windows Update Operational Events',
                                       provider='Microsoft-Windows-WindowsUpdateClient')
        self.assertEqual([(row[11], row[1], row[3], row[7]) for row in rows], [('23', '41', 'B', ''), ('21', '26', '', '1'), ('22', '41', 'A', ''), ('24', '9999', '', '')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(wuop, 'read_event_records', return_value=([record('1', '29', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(wuop.windowsUpdateOperationalEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(wuop, 'read_event_records', return_value=([], [])):
            self.assertEqual(wuop.windowsUpdateOperationalEvents.__wrapped__(_Context()), (self.HEADERS, [], ''))


if __name__ == '__main__':
    unittest.main()
