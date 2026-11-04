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
import re
import struct
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlsplit

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
# The large columns whose values ESE may store apart from the record, read from
# the long value tree by default.
_LONG_VALUE_COLUMNS = frozenset({"Url", "Filename"})

__artifacts_v2__ = {
    "webcacheHistory": {
        "name": "WebCache History",
        "description": "URL and local-file history recorded by WinINet, Internet "
                       "Explorer and legacy Edge, from the History containers of "
                       "WebCacheV01.dat, with the access time and access count.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-10-24",
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
                 "characters long, and every one was assembled. In a WebCacheV01.dat cut "
                 "short, such as a partial copy, a page of a container that lies past the "
                 "end of the file is passed over, with every page beneath it, and the pages that "
                 "remain are read, and "
                 "the run log names the container and counts the pages it reached that lie past the "
                 "end. Copies "
                 "of af_case2_win10's file cut to 90, 75, 50 and 25 percent of its "
                 "length gave 42, 41, 35 and 12 of the 42 rows the whole file gives. A "
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
        "last_update_date": "2026-10-24",
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
                 "stored apart. In a WebCacheV01.dat cut short, such as a partial copy, "
                 "a page of a container that lies past the end of the file is passed over, with every"
                 " page beneath it, and the pages that remain are read, and the run log names the "
                 "container and counts the pages it reached that lie past the end. Copies of "
                 "af_case2_win10's file cut to "
                 "90, 75, 50 and 25 percent of its length gave 50, 50, 48 and 0 of the "
                 "50 rows the whole file gives. A "
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
    "webcacheLocationParameters": {
        "name": "WebCache Location Parameters",
        "description": "Latitude and longitude carried in the clientLocation or location parameter of URLs cached in "
                       "WebCacheV01.dat, with the accuracy, provider and timestamp parameters of the same URL and the "
                       "cache entry's creation time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Reads every container the WebCacheV01.dat Containers table names, with the same ESE reader as WebCache "
                 "History and WebCache Content, and gives one row per cached URL whose query has a parameter named "
                 "exactly clientLocation or location whose URL-decoded value is two numbers joined by \"|\", the first in "
                 "-90 to 90 and the second in -180 to 180. A parameter of either name with another value is counted in "
                 "the run log and gives no row. Latitude and Longitude are the first and second number. On szechuan_win10 "
                 "the second number is outside the latitude range on all 20 rows, so that value is latitude then "
                 "longitude; on pc_mus_001_win11 both numbers fit either range, and latitude first rests on that order "
                 "and on a published description of these URLs (https://thelocalh0st.com/posts/webcache-geolocation/), "
                 "not on a Microsoft source. Accuracy (as stored) and Provider (as stored) are the clientLocationAccuracy "
                 "and clientLocationProvider parameters of the same URL after URL decoding; their units and meaning are "
                 "not established here. Location Time (UTC) is the clientLocationTimestamp parameter, read as UTC from "
                 "its trailing Z; on all 14 rows of pc_mus_001_win11 it was under 2 seconds before Cache Entry Created "
                 "(UTC), the entry's CreationTime FILETIME: 0.8 to 1.9 seconds, with the parameter itself carrying whole "
                 "seconds. For a location parameter the artifact reads no accuracy, provider or time, so those columns "
                 "are blank on its rows; the 20 szechuan_win10 URLs carried no such parameters. Location (as stored) is "
                 "the parameter value after URL decoding, and URL is the cached URL. Cache Directory is the container's "
                 "Directory, which names the application whose cache the entry belongs to. A row records what a cached "
                 "request carried, not that the device or a person was at that point at that time, and not who chose the "
                 "location. Tested rows: on pc_mus_001_win11 (Windows 11 22H2) 14 rows, all clientLocation, all from the "
                 "Content container under the MicrosoftWindows.Client.WebExperience_cw5n1h2txyewy package's cache, 14 "
                 "distinct points with 17 decimal places; Parameter held clientLocation, Provider (as stored) held WiFi "
                 "and Cache Directory held one value on all 14 rows. On szechuan_win10 (Windows 10 2004) 20 rows, all "
                 "location, all from the Content container under the microsoft.microsoftedge_8wekyb3d8bbwe package's "
                 "cache in two directories: Parameter held location, Latitude, Longitude and Location (as stored) held "
                 "one value on all 20 rows, with 4 and 3 decimal places, and Location Time (UTC), Accuracy (as stored) "
                 "and Provider (as stored) were empty on all 20. What sets the location parameter is not established. "
                 "Other parameter names that can carry a position (lat and lon, latlng, ll, coords) are not read; on the "
                 "tested images, in every container, the ll, lng and loc parameters found held single numbers, language "
                 "tags and URLs, not points. Not read: records ESE marks deleted, and the .log transaction logs, which "
                 "are not replayed. A byte search for the parameter name as UTF-16LE, which is not a reading of the "
                 "database, matched more times in pc_mus_001_win11's file than the 14 rows account for (92 matches in the "
                 "file and 32 in its logs; the 14 rows account for 56, four names each) and 5 times in "
                 "hexordia_mvs2025_win11's file, which gave no row; those copies are not reported. The replay helper "
                 "DLEAPP uses for other ESE stores refuses these files, whose pages are 32 KiB. Writes a KML file of the "
                 "points.",
        "paths": ("*/AppData/Local/Microsoft/Windows/WebCache/WebCacheV01.dat",),
        "output_types": ["html", "tsv", "timeline", "lava", "kml"],
        "artifact_icon": "map-pin",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 14 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 20 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no cached URL carries a location parameter)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no cached URL carries a location parameter)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no cached URL the reader reaches carries a location parameter)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no cached URL carries a location parameter)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no cached URL carries a location parameter)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no cached URL carries a location parameter)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no cached URL carries a location parameter)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no cached URL carries a location parameter)",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no WebCacheV01.dat)",
        },
    },
    "webcacheDownloads": {
        "name": "WebCache Downloads",
        "description": "Files downloaded with Internet Explorer and legacy Edge, from the iedownload "
                       "containers of WebCacheV01.dat, with the download URL, the path the file was saved "
                       "to, its size and the record's access time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the WebCacheV01.dat containers named iedownload. Read from WebCacheV01.dat, "
                 "named in Source File, with the ESE reader adapted from impacket in scripts/vendor. "
                 "Each row is one entry in an iedownload Container_<id> table. Accessed (UTC) is the "
                 "entry's AccessedTime column, a little-endian Windows FILETIME; a 0 or out-of-range "
                 "value is shown blank. The other columns come from the entry's ResponseHeaders value, "
                 "which on these entries is a binary record, not HTTP headers. No published "
                 "description of that record was found (libyal esedb-kb lists the column only as "
                 "large binary data), so what is read from it rests on the six entries on the tested "
                 "images, compared with a second record of the same download on each. The record "
                 "starts with a 32-bit value that was 140 on the Windows 10 entries, whose cache "
                 "path is in the legacy Edge package folder, and 137 on the Windows 7 and Server "
                 "2012 R2 entries; it is followed by fixed fields and then by "
                 "NUL-terminated UTF-16LE strings, which began at byte 344 when the first value was "
                 "140 and at byte 336 when it was 137. A record whose first value is neither, or that "
                 "is shorter than its string area's start, gives a row with only Accessed (UTC) and "
                 "Source File, and the run log counts it. File Size (bytes) is the 64-bit "
                 "little-endian value at byte 72 (0x48); on all six tested entries it equalled the "
                 "size in the $MFT of the file at Saved To, or, for two files no longer at that path, "
                 "of a file of the same name elsewhere on the volume. A second 64-bit value at byte 80 "
                 "equalled it on four entries and was smaller on two, and is not shown, since what it "
                 "counts is not established. Download URL is the second-to-last string and Saved To "
                 "the last, as stored. On the one tested entry whose saved file kept a Zone.Identifier "
                 "stream, Download URL equalled that stream's HostUrl. Saved To matched the $MFT path "
                 "of the saved file on four entries; on the other two the file had since been moved, "
                 "so Saved To is where the file was saved, not proof it is still there. Both are left "
                 "blank, and the run log counts the entry, unless the last string starts with a drive "
                 "letter and colon or with two backslashes and the second-to-last string starts with a "
                 "URL scheme followed by a colon. Other Values lists the strings before those two, in "
                 "the order stored, separated by \" | \"; a string that is not printable text is "
                 "shown as a byte count instead. On the tested entries they held, in varying number "
                 "and order, a web address, a media type, a path in the browser's cache folder and, "
                 "on some entries, a publisher name and a SmartScreen result; they are not given "
                 "separate columns because their positions differ between entries. A record ESE marks "
                 "deleted (its fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, and a record the ESE reader cannot convert is skipped; both are counted "
                 "in the run log. The iedownload containers on the tested images held one record ESE "
                 "marks deleted, on lonewolf_win10, and none the reader could not convert. A "
                 "ResponseHeaders value ESE stores apart from its record is read from the table's long "
                 "value tree; one that cannot be assembled is left blank and counted in the run log. "
                 "Four of the six tested values were stored apart, and every one was assembled. An "
                 "entry records a download through these components, not who was at the keyboard. "
                 "The .jfm and .log transaction logs beside WebCacheV01.dat are not "
                 "replayed. Format of the database: libyal esedb-kb, MSIE web cache, "
                 "https://github.com/libyal/esedb-kb/blob/main/documentation/MSIE%20web%20cache.asciidoc",
        "paths": ("*/AppData/Local/Microsoft/Windows/WebCache/WebCacheV01.dat",),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no iedownload container holds an entry)",
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


