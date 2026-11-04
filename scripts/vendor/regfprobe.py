#!/usr/bin/env python3
"""regfprobe: read Windows registry hive files (regf), offline and read-only.

One file, Python 3 standard library only. It reads a hive the way the format specification
describes it, replays the hive's transaction logs when the hive is dirty, and never writes to
the hive or its logs. It is meant to be copied verbatim into other tools (vendored), and it
also runs on its own:

    python3 regfprobe.py info HIVE
    python3 regfprobe.py ls HIVE [KEY]
    python3 regfprobe.py cat HIVE KEY [VALUE]
    python3 regfprobe.py find HIVE TEXT [--names | --data] [--regex]
    python3 regfprobe.py timeline HIVE [--out FILE]
    python3 regfprobe.py export HIVE [KEY] --format json|csv|reg [--out FILE]
    python3 regfprobe.py logs HIVE
    python3 regfprobe.py hives --image IMAGE          list the hives inside a disk image
    python3 regfprobe.py info --image IMAGE --path Windows/System32/config/SYSTEM

Sources. The layout is taken from Maxim Suhanov's "Windows registry file format specification",
https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md
(cited below as "spec"). The value type numbers are the REG_* constants of winnt.h, and the
security descriptor, SID and ACE layouts are those of Microsoft's [MS-DTYP] sections 2.4.2,
2.4.4 and 2.4.6. Marvin32, which checks each entry of a new-format transaction log, follows
Microsoft's SymCrypt (lib/marvin32.c at 286762b) and reproduces its known answer. No code is
taken from any other registry reader.

Author: @AlexisBrignoni, Claude. MIT licence.
"""

import argparse
import csv
import json
import os
import re
import struct
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

__version__ = '0.1.0'

__all__ = ['Hive', 'Key', 'Value', 'RegfError', 'KeyNotFound', 'ValueNotFound', 'open_hive',
           'find_logs', 'recover', 'filetime_to_datetime', 'REG_TYPES', 'CompatRegistry',
           'hives_in_image', 'read_from_image', 'extract_hives', 'export_key']

# ---------------------------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------------------------

_MASK = 0xFFFFFFFF
_PAGE = 4096          # base block size and hive bin alignment (spec, "Base block", "Hive bin")
_SECTOR = 512
_NO_CELL = 0xFFFFFFFF  # an offset field that points at nothing (spec)
_BIG_DATA_SEGMENT = 16344  # largest data a cell holds before big data is used (spec, "Big data")

REG_TYPES = {
    0: 'REG_NONE', 1: 'REG_SZ', 2: 'REG_EXPAND_SZ', 3: 'REG_BINARY', 4: 'REG_DWORD',
    5: 'REG_DWORD_BIG_ENDIAN', 6: 'REG_LINK', 7: 'REG_MULTI_SZ', 8: 'REG_RESOURCE_LIST',
    9: 'REG_FULL_RESOURCE_DESCRIPTOR', 10: 'REG_RESOURCE_REQUIREMENTS_LIST', 11: 'REG_QWORD',
}

# Key node flags (spec, "Key node", Flags).
KEY_FLAGS = {
    0x0001: 'KEY_VOLATILE', 0x0002: 'KEY_HIVE_EXIT', 0x0004: 'KEY_HIVE_ENTRY',
    0x0008: 'KEY_NO_DELETE', 0x0010: 'KEY_SYM_LINK', 0x0020: 'KEY_COMP_NAME',
    0x0040: 'KEY_PREDEF_HANDLE', 0x0080: 'KEY_VIRTUAL_SOURCE', 0x0100: 'KEY_VIRTUAL_TARGET',
    0x0200: 'KEY_VIRTUAL_STORE',
}
_KEY_COMP_NAME = 0x0020
# Key value flags (spec, "Key value", Flags).
_VALUE_COMP_NAME = 0x0001
_IS_TOMBSTONE = 0x0002

_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)

# Well-known SIDs, [MS-DTYP] 2.4.2.4. Shown as a label next to the SID, never in place of it.
WELL_KNOWN_SIDS = {
    'S-1-0-0': 'Nobody', 'S-1-1-0': 'Everyone', 'S-1-2-0': 'Local', 'S-1-3-0': 'Creator Owner',
    'S-1-3-1': 'Creator Group', 'S-1-5-7': 'Anonymous', 'S-1-5-11': 'Authenticated Users',
    'S-1-5-12': 'Restricted', 'S-1-5-18': 'Local System', 'S-1-5-19': 'Local Service',
    'S-1-5-20': 'Network Service', 'S-1-5-32-544': 'Administrators', 'S-1-5-32-545': 'Users',
    'S-1-5-32-546': 'Guests', 'S-1-5-32-547': 'Power Users', 'S-1-15-2-1': 'All App Packages',
}
# ACE types whose body is a mask followed by a SID, [MS-DTYP] 2.4.4.1 and 2.4.4.2.
ACE_TYPES = {0x00: 'ACCESS_ALLOWED', 0x01: 'ACCESS_DENIED', 0x02: 'SYSTEM_AUDIT',
             0x03: 'SYSTEM_ALARM', 0x11: 'SYSTEM_MANDATORY_LABEL'}


class RegfError(Exception):
    """The data is not a hive, or a structure the caller asked for cannot be read."""


class KeyNotFound(RegfError, KeyError):
    """No key at the path asked for."""


class ValueNotFound(RegfError, KeyError):
    """No value of the name asked for."""


