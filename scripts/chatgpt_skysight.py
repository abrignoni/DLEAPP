"""Shared helpers for the ChatGPT (macOS) activity recording artifacts.

The ChatGPT desktop app ships a bundled service whose own binary names the
activity-recording subsystem Skysight. Two features write records in the same
newline-delimited JSON format:

* Record & Replay writes one on-demand session per folder, alongside a
  ``session.json`` describing it.
* Computer History writes a rolling set of ``segments/<timestamp>/`` folders,
  each with an ``events.jsonl``, an optional ``suppressed.jsonl`` and a
  ``metadata.json``.

The event-kind vocabulary below is spelled as it appears in the recorder binary
and in recorded output. ``terminal.value_changed`` and ``debug.error`` are
declared by the recorder but were not produced by the tested capture.

Author: @AlexisBrignoni, Claude
"""

import json
from datetime import datetime

# Long free-text fields are clipped so a single accessibility snapshot cannot
# dominate the report. The clip is marked with a trailing ellipsis.
TEXT_LIMIT = 10000

EVENT_KINDS = (
    "session.started",
    "session.ended",
    "window.changed",
    "mouse.click",
    "mouse.context_menu",
    "mouse.drag",
    "keyboard.text_input",
    "keyboard.submit",
    "keyboard.shortcut",
    "terminal.value_changed",
    "selection.changed",
    "debug.error",
)

EVENT_HEADERS = (
    ("Timestamp", "datetime"),
    "Event",
    "Application",
    "Bundle ID",
    "Window Title",
    "Window URL",
    "Typed Text",
    "Selected Text",
    "Selection Offset",
    "Selection Length",
    "Key Equivalent",
    "Modifiers",
    "Mouse Button",
    "Drag Origin (App / Window)",
    "Drag Destination (App / Window)",
    "Element Role",
    "Element Subrole",
    "Element Identifier",
    "Element Title",
    "Element Value",
    "Element Description",
    "Accessibility Capture Mode",
    "Accessibility Tree",
    "Event ID",
    "Source File",
)


def iso_datetime(value):
    """Parse the ISO-8601 UTC timestamp carried on each event record."""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return ""


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return None


def iter_events(path):
    """Yield ``(line number, record)`` for each decodable line of an events file.

    A line that does not decode is skipped rather than aborting the file, so one
    truncated write does not discard the events around it.
    """
    try:
        handle = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return
    with handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                yield line_number, record


def clip(value, limit=TEXT_LIMIT):
    """Render a value as text, clipping to ``limit`` characters."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    elif not isinstance(value, str):
        value = str(value)
    if len(value) > limit:
        return value[:limit] + "…"
    return value


def _dict(parent, key):
    value = parent.get(key) if isinstance(parent, dict) else None
    return value if isinstance(value, dict) else {}


def _endpoint(node):
    """Summarise a drag endpoint as its application and window, as recorded."""
    if not isinstance(node, dict):
        return ""
    app = _dict(node, "app").get("name", "")
    window = _dict(node, "window").get("title", "")
    parts = [part for part in (app, window) if part]
    return " / ".join(parts)


def _element(record):
    """Return the element the event names, wherever the record carries it.

    The recorder attaches it as ``target`` under mouse, keyboard and selection
    events, and as ``element`` inside a drag's destination.
    """
    mouse = _dict(record, "mouse")
    for candidate in (
        _dict(record, "selection").get("target"),
        _dict(record, "keyboard").get("target"),
        mouse.get("target"),
        _dict(mouse, "destination").get("element"),
        _dict(mouse, "origin").get("element"),
    ):
        if isinstance(candidate, dict) and candidate:
            return candidate
    return {}


def event_row(record, source_file):
    """Flatten one event record into a row matching ``EVENT_HEADERS``."""
    app = _dict(record, "app")
    window = _dict(record, "window")
    mouse = _dict(record, "mouse")
    keyboard = _dict(record, "keyboard")
    selection = _dict(record, "selection")
    accessibility = _dict(record, "ax")
    element = _element(record)
    selected_range = _dict(selection, "selectedRange")
    modifiers = keyboard.get("modifiers") or mouse.get("modifiers") or []
    if isinstance(modifiers, list):
        modifiers = ", ".join(str(item) for item in modifiers)

    return (
        iso_datetime(record.get("timestamp")),
        record.get("kind", ""),
        app.get("name", ""),
        app.get("bundleIdentifier", ""),
        window.get("title", ""),
        window.get("url", ""),
        clip(keyboard.get("text", "")),
        clip(selection.get("selectedText", "")),
        selected_range.get("location", ""),
        selected_range.get("length", ""),
        keyboard.get("keyEquivalent", ""),
        clip(modifiers),
        mouse.get("button", ""),
        _endpoint(mouse.get("origin")),
        _endpoint(mouse.get("destination")),
        element.get("role", ""),
        element.get("subrole", ""),
        element.get("identifier", ""),
        clip(element.get("title", "")),
        clip(element.get("value", "")),
        clip(element.get("description", "")),
        accessibility.get("mode", ""),
        clip(accessibility.get("text", "")),
        record.get("id", ""),
        source_file,
    )


def sort_key(row):
    """Sort rows by timestamp, keeping undated rows together at the start."""
    value = row[0]
    return (0, value) if isinstance(value, datetime) else (1, datetime.min)
