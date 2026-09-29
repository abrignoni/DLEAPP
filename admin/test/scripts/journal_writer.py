"""A minimal systemd journal file writer for the journal tests.

It lays objects out the way journald does (src/libsystemd/sd-journal/journal-file.c at systemd v259.5): each new
DATA object is appended, linked into the data hash table and put at the head of its field's list, followed by its
FIELD object when the field is new; the ENTRY object comes after its DATA objects, and entries are linked into the
header's chain of entry arrays and into each DATA object's list (the first entry inline, the rest in arrays whose
capacity doubles from 4, as link_entry_into_array does). Every fixture the tests build with it was read by
journalctl from systemd 259.5 (journalctl --verify, and -o export compared field by field with what this repo's
reader returns); see the module docstring of test_linux_journal.py.
"""
import lzma
import struct

from scripts.systemd_journal import jenkins_hash64, siphash24

INCOMPATIBLE = {'xz': 1, 'lz4': 2, 'keyed': 4, 'zstd': 8, 'compact': 16}
FLAG = {'xz': 1, 'lz4': 2, 'zstd': 4}


def lz4_compress(src):
    """A greedy LZ4 block encoder that keeps the format's end rules: the last match starts at least 12 bytes
    before the end and the last 5 bytes are literals."""
    n = len(src)
    out = bytearray()
    anchor = i = 0
    table = {}

    def length(value):
        while value >= 255:
            out.append(255)
            value -= 255
        out.append(value)

    while i < n - 12:
        key = src[i:i + 4]
        candidate = table.get(key)
        table[key] = i
        if candidate is None or i - candidate > 65535:
            i += 1
            continue
        match = 4
        while i + match < n - 5 and src[candidate + match] == src[i + match]:
            match += 1
        literals = i - anchor
        out.append((min(literals, 15) << 4) | min(match - 4, 15))
        if literals >= 15:
            length(literals - 15)
        out += src[anchor:i]
        out += (i - candidate).to_bytes(2, 'little')
        if match - 4 >= 15:
            length(match - 4 - 15)
        i += match
        anchor = i
    literals = n - anchor
    out.append(min(literals, 15) << 4)
    if literals >= 15:
        length(literals - 15)
    out += src[anchor:]
    return bytes(out)


