"""Windows Kerberos, NTLM, network share and directory object access event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads eight Microsoft-Windows-Security-Auditing events of the Security event log:
4768, 4769, 4770 and 4771 (Kerberos ticket requests, renewals and pre-authentication
failures), 4776 (NTLM credential validation), 5140 and 5145 (network share access) and
4662 (an operation on a directory object). The four artifacts share one read of the log.

The codes these records store are given their names only from the tables Microsoft
publishes on each event's page, and only for the event whose page carries the table
(see the notes). A value no table names is reported as stored.
"""

import os
import re

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Domain Authentication Events'
_LOG = 'security.evtx'
_SECURITY = 'Microsoft-Windows-Security-Auditing'

# Each event's title, the heading of its page in Microsoft's audit documentation.
_KERBEROS = {
    '4768': 'A Kerberos authentication ticket (TGT) was requested.',
    '4769': 'A Kerberos service ticket was requested.',
    '4770': 'A Kerberos service ticket was renewed.',
    '4771': 'Kerberos pre-authentication failed.',
}
_NTLM = '4776'
_SHARES = {
    '5140': 'A network share object was accessed.',
    '5145': 'A network share object was checked to see whether client can be granted desired access.',
}
_DIRECTORY = '4662'
_EVENT_IDS = {*_KERBEROS, _NTLM, *_SHARES, _DIRECTORY}

# 'Table 2. Kerberos ticket flags', the same on the 4768, 4769, 4770 and 4771 pages. Bits are
# numbered from the most significant (MSB 0), as those pages number them; 16 to 25 and 29 are
# listed as unused and 0 as reserved.
_TICKET_FLAGS = {
    1: 'Forwardable', 2: 'Forwarded', 3: 'Proxiable', 4: 'Proxy', 5: 'Allow-postdate',
    6: 'Postdated', 7: 'Invalid', 8: 'Renewable', 9: 'Initial', 10: 'Pre-authent',
    11: 'Opt-hardware-auth', 12: 'Transited-policy-checked', 13: 'Ok-as-delegate',
    14: 'Request-anonymous', 15: 'Name-canonicalize', 26: 'Disable-transited-check',
    27: 'Renewable-ok', 28: 'Enc-tkt-in-skey', 30: 'Renew', 31: 'Validate',
}

# 'Table 4. Kerberos encryption types' of the 4768 page; the 4769 and 4770 pages give the same table.
_ENCRYPTION_TYPES = {
    0x1: 'DES-CBC-CRC', 0x3: 'DES-CBC-MD5', 0x11: 'AES128-CTS-HMAC-SHA1-96',
    0x12: 'AES256-CTS-HMAC-SHA1-96', 0x17: 'RC4-HMAC', 0x18: 'RC4-HMAC-EXP',
}

# 'Table 5. Kerberos Pre-Authentication types' of the 4768 and 4771 pages.
_PRE_AUTH_TYPES = {
    0: '-', 2: 'PA-ENC-TIMESTAMP', 11: 'PA-ETYPE-INFO', 15: 'PA-PK-AS-REP_OLD',
    16: 'PA-PK-AS-REQ', 17: 'PA-PK-AS-REP', 19: 'PA-ETYPE-INFO2', 20: 'PA-SVR-REFERRAL-INFO',
    138: 'PA-ENCRYPTED-CHALLENGE',
}