def _raw(value):
    """The bytes of a binary column; impacket returns a separated value as ASCII hex."""
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        try:
            return binascii.unhexlify(value)
        except (binascii.Error, ValueError):
            return bytes(value)
    return b""


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
                    row_builder, rows, label, relative_source="",
                    long_value_columns=_LONG_VALUE_COLUMNS):
    """Append a built row per entry of one Container_<id> table.

    A record ESE marks deleted is not read, and a record the ESE reader cannot
    convert is skipped so the rest of the table is still read; both are counted
    in the run log. Returns the number skipped.
    """
    table = "Container_%s" % container_id
    if table not in table_names:
        return 0
    walk = ese_rows.TableRows(database, table, cap=_ROW_CAP, long_value_columns=long_value_columns)
    for row in walk:
        built = row_builder(_norm_row(row), name, directory)
        if built is not None:
            rows.append(built)
    if walk.summary():
        logfunc(f"{label}: {relative_source}, {walk.summary()}")
    return walk.deleted + walk.unreadable


def _table_names(database):
    return {t.decode("latin-1") if isinstance(t, (bytes, bytearray)) else t
            for t in database._ESENT_DB__tables.keys()}  # pylint: disable=protected-access


def _run(context, headers, select, row_builder, label, with_source=True,
         long_value_columns=_LONG_VALUE_COLUMNS):
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
            database = ese_rows.ESEDatabase(source)
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
                                        label, relative_source,
                                        long_value_columns)
                for row in rows:
                    data_list.append(row + (relative_source,) if with_source else row)
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


