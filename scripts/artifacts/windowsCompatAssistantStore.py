"""Windows Program Compatibility Assistant Store parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Compatibility Assistant\\Store key of each user's NTUSER.DAT, under
Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags. Each value of
the key is named for a program and is one row: the user, the value's name and
the key's last written time. The value data is not decoded: the time it holds
was measured against Prefetch and UserAssist and is not a time the program
ran (see notes).
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive,
                                      open_key, user_from_path)

_LABEL = 'Compatibility Assistant Store'
_STORE = (r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags"
          r"\Compatibility Assistant\Store")

__artifacts_v2__ = {
    "compatibilityAssistantStore": {
        "name": "Compatibility Assistant Store",
        "description": "Programs named by the values of each user's Compatibility Assistant Store key in NTUSER.DAT, "
                       "with the user and the key's last written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from each user's NTUSER.DAT, named in the report's located-at line. Each value of "
                 "Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Compatibility Assistant\\Store is one "
                 "row. Program is the value's name, as stored. User is the folder after Users in the hive's path. "
                 "Key Last Written (UTC) is the last-written time of the Store key, so every row of one hive shares "
                 "it and no row has a time of its own. The AppCompatFlags2 plugin in Eric Zimmerman's "
                 "RegistryPlugins lists the value names of the same key (Hyun Yi, 'AppCompatFlags2', "
                 "https://github.com/EricZimmerman/RegistryPlugins/blob/c16219db698f7ee66fbd97de7ec5d17fc10bdf8e/RegistryPlugin.AppCompatFlags2/AppCompatFlags2.cs#L78-L85). "
                 "No source for what makes Windows add a value was found; the measurements that follow are what was "
                 "established. The tested hives give 10, 26, 35 and 15 rows on af_case2_win10, lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10, from 1, 1, 1 and 4 user hives, and 91 on "
                 "windows11_arm_known_20261001, the NTUSER.DAT of a Windows 11 build 26200 ARM64 virtual machine "
                 "saved with reg.exe on 1 October 2026; on each public image one more user hive holds no Store key. "
                 "Of the 177 names, 138 are a path on a drive letter, each ending in .exe, 33 are a UNC path, all on "
                 "the capture, and 6 begin SIGN.MEDIA= followed by a hexadecimal number, a space and a path with no "
                 "drive; what that number identifies was not established. On the four public images 71 of the 86 "
                 "names have a Prefetch row for the same executable name (see Prefetch), and of the 79 names on "
                 "drive C the image holds a file at that path for 57, so the image need not hold a file at the path "
                 "a name gives. On 6 of the 7 user hives of those images Key Last Written (UTC) is within 7 seconds "
                 "of a Prefetch run time of a program the key names, within 0.1 second on 4 of them, and on the "
                 "seventh the nearest is 143 seconds earlier. Each value's data is binary, begins with the bytes "
                 "SACP and is not decoded. The eight bytes at byte 44 read as a FILETIME that is one date on every "
                 "value of af_case2_win10, lonewolf_win10 and szechuan_win10 and one of two dates on "
                 "pc_mus_001_win11 and on the capture. For the 125 values whose program has a Prefetch or UserAssist "
                 "time, that FILETIME is earlier than every one of those times, by 178 days or more on the public "
                 "images. It is the same on unrelated programs and earlier than their recorded runs, so it is not "
                 "reported as a time the program ran; what it records was not established. Key Last Written (UTC) "
                 "and User held one value on every row of af_case2_win10, lonewolf_win10, pc_mus_001_win11 and the "
                 "capture, where one user hive holds the key. Not read: the Layers and Compatibility "
                 "Assistant\\Persisted keys beside it, which hold no value in any tested user hive. A row records "
                 "that the key of that user's hive holds a value named for the program; it does not by itself show "
                 "that the user ran the program, or when. Reading the hive needs the python-registry package. A "
                 "dirty hive, one whose base block's two sequence numbers differ, is read after the entries in its "
                 ".LOG1 and .LOG2 transaction logs that continue its sequence are applied, following Maxim Suhanov's "
                 "'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "package",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 91 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 35 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 26 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 15 rows",
        },
    },
}


def store_rows(key, user):
    """One row per value of a Store key: the key's last written time, the user and the value's name."""
    written = key_written_utc(key)
    return [(written, user, value.name()) for value in key.values()]


@artifact_processor
def compatibilityAssistantStore(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'Program')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in found_hives(context, 'NTUSER.DAT'):
        relative_source = context.get_relative_path(source)
        try:
            key = open_key(open_hive(source, context), _STORE)
            rows = [] if key is None else store_rows(key, user_from_path(relative_source))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        data_list.extend(rows)

    return data_headers, data_list, '\n'.join(sources)
