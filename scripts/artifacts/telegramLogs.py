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
                 "are reported as local wall-clock values without one."
                 " On Linux, Telegram Desktop's working folder, which holds tdata and its log files, is the one"
                 " psAppDataPath gives unless a portable or custom working folder is in use "
                 "(https://github.com/telegramdesktop/tdesktop/blob/d81a5ac270fdcb5315b49f813614caa71f85697f/Telegram/SourceFiles/logs.cpp#L358-L377):"
                 " ~/.TelegramDesktop when its tdata already holds settings, otherwise the AppLocalDataLocation"
                 " folder "
                 "(https://github.com/telegramdesktop/tdesktop/blob/d81a5ac270fdcb5315b49f813614caa71f85697f/Telegram/SourceFiles/platform/linux/specific_linux.cpp#L688-L702),"
                 " which Qt resolves to $XDG_DATA_HOME/TelegramDesktop, ~/.local/share/TelegramDesktop by "
                 "default, for an application named TelegramDesktop "
                 "(https://github.com/qt/qtbase/blob/5a8637e4516bc48a0b3f4b5ec3b18618b92e7222/src/corelib/io/qstandardpaths_unix.cpp#L28-L39"
                 " and "
                 "https://github.com/qt/qtbase/blob/5a8637e4516bc48a0b3f4b5ec3b18618b92e7222/src/corelib/io/qstandardpaths_unix.cpp#L219-L237;"
                 " "
                 "https://github.com/telegramdesktop/tdesktop/blob/d81a5ac270fdcb5315b49f813614caa71f85697f/Telegram/SourceFiles/core/launcher.cpp#L343)."
                 " The declared paths match both folder names; that was tested only with a copy of the macOS "
                 "profile placed under ~/.local/share/TelegramDesktop and under ~/.TelegramDesktop, which gave "
                 "the same rows as at the macOS path apart from the source file paths.",
        "paths": (
            "*/Telegram Desktop/log*.txt",
            "*/TelegramDesktop/log*.txt",
            "*/.TelegramDesktop/log*.txt",
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
