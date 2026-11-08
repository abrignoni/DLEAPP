"""Read one entry file of Firefox's HTTP disk cache (cache2). Author: @AlexisBrignoni, Claude.

Layout from netwerk/cache2 at the FIREFOX_159_0_1_RELEASE tag
(https://github.com/mozilla-firefox/firefox/tree/6181e6b5f28a8fbae1d5c3ef6f6626b5a2180213/netwerk/cache2):

* The file is the response body, then a metadata block, then a trailer. Entries
  of version 4 end with two big-endian words, the version and the logical data
  size, whose high bit marks an entry encrypted at rest; older entries end with
  the data size alone (CacheFileMetadata.cpp, lines 26 to 99).
* The metadata block is a 32-bit hash of the rest of the block, one 16-bit hash
  per 256 KiB chunk of data, the header (version, fetch count, last fetched,
  last modified, frecency, expiration time, key size and, from version 2, flags,
  all big-endian 32-bit), the key with a terminating NUL, then NUL-terminated
  name and value pairs (CacheFileMetadata.h, lines 48 to 116; CacheFileMetadata.cpp,
  lines 1054 to 1160).
* The block hash is the one CacheHashUtils.cpp attributes to Bob Jenkins
  (burtleburtle.net/bob/hash/evahash.html), with an initial value of 0
  (CacheHashUtils.cpp, lines 13 to 115; CacheHashUtils.h, line 35). Firefox
  refuses an entry whose hash does not match, and so does this reader.
"""

import struct
from collections import namedtuple

CHUNK_SIZE = 256 * 1024          # CacheFileChunk.h, line 19
NO_EXPIRATION = 0xFFFFFFFF       # nsICacheEntry.idl, line 43
_ENCRYPTED_FLAG = 0x80000000
_CURRENT_VERSION = 4
_HEADER = struct.Struct('>8I')
_HEADER_V1 = struct.Struct('>7I')
_M = 0xFFFFFFFF

Entry = namedtuple('Entry', 'version fetch_count last_fetched last_modified expiration flags key elements data_size')


class Cache2Error(ValueError):
    """The file is not a cache2 entry this reader can read."""


class EncryptedEntry(Cache2Error):
    """A version 4 entry encrypted at rest; its metadata cannot be read without the profile's key."""


def _mix(a, b, c):
    a = (a - b - c) & _M; a ^= c >> 13
    b = (b - c - a) & _M; b ^= (a << 8) & _M
    c = (c - a - b) & _M; c ^= b >> 13
    a = (a - b - c) & _M; a ^= c >> 12
    b = (b - c - a) & _M; b ^= (a << 16) & _M
    c = (c - a - b) & _M; c ^= b >> 5
    a = (a - b - c) & _M; a ^= c >> 3
    b = (b - c - a) & _M; b ^= (a << 10) & _M
    c = (c - a - b) & _M; c ^= b >> 15
    return a, b, c


def cache_hash(data, initval=0):
    """CacheHash::Hash over little-endian 32-bit words."""
    a = b = 0x9e3779b9
    c = initval
    length = len(data)
    i = 0
    while length - i >= 12:
        a = (a + int.from_bytes(data[i:i + 4], 'little')) & _M
        b = (b + int.from_bytes(data[i + 4:i + 8], 'little')) & _M
        c = (c + int.from_bytes(data[i + 8:i + 12], 'little')) & _M
        a, b, c = _mix(a, b, c)
        i += 12
    c = (c + length) & _M
    tail = data[i:] + bytes(11 - (length - i))
    # The switch in CacheHashUtils.cpp adds bytes 8 to 10 to c from the second byte up
    # (the low byte of c is left for the length), 4 to 7 to b and 0 to 3 to a.
    c = (c + (int.from_bytes(tail[8:11], 'little') << 8)) & _M
    b = (b + int.from_bytes(tail[4:8], 'little')) & _M
    a = (a + int.from_bytes(tail[0:4], 'little')) & _M
    return _mix(a, b, c)[2]


