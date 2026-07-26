__artifacts_v2__ = {
    "signalConversations": {
        "name": "Signal Conversations",
        "description": "Direct conversations and groups held in the Signal "
                       "Desktop database, with the phone number and service "
                       "identifiers Signal recorded for each, the number of "
                       "messages recovered and the span they cover.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "PyCryptodome; the Signal database credential",
        "category": "Signal (Desktop)",
        "notes": "A conversation exists here once Signal has learned of the "
                 "account, which includes accounts that were never messaged "
                 "from this device. The message count distinguishes those.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 173 rows",
        },
    },
    "signalCalls": {
        "name": "Signal Calls",
        "description": "Call history from the Signal Desktop database: who the "
                       "call was with, whether it was audio or video, its "
                       "direction, how it ended and when.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "PyCryptodome; the Signal database credential",
        "category": "Signal (Desktop)",
        "notes": "Signal Desktop records calls it observed. A call placed or "
                 "answered on a phone linked to the same account may not appear "
                 "here, so an absent call is not evidence no call took place.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "phone",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 15 rows",
        },
    },
    "signalSessions": {
        "name": "Signal Sessions & Identity Keys",
        "description": "Signal Protocol sessions and identity keys the client "
                       "holds. A session exists for each device the client has "
                       "exchanged messages with, and an identity key record is "
                       "kept for each account whose key it has seen, together "
                       "with when that key was first recorded.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "PyCryptodome; the Signal database credential",
        "category": "Signal (Desktop)",
        "notes": "These records show cryptographic contact at the protocol "
                 "level, which can name accounts that no longer appear in any "
                 "message. Key material itself is not reported.",
        "paths": (
            '*/Signal*/sql/db.sqlite',
            '*/Signal*/config.json',
            '*/signal_password.txt',
            '*/signal-keychain.txt',
            '*/signal_db_key.txt',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "signal_macos": "Signal Desktop macOS, credential supplied | 165 rows",
        },
    },
}

import json
from datetime import datetime, timezone

from scripts import signal_desktop
from scripts.ilapfuncs import artifact_processor, logfunc

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)

_CALL_TYPES = {"Audio": "Audio", "Video": "Video", "Group": "Group call", "Adhoc": "Call link"}
_CALL_DIRECTIONS = {"Incoming": "Incoming", "Outgoing": "Outgoing"}


def _source(files_found):
    return next(iter(signal_desktop.database_files(files_found)), "")