# 'Table 3. TGT/TGS issue error codes' of the 4768 page (Result Code).
_TGT_CODES = {
    0x0: 'KDC_ERR_NONE', 0x1: 'KDC_ERR_NAME_EXP', 0x2: 'KDC_ERR_SERVICE_EXP', 0x3: 'KDC_ERR_BAD_PVNO',
    0x4: 'KDC_ERR_C_OLD_MAST_KVNO', 0x5: 'KDC_ERR_S_OLD_MAST_KVNO', 0x6: 'KDC_ERR_C_PRINCIPAL_UNKNOWN',
    0x7: 'KDC_ERR_S_PRINCIPAL_UNKNOWN', 0x8: 'KDC_ERR_PRINCIPAL_NOT_UNIQUE', 0x9: 'KDC_ERR_NULL_KEY',
    0xA: 'KDC_ERR_CANNOT_POSTDATE', 0xB: 'KDC_ERR_NEVER_VALID', 0xC: 'KDC_ERR_POLICY',
    0xD: 'KDC_ERR_BADOPTION', 0xE: 'KDC_ERR_ETYPE_NOTSUPP', 0xF: 'KDC_ERR_SUMTYPE_NOSUPP',
    0x10: 'KDC_ERR_PADATA_TYPE_NOSUPP', 0x11: 'KDC_ERR_TRTYPE_NO_SUPP', 0x12: 'KDC_ERR_CLIENT_REVOKED',
    0x13: 'KDC_ERR_SERVICE_REVOKED', 0x14: 'KDC_ERR_TGT_REVOKED', 0x15: 'KDC_ERR_CLIENT_NOTYET',
    0x16: 'KDC_ERR_SERVICE_NOTYET', 0x17: 'KDC_ERR_KEY_EXPIRED', 0x18: 'KDC_ERR_PREAUTH_FAILED',
    0x19: 'KDC_ERR_PREAUTH_REQUIRED', 0x1A: 'KDC_ERR_SERVER_NOMATCH', 0x1D: 'KDC_ERR_SVC_UNAVAILABLE',
    0x1F: 'KRB_AP_ERR_BAD_INTEGRITY', 0x20: 'KRB_AP_ERR_TKT_EXPIRED', 0x21: 'KRB_AP_ERR_TKT_NYV',
    0x22: 'KRB_AP_ERR_REPEAT', 0x23: 'KRB_AP_ERR_NOT_US', 0x24: 'KRB_AP_ERR_BADMATCH',
    0x25: 'KRB_AP_ERR_SKEW', 0x26: 'KRB_AP_ERR_BADADDR', 0x27: 'KRB_AP_ERR_BADVERSION',
    0x28: 'KRB_AP_ERR_MSG_TYPE', 0x29: 'KRB_AP_ERR_MODIFIED', 0x2A: 'KRB_AP_ERR_BADORDER',
    0x2C: 'KRB_AP_ERR_BADKEYVER', 0x2D: 'KRB_AP_ERR_NOKEY', 0x2E: 'KRB_AP_ERR_MUT_FAIL',
    0x2F: 'KRB_AP_ERR_BADDIRECTION', 0x30: 'KRB_AP_ERR_METHOD', 0x31: 'KRB_AP_ERR_BADSEQ',
    0x32: 'KRB_AP_ERR_INAPP_CKSUM', 0x33: 'KRB_AP_PATH_NOT_ACCEPTED', 0x34: 'KRB_ERR_RESPONSE_TOO_BIG',
    0x3C: 'KRB_ERR_GENERIC', 0x3D: 'KRB_ERR_FIELD_TOOLONG', 0x3E: 'KDC_ERR_CLIENT_NOT_TRUSTED',
    0x3F: 'KDC_ERR_KDC_NOT_TRUSTED', 0x40: 'KDC_ERR_INVALID_SIG', 0x41: 'KDC_ERR_KEY_TOO_WEAK',
    0x42: 'KRB_AP_ERR_USER_TO_USER_REQUIRED', 0x43: 'KRB_AP_ERR_NO_TGT', 0x44: 'KDC_ERR_WRONG_REALM',
}
# The failure code table of the 4769 page (Failure Code): it lists 0x1B, which the 4768 table does not,
# and not 0x1D.
_TGS_CODES = {
    0x0: 'KDC_ERR_NONE', 0x1: 'KDC_ERR_NAME_EXP', 0x2: 'KDC_ERR_SERVICE_EXP', 0x3: 'KDC_ERR_BAD_PVNO',
    0x4: 'KDC_ERR_C_OLD_MAST_KVNO', 0x5: 'KDC_ERR_S_OLD_MAST_KVNO', 0x6: 'KDC_ERR_C_PRINCIPAL_UNKNOWN',
    0x7: 'KDC_ERR_S_PRINCIPAL_UNKNOWN', 0x8: 'KDC_ERR_PRINCIPAL_NOT_UNIQUE', 0x9: 'KDC_ERR_NULL_KEY',
    0xA: 'KDC_ERR_CANNOT_POSTDATE', 0xB: 'KDC_ERR_NEVER_VALID', 0xC: 'KDC_ERR_POLICY',
    0xD: 'KDC_ERR_BADOPTION', 0xE: 'KDC_ERR_ETYPE_NOTSUPP', 0xF: 'KDC_ERR_SUMTYPE_NOSUPP',
    0x10: 'KDC_ERR_PADATA_TYPE_NOSUPP', 0x11: 'KDC_ERR_TRTYPE_NO_SUPP', 0x12: 'KDC_ERR_CLIENT_REVOKED',
    0x13: 'KDC_ERR_SERVICE_REVOKED', 0x14: 'KDC_ERR_TGT_REVOKED', 0x15: 'KDC_ERR_CLIENT_NOTYET',
    0x16: 'KDC_ERR_SERVICE_NOTYET', 0x17: 'KDC_ERR_KEY_EXPIRED', 0x18: 'KDC_ERR_PREAUTH_FAILED',
    0x19: 'KDC_ERR_PREAUTH_REQUIRED', 0x1A: 'KDC_ERR_SERVER_NOMATCH', 0x1B: 'KDC_ERR_MUST_USE_USER2USER',
    0x1F: 'KRB_AP_ERR_BAD_INTEGRITY', 0x20: 'KRB_AP_ERR_TKT_EXPIRED', 0x21: 'KRB_AP_ERR_TKT_NYV',
    0x22: 'KRB_AP_ERR_REPEAT', 0x23: 'KRB_AP_ERR_NOT_US', 0x24: 'KRB_AP_ERR_BADMATCH',
    0x25: 'KRB_AP_ERR_SKEW', 0x26: 'KRB_AP_ERR_BADADDR', 0x27: 'KRB_AP_ERR_BADVERSION',
    0x28: 'KRB_AP_ERR_MSG_TYPE', 0x29: 'KRB_AP_ERR_MODIFIED', 0x2A: 'KRB_AP_ERR_BADORDER',
    0x2C: 'KRB_AP_ERR_BADKEYVER', 0x2D: 'KRB_AP_ERR_NOKEY', 0x2E: 'KRB_AP_ERR_MUT_FAIL',
    0x2F: 'KRB_AP_ERR_BADDIRECTION', 0x30: 'KRB_AP_ERR_METHOD', 0x31: 'KRB_AP_ERR_BADSEQ',
    0x32: 'KRB_AP_ERR_INAPP_CKSUM', 0x33: 'KRB_AP_PATH_NOT_ACCEPTED', 0x34: 'KRB_ERR_RESPONSE_TOO_BIG',
    0x3C: 'KRB_ERR_GENERIC', 0x3D: 'KRB_ERR_FIELD_TOOLONG', 0x3E: 'KDC_ERR_CLIENT_NOT_TRUSTED',
    0x3F: 'KDC_ERR_KDC_NOT_TRUSTED', 0x40: 'KDC_ERR_INVALID_SIG', 0x41: 'KDC_ERR_KEY_TOO_WEAK',
    0x42: 'KRB_AP_ERR_USER_TO_USER_REQUIRED', 0x43: 'KRB_AP_ERR_NO_TGT', 0x44: 'KDC_ERR_WRONG_REALM',
}
# The failure code table of the 4771 page (Failure Code), which lists more codes and spells some names
# differently.
_PRE_AUTH_CODES = {
    0x0: 'KDC_ERR_NONE', 0x1: 'KDC_ERR_NAME_EXP', 0x2: 'KDC_ERR_SERVICE_EXP', 0x3: 'KDC_ERR_BAD_PVNO',
    0x4: 'KDC_ERR_C_OLD_MAST_KVNO', 0x5: 'KDC_ERR_S_OLD_MAST_KVNO', 0x6: 'KDC_ERR_C_PRINCIPAL_UNKNOWN',
    0x7: 'KDC_ERR_S_PRINCIPAL_UNKNOWN', 0x8: 'KDC_ERR_PRINCIPAL_NOT_UNIQUE', 0x9: 'KDC_ERR_NULL_KEY',
    0xA: 'KDC_ERR_CANNOT_POSTDATE', 0xB: 'KDC_ERR_NEVER_VALID', 0xC: 'KDC_ERR_POLICY',
    0xD: 'KDC_ERR_BADOPTION', 0xE: 'KDC_ERR_ETYPE_NOSUPP', 0xF: 'KDC_ERR_SUMTYPE_NOSUPP',
    0x10: 'KDC_ERR_PADATA_TYPE_NOSUPP', 0x11: 'KDC_ERR_TRTYPE_NOSUPP', 0x12: 'KDC_ERR_CLIENT_REVOKED',
    0x13: 'KDC_ERR_SERVICE_REVOKED', 0x14: 'KDC_ERR_TGT_REVOKED', 0x15: 'KDC_ERR_CLIENT_NOTYET',
    0x16: 'KDC_ERR_SERVICE_NOTYET', 0x17: 'KDC_ERR_KEY_EXPIRED', 0x18: 'KDC_ERR_PREAUTH_FAILED',
    0x19: 'KDC_ERR_PREAUTH_REQUIRED', 0x1A: 'KDC_ERR_SERVER_NOMATCH', 0x1B: 'KDC_ERR_MUST_USE_USER2USER',
    0x1C: 'KDC_ERR_PATH_NOT_ACCEPTED', 0x1D: 'KDC_ERR_SVC_UNAVAILABLE', 0x1F: 'KRB_AP_ERR_BAD_INTEGRITY',
    0x20: 'KRB_AP_ERR_TKT_EXPIRED', 0x21: 'KRB_AP_ERR_TKT_NYV', 0x22: 'KRB_AP_ERR_REPEAT',
    0x23: 'KRB_AP_ERR_NOT_US', 0x24: 'KRB_AP_ERR_BADMATCH', 0x25: 'KRB_AP_ERR_SKEW',
    0x26: 'KRB_AP_ERR_BADADDR', 0x27: 'KRB_AP_ERR_BADVERSION', 0x28: 'KRB_AP_ERR_MSG_TYPE',
    0x29: 'KRB_AP_ERR_MODIFIED', 0x2A: 'KRB_AP_ERR_BADORDER', 0x2C: 'KRB_AP_ERR_BADKEYVER',
    0x2D: 'KRB_AP_ERR_NOKEY', 0x2E: 'KRB_AP_ERR_MUT_FAIL', 0x2F: 'KRB_AP_ERR_BADDIRECTION',
    0x30: 'KRB_AP_ERR_METHOD', 0x31: 'KRB_AP_ERR_BADSEQ', 0x32: 'KRB_AP_ERR_INAPP_CKSUM',
    0x33: 'KRB_AP_PATH_NOT_ACCEPTED', 0x34: 'KRB_ERR_RESPONSE_TOO_BIG', 0x3C: 'KRB_ERR_GENERIC',
    0x3D: 'KRB_ERR_FIELD_TOOLONG', 0x3E: 'KDC_ERROR_CLIENT_NOT_TRUSTED', 0x3F: 'KDC_ERROR_KDC_NOT_TRUSTED',
    0x40: 'KDC_ERROR_INVALID_SIG', 0x41: 'KDC_ERR_KEY_TOO_WEAK', 0x42: 'KDC_ERR_CERTIFICATE_MISMATCH',
    0x43: 'KRB_AP_ERR_NO_TGT', 0x44: 'KDC_ERR_WRONG_REALM', 0x45: 'KRB_AP_ERR_USER_TO_USER_REQUIRED',
    0x46: 'KDC_ERR_CANT_VERIFY_CERTIFICATE', 0x47: 'KDC_ERR_INVALID_CERTIFICATE',
    0x48: 'KDC_ERR_REVOKED_CERTIFICATE', 0x49: 'KDC_ERR_REVOCATION_STATUS_UNKNOWN',
    0x4A: 'KDC_ERR_REVOCATION_STATUS_UNAVAILABLE', 0x4B: 'KDC_ERR_CLIENT_NAME_MISMATCH',
    0x4C: 'KDC_ERR_KDC_NAME_MISMATCH',
}
_RESULT_CODES = {'4768': _TGT_CODES, '4769': _TGS_CODES, '4771': _PRE_AUTH_CODES}

