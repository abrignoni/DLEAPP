__artifacts_v2__ = {
    "discordMessages": {
        "name": "Discord Messages",
        "description": "Chat messages recovered from the Discord Desktop HTTP "
                       "cache. Discord renders its UI from REST API responses, "
                       "and those JSON responses stay in the Chromium cache "
                       "after the app closes. A cached response is a copy of "
                       "what the API returned to this client at the moment it "
                       "was stored, and it is not updated if the message is "
                       "later edited or deleted server-side. The cache evicts "
                       "over time, so the absence of a message here does not "
                       "indicate it was never sent. Where the attachment image "
                       "is also still cached it is recovered and shown against "
                       "its message.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Parses cached responses to /api/v*/channels/<id>/messages and "
                 "the message search endpoints. Each cached copy is a "
                 "point-in-time snapshot and the most recent one is reported, so "
                 "an edit made after the last cache write is not reflected here. "
                 "Direction is resolved against the signed-in account id taken "
                 "from the Sentry scope and Local Storage.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-circle",
        "data_views": {
            "conversation": {
                "conversationDiscriminatorColumn": "Channel ID",
                "conversationLabelColumn": "Channel",
                "textColumn": "Message",
                "timeColumn": "Timestamp",
                "directionColumn": "Direction",
                "directionSentValue": "Sent",
                "senderColumn": "Sender",
                "mediaColumn": "Attachments",
            }
        },
    },
    "discordAttachments": {
        "name": "Discord Attachments",
        "description": "Files shared in Discord conversations, taken from the "
                       "attachment metadata inside cached message responses and "
                       "linked to the cached copy of the file itself where one "
                       "survives. Each row records an attachment the API "
                       "reported on a message: its filename, declared size and "
                       "type, the account that posted the message and the "
                       "channel it appeared in. The attachment ID is a "
                       "snowflake, so the upload time is recoverable from the "
                       "URL alone even when the file itself is gone. The cache "
                       "evicts over time, so the absence of a file here does "
                       "not indicate it was never shared.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Cached copies are frequently the WebP variant Discord serves "
                 "to the client rather than the original upload, so the "
                 "recovered bytes can differ from the file the sender chose. "
                 "The reported size is the size declared by the API.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "paperclip",
    },
}

import os
from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.chromium.simple_cache import read_entry
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

# Discord caps a message at ten attachments, so this never truncates a message.
_MAX_MEDIA_PER_MESSAGE = 10


def _channel_label(scan, channel_id):
    channel = scan.channels.get(channel_id) or {}
    if channel.get("name"):
        return f"#{channel['name']}"
    if channel.get("recipients"):
        return channel["recipients"]
    return channel_id or ""


def _best_cached_media(scan):
    """Map attachment id -> the largest cached copy of that attachment."""
    best = {}
    for path, media in scan.media.items():
        if media["kind"] != "Attachment" or not media["owner_id"]:
            continue
        current = best.get(media["owner_id"])
        if current is None or media["size"] > current[1]["size"]:
            best[media["owner_id"]] = (path, media)
    return best


def _recover_media(path, media, filename):
    """Check the cached bytes in as a media item and return its reference id."""
    entry = read_entry(path)
    if entry is None:
        return None
    body = entry.decoded_body()
    if not body:
        return None
    extension = os.path.splitext(filename)[1].lstrip(".")
    content_type = media.get("content_type", "").split(";")[0].strip()
    # Discord transcodes to WebP on delivery; trust the served type over the name.
    if content_type.startswith("image/") or content_type.startswith("video/"):
        extension = content_type.split("/")[-1]
    return check_in_embedded_media(
        path, body, filename or f"{media['owner_id']}.{extension or 'bin'}",
        force_type=content_type or None,
        force_extension=extension or None,
        force_creation_date=_epoch(media.get("cached")),
    )


def _epoch(value):
    if isinstance(value, datetime):
        return int(value.timestamp())
    return None


def _describe_embeds(message):
    parts = []
    for embed in message.get("embeds") or []:
        if not isinstance(embed, dict):
            continue
        label = embed.get("title") or embed.get("description") or embed.get("type") or ""
        url = embed.get("url") or ""
        parts.append(f"{label} {url}".strip() if label or url else "embed")
    return "\n".join(parts)


def _describe_stickers(message):
    return ", ".join(
        sticker.get("name", "") for sticker in (message.get("sticker_items") or [])
        if isinstance(sticker, dict))


def _reply_reference(message):
    reference = message.get("message_reference")
    if not isinstance(reference, dict):
        return ""
    referenced = message.get("referenced_message")
    if isinstance(referenced, dict):
        author = discord_api.user_display(referenced.get("author"))
        content = (referenced.get("content") or "").replace("\n", " ")
        if author or content:
            return f"{author}: {content[:120]}"
    return f"message {reference.get('message_id', '')}"


