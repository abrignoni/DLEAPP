__artifacts_v2__ = {
    "telegramAccounts": {
        "name": "Telegram Desktop Accounts",
        "description": "Account identity and installation metadata recovered "
                       "offline from Telegram Desktop's authenticated tdata "
                       "storage, including user ID, names, username, phone value, "
                       "main data center, active-account state and app version.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "PyCryptodome",
        "category": "Telegram Desktop",
        "notes": "The parser validates TDF checksums and local encryption integrity. "
                 "It never reports Telegram local keys, MTProto authorization "
                 "keys, or peer access hashes. An empty local passcode is tried "
                 "by default; for a passcode-protected acquisition an examiner "
                 "may place telegram_local_passcode.txt beside tdata."
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
            "*/Telegram Desktop/telegram_local_passcode.txt",
            "*/TelegramDesktop/telegram_local_passcode.txt",
            "*/.TelegramDesktop/telegram_local_passcode.txt",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "telegram_macos": "Telegram Desktop 7.0.6 macOS | 1 row",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.telegram import TelegramDataError, load_profile


@artifact_processor
def telegramAccounts(context):
    data_headers = (
        "Account Index", "Active", "User ID", "First Name", "Last Name",
        "Username", "Phone", "Main DC", "App Version", "tdata Directory",
    )
    try:
        profile = load_profile(context.get_files_found())
    except (OSError, TelegramDataError) as ex:
        logfunc(f"Telegram Desktop Accounts: {ex}")
        return data_headers, [], ""

    rows = []
    for account in profile.accounts:
        peer = account["self"]
        rows.append((
            account["index"] + 1,
            "Yes" if account["active"] else "No",
            account["user_id"],
            peer.get("first_name", ""),
            peer.get("last_name", ""),
            peer.get("username", ""),
            peer.get("phone", ""),
            account["main_dc"],
            profile.version,
            context.get_relative_path(str(profile.tdata)),
        ))
    logfunc(f"Telegram Desktop Accounts: {len(rows)} account(s).")
    return data_headers, rows, str(profile.tdata / "key_datas")
