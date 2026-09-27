__artifacts_v2__ = {
    "discordCacheRecords": {
        "name": "Discord Cache Records",
        "description": "Responses held in the Discord client's Chromium HTTP cache, one row per cached response "
                       "with the times Chromium recorded for its request and response, leaving out the client's "
                       "own script, data, style sheet, font, source map and icon files.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Discord (macOS)",
        "notes": "Reads the Discord client's HTTP cache in both of Chromium's formats: the simple cache, "
                 "one *_0 file per entry under Cache/Cache_Data, as in the tested macOS profile, and the "
                 "blockfile cache, an index file with data_N block files and f_ files directly under "
                 "Cache, as in the Discord 1.0.9008 installation on pc_mus_001_win11. It also reads "
                 "Service Worker CacheStorage entries, which use the simple format (2 rows on "
                 "discord_macos). The paths also take a blockfile cache under Cache/Cache_Data; no tested "
                 "image holds one, and that layout is exercised only by constructed caches in the unit "
                 "tests. Each row is one cached response with a URL, apart from responses for files under "
                 "https://discord.com/assets/ or https://discordapp.com/assets/ whose path ends in .js, "
                 ".json, .css, .woff, .woff2, .map, .svg or .ico, which are left out: 28,506 of the 57,589 "
                 "cached responses with a URL on discord_macos and 196 of the 313 on pc_mus_001_win11. "
                 "Requested and Cached are the request_time and response_time Chromium stores with a "
                 "response: the time the request was made and the time the response headers were received, "
                 "both of which become the time of the last validation when Chromium revalidates a cached "
                 "entry "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/net/http/http_response_info.h#L163-L169). "
                 "Chromium removes entries once the cache grows past its size limit "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/net/disk_cache/simple/simple_index.cc#L486-L491 "
                 "for the simple cache and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/net/disk_cache/blockfile/eviction.cc#L112-L129 "
                 "for the blockfile cache), so a URL missing here may still have been fetched. Hosts other "
                 "than discord.com, discordapp.com, discordapp.net and their subdomains appear too: 1,784 "
                 "rows from 26 such hosts on discord_macos, and 95 of the 117 rows on pc_mus_001_win11, "
                 "all from hcaptcha.com and its subdomains. Media Kind names the kind of Discord media the "
                 "URL points to, from the kinds the Discord Recovered Media description lists, and is "
                 "empty for any other URL; it was empty on all 117 rows of pc_mus_001_win11. HTTP Status "
                 "held 200 on all 117 rows of pc_mus_001_win11. Body Size (bytes) is the stored size of "
                 "the response body, before any content encoding is removed. Source Cache File names the "
                 "file holding the entry: its own *_0 file in a simple cache, or in a blockfile cache the "
                 "data_N file whose 256-byte block records the entry "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/net/disk_cache/blockfile/backend_impl.cc#L602), "
                 "which was data_1 on all 117 rows of pc_mus_001_win11, while the response body is kept in "
                 "a data_N block or in an f_ file of its own.",
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
        "artifact_icon": "list",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "discord_macos": "Discord 0.0.402 macOS | 29083 rows",
            "discord_win_ptb": "Discord 0.0.402 Windows PTB layout | 189 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Discord 1.0.9008 | 117 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
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
