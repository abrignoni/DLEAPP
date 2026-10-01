"""Windows user profile list parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the ProfileList key of the SOFTWARE hive, Microsoft\\Windows
NT\\CurrentVersion\\ProfileList, whose subkeys are named for the SIDs that have
a profile on the machine. Each subkey is one row: the SID, the profile's
folder, the times the profile was last loaded and unloaded where the subkey
stores them, and the key's last written time. The values were compared with
the User Profile Service event log of the test images;
sources and measurements are in the notes.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, filetime_utc, found_hives, key_written_utc,
                                      open_hive, open_key, value_of)

_LABEL = 'User Profile List'
_PROFILE_LIST = r"Microsoft\Windows NT\CurrentVersion\ProfileList"

__artifacts_v2__ = {
    "userProfileList": {
        "name": "User Profile List",
        "description": "User profiles listed under the ProfileList key of the SOFTWARE hive, one row per SID, with "
                       "the profile's folder, the times the profile service last loaded and unloaded it where the "
                       "key stores them, and the key's last written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from the SOFTWARE hive, named in the report's located-at line. Each subkey of "
                 "Microsoft\\Windows NT\\CurrentVersion\\ProfileList is one row. SID is the subkey's name and Profile "
                 "Path its ProfileImagePath value, as stored. Profile Load Time (UTC) is read from the subkey's "
                 "LocalProfileLoadTimeHigh and LocalProfileLoadTimeLow values and Profile Unload Time (UTC) from its "
                 "LocalProfileUnloadTimeHigh and LocalProfileUnloadTimeLow values, each pair taken as the high and "
                 "low 32 bits of a FILETIME; a time is blank when either half is absent or is not a number, and when "
                 "the FILETIME is zero or past the year 9999. Microsoft gives these values as tracking the last load "
                 "and the last unload of the profile by the profile service on Windows 10 version 1809, Windows "
                 "Server 2019 and later, and its script joins the halves the same way (Microsoft, 'Scripts: Retrieve "
                 "profile age', "
                 "https://github.com/MicrosoftDocs/SupportArticles-docs/blob/e07fb125ebfac8934278aa3383232f43106c4416/support/windows-server/support-tools/scripts-to-retrieve-profile-age.md#L26-L36, "
                 "https://github.com/MicrosoftDocs/SupportArticles-docs/blob/e07fb125ebfac8934278aa3383232f43106c4416/support/windows-server/support-tools/scripts-to-retrieve-profile-age.md#L65-L74). "
                 "Velociraptor's Windows.Sys.Users artifact reads the same four values as two times (Velociraptor, "
                 "'Windows.Sys.Users', "
                 "https://github.com/Velocidex/velociraptor/blob/74d2e0a9442f93f2ddedeca16436e7499209bcb6/artifacts/definitions/Windows/Sys/Users.yaml#L29-L30, "
                 "https://github.com/Velocidex/velociraptor/blob/74d2e0a9442f93f2ddedeca16436e7499209bcb6/artifacts/definitions/Windows/Sys/Users.yaml#L45-L48). "
                 "Value names are matched without case: the tested hives spell the unload values "
                 "LocalProfileUnloadTime and the Microsoft page LocalProfileUnLoadTime. State (as stored) is the "
                 "subkey's State value, a number in every tested subkey; no source for the meaning of its values was "
                 "found. Key Last Written (UTC) is the subkey's last-written time. The tested hives hold 4, 4, 4 and "
                 "7 subkeys on af_case2_win10, lonewolf_win10, pc_mus_001_win11 and szechuan_win10 and 4 on "
                 "windows11_arm_known_20261001, the SOFTWARE hive of a Windows 11 build 26200 ARM64 virtual machine "
                 "saved with reg.exe on 1 October 2026; each image matched one SOFTWARE hive and each subkey is a "
                 "row, 23 in all. Every hive holds S-1-5-18, S-1-5-19 and S-1-5-20, which Microsoft lists as System, "
                 "LocalService and NetworkService (Microsoft, 'Security identifiers', "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/4b24e83a4f6a988ed454c8d86c6a3bc6c89721bb/WindowsServerDocs/identity/ad-ds/manage/understand-security-identifiers.md#L193-L195). "
                 "None of those 15 subkeys holds a load or unload value, so both times are blank on their rows; on "
                 "13 of the 15 the Profile Path begins with %systemroot%, which is not expanded. The other 8 subkeys "
                 "are named for account SIDs (S-1-5-21-...), 4 on szechuan_win10 and 1 on each other hive, and each "
                 "Profile Path is under C:\\Users; on the four public images the image holds an NTUSER.DAT in that "
                 "folder for all 7. 7 of the 8 hold both times. The one on lonewolf_win10, whose hive gives its "
                 "release as 1709, holds neither, so Profile Load Time (UTC) and Profile Unload Time (UTC) are blank "
                 "on every lonewolf_win10 row. On those 7 the key's last-written time equals the later of the two "
                 "times to the microsecond. For the 6 of them on the public images, the User Profile Service log of "
                 "the same image (see User Profile Service Events) holds an Event ID 1, a logon notification, for "
                 "the SID 6.4 to 394.2 ms before Profile Load Time and an Event ID 3, a logoff notification, 6.1 to "
                 "48.9 ms before Profile Unload Time, each the SID's last such event in the log; those three images' "
                 "active time zone biases are 5 to 8 hours, so the stored times count in UTC. Load is later than "
                 "unload on 3 of the 7: on pc_mus_001_win11 and on one szechuan_win10 profile, where the SID's last "
                 "1 or 3 event is a 1, and on the capture, whose profile is that of the account that ran the capture "
                 "script and whose load time is earlier than the script's first logged step. A comment in "
                 "Microsoft's script says the load time being the latest of the times would most likely indicate a "
                 "profile currently loaded or a machine that crashed "
                 "(https://github.com/MicrosoftDocs/SupportArticles-docs/blob/e07fb125ebfac8934278aa3383232f43106c4416/support/windows-server/support-tools/scripts-to-retrieve-profile-age.md#L131-L134). "
                 "State (as stored) held one value, 0, on every row of four hives; on szechuan_win10 one row holds "
                 "772 and the other 6 hold 0. A row gives a SID and a folder, not an account name, and the times are "
                 "the profile service's record of a load and an unload: they do not say how the account logged on. "
                 "Not reported: the subkeys' Flags, FullProfile, Guid, Migrated, NextLogonCacheable, "
                 "ProfileAttemptedProfileDownloadTimeHigh, ProfileAttemptedProfileDownloadTimeLow, "
                 "ProfileLoadTimeHigh, ProfileLoadTimeLow, RefCount, RunLogonScriptSync and Sid values, and the "
                 "ProfileList key's own Default, ProfilesDirectory, ProgramData and Public values. "
                 "ProfileLoadTimeHigh and ProfileLoadTimeLow are zero in all 8 account subkeys; Sid, binary and "
                 "present in 13 of the 23 subkeys, decodes to the subkey's name in all 13. "
                 "LocalProfileCleanupCheckTimeLow and LocalProfileCleanupCheckTimeHigh, which the Microsoft page "
                 "gives as tracking a cleanup time "
                 "(https://github.com/MicrosoftDocs/SupportArticles-docs/blob/e07fb125ebfac8934278aa3383232f43106c4416/support/windows-server/support-tools/scripts-to-retrieve-profile-age.md#L38-L41), "
                 "are in none of the 23 subkeys and are not read. Reading the hive needs the python-registry "
                 "package. A dirty hive, one whose base block's two sequence numbers differ, is read after the "
                 "entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are applied, following "
                 "Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 4 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 7 rows",
        },
    },
}


def _stored(key, name):
    """The value as stored, or '' when the key has no such value (a stored 0 stays 0)."""
    value = value_of(key, name)
    return '' if value is None else value


def split_filetime(key, name):
    """The time a pair of values, name + 'High' and name + 'Low', stores as the two halves of a
    FILETIME; '' when either half is absent or the time is zero."""
    high, low = value_of(key, name + 'High'), value_of(key, name + 'Low')
    if not isinstance(high, int) or not isinstance(low, int):
        return ''
    return filetime_utc((high << 32) | low)


def profile_row(profile):
    return (key_written_utc(profile), split_filetime(profile, 'LocalProfileLoadTime'),
            split_filetime(profile, 'LocalProfileUnloadTime'), profile.name(),
            _stored(profile, 'ProfileImagePath'), _stored(profile, 'State'))


@artifact_processor
def userProfileList(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), ('Profile Load Time (UTC)', 'datetime'),
                    ('Profile Unload Time (UTC)', 'datetime'), 'SID', 'Profile Path',
                    'State (as stored)')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in found_hives(context, 'SOFTWARE'):
        relative_source = context.get_relative_path(source)
        try:
            key = open_key(open_hive(source, context), _PROFILE_LIST)
            rows = [] if key is None else [profile_row(profile) for profile in key.subkeys()]
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        if key is None:
            logfunc(f'{_LABEL}: {relative_source} has no ProfileList key')
        data_list.extend(rows)

    return data_headers, data_list, '\n'.join(sources)
