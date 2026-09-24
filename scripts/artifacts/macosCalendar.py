"""Items in the macOS Calendar stores, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosCalendarItems": {
        "name": "Calendar Items",
        "description": "Items in each user's Calendar store (Calendar Cache, or "
                       "Calendar.sqlitedb in the calendar group container): title, start "
                       "and end, the plain date of whole-day items, the calendar and its "
                       "type, location, notes, recurrence and the stored creation and "
                       "modification times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Calendar (macOS)",
        "notes": "Reads each user's Calendar store: Calendar Cache under "
                 "~/Library/Calendars, as on dleapp_macos_bigsur, or Calendar.sqlitedb in "
                 "the group.com.apple.calendar group container, as on the public MacBook "
                 "Pro logical extraction (macOS 15.4, not a registered corpus key). One "
                 "row per ZCALENDARITEM row in Calendar Cache and per CalendarItem row in "
                 "Calendar.sqlitedb. Start (UTC), End (UTC), Created (UTC) and Last "
                 "Modified (UTC) are ZSTARTDATE, ZENDDATE, ZCREATIONDATE and "
                 "ZLASTMODIFIEDDATE, or start_date, end_date, creation_date and "
                 "last_modified, read as seconds since 00:00:00 UTC on 1 January 2001, the "
                 "reference date Apple documents for NSDate; read that way the items on "
                 "dleapp_macos_bigsur were created between April 2020 and February 2021, "
                 "where the 1970 epoch would place them in 1989 and 1990. All-Day Date is "
                 "the date of Start (UTC) for an item stored as all-day (ZISALLDAY or "
                 "all_day) whose start falls at 00:00:00 UTC, and is blank otherwise; it "
                 "is a plain date, so no time zone conversion can move it. On "
                 "dleapp_macos_bigsur 104 of the 105 items are all-day, each starting at "
                 "00:00:00 UTC and ending 86,400 seconds later; on the MacBook Pro all 135 "
                 "items are all-day, each ending 86,399 seconds after a 00:00:00 UTC "
                 "start. Time Zone is ZTIMEZONE or start_tz as stored. Time Zone is blank "
                 "on the 104 all-day items on dleapp_macos_bigsur and an IANA zone name on "
                 "its one other item, and held one value, _float, on all MacBook Pro rows. "
                 "Calendar is the title of the item's calendar. Calendar Type is, for "
                 "Calendar Cache, the entity name of the calendar in Z_PRIMARYKEY "
                 "(CalDAVCalendar for 1 item and SubscriptionCalendar for 104 on "
                 "dleapp_macos_bigsur) and, for Calendar.sqlitedb, the name and type "
                 "number of the Store the calendar belongs to. Item Type is the entity "
                 "name of the item in Z_PRIMARYKEY for Calendar Cache and "
                 "CalendarItem.entity_type for Calendar.sqlitedb, as stored. Item Type "
                 "held one value on all 105 rows of dleapp_macos_bigsur and on all MacBook "
                 "Pro rows. Location and Location Address are the title and address of the "
                 "item's location record. In Calendar Cache, Latitude and Longitude are "
                 "read from the location's ZGEOURLSTRING, a geo URI whose first number is "
                 "the latitude and second the longitude (RFC 5870, section 3.3, "
                 "https://www.rfc-editor.org/rfc/rfc5870#section-3.3), and a value not in "
                 "that form leaves both blank; in Calendar.sqlitedb they are the latitude "
                 "and longitude of the Location row. 1 item on dleapp_macos_bigsur has a "
                 "location, and Location, Location Address, Latitude and Longitude have no "
                 "value on any MacBook Pro row. Recurrence is, for Calendar Cache, the "
                 "ZRECURRENCERULE text and, for Calendar.sqlitedb, the frequency, "
                 "interval, count, specifier and by_month_months fields of the item's "
                 "Recurrence row, as stored; an item with a recurrence is one row, and the "
                 "occurrences it describes are not listed. 26 items on dleapp_macos_bigsur "
                 "and 28 on the MacBook Pro carry one. Notes, URL and Unique Identifier "
                 "are ZNOTES, ZURLSTRING and ZUNIVERSALIDENTIFIER, or description, url and "
                 "unique_identifier, as stored. On dleapp_macos_bigsur 104 items carry 46 "
                 "distinct Unique Identifier values, so one value can belong to several "
                 "rows. URL is empty on both tested images. On the MacBook Pro the 134 "
                 "items of the subscribed calendar store no creation date and share one "
                 "last-modified value, dated 1976, and the Users/ and "
                 "System/Volumes/Data/Users/ copies differ and both are read, so each item "
                 "appears twice, identical in every column but Source File. All rows on "
                 "each image come from one user, so User holds one value there. When a "
                 "logical extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/, a byte-identical second copy is read once "
                 "and counted in the run log. Reference: Apple, 'NSDate', "
                 "https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 105 rows",
                       },
        "paths": ('*/Library/Calendars/Calendar Cache*',
                  '*/Library/Group Containers/group.com.apple.calendar/Calendar.sqlitedb*'),
        "output_types": ["html", "tsv", "timeline", "lava", "kml"],
        "artifact_icon": "calendar",
    }
}

import os
import re
from datetime import time

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import mac_absolute_utc, unique_sources, user_from_path

_LABEL = 'Calendar Items'
_CACHE = 'Calendar Cache'
_SQLITEDB = 'Calendar.sqlitedb'

# Calendar Cache (Core Data): ZCALENDARITEM columns read, in row order.
_CACHE_ITEM_COLUMNS = ('ZSTARTDATE', 'ZENDDATE', 'ZISALLDAY', 'ZTITLE', 'ZNOTES', 'ZURLSTRING',
                       'ZTIMEZONE', 'ZRECURRENCERULE', 'ZCREATIONDATE', 'ZLASTMODIFIEDDATE',
                       'ZUNIVERSALIDENTIFIER', 'ZCALENDAR', 'ZSTRUCTUREDLOCATION', 'Z_ENT')
# Calendar.sqlitedb: CalendarItem columns read, in row order.
_DB_ITEM_COLUMNS = ('start_date', 'end_date', 'all_day', 'summary', 'description', 'url',
                    'start_tz', 'creation_date', 'last_modified', 'unique_identifier',
                    'calendar_id', 'location_id', 'entity_type', 'ROWID')
_RECURRENCE_FIELDS = ('frequency', 'interval', 'count', 'specifier', 'by_month_months')
# RFC 5870 geo URI: geo:<latitude>,<longitude>[,<altitude>][;parameters]
_GEO_URI = re.compile(r'^geo:(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', re.IGNORECASE)


def _text(value):
    return '' if value is None else str(value)


def _columns(path, table, names):
    """The named columns, with NULL standing in for any the table lacks; ROWID is always kept."""
    return ', '.join(name if name == 'ROWID' or does_column_exist_in_db(path, table, name)
                     else f'NULL AS {name}' for name in names)


def _all_day_date(start, all_day):
    """The UTC date of an all-day item's start when it falls at 00:00:00 UTC, else ''."""
    if all_day and start and start.time() == time(0, 0):
        return start.date()
    return ''


