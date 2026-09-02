__artifacts_v2__ = {
    "slackSessions": {
        "name": "Slack Client Sessions",
        "description": "Client usage sessions reconstructed from the Slack "
                       "desktop app's 'activitySession_<teamId>' Local Storage "
                       "keys, one set per workspace. Each recovered version of "
                       "the key records a session with a start time, a "
                       "last-activity time and a last-logged time, giving a "
                       "usage timeline per workspace independent of any message "
                       "content. Because Local Storage is a LevelDB, superseded "
                       "versions of the key surface earlier sessions as well as "
                       "the most recent.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Slack (Desktop)",
        "notes": "'Duration' is Last Activity minus Session Start and is best "
                 "read as a lower bound on how long the client was open for "
                 "that session, not a guarantee it was in the foreground the "
                 "whole time. Slack Desktop is closed source, so the field "
                 "meanings follow the observed activitySession structure; they "
                 "were validated against a constructed known-data fixture, not "
                 "confirmed against Slack's own documentation.",
        "paths": (
            "*/Slack/Local Storage/leveldb/*",
            "*/slack/Local Storage/leveldb/*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "dleapp_slack_known": "Constructed known-data Slack Local Storage "
                "fixture (authored, not from a real device) | 3 sessions "
                "across 2 workspaces",
        },
    },
}

import json
import struct
import zlib
from datetime import datetime, timezone

from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.ilapfuncs import artifact_processor, logfunc

_READ_ERRORS = (OSError, ValueError, EOFError, IndexError, KeyError,
                struct.error, zlib.error)


def _records(context):
    records = []
    for folder in leveldb_folders([str(f) for f in context.get_files_found()]):
        try:
            for record in read_records(folder):
                if record.origin and "slack.com" not in record.origin.lower():
                    continue
                records.append(record)
        except _READ_ERRORS as ex:
            logfunc(f"Slack Client Sessions: could not read '{folder}': {ex}")
    records.sort(key=lambda record: -record.sequence)
    return records


def _load_json(record):
    try:
        return json.loads(record.value)
    except (ValueError, TypeError):
        return None


def _epoch_ms_to_dt(value):
    if not value:
        return ""
    try:
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return ""


def _format_duration(start_dt, end_dt):
    if not isinstance(start_dt, datetime) or not isinstance(end_dt, datetime):
        return ""
    seconds = (end_dt - start_dt).total_seconds()
    if seconds < 0:
        return ""
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


@artifact_processor
def slackSessions(context):
    data_headers = (
        "Team ID", "Session ID", ("Session Start", "datetime"),
        ("Last Activity", "datetime"), ("Last Logged", "datetime"), "Duration",
        "LevelDB Sequence", "Record State", "Source File",
    )

    data_list = []
    seen = set()
    source_path = ""

    for record in _records(context):
        if not record.key.startswith("activitySession_"):
            continue
        sessions = _load_json(record)
        if not isinstance(sessions, dict):
            continue
        team_id = record.key[len("activitySession_"):]

        for session_id, session in sessions.items():
            if not isinstance(session, dict):
                continue
            source_path = source_path or context.get_relative_path(record.source)

            start_dt = _epoch_ms_to_dt(session.get("startTime"))
            activity_dt = _epoch_ms_to_dt(session.get("lastActivity"))
            logged_dt = _epoch_ms_to_dt(session.get("lastLogged"))

            key = (team_id, session_id, session.get("startTime"),
                   session.get("lastActivity"), session.get("lastLogged"))
            if key in seen:
                continue
            seen.add(key)

            data_list.append((
                team_id,
                session_id,
                start_dt,
                activity_dt,
                logged_dt,
                _format_duration(start_dt, activity_dt),
                record.sequence,
                record.state,
                context.get_relative_path(record.source),
            ))

    data_list.sort(
        key=lambda row: row[2] if isinstance(row[2], datetime)
        else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    logfunc(f"Slack Client Sessions: {len(data_list)} session(s) recovered.")
    return data_headers, data_list, source_path
