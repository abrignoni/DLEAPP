__artifacts_v2__ = {
    "discordUsers": {
        "name": "Discord Users Seen",
        "description": "Every Discord account observed anywhere in the cached "
                       "application data: message authors, mentioned users, "
                       "direct message recipients, people who reacted to a "
                       "message, invite creators and viewed profiles. User IDs "
                       "are snowflakes, so each account's registration date is "
                       "recoverable, and a cached avatar is embedded where one "
                       "survives.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "First and last seen reflect the cached evidence, not the "
                 "account's real activity window. Profile fields (bio, pronouns, "
                 "connected accounts) are only present for profiles the user "
                 "actually opened in the client.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/sentry/scope_v3.json',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
    },
    "discordChannels": {
        "name": "Discord Channels",
        "description": "Channels, direct messages and group chats referenced by "
                       "the cached data, with the number of messages recovered "
                       "for each and the span those messages cover. Channel IDs "
                       "are snowflakes, so the channel creation date is "
                       "recoverable even for a channel only seen once in a URL.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "Channel names and topics are only known where the client "
                 "cached a channel object or a search response describing them; "
                 "otherwise only the ID is reported. The server a channel "
                 "belongs to is resolved from cached channel objects, the "
                 "renderer log's routing entries and the Local Storage channel "
                 "selection state.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/logs/renderer_js*.log',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hash",
    },
    "discordGuilds": {
        "name": "Discord Servers",
        "description": "Discord servers (guilds) the client encountered, built "
                       "from cached server profiles, invite lookups, the server "
                       "IDs attached to cached channels and the servers the "
                       "renderer log shows the user navigating to. Server IDs "
                       "are snowflakes, so the server's creation date is "
                       "recoverable even when only the ID survives.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "A server appearing here means the client saw it, which "
                 "includes servers reached through an invite link without ever "
                 "joining. Member counts are the approximate values Discord "
                 "returned at the time the response was cached.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/logs/renderer_js*.log',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "server",
    },
    "discordInvites": {
        "name": "Discord Invites",
        "description": "Server invite links the client looked up. Discord "
                       "resolves an invite code through the API before showing "
                       "the join prompt, and that response names the server, the "
                       "channel the invite points at, who created it and when it "
                       "expires.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (Desktop)",
        "notes": "An invite appearing here shows the link was opened or "
                 "previewed in the client. It does not establish that the user "
                 "joined the server.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "link",
    },
}

import json
import os
import re
from datetime import datetime

from scripts.chromium import discord_api
from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.chromium.simple_cache import read_entry
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

_ROUTE_RE = re.compile(r"Transitioning to /channels/(\d+)/(\d+)")