# 'Table 1. Winlogon Error Codes' of the 4776 page: the code and Microsoft's description.
_NTLM_CODES = {
    0xC0000064: 'The username you typed does not exist. Bad username.',
    0xC000006A: 'Account logon with misspelled or bad password.',
    0xC000006D: 'Generic logon failure.',
    0xC000006F: 'Account logon outside authorized hours.',
    0xC0000070: 'Account logon from unauthorized workstation.',
    0xC0000071: 'Account logon with expired password.',
    0xC0000072: 'Account logon to account disabled by administrator.',
    0xC0000193: 'Account logon with expired account.',
    0xC0000224: 'Account logon with "Change Password at Next Logon" flagged.',
    0xC0000234: 'Account logon with account locked.',
    0xC0000371: 'The local account store does not contain secret material for the specified account.',
    0x0: 'No errors.',
}

# 'Table of file access codes' (Table 13) of the 5145 page: each access right's parameter
# reference (schema value) and name. The 5140 page refers to the same table.
_FILE_ACCESSES = {
    4416: 'ReadData (or ListDirectory)', 4417: 'WriteData (or AddFile)',
    4418: 'AppendData (or AddSubdirectory or CreatePipeInstance)', 4419: 'ReadEA', 4420: 'WriteEA',
    4421: 'Execute/Traverse', 4422: 'DeleteChild', 4423: 'ReadAttributes', 4424: 'WriteAttributes',
    1537: 'DELETE', 1538: 'READ_CONTROL', 1539: 'WRITE_DAC', 1540: 'WRITE_OWNER', 1541: 'SYNCHRONIZE',
    1542: 'ACCESS_SYS_SEC',
}

# 'Table 9. Active Directory Access Codes and Rights' of the 4662 page: mask bit and name.
_DIRECTORY_ACCESSES = (
    (0x1, 'Create Child'), (0x2, 'Delete Child'), (0x4, 'List Contents'), (0x8, 'SELF'),
    (0x10, 'Read Property'), (0x20, 'Write Property'), (0x40, 'Delete Tree'), (0x80, 'List Object'),
    (0x100, 'Control Access'), (0x10000, 'DELETE'), (0x20000, 'READ_CONTROL'), (0x40000, 'WRITE_DAC'),
    (0x80000, 'WRITE_OWNER'), (0x100000, 'SYNCHRONIZE'), (0x1000000, 'ADS_RIGHT_ACCESS_SYSTEM_SECURITY'),
    (0x10000000, 'ADS_RIGHT_GENERIC_ALL'), (0x20000000, 'ADS_RIGHT_GENERIC_EXECUTE'),
    (0x40000000, 'ADS_RIGHT_GENERIC_WRITE'), (0x80000000, 'ADS_RIGHT_GENERIC_READ'),
)

