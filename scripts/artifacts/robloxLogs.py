__artifacts_v2__ = {
    "robloxGameJoins": {
        "name": "Roblox Game Joins",
        "description": "Roblox experience joins reconstructed from Player logs, "
                       "including UTC time, place and universe IDs, game instance, "
                       "account, join attempt, party, join origin, and the UDMUX and "
                       "RCC server addresses recorded by the client.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "UDMUX and RCC labels follow the source log. In the tested corpus "
                 "UDMUX was public-routable and RCC used private address space, but "
                 "that relationship is an observation rather than a guaranteed "
                 "Roblox format rule. Log rotation limits historical coverage.",
        "paths": (
            "*/Library/Logs/Roblox/*_Player_*.log",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 3 rows",
        },
    },
    "robloxHttpActivity": {
        "name": "Roblox HTTP Activity",
        "description": "HTTP responses and failures recorded by Roblox Player, "
                       "showing the log-event time, destination URL and host, status, "
                       "server IP, elapsed time, body size and retry state.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "URLs and query parameters are reported verbatim for evidentiary "
                 "analysis and may contain tokens or credential-like values. The "
                 "parser does not determine whether those values remain valid or "
                 "reusable. Player-log URLs form a partial activity record, not "
                 "browser history.",
        "paths": (
            "*/Library/Logs/Roblox/*_Player_*.log",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 71 rows",
        },
    },
    "robloxPlayerLog": {
        "name": "Roblox Player Log",
        "description": "All structured Roblox Player log events with their UTC "
                       "timestamp, process-relative elapsed time, severity, logging "
                       "component and message.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (macOS)",
        "notes": "Long messages are limited to 10,000 characters. The first "
                 "untimestamped policy line and multiline continuations are omitted.",
        "paths": (
            "*/Library/Logs/Roblox/*_Player_*.log",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "roblox_macos": "Roblox 0.732.0.7321040 macOS | 2249 rows",
        },
    },
}

import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.roblox import iso_datetime


_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T[^,]+),"
    r"(?P<elapsed>[^,]+),(?P<thread>[^,]+),(?P<level>\d+)"
    r"(?:,(?P<severity>\w+))? \[(?P<component>[^\]]+)\] (?P<message>.*)$")
_JOIN_RE = re.compile(
    r"! Joining game ['\"](?P<job>[^'\"]+)['\"] place "
    r"(?P<place>\d+) at (?P<rcc>[0-9a-fA-F:.]+)")
_LOAD_RE = re.compile(
    r"placeid:(?P<place>\d+),\s*userid:(?P<user>\d+),\s*"
    r"universeid:(?P<universe>\d+)", re.I)
_UDMUX_RE = re.compile(
    r"UDMUX Address = (?P<address>[0-9a-fA-F:.]+), Port = (?P<port>\d+)"
    r"(?: \| RCC Server Address = (?P<rcc>[0-9a-fA-F:.]+), Port = (?P<rccport>\d+))?")
_BODY_FIELDS = {
    "join_attempt": re.compile(r'"gameJoinAttemptId"\s*:\s*"([^"]+)"'),
    "party": re.compile(r'"partyId"\s*:\s*"([^"]+)"'),
    "origin": re.compile(r'"joinOrigin"\s*:\s*"([^"]+)"'),
    "place": re.compile(r'"placeId"\s*:\s*(\d+)'),
}
_URL_RE = re.compile(r'url:\{\s*"([^"]+)"')
_STATUS_RE = re.compile(r"\bstatus:(\d+)(?:\s+([^ ]+))?")
_TIME_RE = re.compile(r"\btime:([\d.]+)ms")
_BODY_SIZE_RE = re.compile(r"\bbodySize:(\d+)")
_IP_RE = re.compile(r"\bip:([0-9a-fA-F:.]+)")
_EXTERNAL_RE = re.compile(r"\bexternal:(\d+)")
_RETRY_RE = re.compile(r"\bnumberOfTimesRetried:(\d+)")
_ERROR_RE = re.compile(r"\berror:(\d+)\s+message:([^ ]+)")


def _iter_lines(paths):
    seen = set()
    for path in map(str, paths):
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, 1):
                    match = _LINE_RE.match(line.rstrip("\n"))
                    if match:
                        yield path, line_number, match.groupdict()
        except OSError as ex:
            logfunc(f"Roblox logs: could not read '{path}': {ex}")


def _sort_time(value):
    return value if isinstance(value, datetime) else datetime.min.replace(tzinfo=timezone.utc)


