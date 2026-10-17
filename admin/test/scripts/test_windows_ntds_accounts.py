"""Pin scripts/artifacts/windowsNtdsAccounts.py.

The directory objects are made up (names, SIDs and times); the ESE walk is replaced by lists of
records shaped as scripts/ese_rows.TableRows returns them, with the column names ntds.dit uses.
No record of any real database is used.
"""
import binascii
import datetime
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsNtdsAccounts as ntds  # pylint: disable=wrong-import-position

DOMAIN = (21, 1111111111, 2222222222, 3333333333)


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


def stored_sid(*subs):
    """A SID the way the datatable holds it: hex text, sub-authorities little-endian, the last big-endian."""
    data = bytes([1, len(subs)]) + (5).to_bytes(6, 'big')
    for index, part in enumerate(subs):
        data += part.to_bytes(4, 'big' if index == len(subs) - 1 else 'little')
    return binascii.hexlify(data)


def filetime_of(when):
    return int((when - utc(1601, 1, 1)).total_seconds()) * 10_000_000


def dstime_of(when):
    return int((when - utc(1601, 1, 1)).total_seconds())


class ValueTest(unittest.TestCase):
    def test_the_rid_is_read_big_endian_and_the_domain_little_endian(self):
        self.assertEqual(ntds.sid(stored_sid(*DOMAIN, 1104)), 'S-1-5-21-1111111111-2222222222-3333333333-1104')
        self.assertEqual(ntds.sid(stored_sid(32, 544)), 'S-1-5-32-544')

    def test_a_value_that_is_not_a_sid_is_blank(self):
        self.assertEqual(ntds.sid(None), '')
        self.assertEqual(ntds.sid(b'zz'), '')
        self.assertEqual(ntds.sid(binascii.hexlify(b'\x01\x05' + b'\x00' * 6)), '')   # counts 5, holds none
        self.assertEqual(ntds.sid(binascii.hexlify(b'\x02\x00' + b'\x00' * 6)), '')   # revision 2

    def test_filetime_and_dstime_count_from_1601_in_utc(self):
        when = utc(2024, 2, 9, 21, 1, 54)
        self.assertEqual(ntds.filetime(filetime_of(when) + 1234567), when + datetime.timedelta(microseconds=123456))
        self.assertEqual(ntds.dstime(dstime_of(when)), when)
        self.assertEqual((ntds.filetime(0), ntds.filetime(None), ntds.dstime(0), ntds.dstime('x')), ('', '', '', ''))
        self.assertEqual(ntds.filetime(2 ** 63 - 1), '')

    def test_both_never_expires_values_leave_account_expires_blank(self):
        self.assertEqual(ntds.account_expires(0), '')
        self.assertEqual(ntds.account_expires(0x7FFFFFFFFFFFFFFF), '')
        self.assertEqual(ntds.account_expires(filetime_of(utc(2030, 1, 1))), utc(2030, 1, 1))

    def test_flags_name_every_documented_bit_and_list_the_rest(self):
        self.assertEqual(ntds.flags(0x00010222, ntds._UAC_FLAGS),  # pylint: disable=protected-access
                         '0x00010222 (ADS_UF_ACCOUNT_DISABLE, ADS_UF_PASSWD_NOTREQD, ADS_UF_NORMAL_ACCOUNT, '
                         'ADS_UF_DONT_EXPIRE_PASSWD)')
        self.assertEqual(ntds.flags(0x00400201, ntds._UAC_FLAGS),  # pylint: disable=protected-access
                         '0x00400201 (ADS_UF_NORMAL_ACCOUNT, ADS_UF_DONT_REQUIRE_PREAUTH, unnamed bits 0x1)')
        self.assertEqual(ntds.flags(-2147483643, ntds._GROUP_FLAGS),  # pylint: disable=protected-access
                         '0x80000005 (GROUP_TYPE_BUILTIN_LOCAL_GROUP, GROUP_TYPE_RESOURCE_GROUP, '
                         'GROUP_TYPE_SECURITY_ENABLED)')
        self.assertEqual(ntds.flags(None, ntds._GROUP_FLAGS), '')  # pylint: disable=protected-access
        self.assertEqual(ntds.flags(0, ntds._GROUP_FLAGS), '0x00000000')  # pylint: disable=protected-access

    def test_account_types_are_named_from_the_samr_table_or_kept(self):
        self.assertEqual(ntds.account_type(0x30000001), '0x30000001 (SAM_MACHINE_ACCOUNT)')
        self.assertEqual(ntds.account_type(0x30000009), '0x30000009')
        self.assertEqual(ntds.account_type(None), '')

    def test_the_attribute_ids_used_to_read_the_schema(self):
        self.assertEqual((ntds._ATTRIBUTE_ID, ntds._LDAP_DISPLAY_NAME), (131102, 131532))  # pylint: disable=protected-access


