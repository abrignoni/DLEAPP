"""Pin the User Access Logging - System Identity artifact (scripts/artifacts/windowsUserAccessLogging.py).

No ESE writer is available here, so the record conversion is tested on dicts shaped like the rows
scripts/ese_rows.TableRows gives for SYSTEM_IDENTITY, and the processor with the database read replaced. The
strings are made up. The numbers and timestamps are those of the first and third szechuan_dc01_server2012r2
records.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsUserAccessLogging as ual
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
PAD = '\0' * 12


def record(**changes):
    row = {
        'CreationTime': 132448316944240000,
        'PhysicalProcessorCount': 1, 'CoresPerPhysicalProcessor': 2, 'LogicalProcessorsPerPhysicalProcessor': 4,
        'MaximumMemory': 2147483648,
        'OSMajor': 6, 'OSMinor': 3, 'OSBuildNumber': 9600, 'OSPlatformId': 2,
        'ServicePackMajor': 0, 'ServicePackMinor': 0, 'OSSuiteMask': 272, 'OSProductType': 3,
        'OSCurrentTimeZone': 65116, 'OSDaylightInEffect': 255,
        'SystemManufacturer': 'Maker' + PAD, 'SystemProductName': 'Model' + PAD,
        'SystemSMBIOSUUID': '00000000-1111-2222-3333-444444444444\0', 'SystemSerialNumber': 'SN-1' + PAD,
        'SystemDNSHostName': 'HOST-A' + PAD, 'SystemDomainName': 'example.test' + PAD,
        'OSSerialNumber': '00000-00000-00000-AA000' + PAD, 'OSCountryCode': '1' + PAD,
        'OSLastBootUpTime': '20200917100320.485021-420' + PAD,
    }
    row.update(changes)
    return row


class Values(unittest.TestCase):
    def test_text(self):
        self.assertEqual(ual.text('abc\0\0\0'), 'abc')
        self.assertEqual(ual.text('abc\0junk'), 'abc')
        self.assertEqual(ual.text(b'abc\0'), 'abc')
        self.assertEqual(ual.text(None), '')
        self.assertEqual(ual.text(''), '')

    def test_cim_datetime(self):
        self.assertEqual(ual.cim_datetime_utc('20200917100320.485021-420'),
                         datetime.datetime(2020, 9, 17, 17, 3, 20, 485021, tzinfo=UTC))
        self.assertEqual(ual.cim_datetime_utc('20200917100320.485021+060'),
                         datetime.datetime(2020, 9, 17, 9, 3, 20, 485021, tzinfo=UTC))
        self.assertEqual(ual.cim_datetime_utc('20200917100320.000000+000'),
                         datetime.datetime(2020, 9, 17, 10, 3, 20, tzinfo=UTC))
        self.assertEqual(ual.cim_datetime_utc('20200101003000.000000+060'),
                         datetime.datetime(2019, 12, 31, 23, 30, tzinfo=UTC))

    def test_cim_datetime_not_converted(self):
        for value in ('', '20200917100320.485021-***', '20200917100320.485021', '20201317100320.000000+000',
                      '2020091710032.485021-420', 'x20200917100320.485021-420', '20200917100320.485021-4200'):
            self.assertEqual(ual.cim_datetime_utc(value), '', value)

    def test_signed_minutes(self):
        self.assertEqual(ual.signed_minutes(65116), -420)
        self.assertEqual(ual.signed_minutes(0x8000), -0x8000)
        self.assertEqual(ual.signed_minutes(0x7fff), 0x7fff)
        self.assertEqual(ual.signed_minutes(60), 60)
        self.assertEqual(ual.signed_minutes(0), 0)
        self.assertEqual(ual.signed_minutes(None), '')

    def test_product_type(self):
        self.assertEqual(ual.product_type(1), '1 (Work Station)')
        self.assertEqual(ual.product_type(2), '2 (Domain Controller)')
        self.assertEqual(ual.product_type(3), '3 (Server)')
        self.assertEqual(ual.product_type(7), '7')
        self.assertEqual(ual.product_type(0), '0')
        self.assertEqual(ual.product_type(None), '')


class IdentityRow(unittest.TestCase):
    def test_row(self):
        self.assertEqual(ual.identity_row(record()), (
            datetime.datetime(2020, 9, 17, 15, 54, 54, 424000, tzinfo=UTC),
            datetime.datetime(2020, 9, 17, 17, 3, 20, 485021, tzinfo=UTC),
            '20200917100320.485021-420', -420, 'HOST-A', 'example.test', '3 (Server)', '6.3.9600', '0.0',
            '00000-00000-00000-AA000', 'Maker', 'Model', '00000000-1111-2222-3333-444444444444', 'SN-1',
            1, 2, 4, 2147483648, '1'))

    def test_missing_values(self):
        row = ual.identity_row({})
        self.assertEqual(row, ('',) * 19)
        self.assertEqual(ual.identity_row(record(OSBuildNumber=None))[7], '')
        self.assertEqual(ual.identity_row(record(ServicePackMinor=None))[8], '')
        self.assertEqual(ual.identity_row(record(ServicePackMajor=None))[8], '')
        self.assertEqual(ual.identity_row(record(OSMajor=None))[7], '')

    def test_zero_values_kept(self):
        row = ual.identity_row(record(OSMinor=0, ServicePackMajor=2, ServicePackMinor=1,
                                      PhysicalProcessorCount=0, OSCurrentTimeZone=0))
        self.assertEqual(row[7], '6.0.9600')
        self.assertEqual(row[8], '2.1')
        self.assertEqual(row[3], 0)
        self.assertEqual(row[14], 0)

    def test_creation_time_not_an_integer(self):
        self.assertEqual(ual.identity_row(record(CreationTime=b'\x00' * 8))[0], '')
        self.assertEqual(ual.identity_row(record(CreationTime=0))[0], '')

    def test_boot_time_unconverted_kept_as_stored(self):
        row = ual.identity_row(record(OSLastBootUpTime='20200917100320.485021-***\0'))
        self.assertEqual(row[1:3], ('', '20200917100320.485021-***'))

    def test_named(self):
        self.assertEqual(ual._named({b'OSMajor': 6, 'OSMinor': 3}), {'OSMajor': 6, 'OSMinor': 3})  # pylint: disable=protected-access


class Processor(unittest.TestCase):
    def run_artifact(self, names, read):
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for name in names:
                path = os.path.join(folder, *name.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(b'x')
                paths.append(path)
            context = mock.Mock()
            context.get_files_found.return_value = paths
            context.get_relative_path.side_effect = lambda p: os.path.relpath(p, folder)
            logged = []
            with mock.patch.object(ual, '_read', side_effect=read), \
                    mock.patch.object(ual, 'logfunc', side_effect=logged.append):
                result = ual.windowsUserAccessLoggingSystemIdentity.__wrapped__(context)
            return result, [os.path.relpath(p, folder) for p in result[2].split('\n') if p], logged

    def test_rows_sorted_and_only_the_database_read(self):
        late = ual.identity_row(record(CreationTime=132449418114420000))
        early = ual.identity_row(record())
        seen = []

        def read(_path, relative):
            seen.append(relative)
            return [late, early]

        (headers, rows, _), sources, logged = self.run_artifact(
            ['Sum/SystemIdentity.mdb', 'Sum/Current.mdb'], read)
        self.assertEqual(len(headers), 19)
        self.assertEqual(rows, [early, late])
        self.assertEqual(seen, [os.path.join('Sum', 'SystemIdentity.mdb')])
        self.assertEqual(sources, [os.path.join('Sum', 'SystemIdentity.mdb')])
        self.assertEqual(logged, [])

    def test_unreadable_database_logged_and_skipped(self):
        def read(_path, relative):
            if relative.startswith('b'):
                raise ValueError('bad page')
            return [ual.identity_row(record())]

        (_, rows, _), sources, logged = self.run_artifact(
            ['a/SystemIdentity.mdb', 'b/SystemIdentity.mdb'], read)
        self.assertEqual(len(rows), 1)
        self.assertEqual(sources, [os.path.join('a', 'SystemIdentity.mdb')])
        self.assertEqual(len(logged), 1)
        self.assertIn('could not read', logged[0])
        self.assertIn('ValueError: bad page', logged[0])

    def test_empty_table_still_names_the_file(self):
        (_, rows, _), sources, _ = self.run_artifact(['Sum/SystemIdentity.mdb'], lambda path, relative: [])
        self.assertEqual(rows, [])
        self.assertEqual(sources, [os.path.join('Sum', 'SystemIdentity.mdb')])

    def test_reader_missing(self):
        with mock.patch.object(ual, 'ese_rows', None):
            (_, rows, source), _, logged = self.run_artifact(['Sum/SystemIdentity.mdb'], lambda *a: [])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn('not available', logged[0])


GUID_LE = bytes.fromhex('6f22a910ee50d849a3939a501d47ce04')
GUID_TEXT = '{10a9226f-50ee-49d8-a393-9a501d47ce04}'


def client(**changes):
    row = {'RoleGuid': GUID_LE, 'TenantId': bytes(16), 'TotalAccesses': 3,
           'InsertDate': 133485408224407884, 'LastAccess': 133485840000000000,
           'Address': b'0a000005', 'AuthenticatedUserName': 'example\\someone' + PAD, 'ClientName': None,
           'Day1': 1, 'Day2': 2}
    row.update(changes)
    return row


class AccessValues(unittest.TestCase):
    def test_guid(self):
        self.assertEqual(ual.guid(GUID_LE), GUID_TEXT)
        self.assertEqual(ual.guid(bytes(16)), '{00000000-0000-0000-0000-000000000000}')
        self.assertEqual(ual.guid(b'short'), '')
        self.assertEqual(ual.guid(None), '')
        self.assertEqual(ual.guid('not bytes'), '')

    def test_client_address(self):
        self.assertEqual(ual.client_address(b'0a000005'), '10.0.0.5')
        self.assertEqual(ual.client_address(b'00000000000000000000000000000001'), '::1')
        self.assertEqual(ual.client_address('c0a80001'), '192.168.0.1')
        self.assertEqual(ual.client_address(b'0a0000'), '0a0000')
        self.assertEqual(ual.client_address(b'zz'), 'zz')
        self.assertEqual(ual.client_address('odd'), 'odd')
        self.assertEqual(ual.client_address(None), '')

    def test_daily_counts(self):
        self.assertEqual(ual.daily_counts({'Day1': 1, 'Day40': 7, 'Day2': 0}, 2024), '2024-01-01: 1; 2024-02-09: 7')
        self.assertEqual(ual.daily_counts({'Day366': 4}, 2024), '2024-12-31: 4')
        self.assertEqual(ual.daily_counts({'Day60': 1}, 2023), '2023-03-01: 1')
        self.assertEqual(ual.daily_counts({'Day1': None, 'Day3': 0}, 2024), '')
        self.assertEqual(ual.daily_counts({'Day1': 1}, None), '')
        self.assertEqual(ual.daily_counts({'Day366': 1}, 9999), '')

    def test_client_row(self):
        self.assertEqual(ual.client_row(client(), {GUID_TEXT: 'File Server'}), (
            datetime.datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
            datetime.datetime(2024, 1, 1, 0, 0, 22, 440788, tzinfo=UTC),
            'File Server', 'example\\someone', '10.0.0.5', 3, '2024-01-01: 1; 2024-01-02: 2', GUID_TEXT,
            '{00000000-0000-0000-0000-000000000000}'))

    def test_client_row_unknown_role_and_missing_values(self):
        row = ual.client_row(client(InsertDate=None, LastAccess=None, TotalAccesses=None), {})
        self.assertEqual(row[:3], ('', '', ''))
        self.assertEqual(row[5:8], ('', '', GUID_TEXT))
        row = ual.client_row(client(InsertDate=b'\x01' * 8, LastAccess=1.5), {})
        self.assertEqual(row[:2], ('', ''))
        self.assertEqual(row[6], '')

    def test_role_access_and_dns_rows(self):
        self.assertEqual(ual.role_access_row({'RoleGuid': GUID_LE, 'FirstSeen': 133485408224407884,
                                              'LastSeen': 133485840000000000}, {GUID_TEXT: 'File Server'}),
                         (datetime.datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
                          datetime.datetime(2024, 1, 1, 0, 0, 22, 440788, tzinfo=UTC), 'File Server', GUID_TEXT))
        self.assertEqual(ual.dns_row({'LastSeen': 133485840000000000, 'HostName': 'host\0',
                                      'Address': '10.0.0.5\0'}, {}),
                         (datetime.datetime(2024, 1, 1, 12, 0, tzinfo=UTC), 'host', '10.0.0.5'))


class AccessProcessor(unittest.TestCase):
    def run_access(self, artifact, tables, names):
        """tables: {(basename, table): [records]}; names: files to create, relative to a Sum folder."""
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for name in names:
                path = os.path.join(folder, *name.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(b'x')
                paths.append(path)
            context = mock.Mock()
            context.get_files_found.return_value = paths
            context.get_relative_path.side_effect = lambda p: os.path.relpath(p, folder)
            asked = []

            def table(path, name, _label, relative):
                asked.append((relative, name))
                key = (os.path.relpath(path, folder), name)
                if key not in tables:
                    raise ValueError('unreadable')
                return tables[key]

            logged = []
            with mock.patch.object(ual, '_table', side_effect=table), \
                    mock.patch.object(ual, 'logfunc', side_effect=logged.append):
                headers, rows, source = artifact.__wrapped__(context)
            return headers, rows, [os.path.relpath(p, folder) for p in source.split('\n') if p], asked, logged

    def test_identical_records_merge_and_differing_ones_do_not(self):
        same, changed = client(), client(TotalAccesses=4, Day2=3)
        tables = {('a/Sum/Current.mdb', 'CLIENTS'): [same, changed],
                  ('a/Sum/{12345678-ABCD-4EF0-9123-456789ABCDEF}.mdb', 'CLIENTS'): [same],
                  ('a/Sum/SystemIdentity.mdb', 'ROLE_IDS'): [{'RoleGuid': GUID_LE, 'RoleName': 'File Server' + PAD}]}
        headers, rows, sources, asked, logged = self.run_access(
            ual.windowsUserAccessLoggingClients, tables,
            ['a/Sum/Current.mdb', 'a/Sum/{12345678-ABCD-4EF0-9123-456789ABCDEF}.mdb', 'a/Sum/SystemIdentity.mdb',
             'a/Sum/Other.mdb', 'a/Sum/{not-a-guid}.mdb'])
        self.assertEqual(len(headers), 10)
        self.assertEqual(len(rows), 2)
        merged = [row for row in rows if row[5] == 3][0]
        alone = [row for row in rows if row[5] == 4][0]
        self.assertEqual(merged[-1], 'Current.mdb; {12345678-ABCD-4EF0-9123-456789ABCDEF}.mdb')
        self.assertEqual(alone[-1], 'Current.mdb')
        self.assertEqual(merged[2], 'File Server')
        self.assertEqual(sorted(sources), sorted([os.path.join('a', 'Sum', 'Current.mdb'),
                                                  os.path.join('a', 'Sum', '{12345678-ABCD-4EF0-9123-456789ABCDEF}.mdb')]))
        self.assertNotIn(os.path.join('a', 'Sum', 'Other.mdb'), [relative for relative, _ in asked])
        self.assertEqual(logged, [])

    def test_folders_are_kept_apart(self):
        same = client()
        tables = {('a/Sum/Current.mdb', 'CLIENTS'): [same], ('b/Sum/Current.mdb', 'CLIENTS'): [same],
                  ('a/Sum/SystemIdentity.mdb', 'ROLE_IDS'): [{'RoleGuid': GUID_LE, 'RoleName': 'File Server'}]}
        _, rows, _, _, _ = self.run_access(ual.windowsUserAccessLoggingClients, tables,
                                           ['a/Sum/Current.mdb', 'b/Sum/Current.mdb', 'a/Sum/SystemIdentity.mdb'])
        self.assertEqual(sorted(row[2] for row in rows), ['', 'File Server'])
        self.assertEqual([row[-1] for row in rows], ['Current.mdb', 'Current.mdb'])

    def test_unreadable_database_logged_and_left_out(self):
        tables = {('a/Sum/Current.mdb', 'DNS'): [{'LastSeen': 133485840000000000, 'HostName': 'h', 'Address': 'x'}]}
        _, rows, sources, _, logged = self.run_access(
            ual.windowsUserAccessLoggingDns, tables,
            ['a/Sum/Current.mdb', 'a/Sum/{12345678-ABCD-4EF0-9123-456789ABCDEF}.mdb'])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][-1], 'Current.mdb')
        self.assertEqual(sources, [os.path.join('a', 'Sum', 'Current.mdb')])
        self.assertEqual(len(logged), 1)
        self.assertIn('could not read', logged[0])

    def test_unreadable_role_ids_leaves_roles_blank(self):
        tables = {('a/Sum/Current.mdb', 'ROLE_ACCESS'): [{'RoleGuid': GUID_LE, 'FirstSeen': 1, 'LastSeen': 2}]}
        _, rows, _, _, logged = self.run_access(ual.windowsUserAccessLoggingRoleAccess, tables,
                                                ['a/Sum/Current.mdb', 'a/Sum/SystemIdentity.mdb'])
        self.assertEqual(rows[0][2:4], ('', GUID_TEXT))
        self.assertEqual(len(logged), 1)

    def test_rows_sorted_by_first_column(self):
        early = client(LastAccess=133485408224407884)
        late = client(LastAccess=133485840000000000, Day2=5)
        tables = {('a/Sum/Current.mdb', 'CLIENTS'): [late, early]}
        _, rows, _, _, _ = self.run_access(ual.windowsUserAccessLoggingClients, tables, ['a/Sum/Current.mdb'])
        self.assertLess(rows[0][0], rows[1][0])

    def test_empty_table_still_names_the_file(self):
        _, rows, sources, _, _ = self.run_access(ual.windowsUserAccessLoggingDns,
                                                 {('a/Sum/Current.mdb', 'DNS'): []}, ['a/Sum/Current.mdb'])
        self.assertEqual((rows, sources), ([], [os.path.join('a', 'Sum', 'Current.mdb')]))

    def test_reader_missing(self):
        with mock.patch.object(ual, 'ese_rows', None):
            _, rows, sources, _, logged = self.run_access(ual.windowsUserAccessLoggingRoleAccess, {},
                                                          ['a/Sum/Current.mdb'])
        self.assertEqual((rows, sources), ([], []))
        self.assertIn('not available', logged[0])


if __name__ == '__main__':
    unittest.main()