class JournalWriter:
    """Build one journal file in memory. header_size is 272 (v254 and later), 264 (v252), 256 (v246) or 240
    (v189 to v245); compact and keyed need the matching systemd versions and are the caller's choice."""

    def __init__(self, compact=True, keyed=True, compression=None, header_size=272, state=0,
                 file_id=bytes(range(16)), machine_id=bytes(range(16, 32)), seqnum_id=bytes(range(32, 48)),
                 boot_id=bytes(range(48, 64)), tail_entry_boot_id_flag=True, frames=None,
                 data_buckets=64, field_buckets=16):
        self.compact, self.keyed, self.compression = compact, keyed, compression
        self.header_size, self.state = header_size, state
        self.file_id, self.machine_id, self.seqnum_id, self.boot_id = file_id, machine_id, seqnum_id, boot_id
        self.compatible = 2 if tail_entry_boot_id_flag else 0
        # Compressed payloads given as bytes, so a fixture does not depend on the compressor installed.
        self.frames = frames or {}
        self.buf = bytearray(header_size)
        self.counts = {'objects': 0, 'data': 0, 'fields': 0, 'entry_arrays': 0, 'entries': 0}
        self.tail_object = 0
        self.data_at = {}
        self.field_at = {}
        self.first_seqnum = self.last_seqnum = 0
        self.first_realtime = self.last_realtime = self.last_monotonic = 0
        self.tail_boot = boot_id
        self.last_entry = 0
        self.main = {'first': 0, 'n': 0, 'tail': 0, 'tidx': 0}
        self.field_table = self._append(5, b'\0' * (16 * field_buckets)) + 16
        self.field_buckets = field_buckets
        self.data_table = self._append(4, b'\0' * (16 * data_buckets)) + 16
        self.data_buckets = data_buckets

    # -------------------------------------------------------------------- low level

    def _hash(self, payload):
        return siphash24(payload, self.file_id) if self.keyed else jenkins_hash64(payload)

    def _append(self, kind, body, flags=0):
        offset = (len(self.buf) + 7) & ~7
        self.buf += b'\0' * (offset - len(self.buf))
        self.buf += struct.pack('<BB6xQ', kind, flags, 16 + len(body)) + body
        self.counts['objects'] += 1
        self.tail_object = offset
        return offset

    def _u64(self, offset, value=None):
        if value is None:
            return int.from_bytes(self.buf[offset:offset + 8], 'little')
        self.buf[offset:offset + 8] = value.to_bytes(8, 'little')
        return value

    def _u32(self, offset, value=None):
        if value is None:
            return int.from_bytes(self.buf[offset:offset + 4], 'little')
        self.buf[offset:offset + 4] = value.to_bytes(4, 'little')
        return value

    def _link_table(self, table, buckets, h, offset, next_at):
        bucket = table + 16 * (h % buckets)
        tail = self._u64(bucket + 8)
        if tail:
            self._u64(tail + next_at, offset)
        else:
            self._u64(bucket, offset)
        self._u64(bucket + 8, offset)

    # -------------------------------------------------------------------- data and fields

    def _data(self, payload):
        if payload in self.data_at:
            return self.data_at[payload]
        h = self._hash(payload)
        stored, flags = payload, 0
        if self.compression and len(payload) >= 512:
            if payload in self.frames:
                packed = self.frames[payload]
            elif self.compression == 'xz':
                packed = lzma.compress(payload, format=lzma.FORMAT_XZ, check=lzma.CHECK_NONE)
            elif self.compression == 'lz4':
                packed = struct.pack('<Q', len(payload)) + lz4_compress(payload)
            else:
                raise ValueError('a zstd fixture needs its compressed payloads given in frames')
            if len(packed) < len(payload):
                stored, flags = packed, FLAG[self.compression]
        body = struct.pack('<QQQQQQ', h, 0, 0, 0, 0, 0)
        if self.compact:
            body += struct.pack('<II', 0, 0)
        offset = self._append(1, body + stored, flags)
        self.counts['data'] += 1
        self._link_table(self.data_table, self.data_buckets, h, offset, 24)
        field = self._field(payload.partition(b'=')[0])
        self._u64(offset + 32, self._u64(field + 32))       # next_field_offset = field.head_data_offset
        self._u64(field + 32, offset)                        # field.head_data_offset = this DATA object
        self.data_at[payload] = offset
        return offset

    def _field(self, name):
        if name in self.field_at:
            return self.field_at[name]
        h = self._hash(name)
        offset = self._append(2, struct.pack('<QQQ', h, 0, 0) + name)
        self.counts['fields'] += 1
        self._link_table(self.field_table, self.field_buckets, h, offset, 24)
        self.field_at[name] = offset
        return offset

    # -------------------------------------------------------------------- entry arrays

    def _link_array(self, state, entry, index):
        """link_entry_into_array: put entry at position index of a chain, appending an array when full."""
        item = 4 if self.compact else 8
        use_tail = state.get('tail') is not None and state['tail']
        a = state['tail'] if use_tail else state['first']
        i = state['tidx'] if use_tail else index
        n = 0
        last = 0
        while a:
            n = (self._u64(a + 8) - 24) // item
            if i < n:
                self.buf[a + 24 + i * item:a + 24 + (i + 1) * item] = entry.to_bytes(item, 'little')
                if state.get('tail') is not None:
                    state['tidx'] += 1
                return
            i -= n
            last = a
            a = self._u64(a + 16)
        n = (index + 1) * 2 if index > n else n * 2
        n = max(n, 4)
        new = self._append(6, b'\0' * (8 + n * item))
        self.counts['entry_arrays'] += 1
        self.buf[new + 24:new + 24 + item] = entry.to_bytes(item, 'little')
        if last == 0:
            state['first'] = new
        else:
            self._u64(last + 16, new)
        if state.get('tail') is not None:
            state['tail'] = new
            state['tidx'] = 1

    def _link_data(self, data, entry):
        """link_entry_into_array_plus_one for a DATA object's list of entries."""
        count = self._u64(data + 56)
        if count == 0:
            self._u64(data + 40, entry)
        else:
            state = {'first': self._u64(data + 48)}
            if self.compact:
                state['tail'] = self._u32(data + 64)
                state['tidx'] = self._u32(data + 68)
            else:
                state['tail'] = None
            self._link_array(state, entry, count - 1)
            self._u64(data + 48, state['first'])
            if self.compact:
                self._u32(data + 64, state['tail'])
                self._u32(data + 68, state['tidx'])
        self._u64(data + 56, count + 1)

    # -------------------------------------------------------------------- entries

    def add_entry(self, fields, realtime, monotonic, seqnum=None, boot_id=None, link=True):
        """Append an entry of (name, value bytes) fields. link=False leaves it out of every chain, as an entry
        written but not yet linked would be."""
        boot_id = boot_id or self.boot_id
        seqnum = seqnum or (self.last_seqnum + 1)
        xor = 0
        items = []
        for name, value in fields:
            payload = name.encode() + b'=' + value
            offset = self._data(payload)
            xor ^= jenkins_hash64(payload) if self.keyed else self._u64(offset + 16)
            items.append((offset, self._u64(offset + 16)))
        items = sorted(set(items))
        body = struct.pack('<QQQ16sQ', seqnum, realtime, monotonic, boot_id, xor)
        for offset, h in items:
            body += struct.pack('<I', offset) if self.compact else struct.pack('<QQ', offset, h)
        entry = self._append(3, body)
        if not link:
            return entry
        self.counts['entries'] += 1
        header_tail = self.header_size >= 264
        state = self.main
        if not header_tail:
            state['tail'] = None
        self._link_array(state, entry, state['n'])
        state['n'] += 1
        for offset, _h in items:
            self._link_data(offset, entry)
        if not self.first_seqnum:
            self.first_seqnum, self.first_realtime = seqnum, realtime
        self.last_seqnum, self.last_realtime, self.last_monotonic = seqnum, realtime, monotonic
        self.tail_boot = boot_id
        self.last_entry = entry
        return entry

    # -------------------------------------------------------------------- file

    def bytes(self):
        """The finished file: the header written over the first header_size bytes, the arena padded to 8."""
        self.buf += b'\0' * (-len(self.buf) % 8)
        incompatible = (INCOMPATIBLE['keyed'] if self.keyed else 0) | (INCOMPATIBLE['compact'] if self.compact else 0)
        if self.compression:
            incompatible |= INCOMPATIBLE[self.compression]
        header = struct.pack('<8sIIB7x16s16s16s16sQQQQQQQQQQQQQQQ', b'LPKSHHRH', self.compatible, incompatible,
                             self.state, self.file_id, self.machine_id, self.tail_boot, self.seqnum_id,
                             self.header_size, len(self.buf) - self.header_size, self.data_table,
                             16 * self.data_buckets, self.field_table, 16 * self.field_buckets, self.tail_object,
                             self.counts['objects'], self.counts['entries'], self.last_seqnum, self.first_seqnum,
                             self.main['first'], self.first_realtime, self.last_realtime, self.last_monotonic)
        extra = struct.pack('<QQQQ', self.counts['data'], self.counts['fields'], 0, self.counts['entry_arrays'])
        if self.header_size >= 256:
            extra += struct.pack('<QQ', 0, 0)
        if self.header_size >= 264:
            extra += struct.pack('<II', self.main['tail'] or 0, self.main['tidx'] or 0)
        if self.header_size >= 272:
            extra += struct.pack('<Q', self.last_entry)
        header = (header + extra)[:self.header_size]
        return bytes(header) + bytes(self.buf[self.header_size:])
