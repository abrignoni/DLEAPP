"""Pin the rows in scripts/artifacts/windowsDomainAuthEvents.py.

The records are built from XML of the shape python-evtx renders for these events (made-up names,
SIDs and addresses); the expected rows are written out.
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

from scripts.artifacts import windowsDomainAuthEvents as domain  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1104'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Security.evtx'
WHEN = '2023-01-05 20:15:01.100000+00:00'
SUBJECT = [('SubjectUserSid', SID), ('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB'),
           ('SubjectLogonId', '0x12345')]
SUBJECT_ROW = ('examiner', 'LAB', SID, '0x12345')


def record(event_id, fields, record_id='300', provider='Microsoft-Windows-Security-Auditing'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}"></Provider>'
           f'<EventID Qualifiers="">{event_id}</EventID><Version>0</Version><Level>0</Level>'
           f'<TimeCreated SystemTime="{WHEN}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="704" ThreadID="5104"></Execution><Channel>Security</Channel>'
           f'<Computer>DC1.lab.example</Computer><Security UserID=""></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


TIME = datetime.datetime(2023, 1, 5, 20, 15, 1, 100000, tzinfo=datetime.timezone.utc)

TGT = record('4768', [('TargetUserName', 'user1'), ('TargetDomainName', 'LAB.EXAMPLE'), ('TargetSid', SID),
                      ('ServiceName', 'krbtgt'), ('ServiceSid', SID[:-4] + '502'), ('TicketOptions', '0x40810010'),
                      ('Status', '0x0'), ('TicketEncryptionType', '0x12'), ('PreAuthType', '2'),
                      ('IpAddress', '::ffff:10.0.0.12'), ('IpPort', '49273'), ('CertIssuerName', ''),
                      ('CertSerialNumber', ''), ('CertThumbprint', '')])
TGS = record('4769', [('TargetUserName', 'user1@LAB.EXAMPLE'), ('TargetDomainName', 'LAB.EXAMPLE'),
                      ('ServiceName', 'HOST1$'), ('ServiceSid', SID[:-4] + '1105'), ('TicketOptions', '0x40810000'),
                      ('TicketEncryptionType', '0x00000017'), ('IpAddress', '::1'), ('IpPort', '0'),
                      ('Status', '0x00000020'), ('LogonGuid', '{00000000-0000-0000-0000-000000000000}'),
                      ('TransmittedServices', '-')])
RENEW = record('4770', [('TargetUserName', 'HOST1$@LAB.EXAMPLE'), ('TargetDomainName', 'LAB.EXAMPLE'),
                        ('ServiceName', 'krbtgt'), ('ServiceSid', SID[:-4] + '502'), ('TicketOptions', '0x00010002'),
                        ('TicketEncryptionType', '0x12'), ('IpAddress', '::ffff:10.0.0.13'), ('IpPort', '61750')])
PREAUTH = record('4771', [('TargetUserName', 'user2'), ('TargetSid', SID[:-4] + '1106'),
                          ('ServiceName', 'krbtgt/LAB.EXAMPLE'), ('TicketOptions', '0x40810010'),
                          ('Status', '0x18'), ('PreAuthType', '2'), ('IpAddress', '::ffff:10.0.0.14'),
                          ('IpPort', '50000'), ('CertIssuerName', 'Lab CA'), ('CertSerialNumber', '01AB'),
                          ('CertThumbprint', 'FF00')])
NTLM = record('4776', [('PackageName', 'MICROSOFT_AUTHENTICATION_PACKAGE_V1_0'), ('TargetUserName', 'user3'),
                       ('Workstation', 'WS01'), ('Status', '0xc0000064')])
SHARE = record('5140', SUBJECT + [('ObjectType', 'File'), ('IpAddress', '10.0.0.15'), ('IpPort', '60168'),
                                  ('ShareName', '\\\\*\\C$'), ('ShareLocalPath', '\\??\\C:\\'),
                                  ('AccessMask', '0x1'), ('AccessList', '%%4416\n\t\t\t\t')])
CHECK = record('5145', SUBJECT + [('ObjectType', 'File'), ('IpAddress', '10.0.0.15'), ('IpPort', '63564'),
                                  ('ShareName', '\\\\*\\ADMIN$'), ('ShareLocalPath', '\\??\\C:\\Windows'),
                                  ('RelativeTargetName', 'Temp\\a.exe'), ('AccessMask', '0x100081'),
                                  ('AccessList', '%%1541\n\t\t\t\t%%4416\n\t\t\t\t%%4423\n\t\t\t\t%%9999\n\t\t\t\t'),
                                  ('AccessReason', '-')])
DIRECTORY = record('4662', SUBJECT + [
    ('ObjectServer', 'DS'), ('ObjectType', '%{19195a5b-6da0-11d0-afd3-00c04fd930c9}'),
    ('ObjectName', '%{11111111-2222-3333-4444-555555555555}'), ('OperationType', 'Object Access'),
    ('HandleId', '0x0'), ('AccessList', '%%7688\n\t\t\t\t'), ('AccessMask', '0x100'),
    ('Properties', '%%7688\n\t\t{1131F6AD-9c07-11d1-f79f-00c04fc2dcd2}\n\t\t{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}'
                   '\n\t{19195a5b-6da0-11d0-afd3-00c04fd930c9}\n'),
    ('AdditionalInfo', '-'), ('AdditionalInfo2', '')])


class KerberosTest(unittest.TestCase):
    def test_a_tgt_request_names_its_codes_from_the_4768_tables(self):
        self.assertEqual(domain.kerberos_row(TGT), (
            TIME, '4768', 'A Kerberos authentication ticket (TGT) was requested.', 'user1', 'LAB.EXAMPLE', SID,
            'krbtgt', SID[:-4] + '502', '::ffff:10.0.0.12', '49273', '0x0 (KDC_ERR_NONE)',
            '0x40810010 (Forwardable, Renewable, Name-canonicalize, Renewable-ok)',
            '0x12 (AES256-CTS-HMAC-SHA1-96)', '2 (PA-ENC-TIMESTAMP)', '', '', '', '300', 'DC1.lab.example'))

    def test_a_service_ticket_keeps_the_stored_spelling_of_each_code(self):
        row = domain.kerberos_row(TGS)
        self.assertEqual(row[1:3], ('4769', 'A Kerberos service ticket was requested.'))
        self.assertEqual(row[5], '')
        self.assertEqual(row[10:17], ('0x00000020 (KRB_AP_ERR_TKT_EXPIRED)',
                                      '0x40810000 (Forwardable, Renewable, Name-canonicalize)',
                                      '0x00000017 (RC4-HMAC)', '', '{00000000-0000-0000-0000-000000000000}', '-',
                                      ''))

    def test_a_renewal_has_no_result_code_and_names_its_encryption_type(self):
        row = domain.kerberos_row(RENEW)
        self.assertEqual(row[10:14], ('', '0x00010002 (Name-canonicalize, Renew)', '0x12 (AES256-CTS-HMAC-SHA1-96)',
                                      ''))

    def test_a_pre_authentication_type_on_a_service_ticket_is_kept_as_stored(self):
        self.assertEqual(domain.kerberos_row(record('4769', [('PreAuthType', '2')]))[13], '2')

    def test_a_pre_authentication_failure_names_its_code_from_the_4771_table(self):
        row = domain.kerberos_row(PREAUTH)
        self.assertEqual(row[2], 'Kerberos pre-authentication failed.')
        self.assertEqual(row[10], '0x18 (KDC_ERR_PREAUTH_FAILED)')
        self.assertEqual(row[13], '2 (PA-ENC-TIMESTAMP)')
        self.assertEqual(row[16], 'Lab CA | 01AB | FF00')

    def test_the_three_code_tables_differ_where_microsoft_tables_differ(self):
        self.assertEqual(domain.named('0x1D', domain._TGT_CODES), '0x1D (KDC_ERR_SVC_UNAVAILABLE)')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0x1D', domain._TGS_CODES), '0x1D')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0x1B', domain._TGS_CODES), '0x1B (KDC_ERR_MUST_USE_USER2USER)')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0x1B', domain._TGT_CODES), '0x1B')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0x3E', domain._PRE_AUTH_CODES), '0x3E (KDC_ERROR_CLIENT_NOT_TRUSTED)')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0x42', domain._TGT_CODES), '0x42 (KRB_AP_ERR_USER_TO_USER_REQUIRED)')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0x42', domain._PRE_AUTH_CODES), '0x42 (KDC_ERR_CERTIFICATE_MISMATCH)')  # pylint: disable=protected-access

    def test_each_event_takes_its_result_code_from_its_own_page(self):
        self.assertEqual(domain.kerberos_row(record('4769', [('Status', '0x1D')]))[10], '0x1D')
        self.assertEqual(domain.kerberos_row(record('4768', [('Status', '0x1D')]))[10], '0x1D (KDC_ERR_SVC_UNAVAILABLE)')
        self.assertEqual(domain.kerberos_row(record('4771', [('Status', '0x42')]))[10],
                         '0x42 (KDC_ERR_CERTIFICATE_MISMATCH)')

    def test_a_right_named_twice_in_properties_is_listed_once(self):
        twice = '%%7688 {1131f6aa-9c07-11d1-f79f-00c04fc2dcd2} {1131F6AA-9C07-11D1-F79F-00C04FC2DCD2}'
        self.assertEqual(domain.control_access_rights(twice), 'DS-Replication-Get-Changes')

    def test_a_value_no_table_names_is_kept(self):
        self.assertEqual(domain.named('0x99', domain._TGT_CODES), '0x99')  # pylint: disable=protected-access
        self.assertEqual(domain.named('-', domain._TGT_CODES), '-')  # pylint: disable=protected-access
        self.assertEqual(domain.named('0xffffffff', domain._ENCRYPTION_TYPES), '0xffffffff')  # pylint: disable=protected-access
        self.assertEqual(domain.named('-', domain._PRE_AUTH_TYPES, base=10), '-')  # pylint: disable=protected-access

    def test_ticket_options_number_bits_from_the_most_significant(self):
        self.assertEqual(domain.ticket_options('0x80000000'), '0x80000000 (unnamed bit 0)')
        self.assertEqual(domain.ticket_options('0x00000001'), '0x00000001 (Validate)')
        self.assertEqual(domain.ticket_options('0x00000040'), '0x00000040 (unnamed bit 25)')
        self.assertEqual(domain.ticket_options('0x0'), '0x0')
        self.assertEqual(domain.ticket_options(''), '')
        self.assertEqual(domain.ticket_options('0x1FFFFFFFF'), '0x1FFFFFFFF')


class OtherEventsTest(unittest.TestCase):
    def test_an_ntlm_validation(self):
        self.assertEqual(domain.ntlm_row(NTLM), (
            TIME, 'user3', 'WS01', '0xc0000064 (The username you typed does not exist. Bad username.)',
            'MICROSOFT_AUTHENTICATION_PACKAGE_V1_0', '300', 'DC1.lab.example'))

    def test_a_share_access_and_a_share_check(self):
        self.assertEqual(domain.share_row(SHARE), (
            TIME, '5140', 'A network share object was accessed.', '\\\\*\\C$', '\\??\\C:\\', '',
            'ReadData (or ListDirectory) (%%4416)', '0x1', '', *SUBJECT_ROW, '10.0.0.15', '60168', '300',
            'DC1.lab.example'))
        row = domain.share_row(CHECK)
        self.assertEqual(row[2], 'A network share object was checked to see whether client can be granted '
                                 'desired access.')
        self.assertEqual(row[5:9], ('Temp\\a.exe', 'SYNCHRONIZE (%%1541), ReadData (or ListDirectory) (%%4416), '
                                    'ReadAttributes (%%4423), %%9999', '0x100081', '-'))

    def test_a_directory_object_access_names_control_access_rights_once_each(self):
        self.assertEqual(domain.directory_row(DIRECTORY), (
            TIME, 'Object Access', 'DS', '%{19195a5b-6da0-11d0-afd3-00c04fd930c9}',
            '%{11111111-2222-3333-4444-555555555555}', 'Control Access', '0x100',
            'DS-Replication-Get-Changes-All, DS-Replication-Get-Changes',
            '%%7688 {1131F6AD-9c07-11d1-f79f-00c04fc2dcd2} {1131f6aa-9c07-11d1-f79f-00c04fc2dcd2} '
            '{19195a5b-6da0-11d0-afd3-00c04fd930c9}', '-', '', '0x0', *SUBJECT_ROW, '300', 'DC1.lab.example'))

    def test_directory_accesses_list_unnamed_bits(self):
        self.assertEqual(domain.directory_accesses('0x00000030'), 'Read Property, Write Property')
        self.assertEqual(domain.directory_accesses('0x00000200'), 'unnamed bits 0x200')
        self.assertEqual(domain.directory_accesses('x'), '')

    def test_each_share_field_lands_in_its_own_column(self):
        fields = [('ShareName', 'a'), ('ShareLocalPath', 'b'), ('RelativeTargetName', 'c'), ('AccessList', 'd'),
                  ('AccessMask', 'e'), ('AccessReason', 'f'), ('SubjectUserName', 'g'), ('SubjectDomainName', 'h'),
                  ('SubjectUserSid', 'i'), ('SubjectLogonId', 'j'), ('IpAddress', 'k'), ('IpPort', 'l')]
        self.assertEqual(domain.share_row(record('5145', fields, '9'))[3:],
                         ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', '9', 'DC1.lab.example'))

    def test_each_kerberos_field_lands_in_its_own_column(self):
        fields = [('TargetUserName', 'a'), ('TargetDomainName', 'b'), ('TargetSid', 'c'), ('ServiceName', 'd'),
                  ('ServiceSid', 'e'), ('IpAddress', 'f'), ('IpPort', 'g'), ('Status', 'h'), ('TicketOptions', 'i'),
                  ('TicketEncryptionType', 'j'), ('PreAuthType', 'k'), ('LogonGuid', 'l'),
                  ('TransmittedServices', 'm'), ('CertIssuerName', 'n')]
        self.assertEqual(domain.kerberos_row(record('4768', fields, '9'))[3:],
                         ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n |  | ', '9',
                          'DC1.lab.example'))


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class DomainRecordsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.addCleanup(domain._read.clear)  # pylint: disable=protected-access
        domain._read.clear()  # pylint: disable=protected-access
        self.log = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'System32', 'winevt', 'Logs', 'Security.evtx')
        os.makedirs(os.path.dirname(self.log))
        with open(self.log, 'wb') as handle:
            handle.write(b'x' * 10)

    def test_the_log_is_read_once_for_the_four_artifacts_and_each_takes_its_events(self):
        found = ([TGT, TGS, RENEW, PREAUTH, NTLM, SHARE, CHECK, DIRECTORY], [self.log])
        with mock.patch.object(domain, 'read_event_records', return_value=found) as reader:
            kerberos = domain.kerberosTicketEvents.__wrapped__(_Context([self.log]))
            ntlm = domain.ntlmCredentialValidations.__wrapped__(_Context([self.log]))
            shares = domain.networkShareAccess.__wrapped__(_Context([self.log]))
            directory = domain.directoryServiceAccess.__wrapped__(_Context([self.log]))
        reader.assert_called_once()
        self.assertEqual(reader.call_args.kwargs['provider'], 'Microsoft-Windows-Security-Auditing')
        self.assertEqual(reader.call_args.kwargs['event_ids'],
                         {'4768', '4769', '4770', '4771', '4776', '5140', '5145', '4662'})
        self.assertEqual([len(result[1]) for result in (kerberos, ntlm, shares, directory)], [4, 1, 2, 1])
        for headers, rows, source in (kerberos, ntlm, shares, directory):
            self.assertEqual({len(row) for row in rows}, {len(headers)})
            self.assertEqual(source, self.log)

    def test_a_changed_log_is_read_again(self):
        with mock.patch.object(domain, 'read_event_records', return_value=([], [self.log])) as reader:
            domain.kerberosTicketEvents.__wrapped__(_Context([self.log]))
            with open(self.log, 'ab') as handle:
                handle.write(b'y')
            domain.ntlmCredentialValidations.__wrapped__(_Context([self.log]))
        self.assertEqual(reader.call_count, 2)


if __name__ == '__main__':
    unittest.main()
