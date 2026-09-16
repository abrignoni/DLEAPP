"""Windows Thumbnail Cache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange / ThumbCacheViewer approach. The
thumbcache_*.db files are parsed following libyal libwtcdb's Windows Explorer
thumbnail cache format documentation.

Each cache entry is keyed by a 64-bit ThumbnailCacheId. The Windows Search index
(Windows.edb on Windows 10 and earlier, Windows.db on Windows 11) records a
System.ThumbnailCacheId for the items it has indexed, so joining the two
resolves a cached thumbnail to the file it was made for. The thumbnail image is
extracted and shown inline where the entry carries one.
"""

import os
import struct
import sqlite3
import binascii

try:
    from scripts.vendor import impacket_ese
except ImportError:
    impacket_ese = None

from scripts.ilapfuncs import artifact_processor, logfunc, check_in_embedded_media

_THUMBCACHE_PREFIX = "thumbcache_"
_WINDOWS_EDB = "windows.edb"
_WINDOWS_DB = "windows.db"
_ROW_CAP = 5_000_000

# Image signatures seen in the thumbnail cache; the entry data is stored as one
# of these (older caches use BMP, newer ones PNG/JPEG).
_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "PNG", "png"),
    (b"\xff\xd8\xff", "JPEG", "jpg"),
    (b"BM", "BMP", "bmp"),
    (b"GIF8", "GIF", "gif"),
)

