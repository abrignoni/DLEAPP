__artifacts_v2__ = {
    "telegramLogs": {
        "name": "Telegram Desktop Application Log",
        "description": "Case-relevant timestamped Telegram Desktop log events "
                       "showing launches, version and path information, account/"
                       "encrypted-storage loading, key-count state, and warnings "
                       "or errors.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Telegram Desktop",
        "notes": "Routine rendering, font, display, and audio-device chatter is "
                 "suppressed. A log line mentioning a message is application "
                 "diagnostic text and is not recovered message content. Telegram "
                 "does not encode a timezone in these log timestamps, so they "
                 "are reported as local wall-clock values without one.",
        "paths": (
            "*/Telegram Desktop/log*.txt",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-lines",
        "sample_data": {
            "telegram_macos": "Telegram Desktop 7.0.6 macOS | 12 rows",
        },
    },
}

import re
from datetime import datetime

from scripts.ilapfuncs import artifact_processor, logfunc

_LINE = re.compile(r"^\[(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\] (.*)$")
_KEEP = re.compile(
    r"^(Launched version:|Executable dir:|Working dir:|Command line:|"
    r"App Info: reading accounts info|App Info: reading encrypted info|"
    r"App Info: reading map|App Info: reading encrypted map|"
    r"App Info: reading encrypted user settings|"
    r"App Info: reading encrypted mtp data|MTP Info: read keys|"
    r".*(?:Error|Warning):)",
    re.IGNORECASE,
)


@artifact_processor
def telegramLogs(context):
    data_headers = (("Timestamp", "datetime"), "Event", "Source File")
    rows = []
    sources = []
    for path in map(str, context.get_files_found()):
        sources.append(path)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    match = _LINE.match(line.rstrip())
                    if not match or not _KEEP.search(match.group(2)):
                        continue
                    timestamp = datetime.strptime(
                        match.group(1), "%Y.%m.%d %H:%M:%S"
                    )
                    rows.append((
                        timestamp,
                        match.group(2),
                        context.get_relative_path(path),
                    ))
        except OSError as ex:
            logfunc(f"Telegram Desktop Application Log: {ex}")
    rows.sort(key=lambda row: row[0])
    logfunc(f"Telegram Desktop Application Log: {len(rows)} event(s).")
    return data_headers, rows, "\n".join(sources)