# [MS-ADTS] 5.1.3.2.1 Control Access Rights: each right's symbol and the GUID that identifies it.
_CONTROL_ACCESS_RIGHTS = {
    'ee914b82-0a98-11d1-adbb-00c04fd8d5cd': 'Abandon-Replication',
    '440820ad-65b4-11d1-a3da-0000f875ae0d': 'Add-GUID',
    '1abd7cf8-0a99-11d1-adbb-00c04fd8d5cd': 'Allocate-Rids',
    '68b1d179-0d15-4d4f-ab71-46152e79a7bc': 'Allowed-To-Authenticate',
    'edacfd8f-ffb3-11d1-b41d-00a0c968f939': 'Apply-Group-Policy',
    '0e10c968-78fb-11d2-90d4-00c04f79dc55': 'Certificate-Enrollment',
    'a05b8cc2-17bc-4802-a710-e7c15ab866a2': 'Certificate-AutoEnrollment',
    '014bf69c-7b3b-11d1-85f6-08002be74fab': 'Change-Domain-Master',
    'cc17b1fb-33d9-11d2-97d4-00c04fd8d5cd': 'Change-Infrastructure-Master',
    'bae50096-4752-11d1-9052-00c04fc2d4cf': 'Change-PDC',
    'd58d5f36-0a98-11d1-adbb-00c04fd8d5cd': 'Change-Rid-Master',
    'e12b56b6-0a95-11d1-adbb-00c04fd8d5cd': 'Change-Schema-Master',
    'e2a36dc9-ae17-47c3-b58b-be34c55ba633': 'Create-Inbound-Forest-Trust',
    'fec364e0-0a98-11d1-adbb-00c04fd8d5cd': 'Do-Garbage-Collection',
    'ab721a52-1e2f-11d0-9819-00aa0040529b': 'Domain-Administer-Server',
    '69ae6200-7f46-11d2-b9ad-00c04f79f805': 'DS-Check-Stale-Phantoms',
    '2f16c4a5-b98e-432c-952a-cb388ba33f2e': 'DS-Execute-Intentions-Script',
    '9923a32a-3607-11d2-b9be-0000f87a36b2': 'DS-Install-Replica',
    '4ecc03fe-ffc0-4947-b630-eb672a8a9dbc': 'DS-Query-Self-Quota',
    '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2': 'DS-Replication-Get-Changes',
    '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2': 'DS-Replication-Get-Changes-All',
    '89e95b76-444d-4c62-991a-0facbeda640c': 'DS-Replication-Get-Changes-In-Filtered-Set',
    '1131f6ac-9c07-11d1-f79f-00c04fc2dcd2': 'DS-Replication-Manage-Topology',
    'f98340fb-7c5b-4cdb-a00b-2ebdfa115a96': 'DS-Replication-Monitor-Topology',
    '1131f6ab-9c07-11d1-f79f-00c04fc2dcd2': 'DS-Replication-Synchronize',
    '05c74c5e-4deb-43b4-bd9f-86664c2a7fd5': 'Enable-Per-User-Reversibly-Encrypted-Password',
    'b7b1b3de-ab09-4242-9e30-9980e5d322f7': 'Generate-RSoP-Logging',
    'b7b1b3dd-ab09-4242-9e30-9980e5d322f7': 'Generate-RSoP-Planning',
    '7c0e2a7c-a419-48e4-a995-10180aad54dd': 'Manage-Optional-Features',
    'ba33815a-4f93-4c76-87f3-57574bff8109': 'Migrate-SID-History',
    'b4e60130-df3f-11d1-9c86-006008764d0e': 'msmq-Open-Connector',
    '06bd3201-df3e-11d1-9c86-006008764d0e': 'msmq-Peek',
    '4b6e08c3-df3c-11d1-9c86-006008764d0e': 'msmq-Peek-computer-Journal',
    '4b6e08c1-df3c-11d1-9c86-006008764d0e': 'msmq-Peek-Dead-Letter',
    '06bd3200-df3e-11d1-9c86-006008764d0e': 'msmq-Receive',
    '4b6e08c2-df3c-11d1-9c86-006008764d0e': 'msmq-Receive-computer-Journal',
    '4b6e08c0-df3c-11d1-9c86-006008764d0e': 'msmq-Receive-Dead-Letter',
    '06bd3203-df3e-11d1-9c86-006008764d0e': 'msmq-Receive-journal',
    '06bd3202-df3e-11d1-9c86-006008764d0e': 'msmq-Send',
    'a1990816-4298-11d1-ade2-00c04fd8d5cd': 'Open-Address-Book',
    '1131f6ae-9c07-11d1-f79f-00c04fc2dcd2': 'Read-Only-Replication-Secret-Synchronization',
    '45ec5156-db7e-47bb-b53f-dbeb2d03c40f': 'Reanimate-Tombstones',
    '0bc1554e-0a99-11d1-adbb-00c04fd8d5cd': 'Recalculate-Hierarchy',
    '62dd28a8-7f46-11d2-b9ad-00c04f79f805': 'Recalculate-Security-Inheritance',
    'ab721a56-1e2f-11d0-9819-00aa0040529b': 'Receive-As',
    '9432c620-033c-4db7-8b58-14ef6d0bf477': 'Refresh-Group-Cache',
    '1a60ea8d-58a6-4b20-bcdc-fb71eb8a9ff8': 'Reload-SSL-Certificate',
    '7726b9d5-a4b4-4288-a6b2-dce952e80a7f': 'Run-Protect_Admin_Groups-Task',
    '91d67418-0135-4acc-8d79-c08e857cfbec': 'SAM-Enumerate-Entire-Domain',
    'ab721a54-1e2f-11d0-9819-00aa0040529b': 'Send-As',
    'ab721a55-1e2f-11d0-9819-00aa0040529b': 'Send-To',
    'ccc2dc7d-a6ad-4a7a-8846-c04e3cc53501': 'Unexpire-Password',
    '280f369c-67c7-438e-ae98-1d46f3c6f541': 'Update-Password-Not-Required-Bit',
    'be2bb760-7f46-11d2-b9ad-00c04f79f805': 'Update-Schema-Cache',
    'ab721a53-1e2f-11d0-9819-00aa0040529b': 'User-Change-Password',
    '00299570-246d-11d0-a768-00aa006e0529': 'User-Force-Change-Password',
    '3e0f7e18-2c7a-4c10-ba82-4d926db99a3e': 'DS-Clone-Domain-Controller',
    '084c93a2-620d-4879-a836-f0ae47de0e89': 'DS-Read-Partition-Secrets',
    '94825a8d-b171-4116-8146-1e34d8f54401': 'DS-Write-Partition-Secrets',
    '4125c71f-7fac-4ff0-bcb7-f09a41325286': 'DS-Set-Owner',
    '88a9933e-e5c8-4f2a-9dd7-2527416b8092': 'DS-Bypass-Quota',
    '9b026da6-0d3c-465c-8bee-5199d7165cba': 'DS-Validated-Write-Computer',
}

