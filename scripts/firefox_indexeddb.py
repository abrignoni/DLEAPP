"""Firefox IndexedDB readers. Author: @AlexisBrignoni, Claude.

Each value is a SpiderMonkey structured-clone buffer that Firefox compressed with raw
Snappy; each key uses Firefox's IndexedDB key encoding. The readers below follow
mozilla-firefox/firefox at c32abda0190531351e22da36334f18f9e994d474:
js/src/vm/StructuredClone.cpp (JSStructuredCloneReader), dom/base/StructuredCloneTags.h,
dom/indexedDB/Key.cpp, dom/indexedDB/DBSchema.cpp and dom/indexedDB/ActorsParent.cpp.
The artifact notes cite the lines.
"""

import json
import math
import sqlite3
import struct
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath

from scripts.firefox import snappy_raw_uncompress
from scripts.ilapfuncs import logfunc, open_sqlite_db_readonly
from scripts.macos_plists import unique_sources, user_from_path

_FLOAT_MAX = 0xFFF00000
_HEADER = 0xFFF10000
# enum StructuredDataType, numbered from SCTAG_NULL = 0xFFFF0000 in declaration order.
_SC_NAMES = ('NULL', 'UNDEFINED', 'BOOLEAN', 'INT32', 'STRING', 'DATE_OBJECT', 'REGEXP_OBJECT',
             'ARRAY_OBJECT', 'OBJECT_OBJECT', 'ARRAY_BUFFER_OBJECT_V2', 'BOOLEAN_OBJECT',
             'STRING_OBJECT', 'NUMBER_OBJECT', 'BACK_REFERENCE_OBJECT', 'DO_NOT_USE_1',
             'DO_NOT_USE_2', 'TYPED_ARRAY_OBJECT_V2', 'MAP_OBJECT', 'SET_OBJECT', 'END_OF_KEYS',
             'DO_NOT_USE_3', 'DATA_VIEW_OBJECT_V2', 'SAVED_FRAME_OBJECT', 'JSPRINCIPALS',
             'NULL_JSPRINCIPALS', 'RECONSTRUCTED_SAVED_FRAME_PRINCIPALS_IS_SYSTEM',
             'RECONSTRUCTED_SAVED_FRAME_PRINCIPALS_IS_NOT_SYSTEM', 'SHARED_ARRAY_BUFFER_OBJECT',
             'SHARED_WASM_MEMORY_OBJECT', 'BIGINT', 'BIGINT_OBJECT', 'ARRAY_BUFFER_OBJECT',
             'TYPED_ARRAY_OBJECT', 'DATA_VIEW_OBJECT', 'ERROR_OBJECT',
             'RESIZABLE_ARRAY_BUFFER_OBJECT', 'GROWABLE_SHARED_ARRAY_BUFFER_OBJECT',
             'IMMUTABLE_ARRAY_BUFFER_OBJECT')
_T = {name: 0xFFFF0000 + index for index, name in enumerate(_SC_NAMES)}
# enum StructuredCloneTags (DOM), numbered from SCTAG_BASE = JS_SCTAG_USER_MIN = 0xFFFF8000.
_DOM_NAMES = ('BASE', 'DOM_BLOB', 'DOM_FILE_WITHOUT_LASTMODIFIEDDATE', 'DOM_FILELIST',
              'DOM_MUTABLEFILE', 'DOM_FILE', 'DOM_WASM_MODULE', 'DOM_IMAGEDATA', 'DOM_DOMPOINT',
              'DOM_DOMPOINTREADONLY', 'DOM_CRYPTOKEY', 'DOM_NULL_PRINCIPAL', 'DOM_SYSTEM_PRINCIPAL',
              'DOM_CONTENT_PRINCIPAL', 'DOM_DOMQUAD', 'DOM_RTCCERTIFICATE', 'DOM_DOMRECT',
              'DOM_DOMRECTREADONLY', 'DOM_EXPANDED_PRINCIPAL')
