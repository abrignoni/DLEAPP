"""Replay of registry transaction logs onto a dirty hive, for DLEAPP.

Written from Maxim Suhanov's Windows registry file format specification,
https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md
(base block and its checksum, the new log format at #L679-L724, the dirty state of a hive at
#L728 and the use of two logs at #L747-L749). Marvin32, the hash that checks each log entry,
follows Microsoft's SymCrypt
(https://github.com/microsoft/SymCrypt/blob/286762b7730e2b780678f5ab11fef2b1bad639e0/lib/marvin32.c#L184-L190
and https://github.com/microsoft/SymCrypt/blob/286762b7730e2b780678f5ab11fef2b1bad639e0/lib/marvin32.c#L218-L286)
and reproduces the known answer at the end of that file.

Only the log format Windows 8.1 and later write (file type 6, entries signed HvLE) is replayed.
An older log (file type 1, a dirty vector signed DIRT) is reported and left alone, as is a hive
whose own base block fails its checksum. A dirty hive bin is written as the log holds it; the
specification describes replacing one that fails its checks with a dummy bin, which this does
not do.

One check goes beyond the specification. A key node keeps its cell for its whole life and its
last-written time only moves forward, so replaying logs newer than the hive can only move a
key's time forward. When the replay would give a key in a page it rewrites an earlier
last-written time than the hive already holds for that key (same cell, parent and name), the
logs are older than the hive and the replay is not used. The SYSTEM hive of
pc_mus_001_win11 had logs like that: applying them, as the specification's rules allow, set
three keys, one of them a BAM key, back by 14 to 15 minutes and moved no key forward.

Author: @AlexisBrignoni, Claude.
"""

import struct

_MASK = 0xFFFFFFFF
# The seed the specification gives for the Hash-1 and Hash-2 fields of a log entry, 82 EF 4D 88
# 7A 4E 55 C5, read as one hexadecimal number: its low 32 bits start the first register.
_SEED = 0x82EF4D887A4E55C5
_ENTRY_HEADER = 40
_SECTOR = 512
_PAGE = 4096


def _rotl(value, shift):
    return ((value << shift) | (value >> (32 - shift))) & _MASK


def _block(lo, hi):
    hi ^= lo
    lo = _rotl(lo, 20)
    lo = (lo + hi) & _MASK
    hi = _rotl(hi, 9)
    hi ^= lo
    lo = _rotl(lo, 27)
    lo = (lo + hi) & _MASK
    hi = _rotl(hi, 19)
    return lo, hi


def marvin32(data, seed=_SEED):
    """The 64-bit Marvin32 value of data: the two 32-bit halves before .NET collapses them."""
    lo, hi = seed & _MASK, seed >> 32
    whole = len(data) - len(data) % 4
    for (word,) in struct.iter_unpack('<I', data[:whole]):
        lo = (lo + word) & _MASK
        lo, hi = _block(lo, hi)
    tail = data[whole:]
    final = 0x80 << (8 * len(tail))
    for index, value in enumerate(tail):
        final |= value << (8 * index)
    lo = (lo + (final & _MASK)) & _MASK
    lo, hi = _block(lo, hi)
    lo, hi = _block(lo, hi)
    return (hi << 32) | lo


def xor32(block):
    """The base block checksum: XOR of the first 508 bytes as 32-bit words, 0 and -1 remapped."""
    value = 0
    for (word,) in struct.iter_unpack('<I', block[:508]):
        value ^= word
    if value == 0xFFFFFFFF:
        return 0xFFFFFFFE
    return 1 if value == 0 else value


def base_block(data):
    """The fields of a base block, or None when data does not begin with one."""
    if len(data) < _SECTOR or data[:4] != b'regf':
        return None
    primary, secondary = struct.unpack_from('<II', data, 4)
    return {'primary': primary, 'secondary': secondary,
            'file_type': struct.unpack_from('<I', data, 28)[0],
            'hive_bins_size': struct.unpack_from('<I', data, 40)[0],
            'flags': struct.unpack_from('<I', data, 144)[0],
            'checksum_ok': struct.unpack_from('<I', data, 508)[0] == xor32(data)}


def log_entries(data):
    """The log entries of a new-format log in file order, up to the first that fails a check."""
    entries = []
    offset = _SECTOR
    while offset + _ENTRY_HEADER <= len(data) and data[offset:offset + 4] == b'HvLE':
        size, flags, sequence, hive_bins_size, count = struct.unpack_from('<IIIII', data, offset + 4)
        hash1, hash2 = struct.unpack_from('<QQ', data, offset + 24)
        if (size < _ENTRY_HEADER or size % _SECTOR or offset + size > len(data)
                or hive_bins_size % _PAGE or _ENTRY_HEADER + 8 * count > size):
            break
        entry = data[offset:offset + size]
        if marvin32(entry[_ENTRY_HEADER:]) != hash1 or marvin32(entry[:32]) != hash2:
            break
        pages, position = [], _ENTRY_HEADER + 8 * count
        for index in range(count):
            page_offset, page_size = struct.unpack_from('<II', entry, _ENTRY_HEADER + 8 * index)
            pages.append((page_offset, entry[position:position + page_size]))
            position += page_size
        if position > size:
            break
        entries.append({'sequence': sequence, 'flags': flags, 'hive_bins_size': hive_bins_size,
                        'pages': pages})
        offset += size
    return entries


