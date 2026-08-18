__artifacts_v2__ = {
    "chatgptComputerHistoryEvents": {
        "name": "ChatGPT Computer History Events",
        "description": "Activity events written by the ChatGPT desktop app's "
                       "Computer History feature into rolling segment folders, "
                       "one row per event, carrying the event timestamp and kind, "
                       "the frontmost application and bundle identifier, window "
                       "title and URL, typed text, selected text and range, key "
                       "equivalents and modifiers, mouse button and drag "
                       "endpoints, the accessibility element the event names, and "
                       "the accessibility tree snapshot attached to the record. "
                       "Events the feature's observation rules excluded are "
                       "reported from the suppressed file and marked in the "
                       "Stream column.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-08-18",
        "last_update_date": "2026-08-18",
        "requirements": "none",
        "category": "ChatGPT (macOS)",
        "notes": "VALIDATION BOUNDARY: the event decoder is shared with the "
                 "ChatGPT Record & Replay Events artifact and was proven against "
                 "a recorded capture, but no genuine Computer History segment was "
                 "available. The path pattern, the segment layout and the "
                 "suppressed stream were exercised only against a synthetic "
                 "fixture built by restaging those recorded events, so they are "
                 "shown to run and are not corpus-verified; the segment root "
                 "directory in particular is a plausible placement rather than an "
                 "observed one. The "
                 "app's bundle identifier is com.openai.codex. Computer History "
                 "is off by default and gated by subscription. The recorder's own "
                 "summarizer prompt describes the raw segments as ephemeral and "
                 "not persisted, so segments present at acquisition may cover a "
                 "short window only; the durable output is the Markdown summaries "
                 "covered by the ChatGPT Computer History Memories artifact. Event "
                 "kind values are reported as stored. Typed and selected text, "
                 "element values and accessibility trees are reported verbatim and "
                 "may contain personal or credential-like content. The recorder "
                 "binary carries credit-card, API-key, AWS-key, bearer-token and "
                 "secret redaction placeholders; in a tested Record & Replay "
                 "capture no placeholder appeared and test values typed into "
                 "TextEdit were written in plaintext, and whether this feature "
                 "behaves the same way was not tested, so redaction should not be "
                 "assumed. A row in the Stream column reading suppressed means the "
                 "event was written to the suppressed file; what the observation "
                 "rules were at the time is not recorded in these files. Text "
                 "fields and accessibility trees are clipped at 10,000 characters. "
                 "The path pattern anchors on the app group identifier the "
                 "service declares in its entitlements rather than on the Group "
                 "Containers folder above it, so an extraction rooted part way "
                 "down the tree still matches. Times are as recorded, in UTC.",
        "paths": (
            "*2DC432GLL2.com.openai.sky.CUAService/*/segments/*/events.jsonl",
            "*2DC432GLL2.com.openai.sky.CUAService/*/segments/*/suppressed.jsonl",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "chatgpt_macos": "Computer History not offered on the tested account, no segments present | 0 rows",
            "chatgpt_computerhistory_synthetic": "SYNTHETIC layout fixture, 21 recorded and 2 suppressed | 23 rows",
        },
    },
    "chatgptComputerHistorySegments": {
        "name": "ChatGPT Computer History Segments",
        "description": "One row per Computer History segment, from the "
                       "metadata.json written beside the segment's event files, "
                       "with the recorded start and end times, the reason the "
                       "segment ended, the session and segment identifiers, the "
                       "recorded and suppressed event counts, and the event-file "
                       "paths as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-08-18",
        "last_update_date": "2026-08-18",
        "requirements": "none",
        "category": "ChatGPT (macOS)",
        "notes": "VALIDATION BOUNDARY: exercised only against a synthetic fixture, "
                 "not corpus-verified. No genuine Computer History segment was "
                 "available, so the field names read here were taken from the "
                 "recorder binary's own literals rather than from a decoded file, "
                 "and the fixture was built from those same literals, which means "
                 "it demonstrates the reader runs and cannot confirm the real file "
                 "carries these keys. Any field the file does not carry is "
                 "reported empty. The Record & Replay feature writes a "
                 "session.json with a different key set, so that file is covered "
                 "by a separate artifact and not by this one. A count reported "
                 "here is the count the segment recorded, which is not the same "
                 "claim as the number of rows this parser read from the event "
                 "file. Duration is calculated by this parser from the recorded "
                 "start and end times and is not a stored field. End reason values "
                 "are reported as stored. Times are as recorded, in UTC.",
        "paths": (
            "*2DC432GLL2.com.openai.sky.CUAService/*/segments/*/metadata.json",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "list",
        "sample_data": {
            "chatgpt_macos": "Computer History not offered on the tested account, no segments present | 0 rows",
            "chatgpt_computerhistory_synthetic": "SYNTHETIC layout fixture | 1 rows",
        },
    },
    "chatgptComputerHistoryMemories": {
        "name": "ChatGPT Computer History Memories",
        "description": "Markdown activity summaries written by the ChatGPT "
                       "desktop app's Computer History feature under the Codex "
                       "memories directory, with the timestamp and summary window "
                       "taken from the file name, the summary text, and the file's "
                       "modification time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-08-18",
        "last_update_date": "2026-08-18",
        "requirements": "none",
        "category": "ChatGPT (macOS)",
        "notes": "VALIDATION BOUNDARY: exercised only against a synthetic fixture, "
                 "not corpus-verified. No genuine memory file was available, so "
                 "the fixture's file names were built from the same documentation "
                 "this parser reads them with. The directory layout and the "
                 "10min and 6h summary windows come from the skill documentation "
                 "the app ships at plugins/computer-history/skills/computer-"
                 "history/SKILL.md, and the file-name timestamp is parsed with the "
                 "date format the recorder binary carries. A file name that does "
                 "not match is reported with its stem intact and an empty "
                 "timestamp rather than being skipped. These summaries are written "
                 "by a language model from the recorded event stream, so they are "
                 "generated descriptions of activity and not a direct record of "
                 "it; the events they were derived from may no longer be present. "
                 "The instructions.md in the same directory is reported alongside "
                 "them with an empty summary window. File modification time comes "
                 "from the file system of the extraction and may reflect "
                 "acquisition rather than authorship. The memories directory is "
                 "located relative to CODEX_HOME, which the app's own launcher "
                 "script defaults to ~/.codex but allows to be relocated, so the "
                 "path pattern anchors on the memories/extensions/skysight tail "
                 "rather than on the .codex folder name. Content is clipped at "
                 "10,000 characters.",
        "paths": (
            "*/memories/extensions/skysight/resources/*.md",
            "*/memories/extensions/skysight/instructions.md",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "chatgpt_macos": "Computer History not offered on the tested account, no memories present | 0 rows",
            "chatgpt_computerhistory_synthetic": "SYNTHETIC layout fixture, 2 summaries and instructions.md | 3 rows",
        },
    },
}

import os
import re
from datetime import datetime, timezone

from scripts.chatgpt_skysight import (
    EVENT_HEADERS,
    clip,
    event_row,
    iso_datetime,
    iter_events,
    read_json,
    sort_key,
)
from scripts.ilapfuncs import artifact_processor, logfunc

# The recorder binary carries the date format yyyy-MM-dd'T'HH-mm-ss, which is
# what the segment folders and the memory file names are built from.
_STAMP = r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}"
_MEMORY_NAME = re.compile(
    rf"^(?P<stamp>{_STAMP})-(?P<identifier>.+?)-(?P<window>10min|6h)-(?P<slug>.+)$")


