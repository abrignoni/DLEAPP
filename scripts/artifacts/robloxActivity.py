__artifacts_v2__ = {
    "robloxSessionState": {
        "name": "Roblox Session State",
        "description": "The most recently persisted Roblox application or play "
                       "session, with launch, session and synchronization times, "
                       "account and experience identifiers, server address, client "
                       "version, session IDs and result state.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "memProfStorage is rolling state and generally describes the most "
                 "recent session only. Unix timestamps are reported in UTC.",
        "paths": (
            "*/Library/Roblox/LocalStorage/memProfStorage*.json",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 1 row",
        },
    },
    "robloxPresence": {
        "name": "Roblox Presence",
        "description": "Retained Roblox user-presence state from embedded-browser "
                       "Local Storage, identifying users, their presence type and "
                       "last reported location.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "Presence type values are preserved numerically because Roblox may "
                 "change their interpretation. Timestamps are UTC.",
        "paths": (
            "*/Library/WebKit/com.roblox.RobloxPlayer/WebsiteData/*/*/*/"
            "LocalStorage/localstorage.sqlite3",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 2 rows",
        },
    },
    "robloxNotifications": {
        "name": "Roblox Real-Time Notifications",
        "description": "Real-time notifications retained in Roblox embedded-browser "
                       "Local Storage. Chat notifications can preserve the sender, "
                       "conversation ID and message text shown to the user.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "Only live Local Storage versions are parsed. The key can be "
                 "overwritten as notifications arrive, so output is a partial "
                 "notification history rather than a complete message record.",
        "paths": (
            "*/Library/WebKit/com.roblox.RobloxPlayer/WebsiteData/*/*/*/"
            "LocalStorage/localstorage.sqlite3",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 1 row",
        },
    },
}

import json

from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.roblox import decode_webkit_value, epoch_datetime, read_json