def _channel_to_server(scan, files_found):
    """Map channel id -> server id, from every source that records the pairing.

    Cached channel objects carry a guild_id, but most channels are only ever
    seen as an ID in a message. The renderer log's routing entries and the
    Local Storage channel selection state both pair a channel with its server,
    which fills in almost everything the user actually visited.
    """
    mapping = {}
    for channel_id, channel in scan.channels.items():
        if channel.get("guild_id"):
            mapping[channel_id] = str(channel["guild_id"])

    for file_found in files_found:
        file_found = str(file_found)
        if "renderer_js" not in os.path.basename(file_found):
            continue
        try:
            with open(file_found, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    match = _ROUTE_RE.search(line)
                    if match:
                        mapping.setdefault(match.group(2), match.group(1))
        except OSError:
            continue

    for folder in leveldb_folders(files_found):
        try:
            records = list(read_records(folder))
        except Exception:
            continue
        for record in records:
            if record.key != "SelectedChannelStore":
                continue
            try:
                state = json.loads(record.value)
            except (ValueError, TypeError):
                continue
            for field in ("selectedChannelIds", "mostRecentSelectedTextChannelIds"):
                for guild_id, channel_id in (state.get(field) or {}).items():
                    if guild_id and guild_id != "null" and channel_id:
                        mapping.setdefault(str(channel_id), str(guild_id))
    return mapping


def _best_avatars(scan):
    """Map user id -> the largest cached avatar for that user."""
    best = {}
    for path, media in scan.media.items():
        if media["kind"] not in ("Avatar", "Guild Avatar") or not media["owner_id"]:
            continue
        current = best.get(media["owner_id"])
        if current is None or media["size"] > current[1]["size"]:
            best[media["owner_id"]] = (path, media)
    return best


def _avatar_reference(avatars, user_id):
    """Embed the largest cached avatar for a user, if one is cached."""
    best = avatars.get(user_id)
    if best is None:
        return None
    entry = read_entry(best[0])
    if entry is None:
        return None
    body = entry.decoded_body()
    if not body:
        return None
    content_type = (best[1].get("content_type") or "").split(";")[0].strip()
    return check_in_embedded_media(
        best[0], body, f"avatar_{user_id}",
        force_type=content_type or None,
        force_extension=content_type.split("/")[-1] if "/" in content_type else None)


@artifact_processor
def discordUsers(context):
    data_headers = (
        "Username", "Display Name", ("Avatar", "media"), "User ID",
        ("Account Created", "datetime"), "Bot", "Private Note", "Pronouns",
        "Bio", "Legacy Username", "Connected Accounts", "Mutual Servers",
        "Seen As", ("First Seen (Cached)", "datetime"),
        ("Last Seen (Cached)", "datetime"), "Profile Cached",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.users:
        return data_headers, [], ""

    account = discord_api.find_local_account(files_found)
    local_ids = account["ids"]
    avatars = _best_avatars(scan)
    # Private notes the local user wrote about another account.
    notes = {note["user_id"]: note["note"] for note in scan.notes}

    data_list = []
    for user_id, user in scan.users.items():
        profile = (scan.profiles.get(user_id) or {}).get("profile") or {}
        profile_user = profile.get("user") or {}
        user_profile = profile.get("user_profile") or {}
        connections = ", ".join(
            f"{c.get('type')}:{c.get('name')}" for c in (profile.get("connected_accounts") or [])
            if isinstance(c, dict))
        mutual = ", ".join(
            (scan.guilds.get(str(g.get("id")), {}).get("name") or str(g.get("id", "")))
            for g in (profile.get("mutual_guilds") or []) if isinstance(g, dict))

        username = user["username"] or profile_user.get("username", "")
        if user_id in local_ids:
            username = f"{username} (local account)" if username else "(local account)"

        data_list.append((
            username,
            user["global_name"] or profile_user.get("global_name", ""),
            _avatar_reference(avatars, user_id),
            user_id,
            discord_api.snowflake_to_datetime(user_id),
            "Yes" if user["bot"] else "",
            notes.get(user_id, ""),
            user_profile.get("pronouns", ""),
            (profile_user.get("bio") or user_profile.get("bio") or "").strip(),
            profile.get("legacy_username", ""),
            connections,
            mutual,
            ", ".join(sorted(user["seen_in"])),
            user["first_seen"],
            user["last_seen"],
            "Yes" if profile else "",
        ))

    data_list.sort(key=lambda row: (row[0] or "").lower())
    logfunc(f"Discord Users Seen: {len(data_list)} account(s), "
            f"{len(scan.profiles)} with a cached profile.")
    return data_headers, data_list, "\n".join(sorted(scan.source_paths)[:50])


@artifact_processor
def discordChannels(context):
    data_headers = (
        "Channel", "Server", "Type", "Messages Recovered",
        ("First Message", "datetime"), ("Last Message", "datetime"),
        "Participants", "Topic", "Channel ID", "Server ID",
        ("Channel Created", "datetime"), "Parent Channel ID",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.channels:
        return data_headers, [], ""

    servers = _channel_to_server(scan, files_found)
    counts = {}
    spans = {}
    for wrapper in scan.messages.values():
        message = wrapper["message"]
        channel_id = str(message.get("channel_id") or "")
        if not channel_id:
            continue
        counts[channel_id] = counts.get(channel_id, 0) + 1
        sent = discord_api.iso_to_datetime(message.get("timestamp")) \
            or discord_api.snowflake_to_datetime(message.get("id"))
        if isinstance(sent, datetime):
            first, last = spans.get(channel_id, (sent, sent))
            spans[channel_id] = (min(first, sent), max(last, sent))

    data_list = []
    for channel_id, channel in scan.channels.items():
        first, last = spans.get(channel_id, ("", ""))
        name = channel["name"]
        if name:
            name = f"#{name}"
        elif channel["recipients"]:
            name = channel["recipients"]
        guild_id = channel["guild_id"] or servers.get(channel_id, "")
        guild = scan.guilds.get(guild_id) or {}
        data_list.append((
            name or channel_id,
            guild.get("name") or guild_id,
            discord_api.channel_type_name(channel["type"]),
            counts.get(channel_id, 0),
            first,
            last,
            channel["recipients"],
            channel["topic"] or "",
            channel_id,
            guild_id,
            discord_api.snowflake_to_datetime(channel_id),
            channel["parent_id"],
        ))

    data_list.sort(key=lambda row: (-row[3], (row[0] or "").lower()))
    logfunc(f"Discord Channels: {len(data_list)} channel(s) referenced.")
    return data_headers, data_list, "\n".join(sorted(scan.source_paths)[:50])


@artifact_processor
def discordGuilds(context):
    data_headers = (
        "Server", "Description", "Members (approx.)", "Channels Seen",
        "Messages Recovered", ("Server Created", "datetime"), "Server ID",
        "Vanity URL", "Features", "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.guilds:
        return data_headers, [], ""

    channel_to_guild = _channel_to_server(scan, files_found)
    channel_counts = {}
    message_counts = {}
    for guild_id in channel_to_guild.values():
        channel_counts[guild_id] = channel_counts.get(guild_id, 0) + 1
    for wrapper in scan.messages.values():
        guild_id = channel_to_guild.get(str(wrapper["message"].get("channel_id") or ""))
        if guild_id:
            message_counts[guild_id] = message_counts.get(guild_id, 0) + 1

    # Servers only ever seen as an ID in a route or channel mapping still count.
    known = dict(scan.guilds)
    for guild_id in channel_to_guild.values():
        known.setdefault(guild_id, {
            "id": guild_id, "name": "", "description": "", "member_count": None,
            "features": "", "vanity_url": "", "icon": "",
            "source": "channel and navigation references",
        })

    data_list = []
    for guild_id, guild in known.items():
        data_list.append((
            guild["name"] or guild_id,
            guild["description"] or "",
            guild["member_count"] if guild["member_count"] is not None else "",
            channel_counts.get(guild_id, 0),
            message_counts.get(guild_id, 0),
            discord_api.snowflake_to_datetime(guild_id),
            guild_id,
            guild["vanity_url"],
            guild["features"],
            context.get_relative_path(guild["source"]),
        ))

    data_list.sort(key=lambda row: (row[0] or "").lower())
    logfunc(f"Discord Servers: {len(data_list)} server(s) referenced.")
    return data_headers, data_list, "\n".join(sorted(scan.source_paths)[:50])


@artifact_processor
def discordInvites(context):
    data_headers = (
        ("Looked Up", "datetime"), "Invite Code", "Server", "Target Channel",
        "Created By", "Members (approx.)", "Online (approx.)",
        ("Invite Expires", "datetime"), "Server ID", "Channel ID",
        "Inviter ID", "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.invites:
        return data_headers, [], ""

    data_list = []
    seen = set()
    for record in scan.invites:
        invite = record["invite"]
        code = invite.get("code", "")
        if code in seen:
            continue
        seen.add(code)
        guild = invite.get("guild") or {}
        channel = invite.get("channel") or {}
        inviter = invite.get("inviter") or {}
        channel_name = channel.get("name") or ""
        data_list.append((
            record["cached"],
            code,
            guild.get("name") or str(guild.get("id") or ""),
            f"#{channel_name}" if channel_name else str(channel.get("id") or ""),
            discord_api.user_display(inviter),
            invite.get("approximate_member_count", ""),
            invite.get("approximate_presence_count", ""),
            discord_api.iso_to_datetime(invite.get("expires_at")),
            str(guild.get("id") or ""),
            str(channel.get("id") or ""),
            str(inviter.get("id") or ""),
            context.get_relative_path(record["source"]),
        ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else datetime.min)
    logfunc(f"Discord Invites: {len(data_list)} invite lookup(s) recovered.")
    return data_headers, data_list, "\n".join(
        sorted({r["source"] for r in scan.invites})[:50])
