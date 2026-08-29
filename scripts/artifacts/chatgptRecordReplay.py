__artifacts_v2__ = {
    "chatgptRecordReplayEvents": {
        "name": "ChatGPT Record & Replay Events",
        "description": "Activity events written by the ChatGPT desktop app's "
                       "Record & Replay feature, one row per event, carrying the "
                       "event timestamp and kind, the frontmost application and "
                       "bundle identifier, window title and URL, typed text, "
                       "selected text and range, key equivalents and modifiers, "
                       "mouse button and drag endpoints, the accessibility "
                       "element the event names, and the accessibility tree "
                       "snapshot attached to the record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-08-18",
        "last_update_date": "2026-08-29",
        "requirements": "none",
        "category": "ChatGPT (macOS)",
        "notes": "Recording is started from within the app and time-limited by it, so "
                 "these files cover the recorded sessions only and are not a "
                 "continuous activity record. The app's bundle identifier is "
                 "com.openai.codex. Event kind values are reported as stored; "
                 "the recorder declares twelve, of which the tested capture "
                 "produced ten, leaving terminal.value_changed and debug.error "
                 "code-present but unexercised. Typed and selected text, element "
                 "values and accessibility trees are reported verbatim and may "
                 "contain personal or credential-like content. The recorder "
                 "binary carries credit-card, API-key, AWS-key, bearer-token and "
                 "secret redaction placeholders; in the tested capture a "
                 "non-issued test card number and an sk-test- string typed into "
                 "TextEdit were written in plaintext and no placeholder appeared, "
                 "so redaction should not be assumed. Text fields and "
                 "accessibility trees are clipped at 10,000 characters. The path pattern anchors on the "
                 "app group identifier the service declares in its entitlements "
                 "rather than on the Group Containers folder above it, so an "
                 "extraction rooted part way down the tree still matches. Times "
                 "are as recorded, in UTC.",
        "paths": (
            "*2DC432GLL2.com.openai.sky.CUAService/*/RecordAndReplay/*/events.jsonl",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "chatgpt_macos": "ChatGPT 26.810.41047 macOS | 21 rows",
        },
    },
    "chatgptRecordReplaySessions": {
        "name": "ChatGPT Record & Replay Sessions",
        "description": "One row per Record & Replay session folder, from the "
                       "session.json the ChatGPT desktop app writes beside the "
                       "event file, with the recorded start and end times, the "
                       "reason the recording ended, the session identifier and "
                       "the event-file path as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-08-18",
        "last_update_date": "2026-08-18",
        "requirements": "none",
        "category": "ChatGPT (macOS)",
        "notes": "session.json records no event count, unlike the metadata.json "
                 "the Computer History feature writes for its segments. The "
                 "recorded events path is the absolute path on the machine that "
                 "produced the recording and will not resolve inside an "
                 "extraction. End reason values are reported as stored. Duration "
                 "is calculated by this parser from the recorded start and end "
                 "times and is not a stored field. Times are as recorded, in UTC.",
        "paths": (
            "*2DC432GLL2.com.openai.sky.CUAService/*/RecordAndReplay/*/session.json",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "chatgpt_macos": "ChatGPT 26.810.41047 macOS | 1 rows",
        },
    },
}

from scripts.chatgpt_skysight import (
    EVENT_HEADERS,
    event_row,
    iso_datetime,
    iter_events,
    read_json,
    sort_key,
)
from scripts.ilapfuncs import artifact_processor, logfunc


@artifact_processor
def chatgptRecordReplayEvents(context):
    data_list = []
    source_paths = []

    for path in map(str, context.get_files_found()):
        relative = context.get_relative_path(path)
        found = False
        for _line_number, record in iter_events(path):
            data_list.append(event_row(record, relative))
            found = True
        if found and path not in source_paths:
            source_paths.append(path)

    data_list.sort(key=sort_key)
    logfunc(f"ChatGPT Record & Replay Events: {len(data_list)} event(s).")
    return EVENT_HEADERS, data_list, "\n".join(source_paths)


@artifact_processor
def chatgptRecordReplaySessions(context):
    data_headers = (
        ("Started", "datetime"),
        ("Ended", "datetime"),
        "Duration (seconds)",
        "End Reason",
        "Session ID",
        "Recorded Events Path",
        "Source File",
    )
    data_list = []
    source_paths = []

    for path in map(str, context.get_files_found()):
        session = read_json(path)
        if not isinstance(session, dict):
            logfunc(f"ChatGPT Record & Replay: could not read session '{path}'.")
            continue
        started = iso_datetime(session.get("startedAt"))
        ended = iso_datetime(session.get("endedAt"))
        duration = ""
        if started and ended:
            duration = int((ended - started).total_seconds())
        data_list.append((
            started,
            ended,
            duration,
            session.get("endReason", ""),
            session.get("id", ""),
            session.get("eventsPath", ""),
            context.get_relative_path(path),
        ))
        if path not in source_paths:
            source_paths.append(path)

    data_list.sort(key=sort_key)
    logfunc(f"ChatGPT Record & Replay Sessions: {len(data_list)} session(s).")
    return data_headers, data_list, "\n".join(source_paths)
