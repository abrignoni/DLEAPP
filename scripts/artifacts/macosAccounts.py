"""Apple ID and internet accounts on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosAppleIdAccounts": {
        "name": "Apple ID Accounts (MobileMeAccounts)",
        "description": "Apple ID accounts in each user's MobileMeAccounts.plist, with the "
                       "account ID, names, DSID, logged-in state and listed services as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Reads the Accounts array of each user's "
                 "~/Library/Preferences/MobileMeAccounts.plist, one row per account. Services Listed "
                 "names every entry in the account's Services array; Services Marked Enabled and "
                 "Services Marked Not Enabled name the entries whose Enabled value is true or false. "
                 "An entry with no Enabled value appears in neither, so absence from those two columns"
                 " does not mean a service is off: 14 of the 16 listed services on dleapp_macos_bigsur"
                 " carry no Enabled value, and 8 of 22 on the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key). Logged In, Managed Apple ID and Primary "
                 "Email Verified are the LoggedIn, isManagedAppleID and primaryEmailVerified values as"
                 " stored. On both images the account's AccountID equals the username of the Apple ID "
                 "and iCloud accounts in the same user's Accounts4.sqlite. The MacBook Pro's account "
                 "has no LoggedIn or AccountUUID value, so Logged In and Account UUID are empty there."
                 " When a logical extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/, a byte-identical second copy is read once and counted in"
                 " the run log.",
        "paths": ('*/Users/*/Library/Preferences/MobileMeAccounts.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 1 row",
        },
    },
    "macosInternetAccounts": {
        "name": "Internet Accounts (Accounts4)",
        "description": "Accounts recorded in each user's Accounts4.sqlite or Accounts3.sqlite, "
                       "with account type, username, description, parent account and state "
                       "flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Reads ZACCOUNT in each user's Accounts4.sqlite or Accounts3.sqlite, joined to "
                 "ZACCOUNTTYPE for the type and to the parent account ZPARENTACCOUNT names. Date is "
                 "ZDATE read as seconds since 00:00:00 UTC on 1 January 2001, the reference date Apple"
                 " documents for NSDate; on dleapp_macos_bigsur all 12 values then fall between 6 and "
                 "9 minutes after the earliest InstallHistory.plist entry. What event ZDATE records is"
                 " not established. Active, Authenticated and Visible are the ZACTIVE, ZAUTHENTICATED "
                 "and ZVISIBLE values as stored; on dleapp_macos_bigsur Visible is Yes on all 12 rows "
                 "and 5 of the 12 accounts name a parent account. On the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key) the Users/ and "
                 "System/Volumes/Data/Users/ copies share the same database file and carry different "
                 "-wal files, so both are read and each of their 22 accounts appears twice, identical "
                 "in every column but Source File. All rows on each image come from one user, so User "
                 "holds one value there. When a logical extraction holds the same file under Users/ "
                 "and under System/Volumes/Data/Users/, a byte-identical second copy is read once and "
                 "counted in the run log. Reference: Apple, 'NSDate', "
                 "https://developer.apple.com/documentation/foundation/nsdate.",
        "paths": ('*/Users/*/Library/Accounts/Accounts3.sqlite*',
                  '*/Users/*/Library/Accounts/Accounts4.sqlite*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 12 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, get_sqlite_db_records, logfunc
from scripts.macos_plists import (load_plist, mac_absolute_utc, unique_sources,
                                  user_from_path)


def _text(value):
    return '' if value is None else str(value)


def _flag(value):
    return {True: 'Yes', False: 'No'}.get(value, '') if isinstance(value, bool) else _text(value)


@artifact_processor
def macosAppleIdAccounts(context):
    data_headers = ('Account ID', 'Display Name', 'First Name', 'Last Name',
                    'Account Description', 'Logged In', 'Managed Apple ID',
                    'Primary Email Verified', 'Account DSID', 'Alternate DSID', 'Account UUID',
                    'Services Listed', 'Services Marked Enabled', 'Services Marked Not Enabled',
                    'User', 'Source File')
    data_list = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Apple ID Accounts')
    read = []
    for path in paths:
        plist = load_plist(path)
        if not isinstance(plist, dict):
            logfunc(f'Apple ID Accounts: could not read {context.get_relative_path(path)}')
            continue
        read.append(path)
        for account in plist.get('Accounts') or []:
            if not isinstance(account, dict):
                continue
            services = [s for s in account.get('Services') or [] if isinstance(s, dict)]
            data_list.append((
                _text(account.get('AccountID')), _text(account.get('DisplayName')),
                _text(account.get('firstName')), _text(account.get('lastName')),
                _text(account.get('AccountDescription')), _flag(account.get('LoggedIn')),
                _flag(account.get('isManagedAppleID')), _flag(account.get('primaryEmailVerified')),
                _text(account.get('AccountDSID')), _text(account.get('AccountAlternateDSID')),
                _text(account.get('AccountUUID')),
                ', '.join(_text(s.get('Name')) for s in services),
                ', '.join(_text(s.get('Name')) for s in services if s.get('Enabled') is True),
                ', '.join(_text(s.get('Name')) for s in services if s.get('Enabled') is False),
                user_from_path(context.get_relative_path(path)),
                context.get_relative_path(path),
            ))
    return data_headers, data_list, '\n'.join(read)


_ACCOUNTS_QUERY = '''
    SELECT a.ZDATE, t.ZACCOUNTTYPEDESCRIPTION, t.ZIDENTIFIER, a.ZUSERNAME,
           a.ZACCOUNTDESCRIPTION, pt.ZACCOUNTTYPEDESCRIPTION, p.ZUSERNAME,
           a.ZACTIVE, a.ZAUTHENTICATED, a.ZVISIBLE, a.ZIDENTIFIER, a.ZOWNINGBUNDLEID
    FROM ZACCOUNT a
    LEFT JOIN ZACCOUNTTYPE t ON t.Z_PK = a.ZACCOUNTTYPE
    LEFT JOIN ZACCOUNT p ON p.Z_PK = a.ZPARENTACCOUNT
    LEFT JOIN ZACCOUNTTYPE pt ON pt.Z_PK = p.ZACCOUNTTYPE
    ORDER BY a.ZDATE
'''


@artifact_processor
def macosInternetAccounts(context):
    data_headers = (('Date (ZDATE, UTC)', 'datetime'), 'Account Type', 'Account Type Identifier',
                    'Username', 'Account Description', 'Parent Account Type',
                    'Parent Account Username', 'Active', 'Authenticated', 'Visible',
                    'Account Identifier', 'Owning Bundle ID', 'User', 'Source File')
    data_list = []
    databases = [p for p in context.get_files_found()
                 if os.path.basename(str(p)) in ('Accounts3.sqlite', 'Accounts4.sqlite')]
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label='Internet Accounts')
    read = []
    for path in paths:
        records = get_sqlite_db_records(path, _ACCOUNTS_QUERY)
        if not records:
            logfunc(f'Internet Accounts: no accounts read from {context.get_relative_path(path)}')
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        for row in records:
            data_list.append((
                mac_absolute_utc(row[0]), _text(row[1]), _text(row[2]), _text(row[3]),
                _text(row[4]), _text(row[5]), _text(row[6]),
                _flag({1: True, 0: False}.get(row[7], row[7])),
                _flag({1: True, 0: False}.get(row[8], row[8])),
                _flag({1: True, 0: False}.get(row[9], row[9])),
                _text(row[10]), _text(row[11]), user_from_path(relative), relative,
            ))
    return data_headers, data_list, '\n'.join(read)
