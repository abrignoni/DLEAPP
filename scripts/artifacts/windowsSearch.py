"""Windows Search index (Windows.edb) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Search artifacts. Windows.edb is
an ESE (Extensible Storage Engine) database and is read with the ESE reader
adapted from impacket in scripts/vendor/impacket_ese.py.

The indexed-item properties live in the SystemIndex_PropertyStore table, whose
columns are named <number>-<property> (for example 4445-System_ItemPathDisplay).
The number is not fixed: the tested indexes give System_ItemPathDisplay 4428, 4445
and 4447. Each column is therefore found in the index's own schema by the property
name after the first '-'. Some string properties in this store are ESE 7-bit
compressed; the vendored reader decodes them.
"""

import struct
import binascii
from datetime import datetime, timedelta, timezone

try:
    from scripts.vendor import impacket_ese
    from scripts import ese_rows
except ImportError:
    impacket_ese = None
    ese_rows = None

from scripts.ilapfuncs import artifact_processor, logfunc

_PROPERTY_STORE = "SystemIndex_PropertyStore"
_WINDOWS_EDB = "windows.edb"

# Guard against a cursor that stops advancing; the store is far smaller than this.
_ROW_CAP = 5_000_000

# System_Size on folders and other non-file items holds eight 0x2A bytes rather
# than a byte count; reported blank.
_SIZE_SENTINEL = b"\x2a" * 8

# SystemIndex_PropertyStore properties read here. The table names each column
# <number>-<property>, and the number is assigned per index, so a column is found
# by the property name after the first '-' (see _property_columns).
_C_WORKID = "WorkID"
_P_NAME = "System_ItemNameDisplay"
_P_PATH = "System_ItemPathDisplay"
_P_URL = "System_ItemUrl"
_P_TYPE = "System_ItemTypeText"
_P_KIND = "System_KindText"
_P_SIZE = "System_Size"
_P_GATHER = "System_Search_GatherTime"
_P_MODIFIED = "System_DateModified"
_P_CREATED = "System_DateCreated"
_P_ACCESSED = "System_DateAccessed"
_PROPERTIES = (_P_NAME, _P_PATH, _P_URL, _P_TYPE, _P_KIND, _P_SIZE, _P_GATHER,
               _P_MODIFIED, _P_CREATED, _P_ACCESSED)

