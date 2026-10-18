"""Pin the rows in scripts/artifacts/windowsAppLockerEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up paths, names and hashes);
the expected rows are written out. In the tested logs 8001 has no event data, 8003 is UserData holding a
RuleAndFileData element, 8037 and 8038 are plain EventData, an 8038 can carry ProcessingErrorData instead, and 8043
is UserData holding a RegisterUninstallStringEventData element; each shape is built here. The packaged app record
(8022) follows the field names Microsoft's AaronLocker script reads; no tested log holds one.
"""
import base64
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsAppLockerEvents as applocker  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOGS = '/case/data/vol1/Windows/System32/winevt/Logs/'
EXE = LOGS + 'Microsoft-Windows-AppLocker%4EXE and DLL.evtx'
MSI = LOGS + 'Microsoft-Windows-AppLocker%4MSI and Script.evtx'
PACKAGED = LOGS + 'Microsoft-Windows-AppLocker%4Packaged app-Execution.evtx'

SHA1 = bytes(range(20))
SHA256 = bytes(range(32, 64))


def b64(raw):
    return base64.b64encode(raw).decode()


def record(when, record_id, event_id, body, version='0', channel='EXE and DLL', user='S-1-5-18', pid='4',
           provider='Microsoft-Windows-AppLocker'):
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" '
           f'Guid="{{cbda4dbf-8d5d-4f69-9578-be14aa540d22}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="{pid}" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-AppLocker/{channel}</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="{user}"></Security></System>{body}</Event>')
    return EventRecord(ElementTree.fromstring(xml), EXE)


def user_data(element, fields):
    data = ''.join(f'<{name}>{value}</{name}>' for name, value in fields)
    return (f'<UserData><{element} xmlns="http://schemas.microsoft.com/schemas/event/Microsoft.Windows/1.0.0.0">'
            f'{data}</{element}></UserData>')


def event_data(fields):
    return '<EventData>' + ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields) + '</EventData>'


def rule_fields(path_field, path):
    return [('PolicyNameLength', '3'), ('PolicyName', 'EXE'), ('RuleId', '{00000000-0000-0000-0000-000000000001}'),
            ('RuleNameLength', '9'), ('RuleName', 'Lab rule'), ('RuleSddlLength', '1'), ('RuleSddl', 'D:(XA;;FX;;;WD)'),
            ('TargetUser', 'S-1-5-21-1-2-3-1001'), ('TargetProcessId', '4242'), (path_field + 'Length', '20'),
            (path_field, path)]


