"""Read the one file a Microsoft cabinet (.cab) holds, compressed with MSZIP or LZX.

Author: @AlexisBrignoni, Claude.

The cabinet layout (CFHEADER, CFFOLDER, CFFILE, CFDATA) follows the Microsoft Cabinet File Format
(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)). MSZIP follows [MS-MCI]
(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69):
each CFDATA block is "CK" and a deflate stream whose history is the 32 KiB of output before it.

LZX follows the LZX section of the same cabinet document, with three points where Windows' own makecab.exe
(Windows 11 build 26200) writes differently from that text, each settled by decoding makecab output back to the
input it was made from (admin/test/scripts/test_cab_reader.py):

- a path length coded 0 to 16 in a pretree is (previous length - code) mod 17;
- in an aligned offset block, a position slot with 3 footer bits takes them from the aligned offset tree;
- E8 call translation leaves the last 10 bytes of each 32 KiB frame alone.

The window size, 2^15 to 2^21 bytes, is given by the folder's compression type. A 2 MiB window has 50 position
slots: from slot 36 on each slot spans 2^17 positions, and slots 36 to 49 reach 2^21.

Only a cabinet with one folder and one file is read. Every block's recorded uncompressed size (MSZIP) or the
file's recorded size (both) is checked, and a mismatch raises CabError.
"""

import struct
import zlib

FRAME = 32768
_NONE, _MSZIP, _LZX = 0, 1, 3
_SLOTS = {15: 30, 16: 32, 17: 34, 18: 36, 19: 38, 20: 42, 21: 50}


class CabError(ValueError):
    """A cabinet this reader does not read, or whose data does not decode to the sizes it records."""


def _layout(data):
    try:
        return _read_layout(data)
    except (struct.error, ValueError) as exc:
        if isinstance(exc, CabError):
            raise
        raise CabError(f'a cabinet whose header or file entry is cut short ({exc})') from exc


def _read_layout(data):
    if data[:4] != b'MSCF':
        raise CabError('not a cabinet (no MSCF signature)')
    if len(data) < 44:
        raise CabError('a cabinet header cut short')
    coff_files, = struct.unpack_from('<I', data, 16)
    folders, files, flags = struct.unpack_from('<HHH', data, 26)
    if folders != 1 or files != 1:
        raise CabError(f'{folders} folders and {files} files, where one of each is read')
    offset, per_data = 36, 0
    if flags & 4:
        reserve_header, _, per_data = struct.unpack_from('<HBB', data, 36)
        offset += 4 + reserve_header
    first_data, count, compression = struct.unpack_from('<IHH', data, offset)
    size, = struct.unpack_from('<I', data, coff_files)
    name_at = coff_files + 16
    name = data[name_at:data.index(b'\0', name_at)].decode('latin-1')
    blocks, position = [], first_data
    for _ in range(count):
        if position + 8 + per_data > len(data):
            raise CabError('a data block past the end of the file')
        _, packed, unpacked = struct.unpack_from('<IHH', data, position)
        position += 8 + per_data
        if position + packed > len(data):
            raise CabError('a data block past the end of the file')
        blocks.append((data[position:position + packed], unpacked))
        position += packed
    return name, size, compression, blocks


def cab_member(data):
    """The name and bytes of the one file in a cabinet, uncompressed, MSZIP or LZX."""
    name, size, compression, blocks = _layout(data)
    kind = compression & 0xf
    if kind == _NONE:
        out = b''.join(block for block, _ in blocks)
    elif kind == _MSZIP:
        out = _mszip(blocks)
    elif kind == _LZX:
        window = (compression >> 8) & 0x1f
        if window not in _SLOTS:
            raise CabError(f'an LZX window of 2^{window} bytes, where 2^15 to 2^21 are read')
        out = lzx_decode(b''.join(block for block, _ in blocks), window, size)
    else:
        raise CabError(f'compression type {kind}, where none (0), MSZIP (1) and LZX (3) are read')
    if len(out) != size:
        raise CabError(f'{len(out)} bytes where the cab records {size} for {name}')
    return name, out


def _mszip(blocks):
    out = bytearray()
    for block, unpacked in blocks:
        if block[:2] != b'CK':
            raise CabError('an MSZIP block without its CK signature')
        history = bytes(out[-FRAME:])
        inflater = zlib.decompressobj(-15, zdict=history) if history else zlib.decompressobj(-15)
        chunk = inflater.decompress(block[2:]) + inflater.flush()
        if len(chunk) != unpacked:
            raise CabError(f'a block gave {len(chunk)} bytes where the cab records {unpacked}')
        out += chunk
    return bytes(out)


class _Bits:
    """A bitstream of 16-bit little-endian words, read most significant bit first."""

    def __init__(self, data):
        self.data, self.pos, self.buf, self.count = data, 0, 0, 0

    def _fill(self, need):
        while self.count < need:
            word = int.from_bytes(self.data[self.pos:self.pos + 2], 'little')
            self.pos += 2
            self.buf = (self.buf << 16) | word
            self.count += 16

    def read(self, n):
        if n == 0:
            return 0
        self._fill(n)
        self.count -= n
        value = self.buf >> self.count
        self.buf &= (1 << self.count) - 1
        return value

    def peek16(self):
        self._fill(16)
        return self.buf >> (self.count - 16)

    def skip(self, n):
        self.count -= n
        self.buf &= (1 << self.count) - 1

    def align(self):
        self.skip(self.count % 16)

    def seek(self, pos):
        self.pos, self.buf, self.count = pos, 0, 0


