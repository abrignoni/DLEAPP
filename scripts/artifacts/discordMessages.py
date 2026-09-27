__artifacts_v2__ = {
    "discordMessages": {
        "name": "Discord Messages",
        "description": "Chat messages recovered from JSON responses to Discord's REST API held in the client's "
                       "Chromium cache: responses listing a channel's messages and message search results. A "
                       "cached response holds what the API returned when it was received, so a later edit or "
                       "deletion is not reflected unless the client fetched the same URL again. A cached copy of "
                       "an attachment is embedded against its message.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. It parses cached responses to api/v<N>/channels/<id>/messages and to "
                 "channels/<id>/messages/search or guilds/<id>/messages/search. Where several cached "
                 "responses hold the same message, the copy with the latest Cached time is reported. "
                 "Timestamp is the message's timestamp field, or the timestamp in the message ID where "
                 "that field is absent; Edited is its edited_timestamp, and Cached is the Cached time of "
                 "the response the message was read from. Direction is resolved against the account IDs "
                 "found in the Sentry scope and Local Storage (see Discord Users Seen), so it is only "
                 "resolvable when one was found; where none was, Direction is empty on every row rather "
                 "than defaulted. Message Type names the type with the names Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/message.mdx#L82-L120); "
                 "a number missing from that list is shown as Type and the number, as for the one message "
                 "of type 47 on discord_macos. Reply To gives the replied-to message's author and first "
                 "120 characters where the response included that message, and otherwise its message ID. "
                 "The Attachments and Attachment Names columns list at most ten attachments per message; "
                 "no message on discord_macos declared more than ten, and the Discord Attachments artifact "
                 "lists every declared attachment. Source Cache File names the file the response body was "
                 "read from: the entry's *_0 file in a simple cache, or the data_N or f_ file holding the "
                 "body in a blockfile cache. Chromium removes cache entries once the cache grows past its "
                 "size limit (see Discord Cache Records), so a message missing here may still have been "
                 "sent.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Cache/index',
            '*/discord*/Cache/data_*',
            '*/discord*/Cache/f_*',
            '*/discord*/Cache/Cache_Data/index',
            '*/discord*/Cache/Cache_Data/data_*',
            '*/discord*/Cache/Cache_Data/f_*',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "message-circle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 12940 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 164 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
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
        "description": "Attachments declared on recovered Discord messages: file name, declared size and type, "
                       "the posting account and the channel, with the cached copy of the file embedded where the "
                       "cache holds one under the attachment's ID.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "One row per attachment declared by a message that Discord Messages recovers. Uploaded is "
                 "the timestamp in the attachment ID, read with the layout Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156); "
                 "on discord_macos it fell between 5.4 seconds before and 0.2 seconds after the timestamp "
                 "of the message declaring the attachment, for all 1,022 attachments. Declared Size "
                 "(bytes), Content Type and Dimensions are the size, content_type, width and height the "
                 "message declared. Recovered File embeds the largest cached copy under the attachment's "
                 "ID and Cached Copy says whether one was recovered; a copy can be in another format than "
                 "the one declared (see Discord Recovered Media). Source Cache File names the file that "
                 "copy's body was read from, and Message is the first 200 characters of the message text. "
                 "A missing copy does not show that the file was never shared.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Cache/index',
            '*/discord*/Cache/data_*',
            '*/discord*/Cache/f_*',
            '*/discord*/Cache/Cache_Data/index',
            '*/discord*/Cache/Cache_Data/data_*',
            '*/discord*/Cache/Cache_Data/f_*',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "paperclip",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 1022 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 12 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

# Attachments embedded per message row are capped. Ten is an observed cap, not
# a limit Discord documents, so a message carrying more would be truncated here.
# The Discord Attachments artifact reports every attachment without a cap.
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
    entry = discord_api.cached_entry(path)
    if entry is None:
        return None
    body = entry.decoded_body()
    if not body:
        return None
    extension = os.path.splitext(filename)[1].lstrip(".")
    content_type = media.get("content_type", "").split(";")[0].strip()
    # The served type is frequently WebP rather than the uploaded type; trust
    # the served type over the name.
    if content_type.startswith("image/") or content_type.startswith("video/"):
        extension = content_type.split("/")[-1]
    return check_in_embedded_media(
        media.get("source", path), body, filename or f"{media['owner_id']}.{extension or 'bin'}",
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
        ("Timestamp", "datetime"),
        ("Edited", "datetime"),
        ("Cached", "datetime"),
        "Direction",
        "Sender",
        "Channel",
        "Message",
        ("Attachments", "media"),
        "Attachment Names",
        "Reply To",
        "Mentions",
        "Embeds",
        "Stickers",
        "Message Type",
        "Pinned",
        "Sender ID",
        "Channel ID",
        "Message ID",
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

        # Direction is only resolvable against the signed-in account id. When
        # find_local_account resolved nothing, local_ids is empty and every
        # message would otherwise be labelled "Received", so the column is left
        # empty rather than asserting a direction the data does not support.
        if not local_ids:
            direction = ""
        elif author_id and author_id in local_ids:
            direction = "Sent"
        else:
            direction = "Received"

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
            discord_api.iso_to_datetime(message.get("edited_timestamp")),
            wrapper["cached"],
            direction,
            discord_api.user_display(author),
            _channel_label(scan, str(message.get("channel_id") or "")),
            message.get("content") or "",
            media_refs,
            ", ".join(n for n in names if n),
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
                context.get_relative_path(found[1].get("source", found[0])) if found else "",
            ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime)
                   else datetime.min.replace(tzinfo=timezone.utc))
    recovered = sum(1 for row in data_list if row[4])
    logfunc(f"Discord Attachments: {len(data_list)} attachment(s), "
            f"{recovered} recovered from the cache.")
    source = "\n".join(sorted({wrapper["source"] for wrapper in scan.messages.values()})[:50])
    return data_headers, data_list, source
