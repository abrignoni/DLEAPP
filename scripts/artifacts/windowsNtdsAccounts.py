"""The accounts and groups of an Active Directory database (ntds.dit), for DLEAPP.

Author: @AlexisBrignoni, Claude.

ntds.dit is an ESE database and is read with scripts/ese_rows over the vendored ESE reader. Its
datatable holds one record per directory object, with one column per attribute named ATT, a letter
and the attribute's ATTRTYP in decimal (as impacket's secretsdump names them). The ATTRTYP of each
attribute read here is taken from the database's own schema: the attributeSchema record whose
lDAPDisplayName is the attribute's name gives it in attributeID. Those two columns are found by
the ATTRTYPs [MS-DRSR] 5.16.4 MakeAttid gives their OIDs with the default prefix table. Password
hashes and the other secret attributes are never read into a row.

Group membership is read from link_table: a row links a group (link_DNT) to a member
(backlink_DNT) for the member attribute when link_base is half the attribute's linkID. That
layout is not in Microsoft's documentation; the notes give what the data shows.
"""

import binascii
import os
from datetime import datetime, timedelta, timezone

from scripts import ese_recovery, ese_rows
from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL_ACCOUNTS = 'Active Directory Accounts'
_LABEL_GROUPS = 'Active Directory Groups'
_FILE = 'ntds.dit'

# [MS-DRSR] 5.16.4: MakeAttid(OID) = prefixIndex * 65536 + last arc (below 16384), and NewPrefixTable
# gives 1.2.840.113556.1.2 the prefix index 2. attributeID is 1.2.840.113556.1.2.30 and
# lDAPDisplayName 1.2.840.113556.1.2.460 (Microsoft's AD schema pages).
_ATTRIBUTE_ID = 2 * 65536 + 30          # 131102
_LDAP_DISPLAY_NAME = 2 * 65536 + 460    # 131532
_LINK_ID_NAME = 'linkID'

_ATTRIBUTES = ('sAMAccountName', 'objectSid', 'sAMAccountType', 'userAccountControl', 'whenCreated',
               'whenChanged', 'lastLogon', 'lastLogonTimestamp', 'pwdLastSet', 'badPasswordTime',
               'badPwdCount', 'logonCount', 'accountExpires', 'primaryGroupID', 'userPrincipalName',
               'displayName', 'description', 'groupType', 'isDeleted', 'isRecycled', 'lastKnownParent',
               'name')

# [MS-SAMR] 2.2.1.9 ACCOUNT_TYPE Values.
_ACCOUNT_TYPES = {
    0x00000000: 'SAM_DOMAIN_OBJECT', 0x10000000: 'SAM_GROUP_OBJECT',
    0x10000001: 'SAM_NON_SECURITY_GROUP_OBJECT', 0x20000000: 'SAM_ALIAS_OBJECT',
    0x20000001: 'SAM_NON_SECURITY_ALIAS_OBJECT', 0x30000000: 'SAM_USER_OBJECT',
    0x30000001: 'SAM_MACHINE_ACCOUNT', 0x30000002: 'SAM_TRUST_ACCOUNT',
    0x40000000: 'SAM_APP_BASIC_GROUP', 0x40000001: 'SAM_APP_QUERY_GROUP',
}
_ACCOUNT_KINDS = {0x30000000, 0x30000001, 0x30000002}
_GROUP_KINDS = {0x10000000, 0x10000001, 0x20000000, 0x20000001, 0x40000000, 0x40000001}

# [MS-ADTS] 2.2.16 userAccountControl Bits.
_UAC_FLAGS = (
    (0x00000002, 'ADS_UF_ACCOUNT_DISABLE'), (0x00000008, 'ADS_UF_HOMEDIR_REQUIRED'),
    (0x00000010, 'ADS_UF_LOCKOUT'), (0x00000020, 'ADS_UF_PASSWD_NOTREQD'),
    (0x00000040, 'ADS_UF_PASSWD_CANT_CHANGE'), (0x00000080, 'ADS_UF_ENCRYPTED_TEXT_PASSWORD_ALLOWED'),
    (0x00000200, 'ADS_UF_NORMAL_ACCOUNT'), (0x00000800, 'ADS_UF_INTERDOMAIN_TRUST_ACCOUNT'),
    (0x00001000, 'ADS_UF_WORKSTATION_TRUST_ACCOUNT'), (0x00002000, 'ADS_UF_SERVER_TRUST_ACCOUNT'),
    (0x00010000, 'ADS_UF_DONT_EXPIRE_PASSWD'), (0x00040000, 'ADS_UF_SMARTCARD_REQUIRED'),
    (0x00080000, 'ADS_UF_TRUSTED_FOR_DELEGATION'), (0x00100000, 'ADS_UF_NOT_DELEGATED'),
    (0x00200000, 'ADS_UF_USE_DES_KEY_ONLY'), (0x00400000, 'ADS_UF_DONT_REQUIRE_PREAUTH'),
    (0x00800000, 'ADS_UF_PASSWORD_EXPIRED'), (0x01000000, 'ADS_UF_TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION'),
    (0x02000000, 'ADS_UF_NO_AUTH_DATA_REQUIRED'), (0x04000000, 'ADS_UF_PARTIAL_SECRETS_ACCOUNT'),
)

