__artifacts_v2__ = {
    "telegramRecentPeers": {
        "name": "Telegram Desktop Recent Peers",
        "description": "Locally retained Telegram Desktop top/recent peer "
                       "suggestions, with rank, rating and cached identity fields "
                       "such as peer ID, name, username, and phone value.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "PyCryptodome",
        "category": "Telegram Desktop",
        "notes": "This is interaction-proximity evidence, not proof that a message "
                 "was exchanged. Peer access hashes are intentionally not "
                 "reported. Last Seen Value is Telegram's raw encoded status, not "
                 "a Unix timestamp. Rows come only from Telegram's live local "
                 "suggestion lists after cryptographic validation."
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
            "*/Telegram Desktop/tdata/key_data*",
            "*/TelegramDesktop/tdata/key_data*",
            "*/.TelegramDesktop/tdata/key_data*",
            "*/Telegram Desktop/tdata/????????????????s",
            "*/TelegramDesktop/tdata/????????????????s",
            "*/.TelegramDesktop/tdata/????????????????s",
            "*/Telegram Desktop/tdata/????????????????/map*",
            "*/TelegramDesktop/tdata/????????????????/map*",
            "*/.TelegramDesktop/tdata/????????????????/map*",
            "*/Telegram Desktop/tdata/????????????????/????????????????s",
            "*/TelegramDesktop/tdata/????????????????/????????????????s",
            "*/.TelegramDesktop/tdata/????????????????/????????????????s",
            "*/Telegram Desktop/telegram_local_passcode.txt",
            "*/TelegramDesktop/telegram_local_passcode.txt",
            "*/.TelegramDesktop/telegram_local_passcode.txt",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "telegram_macos": "Telegram Desktop 7.0.6 macOS | 2 rows",
        },
    },
    "telegramLocalFiles": {
        "name": "Telegram Desktop Local Files",
        "description": "Concrete local file paths retained in Telegram Desktop's "
                       "encrypted file-location map, with Telegram media key, "
                       "recorded modification time and size.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "PyCryptodome",
        "category": "Telegram Desktop",
        "notes": "Internal wildcard placeholders such as *media_cache* are "
                 "suppressed. A retained path indicates Telegram associated a "
                 "media object with that local path; it does not prove the file "
                 "still exists in the acquisition. Qt 5.1 local timestamps do "
                 "not preserve a timezone and are therefore reported without "
                 "one; explicitly UTC values retain UTC."
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
            "*/Telegram Desktop/tdata/key_data*",
            "*/TelegramDesktop/tdata/key_data*",
            "*/.TelegramDesktop/tdata/key_data*",
            "*/Telegram Desktop/tdata/????????????????s",
            "*/TelegramDesktop/tdata/????????????????s",
            "*/.TelegramDesktop/tdata/????????????????s",
            "*/Telegram Desktop/tdata/????????????????/map*",
            "*/TelegramDesktop/tdata/????????????????/map*",
            "*/.TelegramDesktop/tdata/????????????????/map*",
            "*/Telegram Desktop/tdata/????????????????/????????????????s",
            "*/TelegramDesktop/tdata/????????????????/????????????????s",
            "*/.TelegramDesktop/tdata/????????????????/????????????????s",
            "*/Telegram Desktop/telegram_local_passcode.txt",
            "*/TelegramDesktop/telegram_local_passcode.txt",
            "*/.TelegramDesktop/telegram_local_passcode.txt",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file",
        "sample_data": {
            "telegram_macos": "Telegram Desktop 7.0.6 macOS | 2 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.telegram import (
    TelegramDataError, load_profile, parse_locations,
    parse_search_suggestions,
)


@artifact_processor
def telegramRecentPeers(context):
    data_headers = (
        "Account User ID", "List", "Rank", "Rating", "Peer Type", "Peer ID",
        "Name", "Username", "Phone", "Contact", "Last Seen Value", "Source File",
    )
    try:
        profile = load_profile(context.get_files_found())
    except (OSError, TelegramDataError) as ex:
        logfunc(f"Telegram Desktop Recent Peers: {ex}")
        return data_headers, [], ""
    rows = []
    sources = []
    for account in profile.accounts:
        try:
            path, peers, _searches = parse_search_suggestions(profile, account)
        except (OSError, TelegramDataError) as ex:
            logfunc(f"Telegram Desktop Recent Peers: {ex}")
            continue
        if path:
            sources.append(str(path))
        for peer in peers:
            name = peer.get("name") or " ".join(filter(None, (
                peer.get("first_name"), peer.get("last_name")
            )))
            rows.append((
                account["user_id"],
                peer["collection"],
                peer["rank"],
                peer["rating"],
                peer["peer_type"],
                peer["peer_id"],
                name,
                peer.get("username", ""),
                peer.get("phone", ""),
                "Yes" if peer.get("is_contact") else "No",
                peer.get("last_seen", ""),
                context.get_relative_path(str(path)),
            ))
    logfunc(f"Telegram Desktop Recent Peers: {len(rows)} peer(s).")
    return data_headers, rows, "\n".join(sources)


@artifact_processor
def telegramLocalFiles(context):
    data_headers = (
        ("Recorded Modified", "datetime"), "Account User ID", "Local Path",
        "Filename", "Size (bytes)", "Telegram Media Key", "Legacy Type",
        "Source File",
    )
    try:
        profile = load_profile(context.get_files_found())
    except (OSError, TelegramDataError) as ex:
        logfunc(f"Telegram Desktop Local Files: {ex}")
        return data_headers, [], ""
    rows = []
    sources = []
    for account in profile.accounts:
        try:
            path, records = parse_locations(profile, account)
        except (OSError, TelegramDataError) as ex:
            logfunc(f"Telegram Desktop Local Files: {ex}")
            continue
        if path:
            sources.append(str(path))
        for item in records:
            rows.append((
                item["modified"],
                account["user_id"],
                item["filename"],
                os.path.basename(item["filename"]),
                item["size"],
                item["media_key"],
                item["legacy_type"],
                context.get_relative_path(str(path)),
            ))
    rows.sort(key=lambda row: str(row[0]))
    logfunc(f"Telegram Desktop Local Files: {len(rows)} local file(s).")
    return data_headers, rows, "\n".join(sources)
