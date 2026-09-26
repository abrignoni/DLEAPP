"""Pin the rows and value naming of scripts/artifacts/windowsFirewallEvents.py."""
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsFirewallEvents as fwe  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
_LOG_PATH = ('/case/data/vol/Windows/System32/winevt/Logs/'
             'Microsoft-Windows-Windows Firewall With Advanced Security%4Firewall.evtx')
_DLL_PATH = '/case/data/vol/Windows/System32/MPSSVC.dll'
_MUI_PATH = '/case/data/vol/Windows/System32/en-US/mpssvc.dll.mui'

RULE_HEADERS = ('Time', 'Change', 'Rule ID', 'Rule Name', 'Application Path', 'Service Name',
                'Direction', 'Protocol', 'Local Ports', 'Remote Ports', 'Local Addresses',
                'Remote Addresses', 'Action', 'Profiles', 'Active', 'Edge Traversal',
                'Rule Group', 'Origin', 'Store Type', 'Modifying User',
                'Modifying Application', 'Error Code', 'Other Fields', 'Event ID', 'Record ID')

# (event id, version) -> field -> number -> message id, and message id -> text, the shape
# windows_messages returns for a DLL and its .mui.
_MAPS = {
    (2071, 0): {'Action': {2: 102, 3: 103}, 'Direction': {1: 111}, 'Origin': {1: 121}},
    (2002, 0): {'SettingType': {2: 202}, 'Origin': {1: 121}},
    (2011, 0): {'ReasonCode': {2: 302}, 'Protocol': {6: 306}, 'IPVersion': {0: 310}},
}
_MESSAGES = {102: 'Block', 103: 'Allow', 111: 'Inbound', 121: 'Local', 202: 'Current Profile',
             302: 'The application is non interactive', 306: 'TCP', 310: 'IPv4'}


def event(event_id, fields, source=_LOG_PATH):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields.items())
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="{fwe._PROVIDER}"/>'  # pylint: disable=protected-access
           f'<EventID>{event_id}</EventID><Version>0</Version>'
           '<TimeCreated SystemTime="2022-12-08 03:30:17.000000+00:00"/>'
           f'<EventRecordID>41</EventRecordID></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


class FakeContext:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return list(self.files)

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1]


def names_for(files):
    with mock.patch.object(fwe.windows_messages, 'read_event_value_maps', return_value=_MAPS), \
         mock.patch.object(fwe.windows_messages, 'read_message_table', return_value=_MESSAGES):
        names = fwe._Names(FakeContext(files))  # pylint: disable=protected-access
        for root in list(names.files):
            names._load(root[0])  # pylint: disable=protected-access
    return names


class RuleChangeRowTest(unittest.TestCase):
    def test_numbers_are_named_from_the_files_beside_the_log(self):
        names = names_for([_LOG_PATH, _DLL_PATH, _MUI_PATH])
        row = dict(zip(RULE_HEADERS, fwe.rule_change_row(event('2071', {
            'RuleId': 'TCP Query User{X}C:\\a.exe', 'RuleName': 'a.exe', 'Origin': '0',
            'ApplicationPath': 'C:\\a.exe', 'Direction': '1', 'Protocol': '6', 'Action': '2',
            'RemoteMachineAuthorizationList': '', 'Flags': '1', 'SchemaVersion': '544',
            'ModifyingUser': 'S-1-5-18', 'ErrorCode': '0',
        }), names)))
        self.assertEqual(row['Change'], 'Rule added')
        self.assertEqual((row['Action'], row['Direction']), ('Block (2)', 'Inbound (1)'))
        self.assertEqual(row['Origin'], '0')
        self.assertEqual(row['Protocol'], '6')
        self.assertEqual(row['Other Fields'], 'Flags: 1 | SchemaVersion: 544')
        self.assertEqual((row['Rule ID'], row['Modifying User'], row['Error Code']),
                         ('TCP Query User{X}C:\\a.exe', 'S-1-5-18', '0'))
        self.assertEqual((row['Event ID'], row['Record ID']), ('2071', '41'))
        self.assertEqual(names.kept['not in the map'], 1)
        self.assertEqual(names.files_used(), sorted([_DLL_PATH, _MUI_PATH]))

    def test_a_log_on_another_volume_keeps_its_numbers(self):
        names = names_for([_DLL_PATH, _MUI_PATH])
        other_log = _LOG_PATH.replace('/data/vol/', '/data/old/')
        row = dict(zip(RULE_HEADERS, fwe.rule_change_row(
            event('2071', {'RuleId': 'R', 'Action': '3'}, other_log), names)))
        self.assertEqual(row['Action'], '3')
        self.assertEqual(names.kept['no value map'], 1)
        self.assertEqual(names.files_used(), [])

    def test_a_deleted_rule_has_only_its_own_fields(self):
        names = names_for([_LOG_PATH, _DLL_PATH, _MUI_PATH])
        row = dict(zip(RULE_HEADERS, fwe.rule_change_row(event('2006', {
            'RuleId': 'R', 'RuleName': 'n', 'ModifyingUser': 'S-1-5-19',
            'ModifyingApplication': 'C:\\Windows\\System32\\svchost.exe'}), names)))
        self.assertEqual(row['Change'], 'Rule deleted')
        self.assertEqual((row['Action'], row['Other Fields']), ('', ''))


class SettingAndBlockedRowTest(unittest.TestCase):
    def test_setting_row_decodes_the_stored_value(self):
        names = names_for([_LOG_PATH, _DLL_PATH, _MUI_PATH])
        row = fwe.setting_change_row(event('2002', {
            'SettingType': '2', 'SettingValueSize': '4', 'SettingValue': 'AgAAAA==',
            'SettingValueDisplay': 'Private', 'Origin': '1', 'ModifyingUser': 'S-1-5-19'}), names)
        self.assertEqual(row[1:10], ('Setting changed', '', 'Current Profile (2)', 'Private',
                                     'Local (1)', 'S-1-5-19', '', '', '02000000'))

    def test_profile_setting_row_takes_the_string_value(self):
        names = names_for([])
        row = fwe.setting_change_row(event('2003', {
            'Profiles': '4', 'SettingType': '1', 'SettingValue': 'AAAAAA==',
            'SettingValueString': 'No'}), names)
        self.assertEqual(row[1:5], ('Profile setting changed', '4', '1', 'No'))
        self.assertEqual(row[9], '00000000')

    def test_blocked_app_row(self):
        names = names_for([_LOG_PATH, _DLL_PATH, _MUI_PATH])
        row = fwe.blocked_app_row(event('2011', {
            'ReasonCode': '2', 'ApplicationPath': 'C:\\a.exe', 'IPVersion': '0', 'Protocol': '6',
            'Port': '57122', 'ProcessId': '3236', 'ModifyingUser': 'S-1-5-21-1'}), names)
        self.assertEqual(row[1:8], ('C:\\a.exe', '57122', 'TCP (6)', 'IPv4 (0)', '3236',
                                    'The application is non interactive (2)', 'S-1-5-21-1'))


class BinaryHexTest(unittest.TestCase):
    def test_base64_is_hex_and_anything_else_is_kept(self):
        self.assertEqual(fwe.binary_hex('AgAAAA=='), '02000000')
        self.assertEqual(fwe.binary_hex(''), '')
        self.assertEqual(fwe.binary_hex('not base64!'), 'not base64!')


if __name__ == '__main__':
    unittest.main()