__artifacts_v2__ = {
    "kerberosTicketEvents": {
        "name": "Kerberos Ticket Events",
        "description": "Kerberos ticket requests, renewals and pre-authentication failures recorded in the Security "
                       "event log, Event IDs 4768, 4769, 4770 and 4771: the account, the service, the client "
                       "address, the result code and the ticket options and encryption type.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 'Microsoft-Windows-Security-Auditing events 4768, 4769, 4770 and 4771 is one row; only that provider is '
                 'read, because an Event ID means different things for different providers. Event is the title of the '
                 "event's page in Microsoft's audit documentation (Microsoft, '4768(S, F): A Kerberos authentication "
                 "ticket (TGT) was requested.', '4769(S, F): A Kerberos service ticket was requested.', '4770(S): A "
                 "Kerberos service ticket was renewed.' and '4771(F): Kerberos pre-authentication failed.', each as "
                 'updated 27 April 2026, '
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4768, '
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4769, '
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4770, '
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4771). '
                 "Those pages describe the events as generated only on domain controllers. The columns are the record's "
                 'fields as stored, without surrounding white space: Account Name TargetUserName, Account Domain '
                 'TargetDomainName, Account SID TargetSid (4768 and 4771 only; 4769 and 4770 store none), Service Name '
                 'ServiceName, Service SID ServiceSid, Client Address IpAddress, Client Port IpPort, Logon GUID LogonGuid '
                 'and Transited Services TransmittedServices (4769 only), and Certificate the issuer, serial number and '
                 "thumbprint (CertIssuerName, CertSerialNumber, CertThumbprint, 4768 and 4771) joined with ' | ' when any "
                 'is stored. Where the pages label a field differently the column names follow the 4769 page: the 4768 '
                 'page calls Account Domain the Supplied Realm Name and Account SID the User ID, the 4771 page calls '
                 'Account SID the Security ID, the pages call Service SID the Service ID, and the 4769 and 4771 pages call '
                 'Result Code the Failure Code. Four fields show the stored value followed, in parentheses, by the name '
                 "the table on that event's own page gives it: Result Code (Status) from the code table of the 4768, 4769 "
                 'or 4771 page, which differ in which codes they list and in some names; Ticket Encryption Type '
                 "(TicketEncryptionType) from 'Table 4. Kerberos encryption types' of the 4768 page, which the 4769 and "
                 "4770 pages carry uncaptioned; Pre-Authentication Type (PreAuthType) from 'Table 5. Kerberos "
                 "Pre-Authentication types' of the 4768 and 4771 pages; and Ticket Options (TicketOptions) with the names "
                 "of the flags it sets from 'Table 2. Kerberos ticket flags' of the 4768 page (Table 6 on the 4771 page, "
                 'uncaptioned on the 4769 and 4770 pages, the same table on all four), bits numbered from the most '
                 'significant as those pages number them (a set bit the table lists as reserved or unused is named as an '
                 'unnamed bit). A value the table does not list is reported as stored. 4770 stores no result code, so '
                 "Result Code is blank on its rows. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 'scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, counted in '
                 "UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a floating-point "
                 'number, which can differ by microseconds '
                 '(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). '
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are in the "
                 "order each log file holds its records; when several logs match, one log's rows follow another's. The "
                 'tested logs give 214 rows on szechuan_dc01_server2012r2 (62 of 4768, 152 of 4769), 2,948 on '
                 'ou_ransomware_server2022 (1,051 of 4768, 1,764 of 4769, 133 of 4770) and 2 on evtx_mitre_attack_4688_cc0 '
                 "(one 4768 and one 4769, from mdecrevoisier's public CC0 sample logs). No tested log holds a 4771 record, "
                 'so that event and its failure code table are read but unexercised. Result Code is 0x00000000 '
                 '(KDC_ERR_NONE) on every 4768 and 4769 row; no failed ticket request is in the tested logs. Ticket '
                 'Encryption Type is 0x00000012 (AES256-CTS-HMAC-SHA1-96) on every row, Pre-Authentication Type is 2 '
                 "(PA-ENC-TIMESTAMP) on every 4768 row, Transited Services is '-' on every 4769 row and Certificate is "
                 'blank on every row. Client Address is ::1 on 1,992 rows, all with Client Port 0, and an ::ffff: IPv4 '
                 'address on the other 1,172. Every tested record of these four events is event version 0. Microsoft notes '
                 'that Windows Server 2016 and later show an updated 4768 and 4769 after the January 2025 security update, '
                 'with more fields (the encryption types supported and the keys available for the account, the service and '
                 'the domain controller); those fields are not reported, and no tested log holds such a record. Result '
                 'Code held one value on every row of szechuan_dc01_server2012r2. Computer held one value on every row of '
                 'ou_ransomware_server2022. A row records what the domain controller logged for the request; it does not '
                 'show that the ticket was then presented to the named service. The Security logs of af_case2_win10, '
                 'alihadi_challenge3_win81, alihadi_threatsim_server2019, cfreds_leakage_win7, hexordia_mvs2025_win11, '
                 'lonewolf_win10, pc_mus_001_win11, szechuan_win10, windows11_arm_4688_known, windows11_arm_known_20261001 '
                 'and windows11_arm_winlogon_known_20261004 hold none of these events. A record python-evtx cannot render, '
                 'or whose XML does not parse, is counted in the run log and not reported; every record of the tested logs '
                 'rendered. A log marked dirty is read past the chunks its header counts, and the run log says how many '
                 'records came from there; the Security log of szechuan_dc01_server2012r2 is marked dirty and 2,414 of its '
                 '8,574 records come from those chunks. Reading needs the python-evtx package (pip install python-evtx).',
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 214 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 2948 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_mitre_attack_4688_cc0": "Public sample logs, Windows builds not recorded | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (the matched files held nothing this artifact reports)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100) | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
        },
    },
    "ntlmCredentialValidations": {
        "name": "NTLM Credential Validations",
        "description": "NTLM credential validation attempts recorded in the Security event log, Event ID 4776: the "
                       "account, the source workstation and the error code.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 "Microsoft-Windows-Security-Auditing event 4776 is one row; only that provider is read. Microsoft's page "
                 "for the event, '4776(S, F): The computer attempted to validate the credentials for an account.' (as "
                 'updated 27 April 2026, '
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4776), '
                 'describes it as generated on the computer that is authoritative for the credentials, the domain '
                 'controller for a domain account, for successful and failed NTLM credential validation, and says it shows '
                 'only the computer the attempt came from, not the destination. Logon Account is TargetUserName, Source '
                 'Workstation Workstation and Authentication Package PackageName, as stored. Error Code is Status as '
                 "stored, followed by Microsoft's description from 'Table 1. Winlogon Error Codes' of that page when the "
                 "table lists it; a code it does not list is reported as stored. Event Time (UTC) is the record's "
                 'TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with '
                 "integer arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's "
                 'conversion through a floating-point number, which can differ by microseconds '
                 '(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). '
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are in the "
                 "order each log file holds its records; when several logs match, one log's rows follow another's. The "
                 'tested logs give 12 rows on szechuan_dc01_server2012r2, 1,583 on ou_ransomware_server2022 and 10 on '
                 "evtx_mitre_attack_4688_cc0 (mdecrevoisier's public CC0 sample logs). Error Code is 0x00000000 on every "
                 'row of the two servers; on the sample logs 5 rows hold 0x00000000 and 5 hold 0xc0000064, which the table '
                 'describes as a bad user name. Authentication Package held MICROSOFT_AUTHENTICATION_PACKAGE_V1_0 on every '
                 "row, the value Microsoft's page gives for this event. Source Workstation was blank on 1 row of the "
                 'sample logs. Computer held one value on every row of ou_ransomware_server2022. The Security logs of '
                 'af_case2_win10, alihadi_challenge3_win81, alihadi_threatsim_server2019, cfreds_leakage_win7, '
                 'hexordia_mvs2025_win11, lonewolf_win10, pc_mus_001_win11, szechuan_win10, windows11_arm_4688_known, '
                 'windows11_arm_known_20261001 and windows11_arm_winlogon_known_20261004 hold none of these events. A '
                 'record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not '
                 'reported; every record of the tested logs rendered. A log marked dirty is read past the chunks its '
                 'header counts, and the run log says how many records came from there; the Security log of '
                 'szechuan_dc01_server2012r2 is marked dirty and 2,414 of its 8,574 records come from those chunks. '
                 'Reading needs the python-evtx package (pip install python-evtx).',
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "user-check",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 12 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 1583 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_mitre_attack_4688_cc0": "Public sample logs, Windows builds not recorded | 10 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (the matched files held nothing this artifact reports)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100) | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 1 row",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 1 row",
        },
    },
    "networkShareAccess": {
        "name": "Network Share Access",
        "description": "Network share access recorded in the Security event log, Event IDs 5140 and 5145: the "
                       "share, the file or folder under it, the accesses requested, the account and the source "
                       "address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 'Microsoft-Windows-Security-Auditing events 5140 and 5145 is one row; only that provider is read. Event '
                 "is the title of the event's page in Microsoft's audit documentation (Microsoft, '5140(S, F): A network "
                 "share object was accessed.' and '5145(S, F): A network share object was checked to see whether client "
                 "can be granted desired access.', each as updated 27 April 2026, "
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-5140, '
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-5145). '
                 'The 5140 page says that event is generated once per session, at the first access attempt, and the 5145 '
                 'page that a failure is logged only when access is denied at the share level, not when it is denied by '
                 'the file system. Share Name is ShareName, Share Path ShareLocalPath, Relative Target Name '
                 'RelativeTargetName (5145 only, the file or folder under the share), Access Mask AccessMask and Access '
                 'Reason AccessReason (5145 only), as stored. Accesses is AccessList, a list of parameter references '
                 "(%%n): each is given the access right that 'Table 13. File access codes' of the 5145 page lists for it, "
                 "followed by the reference, as in 'ReadData (or ListDirectory) (%%4416)', and a reference the table does "
                 'not list is reported as stored. Whether access was granted is not reported: the 5145 page says the '
                 "Access Reason field carries the result for each access, and that field was '-' on every tested row; the "
                 "record's Keywords are not read. Account Name, Account Domain, Account SID and Logon ID are "
                 'SubjectUserName, SubjectDomainName, SubjectUserSid and SubjectLogonId, and Source Address and Source '
                 'Port are IpAddress and IpPort, as stored. ObjectType is not reported: both pages say it is always File '
                 "for these events, and it was File on every tested record. Event Time (UTC) is the record's TimeCreated "
                 'SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with integer '
                 "arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion "
                 'through a floating-point number, which can differ by microseconds '
                 '(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). '
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are in the "
                 "order each log file holds its records; when several logs match, one log's rows follow another's. Only "
                 "evtx_mitre_attack_4688_cc0, mdecrevoisier's public CC0 sample logs, holds these events among the tested "
                 'logs: 1,781 rows, 384 of 5140 and 1,397 of 5145, across three share names. Account Domain held one value '
                 "on every row. Access Reason is '-' on every 5145 row, and Relative Target Name is filled on every 5145 "
                 'row and blank on every 5140 row. The 5140 records are event version 1 and the 5145 records version 0; '
                 'the 5140 page lists only version 0, and the fields read here are the ones it names. Every reference in '
                 'Accesses was in the table except %%1543, on 2 rows, which is reported as stored. None of the tested logs '
                 'of the two domain controllers holds these events, so share access on a file server or domain controller '
                 'is unexercised. The other Windows logs tested, including those of szechuan_dc01_server2012r2 and '
                 'ou_ransomware_server2022, hold none of these events. A record python-evtx cannot render, or whose XML '
                 'does not parse, is counted in the run log and not reported; every record of the tested logs rendered. A '
                 'log marked dirty is read past the chunks its header counts, and the run log says how many records came '
                 'from there; the Security log of szechuan_dc01_server2012r2 is marked dirty and 2,414 of its 8,574 '
                 'records come from those chunks. Reading needs the python-evtx package (pip install python-evtx).',
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "folder",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (the matched files held nothing this artifact reports)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_mitre_attack_4688_cc0": "Public sample logs, Windows builds not recorded | 1781 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (the matched files held nothing this artifact reports)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100) | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 20 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
        },
    },
    "directoryServiceAccess": {
        "name": "Directory Service Object Access",
        "description": "Operations on Active Directory objects recorded in the Security event log, Event ID 4662: "
                       "the object, the accesses, the control access rights the record names and the account.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security event log, named in the report's located-at line. Each record of "
                 "Microsoft-Windows-Security-Auditing event 4662 is one row; only that provider is read. Microsoft's page "
                 "for the event, '4662(S, F): An operation was performed on an object.' (as updated 27 April 2026, "
                 'https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4662), '
                 'describes it as generated on a domain controller for an operation on an Active Directory object, only '
                 "when the object's system access control list (SACL) asks for it, one event for each type of operation. "
                 'It is reported because the Properties field names the control access rights an operation used, including '
                 'the directory replication rights. Operation Type is OperationType, Object Server ObjectServer, Object '
                 'Type ObjectType (a class GUID on every tested row except the one LSA row named below, which holds a type '
                 'name), Object Name ObjectName, Access Mask AccessMask, Additional Info and Additional Info2 '
                 'AdditionalInfo and AdditionalInfo2, Handle ID HandleId, and Account Name, Account Domain, Account SID '
                 'and Logon ID SubjectUserName, SubjectDomainName, SubjectUserSid and SubjectLogonId, as stored. Accesses '
                 "names the bits of Access Mask from 'Table 9. Active Directory Access Codes and Rights' of that page; a "
                 'bit the table does not list is named as unnamed. Properties is the field as stored with runs of white '
                 'space, line breaks and tabs included, collapsed to single spaces: as the 4662 page describes it, the '
                 'type of access, then a tree of GUIDs of classes or property sets. Control Access Rights names each right '
                 "whose GUID is in Properties and in Microsoft's [MS-ADTS] 5.1.3.2.1 Control Access Rights table, once "
                 'each, in the order its GUID first appears, by the symbol that table gives it (as updated 24 August 2026, '
                 'https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/1522b774-6464-41a3-87a5-1e5633c3fbbb); '
                 'other GUIDs are not named. A 4662 naming DS-Replication-Get-Changes records that the account used that '
                 "right on the object; it does not show by itself what was replicated. Event Time (UTC) is the record's "
                 'TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with '
                 "integer arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's "
                 'conversion through a floating-point number, which can differ by microseconds '
                 '(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). '
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Rows are in the "
                 "order each log file holds its records; when several logs match, one log's rows follow another's. The "
                 'tested logs give 50 rows on szechuan_dc01_server2012r2, 143 on ou_ransomware_server2022 and 3 on '
                 "evtx_mitre_attack_4688_cc0 (mdecrevoisier's public CC0 sample logs). Control Access Rights names "
                 'DS-Replication-Get-Changes on 10 and 123 rows of the two servers, every one with Accesses Control Access '
                 'and an Account Name ending in $; no other right was named. Control Access Rights was blank on every row '
                 'of the sample logs. Operation Type, Object Server and Handle ID held one value on every row of each '
                 "server, Account Domain one value on every row of each server, and Additional Info held '-' on every row "
                 'of the sample logs. On the sample logs 1 row has Object Server LSA, where the 4662 page gives DS for '
                 'this event. Computer held one value on every row of ou_ransomware_server2022. The Security logs of '
                 'af_case2_win10, alihadi_challenge3_win81, alihadi_threatsim_server2019, cfreds_leakage_win7, '
                 'hexordia_mvs2025_win11, lonewolf_win10, pc_mus_001_win11, szechuan_win10, windows11_arm_4688_known, '
                 'windows11_arm_known_20261001 and windows11_arm_winlogon_known_20261004 hold none of these events. A '
                 'record python-evtx cannot render, or whose XML does not parse, is counted in the run log and not '
                 'reported; every record of the tested logs rendered. A log marked dirty is read past the chunks its '
                 'header counts, and the run log says how many records came from there; the Security log of '
                 'szechuan_dc01_server2012r2 is marked dirty and 2,414 of its 8,574 records come from those chunks. '
                 'Reading needs the python-evtx package (pip install python-evtx).',
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "database",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 50 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 143 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_mitre_attack_4688_cc0": "Public sample logs, Windows builds not recorded | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (the matched files held nothing this artifact reports)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100) | 0 rows (the matched files held nothing this artifact reports)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
        },
    },
}

