"""Spotlight shortcuts per user on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSpotlightShortcuts": {
        "name": "Spotlight Shortcuts",
        "description": "Entries in each user's Spotlight shortcuts file: the typed text each "
                       "entry is keyed by, the display name and URL stored with it, and the time "
                       "it was last used.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Spotlight (macOS)",
        "notes": "Reads the Spotlight shortcuts file in each home folder at four locations: "
                 "Library/Application Support/com.apple.spotlight.Shortcuts, Library/Application "
                 "Support/com.apple.spotlight/com.apple.spotlight.Shortcuts, "
                 "com.apple.spotlight.Shortcuts.v3 in that same folder, and Library/Group "
                 "Containers/group.com.apple.spotlight/com.apple.spotlight.Shortcuts.v3. These are four of "
                 "the locations mac_apt reads, whose comments assign them to macOS 10.10 to 10.14, 10.15, "
                 "11 to 13 (marked with a question mark) and 14 and later "
                 "(https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L76-L82). "
                 "Each file is a property list whose keys each hold an entry, and the artifact reports one "
                 "row per entry in the file's order. Sarah Edwards describes the file as holding what was "
                 "typed into the Spotlight search window, what was clicked on, and when "
                 "(https://www.mac4n6.com/blog/2017/7/19/script-update-mac-mru-parser-spotlight-shortcuts-blob-parsing), "
                 "and her macMRU parser reads DISPLAY_NAME, LAST_USED and URL under each key "
                 "(https://github.com/mac4n6/macMRU-Parser/blob/14a1257e0e48f68d42a752910181589b7d755774/macMRU.py#L641-L662) "
                 "of the file in Library/Application Support "
                 "(https://github.com/mac4n6/macMRU-Parser/blob/14a1257e0e48f68d42a752910181589b7d755774/macMRU.py#L684); "
                 "mac_apt reports the key as typed text "
                 "(https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L44-L55). "
                 "Typed Text is the key, Display Name is DISPLAY_NAME, URL is URL as stored, and Last Used "
                 "(UTC) is LAST_USED, a property list date, which the tested file writes in UTC with a "
                 "trailing Z. Any other key of an entry is listed in Other Keys (as stored) as 'key: "
                 "value'; mac_apt also reads a key named IDENTIFIER "
                 "(https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L49), "
                 "which no tested file held, so Other Keys (as stored) was empty on every tested row. The "
                 "UserShortcuts dictionary that mac_apt reads from "
                 "Library/Preferences/com.apple.spotlight.plist for macOS 10.9 and older "
                 "(https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L58-L63 "
                 "and "
                 "https://github.com/ydkhatri/mac_apt/blob/0edb4cd4f2ca4675f0d2ce02a9700bc32f7db43f/plugins/spotlightshortcuts.py#L77) "
                 "is not read. On the public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15"
                 ") the Group Containers file held 6 entries, last used 2025-11-20 to "
                 "2025-12-12, each keyed by text that begins its display name or a word of it, ignoring "
                 "case, with two keys holding the same URL; all 6 rows come from one home folder, so User "
                 "held one value on all 6 rows. A private sample from macOS 26.6 held 13 entries with the "
                 "same three keys, including one keyed by an empty string whose URL is not a file path and "
                 "two whose key begins no word of the display name, so Typed Text and URL are reported as "
                 "stored. dleapp_macos_bigsur holds no file at any of the four locations. When a logical "
                 "extraction holds the same file under Users/ and under System/Volumes/Data/Users/, a "
                 "byte-identical second copy is not read again, and an entry that both of two differing "
                 "copies hold is reported once; both are counted in the run log. User is the folder after "
                 "Users in the source path, or root under private/var/root, and is blank when the input is "
                 "one user's home folder whose path names no user. User does not separate the files a row "
                 "can come from, since the artifact reads four locations in each home folder and both "
                 "copies of a file that differs between two captures, so Source File stays.",
        "paths": ('*/Library/Application Support/com.apple.spotlight.Shortcuts',
                  '*/Library/Application Support/com.apple.spotlight/com.apple.spotlight.Shortcuts',
                  '*/Library/Application Support/com.apple.spotlight/com.apple.spotlight.Shortcuts.v3',
                  '*/Library/Group Containers/group.com.apple.spotlight/com.apple.spotlight.Shortcuts.v3'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
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
    data_headers = (('Last Used (UTC)', 'datetime'), 'Typed Text', 'Display Name', 'URL',
                    'Other Keys (as stored)', 'User', 'Source File')
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
        for typed, entry in plist.items():
            if not isinstance(entry, dict):
                problems['top-level values that are not an entry dictionary'] += 1
                continue
            others = '\n'.join(f'{key}: {_as_text(value)}' for key, value in entry.items()
                               if key not in _KNOWN)
            row = (as_utc(entry.get('LAST_USED')), typed, _text(entry.get('DISPLAY_NAME')),
                   _text(entry.get('URL')), others)
            key = (canonical_relative(relative),) + tuple(str(value) for value in row)
            if key in seen:
                problems['entries the other capture of the same file also holds, not reported again'] += 1
                continue
            seen.add(key)
            data_list.append(row + (user, relative))
        if len(data_list) > before:
            read.append(path)
    if problems:
        logfunc('Spotlight Shortcuts: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    logfunc(f'Spotlight Shortcuts: {len(data_list)} entr(ies).')
    return data_headers, data_list, '\n'.join(read)
