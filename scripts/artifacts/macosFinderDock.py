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
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": "Reads each user's ~/Library/Preferences/com.apple.finder.plist. Recent folder rows "
                 "come from FXRecentFolders, with Path, Volume Name and Target Created read from each "
                 "entry's file-bookmark; Go to Folder rows come from GoToField and GoToFieldHistory, "
                 "the Connect to Server row from FXConnectToLastURL, destination rows from "
                 "RecentMoveAndCopyDestinations, and desktop volume rows are the keys of "
                 "FXDesktopVolumePositions as stored. Order is the entry's position in its stored "
                 "list; that it reflects recency is not established. Target Created is the bookmark's "
                 "file creation date item (0x1040), not a time the folder was opened. On "
                 "dleapp_macos_bigsur the file holds 7 FXRecentFolders entries, all with a bookmark "
                 "path and 5 ending in the stored name, and one FXDesktopVolumePositions key, and none"
                 " of the other keys; on the public MacBook Pro logical extraction (macOS 15.4, not a "
                 "registered corpus key) it holds 9 FXRecentFolders entries, one "
                 "RecentMoveAndCopyDestinations entry and 4 FXDesktopVolumePositions keys. All rows on"
                 " each image come from one user's file, so User holds one value there. When a logical"
                 " extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/, a second copy byte-identical to the first is not "
                 "read again, and is counted in the run log. Reference: mac_alias (dmgbuild), "
                 "bookmark.py, "
                 "https://github.com/dmgbuild/mac_alias/blob/d0c076b4562541c1509d9874f42880378245d268/src/mac_alias/bookmark.py#L128-L169.",
        "paths": ('*/Users/*/Library/Preferences/com.apple.finder.plist',),
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
                 " tiles; on the public MacBook Pro logical extraction (macOS 15.4, not a registered "
                 "corpus key) it holds 18 persistent-apps tiles, one persistent-others tile and 3 "
                 "recent-apps tiles, 21 of the 22 with a bundle identifier. All rows on each image "
                 "come from one user, so User holds one value there. When a logical extraction holds "
                 "the same file under Users/ and under System/Volumes/Data/Users/, a second copy "
                 "byte-identical to the first is not read again, and is counted in the run log.",
        "paths": ('*/Users/*/Library/Preferences/com.apple.dock.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "layout-sidebar",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 18 rows",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
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
