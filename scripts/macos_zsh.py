"""Readers for zsh's own files: compiled wordcode (.zwc), history and Terminal session files.

Every layout here is taken from the zsh 5.9 source, pinned to the zsh-5.9 tag commit
73d317384c9225e46d66444f93b46f0fbe7084ef of https://github.com/zsh-users/zsh:

- Src/parse.c holds the .zwc layout (FD_PRELEN, FD_MAGIC, struct fdhead, write_dump), the
  string encoding in wordcode (ecstrcode, ecgetstr) and the rule that decides whether a
  sourced file's compiled copy is used (try_source_file, check_dump_file, load_dump_header).
- Src/hist.c holds the history file writer and reader (savehistfile, readhistfile,
  readhistline).
- Src/zsh.h and Src/lex.c hold the Meta byte and the lexer tokens (Meta, Pound..Bnullkeep,
  ztokens) that stored strings carry.

Nothing here executes or sources a file; the bytes are only read.
"""

import re
import struct

FD_PRELEN = 12
FD_MAGIC = 0x04050607
FD_OMAGIC = 0x07060504
FDF_MAP = 1
FDHF_KSHLOAD = 1
FDHF_ZSHLOAD = 2
_FDHEAD_WORDS = 6

META = 0x83
# ztokens in Src/lex.c, one character for each token byte from Pound (0x84) to Bnullkeep (0xa0).
_ZTOKENS = '#$^*(())$=|{}[]`<>>?~`,-!\'"\\\\'
_POUND = 0x84
_NULARG = 0xa1
_MARKER = 0xa2


def decode_zsh_string(raw):
    """Text for bytes in zsh's internal form: Meta pairs undone, lexer tokens as the characters.

    Meta (0x83) is followed by the real byte XOR 32. Token bytes 0x84 to 0xa0 stand for the
    characters in ztokens; Nularg and Marker carry no character.
    """
    out = bytearray()
    index = 0
    while index < len(raw):
        byte = raw[index]
        if byte == META and index + 1 < len(raw):
            out.append(raw[index + 1] ^ 32)
            index += 2
            continue
        if _POUND <= byte < _POUND + len(_ZTOKENS):
            out.extend(_ZTOKENS[byte - _POUND].encode('ascii'))
        elif byte not in (_NULARG, _MARKER):
            out.append(byte)
        index += 1
    return out.decode('utf-8', errors='replace')


def unmetafy(raw):
    """Bytes with zsh's Meta pairs undone (Meta 0x83 is followed by the real byte XOR 32)."""
    out = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] == META and index + 1 < len(raw):
            out.append(raw[index + 1] ^ 32)
            index += 2
        else:
            out.append(raw[index])
            index += 1
    return bytes(out)


def _read_copy(data, order):
    """(version, mode, other, entries) for one copy of a .zwc, read in byte order `order`."""
    if len(data) < (FD_PRELEN + 1) * 4 or struct.unpack_from(order + 'I', data, 0)[0] != FD_MAGIC:
        raise ValueError('no .zwc magic number')
    flags = data[4]
    other = data[5] | (data[6] << 8) | (data[7] << 16)
    version = data[8:FD_PRELEN * 4].split(b'\x00', 1)[0].decode('ascii', errors='replace')
    header_words = struct.unpack_from(order + 'I', data, FD_PRELEN * 4)[0]
    if header_words * 4 > len(data) or header_words < FD_PRELEN + _FDHEAD_WORDS:
        raise ValueError('header length runs past the file')
    entries = []
    word = FD_PRELEN
    while word < header_words:
        start, length, _npats, strs, head_words, eflags = struct.unpack_from(order + '6I', data, word * 4)
        if head_words <= _FDHEAD_WORDS or word + head_words > header_words:
            raise ValueError('entry header runs past the file header')
        name_raw = data[(word + _FDHEAD_WORDS) * 4:(word + head_words) * 4].split(b'\x00', 1)[0]
        name = decode_zsh_string(name_raw)
        prog_at = start * 4
        if prog_at + length > len(data) or strs > length:
            raise ValueError(f'entry {name!r} runs past the file')
        table = data[prog_at + strs:prog_at + length]
        entries.append({
            'name': name,
            'tail': decode_zsh_string(name_raw[eflags >> 2:]),
            'load': {FDHF_KSHLOAD: 'ksh', FDHF_ZSHLOAD: 'zsh'}.get(eflags & 3, ''),
            'wordcode_bytes': strs,
            'strings': [decode_zsh_string(part) for part in table.split(b'\x00') if part],
        })
        word += head_words
    return version, ('mapped' if flags & FDF_MAP else 'read'), other, entries