def read_entry(data):
    """Parse one entry file. Raises Cache2Error (or EncryptedEntry) when it cannot be read."""
    if len(data) < 4:
        raise Cache2Error('shorter than a trailer')
    if len(data) >= 8:
        version_word, offset_word = struct.unpack('>II', data[-8:])
    else:
        version_word, offset_word = 0, struct.unpack('>I', data[-4:])[0]
    if 4 <= version_word <= _CURRENT_VERSION:
        if offset_word & _ENCRYPTED_FLAG:
            raise EncryptedEntry('encrypted at rest')
        data_size, trailer = offset_word, 8
    else:
        data_size, trailer = offset_word, 4
    meta = data[data_size:len(data) - trailer] if data_size <= len(data) - trailer else b''
    chunks = data_size // CHUNK_SIZE + (1 if data_size % CHUNK_SIZE else 0)
    header_at = 4 + 2 * chunks
    if len(meta) < header_at + 4:
        raise Cache2Error('metadata block too small for its header')
    version = struct.unpack_from('>I', meta, header_at)[0]
    if version == 1:
        fields = _HEADER_V1.unpack_from(meta, header_at) + (0,)
        header_size = _HEADER_V1.size
    elif 2 <= version <= _CURRENT_VERSION:
        if len(meta) < header_at + _HEADER.size:
            raise Cache2Error('metadata block too small for its header')
        fields = _HEADER.unpack_from(meta, header_at)
        header_size = _HEADER.size
    else:
        raise Cache2Error(f'unknown metadata version {version}')
    _, fetch_count, last_fetched, last_modified, _frecency, expiration, key_size, flags = fields
    key_at = header_at + header_size
    elements_at = key_at + key_size + 1
    if elements_at > len(meta):
        raise Cache2Error('key runs past the metadata block')
    if cache_hash(meta[4:]) != struct.unpack_from('>I', meta, 0)[0]:
        raise Cache2Error('metadata hash does not match')
    if meta[elements_at - 1] != 0:
        raise Cache2Error('key is not NUL-terminated')
    parts = meta[elements_at:].split(b'\0')
    elements = {}
    for i in range(0, len(parts) - 1, 2):
        elements[parts[i].decode('utf-8', 'replace')] = parts[i + 1]
    return Entry(version, fetch_count, last_fetched, last_modified, expiration, flags,
                 meta[key_at:key_at + key_size].decode('utf-8', 'replace'), elements, data_size)


def split_key(key):
    """(prefix, url): the tags before the first ':' tag, as stored, and the URL after it.

    CacheFileUtils.cpp, lines 40 to 130: tags such as a, (anonymous), O^<origin
    attributes>, and ~<id> each end with a comma, and the ':' tag is the last one,
    followed by the URL.
    """
    position = 0
    while position < len(key):
        if key[position] == ':':
            return key[:position], key[position + 1:]
        # Skip one tag and its value; ',,' inside a value is an escaped comma.
        position += 1
        while position < len(key):
            if key[position] == ',':
                if key[position + 1:position + 2] == ',':
                    position += 2
                    continue
                position += 1
                break
            position += 1
    return key, ''


def alt_data_offset(elements):
    """(offset, type) of alternative data from the alt-data element, or (None, '').

    CacheFileUtils.cpp, lines 475 to 511: "1;<offset>,<type>".
    """
    value = elements.get('alt-data')
    if not value:
        return None, ''
    text = value.decode('utf-8', 'replace')
    version, _, rest = text.partition(';')
    offset, _, kind = rest.partition(',')
    if version != '1':
        return None, ''
    try:
        number = int(offset)
    except ValueError:
        return None, ''
    return (number, kind) if number >= 0 else (None, '')


def response_head(elements):
    """(status line, {lower-cased header name: value}) from the response-head element."""
    text = elements.get('response-head', b'').decode('utf-8', 'replace')
    lines = text.split('\r\n') if '\r\n' in text else text.split('\n')
    headers = {}
    for line in lines[1:]:
        name, sep, value = line.partition(':')
        if sep and name.strip():
            headers.setdefault(name.strip().lower(), value.strip())
    return (lines[0].strip() if lines else ''), headers
