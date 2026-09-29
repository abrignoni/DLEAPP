"""systemd journal files (*.journal and *.journal~), read without systemd, for DLEAPP.

Author: @AlexisBrignoni, Claude.

A journal file is a header followed by objects written one after another: DATA objects holding one
NAME=value field each, FIELD objects naming the fields, ENTRY objects listing the DATA objects of one log
entry, the two hash tables, ENTRY_ARRAY objects chaining the entries in order, and TAG objects when the file
is sealed. The layout follows systemd's own description and code at the v259.5 tag (commit
b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a): docs/JOURNAL_FILE_FORMAT.md and
src/libsystemd/sd-journal/journal-def.h and journal-file.c, where the code is authoritative.

The reader walks the objects from the end of the header until it meets space where no object is written, and
reads every ENTRY object it meets together with every entry the header's chain of entry arrays reaches, so an
entry written but not yet linked into the chain, or one past a damaged object, is still read. Each DATA object an
entry names is decoded (XZ with the lzma module, LZ4 with the block decoder below, zstd with compression.zstd
from Python 3.14, or on earlier Pythons with the backports.zstd or zstandard package when one is installed)
and its payload is checked against the hash systemd stored with it: SipHash-2-4 keyed with the file ID in
files flagged KEYED_HASH, Jenkins lookup3 otherwise (journal_file_hash_data in journal-file.c).
"""

import struct

try:
    import lzma
except ImportError:  # a Python built without liblzma
    lzma = None

SIGNATURE = b'LPKSHHRH'

OBJECT_DATA = 1
OBJECT_ENTRY = 3
OBJECT_ENTRY_ARRAY = 6
OBJECT_TYPES = {0: 'unused', 1: 'data', 2: 'field', 3: 'entry', 4: 'data hash table', 5: 'field hash table',
                6: 'entry array', 7: 'tag'}

# ObjectHeader.flags, only valid on DATA objects
COMPRESSED_XZ = 1
COMPRESSED_LZ4 = 2
COMPRESSED_ZSTD = 4

# Header.incompatible_flags and Header.compatible_flags
INCOMPATIBLE_FLAGS = ((1, 'XZ compression'), (2, 'LZ4 compression'), (4, 'keyed hash'), (8, 'zstd compression'),
                      (16, 'compact'))
KNOWN_INCOMPATIBLE = 1 | 2 | 4 | 8 | 16
KEYED_HASH = 4
COMPACT = 16
COMPATIBLE_FLAGS = ((1, 'sealed'), (2, 'tail entry boot ID'))

STATES = {0: 'offline', 1: 'online', 2: 'archived'}

# The fixed part of struct Header, which every revision of the format has (up to tail_entry_monotonic).
_HEADER = struct.Struct('<8sIIB7x16s16s16s16sQQQQQQQQQQQQQQQ')
_OBJECT_HEADER = struct.Struct('<BB6xQ')
_ENTRY_HEAD = struct.Struct('<QQQ16sQ')

DATA_PAYLOAD_REGULAR = 64      # offsetof(DataObject, regular.payload)
DATA_PAYLOAD_COMPACT = 72      # offsetof(DataObject, compact.payload)
ENTRY_ITEMS = 64               # offsetof(EntryObject, items)
ENTRY_ARRAY_ITEMS = 24         # offsetof(EntryArrayObject, items)

ZSTD_MISSING = ('compressed with zstd, which needs Python 3.14 or the backports.zstd or zstandard package, '
                'so it was not decoded')


class JournalError(Exception):
    """The bytes are not a journal file this reader can read."""


class Entry:
    """One ENTRY object: its header values, its fields in stored order and anything wrong with it."""

    __slots__ = ('offset', 'seqnum', 'realtime', 'monotonic', 'boot_id', 'xor_hash', 'fields', 'problems',
                 'linked')

    def __init__(self, offset, seqnum, realtime, monotonic, boot_id, xor_hash, fields, problems, linked):
        self.offset = offset
        self.seqnum = seqnum
        self.realtime = realtime
        self.monotonic = monotonic
        self.boot_id = boot_id
        self.xor_hash = xor_hash
        self.fields = fields          # [(name, value bytes)], value None when the payload could not be read
        self.problems = problems      # [str]
        self.linked = linked          # reached from the header's chain of entry arrays


