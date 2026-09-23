"""Packaged (Store) apps registered per user in the AppX state repository, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsStoreApps": {
        "name": "Store Apps (StateRepository)",
        "description": "Packaged apps registered for each user in StateRepository-Machine.srd, "
                       "with the per-user InstallTime, the package identity and the install "
                       "flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the PackageUser table of StateRepository-Machine.srd, one row per package "
                 "registered for a user, joined to its Package and User rows. Package Name, Version, "
                 "Architecture, Resource ID and Publisher ID are split from PackageFullName in the "
                 "order Microsoft documents for a package full name. User SID is the User table's "
                 "binary SID written as S-R-A-..., and User Profile is the last folder of that SID's "
                 "ProfileImagePath under ProfileList in the SOFTWARE hive; every SID on the three "
                 "registered Windows images resolved. Install Time is PackageUser.InstallTime read as "
                 "a FILETIME in UTC. That reading was checked against the NTFS modification time of "
                 "each package's AppxManifest.xml under Program Files\\WindowsApps, taking each "
                 "package's earliest InstallTime: 83 of 124 comparable packages on pc_mus_001_win11 "
                 "and 62 of 77 on lonewolf_win10 fall within 60 seconds of it, with medians of 8 and 5"
                 " seconds after, while on af_case2_win10 all 79 fall between 4443.7 and 4443.9 hours "
                 "after. What event InstallTime records beyond its name is not established. On "
                 "pc_mus_001_win11 three rows for S-1-5-18 store an InstallTime of 0, so Install Time "
                 "is empty there. Display Name and Publisher Display Name are reported as stored, "
                 "including unresolved ms-resource references (102 of the 215 packages on "
                 "pc_mus_001_win11). IsInbox, IsExplicitlyInstalled and DeploymentState are reported "
                 "as stored; their meanings are not established. On af_case2_win10 and lonewolf_win10 "
                 "every row is for one user and has DeploymentState 2, so User SID, User Profile and "
                 "DeploymentState each hold one value there. Reference: Microsoft, 'An overview of "
                 "Package Identity in Windows apps', "
                 "https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/package-identity-overview.",
        "paths": ('*/ProgramData/Microsoft/Windows/AppRepository/StateRepository-Machine.srd*',
                  '*/Windows/System32/config/SOFTWARE'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "apps",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 220 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 153 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 142 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, get_sqlite_db_records, logfunc
from scripts.windows_registry import Registry, filetime_utc, found_hives, open_key, value_of

_PROFILE_LIST = r'Microsoft\Windows NT\CurrentVersion\ProfileList'

_QUERY = '''
    SELECT pu.InstallTime, p.PackageFullName, p.DisplayName, p.PublisherDisplayName,
           p.IsInbox, pu.IsExplicitlyInstalled, pu.DeploymentState, u.UserSid
    FROM PackageUser pu
    JOIN Package p ON p._PackageID = pu.Package
    LEFT JOIN User u ON u._UserID = pu.User
    ORDER BY pu.InstallTime
'''


def sid_text(blob):
    """A binary SID as S-R-A-S1-S2..., or '' when it cannot be one."""
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 8:
        return ''
    count = blob[1]
    if len(blob) < 8 + 4 * count:
        return ''
    authority = int.from_bytes(blob[2:8], 'big')
    parts = [str(int.from_bytes(blob[8 + 4 * i:12 + 4 * i], 'little')) for i in range(count)]
    return '-'.join(['S', str(blob[0]), str(authority)] + parts)


def _profiles(context):
    """{SID: profile folder name} from ProfileList in every SOFTWARE hive found."""
    profiles = {}
    if Registry is None:
        return profiles
    for hive in found_hives(context, 'SOFTWARE'):
        try:
            root = open_key(Registry.Registry(hive), _PROFILE_LIST)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Store Apps: could not read {context.get_relative_path(hive)}: {exc}')
            continue
        for key in (root.subkeys() if root else []):
            image_path = value_of(key, 'ProfileImagePath')
            if isinstance(image_path, str) and image_path:
                name = image_path.replace('/', '\\').rstrip('\\').rsplit('\\', 1)[-1]
                profiles.setdefault(key.name(), set()).add(name)
    return {sid: ' / '.join(sorted(names)) for sid, names in profiles.items()}


def _identity(full_name):
    """(name, version, architecture, resource id, publisher id) from a package full name."""
    parts = str(full_name or '').split('_')
    return tuple(parts) if len(parts) == 5 else (str(full_name or ''), '', '', '', '')


@artifact_processor
def windowsStoreApps(context):
    data_headers = (('Install Time (UTC)', 'datetime'), 'Package Name', 'Version', 'Architecture',
                    'Resource ID', 'Publisher ID', 'Display Name (as stored)',
                    'Publisher Display Name (as stored)', 'IsInbox (as stored)',
                    'IsExplicitlyInstalled (as stored)', 'DeploymentState (as stored)',
                    'User SID', 'User Profile', 'Source File')
    data_list = []
    read = []
    profiles = _profiles(context)
    for path in context.get_files_found():
        path = str(path)
        if os.path.basename(path) != 'StateRepository-Machine.srd' or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        records = get_sqlite_db_records(path, _QUERY)
        if not records:
            logfunc(f'Store Apps: no package rows read from {relative}')
            continue
        read.append(path)
        for row in records:
            sid = sid_text(row[7])
            data_list.append((filetime_utc(row[0]),) + _identity(row[1]) + (
                row[2] or '', row[3] or '', '' if row[4] is None else row[4],
                '' if row[5] is None else row[5], '' if row[6] is None else row[6],
                sid, profiles.get(sid, ''), relative))
    return data_headers, data_list, '\n'.join(read)
