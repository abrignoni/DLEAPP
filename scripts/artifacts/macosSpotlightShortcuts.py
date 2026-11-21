"""Spotlight shortcuts per user on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSpotlightShortcuts": {
        "name": "Spotlight Shortcuts",
        "description": "Entries in each user's Spotlight shortcuts file: the stored query string, "
                       "the display name and URL recorded for it, and its LAST_USED time. One row is "
                       "one entry in one file. A file holds one entry per distinct query string, so a "
                       "row is not one search.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Spotlight (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were developed independently, using the file "
                 "format, measured data and Apple's code. Tested files: one each from "
                 "magnet2021_macos_bigsur and mvs2026_macbookpro_macos15. Code statements below were read "
                 "in SPShortcuts and SPQueryTask in Spotlight.framework on macOS 27.2.1 (26B131), and its "
                 "record methods were run in memory with synthetic inputs; they say nothing about the "
                 "code of another macOS version. The artifact reads four file locations under any Library "
                 "folder: Library/Application Support/com.apple.spotlight.Shortcuts, Library/Application "
                 "Support/com.apple.spotlight/com.apple.spotlight.Shortcuts, "
                 "com.apple.spotlight.Shortcuts.v3 in that same folder, and Library/Group "
                 "Containers/group.com.apple.spotlight/com.apple.spotlight.Shortcuts.v3. mac_apt's comments "
                 "assign them to macOS 10.10 to 10.14, 10.15, 11 to 13 (marked with a question mark) and 14 "
                 "and later "
                 "(https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L76-L82). "
                 "On 27.2.1 the code loads and writes the Group Containers file, reads the Application "
                 "Support .v3 file once to migrate it and then deletes it, and only deletes the other two; "
                 "none of the tested images holds those two, so their format is not established. The code "
                 "also deletes com.apple.spotlight.Shortcuts.v2 in that folder, which the artifact does "
                 "not read. Each tested file is an XML property list holding one dictionary. On 27.2.1 the "
                 "code lowercases the query string before using it as the key, and every key in the tested "
                 "files is lowercase. A later write for the same lowercased string replaces the entry, so "
                 "a row is not an event. Whether Query String matches the keystrokes entered is not "
                 "established. Rows are sorted newest Last Used first, because the file's own order is a "
                 "key sort with no time meaning. Display Name is DISPLAY_NAME. URL is URL as stored: the "
                 "code writes the result's file path when it has one and otherwise its identifier, so the "
                 "value need not be a URL. Last Used (UTC) is LAST_USED, which the 27.2.1 code sets to the "
                 "current time when it records the entry in memory. The file is written later. In one "
                 "narrow case the code skips the record on a repeat use, so it need not be the latest use. "
                 "When the dictionary holds 250 or more entries and a new string arrives, the code keeps "
                 "the newest 200 and adds the new one, and other code paths also remove entries, so a "
                 "missing entry does not show that a search never happened. Any other key of an entry is "
                 "listed in Other Keys as 'key: value', with dates as ISO 8601 UTC text and data as hex. "
                 "The code writes IDENTIFIER for Core Spotlight results and reads PATH, whose meaning is "
                 "not established; no tested file held either, so Other Keys was empty on every tested "
                 "row. The UserShortcuts dictionary in Library/Preferences/com.apple.spotlight.plist, which "
                 "mac_apt reads for macOS 10.9 and older "
                 "(https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L58-L63 "
                 "and "
                 "https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L77) "
                 "is not read. When a logical extraction holds the same file under Users/, "
                 "System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical copy "
                 "is not read again, and an entry that both of two differing copies hold is reported once; "
                 "both are counted in the run log. User is the folder after Users in the source path, or "
                 "root under private/var/root, and is blank when the input is one user's home folder whose "
                 "path names no user. User held one value on every row of each tested image. User does not "
                 "separate the files a row can come from, since the artifact reads four locations under a "
                 "Library folder and both copies of a file that differs between two captures, so Source "
                 "File stays.",
        "paths": ('*/Library/Application Support/com.apple.spotlight.Shortcuts',
                  '*/Library/Application Support/com.apple.spotlight/com.apple.spotlight.Shortcuts',
                  '*/Library/Application Support/com.apple.spotlight/com.apple.spotlight.Shortcuts.v3',
                  '*/Library/Group Containers/group.com.apple.spotlight/com.apple.spotlight.Shortcuts.v3'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 5 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 6 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter
from datetime import datetime

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, canonical_relative, load_plist, unique_sources, user_from_path

_KNOWN = ('DISPLAY_NAME', 'LAST_USED', 'URL')


def _as_text(value):
    """A plist value as text for the Other Keys column."""
    if isinstance(value, datetime):
        return as_utc(value).isoformat()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    return str(value)


def _text(value):
    return value if isinstance(value, str) else ('' if value is None else _as_text(value))


@artifact_processor
def macosSpotlightShortcuts(context):
    data_headers = (('Last Used (UTC)', 'datetime'), 'Query String', 'Display Name', 'URL',
                    'Other Keys', 'User', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    seen = set()
    files = [path for path in context.get_files_found() if not os.path.isdir(path)]
    paths, _skipped = unique_sources(context, files, label='Spotlight Shortcuts')
    for path in paths:
        relative = context.get_relative_path(path)
        plist = load_plist(path)
        if not isinstance(plist, dict):
            problems['files that are not a property list holding a dictionary'] += 1
            continue
        user = user_from_path(relative)
        before = len(data_list)
        for query, entry in plist.items():
            if not isinstance(entry, dict):
                problems['top-level values that are not an entry dictionary'] += 1
                continue
            others = '\n'.join(f'{key}: {_as_text(value)}' for key, value in entry.items()
                               if key not in _KNOWN)
            row = (as_utc(entry.get('LAST_USED')), query, _text(entry.get('DISPLAY_NAME')),
                   _text(entry.get('URL')), others)
            key = (canonical_relative(relative),) + tuple(str(value) for value in row)
            if key in seen:
                problems['entries the other capture of the same file also holds, not reported again'] += 1
                continue
            seen.add(key)
            data_list.append(row + (user, relative))
        if len(data_list) > before:
            read.append(path)
    # The file's own order is a key sort, so newest first, entries without a time last.
    data_list.sort(key=lambda row: (row[1], row[5], row[6]))
    data_list.sort(key=lambda row: row[0].timestamp() if isinstance(row[0], datetime) else float('-inf'),
                   reverse=True)
    if problems:
        logfunc('Spotlight Shortcuts: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    logfunc(f'Spotlight Shortcuts: {len(data_list)} entr(ies).')
    return data_headers, data_list, '\n'.join(read)
