"""Windows WebCache (WebCacheV01.dat) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
WebCacheV01.dat is the WinINet / Internet Explorer / legacy-Edge web cache, an
ESE (Extensible Storage Engine) database. It is read with the ESE reader adapted
from impacket in scripts/vendor/impacket_ese.py.

Structure (per libyal esedb-kb, MSIE web cache format documentation, cited in the
notes, and confirmed against the file): a Containers table maps each ContainerId
to a Name (History, Content, Cookies, DOMStore, ...) and a Directory, and each
container's records live in a Container_<id> table. The Url and Filename columns
are large-text; AccessedTime, ModifiedTime, CreationTime and ExpiryTime are
little-endian Windows FILETIMEs.
"""

import binascii
from datetime import datetime, timedelta, timezone

try:
    from scripts.vendor import impacket_ese
    from scripts import ese_rows
except ImportError:
    impacket_ese = None
    ese_rows = None

from scripts.ilapfuncs import artifact_processor, logfunc

_CONTAINERS = "Containers"
_WEBCACHE = "webcachev01.dat"
# A container walk stops after visiting this many records, so a corrupt page's
# forward pointer cannot loop forever.
_ROW_CAP = 5_000_000

__artifacts_v2__ = {
    "webcacheHistory": {
        "name": "WebCache History",
        "description": "URL and local-file history recorded by WinINet, Internet "
                       "Explorer and legacy Edge, from the History containers of "
                       "WebCacheV01.dat, with the access time and access count.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-28",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the WebCacheV01.dat History containers: the container "
                 "named History plus the periodic MSHist01 containers, whose name is "
                 "MSHist01 followed by two YYYYMMDD dates marking the history period "
                 "the container groups; entry access times are UTC and can fall outside "
                 "that named boundary. Read from "
                 "WebCacheV01.dat, named in Source File, with the ESE reader adapted "
                 "from impacket in scripts/vendor. Each row is one entry in a History "
                 "Container_<id> table. URL is the entry's Url column as stored; a "
                 "History entry stores a leading marker and the account name ahead of "
                 "the target, which may be a web address or a local file:// path. "
                 "Accessed (UTC) and Expires (UTC) are "
                 "the AccessedTime and ExpiryTime columns, little-endian Windows "
                 "FILETIMEs; a value of 0 or an out-of-range value is shown blank. "
                 "Access Count is the entry's AccessCount as stored. Container is the "
                 "container Name. An entry records that the URL or file was accessed "
                 "through these components, not who was at the keyboard. A record ESE "
                 "marks deleted (its fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are "
                 "counted in the run log, and no History container read on the tested "
                 "images held either. A value this artifact reports that ESE stores "
                 "apart from its record (the record flags it fSeparated, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53) "
                 "is read from the table's long value tree "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/lv.hxx#L36-L62); "
                 "one that cannot be assembled from that tree (a piece missing, for "
                 "example, or a piece stored compressed, which is not decompressed) is "
                 "left blank, and the run log counts it and names the reason. The "
                 "History containers on the tested "
                 "images stored 7 URLs apart, all on lonewolf_win10 and 519 to 922 "
                 "characters long, and every one was assembled. A "
                 "WebCacheV01.dat with no Containers table gives this artifact no "
                 "container index, so it yields no rows for that file and the file is "
                 "named in the run log. The .jfm and .log transaction logs beside "
                 "WebCacheV01.dat are not replayed. Format: libyal esedb-kb, MSIE web "
                 "cache, https://github.com/libyal/esedb-kb/blob/main/documentation/"
                 "MSIE%20web%20cache.asciidoc",
        "paths": ("*/AppData/Local/Microsoft/Windows/WebCache/WebCacheV01.dat",),
        "output_types": ["standard"],
        "artifact_icon": "history",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 45 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 42 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 179 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 132 rows",
        },
    },
    "webcacheContent": {
        "name": "WebCache Content",
        "description": "Web resources cached by WinINet, Internet Explorer and "
                       "legacy Edge, from the Content containers of WebCacheV01.dat, "
                       "with the source URL, cached file name, size and times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-28",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the WebCacheV01.dat Content containers (container Name "
                 "Content), which index the INetCache of Internet Explorer, legacy "
                 "Edge and packaged apps. Read from WebCacheV01.dat, named in Source "
                 "File, with the ESE reader adapted from impacket in scripts/vendor. "
                 "Each row is one entry in a Content Container_<id> table. URL is the "
                 "requested resource (Url column) and Filename is the cached copy's "
                 "local file name, both as stored. File Size is the FileSize column "
                 "in bytes. Accessed (UTC), Modified (UTC) and Expires (UTC) are the "
                 "AccessedTime, ModifiedTime and ExpiryTime columns, little-endian "
                 "Windows FILETIMEs; a 0 or out-of-range value is shown blank. Access "
                 "Count is AccessCount as stored. Cache Directory is the container's "
                 "Directory, which names the application whose cache the entry "
                 "belongs to. An entry records that the resource was fetched and "
                 "cached, not that a person deliberately requested it. A record ESE "
                 "marks deleted (its fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are "
                 "counted in the run log. The Content containers read held 3, 7, 8 and "
                 "0 records ESE marks deleted on af_case2_win10, lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10, one per container, and none the "
                 "reader could not convert. A value this artifact reports that ESE "
                 "stores apart from its record (the record flags it fSeparated, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53) "
                 "is read from the table's long value tree "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/lv.hxx#L36-L62); "
                 "one that cannot be assembled from that tree (a piece missing, for "
                 "example, or a piece stored compressed, which is not decompressed) is "
                 "left blank, and the run log counts it and names the reason. The "
                 "Content containers on the tested "
                 "images stored 14 URLs apart on pc_mus_001_win11, each 703 characters "
                 "long, and 102 on szechuan_win10, 511 to 2,342 characters long, and "
                 "every one was assembled; no other value this artifact reports was "
                 "stored apart. A "
                 "WebCacheV01.dat with no Containers table gives this artifact no "
                 "container index, so it yields no rows for that file and the file is "
                 "named in the run log. The .jfm and .log transaction logs beside "
                 "WebCacheV01.dat are not replayed. Format: libyal esedb-kb, MSIE web "
                 "cache, https://github.com/libyal/esedb-kb/blob/main/documentation/"
                 "MSIE%20web%20cache.asciidoc",
        "paths": ("*/AppData/Local/Microsoft/Windows/WebCache/WebCacheV01.dat",),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 197 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 50 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 40 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1,853 rows",
        },
    },
}