WHEN = '2026-10-18 05:24:32.108000+00:00'
TIME = datetime.datetime(2026, 10, 18, 5, 24, 32, 108000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [EXE, MSI, PACKAGED]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class HelperTest(unittest.TestCase):
    def test_binary_hex(self):
        self.assertEqual(applocker.binary_hex(b64(SHA1)), SHA1.hex().upper())
        self.assertEqual(applocker.binary_hex(''), '')
        self.assertEqual(applocker.binary_hex(' '), '')
        self.assertEqual(applocker.binary_hex('-'), '-')
        self.assertEqual(applocker.binary_hex('0xABCD'), '0xABCD')
        self.assertEqual(applocker.binary_hex('QUJD\n'), '414243')
        self.assertEqual(applocker.binary_hex('QUJ'), 'QUJ')

    def test_signed_hex(self):
        self.assertEqual(applocker.signed_hex('0'), '0x00000000 (0)')
        self.assertEqual(applocker.signed_hex('-790036478'), '0xD0E90002 (-790036478)')
        self.assertEqual(applocker.signed_hex('4294967295'), '0xFFFFFFFF (4294967295)')
        self.assertEqual(applocker.signed_hex('4294967296'), '4294967296')
        self.assertEqual(applocker.signed_hex('0x5'), '0x5')
        self.assertEqual(applocker.signed_hex(''), '')

    def test_the_event_tables_do_not_overlap(self):
        rule = set(applocker._RULE_EVENTS)  # pylint: disable=protected-access
        ci = set(applocker._CONFIG_CI_EVENTS)  # pylint: disable=protected-access
        policy = set(applocker._POLICY_EVENTS)  # pylint: disable=protected-access
        self.assertEqual(rule, {str(n) for n in range(8002, 8008)} | {str(n) for n in range(8020, 8026)})
        self.assertEqual(ci, {'8028', '8029', '8036', '8037', '8038', '8039', '8040'})
        self.assertEqual(policy, {'8000', '8001', '8008', '8009', '8026', '8027', '8041', '8042', '8043', '8044'})
        self.assertFalse(rule & ci or rule & policy or ci & policy)


class RuleRowTest(unittest.TestCase):
    def test_an_audited_file(self):
        fields = rule_fields('FilePath', '%SYSTEM32%\\LAB.DLL') + [
            ('FileHashLength', '32'), ('FileHash', b64(SHA256)), ('FqbnLength', '1'), ('Fqbn', '-'),
            ('TargetLogonId', '0x00000000000003e7'), ('FullFilePathLength', '27'),
            ('FullFilePath', 'C:\\Windows\\System32\\lab.dll')]
        row = applocker.rule_row(record(WHEN, '11', '8003', user_data('RuleAndFileData', fields)))
        self.assertEqual(row, (TIME, '8003', applocker._AUDITED, 'EXE',  # pylint: disable=protected-access
                               'C:\\Windows\\System32\\lab.dll', '%SYSTEM32%\\LAB.DLL', '', SHA256.hex().upper(), '-',
                               'Lab rule', '{00000000-0000-0000-0000-000000000001}', 'D:(XA;;FX;;;WD)',
                               'S-1-5-21-1-2-3-1001', '4242', '0x00000000000003e7',
                               'Microsoft-Windows-AppLocker/EXE and DLL', '0', '11', 'LAB-PC'))

    def test_an_older_record_without_full_path_or_logon_id(self):
        fields = rule_fields('FilePath', '%OSDRIVE%\\TOOLS\\LAB.EXE') + [('FileHashLength', '0'), ('FileHash', '')]
        row = applocker.rule_row(record(WHEN, '12', '8004', user_data('RuleAndFileData', fields)))
        self.assertEqual(row[1:9], ('8004', 'Prevented from running', 'EXE', '', '%OSDRIVE%\\TOOLS\\LAB.EXE', '', '',
                                    ''))
        self.assertEqual(row[14], '')

    def test_a_packaged_app_is_read_from_package(self):
        fields = rule_fields('Package', 'LAB.APP_1.0.0.0_X64__ABC') + [
            ('FqbnLength', '30'), ('Fqbn', 'CN=LAB\\LAB.APP\\APPX\\1.0.0.0')]
        row = applocker.rule_row(record(WHEN, '13', '8022', user_data('RuleAndFileData', fields),
                                        channel='Packaged app-Execution'))
        self.assertEqual(row[1:9], ('8022', 'Prevented from running', 'EXE', '', '', 'LAB.APP_1.0.0.0_X64__ABC', '',
                                    'CN=LAB\\LAB.APP\\APPX\\1.0.0.0'))

    def test_outcomes(self):
        outcomes = {event_id: applocker.rule_row(record(WHEN, '1', event_id, ''))[2]
                    for event_id in ('8002', '8005', '8020', '8023', '8006', '8021', '8024', '8007', '8025')}
        self.assertEqual(outcomes, {'8002': 'Allowed to run', '8005': 'Allowed to run', '8020': 'Allowed to run',
                                    '8023': 'Allowed to be installed', '8006': applocker._AUDITED,  # pylint: disable=protected-access
                                    '8021': applocker._AUDITED, '8024': applocker._AUDITED,  # pylint: disable=protected-access
                                    '8007': 'Prevented from running', '8025': 'Prevented from running'})


class ConfigCiRowTest(unittest.TestCase):
    def test_a_file_that_passed(self):
        fields = [('FilePathLength', '18'), ('FilePath', 'C:\\Lab\\setup.msi'), ('Sha1Hash', b64(SHA1)),
                  ('Sha256Hash', b64(SHA256)), ('Result', '0'), ('USN', '410001616'),
                  ('Sha1CatalogHash', b64(SHA1)), ('Sha256CatalogHash', b64(bytes(32))),
                  ('UserWriteable', 'False'), ('DetachedSignatureFilePathLength', '0'),
                  ('DetachedSignatureFilePath', ''), ('OriginalFileNameLength', '9'),
                  ('OriginalFilename', 'setup.msi'), ('InternalNameLength', '0'), ('InternalName', ''),
                  ('FileDescriptionLength', '0'), ('FileDescription', ''), ('ProductNameLength', '3'),
                  ('ProductName', 'Lab'), ('FileVersionLength', '7'), ('FileVersion', '1.0.0.0')]
        row = applocker.config_ci_row(record(WHEN, '21', '8037', event_data(fields), '2', 'MSI and Script',
                                             'S-1-5-21-1-2-3-1001', '7000'))
        self.assertEqual(row, (TIME, '8037', 'Passed Config CI policy and was allowed to run', 'C:\\Lab\\setup.msi',
                               SHA256.hex().upper(), SHA1.hex().upper(), '00' * 32, SHA1.hex().upper(), 'setup.msi',
                               '', '', 'Lab', '1.0.0.0', 'False', '0x00000000 (0)', '410001616', '', '', '', '', '',
                               '', '', '', '', '', 'S-1-5-21-1-2-3-1001', '7000',
                               'Microsoft-Windows-AppLocker/MSI and Script', '2', '21', 'LAB-PC'))

    def test_publisher_info_and_a_processing_error(self):
        fields = [('TotalSignatureCount', '1'), ('Signature', '0'), ('PublisherNameLength', '6'),
                  ('PublisherName', 'CN=Lab'), ('IssuerNameLength', '9'), ('IssuerName', 'CN=Lab CA'),
                  ('PublisherTBSHashSize', '0'), ('PublisherTBSHash', ''), ('IssuerTBSHashSize', '0'),
                  ('IssuerTBSHash', '')]
        row = applocker.config_ci_row(record(WHEN, '22', '8038', event_data(fields), channel='MSI and Script'))
        self.assertEqual(row[1:3] + row[16:20], ('8038', 'Publisher info', 'CN=Lab', 'CN=Lab CA', '0', '1'))
        error = ('<ProcessingErrorData><ErrorCode>15005</ErrorCode><DataItemName>Signature</DataItemName>'
                 '<EventPayload>QUJD</EventPayload></ProcessingErrorData>')
        row = applocker.config_ci_row(record(WHEN, '23', '8038', error, channel='MSI and Script'))
        self.assertEqual(row[25], '15005')
        self.assertEqual(set(row[3:25]), {''})

    def test_a_package_prevented_and_a_clsid(self):
        fields = [('PackageFamilyNameLength', '10'), ('PackageFamilyName', 'Lab.App_ab'),
                  ('PackageVersion', '281474976710656'), ('PolicyNameLength', '3'), ('PolicyName', 'Lab'),
                  ('PolicyIDLength', '3'), ('PolicyID', 'P01'), ('PolicyVersion', '1'),
                  ('PolicyGuid', '{00000000-0000-0000-0000-000000000002}'), ('Status', '0xc0e90002')]
        row = applocker.config_ci_row(record(WHEN, '24', '8040', event_data(fields), channel='MSI and Script'))
        self.assertEqual(row[1:3] + row[20:25],
                         ('8040', 'Prevented from installing or updating due to Config CI policy', 'Lab.App_ab',
                          '281474976710656', 'Name:Lab ID:P01 Version:1 GUID:{00000000-0000-0000-0000-000000000002}',
                          '0xc0e90002', ''))
        row = applocker.config_ci_row(record(WHEN, '25', '8036', event_data(
            [('IsApproved', 'false'), ('CLSID', '{00000000-0000-0000-0000-000000000003}')]), channel='MSI and Script'))
        self.assertEqual(row[1:3] + row[22:25], ('8036', 'Prevented from running due to Config CI policy', '', '',
                                                  '{00000000-0000-0000-0000-000000000003}'))


class PolicyRowTest(unittest.TestCase):
    def test_policy_applied_has_no_fields(self):
        self.assertEqual(applocker.policy_row(record(WHEN, '31', '8001', '')),
                         (TIME, '8001', 'The AppLocker policy was applied successfully to this computer.', '', '', '',
                          '', '', '', '', '', 'S-1-5-18', '4', 'Microsoft-Windows-AppLocker/EXE and DLL', '0', '31',
                          'LAB-PC'))

    def test_an_uninstall_string_registration(self):
        fields = [('UninstallStringLength', '20'), ('UninstallString', '"C:\\Lab\\uninst.exe" /S'),
                  ('UninstallerPathLength', '17'), ('UninstallerPath', 'C:\\Lab\\uninst.exe'),
                  ('ProcessNameLength', '30'), ('ProcessName', '\\Device\\HarddiskVolume3\\Lab\\setup.exe'),
                  ('SessionId', '{00000000-0000-0000-0000-000000000004}'),
                  ('SubSessionId', '{00000000-0000-0000-0000-000000000005}'), ('Status', '0x00000000')]
        row = applocker.policy_row(record(WHEN, '32', '8043', user_data('RegisterUninstallStringEventData', fields),
                                          user='S-1-5-21-1-2-3-1001', pid='9000'))
        self.assertEqual(row[1:13], ('8043', 'Process %6 attempted to register UninstallString %2, Status: %9.',
                                     '\\Device\\HarddiskVolume3\\Lab\\setup.exe', '"C:\\Lab\\uninst.exe" /S',
                                     'C:\\Lab\\uninst.exe', '', '', '', '', '0x00000000', 'S-1-5-21-1-2-3-1001',
                                     '9000'))

    def test_the_other_fields(self):
        row = applocker.policy_row(record(WHEN, '33', '8044', event_data(
            [('Cmdline', 'uninst.exe /S'), ('MatchFound', 'true'), ('Status', '0x0')])))
        self.assertEqual(row[6:11], ('uninst.exe /S', 'true', '', '', '0x0'))
        row = applocker.policy_row(record(WHEN, '34', '8042', event_data([('AuditInfo', 'lab script')])))
        self.assertEqual(row[8], 'lab script')
        row = applocker.policy_row(record(WHEN, '35', '8008', event_data([('FilePathBuffer', 'C:\\lab.exe')])))
        self.assertEqual(row[9], 'C:\\lab.exe')


class ArtifactTest(unittest.TestCase):
    def _run(self, function):
        calls = []

        def fake_read(_context, file_name, label, event_ids=None, provider=None):
            calls.append((file_name, label, event_ids, provider))
            if file_name.endswith('%4exe and dll.evtx'):
                return [record(WHEN, '2', '8003', ''), record(WHEN, '1', '8001', '')], [EXE]
            if file_name.endswith('%4msi and script.evtx'):
                return [record(WHEN, '7', '8037', '', channel='MSI and Script')], [MSI]
            return [], []

        with mock.patch.object(applocker, 'read_event_records', side_effect=fake_read):
            return function.__wrapped__(_Context()), calls

    def test_each_log_is_read_for_its_events_of_the_provider_in_log_order(self):
        for function, label, table in (
                (applocker.appLockerRuleEvents, 'AppLocker Rule Events',
                 applocker._RULE_EVENTS),  # pylint: disable=protected-access
                (applocker.appLockerConfigCiEvents, 'AppLocker Config CI Events',
                 applocker._CONFIG_CI_EVENTS),  # pylint: disable=protected-access
                (applocker.appLockerPolicyEvents, 'AppLocker Policy Events',
                 applocker._POLICY_EVENTS)):  # pylint: disable=protected-access
            (headers, rows, source), calls = self._run(function)
            self.assertEqual([call[0] for call in calls],
                             ['microsoft-windows-applocker%4exe and dll.evtx',
                              'microsoft-windows-applocker%4msi and script.evtx',
                              'microsoft-windows-applocker%4packaged app-deployment.evtx',
                              'microsoft-windows-applocker%4packaged app-execution.evtx'])
            self.assertTrue(all(call[1:] == (label, set(table), 'Microsoft-Windows-AppLocker') for call in calls))
            self.assertEqual(source, EXE + '\n' + MSI)
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(len(row) == len(headers) for row in rows))
            self.assertEqual(headers[0], ('Event Time (UTC)', 'datetime'))

    def test_no_log_gives_no_rows_and_no_source(self):
        with mock.patch.object(applocker, 'read_event_records', return_value=([], [])):
            for function in (applocker.appLockerRuleEvents, applocker.appLockerConfigCiEvents,
                             applocker.appLockerPolicyEvents):
                self.assertEqual(function.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
