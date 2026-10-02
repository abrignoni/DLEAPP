"""Windows Open With list parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the OpenWithList key of each file extension under
Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts in each user's NTUSER.DAT: the program names the
key's lettered values hold, in the order its MRUList value gives.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive, open_key,
                                      user_from_path)

_LABEL = 'Open With List'
_FILEEXTS = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts'
_LIST = 'openwithlist'


__artifacts_v2__ = {
    "openWithList": {
        "name": "Open With List",
        "description": "Programs listed in the OpenWithList key of each file extension in NTUSER.DAT, in the order "
                       "the key's MRUList value gives, with the key's last written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads each NTUSER.DAT the paths match with python-registry: every key named OpenWithList (name "
                 "compared without case) below a subkey of "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts. Each text value of such a key other "
                 "than MRUList is one row: Extension is the name of the subkey the key sits under, Value the value's "
                 "name and Program its data, as stored. Order is the position of the value's name in the key's "
                 "MRUList value, 1 for the first. libyal's Windows Registry knowledge base lists "
                 "FileExts\\%EXTENSION%\\OpenWithList among the keys with a MRUList value, as 'Most recently used "
                 "\"Open With\" commands' on Windows 2000, XP and Vista, and describes MRUList as the value names in "
                 "order of use, the most recently used first (libyal, 'Most recently used (MRU)', "
                 "https://github.com/libyal/winreg-kb/blob/d572cf86269bd3aa393f5eb73932aec181283838/docs/sources/explorer-keys/Most-recently-used.md#L11-L18, "
                 "https://github.com/libyal/winreg-kb/blob/d572cf86269bd3aa393f5eb73932aec181283838/docs/sources/explorer-keys/Most-recently-used.md#L32). "
                 "Eric Zimmerman's FileExts registry plugin lists the key's values in MRUList order; its comments "
                 "say the key 'contains values with name == char and value data of an executable name' and that "
                 "'there is an MRUList that contains the order the executables were selected' "
                 "(https://github.com/EricZimmerman/RegistryPlugins/blob/c16219db698f7ee66fbd97de7ec5d17fc10bdf8e/RegistryPlugin.FileExts/FileExts.cs#L81-L108). "
                 "A value MRUList does not name has a blank Order and follows the named ones; a name in MRUList that "
                 "the key holds no value for gives no row and is counted in the run log, and a name MRUList repeats "
                 "is used once. None of these occurred on the tested hives, where the MRUList of each of the 58 keys "
                 "with values names each of the key's values once and nothing else; they were exercised only by "
                 "constructed keys in the unit tests. Key Last Written (UTC) is the OpenWithList key's last-written "
                 "time, the same on the rows of one key, so no row has a time of its own. User is the folder after "
                 "Users in the hive's path. Tested on four public images (af_case2_win10, build 17763; "
                 "lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which "
                 "gave 6, 11, 6 and 4 rows from 4, 8, 5 and 4 keys, and on one capture of a Windows 11 build 26200 "
                 "machine (windows11_arm_known_20261001), which gave 55 rows from 37 keys; the other capture holds "
                 "no NTUSER.DAT. The tested hives hold 1,253 OpenWithList keys, and the 1,195 with no value give no "
                 "row. Of the 58 keys with values, 38 hold one program and 20 two or more, 4 at most. User held one "
                 "value on af_case2_win10, lonewolf_win10, pc_mus_001_win11 and the capture, each with one hive that "
                 "has rows; szechuan_win10 has rows for 2 users, and Order held one value, 1, on its 4 rows. On the "
                 "82 rows Program is a file name ending .exe on 63 (NOTEPAD.EXE, HxD.exe and kleopatra.exe among "
                 "those of the public images), a name with an exclamation mark on 16 (such as "
                 "Microsoft.Windows.Photos_8wekyb3d8bbwe!App) and a GUID in braces, a backslash and a file name on 3 "
                 "({F38BF404-1D43-42F2-9305-67DE0B28FC23}\\Explorer.exe). Value is one lower case letter on every "
                 "row, every tested value is REG_SZ and every Extension begins with a period. What adds a value to "
                 "the key was not tested here: no known data was made for it. A row records that the hive lists the "
                 "program for the extension in this key; it does not show which file was opened, and the key has one "
                 "time for all its values. 30 of the 58 keys with values sit beside a UserChoice key for the same "
                 "extension (see Default App User Choices). The OpenWithList key was written more than a second "
                 "after that key on 28 of the 30, within a second of it on 1 and more than a second before it on 1. "
                 "A hive that cannot be read is named in the run log and skipped; every tested hive was read. "
                 "Reading the hive needs the python-registry package. A dirty hive, one whose base block's two "
                 "sequence numbers differ, is read after the entries in its .LOG1 and .LOG2 transaction logs that "
                 "continue its sequence are applied, following Maxim Suhanov's 'Windows registry file format "
                 "specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason. 3 tested hives were replayed, one each on "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10. Rows follow the hives in the order the tool "
                 "found them and, within a hive, the extensions in the order the hive lists them. Not read: the "
                 "OpenWithProgids and UserChoice subkeys of the same FileExts keys (Default App User Choices reads "
                 "the second).",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 6 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 11 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 6 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 55 rows",
        },
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "list",
    },
}


def list_rows(key, user, extension):
    """One row per text value of an OpenWithList key other than MRUList, in the order MRUList gives.

    Returns (rows, value names MRUList lists that the key does not hold). A value MRUList does not list has a
    blank Order and follows the listed ones; a name MRUList repeats is used once.
    """
    written = key_written_utc(key)
    order, programs = '', {}
    for value in key.values():
        data = value.value()
        if value.name().lower() == 'mrulist':
            order = data if isinstance(data, str) else ''
        elif isinstance(data, str):
            programs[value.name()] = data
    rows, missing, listed = [], [], set()
    for position, name in enumerate(order, 1):
        if name in programs:
            rows.append((written, user, extension, position, name, programs.pop(name)))
        elif name not in listed:
            missing.append(name)
        listed.add(name)
    rows.extend((written, user, extension, '', name, program) for name, program in programs.items())
    return rows, missing


def extension_rows(fileexts, user):
    """The rows of every OpenWithList key under the subkeys of a FileExts key, and how many names had no value."""
    rows, missing = [], 0
    for extension in fileexts.subkeys():
        for sub in extension.subkeys():
            if sub.name().lower() == _LIST:
                found, absent = list_rows(sub, user, extension.name())
                rows.extend(found)
                missing += len(absent)
    return rows, missing


@artifact_processor
def openWithList(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'Extension', 'Order', 'Value', 'Program')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in found_hives(context, 'NTUSER.DAT'):
        relative_source = context.get_relative_path(source)
        try:
            fileexts = open_key(open_hive(source, context), _FILEEXTS)
            rows, missing = ([], 0) if fileexts is None else extension_rows(fileexts, user_from_path(relative_source))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative_source}: {exc}')
            continue
        if missing:
            logfunc(f'{_LABEL}: MRUList values of {relative_source} list {missing} value name(s) their key does not hold')
        sources.append(source)
        data_list.extend(rows)
    return data_headers, data_list, '\n'.join(sources)
