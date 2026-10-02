"""Pin the rows of the compatibility, device setup, user profile and OpenSSH event log artifacts."""
import datetime
import itertools
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree
from xml.sax.saxutils import escape

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsCompatibilityEvents as compat
from scripts.artifacts import windowsDeviceSetupEvents as dsm
from scripts.artifacts import windowsOpenSshEvents as ssh
from scripts.artifacts import windowsUserProfileEvents as ups
from scripts.windows_evtx import EventRecord
# pylint: enable=wrong-import-position

_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
_UTC = datetime.timezone.utc


def event(provider, event_id, fields, user_data=None, sid='S-1-5-18', pid='1940'):
    """An EventRecord like python-evtx renders one, with EventData or a UserData element."""
    items = ''.join(f'<{name}>{escape(value)}</{name}>' if user_data else
                    f'<Data Name="{name}">{escape(value)}</Data>'
                    for name, value in fields.items())
    body = (f'<UserData><{user_data} xmlns="urn:test">{items}</{user_data}></UserData>'
            if user_data else f'<EventData>{items}</EventData>')
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="{provider}"/>'
           f'<EventID>{event_id}</EventID><Version>0</Version>'
           '<TimeCreated SystemTime="2022-12-08 03:30:17.250000+00:00"/>'
           '<EventRecordID>41</EventRecordID>'
           f'<Execution ProcessID="{pid}" ThreadID="2"/><Computer>HOST</Computer>'
           f'<Security UserID="{sid}"/></System>{body}</Event>')
    return EventRecord(ElementTree.fromstring(xml), '/case/data/vol/log.evtx')


def at(text):
    return datetime.datetime.fromisoformat(text).astimezone(_UTC)


class CompatibilityFixTest(unittest.TestCase):
    def fix(self, **overrides):
        fields = {'ProcessId': '5716', 'StartTime': '2022-11-23 00:43:27.659943+00:00',
                  'FixID': '{d10ebdb2-9881-4161-a4ac-bbb93344d224}', 'Flags': '0x80010101',
                  'ExePath': 'C:\\Program Files\\App\\app.exe', 'FixName': 'Some Fix'}
        fields.update(overrides)
        return event(compat._TELEMETRY_PROVIDER, '505', fields,  # pylint: disable=protected-access
                     user_data='CompatibilityFixEvent', sid='S-1-5-21-1-2-3-1001')

    def test_row_keeps_the_process_start_time_and_the_fix(self):
        row = compat.fix_row(self.fix())
        self.assertEqual(row[0], at('2022-12-08T03:30:17.250000+00:00'))
        self.assertEqual(row[1], at('2022-11-23T00:43:27.659943+00:00'))
        self.assertEqual(row[2:], ('505', 'C:\\Program Files\\App\\app.exe', '5716', 'Some Fix',
                                   '{d10ebdb2-9881-4161-a4ac-bbb93344d224}', '0x80010101',
                                   'S-1-5-21-1-2-3-1001', '41', 'HOST'))

    def test_a_start_time_that_does_not_parse_is_blank(self):
        self.assertEqual(compat.fix_row(self.fix(StartTime=''))[1], '')
        self.assertEqual(compat.fix_row(self.fix(StartTime='not a time'))[1], '')

    def test_resolver_row(self):
        record = event(compat._PCA_PROVIDER, '17',  # pylint: disable=protected-access
                       {'ExePath': 'C:\\Users\\u\\Downloads\\setup.exe',
                        'ResolverName': 'CrashOnLaunch'}, user_data='ResolverFiredEvent')
        self.assertEqual(compat.resolver_row(record)[1:],
                         ('C:\\Users\\u\\Downloads\\setup.exe', 'CrashOnLaunch', '41', 'HOST'))


