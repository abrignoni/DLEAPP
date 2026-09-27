"""Reader for the OneDrive client's own log files (.odl, .odlgz, .odlsent, .aodl), for DLEAPP.

Author: @AlexisBrignoni, Claude.

Written from Yogesh Khatri's description of the format ('Reading OneDrive Logs',
https://www.swiftforensics.com/2022/02/reading-onedrive-logs.html, and 'Reading OneDrive Logs
Part 2', https://www.swiftforensics.com/2022/11/reading-onedrive-logs-part-2.html) and his
MIT-licensed reader, odl.py, at 9ad135ecf56cd2086256cf8440b98b5eaa50c0ab
(https://github.com/ydkhatri/OneDrive/blob/9ad135ecf56cd2086256cf8440b98b5eaa50c0ab/odl.py),
checked against the files on the test images. No code is copied from it.

A file is a 0x100-byte header (the signature EBFGONED, the format version and the OneDrive
and operating system version strings, odl.py L99-L108) followed by records, either as they are
or as one gzip stream (odl.py L472-L485). A version 2 record has a 56-byte header and a
version 3 record a 32-byte one, both beginning CC DD EE FF and carrying a timestamp in
milliseconds since 1970 and the length of the record's data (odl.py L74-L97); in version 3
the data begins with a context block of the length the header gives, or 24 bytes when that
length is zero (odl.py L396-L404). The data holds the code file name and the function name,
each preceded by its length in bytes, with a 32-bit value between them, and then the
parameters (odl.py L407-L413).

The parameters mix numbers and text with no type information, so only their text is read:
a 32-bit length followed by that many bytes of printable text, the approach odl.py's
extract_strings takes (L276-L299), here with a minimum of three characters, one trailing NUL
dropped, text taken as UTF-8 and line breaks kept as stored.

Words in that text can be obfuscated. Older clients replace a word with a token listed in
ObfuscationStringMap.txt, one tab-separated entry per line, usually kept in the Business1 or
Personal log folder and used for the other folders' files too (odl.py L26-L33, L200-L231).
Where a token is listed more than once, the first entry is used, as odl.py does, and the
token is reported as repeated. Newer clients encrypt a word with AES in CBC mode with a zero
IV, under the key in general.keystore beside the log file, and write it as base64 with '/'
and '+' replaced by '_' and '-' (odl.py L141-L198). The plain text is UTF-16LE, or UTF-32LE,
which odl.py also decodes (L176-L180, L192); odl.py chooses UTF-32 when the key's text ends
with the twelve characters \\u0000\\u0000, and here each word is tried as UTF-16LE and then as
UTF-32LE instead. A word is a run of characters between the separators odl.py uses
(L233-L274). A word is decrypted when it decodes to whole cipher blocks, its padding is valid
and its plain text is printable in one of those encodings; otherwise a
word found in the string map is replaced by its entry. A word holding '+' that does neither
has each part between its plus signs decrypted where that part decrypts, since the client
writes a word such as 101+LM with only the part after the plus sign encrypted; any other word
is kept as stored.
"""

import base64
import json
import os
import re
import struct
import zlib

from Crypto.Cipher import AES

LOG_EXTENSIONS = ('.odl', '.odlgz', '.odlsent', '.aodl')
_SIGNATURE = b'EBFGONED'
_HEADER_SIZE = 0x100
_RECORD = b'\xcc\xdd\xee\xff'
_V2_HEADER = 56
_V3_HEADER = 32
_V3_UNSIZED_CONTEXT = 24
_MIN_TEXT = 3
_PLAIN_ENCODINGS = ('utf-16-le', 'utf-32-le')
_SEPARATORS = ':\\.@%#&*|{}!?<>;~()/"\''
_WORD_OR_SEPARATORS = re.compile('([' + re.escape(_SEPARATORS) + ']+)')


class OdlFile:
    """One log file: its header and its records, read from bytes."""

    def __init__(self, data):
        self.version = None
        self.onedrive_version = ''
        self.records = []
        self.stopped_at = None
        self.zero_bytes = 0
        self.gzip_cut_short = False
        self.body_size = 0
        if len(data) < _HEADER_SIZE or data[:8] != _SIGNATURE:
            raise ValueError('not an OneDrive log file (no EBFGONED header)')
        self.version = struct.unpack_from('<I', data, 8)[0]
        self.onedrive_version = _c_string(data[0x1C:0x5C])
        body = data[_HEADER_SIZE:]
        if body[:2] == b'\x1f\x8b':
            stream = zlib.decompressobj(31)
            body = stream.decompress(body)
            self.gzip_cut_short = not stream.eof
        self.body_size = len(body)
        if self.version == 2:
            self._walk(body, _V2_HEADER, _v2_record)
        elif self.version == 3:
            self._walk(body, _V3_HEADER, _v3_record)
        else:
            raise ValueError(f'format version {self.version} is not read')

    def _walk(self, body, header_size, read_record):
        offset = 0
        while offset < len(body):
            record = None
            if offset + header_size <= len(body) and body[offset:offset + 4] == _RECORD:
                record = read_record(body, offset)
            if record is None:
                if any(body[offset:]):
                    self.stopped_at = offset
                else:
                    self.zero_bytes = len(body) - offset
                return
            timestamp, data, size = record
            self.records.append(_parse_data(timestamp, data))
            offset += size


def _c_string(raw):
    return raw.split(b'\x00', 1)[0].decode('utf-8', 'replace')


