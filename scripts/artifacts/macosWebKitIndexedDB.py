__artifacts_v2__ = {
    "macosWebKitIndexedDBDatabases": {
        "name": "WebKit IndexedDB Databases",
        "description": "IndexedDB databases kept by Safari and by other macOS apps that show web content with "
                       "WebKit: origin, database name and version, object stores and record counts.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": (
            "One row per IndexedDB database. Reads IndexedDB.sqlite3 in two layouts: current, under an app's "
            'WebKit WebsiteData folder, with a file named origin two folders above the database folder, and '
            'older, Library/Safari/Databases/___IndexedDB/v1/. Origin and Top Origin are decoded from the '
            "origin file with the WebKit Local Storage artifact's reader, and both are empty when the file is "
            'missing or does not decode, which did not happen on the tested images. In the older layout the '
            'folder under v1 is named for the top origin, and a database partitioned under another site sits '
            "one folder deeper under its own origin's folder (IDBDatabaseIdentifier.cpp, WebKit source at "
            "commit 35c61160953bce52ee5828033bd5a079b7db22a8): Origin is the deeper folder's name as stored and"
            " Top Origin the top folder's name, or, for a database directly under the top folder, Origin is "
            "that folder's name and Top Origin is empty. Every older-layout database on the two macOS 11.2.1 "
            'images sat directly under one folder, so the partitioned form was not exercised. Origin and Top '
            'Origin were identical on every row of the macOS 15.4 and 26.2 images, so storage partitioned under'
            ' another top site was not exercised in the current layout either. Database Name is the '
            'DatabaseName value of IDBDatabaseInfo, decoded by how SQLite stores it: a TEXT value as UTF-8, and'
            " a BLOB as the name's UTF-16 code units, which is how WebKit writes it at metadata version 2 "
            '(SQLiteIDBBackingStore.cpp lines 491-493 and SQLiteStatement.cpp lines 108-120, same commit). On '
            'the tested images every metadata version 1 name was TEXT and every version 2 name a BLOB; the '
            'folder named by a hash held the SHA-256 of the decoded name for all 24 databases. The database is '
            "read with the -wal applied, and the record keys are declared with WebKit's own IDBKEY collation, "
            'which is registered here only so the tables open: nothing is sorted by key. The IndexInfo, '
            'IndexRecords, KeyGenerators, BlobRecords and BlobFiles tables and the keyPath and autoInc columns '
            'of ObjectStoreInfo are not read; BlobRecords and BlobFiles were empty on the tested images, so '
            'values kept in separate blob files were not exercised. App Folder is the container folder or the '
            'folder under Library/WebKit, or Safari for the older layout; the Library/WebKit form outside a '
            'container was not exercised. When a logical extraction holds the same file under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy (database and '
            '-wal) is not read again and the run log counts it. No row on the tested images was folded from '
            'differing copies. No member of evidencelocker_macos14 matches the declared paths. Database Version'
            ' (as stored) and Metadata Version (as stored) are the DatabaseVersion and MetadataVersion values '
            'as stored. Object Stores lists each ObjectStoreInfo name with its number of rows in Records, one '
            "per line, and Records is the database's total. A database with no record still gives a row: 1, 2, "
            '4 and 3 of the databases on magnet2021_macos_bigsur, dleapp_macos_bigsur, '
            'mvs2026_macbookpro_macos15 and adams_macbookpro_macos26 held none. Metadata Version held one value'
            ' (1) on every row of the macOS 11.2.1 and 15.4 images, and the macOS 26.2 image held 7 databases '
            'at version 2 and 2 at version 1. Database Version held one value on every row of '
            'dleapp_macos_bigsur and adams_macbookpro_macos26. App Folder held one value on every row of '
            'magnet2021_macos_bigsur, dleapp_macos_bigsur and adams_macbookpro_macos26, and on '
            "mvs2026_macbookpro_macos15 3 of the 6 databases came from a third-party app's WebKit store. No "
            'table read here has a timestamp column.'
        ),
        "paths": ('*/WebsiteData/*/IndexedDB/*/IndexedDB.sqlite3*', '*/WebsiteData/*/origin',
                  '*/Library/Safari/Databases/___IndexedDB/*/IndexedDB.sqlite3*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 6 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 6 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 9 rows",
        },
    },
    "macosWebKitIndexedDBRecords": {
        "name": "WebKit IndexedDB Records",
        "description": "Records of the IndexedDB databases kept by Safari and by other macOS apps that show web "
                       "content with WebKit: object store, decoded key and the size of the stored value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": (
            "One row per row of a database's Records table, from databases that hold at least one. Reads "
            "IndexedDB.sqlite3 in two layouts: current, under an app's WebKit WebsiteData folder, with a file "
            'named origin two folders above the database folder, and older, '
            'Library/Safari/Databases/___IndexedDB/v1/. Origin and Top Origin are decoded from the origin file '
            "with the WebKit Local Storage artifact's reader, and both are empty when the file is missing or "
            'does not decode, which did not happen on the tested images. In the older layout the folder under '
            'v1 is named for the top origin, and a database partitioned under another site sits one folder '
            "deeper under its own origin's folder (IDBDatabaseIdentifier.cpp, WebKit source at commit "
            "35c61160953bce52ee5828033bd5a079b7db22a8): Origin is the deeper folder's name as stored and Top "
            "Origin the top folder's name, or, for a database directly under the top folder, Origin is that "
            "folder's name and Top Origin is empty. Every older-layout database on the two macOS 11.2.1 images "
            'sat directly under one folder, so the partitioned form was not exercised. Origin and Top Origin '
            'were identical on every row of the macOS 15.4 and 26.2 images, so storage partitioned under '
            'another top site was not exercised in the current layout either. Database Name is the DatabaseName'
            ' value of IDBDatabaseInfo, decoded by how SQLite stores it: a TEXT value as UTF-8, and a BLOB as '
            "the name's UTF-16 code units, which is how WebKit writes it at metadata version 2 "
            '(SQLiteIDBBackingStore.cpp lines 491-493 and SQLiteStatement.cpp lines 108-120, same commit). On '
            'the tested images every metadata version 1 name was TEXT and every version 2 name a BLOB; the '
            'folder named by a hash held the SHA-256 of the decoded name for all 24 databases. The database is '
            "read with the -wal applied, and the record keys are declared with WebKit's own IDBKEY collation, "
            'which is registered here only so the tables open: nothing is sorted by key. The IndexInfo, '
            'IndexRecords, KeyGenerators, BlobRecords and BlobFiles tables and the keyPath and autoInc columns '
            'of ObjectStoreInfo are not read; BlobRecords and BlobFiles were empty on the tested images, so '
            'values kept in separate blob files were not exercised. App Folder is the container folder or the '
            'folder under Library/WebKit, or Safari for the older layout; the Library/WebKit form outside a '
            'container was not exercised. When a logical extraction holds the same file under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy (database and '
            '-wal) is not read again and the run log counts it. No row on the tested images was folded from '
            'differing copies. No member of evidencelocker_macos14 matches the declared paths. Object Store is '
            "the ObjectStoreInfo name of the record's objectStoreID, or the number itself when no "
            'ObjectStoreInfo row has it, which did not happen on the tested images. Key is the record key '
            "decoded as WebKit's deserializeIDBKeyData reads it (IDBSerialization.cpp lines 124-162 and "
            '271-389, same commit): a version byte 0x00, then a type byte and its data, with numbers and dates '
            'as little-endian doubles, strings as a 32-bit length and UTF-16 code units, binary keys as a '
            '64-bit size and bytes, shown as hex, and arrays as a 64-bit count and their keys, shown in '
            'brackets with a comma between elements and no type per element. A whole number is shown without a '
            'decimal point, and the min and max key types are shown as (min) and (max). A date key is shown as '
            'milliseconds since 1970-01-01 UTC, which is what WebKit stores for a Date key '
            '(IDBBindingUtilities.cpp, same commit). An array nested deeper than 64 levels is reported as not '
            'decoded, a limit WebKit does not have. Key Type names the type, or says why a key was not decoded:'
            " an older key stored as a property list, beginning with 'b', is not decoded, and the run log "
            'counts keys that were not. Every key on the tested images decoded, as a string or a number; '
            'binary, date and array keys were not exercised. Value Size (bytes) is the length of the stored '
            "value. The value is the record's value as WebKit stored it (IDBValue data, "
            'SQLiteIDBBackingStore.cpp, same commit) and is not decoded, so what a record holds is not shown '
            'here. Records on the tested images: 76, 1, 5 and 28 on magnet2021_macos_bigsur, '
            'dleapp_macos_bigsur, mvs2026_macbookpro_macos15 and adams_macbookpro_macos26, the same counts a '
            'separate read of each Records table gave. Key Type held one value (string) on every row of '
            'magnet2021_macos_bigsur. App Folder held one value on every row of magnet2021_macos_bigsur and '
            'adams_macbookpro_macos26, and 1 of the 5 rows on mvs2026_macbookpro_macos15 came from a '
            "third-party app's WebKit store. The Records table has no timestamp column; a key can be a date, "
            'and none was on the tested images.'
        ),
        "paths": ('*/WebsiteData/*/IndexedDB/*/IndexedDB.sqlite3*', '*/WebsiteData/*/origin',
                  '*/Library/Safari/Databases/___IndexedDB/*/IndexedDB.sqlite3*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 76 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 5 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 28 rows",
        },
    },
}

