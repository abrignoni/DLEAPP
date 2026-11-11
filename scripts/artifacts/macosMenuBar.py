__artifacts_v2__ = {
    "macosMenuBarStatusItems": {
        "name": "macOS Menu Bar Status Items",
        "description": "NSStatusItem keys of a user's systemuiserver and controlcenter preferences on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Menu Bar (macOS)",
        "notes": (
            "One row per item per file, for each item named by an NSStatusItem key of a user's "
            "com.apple.systemuiserver.plist or com.apple.controlcenter.plist. The keys read 'NSStatusItem "
            "Visible <item>', 'NSStatusItem VisibleCC <item>' and 'NSStatusItem Preferred Position <item>'. The"
            ' split into those words and an item name is read from the key text, not from Apple documentation, '
            'and what each value does is not sourced here. Visible, Visible CC and Preferred Position are the '
            'values of those keys as stored. A key with other words after NSStatusItem is listed whole, with '
            'its value, in Other NSStatusItem Keys on a row of its own. Other NSStatusItem Keys held no value '
            'on any row of the five tested images. Visible CC held no value on any row of four images: only the'
            ' macOS 26.2 image held those keys. Preferred Position held no value on any row of the two macOS '
            '11.2.1 images. Other preference files can hold the same keys and are not read. On the Magnet macOS'
            ' 11.2.1 image two other preference files (com.apple.Spotlight and com.apple.TextInputMenuAgent) '
            'each held one NSStatusItem Visible key. On the macOS 15.4 image those two and com.apple.Passwords '
            'each held one. The other three images were not searched. User is the folder after Users in the '
            'path, root under private/var/root, otherwise blank. User held one value on every row of each '
            'tested image. When a logical extraction holds the same file under System/Volumes/Data/ or '
            'System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read again and the run log '
            'counts it. When the views hold different bytes but give the same row, the row is reported once and'
            ' Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Preferences/com.apple.systemuiserver.plist',
                  '*/Library/Preferences/com.apple.controlcenter.plist'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "menu",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 13 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 11 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 19 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 11 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 10 rows",
        },
    },
    "macosMenuExtras": {
        "name": "macOS Menu Extras",
        "description": "Entries of the menuExtras list in a user's systemuiserver preferences on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Menu Bar (macOS)",
        "notes": (
            "One row per entry of the menuExtras list of a user's com.apple.systemuiserver.plist, as stored. "
            "Position is the entry's place in the list, counted from 0. What writes the list and when is not "
            'sourced here. Three of the five tested images held the list, with one or two entries. User is the '
            'folder after Users in the path, root under private/var/root, otherwise blank. User held one value '
            'on every row of each image with rows. When a logical extraction holds the same file under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read '
            'again and the run log counts it. When the views hold different bytes but give the same row, the '
            'row is reported once and Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Preferences/com.apple.systemuiserver.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "menu",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 2 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (the file holds no menuExtras key)",
            "evidencelocker_macos14": "macOS 14.6.1 | 1 row",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (the file holds no menuExtras key)",
            "adams_macbookpro_macos26": "macOS 26.2 | 1 row",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor
from scripts.macos_plists import fold_view_rows, load_plist, unique_sources, user_from_path

_FILES = ('com.apple.systemuiserver.plist', 'com.apple.controlcenter.plist')
_PREFIX = 'NSStatusItem '
# The words after NSStatusItem that are split into their own column; the item name follows them.
_KINDS = (('Visible ', 'visible'), ('VisibleCC ', 'visible_cc'), ('Preferred Position ', 'position'))


def _text(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, float):
        return repr(value)
    return '' if value is None else str(value)


def _plists(context, names, label):
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) in names]
    paths, _skipped = unique_sources(context, found, label=label)
    for path in paths:
        plist = load_plist(path)
        if isinstance(plist, dict):
            yield path, plist


@artifact_processor
def macosMenuBarStatusItems(context):
    data_headers = ('Item', 'Visible', 'Visible CC', 'Preferred Position', 'Other NSStatusItem Keys', 'User',
                    'Source File')
    rows, read = [], []
    for path, plist in _plists(context, _FILES, 'macOS Menu Bar Status Items'):
        items, other = {}, []
        for key in plist:
            if not isinstance(key, str) or not key.startswith(_PREFIX):
                continue
            rest = key[len(_PREFIX):]
            for words, column in _KINDS:
                if rest.startswith(words):
                    items.setdefault(rest[len(words):], {})[column] = _text(plist[key])
                    break
            else:
                other.append(f'{key} = {_text(plist[key])}')
        if not items and not other:
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for item in sorted(items):
            values = items[item]
            rows.append((item, values.get('visible', ''), values.get('visible_cc', ''), values.get('position', ''),
                         '', user, relative))
        if other:
            rows.append(('', '', '', '', '\n'.join(sorted(other)), user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosMenuExtras(context):
    data_headers = ('Menu Extra', 'Position', 'User', 'Source File')
    rows, read = [], []
    for path, plist in _plists(context, _FILES[:1], 'macOS Menu Extras'):
        extras = plist.get('menuExtras')
        if not isinstance(extras, list):
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for position, extra in enumerate(extras):
            rows.append((_text(extra), position, user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
