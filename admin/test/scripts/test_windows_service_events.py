"""Pin the Service Control Manager event rows in scripts/artifacts/windowsServiceEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up service names and SIDs); the
expected rows are written out.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsServiceEvents as services  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'
MUI = '/case/data/vol1/Windows/System32/en-US/kernel32.dll.mui'
OTHER = '/case/data/vol2/Windows/System32/en-US/kernel32.dll.mui'
MESSAGES = {21: 'The device is not ready.\r\n', 1056: 'An instance of the service\r\nis already running.\r\n', 1068: 'Dependency failed.'}
WHEN = '2021-03-04 05:06:07.800900+00:00'


def record(event_id, record_id, params, user_sid='', source=LOG, provider='Service Control Manager', when=WHEN):
    data = ''.join(f'<Data Name="param{number}">{value}</Data>' for number, value in enumerate(params, 1))
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{555908d1-a6d7-4695-8e1e-26931d2012f4}}" '
           f'EventSourceName="Service Control Manager"></Provider><EventID Qualifiers="16384">{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="704" ThreadID="5104"></Execution>'
           f'<Channel>System</Channel><Computer>LAB-PC</Computer><Security UserID="{user_sid}"></Security></System>'
           f'<EventData>{data}<Binary>770069006E00</Binary></EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


TIME = utc(2021, 3, 4, 5, 6, 7, 800900)
CHANGE = record('7040', '41', ['Example Transfer Service', 'demand start', 'auto start', 'ExampleSvc'], SID)
SYSTEM_CHANGE = record('7040', '42', ['Other Service', 'auto start', 'disabled', 'OtherSvc'], 'S-1-5-18',
                       when='2021-03-04 05:06:09.000000+00:00')
FAILED = record('7000', '50', ['ExampleSvc', '%%21'])
DEPENDS = record('7001', '51', ['Example Transfer Service', 'Base Service', '%%1068'])
CONNECT = record('7009', '52', ['30000', 'ExampleSvc'])
TRANSACTION = record('7011', '53', ['45000', 'ExampleSvc'])
HUNG = record('7022', '54', ['Example Transfer Service'])
ENDED = record('7023', '55', ['ExampleSvc', '%%2147942414'])
SPECIFIC = record('7024', '56', ['ExampleSvc', '%%3221229627'])
UNEXPECTED = record('7031', '57', ['ExampleSvc', '2', '30000', '1', 'Restart the service'])
ACTION = record('7032', '58', ['1', 'Restart the service', 'Example Transfer Service', '%%1056'])
AGAIN = record('7034', '59', ['Example Transfer Service', '3'])
SHUTDOWN = record('7043', '60', ['ExampleSvc'])
INSTALL = record('7045', '61', ['ExampleSvc', 'C:\\x.exe', 'user mode service', 'demand start', 'LocalSystem'])
ALL = [CHANGE, FAILED, DEPENDS, CONNECT, TRANSACTION, HUNG, ENDED, SPECIFIC, UNEXPECTED, ACTION, AGAIN, SHUTDOWN,
       SYSTEM_CHANGE]


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class _Text:
    """Stands in for _ParameterText: shows what it was asked for."""

    @staticmethod
    def text(_record, value):
        return f'<{value}>'


class ChangeRowTest(unittest.TestCase):
    def test_a_start_type_change_takes_the_four_parameters_and_the_sid_of_the_record(self):
        self.assertEqual(services.change_row(CHANGE),
                         (TIME, 'Example Transfer Service', 'ExampleSvc', 'demand start', 'auto start', SID, '41',
                          'LAB-PC'))

    def test_a_record_with_three_parameters_and_no_sid_has_blank_cells(self):
        short = record('7040', '43', ['Example Transfer Service', 'demand start', 'auto start'])
        self.assertEqual(services.change_row(short)[1:], ('Example Transfer Service', '', 'demand start', 'auto start',
                                                          '', '43', 'LAB-PC'))


class FailureRowTest(unittest.TestCase):
    def rows(self, *records):
        return [services.failure_row(item, _Text())[1:5] for item in records]

    def test_events_with_an_error_fill_the_message_and_the_error_column_with_its_text(self):
        self.assertEqual(self.rows(FAILED, DEPENDS, ENDED, SPECIFIC, ACTION), [
            ('7000', 'ExampleSvc', 'The ExampleSvc service failed to start due to the following error: <%%21>', '<%%21>'),
            ('7001', 'Example Transfer Service', 'The Example Transfer Service service depends on the Base Service '
             'service which failed to start because of the following error: <%%1068>', '<%%1068>'),
            ('7023', 'ExampleSvc', 'The ExampleSvc service terminated with the following error: <%%2147942414>',
             '<%%2147942414>'),
            ('7024', 'ExampleSvc', 'The ExampleSvc service terminated with the following service-specific error: '
             '<%%3221229627>', '<%%3221229627>'),
            ('7032', 'Example Transfer Service', 'The Service Control Manager tried to take a corrective action '
             '(Restart the service) after the unexpected termination of the Example Transfer Service service, but '
             'this action failed with the following error: <%%1056>', '<%%1056>'),
        ])

    def test_events_without_an_error_leave_the_error_column_blank(self):
        self.assertEqual(self.rows(CONNECT, TRANSACTION, HUNG, UNEXPECTED, AGAIN, SHUTDOWN), [
            ('7009', 'ExampleSvc', 'A timeout was reached (30000 milliseconds) while waiting for the ExampleSvc '
             'service to connect.', ''),
            ('7011', 'ExampleSvc', 'A timeout (45000 milliseconds) was reached while waiting for a transaction '
             'response from the ExampleSvc service.', ''),
            ('7022', 'Example Transfer Service', 'The Example Transfer Service service hung on starting.', ''),
            ('7031', 'ExampleSvc', 'The ExampleSvc service terminated unexpectedly. It has done this 2 time(s). The '
             'following corrective action will be taken in 30000 milliseconds: Restart the service.', ''),
            ('7034', 'Example Transfer Service', 'The Example Transfer Service service terminated unexpectedly. It '
             'has done this 3 time(s).', ''),
            ('7043', 'ExampleSvc', 'The ExampleSvc service did not shut down properly after receiving a preshutdown '
             'control.', ''),
        ])

    def test_the_row_keeps_the_time_the_record_id_and_the_computer(self):
        row = services.failure_row(AGAIN, _Text())
        self.assertEqual((row[0], row[5], row[6]), (TIME, '59', 'LAB-PC'))

    def test_a_missing_parameter_is_filled_in_as_nothing_and_a_parameter_holding_an_insert_is_kept_as_text(self):
        self.assertEqual(self.rows(record('7034', '62', ['%2 Service'])),
                         [('7034', '%2 Service', 'The %2 Service service terminated unexpectedly. It has done this '
                           ' time(s).', '')])

    def test_every_failure_event_names_its_service_and_error_parameters_within_the_message(self):
        for event_id, (template, service, error) in services._FAILURES.items():  # pylint: disable=protected-access
            self.assertIn(f'%{service} service', template, event_id)
            self.assertEqual(bool(error), 'error: %' in template, event_id)
            if error:
                self.assertTrue(template.endswith(f'error: %{error}'), event_id)


class ParameterTextTest(unittest.TestCase):
    def parameters(self, files, messages=None):
        read = mock.patch.object(services.windows_messages, 'read_message_table',
                                 return_value=MESSAGES if messages is None else messages).start()
        self.addCleanup(mock.patch.stopall)
        with mock.patch.object(services.os.path, 'isdir', return_value=False):
            return services._ParameterText(_Context(files), 'Service Failures'), read  # pylint: disable=protected-access

    def test_a_reference_is_given_its_text_from_the_file_on_the_same_volume_with_line_breaks_as_spaces(self):
        parameters, read = self.parameters([LOG, OTHER, MUI])
        self.assertEqual(parameters.text(FAILED, '%%21'), 'The device is not ready. (%%21)')
        self.assertEqual(parameters.text(FAILED, '%%1056'), 'An instance of the service is already running. (%%1056)')
        read.assert_called_once_with(MUI)
        self.assertEqual(parameters.files_used(), [MUI])

    def test_a_reference_the_file_does_not_hold_is_kept_and_a_value_that_is_not_a_reference_is_not_looked_up(self):
        parameters, read = self.parameters([LOG, MUI])
        self.assertEqual(parameters.text(FAILED, 'plain text'), 'plain text')
        self.assertEqual(parameters.text(FAILED, ''), '')
        read.assert_not_called()
        self.assertEqual(parameters.text(FAILED, '%%3221229627'), '%%3221229627')
        self.assertEqual(parameters.files_used(), [])

    def test_without_a_message_file_on_the_volume_the_reference_is_kept_and_counted(self):
        parameters, _read = self.parameters([LOG, OTHER])
        self.assertEqual(parameters.text(FAILED, '%%21'), '%%21')
        self.assertEqual(parameters.files_used(), [])
        with mock.patch.object(services, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Service Failures: 1 parameter reference(s) reported as stored; no English '
                          'kernel32.dll.mui on the same volume gave their text'
                          + ('' if services.windows_messages.pefile else ' (pefile is not installed)')])

    def test_the_run_log_names_the_file_that_gave_the_text(self):
        parameters, _read = self.parameters([LOG, MUI])
        parameters.text(FAILED, '%%21')
        parameters.text(FAILED, '%%1068')
        with mock.patch.object(services, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Service Failures: 2 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/kernel32.dll.mui'])


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.addCleanup(services._read.clear)  # pylint: disable=protected-access
        services._read.clear()  # pylint: disable=protected-access
        self.log = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'System32', 'winevt', 'Logs', 'System.evtx')
        os.makedirs(os.path.dirname(self.log))
        with open(self.log, 'wb') as handle:
            handle.write(b'x' * 10)
        self.mui = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'System32', 'en-US', 'kernel32.dll.mui')
        os.makedirs(os.path.dirname(self.mui))
        with open(self.mui, 'wb') as handle:
            handle.write(b'y')
        self.folder = os.path.join(folder.name, 'data', 'vol2', 'System.evtx')
        os.makedirs(self.folder)

    def test_the_logs_are_read_once_for_the_two_artifacts_and_again_when_a_log_changes(self):
        found = (ALL, [self.log])
        with mock.patch.object(services, 'read_event_records', return_value=found) as reader, \
                mock.patch.object(services, 'logfunc'):
            first = services.serviceStartTypeChanges.__wrapped__(_Context([self.log, self.mui]))
            second = services.serviceFailures.__wrapped__(_Context([self.folder, self.log]))
            self.assertEqual(reader.call_count, 1)
            reader.assert_called_once_with(
                mock.ANY, 'system.evtx', 'Service Control Manager Events',
                event_ids={'7000', '7001', '7009', '7011', '7022', '7023', '7024', '7031', '7032', '7034', '7040', '7043'},
                provider='Service Control Manager')
            with open(self.log, 'ab') as handle:
                handle.write(b'more')
            services.serviceFailures.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 2)
            times = os.stat(self.log)
            with open(self.log, 'ab') as handle:
                handle.write(b'same time, other size')
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns))
            services.serviceFailures.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 3)
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns + 5 * 10 ** 9))
            services.serviceFailures.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 4)
            services.serviceFailures.__wrapped__(_Context([]))
            self.assertEqual(reader.call_count, 5)
        self.assertEqual([row[6] for row in first[1]], ['41', '42'])
        self.assertEqual([row[1] for row in second[1]],
                         ['7000', '7001', '7009', '7011', '7022', '7023', '7024', '7031', '7032', '7034', '7043'])
        self.assertEqual([result[2] for result in (first, second)], [self.log] * 2)

    def test_the_headers(self):
        with mock.patch.object(services, 'read_event_records', return_value=([], [])):
            changes = services.serviceStartTypeChanges.__wrapped__(_Context([]))
            failures = services.serviceFailures.__wrapped__(_Context([]))
        self.assertEqual(changes, ((('Event Time (UTC)', 'datetime'), 'Service', 'Service Name', 'Previous Start Type',
                                    'New Start Type', 'User SID', 'Record ID', 'Computer'), [], ''))
        self.assertEqual(failures, ((('Event Time (UTC)', 'datetime'), 'Event ID', 'Service', 'Message', 'Error',
                                     'Record ID', 'Computer'), [], ''))

    def test_the_failures_artifact_resolves_from_the_message_file_and_names_it_as_a_source(self):
        with mock.patch.object(services, 'read_event_records', return_value=([FAILED, ACTION, AGAIN, CHANGE], [LOG])), \
                mock.patch.object(services, '_system_logs', return_value=[]), \
                mock.patch.object(services.windows_messages, 'read_message_table', return_value=MESSAGES), \
                mock.patch.object(services, 'logfunc') as log:
            _headers, rows, source = services.serviceFailures.__wrapped__(_Context([LOG, MUI]))
        self.assertEqual(rows, [
            (TIME, '7000', 'ExampleSvc', 'The ExampleSvc service failed to start due to the following error: The '
             'device is not ready. (%%21)', 'The device is not ready. (%%21)', '50', 'LAB-PC'),
            (TIME, '7032', 'Example Transfer Service', 'The Service Control Manager tried to take a corrective action '
             '(Restart the service) after the unexpected termination of the Example Transfer Service service, but '
             'this action failed with the following error: An instance of the service is already running. (%%1056)',
             'An instance of the service is already running. (%%1056)', '58', 'LAB-PC'),
            (TIME, '7034', 'Example Transfer Service', 'The Example Transfer Service service terminated unexpectedly. '
             'It has done this 3 time(s).', '', '59', 'LAB-PC')])
        self.assertEqual(source, LOG + '\n' + MUI)
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Service Failures: 2 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/kernel32.dll.mui'])

    def test_two_logs_are_each_named_on_their_own_line_of_the_source(self):
        second = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        other = record('7040', '7', ['Other Service', 'auto start', 'disabled', 'OtherSvc'], 'S-1-5-18', source=second)
        with mock.patch.object(services, 'read_event_records', return_value=([CHANGE, other, FAILED], [LOG, second])), \
                mock.patch.object(services, '_system_logs', return_value=[]), mock.patch.object(services, 'logfunc'):
            changes = services.serviceStartTypeChanges.__wrapped__(_Context([LOG, second]))
            failures = services.serviceFailures.__wrapped__(_Context([LOG, second]))
        self.assertEqual([row[6] for row in changes[1]], ['41', '7'])
        self.assertEqual((changes[2], failures[2]), (LOG + '\n' + second, LOG + '\n' + second))

    def test_an_install_record_is_in_neither_artifact(self):
        with mock.patch.object(services, 'read_event_records', return_value=([INSTALL], [LOG])), \
                mock.patch.object(services, '_system_logs', return_value=[]), mock.patch.object(services, 'logfunc'):
            self.assertEqual(services.serviceStartTypeChanges.__wrapped__(_Context([LOG]))[1], [])
            self.assertEqual(services.serviceFailures.__wrapped__(_Context([LOG]))[1], [])


if __name__ == '__main__':
    unittest.main()
