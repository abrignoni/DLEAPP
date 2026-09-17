"""Windows SRUM (System Resource Usage Monitor) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.SRUM artifact; the
provider-table GUID names used here are taken from that artifact. SRUDB.dat is an
ESE (Extensible Storage Engine) database and is read with the ESE reader adapted
from impacket in scripts/vendor/impacket_ese.py.

The entry TimeStamp column is decoded as an OLE automation date. That reading is
corroborated against the EndTime FILETIME on the Execution Stats table, which
shares the same instant on a row and agrees to within a minute; EndTime and
ConnectStartTime are Windows FILETIMEs, matching the Velociraptor artifact's
winfiletime handling of those columns.
"""

import struct
import binascii
from datetime import datetime, timedelta, timezone

try:
    from scripts.vendor import impacket_ese
except ImportError:
    impacket_ese = None

from scripts.ilapfuncs import artifact_processor, logfunc

# SRUM keeps one ESE table per provider, named by a GUID. These four provider
# GUIDs and their names are from the Velociraptor Windows.Forensics.SRUM artifact
# (NetworkUsageGUID, ApplicationResourceUsageGUID, NetworkConnectionsGUID,
# ExecutionGUID). Each row's AppId and UserId are integer indexes into
# SruDbIdMapTable, which resolves them to an application id string or a user SID.
_NETWORK_USAGE = "{973F5D5C-1D90-4944-BE8E-24B94231A174}"
_APP_RESOURCE = "{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}"
_NETWORK_CONNECTIONS = "{DD6636C4-8929-4683-974E-22C046A43763}"
_EXECUTION = "{5C8CF1C7-7257-4F13-B223-970EF5939312}"

_IDMAP = "SruDbIdMapTable"
_SRUDB = "srudb.dat"