def read_zwc(data):
    """The header and entries of a .zwc file, from the copy in the byte order it was written in.

    write_dump writes the header and code twice: first in the byte order of the machine that
    compiled it, then byte-swapped, starting at the offset recorded in the first header.
    Returns a dict with version, byte_order (of the machine that compiled it), mode
    ('mapped' or 'read'), second_copy ('same entries', 'different entries', 'absent' or
    'unreadable') and entries. Each entry has name, tail (the name after its last '/',
    which is what zsh matches a sourced file against), load ('ksh', 'zsh' or ''),
    wordcode_bytes and strings (the string table: strings of four or more characters, once
    each, in the order they were stored; shorter ones live inside the wordcode and are not
    listed). Raises ValueError when the bytes are not a .zwc file.
    """
    for order, other_order, label in (('<', '>', 'little-endian'), ('>', '<', 'big-endian')):
        if len(data) >= 4 and struct.unpack_from(order + 'I', data, 0)[0] == FD_MAGIC:
            break
    else:
        raise ValueError('no .zwc magic number')
    version, mode, other, entries = _read_copy(data, order)
    if not other or other >= len(data):
        second = 'absent'
    else:
        try:
            second_entries = _read_copy(data[other:], other_order)[3]
            second = 'same entries' if second_entries == entries else 'different entries'
        except ValueError:
            second = 'unreadable'
    return {'version': version, 'byte_order': label, 'mode': mode, 'second_copy': second,
            'entries': entries}


def compiled_copy_selected(plain_mtime, compiled_mtime, compiled, plain_name):
    """Why zsh 5.9 would or would not run the compiled copy of a sourced file.

    Mirrors try_source_file and check_dump_file in Src/parse.c: the .zwc is used when it
    exists, the plaintext is absent or not newer than it (st_mtime, whole seconds, so equal
    times select the .zwc), and it holds an entry whose name after the last '/' equals the
    sourced file's name. load_dump_header also requires the version recorded in the .zwc to
    equal the running shell's; that is not decided here. Returns (selected, reason).
    """
    if compiled is None:
        return False, 'no compiled copy'
    if not any(entry['tail'] == plain_name for entry in compiled['entries']):
        return False, f'compiled copy holds no entry named {plain_name}'
    if plain_mtime is None:
        return True, 'plaintext absent'
    if int(compiled_mtime) >= int(plain_mtime):
        return True, 'compiled copy not older than plaintext'
    return False, 'compiled copy older than plaintext'


def read_history(data):
    """Commands in a zsh history file, as readhistfile in Src/hist.c reads them.

    A line ending in a backslash continues on the next line (the backslash stands for a
    newline inside the command). A line beginning ':' carries ': <start>:<elapsed>;' from
    extended_history; a line beginning '\\:' is a plain command that starts with ':'.
    Returns a list of dicts: line (first line number), start (epoch seconds or None),
    elapsed (seconds or None) and command.
    """
    records = []
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    index = 0
    while index < len(lines):
        first = index + 1
        buf = lines[index]
        index += 1
        while buf.endswith(b'\\') and index < len(lines):
            buf = buf[:-1] + b'\n' + lines[index]
            index += 1
        stripped = buf.rstrip(b' ')
        if stripped != buf and stripped.endswith(b'\\'):
            buf = stripped[:-1]
        start = elapsed = None
        text = buf
        match = re.match(rb':\s*(-?\d+):(-?\d+);', buf)
        if match:
            start = int(match.group(1))
            elapsed = int(match.group(2))
            text = buf[match.end():]
        elif buf.startswith(b'\\:'):
            text = buf[1:]
        records.append({'line': first, 'start': start, 'elapsed': elapsed,
                        'command': unmetafy(text).decode('utf-8', errors='replace')})
    return records


_SESSION_SAVED = re.compile(rb'/bin/date -r (\d+)')


def session_saved_time(data):
    """The epoch seconds a Terminal .session file records, or None.

    /etc/zshrc_Apple_Terminal writes the file when the shell exits, as
    echo Restored session: "$(/bin/date -r <seconds>)", where <seconds> is the output of
    /bin/date +%s at that moment.
    """
    match = _SESSION_SAVED.search(data)
    return int(match.group(1)) if match else None