# ---------------------------------------------------------------------------------------------- hashes

_M64 = (1 << 64) - 1
_M32 = (1 << 32) - 1


def siphash24(data, key):
    """SipHash-2-4 of data with a 16-byte key, the hash systemd's siphash24.c computes."""
    k0, k1 = struct.unpack('<QQ', key)
    v0 = k0 ^ 0x736f6d6570736575
    v1 = k1 ^ 0x646f72616e646f6d
    v2 = k0 ^ 0x6c7967656e657261
    v3 = k1 ^ 0x7465646279746573
    length = len(data)
    end = length - length % 8
    words = list(struct.unpack_from(f'<{end // 8}Q', data)) if end else []
    words.append(((length & 0xff) << 56) | int.from_bytes(data[end:], 'little'))
    for m in words:
        v3 ^= m
        for _ in range(2):
            v0 = (v0 + v1) & _M64
            v1 = ((v1 << 13) | (v1 >> 51)) & _M64
            v1 ^= v0
            v0 = ((v0 << 32) | (v0 >> 32)) & _M64
            v2 = (v2 + v3) & _M64
            v3 = ((v3 << 16) | (v3 >> 48)) & _M64
            v3 ^= v2
            v0 = (v0 + v3) & _M64
            v3 = ((v3 << 21) | (v3 >> 43)) & _M64
            v3 ^= v0
            v2 = (v2 + v1) & _M64
            v1 = ((v1 << 17) | (v1 >> 47)) & _M64
            v1 ^= v2
            v2 = ((v2 << 32) | (v2 >> 32)) & _M64
        v0 ^= m
    v2 ^= 0xff
    for _ in range(4):
        v0 = (v0 + v1) & _M64
        v1 = ((v1 << 13) | (v1 >> 51)) & _M64
        v1 ^= v0
        v0 = ((v0 << 32) | (v0 >> 32)) & _M64
        v2 = (v2 + v3) & _M64
        v3 = ((v3 << 16) | (v3 >> 48)) & _M64
        v3 ^= v2
        v0 = (v0 + v3) & _M64
        v3 = ((v3 << 21) | (v3 >> 43)) & _M64
        v3 ^= v0
        v2 = (v2 + v1) & _M64
        v1 = ((v1 << 17) | (v1 >> 47)) & _M64
        v1 ^= v2
        v2 = ((v2 << 32) | (v2 >> 32)) & _M64
    return v0 ^ v1 ^ v2 ^ v3


def _rot(x, k):
    return ((x << k) | (x >> (32 - k))) & _M32


def jenkins_hash64(data):
    """jenkins_hash64() in lookup3.h: hashlittle2 with both initial values 0, the first result as the high 32
    bits and the second as the low 32 bits."""
    length = len(data)
    a = b = c = (0xdeadbeef + length) & _M32
    i = 0
    while length - i > 12:
        x, y, z = struct.unpack_from('<III', data, i)
        a = (a + x) & _M32
        b = (b + y) & _M32
        c = (c + z) & _M32
        a = (a - c) & _M32
        a ^= _rot(c, 4)
        c = (c + b) & _M32
        b = (b - a) & _M32
        b ^= _rot(a, 6)
        a = (a + c) & _M32
        c = (c - b) & _M32
        c ^= _rot(b, 8)
        b = (b + a) & _M32
        a = (a - c) & _M32
        a ^= _rot(c, 16)
        c = (c + b) & _M32
        b = (b - a) & _M32
        b ^= _rot(a, 19)
        a = (a + c) & _M32
        c = (c - b) & _M32
        c ^= _rot(b, 4)
        b = (b + a) & _M32
        i += 12
    rest = length - i
    if rest == 0:
        return (c << 32) | b
    x, y, z = struct.unpack('<III', data[i:] + b'\0' * (12 - rest))
    a = (a + x) & _M32
    b = (b + y) & _M32
    c = (c + z) & _M32
    c ^= b
    c = (c - _rot(b, 14)) & _M32
    a ^= c
    a = (a - _rot(c, 11)) & _M32
    b ^= a
    b = (b - _rot(a, 25)) & _M32
    c ^= b
    c = (c - _rot(b, 16)) & _M32
    a ^= c
    a = (a - _rot(c, 4)) & _M32
    b ^= a
    b = (b - _rot(a, 14)) & _M32
    c ^= b
    c = (c - _rot(b, 24)) & _M32
    return (c << 32) | b


