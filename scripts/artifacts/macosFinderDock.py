"""Finder recent locations and Dock items per user, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosFinderRecents": {
        "name": "Finder Recent Locations",
        "description": "Recent folders, Go to Folder entries, the last Connect to Server URL, "
                       "move and copy destinations and desktop volume entries in each user's "
                       "com.apple.finder.plist, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-11-12",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": "Reads each user's ~/Library/Preferences/com.apple.finder.plist. Recent folder rows "
                 "come from FXRecentFolders, with Path, Volume Name and Target Created read from each "
                 "entry's file-bookmark; Go to Folder rows come from GoToField and GoToFieldHistory, "
                 "the Connect to Server row from FXConnectToLastURL, destination rows from "
                 "RecentMoveAndCopyDestinations, and desktop volume rows are the keys of "
                 "FXDesktopVolumePositions as stored. The Finder Desktop Volumes artifact "
                 "splits those keys into a volume name and a time decoded from the key suffix. Order is the entry's position in its stored "
                 "list; that it reflects recency is not established. Target Created is the bookmark's "
                 "file creation date item (0x1040), not a time the folder was opened. On "
                 "dleapp_macos_bigsur the file holds 7 FXRecentFolders entries, all with a bookmark "
                 "path and 5 ending in the stored name, and one FXDesktopVolumePositions key, and none"
                 " of the other keys; on the public MacBook Pro logical extraction (macOS 15.4, corpus key "
                 "mvs2026_macbookpro_macos15) it holds 9 FXRecentFolders entries, one "
                 "RecentMoveAndCopyDestinations entry and 4 FXDesktopVolumePositions keys. All rows on"
                 " each image come from one user's file, so User holds one value there. When a logical"
                 " extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/, a second copy byte-identical to the first is not "
                 "read again, and is counted in the run log."
                 " User is the folder after Users in the source path, or root under private/var/root,"
                 " and is blank when the input is one user's home folder whose path names no user, as"
                 " in an acquisition of a single user folder."
                 " Reference: mac_alias (dmgbuild), "
                 "bookmark.py, "
                 "https://github.com/dmgbuild/mac_alias/blob/d0c076b4562541c1509d9874f42880378245d268/src/mac_alias/bookmark.py#L128-L169.",
        "paths": ('*/Library/Preferences/com.apple.finder.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "folder",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 8 rows",
        },
    },
    "macosDockItems": {
        "name": "Dock Items",
        "description": "Applications and other items in each user's Dock, from the "
                       "persistent-apps, persistent-others and recent-apps lists of "
                       "com.apple.dock.plist.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": "Reads the persistent-apps, persistent-others and recent-apps lists of each user's "
                 "~/Library/Preferences/com.apple.dock.plist, one row per tile; Label, Bundle ID and "
                 "URL are the tile's file-label, bundle-identifier and file-data _CFURLString values, "
                 "and Order is its position in the list. /Library/Preferences/com.apple.dock.plist is "
                 "not read. On dleapp_macos_bigsur the user's file holds 17 persistent-apps tiles, "
                 "each with a bundle identifier and URL, one persistent-others tile and no recent-apps"
                 " tiles; on the public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15"
                 ") it holds 18 persistent-apps tiles, one persistent-others tile and 3 "
                 "recent-apps tiles, 21 of the 22 with a bundle identifier. All rows on each image "
                 "come from one user, so User holds one value there. When a logical extraction holds "
                 "the same file under Users/ and under System/Volumes/Data/Users/, a second copy "
                 "byte-identical to the first is not read again, and is counted in the run log."
                 " User is the folder after Users in the source path, or root under private/var/root,"
                 " and is blank when the input is one user's home folder whose path names no user, as"
                 " in an acquisition of a single user folder.",
        "paths": ('*/Library/Preferences/com.apple.dock.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "layout-sidebar",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 18 rows",
        },
    },
    "macosFinderDesktopVolumes": {
        "name": "Finder Desktop Volumes",
        "description": "Entries of FXDesktopVolumePositions in each user's com.apple.finder.plist: the "
                       "volume name and a time decoded from each key, with the stored position values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-12",
        "last_update_date": "2026-11-12",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": (
            "One row per key of FXDesktopVolumePositions in each user's "
            '~/Library/Preferences/com.apple.finder.plist, the Finder preference keyed by volume. On the tested'
            ' images every key (35 of 35) was a volume name, an underscore, and a C99 hexadecimal '
            "floating-point value, for example '<name>_0x1.<hex>p+29'. Volume Name is the key with that suffix "
            'removed, as stored, and Position Key (as stored) is the whole key; a key with no such suffix would'
            ' be kept whole as the name, which no tested image held. Volume Created (UTC) is the suffix read as'
            ' seconds since 2001-01-01 UTC. On four of the five images, 5 of the keys also appear as a '
            "FXRecentFolders bookmark in the same file whose volume name equals the key's name and whose volume"
            ' creation date (bookmark item 0x2013, named kBookmarkVolumeCreationDate in the mac_alias reference'
            ' Finder Recent Locations uses) equals the decoded value to the microsecond; where such a bookmark '
            "exists the decoded value is that volume's creation date, and it is not a mount or access time and "
            'the entry stores no time of its own. For the keys with no matching bookmark the meaning is '
            'measured only by that match, and no Apple source is cited for the key format itself. The 30 filled'
            ' values fall between January 2020 and February 2026. The suffix can be negative: one value, '
            '-978307200, recurred on evidencelocker_macos14 (2 keys) and adams_macbookpro_macos26 (3 keys) and '
            'is 1970-01-01 00:00:00 UTC on this epoch; on adams a same-name bookmark carries that same date. '
            'Volume Created is filled only when the value is between 2001 and 2100, so those rows are blank, '
            'and the suffix stays in Position Key (as stored). One name can appear on several keys with '
            'different suffixes (14 names over 22 keys on evidencelocker_macos14), and two keys with different '
            'names can carry the same suffix, so a decoded time does not identify one volume by itself. Screen '
            "ID, Anchor Relative To, x Relative and y Relative are the key's ScreenID, AnchorRelativeTo, "
            'xRelative and yRelative values as stored; their meaning is not established here, and they are '
            'integers, not times. Screen ID held one value (0) on every tested image. User held one value on '
            "every tested image, each of which has one user's com.apple.finder.plist; Anchor Relative To and x "
            'Relative each held one value on the macOS 15.4 and 26.2 images and varied on '
            'evidencelocker_macos14 (2 and 7 values). The same keys also appear, as stored, as the Desktop '
            'volume entry rows of Finder Recent Locations; this artifact splits and decodes them. User is the '
            'folder after Users in the path, root under private/var/root, otherwise blank. When a logical '
            'extraction holds the file under more than one volume view, a byte-identical copy is read once and '
            'the run log counts it. Measured on magnet2021_macos_bigsur (1 row), dleapp_macos_bigsur (1 row), '
            'evidencelocker_macos14 (22 rows, 2 with no creation time), mvs2026_macbookpro_macos15 (4 rows) and'
            ' adams_macbookpro_macos26 (7 rows, 3 with no creation time).'
        ),
        "paths": ('*/Library/Preferences/com.apple.finder.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 1 row",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "evidencelocker_macos14": "macOS 14.6.1 | 22 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 4 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 7 rows",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
import re
from datetime import datetime, timedelta, timezone

from scripts.macos_plists import bookmark_fields, load_plist, unique_sources, user_from_path


def _text(value):
    return '' if value is None else str(value)


def _finder_rows(plist):
    """(kind, order, name, path, volume name, target created) rows from com.apple.finder.plist."""
    rows = []
    for order, entry in enumerate(plist.get('FXRecentFolders') or []):
        if not isinstance(entry, dict):
            continue
        mark = bookmark_fields(entry.get('file-bookmark')) or {}
        rows.append(('Recent folder (FXRecentFolders)', order, _text(entry.get('name')),
                     mark.get('path', ''), mark.get('volume_name', ''), mark.get('file_created', '')))
    if isinstance(plist.get('GoToField'), str):
        rows.append(('Go to Folder, last entry (GoToField)', '', '', plist['GoToField'], '', ''))
    for order, entry in enumerate(plist.get('GoToFieldHistory') or []):
        rows.append(('Go to Folder history (GoToFieldHistory)', order, '', _text(entry), '', ''))
    if plist.get('FXConnectToLastURL'):
        rows.append(('Connect to Server, last URL (FXConnectToLastURL)', '', '',
                     _text(plist['FXConnectToLastURL']), '', ''))
    for order, entry in enumerate(plist.get('RecentMoveAndCopyDestinations') or []):
        rows.append(('Move or copy destination (RecentMoveAndCopyDestinations)', order, '',
                     _text(entry), '', ''))
    for key in sorted(plist.get('FXDesktopVolumePositions') or {}):
        rows.append(('Desktop volume entry (FXDesktopVolumePositions)', '', _text(key), '', '', ''))
    return rows


@artifact_processor
def macosFinderRecents(context):
    data_headers = ('Kind', 'Order', 'Name', 'Path', 'Volume Name',
                    ('Target Created (UTC, bookmark)', 'datetime'), 'User', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Finder Recent Locations')
    for path in paths:
        relative = context.get_relative_path(path)
        plist = load_plist(path)
        if not isinstance(plist, dict):
            logfunc(f'Finder Recent Locations: could not read {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        data_list.extend(row + (user, relative) for row in _finder_rows(plist))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosDockItems(context):
    data_headers = ('List', 'Order', 'Label', 'Bundle ID', 'URL', 'Tile Type', 'User',
                    'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Dock Items')
    for path in paths:
        relative = context.get_relative_path(path)
        plist = load_plist(path)
        if not isinstance(plist, dict):
            logfunc(f'Dock Items: could not read {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        for section in ('persistent-apps', 'persistent-others', 'recent-apps'):
            for order, tile in enumerate(plist.get(section) or []):
                if not isinstance(tile, dict):
                    continue
                data = tile.get('tile-data') if isinstance(tile.get('tile-data'), dict) else {}
                file_data = data.get('file-data') if isinstance(data.get('file-data'), dict) else {}
                data_list.append((section, order, _text(data.get('file-label')),
                                  _text(data.get('bundle-identifier')),
                                  _text(file_data.get('_CFURLString')), _text(tile.get('tile-type')),
                                  user, relative))
    return data_headers, data_list, '\n'.join(read)


_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
_SANE_START = datetime(2001, 1, 1, tzinfo=timezone.utc)
_SANE_END = datetime(2100, 1, 1, tzinfo=timezone.utc)


# An FXDesktopVolumePositions key ends in '_<hexfloat>', the hexfloat a C99 literal that may be
# negative, e.g. '_0x1.2ceab4ap+29' or '_-0x1.d27e44p+29'.
_VOLUME_SUFFIX = re.compile(r'^(.*)_(-?0x[0-9a-fA-F]+(?:\.[0-9a-fA-F]+)?p[+-]\d+)$')


def _volume_key(key):
    """(volume name, created) from an FXDesktopVolumePositions key '<name>_<hexfloat>'.

    The hexfloat after the last underscore is a C99 floating-point value read as seconds since
    2001-01-01 UTC. The suffix is stripped from the name when it is a hexfloat. Created is filled
    only when that time is in a sane range (2001 to 2100); a value that does not parse or falls
    outside it, such as the recurring negative value equal to 1970-01-01 UTC, leaves Created blank.
    A key with no hexfloat suffix is kept whole as the name.
    """
    match = _VOLUME_SUFFIX.match(key)
    if not match:
        return key, ''
    name = match.group(1)
    try:
        created = _MAC_EPOCH + timedelta(seconds=float.fromhex(match.group(2)))
    except (ValueError, OverflowError, OSError):
        return name, ''
    if not _SANE_START <= created < _SANE_END:
        return name, ''
    return name, created


@artifact_processor
def macosFinderDesktopVolumes(context):
    data_headers = (('Volume Created (UTC)', 'datetime'), 'Volume Name', 'Position Key (as stored)',
                    'Screen ID', 'Anchor Relative To', 'x Relative', 'y Relative', 'User', 'Source File')
    data_list, read = [], []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Finder Desktop Volumes')
    for path in paths:
        relative = context.get_relative_path(path)
        plist = load_plist(path)
        if not isinstance(plist, dict):
            continue
        positions = plist.get('FXDesktopVolumePositions')
        if not isinstance(positions, dict) or not positions:
            continue
        read.append(path)
        user = user_from_path(relative)
        for key in sorted(positions):
            name, created = _volume_key(str(key))
            entry = positions[key] if isinstance(positions[key], dict) else {}
            data_list.append((created, name, str(key), _text(entry.get('ScreenID')),
                              _text(entry.get('AnchorRelativeTo')), _text(entry.get('xRelative')),
                              _text(entry.get('yRelative')), user, relative))
    return data_headers, data_list, '\n'.join(read)
