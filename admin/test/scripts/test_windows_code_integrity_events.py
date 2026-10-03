"""Pin the rows in scripts/artifacts/windowsCodeIntegrityEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up file names and values); the
expected rows and the whole (Event ID, version) table are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsCodeIntegrityEvents as ci  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-CodeIntegrity%4Operational.evtx'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
ACT = '{0A1B2C3D-1111-2222-3333-444455556666}'
FILE = '\\Device\\HarddiskVolume3\\Windows\\System32\\drivers\\sample.sys'
PROC = '\\Device\\HarddiskVolume3\\Program Files\\Sample\\sample.exe'


def record(record_id, event_id, fields, version='0', user='S-1-5-18', activity=ACT):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    correlation = f'<Correlation ActivityID="{activity}"></Correlation>' if activity else ''
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-CodeIntegrity" '
           f'Guid="{{4ee76bd8-3cf4-44a0-a0ac-3937643e37a3}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>2</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID>{correlation}<Execution ProcessID="4" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-CodeIntegrity/Operational</Channel><Computer>LAB-PC</Computer>{security}'
           f'</System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_signing_level_record_has_the_file_the_process_and_the_activity_id(self):
        fields = [('FileNameLength', '47'), ('FileNameBuffer', f' {FILE} '), ('ProcessNameLength', '55'), ('ProcessNameBuffer', PROC),
                  ('RequestedPolicy', '1'), ('ValidatedPolicy', '7'), ('Status', '3221226536')]
        self.assertEqual(ci.code_integrity_row(record('7', '3033', fields)),
                         (TIME, '3033', 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the %5 '
                          'signing level requirements.', FILE, PROC, '', '', '', ACT,
                          'FileNameLength: 47 | ProcessNameLength: 55 | RequestedPolicy: 1 | ValidatedPolicy: 7 | Status: 3221226536',
                          'S-1-5-18', '7', 'LAB-PC'))

    def test_a_signature_record_has_the_publisher_and_the_issuer(self):
        fields = [('TotalSignatureCount', '6'), ('Signature', '0'), ('Hash', 'QUJD'), ('PublisherName', ' Sample Publisher '),
                  ('IssuerName', 'Sample CA'), ('Blank', '  ')]
        row = ci.code_integrity_row(record('8', '3089', fields, version='2', user='', activity=''))
        self.assertEqual(row[1:], ('3089', 'Signature information for another event.', '', '', '', 'Sample Publisher', 'Sample CA', '',
                                   'TotalSignatureCount: 6 | Signature: 0 | Hash: QUJD', '', '8', 'LAB-PC'))

    def test_the_spaced_spellings_and_the_policy_name_fill_the_same_columns(self):
        fields = [('PolicyName', 'Sample Policy'), ('File Name', 'a.dll'), ('Process Name', 'b.exe'), ('PolicyID', '{p}')]
        row = ci.code_integrity_row(record('9', '3076', fields, version='1'))
        self.assertEqual(row[3:10], ('a.dll', 'b.exe', 'Sample Policy', '', '', ACT, 'PolicyID: {p}'))
        row = ci.code_integrity_row(record('10', '3099', [('PolicyNameLength', '2'), ('PolicyNameBuffer', 'P1')], version='1'))
        self.assertEqual(row[2:10], ('Refreshed and activated Code Integrity policy %5 %2.', '', '', 'P1', '', '', ACT, 'PolicyNameLength: 2'))

    def test_of_two_spellings_the_first_in_the_fixed_order_is_shown_and_the_other_is_kept(self):
        fields = [('File Name', 'second'), ('FileNameBuffer', 'first'), ('Process Name', 'p2'), ('ProcessNameBuffer', 'p1'),
                  ('PolicyName', 'q2'), ('PolicyNameBuffer', 'q1')]
        row = ci.code_integrity_row(record('11', '9999', fields))
        self.assertEqual((row[2], row[3], row[4], row[5], row[9]), ('', 'first', 'p1', 'q1', 'File Name: second | Process Name: p2 | PolicyName: q2'))

    def test_an_empty_first_spelling_still_takes_the_column_and_other_values_lose_outer_white_space(self):
        row = ci.code_integrity_row(record('16', '3076', [('FileNameBuffer', ''), ('File Name', 'kept.dll'), ('Note', '  padded  ')], version='1'))
        self.assertEqual((row[3], row[9]), ('', 'File Name: kept.dll | Note: padded'))

    def test_the_event_text_is_chosen_by_event_id_and_version(self):
        self.assertEqual(ci.code_integrity_row(record('12', '3085', [('Settings', '0x1'), ('Exemption', '0')]))[2],
                         'Code Integrity will disable WHQL driver enforcement for this boot session.')
        self.assertEqual(ci.code_integrity_row(record('13', '3085', [], version='9'))[2], '')
        self.assertEqual(ci.code_integrity_row(record('14', '3093', []))[2], ci._EVENTS[('3093', '0')])  # pylint: disable=protected-access
        self.assertEqual(ci.code_integrity_row(record('15', '3010', []))[2], '')

    def test_the_table_holds_the_events_of_the_operational_channel(self):
        self.assertEqual(ci._EVENTS, {  # pylint: disable=protected-access
            ('3001', '0'): 'Code Integrity determined an unsigned kernel module %2 is loaded into the system.',
            ('3001', '1'): 'Code Integrity determined an unsigned kernel module %2 is loaded into the system.',
            ('3002', '0'): 'Code Integrity is unable to verify the image integrity of the file %2 because '
                           'the set of per-page image hashes could not be found on the system.',
            ('3002', '1'): 'Code Integrity is unable to verify the image integrity of the file %2 because '
                           'the set of per-page image hashes could not be found on the system.',
            ('3003', '0'): 'Code Integrity is unable to verify the image integrity of the file %2 because '
                           'the set of per-page image hashes could not be found on the system.',
            ('3003', '1'): 'Code Integrity is unable to verify the image integrity of the file %2 because '
                           'the set of per-page image hashes could not be found on the system.',
            ('3004', '0'): 'Windows is unable to verify the image integrity of the file %2 because file hash '
                           'could not be found on the system.',
            ('3004', '1'): 'Windows is unable to verify the image integrity of the file %2 because file hash '
                           'could not be found on the system.',
            ('3005', '0'): 'Code Integrity is unable to verify the image integrity of the file %2 because a '
                           'file hash could not be found on the system.',
            ('3005', '1'): 'Code Integrity is unable to verify the image integrity of the file %2 because a '
                           'file hash could not be found on the system.',
            ('3010', '0'): '',
            ('3010', '1'): 'Code Integrity was unable to load the %2 catalog.',
            ('3021', '0'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
            ('3021', '1'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
            ('3022', '0'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
            ('3022', '1'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
            ('3023', '0'): 'The driver %2 is blocked from loading as the driver has been revoked by Microsoft.',
            ('3023', '1'): 'The driver %2 is blocked from loading as the driver has been revoked by Microsoft.',
            ('3024', '0'): 'Windows was unable to update the boot catalog cache file.',
            ('3026', '0'): 'Code Integrity was unable to load the %2 catalog because the signing certificate '
                           'for this catalog has been revoked.',
            ('3032', '0'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
            ('3032', '1'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
            ('3033', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements.',
            ('3034', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3035', '0'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
            ('3035', '1'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
            ('3036', '0'): 'Windows is unable to verify the integrity of the file %2 because the signing '
                           'certificate has been revoked.',
            ('3036', '1'): 'Windows is unable to verify the integrity of the file %2 because the signing '
                           'certificate has been revoked.',
            ('3037', '0'): 'Code Integrity determined an unsigned image %2 is loaded into the system.',
            ('3037', '1'): 'Code Integrity determined an unsigned image %2 is loaded into the system.',
            ('3050', '0'): 'Code Integrity completed retrieval of file cache.',
            ('3051', '0'): 'Code Integrity completed retrieval of file cache.',
            ('3052', '0'): 'Code Integrity completed retrieval of file cache.',
            ('3057', '0'): 'Code Integrity completed retrieval of file cache.',
            ('3058', '0'): 'Code Integrity completed retrieval of file cache.',
            ('3063', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the security requirements for %5.',
            ('3065', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the security requirements for %5.',
            ('3066', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3067', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3068', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3069', '0'): 'Code Integrity was unable to load the weak crypto policy value from registry.',
            ('3070', '0'): 'Code Integrity was unable to load the weak crypto policy from registry store.',
            ('3071', '0'): 'Code Integrity was unable to load the weak crypto policies.',
            ('3072', '0'): 'Code Integrity determined that the module %2 is not compatible with hypervisor '
                           'enforcement due to it having non-page aligned sections.',
            ('3073', '0'): 'Code Integrity determined that the module %2 is not compatible with strict mode '
                           'hypervisor enforcement due to it having an executable section that is also '
                           'writable.',
            ('3074', '0'): 'Code Integrity was unable to verify a page for a module verified using '
                           'hypervisor enforcement.',
            ('3076', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3076', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3076', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3076', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3076', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy (Policy '
                           'ID:%29).',
            ('3076', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy (Policy '
                           'ID:%33).',
            ('3077', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3077', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3077', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3077', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3077', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy (Policy '
                           'ID:%29).',
            ('3077', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy (Policy '
                           'ID:%33).',
            ('3078', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3078', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3078', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3078', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3079', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3079', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3079', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3079', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated Advanced Threat Protection '
                           'policy.',
            ('3080', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated '
                           'Driver policy.',
            ('3080', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '6'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '7'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated Advanced Threat Protection '
                           'policy.',
            ('3080', '8'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated '
                           'Driver policy.',
            ('3080', '9'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '10'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                            'meet the %5 signing level requirements or violated code integrity policy.',
            ('3080', '11'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                            'meet the %5 signing level requirements or violated Advanced Threat Protection '
                            'policy.',
            ('3080', '12'): 'Code Integrity determined that a process (%4) attempted to load %2 that '
                            'violated Driver policy.',
            ('3081', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated Advanced Threat Protection '
                           'policy.',
            ('3081', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated '
                           'Driver policy.',
            ('3081', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '6'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '7'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated Advanced Threat Protection '
                           'policy.',
            ('3081', '8'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated '
                           'Driver policy.',
            ('3081', '9'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '10'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                            'meet the %5 signing level requirements or violated code integrity policy.',
            ('3081', '11'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                            'meet the %5 signing level requirements or violated Advanced Threat Protection '
                            'policy.',
            ('3081', '12'): 'Code Integrity determined that a process (%4) attempted to load %2 that '
                            'violated Driver policy.',
            ('3082', '0'): 'Code Integrity determined kernel module %2 that did not meet the WHQL '
                           'requirements is loaded into the system.',
            ('3083', '0'): 'Code Integrity determined kernel module %2 that did not meet the WHQL '
                           'requirements is loaded into the system.',
            ('3084', '0'): 'Code Integrity will enable WHQL driver enforcement for this boot session.',
            ('3085', '0'): 'Code Integrity will disable WHQL driver enforcement for this boot session.',
            ('3086', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the signing requirements for Isolated User Mode.',
            ('3087', '0'): 'Code Integrity determined that the kernel module %2 is not compatible with '
                           'hypervisor enforcement.',
            ('3087', '1'): 'Code Integrity determined that a process (%6) attempted to load %2 that is not '
                           'compatible with hypervisor enforcement.',
            ('3089', '0'): 'Signature information for another event.',
            ('3089', '1'): 'Signature information for another event.',
            ('3089', '2'): 'Signature information for another event.',
            ('3089', '3'): 'Signature information for another event.',
            ('3090', '0'): 'Code Integrity testing module %2 against policy %11.',
            ('3091', '0'): 'Code Integrity testing module %2 against policy %11.',
            ('3092', '0'): 'Code Integrity testing module %2 against policy %11.',
            ('3093', '0'): 'other (see event data)',
            ('3094', '0'): 'other (see event data)',
            ('3095', '0'): 'Code Integrity policy %5 %2 is set to unrefreshable.',
            ('3095', '1'): 'Code Integrity policy %5 %2 is set to unrefreshable.',
            ('3096', '0'): 'No change in active Code Integrity policy %5 %2 after refresh.',
            ('3096', '1'): 'No change in active Code Integrity policy %5 %2 after refresh.',
            ('3097', '0'): 'Not allowed to refresh Code Integrity policy %5 %2.',
            ('3097', '1'): 'Not allowed to refresh Code Integrity policy %5 %2.',
            ('3098', '0'): 'other (see event data)',
            ('3099', '0'): 'Refreshed and activated Code Integrity policy %5 %2.',
            ('3099', '1'): 'Refreshed and activated Code Integrity policy %5 %2.',
            ('3100', '0'): 'Refreshed but not activated Code Integrity policy %5 %2.',
            ('3100', '1'): 'Refreshed but not activated Code Integrity policy %5 %2.',
            ('3101', '0'): 'Code Integrity policy refresh started for %1 policies.',
            ('3102', '0'): 'Code Integrity policy refresh finished for %1 policies.',
            ('3103', '0'): 'Ignoring refresh for Code Integrity policy ID %1.',
            ('3103', '1'): 'Ignoring refresh for Code Integrity policy ID %1.',
            ('3104', '0'): 'Windows blocked file %2 which has been disallowed for protected processes.',
            ('3105', '0'): 'Trying to refresh Code Integrity policy with policy ID %1.',
            ('3108', '0'): 'Code Integrity successfully switched from %3 mode to %4 mode.',
            ('3109', '0'): 'Code Integrity already switched from %3 mode to %4 mode.',
            ('3110', '0'): 'Code Integrity failed to switch from %3 mode to %4 mode with error code %5.',
            ('3111', '0'): 'Code Integrity determined that a process (%6) attempted to load %2 that is not '
                           'compatible with hypervisor enforcement.',
            ('3112', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not '
                           'meet the %5 signing level requirements or violated code integrity policy.',
            ('3113', '0'): 'Code Integrity could not update the driver.stl revocation list.',
            ('3114', '0'): 'Code Integrity determined that %4 is trying to load %2 which failed the dynamic '
                           'code trust verification with error code of %5.',
            ('3115', '0'): 'Code Integrity determined that %4 is trying to load %2 which failed the dynamic '
                           'code trust verification with error code of %5.',
            ('3116', '0'): 'Signature information for Code Integrity policy ID %1.',
        })


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'File Name', 'Process Name', 'Policy Name', 'Publisher', 'Issuer',
               'Activity ID', 'Other Fields', 'User SID', 'Record ID', 'Computer')

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '3033', [('FileNameBuffer', 'B')]), record('21', '3085', [('Settings', '1')]), record('22', '3089', [('PublisherName', 'P')], version='2'),
                   record('24', '9999', [])]
        with mock.patch.object(ci, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = ci.codeIntegrityEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-CodeIntegrity%4Operational.evtx', 'Code Integrity Events',
                                       provider='Microsoft-Windows-CodeIntegrity')
        self.assertEqual([(row[11], row[1], row[3], row[6]) for row in rows], [('23', '3033', 'B', ''), ('21', '3085', '', ''), ('22', '3089', '', 'P'), ('24', '9999', '', '')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(ci, 'read_event_records', return_value=([record('1', '3085', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(ci.codeIntegrityEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(ci, 'read_event_records', return_value=([], [])):
            self.assertEqual(ci.codeIntegrityEvents.__wrapped__(_Context()), (self.HEADERS, [], ''))


if __name__ == '__main__':
    unittest.main()