__artifacts_v2__ = {
    "srumNetworkUsage": {
        "name": "SRUM Network Usage",
        "description": "Per-application network bytes sent and received recorded by "
                       "SRUM, from the Network Usage provider in SRUDB.dat, with the "
                       "application, user SID, network interface and snapshot time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Network Usage table "
                 "{973F5D5C-1D90-4944-BE8E-24B94231A174}. Bytes Sent and Bytes "
                 "Received are byte counts for the snapshot as stored. Interface "
                 "LUID and L2 Profile ID are the network interface and profile "
                 "identifiers as stored; they are not resolved to a network name "
                 "here. Read from SRUDB.dat, named in Source File, with the ESE "
                 "reader adapted from impacket in scripts/vendor. Each row is one "
                 "entry in this SRUM provider table. Timestamp (UTC) is the entry's "
                 "TimeStamp column decoded as an OLE automation date (days since "
                 "1899-12-30); decoded as a Windows FILETIME the same value is out "
                 "of range, and the OLE reading places every row in the same period "
                 "as the FILETIME columns in these tables. "
                 "Application and User are resolved from SruDbIdMapTable: "
                 "Application is the stored application id (a package moniker, a "
                 "service name, or an executable path as stored) and User is the "
                 "account SID; either is blank when the entry's id is 0 or absent "
                 "from the map. SRUM aggregates usage into periodic snapshots, so a "
                 "row is a recorded total for a snapshot and not a single user "
                 "action, and it does not record who was at the keyboard. A "
                 "SRUDB.dat that does not carry this provider table gives this "
                 "artifact no rows for that file, and the file is named in the "
                 "run log. The .jfm "
                 "and .log transaction logs beside SRUDB.dat are not replayed. GUID "
                 "names: Velocidex, Windows.Forensics.SRUM, https://github.com/"
                 "Velocidex/velociraptor/blob/master/artifacts/definitions/Windows/"
                 "Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat",),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2242 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 57 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2471 rows",
        },
    },
    "srumApplicationResourceUsage": {
        "name": "SRUM Application Resource Usage",
        "description": "Per-application disk bytes read and written and CPU cycle "
                       "time recorded by SRUM, from the Application Resource Usage "
                       "provider in SRUDB.dat, with the application, user SID and "
                       "snapshot time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Application Resource Usage table "
                 "{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}. Foreground and Background "
                 "Bytes Read and Bytes Written are disk byte counts for the snapshot "
                 "as stored. Foreground and Background Cycle Time are CPU cycle "
                 "counts as stored; their unit is not converted. Read from "
                 "SRUDB.dat, named in Source File, with the ESE reader adapted from "
                 "impacket in scripts/vendor. Each row is one entry in this SRUM "
                 "provider table. Timestamp (UTC) is the entry's TimeStamp column "
                 "decoded as an OLE automation date (days since 1899-12-30); decoded "
                 "as a Windows FILETIME the same value is out of range, and the OLE "
                 "reading places every row in the same period as the FILETIME "
                 "columns in these tables. Application and User "
                 "are resolved from SruDbIdMapTable: Application is the stored "
                 "application id (a package moniker, a service name, or an "
                 "executable path as stored) and User is the account SID; either is "
                 "blank when the entry's id is 0 or absent from the map. SRUM "
                 "aggregates usage into periodic snapshots, so a row is a recorded "
                 "total for a snapshot and not a single user action, and it does not "
                 "record who was at the keyboard. A SRUDB.dat that does not carry "
                 "this provider table gives this artifact no rows for that file, and "
                 "the file is named in the run log. The .jfm and .log transaction "
                 "logs beside SRUDB.dat are not replayed. GUID names: Velocidex, "
                 "Windows.Forensics.SRUM, https://github.com/Velocidex/velociraptor/"
                 "blob/master/artifacts/definitions/Windows/Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 14667 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1458 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 15055 rows",
        },
    },
    "srumNetworkConnections": {
        "name": "SRUM Network Connections",
        "description": "Network interface connection periods recorded by SRUM, from "
                       "the Network Connections provider in SRUDB.dat, with the "
                       "connection start time and the connected-time counter.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Network Connections table "
                 "{DD6636C4-8929-4683-974E-22C046A43763}. Connect Start Time (UTC) "
                 "is a Windows FILETIME as stored, matching the Velociraptor "
                 "artifact's winfiletime handling of that column. Connected Time is "
                 "the connected-time counter as stored; its unit is not converted. "
                 "Interface LUID and L2 Profile ID are the network interface and "
                 "profile identifiers as stored. The application and user ids are 0 "
                 "on the tested images, so no application or user is surfaced here. "
                 "Read from SRUDB.dat, named in Source File, "
                 "with the ESE reader adapted from impacket in scripts/vendor. Each "
                 "row is one entry in this SRUM provider table. Timestamp (UTC) is "
                 "the entry's TimeStamp column decoded as an OLE automation date "
                 "(days since 1899-12-30); decoded as a Windows FILETIME the same "
                 "value is out of range, and the OLE reading places every row in the "
                 "same period as the Connect Start Time FILETIME. SRUM aggregates "
                 "usage into periodic snapshots, so "
                 "a row is a recorded total for a snapshot and not a single user "
                 "action, and it does not record who was at the keyboard. A "
                 "SRUDB.dat that does not carry this provider table gives this "
                 "artifact no rows for that file, and the file is named in the "
                 "run log. The .jfm "
                 "and .log transaction logs beside SRUDB.dat are not replayed. GUID "
                 "names: Velocidex, Windows.Forensics.SRUM, https://github.com/"
                 "Velocidex/velociraptor/blob/master/artifacts/definitions/Windows/"
                 "Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat",),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 224 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 201 rows",
        },
    },
    "srumExecutionStats": {
        "name": "SRUM Execution Stats",
        "description": "Per-application foreground execution periods recorded by "
                       "SRUM, from the Execution Stats provider in SRUDB.dat, with "
                       "the application, user SID, end time and duration.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Execution Stats table "
                 "{5C8CF1C7-7257-4F13-B223-970EF5939312}. End Time (UTC) is a "
                 "Windows FILETIME as stored, matching the Velociraptor artifact's "
                 "winfiletime handling of that column. Duration (ms) and Span (ms) "
                 "are the recorded duration and span for the entry in milliseconds "
                 "as stored. The table's other timeline and cycle columns are not "
                 "surfaced here. Read from SRUDB.dat, named in Source File, with the "
                 "ESE reader adapted from impacket in scripts/vendor. Each row is one "
                 "entry in this SRUM provider table. Timestamp (UTC) is the entry's "
                 "TimeStamp column decoded as an OLE automation date (days since "
                 "1899-12-30); decoded as a Windows FILETIME the same value is out "
                 "of range, and the OLE reading places every row in the same period "
                 "as the End Time FILETIME in this table. Timestamp is the snapshot "
                 "time and End Time is when the entry's execution period ended, so "
                 "the two need not be the same instant on a row. Application and User are "
                 "resolved from "
                 "SruDbIdMapTable: Application is the stored application id (a "
                 "package moniker, a service name, or an executable path as stored) "
                 "and User is the account SID; either is blank when the entry's id "
                 "is 0 or absent from the map. SRUM aggregates usage into periodic "
                 "snapshots, so a row is a recorded total for a snapshot and not a "
                 "single user action, and it does not record who was at the "
                 "keyboard. A SRUDB.dat that does not carry this provider table "
                 "gives this artifact no rows for that file, and the file is named "
                 "in the run log. The .jfm and .log transaction logs beside "
                 "SRUDB.dat are not replayed. GUID names: Velocidex, "
                 "Windows.Forensics.SRUM, "
                 "https://github.com/Velocidex/velociraptor/blob/master/artifacts/"
                 "definitions/Windows/Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat",),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 19708 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2777 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 12332 rows",
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