@artifact_processor
def discordMessages(context):
    data_headers = (
        ("Timestamp", "datetime"), "Direction", "Sender", "Channel", "Message",
        ("Attachments", "media"), "Attachment Names", ("Edited", "datetime"),
        "Reply To", "Mentions", "Embeds", "Stickers", "Message Type", "Pinned",
        "Sender ID", "Channel ID", "Message ID", ("Cached", "datetime"),
        "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.messages:
        return data_headers, [], ""

    account = discord_api.find_local_account(files_found)
    local_ids = account["ids"] or ({account["id"]} if account["id"] else set())
    cached_media = _best_cached_media(scan)

    data_list = []
    for message_id, wrapper in scan.messages.items():
        message = wrapper["message"]
        author = message.get("author") or {}
        author_id = str(author.get("id") or "")
        sent = discord_api.iso_to_datetime(message.get("timestamp")) \
            or discord_api.snowflake_to_datetime(message_id)

        media_refs = []
        names = []
        for attachment in (message.get("attachments") or [])[:_MAX_MEDIA_PER_MESSAGE]:
            if not isinstance(attachment, dict):
                continue
            names.append(attachment.get("filename", ""))
            found = cached_media.get(str(attachment.get("id")))
            if found:
                reference = _recover_media(found[0], found[1],
                                           attachment.get("filename", ""))
                if reference:
                    media_refs.append(reference)

        data_list.append((
            sent,
            "Sent" if author_id and author_id in local_ids else "Received",
            discord_api.user_display(author),
            _channel_label(scan, str(message.get("channel_id") or "")),
            message.get("content") or "",
            media_refs,
            ", ".join(n for n in names if n),
            discord_api.iso_to_datetime(message.get("edited_timestamp")),
            _reply_reference(message),
            ", ".join(discord_api.user_display(m) for m in (message.get("mentions") or [])
                      if isinstance(m, dict)),
            _describe_embeds(message),
            _describe_stickers(message),
            discord_api.message_type_name(message.get("type")),
            "Yes" if message.get("pinned") else "",
            author_id,
            str(message.get("channel_id") or ""),
            message_id,
            wrapper["cached"],
            context.get_relative_path(wrapper["source"]),
        ))

    data_list.sort(key=lambda row: (row[15], row[0] if isinstance(row[0], datetime)
                                    else datetime.min.replace(tzinfo=timezone.utc)))
    logfunc(f"Discord Messages: {len(data_list)} message(s) from "
            f"{len(scan.channels)} channel(s) across {scan.entry_count} cache entries.")
    source = "\n".join(sorted({wrapper["source"] for wrapper in scan.messages.values()})[:50])
    return data_headers, data_list, source


@artifact_processor
def discordAttachments(context):
    data_headers = (
        ("Uploaded", "datetime"), "Sender", "Channel", "Filename",
        ("Recovered File", "media"), "Declared Size (bytes)", "Content Type",
        "Dimensions", "Cached Copy", ("Message Sent", "datetime"), "Message",
        "Sender ID", "Channel ID", "Attachment ID", "Message ID", "URL",
        "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.messages:
        return data_headers, [], ""

    cached_media = _best_cached_media(scan)

    data_list = []
    for message_id, wrapper in scan.messages.items():
        message = wrapper["message"]
        attachments = message.get("attachments") or []
        if not attachments:
            continue
        author = message.get("author") or {}
        channel_id = str(message.get("channel_id") or "")
        sent = discord_api.iso_to_datetime(message.get("timestamp")) \
            or discord_api.snowflake_to_datetime(message_id)

        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue
            attachment_id = str(attachment.get("id") or "")
            filename = attachment.get("filename", "")
            found = cached_media.get(attachment_id)
            reference = None
            if found:
                reference = _recover_media(found[0], found[1], filename)
            width, height = attachment.get("width"), attachment.get("height")
            data_list.append((
                discord_api.snowflake_to_datetime(attachment_id),
                discord_api.user_display(author),
                _channel_label(scan, channel_id),
                filename,
                reference,
                attachment.get("size", ""),
                attachment.get("content_type", ""),
                f"{width}x{height}" if width and height else "",
                "Yes" if reference else "No",
                sent,
                (message.get("content") or "")[:200],
                str(author.get("id") or ""),
                channel_id,
                attachment_id,
                message_id,
                attachment.get("url", ""),
                context.get_relative_path(found[0]) if found else "",
            ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime)
                   else datetime.min.replace(tzinfo=timezone.utc))
    recovered = sum(1 for row in data_list if row[4])
    logfunc(f"Discord Attachments: {len(data_list)} attachment(s), "
            f"{recovered} recovered from the cache.")
    source = "\n".join(sorted({wrapper["source"] for wrapper in scan.messages.values()})[:50])
    return data_headers, data_list, source
