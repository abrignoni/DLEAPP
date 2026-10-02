"""Pin the rows in scripts/artifacts/windowsAppModelRuntimeEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up names and values); the
expected rows and the whole Event ID table are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsAppModelRuntimeEvents as appmodel  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-AppModel-Runtime%4Admin.evtx'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
FULL = 'Vendor.App_1.2.3.0_x64__abcdefgh12345'


def record(record_id, event_id, fields, user='S-1-5-18', data='EventData'):
    items = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-AppModel-Runtime" '
           f'Guid="{{f1ef270a-0d32-4352-ba52-dbab41e1d859}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="700" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-AppModel-Runtime/Admin</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<{data}>{items}</{data}></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_created_process_record_has_the_package_the_image_and_the_process_id(self):
        fields = [('ProcessID', ' 4321 '), ('PackageName', f' {FULL}\n'), ('ImageName', ' App.exe '), ('ApplicationName', 'App'),
                  ('Message', '')]
        self.assertEqual(appmodel.app_model_row(record('7', '201', fields)),
                         (TIME, '201', 'Created process %1 for application %4 in package %2.', FULL, 'App.exe', '4321',
                          'ApplicationName: App', 'S-1-5-18', '7', 'LAB-PC'))

    def test_each_of_the_three_package_fields_fills_the_package_column(self):
        full = appmodel.app_model_row(record('8', '68', [('PackageFullName', FULL), ('DesiredStatus', '0'), ('CurrentStatus', '8')]))
        self.assertEqual(full[2:7], ('AppModel Runtime status for package %1 successfully updated to %2 (previous status = %3).',
                                     FULL, '', '', 'DesiredStatus: 0 | CurrentStatus: 8'))
        family = appmodel.app_model_row(record('9', '79', [('PackageFamilyName', 'Vendor.App_abcdefgh12345'), ('ErrorCode', '0x1')],
                                               user=SID))
        self.assertEqual(family[3:8], ('Vendor.App_abcdefgh12345', '', '', 'ErrorCode: 0x1', SID))
        added = appmodel.app_model_row(record('10', '211', [('ProcessID', '99'), ('PackageName', FULL), ('ContainerId', '{a-b}')]))
        self.assertEqual(added[3:7], (FULL, '', '99', 'ContainerId: {a-b}'))

    def test_of_two_package_fields_the_first_in_the_fixed_order_is_shown_and_the_other_is_kept(self):
        fields = [('PackageFamilyName', 'Family'), ('PackageName', 'Name'), ('PackageFullName', 'Full')]
        row = appmodel.app_model_row(record('11', '9999', fields))
        self.assertEqual((row[2], row[3], row[6]), ('', 'Full', 'PackageFamilyName: Family | PackageName: Name'))
        row = appmodel.app_model_row(record('12', '9999', fields[:2]))
        self.assertEqual((row[3], row[6]), ('Name', 'PackageFamilyName: Family'))

    def test_an_empty_package_field_still_takes_the_column(self):
        row = appmodel.app_model_row(record('13', '70', [('PackageFullName', ''), ('PackageName', 'Name'), ('User', SID)]))
        self.assertEqual((row[3], row[6]), ('', f'PackageName: Name | User: {SID}'))

    def test_other_fields_are_listed_in_record_order_without_the_empty_ones_and_keep_inner_line_breaks(self):
        fields = [('AppContainerName', ' vendor.app_abcdefgh12345 '), ('Blank', '   '), ('Empty', ''), ('Text', 'a\nb  c')]
        row = appmodel.app_model_row(record('14', '39', fields, user=''))
        self.assertEqual(row, (TIME, '39', 'Successfully created AppContainer %1.', '', '', '',
                               'AppContainerName: vendor.app_abcdefgh12345 | Text: a\nb  c', '', '14', 'LAB-PC'))

    def test_a_record_with_no_event_data_has_only_its_own_columns(self):
        row = appmodel.app_model_row(record('15', '219', [], data='ProcessingErrorData'))
        self.assertEqual(row, (TIME, '219', 'PSMFlags for Desktop AppX process %1 with applicationID %2 is %3.', '', '', '', '',
                               'S-1-5-18', '15', 'LAB-PC'))
        self.assertEqual(appmodel.app_model_row(record('16', '9999', []))[2:7], ('', '', '', '', ''))


class EventTextTest(unittest.TestCase):
    def test_a_status_record_with_the_earlier_fields_is_given_the_earlier_text(self):
        old = [('PackageFullName', FULL), ('User', SID), ('DesiredStatus', '0'), ('CurrentStatus', '8')]
        new = [('PackageFullName', FULL), ('User', SID), ('StatusToClear', '8'), ('StatusToSet', '0')]
        self.assertEqual(appmodel.event_text(record('1', '70', old)),
                         'AppModel Runtime status for package %1 for user %2 successfully updated to %3 (previous status = %4).')
        self.assertEqual(appmodel.event_text(record('2', '70', new)),
                         'Successfully updated AppModel Runtime status for package %1 for user %2 (clear=%3, set=%4).')
        self.assertEqual(appmodel.event_text(record('3', '69', [('ErrorCode', '5')] + old)),
                         'Failed with %1 modifying AppModel Runtime status for package %2 for user %3 (current status = %5, '
                         'desired status = %4).')
        self.assertEqual(appmodel.event_text(record('4', '69', [('ErrorCode', '5')] + new)),
                         'Failed with %1 modifying AppModel Runtime status for package %2 for user %3 (clear=%4, set=%5).')
        self.assertEqual(appmodel.app_model_row(record('5', '70', old))[2], appmodel.event_text(record('1', '70', old)))

    def test_only_69_and_70_have_an_earlier_text_and_only_with_the_earlier_field(self):
        self.assertEqual(appmodel.event_text(record('1', '68', [('PackageFullName', FULL), ('DesiredStatus', '0')])),
                         'AppModel Runtime status for package %1 successfully updated to %2 (previous status = %3).')
        self.assertEqual(appmodel.event_text(record('2', '70', [('CurrentStatus', '8')])),
                         'Successfully updated AppModel Runtime status for package %1 for user %2 (clear=%3, set=%4).')
        self.assertEqual(appmodel.event_text(record('3', '70', [('DesiredStatus', '')])),
                         'AppModel Runtime status for package %1 for user %2 successfully updated to %3 (previous status = %4).')
        self.assertEqual(appmodel.event_text(record('4', '9999', [('DesiredStatus', '0')])), '')
        self.assertEqual(appmodel._EARLIER, {  # pylint: disable=protected-access
            '69': 'Failed with %1 modifying AppModel Runtime status for package %2 for user %3 (current status = %5, '
                  'desired status = %4).',
            '70': 'AppModel Runtime status for package %1 for user %2 successfully updated to %3 (previous status = '
                  '%4).',
        })

    def test_the_table_holds_the_events_of_the_admin_channel(self):
        self.assertEqual(appmodel._EVENTS, {  # pylint: disable=protected-access
            '2': '%2: Cannot create the process for package %1 because an error was encountered.',
            '3': '%2: Cannot create the process for package %1 because an error was encountered while querying the '
                 'fast cache.',
            '4': '%2: Cannot create the process for package %1 because an error was encountered while preparing the '
                 'App credentials.',
            '5': '%2: Cannot create the process for package %1 because an error was encountered while checking the '
                 'user-level package status.',
            '6': '%2: Cannot create the process for package %1 because an error was encountered while checking the '
                 'machine-level package status.',
            '7': '%2: Cannot create the process for package %1 because an error was encountered while verifying the '
                 'App credentials.',
            '8': 'App %1 was terminated with error %2 because of an issue with application binary %3.',
            '11': 'App %1 prevented the load of generated binary %3 due to error %2.',
            '12': 'An app prevented the load of a binary due to error %1.',
            '14': '%2: Package runtime information %1 is corrupted (address=%5, size=%3, offset=%4, section=%6, '
                  'processid=%7).',
            '15': '%2: Package runtime information %1 is missing expected data (address=%4, size=%3, section=%5, '
                  'processid=%6).',
            '16': '%2: Package runtime information %1 contains conflicting data (address=%5, size=%3, offset=%4, '
                  'section=%6, processid=%7).',
            '17': '%2: Package runtime information %1 contains unexpected data (address=%5, size=%3, offset=%4, '
                  'section=%6, processid=%7).',
            '18': '%2: Package runtime information %1 failed to load (processid=%3).',
            '19': 'Package runtime information %1 failed to load because exception %2 occurred.',
            '20': '%2: Cannot create the process for package %1 because an error was encountered while loading the '
                  'runtime information.',
            '21': 'CreateAppContainerProfile failed for AppContainer %2 with error %1.',
            '22': 'DeleteAppContainerProfile failed for AppContainer %2 with error %1.',
            '23': 'UpdateAppContainerProfile failed for AppContainer %2 with error %1.',
            '24': 'CreateAppContainerProfile failed with error %1 because it was unable to create registry key %2.',
            '25': 'CreateAppContainerProfile failed with error %1 because it was unable to set security on registry '
                  'key %2.',
            '26': 'AppContainer profile failed with error %1 because it was unable to delete registry key %2.',
            '27': 'CreateAppContainerProfile failed with error %1 because it was unable to create folder %2.',
            '28': 'CreateAppContainerProfile failed with error %1 because it was unable to set attributes on folder '
                  '%2.',
            '29': 'CreateAppContainerProfile failed with error %1 because it was unable to verify the existence of '
                  'registry key %2.',
            '30': 'CreateAppContainerProfile failed with error %1 because it was unable to verify the existence of '
                  'folder %2.',
            '31': 'CreateAppContainerProfile failed with error %1 because it was unable to find the users local app '
                  'data folder.',
            '32': 'AppContainer profile failed with error %1 because it was unable to delete folder %2 or its '
                  'contents.',
            '33': 'AppContainer profile failed with error %1 because it was unable to look up the AppContainer name.',
            '34': 'AppContainer profile failed with error %1 because it was unable to look up the AppContainer '
                  'display name.',
            '35': 'CreateAppContainerProfile failed with error %1 because it was unable to register with the '
                  'firewall.',
            '36': 'DeleteAppContainerProfile failed with error %1 because it was unable to unregister with the '
                  'firewall.',
            '37': 'App Container profile failed with error %1 because it was unable to register the AppContainer '
                  'SID.',
            '38': 'DeleteAppContainerProfile failed with error %1 because it was unable to unregister the '
                  'AppContainer SID.',
            '39': 'Successfully created AppContainer %1.',
            '40': 'AppContainer %1 was not created because it already exists.',
            '41': 'Successfully deleted AppContainer %1.',
            '42': 'Successfully updated AppContainer %1.',
            '43': '%2: Package runtime information %1 is missing expected data (address=%4, size=%3, section=%5, '
                  'processid=%6).',
            '44': '%2: Application identity not accessible while loading package runtime information %1 (address=%4, '
                  'size=%3, processid=%5).',
            '45': 'Failed with %1 while retrieving AppContainer %2 information during interaction with Restricted '
                  'AppContainer.',
            '46': 'Failed with %1 while retrieving AppContainer information during interaction with Restricted '
                  'AppContainer.',
            '47': 'Failed with %1 while retrieving AppContainer information.',
            '48': 'Failed to create shared context object for Restricted AppContainer %2 with %1.',
            '49': 'Failed to activate Restricted AppContainer %2 with %1.',
            '50': 'Creation of Restricted AppContainer %2 failed with %1 because an invalid capability was '
                  'specified.',
            '51': 'Opening existing Restricted AppContainer %2 failed with %1 because the capabilities storage value '
                  'could not be read.',
            '52': 'Failed to create the capabilities storage value for Restricted AppContainer %2 with %1.',
            '53': 'The package %1 requires validation.',
            '54': 'Modification was detected in package %1.',
            '55': 'Failed to terminate app with package %1.',
            '56': 'Validation of app with package %1 was successful.',
            '57': 'Failed with %1 to retrieve the trust state of the package %2 folder.',
            '58': 'App Integrity check failed with %1 while checking %2.',
            '59': 'App Integrity terminated an application.',
            '60': 'App Integrity check for %1 timed out.',
            '61': '%2: Cannot create the process for package %1 because an error was encountered while performing '
                  'the integrity check.',
            '62': 'Deployment server integrity check of package %1 failed with %2.',
            '63': 'Failed with %1 retrieving AppModel Runtime group policy values.',
            '64': 'Failed with %1 validating AppModel Runtime group policy values.',
            '65': 'Failed with %1 retrieving AppModel Runtime status for package %2.',
            '66': 'Failed with %1 retrieving AppModel Runtime status for package %2 for user %3.',
            '67': 'Failed with %1 modifying AppModel Runtime status for package %2 (current status = %4, desired '
                  'status = %3).',
            '68': 'AppModel Runtime status for package %1 successfully updated to %2 (previous status = %3).',
            '69': 'Failed with %1 modifying AppModel Runtime status for package %2 for user %3 (clear=%4, set=%5).',
            '70': 'Successfully updated AppModel Runtime status for package %1 for user %2 (clear=%3, set=%4).',
            '71': 'Failed with %1 modifying AppModel Runtime status version (context = %2).',
            '73': '%2: Cannot create the process for package %1 because an error was encountered while performing '
                  'the app data creation.',
            '74': 'Package runtime information %1 failed to refresh because the following error %2 occurred in '
                  'operation type %3.',
            '75': 'error %2: Cannot register the %1 package because the following error was encountered while '
                  'opening the HKEY_USERS registry key',
            '76': 'error %4: Cannot register the %1 package because the following error was encountered while '
                  'enumerating to remove the %2\\%3 package family registry key',
            '77': 'error %4 : Cannot register the %1 package because the following error was encountered while '
                  'creating the %2\\%3 package family registry key',
            '78': 'error %4: Cannot register the %1 package because the following error was encountered while '
                  'removing the %2\\%3 package family registry key',
            '79': '%2: Package family %1 runtime information is corrupted.',
            '80': '%2: Package family %1 runtime information is corrupted but we cannot repair it at this time.',
            '81': 'Failed with %1 to get IsPackageStageInPlace info from State Repository cache for package %2.',
            '201': 'Created process %1 for application %4 in package %2.',
            '202': '%4: Cannot create the process for package %1 because an error was encountered.',
            '203': '%4: Cannot create the process for package %1 because an error was encountered while preparing '
                   'for activation.',
            '204': '%4: Cannot create the process for package %1 because an error was encountered while elevating '
                   'the token.',
            '205': '%4: Cannot create the process for package %1 because UI Access is not supported for Desktop AppX '
                   'processes.',
            '206': '%4: Cannot create the process for package %1 because an error was encountered while adjusting '
                   'the token.',
            '207': '%4: Cannot create the process for package %1 because an error was encountered while launching.',
            '208': '%4: Cannot create the process for package %1 because an error was encountered while configuring '
                   'runtime.',
            '209': '%4: Cannot create the process for package %1 because an error was encountered while resuming the '
                   'thread.',
            '210': 'Created Desktop AppX container %3 for package %1.',
            '211': 'Added process %1 to Desktop AppX container %3 for package %2.',
            '212': '%1: Cannot add process %2 to Desktop AppX container %4 for package %3 because an error was '
                   'encountered.',
            '213': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
                   'creating the job.',
            '214': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
                   'creating the description.',
            '215': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
                   'converting the job.',
            '216': '%1: Cannot create the Desktop AppX container for package %2 because an error was encountered '
                   'configuring the runtime.',
            '217': 'Destroyed Desktop AppX container %2 for package %1.',
            '218': 'Cannot destroy Desktop AppX container %2 for package %1.',
            '219': 'PSMFlags for Desktop AppX process %1 with applicationID %2 is %3.',
        })


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Package', 'Image Name', 'Process ID', 'Other Fields',
               'User SID', 'Record ID', 'Computer')

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '39', [('AppContainerName', 'a')]), record('21', '201', [('ProcessID', '5'), ('PackageName', FULL)]),
                   record('22', '39', [('AppContainerName', 'b')]), record('24', '9999', [])]
        with mock.patch.object(appmodel, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = appmodel.appModelRuntimeEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-AppModel-Runtime%4Admin.evtx', 'AppModel Runtime Events',
                                       provider='Microsoft-Windows-AppModel-Runtime')
        self.assertEqual([(row[8], row[1], row[3], row[6]) for row in rows], [
            ('23', '39', '', 'AppContainerName: a'), ('21', '201', FULL, ''), ('22', '39', '', 'AppContainerName: b'), ('24', '9999', '', '')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(appmodel, 'read_event_records', return_value=([record('1', '39', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(appmodel.appModelRuntimeEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(appmodel, 'read_event_records', return_value=([], [])):
            self.assertEqual(appmodel.appModelRuntimeEvents.__wrapped__(_Context()), (self.HEADERS, [], ''))


if __name__ == '__main__':
    unittest.main()
