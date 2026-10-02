"""Pin the rows in scripts/artifacts/windowsGroupPolicyEvents.py.

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

from scripts.artifacts import windowsGroupPolicyEvents as gp  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-GroupPolicy%4Operational.evtx'
MUI = '/case/data/vol1/Windows/System32/en-US/gpsvc.dll.mui'
OTHER_MUI = '/case/data/vol2/Windows/System32/en-US/gpsvc.dll.mui'
ACTIVITY = '{0A1B2C3D-1111-2222-3333-444455556666}'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
MESSAGES = {4114: 'Attempting to retrieve the account information.', 4113: ' fast\r\n', 4102: 'Changes were detected.',
            4200: ''}


def record(record_id, event_id, fields, activity=ACTIVITY, user='S-1-5-18', source=LOG):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    correlation = f'<Correlation ActivityID="{activity}"></Correlation>' if activity else '<Correlation></Correlation>'
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-GroupPolicy" '
           f'Guid="{{aea1b4fa-97d1-45f2-a64c-4d69fffd92c9}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>1</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID>{correlation}'
           f'<Execution ProcessID="700" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-GroupPolicy/Operational</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


START = [('PolicyActivityId', ACTIVITY), ('PrincipalSamName', ' LAB-PC\\examiner '), ('IsMachine', '0'),
         ('IsDomainJoined', 'False'), ('IsBackgroundProcessing', 'False'), ('IsAsyncProcessing', 'False'),
         ('IsServiceRestart', 'False'), ('ReasonForSyncProcessing', '0')]


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class _Plain:
    """Stands in for _ParameterText: marks what it was asked for."""

    @staticmethod
    def text(_record, value):
        return f'<{value}>'


class RowTest(unittest.TestCase):
    def test_a_policy_start_record_has_the_account_the_activity_and_its_other_fields_in_record_order(self):
        self.assertEqual(gp.group_policy_row(record('7', '4001', START), _Plain()),
                         (TIME, '4001', 'Starting user logon Policy processing for %2.', 'LAB-PC\\examiner', ACTIVITY,
                          f'PolicyActivityId: <{ACTIVITY}> | IsMachine: <0> | IsDomainJoined: <False> | '
                          'IsBackgroundProcessing: <False> | IsAsyncProcessing: <False> | IsServiceRestart: <False> | '
                          'ReasonForSyncProcessing: <0>', 'S-1-5-18', '7', 'LAB-PC'))

    def test_empty_fields_are_left_out_and_line_breaks_inside_a_value_are_kept(self):
        fields = [('DescriptionString', ' Local Group Policy\nSecond line  '), ('Blank', '   '), ('Empty', ''),
                  ('GPOInfoList', '<GPO ID="x"></GPO>'.replace('<', '&lt;').replace('>', '&gt;'))]
        row = gp.group_policy_row(record('8', '5312', fields, activity='', user=''), _Plain())
        self.assertEqual(row, (TIME, '5312', 'List of applicable Group Policy objects:', '', '',
                               'DescriptionString: <Local Group Policy\nSecond line> | GPOInfoList: <<GPO ID="x"></GPO>>',
                               '', '8', 'LAB-PC'))

    def test_an_event_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(gp.group_policy_row(record('9', '4116', []), _Plain())[2:6],
                         ('Started the Group Policy service initialization phase.', '', ACTIVITY, ''))
        row = gp.group_policy_row(record('10', '9999', [('Extra', 'kept'), ('PrincipalSamName', 'LAB-PC$')]), _Plain())
        self.assertEqual(row[1:6], ('9999', '', 'LAB-PC$', ACTIVITY, 'Extra: <kept>'))

    def test_the_table_holds_the_events_of_the_operational_channel(self):
        self.assertEqual(gp._EVENTS, {  # pylint: disable=protected-access
            '4000': 'Starting computer boot policy processing for %2.',
            '4001': 'Starting user logon Policy processing for %2.',
            '4002': 'Starting policy processing due to network state change for computer %2.',
            '4003': 'Starting policy processing due to network state change for user %2.',
            '4004': 'Starting manual processing of policy for computer %2.',
            '4005': 'Starting manual processing of policy for user %2.',
            '4006': 'Starting periodic policy processing for computer %2.',
            '4007': 'Starting periodic policy processing for user %2.',
            '4016': 'Starting %2 Extension Processing.',
            '4017': '%1',
            '4018': 'Starting %2 for %1.',
            '4019': 'Running script name %1.',
            '4115': 'Group Policy Service started.',
            '4116': 'Started the Group Policy service initialization phase.',
            '4117': 'Group Policy Session started.',
            '4126': 'Group Policy receiving applicable GPOs from the domain controller.',
            '4216': 'Starting to save policies to the local datastore.',
            '4217': 'Starting to load policies from the local datastore.',
            '4218': 'Starting the first WMI query for the policy.',
            '4257': 'Starting to download policies.',
            '4326': 'Group Policy is trying to discover the Domain Controller information.',
            '5016': 'Completed %3 Extension Processing in %1 milliseconds.',
            '5017': '%3',
            '5018': 'Completed %4 for %3 in %1 seconds.',
            '5019': 'Completed %3 in %1 seconds.',
            '5115': 'Group Policy Service stopped.',
            '5116': 'Successfully completed the Group Policy Service initialization phase.',
            '5117': 'Group policy session completed successfully.',
            '5126': 'Group Policy successfully got applicable GPOs from the domain controller.',
            '5216': 'Successfully saved policies to the local datastore.',
            '5217': 'Successfully loaded policies from the local datastore.',
            '5218': 'Successfully completed the first WMI query.',
            '5257': 'Successfully completed downloading policies.',
            '5308': 'Domain Controller details:',
            '5309': 'Computer details:',
            '5310': 'Account details:',
            '5311': 'The loopback policy processing mode is %1.',
            '5312': 'List of applicable Group Policy objects:',
            '5313': 'The following Group Policy objects were not applicable because they were filtered out :',
            '5314': 'A %6 link was detected.',
            '5315': 'Next policy processing for %1 will be attempted in %2 %3.',
            '5320': '%1',
            '5321': '%1 Parameter: %2',
            '5322': 'Group Policy waited for %3 milliseconds for the network subsystem at computer boot.',
            '5323': 'Invalid Error Message.',
            '5324': 'Group Policy received the notification %1 from Winlogon for session %2.',
            '5325': 'Group Policy received %1 notification from Service Control Manager.',
            '5326': 'Group Policy successfully discovered the Domain Controller in %1 milliseconds.',
            '5327': 'Estimated network bandwidth on one of the connections: %1 kbps.',
            '5331': 'Service configuration update to standalone was attempted due to the presence of Group Policy '
                    'client extension %1 that is not part of the operating system and completed with status %3.',
            '5332': 'Group Policy waited for %3 milliseconds for the Direct Access CorpNet connectivity at computer boot.',
            '5340': 'The Group Policy processing mode is %1.',
            '5351': 'Group policy session returned to winlogon.',
            '6000': 'Invalid Error Message.',
            '6001': 'Invalid Error Message.',
            '6002': 'Invalid Error Message.',
            '6003': 'Invalid Error Message.',
            '6004': 'Invalid Error Message.',
            '6005': 'Invalid Error Message.',
            '6006': 'Invalid Error Message.',
            '6007': 'Invalid Error Message.',
            '6016': 'Completed %3 Extension Processing in %1 milliseconds.',
            '6017': 'Invalid Error Message.',
            '6018': 'Invalid Error Message.',
            '6019': 'Invalid Error Message.',
            '6033': 'Skipped %1 Extension based on Group Policy client-side processing rules.',
            '6034': 'Group Policy changed from synchronous foreground to asynchronous foreground based on slow link '
                    'detection.',
            '6035': '%1 Extension deferred processing until next synchronous foreground.',
            '6226': 'Invalid Error Message.',
            '6308': 'Invalid Error Message.',
            '6309': 'Invalid Error Message.',
            '6310': 'Invalid Error Message.',
            '6311': 'Invalid Error Message.',
            '6312': 'Invalid Error Message.',
            '6313': 'Invalid Error Message.',
            '6314': 'Group Policy bandwidth estimation failed.',
            '6315': 'Invalid Error Message.',
            '6320': 'Warning: %1 Warning code %2.',
            '6321': 'Warning: %1 Parameter: %3 : Warning code %2.',
            '6322': 'Invalid Error Message.',
            '6323': 'Group Policy dependency (%1) did not start.',
            '6324': 'Invalid Error Message.',
            '6325': 'Invalid Error Message.',
            '6326': 'Invalid Error Message.',
            '6327': 'Invalid Error Message.',
            '6330': 'An unfinished invocation of the Group Policy Client Side Extension %1 from a previous instance '
                    'of the Group Policy Service was detected.',
            '6331': 'Invalid Error Message.',
            '6332': 'Invalid Error Message.',
            '6337': 'Group Policy network connection is via Direct Access.',
            '6338': 'Group Policy Winlogon status reporting has completed.',
            '6339': 'Group Policy Winlogon Start Shell handling completed.',
            '6341': 'A Group Policy setting was used to override the fast/slow link detection.',
            '6342': 'The network connection is using a WWAN device for connectivity.',
            '6344': 'Group Policy detected a slow link during sync mode processing.',
            '6345': 'The connection to DC timed out during the Group Policy sync mode process.',
            '6346': 'Group Policy switched the sync mode process to async mode.',
            '7000': 'Computer boot policy processing failed for %3 in %1 seconds.',
            '7001': 'User logon policy processing failed for %3 in %1 seconds.',
            '7002': 'Policy processing due to network state change failed for computer %3 in %1 seconds.',
            '7003': 'Policy processing due to network state change failed for user %3 in %1 seconds.',
            '7004': 'Manual processing of policy failed for computer %3 in %1 seconds.',
            '7005': 'Manual processing of policy failed for user %3 in %1 seconds.',
            '7006': 'Periodic policy processing failed for computer %3 in %1 seconds.',
            '7007': 'Periodic policy processing failed for user %3 in %1 seconds.',
            '7016': 'Completed %3 Extension Processing in %1 milliseconds.',
            '7017': '%3',
            '7018': 'Script for %3 failed in %1 seconds.',
            '7019': 'Invalid Error Message.',
            '7117': 'Group policy session completed with error.',
            '7126': 'Group Policy could not get applicable GPOs from the domain controller.',
            '7216': 'Saved policies to the local datastore with error.',
            '7217': 'Loaded policies from the local datastore with error.',
            '7257': 'Downloaded policies with error.',
            '7308': 'Invalid Error Message.',
            '7309': 'Invalid Error Message.',
            '7310': 'Invalid Error Message.',
            '7311': 'Invalid Error Message.',
            '7312': 'Invalid Error Message.',
            '7313': 'Invalid Error Message.',
            '7314': 'Invalid Error Message.',
            '7315': 'Invalid Error Message.',
            '7320': 'Error: %1 Error code %2.',
            '7321': 'Error: %1 Parameter: %3 : Error code %2.',
            '7322': 'Invalid Error Message.',
            '7323': 'Invalid Error Message.',
            '7324': 'Invalid Error Message.',
            '7325': 'Invalid Error Message.',
            '7326': 'Group Policy failed to discover the Domain Controller details in %1 milliseconds.',
            '7327': 'Invalid Error Message.',
            '7331': 'Service configuration update to standalone was attempted due to the presence of Group Policy '
                    'client extension %1 that is not part of the operating system and completed with status %3.',
            '7332': 'Invalid Error Message.',
            '8000': 'Completed computer boot policy processing for %3 in %1 seconds.',
            '8001': 'Completed user logon policy processing for %3 in %1 seconds.',
            '8002': 'Completed policy processing due to network state change for computer %3 in %1 seconds.',
            '8003': 'Completed policy processing due to network state change for user %3 in %1 seconds.',
            '8004': 'Completed manual processing of policy for computer %3 in %1 seconds.',
            '8005': 'Completed manual processing of policy for user %3 in %1 seconds.',
            '8006': 'Completed periodic policy processing for computer %3 in %1 seconds.',
            '8007': 'Completed periodic policy processing for user %3 in %1 seconds.',
            '8016': '%1 Extension (%2) requests a sync mode process.',
            '9001': 'This machine is configured to retrieve Group Policy files from a file share in an insecure way.',
        })


class ParameterTextTest(unittest.TestCase):
    def parameters(self, files, messages=None):
        read = mock.patch.object(gp.windows_messages, 'read_message_table',
                                 return_value=MESSAGES if messages is None else messages).start()
        self.addCleanup(mock.patch.stopall)
        with mock.patch.object(gp.os.path, 'isdir', return_value=False):
            return gp._ParameterText(_Context(files), 'Group Policy Operational Events'), read  # pylint: disable=protected-access

    def test_a_reference_is_given_its_text_from_the_file_on_the_same_volume(self):
        parameters, read = self.parameters([LOG, OTHER_MUI, MUI])
        rec = record('1', '5320', [])
        self.assertEqual(parameters.text(rec, '%%4114'), 'Attempting to retrieve the account information. (%%4114)')
        self.assertEqual(parameters.text(rec, '%%4113'), 'fast (%%4113)')
        read.assert_called_once_with(MUI)
        self.assertEqual(parameters.files_used(), [MUI])

    def test_the_file_is_matched_without_case_and_a_folder_of_that_name_is_not_a_file(self):
        lower = MUI.replace('System32/en-US', 'system32/EN-us')
        parameters, read = self.parameters([LOG, lower])
        self.assertEqual(parameters.text(record('1', '5320', []), '%%4102'), 'Changes were detected. (%%4102)')
        read.assert_called_once_with(lower)
        read = mock.patch.object(gp.windows_messages, 'read_message_table', return_value=MESSAGES).start()
        with mock.patch.object(gp.os.path, 'isdir', side_effect=lambda path: path == MUI):
            parameters = gp._ParameterText(_Context([LOG, MUI]), 'x')  # pylint: disable=protected-access
        self.assertEqual(parameters.text(record('1', '5320', []), '%%4102'), '%%4102')
        read.assert_not_called()

    def test_several_references_in_one_value_are_each_given_their_text_and_other_text_is_kept(self):
        parameters, _read = self.parameters([LOG, MUI])
        rec = record('1', '5320', [])
        self.assertEqual(parameters.text(rec, 'a %%4102, %%4113 b'), 'a Changes were detected. (%%4102), fast (%%4113) b')
        self.assertEqual(parameters.text(rec, '%%4102, %%9999'), 'Changes were detected. (%%4102), %%9999')
        self.assertEqual(parameters.text(rec, '%%4200'), '%%4200')
        self.assertEqual(parameters.kept, 2)

    def test_a_value_that_is_not_a_reference_is_kept(self):
        parameters, read = self.parameters([LOG, MUI])
        rec = record('1', '5320', [])
        self.assertEqual(parameters.text(rec, 'Changes were detected.'), 'Changes were detected.')
        self.assertEqual(parameters.text(rec, '%4102 and 100%'), '%4102 and 100%')
        self.assertEqual(parameters.text(rec, ''), '')
        read.assert_not_called()

    def test_without_a_message_file_on_the_volume_the_reference_is_kept_and_counted(self):
        parameters, _read = self.parameters([LOG, OTHER_MUI])
        self.assertEqual(parameters.text(record('1', '5320', []), '%%4114'), '%%4114')
        self.assertEqual(parameters.text(record('1', '5320', [], source=''), '%%4114'), '%%4114')
        self.assertEqual(parameters.files_used(), [])
        with mock.patch.object(gp, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Group Policy Operational Events: 2 parameter reference(s) reported as stored; no English '
                          'gpsvc.dll.mui on the same volume gave their text'
                          + ('' if gp.windows_messages.pefile else ' (pefile is not installed)')])

    def test_only_the_english_file_of_the_system32_folder_on_the_logs_own_volume_is_used(self):
        for wrong in (MUI.replace('en-US', 'de-DE'), MUI + '.old', MUI.replace('System32', 'SysWOW64'), OTHER_MUI):
            parameters, read = self.parameters([LOG, wrong])
            self.assertEqual(parameters.text(record('1', '5320', []), '%%4102'), '%%4102', wrong)
            read.assert_not_called()
            mock.patch.stopall()
        nested_log = LOG.replace('vol1/', 'vol1/w/')
        parameters, read = self.parameters([nested_log, MUI + '/x'])
        self.assertEqual(parameters.text(record('1', '5320', [], source=nested_log), '%%4102'), '%%4102')
        read.assert_not_called()
        mock.patch.stopall()
        parameters, read = self.parameters([LOG, MUI])
        elsewhere = record('1', '5320', [], source=LOG.replace('/Logs/', '/Other/'))
        self.assertEqual(parameters.text(elsewhere, '%%4102'), '%%4102')
        self.assertEqual(parameters.text(record('1', '5320', [], source=None), '%%4102'), '%%4102')
        read.assert_not_called()

    def test_a_volume_with_no_file_is_not_given_another_volumes_text(self):
        parameters, read = self.parameters([LOG, MUI])
        self.assertEqual(parameters.text(record('1', '5320', []), '%%4102'), 'Changes were detected. (%%4102)')
        other = record('2', '5320', [], source=LOG.replace('vol1', 'vol2'))
        self.assertEqual(parameters.text(other, '%%4102'), '%%4102')
        read.assert_called_once_with(MUI)
        with mock.patch.object(gp, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Group Policy Operational Events: 1 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/gpsvc.dll.mui',
                          'Group Policy Operational Events: 1 parameter reference(s) reported as stored; no English '
                          'gpsvc.dll.mui on the same volume gave their text'
                          + ('' if gp.windows_messages.pefile else ' (pefile is not installed)')])

    def test_an_extraction_with_no_volume_folder_and_one_under_a_folder_named_like_the_log_folder(self):
        log, mui = 'Windows/System32/winevt/Logs/x.evtx', 'Windows/System32/en-US/gpsvc.dll.mui'
        parameters, read = self.parameters([log, mui])
        self.assertEqual(parameters.text(record('1', '5320', [], source=log), '%%4102'), 'Changes were detected. (%%4102)')
        read.assert_called_once_with(mui)
        mock.patch.stopall()
        staged = '/cases/Windows/System32/winevt/Logs/report/data/'
        parameters, read = self.parameters([staged + 'vol1/' + log, staged + 'vol1/' + mui])
        rec = record('1', '5320', [], source=staged + 'vol1/' + log)
        self.assertEqual(parameters.text(rec, '%%4102'), 'Changes were detected. (%%4102)')
        read.assert_called_once_with(staged + 'vol1/' + mui)

    def test_of_two_files_of_one_volume_the_first_in_path_order_is_read(self):
        second = MUI.replace('en-US', 'en-us')
        parameters, read = self.parameters([second, LOG, MUI])
        parameters.text(record('1', '5320', []), '%%4102')
        read.assert_called_once_with(MUI)
        self.assertEqual(parameters.files_used(), [MUI])

    def test_a_file_that_gave_no_text_is_not_a_file_used_and_the_run_log_says_when_pefile_is_missing(self):
        parameters, read = self.parameters([LOG, MUI])
        self.assertEqual(parameters.text(record('1', '5320', []), '%%9999'), '%%9999')
        read.assert_called_once_with(MUI)
        self.assertEqual(parameters.files_used(), [])
        for installed, tail in ((None, ' (pefile is not installed)'), (object(), '')):
            with mock.patch.object(gp, 'logfunc') as log, mock.patch.object(gp.windows_messages, 'pefile', installed):
                parameters.log()
            self.assertEqual([call.args[0] for call in log.call_args_list],
                             ['Group Policy Operational Events: 1 parameter reference(s) reported as stored; no English '
                              'gpsvc.dll.mui on the same volume gave their text' + tail])

    def test_each_volume_reads_its_own_file_once_and_the_run_log_names_the_files(self):
        parameters, read = self.parameters([LOG, MUI, OTHER_MUI])
        other_log = LOG.replace('vol1', 'vol2')
        parameters.text(record('1', '5320', []), '%%4114')
        parameters.text(record('2', '5320', []), '%%4102')
        parameters.text(record('3', '5320', [], source=other_log), '%%4102')
        self.assertEqual([call.args[0] for call in read.call_args_list], [MUI, OTHER_MUI])
        self.assertEqual(parameters.files_used(), [MUI, OTHER_MUI])
        with mock.patch.object(gp, 'logfunc') as log:
            parameters.log()
        self.assertEqual([call.args[0] for call in log.call_args_list],
                         ['Group Policy Operational Events: 2 parameter reference(s) given their text from '
                          'vol1/Windows/System32/en-US/gpsvc.dll.mui',
                          'Group Policy Operational Events: 1 parameter reference(s) given their text from '
                          'vol2/Windows/System32/en-US/gpsvc.dll.mui'])


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Account', 'Activity ID', 'Other Fields',
               'User SID', 'Record ID', 'Computer')

    def run_artifact(self, records, sources, files):
        with mock.patch.object(gp, 'read_event_records', return_value=(records, sources)) as reader, \
                mock.patch.object(gp.windows_messages, 'read_message_table', return_value=MESSAGES), \
                mock.patch.object(gp.os.path, 'isdir', return_value=False), \
                mock.patch.object(gp, 'logfunc') as log:
            result = gp.groupPolicyOperationalEvents.__wrapped__(_Context(files))
        return result, reader, [call.args[0] for call in log.call_args_list]

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order_with_references_given_text(self):
        records = [record('23', '5320', [('InfoDescription', '%%4114')]), record('21', '4001', START),
                   record('22', '5314', [('LinkDescription', '%%4113'), ('IsSlowLink', 'False')]), record('24', '9999', [])]
        (headers, rows, source), reader, logged = self.run_artifact(records, [LOG], [LOG, MUI])
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-GroupPolicy%4Operational.evtx',
                                       'Group Policy Operational Events', provider='Microsoft-Windows-GroupPolicy')
        self.assertEqual([(row[7], row[1], row[5].split(' | ')[0]) for row in rows], [
            ('23', '5320', 'InfoDescription: Attempting to retrieve the account information. (%%4114)'),
            ('21', '4001', f'PolicyActivityId: {ACTIVITY}'), ('22', '5314', 'LinkDescription: fast (%%4113)'), ('24', '9999', '')])
        self.assertEqual(rows[2][5], 'LinkDescription: fast (%%4113) | IsSlowLink: False')
        self.assertEqual(source, LOG + '\n' + MUI)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(logged, ['Group Policy Operational Events: 2 parameter reference(s) given their text from '
                                  'vol1/Windows/System32/en-US/gpsvc.dll.mui'])

    def test_a_message_file_that_gave_no_text_is_not_a_source(self):
        (_headers, rows, source), _reader, logged = self.run_artifact([record('1', '4001', START)], [LOG, LOG + '.copy'],
                                                                      [LOG, MUI])
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, LOG + '\n' + LOG + '.copy')
        self.assertEqual(logged, [])

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        (headers, rows, source), _reader, logged = self.run_artifact([], [], [MUI])
        self.assertEqual((headers, rows, source, logged), (self.HEADERS, [], '', []))


if __name__ == '__main__':
    unittest.main()