_read = {}
_GUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
_REFERENCE = re.compile(r'%%(\d+)')


def _security_logs(context):
    return sorted(path for path in (str(f) for f in context.get_files_found())
                  if path.lower().endswith(_LOG) and not os.path.isdir(path))


def domain_records(context):
    """The records of the eight events in every Security log found, and the logs read.

    The module's four artifacts are given the same staged logs one after the other, so the
    logs are read once and the result is kept while their paths, sizes and modification
    times stay the same.
    """
    key = tuple((path, os.path.getsize(path), os.path.getmtime(path))
                for path in _security_logs(context))
    if _read.get('key') != key:
        records, sources = read_event_records(context, _LOG, _LABEL, event_ids=_EVENT_IDS,
                                              provider=_SECURITY)
        _read.clear()
        _read.update(key=key, records=records, sources=sources)
    return _read['records'], _read['sources']


def _number(value, base=16):
    """The stored number, or None when the text is not one."""
    text = (value or '').strip()
    try:
        return int(text, base)
    except ValueError:
        return None


def named(value, table, base=16):
    """'value (name)' when `table` names the stored number, else the value as stored."""
    text = (value or '').strip()
    number = _number(text, base)
    if number is None or number not in table:
        return text
    return f'{text} ({table[number]})'


def ticket_options(value):
    """The stored ticket options with the names of the flags they set, MSB 0 numbering."""
    text = (value or '').strip()
    number = _number(text)
    if number is None or not 0 <= number <= 0xFFFFFFFF:
        return text
    names = [name for bit, name in sorted(_TICKET_FLAGS.items()) if number & (1 << (31 - bit))]
    unnamed = [str(bit) for bit in range(32)
               if number & (1 << (31 - bit)) and bit not in _TICKET_FLAGS]
    if unnamed:
        names.append('unnamed bit ' + ', '.join(unnamed))
    return f'{text} ({", ".join(names)})' if names else text


