"""Cookies in the .binarycookies stores macOS keeps for Safari and other apps, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosBinaryCookies": {
        "name": "Binary Cookies",
        "description": "Cookies in the .binarycookies stores under a Library/Cookies or "
                       "Library/HTTPStorages folder, such as Safari's: creation and expiry time, "
                       "domain, name, path, value, secure and HTTP only flags and the container "
                       "the store belongs to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Cookies (macOS)",
        "notes": "Reads each .binarycookies file in a Library/Cookies folder, including one inside an app "
                 "container such as Safari's "
                 "Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies, and in a "
                 "Library/HTTPStorages folder, one row per cookie record. The layout followed is the one "
                 "in the dtformats 'Safari cookies file format specification' by Joachim Metz: the "
                 "signature 'cook', a big-endian page count and page sizes, pages that begin with 00 00 01 "
                 "00 and hold a little-endian record count and record offsets, and records holding "
                 "little-endian flags, the offsets of the domain, name, path and value strings, and the "
                 "expiration and creation times as 64-bit Cocoa timestamps "
                 "(https://github.com/libyal/dtformats/blob/6e087e6803ed6c711bf7d19bc27ddf858421f55a/documentation/Safari%20Cookies.asciidoc?plain=1#L81-L93, "
                 "https://github.com/libyal/dtformats/blob/6e087e6803ed6c711bf7d19bc27ddf858421f55a/documentation/Safari%20Cookies.asciidoc?plain=1#L103-L115 "
                 "and "
                 "https://github.com/libyal/dtformats/blob/6e087e6803ed6c711bf7d19bc27ddf858421f55a/documentation/Safari%20Cookies.asciidoc?plain=1#L127-L157). "
                 "Created (UTC) and Expires (UTC) are those times read as seconds since 2001-01-01 UTC. A "
                 "page without that signature, a record shorter than 56 bytes, a record whose string "
                 "offsets fall outside it and a record that does not fit its page are counted in the run "
                 "log and skipped, and a file that does not begin with 'cook' is logged and not read. "
                 "Secure and HTTP Only are the flag bits 0x1 and 0x4, which the specification names as a "
                 "secure (https) cookie and an HTTP only cookie "
                 "(https://github.com/libyal/dtformats/blob/6e087e6803ed6c711bf7d19bc27ddf858421f55a/documentation/Safari%20Cookies.asciidoc?plain=1#L159-L167); "
                 "Flags (as stored) is the whole value in hexadecimal, and the specification does not name "
                 "its other bits. On the public MacBook Pro logical extraction (macOS 15.4, not a "
                 "registered corpus key) every record held, after its value, a binary property list with "
                 "the key AccessTime, and 2 of them also StoragePartition; neither key is in the "
                 "specification, and what writes them is not established. AccessTime (UTC) is AccessTime "
                 "read as seconds since 2001-01-01 UTC, the unit of the record's other two times: it was "
                 "present on all 189 records there and on none was it earlier than Created (UTC). Storage "
                 "Partition (as stored) is the StoragePartition value, a site address on those 2 records. "
                 "None of the 148 records on dleapp_macos_bigsur held such a property list, so AccessTime "
                 "(UTC) and Storage Partition (as stored) are empty on all of its rows. Container is taken "
                 "from the path: the folder after Containers or Group Containers, or the name of an "
                 "HTTPStorages file, which on the tested images was an app's bundle identifier; it is "
                 "blank for a Library/Cookies folder outside a container. A logical extraction holds a "
                 "store at its root and again under System/Volumes/Data: a byte-identical second copy is "
                 "not read, and when the two differ a record both hold is reported once, from the copy at "
                 "the root. On the MacBook Pro the user's com.google.GoogleUpdater HTTPStorages store "
                 "differed between the two, each copy holding one NID cookie with a different creation "
                 "time, so both are reported; its 189 records came from 7 files, 135 of them Safari's, "
                 "created 2025-11-20 to 2025-12-25. On dleapp_macos_bigsur Safari's store held 146 of the "
                 "148 records, created 2021-02-15 to 2021-02-19, and the com.apple.Music HTTPStorages "
                 "store and the com.apple.stocks.widget container one each. The property list at the end "
                 "of each file, NSHTTPCookieAcceptPolicy on both images, is not reported. Values are "
                 "reported verbatim and can include session identifiers; whether any remains valid is not "
                 "tested.",
        "paths": ('*/Library/Cookies/*.binarycookies', '*/Library/HTTPStorages/*.binarycookies'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 148 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import plistlib
import re
import struct
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import mac_absolute_utc, unique_sources

_PAGE_SIGNATURE = b'\x00\x00\x01\x00'
_FIRMLINK = re.compile(r'(^|/)System/Volumes/Data/')
_SECURE = 0x1
_HTTP_ONLY = 0x4


def _string(record, offset, end):
    """The NUL-terminated string at offset, read no further than end."""
    if not 0 < offset < end:
        return ''
    stop = record.find(b'\x00', offset, end)
    return record[offset:stop if stop >= 0 else end].decode('utf-8', errors='replace')


def _record(record, problems):
    """The fields of one cookie record, or None when its offsets do not fit it."""
    if len(record) < 56:
        problems['records shorter than 56 bytes'] += 1
        return None
    flags = struct.unpack_from('<I', record, 8)[0]
    domain, name, path, value = struct.unpack_from('<4I', record, 16)
    expires, created = struct.unpack_from('<2d', record, 40)
    if not all(56 <= offset < len(record) for offset in (domain, name, path, value)):
        problems['records whose string offsets fall outside them'] += 1
        return None
    value_end = record.find(b'\x00', value)
    value_end = len(record) if value_end < 0 else value_end
    extra = {}
    plist_at = record.find(b'bplist00', value_end)
    if plist_at >= 0:
        try:
            loaded = plistlib.loads(record[plist_at:])
        except (plistlib.InvalidFileException, ValueError, TypeError, struct.error):
            problems['records whose trailing property list could not be read'] += 1
        else:
            extra = loaded if isinstance(loaded, dict) else {}
    access = extra.get('AccessTime')
    partition = extra.get('StoragePartition')
    return (mac_absolute_utc(created), mac_absolute_utc(expires),
            mac_absolute_utc(access) if isinstance(access, (int, float)) else '',
            _string(record, domain, len(record)), _string(record, name, len(record)),
            _string(record, path, len(record)), record[value:value_end].decode('utf-8', errors='replace'),
            'true' if flags & _SECURE else 'false', 'true' if flags & _HTTP_ONLY else 'false',
            f'0x{flags:08X}', partition if isinstance(partition, str) else '')


def _cookies(data, problems):
    """Every cookie record in a .binarycookies file, or None when it is not one."""
    if len(data) < 8 or data[:4] != b'cook':
        return None
    pages = struct.unpack_from('>I', data, 4)[0]
    if 8 + 4 * pages > len(data):
        return None
    sizes = struct.unpack_from(f'>{pages}I', data, 8)
    position = 8 + 4 * pages
    rows = []
    for size in sizes:
        page = data[position:position + size]
        position += size
        if len(page) < 8 or page[:4] != _PAGE_SIGNATURE:
            problems['pages without the page signature'] += 1
            continue
        count = struct.unpack_from('<I', page, 4)[0]
        if 8 + 4 * count > len(page):
            problems['pages whose record table overruns them'] += 1
            continue
        for offset in struct.unpack_from(f'<{count}I', page, 8):
            if offset + 4 > len(page):
                problems['records starting outside their page'] += 1
                continue
            length = struct.unpack_from('<I', page, offset)[0]
            if offset + length > len(page):
                problems['records ending outside their page'] += 1
                continue
            cookie = _record(page[offset:offset + length], problems)
            if cookie is not None:
                rows.append(cookie)
    return rows


def _container(relative):
    """The app container or HTTPStorages store a cookie file belongs to, from its path."""
    parts = relative.replace('\\', '/').split('/')
    if len(parts) >= 2 and parts[-2] == 'HTTPStorages':
        return parts[-1][:-len('.binarycookies')]
    for index in range(len(parts) - 1):
        if parts[index] in ('Containers', 'Group Containers') and index + 1 < len(parts):
            return parts[index + 1]
    return ''


@artifact_processor
def macosBinaryCookies(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Expires (UTC)', 'datetime'), ('AccessTime (UTC)', 'datetime'),
                    'Domain', 'Name', 'Path', 'Value', 'Secure', 'HTTP Only', 'Flags (as stored)',
                    'Storage Partition (as stored)', 'Container', 'Source File')
    data_list = []
    sources = []
    problems = Counter()
    seen = set()
    repeated = 0
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Binary Cookies')
    # unique_sources orders the paths by length, so the capture outside System/Volumes/Data comes
    # first; a record the other capture of the same store also holds is reported once.
    for path in paths:
        if os.path.isdir(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            logfunc(f'Binary Cookies: could not read {relative}')
            continue
        rows = _cookies(data, problems)
        if rows is None:
            logfunc(f'Binary Cookies: not a binary cookie file: {relative}')
            continue
        container = _container(relative)
        store = _FIRMLINK.sub(r'\1', relative.replace('\\', '/'), count=1)
        kept = []
        for row in rows:
            if (store,) + row in seen:
                repeated += 1
                continue
            seen.add((store,) + row)
            kept.append(row + (container, relative))
        data_list.extend(kept)
        if kept:
            sources.append(path)
    if repeated:
        logfunc(f'Binary Cookies: {repeated} record(s) the other capture of the same store also holds not '
                'reported again')
    if problems:
        logfunc('Binary Cookies: skipped ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    logfunc(f'Binary Cookies: {len(data_list)} cookie(s) from {len(sources)} file(s).')
    return data_headers, data_list, '\n'.join(sources)
