"""Shared file lists (.sfl2, .sfl3 and .sfl4): recent items, favorites and volumes, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosSharedFileLists": {
        "name": "Shared File Lists (sfl2, sfl3, sfl4)",
        "description": "Items in each user's .sfl2, .sfl3 and .sfl4 shared file lists (recent "
                       "applications, documents and servers, favorites, volumes and per-app "
                       "recent documents), with the path, URL and volume their bookmarks record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Recent Items (macOS)",
        "notes": "Reads the .sfl2, .sfl3 and .sfl4 files under each user's ~/Library/Application "
                 "Support/com.apple.sharedfilelist, including the per-application lists in its "
                 "subfolders, and the same folder under /private/var/root. Each file is an "
                 "NSKeyedArchiver archive, each entry in its items array is one row, and Order is the "
                 "entry's position there. Path, URL, Volume Name, Volume Path and Target Created are "
                 "read from the entry's Bookmark data (items 0x1004, 0x1003, 0x2010, 0x2002 and "
                 "0x1040): an entry such as a Finder tag or the iCloud Drive item carries a URL and no"
                 " path. Target Created is the bookmarked item's creation date, not a time it was "
                 "opened. Special Item Identifier is the SpecialItemIdentifier custom property as "
                 "stored. Hidden is the ItemIsHidden custom property, shown as Yes or No when it is "
                 "a boolean. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur the 9 files hold 46 entries, 28 "
                 "with a path and 18 with a URL. On the public MacBook Pro logical extraction (macOS "
                 "15.4, corpus key mvs2026_macbookpro_macos15) every list is .sfl3: 31 files are read and "
                 "11 of them hold 55 entries, 36"
                 " with a path and 18 with a URL, and one entry holds no Bookmark, so it carries "
                 "neither. When a logical extraction holds the same file under Users/ or "
                 "private/var/root/ and again under System/Volumes/Data/, a second copy "
                 "byte-identical to the first is not read again, and is counted in the run log. "
                 "A .sfl4 file is read the same way as a .sfl3 file. On two private macOS 27 systems "
                 "(27.0 and 27.0.1) every .sfl4 file was an NSKeyedArchiver binary plist with the "
                 "same root keys (items, properties) and the same item keys as the .sfl3 files beside "
                 "them (Bookmark, CustomItemProperties, uuid and visibility on every item, Name on "
                 "some), and "
                 "every Bookmark decoded. On one of them the first .sfl4 file was created within a "
                 "minute of the install of macOS 26.2 (an upgrade from 15.7.3) and no .sfl3 file changed after "
                 "that. The older .sfl3 files stay on disk and are read too, so one list can appear "
                 "under both extensions; the List column names the file. Which macOS release first "
                 "writes .sfl4 is not established. A search on 2026-10-17 found no Apple or published "
                 "description of the .sfl4 layout, and no public corpus image holds a .sfl4 file "
                 "(dleapp_macos_bigsur and magnet2021_macos_bigsur hold .sfl2, "
                 "mvs2026_macbookpro_macos15 .sfl3), so the "
                 ".sfl4 reading is shown on those private systems, whose counts and values are not "
                 "published, and by tests built on synthetic files. "
                 "Reference: "
                 "mac_alias (dmgbuild), bookmark.py, "
                 "https://github.com/dmgbuild/mac_alias/blob/d0c076b4562541c1509d9874f42880378245d268/src/mac_alias/bookmark.py#L128-L169.",
        "paths": ('*/Library/Application Support/com.apple.sharedfilelist/*.sfl2',
                  '*/Library/Application Support/com.apple.sharedfilelist/*.sfl3',
                  '*/Library/Application Support/com.apple.sharedfilelist/*.sfl4'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "history",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 46 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import (bookmark_fields, load_plist, resolve_keyed_archive,
                                  unique_sources, user_from_path)


def _text(value):
    return '' if value is None else str(value)


@artifact_processor
def macosSharedFileLists(context):
    data_headers = ('List', 'Order', 'Name', 'Path', 'URL', 'Volume Name', 'Volume Path',
                    ('Target Created (UTC, bookmark)', 'datetime'), 'Special Item Identifier',
                    'Hidden', 'User', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Shared File Lists')
    for path in paths:
        relative = context.get_relative_path(path)
        root = resolve_keyed_archive(load_plist(path))
        if not isinstance(root, dict):
            logfunc(f'Shared File Lists: could not read {relative}')
            continue
        read.append(path)
        name = os.path.basename(path)
        user = user_from_path(relative)
        for order, item in enumerate(root.get('items') or []):
            if not isinstance(item, dict):
                continue
            mark = bookmark_fields(item.get('Bookmark')) or {}
            props = item.get('CustomItemProperties') if isinstance(item.get('CustomItemProperties'), dict) else {}
            hidden = props.get('com.apple.LSSharedFileList.ItemIsHidden')
            data_list.append((name, order, _text(item.get('Name')), mark.get('path', ''),
                              mark.get('url', ''), mark.get('volume_name', ''),
                              mark.get('volume_path', ''), mark.get('file_created', ''),
                              _text(props.get('com.apple.LSSharedFileList.SpecialItemIdentifier')),
                              {True: 'Yes', False: 'No'}.get(hidden, _text(hidden)), user, relative))
    return data_headers, data_list, '\n'.join(read)