# ---------------------------------------------------------------------------------------------- decompression

def lz4_block(src, size):
    """Decode one LZ4 block to exactly size bytes. systemd stores an LZ4 payload as its uncompressed size (a
    little-endian 64-bit integer) followed by the block (compress_blob_lz4 in src/basic/compress.c)."""
    out = bytearray()
    i, n = 0, len(src)
    while i < n:
        token = src[i]
        i += 1
        literals = token >> 4
        if literals == 15:
            while True:
                if i >= n:
                    raise ValueError('LZ4 literal length runs past the block')
                more = src[i]
                i += 1
                literals += more
                if more != 255:
                    break
        if i + literals > n:
            raise ValueError('LZ4 literals run past the block')
        out += src[i:i + literals]
        i += literals
        if i == n:
            break
        if i + 2 > n:
            raise ValueError('LZ4 match offset runs past the block')
        distance = src[i] | (src[i + 1] << 8)
        i += 2
        if distance == 0 or distance > len(out):
            raise ValueError('LZ4 match offset points before the output')
        match = token & 15
        if match == 15:
            while True:
                if i >= n:
                    raise ValueError('LZ4 match length runs past the block')
                more = src[i]
                i += 1
                match += more
                if more != 255:
                    break
        match += 4
        start = len(out) - distance
        if distance >= match:
            out += out[start:start + match]
        else:
            for k in range(match):
                out.append(out[start + k])
        if len(out) > size:
            raise ValueError('LZ4 output is longer than the stored size')
    if len(out) != size:
        raise ValueError('LZ4 output is shorter than the stored size')
    return bytes(out)


def _zstd_decompressor():
    """A zstd decompress function, from the standard library (Python 3.14) or the backports.zstd or zstandard
    package, or None when none is installed."""
    try:
        from compression import zstd  # pylint: disable=import-error
        return zstd.decompress
    except ImportError:
        pass
    try:
        from backports import zstd as backport  # pylint: disable=import-error
        return backport.decompress
    except ImportError:
        pass
    try:
        import zstandard  # pylint: disable=import-error
    except ImportError:
        return None
    return lambda data: zstandard.ZstdDecompressor().decompress(data)


_ZSTD = _zstd_decompressor()


def decompress(flags, raw):
    """The payload of a DATA object whose flags name a compression, or raise ValueError."""
    if flags == COMPRESSED_XZ:
        if lzma is None:
            raise ValueError('compressed with XZ, which needs a Python with the lzma module, so it was not decoded')
        try:
            return lzma.decompress(raw)
        except lzma.LZMAError as exc:
            raise ValueError(f'XZ data could not be decoded ({exc})') from exc
    if flags == COMPRESSED_LZ4:
        if len(raw) <= 8:
            raise ValueError('LZ4 payload is shorter than its size field')
        return lz4_block(raw[8:], int.from_bytes(raw[:8], 'little'))
    if flags == COMPRESSED_ZSTD:
        if _ZSTD is None:
            raise ValueError(ZSTD_MISSING)
        try:
            return _ZSTD(raw)
        except Exception as exc:  # pylint: disable=broad-except
            raise ValueError(f'zstd data could not be decoded ({type(exc).__name__})') from exc
    raise ValueError(f'object flags {flags:#x} name more than one compression or an unknown one')