def _table(lengths):
    """A 65536-entry lookup of (symbol, code length) for a canonical Huffman code."""
    table = [None] * 65536
    code = 0
    for length in range(1, 17):
        for symbol, symbol_length in enumerate(lengths):
            if symbol_length == length:
                start = code << (16 - length)
                end = start + (1 << (16 - length))
                if end > 65536:
                    raise CabError('an over-subscribed Huffman code')
                table[start:end] = [(symbol, length)] * (end - start)
                code += 1
        code <<= 1
    return table


def _symbol(bits, table):
    entry = table[bits.peek16()]
    if entry is None:
        raise CabError('a Huffman code that is not in its tree')
    bits.skip(entry[1])
    return entry[0]


def _read_lengths(bits, lengths, first, last):
    pretree = _table([bits.read(4) for _ in range(20)])
    x = first
    while x < last:
        code = _symbol(bits, pretree)
        if code in (17, 18):
            run = bits.read(4) + 4 if code == 17 else bits.read(5) + 20
            if x + run > last:
                raise CabError('a run of path lengths past the end of its tree')
            lengths[x:x + run] = [0] * run
            x += run
        elif code == 19:
            run = bits.read(1) + 4
            code = _symbol(bits, pretree)
            if code > 16 or x + run > last:
                raise CabError('a bad run of path lengths')
            value = (lengths[x] - code) % 17
            lengths[x:x + run] = [value] * run
            x += run
        else:
            lengths[x] = (lengths[x] - code) % 17
            x += 1


def _translate_e8(frame, start, file_size):
    """Undo E8 call translation in one frame, in place; start is the frame's offset in the output."""
    i, stop = 0, len(frame) - 10
    while i < stop:
        if frame[i] != 0xE8:
            i += 1
            continue
        value = int.from_bytes(frame[i + 1:i + 5], 'little', signed=True)
        if -(start + i) <= value < file_size:
            relative = value - (start + i) if value >= 0 else value + file_size
            frame[i + 1:i + 5] = relative.to_bytes(4, 'little', signed=True)
        i += 5


def lzx_decode(data, window_bits, total):
    """The first total bytes the LZX stream in data decodes to, with a window of 2^window_bits bytes."""
    slots = _SLOTS[window_bits]
    extra = [0, 0, 0, 0] + [min((slot - 2) // 2, 17) for slot in range(4, slots)]
    base, position = [], 0
    for bits_count in extra:
        base.append(position)
        position += 1 << bits_count
    main_count = 256 + slots * 8
    main_lengths, length_lengths = [0] * main_count, [0] * 249
    bits = _Bits(data)
    r0 = r1 = r2 = 1
    window, out = bytearray(), bytearray()
    e8_size = (bits.read(16) << 16 | bits.read(16)) if bits.read(1) else 0
    remaining = block_type = block_size = 0
    main_tree = length_tree = aligned_tree = None
    while len(window) < total:
        if remaining == 0:
            if block_type == 3 and block_size % 2:
                bits.seek(bits.pos + 1)
            block_type = bits.read(3)
            block_size = remaining = bits.read(24)
            if block_type in (1, 2):
                aligned_tree = _table([bits.read(3) for _ in range(8)]) if block_type == 2 else None
                _read_lengths(bits, main_lengths, 0, 256)
                _read_lengths(bits, main_lengths, 256, main_count)
                main_tree = _table(main_lengths)
                _read_lengths(bits, length_lengths, 0, 249)
                length_tree = _table(length_lengths) if any(length_lengths) else None
            elif block_type == 3:
                if bits.count:
                    bits.skip(bits.count % 16 or 16)
                else:
                    bits.read(16)
                start = bits.pos - bits.count // 8
                r0, r1, r2 = struct.unpack_from('<III', data, start)
                bits.seek(start + 12)
            else:
                raise CabError(f'an LZX block of type {block_type}')
            if remaining == 0:
                raise CabError('an LZX block of no bytes')
        frame_end = min((len(window) // FRAME + 1) * FRAME, total)
        if block_type == 3:
            take = min(remaining, frame_end - len(window))
            if bits.pos + take > len(data):
                raise CabError('an uncompressed LZX block past the end of the data')
            window += data[bits.pos:bits.pos + take]
            bits.seek(bits.pos + take)
            remaining -= take
        else:
            while remaining > 0 and len(window) < frame_end:
                element = _symbol(bits, main_tree)
                if element < 256:
                    window.append(element)
                    remaining -= 1
                    continue
                element -= 256
                length = element & 7
                if length == 7:
                    if length_tree is None:
                        raise CabError('a match length with no length tree')
                    length += _symbol(bits, length_tree)
                length += 2
                slot = element >> 3
                if slot == 0:
                    offset = r0
                elif slot == 1:
                    offset, r1, r0 = r1, r0, r1
                elif slot == 2:
                    offset, r2, r0 = r2, r0, r2
                else:
                    footer = extra[slot]
                    if block_type == 2 and footer >= 3:
                        offset = base[slot] + (bits.read(footer - 3) << 3) + _symbol(bits, aligned_tree) - 2
                    else:
                        offset = base[slot] + bits.read(footer) - 2
                    r2, r1, r0 = r1, r0, offset
                start = len(window) - offset
                if start < 0 or offset == 0:
                    raise CabError('an LZX match before the start of the data')
                if offset >= length:
                    window += window[start:start + length]
                else:
                    for i in range(length):
                        window.append(window[start + i])
                remaining -= length
            if remaining < 0:
                raise CabError('an LZX match past the end of its block')
        if len(window) == frame_end:
            frame_start = (frame_end - 1) // FRAME * FRAME
            if block_type != 3:
                bits.align()
            frame = bytearray(window[frame_start:frame_end])
            if e8_size and frame_start // FRAME < 32768:
                _translate_e8(frame, frame_start, e8_size)
            out += frame
    return bytes(out)
