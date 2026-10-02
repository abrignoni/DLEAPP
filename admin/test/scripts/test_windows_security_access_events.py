"""Pin the rows in scripts/artifacts/windowsSecurityAccessEvents.py.

The records are built from XML of the shape python-evtx renders for the four events (made-up names and SIDs); the
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

from scripts.artifacts import windowsSecurityAccessEvents as access  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Security.evtx'
MUI = '/case/data/vol1/Windows/System32/en-US/msobjs.dll.mui'
SUBJECT = [('SubjectUserSid', SID), ('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB-PC'),
           ('SubjectLogonId', '0x0000000000012345')]
SUBJECT_ROW = ('examiner', 'LAB-PC', SID, '0x0000000000012345')
MESSAGES = {8099: 'Read Credential\r\n', 8100: 'Enumerate Credentials'}


def record(event_id, when, record_id, fields, source=LOG, provider='Microsoft-Windows-Security-Auditing'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{54849625-5478-4994-a5ba-3e3b0328c30d}}">'
           f'</Provider><EventID Qualifiers="">{event_id}</EventID><Version>0</Version><Level>0</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="704" ThreadID="5104"></Execution><Channel>Security</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID=""></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


PRIVILEGED = record('4672', '2023-01-05 20:15:01.100000+00:00', '300', SUBJECT + [
    ('PrivilegeList', 'SeSecurityPrivilege\n\t\t\tSeBackupPrivilege\n\t\t\tSeDebugPrivilege')])
USER_GROUPS = record('4798', '2023-01-05 20:16:02.200000+00:00', '301', [
    ('TargetUserName', 'guest'), ('TargetDomainName', 'LAB-PC'), ('TargetSid', SID[:-4] + '501')] + SUBJECT + [
        ('CallerProcessId', '0x1a2c'), ('CallerProcessName', 'C:\\Windows\\System32\\net1.exe')])
GROUP_MEMBERS = record('4799', '2023-01-05 20:17:03.300000+00:00', '302', [
    ('TargetUserName', 'Administrators'), ('TargetDomainName', 'Builtin'), ('TargetSid', 'S-1-5-32-544')] + SUBJECT + [
        ('CallerProcessId', '0x2b0'), ('CallerProcessName', 'C:\\Windows\\System32\\svchost.exe')])
READ = record('5379', '2023-01-05 20:18:04.400000+00:00', '303', SUBJECT + [
    ('TargetName', 'TERMSRV/10.0.0.5'), ('Type', '2'), ('CountOfCredentialsReturned', '1'),
    ('ReadOperation', '%%8099'), ('ReturnCode', '0'), ('ProcessCreationTime', '2023-01-05 20:10:00.123456+00:00'),
    ('ClientProcessId', '4312')])


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


class RowTest(unittest.TestCase):
    def test_special_privileges_are_listed_in_stored_order_with_one_separator(self):
        self.assertEqual(access.privilege_row(PRIVILEGED),
                         (utc(2023, 1, 5, 20, 15, 1, 100000), *SUBJECT_ROW,
                          'SeSecurityPrivilege, SeBackupPrivilege, SeDebugPrivilege', '300', 'LAB-PC'))

    def test_one_privilege_and_no_privilege(self):
        one = record('4672', '2023-01-05 20:15:01.100000+00:00', '1', SUBJECT + [('PrivilegeList', 'SeImpersonatePrivilege')])
        none = record('4672', '2023-01-05 20:15:01.100000+00:00', '2', SUBJECT)
        self.assertEqual(access.privileges(one), 'SeImpersonatePrivilege')
        self.assertEqual(access.privileges(none), '')

    def test_a_user_enumeration_and_a_group_enumeration_carry_their_own_event_text(self):
        self.assertEqual(access.enumeration_row(USER_GROUPS),
                         (utc(2023, 1, 5, 20, 16, 2, 200000), '4798', "A user's local group membership was enumerated",
                          'guest', 'LAB-PC', SID[:-4] + '501', 'C:\\Windows\\System32\\net1.exe', '0x1a2c',
                          *SUBJECT_ROW, '301', 'LAB-PC'))
        self.assertEqual(access.enumeration_row(GROUP_MEMBERS),
                         (utc(2023, 1, 5, 20, 17, 3, 300000), '4799',
                          'A security-enabled local group membership was enumerated', 'Administrators', 'Builtin',
                          'S-1-5-32-544', 'C:\\Windows\\System32\\svchost.exe', '0x2b0', *SUBJECT_ROW, '302', 'LAB-PC'))

    def test_a_credential_read(self):
        self.assertEqual(access.read_row(READ, _Text()),
                         (utc(2023, 1, 5, 20, 18, 4, 400000), utc(2023, 1, 5, 20, 10, 0, 123456), '<%%8099>',
                          'TERMSRV/10.0.0.5', '2', '1', '0', '4312', *SUBJECT_ROW, '303', 'LAB-PC'))

    def test_a_credential_read_with_no_event_data_keeps_its_time_and_blank_fields(self):
        bare = record('5379', '2020-09-18 05:41:31.000000+00:00', '7', [])
        self.assertEqual(access.read_row(bare, _Text()),
                         (utc(2020, 9, 18, 5, 41, 31), '', '<>', '', '', '', '', '', '', '', '', '', '7', 'LAB-PC'))

    def test_each_read_field_lands_in_its_own_column(self):
        fields = [('TargetName', 'a'), ('Type', 'b'), ('CountOfCredentialsReturned', 'c'), ('ReadOperation', 'd'),
                  ('ReturnCode', 'e'), ('ProcessCreationTime', 'f'), ('ClientProcessId', 'g'), ('SubjectUserName', 'h'),
                  ('SubjectDomainName', 'i'), ('SubjectUserSid', 'j'), ('SubjectLogonId', 'k')]
        row = access.read_row(record('5379', '2020-09-18 05:41:31.000000+00:00', '8', fields), _Text())
        self.assertEqual(row[1:], ('', '<d>', 'a', 'b', 'c', 'e', 'g', 'h', 'i', 'j', 'k', '8', 'LAB-PC'))

    def test_each_enumeration_field_lands_in_its_own_column(self):
        fields = [('TargetUserName', 'a'), ('TargetDomainName', 'b'), ('TargetSid', 'c'), ('CallerProcessId', 'd'),
                  ('CallerProcessName', 'e'), ('SubjectUserName', 'h'), ('SubjectDomainName', 'i'),
                  ('SubjectUserSid', 'j'), ('SubjectLogonId', 'k')]
        row = access.enumeration_row(record('4799', '2020-09-18 05:41:31.000000+00:00', '9', fields))
        self.assertEqual(row[1:], ('4799', 'A security-enabled local group membership was enumerated', 'a', 'b', 'c',
                                   'e', 'd', 'h', 'i', 'j', 'k', '9', 'LAB-PC'))


class ParameterTextTest(unittest.TestCase):
    OTHER = '/case/data/vol2/Windows/System32/en-US/msobjs.dll.mui'

    def parameters(self, files, messages=None):
        read = mock.patch.object(access.windows_messages, 'read_message_table',
                                 return_value=MESSAGES if messages is None else messages).start()
        self.addCleanup(mock.patch.stopall)
        with mock.patch.object(access.os.path, 'isdir', return_value=False):
            return access._ParameterText(_Context(files), 'Credential Manager Reads'), read  # pylint: disable=protected-access

    def test_a_reference_is_given_its_text_from_the_file_on_the_same_volume(self):
        parameters, read = self.parameters([LOG, self.OTHER, MUI])
        self.assertEqual(parameters.text(READ, '%%8099'), 'Read Credential (%%8099)')
        self.assertEqual(parameters.text(READ, '%%8100'), 'Enumerate Credentials (%%8100)')
        read.assert_called_once_with(MUI)
        self.assertEqual(parameters.files_used(), [MUI])

    def test_a_value_that_is_not_a_reference_is_kept(self):
        parameters, read = self.parameters([LOG, MUI])
        self.assertEqual(parameters.text(READ, 'Read Credential'), 'Read Credential')
        self.assertEqual(parameters.text(READ, ''), '')
        read.assert_not_called()

    def test_a_reference_the_file_does_not_hold_is_kept_and_counted(self):
        parameters, _read = self.parameters([LOG, MUI])
        self.assertEqual(parameters.text(READ, '%%9999'), '%%9999')
        self.assertEqual((parameters.kept, parameters.files_used()), (1, []))

    def test_without_a_message_file_on_the_volume_the_reference_is_kept_and_counted(self):
        parameters, _read = self.parameters([LOG, self.OTHER])
        self.assertEqual(parameters.text(READ, '%%8099'), '%%8099')
        self.assertEqual(parameters.files_used(), [])
        with mock.patch.object(access, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Credential Manager Reads: 1 parameter reference(s) reported as stored; no English '
                          'msobjs.dll.mui on the same volume gave their text'
                          + ('' if access.windows_messages.pefile else ' (pefile is not installed)')])

    def test_the_run_log_names_the_file_that_gave_the_text(self):
        parameters, _read = self.parameters([LOG, MUI])
        parameters.text(READ, '%%8099')
        parameters.text(READ, '%%8100')
        with mock.patch.object(access, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Credential Manager Reads: 2 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/msobjs.dll.mui'])


class AccessRecordsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.addCleanup(access._read.clear)  # pylint: disable=protected-access
        access._read.clear()  # pylint: disable=protected-access
        self.log = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'System32', 'winevt', 'Logs', 'Security.evtx')
        os.makedirs(os.path.dirname(self.log))
        with open(self.log, 'wb') as handle:
            handle.write(b'x' * 10)
        self.other = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'System32', 'en-US', 'msobjs.dll.mui')
        os.makedirs(os.path.dirname(self.other))
        with open(self.other, 'wb') as handle:
            handle.write(b'y')
        self.folder = os.path.join(folder.name, 'data', 'vol2', 'Security.evtx')
        os.makedirs(self.folder)

    def test_the_logs_are_read_once_for_the_three_artifacts_and_again_when_a_log_changes(self):
        found = ([PRIVILEGED, USER_GROUPS, GROUP_MEMBERS, READ], [self.log])
        with mock.patch.object(access, 'read_event_records', return_value=found) as reader, \
                mock.patch.object(access, 'logfunc'):
            first = access.specialPrivilegeLogons.__wrapped__(_Context([self.log]))
            second = access.localGroupEnumerations.__wrapped__(_Context([self.folder, self.log]))
            third = access.credentialManagerReads.__wrapped__(_Context([self.log, self.other]))
            self.assertEqual(reader.call_count, 1)
            reader.assert_called_once_with(mock.ANY, 'security.evtx', 'Security Access Events',
                                           event_ids={'4672', '4798', '4799', '5379'},
                                           provider='Microsoft-Windows-Security-Auditing')
            with open(self.log, 'ab') as handle:
                handle.write(b'more')
            access.localGroupEnumerations.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 2)
            times = os.stat(self.log)
            with open(self.log, 'ab') as handle:
                handle.write(b'same time, other size')
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns))
            access.localGroupEnumerations.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 3)
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns + 5 * 10 ** 9))
            access.localGroupEnumerations.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 4)
            access.localGroupEnumerations.__wrapped__(_Context([]))
            self.assertEqual(reader.call_count, 5)
        self.assertEqual([len(result[1]) for result in (first, second, third)], [1, 2, 1])
        self.assertEqual([row[1] for row in second[1]], ['4798', '4799'])
        self.assertEqual([result[2] for result in (first, second, third)], [self.log] * 3)

    def test_another_log_of_the_same_size_and_time_is_read_on_its_own(self):
        twin = os.path.join(os.path.dirname(os.path.dirname(self.folder)), 'vol3', 'Security.evtx')
        os.makedirs(os.path.dirname(twin))
        with open(twin, 'wb') as handle:
            handle.write(b'x' * 10)
        times = os.stat(self.log)
        os.utime(twin, ns=(times.st_atime_ns, times.st_mtime_ns))
        with mock.patch.object(access, 'read_event_records', return_value=([PRIVILEGED], [self.log])) as reader:
            access.specialPrivilegeLogons.__wrapped__(_Context([self.log]))
            access.specialPrivilegeLogons.__wrapped__(_Context([twin]))
        self.assertEqual(reader.call_count, 2)

    def test_two_logs_are_both_named_one_to_a_line(self):
        found = ([PRIVILEGED, USER_GROUPS], [LOG, '/case/data/vol2/Windows/System32/winevt/Logs/Security.evtx'])
        with mock.patch.object(access, 'read_event_records', return_value=found), \
                mock.patch.object(access, '_security_logs', return_value=[]):
            privileged = access.specialPrivilegeLogons.__wrapped__(_Context([]))
            enumerated = access.localGroupEnumerations.__wrapped__(_Context([]))
        self.assertEqual(privileged[2], LOG + '\n/case/data/vol2/Windows/System32/winevt/Logs/Security.evtx')
        self.assertEqual(enumerated[2], privileged[2])

    def test_the_headers(self):
        with mock.patch.object(access, 'read_event_records', return_value=([], [])):
            privileged = access.specialPrivilegeLogons.__wrapped__(_Context([]))
            enumerated = access.localGroupEnumerations.__wrapped__(_Context([]))
            reads = access.credentialManagerReads.__wrapped__(_Context([]))
        self.assertEqual(privileged, ((('Event Time (UTC)', 'datetime'), 'Account Name', 'Account Domain', 'Account SID',
                                       'Logon ID', 'Privileges', 'Record ID', 'Computer'), [], ''))
        self.assertEqual(enumerated, ((('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Target Name',
                                       'Target Domain', 'Target SID', 'Process Name', 'Process ID (as stored)',
                                       'Account Name', 'Account Domain', 'Account SID', 'Logon ID', 'Record ID',
                                       'Computer'), [], ''))
        self.assertEqual(reads, ((('Event Time (UTC)', 'datetime'), ('Process Creation Time (UTC)', 'datetime'),
                                  'Read Operation', 'Target Name', 'Type (as stored)', 'Credentials Returned',
                                  'Return Code (as stored)', 'Client Process ID', 'Account Name', 'Account Domain',
                                  'Account SID', 'Logon ID', 'Record ID', 'Computer'), [], ''))

    def test_the_read_artifact_resolves_from_the_message_file_and_names_it_as_a_source(self):
        with mock.patch.object(access, 'read_event_records', return_value=([READ, PRIVILEGED], [LOG])), \
                mock.patch.object(access, '_security_logs', return_value=[]), \
                mock.patch.object(access.windows_messages, 'read_message_table', return_value=MESSAGES), \
                mock.patch.object(access, 'logfunc') as log:
            _headers, rows, source = access.credentialManagerReads.__wrapped__(_Context([LOG, MUI]))
        self.assertEqual(rows, [(utc(2023, 1, 5, 20, 18, 4, 400000), utc(2023, 1, 5, 20, 10, 0, 123456),
                                 'Read Credential (%%8099)', 'TERMSRV/10.0.0.5', '2', '1', '0', '4312', *SUBJECT_ROW,
                                 '303', 'LAB-PC')])
        self.assertEqual(source, LOG + '\n' + MUI)
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Credential Manager Reads: 1 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/msobjs.dll.mui'])

    def test_a_creation_time_that_cannot_be_read_is_blank_and_logged(self):
        odd = record('5379', '2023-01-05 20:18:04.400000+00:00', '304', SUBJECT + [
            ('ReadOperation', 'Read Credential'), ('ProcessCreationTime', 'not a time')])
        none = record('5379', '2023-01-05 20:18:05.400000+00:00', '305', SUBJECT + [('ReadOperation', 'x')])
        with mock.patch.object(access, 'read_event_records', return_value=([odd, none, READ], [LOG])), \
                mock.patch.object(access, '_security_logs', return_value=[]), \
                mock.patch.object(access.windows_messages, 'read_message_table', return_value={}), \
                mock.patch.object(access, 'logfunc') as log:
            _headers, rows, source = access.credentialManagerReads.__wrapped__(_Context([LOG]))
        self.assertEqual([row[1] for row in rows], ['', '', utc(2023, 1, 5, 20, 10, 0, 123456)])
        self.assertEqual([row[2] for row in rows], ['Read Credential', 'x', '%%8099'])
        self.assertEqual(source, LOG)
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Credential Manager Reads: 1 parameter reference(s) reported as stored; no English '
                          'msobjs.dll.mui on the same volume gave their text'
                          + ('' if access.windows_messages.pefile else ' (pefile is not installed)'),
                          'Credential Manager Reads: 1 record(s) store a process creation time that could not be read '
                          'as a time; the column is blank on those rows'])

    def test_each_artifact_takes_only_its_own_events(self):
        found = ([READ, GROUP_MEMBERS, PRIVILEGED, USER_GROUPS], [LOG])
        with mock.patch.object(access, 'read_event_records', return_value=found), \
                mock.patch.object(access, '_security_logs', return_value=[]), \
                mock.patch.object(access, 'logfunc'):
            privileged = access.specialPrivilegeLogons.__wrapped__(_Context([LOG]))[1]
            enumerated = access.localGroupEnumerations.__wrapped__(_Context([LOG]))[1]
            reads = access.credentialManagerReads.__wrapped__(_Context([LOG]))[1]
        self.assertEqual([row[-2] for row in privileged], ['300'])
        self.assertEqual([row[-2] for row in enumerated], ['302', '301'])
        self.assertEqual([row[-2] for row in reads], ['303'])


if __name__ == '__main__':
    unittest.main()