_TAG_NAME = {value: f'SCTAG_{name}' for name, value in _T.items()}
_TAG_NAME.update({0xFFFF8000 + index: f'SCTAG_{name}' for index, name in enumerate(_DOM_NAMES)})
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class NotDecoded(Exception):
    """A value uses a part of the format this reader does not decode."""


def _tag_name(tag):
    return _TAG_NAME.get(tag, f'tag 0x{tag:08X}')


def _number(value):
    if math.isfinite(value):
        return int(value) if value.is_integer() and abs(value) < 2 ** 53 else value
    return {'$number': 'NaN' if math.isnan(value) else ('Infinity' if value > 0 else '-Infinity')}


def _date(ms):
    try:
        if not math.isfinite(ms):
            raise ValueError
        return {'$date': (_EPOCH + timedelta(milliseconds=ms)).isoformat().replace('+00:00', 'Z')}
    except (ValueError, OverflowError):
        return {'$date': 'invalid'}


class _Container:
    """An object, array, Map or Set still being filled, as the reader's objs stack holds it."""

    def __init__(self, kind):
        self.kind, self.items = kind, []

    def value(self):
        if self.kind == 'set':
            return {'$set': [_plain(v) for v in self.items]}
        if self.kind == 'map':
            return {'$map': [[_plain(k), _plain(v)] for k, v in self.items]}
        if self.kind == 'array':
            if all(isinstance(k, int) for k, _ in self.items):
                length = max((k for k, _ in self.items), default=-1) + 1
                out = [None] * length
                for k, v in self.items:
                    out[k] = _plain(v)
                return out
        return {str(_plain(k)): _plain(v) for k, v in self.items}


def _plain(value):
    return value.value() if isinstance(value, _Container) else value


class _CloneReader:
    """JSStructuredCloneReader::read over a decompressed buffer."""

    def __init__(self, raw):
        self.raw, self.pos, self.objects = raw, 0, 0

    def _word(self):
        if self.pos + 8 > len(self.raw):
            raise ValueError('truncated structured clone')
        value = struct.unpack_from('<Q', self.raw, self.pos)[0]
        self.pos += 8
        return value

    def _pair(self):
        value = self._word()
        return value >> 32, value & 0xFFFFFFFF

    def _peek_tag(self):
        if self.pos + 8 > len(self.raw):
            raise ValueError('truncated structured clone')
        return struct.unpack_from('<Q', self.raw, self.pos)[0] >> 32

    def _bytes(self, count, size):
        nbytes = count * size
        data = self.raw[self.pos:self.pos + nbytes]
        if len(data) != nbytes:
            raise ValueError('truncated structured clone')
        self.pos += nbytes + ((-((count % 8) * size)) & 7)
        return data

    def _string(self, data):
        nchars = data & 0x3FFFFFFF
        if data & (1 << 30):
            raise NotDecoded('string buffer reference')
        if data & (1 << 31):
            return self._bytes(nchars, 1).decode('latin-1')
        return self._bytes(nchars, 2).decode('utf-16-le', errors='replace')

    def _double(self):
        return struct.unpack('<d', struct.pack('<Q', self._word()))[0]

    def _object(self, value):
        self.objects += 1
        return value

    def _start(self, stack):
        tag, data = self._pair()
        if tag == _T['NULL']:
            return None
        if tag == _T['UNDEFINED']:
            return {'$undefined': True}
        if tag == _T['INT32']:
            return struct.unpack('<i', struct.pack('<I', data))[0]
        if tag == _T['BOOLEAN']:
            return bool(data)
        if tag == _T['BOOLEAN_OBJECT']:
            return self._object(bool(data))
        if tag == _T['STRING']:
            return self._string(data)
        if tag == _T['STRING_OBJECT']:
            return self._object(self._string(data))
        if tag == _T['NUMBER_OBJECT']:
            return self._object(_number(self._double()))
        if tag == _T['DATE_OBJECT']:
            return self._object(_date(self._double()))
        if tag == _T['REGEXP_OBJECT']:
            tag2, source = self._pair()
            if tag2 != _T['STRING']:
                raise ValueError('regular expression source is not a string')
            return self._object({'$regexp': self._string(source), 'flags': data})
        if tag in (_T['ARRAY_OBJECT'], _T['OBJECT_OBJECT'], _T['MAP_OBJECT'], _T['SET_OBJECT']):
            kind = {_T['ARRAY_OBJECT']: 'array', _T['OBJECT_OBJECT']: 'object',
                    _T['MAP_OBJECT']: 'map', _T['SET_OBJECT']: 'set'}[tag]
            container = self._object(_Container(kind))
            stack.append(container)
            return container
        if tag == _T['BACK_REFERENCE_OBJECT']:
            if data >= self.objects:
                raise ValueError('invalid back reference')
            return {'$backref': data}
        if tag in (_T['ARRAY_BUFFER_OBJECT_V2'], _T['ARRAY_BUFFER_OBJECT'],
                   _T['IMMUTABLE_ARRAY_BUFFER_OBJECT'], _T['RESIZABLE_ARRAY_BUFFER_OBJECT']):
            nbytes = data if tag == _T['ARRAY_BUFFER_OBJECT_V2'] else self._word()
            if tag == _T['RESIZABLE_ARRAY_BUFFER_OBJECT']:
                self._word()
            return self._object({'$arraybuffer': self._bytes(nbytes, 1).hex()})
        if tag <= _FLOAT_MAX:
            return _number(struct.unpack('<d', struct.pack('<Q', (tag << 32) | data))[0])
        raise NotDecoded(_tag_name(tag))

    def read(self):
        if self._peek_tag() == _HEADER:
            self._pair()
        if 0xFFFF0200 <= self._peek_tag() <= 0xFFFF0204:
            raise NotDecoded('transfer map')
        stack = []
        top = self._start(stack)
        while stack:
            container = stack[-1]
            if self._peek_tag() == _T['END_OF_KEYS']:
                self._pair()
                stack.pop()
                continue
            key = self._start(stack)
            if container.kind == 'set':
                container.items.append(key)
            elif container.kind == 'map':
                container.items.append((key, self._start(stack)))
            elif key is None:
                stack.pop()
            else:
                container.items.append((key, self._start(stack)))
        return _plain(top), len(self.raw) - self.pos