import math
import os
import sqlite3
import struct
from datetime import datetime, timedelta, timezone

from scripts.artifacts.macosWebKitLocalStorage import _app, read_origin_file
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import fold_view_rows, unique_sources

_NAME = 'IndexedDB.sqlite3'
_LEGACY_MARKER = '/___IndexedDB/'
_KEY_VERSION = 0x00
_MIN, _NUMBER, _DATE, _STRING, _BINARY, _ARRAY, _MAX = 0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xFF
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class _BadKey(Exception):
    pass


def _take(data, offset, size):
    if size < 0 or offset + size > len(data):
        raise _BadKey('short')
    return data[offset:offset + size], offset + size


def _decode_key(data, offset, depth=0):
    """(key text, key type, next offset) for one key buffer, as WebKit's decodeKey reads it."""
    if depth > 64:
        raise _BadKey('nesting')
    kind, offset = _take(data, offset, 1)
    kind = kind[0]
    if kind == _MIN:
        return '(min)', 'min', offset
    if kind == _MAX:
        return '(max)', 'max', offset
    if kind in (_NUMBER, _DATE):
        raw, offset = _take(data, offset, 8)
        value = struct.unpack('<d', raw)[0]
        if kind == _NUMBER:
            return (str(int(value)) if value.is_integer() and abs(value) < 2 ** 53 else repr(value)), 'number', offset
        if math.isfinite(value):
            try:
                return (_EPOCH + timedelta(milliseconds=value)).isoformat(), 'date', offset
            except OverflowError:
                pass
        return repr(value), 'date', offset
    if kind == _STRING:
        raw, offset = _take(data, offset, 4)
        length = struct.unpack('<I', raw)[0]
        raw, offset = _take(data, offset, length * 2)
        return raw.decode('utf-16-le', 'replace'), 'string', offset
    if kind == _BINARY:
        raw, offset = _take(data, offset, 8)
        size = struct.unpack('<Q', raw)[0]
        raw, offset = _take(data, offset, size)
        return raw.hex(), 'binary', offset
    if kind == _ARRAY:
        raw, offset = _take(data, offset, 8)
        count = struct.unpack('<Q', raw)[0]
        if count > len(data):
            raise _BadKey('count')
        parts = []
        for _index in range(count):
            text, _kind, offset = _decode_key(data, offset, depth + 1)
            parts.append(text)
        return '[' + ', '.join(parts) + ']', 'array', offset
    raise _BadKey(f'type 0x{kind:02x}')