def _v2_record(body, offset):
    timestamp, = struct.unpack_from('<Q', body, offset + 8)
    data_len, = struct.unpack_from('<I', body, offset + 48)
    start = offset + _V2_HEADER
    if start + data_len > len(body):
        return None
    return timestamp, body[start:start + data_len], _V2_HEADER + data_len


def _v3_record(body, offset):
    context_len, = struct.unpack_from('<H', body, offset + 4)
    timestamp, = struct.unpack_from('<Q', body, offset + 8)
    data_len, = struct.unpack_from('<I', body, offset + 24)
    skip = context_len or _V3_UNSIZED_CONTEXT
    start = offset + _V3_HEADER
    if data_len < skip or start + data_len > len(body):
        return None
    return timestamp, body[start + skip:start + data_len], _V3_HEADER + data_len


def _parse_data(timestamp, data):
    code_file, position = _length_prefixed(data, 0)
    function, position = _length_prefixed(data, position + 4)
    return {'timestamp': timestamp, 'code_file': code_file, 'function': function,
            'params': data[position:]}


def _length_prefixed(data, position):
    if position + 4 > len(data):
        return '', len(data)
    size, = struct.unpack_from('<I', data, position)
    end = position + 4 + size
    if end > len(data):
        return '', len(data)
    return data[position + 4:end].decode('utf-8', 'replace'), end


def param_texts(params):
    """The text values in a record's parameter bytes, in order."""
    texts = []
    position = 0
    while position + 4 <= len(params):
        size, = struct.unpack_from('<I', params, position)
        text = _text_at(params, position, size)
        if text is None:
            position += 1
            continue
        texts.append(text)
        position += 4 + size
    return texts


def _text_at(params, position, size):
    if size < _MIN_TEXT or position + 4 + size > len(params):
        return None
    raw = params[position + 4:position + 4 + size]
    if raw.endswith(b'\x00'):
        raw = raw[:-1]
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if len(text) < _MIN_TEXT or not _printable(text):
        return None
    return text


def _printable(text):
    return all(char.isprintable() or char in '\t\r\n' for char in text)


def read_keystore(data):
    """The AES key a general.keystore holds, or None when it holds no version 1 key."""
    text = data.decode('utf-16-le') if data[1:2] == b'\x00' else data.decode('utf-8-sig')
    entries = json.loads(text)
    if not entries or entries[0].get('Version') != 1:
        return None
    key = base64.b64decode(entries[0]['Key'].rstrip('\x00'))
    return key if len(key) in (16, 24, 32) else None


def read_string_map(data):
    """The (token, text) entries of ObfuscationStringMap.txt, in file order.

    A line without exactly one tab continues the text of the entry above it, as odl.py
    reads the file (L200-L231).
    """
    text = data.decode('utf-16-le') if data[1:2] == b'\x00' else data.decode('utf-8', 'replace')
    entries = []
    for line in text.lstrip('\ufeff').splitlines():
        parts = line.split('\t')
        if len(parts) == 2:
            entries.append([parts[0], parts[1]])
        elif entries:
            entries[-1][1] += '\n' + line
    return [tuple(entry) for entry in entries]


def string_map(entry_lists):
    """(token to text, tokens listed with more than one text) from string map entries.

    The first entry for a token is used, as odl.py does (L200-L231).
    """
    mapping, repeated = {}, set()
    for entries in entry_lists:
        for token, text in entries:
            if token not in mapping:
                mapping[token] = text
            elif mapping[token] != text:
                repeated.add(token)
    return mapping, repeated


def decrypt_word(word, key):
    """A word's plain text under the keystore key, or None when it does not decrypt."""
    if key is None or len(word) < 22 or len(word) % 4 == 1:
        return None
    encoded = word.replace('_', '/').replace('-', '+')
    encoded += '=' * (-len(encoded) % 4)
    try:
        cipher_text = base64.b64decode(encoded, validate=True)
    except ValueError:
        return None
    if not cipher_text or len(cipher_text) % 16:
        return None
    plain = AES.new(key, AES.MODE_CBC, iv=bytes(16)).decrypt(cipher_text)
    pad = plain[-1]
    if not 1 <= pad <= 16 or plain[-pad:] != bytes([pad]) * pad:
        return None
    for encoding in _PLAIN_ENCODINGS:
        try:
            text = plain[:-pad].decode(encoding)
        except UnicodeDecodeError:
            continue
        if text and _printable(text):
            return text
    return None


def decode_text(text, key, mapping, repeated=frozenset()):
    """(decoded text, words replaced, words replaced from a token listed with more than one text)."""
    parts = _WORD_OR_SEPARATORS.split(text)
    replaced = uncertain = 0
    for index, part in enumerate(parts):
        if not part or index % 2:
            continue
        plain = decrypt_word(part, key)
        if plain is None and part in mapping:
            plain = mapping[part]
            uncertain += part in repeated
        if plain is not None:
            parts[index] = plain
            replaced += 1
        elif key is not None and '+' in part:
            pieces = [(piece, decrypt_word(piece, key)) for piece in part.split('+')]
            parts[index] = '+'.join(piece if clear is None else clear for piece, clear in pieces)
            replaced += sum(clear is not None for _, clear in pieces)
    return ''.join(parts), replaced, uncertain


def logs_root(path):
    """The OneDrive logs folder a log file sits under (Windows or macOS), or its own folder."""
    lowered = path.replace('\\', '/').lower()
    for marker in ('/onedrive/logs/', '/library/logs/onedrive/'):
        at = lowered.rfind(marker)
        if at >= 0:
            return path[:at + len(marker) - 1]
    return os.path.dirname(path)