def _unhex(blob):
    """impacket returns binary columns as ASCII hex bytes; recover the raw bytes."""
    if blob is None:
        return None
    if isinstance(blob, (bytes, bytearray)):
        try:
            return binascii.unhexlify(blob)
        except (binascii.Error, ValueError):
            return bytes(blob)
    return None


def _fmt_sid(raw):
    """Format a binary Windows SID as S-1-<authority>-<sub>-<sub>..."""
    if not raw or len(raw) < 8:
        return ""
    revision = raw[0]
    subauth_count = raw[1]
    authority = int.from_bytes(raw[2:8], "big")
    subs = []
    offset = 8
    for _ in range(subauth_count):
        if offset + 4 > len(raw):
            break
        subs.append(struct.unpack("<I", raw[offset:offset + 4])[0])
        offset += 4
    return "S-%d-%d%s" % (revision, authority, "".join("-%d" % s for s in subs))


def _decode_idblob(blob, id_type):
    raw = _unhex(blob)
    if raw is None:
        return ""
    if id_type == 3:  # user SID
        return _fmt_sid(raw)
    return raw.decode("utf-16-le", "replace").rstrip("\x00")


def _build_idmap(database, label, relative_source):
    """Map SruDbIdMapTable's IdIndex to its resolved application id or user SID."""
    idmap = {}
    cursor = database.openTable(_IDMAP)
    if cursor is None:
        logfunc(f"{label}: {relative_source} has no {_IDMAP}, so Application and "
                "User are left blank")
        return idmap
    while True:
        row = database.getNextRow(cursor)
        if row is None:
            break
        row = _norm_row(row)
        idmap[row.get("IdIndex")] = _decode_idblob(row.get("IdBlob"),
                                                    row.get("IdType"))
    return idmap


