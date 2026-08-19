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
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Timestamps are interpreted as Unix "
                 "seconds in UTC. Payloads that are not JSON remain visible.",
        "paths": (
            "*/AppData/Local/ConnectedDevicesPlatform/*/ActivitiesCache.db*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "windows11_arm_parallels": "Windows build 26200 | 5 rows",
        },
    },
    "windowsNotifications": {
        "name": "Notifications",
        "description": "Windows notification records with arrival and expiry "
                       "times, handler identity, notification type, extracted "
                       "text, and the preserved payload.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-30",
        "requirements": "beautifulsoup4",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Arrival and expiry values use the "
                 "Windows FILETIME epoch and are reported in UTC. Boot ID is "
                 "reported as stored because its encoding is not documented.",
        "paths": (
            "*/AppData/Local/Microsoft/Windows/Notifications/wpndatabase.db*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
        "sample_data": {
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
        "description": "Section-level events from setupapi.dev.log, including "
                       "device-install and other setup operations, their local "
                       "start/end times, device instance identifiers when "
                       "present, and recorded exit status.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-08-19",
        "requirements": "none",
        "category": "Windows System",
        "notes": "Modernized from WLEAPP. Timestamps in setupapi.dev.log "
                 "carry no UTC offset and are treated as device-local, "
                 "consistent with Microsoft's documented SetupAPI logging "
                 "behavior. A section start is not automatically labeled as "
                 "a device's first connection.",
        "paths": (
            "*/[Ww][Ii][Nn][Dd][Oo][Ww][Ss]/INF/setupapi.dev.log",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "plug",
        "sample_data": {
            "windows11_arm_parallels": "Windows build 26200 | 1 row",
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
            records = database.execute(
                """
                SELECT StartTime, EndTime, LastModifiedTime, ExpirationTime,
                       LastModifiedOnClient, AppActivityId, AppId, Payload,
                       ActivityType, ActivityStatus, Tag, "Group", IsLocalOnly,
                       IsRead
                  FROM Activity
                 ORDER BY StartTime DESC
                """
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
            records = database.execute(
                """
                SELECT n.ArrivalTime, n.ExpiryTime, h.CreatedTime,
                       h.ModifiedTime, n.BootId, n.Id, n.HandlerId,
                       h.PrimaryId, h.HandlerType, n.Type, n.PayloadType,
                       n.Payload, n.Tag, n."Group", n.ExpiresOnReboot
                  FROM Notification AS n
                  LEFT JOIN NotificationHandler AS h
                    ON h.RecordId = n.HandlerId
                 ORDER BY n.ArrivalTime DESC
                """
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


def _setup_device(header):
    match = re.match(
        r"Device Install \([^)]+\)\s*-\s*(.+)$",
        header,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _parse_setup_sections(text, source):
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
            source,
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
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "setupapi.dev.log":
            continue
        try:
            with open(file_found, "r", encoding="utf-8-sig", errors="replace") as source:
                text = source.read()
        except OSError as exception:
            logfunc(f"SetupAPI Sections: could not read '{file_found}': {exception}")
            continue
        sources.append(file_found)
        rows.extend(_parse_setup_sections(
            text, context.get_relative_path(file_found)
        ))
    return data_headers, rows, "\n".join(sources)
