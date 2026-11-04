__artifacts_v2__ = {
    "chromiumCacheRecords": {
        "name": "Chromium Cache Records",
        "description": "Entries of the HTTP disk cache of Google Chrome, Microsoft Edge, Brave, Vivaldi and "
                       "Chromium profiles on Windows: cached URL, HTTP status, content type, body size, the "
                       "entry's created and last used times, the request and response times, and the cached "
                       "picture, video or audio.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "One row per entry of the HTTP disk cache of a Chromium-based browser profile on Windows, "
                 "read from the blockfile cache (an index file with data_0 to data_3 and f_ files) in the "
                 "profile's Cache/Cache_Data folder or, on the older tested builds, its Cache folder. Every "
                 "entry the index reaches through its hash chains is read; an entry whose state is not "
                 "ENTRY_NORMAL (evicted or doomed) is not reported "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/disk_cache/blockfile/disk_format.h#L117-L144). "
                 "Created is the entry's creation_time and Last Used the last_used of its rankings node, "
                 "base::Time values, microseconds since 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/disk_cache/blockfile/disk_format.h#L154-L162). "
                 "Reuse Count is the entry's reuse_count as stored, which disk_format.h describes as how often "
                 "the entry is used. On windows11_arm_chromium_cache_known_20261103, where Chrome 157 and Edge "
                 "156 each loaded three URLs in two rounds, the second round starting 60 seconds after the "
                 "first ended, Created fell 0.01 to 0.14 seconds after each logged first load of those URLs "
                 "began and Last Used 0.007 to 0.018 seconds after each second load began; Reuse Count held 1 "
                 "on the six entries of the logged URLs and on one script entry per browser whose Last Used "
                 "fell 78 seconds after Created, and 0 on the other three entries per browser, whose Last Used "
                 "fell within 0.4 seconds of Created. On no tested row was Last Used earlier than Created. "
                 "Response Time and Request Time are the response_time and request_time of the entry's "
                 "HttpResponseInfo, read as Chromium writes it: a pickle of flags, extra flags when flag bit "
                 "31 is set, the request time, the response time, an original response time when extra flag "
                 "bit 2 is set, then the raw headers "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/http/http_response_info.cc#L168-L209, "
                 "and "
                 "https://github.com/chromium/chromium/blob/65.0.3325.181/net/http/http_response_info.cc#L130-L158 "
                 "for Chrome 65). On the known data Request Time fell 0.01 to 0.24 seconds and Response Time "
                 "0.10 to 0.28 seconds after each first load began, and neither moved after the second load. A "
                 "response info whose version is not 3, the only version Chromium reads "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/http/http_response_info.cc#L48-L51), "
                 "or whose pickle is shorter than its header states, leaves Response Time, Request Time, HTTP "
                 "Status and Content Type blank: 286 of the 42,160 tested entries: 244 held no response info "
                 "(3 of them quicserverinfo entries), 41 were quicserverinfo entries whose stored data is not "
                 "a response info of version 3, and 1 on lonewolf_win10 was 4 bytes shorter than its header "
                 "states. On the other 41,874 the times, status line and headers equal what DLEAPP's other "
                 "cache reader takes from the same bytes. HTTP Status is the code in the stored status line, "
                 "as stored, and Content Type the media type of the content-type header, lower-cased. Body "
                 "Size (bytes) is the size stored for the body stream. URL is the entry key's URL: Chrome 65 "
                 "keys are the URL, preceded by an upload id for an upload "
                 "(https://github.com/chromium/chromium/blob/65.0.3325.181/net/http/http_cache.cc#L570-L583); "
                 "current keys carry a credential and upload id prefix and, when the cache is split by site, "
                 "an isolation key after _dk_, and the URL is the text after the key's rightmost space, as "
                 "Chromium reads it "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/http/http_cache.cc#L783-L893). "
                 "Isolation Key is that isolation key, with its s_ or cn_ marker kept, and Key Prefix the text "
                 "before it, both as stored; 236 tested keys began with Range_, whose writer is not "
                 "established, and a key that names no resource URL, such as a quicserverinfo entry, is kept "
                 "whole in Key Prefix with URL blank. Host is the URL's host. Cached Media is the body of an "
                 "image, video or audio entry, with its Content-Encoding (gzip, deflate, br, and zstd on "
                 "Python 3.14 or with the zstandard package) undone; Chromium also zstd-compresses some bodies "
                 "on disk, marked by extra flag bit 4 "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/http/http_response_info.cc#L140-L157), "
                 "which is undone first, a branch no tested entry exercised (exercised on a constructed body "
                 "only). A body whose data is not in the cache files is absent, and a body that does not "
                 "decode is shown as stored. Every image, video and audio entry with a stored body on the "
                 "tested images was shown: 14,222 rows, 13,992 of them images. Browser, Profile and User come "
                 "from the path, as in the other Chromium artifacts, and separate every cache folder on the "
                 "tested images; the folder's index file is in the source list of the report. Tested: "
                 "windows11_arm_chromium_cache_known_20261103 (Chrome 157.0.8103.39 and Edge 156.0.4314.58, 14 "
                 "rows), cfreds_leakage_win7 (2,345), hexordia_mvs2025_win11 (5,273), lonewolf_win10 (Chrome "
                 "65.0.3325.181, 12,962), ou_ransomware_server2022 (2,893) and pc_mus_001_win11 (Chrome "
                 "108.0.5359.125 and Edge 108.0.1462.54, 18,673); on pc_mus_001_win11 the Guest Profile and "
                 "System Profile caches held no entry. Isolation Key had no value on any row of "
                 "cfreds_leakage_win7 or lonewolf_win10, whose keys are not split by site. Not read: the "
                 "server IP address, certificate and other fields stored after the headers in the response "
                 "info; the Media Cache and Application Cache folders, which the older tested builds kept "
                 "beside Cache GPUCache and Code Cache; No_Vary_Search; the simple cache format (one file per "
                 "entry); Opera, whose folders these paths do not name; and WebView2 or Electron app caches.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Cache/*',
            '*/AppData/Local/Chromium/User Data/*/Cache/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Cache/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Cache/*',
            '*/AppData/Local/Vivaldi/User Data/*/Cache/*',
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "windows11_arm_chromium_cache_known_20261103": "Windows 11 build 26200 (ARM64), Chrome 157.0.8103.39 and Edge 156.0.4314.58 | 14 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2345 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 5273 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 12962 rows",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 2893 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 18673 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from urllib.parse import urlsplit

from scripts.chromium import blockfile_cache
from scripts.chromium.http_cache import parse_response_info, split_key, stored_body
from scripts.chromium.simple_cache import base_time_to_datetime
from scripts.chromium.web_storage import profile_folders
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

# The cache folder inside a profile: Cache_Data inside Cache on the newer tested
# builds, Cache itself on the older ones.
_CACHE_FOLDERS = ('Cache/Cache_Data', 'Cache')
_MEDIA_TYPES = ('image/', 'video/', 'audio/')


def _host(url):
    try:
        return urlsplit(url).hostname or ''
    except ValueError:
        return ''


def _media(entry, folder, content_type, headers, extra_flags):
    """The checked-in body of a picture, video or audio entry, or ''."""
    if not content_type.startswith(_MEDIA_TYPES) or entry.body_size <= 0:
        return ''
    body = stored_body(entry.read_body(), extra_flags,
                       headers.get('content-encoding', '').strip().lower())
    if not body:
        return ''
    extension = content_type.split('/', 1)[1].split('+')[0] or None
    return check_in_embedded_media(entry.body_source or folder, body,
                                   force_type=content_type, force_extension=extension) or ''


@artifact_processor
def chromiumCacheRecords(context):
    label = 'Chromium Cache Records'
    data_list = []
    sources = []
    for folder_name in _CACHE_FOLDERS:
        for store in profile_folders(context, folder_name, label):
            index = os.path.join(store.path, 'index')
            if not os.path.isfile(index):
                continue
            files = [os.path.join(store.path, name) for name in sorted(os.listdir(store.path))]
            rows = 0
            for entry in blockfile_cache.iter_entries(files, folder_names=(os.path.basename(store.path),)):
                prefix, isolation, url = split_key(entry.key)
                parsed = parse_response_info(entry.response_info)
                if parsed is None:
                    request_time = response_time = None
                    status_line, headers, extra_flags = '', {}, 0
                else:
                    request_time, response_time, status_line, headers, extra_flags = parsed
                content_type = headers.get('content-type', '').split(';')[0].strip().lower()
                pieces = status_line.split()
                status = pieces[1] if len(pieces) > 1 and pieces[0].startswith('HTTP/') else ''
                data_list.append((entry.last_used, entry.created, base_time_to_datetime(response_time),
                                  base_time_to_datetime(request_time), url, _host(url), status,
                                  content_type, entry.body_size,
                                  _media(entry, store.path, content_type, headers, extra_flags), entry.reuse_count,
                                  isolation, prefix, store.browser, store.profile, store.user))
                rows += 1
            if rows:
                sources.append(index)
            else:
                logfunc(f'{label}: {store.relative} has no blockfile index with entries')
    data_headers = (('Last Used', 'datetime'), ('Created', 'datetime'), ('Response Time', 'datetime'),
                    ('Request Time', 'datetime'), 'URL', 'Host', 'HTTP Status', 'Content Type',
                    'Body Size (bytes)', ('Cached Media', 'media'), 'Reuse Count', 'Isolation Key',
                    'Key Prefix', 'Browser', 'Profile', 'User')
    return data_headers, data_list, '\n'.join(sources)
