__artifacts_v2__ = {
    "discordSearches": {
        "name": "Discord Searches",
        "description": "Search requests found in the Discord client's cache: message searches in a channel or "
                       "server, with their terms, filters and result counts, and GIF searches. The search term "
                       "is part of the request URL, so it survives in the cached entry's key.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. A message search is a cached response to channels/<id>/messages/search or "
                 "guilds/<id>/messages/search: Search Terms is its content parameter, Filters lists the "
                 "filter parameters Discord documents for message search "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/message.mdx#L957-L972) "
                 "other than content, Scope is channel or guild with the ID, and Total Results is the "
                 "response's total_results, which Discord says may not be accurate while messages are "
                 "being created or deleted "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/message.mdx#L944). "
                 "Discord's search can run on filters alone: 3 message searches on discord_macos had "
                 "filters and no terms, and they appear with an empty Search Terms. Hits In Response "
                 "counts the messages the response marked as hits. Those messages are also reported by "
                 "Discord Messages, so a message found by a search can be recovered even when no cached "
                 "response to its channel's messages holds it. A GIF search is a request to gifs/search, "
                 "with its q parameter as Search Terms and its provider parameter as Scope; it carries no "
                 "result count. A request with neither terms nor filters is not listed, which leaves out "
                 "every request to gifs/trending: discord_macos held 3.",
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
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 215 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 1 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "discordReactions": {
        "name": "Discord Reactions",
        "description": "Accounts listed as having reacted to a Discord message with an emoji, from cached "
                       "responses to Discord's reaction listing endpoint. Rows exist only for messages whose "
                       "reactions the client requested.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the same cache as Discord Cache Records, whose notes describe its formats and "
                 "times. Each row is one user in a cached response to "
                 "channels/<channel>/messages/<message>/reactions/<emoji>, which Discord documents as "
                 "listing the users that reacted with that emoji "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/message.mdx#L1144); "
                 "Emoji is the URL-decoded emoji from the request URL. A response lists at most the number "
                 "of users its limit parameter asked for, which Discord documents as 1 to 100 with a "
                 "default of 25 "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/resources/message.mdx#L1154): "
                 "255 of the 264 listing requests on discord_macos asked for 3 and 9 asked for 100, so a "
                 "message can have more reacting accounts than are listed. Message Sent is the timestamp "
                 "in the message ID from the request URL, read with the layout Discord documents "
                 "(https://github.com/discord/discord-api-docs/blob/ce076f016923cc841774dc51d95bde0eb25c4dcb/developers/reference.mdx#L156), "
                 "so it is filled when the message itself was not recovered; Message is the recovered "
                 "message's first 200 characters and is empty when it was not.",
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
        "artifact_icon": "smile",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 335 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 3 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
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
