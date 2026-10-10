"""Path history 7-Zip keeps in a user's registry hive on Windows, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sevenZipHistory": {
        "name": "7-Zip History",
        "description": "Paths 7-Zip remembers for a Windows user: archive paths from the Add to Archive dialog, "
                       "destination folders from the Extract dialog, and the File Manager's folder history, copy "
                       "destinations, folder shortcuts and panel paths.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "7-Zip",
        "notes": "Reads the path lists 7-Zip keeps under Software\\7-Zip in each user's NTUSER.DAT (Reference: "
                 "7-Zip 25.01, commit 5e96a8279489832924056b1fa82f29d5837c9469, "
                 "'CPP/7zip/UI/Common/ZipRegistry.cpp' line 23 and 'CPP/7zip/UI/FileManager/ViewSettings.cpp' "
                 "line 18, https://github.com/ip7z/7zip). One row is reported per path. List says which list: "
                 "the archive paths of the Add to Archive dialog, the ArcHistory value of the Compression key, "
                 "which the dialog saves when OK is pressed, the path just entered first and then the earlier "
                 "ones, each kept once without regard to case, up to 20 ('CPP/7zip/UI/GUI/CompressDialog.cpp' "
                 "lines 86, 1118 to 1128 and 1235 to 1241; 'ZipRegistry.cpp' lines 273 to 274); the destination "
                 "folders of the Extract dialog, the PathHistory value of the Extraction key, saved the same way "
                 "when OK is pressed ('CPP/7zip/UI/GUI/ExtractDialog.cpp' lines 392 to 408; 'ZipRegistry.cpp' "
                 "lines 120 to 121); and from the FM key of the 7-Zip File Manager, FolderHistory, to whose head "
                 "a folder is moved when a panel opens it, kept to 100 "
                 "('CPP/7zip/UI/FileManager/PanelFolderChange.cpp' line 409; 'App.cpp' lines 980 to 1002), "
                 "CopyHistory, the destinations of copy and move operations with the latest first, kept to 20 "
                 "('App.cpp' lines 754 to 757), FolderShortcuts, and the PanelPath values with the folder each "
                 "panel showed when the File Manager saved its state ('App.cpp' lines 388 to 396; "
                 "'ViewSettings.cpp' lines 27 to 32 and 257 to 305). Position is the place of a path in its "
                 "list, 1 being the first stored, which for the two dialog lists, FolderHistory and CopyHistory "
                 "is the most recent; a panel path has no position. Path is the string as stored. Value is the "
                 "key and value name, and Key Last Written (UTC) is the last-written time of that key, which "
                 "changes when any of its values is written: it is the time of the latest save of that key, not "
                 "a time for each path, and the lists hold no time of their own. User is the folder name under "
                 "Users in the hive's path and Source File is the hive. A list is stored as binary data, UTF-16 "
                 "strings each ended by a zero, and is read as 7-Zip reads it ('CPP/Windows/Registry.cpp' lines "
                 "424 to 472): data that is not a whole number of 16-bit units is not read and anything after "
                 "the last zero is not read, both counted in the run log and tested with constructed input only. "
                 "A path in a list shows that it was entered in that dialog or opened in the File Manager by "
                 "that user; it does not show that an archive was created or that files were extracted, and the "
                 "lists can be cleared. windows11_arm_7zip_known_20261010 is known data from a Windows 11 build "
                 "26200 ARM64 virtual machine with 7-Zip 25.01 that had been used before: an archive was added "
                 "in the Add to Archive dialog, extracted in the Extract dialog, and the File Manager was opened "
                 "on the test folder and closed. In its 33 rows the archive path is position 1 of 2 in the "
                 "archive list, the destination folder is the only extraction path, a list the capture taken "
                 "before the test (windows11_arm_known_20261010, 30 rows) does not have, the test folder is "
                 "position 1 of 27 in the folder history and is the first panel's path, and the Compression, "
                 "Extraction and FM keys were last written inside the recorded time span of the matching step. "
                 "The other 29 rows are earlier use of that machine. User held one value on all 33 rows, the "
                 "capture having one account, and on all 30 rows of each of the two other captures. Not "
                 "exercised: the command-line 7z.exe, the Explorer context menu commands that open no dialog, "
                 "the folder shortcuts, which are empty in the three captures, and versions other than 25.01. "
                 "pc_mus_001_win11 and af_case2_win10 have 7-Zip installed, and one user hive of each has a "
                 "Software\\7-Zip key that holds only the Path and Path64 values, so they give no row. Reading "
                 "the hives requires the python-registry package; a dirty hive is read after its transaction "
                 "logs are applied, and the run log names each.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "archive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no user hive holds one of the lists)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no user hive holds one of the lists)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no user hive holds one of the lists)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no user hive holds one of the lists)",
            "windows11_arm_7zip_known_20261010": "Windows 11 build 26200, 7-Zip 25.01 | 33 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 30 rows",
            "windows11_arm_known_20261010": "Windows 11 build 26200, 7-Zip 25.01 | 30 rows",
        },
    },
}

from collections import Counter

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, key_written_utc, open_hive, open_key, user_from_path

_BASE = 'Software\\7-Zip'
# (List for the row, subkey of Software\7-Zip, value name in lower case): values that hold a list of strings
_LISTS = (
    ('Add to Archive: archive paths', 'Compression', 'archistory'),
    ('Extract: destination folders', 'Extraction', 'pathhistory'),
    ('File Manager: folder history', 'FM', 'folderhistory'),
    ('File Manager: copy destinations', 'FM', 'copyhistory'),
    ('File Manager: folder shortcuts', 'FM', 'foldershortcuts'),
)
_PANEL = ('File Manager: panel path', 'FM', 'panelpath')


def list_strings(raw):
    """The strings of a 7-Zip string list as 7-Zip reads them, and the count of 16-bit units after the last
    terminator, which 7-Zip does not read: UTF-16 little-endian strings, each ended by a zero. None for the list
    when the data is not a whole number of 16-bit units, which 7-Zip refuses."""
    if len(raw) % 2:
        return None, 0
    strings, start = [], 0
    for at in range(0, len(raw), 2):
        if raw[at:at + 2] == b'\x00\x00':
            strings.append(raw[start:at].decode('utf-16-le', errors='backslashreplace'))
            start = at + 2
    return strings, (len(raw) - start) // 2


def history_rows(reg, counts):
    """The rows for one user hive: (key last written, list, position, path, key and value name)."""
    rows = []
    for label, subkey, wanted in _LISTS + (_PANEL,):
        key = open_key(reg, _BASE + '\\' + subkey)
        if key is None:
            continue
        for value in key.values():
            name = value.name()
            place = subkey + '\\' + name
            if (label, subkey, wanted) == _PANEL:
                if name.lower().startswith(wanted) and isinstance(value.value(), str):
                    rows.append((key_written_utc(key), label, '', value.value(), place))
                continue
            if name.lower() != wanted:
                continue
            strings, extra = list_strings(value.raw_data())
            if strings is None:
                counts['lists that are not whole 16-bit units, not read'] += 1
                continue
            if extra:
                counts['16-bit units after the last terminator of a list, not read'] += extra
            rows.extend((key_written_utc(key), label, position, text, place)
                        for position, text in enumerate(strings, 1))
    return rows


@artifact_processor
def sevenZipHistory(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'List', 'Position', 'Path', 'Value', 'User',
                    'Source File')
    data_list, sources, problems = [], [], Counter()
    if Registry is None:
        logfunc('7-Zip History: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'NTUSER.DAT')):
        relative = context.get_relative_path(source)
        try:
            rows = history_rows(open_hive(source, context), problems)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'7-Zip History: could not read {relative}: {exc}')
            continue
        user = user_from_path(relative)
        data_list.extend(row + (user, relative) for row in rows)
        if rows:
            sources.append(source)
    if problems:
        logfunc('7-Zip History: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(sources)