def decode_key(data):
    """(key text, key type) for a stored record key; ('', 'not decoded: <reason>') when it does not decode."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        return '', 'not decoded: empty'
    data = bytes(data)
    if data[:1] == b'b':
        return '', 'not decoded: older property list key'
    if data[0] != _KEY_VERSION:
        return '', f'not decoded: version 0x{data[0]:02x}'
    try:
        text, kind, offset = _decode_key(data, 1)
    except _BadKey as error:
        return '', f'not decoded: {error}'
    if offset != len(data):
        return '', 'not decoded: bytes left over'
    return text, kind


def _text(value):
    if value is None:
        return ''
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode('utf-8', 'replace')
    return str(value)


def _database_name(raw, storage_class):
    """The stored database name: a TEXT value as UTF-8, a BLOB as the UTF-16 code units WebKit binds."""
    if isinstance(raw, (bytes, bytearray)) and storage_class == b'blob':
        return bytes(raw).decode('utf-16-le', 'replace')
    return _text(raw)


def _origin(path, relative):
    """(origin, top origin) for a database: the origin file two folders up, or the older layout's folder names.

    The older layout is v1/<top origin folder>/<hash>/ or, for a database partitioned under another site,
    v1/<top origin folder>/<origin folder>/<hash>/.
    """
    normalized = '/' + relative.replace('\\', '/')
    if _LEGACY_MARKER in normalized:
        parts = normalized.split(_LEGACY_MARKER, 1)[1].split('/')[1:]
        if len(parts) >= 4:
            return parts[1], parts[0]
        return parts[0], ''
    # .../WebsiteData/Default/<top hash>/<origin hash>/IndexedDB/<database hash>/IndexedDB.sqlite3
    top, origin = read_origin_file(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(path))), 'origin'))
    return origin, top


def _open(path):
    db = open_sqlite_db_readonly(path)
    if db is None:
        return None
    db.text_factory = bytes
    # The key columns are declared COLLATE IDBKEY; only plain reads run here, no ordering by key.
    db.create_collation('IDBKEY', lambda left, right: (left > right) - (left < right))
    return db


def _databases(context, label):
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == _NAME]
    paths, _skipped = unique_sources(context, found, sidecars=('-wal',), label=label)
    for path in paths:
        relative = context.get_relative_path(path)
        db = _open(path)
        if db is None:
            continue
        try:
            info = {_text(key): (value, kind) for key, value, kind in
                    db.execute('SELECT key, value, typeof(value) FROM IDBDatabaseInfo')}
            stores = {row[0]: _text(row[1]) for row in db.execute('SELECT id, name FROM ObjectStoreInfo')}
            records = db.execute('SELECT objectStoreID, key, length(value) FROM Records ORDER BY rowid').fetchall()
        except sqlite3.Error as error:
            logfunc(f'{label}: {relative} not read: {error}')
            db.close()
            continue
        db.close()
        yield path, relative, info, stores, records


@artifact_processor
def macosWebKitIndexedDBDatabases(context):
    data_headers = ('Origin', 'Top Origin', 'Database Name', 'Database Version (as stored)',
                    'Metadata Version (as stored)', 'Object Stores', 'Records', 'App Folder', 'Source File')
    rows, read = [], []
    for path, relative, info, stores, records in _databases(context, 'WebKit IndexedDB Databases'):
        read.append(path)
        origin, top = _origin(path, relative)
        metadata = _text(info.get('MetadataVersion', (None,))[0])
        counts = {}
        for store_id, _key, _size in records:
            counts[store_id] = counts.get(store_id, 0) + 1
        listed = '\n'.join(f'{stores[store_id]} ({counts.get(store_id, 0)})' for store_id in sorted(stores))
        rows.append((origin, top, _database_name(*info.get('DatabaseName', (None, None))),
                     _text(info.get('DatabaseVersion', (None,))[0]), metadata, listed, len(records),
                     _app(relative), relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosWebKitIndexedDBRecords(context):
    data_headers = ('Origin', 'Top Origin', 'Database Name', 'Object Store', 'Key', 'Key Type',
                    'Value Size (bytes)', 'App Folder', 'Source File')
    rows, read, undecoded = [], [], 0
    for path, relative, info, stores, records in _databases(context, 'WebKit IndexedDB Records'):
        if not records:
            continue
        read.append(path)
        origin, top = _origin(path, relative)
        name = _database_name(*info.get('DatabaseName', (None, None)))
        app = _app(relative)
        for store_id, key, size in records:
            text, kind = decode_key(key)
            undecoded += kind.startswith('not decoded')
            rows.append((origin, top, name, stores.get(store_id, str(store_id)), text, kind,
                         '' if size is None else size, app, relative))
    if undecoded:
        logfunc(f'WebKit IndexedDB Records: {undecoded} key(s) not decoded; Key Type says why')
    return data_headers, fold_view_rows(rows), '\n'.join(read)
