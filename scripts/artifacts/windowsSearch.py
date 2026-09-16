"""Windows Search index (Windows.edb) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Search artifacts. Windows.edb is
an ESE (Extensible Storage Engine) database and is read with the ESE reader
adapted from impacket in scripts/vendor/impacket_ese.py.

The indexed-item properties live in the SystemIndex_PropertyStore table, whose
columns are named for the System.* property they hold (for example
4445-System_ItemPathDisplay). The column names used here are read from the
index's own schema in the file. Some string properties in this store are ESE
7-bit compressed; the vendored reader decodes them.
"""

import struct
import binascii
from datetime import datetime, timedelta, timezone

try:
    from scripts.vendor import impacket_ese
except ImportError:
    impacket_ese = None

from scripts.ilapfuncs import artifact_processor, logfunc

_PROPERTY_STORE = "SystemIndex_PropertyStore"
_WINDOWS_EDB = "windows.edb"

# Guard against a cursor that stops advancing; the store is far smaller than this.
_ROW_CAP = 5_000_000

# System_Size on folders and other non-file items holds eight 0x2A bytes rather
# than a byte count; reported blank.
_SIZE_SENTINEL = b"\x2a" * 8

# SystemIndex_PropertyStore column names, as stored in the index schema.
_C_WORKID = "WorkID"
_C_NAME = "4441-System_ItemNameDisplay"
_C_PATH = "4445-System_ItemPathDisplay"
_C_URL = "33-System_ItemUrl"
_C_TYPE = "5-System_ItemTypeText"
_C_KIND = "4455-System_KindText"
_C_SIZE = "13F-System_Size"
_C_GATHER = "4629F-System_Search_GatherTime"
_C_MODIFIED = "15F-System_DateModified"
_C_CREATED = "16F-System_DateCreated"
_C_ACCESSED = "17F-System_DateAccessed"

__artifacts_v2__ = {
    "windowsSearch": {
        "name": "Windows Search Index",
        "description": "Items indexed by Windows Search from Windows.edb, with the "
                       "item path, name, type, size and the gather, modified, "
                       "created and accessed times the index recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SystemIndex_PropertyStore table in Windows.edb, the "
                 "Windows Search index. Each row is one indexed item, keyed by Work "
                 "ID. Item Name, Item Path and Item URL are the "
                 "System_ItemNameDisplay, System_ItemPathDisplay and System_ItemUrl "
                 "properties as stored; Item Path is the display path and Item URL "
                 "is the stored locator (for a file it is a file: URL of the same "
                 "location, and on other item kinds it can carry a different "
                 "scheme). Gather Time, Date Modified, Date Created and Date "
                 "Accessed are Windows FILETIMEs (UTC) from the "
                 "System_Search_GatherTime, System_DateModified, System_DateCreated "
                 "and System_DateAccessed properties; Gather Time is the time the "
                 "Windows Search indexer recorded for the item and the other three "
                 "are the file system times the index stored. Size (bytes) is "
                 "System_Size decoded from its stored 8-byte value; folders and "
                 "other non-file items store a placeholder of eight 0x2A bytes in "
                 "this property rather than a byte count, and that placeholder is "
                 "reported blank (on the tested image it was present on 473 of 587 "
                 "rows, all of them folders or items with no stored type, and on no "
                 "item that carried a real size). Type and Kind are "
                 "System_ItemTypeText and System_KindText as stored, blank where the "
                 "index holds none. "
                 "Column names are read from the index's own schema in the file. "
                 "Some string properties in this store are ESE 7-bit compressed; the "
                 "reader adapted from impacket in scripts/vendor decodes them. Read "
                 "from Windows.edb, named in Source File. An indexed entry records "
                 "that Windows Search gathered the item at Gather Time; it does not "
                 "by itself establish that a user opened the item, and the index can "
                 "retain an entry after the item is removed from disk. Windows.edb "
                 "is the Windows 10 and earlier Windows Search store; Windows 11 "
                 "22H2 and later replaced it with Windows.db (a SQLite database), "
                 "which this artifact does not read. The transaction logs beside "
                 "Windows.edb are not replayed.",
        "paths": ("*/[Ss]earch/[Dd]ata/[Aa]pplications/[Ww]indows/"
                  "[Ww]indows.[Ee][Dd][Bb]",),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 587 rows",
        },
    },
}