_LOCATION_PARAMETERS = ('clientLocation', 'location')


def _number(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if value == value else None


def location_parameters(url, problems):
    """The location fields of one cached URL, or None when it carries no location parameter.

    A URL qualifies when its query has a clientLocation or location parameter (that exact name) whose value, once
    URL-decoded, is two numbers joined by "|" with the first in [-90, 90] and the second in [-180, 180]. A
    qualifying parameter whose value has another shape is counted in problems, and the URL gives no row.
    """
    try:
        query = parse_qsl(urlsplit(url).query, keep_blank_values=True)
    except ValueError:
        return None
    values = {}
    for key, value in query:
        values.setdefault(key, value)
    for parameter in _LOCATION_PARAMETERS:
        if parameter not in values:
            continue
        stored = values[parameter]
        parts = stored.split('|')
        latitude = _number(parts[0]) if len(parts) == 2 else None
        longitude = _number(parts[1]) if len(parts) == 2 else None
        if latitude is None or longitude is None or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            problems[f'{parameter} parameters that are not two numbers in range joined by |, no row'] += 1
            return None
        stamp = ''
        if parameter == 'clientLocation' and values.get('clientLocationTimestamp'):
            try:
                stamp = datetime.strptime(values['clientLocationTimestamp'], '%Y-%m-%dT%H:%M:%SZ').replace(
                    tzinfo=timezone.utc)
            except ValueError:
                problems['clientLocationTimestamp values not in the form YYYY-MM-DDTHH:MM:SSZ, left blank'] += 1
        prefix = 'clientLocation' if parameter == 'clientLocation' else None
        return {'time': stamp, 'latitude': latitude, 'longitude': longitude, 'parameter': parameter,
                'stored': stored,
                'accuracy': values.get(f'{prefix}Accuracy', '') if prefix else '',
                'provider': values.get(f'{prefix}Provider', '') if prefix else ''}
    return None


@artifact_processor
def webcacheLocationParameters(context):
    headers = (('Location Time (UTC)', 'datetime'), ('Cache Entry Created (UTC)', 'datetime'), 'Latitude',
               'Longitude', 'Accuracy (as stored)', 'Provider (as stored)', 'Parameter', 'Location (as stored)',
               'Cache Directory', 'URL')
    problems = Counter()

    def build(row, _name, directory):
        url = _text(row.get('Url'))
        found = location_parameters(url, problems)
        if found is None:
            return None
        return (found['time'], _filetime_datetime(row.get('CreationTime')), found['latitude'], found['longitude'],
                found['accuracy'], found['provider'], found['parameter'], found['stored'], directory, url)

    result = _run(context, headers, lambda name: True, build, "WebCache Location Parameters", with_source=False)
    for problem, count in sorted(problems.items()):
        logfunc(f"WebCache Location Parameters: {count} {problem}")
    return result


# The first 32-bit value of an iedownload ResponseHeaders record, and the byte at
# which its strings began on the tested entries (see the webcacheDownloads notes).
_DOWNLOAD_STRING_START = {137: 336, 140: 344}
_DOWNLOAD_SIZE_OFFSET = 72
_SAVED_PATH_START = re.compile(r"^(?:[A-Za-z]:|\\\\)")
_URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def download_record(blob, problems):
    """The fields read from one iedownload ResponseHeaders record, or None for an unknown shape.

    Returns a dict with url, saved_to, size and other; url and saved_to are blank when the last
    two strings do not have the shapes the notes describe. Every shape not decoded is counted in
    problems.
    """
    if not blob or len(blob) < 4:
        problems['records with no ResponseHeaders value, only the access time shown'] += 1
        return None
    first = struct.unpack_from('<I', blob, 0)[0]
    start = _DOWNLOAD_STRING_START.get(first)
    if start is None or len(blob) < start:
        problems['records whose first value is not 137 or 140 or that end before their strings, '
                 'only the access time shown'] += 1
        return None
    size = struct.unpack_from('<Q', blob, _DOWNLOAD_SIZE_OFFSET)[0]
    area = blob[start:]
    if len(area) % 2:
        area = area[:-1]
    strings = [text for text in area.decode('utf-16-le', 'replace').split('\x00') if text]
    url = saved_to = ''
    middle = strings
    if (len(strings) >= 2 and _SAVED_PATH_START.match(strings[-1])
            and _URL_SCHEME.match(strings[-2])):
        url, saved_to = strings[-2], strings[-1]
        middle = strings[:-2]
    else:
        problems['records whose last two strings are not a URL and a saved path, both left blank'] += 1
    other = ' | '.join(text if text.isprintable() and '\ufffd' not in text
                       else f'({len(text.encode("utf-16-le"))} bytes that are not text, not shown)'
                       for text in middle)
    return {'url': url, 'saved_to': saved_to, 'size': size, 'other': other}


@artifact_processor
def webcacheDownloads(context):
    headers = (('Accessed (UTC)', 'datetime'), 'Download URL', 'Saved To', 'File Size (bytes)',
               'Other Values', 'Source File')
    problems = Counter()

    def is_download(name):
        return name == "iedownload"

    def build(row, _name, _directory):
        found = download_record(_raw(row.get('ResponseHeaders')), problems)
        if found is None:
            return (_filetime_datetime(row.get('AccessedTime')), '', '', '', '')
        return (_filetime_datetime(row.get('AccessedTime')), found['url'], found['saved_to'],
                found['size'], found['other'])

    result = _run(context, headers, is_download, build, "WebCache Downloads",
                  long_value_columns=frozenset({"ResponseHeaders"}))
    for problem, count in sorted(problems.items()):
        logfunc(f"WebCache Downloads: {count} {problem}")
    return result