# Column names as ntds.dit spells them; ATTRTYPs as the schema below gives them.
SCHEMA = {'sAMAccountName': 590045, 'objectSid': 589970, 'sAMAccountType': 590126, 'userAccountControl': 589832,
          'whenCreated': 131074, 'whenChanged': 131075, 'lastLogon': 589876, 'lastLogonTimestamp': 591520,
          'pwdLastSet': 589920, 'badPasswordTime': 589873, 'badPwdCount': 589836, 'logonCount': 589993,
          'accountExpires': 589983, 'primaryGroupID': 589922, 'userPrincipalName': 590480, 'displayName': 131085,
          'description': 13, 'groupType': 590574, 'isDeleted': 131120, 'isRecycled': 591882,
          'lastKnownParent': 590605, 'name': 589825, 'linkID': 131122,
          'member': 31, 'lDAPDisplayName': 131532, 'attributeID': 131102}
LETTERS = {'sAMAccountName': 'm', 'objectSid': 'r', 'whenCreated': 'l', 'whenChanged': 'l', 'description': 'm',
           'userPrincipalName': 'm', 'displayName': 'm', 'name': 'm', 'lDAPDisplayName': 'm', 'attributeID': 'c',
           'isDeleted': 'i', 'isRecycled': 'i', 'lastKnownParent': 'b', 'member': 'b'}
COLUMNS = {name: f'ATT{LETTERS.get(name, "q" if "Time" in name or name in ("lastLogon", "lastLogonTimestamp", "pwdLastSet", "accountExpires") else "j")}{ident}'.encode()
           for name, ident in SCHEMA.items()}


def schema_records():
    records = []
    for name, ident in SCHEMA.items():
        record = {b'DNT_col': 1000 + ident % 997, COLUMNS['lDAPDisplayName']: name, COLUMNS['attributeID']: ident}
        if name == 'member':
            record[COLUMNS['linkID']] = 2
        records.append(record)
    return records


def obj(dnt, **values):
    record = {b'DNT_col': dnt}
    for name, value in values.items():
        record[COLUMNS[name]] = value
    return record


CREATED = utc(2020, 9, 17, 18, 0, 0)
ADMIN = obj(10, sAMAccountName='admin1', objectSid=stored_sid(*DOMAIN, 500), sAMAccountType=0x30000000,
            userAccountControl=0x10200, whenCreated=dstime_of(CREATED), whenChanged=dstime_of(CREATED) + 60,
            lastLogon=filetime_of(utc(2020, 9, 19, 1, 0, 0)), pwdLastSet=filetime_of(CREATED), badPwdCount=0,
            logonCount=7, accountExpires=0, primaryGroupID=513, description='made-up account', name='admin1')
HOST = obj(11, sAMAccountName='HOST1$', objectSid=stored_sid(*DOMAIN, 1104), sAMAccountType=0x30000001,
           userAccountControl=0x1000, whenCreated=dstime_of(CREATED) + 5, whenChanged=dstime_of(CREATED) + 5,
           primaryGroupID=515, accountExpires=0x7FFFFFFFFFFFFFFF, name='HOST1')
USERS = obj(20, sAMAccountName='Domain Users', objectSid=stored_sid(*DOMAIN, 513), sAMAccountType=0x10000000,
            groupType=-2147483646, whenCreated=dstime_of(CREATED), whenChanged=dstime_of(CREATED), name='Domain Users')
ADMINS = obj(21, sAMAccountName='Administrators', objectSid=stored_sid(32, 544), sAMAccountType=0x20000000,
             groupType=-2147483643, whenCreated=dstime_of(CREATED), whenChanged=dstime_of(CREATED),
             description='made-up group', name='Administrators')
