"""Apple Maps history, favorites and saved places from each macOS user's MapsSync store, for DLEAPP.

Ported from iLEAPP's mapsSync.py (abrignoni/iLEAPP#2735, @nwish and @AlexisBrignoni), reading the
same store in the Maps container on macOS. The protobuf BLOBs are read with the schema-less field
reader in scripts/macos_biome.py, following fixed field paths, instead of blackboxprotobuf, which
DLEAPP does not carry.

Author: @AlexisBrignoni, @nwish, Claude.
"""

__artifacts_v2__ = {
    "macosMapsSync": {
        "name": "Maps History (MapsSync)",
        "description": "Apple Maps history rows from each user's MapsSync_0.0.1 store: searches, places opened and "
                       "directions, with the query text Maps sent and the text typed before a suggestion was chosen "
                       "where the row's request payloads hold them.",
        "author": "@AlexisBrignoni, @nwish, Claude",
        "creation_date": "2026-11-16",
        "last_update_date": "2026-11-16",
        "requirements": "none",
        "category": "Maps (macOS)",
        "platforms": ("macOS",),
        "notes": "Reads the ZHISTORYITEM table of MapsSync_0.0.1 in each user's "
                 "Library/Containers/com.apple.Maps/Data/Maps, with its -wal: on maps_known_data_macos27 every row is "
                 "in the -wal, and the database read without it has every Maps table empty. Created and Modified are "
                 "ZCREATETIME and ZMODIFICATIONTIME, Core Data seconds since 2001, shown in UTC. Created and Modified "
                 "were identical on all 9 rows of that sample. Entity is the Z_NAME the same store's Z_PRIMARYKEY table gives for the "
                 "row's Z_ENT, which is also shown as stored; the numbers differ between stores (HistoryPlaceItem is "
                 "14 on the macOS 11.2.1 store, 19 on the 15.4 store and 21 on the 27.2.1 store), so none is mapped "
                 "by a fixed list. Location Search and Location Display are ZQUERY and ZLOCATIONDISPLAY; on the known "
                 "data only the HistorySearchItem row, from a search submitted with Enter that returned a list, held "
                 "them. Place Name and Address are read from the row's map item, ZMIXINMAPITEM.ZMAPITEMSTORAGE joined "
                 "on ZMAPITEM, at protobuf fields 1.4.8.30.1 and 1.4.8.31.1.101.2.11, the address lines joined with "
                 "', '. On a HistoryDirectionsItem row they are read the same way from each waypoint of "
                 "ZROUTEREQUESTSTORAGE (field 1.n.2), joined with ' -> ' in stored order. These field paths were found "
                 "on the 27.2.1 store and checked against the ZMAPITEMNAME and ZMAPITEMADDRESS that the same store "
                 "keeps for 4 of its map items; they are not exercised on other macOS versions, since the two public "
                 "stores tested have no rows. Query (Sent) and Query (Raw) come from every base64 'placeRequest=' value "
                 "in those BLOBs, found by walking their protobuf fields: Sent is field 8.1.3 and Raw field "
                 "8.1.7.10000 of the decoded request, the fields iLEAPP's mapsSync artifact reads, distinct values "
                 "joined with '; '. On the known data, recorded with a timed activity log: on the 4 rows from searches "
                 "submitted with Enter that opened one place, Sent held the text as typed, including on a row whose "
                 "typed text had lost a keystroke and so differed from the place name, and Raw was empty; on the 3 "
                 "rows where partial text was typed and a suggestion was then chosen, Sent held the suggestion's title "
                 "and Raw exactly the partial text typed; the directions row held both, for each waypoint. That is an "
                 "observation from one store, not a sourced rule, and Sent and Raw are labels chosen here, not "
                 "Apple's names. Latitude and Longitude are ZLATITUDE and ZLONGITUDE, otherwise ZLATITUDE1 and "
                 "ZLONGITUDE1; on the known data the first pair was empty on every row and the second held the "
                 "coordinates of the 7 place rows. Created can be later than the action: the store's persistent "
                 "history (ACHANGE, ATRANSACTION) shows one history row inserted at the moment a suggestion was chosen "
                 "and deleted 9 seconds later, when the row reported here was inserted. Those persistent history "
                 "tables, the CloudKit tables (ANSCK*) and MapsSync_0.0.1_deviceLocalCache.db are not read; the last "
                 "had no rows in any store tested. User is the folder name under Users, and was the one user 'kdu' on "
                 "all 9 rows of the known data. When an extraction holds the store under Users and under "
                 "System/Volumes/Data/Users with identical bytes and -wal it is read once; when the copies differ "
                 "both are read and a row both hold is reported once with both files in Source File, tested only on "
                 "a constructed tree, since the two views of the 15.4 store differ but have no rows. A row is an "
                 "entry in Maps history; it is not evidence that travel took place, and whether it was made on this "
                 "Mac or synced from another device on the same account is not established. The known-data guest had "
                 "no Apple Account, so its rows were all made on it.",
        "paths": ("*/Library/Containers/com.apple.Maps/Data/Maps/MapsSync_0.0.1*",),
        "output_types": "all",
        "artifact_icon": "map-pin",
        "sample_data": {
            "maps_known_data_macos27": "macOS 27.2.1 | 9 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (store present under two views, every Maps table empty)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (store present under three views, every Maps table empty)",
        },
    },
    "macosMapsFavorites": {
        "name": "Maps Favorites (MapsSync)",
        "description": "Rows of the ZFAVORITEITEM table of each user's Apple Maps MapsSync_0.0.1 store, the places "
                       "pinned to Places, with the name, address, coordinates and request query text where stored.",
        "author": "@AlexisBrignoni, @nwish, Claude",
        "creation_date": "2026-11-16",
        "last_update_date": "2026-11-16",
        "requirements": "none",
        "category": "Maps (macOS)",
        "platforms": ("macOS",),
        "notes": "Reads the ZFAVORITEITEM table of MapsSync_0.0.1 in each user's "
                 "Library/Containers/com.apple.Maps/Data/Maps, with its -wal. On maps_known_data_macos27, recorded "
                 "with a timed activity log, Places > Add (a landmark chosen in its search) wrote one row and Pin on a "
                 "place card wrote the other; the Favorites star on a place card wrote no row here, it wrote a "
                 "ZCOLLECTIONITEM row (see Maps Saved Places and Guides), so an empty table is not evidence that no "
                 "place was marked a favorite. Created and Modified are ZCREATETIME and ZMODIFICATIONTIME, Core Data "
                 "seconds since 2001, shown in UTC. Custom Name is ZCUSTOMNAME as stored: set on the Places > Add row "
                 "and empty on the Pin row. Place Name is ZMAPITEMNAME, otherwise the name decoded from the joined "
                 "ZMIXINMAPITEM map item; Address is ZMAPITEMADDRESS, otherwise the decoded address, otherwise "
                 "ZORIGINATINGADDRESSSTRING; both rows stored ZMAPITEMNAME and ZMAPITEMADDRESS, so the fallbacks were "
                 "not reached. Category is ZMAPITEMCATEGORY as stored. Favorite Type, Source and Hidden are ZTYPE, "
                 "ZSOURCE and ZHIDDEN, integers reported as stored; both rows held 1, 0 and 0, and their meanings are "
                 "not sourced. Query (Sent) and Query (Raw) are read from the map item the way Maps History (MapsSync) "
                 "reads them: on the Places > Add row Sent held the chosen suggestion's title and address and Raw the "
                 "partial text typed in that search; the Pin row, made from a place opened from Recents, held neither. "
                 "Sent and Raw are labels chosen here, not Apple's names. Latitude and Longitude are the row's own "
                 "ZLATITUDE and ZLONGITUDE, otherwise the map item's; both rows had their own. Not exercised: the Home, "
                 "Work and School types offered by Places > Add. User and Source File, and the reading of a store held "
                 "under two views, are as in Maps History (MapsSync). A row shows the place was kept in Maps; it is "
                 "not evidence that anyone was there, and whether it was made on this Mac or synced is not "
                 "established. The table is empty on the macOS 15.4 and 11.2.1 stores tested.",
        "paths": ("*/Library/Containers/com.apple.Maps/Data/Maps/MapsSync_0.0.1*",),
        "output_types": "all",
        "artifact_icon": "star",
        "sample_data": {
            "maps_known_data_macos27": "macOS 27.2.1 | 2 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (ZFAVORITEITEM present and empty)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (ZFAVORITEITEM present and empty)",
        },
    },
    "macosMapsCollectionItems": {
        "name": "Maps Saved Places and Guides (MapsSync)",
        "description": "Rows of the ZCOLLECTIONITEM table of each user's Apple Maps MapsSync_0.0.1 store, places "
                       "saved in Maps, with the guides each belongs to, the name, address and coordinates.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-16",
        "last_update_date": "2026-11-16",
        "requirements": "none",
        "category": "Maps (macOS)",
        "platforms": ("macOS",),
        "notes": "Reads the ZCOLLECTIONITEM table of MapsSync_0.0.1 in each user's "
                 "Library/Containers/com.apple.Maps/Data/Maps, with its -wal, one output row per table row. On "
                 "maps_known_data_macos27, recorded with a timed activity log, the Favorites star on a place card "
                 "wrote the row with ZTYPE 1 and the card's + button, which saves the place to Places, wrote the row "
                 "with ZTYPE 0; Item Type is ZTYPE as stored, and beyond those two observations its meaning is not "
                 "sourced. Entity is the Z_NAME the store's Z_PRIMARYKEY gives for the row's Z_ENT; both rows were "
                 "CollectionPlaceItem. Guides lists the ZTITLE of every ZCOLLECTION row linked to the item through "
                 "the store's many-to-many table, whose name changes with the entity numbers (Z_4PLACES on the macOS "
                 "11.2.1 store, Z_5PLACES on 15.4, Z_7PLACES on 27.2.1) and is found from the schema. Adding the + row "
                 "to a new guide linked it here and set its ZMODIFICATIONTIME to that moment. The Favorites guide that "
                 "Maps shows has no ZCOLLECTION row in that store. Created and Modified are ZCREATETIME and "
                 "ZMODIFICATIONTIME, Core Data seconds since 2001, shown in UTC. Custom Name is ZCUSTOMNAME and Note "
                 "ZPLACEITEMNOTE, as stored. Custom Name and Note were empty on both rows, since neither place was "
                 "renamed or given a note. Place Name is ZMAPITEMNAME, otherwise the name decoded from the joined ZMIXINMAPITEM "
                 "map item; Address is ZMAPITEMADDRESS, otherwise the decoded address; both rows stored them, so the "
                 "fallbacks were not reached. Category is ZMAPITEMCATEGORY as stored. Query (Sent) and Query (Raw) are "
                 "read from the map item the way Maps History (MapsSync) reads them, and on both rows matched the "
                 "history row of the search that found the place. Latitude and Longitude are the row's own, otherwise "
                 "the map item's. Not exercised: CollectionTransitItem rows, dropped pins and notes. User and Source "
                 "File, and the reading of a store held under two views, are as in Maps History (MapsSync). A row "
                 "shows the place was kept in Maps; it is not evidence that anyone was there, and whether it was made "
                 "on this Mac or synced is not established. The table is empty on the macOS 15.4 and 11.2.1 stores "
                 "tested.",
        "paths": ("*/Library/Containers/com.apple.Maps/Data/Maps/MapsSync_0.0.1*",),
        "output_types": "all",
        "artifact_icon": "bookmark",
        "sample_data": {
            "maps_known_data_macos27": "macOS 27.2.1 | 2 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (ZCOLLECTIONITEM present and empty)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (ZCOLLECTIONITEM present and empty)",
        },
    },
}

