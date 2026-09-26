"""Windows RecentApps parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Some Windows 10 releases keep, in each user's NTUSER.DAT, a
Software\\Microsoft\\Windows\\CurrentVersion\\Search\\RecentApps key with a subkey per
application (its AppId, AppPath, LaunchCount and LastAccessedTime) and, under some of
those, a RecentItems key with a subkey per file (its Path, DisplayName and
LastAccessedTime). This reads both.
"""

import os

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import filetime_utc, user_from_path

_RECENT_APPS = 'Software\\Microsoft\\Windows\\CurrentVersion\\Search\\RecentApps'

__artifacts_v2__ = {
    "windowsRecentApps": {
        "name": "RecentApps",
        "description": "Applications in each user's RecentApps registry key, with the launch "
                       "count and last accessed time the key stores and the number of recent "
                       "items recorded under each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads Software\\Microsoft\\Windows\\CurrentVersion\\Search\\RecentApps in each user's "
                 "NTUSER.DAT, one row per subkey, the key Velociraptor's Windows.Forensics.RecentApps "
                 "artifact reads; that artifact says the key is populated from Windows 10 1607 to 1709 "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/RecentApps.yaml#L9-L11, "
                 "https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/RecentApps.yaml#L34-L35). "
                 "Phill Moore found the key in base installs of 1607 and 1703 and not of 1507, 1511 or "
                 "1803, with 1709 unconfirmed (Reference: Phill Moore, 'When did RecentApps go?', "
                 "https://thinkdfir.com/2020/10/23/when-did-recentapps-go/). Of the tested images only "
                 "lonewolf_win10, whose SOFTWARE hive records ReleaseId 1709, carried the key, in one "
                 "user's hive, with 21 applications; no NTUSER.DAT on af_case2_win10 (ReleaseId 1809) "
                 "or pc_mus_001_win11 (DisplayVersion 22H2) had it. App ID, App Path and Launch Count "
                 "are the subkey's AppId, AppPath and LaunchCount values as stored, and Last Accessed "
                 "(UTC) is its LastAccessedTime, a FILETIME, a zero shown blank; Velociraptor's "
                 "artifact reads LastAccessedTime as the last execution "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/RecentApps.yaml#L47-L51). "
                 "On lonewolf_win10 every App ID also appeared as a program in the same hive's "
                 "UserAssist key, and Last Accessed and Launch Count equalled that UserAssist entry's "
                 "last execution time and run count on 20 of the 21 applications. On the other, App ID "
                 "windows.immersivecontrolpanel_cw5n1h2txyewy!microsoft.windows.immersivecontrolpanel, "
                 "RecentApps held one launch on 2018-03-27 where UserAssist held three, the last on "
                 "2018-04-06. Recent Items is the number of subkeys of the application's RecentItems "
                 "key, which RecentApps Items reports; 5 of the 21 had any. User is the folder after "
                 "Users in the hive's path and App Key the subkey's name.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["standard"],
        "artifact_icon": "apps",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no NTUSER.DAT holds the RecentApps key)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 21 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no NTUSER.DAT holds the RecentApps key)",
        },
    },
    "windowsRecentAppItems": {
        "name": "RecentApps Items",
        "description": "Files recorded under the RecentItems key of an application in each "
                       "user's RecentApps registry key, with the path, display name and last "
                       "accessed time the key stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the RecentItems key under each application subkey of the RecentApps key that "
                 "the RecentApps artifact reads, one row per subkey. Path and Display Name are its "
                 "Path and DisplayName values as stored, and Last Accessed (UTC) is its "
                 "LastAccessedTime, a FILETIME, a zero shown blank; App ID is the parent application's "
                 "AppId, User is the folder after Users in the hive's path and Item Key the subkey's "
                 "name. Of the tested images only lonewolf_win10 carried the RecentApps key: 14 items "
                 "under 5 applications, whose App IDs are Chrome, "
                 "Microsoft.MicrosoftEdge_8wekyb3d8bbwe!MicrosoftEdge, a path ending in NOTEPAD.EXE, "
                 "Microsoft.Office.POWERPNT.EXE.15 and Microsoft.Office.WINWORD.EXE.15. For each item "
                 "a shortcut named for its Display Name, apostrophes written as underscores, sat in "
                 "the same user's AppData/Roaming/Microsoft/Windows/Recent folder, and Last Accessed "
                 "fell less than a second before that shortcut's modification time on 12 of the 14. On "
                 "the other two the shortcut's modification time was 6.5 seconds before the item's "
                 "time, where the same file's item under the Microsoft Edge App ID matched it, and 31 "
                 "minutes after it. Values not reported: Type, which was 0 on all 14, and Points, a "
                 "4-byte value whose meaning was not established.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["standard"],
        "artifact_icon": "files",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no NTUSER.DAT holds the RecentApps key)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 14 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no NTUSER.DAT holds the RecentApps key)",
        },
    },
}


def _values(key):
    return {value.name(): value.value() for value in key.values()}


def _text(value):
    return value if isinstance(value, str) else ''


def _count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else ''


def _time(value):
    return filetime_utc(value) if isinstance(value, int) else ''


def recent_apps(context, label):
    """Yield (relative hive path, user, app key, app values, item keys) for each application."""
    for source in sorted({str(f) for f in context.get_files_found()}):
        if not os.path.isfile(source) or not source.upper().endswith('NTUSER.DAT'):
            continue
        relative = context.get_relative_path(source)
        try:
            root = Registry.Registry(source).open(_RECENT_APPS)
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        for app in root.subkeys():
            items = []
            for child in app.subkeys():
                if child.name().lower() == 'recentitems':
                    items.extend(child.subkeys())
            yield source, user_from_path(relative), app, _values(app), items


@artifact_processor
def windowsRecentApps(context):
    data_headers = (('Last Accessed (UTC)', 'datetime'), 'App ID', 'App Path', 'Launch Count',
                    'Recent Items', 'User', 'App Key')
    data_list, sources = [], []
    if Registry is None:
        logfunc('RecentApps: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source, user, app, values, items in recent_apps(context, 'RecentApps'):
        data_list.append((_time(values.get('LastAccessedTime')), _text(values.get('AppId')),
                          _text(values.get('AppPath')), _count(values.get('LaunchCount')),
                          len(items), user, app.name()))
        if source not in sources:
            sources.append(source)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0])))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsRecentAppItems(context):
    data_headers = (('Last Accessed (UTC)', 'datetime'), 'Path', 'Display Name', 'App ID',
                    'User', 'Item Key')
    data_list, sources = [], []
    if Registry is None:
        logfunc('RecentApps Items: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source, user, _, values, items in recent_apps(context, 'RecentApps Items'):
        for item in items:
            item_values = _values(item)
            data_list.append((_time(item_values.get('LastAccessedTime')),
                              _text(item_values.get('Path')), _text(item_values.get('DisplayName')),
                              _text(values.get('AppId')), user, item.name()))
            if source not in sources:
                sources.append(source)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0])))
    return data_headers, data_list, '\n'.join(sources)