CONTAINER = obj(30, name='Users')                      # no sAMAccountType: not reported
FOREIGN = obj(31, name='S-1-5-11')                     # a member without a SAM name
# A deleted account as the tested databases hold one: no sAMAccountType, still a SAM name, SID and flags.
GONE = obj(12, sAMAccountName='olduser', objectSid=stored_sid(*DOMAIN, 1107), userAccountControl=0x200,
           whenCreated=dstime_of(CREATED), whenChanged=dstime_of(CREATED) + 3600, isDeleted=1, isRecycled=1,
           lastKnownParent=30, name='olduser\nDEL:made-up')
GONE_GROUP = obj(22, sAMAccountName='oldgroup', objectSid=stored_sid(*DOMAIN, 1108), groupType=-2147483646,
                 whenCreated=dstime_of(CREATED), whenChanged=dstime_of(CREATED), isDeleted=1, name='oldgroup')
UNKNOWN_GONE = obj(13, objectSid=stored_sid(*DOMAIN, 1109), isDeleted=1, name='x')    # neither: not reported
DELETED_NO_SID = obj(14, sAMAccountName='nosid', isDeleted=1, userAccountControl=0x200)  # no SID: not kept
FILLER = 0x2A2A2A2A2A2A2A2A          # the value the tested databases hold on every current link
REMOVED = utc(2020, 9, 19, 2, 0, 0)
LINKS = [{b'link_DNT': 21, b'backlink_DNT': 10, b'link_base': 1, b'link_deltime': FILLER},
         {b'link_DNT': 21, b'backlink_DNT': 31, b'link_base': 1},
         {b'link_DNT': 21, b'backlink_DNT': 11, b'link_base': 47},   # another linked attribute
         # a member link with a deletion time: HOST1$ removed from Administrators
         {b'link_DNT': 21, b'backlink_DNT': 11, b'link_base': 1, b'link_deltime': dstime_of(REMOVED)}]


class _Walk:
    """Stands in for ese_rows.TableRows over made-up records."""

    tables = {}

    def __init__(self, _database, table_name, long_value_columns=None):
        self.table_name = table_name
        self.long_value_columns = long_value_columns
        self.found = table_name in self.tables

    def __iter__(self):
        return iter(self.tables.get(self.table_name, []))

    @staticmethod
    def summary():
        return ''


class _Database:
    def __init__(self, path, data=None):
        self.path, self.data = path, data
        self.closed = False

    def mountDB(self):  # pylint: disable=invalid-name
        pass

    @staticmethod
    def openTable(_name):  # pylint: disable=invalid-name
        return {'TableData': {'Columns': {column: {} for column in COLUMNS.values()} | {b'DNT_col': {}}}}

    def close(self):
        self.closed = True