def clone_value(raw):
    """(value, trailing byte count) for a decompressed structured-clone buffer."""
    return _CloneReader(bytes(raw)).read()


# dom/indexedDB/Key.h type constants
_K_TERMINATOR, _K_FLOAT, _K_DATE, _K_STRING, _K_BINARY, _K_ARRAY = 0, 0x10, 0x20, 0x30, 0x40, 0x50
_K_MAX_TYPE, _K_MAX_ARRAY_COLLAPSE = 0x50, 3


def _key_stringy(buf, pos, wide):
    """Key::DecodeStringy: the decoded units and the position after the terminator."""
    out, i = [], pos
    while i < len(buf) and buf[i] != _K_TERMINATOR:
        b0 = buf[i]
        if not b0 & 0x80:
            out.append(b0 - 1)
            i += 1
        elif not wide or not b0 & 0x40:
            c = b0 << 8
            if i + 1 < len(buf):
                c |= buf[i + 1]
            out.append((c + 0x7F - 0x8000) & 0xFFFF)
            i += 2
        else:
            c = b0 << 10
            if i + 1 < len(buf):
                c |= buf[i + 1] << 2
            if i + 2 < len(buf):
                c |= buf[i + 2] >> 6
            out.append(c & 0xFFFF)
            i += 3
    return out, i + 1


def _key_number(buf, pos):
    """Key::DecodeNumber, reading a trimmed tail as zero bytes."""
    chunk = bytes(buf[pos:pos + 8]).ljust(8, b'\x00')
    number = int.from_bytes(chunk, 'big')
    sign = 1 << 63
    bits = number & ~sign if number & sign else (-number) & 0xFFFFFFFFFFFFFFFF
    return struct.unpack('<d', struct.pack('<Q', bits))[0], pos + 8


