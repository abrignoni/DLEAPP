__artifacts_v2__ = {
    "discordRecoveredMedia": {
        "name": "Discord Recovered Media",
        "description": "Discord media recovered from the client's cache and embedded in the report: attachments, "
                       "avatars, server avatars, emoji, stickers, server icons, banners and images fetched "
                       "through images-ext-N.discordapp.net/external/, identified by URL. An attachment's URL "
                       "carries its channel ID and attachment ID, so the file can be dated and placed in its "
                       "channel even when no cached message carries it.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. A response is recovered when its URL has one of the forms named in the "
                 "description and its cached body is not empty; the kind comes from the URL, not from the "
                 "bytes. Created is the timestamp in the attachment, emoji or sticker ID, read with the "
                 "layout Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156), "
                 "and is empty for other kinds. Attachment URLs have the form attachments/<channel "
                 "ID>/<attachment ID>/<file name>: on discord_macos the first number was the channel of "
                 "the message declaring the attachment for all 3,070 cached copies whose message was "
                 "recovered. Message Recovered is Yes when a recovered message declares the attachment's "
                 "ID and No when none does, and is empty for other kinds. 7,491 of the 7,736 cached "
                 "attachment copies on discord_macos were fetched with a format parameter in the URL, and "
                 "2,770 of the 3,070 copies whose message was recovered were served as image/webp where "
                 "the message declared another type, so a recovered file need not match the uploaded file "
                 "byte for byte. One row per cached response: 1,670 of the 2,231 attachment IDs with a "
                 "cached copy on discord_macos had more than one copy, each at a different URL. Identical "
                 "bytes are stored in the report once, because a media item is keyed on the SHA-1 of its "
                 "bytes. Size (bytes) is the length of the body after any content encoding is removed. "
                 "Source Cache File names the file the response body was read from: the entry's *_0 file "
                 "in a simple cache, or the data_N or f_ file holding the body in a blockfile cache. "
                 "Chromium removes cache entries once the cache grows past its size limit (see Discord "
                 "Cache Records), so a file missing here may still have been fetched.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Cache/index',
            '*/discord*/Cache/data_*',
            '*/discord*/Cache/f_*',
            '*/discord*/Cache/Cache_Data/index',
            '*/discord*/Cache/Cache_Data/data_*',
            '*/discord*/Cache/Cache_Data/f_*',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "image",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 12424 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 84 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the cache held no Discord media URL)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc


def _channel_label(scan, channel_id):
    channel = scan.channels.get(channel_id) or {}
    if channel.get("name"):
        return f"#{channel['name']}"
    return channel.get("recipients") or channel_id or ""


@artifact_processor
def discordRecoveredMedia(context):
    data_headers = (
        ("Created", "datetime"), "Kind", ("Media", "media"), "Filename",
        "Channel", "Message Recovered", "Content Type", "Size (bytes)",
        "Owner ID", "Related ID", ("Cached", "datetime"), "URL",
        "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.media:
        return data_headers, [], ""

    # Attachment ids that still have a cached message behind them.
    known_attachments = {}
    for message_id, wrapper in scan.messages.items():
        for attachment in wrapper["message"].get("attachments") or []:
            if isinstance(attachment, dict) and attachment.get("id"):
                known_attachments[str(attachment["id"])] = message_id

    data_list = []
    for path, media in sorted(scan.media.items(), key=lambda item: item[1]["url"]):
        entry = discord_api.cached_entry(path)
        if entry is None:
            continue
        body = entry.decoded_body()
        if not body:
            continue

        content_type = (media.get("content_type") or "").split(";")[0].strip()
        filename = discord_api.attachment_filename(media["url"])
        # Prefer the served type for images and video (frequently WebP rather
        # than the uploaded type), otherwise keep the uploaded extension.
        if content_type.startswith(("image/", "video/", "audio/")):
            extension = content_type.split("/")[-1]
        else:
            extension = os.path.splitext(filename)[1].lstrip(".")
        created = discord_api.snowflake_to_datetime(media["owner_id"]) \
            if media["kind"] in ("Attachment", "Emoji", "Sticker") else ""
        reference = check_in_embedded_media(
            media.get("source", path), body, filename or f"{media['owner_id'] or 'media'}.{extension or 'bin'}",
            force_type=content_type or None, force_extension=extension or None)
        if not reference:
            continue

        linked = ""
        if media["kind"] == "Attachment":
            linked = "Yes" if media["owner_id"] in known_attachments else "No"

        data_list.append((
            created,
            media["kind"],
            reference,
            filename,
            _channel_label(scan, media["related_id"]) if media["related_id"] else "",
            linked,
            content_type,
            len(body),
            media["owner_id"],
            media["related_id"],
            media["cached"],
            media["url"],
            context.get_relative_path(media.get("source", path)),
        ))

    data_list.sort(key=lambda row: (row[1], row[0] if isinstance(row[0], datetime)
                                    else datetime.min.replace(tzinfo=timezone.utc)))
    orphans = {row[8] for row in data_list if row[5] == "No"}
    logfunc(f"Discord Recovered Media: {len(data_list)} cached file(s) recovered, "
            f"including {len(orphans)} attachment(s) with no surviving cached message.")
    sources = sorted({media.get("source", path) for path, media in scan.media.items()})
    return data_headers, data_list, "\n".join(sources[:50])
