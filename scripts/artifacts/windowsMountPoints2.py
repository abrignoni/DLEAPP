"""Explorer MountPoints2 volume and share entries per user, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "mountPoints2": {
        "name": "MountPoints2",
        "description": "Volumes and network shares recorded under the Explorer MountPoints2 "
                       "key in each NTUSER.DAT, with each entry's key last-written time and "
                       "any stored label.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-27",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the subkeys of Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2"
                 " in each NTUSER.DAT. A name in braces is typed Volume GUID, a name beginning ## "
                 "Network share, and anything else Other. Share Path rewrites a ## name with the "
                 "leading ## as \\\\ and each other # as \\; on szechuan_win10, the public DFIR Madness "
                 "'Stolen Szechuan Sauce' image, the one such entry rewritten "
                 "this way equals the same user's mapped drive RemotePath and Map Network Drive MRU "
                 "value. The CPC subkey is not reported; on the four tested images it held only an empty "
                 "Volume subkey. Label is _LabelFromReg, or "
                 "_LabelFromDesktopINI when that is absent or empty. Label is empty on every row "
                 "of the four tested images, where the only such values are two empty _LabelFromDesktopINI "
                 "strings on af_case2_win10 and one on szechuan_win10. Key "
                 "Last Written is when the subkey was last written, which is not established as when "
                 "the volume or share was attached or used. Volume GUIDs are not resolved to drive "
                 "letters or devices here. On af_case2_win10, lonewolf_win10 and pc_mus_001_win11 every "
                 "reported entry is a Volume GUID and comes from the one user hive holding the key, so Type "
                 "and User each hold one value there and Share Path is empty; on szechuan_win10 the 6 rows "
                 "are 5 Volume GUIDs and 1 Network share, the only row with a Share Path, and come from 3 of "
                 "the 4 user hives holding the key, so User holds three values there."
                 " A dirty hive, one whose base block's two sequence numbers differ, is read after the "
                 "entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are applied, "
                 "following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay "
                 "that would give a key an earlier last-written time than the hive already holds, a check "
                 "added here beyond the specification; the run log names each hive replayed, with the "
                 "sequence numbers applied, and each dirty hive read as it is, with the reason.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 6 rows",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive, open_key,
                                      user_from_path, value_of)

_MP2 = r'Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2'


def _entry(name):
    """(type, share path) for a MountPoints2 subkey name."""
    if name.startswith('##'):
        return 'Network share', '\\\\' + name[2:].replace('#', '\\')
    if name.startswith('{') and name.endswith('}'):
        return 'Volume GUID', ''
    return 'Other', ''


def _label(key):
    for name in ('_LabelFromReg', '_LabelFromDesktopINI'):
        label = value_of(key, name)
        if label:
            return label
    return ''


@artifact_processor
def mountPoints2(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Entry', 'Type', 'Share Path',
                    'Label', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('MountPoints2: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        try:
            root = open_key(open_hive(path, context), _MP2)
            for entry in (root.subkeys() if root else []):
                if entry.name() == 'CPC':
                    continue
                kind, share = _entry(entry.name())
                data_list.append((key_written_utc(entry), entry.name(), kind, share,
                                  _label(entry), user, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'MountPoints2: could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