import base64
import binascii
import sqlite3
from collections import Counter
from urllib.parse import unquote_to_bytes

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_biome import fields
from scripts.macos_plists import fold_view_rows, mac_absolute_utc, unique_sources, user_from_path

_STORE = 'MapsSync_0.0.1'
_PLACE_REQUEST = b'placeRequest='

# Field paths inside a decoded placeRequest payload, as iLEAPP's mapsSync.py and
# appleMapsSearchHistory.py read them: 8.1.3 is the query sent, 8.1.7.10000 the text typed.
_SENT_PATH = (8, 1, 3)
_RAW_PATH = (8, 1, 7, 10000)
# Inside a map item message (ZMIXINMAPITEM.ZMAPITEMSTORAGE, or one waypoint of a route request):
# the place name, and the address lines.
_NAME_PATH = (1, 4, 8, 30, 1)
_ADDRESS_PATH = (1, 4, 8, 31, 1, 101, 2, 11)
# A route request (ZHISTORYITEM.ZROUTEREQUESTSTORAGE) holds one map item message per waypoint at 1.n.2.
_WAYPOINT_PATH = (1, 2)


def _values(blob, path):
    """Every value at a field path, following repeated fields; a value that is not a message ends its branch."""
    current = [blob]
    for number in path:
        found = []
        for item in current:
            if not isinstance(item, (bytes, bytearray)):
                continue
            try:
                found.extend(fields(bytes(item)).get(number, []))
            except ValueError:
                continue
        current = found
    return current


