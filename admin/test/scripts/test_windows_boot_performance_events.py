"""Pin the rows in scripts/artifacts/windowsBootPerformanceEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up names and times); the
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

from scripts.artifacts import windowsBootPerformanceEvents as boot  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = ('/case/data/vol1/Windows/System32/winevt/Logs/'
       'Microsoft-Windows-Diagnostics-Performance%4Operational.evtx')
UTC = datetime.timezone.utc


def record(when, record_id, event_id, fields):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Diagnostics-Performance" '
           f'Guid="{{cfc18ec0-96b1-4eba-961b-622caee05b0a}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>2</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1000" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-Diagnostics-Performance/Operational</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="S-1-5-19"></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=UTC)
START = datetime.datetime(2023, 2, 20, 22, 14, 1, 250000, tzinfo=UTC)
END = datetime.datetime(2023, 2, 20, 22, 15, 59, 750000, tzinfo=UTC)
BOOT = [('BootTsVersion', '2'), ('BootStartTime', '2023-02-20 22:14:01.250000+00:00'),
        ('BootEndTime', '2023-02-20 22:15:59.750000+00:00'), ('BootTime', '45049'), ('MainPathBootTime', '16949'),
        ('BootPostBootTime', '28100'), ('BootNumStartupApps', '8'), ('BootIsRebootAfterInstall', 'False'),
        ('BootIsDegradation', 'True'), ('ShutdownTime', '1'), ('ShutdownIsDegradation', 'False')]
SHUTDOWN = [('ShutdownTsVersion', '1'), ('ShutdownStartTime', '2023-02-20 22:14:01.250000+00:00'),
            ('ShutdownEndTime', '2023-02-20 22:15:59.750000+00:00'), ('ShutdownTime', '3508'),
            ('ShutdownIsDegradation', 'False'), ('BootTime', '1'), ('BootIsDegradation', 'True')]
SLOW = [('StartTime', '2023-02-20 22:14:01.250000+00:00'), ('NameLength', '12'), ('Name', 'example.exe'),
        ('FriendlyNameLength', '13'), ('FriendlyName', 'Example Tool'), ('VersionLength', '8'), ('Version', '1.2.3.4'),
        ('TotalTime', '4956'), ('DegradationTime', '956'), ('PathLength', '24'), ('Path', 'C:\\Tools\\example.exe'),
        ('ProductNameLength', '8'), ('ProductName', 'Example'), ('CompanyNameLength', '12'),
        ('CompanyName', 'Example Corp')]


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class PerformanceRowTest(unittest.TestCase):
    def test_a_start_up_record_carries_its_boot_fields(self):
        self.assertEqual(boot.performance_row(record(WHEN, '11', '100', BOOT)),
                         (TIME, START, END, '100', 'Windows has started up', '45049', '16949', '28100', 'True', '8', 'False',
                          '11', 'LAB-PC'))

    def test_a_shutdown_record_carries_its_shutdown_fields_and_no_boot_only_ones(self):
        self.assertEqual(boot.performance_row(record(WHEN, '12', '200', SHUTDOWN)),
                         (TIME, START, END, '200', 'Windows has shutdown', '3508', '', '', 'False', '', '', '12', 'LAB-PC'))

    def test_a_time_that_does_not_parse_or_is_missing_is_blank(self):
        fields = [('BootStartTime', 'not a time'), ('BootTime', '10')]
        self.assertEqual(boot.performance_row(record(WHEN, '13', '100', fields))[1:6],
                         ('', '', '100', 'Windows has started up', '10'))
        self.assertEqual(boot.performance_row(record(WHEN, '14', '200', []))[1:13],
                         ('', '', '200', 'Windows has shutdown', '', '', '', '', '', '', '14', 'LAB-PC'))


class DelayRowTest(unittest.TestCase):
    def test_a_delay_record_with_a_file_carries_every_field(self):
        self.assertEqual(boot.delay_row(record(WHEN, '21', '203', SLOW)),
                         (TIME, START, '203', 'This service caused a delay in the system shutdown process', 'example.exe',
                          'Example Tool', '1.2.3.4', '4956', '956', 'C:\\Tools\\example.exe', 'Example', 'Example Corp', '21',
                          'LAB-PC'))

    def test_a_delay_record_with_only_a_name_leaves_the_file_columns_blank(self):
        fields = [('StartTime', '2023-02-20 22:14:01.250000+00:00'), ('NameLength', '9'), ('Name', 'SMSSInit'),
                  ('TotalTime', '16484'), ('DegradationTime', '6484')]
        self.assertEqual(boot.delay_row(record(WHEN, '22', '110', fields)),
                         (TIME, START, '110', 'Session manager initialization caused a slow down in the startup process',
                          'SMSSInit', '', '', '16484', '6484', '', '', '', '22', 'LAB-PC'))

    def test_every_delay_event_has_its_own_label(self):
        labels = {event_id: boot.delay_row(record(WHEN, '23', event_id, []))[3]
                  for event_id in ('101', '102', '103', '104', '105', '106', '107', '108', '109', '110', '201', '202', '203')}
        self.assertEqual(len(set(labels.values())), 13)
        self.assertEqual(labels['101'], 'This application took longer than usual to start up')
        self.assertEqual(labels['102'], 'This driver took longer to initialize')
        self.assertEqual(labels['103'], 'This startup service took longer than expected to startup')
        self.assertEqual(labels['104'], 'Core system took longer to initialize')
        self.assertEqual(labels['105'], 'Foreground optimizations (prefetching) took longer to complete')
        self.assertEqual(labels['106'], 'Background optimizations (prefetching) took longer to complete')
        self.assertEqual(labels['107'], 'Application of machine policy caused a slow down in the system start up process')
        self.assertEqual(labels['108'], 'Application of user policy caused a slow down in the system start up process')
        self.assertEqual(labels['109'], 'This device took longer to initialize')
        self.assertEqual(labels['201'], 'This application caused a delay in the system shutdown process')
        self.assertEqual(labels['202'], 'This device caused a delay in the system shutdown process')

    def test_a_quoted_path_and_a_name_longer_than_its_length_field_are_kept_as_stored(self):
        fields = [('NameLength', '3'), ('Name', 'WinDefend'), ('PathLength', '9'),
                  ('Path', '"c:\\programdata\\example\\MsMpEng.exe"')]
        row = boot.delay_row(record(WHEN, '25', '203', fields))
        self.assertEqual((row[4], row[9]), ('WinDefend', '"c:\\programdata\\example\\MsMpEng.exe"'))

    def test_white_space_at_either_end_of_a_value_is_removed(self):
        fields = [('Name', ' audiodg.exe '), ('FriendlyName', 'Windows Audio Device Graph Isolation '), ('Path', ' C:\\x y\\a.exe ')]
        self.assertEqual(boot.delay_row(record(WHEN, '24', '101', fields))[4:10],
                         ('audiodg.exe', 'Windows Audio Device Graph Isolation', '', '', '', 'C:\\x y\\a.exe'))


class ArtifactTest(unittest.TestCase):
    def test_each_artifact_reads_the_log_for_its_own_events_and_keeps_file_order(self):
        found = ([record(WHEN, '32', '100', BOOT), record(WHEN, '31', '200', SHUTDOWN)], [LOG])
        with mock.patch.object(boot, 'read_event_records', return_value=found) as reader:
            headers, rows, source = boot.bootShutdownPerformance.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-diagnostics-performance%4operational.evtx',
                                       'Boot and Shutdown Performance', event_ids={'100', '200'},
                                       provider='Microsoft-Windows-Diagnostics-Performance')
        self.assertEqual([(row[11], row[3]) for row in rows], [('32', '100'), ('31', '200')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), ('Start Time (UTC)', 'datetime'),
                                   ('End Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Duration (ms)',
                                   'Main Path Boot Time (ms)', 'Post Boot Time (ms)', 'Degradation', 'Startup Apps',
                                   'Reboot After Install', 'Record ID', 'Computer'))
        found = ([record(WHEN, '42', '203', SLOW), record(WHEN, '41', '101', SLOW)], [LOG])
        with mock.patch.object(boot, 'read_event_records', return_value=found) as reader:
            headers, rows, source = boot.bootShutdownDelays.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-diagnostics-performance%4operational.evtx',
                                       'Boot and Shutdown Delays',
                                       event_ids={'101', '102', '103', '104', '105', '106', '107', '108', '109', '110', '201',
                                                  '202', '203'},
                                       provider='Microsoft-Windows-Diagnostics-Performance')
        self.assertEqual([(row[12], row[2]) for row in rows], [('42', '203'), ('41', '101')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), ('Incident Time (UTC)', 'datetime'), 'Event ID', 'Event',
                                   'Name', 'Friendly Name', 'Version', 'Total Time (ms)', 'Degradation Time (ms)', 'Path',
                                   'Product Name', 'Company Name', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        for artifact in (boot.bootShutdownPerformance, boot.bootShutdownDelays):
            with mock.patch.object(boot, 'read_event_records', return_value=([], [LOG, other])):
                self.assertEqual(artifact.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
            with mock.patch.object(boot, 'read_event_records', return_value=([], [])):
                self.assertEqual(artifact.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