# [MS-ADTS] 2.2.12 Group Type Flags.
_GROUP_FLAGS = (
    (0x00000001, 'GROUP_TYPE_BUILTIN_LOCAL_GROUP'), (0x00000002, 'GROUP_TYPE_ACCOUNT_GROUP'),
    (0x00000004, 'GROUP_TYPE_RESOURCE_GROUP'), (0x00000008, 'GROUP_TYPE_UNIVERSAL_GROUP'),
    (0x00000010, 'GROUP_TYPE_APP_BASIC_GROUP'), (0x00000020, 'GROUP_TYPE_APP_QUERY_GROUP'),
    (0x80000000, 'GROUP_TYPE_SECURITY_ENABLED'),
)

# accountExpires values Microsoft's schema page says mean the account never expires.
_NEVER = (0, 0x7FFFFFFFFFFFFFFF)
_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)

__artifacts_v2__ = {
    "ntdsAccounts": {
        "name": "Active Directory Accounts",
        "description": "User, computer and trust accounts in an Active Directory database (ntds.dit): account "
                       "name, SID, account control flags, the groups that list them, and the creation, change, "
                       "logon, password set and bad password times the directory holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Reads the datatable and link_table tables of Windows/NTDS/ntds.dit, the Active Directory database a '
                 'domain controller keeps, an ESE database read with scripts/ese_rows over the vendored ESE reader. One '
                 'row per datatable record whose sAMAccountType is a user, computer or trust account (SAM_USER_OBJECT, '
                 "SAM_MACHINE_ACCOUNT, SAM_TRUST_ACCOUNT in Microsoft's [MS-SAMR] 2.2.1.9 ACCOUNT_TYPE Values, "
                 'https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-samr/e742be45-665d-4576-b872-0bc99d1e1fbe), '
                 'plus each deleted record (isDeleted set) that still holds an objectSid and a userAccountControl. Account '
                 "Type is the stored sAMAccountType with that table's name, and is blank on a deleted record: on the two "
                 'tested databases that hold deleted accounts, every one of them (9 on szechuan_dc01_server2012r2, 1,000 '
                 'on ou_ransomware_server2022) keeps sAMAccountName, objectSid, userAccountControl, whenCreated, '
                 'whenChanged, isRecycled and lastKnownParent and holds no sAMAccountType, so those rows show the account '
                 "as the database still has it. The datatable names its columns ATT, a letter and the attribute's ATTRTYP "
                 "in decimal, as impacket's secretsdump names them "
                 '(https://github.com/fortra/impacket/blob/c456746d7a0f0bb25e8968a59f25aae1ad519935/impacket/examples/secretsdump.py#L2496-L2519). '
                 "Each attribute's ATTRTYP is read from the database's own schema: the record whose lDAPDisplayName is the "
                 "attribute's name gives it in attributeID, and those two columns are found by the ATTRTYPs 131102 and "
                 "131532 that MakeAttid in Microsoft's [MS-DRSR] 5.16.4 ATTRTYP-to-OID Conversion gives their OIDs, "
                 '1.2.840.113556.1.2.30 and 1.2.840.113556.1.2.460, with the default prefix table '
                 '(https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-drsr/6f53317f-2263-48ee-86c1-4580bf97232c; '
                 "OIDs from Microsoft's schema pages, "
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-attributeid and '
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-ldapdisplayname). All 22 attributes this '
                 'module reads resolved to a column that way on each of the three tested databases. Password hashes, '
                 'password history and the other secret attributes are not put in any row. Created (UTC) and Changed (UTC) '
                 'are whenCreated and whenChanged, which the datatable stores as a whole number of seconds and are read as '
                 'a DSTIME, seconds since 1 January 1601 ([MS-DRSR] 5.51 DSTIME, '
                 'https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-drsr/a72a16b9-73e4-41ca-a5c1-afc5fc54e175). '
                 'No Microsoft source says the datatable stores them that way; the data does: Password Last Set (UTC) lies '
                 'within 60 seconds of Created (UTC) on 521 of the 532 live accounts with both (10 of 12, 502 of 510 and 9 '
                 'of 10 on alihadi_threatsim_server2019, ou_ransomware_server2022 and szechuan_dc01_server2012r2), and on '
                 'the first and the third it is earlier for the account with RID 500, by 3,378 and 4,325 seconds. Last '
                 'Logon (UTC), Last Logon Timestamp (UTC), Password Last Set (UTC), Bad Password Time (UTC) and Account '
                 'Expires (UTC) are lastLogon, lastLogonTimestamp, pwdLastSet, badPasswordTime and accountExpires, counts '
                 "of 100 nanosecond intervals since 1 January 1601 UTC as Microsoft's schema pages describe them "
                 '(https://learn.microsoft.com/en-us/windows/win32/adschema/a-lastlogon, '
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-lastlogontimestamp, '
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-pwdlastset, '
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-badpasswordtime, '
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-accountexpires). A stored zero is left blank; '
                 'the lastLogon and badPasswordTime pages say zero means the time is unknown, and the pwdLastSet page says '
                 'zero, without the ADS_UF_DONT_EXPIRE_PASSWD flag, means the password must be set at the next logon (one '
                 'account per database stores pwdLastSet 0). Account Expires (UTC) is also blank for 0x7FFFFFFFFFFFFFFF, '
                 'which that page says, like 0, means the account never expires; it was blank on every tested row (12 '
                 'accounts store 0x7FFFFFFFFFFFFFFF and 1 stores 0 on alihadi_threatsim_server2019, 511 and 0 on '
                 'ou_ransomware_server2022, 10 and 1 on szechuan_dc01_server2012r2, and the deleted accounts store none). '
                 "Of the accounts with a Last Logon (UTC) that the server's own Security log names in a Kerberos or NTLM "
                 'record (4768, 4769 or 4776), Last Logon (UTC) is within 2 seconds of such a record for that account on '
                 '33 of 39 on ou_ransomware_server2022 and 4 of 5 on szechuan_dc01_server2012r2, reading the dirty log of '
                 'the second past the chunks its header counts (two of the four matches lie there). SAM Account Name is '
                 'sAMAccountName. SID is objectSid, stored with the domain sub-authorities little-endian and the last one, '
                 'the RID, big-endian (impacket reads it so, '
                 'https://github.com/fortra/impacket/blob/c456746d7a0f0bb25e8968a59f25aae1ad519935/impacket/examples/secretsdump.py#L2670-L2681): '
                 'read that way, of the 46 pairs of account name and domain SID that the Security logs of '
                 'ou_ransomware_server2022 and szechuan_dc01_server2012r2 name in 4768, 4769, 4770 and 4771 records '
                 '(TargetSid with TargetUserName, ServiceSid with ServiceName; names compared without the realm and '
                 'without case, the dirty log read past the chunks its header counts), 45 name an account this artifact '
                 'reports under that name with the same SID, and the other 1, on szechuan_dc01_server2012r2, carries the '
                 'SID of an account the database holds under another name. User Account Control is userAccountControl in '
                 "hexadecimal with the names of the flags it sets from Microsoft's [MS-ADTS] 2.2.16 userAccountControl "
                 'Bits '
                 '(https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/dd302fd1-0aa7-406b-ad91-2a6b35738557); '
                 'a bit that table does not list is named as unnamed. It is the value the database stores; whether Windows '
                 'also computes lockout or password expiry for the account is not shown here. Primary Group is '
                 "primaryGroupID, the RID of the account's primary group "
                 '(https://learn.microsoft.com/en-us/windows/win32/adschema/a-primarygroupid), with the name of the group '
                 "whose SID is the account's domain SID and that RID, or the RID alone when the database holds no such "
                 'group. Member Of lists the groups the database links the account to through the member attribute with no '
                 'deletion time on the link, and Removed From the groups whose link to the account carries one, each with '
                 'that time (see Active Directory Groups for how those links are read); the primary group is not listed '
                 'there, groups inside groups are not followed, and no deleted account had a link. Removed From was filled '
                 'on 1 row, of ou_ransomware_server2022, and blank on every row of the other two databases. Bad Password '
                 'Count and Logon Count are badPwdCount and logonCount as stored; Bad Password Count held 0 on every row '
                 'of alihadi_threatsim_server2019 and on every live row of szechuan_dc01_server2012r2, and the deleted '
                 'rows hold none. User Principal Name, Display Name and Description are userPrincipalName, displayName and '
                 'description; Display Name was blank on every row of alihadi_threatsim_server2019. Is Deleted and Is '
                 'Recycled are isDeleted and isRecycled, TRUE when set, FALSE when stored as not set, and blank when the '
                 'record does not hold them (https://learn.microsoft.com/en-us/windows/win32/adschema/a-isdeleted, '
                 'https://learn.microsoft.com/en-us/windows/win32/adschema/a-isrecycled). They are two attributes: the '
                 'first page describes an object marked for deletion and the second a recycled object, for use with AD '
                 'Recycle Bin. Is Deleted and Is Recycled were identical on every tested row: both TRUE on every deleted '
                 'row and blank on every other row, and both blank on every row of alihadi_threatsim_server2019, which '
                 'holds no deleted account. Last Known Parent is the name of the object lastKnownParent points to '
                 '(https://learn.microsoft.com/en-us/windows/win32/adschema/a-lastknownparent), its relative name only, '
                 'not its full distinguished name. Last Known Parent was blank on every live row and on every row of '
                 'alihadi_threatsim_server2019. Bad Password Time (UTC) was blank on every row of '
                 'alihadi_threatsim_server2019. Database State is the state the database header records '
                 '(JET_dbstateDirtyShutdown 2, JET_dbstateCleanShutdown 3, '
                 'https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/published/inc/jethdr.w#L5406-L5408) '
                 'and how it was read, the same on every row of one database. The database is read as stored: a database '
                 'whose header records a dirty shutdown would first have its transaction logs replayed in memory by '
                 'scripts/ese_recovery, but that replay is checked only on 4 KiB pages and refuses the 8 KiB pages of '
                 'every tested ntds.dit, so the run log says the database was not replayed, and the edb*.log files beside '
                 'it are not collected. Changes still only in those logs are therefore not shown. '
                 'szechuan_dc01_server2012r2 and ou_ransomware_server2022 record a dirty shutdown and '
                 'alihadi_threatsim_server2019 a clean one. Only ntds.dit under Windows/NTDS is read; a database moved '
                 "elsewhere by its domain controller's settings is not found, and any other copy of ntds.dit, for example "
                 'under System32 or WinSxS, is not read. Rows are ordered by Created (UTC), then SAM Account Name. The '
                 'other Windows keys hold no ntds.dit under Windows/NTDS and give no row.',
        "paths": ('*/Windows/NTDS/ntds.dit',),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 20 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 1511 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 13 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100) | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no member matches the declared paths)",
        },
    },
    "ntdsGroups": {
        "name": "Active Directory Groups",
        "description": "Groups in an Active Directory database (ntds.dit): group name, SID, group type, "
                       "description and the members the database links to each group.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Reads the same database the same way as Active Directory Accounts, whose notes give the attribute '
                 'reading, the SID reading, the time reading and the database state. One row per datatable record whose '
                 "sAMAccountType is a group or alias type in Microsoft's [MS-SAMR] 2.2.1.9 ACCOUNT_TYPE Values "
                 '(https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-samr/e742be45-665d-4576-b872-0bc99d1e1fbe), '
                 'plus each deleted record that still holds an objectSid and a groupType; no tested database holds a '
                 'deleted group. Group Type is groupType in hexadecimal with the names of the flags it sets from '
                 "Microsoft's [MS-ADTS] 2.2.12 Group Type Flags "
                 '(https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/11972272-09ec-4a42-bf5e-3e99b321cf55). '
                 'Members lists the objects the database links to the group through the member attribute with no deletion '
                 "time on the link, by sAMAccountName, or by the object's name when it has none, and Member Count is how "
                 'many such links there are. Removed Members lists the objects whose link to the group carries a deletion '
                 'time, each followed by that time in UTC. The links are read from link_table: a row links the group '
                 "(link_DNT, the group's DNT_col) to a member (backlink_DNT) for the attribute whose linkID is twice "
                 "link_base. member's linkID is 2 in Microsoft's schema "
                 "(https://learn.microsoft.com/en-us/windows/win32/adschema/a-member) and in each tested database's own "
                 'schema, so member links are the rows with link_base 1. No Microsoft documentation of that table layout '
                 'was found. The data supports it: on all three databases every link_base value in link_table is half the '
                 'linkID of an attribute in the schema, and the links give the built-in Administrators group '
                 '(S-1-5-32-544) the members Microsoft lists as its default members, the accounts or groups with RIDs 500, '
                 '512 and 519 (Administrator, Domain Admins, Enterprise Admins; '
                 'https://github.com/MicrosoftDocs/windowsserverdocs/blob/6e20f882e7400d3b423267a6a5e728ad16b2a7c0/WindowsServerDocs/identity/ad-ds/manage/understand-security-groups.md#L211-L214), '
                 'with one more member on szechuan_dc01_server2012r2 and on ou_ransomware_server2022. A link whose '
                 'link_deltime reads as a DSTIME (seconds since 1601, as whenCreated is read) is treated as a removed '
                 'membership with that deletion time. No Microsoft documentation of that column was found. Two published '
                 'readers of ntds.dit support the reading: ntdsxtract (Csaba Barta, GPL-3.0) reads link_deltime as a '
                 'DSTIME and lists a group member whose link has one as deleted at that time '
                 '(https://github.com/csababarta/ntdsxtract/blob/7fa1c8c28cbbf97a42bef40f20009dba85e4c25f/ntds/dslink.py#L84-L100, '
                 'https://github.com/csababarta/ntdsxtract/blob/7fa1c8c28cbbf97a42bef40f20009dba85e4c25f/dsgroups.py#L186-L213), '
                 'and DSInternals (Michael Grafnetter, MIT) reads members through the link_table index it describes as the '
                 'index of valid links '
                 '(https://github.com/MichaelGrafnetter/DSInternals/blob/f54c3c3075bb6c3637623f775c93ed3a339b5ec6/Src/DSInternals.DataStore/LinkResolver.cs#L15-L20, '
                 '#L76). No code from either is used. The data agrees: on the tested databases link_deltime holds the '
                 'value 0x2A2A2A2A2A2A2A2A, which is out of range for a DSTIME, on every member link except 4 on '
                 "ou_ransomware_server2022, from one account to four groups, and for each of those 4 the server's own "
                 'Security log holds a member removed record (4729 or 4757) naming the same member SID and group SID 0.4 '
                 "to 1.4 seconds after the link's deletion time (see Windows Account Management). link_deactivetime held "
                 'that same value on every member link and is not read; what a value there would mean is not established. '
                 'The tested databases hold 28, 25 and 25 member links (alihadi_threatsim_server2019, '
                 'ou_ransomware_server2022, szechuan_dc01_server2012r2), 28, 21 and 25 of them with no deletion time, and '
                 '5 on each database to objects without an sAMAccountName. Removed Members was filled on 4 rows of '
                 "ou_ransomware_server2022 and blank on every row of the other two databases. A member's own primary group "
                 'is not a link and is not counted here (see Primary Group in Active Directory Accounts). Is Deleted, Is '
                 'Recycled and Last Known Parent are read as in Active Directory Accounts and were blank on every tested '
                 'row; Is Deleted and Is Recycled were identical on every tested row. Database State held one value on '
                 'every row of each database. Rows are ordered by Created (UTC), then SAM Account Name.',
        "paths": ('*/Windows/NTDS/ntds.dit',),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 46 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 50 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 49 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100) | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no member matches the declared paths)",
        },
    },
}


