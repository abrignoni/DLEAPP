"""Read the records of a macOS Finder .DS_Store file.

Written for DLEAPP from Wim Lewis's notes on the format, which build on Mark Mentovai's
reverse engineering (Wim Lewis, 'DS_Store Format', DSStoreFormat.pod in the
Mac-Finder-DSStore 1.00 distribution,
https://cpan.metacpan.org/authors/id/W/WI/WIML/Mac-Finder-DSStore-1.00.tar.gz;
Mark Mentovai, https://wiki.mozilla.org/DS_Store_File_Format). Apple does not document
the format.

The file is a four-byte header (00 00 00 01) followed by an area managed by a buddy
allocator; the allocator's table of contents names the master block of a B-tree
('DSDB'), and the B-tree holds the records. A record names a file in the folder (or '.'
for the folder itself), a four-character structure code, a four-character data type and
a value. Every value is returned as stored: text as text, numbers as numbers, blobs as
bytes. Nothing here interprets what a structure code means.
"""
import struct

_MAGIC = b'\x00\x00\x00\x01Bud1'
# More nodes than this in one file is a loop or damage, not a folder.
_MAX_NODES = 1 << 16


class DSStoreError(Exception):
    """The bytes are not a .DS_Store file this reader can walk."""


def _u32(data, offset, end):
    if offset < 0 or offset + 4 > end:
        raise DSStoreError(f'a 4-byte field at {offset} runs past {end}')
    return struct.unpack_from('>I', data, offset)[0]


def _take(data, offset, length, end):
    if offset < 0 or length < 0 or offset + length > end:
        raise DSStoreError(f'{length} bytes at {offset} run past {end}')
    return data[offset:offset + length]


def _allocator(data):
    """(block addresses, table of contents) from the buddy allocator's bookkeeping block."""
    if len(data) < 36 or data[:8] != _MAGIC:
        raise DSStoreError('no Bud1 header')
    offset, size, second = struct.unpack_from('>III', data, 8)
    if offset != second:
        raise DSStoreError('the two copies of the allocator offset disagree')
    start = 4 + offset
    end = min(len(data), start + size)
    count = _u32(data, start, end)
    position = start + 8
    addresses = [_u32(data, position + 4 * i, end) for i in range(count)]
    position += 4 * (-(-count // 256) * 256)
    entries = _u32(data, position, end)
    position += 4
    contents = {}
    for _ in range(entries):
        length = _take(data, position, 1, end)[0]
        name = _take(data, position + 1, length, end).decode('mac_roman')
        contents[name] = _u32(data, position + 1 + length, end)
        position += 5 + length
    return addresses, contents


def _block(data, addresses, number):
    """(start, end) of an allocated block, the end capped at the end of the file; a block
    past the end is then refused by the bounded reads that follow."""
    if number >= len(addresses) or not addresses[number]:
        raise DSStoreError(f'block {number} is not allocated')
    address = addresses[number]
    start = 4 + (address & ~0x1F)
    return start, min(len(data), start + (1 << (address & 0x1F)))


def _record(data, position, end):
    """One record at position: ((name, code, data type, value), next position)."""
    length = _u32(data, position, end)
    name = _take(data, position + 4, 2 * length, end).decode('utf-16-be', 'replace')
    position += 4 + 2 * length
    code = _take(data, position, 4, end).decode('mac_roman')
    kind = _take(data, position + 4, 4, end).decode('mac_roman')
    position += 8
    if kind in ('long', 'shor'):
        value, position = _u32(data, position, end), position + 4
    elif kind == 'bool':
        value, position = _take(data, position, 1, end)[0], position + 1
    elif kind == 'type':
        value, position = _take(data, position, 4, end).decode('mac_roman'), position + 4
    elif kind in ('comp', 'dutc'):
        value, position = struct.unpack('>Q', _take(data, position, 8, end))[0], position + 8
    elif kind == 'blob':
        size = _u32(data, position, end)
        value, position = bytes(_take(data, position + 4, size, end)), position + 4 + size
    elif kind == 'ustr':
        size = _u32(data, position, end)
        value = _take(data, position + 4, 2 * size, end).decode('utf-16-be', 'replace')
        position += 4 + 2 * size
    else:
        raise DSStoreError(f'record for {name!r} has data type {kind!r}, which this reader does not know')
    return (name, code, kind, value), position


def read_ds_store(data):
    """(records, declared record count) for the .DS_Store file held in data.

    records are (name, structure code, data type, value) tuples in the B-tree's order.
    The declared count is the one the file's own B-tree master block states; a caller
    comparing the two can tell a complete walk from a partial one.
    """
    addresses, contents = _allocator(data)
    if 'DSDB' not in contents:
        raise DSStoreError('no DSDB entry in the table of contents')
    start, end = _block(data, addresses, contents['DSDB'])
    root, _levels, declared = struct.unpack('>III', _take(data, start, 12, end))
    records = []
    seen = set()
    # (block number, None) walks a node; (None, record) emits a record already read.
    stack = [(root, None)]
    while stack:
        number, record = stack.pop()
        if record is not None:
            records.append(record)
            continue
        if number in seen or len(seen) >= _MAX_NODES:
            raise DSStoreError(f'node {number} is reached twice or the tree is too large')
        seen.add(number)
        start, end = _block(data, addresses, number)
        last, count = struct.unpack('>II', _take(data, start, 8, end))
        position = start + 8
        if last == 0:
            leaf = []
            for _ in range(count):
                entry, position = _record(data, position, end)
                leaf.append(entry)
            stack.extend((None, entry) for entry in reversed(leaf))
            continue
        # An internal node: count (child, record) pairs, then its rightmost child.
        pending = []
        for _ in range(count):
            child = _u32(data, position, end)
            entry, position = _record(data, position + 4, end)
            pending.append((child, None))
            pending.append((None, entry))
        pending.append((last, None))
        stack.extend(reversed(pending))
    return records, declared
