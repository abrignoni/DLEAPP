"""Account values and OneNote notebook values from packaged-app settings.dat hives.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "packagedAppAccounts": {
        "name": "Packaged App Accounts",
        "description": "Account values that the Microsoft Store, OneNote, Skype and OneDrive "
                       "packaged apps keep in their Settings/settings.dat hives, one row per "
                       "value with the time stored with it: values about the signed-in account "
                       "(sign-in state, account ids, names and email addresses) and, for "
                       "OneNote, the values of the account's Office profile key, reported "
                       "as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Reads Settings/settings.dat under a user's Packages/Microsoft.WindowsStore_*, "
                 "Packages/Microsoft.Office.OneNote_*, Packages/Microsoft.SkypeApp_* and "
                 "Packages/Microsoft.MicrosoftSkyDrive_* folders (the family name compared "
                 "without case). "
                 "The hive is opened as DLEAPP opens every hive (a dirty hive's .LOG1 and .LOG2 entries are "
                 "applied first and the run log says so) and its values are decoded by DLEAPP's own "
                 "scripts/windows_app_settings.py, from the type numbers and composite layout of "
                 "python-registry's SettingsParse.py (Yogesh Khatri, MIT; "
                 "https://github.com/williballenthin/python-registry/blob/4edb5d1b72597faf257878060aa68baa9c5b28df/Registry/SettingsParse.py#L38-L165). "
                 "Value Written is the FILETIME stored at the end of the value, which ogmini's "
                 "Notepad-State-Library (MIT) describes as the time of the setting's change "
                 "(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L298-L307): "
                 "the time the value was written, not the time of any event the value names. Key Last "
                 "Written is the key's own last-written time. "
                 "Only these values are reported, by key and name: Microsoft Store: "
                 "HasUserSignedInBefore_StoreSetting in LocalState, SignedOut in "
                 "LocalState\\Identity, every value of LocalState\\Identity\\CachedAccounts and "
                 "LocalState\\Identity\\CachedProviders (each value named for an account id), "
                 "FirstName, LastName, Provider and IsDefault in each subkey of "
                 "LocalState\\Identity\\CachedIdentities, MoBillingMsaId in "
                 "LocalState\\MODiscoveryDatabase, and LastSignedInUserSignInName, "
                 "LastSignedInUserCid, LastSignedInUserId, LastSignedInUserFirstName, "
                 "LastSignedInUserLastName, LastSignedInUserAccountLocale, LastSignInAccountRegion "
                 "and UserExplicitlySignedOut in LocalState\\configuration\\Service. OneNote: "
                 "ConnectedAccountCID, OneNotePrimaryAccountCID and OneNoteConnectedAccountCID in "
                 "LocalState\\HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\16.0\\Common\\Identity, "
                 "and every value of each subkey of its Identities subkey and of the keys below it "
                 "(on lonewolf_win10 one profile key and its AuthHistory key). Skype: LastSignInName, "
                 "LastSkypeName, MSAWebAccountId, PrimaryDeviceMsa, IsUWPAppSignedIn and "
                 "IsLegacyAppSignedIn in LocalState\\SkypeHost, and MSASkypeName, MSACIDHEX and "
                 "SMSWebAccountId in any subkey of LocalState. OneDrive: CameraBackupAccountEmailKey, "
                 "CameraBackupAccountIdKey and recent_account_id in LocalState. No vendor "
                 "description of these Store, Skype or OneDrive values was found, so each is "
                 "reported under its own name with its value as stored, and what it records "
                 "beyond its name is not established. For the OneNote Identities values, "
                 "Microsoft's 'Identity, authentication, and authorization in Office 2016' "
                 "(https://learn.microsoft.com/en-us/office/2016/security/identity-authentication-authorization, "
                 "page dated 2025-04-24, section 'Delete the Office Profile, and credentials, "
                 "associated with a removed sign in identity') says that signing in to an Office "
                 "app with a Microsoft account or organization ID creates an Office profile for "
                 "that identity under HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\16.0\\Common\\"
                 "Identity\\Identities; in the OneNote hive the same path sits under LocalState, "
                 "and that the page describes this copy is inferred from the path, not stated "
                 "by Microsoft. LastLoginTime under the AuthHistory key is a UInt64 shown as stored, not converted. "
                 "App names the package family (Microsoft.MicrosoftSkyDrive as OneDrive, some "
                 "of whose value names, 4 of 28 on lonewolf_win10, begin Microsoft.OneDrive.App); "
                 "Package is the package folder name as stored, which was lowercase "
                 "(microsoft.microsoftskydrive_8wekyb3d8bbwe) on lonewolf_win10. User and "
                 "Package name the hive a row came from; full paths are in the located-at list. "
                 "Not reported: values holding tokens or credential data (the Store's "
                 "DeviceToken and the Tickets subkeys of CachedIdentities, Skype's "
                 "CachedCredentials, ContactSyncKey, the RegistrationToken values under "
                 "LocalState\\Messaging and the values of LocalState\\ProtectedStorage), the "
                 "Store's other LastSignedInUser* values (subscription, trial, tuner, metering, "
                 "age and privilege values), and every other value of these hives "
                 "(configuration, telemetry, live tile, window and experiment values); OneNote's "
                 "notebook values are in OneNote Notebook Settings. A value that is absent is not "
                 "evidence that no account was used: the apps need not write these values at all. "
                 "Tested: lonewolf_win10 48 rows (Microsoft Store 17, OneNote 18, Skype 10, "
                 "OneDrive 3; the sign-in name, first name and last name values agree across the "
                 "four apps, and whether every id value belongs to that one account is not "
                 "established); pc_mus_001_win11 9 and hexordia_mvs2025_win11 "
                 "7, all Microsoft Store, where Identity\\CachedIdentities held FirstName and "
                 "LastName as empty strings on pc_mus_001_win11 and hexordia_mvs2025_win11 held "
                 "no configuration\\Service, SignedOut or MoBillingMsaId value. User held one "
                 "value on every row of each image (one home folder with these packages), and App "
                 "and Package held one value on pc_mus_001_win11 and hexordia_mvs2025_win11. The "
                 "Store, Skype and OneNote hives of af_case2_win10 (one each) and szechuan_win10 "
                 "(4, 3 and 3, in four home folders) hold none of these values, and the OneNote "
                 "and Skype hives of alihadi_challenge3_win81 hold no values (its Store package "
                 "folder is named winstore_cw5n1h2txyewy, not read here, and its hive holds no "
                 "values either). On a test tree holding the lonewolf_win10 hives as one user, "
                 "the pc_mus_001_win11 Store hive as a second, and copies under a decoy package "
                 "name and in a deeper Settings folder, the artifact gave 57 rows (48 plus 9, "
                 "each user's rows equal to its image's) and the decoys added none. Not "
                 "exercised: a hive holding more than one account, an organization (work or "
                 "school) account, and Skype or OneDrive hives on any image but lonewolf_win10.",
        "paths": ('*/AppData/Local/Packages/Microsoft.WindowsStore_*/Settings/settings.dat*',
                  '*/AppData/Local/Packages/Microsoft.Office.OneNote_*/Settings/settings.dat*',
                  '*/AppData/Local/Packages/Microsoft.SkypeApp_*/Settings/settings.dat*',
                  '*/AppData/Local/Packages/[Mm]icrosoft.[Mm]icrosoft[Ss]ky[Dd]rive_*/Settings/settings.dat*'),
        "output_types": "standard",
        "artifact_icon": "user",
        "sample_data": {
            "lonewolf_win10": "Windows 10 1709 build 16299 | 48 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 7 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (hives hold none of the listed values)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (hives hold none of the listed values)",
            "alihadi_challenge3_win81": "Windows 8.1 build 9600 | 0 rows (hives hold no values)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no file matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 SP1 build 7601 | 0 rows (no file matches the declared paths)",
            "windows11_arm_parallels": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
        },
    },
    "oneNoteNotebookSettings": {
        "name": "OneNote Notebook Settings",
        "description": "Values of the OneNote packaged app's (Microsoft.Office.OneNote) "
                       "OneNote General key in its Settings/settings.dat hive whose names refer "
                       "to notebooks, sections and pages (ActiveNotebook, the Share* values and "
                       "LastMyDocumentsPathUsed), and the names of the subkeys of its Office "
                       "Server Cache key (URLs on the tested image), with the times stored with "
                       "them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Reads Settings/settings.dat under a user's Packages/Microsoft.Office.OneNote_* "
                 "folder. "
                 "The hive is opened as DLEAPP opens every hive (a dirty hive's .LOG1 and .LOG2 entries are "
                 "applied first and the run log says so) and its values are decoded by DLEAPP's own "
                 "scripts/windows_app_settings.py, from the type numbers and composite layout of "
                 "python-registry's SettingsParse.py (Yogesh Khatri, MIT; "
                 "https://github.com/williballenthin/python-registry/blob/4edb5d1b72597faf257878060aa68baa9c5b28df/Registry/SettingsParse.py#L38-L165). "
                 "Value Written is the FILETIME stored at the end of the value, which ogmini's "
                 "Notepad-State-Library (MIT) describes as the time of the setting's change "
                 "(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L298-L307): "
                 "the time the value was written, not the time of any event the value names. Key Last "
                 "Written is the key's own last-written time. "
                 "Reports the values named ActiveNotebook, ShareCurrentNotebook, "
                 "ShareCurrentSection, ShareCurrentSectionPath, ShareCurrentPage, "
                 "ShareQuickNotebook, ShareQuickSection, ShareRecentSections and "
                 "LastMyDocumentsPathUsed in LocalState\\HKEY_CURRENT_USER\\Software\\Microsoft\\"
                 "Office\\16.0\\OneNote\\General, under their own names. No published description "
                 "of these values was found, so what each records (for example which notebook "
                 "the Share values refer to, or when) is not established. A UInt8Array value is "
                 "shown read as UTF-16LE text, split at each NUL and the parts joined with ' | ', "
                 "when its bytes are an even number and decode cleanly, and as stored otherwise; "
                 "Read As says which. That reading is DLEAPP's own, not a documented format: on "
                 "lonewolf_win10 ShareCurrentPage and ShareRecentSections are UInt8Array values "
                 "that read cleanly this way. Each Server Cache entry row is one direct subkey "
                 "of LocalState\\HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\16.0\\Common\\"
                 "Internet\\Server Cache: Value is the subkey's name as stored (a URL on every "
                 "row of the tested image), Key Last Written its last-written time, and Value "
                 "Written held no value on those rows because a key carries no value time; the "
                 "subkeys' own values (Type, Protocol, Expiration and others) are not reported "
                 "and their meaning is not established. The hive's other values (feature flights, "
                 "experiments, telemetry, note tags, AutoCorrect and the rest) are not reported; "
                 "its identity values are in Packaged App Accounts. User names the hive a row "
                 "came from; full paths are in the located-at list. Tested on lonewolf_win10: 12 "
                 "rows, the 9 named values and 3 Server Cache entries, and User held one value on "
                 "every row. The OneNote hives of af_case2_win10, pc_mus_001_win11, "
                 "szechuan_win10 (3) and alihadi_challenge3_win81 (2) hold no values (0 rows). "
                 "Not exercised: a user with more than one notebook, and any image but "
                 "lonewolf_win10 with OneNote values.",
        "paths": ('*/AppData/Local/Packages/Microsoft.Office.OneNote_*/Settings/settings.dat*',),
        "output_types": "standard",
        "artifact_icon": "book",
        "sample_data": {
            "lonewolf_win10": "Windows 10 1709 build 16299 | 12 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (hive holds no values)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (hive holds no values)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (hives hold no values)",
            "alihadi_challenge3_win81": "Windows 8.1 build 9600 | 0 rows (hives hold no values)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no file matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no file matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 SP1 build 7601 | 0 rows (no file matches the declared paths)",
            "windows11_arm_parallels": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
        },
    },
}

import fnmatch

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_app_settings import HIVE_ERRORS, keys, open_settings, package_hives, settings

_OFFICE = 'LocalState\\HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\16.0'

# (package family, app, ((key path pattern, value name patterns), ...)), compared without case.
# A key path pattern is an fnmatch pattern, so * there also matches a backslash.
ACCOUNT_VALUES = (
    ('Microsoft.WindowsStore', 'Microsoft Store', (
        ('LocalState', ('HasUserSignedInBefore_StoreSetting',)),
        ('LocalState\\Identity', ('SignedOut',)),
        ('LocalState\\Identity\\CachedAccounts', ('*',)),
        ('LocalState\\Identity\\CachedProviders', ('*',)),
        ('LocalState\\Identity\\CachedIdentities\\*', ('FirstName', 'LastName', 'Provider',
                                                      'IsDefault')),
        ('LocalState\\MODiscoveryDatabase', ('MoBillingMsaId',)),
        ('LocalState\\configuration\\Service', (
            'LastSignedInUserSignInName', 'LastSignedInUserCid', 'LastSignedInUserId',
            'LastSignedInUserFirstName', 'LastSignedInUserLastName',
            'LastSignedInUserAccountLocale', 'LastSignInAccountRegion',
            'UserExplicitlySignedOut')),
    )),
    ('Microsoft.Office.OneNote', 'OneNote', (
        (_OFFICE + '\\Common\\Identity', ('ConnectedAccountCID', 'OneNotePrimaryAccountCID',
                                          'OneNoteConnectedAccountCID')),
        (_OFFICE + '\\Common\\Identity\\Identities\\*', ('*',)),
    )),
    ('Microsoft.SkypeApp', 'Skype', (
        ('LocalState\\SkypeHost', ('LastSignInName', 'LastSkypeName', 'MSAWebAccountId',
                                   'PrimaryDeviceMsa', 'IsUWPAppSignedIn',
                                   'IsLegacyAppSignedIn')),
        ('LocalState\\*', ('MSASkypeName', 'MSACIDHEX', 'SMSWebAccountId')),
    )),
    ('Microsoft.MicrosoftSkyDrive', 'OneDrive', (
        ('LocalState', ('CameraBackupAccountEmailKey', 'CameraBackupAccountIdKey',
                        'recent_account_id')),
    )),
)

ONENOTE_GENERAL = _OFFICE + '\\OneNote\\General'
ONENOTE_SERVER_CACHE = _OFFICE + '\\Common\\Internet\\Server Cache'
ONENOTE_NAMES = ('ActiveNotebook', 'ShareCurrentNotebook', 'ShareCurrentSection',
                 'ShareCurrentSectionPath', 'ShareCurrentPage', 'ShareQuickNotebook',
                 'ShareQuickSection', 'ShareRecentSections', 'LastMyDocumentsPathUsed')
UTF16_READ = 'bytes read as UTF-16LE text, parts split at NUL joined with " | "'


def _wanted(rules, key_path, name):
    key_path, name = key_path.lower(), name.lower()
    for key_pattern, names in rules:
        if fnmatch.fnmatchcase(key_path, key_pattern.lower()) and \
                any(fnmatch.fnmatchcase(name, pattern.lower()) for pattern in names):
            return True
    return False


@artifact_processor
def packagedAppAccounts(context):
    data_headers = (
        ('Value Written', 'datetime'),
        ('Key Last Written', 'datetime'),
        'App',
        'Setting',
        'Value',
        'Type',
        'Key',
        'Package',
        'User',
    )
    label = 'Packaged App Accounts'
    data_list = []
    sources = []
    for family, app, rules in ACCOUNT_VALUES:
        for path, relative, package, user in package_hives(context, family):
            rows = []
            try:
                reg = open_settings(path, context)
                for key_path, key, key_written in keys(reg):
                    for name, setting in settings(key).items():
                        if not _wanted(rules, key_path, name):
                            continue
                        if setting.error:
                            logfunc(f'{label}: {relative}: {key_path}\\{name} not decoded, '
                                    f'reported as stored: {setting.error}')
                        rows.append((setting.written, key_written, app, name, setting.text(),
                                     setting.type_name, key_path, package, user))
            except HIVE_ERRORS as ex:
                logfunc(f'{label}: could not read {relative}: {ex}')
                continue
            sources.append(path)
            rows.sort(key=lambda r: (r[6].lower(), r[3].lower()))
            data_list.extend(rows)
    return data_headers, data_list, '\n'.join(sources)


def _utf16_parts(data):
    """The bytes as UTF-16LE text split at NUL, or None when they are not clean UTF-16LE."""
    if len(data) % 2:
        return None
    try:
        text = data.decode('utf-16-le')
    except UnicodeDecodeError:
        return None
    return ' | '.join(part for part in text.split('\x00') if part)


@artifact_processor
def oneNoteNotebookSettings(context):
    data_headers = (
        ('Value Written', 'datetime'),
        ('Key Last Written', 'datetime'),
        'Setting',
        'Value',
        'Read As',
        'Type',
        'Key',
        'User',
    )
    label = 'OneNote Notebook Settings'
    wanted = {name.lower() for name in ONENOTE_NAMES}
    data_list = []
    sources = []
    for path, relative, _package, user in package_hives(context, 'Microsoft.Office.OneNote'):
        rows = []
        try:
            reg = open_settings(path, context)
            for key_path, key, key_written in keys(reg):
                lowered = key_path.lower()
                if lowered == ONENOTE_GENERAL.lower():
                    for name, setting in settings(key).items():
                        if name.lower() not in wanted:
                            continue
                        value, read_as = setting.text(), 'as stored'
                        if setting.type_name == 'UInt8Array' and not setting.error:
                            text = _utf16_parts(bytes(setting.value))
                            if text is not None:
                                value, read_as = text, UTF16_READ
                        if setting.error:
                            logfunc(f'{label}: {relative}: {key_path}\\{name} not decoded, '
                                    f'reported as stored: {setting.error}')
                        rows.append((setting.written, key_written, name, value, read_as,
                                     setting.type_name, key_path, user))
                elif lowered.startswith(ONENOTE_SERVER_CACHE.lower() + '\\') and \
                        '\\' not in key_path[len(ONENOTE_SERVER_CACHE) + 1:]:
                    rows.append(('', key_written, 'Server Cache entry',
                                 key_path[len(ONENOTE_SERVER_CACHE) + 1:],
                                 'key name as stored', 'Key', key_path, user))
        except HIVE_ERRORS as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        sources.append(path)
        rows.sort(key=lambda r: (r[6].lower(), r[2].lower(), r[3].lower()))
        data_list.extend(rows)
    return data_headers, data_list, '\n'.join(sources)
