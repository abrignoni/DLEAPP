"""Pin the rows in scripts/artifacts/windowsKernelBootEvents.py.

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

from scripts.artifacts import windowsKernelBootEvents as boot  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'


def record(record_id, event_id, fields, version='0', unnamed=(), user='S-1-5-18'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    data += ''.join(f'<Data>{value}</Data>' for value in unnamed)
    user = f' UserID="{user}"' if user else ''
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Kernel-Boot" '
           f'Guid="{{15ca44ff-4d7a-4baa-bba5-0998955e531e}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="8"></Execution>'
           f'<Channel>System</Channel><Computer>LAB-PC</Computer><Security{user}></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_boot_type_record_carries_the_type_as_stored_and_the_load_options(self):
        fields = [('BootType', '2'), ('LoadOptions', ' NOEXECUTE=OPTIN  FVEBOOT=1')]
        self.assertEqual(boot.boot_row(record('7', '27', fields, version='1')),
                         (TIME, '27', 'The boot type was %1.', '2', 'NOEXECUTE=OPTIN  FVEBOOT=1', '', '', '', 'S-1-5-18', '7',
                          'LAB-PC'))
        self.assertEqual(boot.boot_row(record('8', '27', [('BootType', '0')]))[3:8], ('0', '', '', '', ''))

    def test_a_last_shutdown_record_carries_both_flags_and_the_rest_in_other_fields(self):
        fields = [('LastShutdownGood', 'False'), ('LastBootGood', 'True'), ('LastBootId', '12'), ('BootStatusPolicy', '2')]
        self.assertEqual(boot.boot_row(record('9', '20', fields, version='1')),
                         (TIME, '20', "The last shutdown's success status was %1.", '', '', 'False', 'True',
                          'LastBootId: 12 | BootStatusPolicy: 2', 'S-1-5-18', '9', 'LAB-PC'))

    def test_other_fields_keeps_record_order_and_leaves_out_empty_and_shown_fields(self):
        fields = [('Zeta', 'z'), ('LoadOptions', 'opts'), ('Empty', ''), ('Blank', '   '), ('Alpha', ' a '), ('BootType', '1')]
        row = boot.boot_row(record('10', '27', fields))
        self.assertEqual(row[3:8], ('1', 'opts', '', '', 'Zeta: z | Alpha: a'))

    def test_the_firmware_metrics_and_the_time_zone_fields_go_to_other_fields(self):
        fields = [('ResetEndStart', '0'), ('LoadOSImageStart', '4166'), ('StartOSImageStart', '4247'),
                  ('ExitBootServicesEntry', '5817'), ('ExitBootServicesExit', '5818')]
        row = boot.boot_row(record('11', '30', fields))
        self.assertEqual(row[2], 'The firmware reported boot metrics.')
        self.assertEqual(row[7], 'ResetEndStart: 0 | LoadOSImageStart: 4166 | StartOSImageStart: 4247 | '
                                 'ExitBootServicesEntry: 5817 | ExitBootServicesExit: 5818')
        zone = [('EfiTimeZoneBias', '2047'), ('EfiDaylightFlags', '0'), ('EfiTime', '2023-01-03 17:29:10+00:00')]
        row = boot.boot_row(record('12', '238', zone, version='1'))
        self.assertEqual(row[2], 'EFI time zone bias: %1.')
        self.assertEqual(row[7], 'EfiTimeZoneBias: 2047 | EfiDaylightFlags: 0 | EfiTime: 2023-01-03 17:29:10+00:00')

    def test_a_record_with_no_fields_keeps_its_time_and_text(self):
        self.assertEqual(boot.boot_row(record('13', '26', [])),
                         (TIME, '26', 'A one-time boot sequence was used during this boot.', '', '', '', '', '', 'S-1-5-18', '13',
                          'LAB-PC'))

    def test_an_event_id_outside_the_table_has_a_blank_event_and_keeps_its_fields(self):
        row = boot.boot_row(record('14', '9999', [('BootType', '0'), ('Extra', 'kept')]))
        self.assertEqual((row[1], row[2], row[3], row[7]), ('9999', '', '0', 'Extra: kept'))

    def test_a_data_item_without_a_name_is_not_shown_and_a_record_without_a_user_has_a_blank_user_sid(self):
        row = boot.boot_row(record('15', '18', [('EntryCount', '1')], unnamed=('loose',), user=''))
        self.assertEqual(row[7:], ('EntryCount: 1', '', '15', 'LAB-PC'))
        self.assertNotIn('loose', ' '.join(str(cell) for cell in row))
        self.assertEqual(len(row), 11)
        self.assertEqual(boot.boot_row(record('16', '18', [], user='S-1-5-21-1-2-3-1001'))[8], 'S-1-5-21-1-2-3-1001')

    def test_the_table_holds_the_34_system_channel_events(self):
        self.assertEqual(len(boot._EVENTS), 34)  # pylint: disable=protected-access
        self.assertEqual(boot._EVENTS['247'], 'Unable to load Pluton-Windows firmware.')  # pylint: disable=protected-access
        self.assertEqual(boot._EVENTS['153'], 'Virtualization-based security (policies: %3) is %2.')  # pylint: disable=protected-access
        self.assertEqual(boot._EVENTS['18'], 'There are %1 boot options on this system.')  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def test_the_system_log_is_read_for_every_record_of_the_provider_in_file_order(self):
        found = ([record('22', '27', [('BootType', '0')]), record('21', '20', []), record('23', '9999', [])], [LOG])
        with mock.patch.object(boot, 'read_event_records', return_value=found) as reader:
            headers, rows, source = boot.kernelBootEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'Kernel Boot Events', provider='Microsoft-Windows-Kernel-Boot')
        self.assertEqual([(row[9], row[1]) for row in rows], [('22', '27'), ('21', '20'), ('23', '9999')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Boot Type (as stored)', 'Load Options',
                                   'Last Shutdown Good', 'Last Boot Good', 'Other Fields', 'User SID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        with mock.patch.object(boot, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(boot.kernelBootEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(boot, 'read_event_records', return_value=([], [])):
            self.assertEqual(boot.kernelBootEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
