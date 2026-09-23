"""Explorer taskbar FeatureUsage counters per user, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "featureUsage": {
        "name": "Taskbar FeatureUsage",
        "description": "Counts under each subkey of the Explorer FeatureUsage key in each "
                       "NTUSER.DAT, with the key's KeyCreationTime value, reported as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads every subkey of "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FeatureUsage in each NTUSER.DAT "
                 "and reports each value in it, with Value Name as stored and Count as its data. Value"
                 " Name is not always an application: on pc_mus_001_win11 TrayButtonClicked holds a "
                 "StartButton value. Feature Key Last Written is that subkey's last-written time, not "
                 "a time for any one value. FeatureUsage Key Creation Time is the FeatureUsage key's "
                 "KeyCreationTime value read as a FILETIME. CrowdStrike's write-up describes the key "
                 "as found from Windows 10 version 1903, KeyCreationTime as when the key was created, "
                 "which it takes to be the account's first interactive logon, and the counts as "
                 "follows: AppLaunch, runs of an application pinned to the taskbar; AppSwitched, "
                 "left-clicks on the taskbar that switched focus to the application; ShowJumpView, "
                 "right-clicks on the application on the taskbar; AppBadgeUpdated, updates to a "
                 "running application's badge icon; TrayButtonClicked, clicks on built-in taskbar "
                 "buttons such as the clock and Start. Those meanings are the write-up's and were not "
                 "tested here. Of the three registered Windows images only pc_mus_001_win11 (build "
                 "22621) has the key, in the user's NTUSER.DAT and not the Default profile's; "
                 "af_case2_win10 (version 1809) and lonewolf_win10 (version 1709) have none. "
                 "FeatureUsage Key Creation Time is one value per NTUSER.DAT, the same on every row "
                 "from that hive, and on pc_mus_001_win11 one hive holds the key, so it and User each "
                 "hold one value there. Reference: Jai Minton (CrowdStrike), 'How to Employ "
                 "FeatureUsage for Windows 10 Taskbar Forensics', "
                 "https://www.crowdstrike.com/en-us/blog/how-to-employ-featureusage-for-windows-10-taskbar-forensics/.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 30 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no FeatureUsage key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no FeatureUsage key)",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, filetime_bytes_utc, filetime_utc, found_hives,
                                      key_written_utc, open_key, user_from_path, value_of)

_FEATURE_USAGE = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage'


def _creation_time(root):
    """The FeatureUsage key's KeyCreationTime value, a FILETIME stored as a REG_QWORD."""
    stored = value_of(root, 'KeyCreationTime')
    if isinstance(stored, int):
        return filetime_utc(stored)
    return filetime_bytes_utc(stored)


@artifact_processor
def featureUsage(context):
    data_headers = (('Feature Key Last Written (UTC)', 'datetime'),
                    ('FeatureUsage Key Creation Time (UTC)', 'datetime'), 'Feature',
                    'Value Name', 'Count', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Taskbar FeatureUsage: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        user = user_from_path(path)
        try:
            root = open_key(Registry.Registry(path), _FEATURE_USAGE)
            created = _creation_time(root) if root is not None else ''
            for feature in (root.subkeys() if root is not None else []):
                written = key_written_utc(feature)
                for value in feature.values():
                    data_list.append((written, created, feature.name(), value.name(),
                                      value.value(), user, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Taskbar FeatureUsage: could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
