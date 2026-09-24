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
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the subkeys of Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2"
                 " in each NTUSER.DAT. A name in braces is typed Volume GUID, a name beginning ## "
                 "Network share, and anything else Other. Share Path rewrites a ## name with the "
                 "leading ## as \\\\ and each other # as \\; on the public DFIR Madness 'Stolen Szechuan "
                 "Sauce' image, which is not a registered corpus key, the one such entry rewritten "
                 "this way equals the same user's mapped drive RemotePath and Map Network Drive MRU "
                 "value. The CPC subkey is not reported; on the three registered Windows images it "
                 "held only an empty Volume subkey. Label is _LabelFromReg, or _LabelFromDesktopINI "
                 "when that is absent; no entry on the three registered images carried either. Key "
                 "Last Written is when the subkey was last written, which is not established as when "
                 "the volume or share was attached or used. Volume GUIDs are not resolved to drive "
                 "letters or devices here. On the three registered Windows images every reported entry"
                 " is a Volume GUID and comes from the one user hive holding the key, so Type and User"
                 " each hold one value there and Share Path is empty.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_key,
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
            root = open_key(Registry.Registry(path), _MP2)
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