def _stamp_datetime(value):
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H-%M-%S")
    except (TypeError, ValueError):
        return ""
    return parsed.replace(tzinfo=timezone.utc)


def _segment_folder(path):
    return os.path.basename(os.path.dirname(path))


@artifact_processor
def chatgptComputerHistoryEvents(context):
    data_headers = EVENT_HEADERS[:-1] + ("Stream", "Segment", "Source File")
    data_list = []
    source_paths = []

    for path in map(str, context.get_files_found()):
        name = os.path.basename(path).lower()
        if name not in ("events.jsonl", "suppressed.jsonl"):
            continue
        stream = "suppressed" if name.startswith("suppressed") else "events"
        relative = context.get_relative_path(path)
        segment = _segment_folder(path)
        found = False
        for _line_number, record in iter_events(path):
            data_list.append(
                event_row(record, relative)[:-1] + (stream, segment, relative))
            found = True
        if found and path not in source_paths:
            source_paths.append(path)

    data_list.sort(key=sort_key)
    logfunc(f"ChatGPT Computer History Events: {len(data_list)} event(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def chatgptComputerHistorySegments(context):
    data_headers = (
        ("Started", "datetime"),
        ("Ended", "datetime"),
        "Duration (seconds)",
        "End Reason",
        "Session ID",
        "Segment ID",
        "Recorded Event Count",
        "Recorded Suppressed Event Count",
        "Recorded Events Path",
        "Recorded Suppressed Events Path",
        "Segment Folder",
        "Source File",
    )
    data_list = []
    source_paths = []

    for path in map(str, context.get_files_found()):
        metadata = read_json(path)
        if not isinstance(metadata, dict):
            logfunc(f"ChatGPT Computer History: could not read segment '{path}'.")
            continue
        started = iso_datetime(metadata.get("startedAt"))
        ended = iso_datetime(metadata.get("endedAt"))
        duration = ""
        if started and ended:
            duration = int((ended - started).total_seconds())
        data_list.append((
            started,
            ended,
            duration,
            metadata.get("endReason", ""),
            metadata.get("sessionID", ""),
            metadata.get("segmentID", ""),
            metadata.get("eventCount", ""),
            metadata.get("suppressedEventCount", ""),
            metadata.get("eventsPath", ""),
            metadata.get("suppressedEventsPath", ""),
            _segment_folder(path),
            context.get_relative_path(path),
        ))
        if path not in source_paths:
            source_paths.append(path)

    data_list.sort(key=sort_key)
    logfunc(f"ChatGPT Computer History Segments: {len(data_list)} segment(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def chatgptComputerHistoryMemories(context):
    data_headers = (
        ("Summary Timestamp", "datetime"),
        ("File Modified", "datetime"),
        "Summary Window",
        "Identifier",
        "Slug",
        "Characters",
        "Content",
        "Source File",
    )
    data_list = []
    source_paths = []

    for path in map(str, context.get_files_found()):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except OSError as ex:
            logfunc(f"ChatGPT Computer History: could not read memory '{path}': {ex}")
            continue

        stem = os.path.splitext(os.path.basename(path))[0]
        match = _MEMORY_NAME.match(stem)
        if match:
            stamp = _stamp_datetime(match.group("stamp"))
            identifier = match.group("identifier")
            window = match.group("window")
            slug = match.group("slug")
        else:
            stamp = ""
            identifier = stem
            window = ""
            slug = ""

        try:
            modified = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            modified = ""

        data_list.append((
            stamp,
            modified,
            window,
            identifier,
            slug,
            len(content),
            clip(content),
            context.get_relative_path(path),
        ))
        if path not in source_paths:
            source_paths.append(path)

    data_list.sort(key=sort_key)
    logfunc(f"ChatGPT Computer History Memories: {len(data_list)} memory file(s).")
    return data_headers, data_list, "\n".join(source_paths)