def filetime(value):
    """An aware UTC datetime for a FILETIME count, or '' for none, zero or out of range."""
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _FILETIME_EPOCH + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def dstime(value):
    """An aware UTC datetime for a DSTIME (seconds since 1601-01-01), or '' for none or zero."""
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _FILETIME_EPOCH + timedelta(seconds=value)
    except OverflowError:
        return ''


def account_expires(value):
    """accountExpires as a time; '' when not stored or one of the two never-expires values."""
    if value in _NEVER:
        return ''
    return filetime(value)


def sid(value):
    """The SID the datatable stores as hex text, its RID read big-endian, or '' when not a SID.

    The domain sub-authorities are little-endian and the last (the RID) big-endian, the reading
    that matches the SIDs the Security event log of the same server records (see the notes)."""
    if not value:
        return ''
    try:
        data = binascii.unhexlify(value) if isinstance(value, (str, bytes)) else bytes(value)
    except (binascii.Error, TypeError, ValueError):
        return ''
    if len(data) < 8 or data[0] != 1 or len(data) != 8 + 4 * data[1]:
        return ''
    count = data[1]
    subs = []
    for index in range(count):
        piece = data[8 + 4 * index:12 + 4 * index]
        subs.append(int.from_bytes(piece, 'big' if index == count - 1 else 'little'))
    authority = int.from_bytes(data[2:8], 'big')
    return f'S-{data[0]}-{authority}' + ''.join(f'-{part}' for part in subs)


