"""Notifications recorded in the macOS Notification Center database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosNotifications": {
        "name": "Notification Center Records",
        "description": "Notification records in the Notification Center database (db2/db, under "
                       "private/var/folders or the usernoted group container): delivery time, "
                       "app, title, subtitle and body, with the stored presented and style "
                       "values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Notifications (macOS)",
        "notes": "Reads the Notification Center database db2/db: under "
                 "private/var/folders/<xx>/<yyyy>/0/com.apple.notificationcenter on "
                 "dleapp_macos_bigsur, and in the group.com.apple.usernoted group "
                 "container on the public MacBook Pro logical extraction (macOS 15.4, not "
                 "a registered corpus key), the locations mac_apt's notifications plugin "
                 "documents (mac_apt, plugins/notifications.py, "
                 "https://github.com/ydkhatri/mac_apt/blob/fb2360857aee2e4fafc8dff8eda2f82c97d86c54/plugins/notifications.py#L36-L42). "
                 "One row per record in the record table, with App the identifier of its "
                 "app row. Delivered (UTC) is delivered_date read as seconds since "
                 "00:00:00 UTC on 1 January 2001, the reference date Apple documents for "
                 "NSDate, as mac_apt reads it (#L168); on all 8 records on the two images "
                 "it equalled the date value inside the record's data property list, and "
                 "on dleapp_macos_bigsur the 6 records fall between 17 and 19 February "
                 "2021, where the 1970 epoch would place them in 1990. Title, Subtitle, "
                 "Body and Request Identifier are the titl, subt, body and iden values of "
                 "the req dictionary in that property list, the keys mac_apt reads as "
                 "title, subtitle, message and identifier (#L155-L158); a value stored as "
                 "a list, as on the MacBook Pro's App Store record, is shown with its "
                 "parts joined by '; '. Other Request Fields (as stored) lists the other "
                 "text and number values of req as 'key: value'. Presented and Style are "
                 "presented and style as stored; on dleapp_macos_bigsur Presented and "
                 "Style each held one value on all 6 rows. The 6 records on "
                 "dleapp_macos_bigsur are in the database of one private/var/folders "
                 "subfolder, and the database in a second subfolder holds no records. User "
                 "is blank for a database under private/var/folders, whose path does not "
                 "name the account, as on all 6 rows of dleapp_macos_bigsur. On the "
                 "MacBook Pro the Users/ copy holds 2 records and the "
                 "System/Volumes/Data/Users/ copy 1 of them, so both are read, and "
                 "Subtitle has no value on any MacBook Pro row. When a logical extraction "
                 "holds the same file with and without a System/Volumes/Data/ prefix, a "
                 "byte-identical second copy is read once and counted in the run log. The "
                 "older com.apple.notificationcenter/db/db database is not read. "
                 "Reference: Apple, 'NSDate', "
                 "https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 6 rows",
                       },
        "paths": ('*/private/var/folders/*/com.apple.notificationcenter/db2/db*',
                  '*/Library/Group Containers/group.com.apple.usernoted/db2/db*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
    }
}

import os
import plistlib

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import mac_absolute_utc, unique_sources, user_from_path

_LABEL = 'Notification Center Records'
_RECORD_COLUMNS = ('rec_id', 'app_id', 'data', 'delivered_date', 'presented', 'style')
# Request keys read into their own columns; see notes for the source.
_MAPPED_KEYS = ('titl', 'subt', 'body', 'iden')


def _text(value):
    return '' if value is None else str(value)


def _flat(value):
    """A stored string, or the parts of a stored list joined by '; '."""
    if isinstance(value, list):
        return '; '.join(part for part in (_flat(item) for item in value) if part)
    if isinstance(value, (bytes, bytearray, dict)):
        return ''
    return _text(value)


def _columns(path, table, names):
    return ', '.join(name if does_column_exist_in_db(path, table, name) else f'NULL AS {name}'
                     for name in names)


def _rows(path, relative):
    apps = {}
    if does_table_exist_in_db(path, 'app'):
        apps = {row[0]: row[1] for row in get_sqlite_db_records(
            path, f"SELECT {_columns(path, 'app', ('app_id', 'identifier'))} FROM app") or []}
    records = get_sqlite_db_records(
        path, f"SELECT {_columns(path, 'record', _RECORD_COLUMNS)} FROM record "
              "ORDER BY delivered_date") or []
    unreadable = 0
    for rec_id, app_id, data, delivered, presented, style in records:
        request = None
        try:
            record = plistlib.loads(data) if data else {}
            request = record.get('req') if isinstance(record, dict) else None
        except (plistlib.InvalidFileException, ValueError, TypeError):
            unreadable += 1
        if not isinstance(request, dict):
            request = {}
        others = '; '.join(f'{key}: {_flat(value)}' for key, value in request.items()
                           if key not in _MAPPED_KEYS and _flat(value))
        yield (mac_absolute_utc(delivered), _text(apps.get(app_id, app_id)),
               _flat(request.get('titl')), _flat(request.get('subt')), _flat(request.get('body')),
               _flat(request.get('iden')), others, _text(presented), _text(style), _text(rec_id))
    if unreadable:
        logfunc(f'{_LABEL}: {unreadable} record(s) in {relative} whose data did not read as a '
                'property list; their text columns are blank')


@artifact_processor
def macosNotifications(context):
    data_headers = (('Delivered (UTC)', 'datetime'), 'App', 'Title', 'Subtitle', 'Body',
                    'Request Identifier', 'Other Request Fields (as stored)',
                    'Presented (as stored)', 'Style (as stored)', 'Record ID', 'User',
                    'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'db']
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'record'):
            logfunc(f'{_LABEL}: no record table read from {relative}')
            continue
        read.append(path)
        found = [row + (user_from_path(relative), relative) for row in _rows(path, relative)]
        if not found:
            logfunc(f'{_LABEL}: no notification records in {relative}')
        data_list.extend(found)
    return data_headers, data_list, '\n'.join(read)
