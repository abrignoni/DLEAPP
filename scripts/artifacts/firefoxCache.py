__artifacts_v2__ = {
    "firefoxCache": {
        "name": "Firefox Cache Entries",
        "description": "Entries of Firefox's HTTP disk cache (cache2): cached URL, request method, HTTP status, "
                       "content type, body size, the entry's last fetched, last modified and expiration times "
                       "and fetch count, and the cached picture, video or audio.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Firefox",
        "notes": "One row per entry file in the cache2/entries or cache2/doomed folder of a Firefox profile's local folder: AppData\\Local\\Mozilla\\Firefox\\Profiles\\<profile> on Windows, ~/Library/Caches/Firefox/Profiles/<profile> on macOS and ~/.cache/mozilla/firefox/<profile> (or under XDG_CACHE_HOME) on Linux, the local folder Firefox 159.0.1 uses for a profile (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/toolkit/xre/nsXREDirProvider.cpp#L1122-L1180, #L286-L293, #L1461-L1465 and #L1586-L1658). A profile kept in a folder of its own choosing, outside those, is not matched. The entry is read with Firefox's own layout from netwerk/cache2 at the FIREFOX_159_0_1_RELEASE tag: the response body, then a metadata block whose first word is a hash of the rest of the block, then a trailer (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/cache2/CacheFileMetadata.cpp#L26-L99 and #L1054-L1160); an entry whose hash does not match, which Firefox itself refuses, is not reported. Entries of metadata version 3 and 4 were read on tested data: 587 of version 4 on windows11_arm_firefox_cache2_known_20261108, 506 of version 3 and 525 of version 4 on ubuntu2604_arm64_firefox_xdg_known_20261031, and 3,511 of version 3 on packt_dfc_linux_mint_usb; the hash matched on all 5,129, and one zero-byte entry file on packt_dfc_linux_mint_usb was not read (the run log counts files not read, and why). A version 4 entry can be encrypted at rest when browser.cache.disk.encryption.enabled is set, which is off by default at 159.0.1 (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/modules/libpref/init/StaticPrefList.yaml#L1100-L1108); such an entry cannot be read without the profile's key, is not reported, and is counted in the run log. No tested entry was encrypted. Last Fetched, Last Modified and Expires are the entry header's lastFetched, lastModified and expirationTime, seconds since 1970 UTC, and Fetch Count its fetchCount (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/cache2/nsICacheEntry.idl#L69-L86). Last Fetched is blank when the stored value is 0, on 80 tested rows, all with Fetch Count 0. Expires is blank on 61 tested rows: 22 stored 0xFFFFFFFF, the placeholder for an unset expiration time (#L43), and 39 stored 0, the value Firefox leaves when the response must be revalidated (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/protocol/http/nsHttpChannel.cpp#L5827-L5873). At 159.0.1 Firefox updates the last fetched time and fetch count in memory only, and they reach the file when the metadata is written for another reason (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/cache2/CacheFileMetadata.cpp#L727-L732), so both can be older than the last use. On windows11_arm_firefox_cache2_known_20261108 (Firefox 159.0.1 on Windows 11; a local test page with an image, a script, JSON, a gzip-encoded response and a 302 redirect, each sent with a max-age of 3,600 seconds), the seven test URLs had Last Fetched and Last Modified on the second the test script recorded for the step that loaded them, and the six with a 200 or 302 response had Expires 3,600 seconds later (the 404 for favicon.ico had an expiration time of 0); after the 302 to the test page the test server logged no second request for that page (its request log is kept with the known data), and its row kept Fetch Count 1 and the first load's Last Fetched. URL is the text after the ':' tag of the entry key and Key Prefix the tags before it, as stored: a, marks an anonymous load, O^ the origin attributes such as the partition key, ~ an id (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/cache2/CacheFileUtils.cpp#L58-L124). Request Method is the request-method element, blank on 22 tested rows that had none; HTTP Status is the code in the status line of the response-head element, and Content Type (lower-cased media type) and Content Encoding come from its headers. Body Size (bytes) is the data size in the trailer or, when an alt-data element names alternative data stored after the body, its offset (https://github.com/mozilla-firefox/firefox/blob/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/cache2/CacheFileUtils.cpp#L475-L511); Alternative Data Type is the type named there (3 tested rows: script twice and a javascript/moz-script-bytecode type once). Peer Address is the peer-ip-address element, on 7 tested rows. Cached Media is the body of an entry whose Content-Type is image, video or audio, with its Content-Encoding (gzip, deflate, br with the Brotli package DLEAPP requires, and zstd on Python 3.14 or with the zstandard package) undone, a body the decoder cannot undo being kept as stored, typed from its bytes when they read as a picture, video or audio and from the stored Content-Type otherwise: 1,345 tested rows, of which 11 were typed differently from their Content-Type (7 sent as image/vnd.microsoft.icon and read as image/x-icon, and 4 whose bytes are PNG sent as image/x-icon once and image/jpeg three times); 4 entries with an image type had a body size of 0. Folder is entries or doomed; every tested row was in entries. Profile is the folder holding cache2 and User the home folder it sits in. Folder, Profile and User were uniform on windows11_arm_firefox_cache2_known_20261108 and on packt_dfc_linux_mint_usb, each holding one profile, and Folder on every tested image; Alternative Data Type was empty on every row of the first and Peer Address on every row of the second. They are kept because ubuntu2604_arm64_firefox_xdg_known_20261031 held three profiles of two users, and alternative data and peer addresses were present on other tested rows. The cache2 index and index.log files are not read. Not exercised on real data: macOS, the doomed folder, encrypted entries, metadata versions 1 and 2, video and audio bodies, and deflate-encoded bodies. On windows11_arm_firefox_cache2_known_20261108 580 of the 587 entries were fetched before the test started (the known data's README records Firefox already open, and not how it was opened), so a row records a response Firefox kept, not that anyone opened it.",
        "paths": ('*/[Mm]ozilla/[Ff]irefox/*/cache2/entries/*',
                  '*/[Mm]ozilla/[Ff]irefox/*/cache2/doomed/*',
                  '*/Library/Caches/Firefox/Profiles/*/cache2/entries/*',
                  '*/Library/Caches/Firefox/Profiles/*/cache2/doomed/*'),
        "output_types": "standard",
        "artifact_icon": "globe",
        "sample_data": {
            "windows11_arm_firefox_cache2_known_20261108": "Windows 11 build 26200 (ARM64), Firefox 159.0.1 | 587 rows",
            "ubuntu2604_arm64_firefox_xdg_known_20261031": "Ubuntu 26.04 LTS aarch64, Firefox 146.0 and 159.0 | 1031 rows",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 3511 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from scripts.chromium.simple_cache import decode_body
from scripts.filetype import guess_extension, guess_mime
from scripts.firefox_cache2 import (NO_EXPIRATION, Cache2Error, EncryptedEntry, alt_data_offset, read_entry,
                                    response_head, split_key)
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc
from scripts.macos_plists import user_from_path

_FOLDERS = ('entries', 'doomed')
_MEDIA_TYPES = ('image/', 'video/', 'audio/')


def _time(value):
    if not value or value == NO_EXPIRATION:
        return ''
    return datetime.fromtimestamp(value, timezone.utc)


def _host(url):
    try:
        return urlsplit(url).hostname or ''
    except ValueError:
        return ''


def _home_user(parts):
    """The folder after home/ on Linux, which user_from_path does not name."""
    if 'home' in parts and parts.index('home') + 1 < len(parts):
        return parts[parts.index('home') + 1]
    return ''


@artifact_processor
def firefoxCache(context):
    label = 'Firefox Cache Entries'
    data_list = []
    sources = set()
    skipped = {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path):
            continue
        relative_path = context.get_relative_path(path)
        relative = str(relative_path).replace('\\', '/')
        parts = PurePosixPath(relative).parts
        if len(parts) < 4 or parts[-3] != 'cache2' or parts[-2] not in _FOLDERS:
            continue
        with open(path, 'rb') as handle:
            data = handle.read()
        try:
            entry = read_entry(data)
        except EncryptedEntry:
            skipped['encrypted at rest'] = skipped.get('encrypted at rest', 0) + 1
            continue
        except Cache2Error as exc:
            skipped[str(exc)] = skipped.get(str(exc), 0) + 1
            continue
        prefix, url = split_key(entry.key)
        status_line, headers = response_head(entry.elements)
        pieces = status_line.split()
        status = pieces[1] if len(pieces) > 1 and pieces[0].startswith('HTTP/') else ''
        content_type = headers.get('content-type', '').split(';')[0].strip().lower()
        encoding = headers.get('content-encoding', '').strip().lower()
        offset, alt_type = alt_data_offset(entry.elements)
        body_size = offset if offset is not None else entry.data_size
        media = ''
        if content_type.startswith(_MEDIA_TYPES) and body_size > 0:
            body = decode_body(data[:min(body_size, entry.data_size)], encoding)
            # The bytes decide the type when they read as a picture, video or audio; otherwise (not
            # recognised, or an SVG the sniffer reads as HTML) the stored Content-Type stays.
            sniffed = guess_mime(body) if body else None
            if not (sniffed or '').startswith(_MEDIA_TYPES):
                sniffed = None
            mime = sniffed or content_type
            extension = (guess_extension(body) if sniffed else content_type.split('/', 1)[1].split('+')[0]) or None
            media = check_in_embedded_media(path, body, force_type=mime, force_extension=extension) or ''
        data_list.append((
            _time(entry.last_fetched), _time(entry.last_modified), _time(entry.expiration),
            url, _host(url), entry.elements.get('request-method', b'').decode('utf-8', 'replace'), status,
            content_type, encoding, body_size, media, entry.fetch_count, prefix, alt_type,
            entry.elements.get('peer-ip-address', b'').decode('utf-8', 'replace'),
            parts[-2], parts[-4], user_from_path(relative_path) or _home_user(parts)))
        sources.add(os.path.dirname(path))
    for reason, count in sorted(skipped.items()):
        logfunc(f'{label}: {count} entry file(s) not read: {reason}')
    data_headers = (('Last Fetched', 'datetime'), ('Last Modified', 'datetime'), ('Expires', 'datetime'),
                    'URL', 'Host', 'Request Method', 'HTTP Status', 'Content Type', 'Content Encoding',
                    ('Body Size (bytes)', 'number'), ('Cached Media', 'media'), ('Fetch Count', 'number'),
                    'Key Prefix', 'Alternative Data Type', 'Peer Address', 'Folder', 'Profile', 'User')
    return data_headers, data_list, '\n'.join(sorted(sources))
