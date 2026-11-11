__artifacts_v2__ = {
    "macosLoginWindowRelaunchApps": {
        "name": "macOS Apps To Relaunch At Login",
        "description": "Entries of the TALAppsToRelaunchAtLogin list in a user's ByHost loginwindow preferences on "
                       "macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Login Window (macOS)",
        "notes": (
            "One row per entry of the TALAppsToRelaunchAtLogin list of a user's "
            'Library/Preferences/ByHost/com.apple.loginwindow.<id>.plist. Bundle ID, Path, Hide and Background '
            "State are the entry's BundleID, Path, Hide and BackgroundState values as stored. Other Values "
            "holds any other key of the entry as JSON. Position is the entry's place in the list, counted from "
            '0. What writes the list, when, and what Hide and Background State mean are not sourced here: a row'
            ' shows that the list named the app, not when the app ran. Hide held one value on every row of the '
            'three images with rows (false), and Background State held one value on every row of those images '
            '(2). Other Values held no value on any row. User is the folder after Users in the path, root under'
            ' private/var/root, otherwise blank. User held one value on every row of each image with rows. When'
            ' a logical extraction holds the same file under System/Volumes/Data/ or '
            'System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read again and the run log '
            'counts it. When the views hold different bytes but give the same row, the row is reported once and'
            ' Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Preferences/ByHost/com.apple.loginwindow.*.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (the one ByHost file found holds no keys)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (the one ByHost file found holds no keys)",
            "evidencelocker_macos14": "macOS 14.6.1 | 2 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 6 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 4 rows",
        },
    },
    "macosLoginWindowUserPreferences": {
        "name": "macOS Login Window User Preferences",
        "description": "Top-level keys and values of a user's loginwindow preferences files on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Login Window (macOS)",
        "notes": (
            "One row per top-level key of a user's Library/Preferences/com.apple.loginwindow.plist and "
            'Library/Preferences/ByHost/com.apple.loginwindow.<id>.plist, with the key name as stored and no '
            'interpretation of what a key means. Value Type is the plist type. Dates are shown as UTC ISO 8601 '
            'text, reals as stored, arrays and dictionaries as JSON text, and data values as a byte count only.'
            ' Only boolean and string values occurred on the tested images; the other types were not exercised.'
            ' TALAppsToRelaunchAtLogin is left out because the macOS Apps To Relaunch At Login artifact reports'
            ' it. A file outside a user folder, such as the system-wide '
            '/Library/Preferences/com.apple.loginwindow.plist that macOS System Information reads, is not '
            'reported. On the five tested images the rows came from four key names (MiniBuddyLaunch, '
            'TALLogoutReason, TALLogoutSavesState, oneTimeSSMigrationComplete) and no ByHost file held a key '
            'other than TALAppsToRelaunchAtLogin. User is the folder after Users in the path, root under '
            'private/var/root, otherwise blank. User held one value on every row of three images; the macOS '
            '15.4 and 26.2 images also held a row for root. When a logical extraction holds the same file under'
            ' System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read '
            'again and the run log counts it. When the views hold different bytes but give the same row, the '
            'row is reported once and Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Preferences/com.apple.loginwindow.plist',
                  '*/Library/Preferences/ByHost/com.apple.loginwindow.*.plist'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 4 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 4 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 4 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 5 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 4 rows",
        },
    },
}

import json
import os
from datetime import datetime

from scripts.ilapfuncs import artifact_processor
from scripts.macos_plists import as_utc, fold_view_rows, load_plist, unique_sources, user_from_path

_RELAUNCH_KEY = 'TALAppsToRelaunchAtLogin'
_ENTRY_KEYS = ('BundleID', 'Path', 'Hide', 'BackgroundState')


def _json_default(value):
    if isinstance(value, datetime):
        return as_utc(value).isoformat()
    if isinstance(value, (bytes, bytearray)):
        return f'({len(value)} bytes)'
    return str(value)


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=_json_default)


def _shown(value):
    """(text, type name) for one preference value; bytes are shown as a byte count only."""
    if isinstance(value, bool):
        return ('true' if value else 'false'), 'boolean'
    if isinstance(value, datetime):
        return as_utc(value).isoformat(), 'date'
    if isinstance(value, (bytes, bytearray)):
        return f'({len(value)} bytes)', 'data'
    if isinstance(value, (dict, list)):
        return _json(value), ('dictionary' if isinstance(value, dict) else 'array')
    if isinstance(value, str):
        return value, 'string'
    if isinstance(value, int):
        return str(value), 'integer'
    if isinstance(value, float):
        return repr(value), 'real'
    return str(value), type(value).__name__


def _is_byhost(relative):
    return relative.replace('\\', '/').split('/')[-2:-1] == ['ByHost']


def _files(context, label, byhost_only):
    found = [str(p) for p in context.get_files_found()
             if os.path.basename(str(p)).startswith('com.apple.loginwindow.')
             and os.path.basename(str(p)).endswith('.plist')]
    paths, _skipped = unique_sources(context, found, label=label)
    return [path for path in paths if not byhost_only or _is_byhost(context.get_relative_path(path))]


@artifact_processor
def macosLoginWindowRelaunchApps(context):
    data_headers = ('Bundle ID', 'Path', 'Hide', 'Background State', 'Other Values', 'Position', 'User',
                    'Source File')
    rows, read = [], []
    for path in _files(context, 'macOS Apps To Relaunch At Login', True):
        plist = load_plist(path)
        if not isinstance(plist, dict) or not isinstance(plist.get(_RELAUNCH_KEY), list):
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for position, entry in enumerate(plist[_RELAUNCH_KEY]):
            if not isinstance(entry, dict):
                rows.append(('', '', '', '', _json(entry), position, user, relative))
                continue
            other = {key: value for key, value in entry.items() if key not in _ENTRY_KEYS}
            rows.append((
                _shown(entry.get('BundleID'))[0] if 'BundleID' in entry else '',
                _shown(entry.get('Path'))[0] if 'Path' in entry else '',
                _shown(entry.get('Hide'))[0] if 'Hide' in entry else '',
                _shown(entry.get('BackgroundState'))[0] if 'BackgroundState' in entry else '',
                _json(other) if other else '',
                position, user, relative,
            ))
    return data_headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosLoginWindowUserPreferences(context):
    data_headers = ('Key', 'Value', 'Value Type', 'User', 'Source File')
    rows, read = [], []
    for path in _files(context, 'macOS Login Window User Preferences', False):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        if not user:
            continue
        plist = load_plist(path)
        if not isinstance(plist, dict):
            continue
        read.append(path)
        for key in sorted(plist):
            if key == _RELAUNCH_KEY:
                continue
            text, kind = _shown(plist[key])
            rows.append((key, text, kind, user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