def _certificate(record):
    parts = [record.get('CertIssuerName'), record.get('CertSerialNumber'), record.get('CertThumbprint')]
    return ' | '.join(parts) if any(parts) else ''


def kerberos_row(record):
    event_id = record.event_id
    codes = _RESULT_CODES.get(event_id)
    result = named(record.get('Status'), codes) if codes is not None else record.get('Status')
    encryption = record.get('TicketEncryptionType')
    if event_id in ('4768', '4769', '4770'):
        encryption = named(encryption, _ENCRYPTION_TYPES)
    pre_auth = record.get('PreAuthType')
    if event_id in ('4768', '4771'):
        pre_auth = named(pre_auth, _PRE_AUTH_TYPES, base=10)
    return (record.time, event_id, _KERBEROS[event_id], record.get('TargetUserName'),
            record.get('TargetDomainName'), record.get('TargetSid'), record.get('ServiceName'),
            record.get('ServiceSid'), record.get('IpAddress'), record.get('IpPort'), result,
            ticket_options(record.get('TicketOptions')), encryption, pre_auth,
            record.get('LogonGuid'), record.get('TransmittedServices'), _certificate(record),
            record.record_id, record.computer)


def ntlm_row(record):
    return (record.time, record.get('TargetUserName'), record.get('Workstation'),
            named(record.get('Status'), _NTLM_CODES), record.get('PackageName'),
            record.record_id, record.computer)