def _geo(uri):
    match = _GEO_URI.match(uri or '')
    return (match.group(1), match.group(2)) if match else ('', '')


def _cache_rows(path):
    """Rows from a Calendar Cache (Core Data) store."""
    item_columns = _columns(path, 'ZCALENDARITEM', _CACHE_ITEM_COLUMNS)
    records = get_sqlite_db_records(
        path, f'SELECT {item_columns} FROM ZCALENDARITEM ORDER BY ZSTARTDATE') or []
    entities = {row[0]: row[1] for row in
                get_sqlite_db_records(path, 'SELECT Z_ENT, Z_NAME FROM Z_PRIMARYKEY') or []}
    nodes = {}
    if does_table_exist_in_db(path, 'ZNODE'):
        node_columns = _columns(path, 'ZNODE', ('Z_PK', 'Z_ENT', 'ZTITLE'))
        nodes = {row[0]: (row[2], entities.get(row[1], '')) for row in
                 get_sqlite_db_records(path, f'SELECT {node_columns} FROM ZNODE') or []}
    locations = {}
    if does_table_exist_in_db(path, 'ZLOCATION'):
        location_columns = _columns(path, 'ZLOCATION', ('Z_PK', 'ZTITLE', 'ZADDRESS', 'ZGEOURLSTRING'))
        locations = {row[0]: row[1:] for row in
                     get_sqlite_db_records(path, f'SELECT {location_columns} FROM ZLOCATION') or []}
    for row in records:
        (start, end, all_day, title, notes, url, zone, rule, created, modified, uid,
         calendar, location, entity) = row
        calendar_title, calendar_type = nodes.get(calendar, ('', ''))
        place, address, geo = locations.get(location, ('', '', ''))
        latitude, longitude = _geo(geo)
        start = mac_absolute_utc(start)
        yield (start, mac_absolute_utc(end), _all_day_date(start, all_day), _text(title),
               _text(calendar_title), _text(calendar_type), _text(entities.get(entity, entity)),
               _text(place), _text(address), latitude, longitude, _text(notes), _text(url),
               _text(zone), _text(rule), mac_absolute_utc(created), mac_absolute_utc(modified),
               _text(uid))