class DeviceSetupTest(unittest.TestCase):
    def row(self, event_id, fields):
        return dict(zip(('Time', 'Event ID', 'Event', 'Device Name', 'Container ID',
                         'Device Instance ID', 'Driver Package ID', 'Software', 'Store Link',
                         'Result', 'Record ID', 'Computer'),
                        dsm.device_row(event(dsm._PROVIDER, event_id, fields))))  # pylint: disable=protected-access

    def test_serviced_and_removed_devices_have_their_name_and_container(self):
        for event_id in ('112', '150', '151'):
            row = self.row(event_id, {'Prop_DeviceName': 'Cruzer Dial',
                                      'Prop_ContainerId': '{0235bed7-f417-50d9-8aa9-900220de8ee4}',
                                      'Prop_TaskCount': '7', 'Prop_PropertyCount': '12',
                                      'Prop_WorkTime_MilliSeconds': '120'})
            self.assertEqual((row['Event'], row['Device Name'], row['Container ID']),
                             (dsm._EVENTS[event_id], 'Cruzer Dial',  # pylint: disable=protected-access
                              '{0235bed7-f417-50d9-8aa9-900220de8ee4}'))
            self.assertEqual((row['Device Instance ID'], row['Driver Package ID'], row['Software'],
                              row['Store Link'], row['Result']), ('',) * 5)
        self.assertEqual(self.row('150', {})['Event'], 'The device has been removed')

    def test_each_event_takes_the_instance_id_from_its_own_field(self):
        cases = {
            '121': ({'Prop_DevnodeId': 'USB\\VID_0E0F&PID_0003\\1', 'HRESULT': '2149842974'},
                    'USB\\VID_0E0F&PID_0003\\1'),
            '123': ({'Prop_Seconds': '29', 'Prop_DeviceId': 'PCI\\VEN_1\\2'}, 'PCI\\VEN_1\\2'),
            '124': ({'Prop_PackageId': 'pkg-2', 'Prop_DeviceInstanceId': 'USB\\A\\1',
                     'Prop_MilliSeconds': '9'}, 'USB\\A\\1'),
            '125': ({'Prop_DevnodeId': 'USB\\B\\1'}, 'USB\\B\\1'),
            '126': ({'Prop_DeviceInstanceId': 'ACPI\\X\\1', 'Prop_PackageId': 'pkg-1'},
                    'ACPI\\X\\1'),
            '152': ({'Prop_DevnodeId': 'USB\\C\\1', 'HRESULT': '5'}, 'USB\\C\\1'),
            '160': ({'Prop_SoftwareName': 'Helper App', 'Prop_DeviceInstanceId': 'BTH\\D\\1',
                     'Prop_InstallTime': '7'}, 'BTH\\D\\1'),
            '166': ({'Prop_DeviceInstanceId': 'SWD\\Y\\1', 'Prop_SoftwareLinks': 'Pfn_1'},
                    'SWD\\Y\\1'),
            '234': ({'Prop_DevnodeId': 'ACPI\\Z\\1', 'Prop_MilliSeconds': '31463'}, 'ACPI\\Z\\1'),
        }
        for event_id, (fields, instance) in cases.items():
            row = self.row(event_id, fields)
            self.assertEqual(row['Device Instance ID'], instance, event_id)
            self.assertEqual(row['Event'], dsm._EVENTS[event_id])  # pylint: disable=protected-access
            self.assertEqual((row['Device Name'], row['Container ID']), ('', ''), event_id)
        self.assertEqual(self.row('121', cases['121'][0])['Result'], '0x8024001E (2149842974)')
        self.assertEqual(self.row('152', cases['152'][0])['Result'], '0x00000005 (5)')
        self.assertEqual(self.row('124', cases['124'][0])['Driver Package ID'], 'pkg-2')
        self.assertEqual(self.row('126', cases['126'][0])['Driver Package ID'], 'pkg-1')
        self.assertEqual(self.row('160', cases['160'][0])['Software'], 'Helper App')
        self.assertEqual(self.row('166', cases['166'][0])['Store Link'], 'Pfn_1')
        self.assertEqual(self.row('112', {'HRESULT': '5', 'Prop_PackageId': 'p',
                                          'Prop_SoftwareName': 's'})['Result'], '')
        self.assertEqual(self.row('112', {'Prop_PackageId': 'p'})['Driver Package ID'], '')

    def test_a_removal_failure_with_the_newer_fields_has_its_name_and_container(self):
        row = self.row('152', {'Prop_DeviceName': 'Example Printer', 'Prop_ContainerId': '{0000-1}', 'HRESULT': '5'})
        self.assertEqual((row['Device Name'], row['Container ID'], row['Device Instance ID'], row['Result']),
                         ('Example Printer', '{0000-1}', '', '0x00000005 (5)'))
        older = self.row('152', {'Prop_DevnodeId': 'USB\\C\\1', 'HRESULT': '5'})
        self.assertEqual((older['Device Name'], older['Container ID'], older['Device Instance ID']), ('', '', 'USB\\C\\1'))


