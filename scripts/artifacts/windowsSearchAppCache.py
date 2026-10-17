"""Windows Search DeviceSearchCache app cache files for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the AppCache<number>.txt files in each user's
AppData/Local/Packages/<search package>/LocalState/DeviceSearchCache folder: a
JSON array with one object per app, each property stored as an object with a
Value and a Type. Sources are in the notes.
"""

__artifacts_v2__ = {
    "windowsSearchAppCache": {
        "name": "Windows Search App Cache",
        "description": "Apps in the Windows Search app cache of each user, with the times-used count and date-accessed time the cache stores for each, from the DeviceSearchCache AppCache files.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows Search",
        "notes": "Reads the AppCache<number>.txt files in each user's AppData/Local/Packages/Microsoft.Windows.Search_<id>/LocalState/DeviceSearchCache folder, and in the Microsoft.Windows.Cortana_<id> package folder that holds it on older builds: on the tested images the Cortana folder on builds 16299 and 17763 (lonewolf_win10, af_case2_win10, alihadi_threatsim_server2019) and the Search folder on builds 19041 and 20348 (szechuan_win10, ou_ransomware_server2022). Each file is a JSON array with one object per app, each property stored as an object holding a Value and a Type; Type is not reported. User is the folder after Users in the path, so each user's files are read separately, and Source File names the file a row came from. The files are successive snapshots: the number in the file name is read as a Windows FILETIME, as WinSearchAppCache describes it (https://github.com/dfirdetective/WinSearchAppCache/blob/0bf8a0aacbdd488c5974ad8d6d57f022962fa568/README.md?plain=1#L11), and First Snapshot and Last Snapshot are the earliest and latest such times among the files of the same folder that hold the row's values; of the 311 non-zero DateAccessed values in the 43 tested files, 309 were at or before the time in their own file's name and 2 were 46 seconds or less after it. A row whose values repeat unchanged in several files of one folder is reported once: Snapshots counts the files that hold it, In Newest Snapshot says whether the folder's newest file holds it, and Source File names the newest file that holds it. A file that is not a JSON array is named in the run log and not read; none on the tested images. Not read: SettingsCache.txt in the same folder, whose entries on the tested images carried Settings page properties (System.Setting.*, System.HighKeywords, System.Comment) and no use count or access time. pc_mus_001_win11 and hexordia_mvs2025_win11 held a DeviceSearchCache folder only in the windows.immersivecontrolpanel_<id> package, with a SettingsCache.txt and no AppCache file, so both report 0 rows. One row per app entry with a non-zero System.Software.TimesUsed, a non-zero System.DateAccessed or at least one jump list item; entries with none of the three are not reported and the run log counts them per folder (af_case2_win10 170, alihadi_threatsim_server2019 61, lonewolf_win10 84, ou_ransomware_server2022 90, szechuan_win10 2,736 across 37 files). Each column after the times is the property of the matching name, as stored: Item Name Display (System.ItemNameDisplay), Parsing Name (System.ParsingName), Encoded Target Path (System.Tile.EncodedTargetPath), File Name (System.FileName), File Extension (System.FileExtension), Kind (System.Kind), Item Type (System.ItemType), Product Version (System.Software.ProductVersion), Identity (System.Identity) and Package Full Name (System.AppUserModel.PackageFullName). Microsoft documents System.DateAccessed as the last time the item was accessed (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/properties/props-system-dateaccessed.md?plain=1#L11), and its property reference has no page for System.Software.TimesUsed, System.Tile.EncodedTargetPath or System.ConnectedSearch.JumpList; how Windows Search fills these properties in this cache is not documented in the sources cited here. In the tested files no File Name ended with its File Extension on the 1,988 entries whose File Extension began with a period, which differs from Microsoft's description of System.FileName as including its extension (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/properties/props-system-filename.md?plain=1#L11). Date Accessed is System.DateAccessed read as a FILETIME, 100-nanosecond intervals since 1601-01-01 UTC, blank when it is 0; in the tested files every non-zero value was written as a JSON number in floating-point form (311 of 311), so Date Accessed (as stored) keeps the text as written and the time is only as precise as that text. That the value is a UTC FILETIME is measured: of 47 rows on af_case2_win10, lonewolf_win10, ou_ransomware_server2022 and szechuan_win10 whose Encoded Target Path file name matched, ignoring case, the program file name of a UserAssist entry of the same user that had a last executed time (Windows UserAssist), 37 had a Date Accessed equal to that time to the millisecond, 9 an earlier one and 1 a later one. Times Used is System.Software.TimesUsed as stored; what it counts is not established. On those 37 rows it equalled the UserAssist run count 11 times, was lower 15 times and higher 11 times, and WinSearchAppCache reports it did not match Prefetch run counts (https://github.com/dfirdetective/WinSearchAppCache/blob/0bf8a0aacbdd488c5974ad8d6d57f022962fa568/README.md?plain=1#L25). Jump List Items is the number of items in the entry's System.ConnectedSearch.JumpList, listed in Windows Search App Cache Jump Lists; the two artifacts fold repeated values separately, so the items counted here need not equal the rows there. Absence of an app here is not evidence it was not run, and a Times Used of 0 is not evidence it never was. Measured: af_case2_win10 17 rows from 2 files; lonewolf_win10 24 from 1; ou_ransomware_server2022 35 from 2 files of 2 users (Administrator 18, admin 17); szechuan_win10 52 from 37 files of 4 users (11, 6, 15 and 20 rows); alihadi_threatsim_server2019 0, every entry of its one file having Times Used 0, Date Accessed 0 and no jump list item. Kind held program on every row of the four images with rows. On af_case2_win10 and lonewolf_win10, each with one user, User held one value and First Snapshot, Last Snapshot, Snapshots and In Newest Snapshot each held one value, every row being in both of af_case2_win10's files and lonewolf_win10 having one file; on ou_ransomware_server2022, whose two users have one file each, Snapshots held 1 and In Newest Snapshot Yes on every row and First Snapshot equalled Last Snapshot, and User and Source File name the same split there.",
        "paths": (
            '*/AppData/Local/Packages/Microsoft.Windows.Search_*/LocalState/DeviceSearchCache/AppCache*.txt',
            '*/AppData/Local/Packages/Microsoft.Windows.Cortana_*/LocalState/DeviceSearchCache/AppCache*.txt',
        ),
        "output_types": "standard",
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 17 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (1 AppCache file, no entry with a use count, access time or jump list item)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no AppCache file; DeviceSearchCache holds only SettingsCache.txt)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 24 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 35 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no AppCache file; DeviceSearchCache holds only SettingsCache.txt)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 52 rows",
        },
    },
    "windowsSearchAppCacheJumpLists": {
        "name": "Windows Search App Cache Jump Lists",
        "description": "Items listed in the jump list field of each app in the Windows Search app cache of each user, with the item name, path, description and the date stored with it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows Search",
        "notes": "Reads the AppCache<number>.txt files in each user's AppData/Local/Packages/Microsoft.Windows.Search_<id>/LocalState/DeviceSearchCache folder, and in the Microsoft.Windows.Cortana_<id> package folder that holds it on older builds: on the tested images the Cortana folder on builds 16299 and 17763 (lonewolf_win10, af_case2_win10, alihadi_threatsim_server2019) and the Search folder on builds 19041 and 20348 (szechuan_win10, ou_ransomware_server2022). Each file is a JSON array with one object per app, each property stored as an object holding a Value and a Type; Type is not reported. User is the folder after Users in the path, so each user's files are read separately, and Source File names the file a row came from. The files are successive snapshots: the number in the file name is read as a Windows FILETIME, as WinSearchAppCache describes it (https://github.com/dfirdetective/WinSearchAppCache/blob/0bf8a0aacbdd488c5974ad8d6d57f022962fa568/README.md?plain=1#L11), and First Snapshot and Last Snapshot are the earliest and latest such times among the files of the same folder that hold the row's values; of the 311 non-zero DateAccessed values in the 43 tested files, 309 were at or before the time in their own file's name and 2 were 46 seconds or less after it. A row whose values repeat unchanged in several files of one folder is reported once: Snapshots counts the files that hold it, In Newest Snapshot says whether the folder's newest file holds it, and Source File names the newest file that holds it. A file that is not a JSON array is named in the run log and not read; none on the tested images. Not read: SettingsCache.txt in the same folder, whose entries on the tested images carried Settings page properties (System.Setting.*, System.HighKeywords, System.Comment) and no use count or access time. pc_mus_001_win11 and hexordia_mvs2025_win11 held a DeviceSearchCache folder only in the windows.immersivecontrolpanel_<id> package, with a SettingsCache.txt and no AppCache file, so both report 0 rows. One row per item in the System.ConnectedSearch.JumpList value of an app entry, a JSON array of groups, each with a Type and an Items list, and some with a Name; each item carries Name, Path, Description and Type, and some carry Date and Points. App Item Name Display and App Parsing Name are the entry's System.ItemNameDisplay and System.ParsingName. Item Name, Item Path and Item Description are the item's Name, Path and Description as stored. Date (as stored) is the item's Date text, a calendar date with no time or zone in the tested files, and is not converted. Group Type (as stored), Group Name, Item Type (as stored) and Points (as stored) are the group's Type and Name and the item's Type and Points; Microsoft's property reference has no page for System.ConnectedSearch.JumpList, so their meanings are not established, and WinSearchAppCache offers hypotheses for the types and for Points (https://github.com/dfirdetective/WinSearchAppCache/blob/0bf8a0aacbdd488c5974ad8d6d57f022962fa568/README.md?plain=1#L40-L53). The items are what the cache stored for the app; this artifact does not establish when or by whom an item was opened. Measured: af_case2_win10 16 rows; lonewolf_win10 29; ou_ransomware_server2022 44 (Administrator 23, admin 21); szechuan_win10 37 (6, 8, 14 and 9 rows for its 4 users); alihadi_threatsim_server2019 0, no entry of its file holding a jump list item. Group Name was blank on every row of szechuan_win10 and af_case2_win10. On af_case2_win10 and lonewolf_win10 User, First Snapshot, Last Snapshot, Snapshots and In Newest Snapshot each held one value; on ou_ransomware_server2022 Snapshots held 1 and In Newest Snapshot Yes on every row and First Snapshot equalled Last Snapshot, and User and Source File name the same split there.",
        "paths": (
            '*/AppData/Local/Packages/Microsoft.Windows.Search_*/LocalState/DeviceSearchCache/AppCache*.txt',
            '*/AppData/Local/Packages/Microsoft.Windows.Cortana_*/LocalState/DeviceSearchCache/AppCache*.txt',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "list",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 16 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (1 AppCache file, no entry with a use count, access time or jump list item)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no AppCache file; DeviceSearchCache holds only SettingsCache.txt)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 29 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 44 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no AppCache file; DeviceSearchCache holds only SettingsCache.txt)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 37 rows",
        },
    },
}