def flags(value, table):
    """'0x........ (names)' for a stored flag word; names from `table`, other bits listed."""
    if not isinstance(value, int):
        return ''
    number = value & 0xFFFFFFFF
    names = [name for bit, name in table if number & bit]
    rest = number & ~sum(bit for bit, _name in table)
    if rest:
        names.append(f'unnamed bits 0x{rest:X}')
    text = f'0x{number:08X}'
    return f'{text} ({", ".join(names)})' if names else text


def account_type(value):
    if not isinstance(value, int):
        return ''
    name = _ACCOUNT_TYPES.get(value)
    return f'0x{value:08X} ({name})' if name else f'0x{value:08X}'


def _text(value):
    if value is None:
        return ''
    if isinstance(value, (list, tuple)):
        return '; '.join(_text(item) for item in value if item is not None)
    return str(value).strip()


def _number(value):
    return value if isinstance(value, int) else ''


class Directory:
    """The SAM objects and member links of one ntds.dit, read once for both artifacts."""

    def __init__(self):
        self.objects = {}       # DNT -> {attribute name: value}
        self.members = {}       # group DNT -> [member DNT]
        self.member_of = {}     # member DNT -> [group DNT]
        self.removed_members = {}   # group DNT -> [(member DNT, deletion time)]
        self.removed_from = {}      # member DNT -> [(group DNT, deletion time)]
        self.names = {}         # DNT -> name, for every object, for members without a SAM name
        self.state = ''
        self.columns = {}
        self.notes = []


