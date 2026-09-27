"""Pin the rows of the Windows System Time Changes and Windows Security Time Changes artifacts."""
import datetime
import fnmatch
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree
from xml.sax.saxutils import escape

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsTimeChanges as tc
from scripts.windows_evtx import EventRecord
# pylint: enable=wrong-import-position

_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
_UTC = datetime.timezone.utc
_LOG = '/case/data/p3/Windows/System32/winevt/Logs/System.evtx'


def event(provider, event_id, fields, version='1', record_id='41', source=_LOG):
    """An EventRecord like python-evtx renders one."""
    items = ''.join(f'<Data Name="{name}">{escape(value)}</Data>' for name, value in fields.items())
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="{provider}"/>'
           f'<EventID>{event_id}</EventID><Version>{version}</Version>'
           '<TimeCreated SystemTime="2022-11-23 03:57:03.413883+00:00"/>'
           f'<EventRecordID>{record_id}</EventRecordID>'
           '<Execution ProcessID="3872" ThreadID="2"/><Computer>HOST</Computer>'
           f'<Security UserID="S-1-5-19"/></System><EventData>{items}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def at(text):
    return datetime.datetime.fromisoformat(text).astimezone(_UTC)


def kernel_general_1(version='4', record_id='41', **overrides):
    fields = {'NewTime': '2022-11-23 03:57:03.413570+00:00',
              'OldTime': '2022-11-23 03:57:03.411581+00:00',
              'TimeDeltaInMs': '1', 'Reason': '1',
              'ProcessName': '\\Device\\HarddiskVolume3\\Windows\\System32\\svchost.exe',
              'ProcessID': '3872', 'CmosTime': '2022-11-22 22:57:03.413570+00:00',
              'TimeZoneBias': '300', 'RealTimeIsUniversal': 'False', 'SystemInCmosMode': 'False'}
    if version == '1':
        fields = {name: fields[name] for name in ('NewTime', 'OldTime', 'Reason')}
    elif version == '2':
        fields = {name: fields[name] for name in ('NewTime', 'OldTime', 'Reason', 'ProcessName', 'ProcessID')}
    fields.update(overrides)
    return event(tc._KERNEL_GENERAL, '1', fields, version=version,  # pylint: disable=protected-access
                 record_id=record_id)


class SystemTimeRowTest(unittest.TestCase):
    def test_a_version_4_event_gives_both_times_the_change_process_and_bias(self):
        row = tc.system_time_row(kernel_general_1(), 'Reason text')
        self.assertEqual(row, (at('2022-11-23T03:57:03.413883+00:00'),
                               at('2022-11-23T03:57:03.411581+00:00'),
                               at('2022-11-23T03:57:03.413570+00:00'), '0.001989', 'Reason text',
                               '\\Device\\HarddiskVolume3\\Windows\\System32\\svchost.exe', '3872',
                               '300', 'HOST'))

    def test_a_version_1_event_takes_the_execution_process_id_and_leaves_the_rest_blank(self):
        row = tc.system_time_row(kernel_general_1(version='1'), '3')
        # Version 1 stores no ProcessID, so the Execution element's process ID is reported.
        self.assertEqual(row[3:], ('0.001989', '3', '', '3872', '', 'HOST'))

    def test_a_backward_change_is_negative_and_a_missing_time_gives_no_change(self):
        row = tc.system_time_row(kernel_general_1(NewTime='2022-11-23 02:57:03.411581+00:00'), '1')
        self.assertEqual(row[3], '-3600.000000')
        row = tc.system_time_row(kernel_general_1(OldTime=''), '1')
        self.assertEqual((row[1], row[3]), ('', ''))


class SecurityTimeRowTest(unittest.TestCase):
    def test_a_4616_gives_the_times_the_process_in_decimal_and_the_account(self):
        record = event(tc._SECURITY, '4616', {  # pylint: disable=protected-access
            'SubjectUserSid': 'S-1-5-19', 'SubjectUserName': 'LOCAL SERVICE',
            'SubjectDomainName': 'NT AUTHORITY', 'SubjectLogonId': '0x00000000000003e5',
            'PreviousTime': '2020-09-19 01:26:37.100000+00:00',
            'NewTime': '2020-09-19 02:26:36.315677+00:00',
            'ProcessId': '0x0000000000000ed4',
            'ProcessName': 'C:\\Windows\\System32\\svchost.exe'},
            source='/case/data/p3/Windows/System32/winevt/Logs/Security.evtx')
        self.assertEqual(tc.security_time_row(record), (
            at('2022-11-23T03:57:03.413883+00:00'), at('2020-09-19T01:26:37.100000+00:00'),
            at('2020-09-19T02:26:36.315677+00:00'), '3599.215677',
            'C:\\Windows\\System32\\svchost.exe', '3796', 'LOCAL SERVICE', 'NT AUTHORITY',
            'S-1-5-19', '0x00000000000003e5', 'HOST'))

    def test_a_process_id_that_is_not_hexadecimal_is_kept_as_stored(self):
        self.assertEqual(tc._decimal('1234'), '1234')  # pylint: disable=protected-access
        self.assertEqual(tc._decimal('0xZZ'), '0xZZ')  # pylint: disable=protected-access


