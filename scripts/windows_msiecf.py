"""Read MSIE Cache File (index.dat) records, format version 5.2.

Layout from the libyal MSIE Cache File (index.dat) format specification:
https://github.com/libyal/libmsiecf/blob/a99a703d190d62f6c21b6225cf84ce80037e45d5/documentation/MSIE%20Cache%20File%20(index.dat)%20format.asciidoc
Records are found by reading every 128-byte block from 0x4000 for a record signature, as libmsiecf does, and marked
allocated or not from the allocation bitmap; a record whose blocks are partly allocated and partly not is skipped.
"""

import struct

SIGNATURE = b'Client UrlCache MMF Ver '
_BLOCK = 128
_FIRST_BLOCK = 0x4000
_UNINITIALIZED = (0x0BADF00D, 0xDEADBEEF)


class MsiecfError(ValueError):
    """The bytes are not an index.dat this reader handles."""


def _u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def _u64(data, offset):
    return struct.unpack_from('<Q', data, offset)[0]


def _cstring(data, start, end):
    """The NUL-terminated byte string at start, no further than end, as text (Windows-1252)."""
    if not start or start >= end:
        return ''
    stop = data.find(b'\x00', start, end)
    return data[start:end if stop == -1 else stop].decode('cp1252', 'replace')


def fat_datetime(value):
    """(year, month, day, hour, minute, second) of a 32-bit FAT date time (date in the low 16 bits), or None."""
    if value in (0, 0xFFFFFFFF):
        return None
    date, time = value & 0xFFFF, value >> 16
    day, month, year = date & 0x1F, (date >> 5) & 0x0F, 1980 + (date >> 9)
    second, minute, hour = (time & 0x1F) * 2, (time >> 5) & 0x3F, time >> 11
    if not (1 <= month <= 12 and 1 <= day <= 31 and hour < 24 and minute < 60 and second < 60):
        return None
    return year, month, day, hour, minute, second


def parse(data):
    """(version, cache directory names, records) of one index.dat.

    Each record is a dict with offset, type ('URL', 'REDR' or 'LEAK') and the fields that type carries.
    """
    if len(data) < 0x250 or not data.startswith(SIGNATURE):
        raise MsiecfError('not an MSIE cache file')
    version = data[24:27].decode('ascii', 'replace')
    if version != '5.2':
        raise MsiecfError(f'format version {version} is not read')
    directories = []
    count = _u32(data, 72)
    for index in range(min(count, 32)):
        entry = 76 + index * 12
        directories.append(data[entry + 4:entry + 12].split(b'\x00')[0].decode('ascii', 'replace'))
    records = []
    offset = _FIRST_BLOCK
    while offset + 8 <= len(data):
        signature = data[offset:offset + 4]
        blocks = _u32(data, offset + 4)
        if signature in (b'URL ', b'REDR', b'LEAK', b'HASH') and blocks:
            span = min(blocks, (len(data) - offset) // _BLOCK) or 1
            states = {_allocated(data, offset + index * _BLOCK) for index in range(span)}
            if signature != b'HASH':
                if states == {True} or states == {False}:
                    record = _record(data, offset)
                    if record is not None:
                        record['allocated'] = states == {True}
                        records.append(record)
            offset += span * _BLOCK
            continue
        offset += _BLOCK
    return version, directories, records


def _allocated(data, offset):
    """Whether the allocation bitmap at 0x250 marks the 128-byte block at offset as in use."""
    index = (offset - _FIRST_BLOCK) // _BLOCK
    position = 0x250 + index // 8
    return position < _FIRST_BLOCK and bool(data[position] >> (index % 8) & 1)


def _record(data, offset):
    signature = data[offset:offset + 4]
    blocks = _u32(data, offset + 4)
    end = min(len(data), offset + max(blocks, 1) * _BLOCK)
    if signature == b'URL ' and end - offset >= 96:
        location = _u32(data, offset + 52)
        filename = _u32(data, offset + 60)
        data_offset, data_size = _u32(data, offset + 68), _u32(data, offset + 72)
        payload = b''
        if data_offset and data_size and offset + data_offset + data_size <= end:
            payload = data[offset + data_offset:offset + data_offset + data_size]
        return {'offset': offset, 'type': 'URL',
                'secondary': _u64(data, offset + 8), 'primary': _u64(data, offset + 16),
                'expiration': _u32(data, offset + 24),
                'size': _u32(data, offset + 32) | (_u32(data, offset + 36) << 32),
                'location': _cstring(data, offset + location, end) if location else '',
                'directory': data[offset + 56],
                'filename': _cstring(data, offset + filename, end) if filename else '',
                'flags': _u32(data, offset + 64), 'data': payload,
                'last_checked': _u32(data, offset + 80), 'hits': _u32(data, offset + 84)}
    if signature == b'REDR' and end - offset >= 16:
        return {'offset': offset, 'type': 'REDR', 'location': _cstring(data, offset + 16, end)}
    if signature == b'LEAK' and end - offset >= 96:
        filename = _u32(data, offset + 60)
        return {'offset': offset, 'type': 'LEAK', 'size': _u32(data, offset + 32), 'directory': data[offset + 56],
                'filename': _cstring(data, offset + filename, end) if filename else ''}
    return None
