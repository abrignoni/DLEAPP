"""Modern Windows system artifacts migrated from WLEAPP.

The implementations retain records with unfamiliar payloads instead of
silently discarding them and label timestamp epochs and device-local values.

Authors: @AlexisBrignoni, Codex
Predecessor: abrignoni/WLEAPP activitiesCache.py, windowsNotification.py,
windowsStickyNotes.py, and setupapiDev.py.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly


__artifacts_v2__ = {
    "activitiesCache": {
        "name": "ActivitiesCache",
        "description": "Windows Connected Devices Platform activity records, "
                       "including event times, application identifiers, status "
                       "fields, and preserved payload content.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-10-25",
        "requirements": "none",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Timestamps are interpreted as Unix "
                 "seconds in UTC. Payloads that are not JSON remain visible. "
                 "The Activity table's columns differ between Windows builds: "
                 "the Read column (IsRead) is absent from the table on the "
                 "tested build 16299 image and is reported blank there, and is "
                 "present on the tested build 17763, 19041 and 22621 images. The schema "
                 "is probed and any absent column is reported blank rather than "
                 "failing the read."
                 " The database is opened read-only with its -wal when one is staged beside it, so rows that exist"
                 " only in the -wal are read: 41 of the 344 rows of pc_mus_001_win11, and 9 of the 18 rows of one "
                 "of the four files of szechuan_win10. The Activity table's ClipboardPayload column is not read: on every tested image whose table has the column it held NULL, except 5 rows of hexordia_mvs2025_win11 that held an empty JSON list, and the build 16299 image has no such column, so no reading of it could be tested. Of the file's other tables, ActivityOperation is reported "
                 "by the ActivitiesCache Operations artifact. Activity_PackageId, whose columns are ActivityId, Platform, PackageName and ExpirationTime where present (the build 16299 image has no such table), is not read; Applications is taken from the activity's"
                 " own AppId. The remaining tables (Asset, or ActivityAssetCache on the build 16299 and 17763 images, DataEncryptionKeys, AppSettings, Metadata and ManualSequence) are not read.",
        "paths": (
            "*/AppData/Local/ConnectedDevicesPlatform/*/ActivitiesCache.db*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "lonewolf_win10": "Windows 10 1709 (build 16299) | 0 rows "
                              "(Activity table empty on this image)",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 76 rows",
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 344 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 122 rows",
            "windows11_arm_parallels": "Windows build 26200 | 5 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 194 rows",
        },
    },
    "activitiesCacheOperations": {
        "name": "ActivitiesCache Operations",
        "description": "Rows of the ActivityOperation table of the Windows Connected Devices Platform "
                       "ActivitiesCache.db, with their times, operation order and type as stored, whether "
                       "the same Id is in the Activity table, and the activity fields they carry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-25",
        "last_update_date": "2026-10-25",
        "requirements": "none",
        "category": "Windows System",
        "notes": "Each row is one row of the ActivityOperation table of ActivitiesCache.db, read read-only "
                 "together with its -wal when one is staged beside it. Eric Zimmerman's WxTCmd reads the same "
                 "table (EricZimmerman/WxTCmd, WxTCmd/Classes/ActivitiesCache.cs, commit "
                 "805740701c1b7f339d2a96c89c04d0325acd9fc9) and reads OperationOrder and OperationType as integers"
                 " without naming their values; Operation Order and Operation Type (as stored) are those columns "
                 "as stored. Operation Type held 1 on all 72 rows of pc_mus_001_win11 and 1, 2 and 3 on 13, 3 and "
                 "1 of the 17 rows of hexordia_mvs2025_win11. Id In Activity Table is Yes when the Activity table, "
                 "which the ActivitiesCache artifact reports, holds a row with the same Id, No otherwise, and blank when the file has no Activity table. It "
                 "was No on all 72 rows of pc_mus_001_win11 and on 13 of the 17 of hexordia_mvs2025_win11, By content, 24 of those 72 rows of pc_mus_001_win11 share an AppActivityId with an Activity row and 6 others share AppId and StartTime with one, so 42 of them, and all 13 of hexordia_mvs2025_win11, match no Activity row by Id, AppActivityId or AppId and StartTime. All 17 rows of hexordia_mvs2025_win11 and 3 of the 72 of pc_mus_001_win11 exist only in the -wal. Start Time, End Time, Created Time, Last Modified, Last "
                 "Modified on Client and Expiration Time are read as Unix seconds in UTC, as the ActivitiesCache "
                 "artifact reads the Activity table's time columns. On both images none of Start "
                 "Time, Created Time, Last Modified or Last Modified on Client is earlier than the oldest Start "
                 "Time of that image's Activity rows, and on hexordia_mvs2025_win11 the newest Last Modified, 24 "
                 "November 2024, is later than the newest Last Modified of its Activity rows, 19 November 2024. "
                 "Operation Expiration Time is shown as stored: read as Unix seconds, 54 of the 72 values of pc_mus_001_win11 fall in 2023, and the other 18 and all 17 of hexordia_mvs2025_win11 fall in the years 6105 to 6107, so the column holds values of more than one shape and its unit is not established. Applications, Display Text, App Display "
                 "Name, Payload Preview, Payload and App ID JSON are derived from AppId and Payload as in the "
                 "ActivitiesCache artifact, and Activity Type is ActivityType as stored. The table's "
                 "ClipboardPayload column is not read: it held NULL on every row of both images. On hexordia_mvs2025_win11 End Time (UTC), Display Text and "
                 "App Display Name held no value on any of the 17 rows: EndTime was 0 on every row and no Payload "
                 "there is JSON. WxTCmd's class comment (ActivityOperationEntry.cs line 5 at the same commit) describes the table as activities waiting to be uploaded. No Microsoft documentation of the table was read here, so a row is reported as stored and is "
                 "not read as a record that anything was uploaded, opened or seen.",
        "paths": (
            "*/AppData/Local/ConnectedDevicesPlatform/*/ActivitiesCache.db*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 72 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 17 rows",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 0 rows (the table is empty)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the table is empty in all four files)",
            "lonewolf_win10": "Windows 10 1709 (build 16299) | 0 rows (the table is empty)",
            "windows11_arm_parallels": "Windows build 26200 | 0 rows (the table is empty in the database file; no -wal was in the extraction)",
        },
    },
    "windowsNotifications": {
        "name": "Notifications",
        "description": "Windows notification records with arrival and expiry "
                       "times, handler identity, notification type, extracted "
                       "text, and the preserved payload.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-09-27",
        "requirements": "beautifulsoup4",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Arrival and expiry values use the "
                 "Windows FILETIME epoch and are reported in UTC. Boot ID is "
                 "reported as stored because its encoding is not documented. The "
                 "Notification table's columns differ between Windows builds: "
                 "Payload Type (PayloadType) is absent on the tested build 16299 "
                 "image and present on the tested build 17763, 19041 and 22621 images; "
                 "Boot ID (BootId) and Expires on Reboot (ExpiresOnReboot) are "
                 "absent on the tested build 16299 and 17763 images and present "
                 "on the tested build 19041 and 22621 images. The schema is probed and any "
                 "absent column is reported blank rather than failing the read; "
                 "the build where each column first appears was not established.",
        "paths": (
            "*/AppData/Local/Microsoft/Windows/Notifications/wpndatabase.db*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
        "sample_data": {
            "lonewolf_win10": "Windows 10 1709 (build 16299) | 34 rows",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 8 rows",
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 19 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 42 rows",
            "windows11_arm_parallels": "Windows build 26200 | 3 rows",
        },
    },
    "windowsStickyNotes": {
        "name": "Sticky Notes",
        "description": "Windows Sticky Notes content and state, including "
                       "updated, created, and deleted times, note identifiers, "
                       "open state, pin state, theme, and window position.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Times are .NET ticks converted to "
                 "UTC. Empty notes are retained because their metadata can "
                 "still have forensic value.",
        "paths": (
            "*/AppData/Local/Packages/Microsoft.MicrosoftStickyNotes_*/"
            "LocalState/plum.sqlite*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "windows11_arm_parallels": "Sticky Notes 6.1.4.0 | 2 rows",
        },
    },
    "setupapiSections": {
        "name": "SetupAPI Sections",
        "description": "Section-level events from setupapi.dev.log and the dated "
                       "setupapi.dev.<date>_<time>.log copies beside it, including "
                       "device-install and other setup operations, their local "
                       "start/end times, device instance identifiers when "
                       "present, and recorded exit status.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Read from setupapi.dev.log in the Windows inf folder, whatever the "
                 "letter case of the folder and file names, and from the files beside it named "
                 "setupapi.dev.<8 digits>_<6 digits>.log; Source File names the file each row came from. "
                 "Microsoft documents the device installation text log as SetupAPI.dev.log in the "
                 "%SystemRoot%\\inf folder (Microsoft, 'SetupAPI Text Logs', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/81d06fd79dd36cdd74ec0b3aeed6c4e52c2e2fc3/windows-driver-docs-pr/install/setupapi-text-logs.md#L20-L24); "
                 "that page does not describe the dated files. The folder is INF on most tested images, inf on "
                 "cfreds_leakage_win7 and Inf on alihadi_challenge3_win81 and szechuan_dc01_server2012r2. Dated "
                 "files are on hexordia_mvs2025_win11 (1) and ou_ransomware_server2022 (3); on both, each dated "
                 "file's last section ends no later than the second its name gives, and the next file's first "
                 "section starts after that second, so on these images the dated files hold the earlier sections "
                 "of the same log. That reading rests on these two images only. Files are read in path order, so "
                 "the dated files come before setupapi.dev.log, and each file's sections in the order the file "
                 "holds them. The setupapi.setup.log, setupapi.offline*.log, setupapi.app.log and "
                 "setupapi.upgrade.log files are not read. Timestamps carry no UTC offset. Microsoft "
                 "describes the section start time stamp as local time (Microsoft, 'Format of a Text Log "
                 "Section Header', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/81d06fd79dd36cdd74ec0b3aeed6c4e52c2e2fc3/windows-driver-docs-pr/install/format-of-a-text-log-section-header.md#L45), "
                 "so they are labelled device local here. A section start is not automatically labeled as "
                 "a device's first connection. Device Instance ID is read only from a section title of the form "
                 "Device Install (<text>) - <ID>. It is blank on every other title, including Device "
                 "Installation Restrictions, and so on every row of alihadi_threatsim_server2019 and "
                 "windows11_arm_parallels. Exit Status held SUCCESS on every row of alihadi_challenge3_win81, "
                 "alihadi_threatsim_server2019, cfreds_leakage_win7, ou_ransomware_server2022 and "
                 "windows11_arm_parallels. Section held one value on all 3 rows of alihadi_threatsim_server2019. "
                 "Of the 47,933 rows of ou_ransomware_server2022, 45,551 come from its three dated files and "
                 "47,876 are sections whose title begins Delete Device.",
        "paths": (
            "*/[Ww][Ii][Nn][Dd][Oo][Ww][Ss]/[Ii][Nn][Ff]/[Ss][Ee][Tt][Uu][Pp][Aa][Pp][Ii].[Dd][Ee][Vv].[Ll][Oo][Gg]",
            "*/[Ww][Ii][Nn][Dd][Oo][Ww][Ss]/[Ii][Nn][Ff]/[Ss][Ee][Tt][Uu][Pp][Aa][Pp][Ii].[Dd][Ee][Vv]."
            "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9].[Ll][Oo][Gg]",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "plug",
        "sample_data": {
            "windows11_arm_parallels": "Windows build 26200 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 55 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 10 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 3 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 223 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 335 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 107 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 47933 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 25 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 22 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 24 rows",
        },
    },
}


_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WINDOWS_FILETIME_EPOCH_TICKS = 116444736000000000
_DOTNET_UNIX_EPOCH_TICKS = 621355968000000000
_TICKS_PER_SECOND = 10_000_000
_NOTE_MARKUP = re.compile(
    r"\\id=[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}\s*",
    re.IGNORECASE,
)
_SETUP_SECTION = re.compile(
    r"^>>>\s+\[(?P<header>.+?)\]\s*$"
    r"(?P<body>.*?)"
    r"^<<<\s+Section end\s+(?P<end>\d{4}/\d{2}/\d{2}\s+"
    r"\d{2}:\d{2}:\d{2}\.\d+)\s*$"
    r"(?P<trailer>.*?)(?=^>>>\s+\[|\Z)",
    re.MULTILINE | re.DOTALL,
)
_SETUP_START = re.compile(
    r"^>>>\s+Section start\s+(?P<start>\d{4}/\d{2}/\d{2}\s+"
    r"\d{2}:\d{2}:\d{2}\.\d+)\s*$",
    re.MULTILINE,
)
_SETUP_STATUS = re.compile(r"^<<<\s+\[Exit status:\s*(.+?)\]\s*$", re.MULTILINE)


def _utc_from_unix_seconds(value):
    if value in (None, "", 0):
        return ""
    try:
        return _UNIX_EPOCH + timedelta(seconds=float(value))
    except (OverflowError, TypeError, ValueError):
        return ""


def _utc_from_filetime(value):
    if value in (None, "", 0):
        return ""
    try:
        seconds = (int(value) - _WINDOWS_FILETIME_EPOCH_TICKS) / _TICKS_PER_SECOND
        return _UNIX_EPOCH + timedelta(seconds=seconds)
    except (OverflowError, TypeError, ValueError):
        return ""


def _utc_from_dotnet_ticks(value):
    if value in (None, "", 0):
        return ""
    try:
        seconds = (int(value) - _DOTNET_UNIX_EPOCH_TICKS) / _TICKS_PER_SECOND
        return _UNIX_EPOCH + timedelta(seconds=seconds)
    except (OverflowError, TypeError, ValueError):
        return ""


def _yes_no(value):
    if value == 1:
        return "Yes"
    if value == 0:
        return "No"
    return "Unknown" if value is not None else ""


def _decode_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def _table_columns(database, table):
    """Column names present in `table`, lowercased.

    Windows changes these schemas between builds, so a fixed SELECT fails with
    "no such column" on a build that lacks one. PRAGMA table_info returns an
    empty result for a table that is not present, which yields an empty set
    here; the query then fails on the missing FROM table and is caught and
    logged like any other read error.
    """
    return {
        row[1].lower()
        for row in database.execute(
            f'PRAGMA table_info("{table}")').fetchall()
    }


def _column_or_null(present, column, alias=None):
    """A SELECT term for a column that may be absent across Windows builds.

    When the column is present it is selected (qualified by `alias` for a join);
    when it is absent it is emitted as `NULL AS <column>` so the whole query
    still runs and the positional record layout the caller unpacks stays fixed.
    `column` may be a quoted identifier such as '"Group"'.
    """
    if column.replace('"', '').lower() in present:
        return f"{alias}.{column}" if alias else column
    return f"NULL AS {column}"


def _application_ids(raw_app_id):
    text = _decode_text(raw_app_id)
    try:
        values = json.loads(text)
    except (TypeError, ValueError):
        return "", text
    applications = []
    for value in values if isinstance(values, list) else ():
        application = value.get("application") if isinstance(value, dict) else ""
        if application and application not in applications:
            applications.append(application)
    return " | ".join(applications), text


def _activity_payload(raw_payload):
    text = _decode_text(raw_payload)
    display_text = ""
    app_display_name = ""
    preview = ""
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            display_text = payload.get("displayText") or ""
            app_display_name = payload.get("appDisplayName") or ""
    except (TypeError, ValueError):
        try:
            decoded = base64.b64decode(text, validate=True)
        except (ValueError, TypeError):
            decoded = b""
        readable = []
        for match in re.finditer(rb"(?:[\x20-\x7e]\x00){3,}", decoded):
            value = match.group().decode("utf-16-le", "ignore").strip()
            if value and value not in readable:
                readable.append(value)
        for match in re.finditer(rb"[\x20-\x7e]{4,}", decoded):
            value = match.group().decode("utf-8", "ignore").strip()
            if value and value not in readable:
                readable.append(value)
        preview = " | ".join(readable)
    return display_text, app_display_name, preview, text


@artifact_processor
def activitiesCache(context):
    data_headers = (
        ("Start Time (UTC)", "datetime"),
        ("End Time (UTC)", "datetime"),
        ("Last Modified (UTC)", "datetime"),
        ("Expiration Time (UTC)", "datetime"),
        ("Last Modified on Client (UTC)", "datetime"),
        "App Activity ID",
        "Applications",
        "Display Text",
        "App Display Name",
        "Activity Type",
        "Activity Status",
        "Tag",
        "Group",
        "Local Only",
        "Read",
        "Payload Preview",
        "Payload",
        "App ID JSON",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "activitiescache.db":
            continue
        database = open_sqlite_db_readonly(file_found)
        if database is None:
            continue
        try:
            # The Activity schema differs between Windows builds (IsRead is
            # absent on the tested build 16299 image and present on the newer
            # tested builds), so probe the table and substitute NULL for any
            # absent column rather than letting the whole query fail.
            columns = _table_columns(database, "Activity")
            select_list = ", ".join(
                _column_or_null(columns, name) for name in (
                    "StartTime", "EndTime", "LastModifiedTime", "ExpirationTime",
                    "LastModifiedOnClient", "AppActivityId", "AppId", "Payload",
                    "ActivityType", "ActivityStatus", "Tag", '"Group"',
                    "IsLocalOnly", "IsRead",
                )
            )
            records = database.execute(
                f"SELECT {select_list} FROM Activity ORDER BY StartTime DESC"
            ).fetchall()
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"ActivitiesCache: could not read '{file_found}': {exception}")
            database.close()
            continue
        database.close()
        sources.append(file_found)
        relative_source = context.get_relative_path(file_found)
        for record in records:
            applications, raw_app_id = _application_ids(record[6])
            display_text, app_display_name, preview, payload = _activity_payload(
                record[7]
            )
            rows.append((
                _utc_from_unix_seconds(record[0]),
                _utc_from_unix_seconds(record[1]),
                _utc_from_unix_seconds(record[2]),
                _utc_from_unix_seconds(record[3]),
                _utc_from_unix_seconds(record[4]),
                record[5] or "",
                applications,
                display_text,
                app_display_name,
                record[8],
                record[9],
                record[10] or "",
                record[11] or "",
                _yes_no(record[12]),
                _yes_no(record[13]),
                preview,
                payload,
                raw_app_id,
                relative_source,
            ))
    return data_headers, rows, "\n".join(sources)


@artifact_processor
def activitiesCacheOperations(context):
    data_headers = (
        ("Start Time (UTC)", "datetime"),
        ("End Time (UTC)", "datetime"),
        ("Created Time (UTC)", "datetime"),
        ("Last Modified (UTC)", "datetime"),
        ("Last Modified on Client (UTC)", "datetime"),
        ("Expiration Time (UTC)", "datetime"),
        "Operation Expiration Time (as stored)",
        "Operation Order",
        "Operation Type (as stored)",
        "Id In Activity Table",
        "App Activity ID",
        "Applications",
        "Display Text",
        "App Display Name",
        "Activity Type",
        "Payload Preview",
        "Payload",
        "App ID JSON",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "activitiescache.db":
            continue
        database = open_sqlite_db_readonly(file_found)
        if database is None:
            continue
        try:
            columns = _table_columns(database, "ActivityOperation")
            if not columns:
                logfunc(f"ActivitiesCache Operations: no ActivityOperation table in '{file_found}'")
                database.close()
                continue
            select_list = ", ".join(
                _column_or_null(columns, name, "o") for name in (
                    "StartTime", "EndTime", "CreatedTime", "LastModifiedTime",
                    "LastModifiedOnClient", "ExpirationTime", "OperationExpirationTime",
                    "OperationOrder", "OperationType", "AppActivityId", "AppId", "Payload",
                    "ActivityType",
                )
            )
            in_activity = ("EXISTS (SELECT 1 FROM Activity a WHERE a.Id = o.Id)"
                           if _table_columns(database, "Activity") else "NULL")
            records = database.execute(
                f"SELECT {select_list}, {in_activity} FROM ActivityOperation o "
                "ORDER BY o.StartTime DESC"
            ).fetchall()
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"ActivitiesCache Operations: could not read '{file_found}': {exception}")
            database.close()
            continue
        database.close()
        sources.append(file_found)
        relative_source = context.get_relative_path(file_found)
        for record in records:
            applications, raw_app_id = _application_ids(record[10])
            display_text, app_display_name, preview, payload = _activity_payload(record[11])
            rows.append((
                _utc_from_unix_seconds(record[0]),
                _utc_from_unix_seconds(record[1]),
                _utc_from_unix_seconds(record[2]),
                _utc_from_unix_seconds(record[3]),
                _utc_from_unix_seconds(record[4]),
                _utc_from_unix_seconds(record[5]),
                "" if record[6] is None else record[6],
                "" if record[7] is None else record[7],
                "" if record[8] is None else record[8],
                _yes_no(record[13]),
                record[9] or "",
                applications,
                display_text,
                app_display_name,
                record[12],
                preview,
                payload,
                raw_app_id,
                relative_source,
            ))
    return data_headers, rows, "\n".join(sources)


def _payload_details(raw_payload):
    payload = _decode_text(raw_payload)
    text = BeautifulSoup(payload, "html.parser").get_text(" ", strip=True)
    payload_hash = hashlib.sha256(
        raw_payload if isinstance(raw_payload, bytes) else payload.encode("utf-8")
    ).hexdigest().upper()
    return text, payload, len(payload.encode("utf-8")), payload_hash


@artifact_processor
def windowsNotifications(context):
    data_headers = (
        ("Arrival Time (UTC)", "datetime"),
        ("Expiry Time (UTC)", "datetime"),
        "Handler Created (database value)",
        "Handler Modified (database value)",
        "Boot ID (database value)",
        "Notification ID",
        "Handler ID",
        "Handler Primary ID",
        "Handler Type",
        "Type",
        "Payload Type",
        "Text",
        "Tag",
        "Group",
        "Expires on Reboot",
        "Payload Bytes",
        "Payload SHA-256",
        "Payload",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "wpndatabase.db":
            continue
        database = open_sqlite_db_readonly(file_found)
        if database is None:
            continue
        try:
            # The Notification table's columns differ between Windows builds:
            # BootId and ExpiresOnReboot are absent on the tested 16299 and
            # 17763 images, and PayloadType is absent on the tested 16299 image.
            # Probe both tables and substitute NULL for any absent column rather
            # than letting the whole query fail. The positional record layout
            # unpacked below stays fixed.
            notification = _table_columns(database, "Notification")
            handler = _table_columns(database, "NotificationHandler")
            select_list = ", ".join((
                _column_or_null(notification, "ArrivalTime", "n"),
                _column_or_null(notification, "ExpiryTime", "n"),
                _column_or_null(handler, "CreatedTime", "h"),
                _column_or_null(handler, "ModifiedTime", "h"),
                _column_or_null(notification, "BootId", "n"),
                _column_or_null(notification, "Id", "n"),
                _column_or_null(notification, "HandlerId", "n"),
                _column_or_null(handler, "PrimaryId", "h"),
                _column_or_null(handler, "HandlerType", "h"),
                _column_or_null(notification, "Type", "n"),
                _column_or_null(notification, "PayloadType", "n"),
                _column_or_null(notification, "Payload", "n"),
                _column_or_null(notification, "Tag", "n"),
                _column_or_null(notification, '"Group"', "n"),
                _column_or_null(notification, "ExpiresOnReboot", "n"),
            ))
            records = database.execute(
                f"SELECT {select_list} "
                "FROM Notification AS n "
                "LEFT JOIN NotificationHandler AS h "
                "ON h.RecordId = n.HandlerId "
                "ORDER BY n.ArrivalTime DESC"
            ).fetchall()
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"Notifications: could not read '{file_found}': {exception}")
            database.close()
            continue
        database.close()
        sources.append(file_found)
        relative_source = context.get_relative_path(file_found)
        for record in records:
            text, payload, payload_size, payload_hash = _payload_details(record[11])
            rows.append((
                _utc_from_filetime(record[0]),
                _utc_from_filetime(record[1]),
                record[2] or "",
                record[3] or "",
                "" if record[4] is None else record[4],
                record[5],
                record[6],
                record[7] or "",
                record[8] or "",
                record[9] or "",
                record[10] or "",
                text,
                record[12] or "",
                record[13] or "",
                _yes_no(record[14]),
                payload_size,
                payload_hash,
                payload,
                relative_source,
            ))
    return data_headers, rows, "\n".join(sources)


@artifact_processor
def windowsStickyNotes(context):
    data_headers = (
        ("Updated Time (UTC)", "datetime"),
        ("Created Time (UTC)", "datetime"),
        ("Deleted Time (UTC)", "datetime"),
        "Note ID",
        "Parent ID",
        "Text",
        "Open",
        "Always on Top",
        "Theme",
        "Window Position",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "plum.sqlite":
            continue
        database = open_sqlite_db_readonly(file_found)
        if database is None:
            continue
        try:
            records = database.execute(
                """
                SELECT UpdatedAt, CreatedAt, DeletedAt, Id, ParentId, Text,
                       IsOpen, IsAlwaysOnTop, Theme, WindowPosition
                  FROM Note
                 ORDER BY UpdatedAt DESC
                """
            ).fetchall()
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"Sticky Notes: could not read '{file_found}': {exception}")
            database.close()
            continue
        database.close()
        sources.append(file_found)
        relative_source = context.get_relative_path(file_found)
        for record in records:
            rows.append((
                _utc_from_dotnet_ticks(record[0]),
                _utc_from_dotnet_ticks(record[1]),
                _utc_from_dotnet_ticks(record[2]),
                record[3] or "",
                record[4] or "",
                _NOTE_MARKUP.sub("", record[5] or "", count=1),
                _yes_no(record[6]),
                _yes_no(record[7]),
                record[8] or "",
                record[9] or "",
                relative_source,
            ))
    return data_headers, rows, "\n".join(sources)


# setupapi.dev.log, and the dated name the corpus shows for an older copy of it beside it.
_SETUP_LOG_NAME = re.compile(r"setupapi\.dev(?:\.\d{8}_\d{6})?\.log")


def _setup_device(header):
    match = re.match(
        r"Device Install \([^)]+\)\s*-\s*(.+)$",
        header,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _parse_setup_sections(text):
    rows = []
    for section in _SETUP_SECTION.finditer(text):
        start_match = _SETUP_START.search(section.group("body"))
        if not start_match:
            continue
        status_match = _SETUP_STATUS.search(section.group("trailer"))
        start_text = start_match.group("start")
        end_text = section.group("end")
        try:
            start_value = datetime.strptime(start_text, "%Y/%m/%d %H:%M:%S.%f")
            end_value = datetime.strptime(end_text, "%Y/%m/%d %H:%M:%S.%f")
            duration = round((end_value - start_value).total_seconds(), 3)
        except ValueError:
            duration = ""
        header = section.group("header").strip()
        rows.append((
            start_text,
            end_text,
            header,
            _setup_device(header),
            status_match.group(1).strip() if status_match else "",
            duration,
        ))
    return rows


@artifact_processor
def setupapiSections(context):
    data_headers = (
        "Start Time (device local)",
        "End Time (device local)",
        "Section",
        "Device Instance ID",
        "Exit Status",
        "Duration (seconds)",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in sorted(map(str, context.get_files_found())):
        if not _SETUP_LOG_NAME.fullmatch(os.path.basename(file_found).lower()):
            continue
        relative_source = context.get_relative_path(file_found)
        try:
            with open(file_found, "r", encoding="utf-8-sig", errors="replace") as source:
                text = source.read()
        except OSError as exception:
            logfunc(f"SetupAPI Sections: could not read '{relative_source}': {exception}")
            continue
        sources.append(file_found)
        rows.extend(row + (relative_source,) for row in _parse_setup_sections(text))
    return data_headers, rows, "\n".join(sources)