@artifact_processor
def signalConversations(context):
    data_headers = (
        "Conversation", "Type", "Phone Number", "Messages Recovered",
        ("First Message", "datetime"), ("Last Message", "datetime"),
        ("Last Active", "datetime"), "Profile Name", "Service ID", "Group ID",
        "Members", "Conversation ID", "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        return data_headers, [], ""

    counts, spans = {}, {}
    for conversation_id, count, first, last in connection.execute(
            "SELECT conversationId, COUNT(*), MIN(sent_at), MAX(sent_at) "
            "FROM messages GROUP BY conversationId"):
        counts[conversation_id] = count
        spans[conversation_id] = (first, last)

    data_list = []
    query = """SELECT id, type, name, profileFullName, profileName, e164, serviceId,
                      groupId, members, active_at FROM conversations"""
    for (cid, ctype, name, full, profile, e164, service_id,
         group_id, members, active_at) in connection.execute(query):
        first, last = spans.get(cid, (None, None))
        member_list = ""
        if members:
            try:
                parsed = json.loads(members) if members.strip().startswith("[") else members.split()
                member_list = ", ".join(str(m) for m in parsed) if isinstance(parsed, list) else str(members)
            except (ValueError, AttributeError):
                member_list = str(members)
        data_list.append((
            name or full or profile or e164 or cid,
            "Group" if ctype == "group" else "Direct",
            e164 or "",
            counts.get(cid, 0),
            signal_desktop.js_ms_to_datetime(first),
            signal_desktop.js_ms_to_datetime(last),
            signal_desktop.js_ms_to_datetime(active_at),
            full or profile or "",
            service_id or "",
            group_id or "",
            member_list,
            cid or "",
            context.get_relative_path(_source(files_found)),
        ))

    connection.close()
    data_list.sort(key=lambda row: (-row[3], (row[0] or "").lower()))
    groups = sum(1 for row in data_list if row[1] == "Group")
    logfunc(f"Signal Conversations: {len(data_list)} conversation(s), {groups} group(s).")
    return data_headers, data_list, _source(files_found)


@artifact_processor
def signalCalls(context):
    data_headers = (
        ("Started", "datetime"), "With", "Call Type", "Direction", "Status",
        ("Ended", "datetime"), "Duration (s)", "Ringer", "Call ID", "Peer ID",
        "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        return data_headers, [], ""

    labels = signal_desktop.conversation_labels(connection)
    by_service = {}
    for service_id, cid in connection.execute(
            "SELECT serviceId, id FROM conversations WHERE serviceId IS NOT NULL"):
        by_service[service_id.lower()] = labels.get(cid, cid)

    data_list = []
    try:
        rows = connection.execute("""SELECT callId, peerId, ringerId, mode, type, direction,
                                            status, timestamp, endedTimestamp FROM callsHistory""")
    # Deliberately broad: an older schema may lack this table.
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Signal Calls: call history unavailable ({ex}).")
        connection.close()
        return data_headers, [], ""

    for (call_id, peer_id, ringer_id, mode, call_type, direction,
         status, timestamp, ended) in rows:
        duration = ""
        if timestamp and ended and ended > timestamp:
            duration = round((ended - timestamp) / 1000)
        data_list.append((
            signal_desktop.js_ms_to_datetime(timestamp),
            by_service.get((peer_id or "").lower()) or labels.get(peer_id, peer_id or ""),
            _CALL_TYPES.get(call_type, call_type or mode or ""),
            _CALL_DIRECTIONS.get(direction, direction or ""),
            status or "",
            signal_desktop.js_ms_to_datetime(ended),
            duration,
            by_service.get((ringer_id or "").lower()) or (ringer_id or ""),
            str(call_id or ""),
            peer_id or "",
            context.get_relative_path(_source(files_found)),
        ))

    connection.close()
    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Signal Calls: {len(data_list)} call(s).")
    return data_headers, data_list, _source(files_found)


@artifact_processor
def signalSessions(context):
    data_headers = (
        "Record", "Account", "Service ID", "Device ID", ("First Seen", "datetime"),
        "Verified State", "Non-Blocking Approval", "Source File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    connection, note = signal_desktop.open_database(files_found, log=logfunc)
    if connection is None:
        signal_desktop.explain(note, logfunc)
        return data_headers, [], ""

    labels = signal_desktop.conversation_labels(connection)
    by_service = {}
    for service_id, cid in connection.execute(
            "SELECT serviceId, id FROM conversations WHERE serviceId IS NOT NULL"):
        by_service[service_id.lower()] = labels.get(cid, cid)

    data_list = []
    try:
        rows = connection.execute(
            "SELECT conversationId, serviceId, deviceId FROM sessions")
        for conversation_id, service_id, device_id in rows:
            label = labels.get(conversation_id, "")
            if not label and service_id:
                label = by_service.get(service_id.lower(), "")
            data_list.append((
                "Session",
                label or conversation_id or "",
                service_id or "",
                device_id if device_id is not None else "",
                "", "", "",
                context.get_relative_path(_source(files_found)),
            ))
    # Deliberately broad: an older schema may lack this table.
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Signal Sessions: sessions table unavailable ({ex}).")

    try:
        for row in connection.execute("SELECT id, json FROM identityKeys"):
            identity_id, blob = row
            try:
                record = json.loads(blob) if blob else {}
            except (ValueError, TypeError):
                record = {}
            data_list.append((
                "Identity key",
                by_service.get((identity_id or "").lower(), ""),
                identity_id or "",
                "",
                signal_desktop.js_ms_to_datetime(record.get("timestamp")),
                record.get("verified", ""),
                "Yes" if record.get("nonblockingApproval") else "",
                context.get_relative_path(_source(files_found)),
            ))
    # Deliberately broad: an older schema may lack this table.
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Signal Sessions: identityKeys table unavailable ({ex}).")

    connection.close()
    data_list.sort(key=lambda row: (row[0], (row[1] or "").lower()))
    sessions = sum(1 for row in data_list if row[0] == "Session")
    logfunc(f"Signal Sessions & Identity Keys: {sessions} session(s), "
            f"{len(data_list) - sessions} identity key record(s).")
    return data_headers, data_list, _source(files_found)