def _norm_row(row):
    out = {}
    for key, value in row.items():
        name = key.decode("latin-1") if isinstance(key, (bytes, bytearray)) else key
        out[name] = value
    return out


def _text(value):
    """Decode a WebCache text column. Short text (Name, Directory) arrives as a
    str; large text (Url, Filename) arrives as ASCII-hex bytes from impacket."""
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        try:
            value = binascii.unhexlify(value)
        except (binascii.Error, ValueError):
            value = bytes(value)
        for encoding in ("utf-8", "utf-16-le"):
            try:
                return value.decode(encoding).rstrip("\x00")
            except (UnicodeDecodeError, ValueError):
                continue
        return value.decode("latin-1", "replace").rstrip("\x00")
    return str(value).rstrip("\x00")


def _filetime_datetime(value):
    """A little-endian Windows FILETIME: 100-ns intervals since 1601-01-01 UTC."""
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=int(value) / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _cell(value):
    return "" if value is None else value


def _containers(database, label="", relative_source=""):
    """Return [(container_id, name, directory)] from the Containers table."""
    out = []
    walk = ese_rows.TableRows(database, _CONTAINERS, long_value_columns={"Name", "Directory"})
    for row in walk:
        row = _norm_row(row)
        out.append((row.get("ContainerId"),
                    _text(row.get("Name")),
                    _text(row.get("Directory"))))
    if walk.summary():
        logfunc(f"{label}: {relative_source}, {walk.summary()}")
    return out


