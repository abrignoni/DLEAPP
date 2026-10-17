"""Read the tab and window state files of Windows 11 Notepad.

Author: @AlexisBrignoni, Claude.

Notepad keeps one tab file per open tab in LocalState/TabState, with up to two
state files beside it, and one pair of files per window in LocalState/WindowState, under its package folder
Microsoft.WindowsNotepad_8wekyb3d8bbwe. The layout read here is the one ogmini's
Notepad-State-Library documents and parses (MIT licence), at commit
ce53f9d66de4551fa78f3cb19df90d7820f08d94:

  README.md, lines 87 to 203 (tab state) and 205 to 245 (window state)
    https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L87-L245
  NPTabState.cs, ParseBytes, lines 285 to 479
    https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/NotepadStateLibrary/NotepadStateLibrary/NPTabState.cs#L285-L479
  NPWindowState.cs, ParseBytes, lines 159 to 228
    https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/NotepadStateLibrary/NotepadStateLibrary/NPWindowState.cs#L159-L228
  CRC32Check.cs, line 9
    https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/NotepadStateLibrary/NotepadStateLibrary/CRC32Check.cs#L9

The code here is written from that description, not copied from it. Every file
starts with "NP" and an unsigned LEB128 sequence number. Integers are unsigned
LEB128 unless said otherwise, and text is UTF-16LE whose length is counted in
UTF-16 code units. Each block ends with a CRC-32 (the zlib polynomial) of the
bytes it covers, stored most significant byte first; for a tab file it covers
the bytes from the type flag to the CRC, for a tab's state file and a window
file the bytes from the sequence number to the CRC.

Every reader here bounds each read by the bytes present and raises NotepadError
on a file that ends early, rather than returning a short value.
"""

import struct
import uuid
import zlib

MAGIC = b'NP'


class NotepadError(ValueError):
    """A state file whose bytes do not fit the layout."""


class _Reader:
    def __init__(self, data, offset=0):
        self.data = data
        self.pos = offset

    def remaining(self):
        return len(self.data) - self.pos

    def take(self, count):
        if count < 0 or self.pos + count > len(self.data):
            raise NotepadError(f'needs {count} bytes at offset {self.pos}, '
                               f'{self.remaining()} present')
        chunk = self.data[self.pos:self.pos + count]
        self.pos += count
        return chunk

    def byte(self):
        return self.take(1)[0]

    def leb128(self):
        value = 0
        shift = 0
        while True:
            if shift > 63:
                raise NotepadError(f'LEB128 value longer than 64 bits at offset {self.pos}')
            current = self.byte()
            value |= (current & 0x7F) << shift
            shift += 7
            if not current & 0x80:
                return value

    def utf16(self, units):
        raw = self.take(units * 2)
        return raw.decode('utf-16-le', errors='replace')

    def uint32(self):
        return struct.unpack('<I', self.take(4))[0]


def _crc_ok(data, start, end, stored):
    """Whether the CRC-32 of data[start:end] equals the stored four bytes."""
    return zlib.crc32(data[start:end]) & 0xFFFFFFFF == int.from_bytes(stored, 'big')


def _config(reader):
    word_wrap = reader.byte()
    right_to_left = reader.byte()
    show_unicode = reader.byte()
    option_count = reader.leb128()
    options = reader.take(option_count)
    return {'word_wrap': word_wrap, 'right_to_left': right_to_left,
            'show_unicode': show_unicode, 'options': bytes(options)}


def _chunks(reader):
    """The unsaved buffer chunks after a tab file's CRC, each with its own CRC check."""
    chunks = []
    while reader.remaining():
        start = reader.pos
        position = reader.leb128()
        deleted = reader.leb128()
        added = reader.leb128()
        text = reader.utf16(added)
        end = reader.pos
        stored = reader.take(4)
        chunks.append({'position': position, 'deleted': deleted, 'added': added,
                       'text': text, 'crc_ok': _crc_ok(reader.data, start, end, stored)})
    return chunks


def parse_tab(data):
    """A dict describing one TabState file: a tab file (*.bin) or a tab's state file.

    Raises NotepadError when the bytes do not fit the layout.
    """
    if data[:2] != MAGIC:
        raise NotepadError('no NP signature')
    reader = _Reader(data, 2)
    sequence = reader.leb128()
    flag_at = reader.pos
    type_flag = reader.leb128()
    tab = {'sequence': sequence, 'type_flag': type_flag, 'file_path': None,
           'saved_length': None, 'encoding': None, 'line_ending': None, 'timestamp': None,
           'file_hash': None, 'content': None, 'unsaved_flag': None, 'bin_size': None,
           'chunks': []}
    if type_flag in (0, 1):
        if type_flag == 1:
            tab['file_path'] = reader.utf16(reader.leb128())
            tab['saved_length'] = reader.leb128()
            tab['encoding'] = reader.byte()
            tab['line_ending'] = reader.byte()
            tab['timestamp'] = reader.leb128()
            tab['file_hash'] = bytes(reader.take(32))
            reader.take(2)
        else:
            reader.take(1)
        tab['selection_start'] = reader.leb128()
        tab['selection_end'] = reader.leb128()
        tab.update(_config(reader))
        tab['content'] = reader.utf16(reader.leb128())
        tab['unsaved_flag'] = reader.byte()
        end = reader.pos
        tab['crc_ok'] = _crc_ok(data, flag_at, end, reader.take(4))
        tab['chunks'] = _chunks(reader)
    else:
        reader.take(1)
        tab['bin_size'] = reader.leb128()
        tab['selection_start'] = reader.leb128()
        tab['selection_end'] = reader.leb128()
        tab.update(_config(reader))
        end = reader.pos
        tab['crc_ok'] = _crc_ok(data, 2, end, reader.take(4))
        tab['trailing'] = reader.remaining()
    return tab


def apply_chunks(content, chunks):
    """content with each unsaved buffer chunk applied in order, or None when one does not fit.

    A chunk deletes `deleted` UTF-16 code units at `position` and inserts its text there.
    """
    units = content.encode('utf-16-le')
    for chunk in chunks:
        start = chunk['position'] * 2
        stop = start + chunk['deleted'] * 2
        if start > len(units) or stop > len(units):
            return None
        units = units[:start] + chunk['text'].encode('utf-16-le') + units[stop:]
    return units.decode('utf-16-le', errors='replace')


def parse_window(data):
    """A dict describing one WindowState file. Raises NotepadError when it does not fit."""
    if data[:2] != MAGIC:
        raise NotepadError('no NP signature')
    reader = _Reader(data, 2)
    sequence = reader.leb128()
    bytes_to_crc = reader.leb128()
    reader.take(1)
    count = reader.leb128()
    tabs = [str(uuid.UUID(bytes_le=bytes(reader.take(16)))) for _ in range(count)]
    active = reader.leb128()
    coords = [reader.uint32() for _ in range(6)]
    reader.take(1)
    end = reader.pos
    crc_ok = _crc_ok(data, 2, end, reader.take(4))
    return {'sequence': sequence, 'bytes_to_crc': bytes_to_crc, 'tabs': tabs, 'active': active,
            'top_left': tuple(coords[0:2]), 'bottom_right': tuple(coords[2:4]),
            'size': tuple(coords[4:6]), 'crc_ok': crc_ok, 'slack': reader.remaining()}
