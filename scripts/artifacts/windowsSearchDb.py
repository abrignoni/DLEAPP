"""Windows Search index (Windows.db, Windows 11) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Search work. This is the SQLite
sibling of windowsSearch.py: Windows 11 (22H2 and later) replaced the ESE
Windows.edb search index with a SQLite database, Windows.db.

Windows.db keeps indexed-item properties as (WorkId, ColumnId, Value) triples in
a SystemIndex_<n>_PropertyStore table, with a SystemIndex_<n>_PropertyStore_
Metadata table mapping each ColumnId to its System.* property name. This artifact
pivots the triples back to one row per indexed item.
"""

import sqlite3
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_WINDOWS_DB = "windows.db"

# System.* property names surfaced, resolved to their ColumnId per database
# through the metadata table (so a ColumnId that differs between images is fine).
_GATHER = "System.Search.GatherTime"
_MODIFIED = "System.DateModified"
_CREATED = "System.DateCreated"
_ACCESSED = "System.DateAccessed"
_NAME = "System.ItemNameDisplay"
_PATH = "System.ItemPathDisplay"
_URL = "System.ItemUrl"
_TYPE = "System.ItemTypeText"
_KIND = "System.KindText"
_SIZE = "System.Size"
_WANTED = (_GATHER, _MODIFIED, _CREATED, _ACCESSED, _NAME, _PATH, _URL,
           _TYPE, _KIND, _SIZE)

__artifacts_v2__ = {
    "windowsSearchDb": {
        "name": "Windows 11 Search Index",
        "description": "Items indexed by Windows Search from the Windows 11 Windows.db "
                       "index, with the item path, name, type, size and the gather, "
                       "modified, created and accessed times the index recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "none",
        "category": "Windows",
        "notes": "Rows from the SystemIndex_<n>_PropertyStore table in Windows.db, the "
                 "Windows 11 (22H2 and later) Windows Search index, read from the file "
                 "named in Source File and opened read only. Windows.db keeps each "
                 "indexed item's properties as (WorkId, ColumnId, Value) rows; the "
                 "SystemIndex_<n>_PropertyStore_Metadata table maps each ColumnId to "
                 "its System.* property name, and this artifact pivots the rows back "
                 "to one row per item, keyed by Work ID. Item Name, Item Path and Item "
                 "URL are the System_ItemNameDisplay, System_ItemPathDisplay and "
                 "System_ItemUrl properties as stored; Item Path is the display path "
                 "and Item URL is the stored locator. Gather Time, Date Modified, Date "
                 "Created and Date Accessed (UTC) are Windows FILETIMEs from the "
                 "System_Search_GatherTime, System_DateModified, System_DateCreated "
                 "and System_DateAccessed properties; Gather Time is the time the "
                 "Windows Search indexer recorded for the item and the other three are "
                 "the file system times the index stored. Size (bytes) is System_Size, "
                 "blank for folders and other items the index stored no size for. Type "
                 "and Kind are System_ItemTypeText and System_KindText as stored, blank "
                 "where the index holds none. An indexed entry records that Windows "
                 "Search gathered the item at Gather Time; it does not by itself "
                 "establish that a user opened the item, and the index can retain an "
                 "entry after the item is removed from disk. This is the SQLite Windows "
                 "11 counterpart of the Windows Search Index artifact, which reads the "
                 "older ESE Windows.edb; the two do not appear together on one system. "
                 "The property names are read from the index's own metadata table in "
                 "the file. Format: libyal esedb-kb / Windows Search notes on the "
                 "Windows.db schema, https://github.com/libyal/esedb-kb/blob/main/"
                 "documentation/Windows%20Search.asciidoc",
        "paths": ("*/[Ss]earch/[Dd]ata/[Aa]pplications/[Ww]indows/"
                  "[Ww]indows.[Dd][Bb]",),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2272 rows",
        },
    },
}


def _filetime(value):
    if isinstance(value, (bytes, bytearray)) and len(value) == 8:
        value = struct.unpack("<Q", value)[0]
    if not isinstance(value, int) or value == 0:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.rstrip("\x00")
    if isinstance(value, (bytes, bytearray)):
        # Short-text properties stored as a BLOB are UTF-16LE.
        try:
            return value.decode("utf-16-le").rstrip("\x00")
        except (UnicodeDecodeError, ValueError):
            return value.decode("latin-1", "replace").rstrip("\x00")
    return str(value)


def _size(value):
    if isinstance(value, int):
        return value
    if isinstance(value, (bytes, bytearray)) and len(value) <= 8:
        return int.from_bytes(value, "little")
    return ""


def _table_names(cursor):
    """Find the PropertyStore and its Metadata table (the catalog number varies)."""
    meta = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND "
        "name LIKE 'SystemIndex\\_%\\_PropertyStore_Metadata' ESCAPE '\\' LIMIT 1"
    ).fetchone()
    store = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND "
        "name LIKE 'SystemIndex\\_%\\_PropertyStore' ESCAPE '\\' LIMIT 1"
    ).fetchone()
    return (store[0] if store else None), (meta[0] if meta else None)


def _read_windows_db(source):
    connection = sqlite3.connect(f"file:{source}?mode=ro&immutable=1", uri=True)
    try:
        cursor = connection.cursor()
        store, meta = _table_names(cursor)
        if not store or not meta:
            return []
        colid = {}
        for name in _WANTED:
            row = cursor.execute(
                f'SELECT Id FROM "{meta}" WHERE Name = ?', (name,)).fetchone()
            if row:
                colid[name] = row[0]
        if _PATH not in colid and _URL not in colid and _NAME not in colid:
            return []
        wanted_ids = tuple(colid.values())
        placeholders = ",".join("?" * len(wanted_ids))
        items = {}
        for work_id, column_id, value in cursor.execute(
                f'SELECT WorkId, ColumnId, Value FROM "{store}" '
                f'WHERE ColumnId IN ({placeholders})', wanted_ids):
            items.setdefault(work_id, {})[column_id] = value

        def get(props, name):
            return props.get(colid.get(name)) if name in colid else None

        rows = []
        for work_id in sorted(items):
            props = items[work_id]
            path = _text(get(props, _PATH)) or _text(get(props, _URL))
            name = _text(get(props, _NAME))
            if not path and not name:
                continue
            rows.append((
                _filetime(get(props, _GATHER)),
                _filetime(get(props, _MODIFIED)),
                _filetime(get(props, _CREATED)),
                _filetime(get(props, _ACCESSED)),
                name,
                _text(get(props, _PATH)),
                _text(get(props, _URL)),
                _text(get(props, _TYPE)),
                _text(get(props, _KIND)),
                _size(get(props, _SIZE)),
                work_id,
            ))
        return rows
    finally:
        connection.close()


@artifact_processor
def windowsSearchDb(context):
    data_headers = (('Gather Time (UTC)', 'datetime'),
                    ('Date Modified (UTC)', 'datetime'),
                    ('Date Created (UTC)', 'datetime'),
                    ('Date Accessed (UTC)', 'datetime'),
                    'Item Name', 'Item Path', 'Item URL', 'Type', 'Kind',
                    'Size (bytes)', 'Work ID', 'Source File')
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith(_WINDOWS_DB)]:
        relative_source = context.get_relative_path(source)
        try:
            rows = _read_windows_db(source)
        except sqlite3.Error as exc:
            logfunc(f'Windows Search (Windows.db): could not read {relative_source}: {exc}')
            continue
        for row in rows:
            data_list.append(row + (relative_source,))
        if rows:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)