# ---------------------------------------------------------------------------------------------- file

class JournalFile:
    """The header and entries of one journal file held in memory."""

    CACHE_LIMIT = 100000

    def __init__(self, data):
        if len(data) < _HEADER.size:
            raise JournalError(f'{len(data)} bytes is shorter than a journal header')
        (signature, self.compatible_flags, self.incompatible_flags, self.state, self.file_id, self.machine_id,
         self.tail_entry_boot_id, self.seqnum_id, self.header_size, self.arena_size, _dht_offset, _dht_size,
         _fht_offset, _fht_size, self.tail_object_offset, self.n_objects, self.n_entries, self.tail_entry_seqnum,
         self.head_entry_seqnum, self.entry_array_offset, self.head_entry_realtime, self.tail_entry_realtime,
         self.tail_entry_monotonic) = _HEADER.unpack_from(data, 0)
        if signature != SIGNATURE:
            raise JournalError('the file does not begin with the journal signature LPKSHHRH')
        if self.header_size < _HEADER.size or self.header_size > len(data):
            raise JournalError(f'header size {self.header_size} is not possible for a {len(data)}-byte file')
        self.data = data
        self.keyed = bool(self.incompatible_flags & KEYED_HASH)
        self.compact = bool(self.incompatible_flags & COMPACT)
        self.unknown_incompatible = self.incompatible_flags & ~KNOWN_INCOMPATIBLE
        self.end = min(len(data), self.header_size + self.arena_size)
        self._payload_at = DATA_PAYLOAD_COMPACT if self.compact else DATA_PAYLOAD_REGULAR
        self._cache = {}
        self.walk_stop = None
        self.object_counts = {}
        self._walked = self._walk()
        self._linked = self._chain()

    def features(self):
        """The header flags this file sets, by name, then any unknown ones in hex."""
        names = [name for bit, name in COMPATIBLE_FLAGS if self.compatible_flags & bit]
        names += [name for bit, name in INCOMPATIBLE_FLAGS if self.incompatible_flags & bit]
        unknown_compatible = self.compatible_flags & ~3
        if unknown_compatible:
            names.append(f'unknown compatible flags {unknown_compatible:#x}')
        if self.unknown_incompatible:
            names.append(f'unknown incompatible flags {self.unknown_incompatible:#x}')
        return names

    def _walk(self):
        """Offsets of the ENTRY objects met walking from the header to the first unwritten space."""
        data, end = self.data, self.end
        found = []
        counts = {}
        offset = self.header_size
        offset = (offset + 7) & ~7
        while True:
            if offset + 16 > end:
                rest = data[offset:end]
                self.walk_stop = None if not rest.strip(b'\0') else f'{len(rest)} bytes left at the end of the arena'
                break
            kind, _flags, size = _OBJECT_HEADER.unpack_from(data, offset)
            if size == 0:
                self.walk_stop = None      # unused space: nothing written from here on
                break
            if size < 16 or offset + size > end:
                self.walk_stop = (f'the object at offset {offset} gives a size of {size} bytes, which does not fit '
                                  f'in the arena that ends at offset {end}')
                break
            counts[kind] = counts.get(kind, 0) + 1
            if kind == OBJECT_ENTRY:
                found.append(offset)
            offset = (offset + size + 7) & ~7
        self.object_counts = counts
        return found

    def _chain(self):
        """Offsets the chain of entry arrays reaches from the header, in order."""
        data = self.data
        item = 4 if self.compact else 8
        found = []
        seen = set()
        offset = self.entry_array_offset
        while offset and offset not in seen and self._object_at(offset, OBJECT_ENTRY_ARRAY, ENTRY_ARRAY_ITEMS):
            seen.add(offset)
            size = int.from_bytes(data[offset + 8:offset + 16], 'little')
            nxt = int.from_bytes(data[offset + 16:offset + 24], 'little')
            for i in range(offset + ENTRY_ARRAY_ITEMS, offset + size - item + 1, item):
                value = int.from_bytes(data[i:i + item], 'little')
                if value:
                    found.append(value)
            offset = nxt
        return found

    def _object_at(self, offset, kind, minimum):
        """Whether an object of this type, at least minimum bytes long, starts at offset and fits in the file."""
        data = self.data
        if offset % 8 or offset < self.header_size or offset + 16 > len(data):
            return False
        if data[offset] != kind:
            return False
        size = int.from_bytes(data[offset + 8:offset + 16], 'little')
        return minimum <= size and offset + size <= len(data)

    def entry_offsets(self):
        """(offset, linked) for every ENTRY object the walk met or the chain reached, in file order."""
        linked = {o for o in self._linked if self._object_at(o, OBJECT_ENTRY, ENTRY_ITEMS)}
        offsets = set(self._walked) | linked
        return [(offset, offset in linked) for offset in sorted(offsets)]

    def entries(self):
        """Every entry, in file order. Nothing is read from a file with incompatible flags this reader does not
        know, because the format may then have changed in ways it cannot see."""
        if self.unknown_incompatible:
            return
        for offset, linked in self.entry_offsets():
            yield self._entry(offset, linked)

    def _entry(self, offset, linked):
        data = self.data
        size = int.from_bytes(data[offset + 8:offset + 16], 'little')
        seqnum, realtime, monotonic, boot_id, xor_hash = _ENTRY_HEAD.unpack_from(data, offset + 16)
        problems = [] if linked else ['not reached from the chain of entry arrays']
        item = 4 if self.compact else 16
        items = range(offset + ENTRY_ITEMS, offset + size - item + 1, item)
        if (size - ENTRY_ITEMS) % item:
            problems.append(f'the entry is {size} bytes, which is not a whole number of items')
        fields = []
        for number, i in enumerate(items, 1):
            target = int.from_bytes(data[i:i + (4 if self.compact else 8)], 'little')
            name, value, problem = self._data(target)
            if problem:
                problems.append(f'{name or f"item {number}"}: {problem}')
            if name is not None:
                fields.append((name, value))
        return Entry(offset, seqnum, realtime, monotonic, boot_id.hex(), xor_hash, fields, problems, linked)

    def _data(self, offset):
        """(name, value, problem) for the DATA object at offset; name and value are None when unreadable."""
        cached = self._cache.get(offset)
        if cached is not None:
            return cached
        if len(self._cache) >= self.CACHE_LIMIT:
            self._cache.clear()
        result = self._read_data(offset)
        self._cache[offset] = result
        return result

    def _read_data(self, offset):
        data = self.data
        if not self._object_at(offset, OBJECT_DATA, self._payload_at):
            return None, None, f'does not point to a DATA object (offset {offset})'
        flags = data[offset + 1]
        size = int.from_bytes(data[offset + 8:offset + 16], 'little')
        stored = int.from_bytes(data[offset + 16:offset + 24], 'little')
        payload = data[offset + self._payload_at:offset + size]
        if flags:
            try:
                payload = decompress(flags, payload)
            except ValueError as exc:
                return None, None, f'the DATA object at offset {offset} is {exc}'
        name, equals, value = payload.partition(b'=')
        name = name.decode('ascii', 'replace') if equals else None
        computed = siphash24(payload, self.file_id) if self.keyed else jenkins_hash64(payload)
        problem = None
        if computed != stored:
            problem = 'the hash stored with the DATA object does not match its payload'
        if name is None:
            return None, None, f'the DATA object at offset {offset} holds no "="'
        return name, value, problem


def read_journal(path):
    """A JournalFile for the file at path."""
    with open(path, 'rb') as handle:
        return JournalFile(handle.read())


def head_entry_realtime(path):
    """The time of a journal file's first entry, read from its header alone, or raise JournalError."""
    with open(path, 'rb') as handle:
        head = handle.read(_HEADER.size)
    if len(head) < _HEADER.size or head[:8] != SIGNATURE:
        raise JournalError('the file does not begin with the journal signature LPKSHHRH')
    return _HEADER.unpack_from(head, 0)[20]