def _bins(data):
    """(start, end) of each hive bin, as offsets from the start of the hive bins data."""
    bins, offset, total = [], 0, len(data) - _PAGE
    while offset + 32 <= total and data[_PAGE + offset:_PAGE + offset + 4] == b'hbin':
        size = struct.unpack_from('<I', data, _PAGE + offset + 8)[0]
        if size < _PAGE or size % _PAGE or offset + size > total:
            break
        bins.append((offset, offset + size))
        offset += size
    return bins


def _key_times(data, pages):
    """{cell offset: (parent, name, last written)} for the key nodes that start in pages.

    pages holds page offsets from the start of the hive bins data. Cells are walked from the
    start of each bin that holds one of the pages, since a cell can begin before its page.
    """
    found = {}
    for start, end in _bins(data):
        if not any(start <= page < end for page in pages):
            continue
        cell = start + 32
        while cell + 4 <= end:
            size = struct.unpack_from('<i', data, _PAGE + cell)[0]
            if abs(size) < 8 or cell + abs(size) > end:
                break
            body = _PAGE + cell + 4
            if (size < 0 and cell - cell % _PAGE in pages and data[body:body + 2] == b'nk'
                    and abs(size) >= 4 + 76):
                stamp, = struct.unpack_from('<Q', data, body + 4)
                parent, = struct.unpack_from('<I', data, body + 16)
                length, = struct.unpack_from('<H', data, body + 72)
                found[cell] = (parent, bytes(data[body + 76:body + 76 + length]), stamp)
            cell += abs(size)
    return found


def _keys_set_back(primary, hive, pages):
    """How many key nodes in pages the replayed hive gives an earlier last-written time."""
    before, after = _key_times(primary, pages), _key_times(hive, pages)
    return sum(1 for cell, (parent, name, stamp) in after.items()
               if cell in before and before[cell][:2] == (parent, name) and stamp < before[cell][2])


def _chain(data, primary_secondary):
    """(first, entries) of a log that can be applied, following the specification's checks."""
    header = base_block(data)
    if header is None:
        return None, [], 'no base block'
    if header['file_type'] != 6:
        return None, [], f"file type {header['file_type']}, not the format this replay reads"
    if not header['checksum_ok'] or header['primary'] != header['secondary']:
        return None, [], 'base block not valid'
    entries = log_entries(data)
    if not entries or entries[0]['sequence'] != header['primary'] or header['primary'] < primary_secondary:
        return None, [], 'no subsequent log entries'
    chain = [entries[0]]
    for entry in entries[1:]:
        if entry['sequence'] != chain[-1]['sequence'] + 1:
            break
        chain.append(entry)
    return chain[0]['sequence'], chain, ''


def recover(primary, logs):
    """(hive bytes, summary) with the logs' subsequent entries applied when the hive is dirty.

    logs is a list of (name, bytes). The summary's state is 'clean', 'recovered',
    'dirty, not recovered' or 'not a hive'; applied lists (log name, first, last sequence).
    """
    summary = {'state': '', 'applied': [], 'entries': 0, 'pages': 0, 'reasons': {}}
    header = base_block(primary)
    if header is None or header['file_type'] != 0:
        summary['state'] = 'not a hive'
        return primary, summary
    if header['checksum_ok'] and header['primary'] == header['secondary']:
        summary['state'] = 'clean'
        return primary, summary
    if not header['checksum_ok']:
        summary['state'] = 'dirty, not recovered'
        summary['reasons']['hive'] = 'base block checksum wrong'
        return primary, summary
    chains = []
    for name, data in logs:
        first, chain, reason = _chain(data, header['secondary'])
        if chain:
            chains.append((first, name, chain))
        else:
            summary['reasons'][name] = reason
    chains.sort(key=lambda item: (item[0], item[1]))
    hive = bytearray(primary)
    applied, pages = [], set()
    for first, name, chain in chains:
        if applied and first != applied[-1]['sequence'] + 1:
            summary['reasons'][name] = 'does not continue the sequence of the log applied before it'
            continue
        for entry in chain:
            end = _PAGE + entry['hive_bins_size']
            if len(hive) < end:
                hive.extend(b'\x00' * (end - len(hive)))
            for page_offset, page in entry['pages']:
                start = _PAGE + page_offset
                if len(hive) < start + len(page):
                    hive.extend(b'\x00' * (start + len(page) - len(hive)))
                hive[start:start + len(page)] = page
                pages.update(range(page_offset - page_offset % _PAGE, page_offset + len(page), _PAGE))
            summary['pages'] += len(entry['pages'])
            applied.append(entry)
        summary['applied'].append((name, chain[0]['sequence'], chain[-1]['sequence']))
        summary['entries'] += len(chain)
    if not applied:
        summary['state'] = 'dirty, not recovered'
        return primary, summary
    set_back = _keys_set_back(primary, hive, pages)
    if set_back:
        sources = ' and '.join(name for name, _first, _last in summary['applied'])
        summary['reasons']['hive'] = (f"replaying {sources}, sequence {summary['applied'][0][1]} to "
                                      f"{summary['applied'][-1][2]}, would give {set_back} "
                                      f"{'key' if set_back == 1 else 'keys'} an earlier last-written "
                                      f"time than the hive holds")
        summary.update({'state': 'dirty, not recovered', 'applied': [], 'entries': 0, 'pages': 0})
        return primary, summary
    last = applied[-1]
    struct.pack_into('<II', hive, 4, last['sequence'], last['sequence'])
    struct.pack_into('<I', hive, 40, last['hive_bins_size'])
    flags = (header['flags'] & ~1) | (last['flags'] & 1)
    struct.pack_into('<I', hive, 144, flags)
    struct.pack_into('<I', hive, 508, xor32(hive))
    summary['state'] = 'recovered'
    return bytes(hive), summary
