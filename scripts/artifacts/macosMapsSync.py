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
        "notes": "PLACEHOLDER",
        "paths": ("*/Library/Containers/com.apple.Maps/Data/Maps/MapsSync_0.0.1*",),
        "output_types": "all",
        "artifact_icon": "map-pin",
        "sample_data": {},
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
        "notes": "PLACEHOLDER",
        "paths": ("*/Library/Containers/com.apple.Maps/Data/Maps/MapsSync_0.0.1*",),
        "output_types": "all",
        "artifact_icon": "star",
        "sample_data": {},
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
        "notes": "PLACEHOLDER",
        "paths": ("*/Library/Containers/com.apple.Maps/Data/Maps/MapsSync_0.0.1*",),
        "output_types": "all",
        "artifact_icon": "bookmark",
        "sample_data": {},
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