def _recurrences(path):
    """Recurrence rows of a Calendar.sqlitedb store as 'name: value' text, by owner item."""
    if not does_table_exist_in_db(path, 'Recurrence'):
        return {}
    fields = [f for f in _RECURRENCE_FIELDS if does_column_exist_in_db(path, 'Recurrence', f)]
    if not fields or not does_column_exist_in_db(path, 'Recurrence', 'owner_id'):
        return {}
    rules = {}
    for row in get_sqlite_db_records(
            path, f'SELECT owner_id, {", ".join(fields)} FROM Recurrence ORDER BY ROWID') or []:
        text = '; '.join(f'{name}: {value}' for name, value in zip(fields, row[1:])
                         if value not in (None, ''))
        rules.setdefault(row[0], []).append(text)
    return {owner: ' | '.join(texts) for owner, texts in rules.items()}


def _sqlitedb_rows(path):
    """Rows from a Calendar.sqlitedb store."""
    item_columns = _columns(path, 'CalendarItem', _DB_ITEM_COLUMNS)
    records = get_sqlite_db_records(
        path, f'SELECT {item_columns} FROM CalendarItem ORDER BY start_date') or []
    stores = {}
    if does_table_exist_in_db(path, 'Store'):
        stores = {row[0]: row[1:] for row in
                  get_sqlite_db_records(
                      path, f"SELECT {_columns(path, 'Store', ('ROWID', 'name', 'type'))} FROM Store") or []}
    calendars = {}
    if does_table_exist_in_db(path, 'Calendar'):
        calendars = {row[0]: row[1:] for row in
                     get_sqlite_db_records(
                         path, f"SELECT {_columns(path, 'Calendar', ('ROWID', 'title', 'store_id'))} FROM Calendar") or []}
    locations = {}
    if does_table_exist_in_db(path, 'Location'):
        location_columns = _columns(path, 'Location', ('ROWID', 'title', 'address', 'latitude', 'longitude'))
        locations = {row[0]: row[1:] for row in
                     get_sqlite_db_records(path, f'SELECT {location_columns} FROM Location') or []}
    recurrences = _recurrences(path)
    for row in records:
        (start, end, all_day, title, notes, url, zone, created, modified, uid,
         calendar, location, entity, rowid) = row
        calendar_title, store_id = calendars.get(calendar, ('', None))
        store_name, store_type = stores.get(store_id, ('', None))
        calendar_type = (f'{_text(store_name)} (store type {store_type})'
                         if store_type is not None else _text(store_name))
        place, address, latitude, longitude = locations.get(location, ('', '', '', ''))
        start = mac_absolute_utc(start)
        yield (start, mac_absolute_utc(end), _all_day_date(start, all_day), _text(title),
               _text(calendar_title), calendar_type, _text(entity), _text(place), _text(address),
               _text(latitude), _text(longitude), _text(notes), _text(url), _text(zone),
               recurrences.get(rowid, ''), mac_absolute_utc(created), mac_absolute_utc(modified),
               _text(uid))


@artifact_processor
def macosCalendarItems(context):
    data_headers = (('Start (UTC)', 'datetime'), ('End (UTC)', 'datetime'),
                    ('All-Day Date', 'date'), 'Title', 'Calendar', 'Calendar Type (as stored)',
                    'Item Type (as stored)', 'Location', 'Location Address', 'Latitude',
                    'Longitude', 'Notes', 'URL', 'Time Zone (as stored)',
                    'Recurrence (as stored)', ('Created (UTC)', 'datetime'),
                    ('Last Modified (UTC)', 'datetime'), 'Unique Identifier', 'User',
                    'Source File')
    data_list = []
    read = []
    stores = [p for p in context.get_files_found()
              if os.path.basename(str(p)) in (_CACHE, _SQLITEDB)]
    paths, _skipped = unique_sources(context, stores, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if os.path.basename(str(path)) == _CACHE:
            table, rows = 'ZCALENDARITEM', _cache_rows
        else:
            table, rows = 'CalendarItem', _sqlitedb_rows
        if not does_table_exist_in_db(path, table):
            logfunc(f'{_LABEL}: no {table} table read from {relative}')
            continue
        read.append(path)
        found = [row + (user_from_path(relative), relative) for row in rows(path)]
        if not found:
            logfunc(f'{_LABEL}: no items in {relative}')
        data_list.extend(found)
    return data_headers, data_list, '\n'.join(read)