def _key_value(buf, pos, offset, depth):
    if depth == 64:
        raise ValueError('key nests too deeply')
    if pos >= len(buf):
        raise ValueError('truncated key')
    kind = buf[pos] - offset
    if kind >= _K_ARRAY:
        offset += _K_MAX_TYPE
        if offset == _K_MAX_TYPE * _K_MAX_ARRAY_COLLAPSE:
            pos += 1
            offset = 0
        items = []
        while pos < len(buf) and buf[pos] - offset != _K_TERMINATOR:
            item, pos = _key_value(buf, pos, offset, depth + 1)
            items.append(item)
            offset = 0
        return items, pos + 1
    if kind == _K_STRING:
        units, pos = _key_stringy(buf, pos + 1, True)
        return struct.pack(f'<{len(units)}H', *units).decode('utf-16-le', errors='replace'), pos
    if kind == _K_DATE:
        value, pos = _key_number(buf, pos + 1)
        return _date(value), pos
    if kind == _K_FLOAT:
        value, pos = _key_number(buf, pos + 1)
        return _number(value), pos
    if kind == _K_BINARY:
        units, pos = _key_stringy(buf, pos + 1, False)
        return {'$binary': bytes(u & 0xFF for u in units).hex()}, pos
    raise ValueError(f'unknown key type 0x{buf[pos]:02X}')


def decode_key(blob):
    """An encoded IndexedDB key as a JSON-ready value."""
    if not isinstance(blob, (bytes, bytearray, memoryview)):
        raise TypeError(f'key is {type(blob).__name__}, not bytes')
    buf = bytes(blob)
    if not buf:
        raise ValueError('empty key')
    value, _pos = _key_value(buf, 0, 0, 0)
    return value


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def _value(data):
    """(Value text, status) for one object_data.data cell."""
    if isinstance(data, int) and not isinstance(data, bool):
        return '', 'Not decoded: stored in a file'
    if not isinstance(data, (bytes, bytearray, memoryview)):
        return '', 'Not decoded: not a blob'
    try:
        value, trailing = clone_value(snappy_raw_uncompress(data))
    except NotDecoded as exc:
        return '', f'Not decoded: {exc}'
    except (ValueError, TypeError, struct.error, UnicodeDecodeError) as exc:
        return '', f'Not decoded: {exc}'
    status = 'Decoded' if not trailing else f'Decoded, {trailing} trailing bytes'
    return _json(value), status


def read_indexeddb(context, label):
    """Rows from each profile's storage/default/<origin>/idb/<name>.sqlite."""
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).suffix == '.sqlite'
             and PurePosixPath(str(p).replace('\\', '/')).parent.name == 'idb']
    paths, _ = unique_sources(context, found, sidecars=('-wal',), label=label)
    output, sources, statuses = [], [], {}
    for path in paths:
        relative = context.get_relative_path(path)
        parts = str(relative).replace('\\', '/').split('/')
        profile = parts[-6] if len(parts) >= 6 and parts[-5:-3] == ['storage', 'default'] else ''
        user = user_from_path(relative)
        if not user and 'home' in parts and parts.index('home') + 1 < len(parts):
            user = parts[parts.index('home') + 1]
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            database = db.execute('SELECT name, origin FROM database LIMIT 1').fetchone() or ('', '')
            stores = dict(db.execute('SELECT id, name FROM object_store').fetchall())
            rows = db.execute('SELECT object_store_id, key, file_ids, data FROM object_data '
                              'ORDER BY object_store_id, key').fetchall()
        except sqlite3.Error as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        finally:
            db.close()
        for store_id, key, file_ids, data in rows:
            try:
                key_text = _json(decode_key(key))
            except (ValueError, TypeError, struct.error, UnicodeDecodeError):
                key_text = ''
                statuses['undecoded key'] = statuses.get('undecoded key', 0) + 1
            value_text, status = _value(data)
            statuses[status] = statuses.get(status, 0) + 1
            output.append((database[1], database[0], stores.get(store_id, ''), key_text,
                           value_text, status, file_ids or '', profile, user, relative))
        sources.append(path)
    for status, count in sorted(statuses.items()):
        if status != 'Decoded':
            logfunc(f'{label}: {count} value(s): {status}')
    return output, '\n'.join(sources)
