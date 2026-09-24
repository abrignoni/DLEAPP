"""Items in the iCloud Drive (CloudDocs) client database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosICloudDriveItems": {
        "name": "iCloud Drive Items",
        "description": "Items in each user's iCloud Drive client database (CloudDocs client.db): "
                       "file name, the path rebuilt from the parent entries it stores, the stored "
                       "item type and size, zone and app library, with the stored birth, "
                       "modification and last used times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": "Reads each user's client.db under ~/Library/Application "
                 "Support/CloudDocs/session/db, one row per client_items row. Version "
                 "Modified (UTC), Item Birth Time (UTC) and Last Used (UTC) are "
                 "version_mtime, item_birthtime and item_lastusedtime read as Unix "
                 "seconds, and a stored 0 is reported blank; read that way the Item Birth "
                 "Time values on dleapp_macos_bigsur fall between 1 January 2020 and 19 "
                 "February 2021, where the 2001 epoch would place them in 2051 and 2052. "
                 "Last Used is blank on 56 of the 72 rows there. File Name is "
                 "item_filename. Path joins the item's name to the names of the items its "
                 "item_parent_id chain reaches in the same table, outermost first; a "
                 "parent the table does not hold ends the chain, so Path can start below "
                 "the top of the zone. Item Type, Size, User Visible and Trash Put-Back "
                 "Path are item_type, version_size, item_user_visible and "
                 "item_trash_put_back_path as stored; on dleapp_macos_bigsur the 47 rows "
                 "of type 0 and the 2 of type 4 store no size, and 2 rows carry a put-back "
                 "path. Zone is the zone_name of the client_zones row and App Library the "
                 "app_library_name of the app_libraries row the item names. Zone and App "
                 "Library held the same text on 56 of the 72 rows on dleapp_macos_bigsur "
                 "and were identical on every row of the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key). On the MacBook Pro "
                 "version_mtime is 0 on 27 of the 42 items, so Version Modified is blank "
                 "on those rows, Trash Put-Back Path is empty on every row, and the Users/ "
                 "and System/Volumes/Data/Users/ copies differ and both are read, so each "
                 "item appears twice, identical in every column but Source File. server.db "
                 "is not read. All rows on each image come from one user, so User holds "
                 "one value there. When a logical extraction holds the same file under "
                 "Users/ and under System/Volumes/Data/Users/, a byte-identical second "
                 "copy is read once and counted in the run log.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 72 rows",
                       },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/client.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "cloud",
    }
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import unique_sources, user_from_path

_LABEL = 'iCloud Drive Items'
_ITEM_COLUMNS = ('item_id', 'item_parent_id', 'item_filename', 'item_type', 'version_size',
                 'version_mtime', 'item_birthtime', 'item_lastusedtime', 'zone_rowid',
                 'app_library_rowid', 'item_trash_put_back_path', 'item_user_visible')


def _text(value):
    return '' if value is None else str(value)


def _unix_utc(seconds):
    """Unix seconds as an aware UTC datetime; '' for 0 or anything not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds == 0:
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _select(path, table, names):
    if not does_table_exist_in_db(path, table):
        return []
    columns = ', '.join(name if name == 'rowid' or does_column_exist_in_db(path, table, name)
                        else f'NULL AS {name}' for name in names)
    return get_sqlite_db_records(path, f'SELECT {columns} FROM {table} ORDER BY rowid') or []


def _path(item_id, items):
    """The item's name with the names of the parent entries it stores, outermost first."""
    names = []
    seen = set()
    current = item_id
    while current in items and current not in seen:
        seen.add(current)
        parent, name = items[current]
        names.append(_text(name))
        current = parent
    return '/'.join(reversed(names))


def _rows(path):
    zones = {row[0]: row[1] for row in _select(path, 'client_zones', ('rowid', 'zone_name'))}
    libraries = {row[0]: row[1] for row in _select(
        path, 'app_libraries', ('rowid', 'app_library_name'))}
    records = _select(path, 'client_items', _ITEM_COLUMNS)
    items = {row[0]: (row[1], row[2]) for row in records if row[0] is not None}
    for (item_id, _parent, name, item_type, size, mtime, birth, last_used, zone, library,
         put_back, visible) in records:
        yield (_unix_utc(birth), _unix_utc(mtime), _unix_utc(last_used), _text(name),
               _path(item_id, items), _text(item_type), _text(size), _text(zones.get(zone, zone)),
               _text(libraries.get(library, library)), _text(put_back), _text(visible))


@artifact_processor
def macosICloudDriveItems(context):
    data_headers = (('Item Birth Time (UTC)', 'datetime'), ('Version Modified (UTC)', 'datetime'),
                    ('Last Used (UTC)', 'datetime'), 'File Name', 'Path', 'Item Type (as stored)',
                    'Size (bytes, as stored)', 'Zone', 'App Library',
                    'Trash Put-Back Path (as stored)', 'User Visible (as stored)', 'User',
                    'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'client.db']
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'client_items'):
            logfunc(f'{_LABEL}: no client_items table read from {relative}')
            continue
        read.append(path)
        found = [row + (user_from_path(relative), relative) for row in _rows(path)]
        if not found:
            logfunc(f'{_LABEL}: no items in {relative}')
        data_list.extend(found)
    return data_headers, data_list, '\n'.join(read)