@artifact_processor
def robloxSessionState(context):
    data_headers = (
        ("Session Start", "datetime"), ("Last Sync", "datetime"),
        ("Application Launch", "datetime"), "Session Type", "User ID",
        "Place ID", "Universe ID", "Game Instance ID", "Server Address",
        "Server Port", "Play Session ID", "App Session ID", "Session Result",
        "Session Success", "Application Version", "Engine Version", "Channel",
        "Device", "OS", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        payload = read_json(file_found)
        if not isinstance(payload, dict):
            continue
        session_fields = (
            "SessionStartTime", "AppSessionStartTime", "SyncTime",
            "LaunchTimestamp", "SessionType", "DebugUserId", "UserId",
            "LastPlaceId", "UniverseId", "GameInstanceId", "ServerIp",
            "ServerPort", "PlaySessionId", "AppSessionIdL0",
            "SessionResultV2", "SessionResult", "SessionSuccess",
            "AppVersion", "EngineVersion", "Channel", "Device", "OSType",
            "OSVersion",
        )
        if not any(payload.get(field) not in (None, "") for field in session_fields):
            continue
        source_paths.append(file_found)
        data_list.append((
            epoch_datetime(payload.get("SessionStartTime")
                           or payload.get("AppSessionStartTime")),
            epoch_datetime(payload.get("SyncTime")),
            epoch_datetime(payload.get("LaunchTimestamp")),
            payload.get("SessionType", ""),
            payload.get("DebugUserId") or payload.get("UserId", ""),
            payload.get("LastPlaceId", ""),
            payload.get("UniverseId", ""),
            payload.get("GameInstanceId", ""),
            payload.get("ServerIp", ""),
            payload.get("ServerPort", ""),
            payload.get("PlaySessionId", ""),
            payload.get("AppSessionIdL0", ""),
            payload.get("SessionResultV2") or payload.get("SessionResult", ""),
            payload.get("SessionSuccess", ""),
            payload.get("AppVersion", ""),
            payload.get("EngineVersion", ""),
            payload.get("Channel", ""),
            payload.get("Device", ""),
            f"{payload.get('OSType', '')} {payload.get('OSVersion', '')}".strip(),
            context.get_relative_path(file_found),
        ))
    logfunc(f"Roblox Session State: {len(data_list)} session state record(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _webkit_storage_items(path):
    connection = open_sqlite_db_readonly(path)
    if not connection:
        return []
    try:
        rows = connection.execute("SELECT key, value FROM ItemTable").fetchall()
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Roblox Local Storage: could not read '{path}': {ex}")
        rows = []
    connection.close()
    return rows


def _local_storage_items(files_found):
    files = list(map(str, files_found))
    for path in files:
        if path.endswith("localstorage.sqlite3"):
            for key, value in _webkit_storage_items(path):
                yield key, decode_webkit_value(value), "", "Live", path
    for folder in leveldb_folders(files):
        try:
            for record in read_records(folder):
                if record.is_live:
                    yield (
                        record.key, record.value, record.sequence,
                        record.state, record.source,
                    )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox Local Storage: could not read '{folder}': {ex}")


@artifact_processor
def robloxPresence(context):
    data_headers = (
        ("Last Updated", "datetime"), "User ID", "Presence Type",
        "Last Location", "Storage Sequence", "Source File",
    )
    data_list = []
    source_paths = []
    for key, value, sequence, _state, source in _local_storage_items(
            context.get_files_found()):
        if key != "PresenceData":
            continue
        try:
            payload = json.loads(value)
        except (TypeError, ValueError):
            continue
        source_paths.append(source)
        for stored_user_id, entry in payload.items():
            if not isinstance(entry, dict):
                continue
            presence = entry.get("data") or {}
            data_list.append((
                epoch_datetime(entry.get("lastUpdated")),
                presence.get("userId") or stored_user_id,
                presence.get("userPresenceType", ""),
                presence.get("lastLocation", ""),
                sequence,
                context.get_relative_path(source),
            ))
    data_list.sort(key=lambda row: row[0] if row[0] else epoch_datetime(1))
    logfunc(f"Roblox Presence: {len(data_list)} presence record(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _notification_fields(payload):
    detail = payload.get("detail") or {}
    content = detail.get("content") or {}
    state_name = content.get("currentState") or "default"
    state = (content.get("states") or {}).get(state_name) or {}
    sender_id = (content.get("clientEventsPayload") or {}).get("sender_id", "")
    title = text = conversation_id = ""
    for visual in state.get("visualItems") or []:
        body = visual.get("textBody") if isinstance(visual, dict) else None
        if body:
            title = (body.get("title") or {}).get("text", "")
            text = (body.get("label") or {}).get("text", "")
            try:
                params = json.loads(body.get("actionEventParams") or "{}")
                conversation_id = params.get("conversationId", "")
            except (TypeError, ValueError):
                pass
        thumb = visual.get("thumbnail") if isinstance(visual, dict) else None
        if thumb and not sender_id:
            sender_id = thumb.get("id", "")
    return detail, content, sender_id, title, text, conversation_id


@artifact_processor
def robloxNotifications(context):
    data_headers = (
        ("Delivered", "datetime"), "Notification Type", "Namespace", "Title",
        "Text", "Sender User ID", "Conversation ID", "Notification ID",
        "Priority", "Sequence Number", "Realtime Message ID", "Storage Sequence",
        "Source File",
    )
    data_list = []
    source_paths = []
    for key, value, storage_sequence, _state, source in _local_storage_items(
            context.get_files_found()):
        if key != "Roblox.RealTime.Events.Notification":
            continue
        try:
            payload = json.loads(value)
        except (TypeError, ValueError):
            continue
        detail, content, sender, title, text, conversation = \
            _notification_fields(payload)
        source_paths.append(source)
        data_list.append((
            epoch_datetime(detail.get("deliverTimestamp")),
            content.get("notificationType") or detail.get("Type", ""),
            payload.get("namespace", ""),
            title,
            text,
            sender,
            conversation,
            content.get("id") or detail.get("MessageId", ""),
            content.get("priority", ""),
            detail.get("SequenceNumber")
            or payload.get("namespaceSequenceNumber", ""),
            detail.get("RealtimeMessageIdentifier", ""),
            storage_sequence,
            context.get_relative_path(source),
        ))
    logfunc(f"Roblox Real-Time Notifications: {len(data_list)} notification(s).")
    return data_headers, data_list, "\n".join(source_paths)
