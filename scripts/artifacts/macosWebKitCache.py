"""Records in the WebKit network caches (WebKitCache) that Safari and other apps keep on macOS, for
DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosWebKitCache": {
        "name": "WebKit Network Cache",
        "description": "Records in the WebKit network cache folders (WebKitCache) of Safari and "
                       "other apps: the time stamp WebKit stored with each record, its partition, "
                       "type and URL, and for a cached response its HTTP status, MIME type, HTTP "
                       "version, response headers and body size.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Web Cache (macOS)",
        "notes": "Reads the record files, named by 40 hexadecimal characters, in the Records folders of "
                 "each WebKitCache/Version N folder, such as Safari's under "
                 "Containers/com.apple.Safari/Data/Library/Caches/com.apple.Safari/WebKitCache, one row "
                 "per record, with the salt file beside them; a byte-identical copy of a record under "
                 "System/Volumes/Data is not read again. The layout is WebKit's own, read from its source "
                 "at the last commit writing cache version 17 "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.h#L134) "
                 "and at the last writing version 16 "
                 "(https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.h#L112); "
                 "where only a version 17 line is cited below, the version 16 commit has code doing the "
                 "same. Both write a record as its metadata followed by the header and, when the body is "
                 "kept in the record, the body (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L786-L805; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L628-L647). "
                 "The metadata is, in order, the cache version, the key (partition, type, URL, range and "
                 "two hashes), the time stamp, the header hash and size, the body hash and size, whether "
                 "the body is in the record, and a SHA-1 checksum over those values (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L739-L755 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheCoders.cpp#L37-L45; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L585-L601 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheCoders.cpp#L35-L43). "
                 "Strings, numbers and the checksum are read as WebKit's persistence coder writes them "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/persistence/PersistentCoders.cpp#L91-L107, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/persistence/PersistentEncoder.h#L98-L116, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/persistence/PersistentEncoder.cpp#L45-L50 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/persistence/PersistentEncoder.cpp#L118-L123). "
                 "A record whose metadata cannot be read or whose checksum does not match is counted in "
                 "the run log and left out, as is one whose header hash does not match the SHA-1 of the "
                 "salt followed by the header, the checks WebKit makes before reading a record "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L623-L685, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L687-L705 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheData.cpp#L88-L100). "
                 "The salt is the first 8 bytes of the salt file WebKit keeps in each Version folder, "
                 "which WebKit replaces when it is shorter "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L331-L334, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/FileSystem.h#L141 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/FileSystem.cpp#L414-L437); "
                 "a record with no readable salt file of at least 8 bytes beside it is reported and "
                 "counted as not checked. Every record on both tested images passed both checks. Stored "
                 "(UTC) is the record's time stamp, seconds since 1970-01-01 UTC (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WTF/wtf/persistence/PersistentCoders.cpp#L173-L176; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WTF/wtf/persistence/PersistentCoders.cpp#L172-L175), "
                 "copied from the entry the record is made from (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L791, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L115 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L55; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L633, "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L112 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L52). "
                 "WebKit sets an entry's time stamp to the current time when it makes an entry for a "
                 "response or a redirect (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L43-L45 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L54-L56; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L41-L43 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L52-L54), "
                 "which it does each time it stores a response or a redirect or updates a revalidated "
                 "response (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L561-L562, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L597-L604 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L618-L619; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L503-L504, "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L538-L545 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L559-L560), "
                 "and when it makes a new list of subresources (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L130-L132; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L127-L129), "
                 "so a Resource record's time stamp is that of the store or update that wrote it. A list "
                 "of subresources that WebKit reads back from the cache and rewrites keeps the time stamp "
                 "it was stored with (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheSpeculativeLoadManager.cpp#L252-L254, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L77-L79 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L138-L141; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheSpeculativeLoadManager.cpp#L242-L244, "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L74-L76 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheSubresourcesEntry.cpp#L135-L138), "
                 "so a SubResources record's time stamp can be older than the record's last rewrite. As a "
                 "check, the time stamp was within 60 seconds of the response's own Date header on 1,503 "
                 "of the 1,851 dleapp_macos_bigsur Resource records carrying one and on 1,879 of the 2,951 "
                 "on the public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15), "
                 "with median gaps of 0.7 and 0.8 seconds. Partition, Type and URL are the key's "
                 "partition, type and URL: WebKit makes a response's key from the request's cache "
                 "partition, the type Resource and the URL without its fragment "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L165-L171 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L68-L73), "
                 "and a SubResources record reuses the key of the page it lists subresources for, so its "
                 "URL is that page "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheSpeculativeLoadManager.cpp#L80-L90). "
                 "The key's range, taken from the request's Range header "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCache.cpp#L169), "
                 "held no value on every tested record and is not reported, and the list a SubResources "
                 "record holds is not read. For a Resource record of cache version 16 or 17, HTTP Status, "
                 "MIME Type, HTTP Version and Response Headers are read from the stored response, which "
                 "WebKit writes first in a Resource record's header (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L87-L90; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebKit/NetworkProcess/cache/NetworkCacheEntry.cpp#L85-L88) "
                 "with its fields in the same order in both versions (version 17: "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebCore/platform/WebCorePersistentCoders.cpp#L676-L691 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebCore/platform/WebCorePersistentCoders.cpp#L831-L838; "
                 "version 16: "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebCore/platform/WebCorePersistentCoders.cpp#L728-L743 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/102588eaaeb7cc47ce9308b229049a80bedf4600/Source/WebCore/platform/WebCorePersistentCoders.cpp#L883-L890); "
                 "Response Headers holds each header as 'name: value' on its own line, and the fields "
                 "after the status code are not read. They are blank for a SubResources record, for a "
                 "response WebKit stored as null, and for a response that could not be read or is of "
                 "another cache version, both of which are counted in the run log. Body Size (bytes) is "
                 "the stored body size, and Body Stored In says whether the body is in the record or in a "
                 "separate blob file, named after the record with -blob added, which WebKit uses for a "
                 "body larger than the memory page size "
                 "(https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L56, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L593-L596, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L61-L64, "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L796 "
                 "and "
                 "https://github.com/WebKit/WebKit/blob/33a2d0520bab9ffc18aeebe94dfc166b2da966ff/Source/WebKit/NetworkProcess/cache/NetworkCacheStorage.cpp#L1025-L1028); "
                 "the bodies are not read. On the MacBook Pro a -blob file sat beside each of the 1,975 "
                 "records reported as stored in a blob file and beside none of the other 1,053. The "
                 "largest body kept in a record was 4,088 bytes on dleapp_macos_bigsur and 4,083 on the "
                 "MacBook Pro, and the smallest in a blob file 4,107 and 4,100. Every SubResources record "
                 "had a body size of 0. Cache Version is the version in the metadata, and Cache Folder the "
                 "folder above WebKitCache. On dleapp_macos_bigsur the 1,927 records (1,858 Resource, 69 "
                 "SubResources) are Safari's, stored 2020-12-12 to 2021-02-17; Cache Version held one "
                 "value, 16, and Cache Folder one value, com.apple.Safari, on all 1,927 rows. On the "
                 "MacBook Pro the 3,028 records (2,955 Resource, 73 SubResources) are Safari's, stored "
                 "2025-11-20 to 2025-12-12; Cache Version held one value, 17, and Cache Folder one value, "
                 "com.apple.Safari, on all 3,028 rows, and its byte-identical copies under "
                 "System/Volumes/Data were not read. On both images Safari's WebKitCache under "
                 "Library/Caches had a salt file and no records, as did the Passwords app's on the MacBook "
                 "Pro.",
        "paths": ('*/WebKitCache/Version */Records/*/*/'
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]'
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]'
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]'
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]',
                  '*/WebKitCache/Version */salt'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1,927 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import hashlib
import os
import struct
from collections import Counter
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import unique_sources

# WTF::Persistence salts each value it adds to a checksum with a number for its type.
_SALT = {'bool': 3, 'u32': 11, 'u64': 13, 'i16': 103, 'i64': 19, 'f64': 29, 'data': 101}
_FORMAT = {'bool': '<?', 'u32': '<I', 'u64': '<Q', 'i16': '<h', 'i64': '<q', 'f64': '<d'}
_DECODED_VERSIONS = (16, 17)
_SALT_SIZE = 8  # WebKit reads the first 8 bytes of the salt file and remakes a shorter one


class _Decoder:
    """Reads values the way WTF::Persistence::Decoder does, keeping the running checksum."""

    def __init__(self, data):
        self.data = data
        self.position = 0
        self.sha1 = hashlib.sha1()

    def _take(self, size, salt):
        raw = self.data[self.position:self.position + size]
        if len(raw) < size:
            raise ValueError('record ends early')
        self.sha1.update(struct.pack('<I', salt))
        self.sha1.update(raw)
        self.position += size
        return raw

    def number(self, kind):
        return struct.unpack(_FORMAT[kind], self._take(struct.calcsize(_FORMAT[kind]), _SALT[kind]))[0]

    def fixed(self, size):
        return self._take(size, _SALT['data'])

    def string(self):
        length = self.number('u32')
        if length == 0xFFFFFFFF:
            return None
        if self.number('bool'):
            return self.fixed(length).decode('latin-1')
        return self.fixed(2 * length).decode('utf-16-le', errors='replace')

    def checksum_matches(self):
        saved = self.data[self.position:self.position + 20]
        self.position += 20
        return len(saved) == 20 and saved == self.sha1.digest()


def _metadata(data):
    """The record metadata, or None when it cannot be read or its checksum does not match."""
    decoder = _Decoder(data)
    try:
        version = decoder.number('u32')
        partition, kind, url, _range = (decoder.string() for _ in range(4))
        decoder.fixed(20)
        decoder.fixed(20)
        stamp = decoder.number('f64')
        header_hash = decoder.fixed(20)
        header_size = decoder.number('u64')
        decoder.fixed(20)
        body_size = decoder.number('u64')
        inline = decoder.number('bool')
    except (ValueError, struct.error):
        return None
    if not decoder.checksum_matches():
        return None
    return {'version': version, 'partition': partition, 'type': kind, 'url': url, 'stamp': stamp,
            'header_hash': header_hash, 'header_offset': decoder.position, 'header_size': header_size,
            'body_size': body_size, 'inline': inline}


def _response(header):
    """(status, MIME type, HTTP version, headers) of the response a Resource record stores."""
    decoder = _Decoder(header)
    if decoder.number('bool'):
        return ('', '', '', '')
    decoder.string()
    mime = decoder.string()
    decoder.number('i64')
    decoder.string()
    decoder.string()
    version = decoder.string()
    headers = []
    for _ in range(decoder.number('u64')):
        name = decoder.string()
        headers.append(f'{name}: {decoder.string()}')
    return (str(decoder.number('i16')), mime or '', version or '', '\n'.join(headers))


def _utc(seconds):
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


@artifact_processor
def macosWebKitCache(context):
    data_headers = (('Stored (UTC)', 'datetime'), 'Partition', 'Type', 'URL', 'HTTP Status', 'MIME Type',
                    'HTTP Version', 'Response Headers', 'Body Size (bytes)', 'Body Stored In', 'Cache Version',
                    'Cache Folder', 'Source File')
    data_list = []
    sources = []
    problems = Counter()
    files = [path for path in context.get_files_found() if not os.path.isdir(path)]
    salts = {}
    for path in files:
        if os.path.basename(path) == 'salt':
            try:
                with open(path, 'rb') as handle:
                    salt = handle.read(_SALT_SIZE)
            except OSError:
                continue
            if len(salt) == _SALT_SIZE:
                salts[os.path.dirname(context.get_relative_path(path).replace('\\', '/'))] = salt
    records, _skipped = unique_sources(context, [path for path in files if os.path.basename(path) != 'salt'],
                                       label='WebKit Network Cache')
    for path in records:
        relative = context.get_relative_path(path).replace('\\', '/')
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['records that could not be read'] += 1
            continue
        metadata = _metadata(data)
        if metadata is None:
            problems['records whose metadata could not be read or whose checksum did not match'] += 1
            continue
        header = data[metadata['header_offset']:metadata['header_offset'] + metadata['header_size']]
        version_folder = relative.split('/Records/', 1)[0]
        salt = salts.get(version_folder)
        if salt is None:
            problems['records with no readable salt file of at least 8 bytes beside them, header hash not checked'] += 1
        elif hashlib.sha1(salt + header).digest() != metadata['header_hash']:
            problems['records whose header hash did not match'] += 1
            continue
        response = ('', '', '', '')
        if metadata['type'] == 'Resource':
            if metadata['version'] in _DECODED_VERSIONS:
                try:
                    response = _response(header)
                except (ValueError, struct.error):
                    problems['Resource records whose response could not be read'] += 1
            else:
                problems[f"records of cache version {metadata['version']}, response not read"] += 1
        parts = version_folder.split('/')
        folder = parts[parts.index('WebKitCache') - 1] if 'WebKitCache' in parts[1:] else ''
        data_list.append((_utc(metadata['stamp']), metadata['partition'] or '', metadata['type'] or '',
                          metadata['url'] or '') + response
                         + (metadata['body_size'], 'record' if metadata['inline'] else 'blob file',
                            metadata['version'], folder, context.get_relative_path(path)))
        sources.append(path)
    if problems:
        logfunc('WebKit Network Cache: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    logfunc(f'WebKit Network Cache: {len(data_list)} record(s).')
    return data_headers, data_list, '\n'.join(sources)