__artifacts_v2__ = {
    "windowsThumbcache": {
        "name": "Thumbnail Cache",
        "description": "Thumbnails Windows cached for files and folders, with the "
                       "cached image shown inline and the file name correlated from "
                       "the Windows Search index where the item was indexed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "none (Windows.edb correlation uses the vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the thumbcache_*.db files in a user's Explorer folder, "
                 "read from the files named in Source File. Each row is one cache "
                 "entry that carries a thumbnail image or resolves to a file name, or "
                 "both; a cache entry that is a repeated placeholder with neither is "
                 "not surfaced. Thumbnail is the cached image extracted from the "
                 "entry and shown inline; the entry data is sniffed and only a real "
                 "image (PNG, JPEG, BMP or GIF) is shown, with its format in Data "
                 "Format and byte count in Data Size. Cache Size is the thumbnail "
                 "size the file name encodes (for example 256 from thumbcache_256.db, "
                 "or sr, wide, exif, idx as stored). Cache Entry ID is the entry's "
                 "64-bit ThumbnailCacheId as hex. Identifier is the entry's own "
                 "identifier string as stored, which is sometimes a file path, a "
                 "shell folder GUID or the entry id, and is not a reliable file name. "
                 "Correlated Path and Correlated Name are the item's path and name "
                 "from the Windows Search index, joined on the index's "
                 "System_ThumbnailCacheId matching this entry's id; they are blank "
                 "when the search index did not index the item (many cached "
                 "thumbnails, in particular user interface icons, are for items the "
                 "index does not cover, so on a system with few indexed user files "
                 "most image entries carry no name). The search index is read from "
                 "Windows.edb (Windows 10 and earlier, with the vendored ESE reader) "
                 "or Windows.db (Windows 11, SQLite, read only) when present beside "
                 "the thumbnail caches. A cached thumbnail records that Explorer "
                 "generated a preview for the item; it does not record who viewed it, "
                 "and the item may since have been moved or deleted, so a thumbnail "
                 "can outlive its file. One item is cached at several sizes, so it can "
                 "appear once per thumbcache size file. Format: libyal libwtcdb, "
                 "Windows Explorer thumbnail cache database format, https://github."
                 "com/libyal/libwtcdb/blob/main/documentation/Windows%20Explorer%20"
                 "thumbnail%20cache%20database%20format.asciidoc",
        "paths": ("*/Explorer/[Tt]humbcache_*.[Dd][Bb]",
                  "*/Search/Data/Applications/Windows/[Ww]indows.[Ee][Dd][Bb]",
                  "*/Search/Data/Applications/Windows/[Ww]indows.[Dd][Bb]"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "image",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 142 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 144 rows",
        },
    },
}


def _sniff(data):
    for signature, label, extension in _SIGNATURES:
        if data.startswith(signature):
            return label, extension
    return "", ""


def _cache_size(source):
    base = os.path.basename(source).lower()
    if base.startswith(_THUMBCACHE_PREFIX) and base.endswith(".db"):
        return base[len(_THUMBCACHE_PREFIX):-3]
    return ""


def _parse_thumbcache(path):
    """Yield (entry_id, identifier, data, format_label, extension) for each live
    cache entry, following the libwtcdb format. Only allocated entries are read
    (the walk stops at the first available entry offset)."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:4] != b"CMMM" or len(data) < 24:
        return []
    version = struct.unpack_from("<I", data, 4)[0]
    first = struct.unpack_from("<I", data, 16)[0]
    available = struct.unpack_from("<I", data, 20)[0]
    header_size = 56 if version >= 0x1A else 48   # Win8+ inserts width/height
    limit = available if 0 < available <= len(data) else len(data)
    entries = []
    offset = first
    while offset + header_size <= limit:
        if data[offset:offset + 4] != b"CMMM":
            break
        size = struct.unpack_from("<I", data, offset + 4)[0]
        entry_id = struct.unpack_from("<Q", data, offset + 8)[0]
        id_size = struct.unpack_from("<I", data, offset + 16)[0]
        pad_size = struct.unpack_from("<I", data, offset + 20)[0]
        data_size = struct.unpack_from("<I", data, offset + 24)[0]
        id_start = offset + header_size
        identifier = ""
        if 0 < id_size <= 2048 and id_start + id_size <= len(data):
            identifier = data[id_start:id_start + id_size].decode("utf-16-le", "replace").rstrip("\x00")
        blob = b""
        blob_start = id_start + id_size + pad_size
        if 0 < data_size and blob_start + data_size <= len(data):
            blob = data[blob_start:blob_start + data_size]
        label, extension = _sniff(blob) if blob else ("", "")
        entries.append((entry_id, identifier, blob if label else b"", label, extension))
        if size < header_size or offset + size > limit:
            break
        offset += size
    return entries


def _norm_row(row):
    out = {}
    for key, value in row.items():
        name = key.decode("latin-1") if isinstance(key, (bytes, bytearray)) else key
        out[name] = value
    return out


def _as_cache_id(value):
    if isinstance(value, int):
        return value
    if isinstance(value, (bytes, bytearray)):
        raw = value
        try:
            raw = binascii.unhexlify(value)
        except (binascii.Error, ValueError):
            pass
        if len(raw) == 8:
            return struct.unpack("<Q", raw)[0]
    return None


def _edb_map(path):
    """Map System.ThumbnailCacheId to (path, name) from Windows.edb."""
    result = {}
    if impacket_ese is None:
        return result
    database = impacket_ese.ESENT_DB(path)
    try:
        database.mountDB()
        cursor = database.openTable("SystemIndex_PropertyStore")
        if cursor is None:
            return result
        id_col = path_col = name_col = None
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
            if id_col is None:
                for key in row:
                    if key.endswith("System_ThumbnailCacheId"):
                        id_col = key
                    elif key.endswith("System_ItemPathDisplay"):
                        path_col = key
                    elif key.endswith("System_ItemNameDisplay"):
                        name_col = key
                if id_col is None:
                    return result
            cache_id = _as_cache_id(row.get(id_col))
            if cache_id is not None:
                result[cache_id] = (_edb_text(row.get(path_col)), _edb_text(row.get(name_col)))
        return result
    finally:
        database.close()


def _edb_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.rstrip("\x00")
    if isinstance(value, (bytes, bytearray)):
        try:
            return binascii.unhexlify(value).decode("utf-16-le", "replace").rstrip("\x00")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            return ""
    return str(value)


def _db_map(path):
    """Map System.ThumbnailCacheId to (path, name) from Windows.db."""
    result = {}
    connection = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    try:
        cursor = connection.cursor()
        store = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND "
            "name LIKE 'SystemIndex\\_%\\_PropertyStore' ESCAPE '\\' LIMIT 1").fetchone()
        if not store:
            return result
        store = store[0]
        meta = store + "_Metadata"

        def column(name):
            row = cursor.execute(f'SELECT Id FROM "{meta}" WHERE Name = ?', (name,)).fetchone()
            return row[0] if row else None

        id_col = column("System.ThumbnailCacheId")
        path_col = column("System.ItemPathDisplay")
        name_col = column("System.ItemNameDisplay")
        if id_col is None:
            return result
        wanted = tuple(c for c in (id_col, path_col, name_col) if c is not None)
        items = {}
        for work_id, column_id, value in cursor.execute(
                f'SELECT WorkId, ColumnId, Value FROM "{store}" '
                f'WHERE ColumnId IN ({",".join("?" * len(wanted))})', wanted):
            items.setdefault(work_id, {})[column_id] = value
        for props in items.values():
            cache_id = _as_cache_id(props.get(id_col))
            if cache_id is not None:
                result[cache_id] = (_db_text(props.get(path_col)), _db_text(props.get(name_col)))
        return result
    finally:
        connection.close()


def _db_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.rstrip("\x00")
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-16-le").rstrip("\x00")
        except (UnicodeDecodeError, ValueError):
            return value.decode("latin-1", "replace").rstrip("\x00")
    return str(value)


@artifact_processor
def windowsThumbcache(context):
    data_headers = (('Thumbnail', 'media'), 'Correlated Path', 'Correlated Name',
                    'Cache Size', 'Cache Entry ID', 'Data Format',
                    'Data Size (bytes)', 'Identifier', 'Source File')
    data_list = []
    sources = []
    files = [str(f) for f in context.get_files_found()]
    thumb_files = [f for f in files if os.path.basename(f).lower().startswith(_THUMBCACHE_PREFIX)]
    if not thumb_files:
        return data_headers, data_list, ""

    id_map = {}
    for source in files:
        low = source.lower()
        try:
            if low.endswith(_WINDOWS_EDB):
                id_map.update(_edb_map(source))
            elif low.endswith(_WINDOWS_DB):
                id_map.update(_db_map(source))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Thumbnail Cache: could not read search index {context.get_relative_path(source)}: {exc}')

    for source in thumb_files:
        relative_source = context.get_relative_path(source)
        cache_size = _cache_size(source)
        try:
            entries = _parse_thumbcache(source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Thumbnail Cache: could not read {relative_source}: {exc}')
            continue
        # One item is cached once per file; collapse repeated placeholders, keeping
        # the entry that carries an image.
        best = {}
        for entry_id, identifier, blob, label, extension in entries:
            current = best.get(entry_id)
            if current is None or (blob and not current[1]):
                best[entry_id] = (identifier, blob, label, extension)
        rows_here = 0
        for entry_id, (identifier, blob, label, extension) in best.items():
            correlated = id_map.get(entry_id, ("", ""))
            if not blob and not correlated[0] and not correlated[1]:
                continue
            media_ref = ""
            if blob:
                media_ref = check_in_embedded_media(
                    source, blob, name=correlated[1] or ("%016x.%s" % (entry_id, extension)),
                    force_extension=extension) or ""
            data_list.append((
                media_ref, correlated[0], correlated[1], cache_size,
                "%016x" % entry_id, label, len(blob) if blob else "",
                identifier, relative_source))
            rows_here += 1
        if rows_here:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)
