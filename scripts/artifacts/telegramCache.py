__artifacts_v2__ = {
    "telegramRecoveredCache": {
        "name": "Telegram Desktop Recovered Cache",
        "description": "Live media objects recovered by validating Telegram "
                       "Desktop's cache binlog, decrypting its TDEF objects with "
                       "the profile local key, and accepting only recognized "
                       "image, animation, audio, video, document, or archive "
                       "signatures. Recovered cleartext is embedded in the report.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-08-01",
        "requirements": "PyCryptodome",
        "category": "Telegram Desktop",
        "notes": "Only live binlog entries whose backing object exists and passes "
                 "TDEF authentication are included. Deleted/stale entries and "
                 "unrecognized serialized cache objects are suppressed. The "
                 "cache key is an opaque Telegram media identifier and does not "
                 "by itself identify a chat or message. Cache tags come from "
                 "Telegram's own image/sticker/voice/video-message/animation "
                 "classification. The tag-to-label mapping was established "
                 "from the Telegram Desktop cache implementation cited in "
                 "scripts/telegram.py; a tag outside that mapping is reported "
                 "as Unknown with the raw value shown alongside."
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
            "*/Telegram Desktop/tdata/user_data/cache/*/binlog*",
            "*/TelegramDesktop/tdata/user_data/cache/*/binlog*",
            "*/.TelegramDesktop/tdata/user_data/cache/*/binlog*",
            "*/Telegram Desktop/tdata/user_data/cache/*/*/*",
            "*/TelegramDesktop/tdata/user_data/cache/*/*/*",
            "*/.TelegramDesktop/tdata/user_data/cache/*/*/*",
            "*/Telegram Desktop/tdata/user_data/media_cache/*/binlog*",
            "*/TelegramDesktop/tdata/user_data/media_cache/*/binlog*",
            "*/.TelegramDesktop/tdata/user_data/media_cache/*/binlog*",
            "*/Telegram Desktop/tdata/user_data/media_cache/*/*/*",
            "*/TelegramDesktop/tdata/user_data/media_cache/*/*/*",
            "*/.TelegramDesktop/tdata/user_data/media_cache/*/*/*",
            "*/Telegram Desktop/telegram_local_passcode.txt",
            "*/TelegramDesktop/telegram_local_passcode.txt",
            "*/.TelegramDesktop/telegram_local_passcode.txt",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "image",
        "sample_data": {
            "telegram_macos": "Telegram Desktop 7.0.6 macOS | 239 rows",
        },
    },
}

from scripts.ilapfuncs import (
    artifact_processor, check_in_embedded_media, logfunc,
)
from scripts.telegram import TelegramDataError, iter_cache_media, load_profile

_CACHE_TAGS = {
    0: "Unclassified",
    1: "Image",
    2: "Sticker",
    3: "Voice Message",
    4: "Video Message",
    5: "Animation",
}


@artifact_processor
def telegramRecoveredCache(context):
    data_headers = (
        ("Last Cache Use", "datetime"), ("Recovered Media", "media"),
        "Media Kind", "MIME Type", "Clear Size (bytes)", "Cache", "Cache Key",
        "Cache Tag", "Cache Tag Value", "Encrypted Source File", "Index File",
    )
    try:
        profile = load_profile(context.get_files_found(), load_accounts=False)
    except (OSError, TelegramDataError) as ex:
        logfunc(f"Telegram Desktop Recovered Cache: {ex}")
        return data_headers, [], ""

    rows = []
    for item in iter_cache_media(profile):
        name = (
            f"telegram_{item['cache']}_"
            f"{item['key'].replace(':', '_')}.{item['extension']}"
        )
        reference = check_in_embedded_media(
            str(item["source"]), item["data"], name,
            force_type=item["mime"], force_extension=item["extension"],
            force_modification_date=item["used"] or None,
        )
        rows.append((
            item["used"],
            reference,
            item["kind"],
            item["mime"],
            item["size"],
            item["cache"],
            item["key"],
            _CACHE_TAGS.get(item["tag"], "Unknown"),
            item["tag"],
            context.get_relative_path(str(item["source"])),
            context.get_relative_path(str(item["binlog"])),
        ))
    rows.sort(key=lambda row: str(row[0]))
    logfunc(f"Telegram Desktop Recovered Cache: {len(rows)} media object(s).")
    return data_headers, rows, str(profile.tdata / "user_data")
