__artifacts_v2__ = {
    "discordSearches": {
        "name": "Discord Searches",
        "description": "Searches issued from the Discord client. The search "
                       "term is part of the request URL, so it survives in the "
                       "cache key itself, and the cached response shows how "
                       "many results came back. The terms are those submitted "
                       "to Discord's own search from this installation. Covers "
                       "in-channel and server-wide message searches as well as "
                       "GIF picker searches.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-07-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Message search hits are also folded into the Discord Messages "
                 "artifact, which means a searched-for message can be recovered "
                 "even when the channel's own message responses are gone. "
                 "Discord can search on filters alone, with no typed term; "
                 "those appear with an empty Search Terms and the filter shown "
                 "in the Filters column.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 215 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 1 rows",
        },
    },
    "discordReactions": {
        "name": "Discord Reactions",
        "description": "Users who reacted to a message with a given emoji, from "
                       "cached reaction listings. Each row places a named "
                       "account on a specific message in a specific channel, so "
                       "it records which accounts Discord reported as having "
                       "reacted to that message. Rows exist only where a "
                       "reactions listing response was cached, so coverage is "
                       "limited to messages for which the client requested one.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "The listing is capped by the limit Discord requested, so a "
                 "heavily reacted message may show only the first few accounts. "
                 "Message Sent is derived from the message snowflake in the "
                 "request URL and is available even when the message itself was "
                 "not recovered.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "smile",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 335 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 3 rows",
        },
    },
}

from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.ilapfuncs import artifact_processor, logfunc

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)


def _channel_label(scan, channel_id):
    channel = scan.channels.get(channel_id) or {}
    if channel.get("name"):
        return f"#{channel['name']}"
    return channel.get("recipients") or channel_id or ""


@artifact_processor
def discordSearches(context):
    data_headers = (
        ("Requested", "datetime"), "Search Type", "Search Terms", "Filters",
        "Scope", "Total Results", "Hits In Response", ("Cached", "datetime"),
        "Request URL", "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.searches:
        return data_headers, [], ""

    data_list = []
    for search in scan.searches:
        filters = search.get("filters", "")
        if not search["terms"] and not filters:
            continue
        data_list.append((
            search["requested"],
            search["type"],
            search["terms"],
            filters,
            search["scope"],
            search["results"] if search["results"] is not None else "",
            len(search["hits"]) or "",
            search["cached"],
            search["url"],
            context.get_relative_path(search["source"]),
        ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Discord Searches: {len(data_list)} search(es) recovered.")
    return data_headers, data_list, "\n".join(
        sorted({s["source"] for s in scan.searches})[:50])


@artifact_processor
def discordReactions(context):
    data_headers = (
        ("Message Sent", "datetime"), "Emoji", "Reacting User", "Channel",
        "Message", "User ID", "Message ID", "Channel ID",
        ("Cached", "datetime"), "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.reactions:
        return data_headers, [], ""

    data_list = []
    for reaction in scan.reactions:
        message_wrapper = scan.messages.get(reaction["message_id"])
        message_text = ""
        if message_wrapper:
            message_text = (message_wrapper["message"].get("content") or "")[:200]
        data_list.append((
            discord_api.snowflake_to_datetime(reaction["message_id"]),
            reaction["emoji"],
            discord_api.user_display(reaction["user"]),
            _channel_label(scan, reaction["channel_id"]),
            message_text,
            str((reaction["user"] or {}).get("id") or ""),
            reaction["message_id"],
            reaction["channel_id"],
            reaction["cached"],
            context.get_relative_path(reaction["source"]),
        ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Discord Reactions: {len(data_list)} reaction(s) recovered.")
    return data_headers, data_list, "\n".join(
        sorted({r["source"] for r in scan.reactions})[:50])