def file_accesses(value):
    """The stored access references (%%n) named from the file access table, one per line kept apart."""
    pieces = (value or '').split()
    shown = []
    for piece in pieces:
        match = _REFERENCE.fullmatch(piece)
        if match and int(match.group(1)) in _FILE_ACCESSES:
            shown.append(f'{_FILE_ACCESSES[int(match.group(1))]} ({piece})')
        else:
            shown.append(piece)
    return ', '.join(shown)


def _subject(record):
    return (record.get('SubjectUserName'), record.get('SubjectDomainName'),
            record.get('SubjectUserSid'), record.get('SubjectLogonId'))


def share_row(record):
    return (record.time, record.event_id, _SHARES[record.event_id], record.get('ShareName'),
            record.get('ShareLocalPath'), record.get('RelativeTargetName'),
            file_accesses(record.get('AccessList')), record.get('AccessMask'),
            record.get('AccessReason'), *_subject(record), record.get('IpAddress'),
            record.get('IpPort'), record.record_id, record.computer)


def directory_accesses(value):
    """The names of the access mask bits the 4662 table lists, in the table's order."""
    number = _number(value)
    if number is None:
        return ''
    names = [name for bit, name in _DIRECTORY_ACCESSES if number & bit]
    rest = number & ~sum(bit for bit, _name in _DIRECTORY_ACCESSES)
    if rest:
        names.append(f'unnamed bits 0x{rest:X}')
    return ', '.join(names)


def control_access_rights(properties):
    """The control access rights whose GUIDs the Properties field holds, in stored order."""
    names = []
    for guid in _GUID.findall(properties or ''):
        name = _CONTROL_ACCESS_RIGHTS.get(guid.lower())
        if name and name not in names:
            names.append(name)
    return ', '.join(names)


def _one_line(value):
    return ' '.join((value or '').split())


def directory_row(record):
    properties = record.get('Properties')
    return (record.time, record.get('OperationType'), record.get('ObjectServer'), record.get('ObjectType'),
            record.get('ObjectName'), directory_accesses(record.get('AccessMask')), record.get('AccessMask'),
            control_access_rights(properties), _one_line(properties), record.get('AdditionalInfo'),
            record.get('AdditionalInfo2'), record.get('HandleId'), *_subject(record),
            record.record_id, record.computer)


@artifact_processor
def kerberosTicketEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Account Name', 'Account Domain',
                    'Account SID', 'Service Name', 'Service SID', 'Client Address', 'Client Port',
                    'Result Code', 'Ticket Options', 'Ticket Encryption Type', 'Pre-Authentication Type',
                    'Logon GUID', 'Transited Services', 'Certificate', 'Record ID', 'Computer')
    records, sources = domain_records(context)
    data_list = [kerberos_row(record) for record in records if record.event_id in _KERBEROS]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ntlmCredentialValidations(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Logon Account', 'Source Workstation', 'Error Code',
                    'Authentication Package', 'Record ID', 'Computer')
    records, sources = domain_records(context)
    data_list = [ntlm_row(record) for record in records if record.event_id == _NTLM]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def networkShareAccess(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Share Name', 'Share Path',
                    'Relative Target Name', 'Accesses', 'Access Mask', 'Access Reason', 'Account Name',
                    'Account Domain', 'Account SID', 'Logon ID', 'Source Address', 'Source Port',
                    'Record ID', 'Computer')
    records, sources = domain_records(context)
    data_list = [share_row(record) for record in records if record.event_id in _SHARES]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def directoryServiceAccess(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Operation Type', 'Object Server', 'Object Type',
                    'Object Name', 'Accesses', 'Access Mask', 'Control Access Rights', 'Properties',
                    'Additional Info', 'Additional Info2', 'Handle ID', 'Account Name', 'Account Domain',
                    'Account SID', 'Logon ID', 'Record ID', 'Computer')
    records, sources = domain_records(context)
    data_list = [directory_row(record) for record in records if record.event_id == _DIRECTORY]
    return data_headers, data_list, '\n'.join(sources)