class DirectoryTest(unittest.TestCase):
    def setUp(self):
        _Walk.tables = {'datatable': schema_records() + [ADMIN, HOST, USERS, ADMINS, CONTAINER, FOREIGN, GONE,
                                                         GONE_GROUP, UNKNOWN_GONE, DELETED_NO_SID],
                        'link_table': LINKS}
        mock.patch.object(ntds.ese_rows, 'TableRows', _Walk).start()
        mock.patch.object(ntds.ese_rows, 'ESEDatabase', _Database).start()
        self.addCleanup(mock.patch.stopall)

    def test_only_objects_with_an_account_type_are_kept_and_member_links_read(self):
        directory = ntds.read_directory('/case/data/ntds.dit')
        self.assertEqual(sorted(directory.objects), [10, 11, 12, 13, 20, 21, 22])
        self.assertEqual({dnt: ntds.kind(item) for dnt, item in directory.objects.items()},
                         {10: 'account', 11: 'account', 12: 'account', 13: '', 20: 'group', 21: 'group',
                          22: 'group'})
        self.assertEqual(directory.members, {21: [10, 31]})
        self.assertEqual(directory.member_of, {10: [21], 31: [21]})
        self.assertEqual(directory.removed_members, {21: [(11, REMOVED)]})
        self.assertEqual(directory.removed_from, {11: [(21, REMOVED)]})
        self.assertEqual(directory.notes, [])

    def test_an_account_row(self):
        directory = ntds.read_directory('/case/data/ntds.dit')
        self.assertEqual(ntds.account_row(directory, 10, 'clean shutdown'), (
            CREATED, CREATED + datetime.timedelta(seconds=60), utc(2020, 9, 19, 1, 0, 0), '', CREATED, '', '',
            'admin1', '0x30000000 (SAM_USER_OBJECT)', 'S-1-5-21-1111111111-2222222222-3333333333-500',
            '0x00010200 (ADS_UF_NORMAL_ACCOUNT, ADS_UF_DONT_EXPIRE_PASSWD)', 'Domain Users (513)', 'Administrators',
            '', 0, 7, '', '', 'made-up account', '', '', '', 'clean shutdown'))

    def test_a_removed_membership_is_not_current_and_carries_its_deletion_time(self):
        directory = ntds.read_directory('/case/data/ntds.dit')
        row = ntds.account_row(directory, 11, 'clean shutdown')
        self.assertEqual(row[12:14], ('', 'Administrators (2020-09-19 02:00:00 UTC)'))

    def test_a_deleted_account_row(self):
        directory = ntds.read_directory('/case/data/ntds.dit')
        row = ntds.account_row(directory, 12, 'clean shutdown')
        self.assertEqual((row[0], row[1], row[7], row[8], row[9], row[10], row[19:]), (
            CREATED, CREATED + datetime.timedelta(hours=1), 'olduser', '',
            'S-1-5-21-1111111111-2222222222-3333333333-1107', '0x00000200 (ADS_UF_NORMAL_ACCOUNT)',
            ('TRUE', 'TRUE', 'Users', 'clean shutdown')))

    def test_a_primary_group_the_database_does_not_hold_is_the_rid(self):
        directory = ntds.read_directory('/case/data/ntds.dit')
        row = ntds.account_row(directory, 11, 'dirty shutdown, read as stored')
        self.assertEqual((row[6], row[11], row[12], row[14], row[15]), ('', '515', '', '', ''))

    def test_a_group_row_names_members_by_sam_name_or_object_name(self):
        directory = ntds.read_directory('/case/data/ntds.dit')
        self.assertEqual(ntds.group_row(directory, 21, 'clean shutdown'), (
            CREATED, CREATED, 'Administrators', '0x20000000 (SAM_ALIAS_OBJECT)', 'S-1-5-32-544',
            '0x80000005 (GROUP_TYPE_BUILTIN_LOCAL_GROUP, GROUP_TYPE_RESOURCE_GROUP, GROUP_TYPE_SECURITY_ENABLED)',
            'made-up group', 'admin1, S-1-5-11', 2, 'HOST1$ (2020-09-19 02:00:00 UTC)', '', '', '',
            'clean shutdown'))
        self.assertEqual(ntds.group_row(directory, 20, 'clean shutdown')[7:10], ('', 0, ''))

    def test_no_secret_column_is_asked_for(self):
        asked = []

        class Recording(_Walk):
            def __init__(self, database, table_name, long_value_columns=None):
                super().__init__(database, table_name, long_value_columns)
                asked.append(long_value_columns)

        with mock.patch.object(ntds.ese_rows, 'TableRows', Recording):
            directory = ntds.read_directory('/case/data/ntds.dit')
        self.assertEqual(set(directory.columns), set(ntds._ATTRIBUTES))  # pylint: disable=protected-access
        for secret in ('unicodePwd', 'dBCSPwd', 'ntPwdHistory', 'lmPwdHistory', 'supplementalCredentials',
                       'pekList'):
            self.assertNotIn(secret, ntds._ATTRIBUTES)  # pylint: disable=protected-access
        self.assertEqual(asked[0], set())
        self.assertEqual(asked[1], set(directory.columns.values()))

    def test_a_missing_attribute_is_logged_and_the_rest_still_read(self):
        _Walk.tables['datatable'] = [r for r in schema_records() if r[COLUMNS['lDAPDisplayName']] != 'displayName'] \
            + [ADMIN]
        directory = ntds.read_directory('/case/data/ntds.dit')
        self.assertIn('no datatable column was found for displayName', directory.notes)
        self.assertEqual(ntds.account_row(directory, 10, '')[17], '')

    def test_without_a_member_link_id_no_membership_is_read(self):
        _Walk.tables['datatable'] = [r for r in schema_records() if r[COLUMNS['lDAPDisplayName']] != 'linkID'] + [ADMIN]
        directory = ntds.read_directory('/case/data/ntds.dit')
        self.assertEqual(directory.members, {})
        self.assertIn('the schema gives no linkID for member; no membership was read', directory.notes)


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'NTDS', 'ntds.dit')
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, 'wb') as handle:
            handle.write(b'\x00' * 64)
        _Walk.tables = {'datatable': schema_records() + [ADMIN, HOST, USERS, ADMINS], 'link_table': LINKS}
        mock.patch.object(ntds.ese_rows, 'TableRows', _Walk).start()
        mock.patch.object(ntds.ese_rows, 'ESEDatabase', _Database).start()
        self.log = mock.patch.object(ntds, 'logfunc').start()
        self.addCleanup(mock.patch.stopall)
        self.addCleanup(ntds._READ.clear)  # pylint: disable=protected-access
        ntds._READ.clear()  # pylint: disable=protected-access

    def test_accounts_and_groups_split_by_account_type_and_carry_the_state(self):
        with mock.patch.object(ntds.ese_recovery, 'replayed_database',
                               return_value=(None, 'not replayed: a page size of 8192')), \
                mock.patch.object(ntds, '_header_state', return_value='dirty shutdown'):
            headers, accounts, source = ntds.ntdsAccounts.__wrapped__(_Context([self.path]))
            _headers, groups, _source = ntds.ntdsGroups.__wrapped__(_Context([self.path]))
        self.assertEqual([row[7] for row in accounts], ['admin1', 'HOST1$'])
        self.assertEqual(len(_headers), len(groups[0]))
        self.assertEqual([row[2] for row in groups], ['Administrators', 'Domain Users'])
        self.assertEqual({row[-1] for row in accounts + groups}, {'dirty shutdown, read as stored'})
        self.assertEqual(len(headers), len(accounts[0]))
        self.assertEqual(source, self.path)
        self.log.assert_any_call('Active Directory Accounts: vol1/Windows/NTDS/ntds.dit, not replayed: a page '
                                     'size of 8192; read as stored')

    def test_a_replayed_database_is_read_from_the_replayed_bytes(self):
        opened = []

        class Recording(_Database):
            def __init__(self, path, data=None):
                super().__init__(path, data)
                opened.append(data)

        with mock.patch.object(ntds.ese_recovery, 'replayed_database',
                               return_value=(b'replayed', 'replayed 3 change(s) from edb.log onto 2 page(s)')), \
                mock.patch.object(ntds, '_header_state', return_value='dirty shutdown'), \
                mock.patch.object(ntds.ese_rows, 'ESEDatabase', Recording):
            _headers, accounts, _source = ntds.ntdsAccounts.__wrapped__(_Context([self.path]))
        self.assertEqual(opened, [b'replayed'])
        self.assertEqual(accounts[0][-1], 'dirty shutdown, logs replayed')

    def test_a_database_that_cannot_be_read_is_logged_and_skipped(self):
        with mock.patch.object(ntds, 'read_directory', side_effect=ValueError('bad page')), \
                mock.patch.object(ntds.ese_recovery, 'replayed_database', return_value=(None, 'not replayed: x')):
            _headers, accounts, source = ntds.ntdsAccounts.__wrapped__(_Context([self.path]))
        self.assertEqual((accounts, source), ([], ''))
        self.log.assert_any_call('Active Directory Accounts: could not read vol1/Windows/NTDS/ntds.dit: '
                                     'ValueError: bad page')

    def test_header_state_reads_the_header(self):
        header = bytearray(4096)
        struct.pack_into('<I', header, 4, 0x89ABCDEF)
        struct.pack_into('<I', header, 52, 3)
        struct.pack_into('<I', header, 236, 4096)
        struct.pack_into('<I', header, 0, ntds.ese_recovery.ese_log.checksum_old(bytes(header)))
        with open(self.path, 'wb') as handle:
            handle.write(bytes(header))
        self.assertEqual(ntds._header_state(self.path), 'clean shutdown')  # pylint: disable=protected-access
        with open(self.path, 'wb') as handle:
            handle.write(b'\x00' * 10)
        self.assertEqual(ntds._header_state(self.path), '')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
