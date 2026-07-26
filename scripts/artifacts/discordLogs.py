__artifacts_v2__ = {
    "discordNavigation": {
        "name": "Discord Channel Navigation",
        "description": "Channels and servers the client routed to inside the "
                       "application, taken from the renderer log the desktop "
                       "app writes. Each entry records the destination the "
                       "client navigated to at that time, naming the server, "
                       "the channel and, where the route targeted one, a "
                       "specific message ID. Timestamps are the device's local "
                       "time, not UTC.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Renderer log timestamps are written in the device's local "
                 "time with no offset recorded, so they must be reconciled "
                 "against the time zone reported by the Discord Account & "
                 "Application artifact before being placed on a UTC timeline. "
                 "The log rotates, so coverage reaches back only as far as the "
                 "retained renderer_js logs.",
        "paths": (
            '*/discord*/logs/renderer_js*.log',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "navigation",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 461 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 153 rows",
        },
    },
    "discordGatewaySessions": {
        "name": "Discord Gateway Sessions",
        "description": "Connections the client made to the Discord real-time "
                       "gateway, from the renderer log. Shows when the app came "
                       "online, which regional gateway it used and which "
                       "session it resumed, so the events bracket the intervals "
                       "in which the client held a gateway connection. "
                       "Timestamps are the device's local time, not UTC.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Timestamps are device local time, as written by the client, "
                 "and must be reconciled against the time zone reported by the "
                 "Discord Account & Application artifact. The gateway hostname "
                 "contains the region label Discord assigned to the "
                 "connection.",
        "paths": (
            '*/discord*/logs/renderer_js*.log',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "plug",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 1676 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 194 rows",
        },
    },
}

import os
import re
from datetime import datetime

from scripts.ilapfuncs import artifact_processor, logfunc

_LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[(\w+)\]\s+(.*)$")
_ROUTE_RE = re.compile(
    r"\[Routing/Utils\].*?Transitioning to /channels/(@me|\d+)/(\d+)(?:/(\d+))?")
_GATEWAY_RE = re.compile(r"\[GatewaySocket\]\s+\[([A-Z ]+)\]\s*(.*)$")
_SESSION_RE = re.compile(r"session ([0-9a-f]{16,})")
_HOST_RE = re.compile(r"wss://([^/\s,]+)")
_TIMING_RE = re.compile(r"in (\d+) ?ms|took (\d+)ms")


def _parse_local_time(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return ""


def _iter_log_lines(files_found):
    seen = set()
    for file_found in files_found:
        file_found = str(file_found)
        try:
            real = os.path.realpath(file_found)
        except OSError:
            real = file_found
        if real in seen:
            continue
        seen.add(real)
        try:
            with open(file_found, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    match = _LINE_RE.match(line.rstrip("\n"))
                    if match:
                        yield file_found, match.group(1), match.group(2), match.group(3)
        except OSError as ex:
            logfunc(f"Discord logs: could not read '{file_found}': {ex}")


@artifact_processor
def discordNavigation(context):
    data_headers = (
        ("Timestamp (Device Local Time)", "datetime"), "Destination",
        "Server ID", "Channel ID", "Message ID", "Source File",
    )

    data_list = []
    source_path = ""
    for file_found, timestamp, _level, message in _iter_log_lines(
            context.get_files_found()):
        match = _ROUTE_RE.search(message)
        if not match:
            continue
        source_path = source_path or file_found
        guild = match.group(1)
        data_list.append((
            _parse_local_time(timestamp),
            "Direct messages" if guild == "@me" else f"Server {guild}",
            "" if guild == "@me" else guild,
            match.group(2),
            match.group(3) or "",
            context.get_relative_path(file_found),
        ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else datetime.min)
    logfunc(f"Discord Channel Navigation: {len(data_list)} navigation event(s).")
    return data_headers, data_list, source_path


@artifact_processor
def discordGatewaySessions(context):
    data_headers = (
        ("Timestamp (Device Local Time)", "datetime"), "Event", "Gateway Host",
        "Session ID", "Duration (ms)", "Detail", "Source File",
    )

    data_list = []
    source_path = ""
    for file_found, timestamp, _level, message in _iter_log_lines(
            context.get_files_found()):
        match = _GATEWAY_RE.search(message)
        if not match:
            continue
        source_path = source_path or file_found
        detail = match.group(2).strip()
        host = _HOST_RE.search(detail)
        session = _SESSION_RE.search(detail)
        timing = _TIMING_RE.search(detail)
        data_list.append((
            _parse_local_time(timestamp),
            match.group(1).strip().title(),
            host.group(1) if host else "",
            session.group(1) if session else "",
            (timing.group(1) or timing.group(2)) if timing else "",
            detail,
            context.get_relative_path(file_found),
        ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else datetime.min)
    logfunc(f"Discord Gateway Sessions: {len(data_list)} gateway event(s).")
    return data_headers, data_list, source_path
