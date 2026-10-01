"""Pin the policy change rows in scripts/artifacts/windowsPolicyChangeEvents.py.

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

from scripts.artifacts import windowsPolicyChangeEvents as policy  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Security.evtx'
SUBJECT = [('SubjectUserSid', SID), ('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB-PC'),
           ('SubjectLogonId', '0x0000000000012345')]
SUBJECT_ROW = ('examiner', 'LAB-PC', SID, '0x0000000000012345')
MESSAGES = {8276: 'Detailed Tracking', 13312: 'Process Creation\r\n', 8449: 'Success Added', 8451: 'Failure added'}


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


AUDIT = record('4719', '2026-09-30 13:46:47.973286+00:00', '21871', SUBJECT + [
    ('CategoryId', '%%8276'), ('SubcategoryId', '%%13312'),
    ('SubcategoryGuid', '{0cce922b-69ae-11d9-bed3-505054503030}'), ('AuditPolicyChanges', '%%8449')])
GRANTED = record('4717', '2019-03-19 20:55:31.100000+00:00', '51', SUBJECT + [
    ('TargetSid', 'S-1-5-32-555'), ('AccessGranted', 'SeRemoteInteractiveLogonRight')])
REMOVED = record('4718', '2019-03-19 20:55:32.200000+00:00', '52', SUBJECT + [
    ('TargetSid', 'S-1-1-0'), ('AccessRemoved', 'SeInteractiveLogonRight'), ('AccessGranted', 'not this field')])
DOMAIN = record('4739', '2020-09-18 22:59:44.300000+00:00', '90', [
    ('DomainPolicyChanged', 'Password Policy'), ('DomainName', 'LAB-PC'),
    ('DomainSid', 'S-1-5-21-1111111111-2222222222-3333333333')] + SUBJECT + [
        ('PrivilegeList', '-'), ('MinPasswordAge', '-'), ('MaxPasswordAge', '-'), ('ForceLogoff', '-'),
        ('LockoutThreshold', '-'), ('LockoutObservationWindow', '-'), ('LockoutDuration', '-'),
        ('PasswordProperties', '1'), ('MinPasswordLength', '7'), ('PasswordHistoryLength', '24'),
        ('MachineAccountQuota', '-'), ('MixedDomainMode', '-'), ('DomainBehaviorVersion', '-'), ('OemInformation', '0')])


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
    def test_an_audit_policy_change(self):
        self.assertEqual(policy.audit_row(AUDIT, _Text()),
                         (utc(2026, 9, 30, 13, 46, 47, 973286), '<%%8276>', '<%%13312>',
                          '{0cce922b-69ae-11d9-bed3-505054503030}', '<%%8449>', *SUBJECT_ROW, '21871', 'LAB-PC'))

    def test_a_right_granted_and_a_right_removed_each_take_their_own_field(self):
        self.assertEqual(policy.right_row(GRANTED),
                         (utc(2019, 3, 19, 20, 55, 31, 100000), '4717', 'Access granted',
                          'SeRemoteInteractiveLogonRight', 'S-1-5-32-555', *SUBJECT_ROW, '51', 'LAB-PC'))
        self.assertEqual(policy.right_row(REMOVED),
                         (utc(2019, 3, 19, 20, 55, 32, 200000), '4718', 'Access removed', 'SeInteractiveLogonRight',
                          'S-1-1-0', *SUBJECT_ROW, '52', 'LAB-PC'))

    def test_a_domain_policy_change_lists_only_the_attributes_with_a_value(self):
        self.assertEqual(policy.domain_row(DOMAIN),
                         (utc(2020, 9, 18, 22, 59, 44, 300000), 'Password Policy', 'LAB-PC',
                          'S-1-5-21-1111111111-2222222222-3333333333',
                          'Password Properties: 1; Min. Password Length: 7; Password History Length: 24; '
                          'OEM Information: 0', '-', *SUBJECT_ROW, '90', 'LAB-PC'))

    def test_every_changed_attribute_is_labelled_in_the_order_of_the_message(self):
        every = record('4739', '2020-09-18 22:59:44.300000+00:00', '91',
                       [(field, str(number)) for number, (field, _label) in enumerate(policy._ATTRIBUTES)])  # pylint: disable=protected-access
        self.assertEqual(policy.changed_attributes(every),
                         'Min. Password Age: 0; Max. Password Age: 1; Force Logoff: 2; Lockout Threshold: 3; '
                         'Lockout Observation Window: 4; Lockout Duration: 5; Password Properties: 6; '
                         'Min. Password Length: 7; Password History Length: 8; Machine Account Quota: 9; '
                         'Mixed Domain Mode: 10; Domain Behavior Version: 11; OEM Information: 12')

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        bare = record('4739', '2020-09-18 05:41:31.000000+00:00', '7', [])
        self.assertEqual(policy.domain_row(bare),
                         (utc(2020, 9, 18, 5, 41, 31), '', '', '', '', '', '', '', '', '', '7', 'LAB-PC'))


class ParameterTextTest(unittest.TestCase):
    MUI = '/case/data/vol1/Windows/System32/en-US/msobjs.dll.mui'
    OTHER = '/case/data/vol2/Windows/System32/en-US/msobjs.dll.mui'

    def parameters(self, files, messages=None):
        read = mock.patch.object(policy.windows_messages, 'read_message_table',
                                 return_value=MESSAGES if messages is None else messages).start()
        self.addCleanup(mock.patch.stopall)
        with mock.patch.object(policy.os.path, 'isdir', return_value=False):
            return policy._ParameterText(_Context(files), 'Audit Policy Changes'), read  # pylint: disable=protected-access

    def test_a_reference_is_given_its_text_from_the_file_on_the_same_volume(self):
        parameters, read = self.parameters([LOG, self.OTHER, self.MUI])
        self.assertEqual(parameters.text(AUDIT, '%%8276'), 'Detailed Tracking (%%8276)')
        self.assertEqual(parameters.text(AUDIT, '%%13312'), 'Process Creation (%%13312)')
        read.assert_called_once_with(self.MUI)
        self.assertEqual(parameters.files_used(), [self.MUI])

    def test_several_references_in_one_value_are_each_given_their_text(self):
        parameters, _read = self.parameters([LOG, self.MUI])
        self.assertEqual(parameters.text(AUDIT, '%%8449, %%8451'), 'Success Added (%%8449), Failure added (%%8451)')
        self.assertEqual(parameters.text(AUDIT, '%%8449, %%9999'), 'Success Added (%%8449), %%9999')

    def test_a_value_that_is_not_a_reference_is_kept(self):
        parameters, read = self.parameters([LOG, self.MUI])
        self.assertEqual(parameters.text(AUDIT, 'Success Added'), 'Success Added')
        self.assertEqual(parameters.text(AUDIT, ''), '')
        read.assert_not_called()

    def test_without_a_message_file_on_the_volume_the_reference_is_kept_and_counted(self):
        parameters, _read = self.parameters([LOG, self.OTHER])
        self.assertEqual(parameters.text(AUDIT, '%%8276'), '%%8276')
        self.assertEqual(parameters.files_used(), [])
        with mock.patch.object(policy, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Audit Policy Changes: 1 parameter reference(s) reported as stored; no English '
                          'msobjs.dll.mui on the same volume gave their text'
                          + ('' if policy.windows_messages.pefile else ' (pefile is not installed)')])

    def test_the_run_log_names_the_file_that_gave_the_text(self):
        parameters, _read = self.parameters([LOG, self.MUI])
        parameters.text(AUDIT, '%%8276')
        parameters.text(AUDIT, '%%8449')
        with mock.patch.object(policy, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Audit Policy Changes: 2 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/msobjs.dll.mui'])


class PolicyRecordsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.addCleanup(policy._read.clear)  # pylint: disable=protected-access
        policy._read.clear()  # pylint: disable=protected-access
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
        found = ([AUDIT, GRANTED, REMOVED, DOMAIN], [self.log])
        with mock.patch.object(policy, 'read_event_records', return_value=found) as reader, \
                mock.patch.object(policy, 'logfunc'):
            first = policy.auditPolicyChanges.__wrapped__(_Context([self.log, self.other]))
            second = policy.logonRightChanges.__wrapped__(_Context([self.log]))
            third = policy.domainPolicyChanges.__wrapped__(_Context([self.folder, self.log]))
            self.assertEqual(reader.call_count, 1)
            reader.assert_called_once_with(mock.ANY, 'security.evtx', 'Security Policy Changes',
                                           event_ids={'4717', '4718', '4719', '4739'},
                                           provider='Microsoft-Windows-Security-Auditing')
            with open(self.log, 'ab') as handle:
                handle.write(b'more')
            policy.logonRightChanges.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 2)
            times = os.stat(self.log)
            with open(self.log, 'ab') as handle:
                handle.write(b'same time, other size')
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns))
            policy.logonRightChanges.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 3)
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns + 5 * 10 ** 9))
            policy.logonRightChanges.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 4)
            policy.logonRightChanges.__wrapped__(_Context([]))
            self.assertEqual(reader.call_count, 5)
        self.assertEqual([len(result[1]) for result in (first, second, third)], [1, 2, 1])
        self.assertEqual([row[1] for row in second[1]], ['4717', '4718'])
        self.assertEqual([result[2] for result in (first, second, third)], [self.log] * 3)

    def test_the_headers(self):
        with mock.patch.object(policy, 'read_event_records', return_value=([], [])):
            audit = policy.auditPolicyChanges.__wrapped__(_Context([]))
            rights = policy.logonRightChanges.__wrapped__(_Context([]))
            domain = policy.domainPolicyChanges.__wrapped__(_Context([]))
        self.assertEqual(audit, ((('Event Time (UTC)', 'datetime'), 'Category', 'Subcategory', 'Subcategory GUID',
                                  'Changes', 'Account Name', 'Account Domain', 'Account SID', 'Logon ID', 'Record ID',
                                  'Computer'), [], ''))
        self.assertEqual(rights, ((('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Access Right', 'Target SID',
                                   'Account Name', 'Account Domain', 'Account SID', 'Logon ID', 'Record ID',
                                   'Computer'), [], ''))
        self.assertEqual(domain, ((('Event Time (UTC)', 'datetime'), 'Policy Changed', 'Domain Name', 'Domain SID',
                                   'Changed Attributes', 'Privileges', 'Account Name', 'Account Domain', 'Account SID',
                                   'Logon ID', 'Record ID', 'Computer'), [], ''))

    def test_the_audit_artifact_resolves_from_the_message_file_and_names_it_as_a_source(self):
        with mock.patch.object(policy, 'read_event_records', return_value=([AUDIT], [LOG])), \
                mock.patch.object(policy, '_security_logs', return_value=[]), \
                mock.patch.object(policy.windows_messages, 'read_message_table', return_value=MESSAGES), \
                mock.patch.object(policy, 'logfunc') as log:
            mui = '/case/data/vol1/Windows/System32/en-US/msobjs.dll.mui'
            _headers, rows, source = policy.auditPolicyChanges.__wrapped__(_Context([LOG, mui]))
        self.assertEqual(rows, [(utc(2026, 9, 30, 13, 46, 47, 973286), 'Detailed Tracking (%%8276)',
                                 'Process Creation (%%13312)', '{0cce922b-69ae-11d9-bed3-505054503030}',
                                 'Success Added (%%8449)', *SUBJECT_ROW, '21871', 'LAB-PC')])
        self.assertEqual(source, LOG + '\n' + mui)
        self.assertEqual(log.call_count, 1)


if __name__ == '__main__':
    unittest.main()