class BuildGateTest(unittest.TestCase):
    def test_an_event_after_a_boot_of_the_last_build_is_written_under_it(self):
        boots = [(3, '17763'), (90, '17763')]
        self.assertTrue(tc._written_under_last_build(50, boots))  # pylint: disable=protected-access

    def test_an_event_before_any_boot_or_after_an_older_build_is_not(self):
        boots = [(3, '17134'), (90, '17763')]
        self.assertFalse(tc._written_under_last_build(2, boots))  # pylint: disable=protected-access
        self.assertFalse(tc._written_under_last_build(50, boots))  # pylint: disable=protected-access
        self.assertFalse(tc._written_under_last_build(50, []))  # pylint: disable=protected-access


class FakeContext:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1]


def kernel_general_12(build, record_id, source=_LOG):
    return event(tc._KERNEL_GENERAL, '12', {'BuildVersion': build},  # pylint: disable=protected-access
                 version='1', record_id=record_id, source=source)


def volume_files(volume):
    return (f'/case/data/{volume}/Windows/System32/winevt/Logs/System.evtx',
            f'/case/data/{volume}/Windows/System32/microsoft-windows-system-events.dll',
            f'/case/data/{volume}/Windows/System32/en-US/microsoft-windows-system-events.dll.mui')


class ReasonNamesTest(unittest.TestCase):
    DLL = '/case/data/p3/Windows/System32/microsoft-windows-system-events.dll'
    MUI = '/case/data/p3/Windows/System32/en-US/microsoft-windows-system-events.dll.mui'

    def names(self, maps, messages, files=None, reason='2', record_id='50', boots=((3, '17763'), (40, '17763'))):
        context = FakeContext(files if files is not None else [_LOG, self.DLL, self.MUI])
        with mock.patch.object(tc.windows_messages, 'read_event_value_maps', return_value=maps), \
                mock.patch.object(tc.windows_messages, 'read_message_table', return_value=messages), \
                mock.patch('os.path.isdir', return_value=False):
            names = tc._ReasonNames(context)  # pylint: disable=protected-access
            return names, names.text(kernel_general_1(version='2', record_id=record_id, Reason=reason),
                                     list(boots))

    def test_the_reason_is_named_from_the_value_map_on_the_logs_volume(self):
        names, text = self.names({(1, 2): {'Reason': {2: 7}}}, {7: 'Synchronized\r\n'})
        self.assertEqual(text, 'Synchronized (2)')
        self.assertEqual(names.files_used(), sorted([self.DLL, self.MUI]))

    def test_an_event_written_under_an_earlier_build_keeps_the_number_as_stored(self):
        names, text = self.names({(1, 2): {'Reason': {2: 7}}}, {7: 'Synchronized'},
                                 record_id='20', boots=((3, '17134'), (40, '17763')))
        self.assertEqual(text, '2')
        self.assertEqual(names.kept, {'build': 1})
        self.assertEqual(names.files_used(), [])

    def test_a_dll_on_another_volume_is_not_used(self):
        _log, dll, mui = volume_files('p4')
        names, text = self.names({(1, 2): {'Reason': {2: 7}}}, {7: 'Synchronized'}, files=[_LOG, dll, mui])
        self.assertEqual(text, '2')
        self.assertEqual(names.kept, {'no value map': 1})

    def test_a_reason_that_is_not_a_number_is_kept_as_stored(self):
        names, text = self.names({(1, 2): {'Reason': {2: 7}}}, {7: 'Synchronized'}, reason='')
        self.assertEqual(text, '')
        self.assertEqual(names.files_used(), [])

    def test_the_reason_is_kept_as_stored_without_the_dll_or_its_mui(self):
        names, text = self.names({(1, 2): {'Reason': {2: 7}}}, {7: 'Synchronized'}, files=[_LOG, self.DLL])
        self.assertEqual(text, '2')
        self.assertEqual(names.kept, {'no value map': 1})

    def test_the_reason_is_kept_as_stored_when_the_map_has_no_entry_for_it(self):
        names, text = self.names({(1, 2): {'Reason': {1: 7}}}, {7: 'Changed'})
        self.assertEqual(text, '2')
        self.assertEqual(names.kept, {'not in the map': 1})

    def test_a_map_for_another_version_does_not_name_the_reason(self):
        names, text = self.names({(1, 4): {'Reason': {2: 7}}}, {7: 'Synchronized'})
        self.assertEqual(text, '2')
        self.assertEqual(names.kept, {'not in the map': 1})


