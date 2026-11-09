__artifacts_v2__ = {
    "chromiumCacheRecords": {
        "name": "Chromium Cache Records",
        "description": "Entries of the HTTP disk cache of Google Chrome, Microsoft Edge, Brave, Vivaldi and "
                       "Chromium profiles on Windows: cached URL, HTTP status, content type, body size, the "
                       "entry's created and last used times, the request and response times, and the cached "
                       "picture, video or audio.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-09",
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
                 "before it, both as stored; 236 tested keys began with Range_, the key Chromium gives a child entry holding up to one MiB of a "
                 "sparse entry's data, Range_<parent key>:<signature>:<child number>, both numbers in "
                 "hexadecimal "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/disk_cache/blockfile/sparse_control.cc#L54-L65 and #L538-L541), and a key that names no resource URL, such as a quicserverinfo entry, is kept "
                 "whole in Key Prefix with URL blank. Host is the URL's host. Cached Media is the body of an "
                 "image, video or audio entry, with its Content-Encoding (gzip, deflate, br, and zstd on "
                 "Python 3.14 or with the zstandard package) undone; Chromium also zstd-compresses some bodies "
                 "on disk, marked by extra flag bit 4 "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/net/http/http_response_info.cc#L140-L157), "
                 "which is undone first, a branch no tested entry exercised (exercised on a constructed body "
                 "only). A body whose data is not in the cache files is absent, and a body that does not "
                 "decode is shown as stored. A picture, video or audio entry stored as a "
                 "sparse entry, whose data is in Range_ children, is shown when its children hold all of it, read "
                 "as the notes of Chromium Media Cache Records describe: 35 of the 41 such entries on the tested "
                 "images (1 of 1 on hexordia_mvs2025_win11, 16 of 22 on ou_ransomware_server2022, 18 of 18 on "
                 "pc_mus_001_win11); its Body Size (bytes) stays 0 as stored. Each of the 35 decodes in ffmpeg "
                 "with no error, and each of the 31 among them that begins as an MP4 or WebM container (23 by "
                 "Content Type, plus 8 labelled audio/mpeg) ends exactly where its top-level boxes or its EBML "
                 "Segment say it does. Every image, video and audio entry with a stored body, or a sparse body held whole, "
                 "on the tested images was shown: 14,257 rows, 13,992 of them images. Browser, Profile and User come "
                 "from the path, as in the other Chromium artifacts, and separate every cache folder on the "
                 "tested images; the folder's index file is in the source list of the report. Tested: "
                 "windows11_arm_chromium_cache_known_20261103 (Chrome 157.0.8103.39 and Edge 156.0.4314.58, 14 "
                 "rows), cfreds_leakage_win7 (2,345), hexordia_mvs2025_win11 (5,273), lonewolf_win10 (Chrome "
                 "65.0.3325.181, 12,962), ou_ransomware_server2022 (2,893) and pc_mus_001_win11 (Chrome "
                 "108.0.5359.125 and Edge 108.0.1462.54, 18,673); on pc_mus_001_win11 the Guest Profile and "
                 "System Profile caches held no entry. Isolation Key had no value on any row of "
                 "cfreds_leakage_win7 or lonewolf_win10, whose keys are not split by site. Not read: the "
                 "server IP address, certificate and other fields stored after the headers in the response "
                 "info; the Media Cache and Application Cache folders of the older tested builds, which "
                 "Chromium Media Cache Records and Chromium Application Cache read; GPUCache and Code Cache; "
                 "No_Vary_Search; the simple cache format (one file per "
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
    "chromiumMediaCacheRecords": {
        "name": "Chromium Media Cache Records",
        "description": "Entries of the separate HTTP disk cache older Google Chrome and Chromium builds kept "
                       "for media requests, in a profile's Media Cache folder on Windows: cached URL, HTTP "
                       "status, content type, body size, the entry's created and last used times, the "
                       "request and response times, and the cached picture, video or audio, put back together "
                       "from the pieces the cache stores it in when no piece is missing.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-09",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Media Cache folder of a Chromium-based browser profile on Windows with the same reader, and gives the same columns read the same way, as Chromium Cache Records, whose notes give the sources for each column. Chrome 65 keeps this folder as a separate HTTP disk cache for the profile's media requests (https://github.com/chromium/chromium/blob/65.0.3325.181/chrome/browser/profiles/profile_impl_io_data.cc#L494-L497 and #L637-L656, https://github.com/chromium/chromium/blob/65.0.3325.181/chrome/common/chrome_constants.cc#L155); Chromium's chrome_constants.cc at d5e871096c2c285b2f93f7922b69c2edce5b1de1 names no Media Cache folder. Most entries are the child entries Chromium writes for a sparse entry, whose key is Range_<parent key>:<signature>:<child number>, both numbers in hexadecimal, and each of which holds up to one MiB of the parent's data from offset child number times one MiB (https://github.com/chromium/chromium/blob/65.0.3325.181/net/disk_cache/blockfile/sparse_control.cc#L49-L59 and #L518-L521): 222 of 323 rows on lonewolf_win10 (children of 86 parent entries) and 6 of 8 on cfreds_leakage_win7 (children of 2), and on both every child's parent key is an entry of the same cache. A child row holds no response info, so its Response Time, Request Time, HTTP Status and Content Type are blank, Key Prefix holds Range_, URL holds the rest of the child key (the parent key, then its signature and child number) and Host the host of the parent's URL; its Body Size (bytes) is the size of its own data. The parent row carries the response info and a Body Size (bytes) of 0, since its data is in its children. For a picture, video or audio parent, Cached Media is its data put back together from its children as SparseControl reads them: only children whose own header carries the parent's signature and kIndexMagic, and in each only the 1 KiB blocks its bitmap marks and the part-filled block its header records (https://github.com/chromium/chromium/blob/65.0.3325.181/net/disk_cache/blockfile/sparse_control.cc#L476-L501, #L586-L619 and #L659-L665, https://github.com/chromium/chromium/blob/65.0.3325.181/net/disk_cache/blockfile/disk_format_base.h#L99-L126). It is shown only when those blocks hold every byte from 0 to the parent's stored Content-Length, which Chromium sets to the size of the whole resource when it stores the response and reads back as that size (https://github.com/chromium/chromium/blob/65.0.3325.181/net/http/http_cache_transaction.cc#L1871-L1873, https://github.com/chromium/chromium/blob/65.0.3325.181/net/http/partial_data.cc#L225-L229 and #L360-L363); Body Size (bytes) stays 0 as stored. 85 of the 87 picture, video or audio entries on lonewolf_win10 and both on cfreds_leakage_win7 are sparse parents, and the other two are redirects with no body. 63 of the 85 and both of the 2 were put back together; the children of the other 22 leave a gap (on two, the last child holds 91 and 781 bytes past the blocks its bitmap marks, which are not read; the other 20 are missing whole children). Each of the 65 decodes in ffmpeg with no error, and each of the 61 MP4 and WebM files among them ends exactly where its top-level boxes or its EBML Segment say it does. Reuse Count held 0 and Isolation Key no value on every row of both images, whose keys are not split by site; Host held one value on all 8 rows of cfreds_leakage_win7, and Browser, Profile and User one value on every row of both, which each hold one profile with a Media Cache. Tested: lonewolf_win10 (Chrome 65.0.3325.181, 323 rows) and cfreds_leakage_win7 (8 rows); no other Windows image in the corpus listings holds a Media Cache folder. Not read: the GPUCache folder, Chromium's shader cache (https://github.com/chromium/chromium/blob/65.0.3325.181/gpu/ipc/host/shader_disk_cache.cc#L562), whose entries are not keyed by URL, and the Application Cache, read by Chromium Application Cache.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Media Cache/*',
            '*/AppData/Local/Chromium/User Data/*/Media Cache/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Media Cache/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Media Cache/*',
            '*/AppData/Local/Vivaldi/User Data/*/Media Cache/*',
        ),
        "output_types": "standard",
        "artifact_icon": "film",
        "sample_data": {
            "lonewolf_win10": "Windows 10 Education build 16299, Google Chrome 65.0.3325.181 | 323 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Chrome | 8 rows",
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


def _sparse_media(entry, children, status, headers):
    """A sparse entry's data put back together from its children, or None.

    Chromium stores a 206 response as a sparse entry (net/http/partial_data.cc#L393-L395)
    and replaces its Content-Length with the size of the whole resource, which it reads
    back as that size
    (https://github.com/chromium/chromium/blob/65.0.3325.181/net/http/http_cache_transaction.cc#L1871-L1873,
    net/http/partial_data.cc#L225-L229 and #L360-L363, all at the same tag).
    """
    if status != '206' or entry.sparse_size <= 0:
        return None
    length = headers.get('content-length', '').strip()
    if not length.isdigit():
        return None
    return blockfile_cache.sparse_body(entry, children, int(length))


def _media(entry, folder, content_type, headers, extra_flags, status, children):
    """The checked-in body of a picture, video or audio entry, or ''."""
    if not content_type.startswith(_MEDIA_TYPES):
        return ''
    if entry.body_size > 0:
        raw = entry.read_body()
    else:
        raw = _sparse_media(entry, children, status, headers)
        if raw is None:
            return ''
    body = stored_body(raw, extra_flags,
                       headers.get('content-encoding', '').strip().lower())
    if not body:
        return ''
    extension = content_type.split('/', 1)[1].split('+')[0] or None
    return check_in_embedded_media(entry.body_source or folder, body,
                                   force_type=content_type, force_extension=extension) or ''


def _cache_records(context, folder_names, label):
    data_list = []
    sources = []
    for folder_name in folder_names:
        for store in profile_folders(context, folder_name, label):
            index = os.path.join(store.path, 'index')
            if not os.path.isfile(index):
                continue
            files = [os.path.join(store.path, name) for name in sorted(os.listdir(store.path))]
            rows = 0
            entries = list(blockfile_cache.iter_entries(files, folder_names=(os.path.basename(store.path),)))
            children = blockfile_cache.sparse_children(entries)
            for entry in entries:
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
                                  _media(entry, store.path, content_type, headers, extra_flags, status, children),
                                  entry.reuse_count,
                                  isolation, prefix, store.browser, store.profile, store.user))
                rows += 1
            if rows:
                sources.append(index)
            else:
                logfunc(f'{label}: {store.relative} has no blockfile index with entries')
    return _HEADERS, data_list, '\n'.join(sources)


_HEADERS = (('Last Used', 'datetime'), ('Created', 'datetime'), ('Response Time', 'datetime'),
            ('Request Time', 'datetime'), 'URL', 'Host', 'HTTP Status', 'Content Type',
            'Body Size (bytes)', ('Cached Media', 'media'), 'Reuse Count', 'Isolation Key',
            'Key Prefix', 'Browser', 'Profile', 'User')


@artifact_processor
def chromiumCacheRecords(context):
    return _cache_records(context, _CACHE_FOLDERS, 'Chromium Cache Records')


@artifact_processor
def chromiumMediaCacheRecords(context):
    return _cache_records(context, ('Media Cache',), 'Chromium Media Cache Records')
