__artifacts_v2__ = {
    "discordUsers": {
        "name": "Discord Users Seen",
        "description": "Discord accounts named in the cached API responses this parser reads: message authors, "
                       "mentioned users, direct message recipients, users listed as having reacted, profiles and "
                       "invite creators, with profile details and an avatar where the cache holds them.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. The account IDs found in the Sentry scope's user and in the MultiAccountStore and "
                 "tokens keys of Local Storage are marked by adding (local account) to their Username. "
                 "Seen As lists the responses that named the account: Message author, Mentioned, DM "
                 "channel (a recipient of a direct message channel object), Reacted to message, Profile "
                 "fetched (a cached response to users/<id>/profile) and Invite creator. First Seen "
                 "(Cached) and Last Seen (Cached) are the earliest and latest of the times attached to "
                 "those responses: a message's timestamp for its author and the users it mentions, and the "
                 "Cached time of a reaction listing, profile or invite response; a direct message "
                 "recipient adds no time. They describe what the cache kept, not when the account was "
                 "active. Account Created is the timestamp in the user ID, read with the layout Discord "
                 "documents for its IDs "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156); "
                 "the documentation gives that part of the ID as milliseconds since the first second of "
                 "2015 without naming the event it records. Pronouns, Bio, Legacy Username, Connected "
                 "Accounts (type:name pairs) and Mutual Servers come only from a cached profile response, "
                 "and Profile Cached says whether one was found, so a blank in them means no profile "
                 "response was cached, not that the account had no profile. Avatar embeds the largest "
                 "cached avatar or server avatar image for the account's ID. Bot is Yes when any response "
                 "marked the account as a bot. Private Note comes from a cached response to "
                 "users/@me/notes/<id>, and discord_macos held none, so Private Note was empty on all 590 "
                 "of its rows.",
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
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 590 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 10 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordChannels": {
        "name": "Discord Channels",
        "description": "Channels named in the cached Discord API responses, with the number of recovered "
                       "messages in each and the span of their timestamps.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. A channel is listed when a recovered message names it as its channel, or when a "
                 "cached channel object, message search response or invite response describes it. Messages "
                 "Recovered counts the recovered messages whose channel_id is the channel, and First "
                 "Message and Last Message are the earliest and latest of their timestamps, so they "
                 "describe what the cache kept rather than the conversation. Channel names come from those "
                 "channel descriptions; a direct message channel is named by its recipients where a "
                 "channel object listed them, and a channel with neither is shown by its ID. Type names "
                 "the channel type with the names Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/channel.mdx#L66-L80) "
                 "and is empty when no response gave a type. Server is resolved from the guild_id of a "
                 "channel description, from the renderer log's routing lines (Transitioning to "
                 "/channels/<server>/<channel>), and from the selectedChannelIds and "
                 "mostRecentSelectedTextChannelIds of the SelectedChannelStore key in Local Storage, which "
                 "pair a server with a channel. Channel Created is the timestamp in the channel ID, read "
                 "with the layout Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156); "
                 "the documentation notes that some child objects share their parent's ID "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L143), "
                 "and such a channel carries its parent's time. Topic held no value on any of the 117 rows "
                 "of discord_macos.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Cache/index',
            '*/discord*/Cache/data_*',
            '*/discord*/Cache/f_*',
            '*/discord*/Cache/Cache_Data/index',
            '*/discord*/Cache/Cache_Data/data_*',
            '*/discord*/Cache/Cache_Data/f_*',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/logs/renderer_js*.log',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hash",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 117 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 4 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordGuilds": {
        "name": "Discord Servers",
        "description": "Discord servers named in cached server profiles and invite responses, in the guild_id of "
                       "cached channel descriptions, in the renderer log's routing lines and in the Local "
                       "Storage channel selection state. A row shows the server was named in one of these and "
                       "does not establish membership.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. It also reads the renderer log and the SelectedChannelStore key in Local Storage, "
                 "as the Discord Channels notes describe. Server Created is the timestamp in the server "
                 "ID, read with the layout Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156). "
                 "Members (approx.) is the member_count or approximate_member_count of the first cached "
                 "server profile or invite response read that gave one, as Discord returned it then; "
                 "Discord documents approximate_member_count as an approximate count of total members "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/invite.mdx#L26-L27). "
                 "Channels Seen counts the channels those sources pair with the server, and Messages "
                 "Recovered the recovered messages in those channels. A server named only by a routing "
                 "line or the Local Storage state has no Description, Members, Vanity URL or Features, and "
                 "its Source Cache File reads channel and navigation references, as for 1 of the 2 rows on "
                 "discord_win_ptb.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Cache/index',
            '*/discord*/Cache/data_*',
            '*/discord*/Cache/f_*',
            '*/discord*/Cache/Cache_Data/index',
            '*/discord*/Cache/Cache_Data/data_*',
            '*/discord*/Cache/Cache_Data/f_*',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
            '*/discord*/logs/renderer_js*.log',
            '*/discord*/Local Storage/leveldb/*',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "server",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 25 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 2 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordInvites": {
        "name": "Discord Invites",
        "description": "Invite codes the client looked up, from cached responses to Discord's invites/<code> "
                       "endpoint: the server and channel each invite points to, the account that created it, the "
                       "approximate member and online counts and the expiry Discord returned. A lookup does not "
                       "establish that the server was joined.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. Discord documents invites/<code> as returning the invite object for that code "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/invite.mdx#L171). "
                 "One row per invite code, from its most recent cached lookup: discord_macos held 37 "
                 "lookups of 27 codes. Looked Up is the Cached time of that response. Created By is the "
                 "invite's inviter, which Discord documents as the user who created the invite "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/invite.mdx#L22); "
                 "Members (approx.) and Online (approx.) are approximate_member_count and "
                 "approximate_presence_count, which Discord returns when the request asks with_counts "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/invite.mdx#L26-L27). "
                 "Invite Expires is the expires_at value in that response "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/invite.mdx#L28), "
                 "as Discord reported it at the lookup.",
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
        "artifact_icon": "link",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 27 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 1 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json
import os
import re
from datetime import datetime

from scripts.chromium import discord_api
from scripts.chromium.local_storage import leveldb_folders, read_records
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
        # Deliberately broad: a damaged LevelDB must not stop the mapping.
        except Exception:  # pylint: disable=broad-exception-caught
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
    entry = discord_api.cached_entry(best[0])
    if entry is None:
        return None
    body = entry.decoded_body()
    if not body:
        return None
    content_type = (best[1].get("content_type") or "").split(";")[0].strip()
    return check_in_embedded_media(
        best[1].get("source", best[0]), body, f"avatar_{user_id}",
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


def _later(candidate, current):
    """True when ``candidate`` is a datetime later than ``current``, or ``current`` has none."""
    if not isinstance(candidate, datetime):
        return False
    return not isinstance(current, datetime) or candidate > current


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

    # One row per invite code, from its most recently cached lookup.
    latest = {}
    for record in scan.invites:
        code = record["invite"].get("code", "")
        current = latest.get(code)
        if current is None or _later(record["cached"], current["cached"]):
            latest[code] = record

    data_list = []
    for record in latest.values():
        invite = record["invite"]
        code = invite.get("code", "")
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