class ProcessorTest(unittest.TestCase):
    """Each processor asks for its own log, provider and events, and cites what it read."""

    MAPS = {(1, 2): {'Reason': {2: 7}}}
    MESSAGES = {7: 'Synchronized'}

    def run_processor(self, processor, records, files=()):
        calls = []

        def fake_read(_context, file_name, _label, event_ids=None, provider=None):
            calls.append((file_name, frozenset(event_ids), provider))
            return records, sorted({record.source for record in records})

        with mock.patch.object(tc, 'read_event_records', side_effect=fake_read), \
                mock.patch.object(tc, 'logfunc'), \
                mock.patch.object(tc.windows_messages, 'read_event_value_maps', return_value=self.MAPS), \
                mock.patch.object(tc.windows_messages, 'read_message_table', return_value=self.MESSAGES), \
                mock.patch('os.path.isdir', return_value=False):
            _headers, rows, source = processor.__wrapped__(FakeContext(list(files)))
        return calls, rows, source

    def test_system_reads_events_1_and_12_of_kernel_general_and_reports_only_event_1(self):
        log, dll, mui = volume_files('p3')
        records = [kernel_general_12('17763', '10', source=log),
                   kernel_general_1(version='2', record_id='20', Reason='2', source=log)]
        calls, rows, source = self.run_processor(tc.systemTimeChanges, records, files=(log, dll, mui))
        self.assertEqual(calls, [('system.evtx', frozenset({'1', '12'}), tc._KERNEL_GENERAL)])  # pylint: disable=protected-access
        self.assertEqual([row[4] for row in rows], ['Synchronized (2)'])
        self.assertEqual(source, '\n'.join([log] + sorted([dll, mui])))

    def test_each_log_is_judged_by_its_own_boot_records(self):
        log3, dll3, mui3 = volume_files('p3')
        log4, dll4, mui4 = volume_files('p4')
        # Pooled with p4's later boot of another build, p3's event would look written under an older build.
        records = [kernel_general_12('17763', '10', source=log3),
                   kernel_general_1(version='2', record_id='20', Reason='2', source=log3),
                   kernel_general_12('22621', '30', source=log4)]
        _calls, rows, source = self.run_processor(tc.systemTimeChanges, records,
                                                  files=(log3, dll3, mui3, log4, dll4, mui4))
        self.assertEqual([row[4] for row in rows], ['Synchronized (2)'])
        self.assertEqual(source, '\n'.join([log3] + sorted([dll3, mui3])))

    def test_security_reads_4616_of_security_auditing(self):
        log = '/case/data/p3/Windows/System32/winevt/Logs/Security.evtx'
        record = event(tc._SECURITY, '4616', {'ProcessId': '0x10'}, source=log)  # pylint: disable=protected-access
        calls, rows, source = self.run_processor(tc.securityTimeChanges, [record])
        self.assertEqual(calls, [('security.evtx', frozenset({'4616'}), tc._SECURITY)])  # pylint: disable=protected-access
        self.assertEqual(rows, [tc.security_time_row(record)])
        self.assertEqual(source, log)


class DeclaredPathsTest(unittest.TestCase):
    def matches(self, key, path):
        return any(fnmatch.fnmatch(path, pattern) for pattern in tc.__artifacts_v2__[key]['paths'])

    def test_each_artifact_reads_only_its_own_log(self):
        base = 'p3/Windows/System32/winevt/Logs/'
        self.assertTrue(self.matches('systemTimeChanges', base + 'System.evtx'))
        self.assertTrue(self.matches('securityTimeChanges', base + 'Security.evtx'))
        self.assertFalse(self.matches('systemTimeChanges', base + 'Security.evtx'))
        self.assertFalse(self.matches('securityTimeChanges', base + 'System.evtx'))
        self.assertFalse(self.matches('systemTimeChanges', base + 'Microsoft-Windows-Time-Service%4Operational.evtx'))

    def test_the_reason_dll_and_its_english_mui_are_declared(self):
        self.assertTrue(self.matches('systemTimeChanges', 'p3/Windows/System32/microsoft-windows-system-events.dll'))
        self.assertTrue(self.matches('systemTimeChanges',
                                     'p3/Windows/System32/en-US/microsoft-windows-system-events.dll.mui'))


if __name__ == '__main__':
    unittest.main()