@artifact_processor
def robloxGameJoins(context):
    data_headers = (
        ("Joined", "datetime"), "Place ID", "Universe ID", "Game Instance ID",
        "User ID", "Public Server", "Public Port", "RCC Server", "RCC Port",
        "Join Attempt ID", "Party ID", "Join Origin", "Source File", "Line",
    )
    joins = []
    source_paths = []
    pending = {}
    current_by_file = {}

    for path, line_number, fields in _iter_lines(context.get_files_found()):
        message = fields["message"]
        if "joinGamePost" in message and " BODY:" in message:
            pending[path] = {}
            for key, pattern in _BODY_FIELDS.items():
                match = pattern.search(message)
                pending[path][key] = match.group(1) if match else ""

        match = _JOIN_RE.search(message)
        if match:
            item = {
                "time": iso_datetime(fields["timestamp"]),
                "place": match.group("place"),
                "universe": "",
                "job": match.group("job"),
                "user": "",
                "public": "",
                "public_port": "",
                "rcc": match.group("rcc"),
                "rcc_port": "",
                "join_attempt": pending.get(path, {}).get("join_attempt", ""),
                "party": pending.get(path, {}).get("party", ""),
                "origin": pending.get(path, {}).get("origin", ""),
                "path": path,
                "line": line_number,
            }
            joins.append(item)
            current_by_file[path] = item
            if path not in source_paths:
                source_paths.append(path)
            continue

        current = current_by_file.get(path)
        if not current:
            continue
        match = _LOAD_RE.search(message)
        if match:
            current["place"] = match.group("place")
            current["user"] = match.group("user")
            current["universe"] = match.group("universe")
        match = _UDMUX_RE.search(message)
        if match:
            current["public"] = match.group("address")
            current["public_port"] = match.group("port")
            current["rcc"] = match.group("rcc") or current["rcc"]
            current["rcc_port"] = match.group("rccport") or ""

    data_list = [(
        item["time"], item["place"], item["universe"], item["job"], item["user"],
        item["public"], item["public_port"], item["rcc"], item["rcc_port"],
        item["join_attempt"], item["party"], item["origin"],
        context.get_relative_path(item["path"]), item["line"],
    ) for item in joins]
    data_list.sort(key=lambda row: _sort_time(row[0]))
    logfunc(f"Roblox Game Joins: {len(data_list)} join(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def robloxHttpActivity(context):
    data_headers = (
        ("Response/Failure Logged", "datetime"), "Host", "URL", "HTTP Status", "Error",
        "Server IP", "Elapsed (ms)", "Body Size (bytes)", "External",
        "Retries", "Source File", "Line",
    )
    data_list = []
    source_paths = []
    for path, line_number, fields in _iter_lines(context.get_files_found()):
        message = fields["message"]
        url_match = _URL_RE.search(message)
        if not url_match or "Http" not in fields["component"]:
            continue
        url = url_match.group(1)
        status = _STATUS_RE.search(message)
        timing = _TIME_RE.search(message)
        body_size = _BODY_SIZE_RE.search(message)
        ip_address = _IP_RE.search(message)
        external = _EXTERNAL_RE.search(message)
        retries = _RETRY_RE.search(message)
        error = _ERROR_RE.search(message)
        try:
            host = urlsplit(url).hostname or ""
        except ValueError:
            host = ""
        data_list.append((
            iso_datetime(fields["timestamp"]), host, url,
            status.group(1) if status else "",
            f"{error.group(1)}: {error.group(2)}" if error else "",
            ip_address.group(1) if ip_address else "",
            timing.group(1) if timing else "",
            body_size.group(1) if body_size else "",
            "Yes" if external and external.group(1) == "1" else "No",
            retries.group(1) if retries else "",
            context.get_relative_path(path), line_number,
        ))
        if path not in source_paths:
            source_paths.append(path)
    data_list.sort(key=lambda row: _sort_time(row[0]))
    logfunc(f"Roblox HTTP Activity: {len(data_list)} request record(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def robloxPlayerLog(context):
    data_headers = (
        ("Timestamp", "datetime"), "Elapsed (s)", "Severity", "Component",
        "Thread", "Level", "Message", "Source File", "Line",
    )
    data_list = []
    source_paths = []
    for path, line_number, fields in _iter_lines(context.get_files_found()):
        data_list.append((
            iso_datetime(fields["timestamp"]),
            fields["elapsed"],
            fields["severity"] or "",
            fields["component"],
            fields["thread"],
            fields["level"],
            fields["message"][:10000],
            context.get_relative_path(path),
            line_number,
        ))
        if path not in source_paths:
            source_paths.append(path)
    data_list.sort(key=lambda row: _sort_time(row[0]))
    logfunc(f"Roblox Player Log: {len(data_list)} structured event(s).")
    return data_headers, data_list, "\n".join(source_paths)