def _texts(blob, path):
    """The length-delimited values at a path, as UTF-8 text, distinct and in order."""
    texts = [bytes(value).decode('utf-8', 'replace') for value in _values(blob, path)
             if isinstance(value, (bytes, bytearray))]
    return list(dict.fromkeys(text for text in texts if text))


def _place_requests(blob, depth=0):
    """Every placeRequest payload in a BLOB, found by walking its protobuf fields.

    A value that starts with 'placeRequest=', or holds '?placeRequest=' or '&placeRequest=' as
    a URL parameter, is taken as text and not parsed further; any other length-delimited value
    is tried as a nested message."""
    found = []
    if not isinstance(blob, (bytes, bytearray)) or depth > 16:
        return found
    try:
        message = fields(bytes(blob))
    except ValueError:
        return found
    for values in message.values():
        for value in values:
            if not isinstance(value, (bytes, bytearray)):
                continue
            value = bytes(value)
            text = _request_parameter(value)
            if text is not None:
                found.append(text)
            else:
                found.extend(_place_requests(value, depth + 1))
    return found


def _request_parameter(value):
    """The placeRequest value of a field holding 'placeRequest=...' alone or as a URL parameter, else None."""
    if value.startswith(_PLACE_REQUEST):
        start = len(_PLACE_REQUEST)
    else:
        for marker in (b'?' + _PLACE_REQUEST, b'&' + _PLACE_REQUEST):
            index = value.find(marker)
            if index != -1:
                start = index + len(marker)
                break
        else:
            return None
    return value[start:].split(b'&', 1)[0]