def _norm_row(row):
    """impacket returns column-name keys as bytes; decode them to str."""
    out = {}
    for key, value in row.items():
        name = key.decode("latin-1") if isinstance(key, (bytes, bytearray)) else key
        out[name] = value
    return out


def _raw_bytes(value):
    """A tagged binary column is returned as ASCII hex bytes; recover the raw
    bytes. A short-text column is already a str, which has no raw form here."""
    if isinstance(value, (bytes, bytearray)):
        try:
            return binascii.unhexlify(value)
        except (binascii.Error, ValueError):
            return bytes(value)
    return None


def _text(value):
    """Present a string property; blank when absent."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.rstrip("\x00")
    raw = _raw_bytes(value)
    if raw is None:
        return ""
    return raw.decode("utf-16-le", "replace").rstrip("\x00")


def _filetime(value):
    """A Windows FILETIME (100-ns intervals since 1601-01-01 UTC), stored as an
    8-byte little-endian integer."""
    raw = _raw_bytes(value)
    if raw is None or len(raw) < 8:
        return ""
    ticks = struct.unpack_from("<Q", raw)[0]
    if ticks == 0:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ticks / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _size(value):
    """System_Size as a byte count; the folder placeholder is reported blank."""
    raw = _raw_bytes(value)
    if raw is None or len(raw) < 8 or raw == _SIZE_SENTINEL:
        return ""
    return struct.unpack_from("<Q", raw)[0]


def _cell(value):
    return "" if value is None else value


def _edb_sources(context):
    return [str(f) for f in context.get_files_found()
            if str(f).lower().endswith(_WINDOWS_EDB)]


def _read_property_store(source):
    """Open Windows.edb and build a row per SystemIndex_PropertyStore entry.

    getNextRow can raise on an occasional record but advances the cursor first,
    so the reader skips the bad record and continues under a row cap."""
    database = impacket_ese.ESENT_DB(source)
    try:
        database.mountDB()
        rows = []
        cursor = database.openTable(_PROPERTY_STORE)
        if cursor is None:
            return rows
        seen = 0
        while seen < _ROW_CAP:
            seen += 1
            try:
                row = database.getNextRow(cursor)
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            if row is None:
                break
            row = _norm_row(row)
            rows.append((
                _filetime(row.get(_C_GATHER)),
                _filetime(row.get(_C_MODIFIED)),
                _filetime(row.get(_C_CREATED)),
                _filetime(row.get(_C_ACCESSED)),
                _text(row.get(_C_NAME)),
                _text(row.get(_C_PATH)),
                _text(row.get(_C_URL)),
                _text(row.get(_C_TYPE)),
                _text(row.get(_C_KIND)),
                _size(row.get(_C_SIZE)),
                _cell(row.get(_C_WORKID)),
            ))
        return rows
    finally:
        database.close()


@artifact_processor
def windowsSearch(context):
    headers = (('Gather Time (UTC)', 'datetime'),
               ('Date Modified (UTC)', 'datetime'),
               ('Date Created (UTC)', 'datetime'),
               ('Date Accessed (UTC)', 'datetime'),
               'Item Name', 'Item Path', 'Item URL', 'Type', 'Kind',
               'Size (bytes)', 'Work ID', 'Source File')
    data_list = []
    sources = []
    if impacket_ese is None:
        logfunc("Windows Search: the vendored ESE reader is not available")
        return headers, data_list, ""
    for source in _edb_sources(context):
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            rows = _read_property_store(source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"Windows Search: could not read {relative_source}: {exc}")
            continue
        for row in rows:
            data_list.append(row + (relative_source,))
            rows_here += 1
        if rows_here:
            sources.append(source)
    return headers, data_list, "\n".join(sources)