def _ole_datetime(value):
    """SRUM TimeStamp: an OLE automation date (days since 1899-12-30) stored as a
    float64, which the ESE reader returns as its raw 8-byte integer."""
    if value is None:
        return ""
    try:
        packed = struct.pack("<Q", int(value) & 0xFFFFFFFFFFFFFFFF)
        days = struct.unpack("<d", packed)[0]
        return datetime(1899, 12, 30, tzinfo=timezone.utc) + timedelta(days=days)
    except (struct.error, OverflowError, ValueError, OSError):
        return ""


def _filetime_datetime(value):
    """A Windows FILETIME: 100-nanosecond intervals since 1601-01-01 UTC."""
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=int(value) / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _srudb_sources(context):
    return [str(f) for f in context.get_files_found()
            if str(f).lower().endswith(_SRUDB)]


def _cell(value):
    """Present a missing numeric value as blank, otherwise the value itself."""
    return "" if value is None else value


def _read_table(source, guid, row_builder, label, relative_source):
    """Open SRUDB.dat, build the id map, and build a row per entry of one table."""
    database = impacket_ese.ESENT_DB(source)
    try:
        database.mountDB()
        idmap = _build_idmap(database, label, relative_source)
        rows = []
        cursor = database.openTable(guid)
        if cursor is None:
            logfunc(f"{label}: {relative_source} has no {guid} table, so it holds "
                    "no rows for this SRUM provider")
            return rows
        while True:
            row = database.getNextRow(cursor)
            if row is None:
                break
            rows.append(row_builder(_norm_row(row), idmap))
        return rows
    finally:
        database.close()


def _run(context, guid, headers, row_builder, label):
    data_list = []
    sources = []
    if impacket_ese is None:
        logfunc(f"{label}: the vendored ESE reader is not available")
        return headers, data_list, ""
    for source in _srudb_sources(context):
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            rows = _read_table(source, guid, row_builder, label, relative_source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"{label}: could not read {relative_source}: {exc}")
            continue
        for row in rows:
            data_list.append(row + (relative_source,))
            rows_here += 1
        if rows_here:
            sources.append(source)
    return headers, data_list, "\n".join(sources)


@artifact_processor
def srumNetworkUsage(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               'Interface LUID', 'L2 Profile ID', 'Bytes Sent', 'Bytes Received',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _cell(row.get('InterfaceLuid')),
                _cell(row.get('L2ProfileId')),
                _cell(row.get('BytesSent')),
                _cell(row.get('BytesRecvd')))

    return _run(context, _NETWORK_USAGE, headers, build, "SRUM Network Usage")


@artifact_processor
def srumApplicationResourceUsage(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               'Foreground Bytes Read', 'Foreground Bytes Written',
               'Background Bytes Read', 'Background Bytes Written',
               'Foreground Cycle Time', 'Background Cycle Time', 'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _cell(row.get('ForegroundBytesRead')),
                _cell(row.get('ForegroundBytesWritten')),
                _cell(row.get('BackgroundBytesRead')),
                _cell(row.get('BackgroundBytesWritten')),
                _cell(row.get('ForegroundCycleTime')),
                _cell(row.get('BackgroundCycleTime')))

    return _run(context, _APP_RESOURCE, headers, build,
                "SRUM Application Resource Usage")


@artifact_processor
def srumNetworkConnections(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Interface LUID', 'L2 Profile ID',
               ('Connect Start Time (UTC)', 'datetime'), 'Connected Time',
               'Source File')

    def build(row, _idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                _cell(row.get('InterfaceLuid')),
                _cell(row.get('L2ProfileId')),
                _filetime_datetime(row.get('ConnectStartTime')),
                _cell(row.get('ConnectedTime')))

    return _run(context, _NETWORK_CONNECTIONS, headers, build,
                "SRUM Network Connections")


@artifact_processor
def srumExecutionStats(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               ('End Time (UTC)', 'datetime'), 'Duration (ms)', 'Span (ms)',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _filetime_datetime(row.get('EndTime')),
                _cell(row.get('DurationMS')),
                _cell(row.get('SpanMS')))

    return _run(context, _EXECUTION, headers, build, "SRUM Execution Stats")