def _decode_request(encoded):
    """A placeRequest value as payload bytes. Percent escapes are undone; '+' is kept, being base64."""
    raw = unquote_to_bytes(encoded)
    try:
        return base64.b64decode(raw + b'=' * (-len(raw) % 4), validate=True)
    except (binascii.Error, ValueError):
        return None


def place_queries(*blobs):
    """(sent, raw): the distinct 8.1.3 and 8.1.7.10000 texts of every placeRequest in the BLOBs, each joined with '; '."""
    sent, raw, skipped = [], [], 0
    for blob in blobs:
        for encoded in _place_requests(blob):
            payload = _decode_request(encoded)
            if payload is None:
                skipped += 1
                continue
            sent.extend(_texts(payload, _SENT_PATH))
            raw.extend(_texts(payload, _RAW_PATH))
    return '; '.join(dict.fromkeys(sent)), '; '.join(dict.fromkeys(raw)), skipped


def map_item_place(blob):
    """(name, address) of one map item message: its name, and its address lines joined with ', '."""
    names = _texts(blob, _NAME_PATH)
    return (names[0] if names else ''), ', '.join(_texts(blob, _ADDRESS_PATH))


def route_places(blob):
    """(names, addresses) of a route request's waypoints, each joined with ' -> ' in stored order."""
    names, addresses = [], []
    for waypoint in _values(blob, _WAYPOINT_PATH):
        name, address = map_item_place(waypoint)
        names.append(name)
        addresses.append(address)
    if not any(names) and not any(addresses):
        return '', ''
    return ' -> '.join(names), ' -> '.join(addresses)


