__artifacts_v2__ = {
    "macosSafariRecentWebSearches": {
        "name": "Safari Recent Web Searches",
        "description": "Recent web searches Safari keeps in its preferences file on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari",
        "notes": (
            "Reads the RecentWebSearches list of com.apple.Safari.plist. Date is the entry's Date value, a plist "
            "date, shown as UTC. Search String is SearchString as stored. URLs lists the entry's URLs array, one "
            "per line; the entries on the macOS 15.4 and 26.2 images all had it and the entries on the two macOS "
            "11.2.1 images had none, so the URLs column was empty there. What the list keeps and when Safari "
            "drops an entry is not established: the longest list read held 20 entries. User is the folder after "
            "Users in the path, root under private/var/root, otherwise blank; it held one value on every row of "
            "each tested image, which each hold one user's Safari data. When a logical extraction holds the same "
            "file under Users/ and under System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a "
            "byte-identical copy is not read again and the run log counts it, and a row that copies with "
            "different bytes both hold is reported once with every file that held it in Source File. "
        ),
        "paths": ('*/Library/Containers/com.apple.Safari/Data/Library/Preferences/com.apple.Safari.plist',
                  '*/Library/Preferences/com.apple.Safari.plist'),
        "output_types": "standard",
        "artifact_icon": "search",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 5 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (the one com.apple.Safari.plist found holds no RecentWebSearches key)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 7 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 20 rows",
        },
    },
    "macosSafariPreferences": {
        "name": "Safari Preferences",
        "description": "Top-level keys of Safari's preferences file on macOS, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari",
        "notes": (
            "One row per top-level key of com.apple.Safari.plist, in the Safari container and in "
            "Library/Preferences, with the key name and value as stored and no interpretation of what a key "
            "means. Value Type is the plist type. Dates are shown as UTC ISO 8601 text, reals as stored (a real "
            "that Safari uses as a time is not converted), arrays and dictionaries as JSON text, and data values "
            "as a byte count only: their bytes are not shown or decoded. RecentWebSearches is left out because "
            "the Safari Recent Web Searches artifact reports it. User is the folder after Users in the path, root "
            "under private/var/root, otherwise blank; it held one value on every row of each tested image, which "
            "each hold one user's Safari data. When a logical extraction holds the same file under Users/ and "
            "under System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical copy is not "
            "read again and the run log counts it, and a row that copies with different bytes both hold is "
            "reported once with every file that held it in Source File. "
        ),
        "paths": ('*/Library/Containers/com.apple.Safari/Data/Library/Preferences/com.apple.Safari.plist',
                  '*/Library/Preferences/com.apple.Safari.plist'),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 78 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 64 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 1 row",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 100 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 109 rows",
        },
    },
}

import json
import os
from datetime import datetime

from scripts.ilapfuncs import artifact_processor
from scripts.macos_plists import as_utc, fold_view_rows, load_plist, unique_sources, user_from_path

_SEARCHES_KEY = 'RecentWebSearches'


def _plists(context, label):
    """(path, plist dict) for each distinct com.apple.Safari.plist found."""
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'com.apple.Safari.plist']
    paths, _skipped = unique_sources(context, found, label=label)
    for path in paths:
        plist = load_plist(path)
        if isinstance(plist, dict):
            yield path, plist


def _json_default(value):
    if isinstance(value, datetime):
        return as_utc(value).isoformat()
    if isinstance(value, (bytes, bytearray)):
        return f'({len(value)} bytes)'
    return str(value)


def _shown(value):
    """(text, type name) for one preference value; bytes are shown as a byte count only."""
    if isinstance(value, bool):
        return ('true' if value else 'false'), 'boolean'
    if isinstance(value, datetime):
        return as_utc(value).isoformat(), 'date'
    if isinstance(value, (bytes, bytearray)):
        return f'({len(value)} bytes)', 'data'
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=_json_default)
        return text, ('dictionary' if isinstance(value, dict) else 'array')
    if isinstance(value, str):
        return value, 'string'
    if isinstance(value, int):
        return str(value), 'integer'
    if isinstance(value, float):
        return repr(value), 'real'
    return str(value), type(value).__name__


@artifact_processor
def macosSafariRecentWebSearches(context):
    data_headers = (('Date', 'datetime'), 'Search String', 'URLs', 'User', 'Source File')
    rows, read = [], []
    for path, plist in _plists(context, 'Safari Recent Web Searches'):
        searches = plist.get(_SEARCHES_KEY)
        if not isinstance(searches, list):
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for entry in searches:
            if not isinstance(entry, dict):
                continue
            urls = entry.get('URLs')
            urls = '\n'.join(str(u) for u in urls) if isinstance(urls, list) else ''
            term = entry.get('SearchString')
            rows.append((as_utc(entry.get('Date')), term if isinstance(term, str) else '', urls, user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosSafariPreferences(context):
    data_headers = ('Key', 'Value', 'Value Type', 'User', 'Source File')
    rows, read = [], []
    for path, plist in _plists(context, 'Safari Preferences'):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for key in sorted(plist):
            if key == _SEARCHES_KEY:
                continue
            text, kind = _shown(plist[key])
            rows.append((key, text, kind, user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
