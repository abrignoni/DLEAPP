__artifacts_v2__ = {
    "discordRecoveredMedia": {
        "name": "Discord Recovered Media",
        "description": "Every cached file this parser could identify as Discord "
                       "media and decode, extracted and embedded in the report: "
                       "images, video, avatars, emoji, stickers and server "
                       "icons. Attachment URLs carry the channel ID and an "
                       "attachment snowflake, so a "
                       "cached file can be tied to its channel and dated even "
                       "when the message that carried it is long gone. The "
                       "'Message Recovered' column flags files whose "
                       "attachment ID matches no message recovered from this "
                       "cache. The cache evicts over time, so the absence of a "
                       "file here does not indicate it was never present.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "The served content type is frequently WebP rather than the "
                 "uploaded type, so recovered bytes are often a transcode "
                 "rather than the "
                 "original upload and will not necessarily hash to the file as "
                 "it was uploaded. One "
                 "row per cached file: the same image appears more than once "
                 "where the client fetched it at several sizes, though "
                 "identical bytes are stored only once.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "image",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 12424 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 84 rows",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.chromium.simple_cache import read_entry
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
        entry = read_entry(path)
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
            path, body, filename or f"{media['owner_id'] or 'media'}.{extension or 'bin'}",
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
            context.get_relative_path(path),
        ))

    data_list.sort(key=lambda row: (row[1], row[0] if isinstance(row[0], datetime)
                                    else datetime.min.replace(tzinfo=timezone.utc)))
    orphans = {row[8] for row in data_list if row[5] == "No"}
    logfunc(f"Discord Recovered Media: {len(data_list)} cached file(s) recovered, "
            f"including {len(orphans)} attachment(s) with no surviving cached message.")
    return data_headers, data_list, "\n".join(sorted(scan.media)[:50])