def _columns(cursor, table):
    try:
        return {row[1].upper() for row in cursor.execute(f'PRAGMA table_info("{table}")')}
    except sqlite3.Error:
        return set()


def _pick(columns, table, name):
    return f'{table}.{name}' if name in columns else 'NULL'


def _entity_names(cursor):
    """{Z_ENT: Z_NAME} from the store's own Z_PRIMARYKEY table; entity numbers differ between builds."""
    try:
        return dict(cursor.execute('SELECT Z_ENT, Z_NAME FROM Z_PRIMARYKEY').fetchall())
    except sqlite3.Error:
        return {}


def _coordinate(first, second):
    """The first of two stored coordinates that is a number, else ''."""
    for value in (first, second):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
    return ''


def _stores(context, label):
    found = [str(p) for p in context.get_files_found() if str(p).replace('\\', '/').endswith('/' + _STORE)]
    return sorted(unique_sources(context, found, sidecars=('-wal',), label=label)[0])


def _log(label, counts):
    if counts:
        logfunc(label + ': ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))


def _history_rows(cursor, counts):
    history = _columns(cursor, 'ZHISTORYITEM')
    if 'Z_PK' not in history:
        counts['stores without a ZHISTORYITEM table'] += 1
        return []
    mixin = _columns(cursor, 'ZMIXINMAPITEM')
    joined = 'ZMAPITEM' in history and 'Z_PK' in mixin
    blob = 'ZMIXINMAPITEM.ZMAPITEMSTORAGE' if joined and 'ZMAPITEMSTORAGE' in mixin else 'NULL'
    query = f'''
        SELECT ZHISTORYITEM.Z_PK, {_pick(history, 'ZHISTORYITEM', 'Z_ENT')},
               {_pick(history, 'ZHISTORYITEM', 'ZCREATETIME')}, {_pick(history, 'ZHISTORYITEM', 'ZMODIFICATIONTIME')},
               {_pick(history, 'ZHISTORYITEM', 'ZQUERY')}, {_pick(history, 'ZHISTORYITEM', 'ZLOCATIONDISPLAY')},
               {_pick(history, 'ZHISTORYITEM', 'ZLATITUDE')}, {_pick(history, 'ZHISTORYITEM', 'ZLONGITUDE')},
               {_pick(history, 'ZHISTORYITEM', 'ZLATITUDE1')}, {_pick(history, 'ZHISTORYITEM', 'ZLONGITUDE1')},
               {_pick(history, 'ZHISTORYITEM', 'ZROUTEREQUESTSTORAGE')}, {blob}
        FROM ZHISTORYITEM
        {'LEFT JOIN ZMIXINMAPITEM ON ZMIXINMAPITEM.Z_PK = ZHISTORYITEM.ZMAPITEM' if joined else ''}
        ORDER BY ZHISTORYITEM.Z_PK'''
    entities = _entity_names(cursor)
    rows = []
    for pk, ent, created, modified, search, display, lat, lon, lat1, lon1, route, item in cursor.execute(query):
        sent, raw, skipped = place_queries(route, item)
        counts['placeRequest values that could not be decoded'] += skipped
        if route is not None:
            name, address = route_places(route)
        else:
            name, address = map_item_place(item) if item is not None else ('', '')
        rows.append((mac_absolute_utc(created), mac_absolute_utc(modified), entities.get(ent, ''),
                     '' if ent is None else ent, search or '', display or '', name, address, sent, raw,
                     _coordinate(lat, lat1), _coordinate(lon, lon1), pk))
    return rows


def _favorite_rows(cursor, counts):
    favorite = _columns(cursor, 'ZFAVORITEITEM')
    if 'Z_PK' not in favorite:
        counts['stores without a ZFAVORITEITEM table'] += 1
        return []
    mixin = _columns(cursor, 'ZMIXINMAPITEM')
    joined = 'ZMAPITEM' in favorite and 'Z_PK' in mixin
    blob = 'ZMIXINMAPITEM.ZMAPITEMSTORAGE' if joined and 'ZMAPITEMSTORAGE' in mixin else 'NULL'
    mlat = 'ZMIXINMAPITEM.ZLATITUDE' if joined and 'ZLATITUDE' in mixin else 'NULL'
    mlon = 'ZMIXINMAPITEM.ZLONGITUDE' if joined and 'ZLONGITUDE' in mixin else 'NULL'
    pick = lambda name: _pick(favorite, 'ZFAVORITEITEM', name)  # noqa: E731
    query = f'''
        SELECT ZFAVORITEITEM.Z_PK, {pick('ZCREATETIME')}, {pick('ZMODIFICATIONTIME')}, {pick('ZCUSTOMNAME')},
               {pick('ZMAPITEMNAME')}, {pick('ZMAPITEMADDRESS')}, {pick('ZORIGINATINGADDRESSSTRING')},
               {pick('ZMAPITEMCATEGORY')}, {pick('ZTYPE')}, {pick('ZSOURCE')}, {pick('ZHIDDEN')},
               {pick('ZLATITUDE')}, {pick('ZLONGITUDE')}, {mlat}, {mlon}, {blob}
        FROM ZFAVORITEITEM
        {'LEFT JOIN ZMIXINMAPITEM ON ZMIXINMAPITEM.Z_PK = ZFAVORITEITEM.ZMAPITEM' if joined else ''}
        ORDER BY ZFAVORITEITEM.Z_PK'''
    rows = []
    for (pk, created, modified, custom, map_name, map_address, originating, category, ztype, source, hidden,
         lat, lon, mlat_value, mlon_value, item) in cursor.execute(query):
        sent, raw, skipped = place_queries(item)
        counts['placeRequest values that could not be decoded'] += skipped
        blob_name, blob_address = map_item_place(item) if item is not None else ('', '')
        rows.append((mac_absolute_utc(created), mac_absolute_utc(modified), custom or '', map_name or blob_name,
                     map_address or blob_address or originating or '', category or '',
                     _stored(ztype), _stored(source), _stored(hidden), sent, raw,
                     _coordinate(lat, mlat_value), _coordinate(lon, mlon_value), pk))
    return rows


def _guides(cursor, entities):
    """{collection item Z_PK: [guide titles]} through the Z_<n>PLACES join table, found from the schema."""
    by_name = {name: ent for ent, name in entities.items()}
    collection_ent = by_name.get('Collection')
    if collection_ent is None:
        return {}
    table = f'Z_{collection_ent}PLACES'
    columns = _columns(cursor, table)
    owner = f'Z_{collection_ent}COLLECTIONS'
    places = [name for name in columns if name.endswith('PLACES') and name != owner]
    if owner not in columns or len(places) != 1 or 'ZTITLE' not in _columns(cursor, 'ZCOLLECTION'):
        return {}
    guides = {}
    query = (f'SELECT "{table}"."{places[0]}", ZCOLLECTION.ZTITLE FROM "{table}" '
             f'JOIN ZCOLLECTION ON ZCOLLECTION.Z_PK = "{table}"."{owner}" ORDER BY ZCOLLECTION.Z_PK')
    for item, title in cursor.execute(query):
        guides.setdefault(item, []).append(title or '')
    return guides


def _collection_rows(cursor, counts):
    item_columns = _columns(cursor, 'ZCOLLECTIONITEM')
    if 'Z_PK' not in item_columns:
        counts['stores without a ZCOLLECTIONITEM table'] += 1
        return []
    mixin = _columns(cursor, 'ZMIXINMAPITEM')
    joined = 'ZMAPITEM' in item_columns and 'Z_PK' in mixin
    blob = 'ZMIXINMAPITEM.ZMAPITEMSTORAGE' if joined and 'ZMAPITEMSTORAGE' in mixin else 'NULL'
    mlat = 'ZMIXINMAPITEM.ZLATITUDE' if joined and 'ZLATITUDE' in mixin else 'NULL'
    mlon = 'ZMIXINMAPITEM.ZLONGITUDE' if joined and 'ZLONGITUDE' in mixin else 'NULL'
    pick = lambda name: _pick(item_columns, 'ZCOLLECTIONITEM', name)  # noqa: E731
    query = f'''
        SELECT ZCOLLECTIONITEM.Z_PK, {pick('Z_ENT')}, {pick('ZCREATETIME')}, {pick('ZMODIFICATIONTIME')},
               {pick('ZCUSTOMNAME')}, {pick('ZMAPITEMNAME')}, {pick('ZMAPITEMADDRESS')}, {pick('ZMAPITEMCATEGORY')},
               {pick('ZPLACEITEMNOTE')}, {pick('ZTYPE')}, {pick('ZLATITUDE')}, {pick('ZLONGITUDE')},
               {mlat}, {mlon}, {blob}
        FROM ZCOLLECTIONITEM
        {'LEFT JOIN ZMIXINMAPITEM ON ZMIXINMAPITEM.Z_PK = ZCOLLECTIONITEM.ZMAPITEM' if joined else ''}
        ORDER BY ZCOLLECTIONITEM.Z_PK'''
    entities = _entity_names(cursor)
    rows_read = list(cursor.execute(query))
    guides = _guides(cursor, entities)
    rows = []
    for (pk, ent, created, modified, custom, map_name, map_address, category, note, ztype,
         lat, lon, mlat_value, mlon_value, item) in rows_read:
        sent, raw, skipped = place_queries(item)
        counts['placeRequest values that could not be decoded'] += skipped
        blob_name, blob_address = map_item_place(item) if item is not None else ('', '')
        rows.append((mac_absolute_utc(created), mac_absolute_utc(modified), entities.get(ent, ''), custom or '',
                     map_name or blob_name, map_address or blob_address, category or '', note or '',
                     _stored(ztype), '; '.join(guides.get(pk, [])), sent, raw,
                     _coordinate(lat, mlat_value), _coordinate(lon, mlon_value), pk))
    return rows


def _stored(value):
    return '' if value is None else value


def _run(context, label, reader):
    data_list, read, counts = [], [], Counter()
    for path in _stores(context, label):
        database = open_sqlite_db_readonly(path)
        if database is None:
            counts['stores that could not be opened'] += 1
            continue
        try:
            rows = reader(database.cursor(), counts)
        except sqlite3.Error as error:
            counts[f'stores that could not be read ({type(error).__name__})'] += 1
            continue
        finally:
            database.close()
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        data_list.extend(row + (user, relative) for row in rows)
        if rows:
            read.append(path)
    _log(label, +counts)
    return fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosMapsSync(context):
    data_headers = (('Created', 'datetime'), ('Modified', 'datetime'), 'Entity (Z_PRIMARYKEY Name)',
                    'Z_ENT (As Stored)', 'Location Search', 'Location Display', 'Place Name', 'Address',
                    'Query (Sent)', 'Query (Raw)', ('Latitude', 'latitude'), ('Longitude', 'longitude'),
                    'Item Number', 'User', 'Source File')
    data_list, source = _run(context, 'Maps History (MapsSync)', _history_rows)
    return data_headers, data_list, source


@artifact_processor
def macosMapsFavorites(context):
    data_headers = (('Created', 'datetime'), ('Modified', 'datetime'), 'Custom Name', 'Place Name', 'Address',
                    'Category', 'Favorite Type (As Stored)', 'Source (As Stored)', 'Hidden (As Stored)',
                    'Query (Sent)', 'Query (Raw)', ('Latitude', 'latitude'), ('Longitude', 'longitude'),
                    'Item Number', 'User', 'Source File')
    data_list, source = _run(context, 'Maps Favorites (MapsSync)', _favorite_rows)
    return data_headers, data_list, source


@artifact_processor
def macosMapsCollectionItems(context):
    data_headers = (('Created', 'datetime'), ('Modified', 'datetime'), 'Entity (Z_PRIMARYKEY Name)', 'Custom Name',
                    'Place Name', 'Address', 'Category', 'Note', 'Item Type (As Stored)', 'Guides',
                    'Query (Sent)', 'Query (Raw)', ('Latitude', 'latitude'), ('Longitude', 'longitude'),
                    'Item Number', 'User', 'Source File')
    data_list, source = _run(context, 'Maps Saved Places and Guides (MapsSync)', _collection_rows)
    return data_headers, data_list, source