def filetime_to_datetime(value):
    """A FILETIME (100 ns intervals since 1601-01-01 UTC) as an aware UTC datetime, or None.

    None for 0 and for a count past the end of what datetime can hold; the raw count is always
    kept beside it by the callers.
    """
    if not isinstance(value, int) or value <= 0:
        return None
    try:
        return _EPOCH_1601 + timedelta(microseconds=value // 10)
    except (OverflowError, ValueError):
        return None


def _iso(value):
    stamp = filetime_to_datetime(value)
    return stamp.strftime('%Y-%m-%d %H:%M:%S.%f') + 'Z' if stamp else ''


# ---------------------------------------------------------------------------------------------
# Transaction log replay, copied from DLEAPP's scripts/registry_recovery.py as of DLEAPP commit
# dc77aab (2026-10-29): the same functions, with the same results on the 14 dirty corpus hives
# measured. DLEAPP still carries its own copy.
# ---------------------------------------------------------------------------------------------

# The seed the specification gives for the Hash-1 and Hash-2 fields of a log entry, 82 EF 4D 88
# 7A 4E 55 C5, read as one hexadecimal number: its low 32 bits start the first register.
_SEED = 0x82EF4D887A4E55C5
_ENTRY_HEADER = 40


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
    for (word,) in struct.iter_unpack('<I', bytes(block[:508])):
        value ^= word
    if value == 0xFFFFFFFF:
        return 0xFFFFFFFE
    return 1 if value == 0 else value


def base_block(data):
    """The fields of a base block, or None when data does not begin with one."""
    if len(data) < _SECTOR or bytes(data[:4]) != b'regf':
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


def old_log_pages(data, timestamp):
    """(sequence, hive bins size, [(page offset, 512 bytes)], reason) of an old-format log.

    The pages are those its dirty vector marks, as offsets from the start of the hive bins data.
    The list is empty, with the reason, when the log is not one this replay applies: no valid
    base block, not file type 1, unequal sequence numbers, a last-written timestamp other than
    the hive's, no dirty vector, or fewer dirty pages than the vector marks.
    """
    header = base_block(data)
    if header is None:
        return None, 0, [], 'no base block'
    if header['file_type'] != 1:
        return None, 0, [], f"file type {header['file_type']}, not the older log format"
    if not header['checksum_ok'] or header['primary'] != header['secondary']:
        return None, 0, [], 'base block not valid'
    if data[12:20] != timestamp:
        return None, 0, [], "last-written timestamp is not the hive's"
    if data[_SECTOR:_SECTOR + 4] != b'DIRT':
        return None, 0, [], 'no dirty vector'
    size = header['hive_bins_size']
    if size % _PAGE:
        return None, 0, [], 'hive bins size not a multiple of 4096'
    bitmap = data[_SECTOR + 4:_SECTOR + 4 + size // _SECTOR // 8]
    start = _SECTOR + -(-(4 + len(bitmap)) // _SECTOR) * _SECTOR
    pages, position = [], start
    for index, byte in enumerate(bitmap):
        for bit in range(8):
            if byte >> bit & 1:
                if position + _SECTOR > len(data):
                    return None, 0, [], 'fewer dirty pages than its dirty vector marks'
                pages.append(((8 * index + bit) * _SECTOR, data[position:position + _SECTOR]))
                position += _SECTOR
    if not pages:
        return None, 0, [], 'no dirty pages'
    return header['primary'], size, pages, ''


def _bins_valid(data, pages):
    """Whether every hive bin up to the last one a page falls in has its signature, a valid size and its own offset."""
    wanted = {page - page % _PAGE for page, _bytes in pages}
    offset, total = 0, len(data) - _PAGE
    while wanted and offset < total:
        header = data[_PAGE + offset:_PAGE + offset + 32]
        if len(header) < 32 or header[:4] != b'hbin':
            return False
        own, size = struct.unpack_from('<II', header, 4)
        if own != offset or size < _PAGE or size % _PAGE or offset + size > total:
            return False
        wanted -= set(range(offset, offset + size, _PAGE))
        offset += size
    return not wanted


def _recover_old(primary, logs, summary):
    """(hive bytes or None) with the first applicable old-format log applied, filling summary."""
    timestamp = primary[12:20]
    for name, data in sorted(logs, key=lambda item: item[0].upper().endswith('.LOG2')):
        sequence, size, pages, reason = old_log_pages(data, timestamp)
        if not pages:
            if not reason.startswith('file type'):
                summary['reasons'][name] = reason
            continue
        hive = bytearray(primary)
        if len(hive) < _PAGE + size:
            hive.extend(b'\x00' * (_PAGE + size - len(hive)))
        for page_offset, page in pages:
            hive[_PAGE + page_offset:_PAGE + page_offset + _SECTOR] = page
        if not _bins_valid(hive, pages):
            summary['reasons'][name] = 'a hive bin up to the last dirty page fails its checks'
            continue
        struct.pack_into('<II', hive, 4, sequence, sequence)
        struct.pack_into('<I', hive, 40, size)
        struct.pack_into('<I', hive, 508, xor32(hive))
        summary['reasons'].pop(name, None)
        summary.update({'format': 'old', 'applied': [(name, sequence, sequence)], 'entries': 1,
                        'pages': len(pages)})
        return hive, {page - page % _PAGE for page, _bytes in pages}
    return None, set()


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
    format is 'old' when an older-format log was applied (its one sequence number given as both
    first and last, entries 1 and pages the 512-byte pages written), and 'new' otherwise.

    One check goes beyond the specification. A key node keeps its cell for its whole life and
    its last-written time only moves forward, so replaying logs newer than the hive can only
    move a key's time forward. When the replay would give a key in a page it rewrites an
    earlier last-written time than the hive already holds for that key (same cell, parent and
    name), the logs are older than the hive and the replay is not used.
    """
    summary = {'state': '', 'applied': [], 'entries': 0, 'pages': 0, 'reasons': {}, 'format': 'new'}
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
        old, pages = _recover_old(primary, logs, summary)
        if old is None:
            summary['state'] = 'dirty, not recovered'
            return primary, summary
        hive = old
    set_back = _keys_set_back(primary, hive, pages)
    if set_back:
        sources = ' and '.join(name for name, _first, _last in summary['applied'])
        summary['reasons']['hive'] = (f"replaying {sources}, sequence {summary['applied'][0][1]} to "
                                      f"{summary['applied'][-1][2]}, would give {set_back} "
                                      f"{'key' if set_back == 1 else 'keys'} an earlier last-written "
                                      f"time than the hive holds")
        summary.update({'state': 'dirty, not recovered', 'applied': [], 'entries': 0, 'pages': 0})
        summary['format'] = 'new'
        return primary, summary
    if summary.get('format') == 'old':
        summary['state'] = 'recovered'
        return bytes(hive), summary
    last = applied[-1]
    struct.pack_into('<II', hive, 4, last['sequence'], last['sequence'])
    struct.pack_into('<I', hive, 40, last['hive_bins_size'])
    flags = (header['flags'] & ~1) | (last['flags'] & 1)
    struct.pack_into('<I', hive, 144, flags)
    struct.pack_into('<I', hive, 508, xor32(hive))
    summary['state'] = 'recovered'
    return bytes(hive), summary


def summarise_recovery(summary):
    """One plain sentence describing what recover() did, for logs and the window's banner."""
    state = summary.get('state')
    if state == 'clean':
        return 'Clean hive: the base block sequence numbers match, no replay needed.'
    if state == 'not attempted':
        return 'Transaction logs were not replayed (replay turned off).'
    if state == 'recovered' and summary.get('format') == 'old':
        name, sequence, _last = summary['applied'][0]
        return (f"Dirty hive: wrote the {summary['pages']} dirty pages of {name}, a log in the "
                f"older format, sequence {sequence}.")
    if state == 'recovered':
        sources = ' and '.join(name for name, _f, _l in summary['applied'])
        return (f"Dirty hive: replayed {summary['entries']} log entries, sequence "
                f"{summary['applied'][0][1]} to {summary['applied'][-1][2]}, from {sources}.")
    if state == 'dirty, not recovered':
        reasons = '; '.join(f'{name}: {why}' for name, why in summary.get('reasons', {}).items())
        return f"Dirty hive read as it is ({reasons or 'no transaction log beside it'})."
    return f'Recovery state: {state}.'


_LOG_SUFFIXES = ('.LOG1', '.LOG2')


def find_logs(path):
    """The .LOG1 and .LOG2 files beside a hive file, matched on its name without case."""
    folder, name = os.path.split(os.fspath(path))
    wanted = {(name + suffix).upper() for suffix in _LOG_SUFFIXES}
    try:
        entries = sorted(os.listdir(folder or '.'))
    except OSError:
        return []
    return [os.path.join(folder, entry) for entry in entries
            if entry.upper() in wanted and os.path.isfile(os.path.join(folder, entry))]


# ---------------------------------------------------------------------------------------------
# The hive
# ---------------------------------------------------------------------------------------------

def _read_source(source):
    if isinstance(source, (bytes, bytearray, memoryview)):
        return bytes(source), None
    if hasattr(source, 'read'):
        try:
            source.seek(0)
        except (AttributeError, OSError, ValueError):
            pass
        return source.read(), getattr(source, 'name', None)
    path = os.fspath(source)
    with open(path, 'rb') as handle:
        return handle.read(), path


class Hive:
    """A registry hive, read into memory, its transaction logs replayed when it is dirty.

    source is a path, bytes, or any object with read() (a staged file, a file inside an image).
    logs is None to look for .LOG1 and .LOG2 beside a path, or a list of paths or (name, bytes)
    pairs. recover=False reads the primary file exactly as it is.

    Nothing here raises for a damaged cell. A cell that cannot be read loses that one key,
    value or list, and is counted in faults (by kind) and listed in fault_log, once per
    structure however many times it is read.
    """

    FAULT_LOG_LIMIT = 1000

    def __init__(self, source, logs=None, recover=True, name=None):  # pylint: disable=redefined-outer-name
        primary, path = _read_source(source)
        self.path = path
        self.name = name or (os.path.basename(path) if path else 'hive')
        header = base_block(primary)
        if header is None:
            raise RegfError('not a registry hive: no regf signature at offset 0')
        self.original = primary
        self.logs = []
        if recover:
            if logs is None and path:
                logs = find_logs(path)
            for item in logs or []:
                if isinstance(item, tuple):
                    self.logs.append((item[0], bytes(item[1])))
                else:
                    try:
                        with open(item, 'rb') as handle:
                            self.logs.append((os.path.basename(item), handle.read()))
                    except OSError:
                        continue
            data, self.recovery = globals()['recover'](primary, self.logs)
        else:
            data, self.recovery = primary, {'state': 'not attempted', 'applied': [], 'entries': 0,
                                            'pages': 0, 'reasons': {}, 'format': ''}
        self.data = bytes(data)
        self._view = memoryview(self.data)
        self.faults = Counter()
        self.fault_log = []
        self._fault_seen = set()
        self._parse_base_block()

    # -- base block ------------------------------------------------------------------------

    def _parse_base_block(self):
        d = self.data
        primary, secondary, stamp, major, minor, file_type, file_format, root, bins_size, \
            clustering = struct.unpack_from('<IIQIIIIIII', d, 4)
        raw_name = d[48:48 + 64]
        self.header = {
            'primary_sequence': primary, 'secondary_sequence': secondary,
            'last_written': stamp, 'major_version': major, 'minor_version': minor,
            'file_type': file_type, 'file_format': file_format, 'root_cell_offset': root,
            'hive_bins_size': bins_size, 'clustering_factor': clustering,
            'file_name': _utf16_until_nul(raw_name), 'flags': struct.unpack_from('<I', d, 144)[0],
            'checksum': struct.unpack_from('<I', d, 508)[0],
            'checksum_ok': struct.unpack_from('<I', d, 508)[0] == xor32(d),
        }
        if len(d) >= 4048:
            self.header['boot_type'], self.header['boot_recover'] = struct.unpack_from('<II', d, 4040)
        self.version = f'{major}.{minor}'
        self.minor_version = minor
        self.root_offset = root

    @property
    def was_dirty(self):
        """Whether the primary file, before any replay, had unequal sequence numbers."""
        return struct.unpack_from('<I', self.original, 4)[0] != struct.unpack_from('<I', self.original, 8)[0]

    @property
    def last_written(self):
        return filetime_to_datetime(self.header['last_written'])

    def bins(self):
        """[(offset, size, timestamp)] of the hive bins, up to the first one that fails its checks."""
        result, offset = [], 0
        total = min(self.header['hive_bins_size'], len(self.data) - _PAGE)
        while offset + 32 <= total:
            pos = _PAGE + offset
            if self.data[pos:pos + 4] != b'hbin':
                break
            own, size = struct.unpack_from('<II', self.data, pos + 4)
            stamp = struct.unpack_from('<Q', self.data, pos + 20)[0]
            if size < _PAGE or size % _PAGE or offset + size > total:
                break
            result.append((offset, size, stamp))
            offset += size
            del own
        return result

    # -- cells ------------------------------------------------------------------------------

    def fault(self, kind, offset, reason):
        """Count a damaged structure once, however often it is read, and keep its description
        (up to FAULT_LOG_LIMIT of them)."""
        if (kind, offset) in self._fault_seen:
            return
        self._fault_seen.add((kind, offset))
        self.faults[kind] += 1
        if len(self.fault_log) < self.FAULT_LOG_LIMIT:
            self.fault_log.append((kind, offset, reason))

    def cell(self, offset):
        """The data of the cell at offset (from the start of the hive bins data), as a memoryview.

        Raises RegfError when the offset points outside the file or the cell's size does not fit.
        """
        if offset == _NO_CELL or offset % 8:
            raise RegfError(f'cell offset 0x{offset:x} is not a cell')
        pos = _PAGE + offset
        if pos + 4 > len(self.data):
            raise RegfError(f'cell offset 0x{offset:x} is past the end of the file')
        size = struct.unpack_from('<i', self.data, pos)[0]
        length = -size if size < 0 else size
        if length < 8 or pos + length > len(self.data):
            raise RegfError(f'cell at 0x{offset:x} has an impossible size {size}')
        return self._view[pos + 4:pos + length]

    # -- keys -------------------------------------------------------------------------------

    def root(self):
        """The root key."""
        return Key(self, self.root_offset, '', None)

    def open_key(self, path):
        """The key at path (backslash or slash separated, without the root key's name).

        Names compare without case. Raises KeyNotFound.
        """
        key = self.root()
        for part in re.split(r'[\\/]+', path or ''):
            if part:
                key = key.subkey(part)
        return key

    def walk(self, start=None):
        """Every key under start (default the root), start included, depth first in stored order.

        A key reached twice (a damaged list pointing back up the tree) is visited once and
        counted as a fault.
        """
        first = start or self.root()
        seen = set()
        stack = [first]
        while stack:
            key = stack.pop()
            if key.offset in seen:
                self.fault('cycle', key.offset, f'key at 0x{key.offset:x} reached twice')
                continue
            seen.add(key.offset)
            yield key
            stack.extend(reversed(key.subkeys()))

    def __repr__(self):
        return f'<Hive {self.name} v{self.version} {self.recovery.get("state")}>'


def _utf16_until_nul(raw):
    raw = bytes(raw)
    text = raw[:len(raw) - len(raw) % 2].decode('utf-16-le', errors='replace')
    return text.split('\x00', 1)[0]


def _decode_name(raw, compressed):
    """A key or value name. A compressed name holds one byte per character (spec: "ASCII");
    Latin-1 maps each byte to the same code point, so bytes 0x80 to 0xFF survive unchanged."""
    raw = bytes(raw)
    if compressed:
        return raw.decode('latin-1')
    return raw[:len(raw) - len(raw) % 2].decode('utf-16-le', errors='replace')


class Key:
    """A key node (nk). Fields are read when the key is made; lists when they are asked for."""

    __slots__ = ('hive', 'offset', 'parent_path', 'parent', 'name', 'raw_name', 'flags',
                 'last_written_raw', 'access_bits', 'parent_offset', 'subkey_count',
                 'subkeys_offset', 'value_count', 'values_offset', 'security_offset',
                 'class_offset', 'class_length', 'spare', 'allocated', '_subkeys', '_values')

    def __init__(self, hive, offset, parent_path, parent):
        self.hive = hive
        self.offset = offset
        self.parent_path = parent_path
        self.parent = parent
        self._subkeys = None
        self._values = None
        data = hive.cell(offset)
        if len(data) < 76 or bytes(data[:2]) != b'nk':
            raise RegfError(f'cell at 0x{offset:x} is not a key node')
        self.allocated = struct.unpack_from('<i', hive.data, _PAGE + offset)[0] < 0
        (self.flags, self.last_written_raw, self.access_bits, self.parent_offset,
         self.subkey_count, _volatile_count, self.subkeys_offset, _volatile_offset,
         self.value_count, self.values_offset, self.security_offset, self.class_offset,
         self.spare) = struct.unpack_from('<HQIIIIIIIIIII', data, 2)
        name_length, self.class_length = struct.unpack_from('<HH', data, 72)
        self.raw_name = bytes(data[76:76 + name_length])
        if len(self.raw_name) < name_length:
            hive.fault('nk', offset, 'key name runs past its cell')
        self.name = _decode_name(self.raw_name, self.flags & _KEY_COMP_NAME)

    @property
    def path(self):
        """The key's path below the root, backslash separated; '' for the root."""
        if self.parent is None:
            return ''
        return f'{self.parent_path}\\{self.name}' if self.parent_path else self.name

    @property
    def last_written(self):
        return filetime_to_datetime(self.last_written_raw)

    @property
    def flag_names(self):
        return [label for bit, label in KEY_FLAGS.items() if self.flags & bit]

    @property
    def class_name(self):
        """The key's class name, or '' when it has none."""
        if not self.class_length or self.class_offset == _NO_CELL:
            return ''
        try:
            data = self.hive.cell(self.class_offset)
        except RegfError as error:
            self.hive.fault('class', self.class_offset, str(error))
            return ''
        return _decode_name(data[:self.class_length], False)

    # -- subkeys ----------------------------------------------------------------------------

    def _list_offsets(self, offset, depth=0):
        """The key node offsets an index (li, lf, lh, or ri over those) holds."""
        data = self.hive.cell(offset)
        signature = bytes(data[:2])
        count = struct.unpack_from('<H', data, 2)[0]
        if signature in (b'lf', b'lh'):
            if 4 + 8 * count > len(data):
                self.hive.fault('index', offset, f'{signature.decode()} list of {count} runs past its cell')
                count = (len(data) - 4) // 8
            return [struct.unpack_from('<I', data, 4 + 8 * i)[0] for i in range(count)]
        if signature in (b'li', b'ri'):
            if 4 + 4 * count > len(data):
                self.hive.fault('index', offset, f'{signature.decode()} list of {count} runs past its cell')
                count = (len(data) - 4) // 4
            offsets = [struct.unpack_from('<I', data, 4 + 4 * i)[0] for i in range(count)]
            if signature == b'li':
                return offsets
            if depth > 2:
                self.hive.fault('index', offset, 'index root nested too deep')
                return []
            result = []
            for child in offsets:
                try:
                    result.extend(self._list_offsets(child, depth + 1))
                except RegfError as error:
                    self.hive.fault('index', child, str(error))
            return result
        raise RegfError(f'cell at 0x{offset:x} is not a subkeys list ({signature!r})')

    def subkeys(self):
        """The subkeys, in stored order. A subkey whose cell cannot be read is skipped and counted."""
        if self._subkeys is not None:
            return self._subkeys
        result = []
        if self.subkey_count and self.subkeys_offset != _NO_CELL:
            try:
                offsets = self._list_offsets(self.subkeys_offset)
            except RegfError as error:
                self.hive.fault('index', self.subkeys_offset, str(error))
                offsets = []
            if len(offsets) != self.subkey_count:
                self.hive.fault('count', self.offset,
                                f'{self.path or "(root)"}: {self.subkey_count} subkeys recorded, '
                                f'{len(offsets)} listed')
            for child in offsets:
                try:
                    result.append(Key(self.hive, child, self.path, self))
                except RegfError as error:
                    self.hive.fault('nk', child, str(error))
        self._subkeys = result
        return result

    def subkey(self, name):
        """The subkey of that name, compared without case. Raises KeyNotFound."""
        wanted = name.upper()
        for key in self.subkeys():
            if key.name.upper() == wanted:
                return key
        where = f'{self.path}\\{name}' if self.path else name
        raise KeyNotFound(where)

    # -- values -----------------------------------------------------------------------------

    def values(self):
        """The values, in stored order. A value whose cell cannot be read is skipped and counted."""
        if self._values is not None:
            return self._values
        result = []
        if self.value_count and self.values_offset != _NO_CELL:
            try:
                data = self.hive.cell(self.values_offset)
                count = self.value_count
                if 4 * count > len(data):
                    self.hive.fault('values', self.values_offset,
                                    f'value list of {count} runs past its cell')
                    count = len(data) // 4
                offsets = [struct.unpack_from('<I', data, 4 * i)[0] for i in range(count)]
            except RegfError as error:
                self.hive.fault('values', self.values_offset, str(error))
                offsets = []
            for child in offsets:
                try:
                    result.append(Value(self, child))
                except RegfError as error:
                    self.hive.fault('vk', child, str(error))
        self._values = result
        return result

    def value(self, name):
        """The value of that name ('' or None for the default value), without case. Raises ValueNotFound."""
        wanted = (name or '').upper()
        for value in self.values():
            if value.name.upper() == wanted:
                return value
        raise ValueNotFound(f'{self.path or "(root)"} : {name or "(default)"}')

    def get(self, name, default=None):
        """The decoded data of a value, or default when it is absent."""
        try:
            return self.value(name).data
        except ValueNotFound:
            return default

    # -- security ---------------------------------------------------------------------------

    def security(self):
        """The key's security record (sk), parsed, or None when it cannot be read."""
        if self.security_offset == _NO_CELL:
            return None
        try:
            data = self.hive.cell(self.security_offset)
        except RegfError as error:
            self.hive.fault('sk', self.security_offset, str(error))
            return None
        if len(data) < 20 or bytes(data[:2]) != b'sk':
            self.hive.fault('sk', self.security_offset, 'not a key security record')
            return None
        _reserved, flink, blink, references, size = struct.unpack_from('<HIIII', data, 2)
        descriptor = bytes(data[20:20 + size])
        result = {'offset': self.security_offset, 'flink': flink, 'blink': blink,
                  'references': references, 'descriptor': descriptor}
        result.update(parse_security_descriptor(descriptor))
        return result

    def __repr__(self):
        return f'<Key {self.path or "(root)"} @0x{self.offset:x}>'


class Value:
    """A key value (vk). raw is the data as stored; data is it decoded by type; notes say what
    about the stored bytes did not fit the type (they never stop the value from being read)."""

    __slots__ = ('key', 'offset', 'name', 'raw_name', 'type', 'flags', 'size_field',
                 'data_offset', 'size', 'resident', '_big', 'notes', '_raw', '_data')

    def __init__(self, key, offset):
        hive = key.hive
        self.key = key
        self.offset = offset
        data = hive.cell(offset)
        if len(data) < 20 or bytes(data[:2]) != b'vk':
            raise RegfError(f'cell at 0x{offset:x} is not a key value')
        name_length, self.size_field, self.data_offset, self.type, self.flags = \
            struct.unpack_from('<HIIIH', data, 2)
        self.raw_name = bytes(data[20:20 + name_length])
        self.name = _decode_name(self.raw_name, self.flags & _VALUE_COMP_NAME)
        self.resident = bool(self.size_field & 0x80000000)
        self.size = self.size_field & 0x7FFFFFFF
        self._big = False
        self.notes = []
        self._raw = None
        self._data = None

    @property
    def type_name(self):
        return REG_TYPES.get(self.type, f'unknown type 0x{self.type:x}')

    @property
    def is_default(self):
        return self.name == ''

    @property
    def tombstone(self):
        return bool(self.flags & _IS_TOMBSTONE)

    @property
    def big_data(self):
        """Whether the data is stored as big data (a db record over segments)."""
        _ = self.raw
        return self._big

    @property
    def raw(self):
        """The value's data bytes as stored (empty when they cannot be read; see notes)."""
        if self._raw is None:
            self._raw = self._read_raw()
        return self._raw

    def _read_raw(self):
        hive = self.key.hive
        if self.resident:
            # spec: the data is in the data offset field itself, up to four bytes
            if self.size > 4:
                self.notes.append(f'resident data size {self.size} is more than the four bytes it can hold')
            return struct.pack('<I', self.data_offset)[:min(self.size, 4)]
        if self.size == 0:
            return b''
        try:
            cell = hive.cell(self.data_offset)
        except RegfError as error:
            hive.fault('data', self.data_offset, str(error))
            self.notes.append(f'data cell unreadable: {error}')
            return b''
        if (self.size > _BIG_DATA_SEGMENT and hive.minor_version > 3 and len(cell) >= 8
                and bytes(cell[:2]) == b'db'):
            self._big = True
            return self._read_big(cell)
        if len(cell) < self.size:
            self.notes.append(f'truncated: the data cell holds {len(cell)} of {self.size} bytes')
        return bytes(cell[:self.size])

    def _read_big(self, cell):
        """Data split over segments (spec, "Big data"): each segment but the last holds 16344 bytes."""
        hive = self.key.hive
        count, list_offset = struct.unpack_from('<HI', cell, 2)
        try:
            listing = hive.cell(list_offset)
        except RegfError as error:
            hive.fault('db', list_offset, str(error))
            self.notes.append(f'big data segment list unreadable: {error}')
            return b''
        if 4 * count > len(listing):
            self.notes.append('big data segment list runs past its cell')
            count = len(listing) // 4
        parts, remaining = [], self.size
        for index in range(count):
            if remaining <= 0:
                break
            segment_offset = struct.unpack_from('<I', listing, 4 * index)[0]
            try:
                segment = hive.cell(segment_offset)
            except RegfError as error:
                hive.fault('db', segment_offset, str(error))
                self.notes.append(f'big data segment {index} unreadable: {error}')
                break
            take = min(remaining, _BIG_DATA_SEGMENT, len(segment))
            parts.append(bytes(segment[:take]))
            remaining -= take
        data = b''.join(parts)
        if len(data) < self.size:
            self.notes.append(f'truncated: big data segments hold {len(data)} of {self.size} bytes')
        return data

    @property
    def data(self):
        """The data decoded by its type: str, list of str, int, or bytes when the type is not a
        text or number type or the bytes do not fit it."""
        if self._data is None:
            self._data = self._decode()
        return self._data

    def _decode(self):
        raw = self.raw
        kind = self.type
        if kind in (1, 2, 6):
            text = self._text(raw)
            if kind == 6:
                return text
            head, sep, tail = text.partition('\x00')
            if not sep and raw:
                self.notes.append('no terminating NUL')
            elif tail.strip('\x00'):
                self.notes.append('data after the terminating NUL')
            return head
        if kind == 7:
            text = self._text(raw).rstrip('\x00')
            items = text.split('\x00') if text else []
            if '' in items:
                self.notes.append('an empty string inside the list')
            return items
        if kind in (4, 5):
            if len(raw) < 4:
                if raw or self.size:
                    self.notes.append(f'{len(raw)} bytes, fewer than the four a DWORD needs')
                return raw
            if len(raw) > 4:
                self.notes.append(f'{len(raw)} bytes, more than the four a DWORD holds')
            return struct.unpack_from('<I' if kind == 4 else '>I', raw)[0]
        if kind == 11:
            if len(raw) < 8:
                self.notes.append(f'{len(raw)} bytes, fewer than the eight a QWORD needs')
                return raw
            if len(raw) > 8:
                self.notes.append(f'{len(raw)} bytes, more than the eight a QWORD holds')
            return struct.unpack_from('<Q', raw)[0]
        return raw

    def _text(self, raw):
        if len(raw) % 2:
            self.notes.append('odd length: the last byte is not part of the text')
            raw = raw[:-1]
        try:
            return raw.decode('utf-16-le')
        except UnicodeDecodeError:
            self.notes.append('not valid UTF-16LE: unpaired surrogates replaced')
            return raw.decode('utf-16-le', errors='replace')

    def data_text(self):
        """The decoded data as one line of text, for listings and CSV."""
        data = self.data
        if isinstance(data, list):
            return json.dumps(data, ensure_ascii=False)
        if isinstance(data, (bytes, bytearray)):
            return data.hex(' ')
        return str(data)

    def __repr__(self):
        return f'<Value {self.name or "(default)"} {self.type_name} {self.size} bytes>'


# ---------------------------------------------------------------------------------------------
# Security descriptors ([MS-DTYP] 2.4.6 self-relative form, 2.4.5 ACL, 2.4.4 ACE, 2.4.2 SID)
# ---------------------------------------------------------------------------------------------

def parse_sid(data, offset=0):
    """(SID string, length in bytes) of the SID at offset, or (None, 0)."""
    if offset + 8 > len(data):
        return None, 0
    revision, count = data[offset], data[offset + 1]
    if offset + 8 + 4 * count > len(data):
        return None, 0
    authority = int.from_bytes(data[offset + 2:offset + 8], 'big')
    subs = struct.unpack_from(f'<{count}I', data, offset + 8)
    return 'S-%d-%d' % (revision, authority) + ''.join(f'-{s}' for s in subs), 8 + 4 * count


def _parse_acl(data, offset):
    if offset == 0 or offset + 8 > len(data):
        return None
    _revision, _sbz, size, count = struct.unpack_from('<BBHH', data, offset)
    aces, position, end = [], offset + 8, min(offset + size, len(data))
    for _ in range(count):
        if position + 4 > end:
            break
        ace_type, ace_flags, ace_size = struct.unpack_from('<BBH', data, position)
        if ace_size < 4 or position + ace_size > end:
            break
        ace = {'type': ace_type, 'type_name': ACE_TYPES.get(ace_type, f'type 0x{ace_type:02x}'),
               'flags': ace_flags}
        if ace_type in ACE_TYPES and ace_size >= 16:
            ace['mask'] = struct.unpack_from('<I', data, position + 4)[0]
            ace['sid'] = parse_sid(data[:position + ace_size], position + 8)[0]
        else:
            ace['raw'] = bytes(data[position + 4:position + ace_size])
        aces.append(ace)
        position += ace_size
    return aces


def parse_security_descriptor(data):
    """Owner, group, control and the DACL and SACL entries of a self-relative descriptor."""
    if len(data) < 20:
        return {}
    _revision, _sbz, control, owner, group, sacl, dacl = struct.unpack_from('<BBHIIII', data, 0)
    return {'control': control,
            'owner': parse_sid(data, owner)[0] if owner else None,
            'group': parse_sid(data, group)[0] if group else None,
            'dacl': _parse_acl(data, dacl) if control & 0x0004 else None,
            'sacl': _parse_acl(data, sacl) if control & 0x0010 else None}


# ---------------------------------------------------------------------------------------------
# Opening
# ---------------------------------------------------------------------------------------------

def open_hive(source, logs=None, recover=True, name=None):  # pylint: disable=redefined-outer-name
    """A Hive. See Hive for the arguments."""
    return Hive(source, logs=logs, recover=recover, name=name)


# ---------------------------------------------------------------------------------------------
# Disk images, through qnxprobe and ewfprobe when they sit beside this file or are importable
# ---------------------------------------------------------------------------------------------

_HIVE_NAMES = {'SYSTEM', 'SOFTWARE', 'SAM', 'SECURITY', 'DEFAULT', 'COMPONENTS', 'DRIVERS',
               'BCD-TEMPLATE', 'ELAM', 'USERDIFF', 'NTUSER.DAT', 'USRCLASS.DAT', 'AMCACHE.HVE',
               'SYSCACHE.HVE', 'SETTINGS.DAT', 'BBI', 'BCD', 'USER.DAT', 'USERCLASSES.DAT'}


def _qnxprobe():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import qnxprobe  # pylint: disable=import-outside-toplevel
    except ImportError as error:
        raise RegfError('reading a disk image needs qnxprobe.py (and ewfprobe.py for E01) beside '
                        'regfprobe.py: https://github.com/abrignoni/qnxprobe') from error
    return qnxprobe


def _is_hive_name(path):
    base = path.replace('\\', '/').rsplit('/', 1)[-1].upper()
    return base in _HIVE_NAMES or base.endswith('.HVE')


def _walk_image(image, wanted, password=None, cancel=None):
    """(volume name, path, walker, node, size) for each file in the image that wanted(path) accepts.

    cancel, when given, is called between files; when it returns true the walk stops with
    RegfError('cancelled').
    """
    qnx = _qnxprobe()
    handle = qnx.open_image(image, password=password)
    s_ifmt, s_ifdir = 0o170000, 0o040000
    for volume in qnx.volumes(handle):
        walker = volume.get('walker')
        if walker is None:
            continue
        label = volume.get('name') or ('lba%d' % volume.get('lba', 0))
        for entry in qnx.walk_all(walker):
            if cancel is not None and cancel():
                raise RegfError('cancelled')
            path, node, mode, size = entry[0], entry[1], entry[2], entry[3]
            if (mode & s_ifmt) == s_ifdir or not wanted(path):
                continue
            yield label, path, walker, node, size


def _read_node(walker, node, size):
    data = walker.read_file(node, size)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return b''.join(bytes(chunk) for chunk in data if chunk)


def hives_in_image(image, password=None, cancel=None):
    """[(volume, path, size)] of the files in a disk image named like a hive.

    By name only (SYSTEM, NTUSER.DAT, *.hve and the like): a hive under another name is not
    listed, and a listed file is confirmed a hive only when it is opened.
    """
    return [(label, path, size) for label, path, _w, _n, size in
            _walk_image(image, _is_hive_name, password, cancel)]


def read_from_image(image, hive_path, password=None, recover=True, volume=None,  # pylint: disable=redefined-outer-name
                    cancel=None):
    """A Hive read from inside a disk image, with the .LOG1 and .LOG2 beside it in the same volume.

    volume is the label `hives` prints (p2_lba206848 and the like). It may be left out when only
    one volume holds a file at hive_path; when several do, RegfError names them.
    """
    wanted = hive_path.replace('\\', '/').strip('/').upper()
    names = {wanted, wanted + '.LOG1', wanted + '.LOG2'}
    found = {}
    for label, path, walker, node, size in _walk_image(
            image, lambda p: p.replace('\\', '/').strip('/').upper() in names, password, cancel):
        if volume is not None and label != volume:
            continue
        key = path.replace('\\', '/').strip('/').upper()
        found.setdefault(label, {}).setdefault(key, (path, _read_node(walker, node, size)))
    holding = sorted(label for label, files in found.items() if wanted in files)
    if not holding:
        where = f' in volume {volume}' if volume else ''
        raise RegfError(f'no file at {hive_path}{where} in {image}')
    if len(holding) > 1:
        raise RegfError(f'{hive_path} is in more than one volume ({", ".join(holding)}); '
                        f'name one with --volume')
    label = holding[0]
    files = found[label]
    path, data = files.pop(wanted)
    logs = [(item[0].replace('\\', '/').rsplit('/', 1)[-1], item[1]) for item in files.values()]
    hive = Hive(data, logs=logs, recover=recover, name=path.replace('\\', '/').rsplit('/', 1)[-1])
    hive.path = f'{image}::{label}/{path}'
    return hive


# ---------------------------------------------------------------------------------------------
# A python-registry shaped view, so code written against python-registry can switch by import.
# Return types follow python-registry 1.3.1: naive UTC datetimes, "(default)" for the default
# value's name, paths that begin with the root key's name. The decoded data is regfprobe's own;
# where it differs from python-registry for the same bytes is measured, not assumed.
# ---------------------------------------------------------------------------------------------

class RegistryKeyNotFoundException(KeyNotFound):
    pass


class RegistryValueNotFoundException(ValueNotFound):
    pass


_COMPAT_TYPE_NAMES = {0: 'RegNone', 1: 'RegSZ', 2: 'RegExpandSZ', 3: 'RegBin', 4: 'RegDWord',
                      5: 'RegBigEndian', 6: 'RegLink', 7: 'RegMultiSZ', 8: 'RegResourceList',
                      9: 'RegFullResourceDescriptor', 10: 'RegResourceRequirementsList',
                      11: 'RegQWord'}


class CompatValue:
    def __init__(self, value):
        self._value = value

    def name(self):
        return self._value.name or '(default)'

    def value_type(self):
        return self._value.type

    def value_type_str(self):
        return _COMPAT_TYPE_NAMES.get(self._value.type, 'Unknown type: %s' % hex(self._value.type))

    def value(self):
        """The decoded data. A REG_MULTI_SZ is the whole text split at every NUL, trailing empty
        strings kept, the list shape python-registry 1.3.1 returns; everything else is Value.data."""
        if self._value.type == 7:
            raw = self._value.raw
            raw = raw[:len(raw) - len(raw) % 2]
            return raw.decode('utf-16-le', errors='replace').split('\x00')
        if self._value.type == 6:
            return self._value.raw
        return self._value.data

    def raw_data(self):
        return self._value.raw


class CompatKey:
    def __init__(self, key):
        self._key = key

    def name(self):
        return self._key.name

    def path(self):
        root = self._key.hive.root().name
        return f'{root}\\{self._key.path}' if self._key.path else root

    def timestamp(self):
        """Naive UTC datetime, the FILETIME rounded half-even to the microsecond as python-registry
        1.3.1 rounds it (Key.last_written truncates instead)."""
        whole, rest = divmod(self._key.last_written_raw, 10)
        if rest > 5 or (rest == 5 and whole % 2):
            whole += 1
        try:
            return datetime(1601, 1, 1) + timedelta(microseconds=whole)
        except OverflowError:
            return None

    def subkeys(self):
        return [CompatKey(k) for k in self._key.subkeys()]

    def subkey(self, name):
        try:
            return CompatKey(self._key.subkey(name))
        except KeyNotFound as error:
            raise RegistryKeyNotFoundException(str(error)) from None

    def values(self):
        return [CompatValue(v) for v in self._key.values()]

    def value(self, name):
        try:
            return CompatValue(self._key.value('' if name == '(default)' else name))
        except ValueNotFound as error:
            raise RegistryValueNotFoundException(str(error)) from None

    def __getitem__(self, name):
        return self.value(name)

    def find_key(self, path):
        key = self
        for part in path.split('\\'):
            if part:
                key = key.subkey(part)
        return key

    def values_number(self):
        return self._key.value_count

    def subkeys_number(self):
        return self._key.subkey_count

    def parent(self):
        if self._key.parent is None:
            raise RegistryKeyNotFoundException(self._key.name)
        return CompatKey(self._key.parent)


class CompatRegistry:
    """Answers the python-registry calls Registry.Registry(...) callers make."""

    RegistryKeyNotFoundException = RegistryKeyNotFoundException
    RegistryValueNotFoundException = RegistryValueNotFoundException

    def __init__(self, source, logs=None, recover=True):  # pylint: disable=redefined-outer-name
        self.hive = source if isinstance(source, Hive) else Hive(source, logs=logs, recover=recover)

    def root(self):
        return CompatKey(self.hive.root())

    def open(self, path):
        return self.root().find_key(path)

    def hive_name(self):
        return self.hive.header['file_name']


# ---------------------------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------------------------

def _open_from_args(args):
    if getattr(args, 'image', None):
        if not args.path:
            raise RegfError('--image needs --path, the hive\'s path inside the image '
                            '(list them with: regfprobe.py hives --image IMAGE)')
        return read_from_image(args.image, args.path, password=args.password,
                               recover=not args.no_recover, volume=args.volume)
    if not args.hive:
        raise RegfError('give a hive file, or --image and --path')
    return Hive(args.hive, recover=not args.no_recover)


def _out(args):
    if getattr(args, 'out', None):
        return open(args.out, 'w', encoding='utf-8', newline='')
    return sys.stdout


def _print_faults(hive, stream=sys.stdout):
    if hive.faults:
        parts = ', '.join(f'{kind} {count}' for kind, count in sorted(hive.faults.items()))
        print(f'Damaged structures skipped: {parts}', file=stream)


def cmd_info(args):
    hive = _open_from_args(args)
    h = hive.header
    root = hive.root()
    print(f'File:              {hive.path or hive.name}')
    print(f'Format version:    {hive.version}')
    print(f'Embedded name:     {h["file_name"]}')
    print(f'Root key:          {root.name}')
    print(f'Last written:      {_iso(h["last_written"])} (base block)')
    print(f'Sequence numbers:  {struct.unpack_from("<I", hive.original, 4)[0]} / '
          f'{struct.unpack_from("<I", hive.original, 8)[0]} (as stored)')
    print(f'Base block sum:    {"ok" if base_block(hive.original)["checksum_ok"] else "WRONG"}')
    print(f'Hive bins size:    {h["hive_bins_size"]} bytes, {len(hive.bins())} bins')
    print(f'Transaction logs:  {", ".join(n for n, _d in hive.logs) or "none found"}')
    print(f'Recovery:          {summarise_recovery(hive.recovery)}')
    keys = values = 0
    for key in hive.walk():
        keys += 1
        values += len(key.values())
    print(f'Keys / values:     {keys} / {values}')
    _print_faults(hive)
    return 0


def cmd_ls(args):
    hive = _open_from_args(args)
    key = hive.open_key(args.key or '')
    print(f'[{key.path or "(root) " + key.name}]  last written {_iso(key.last_written_raw)}')
    for sub in key.subkeys():
        print(f'  {_iso(sub.last_written_raw):27}  {sub.name}\\')
    for value in key.values():
        text = value.data_text()
        if len(text) > 100:
            text = text[:97] + '...'
        note = f'  [{"; ".join(value.notes)}]' if value.notes else ''
        print(f'  {value.type_name:20} {value.name or "(default)"} = {text}{note}')
    _print_faults(hive, sys.stderr)
    return 0


def _hexdump(data, width=16):
    lines = []
    for start in range(0, len(data), width):
        chunk = data[start:start + width]
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{start:08x}  {chunk.hex(" "):<{width * 3}} {text}')
    return '\n'.join(lines)


def cmd_cat(args):
    hive = _open_from_args(args)
    key = hive.open_key(args.key)
    values = [key.value(args.value)] if args.value is not None else key.values()
    for value in values:
        print(f'{value.name or "(default)"}  {value.type_name}  {value.size} bytes'
              f'{"  (big data)" if value.big_data else ""}')
        data = value.data
        if isinstance(data, list):
            for item in data:
                print(f'  {item}')
        elif not isinstance(data, (bytes, bytearray)):
            print(f'  {data}')
        if value.notes:
            print(f'  notes: {"; ".join(value.notes)}')
        print(_hexdump(value.raw))
        print()
    return 0


def _matches(args):
    if args.regex:
        pattern = re.compile(args.text, re.IGNORECASE)
        return lambda s: bool(s) and pattern.search(s) is not None
    needle = args.text.casefold()
    return lambda s: bool(s) and needle in s.casefold()


def cmd_find(args):
    hive = _open_from_args(args)
    match = _matches(args)
    names = not args.data
    data = not args.names
    hits = 0
    for key in hive.walk():
        if names and match(key.name):
            print(f'key    {key.path}')
            hits += 1
        for value in key.values():
            where = []
            if names and match(value.name):
                where.append('name')
            if data:
                decoded = value.data
                text = (' '.join(decoded) if isinstance(decoded, list)
                        else '' if isinstance(decoded, (bytes, bytearray)) else str(decoded))
                if match(text):
                    where.append('data')
                elif isinstance(decoded, (bytes, bytearray)) and not args.regex:
                    raw = value.raw
                    if (args.text.encode('utf-16-le') in raw
                            or args.text.encode('latin-1', 'ignore') in raw):
                        where.append('raw bytes')
            if where:
                print(f'value  {key.path}\\{value.name or "(default)"}  ({", ".join(where)})')
                hits += 1
    print(f'{hits} matches', file=sys.stderr)
    return 0 if hits else 1


def cmd_timeline(args):
    hive = _open_from_args(args)
    rows = sorted(((key.last_written_raw, key.path) for key in hive.walk()), reverse=True)
    stream = _out(args)
    writer = csv.writer(stream)
    writer.writerow(['Last Written (UTC)', 'FILETIME', 'Key Path'])
    for stamp, path in rows:
        writer.writerow([_iso(stamp), stamp, path or '(root)'])
    if stream is not sys.stdout:
        stream.close()
    return 0


def _json_data(value):
    data = value.data
    if isinstance(data, (bytes, bytearray)):
        return data.hex()
    return data


def _reg_escape(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')


def _reg_line(value):
    name = '@' if value.is_default else f'"{_reg_escape(value.name)}"'
    data = value.data
    if value.type == 1 and isinstance(data, str) and not value.notes:
        return f'{name}="{_reg_escape(data)}"'
    if value.type == 4 and isinstance(data, int) and len(value.raw) == 4:
        return f'{name}=dword:{data:08x}'
    hexed = ','.join(f'{b:02x}' for b in value.raw)
    if value.type == 3:
        return f'{name}=hex:{hexed}'
    return f'{name}=hex({value.type:x}):{hexed}'


def export_key(hive, start, fmt, stream, prefix=None):
    """Write start and every key under it to stream as 'json', 'csv' or 'reg'.

    reg writes regedit's text format; prefix replaces the root key's name in each [path] line
    (for example HKEY_LOCAL_MACHINE\\SYSTEM). A REG_SZ is written as a quoted string only when
    its bytes decoded without a note; every other value is written as hex of its raw bytes.
    """
    if fmt == 'json':
        stream.write('[\n')
        first = True
        for key in hive.walk(start):
            record = {'path': key.path, 'last_written': _iso(key.last_written_raw),
                      'last_written_filetime': key.last_written_raw, 'class_name': key.class_name,
                      'flags': key.flag_names, 'offset': key.offset,
                      'values': [{'name': v.name, 'type': v.type, 'type_name': v.type_name,
                                  'size': v.size, 'data': _json_data(v), 'raw': v.raw.hex(),
                                  'notes': v.notes, 'offset': v.offset} for v in key.values()]}
            stream.write(('' if first else ',\n') + json.dumps(record, ensure_ascii=False))
            first = False
        stream.write('\n]\n')
    elif fmt == 'csv':
        writer = csv.writer(stream)
        writer.writerow(['Key Last Written (UTC)', 'Key Path', 'Value Name', 'Value Type',
                         'Data Size', 'Data', 'Raw Data (hex)', 'Notes'])
        for key in hive.walk(start):
            values = key.values()
            if not values:
                writer.writerow([_iso(key.last_written_raw), key.path, '', '', '', '', '', ''])
            for v in values:
                writer.writerow([_iso(key.last_written_raw), key.path, v.name or '(default)',
                                 v.type_name, v.size, v.data_text(), v.raw.hex(), '; '.join(v.notes)])
    elif fmt == 'reg':
        prefix = prefix if prefix is not None else hive.root().name
        stream.write('Windows Registry Editor Version 5.00\n\n')
        for key in hive.walk(start):
            path = '\\'.join(p for p in (prefix, key.path) if p)
            stream.write(f'[{path}]\n')
            for v in key.values():
                stream.write(_reg_line(v) + '\n')
            stream.write('\n')
    else:
        raise RegfError(f'unknown export format {fmt!r}')


def cmd_export(args):
    hive = _open_from_args(args)
    start = hive.open_key(args.key or '')
    stream = _out(args)
    try:
        export_key(hive, start, args.format, stream, prefix=args.prefix)
    finally:
        if stream is not sys.stdout:
            stream.close()
    _print_faults(hive, sys.stderr)
    return 0


def cmd_logs(args):
    args.no_recover = False
    hive = _open_from_args(args)
    print(f'Hive: {hive.path or hive.name}, {"dirty" if hive.was_dirty else "clean"} as stored')
    for name, data in hive.logs:
        header = base_block(data)
        if header is None:
            print(f'  {name}: no base block')
            continue
        kind = {6: 'new format (HvLE entries)', 1: 'older format (DIRT vector)'}.get(
            header['file_type'], f'file type {header["file_type"]}')
        line = f'  {name}: {kind}, sequence {header["primary"]}/{header["secondary"]}'
        if header['file_type'] == 6:
            entries = log_entries(data)
            if entries:
                line += (f', {len(entries)} valid entries, sequence {entries[0]["sequence"]} '
                         f'to {entries[-1]["sequence"]}')
            else:
                line += ', no valid entries'
        print(line)
    print(summarise_recovery(hive.recovery))
    if hive.recovery.get('state') == 'recovered':
        changed = sum(1 for i in range(0, min(len(hive.original), len(hive.data)), _PAGE)
                      if hive.original[i:i + _PAGE] != hive.data[i:i + _PAGE])
        grown = max(0, len(hive.data) - len(hive.original))
        print(f'Replay changes {changed} of the hive\'s 4096-byte pages'
              f'{f" and adds {grown} bytes" if grown else ""}. Nothing is written to disk.')
    return 0


def _safe_join(root, *parts):
    """root joined with parts, refusing any part that would climb out of root."""
    cleaned = []
    for part in parts:
        for piece in part.replace('\\', '/').split('/'):
            if piece in ('', '.'):
                continue
            if piece == '..' or ':' in piece:
                raise RegfError(f'refusing path component {piece!r}')
            cleaned.append(piece)
    target = os.path.join(root, *cleaned)
    if os.path.commonpath([os.path.abspath(root), os.path.abspath(target)]) != os.path.abspath(root):
        raise RegfError(f'refusing path outside {root}')
    return target


def extract_hives(image, dest, password=None):
    """Copy every file named like a hive, and the .LOG1/.LOG2 beside it, out of a disk image.

    Files land under dest/<volume>/<path in the volume>. Returns [(volume, path, bytes written)].
    The image is only read.
    """
    def wanted(path):
        upper = path.upper()
        if upper.endswith(('.LOG1', '.LOG2')):
            return _is_hive_name(path[:-5])
        return _is_hive_name(path)
    done = []
    for label, path, walker, node, size in _walk_image(image, wanted, password):
        target = _safe_join(dest, label, path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = _read_node(walker, node, size)
        with open(target, 'wb') as handle:
            handle.write(data)
        done.append((label, path, len(data)))
    return done


def cmd_hives(args):
    if args.extract:
        for label, path, size in extract_hives(args.image, args.extract, password=args.password):
            print(f'{label}\t{path}\t{size}')
        return 0
    for label, path, size in hives_in_image(args.image, password=args.password):
        print(f'{label}\t{path}\t{size}')
    return 0


def _shift_for_image(args):
    """With --image there is no hive file on the line, so the words argparse put in hive, key,
    ... belong one place to the right: `ls --image X --path P Select` lists Select."""
    names = getattr(args, 'positionals', ())
    if not getattr(args, 'image', None) or not names or args.hive is None:
        return
    words = [args.hive] + [getattr(args, name) for name in names]
    args.hive = None
    for name, word in zip(names, words):
        setattr(args, name, word)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='regfprobe', description='Read Windows registry hives, offline and read-only.')
    parser.add_argument('--version', action='version', version=f'regfprobe {__version__}')
    sub = parser.add_subparsers(dest='command', required=True)

    def common(p, *positionals):
        """The hive file, then positionals. With --image the hive comes from the image, so the
        first word on the line is the first of positionals instead (see _shift_for_image)."""
        p.add_argument('hive', nargs='?', help='hive file (its .LOG1/.LOG2 are read from beside it)')
        for name, text in positionals:
            p.add_argument(name, nargs='?', default=None, help=text)
        p.add_argument('--image', help='read the hive from inside this disk image (needs qnxprobe.py)')
        p.add_argument('--path', help='with --image: the hive\'s path inside the image')
        p.add_argument('--volume', help='with --image: the volume holding --path, as `hives` names it')
        p.add_argument('--password', help='password for an encrypted volume in --image')
        p.add_argument('--no-recover', action='store_true', help='do not replay transaction logs')
        p.set_defaults(positionals=tuple(name for name, _text in positionals))

    key_help = ('key', 'key path below the root, \\ or / separated')
    p = sub.add_parser('info', help='base block, recovery and counts')
    common(p)
    p.set_defaults(func=cmd_info)
    p = sub.add_parser('ls', help='subkeys and values of a key')
    common(p, key_help)
    p.set_defaults(func=cmd_ls)
    p = sub.add_parser('cat', help='decoded data and hex of a key\'s values')
    common(p, key_help, ('value', 'one value name; "" for the default value'))
    p.set_defaults(func=cmd_cat, required=('key',))
    p = sub.add_parser('find', help='search key names, value names and data')
    common(p, ('text', 'text to look for, without case'))
    p.add_argument('--names', action='store_true', help='names only')
    p.add_argument('--data', action='store_true', help='data only')
    p.add_argument('--regex', action='store_true')
    p.set_defaults(func=cmd_find, required=('text',))
    p = sub.add_parser('timeline', help='every key by last written time, as CSV')
    common(p)
    p.add_argument('--out')
    p.set_defaults(func=cmd_timeline)
    p = sub.add_parser('export', help='keys and values as JSON, CSV or .reg')
    common(p, key_help)
    p.add_argument('--format', choices=('json', 'csv', 'reg'), default='json')
    p.add_argument('--prefix', help='.reg only: the path to write in place of the root key\'s name, e.g. HKEY_LOCAL_MACHINE\\SYSTEM')
    p.add_argument('--out')
    p.set_defaults(func=cmd_export)
    p = sub.add_parser('logs', help='what the transaction logs hold and what replay changes')
    common(p)
    p.set_defaults(func=cmd_logs)
    p = sub.add_parser('hives', help='list files named like hives inside a disk image')
    p.add_argument('--image', required=True)
    p.add_argument('--password')
    p.add_argument('--extract', metavar='DIR', help='copy them, with their .LOG1/.LOG2, under DIR')
    p.set_defaults(func=cmd_hives)

    args = parser.parse_args(argv)
    _shift_for_image(args)
    for name in getattr(args, 'required', ()):
        if getattr(args, name) is None:
            parser.error(f'{args.command} needs {name.upper()}')
    try:
        return args.func(args)
    except BrokenPipeError:
        # the reader of our output went away (| head); stop without an error
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0
    except (RegfError, OSError) as error:
        print(f'regfprobe: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
