"""Helpers shared by the DLEAPP macOS plist artifacts.

Author: @AlexisBrignoni, Claude.

NSKeyedArchiver archives keep their object graph in $objects, refer to objects with
plistlib.UID values and name the root objects under $top. resolve_keyed_archive() turns
such an archive back into plain dicts, lists, strings, bytes and datetimes.

Bookmark data (the 'book' blobs in shared file lists, Finder preferences and login
items) is read following the layout implemented in mac_alias (dmgbuild project, MIT
licence), src/mac_alias/bookmark.py at d0c076b4562541c1509d9874f42880378245d268: a
'book' header, the offset of the first table of contents, and typed items. Only the
items the artifacts report are kept: the URL (0x1003), the path components (0x1004),
the volume path (0x2002), the volume name (0x2010), the file creation date (0x1040) and
the volume creation date (0x2013). Bookmark dates are big-endian doubles of seconds since
2001-01-01 UTC.
"""

import hashlib
import os
import plistlib
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import logfunc

EPOCH_2001 = datetime(2001, 1, 1, tzinfo=timezone.utc)

_BOOKMARK_URL = 0x1003
_BOOKMARK_PATH = 0x1004
_BOOKMARK_FILE_CREATION = 0x1040
_BOOKMARK_VOLUME_PATH = 0x2002
_BOOKMARK_VOLUME_NAME = 0x2010
_BOOKMARK_VOLUME_CREATION = 0x2013

_TYPE_STRING = 0x0100
_TYPE_DATE = 0x0400
_TYPE_ARRAY = 0x0600


def load_plist(path):
    """The parsed plist at path, or None when it cannot be read as one."""
    try:
        with open(path, 'rb') as handle:
            return plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
        return None


def mac_absolute_utc(seconds):
    """Seconds since 2001-01-01 UTC as an aware datetime, or '' when not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        return ''
    try:
        return EPOCH_2001 + timedelta(seconds=seconds)
    except (OverflowError, ValueError):
        return ''


def as_utc(value):
    """A plist date (naive, UTC in plistlib) as an aware datetime, or ''."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return ''


def resolve_keyed_archive(archive, root='root'):
    """The object graph of an NSKeyedArchiver plist, resolved from $top[root]."""
    if not isinstance(archive, dict) or '$objects' not in archive:
        return None
    objects = archive['$objects']
    top = archive.get('$top', {})

    def resolve(value, seen):
        if isinstance(value, plistlib.UID):
            index = value.data
            if index in seen or index >= len(objects):
                return None
            return resolve_object(objects[index], seen | {index})
        if isinstance(value, list):
            return [resolve(item, seen) for item in value]
        if isinstance(value, dict):
            return {key: resolve(item, seen) for key, item in value.items()}
        return value

    def resolve_object(obj, seen):
        if obj == '$null':
            return None
        if not isinstance(obj, dict) or '$class' not in obj:
            return resolve(obj, seen)
        if 'NS.keys' in obj and 'NS.objects' in obj:
            keys = [resolve(key, seen) for key in obj['NS.keys']]
            return {str(key): resolve(item, seen) for key, item in zip(keys, obj['NS.objects'])}
        if 'NS.objects' in obj:
            return [resolve(item, seen) for item in obj['NS.objects']]
        if 'NS.string' in obj:
            return resolve(obj['NS.string'], seen)
        if 'NS.data' in obj:
            return resolve(obj['NS.data'], seen)
        if 'NS.bytes' in obj:
            return resolve(obj['NS.bytes'], seen)
        if 'NS.time' in obj:
            return mac_absolute_utc(obj['NS.time'])
        if 'NS.relative' in obj:
            base = resolve(obj.get('NS.base'), seen)
            relative = resolve(obj['NS.relative'], seen)
            return f'{base}{relative}' if base else relative
        if 'NS.uuidbytes' in obj:
            raw = resolve(obj['NS.uuidbytes'], seen)
            return raw.hex() if isinstance(raw, bytes) else raw
        return {key: resolve(item, seen) for key, item in obj.items() if key != '$class'}

    return resolve(top.get(root), frozenset())