class UserProfileTest(unittest.TestCase):
    def row(self, event_id, fields, sid='S-1-5-18'):
        return dict(zip(('Time', 'Event ID', 'Event', 'User SID', 'Session', 'Hive File',
                         'HKU Key', 'Logon Type', 'Profile Location', 'Profile Type',
                         'Record ID', 'Computer'),
                        ups.profile_row(event(ups._PROVIDER, event_id, fields, sid=sid))))  # pylint: disable=protected-access

    def test_logon_and_logoff_carry_the_session_and_the_record_sid(self):
        for event_id, label in (('1', 'Received user logon notification'),
                                ('3', 'Received user logoff notification')):
            row = self.row(event_id, {'Session': '2'}, sid='S-1-5-21-1-2-3-1001')
            self.assertEqual((row['Event'], row['User SID'], row['Session']),
                             (label, 'S-1-5-21-1-2-3-1001', '2'))
            self.assertEqual((row['Hive File'], row['Profile Location']), ('', ''))

    def test_hive_load_and_profile_details(self):
        row = self.row('5', {'File': 'C:\\Users\\u\\ntuser.dat', 'Key': 'S-1-5-21-1-2-3-1001'})
        self.assertEqual((row['Hive File'], row['HKU Key'], row['Session']),
                         ('C:\\Users\\u\\ntuser.dat', 'S-1-5-21-1-2-3-1001', ''))
        row = self.row('67', {'LogonType': 'Regular', 'LocalPath': 'C:\\Users\\u',
                              'ProfileType': 'Temporary'})
        self.assertEqual((row['Logon Type'], row['Profile Location'], row['Profile Type']),
                         ('Regular', 'C:\\Users\\u', 'Temporary'))
        self.assertEqual(row['Hive File'], '')


# auth.c auth_log(), Win32-OpenSSH v7.7.2.0 and v10.0.0.0.
_AUTH_FORMAT = '%s %s%s%s for %s%.100s from %.200s port %d ssh2%s%s'


class OpenSshTest(unittest.TestCase):
    def test_lines_built_from_the_sshd_format_are_split_back_out(self):
        combinations = itertools.product(
            ('Accepted', 'Failed', 'Postponed', 'Partial'),
            (('password', None), ('keyboard-interactive', 'pam'), ('publickey', None)),
            (True, False),
            ('IEUser', 'first last'),
            ('192.168.150.1', 'fe80::1%3'),
            (None, 'ED25519 SHA256:aGVsbG8'))
        for result, (method, sub), valid, user, address, extra in combinations:
            line = _AUTH_FORMAT % (result, method, '/' if sub else '', sub or '',
                                   '' if valid else 'invalid user ', user, address, 64621,
                                   ': ' if extra else '', extra or '')
            expected = (result, f'{method}/{sub}' if sub else method, user,
                        '' if valid else 'Yes', address, '64621')
            self.assertEqual(ssh.login_fields(line), expected, line)

    def test_invalid_user_line(self):
        self.assertEqual(ssh.login_fields('Invalid user admin from 10.0.0.5 port 50000'),
                         ('', '', 'admin', 'Yes', '10.0.0.5', '50000'))

    def test_other_messages_leave_the_login_columns_blank(self):
        for line in ('Server listening on :: port 22.',
                     'Did not receive identification string from 192.168.150.1 port 64620',
                     'Received signal 8; terminating.', ''):
            self.assertEqual(ssh.login_fields(line), ('',) * 6, line)

    def test_row_names_the_level_and_keeps_the_record_process(self):
        for event_id, level in (('1', 'Critical'), ('2', 'Error'), ('3', 'Warning'),
                                ('4', 'Informational')):
            row = ssh.ssh_row(event(ssh._PROVIDER, event_id, {  # pylint: disable=protected-access
                'process': 'sshd',
                'payload': 'Accepted password for IEUser from 192.168.150.1 port 64621 ssh2'},
                pid='7852'))
            self.assertEqual(row[1:5], (event_id, level, 'sshd',
                                        'Accepted password for IEUser from 192.168.150.1 port '
                                        '64621 ssh2'))
            self.assertEqual(row[5:], ('Accepted', 'password', 'IEUser', '', '192.168.150.1',
                                       '64621', '7852', '41', 'HOST'))


