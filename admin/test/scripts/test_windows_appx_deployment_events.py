"""Pin the rows in scripts/artifacts/windowsAppxDeploymentEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up package names and SIDs); the
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

from scripts.artifacts import windowsAppxDeploymentEvents as appx  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-AppXDeploymentServer%4Operational.evtx'
PACKAGE = 'Example.Notes_1.2.3.0_x64__abcdefgh12345'
USER = 'S-1-5-21-1111111111-2222222222-3333333333-1001'


def record(when, record_id, event_id, fields, user='S-1-5-18'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-AppXDeployment-Server" '
           f'Guid="{{3f471139-acb7-4a01-b7a7-ff5da4ba2d43}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1000" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-AppXDeploymentServer/Operational</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="{user}"></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
STARTED = 'Started deployment operation'
RUNNING = 'Deployment operation de-queued and running for user'
FINISHED = 'Deployment operation finished successfully'
FAILED = 'Deployment operation failed'
FAILED_FOR = 'AppX Deployment operation failed for package'


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_started_record_carries_the_operation_its_main_parameter_and_the_calling_process(self):
        fields = [('DeploymentOperation', '1'), ('Path', 'file:///C:/Temp/Example.Notes.msix'), ('Flags', '0'),
                  ('FlagsHigh', '0'), ('CallingProcess', 'powershell.exe')]
        self.assertEqual(appx.deployment_row(record(WHEN, '11', '603', fields, user=USER)),
                         (TIME, '603', STARTED, '1', 'Add', '', 'file:///C:/Temp/Example.Notes.msix', '',
                          'powershell.exe', '', '', USER, '11', 'LAB-PC'))

    def test_a_running_record_carries_the_package_and_the_user_it_runs_for(self):
        fields = [('DeploymentOperation', '6'), ('PackageFullName', PACKAGE), ('UserSid', USER), ('CallingProcess', 'NULL')]
        self.assertEqual(appx.deployment_row(record(WHEN, '12', '607', fields)),
                         (TIME, '607', RUNNING, '6', 'Register', PACKAGE, '', USER, 'NULL', '', '', 'S-1-5-18', '12',
                          'LAB-PC'))

    def test_a_finished_record_has_the_white_space_around_its_path_removed(self):
        fields = [('DeploymentOperation', '2'), ('PackageFullName', PACKAGE), ('Path', ' (AppxManifest.xml) '),
                  ('MountPoint', 'C:'), ('CallingProcess', '')]
        self.assertEqual(appx.deployment_row(record(WHEN, '13', '400', fields, user=USER)),
                         (TIME, '400', FINISHED, '2', 'Remove', PACKAGE, '(AppxManifest.xml)', '', '', '', '', USER, '13',
                          'LAB-PC'))
        fields[2] = ('Path', ' ')
        self.assertEqual(appx.deployment_row(record(WHEN, '13', '400', fields))[6], '')

    def test_the_two_failure_records_carry_the_error_code_and_404_the_error_text(self):
        fields = [('DeploymentOperation', '1'), ('PackageFullName', PACKAGE), ('Path', ' (x.msix) '), ('ErrorCode', '0x80073cf3')]
        self.assertEqual(appx.deployment_row(record(WHEN, '14', '401', fields))[2:11],
                         (FAILED, '1', 'Add', PACKAGE, '(x.msix)', '', '', '0x80073cf3', ''))
        fields = [('SummaryError', 'error 0x80073CF3: Package failed updates.'), ('PackageFullName', PACKAGE),
                  ('ErrorCode', '0x80073cf3'), ('CallingProcess', 'powershell.exe')]
        self.assertEqual(appx.deployment_row(record(WHEN, '15', '404', fields))[2:11],
                         (FAILED_FOR, '', '', PACKAGE, '', '', 'powershell.exe', '0x80073cf3',
                          'error 0x80073CF3: Package failed updates.'))

    def test_operations_0_to_33_are_named_and_others_are_left_as_the_number(self):
        names = {'0': 'Invalid', '4': 'Stage', '5': 'DeStage', '12': 'PreRegisterPackage', '20': 'RegisterByPackageFamilyName',
                 '27': 'OnDemandRegisterOperation', '33': 'DeprovisionPackageOperation', '21': '', '34': '', '35': '', '99': '',
                 '': '', '06': '', '0x6': ''}
        for value, name in names.items():
            row = appx.deployment_row(record(WHEN, '16', '603', [('DeploymentOperation', value)]))
            self.assertEqual(row[3:5], (value, name), value)
        self.assertEqual(sorted(int(v) for v in appx._OPERATIONS), [n for n in range(34) if n != 21])  # pylint: disable=protected-access

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(appx.deployment_row(record(WHEN, '17', '400', [])),
                         (TIME, '400', FINISHED, '', '', '', '', '', '', '', '', 'S-1-5-18', '17', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_five_events_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '603', [('DeploymentOperation', '1')]), record(WHEN, '21', '607', [('DeploymentOperation', '1')]),
                  record(WHEN, '23', '401', [('DeploymentOperation', '1')])], [LOG])
        with mock.patch.object(appx, 'read_event_records', return_value=found) as reader:
            headers, rows, source = appx.appPackageDeploymentEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-appxdeploymentserver%4operational.evtx',
                                       'App Package Deployment Events', event_ids={'400', '401', '404', '603', '607'},
                                       provider='Microsoft-Windows-AppXDeployment-Server')
        self.assertEqual([(row[12], row[1]) for row in rows], [('22', '603'), ('21', '607'), ('23', '401')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Operation (as stored)',
                                   'Operation Name', 'Package', 'Path', 'Running for User SID', 'Calling Process',
                                   'Error Code (as stored)', 'Error', 'User SID', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        with mock.patch.object(appx, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(appx.appPackageDeploymentEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(appx, 'read_event_records', return_value=([], [])):
            self.assertEqual(appx.appPackageDeploymentEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