def _bookmark_item(data, header_size, offset, depth=0):
    """One typed item of a bookmark, or None for a type not decoded here."""
    start = header_size + offset
    if depth > 4 or start < 0 or start + 8 > len(data):
        return None
    length, type_code = struct.unpack('<II', data[start:start + 8])
    body = data[start + 8:start + 8 + length]
    if len(body) != length:
        return None
    kind = type_code & 0xFFFFFF00
    if kind == _TYPE_STRING:
        return body.decode('utf-8', 'replace')
    if kind == _TYPE_DATE and length == 8:
        return mac_absolute_utc(struct.unpack('>d', body)[0])
    if kind == _TYPE_ARRAY:
        return [_bookmark_item(data, header_size, struct.unpack('<I', body[i:i + 4])[0], depth + 1)
                for i in range(0, length - length % 4, 4)]
    return None


def _joined_path(components):
    """'/'-joined path components, '/' for an empty list, or '' when not a list of strings."""
    if not isinstance(components, list) or not all(isinstance(part, str) for part in components):
        return ''
    return '/' + '/'.join(components)


def bookmark_fields(data):
    """{'url', 'path', 'volume_path', 'volume_name', 'file_created', 'volume_created'} from 'book' data.

    Values the bookmark does not carry are ''. Returns None when data is not a 'book'
    bookmark or its first table of contents cannot be read.
    """
    if not isinstance(data, (bytes, bytearray)) or len(data) < 20:
        return None
    data = bytes(data)
    magic, size, _version, header_size = struct.unpack('<4sIII', data[:16])
    if magic != b'book' or header_size < 16 or header_size + 4 > len(data) or size > len(data):
        return None
    toc_offset = struct.unpack('<I', data[header_size:header_size + 4])[0]
    base = header_size + toc_offset
    if base + 20 > len(data):
        return None
    _toc_size, toc_magic, _toc_id, _next, count = struct.unpack('<IIIII', data[base:base + 20])
    if toc_magic != 0xFFFFFFFE:
        return None
    items = {}
    for index in range(count):
        entry = base + 20 + 12 * index
        if entry + 12 > len(data):
            break
        item_id, item_offset, _unused = struct.unpack('<III', data[entry:entry + 12])
        items[item_id] = item_offset
    def get(item_id):
        return _bookmark_item(data, header_size, items[item_id]) if item_id in items else None
    path = _joined_path(get(_BOOKMARK_PATH))
    url = get(_BOOKMARK_URL)
    return {
        'url': url if isinstance(url, str) else '',
        'path': path,
        'volume_path': get(_BOOKMARK_VOLUME_PATH) or '',
        'volume_name': get(_BOOKMARK_VOLUME_NAME) or '',
        'file_created': get(_BOOKMARK_FILE_CREATION) or '',
        'volume_created': get(_BOOKMARK_VOLUME_CREATION) or '',
    }


_FIRMLINK_PREFIX = 'System/Volumes/Data/'


def user_from_path(path):
    """The folder name after Users in a path, 'root' under private/var/root, or ''."""
    parts = str(path).replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part == 'Users':
            return parts[index + 1]
        if part == 'private' and parts[index + 1:index + 3] == ['var', 'root']:
            return 'root'
    return ''


def canonical_relative(relative):
    """A path inside the extraction with a leading System/Volumes/Data/ removed.

    macOS firmlinks expose the Data volume's folders both at the root and under
    System/Volumes/Data/, so a logical extraction can hold one file under both paths.
    """
    relative = str(relative).replace('\\', '/').lstrip('/')
    return relative[len(_FIRMLINK_PREFIX):] if relative.startswith(_FIRMLINK_PREFIX) else relative


def _digest(path, sidecars):
    digest = hashlib.sha256()
    for suffix in ('',) + sidecars:
        candidate = str(path) + suffix
        if os.path.isfile(candidate):
            with open(candidate, 'rb') as handle:
                while True:
                    block = handle.read(1 << 20)
                    if not block:
                        break
                    digest.update(block)
        digest.update(b'|')
    return digest.hexdigest()


def unique_sources(context, paths, sidecars=(), label=''):
    """(paths, skipped): paths less byte-identical copies of one file under two views.

    A logical extraction of a Mac can hold the same file under Users/ and under
    System/Volumes/Data/Users/, where macOS firmlinks expose it twice. Two paths that
    differ only by that System/Volumes/Data/ prefix and have identical bytes (and
    identical sidecars, such as -wal) are read once; copies that differ are both kept.
    """
    kept, seen, skipped = [], set(), 0
    for path in sorted({str(p) for p in paths}, key=lambda p: (len(p), p)):
        if not os.path.isfile(path):
            continue
        key = (canonical_relative(context.get_relative_path(path)), _digest(path, sidecars))
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        kept.append(path)
    if skipped and label:
        logfunc(f'{label}: {skipped} byte-identical copy(ies) under System/Volumes/Data not read again')
    return kept, skipped
