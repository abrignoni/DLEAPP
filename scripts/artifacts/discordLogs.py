__artifacts_v2__ = {
    "discordNavigation": {
        "name": "Discord Channel Navigation",
        "description": "Routing lines from the Discord client's renderer log: the server and channel, and any "
                       "message ID, of each route the client moved to, with the time as the log wrote it.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Reads renderer log lines that name [Routing/Utils] and Transitioning to "
                 "/channels/<server>/<channel>, with an optional message ID. A route with @me in place of "
                 "a server ID is shown as Direct messages: the client's script builds a channel route with "
                 "@me when there is no server and names /channels/@me as its ME route "
                 "(https://discord.com/assets/web.b8b5ddfa0f88ae29.js). Timestamp (Device Local Time) is "
                 "the time as the log wrote it, carried as text: the log records no offset, so the time is "
                 "not converted and no instant is asserted. On the tested macOS profile, 65 of the 461 "
                 "routing lines lined up within 7 seconds with a cached message fetch for the same channel "
                 "once shifted by a whole number of hours, and none lined up unshifted. The Time Zone the "
                 "Discord Account & Application artifact reports is the Sentry scope's value as of its "
                 "last write and does not show the zone in use when each line was written. Coverage "
                 "reaches back only as far as the log files the client kept: on discord_macos those were "
                 "renderer_js.log and renderer_js.old.log, with 153 and 308 rows.",
        "paths": (
            '*/discord*/logs/renderer_js*.log',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "navigation",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 461 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 153 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordGatewaySessions": {
        "name": "Discord Gateway Sessions",
        "description": "Lines the Discord client's renderer log wrote about its gateway connection: the event, "
                       "the gateway host, the session ID and any duration, with the time as the log wrote it.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Event is the bracketed tag after [GatewaySocket], title-cased: discord_macos held "
                 "Connect, Connected, Resume, Resumed, Ws Closed, Ready, Fast Connect, Reset and Ack "
                 "Timeout. Gateway Host is the wss:// host named in the line, Session ID a session value "
                 "of 16 or more hexadecimal characters, and Duration (ms) a number written as in N ms or "
                 "took Nms; Detail is the rest of the line. Timestamp (Device Local Time) is the time as "
                 "the log wrote it, carried as text: the log records no offset, so the time is not "
                 "converted and no instant is asserted. See the Discord Channel Navigation notes for how "
                 "those times relate to UTC on the tested macOS profile. On discord_macos 1,482 rows came "
                 "from renderer_js.old.log and 194 from renderer_js.log.",
        "paths": (
            '*/discord*/logs/renderer_js*.log',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "plug",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 1676 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 194 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc

_LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[(\w+)\]\s+(.*)$")
_ROUTE_RE = re.compile(
    r"\[Routing/Utils\].*?Transitioning to /channels/(@me|\d+)/(\d+)(?:/(\d+))?")
_GATEWAY_RE = re.compile(r"\[GatewaySocket\]\s+\[([A-Z ]+)\]\s*(.*)$")
_SESSION_RE = re.compile(r"session ([0-9a-f]{16,})")
_HOST_RE = re.compile(r"wss://([^/\s,]+)")
_TIMING_RE = re.compile(r"in (\d+) ?ms|took (\d+)ms")


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
        "Timestamp (Device Local Time)", "Destination",
        "Server ID", "Channel ID", "Message ID", "Source File",
    )

    data_list = []
    sources = set()
    for file_found, timestamp, _level, message in _iter_log_lines(
            context.get_files_found()):
        match = _ROUTE_RE.search(message)
        if not match:
            continue
        sources.add(file_found)
        guild = match.group(1)
        data_list.append((
            timestamp,
            "Direct messages" if guild == "@me" else f"Server {guild}",
            "" if guild == "@me" else guild,
            match.group(2),
            match.group(3) or "",
            context.get_relative_path(file_found),
        ))

    # Times are kept as written (no offset is recorded); _LINE_RE fixes their
    # YYYY-MM-DD HH:MM:SS.mmm shape, so sorting the text sorts by time.
    data_list.sort(key=lambda row: row[0])
    logfunc(f"Discord Channel Navigation: {len(data_list)} navigation event(s).")
    return data_headers, data_list, "\n".join(sorted(sources))


@artifact_processor
def discordGatewaySessions(context):
    data_headers = (
        "Timestamp (Device Local Time)", "Event", "Gateway Host",
        "Session ID", "Duration (ms)", "Detail", "Source File",
    )

    data_list = []
    sources = set()
    for file_found, timestamp, _level, message in _iter_log_lines(
            context.get_files_found()):
        match = _GATEWAY_RE.search(message)
        if not match:
            continue
        sources.add(file_found)
        detail = match.group(2).strip()
        host = _HOST_RE.search(detail)
        session = _SESSION_RE.search(detail)
        timing = _TIMING_RE.search(detail)
        data_list.append((
            timestamp,
            match.group(1).strip().title(),
            host.group(1) if host else "",
            session.group(1) if session else "",
            (timing.group(1) or timing.group(2)) if timing else "",
            detail,
            context.get_relative_path(file_found),
        ))

    # Times are kept as written (no offset is recorded); _LINE_RE fixes their
    # YYYY-MM-DD HH:MM:SS.mmm shape, so sorting the text sorts by time.
    data_list.sort(key=lambda row: row[0])
    logfunc(f"Discord Gateway Sessions: {len(data_list)} gateway event(s).")
    return data_headers, data_list, "\n".join(sorted(sources))
