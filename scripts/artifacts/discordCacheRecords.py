__artifacts_v2__ = {
    "discordCacheRecords": {
        "name": "Discord Cache Records",
        "description": "Index of the cached responses held in the Discord "
                       "Desktop HTTP cache, excluding versioned application "
                       "bundle assets, with the time the client requested each "
                       "one and the time the response was stored. Discord has no "
                       "browsing history database, so this index is the closest "
                       "equivalent: it shows which API calls, CDN images, "
                       "embedded links and third-party resources the client "
                       "fetched, and when. Hosts outside Discord appear too, "
                       "since the client fetches link previews and embedded "
                       "media from them. The cache evicts over time, so this "
                       "index is a partial record of what the client fetched "
                       "rather than a complete one.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Versioned application bundle assets (js, css, fonts, icons) "
                 "are excluded because they carry no investigative value and "
                 "dominate the cache by volume. Everything else is listed, "
                 "including link previews fetched from sites outside Discord.",
        "paths": (
            '*/discord*/Cache/Cache_Data/*_0',
            '*/discord*/Service Worker/CacheStorage/*/*/*_0',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "list",
        "sample_data": {
            "discord_macos": "Discord 0.0.402 macOS | 29083 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 189 rows",
        },
    },
}

from datetime import datetime, timezone

from scripts.chromium import discord_api
from scripts.ilapfuncs import artifact_processor, logfunc

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)


@artifact_processor
def discordCacheRecords(context):
    data_headers = (
        ("Requested", "datetime"), ("Cached", "datetime"), "Host", "Path",
        "Query", "Media Kind", "HTTP Status", "Content Type",
        "Body Size (bytes)", "URL", "Source Cache File",
    )

    files_found = [str(f) for f in context.get_files_found()]
    scan = discord_api.scan_cache(files_found, log=logfunc)
    if not scan.records:
        return data_headers, [], ""

    data_list = []
    for record in scan.records:
        data_list.append((
            record["requested"],
            record["cached"],
            record["host"],
            record["path"],
            record["query"],
            record["kind"],
            record["status"] if record["status"] is not None else "",
            record["content_type"],
            record["size"],
            record["url"],
            context.get_relative_path(record["source"]),
        ))

    data_list.sort(key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN,
                   reverse=True)
    logfunc(f"Discord Cache Records: {len(data_list)} cached response(s) indexed "
            f"of {scan.entry_count} total cache entries.")
    return data_headers, data_list, "\n".join(
        sorted({r["source"] for r in scan.records})[:50])