__artifacts_v2__ = {
    "windowsSearch": {
        "name": "Windows Search Index",
        "description": "Items indexed by Windows Search from Windows.edb, with the "
                       "item path, name, type, size and the gather, modified, "
                       "created and accessed times the index recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-28",
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
                 "reported blank (present on 473 of the 587 rows on af_case2_win10, "
                 "439 of 822 on lonewolf_win10 and 1,491 of 1,641 on szechuan_win10, "
                 "every one of them an item whose Type is File folder or that stores "
                 "no type). Type and Kind are System_ItemTypeText and System_KindText "
                 "as stored, blank where the index holds none. Item Name, Item Path "
                 "and Gather Time were filled on every row of the three tested "
                 "indexes, and Kind on 518 of 587, 632 of 822 and 1,505 of 1,641. "
                 "Each property is read from the column the index's own schema names "
                 "for it: the table names each column <number>-<property> and the "
                 "number is assigned per index (System_ItemPathDisplay is 4445 on "
                 "af_case2_win10, 4428 on lonewolf_win10 and 4447 on szechuan_win10), "
                 "so the column is found by the property name after the first '-'; a "
                 "property no column carries, or that more than one column carries, is "
                 "left blank and named in the run log. "
                 "Some string properties in this store are ESE 7-bit compressed; the "
                 "reader adapted from impacket in scripts/vendor decodes them. Read "
                 "from Windows.edb, named in Source File. An indexed entry records "
                 "that Windows Search gathered the item at Gather Time; it does not "
                 "by itself establish that a user opened the item, and the index can "
                 "retain an entry after the item is removed from disk: on "
                 "lonewolf_win10 the Item Path of 5 indexed items leads in the MFT only "
                 "to a record no longer in use. Windows.edb "
                 "is the Windows 10 and earlier Windows Search store; Windows 11 "
                 "22H2 and later replaced it with Windows.db (a SQLite database), "
                 "which this artifact does not read. A record ESE marks deleted (its "
                 "fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are "
                 "counted in the run log, and none of the Windows.edb files on the "
                 "tested images held either. A property value this artifact reports that "
                 "ESE stores apart from its record (the record flags it fSeparated, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53) "
                 "is read from the table's long value tree "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/lv.hxx#L36-L62); "
                 "one that cannot be assembled from that tree (a piece missing, for "
                 "example, or a piece stored compressed, which unlike a compressed value "
                 "kept in the record is not decompressed) is left blank although the "
                 "index holds a value, and the run log counts it and names the reason. "
                 "None of "
                 "the properties this artifact reports was stored apart on the tested "
                 "images. The transaction logs beside Windows.edb "
                 "are not replayed.",
        "paths": ("*/[Ss]earch/[Dd]ata/[Aa]pplications/[Ww]indows/"
                  "[Ww]indows.[Ee][Dd][Bb]",),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 587 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 822 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1,641 rows",
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


def _property_columns(database, label="Windows Search", relative_source=""):
    """{property: column name} for the properties read here, from the table's own schema.

    A property no column carries, or that more than one column carries, is left out
    and named in the run log, so its column is blank rather than read from a guess."""
    tables = database._ESENT_DB__tables  # pylint: disable=protected-access
    key = next((k for k in tables if (k.decode("latin-1") if isinstance(k, (bytes, bytearray)) else k)
                == _PROPERTY_STORE), None)
    if key is None:
        return {}
    found = {}
    for column in tables[key]["Columns"]:
        name = column.decode("latin-1") if isinstance(column, (bytes, bytearray)) else column
        if "-" in name:
            found.setdefault(name.split("-", 1)[1], []).append(name)
    resolved = {}
    for prop in _PROPERTIES:
        columns = found.get(prop, [])
        if len(columns) == 1:
            resolved[prop] = columns[0]
        elif not columns:
            logfunc(f"{label}: {relative_source} has no column for {prop}, so it is blank")
        else:
            logfunc(f"{label}: {relative_source} has {len(columns)} columns for {prop} "
                    f"({', '.join(sorted(columns))}), so it is blank")
    return resolved


def _read_property_store(source, label="Windows Search", relative_source=""):
    """Open Windows.edb and build a row per SystemIndex_PropertyStore entry.

    A record ESE marks deleted is not read, and a record the ESE reader cannot
    convert is skipped so the rest of the table is still read, under a row cap;
    both are counted in the run log."""
    database = ese_rows.ESEDatabase(source)
    try:
        database.mountDB()
        rows = []
        columns = _property_columns(database, label, relative_source)

        def value(row, prop):
            return row.get(columns[prop]) if prop in columns else None

        walk = ese_rows.TableRows(database, _PROPERTY_STORE, cap=_ROW_CAP,
                                  long_value_columns=set(columns.values()))
        for row in walk:
            row = _norm_row(row)
            rows.append((
                _filetime(value(row, _P_GATHER)),
                _filetime(value(row, _P_MODIFIED)),
                _filetime(value(row, _P_CREATED)),
                _filetime(value(row, _P_ACCESSED)),
                _text(value(row, _P_NAME)),
                _text(value(row, _P_PATH)),
                _text(value(row, _P_URL)),
                _text(value(row, _P_TYPE)),
                _text(value(row, _P_KIND)),
                _size(value(row, _P_SIZE)),
                _cell(row.get(_C_WORKID)),
            ))
        if walk.summary():
            logfunc(f"{label}: {relative_source}, {walk.summary()}")
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
            rows = _read_property_store(source, "Windows Search", relative_source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"Windows Search: could not read {relative_source}: {exc}")
            continue
        for row in rows:
            data_list.append(row + (relative_source,))
            rows_here += 1
        if rows_here:
            sources.append(source)
    return headers, data_list, "\n".join(sources)