def _column_ids(cursor):
    """{ATTRTYP: column name} for the ATT* columns of datatable."""
    found = {}
    for name in cursor['TableData']['Columns']:
        text = name.decode('latin-1') if isinstance(name, (bytes, bytearray)) else name
        if text.startswith('ATT') and len(text) > 4 and text[4:].isdigit():
            found.setdefault(int(text[4:]), name)
    return found


def _schema(database, columns):
    """{lDAPDisplayName: ATTRTYP} from the attributeSchema records, and {name: linkID}."""
    names = columns.get(_LDAP_DISPLAY_NAME)
    ids = columns.get(_ATTRIBUTE_ID)
    if names is None or ids is None:
        return {}, {}
    walk = ese_rows.TableRows(database, 'datatable', long_value_columns=set())
    found = {}
    rows = []
    for record in walk:
        name, ident = record.get(names), record.get(ids)
        if isinstance(name, str) and isinstance(ident, int):
            found.setdefault(name, ident)
            rows.append(record)
    link_column = columns.get(found.get(_LINK_ID_NAME, -1))
    links = {}
    if link_column is not None:
        for record in rows:
            value = record.get(link_column)
            if isinstance(value, int):
                links[record.get(names)] = value
    return found, links


def read_directory(path, data=None):
    """Read the SAM objects and the member links of the ntds.dit at `path` (or `data`)."""
    directory = Directory()
    database = ese_rows.ESEDatabase(path, data=data) if data is not None else ese_rows.ESEDatabase(path)
    try:
        database.mountDB()
        cursor = database.openTable('datatable')
        if cursor is None:
            directory.notes.append('has no datatable table')
            return directory
        columns = _column_ids(cursor)
        schema, link_ids = _schema(database, columns)
        for attribute in _ATTRIBUTES:
            ident = schema.get(attribute)
            column = columns.get(ident) if ident is not None else None
            if column is None:
                directory.notes.append(f'no datatable column was found for {attribute}')
            else:
                directory.columns[attribute] = column
        wanted = set(directory.columns.values())
        walk = ese_rows.TableRows(database, 'datatable', long_value_columns=wanted)
        name_column = directory.columns.get('name')
        for record in walk:
            dnt = record.get(b'DNT_col', record.get('DNT_col'))
            if name_column is not None and record.get(name_column) is not None:
                directory.names[dnt] = _text(record.get(name_column))
            if not _principal(record, directory.columns):
                continue
            directory.objects[dnt] = {attribute: record.get(column)
                                      for attribute, column in directory.columns.items()}
        if walk.summary():
            directory.notes.append(f'datatable: {walk.summary()}')
        member_link = link_ids.get('member')
        if member_link is not None:
            _read_links(database, directory, member_link // 2)
        else:
            directory.notes.append('the schema gives no linkID for member; no membership was read')
    finally:
        database.close()
    return directory


def _principal(record, columns):
    """Whether a datatable record is a security principal this module reports: it holds an
    sAMAccountType, or it is deleted (isDeleted) and still holds an objectSid. On the tested
    databases a deleted account keeps sAMAccountName, objectSid and userAccountControl but
    not sAMAccountType (see the notes)."""
    type_column = columns.get('sAMAccountType')
    if type_column is not None and isinstance(record.get(type_column), int):
        return True
    deleted = columns.get('isDeleted')
    sid_column = columns.get('objectSid')
    return bool(deleted is not None and sid_column is not None and record.get(deleted)
                and record.get(sid_column))


def kind(item):
    """'account', 'group' or '' for an object: by sAMAccountType when it holds one, otherwise
    (a deleted object) by whether it holds userAccountControl or groupType."""
    value = item.get('sAMAccountType')
    if isinstance(value, int):
        if value in _ACCOUNT_KINDS:
            return 'account'
        return 'group' if value in _GROUP_KINDS else ''
    if isinstance(item.get('userAccountControl'), int):
        return 'account'
    return 'group' if isinstance(item.get('groupType'), int) else ''


def _read_links(database, directory, base):
    walk = ese_rows.TableRows(database, 'link_table', long_value_columns=set())
    for record in walk:
        if record.get(b'link_base', record.get('link_base')) != base:
            continue
        group = record.get(b'link_DNT', record.get('link_DNT'))
        member = record.get(b'backlink_DNT', record.get('backlink_DNT'))
        removed = dstime(record.get(b'link_deltime', record.get('link_deltime')))
        if removed:
            directory.removed_members.setdefault(group, []).append((member, removed))
            directory.removed_from.setdefault(member, []).append((group, removed))
            continue
        directory.members.setdefault(group, []).append(member)
        directory.member_of.setdefault(member, []).append(group)
    if not walk.found:
        directory.notes.append('has no link_table table; no membership was read')
    elif walk.summary():
        directory.notes.append(f'link_table: {walk.summary()}')


def _label(directory, dnt):
    item = directory.objects.get(dnt)
    if item is not None and _text(item.get('sAMAccountName')):
        return _text(item.get('sAMAccountName'))
    return directory.names.get(dnt, f'DNT {dnt}')


def _names(directory, dnts):
    return ', '.join(sorted({_label(directory, dnt) for dnt in dnts}, key=str.lower))


def _removed(directory, pairs):
    """'name (time UTC)' for each link with a deletion time, ordered by name."""
    shown = sorted({(_label(directory, dnt), when) for dnt, when in pairs},
                   key=lambda pair: (pair[0].lower(), pair[1]))
    return ', '.join(f'{name} ({when:%Y-%m-%d %H:%M:%S} UTC)' for name, when in shown)


def _primary_group(directory, item):
    """The group whose SID is the account's domain SID and its primaryGroupID, or the RID as stored."""
    rid = item.get('primaryGroupID')
    if not isinstance(rid, int):
        return ''
    own = sid(item.get('objectSid'))
    domain = own.rsplit('-', 1)[0] if own else ''
    for dnt, other in directory.objects.items():
        if domain and sid(other.get('objectSid')) == f'{domain}-{rid}':
            return f'{_label(directory, dnt)} ({rid})'
    return str(rid)


def _boolean(item, attribute):
    value = item.get(attribute)
    if value is None:
        return ''
    return 'TRUE' if value else 'FALSE'


def _parent(directory, item):
    dnt = item.get('lastKnownParent')
    return directory.names.get(dnt, f'DNT {dnt}') if isinstance(dnt, int) else ''


def account_row(directory, dnt, state):
    item = directory.objects[dnt]
    return (dstime(item.get('whenCreated')), dstime(item.get('whenChanged')),
            filetime(item.get('lastLogon')), filetime(item.get('lastLogonTimestamp')),
            filetime(item.get('pwdLastSet')), filetime(item.get('badPasswordTime')),
            account_expires(item.get('accountExpires')), _text(item.get('sAMAccountName')),
            account_type(item.get('sAMAccountType')), sid(item.get('objectSid')),
            flags(item.get('userAccountControl'), _UAC_FLAGS), _primary_group(directory, item),
            _names(directory, directory.member_of.get(dnt, [])),
            _removed(directory, directory.removed_from.get(dnt, [])), _number(item.get('badPwdCount')),
            _number(item.get('logonCount')), _text(item.get('userPrincipalName')),
            _text(item.get('displayName')), _text(item.get('description')), _boolean(item, 'isDeleted'),
            _boolean(item, 'isRecycled'), _parent(directory, item), state)


def group_row(directory, dnt, state):
    item = directory.objects[dnt]
    members = directory.members.get(dnt, [])
    return (dstime(item.get('whenCreated')), dstime(item.get('whenChanged')),
            _text(item.get('sAMAccountName')), account_type(item.get('sAMAccountType')),
            sid(item.get('objectSid')), flags(item.get('groupType'), _GROUP_FLAGS),
            _text(item.get('description')), _names(directory, members), len(members),
            _removed(directory, directory.removed_members.get(dnt, [])), _boolean(item, 'isDeleted'), _boolean(item, 'isRecycled'), _parent(directory, item), state)


# What each database read as, keyed by path, size and modification time, so the two artifacts
# read each staged ntds.dit once.
_READ = {}


def _directory(path, label, relative):
    stat = os.stat(path)
    key = (path, stat.st_size, stat.st_mtime_ns)
    if key not in _READ:
        try:
            data, summary = ese_recovery.replayed_database(path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            data, summary = None, f'not replayed: {type(exc).__name__}: {exc}'
        replayed = data is not None and summary.startswith('replayed')
        state = _header_state(path)
        directory = read_directory(path, data if replayed else None)
        directory.state = f'{state}, logs replayed' if replayed else (
            f'{state}, read as stored' if state else 'read as stored')
        _READ.clear()
        _READ[key] = (directory, summary, replayed)
    directory, summary, replayed = _READ[key]
    if replayed or 'clean shutdown' not in summary:
        logfunc(f'{label}: {relative}, {summary}' + ('' if replayed else '; read as stored'))
    for note in directory.notes:
        logfunc(f'{label}: {relative} {note}')
    return directory


def _header_state(path):
    try:
        with open(path, 'rb') as handle:
            header = ese_recovery.DatabaseHeader(handle.read(32768))
    except (OSError, ese_recovery.ReplayRefused):
        return ''
    return header.state_name


def _databases(context):
    return sorted(path for path in (str(f) for f in context.get_files_found())
                  if os.path.basename(path).lower() == _FILE and not os.path.isdir(path))


def _rows(context, label, wanted, make_row):
    data_list, sources = [], []
    for path in _databases(context):
        relative = context.get_relative_path(path)
        try:
            directory = _directory(path, label, relative)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {type(exc).__name__}: {exc}')
            continue
        sources.append(path)
        rows = [make_row(directory, dnt, directory.state) for dnt, item in directory.objects.items()
                if kind(item) == wanted]
        data_list.extend(sorted(rows, key=lambda row: (str(row[0]), row[2] if wanted == 'group' else row[7])))
    return data_list, sources


@artifact_processor
def ntdsAccounts(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Changed (UTC)', 'datetime'), ('Last Logon (UTC)', 'datetime'),
                    ('Last Logon Timestamp (UTC)', 'datetime'), ('Password Last Set (UTC)', 'datetime'),
                    ('Bad Password Time (UTC)', 'datetime'), ('Account Expires (UTC)', 'datetime'),
                    'SAM Account Name', 'Account Type', 'SID', 'User Account Control', 'Primary Group',
                    'Member Of', 'Removed From', 'Bad Password Count', 'Logon Count', 'User Principal Name', 'Display Name',
                    'Description', 'Is Deleted', 'Is Recycled', 'Last Known Parent', 'Database State')
    data_list, sources = _rows(context, _LABEL_ACCOUNTS, 'account', account_row)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ntdsGroups(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Changed (UTC)', 'datetime'), 'SAM Account Name',
                    'Account Type', 'SID', 'Group Type', 'Description', 'Members', 'Member Count', 'Removed Members',
                    'Is Deleted', 'Is Recycled', 'Last Known Parent', 'Database State')
    data_list, sources = _rows(context, _LABEL_GROUPS, 'group', group_row)
    return data_headers, data_list, '\n'.join(sources)