class ProcessorTest(unittest.TestCase):
    """Each processor asks for its own log, provider and events, and cites what it read."""

    def run_processor(self, processor, records_by_log):
        calls = []

        def fake_read(_context, file_name, _label, event_ids=None, provider=None):
            calls.append((file_name, frozenset(event_ids), provider))
            records = records_by_log.get(file_name, [])
            return records, [f'/case/data/vol/{file_name}'] if records else []

        module = sys.modules[processor.__module__]
        with mock.patch.object(module, 'read_event_records', side_effect=fake_read):
            _headers, rows, source = processor.__wrapped__(object())
        return calls, rows, source

    def test_reads(self):
        calls, rows, source = self.run_processor(compat.compatibilityFixEvents, {})
        self.assertEqual(calls, [(compat._TELEMETRY_LOG, frozenset({'500', '505'}),  # pylint: disable=protected-access
                                  'Microsoft-Windows-Application-Experience')])
        self.assertEqual((rows, source), ([], ''))
        calls, _rows, _source = self.run_processor(compat.pcaResolverEvents, {})
        self.assertEqual(calls, [(compat._PCA_LOG, frozenset({'17'}),  # pylint: disable=protected-access
                                  'Microsoft-Windows-Program-Compatibility-Assistant')])
        calls, _rows, _source = self.run_processor(dsm.deviceSetupManagerEvents, {})
        device_events = frozenset({'112', '121', '123', '124', '125', '126', '150', '151', '152',
                                   '160', '166', '234'})
        self.assertEqual(calls, [(dsm._LOG, device_events,  # pylint: disable=protected-access
                                  'Microsoft-Windows-DeviceSetupManager')])
        calls, _rows, _source = self.run_processor(ups.userProfileServiceEvents, {})
        self.assertEqual(calls, [(ups._LOG, frozenset({'1', '3', '5', '67'}),  # pylint: disable=protected-access
                                  'Microsoft-Windows-User Profiles Service')])

    def test_openssh_reads_both_logs_and_cites_each(self):
        operational = event(ssh._PROVIDER, '4', {'process': 'sshd', 'payload': 'a'})  # pylint: disable=protected-access
        admin = event(ssh._PROVIDER, '2', {'process': 'sshd', 'payload': 'b'})  # pylint: disable=protected-access
        calls, rows, source = self.run_processor(ssh.openSshEvents, {
            'OpenSSH%4Operational.evtx': [operational], 'OpenSSH%4Admin.evtx': [admin]})
        self.assertEqual([call[0] for call in calls],
                         ['OpenSSH%4Operational.evtx', 'OpenSSH%4Admin.evtx'])
        self.assertTrue(all(call[1:] == (frozenset({'1', '2', '3', '4'}), 'OpenSSH')
                            for call in calls))
        self.assertEqual([row[4] for row in rows], ['a', 'b'])
        self.assertEqual(source, '/case/data/vol/OpenSSH%4Operational.evtx\n'
                                 '/case/data/vol/OpenSSH%4Admin.evtx')

    def test_each_artifact_declares_the_log_it_reads(self):
        pairs = ((compat, 'compatibilityFixEvents', compat._TELEMETRY_LOG),  # pylint: disable=protected-access
                 (compat, 'pcaResolverEvents', compat._PCA_LOG),  # pylint: disable=protected-access
                 (dsm, 'deviceSetupManagerEvents', dsm._LOG),  # pylint: disable=protected-access
                 (ups, 'userProfileServiceEvents', ups._LOG))  # pylint: disable=protected-access
        for module, key, log in pairs:
            self.assertEqual(module.__artifacts_v2__[key]['paths'],
                             (f'*/Windows/System32/winevt/Logs/{log}',))
        self.assertEqual(ssh.__artifacts_v2__['openSshEvents']['paths'],
                         tuple(f'*/Windows/System32/winevt/Logs/{log}'
                               for log in ssh._LOGS))  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
