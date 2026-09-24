"""Biome stream helpers for the macOS Biome artifacts in DLEAPP.

Author: @AlexisBrignoni, Claude.

A Biome stream is a folder of SEGB files, read with the vendored ccl_segb package, and each
record holds one protobuf message. `stream_records()` returns the written records of every
file an artifact matched; `fields()` reads one message's top-level fields by number, without
a schema.
"""

import os
import struct
from datetime import timezone

from scripts.ilapfuncs import logfunc
from scripts.macos_plists import user_from_path
from scripts.vendor.ccl_segb.ccl_segb import read_segb_file
from scripts.vendor.ccl_segb.ccl_segb_common import EntryState

_FIRMLINK_PREFIX = 'System/Volumes/Data/'


class StreamRecord:
    """One written SEGB record and where it was read from."""

    __slots__ = ('time', 'data', 'origin', 'source', 'offset', 'user')

    def __init__(self, time, data, origin, source, offset, user):
        self.time = time
        self.data = data
        self.origin = origin
        self.source = source
        self.offset = offset
        self.user = user


def sync_origin(relative_path):
    """'Local' for a stream's local folder, 'Remote (<folder>)' for a folder under remote/."""
    normalized = str(relative_path).replace('\\', '/')
    if '/remote/' in normalized:
        trailer = normalized.split('/remote/', 1)[1]
        return f"Remote ({trailer.split('/', 1)[0]})" if '/' in trailer else 'Remote'
    return 'Local'


def _view_key(relative_path):
    """The path with any System/Volumes/Data/ prefix removed, so both firmlink views match."""
    normalized = str(relative_path).replace('\\', '/').lstrip('/')
    if normalized.startswith(_FIRMLINK_PREFIX):
        return normalized[len(_FIRMLINK_PREFIX):]
    return normalized


def stream_records(context, label):
    """(records, sources): the written records of every SEGB file the artifact matched, and
    the files that contributed at least one of them.

    Hidden files, directories, the stream's lock file and anything under a tombstone folder
    are skipped. Records the SEGB file does not mark as written are counted in the run log
    and not returned. A logical extraction of a Mac can hold one stream file under Users/
    and under System/Volumes/Data/Users/; a record with the same offset, time and bytes in
    both copies is returned once, from the copy read first.
    """
    sources = []
    records = []
    seen = set()
    paths = sorted((str(p) for p in context.get_files_found()), key=lambda p: (len(p), p))
    for path in paths:
        name = os.path.basename(path)
        relative = context.get_relative_path(path)
        normalized = '/' + str(relative).replace('\\', '/') + '/'
        if name.startswith('.') or name == 'lock' or not os.path.isfile(path):
            continue
        if '/tombstone/' in normalized:
            continue
        try:
            entries = list(read_segb_file(path))
        except (ValueError, OSError, struct.error) as exc:
            logfunc(f'{label}: {relative} was not read as a SEGB file ({type(exc).__name__})')
            continue
        origin = sync_origin(relative)
        user = user_from_path(relative)
        view_key = _view_key(relative)
        written = other = repeated = 0
        for entry in entries:
            if entry.state != EntryState.Written:
                other += 1
                continue
            key = (view_key, entry.data_start_offset, entry.timestamp1, bytes(entry.data))
            if key in seen:
                repeated += 1
                continue
            seen.add(key)
            written += 1
            records.append(StreamRecord(entry.timestamp1.replace(tzinfo=timezone.utc),
                                        bytes(entry.data), origin, relative,
                                        entry.data_start_offset, user))
        if written:
            sources.append(path)
        note = f', {repeated} already read from the other view of this file' if repeated else ''
        logfunc(f'{label}: {written} written and {other} other records in {relative}{note}')
    return records, sources


def _varint(data, position):
    result = shift = 0
    while True:
        if position >= len(data):
            raise ValueError('varint runs past the end of the message')
        byte = data[position]
        position += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, position
        shift += 7
        if shift > 63:
            raise ValueError('varint longer than 64 bits')


def fields(data):
    """{field number: [values]} for one protobuf message, read without a schema.

    Varints come back as int, 64-bit and 32-bit fields as their raw little-endian bytes,
    and length-delimited fields as bytes. Raises ValueError on a malformed message.
    """
    found = {}
    position = 0
    length = len(data)
    while position < length:
        key, position = _varint(data, position)
        number, wire_type = key >> 3, key & 7
        if wire_type == 0:
            value, position = _varint(data, position)
        elif wire_type == 1:
            value, position = data[position:position + 8], position + 8
        elif wire_type == 2:
            size, position = _varint(data, position)
            value, position = data[position:position + size], position + size
        elif wire_type == 5:
            value, position = data[position:position + 4], position + 4
        else:
            raise ValueError(f'unsupported wire type {wire_type}')
        if position > length or number == 0:
            raise ValueError('field runs past the end of the message')
        found.setdefault(number, []).append(value)
    return found


def first(found, number):
    """The first value of a field, or None."""
    values = found.get(number)
    return values[0] if values else None


def text(value):
    """A length-delimited value as UTF-8 text ('' when absent)."""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode('utf-8', errors='replace')
    return '' if value is None else str(value)


def double(value):
    """A 64-bit field read as a little-endian double, or None."""
    if isinstance(value, (bytes, bytearray)) and len(value) == 8:
        return struct.unpack('<d', value)[0]
    return None