import datetime
import decimal
import json
import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc

_WINDOWS_EPOCH = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)
_FILE_NAME = re.compile(r'^AppCache(\d+)\.txt$')


def _filetime(value):
    """A FILETIME, 100-nanosecond intervals since 1601-01-01 UTC, as a datetime.

    `value` is an int or the text of a JSON number. Returns '' for a missing,
    zero, negative or out of range value.
    """
    if value is None or isinstance(value, bool):
        return ''
    try:
        ticks = int(decimal.Decimal(str(value)))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return ''
    if ticks <= 0:
        return ''
    try:
        return _WINDOWS_EPOCH + datetime.timedelta(microseconds=ticks // 10)
    except OverflowError:
        return ''


def _value(entry, name):
    """The Value of one property, or None when the entry does not carry it."""
    prop = entry.get(name)
    if isinstance(prop, dict):
        return prop.get('Value')
    return None


def _text(value):
    if value is None:
        return ''
    return str(value)


def _user(relative):
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() == 'users':
            return parts[index + 1]
    return ''


def _snapshots(context, label):
    """[(folder, user, [(file name time, path, relative, entries)])], one per cache folder.

    A file whose name does not end in a number, that is not a JSON array, or
    that cannot be read, is logged and left out.
    """
    folders = {}
    for found in context.get_files_found():
        path = str(found)
        if not os.path.isfile(path):
            continue
        match = _FILE_NAME.match(os.path.basename(path))
        if not match:
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                text = handle.read().decode('utf-8-sig').rstrip('\x00 \r\n\t')
            entries = json.loads(text, parse_float=str)
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        if not isinstance(entries, list):
            logfunc(f'{label}: {relative} is not a JSON array; not read')
            continue
        folder = os.path.dirname(relative.replace('\\', '/'))
        snapshot = (_filetime(int(match.group(1))), path, relative,
                    [entry for entry in entries if isinstance(entry, dict)])
        folders.setdefault(folder, []).append(snapshot)
    out = []
    for folder in sorted(folders):
        seen, files = set(), []
        for item in sorted(folders[folder], key=lambda item: (_number(item[2]), item[2])):
            if item[2] not in seen:
                seen.add(item[2])
                files.append(item)
        out.append((folder, _user(folder), files))
    return out


def _number(relative):
    match = _FILE_NAME.match(relative.replace('\\', '/').rsplit('/', 1)[-1])
    return int(match.group(1)) if match else 0


def _jump_list(entry):
    """The groups of System.ConnectedSearch.JumpList, parsed from its JSON text, or []."""
    value = _value(entry, 'System.ConnectedSearch.JumpList')
    if not value:
        return []
    try:
        groups = json.loads(value, parse_float=str) if isinstance(value, str) else value
    except ValueError:
        return None
    return groups if isinstance(groups, list) else None


def _fold(states):
    """Rows from (state, snapshot time, relative path, newest) tuples, one per distinct state.

    Returns (state, first snapshot, last snapshot, number of files holding the
    state, in newest snapshot, newest file holding the state) in the order each state was first seen.
    """
    order, held, files = [], {}, {}
    for state, when, relative, newest in states:
        if state not in held:
            held[state] = [when, when, 0, False, relative]
            files[state] = set()
            order.append(state)
        record = held[state]
        record[1] = when
        if relative not in files[state]:
            files[state].add(relative)
            record[2] += 1
        record[3] = record[3] or newest
        record[4] = relative
    return [(state,) + tuple(held[state]) for state in order]


@artifact_processor
def windowsSearchAppCache(context):
    label = 'Windows Search App Cache'
    data_list = []
    sources = []
    for _folder, user, files in _snapshots(context, label):
        states = []
        newest = files[-1][2] if files else ''
        skipped = 0
        for when, path, relative, entries in files:
            sources.append(path)
            for entry in entries:
                times_used = _value(entry, 'System.Software.TimesUsed')
                accessed = _value(entry, 'System.DateAccessed')
                groups = _jump_list(entry)
                if groups is None:
                    logfunc(f'{label}: {relative}: a jump list value is not a JSON array; '
                            f'its item count is blank')
                items = '' if groups is None else sum(
                    len(group.get('Items') or []) for group in groups if isinstance(group, dict))
                used = isinstance(times_used, int) and not isinstance(times_used, bool) and times_used > 0
                if not used and not _filetime(accessed) and not items:
                    skipped += 1
                    continue
                state = (
                    _text(accessed),
                    _text(times_used),
                    _text(_value(entry, 'System.ItemNameDisplay')),
                    _text(_value(entry, 'System.ParsingName')),
                    _text(_value(entry, 'System.Tile.EncodedTargetPath')),
                    _text(_value(entry, 'System.FileName')),
                    _text(_value(entry, 'System.FileExtension')),
                    _text(_value(entry, 'System.Kind')),
                    _text(_value(entry, 'System.ItemType')),
                    _text(_value(entry, 'System.Software.ProductVersion')),
                    _text(_value(entry, 'System.Identity')),
                    _text(_value(entry, 'System.AppUserModel.PackageFullName')),
                    items,
                )
                states.append((state, when, relative, relative == newest))
        if skipped:
            logfunc(f'{label}: {_folder}: {skipped} entries with Times Used 0, Date Accessed 0 '
                    f'and no jump list items not reported')
        for state, first, last, count, in_newest, relative in _fold(states):
            accessed, times_used = state[0], state[1]
            data_list.append((_filetime(accessed), first, last, accessed,
                              int(times_used) if times_used.lstrip('-').isdigit() else times_used)
                             + state[2:] + (count, 'Yes' if in_newest else 'No', user, relative))
    data_headers = (('Date Accessed', 'datetime'), ('First Snapshot', 'datetime'),
                    ('Last Snapshot', 'datetime'), 'Date Accessed (as stored)', 'Times Used',
                    'Item Name Display', 'Parsing Name', 'Encoded Target Path', 'File Name',
                    'File Extension', 'Kind', 'Item Type', 'Product Version', 'Identity',
                    'Package Full Name', 'Jump List Items', 'Snapshots', 'In Newest Snapshot',
                    'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsSearchAppCacheJumpLists(context):
    label = 'Windows Search App Cache Jump Lists'
    data_list = []
    sources = []
    for _folder, user, files in _snapshots(context, label):
        states = []
        newest = files[-1][2] if files else ''
        for when, path, relative, entries in files:
            sources.append(path)
            for entry in entries:
                groups = _jump_list(entry)
                if not groups:
                    continue
                app = (_text(_value(entry, 'System.ItemNameDisplay')),
                       _text(_value(entry, 'System.ParsingName')))
                for group in groups:
                    if not isinstance(group, dict):
                        continue
                    for item in group.get('Items') or []:
                        if not isinstance(item, dict):
                            continue
                        state = (
                            _text(item.get('Date')),
                        ) + app + (
                            _text(item.get('Name')),
                            _text(item.get('Path')),
                            _text(item.get('Description')),
                            _text(group.get('Type')),
                            _text(group.get('Name')),
                            _text(item.get('Type')),
                            _text(item.get('Points')),
                        )
                        states.append((state, when, relative, relative == newest))
        for state, first, last, count, in_newest, relative in _fold(states):
            data_list.append(state[:1] + (first, last) + state[1:]
                             + (count, 'Yes' if in_newest else 'No', user, relative))
    data_headers = ('Date (as stored)', ('First Snapshot', 'datetime'),
                    ('Last Snapshot', 'datetime'), 'App Item Name Display', 'App Parsing Name',
                    'Item Name', 'Item Path', 'Item Description', 'Group Type (as stored)',
                    'Group Name', 'Item Type (as stored)', 'Points (as stored)', 'Snapshots',
                    'In Newest Snapshot', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
