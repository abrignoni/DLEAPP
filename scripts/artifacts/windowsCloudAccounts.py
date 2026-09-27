"""OneDrive and Microsoft account identities per user, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "oneDriveAccounts": {
        "name": "OneDrive Accounts",
        "description": "OneDrive client account entries under Software\\Microsoft\\OneDrive\\"
                       "Accounts in each NTUSER.DAT, with their UserEmail, UserFolder, cid and "
                       "sign-in time values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-27",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads each subkey of Software\\Microsoft\\OneDrive\\Accounts in each NTUSER.DAT and "
                 "reports it when it holds a non-empty UserEmail, UserFolder, cid or UserCID "
                 "value; other "
                 "subkeys are skipped. CID is cid, or UserCID when cid is absent or empty. Last "
                 "Sign In and "
                 "Client First Sign In are LastSignInTime and ClientFirstSignInTimestamp read as "
                 "seconds since 1970 UTC. That reading was checked against the OneDrive client's own "
                 "log files: on pc_mus_001_win11 a file in the user's OneDrive logs folder was written"
                 " 0.1 seconds after LastSignInTime and another 2.7 seconds after "
                 "ClientFirstSignInTimestamp, and on lonewolf_win10 one was written 50 seconds after "
                 "ClientFirstSignInTimestamp. Key Last Written is when the account subkey was last "
                 "written. On af_case2_win10 the one account subkey reported holds a UserFolder value "
                 "and no UserEmail, cid, UserCID, LastSignInTime or ClientFirstSignInTimestamp value, "
                 "so User Email, CID, Last Sign In and Client First Sign In are empty there. On "
                 "lonewolf_win10 the account subkey has no UserEmail or LastSignInTime value, so User "
                 "Email and Last Sign In are empty."
                 " A dirty hive, one whose base block's two sequence numbers differ, is read after the "
                 "entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are "
                 "applied, following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a "
                 "replay that would give a key an earlier last-written time than the hive already "
                 "holds, a check added here beyond the specification; the run log names each hive "
                 "replayed, with the sequence numbers applied, and each dirty hive read as it is, with "
                 "the reason.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
        },
    },
    "microsoftAccounts": {
        "name": "Microsoft Accounts (IdentityCRL)",
        "description": "Entries under Software\\Microsoft\\IdentityCRL\\UserExtendedProperties "
                       "in each NTUSER.DAT, one row per subkey, with its cid and "
                       "lastusedcredtype values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-27",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads each subkey of Software\\Microsoft\\IdentityCRL\\UserExtendedProperties in each "
                 "NTUSER.DAT. Account is the subkey name as stored; on pc_mus_001_win11 and "
                 "lonewolf_win10 it is an email address, and CID, the cid value, equals the cid of the"
                 " same user's OneDrive account entry. Last Used Credential Type is the "
                 "lastusedcredtype value as stored; its meaning is not established. Key Last Written "
                 "is when the subkey was last written, which is not established as a sign-in time. "
                 "af_case2_win10 has no such key."
                 " A dirty hive, one whose base block's two sequence numbers differ, is read after the "
                 "entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are "
                 "applied, following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a "
                 "replay that would give a key an earlier last-written time than the hive already holds, "
                 "a check added here beyond the specification; the run log names each hive replayed, "
                 "with the sequence numbers applied, and each dirty hive read as it is, with the reason.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no IdentityCRL UserExtendedProperties key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive, open_key,
                                      unix_utc, user_from_path, value_of)

_ONEDRIVE = r'Software\Microsoft\OneDrive\Accounts'
_IDENTITY_CRL = r'Software\Microsoft\IdentityCRL\UserExtendedProperties'


def _text(value):
    return str(value) if value not in (None, '') else ''


@artifact_processor
def oneDriveAccounts(context):
    data_headers = (('Last Sign In (UTC)', 'datetime'), ('Client First Sign In (UTC)', 'datetime'),
                    ('Key Last Written (UTC)', 'datetime'), 'Account Key', 'User Email',
                    'User Folder', 'CID', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('OneDrive Accounts: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        try:
            root = open_key(open_hive(path, context), _ONEDRIVE)
            for account in (root.subkeys() if root else []):
                email = _text(value_of(account, 'UserEmail'))
                folder = _text(value_of(account, 'UserFolder'))
                cid = _text(value_of(account, 'cid') or value_of(account, 'UserCID'))
                if not (email or folder or cid):
                    continue
                data_list.append((unix_utc(value_of(account, 'LastSignInTime')),
                                  unix_utc(value_of(account, 'ClientFirstSignInTimestamp')),
                                  key_written_utc(account), account.name(), email, folder, cid,
                                  user, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'OneDrive Accounts: could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def microsoftAccounts(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Account', 'CID',
                    'Last Used Credential Type (as stored)', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Microsoft Accounts (IdentityCRL): the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        try:
            root = open_key(open_hive(path, context), _IDENTITY_CRL)
            for account in (root.subkeys() if root else []):
                data_list.append((key_written_utc(account), account.name(),
                                  _text(value_of(account, 'cid')),
                                  _text(value_of(account, 'lastusedcredtype')), user, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Microsoft Accounts (IdentityCRL): could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