def _read_container(database, table_names, container_id, name, directory,
                    row_builder, rows, label, relative_source=""):
    """Append a built row per entry of one Container_<id> table.

    A record ESE marks deleted is not read, and a record the ESE reader cannot
    convert is skipped so the rest of the table is still read; both are counted
    in the run log. Returns the number skipped.
    """
    table = "Container_%s" % container_id
    if table not in table_names:
        return 0
    walk = ese_rows.TableRows(database, table, cap=_ROW_CAP, long_value_columns={"Url", "Filename"})
    for row in walk:
        rows.append(row_builder(_norm_row(row), name, directory))
    if walk.summary():
        logfunc(f"{label}: {relative_source}, {walk.summary()}")
    return walk.deleted + walk.unreadable


def _table_names(database):
    return {t.decode("latin-1") if isinstance(t, (bytes, bytearray)) else t
            for t in database._ESENT_DB__tables.keys()}  # pylint: disable=protected-access


def _run(context, headers, select, row_builder, label):
    data_list = []
    sources = []
    if impacket_ese is None:
        logfunc(f"{label}: the vendored ESE reader is not available")
        return headers, data_list, ""
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith(_WEBCACHE)]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            database = impacket_ese.ESENT_DB(source)
            try:
                database.mountDB()
                table_names = _table_names(database)
                rows = []
                if _CONTAINERS not in table_names:
                    # A WebCacheV01.dat that never populated (for example the
                    # SYSTEM account's store on a device nobody browsed with)
                    # carries the ESE system tables but no Containers table, so
                    # openTable would return None and there are no history or
                    # content containers to enumerate.
                    logfunc(f"{label}: {relative_source} has no Containers "
                            "table, so it holds no WebCache history or content")
                else:
                    for container_id, name, directory in _containers(
                            database, label, relative_source):
                        if not select(name):
                            continue
                        _read_container(database, table_names, container_id,
                                        name, directory, row_builder, rows,
                                        label, relative_source)
                for row in rows:
                    data_list.append(row + (relative_source,))
                    rows_here += 1
            finally:
                database.close()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"{label}: could not read {relative_source}: {exc}")
            continue
        if rows_here:
            sources.append(source)
    return headers, data_list, "\n".join(sources)


@artifact_processor
def webcacheHistory(context):
    headers = (('Accessed (UTC)', 'datetime'), 'URL', 'Access Count',
               ('Expires (UTC)', 'datetime'), 'Container', 'Source File')

    def is_history(name):
        return name == "History" or name.startswith("MSHist01")

    def build(row, name, _directory):
        return (_filetime_datetime(row.get('AccessedTime')),
                _text(row.get('Url')),
                _cell(row.get('AccessCount')),
                _filetime_datetime(row.get('ExpiryTime')),
                name)

    return _run(context, headers, is_history, build, "WebCache History")


@artifact_processor
def webcacheContent(context):
    headers = (('Accessed (UTC)', 'datetime'), 'URL', 'Filename',
               'File Size (bytes)', ('Modified (UTC)', 'datetime'),
               ('Expires (UTC)', 'datetime'), 'Access Count', 'Cache Directory',
               'Source File')

    def is_content(name):
        return name == "Content"

    def build(row, _name, directory):
        return (_filetime_datetime(row.get('AccessedTime')),
                _text(row.get('Url')),
                _text(row.get('Filename')),
                _cell(row.get('FileSize')),
                _filetime_datetime(row.get('ModifiedTime')),
                _filetime_datetime(row.get('ExpiryTime')),
                _cell(row.get('AccessCount')),
                directory)

    return _run(context, headers, is_content, build, "WebCache Content")
