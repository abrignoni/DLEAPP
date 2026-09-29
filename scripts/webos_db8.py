"""Reader for webOS DB8 stores that use the LevelDB "sandwich" engine, as on LG webOS TVs.

Every layout here is taken from published source, pinned to commits:

- webOS OSE db8 (Apache-2.0), https://github.com/webosose/db8, commit
  7b551709f5bbd932e7119752e4929014f4bf8837 (tag submissions/32):
  - inc/core/MojObjectSerialization.h lines 32 to 54: the value markers (0 to 16) and
    TokenStartMarker 32.
  - src/core/MojObjectSerialization.cpp lines 87 to 120 (integer widths), 169 to 189 (a string is
    one token byte, or marker 4, its bytes and a NUL), 230 to 384 (the reader, including a token
    byte where a property name or a string value is expected, and the extension marker's uint32
    length) and 394 to 431 (integers).
  - src/core/MojDataSerialization.cpp lines 106 to 143: integers are big-endian and a decimal is
    an int64 holding the value times MojDecimal::Numerator, 1000000 (inc/core/MojDecimal.h
    line 31).
  - src/db/MojDbObjectHeader.cpp lines 82 to 126: an object in objects.db starts with a version byte (1), the
    kind token and the revision as integers, an optional deleted flag, and marker 16; the body
    that follows is read with the kind's token set.
  - src/db/MojDbKindState.cpp lines 24 to 26: kinds.db holds each kind's "tokens" map and
    indexIds.db its "kindTokens" and "indexIds" maps, as plain serialized objects keyed by kind id.
  - src/engine/sandwich/MojDbSandwichEngine.cpp lines 297 to 316 and MojDbSandwichDatabase.cpp
    lines 188 to 202: every logical database is a "part" of one LevelDB, and a key within a part
    is the object id serialized.
  - src/db/MojDb.cpp lines 889 to 897 (every write takes _rev from the store-wide id sequence)
    and 976 to 1021 (a delete either purges the object or writes it again with _del set).
- leveldb-tl, https://github.com/ony/leveldb-tl, commit
  fc5850f31e2668893a2398fdd6725521fa7bb8bf, include/leveldb/sandwich_db.hpp lines 10 to 19 and
  59 to 84: a part's keys carry
  a two-byte prefix (unsigned short in host order, the "cookie"); part 0 is the meta part mapping
  each database name to its cookie, and its empty key holds the next cookie.

The serialization and header code is the same in Open webOS db8 4.0.0 (tag versions/4.0.0,
commit 4d63046617ea9a1b3167c47907cd387ed05ce2df, 2013, https://github.com/openwebos/db8) apart
from a flag that decides whether new property names are added to the token set and an error path
for an integer marker the reader never passes it; neither changes the bytes read or written.

The LevelDB files are read with the vendored ccl_leveldb, which returns every record in the log
and table files. The newest record for each key wins, as in LevelDB itself; a key whose newest
record is a LevelDB deletion is not live. A DB8 object whose header carries the deleted flag is a
separate thing: DB8 keeps it as a live LevelDB record until it is purged, and it is reported with
``deleted`` set.
"""

import struct
from decimal import Decimal

from scripts.ccl import ccl_leveldb

MARKER_OBJECT_END = 0
MARKER_NULL = 1
MARKER_OBJECT_BEGIN = 2
MARKER_ARRAY_BEGIN = 3
MARKER_STRING = 4
MARKER_FALSE = 5
MARKER_TRUE = 6
MARKER_NEG_DECIMAL = 7
MARKER_POS_DECIMAL = 8
MARKER_NEG_INT = 9
MARKER_ZERO_INT = 10
MARKER_UINT8 = 11
MARKER_UINT16 = 12
MARKER_UINT32 = 13
MARKER_INT64 = 14
MARKER_EXTENSION = 15
MARKER_HEADER_END = 16
TOKEN_START = 32
_SKIPPED = object()
HEADER_VERSION = 1
DECIMAL_NUMERATOR = 1000000

OBJECTS_DB = b'objects.db'
KINDS_DB = b'kinds.db'
INDEX_IDS_DB = b'indexIds.db'


class Db8Error(ValueError):
    """A record that does not follow the DB8 layout."""


class _Reader:
    def __init__(self, data, pos=0, tokens=None):
        self.data = data
        self.pos = pos
        self.tokens = tokens

    def byte(self):
        if self.pos >= len(self.data):
            raise Db8Error('unexpected end of data')
        b = self.data[self.pos]
        self.pos += 1
        return b

    def take(self, n):
        if self.pos + n > len(self.data):
            raise Db8Error('unexpected end of data')
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def cstring(self):
        end = self.data.find(b'\0', self.pos)
        if end < 0:
            raise Db8Error('string without its NUL')
        raw = self.data[self.pos:end]
        self.pos = end + 1
        return raw.decode('utf-8', 'replace')

    def token(self, marker):
        if self.tokens is None:
            raise Db8Error(f'unexpected marker {marker}')
        idx = marker - TOKEN_START
        if idx < 0 or idx >= len(self.tokens) or self.tokens[idx] is None:
            raise Db8Error(f'token {marker} not in the kind\'s token set')
        return self.tokens[idx]

    def value(self, marker=None):
        if marker is None:
            marker = self.byte()
        if marker == MARKER_OBJECT_BEGIN:
            return self.object_body()
        if marker == MARKER_ARRAY_BEGIN:
            out = []
            while True:
                m = self.byte()
                if m == MARKER_OBJECT_END:
                    return out
                item = self.value(m)
                if item is not _SKIPPED:
                    out.append(item)
        if marker == MARKER_STRING:
            return self.cstring()
        if marker == MARKER_NULL:
            return None
        if marker == MARKER_TRUE:
            return True
        if marker == MARKER_FALSE:
            return False
        if marker in (MARKER_NEG_DECIMAL, MARKER_POS_DECIMAL):
            rep = struct.unpack('>q', self.take(8))[0]
            return Decimal(rep) / DECIMAL_NUMERATOR
        if marker == MARKER_ZERO_INT:
            return 0
        if marker == MARKER_UINT8:
            return self.byte()
        if marker == MARKER_UINT16:
            return struct.unpack('>H', self.take(2))[0]
        if marker == MARKER_UINT32:
            return struct.unpack('>I', self.take(4))[0]
        if marker in (MARKER_NEG_INT, MARKER_INT64):
            return struct.unpack('>q', self.take(8))[0]
        if marker == MARKER_EXTENSION:
            # db8's reader skips an extension value and visits nothing for it.
            size = struct.unpack('>I', self.take(4))[0]
            self.take(size)
            return _SKIPPED
        return self.token(marker)

    def object_body(self):
        out = {}
        while True:
            m = self.byte()
            if m == MARKER_OBJECT_END:
                return out
            if m == MARKER_STRING:
                name = self.cstring()
            else:
                name = self.token(m)
            item = self.value()
            out[name] = None if item is _SKIPPED else item


def decode_value(data, tokens=None):
    """One serialized value (a whole object for kinds.db and indexIds.db records, or a key).

    Raises Db8Error unless the value uses every byte."""
    r = _Reader(data, 0, tokens)
    value = r.value()
    if value is _SKIPPED:
        value = None
    if r.pos != len(data):
        raise Db8Error(f'{len(data) - r.pos} bytes after the value')
    return value


def read_header(data):
    """(kind token, revision, deleted, body offset) from an objects.db record."""
    r = _Reader(data)
    version = r.byte()
    if version != HEADER_VERSION:
        raise Db8Error(f'header version {version}')
    kind_token = r.value()
    rev = r.value()
    if not isinstance(kind_token, int) or not isinstance(rev, int) or isinstance(kind_token, bool):
        raise Db8Error('header kind or revision is not an integer')
    deleted = False
    if r.pos < len(data) and data[r.pos] != MARKER_HEADER_END:
        deleted = r.value()
        if not isinstance(deleted, bool):
            raise Db8Error('header deleted flag is not a boolean')
    # Values the reader does not know about are skipped up to the header end, as
    # MojDbObjectHeader::read does.
    while r.pos < len(data) and data[r.pos] != MARKER_HEADER_END:
        r.value()
    if r.byte() != MARKER_HEADER_END:
        raise Db8Error('header without its end marker')
    return kind_token, rev, deleted, r.pos


STATUS_LIVE = 'Live'
STATUS_SUPERSEDED = 'Superseded (older version of a live key)'
STATUS_REMOVED = 'Removed (key deleted in LevelDB)'


class Db8Object:
    """One version of an object from objects.db.

    ``status`` is STATUS_LIVE for the newest record of a live key, STATUS_SUPERSEDED for an older
    record of a live key, and STATUS_REMOVED for a record whose key's newest LevelDB record is a
    deletion. ``deleted`` is DB8's own deleted flag from the object header."""

    __slots__ = ('id', 'kind', 'kind_token', 'rev', 'deleted', 'body', 'seq', 'origin_file', 'status')

    def __init__(self, obj_id, kind, kind_token, rev, deleted, body, seq, origin_file,
                 status=STATUS_LIVE):
        self.id = obj_id
        self.kind = kind
        self.kind_token = kind_token
        self.rev = rev
        self.deleted = deleted
        self.body = body
        self.seq = seq
        self.origin_file = origin_file
        self.status = status


def _all_records(folder):
    """{user key: [records, oldest first]} for every record in the folder's log and table files."""
    by_key = {}
    db = ccl_leveldb.RawLevelDb(folder)
    try:
        for rec in db.iterate_records_raw():
            by_key.setdefault(rec.user_key, []).append(rec)
    finally:
        db.close()
    for recs in by_key.values():
        recs.sort(key=lambda r: r.seq)
    return by_key


class Db8Store:
    """A DB8 sandwich store read from its LevelDB folder.

    ``parts`` maps each database name to its two-byte cookie, ``kinds`` maps each kind token to
    the kind id, ``tokens`` maps each kind id to its property-name list (index = token - 32), and
    ``errors`` lists (part name, key, reason) for records that did not decode."""

    def __init__(self, folder):
        self.folder = folder
        self._records = _all_records(folder)
        self._live = {k: recs[-1] for k, recs in self._records.items()
                      if recs[-1].state == ccl_leveldb.KeyState.Live}
        self.errors = []
        self.parts = {}
        for key, rec in self._live.items():
            if key[:2] == b'\0\0' and len(key) > 2 and len(rec.value) == 2:
                self.parts[key[2:]] = rec.value
        self.kinds = {}
        self.tokens = {}
        for key, rec in self.part_records(INDEX_IDS_DB):
            obj = self._plain(INDEX_IDS_DB, key, rec)
            if isinstance(obj, dict):
                for kind_id, tok in (obj.get('kindTokens') or {}).items():
                    if isinstance(tok, int):
                        self.kinds[tok] = kind_id
        for key, rec in self.part_records(KINDS_DB):
            obj = self._plain(KINDS_DB, key, rec)
            if not isinstance(obj, dict):
                continue
            kind_id = obj_key(key)
            names = []
            for name, tok in (obj.get('tokens') or {}).items():
                if isinstance(tok, int) and TOKEN_START <= tok < 256:
                    idx = tok - TOKEN_START
                    names.extend([None] * (idx + 1 - len(names)))
                    names[idx] = name
            self.tokens[kind_id] = names

    def is_db8(self):
        """True when the meta part names DB8's objects database."""
        return OBJECTS_DB in self.parts

    def part_records(self, name):
        """(key within the part, record) for every live key in the named part, in key order."""
        cookie = self.parts.get(name)
        if cookie is None:
            return []
        return sorted(((k[2:], r) for k, r in self._live.items() if k[:2] == cookie),
                      key=lambda kr: kr[0])

    def _plain(self, part, key, rec):
        try:
            return decode_value(rec.value)
        except Db8Error as exc:
            self.errors.append((part.decode(), key, str(exc)))
            return None

    def objects(self):
        """Every live objects.db record as a Db8Object, in key order.

        A record that does not decode is added to ``errors`` and skipped."""
        for key, rec in self.part_records(OBJECTS_DB):
            obj = self._decode_object(key, rec, STATUS_LIVE)
            if obj is not None:
                yield obj

    def object_versions(self):
        """Every objects.db record in the files, live or not, in key order and oldest first.

        LevelDB deletion markers carry no object and are not returned, nor is an older record
        whose bytes equal the next record's for the same key. A record that does not decode is
        added to ``errors`` and skipped."""
        cookie = self.parts.get(OBJECTS_DB)
        if cookie is None:
            return
        for key in sorted(k for k in self._records if k[:2] == cookie):
            recs = self._records[key]
            newest = recs[-1]
            key_live = newest.state == ccl_leveldb.KeyState.Live
            for pos, rec in enumerate(recs):
                if rec.state != ccl_leveldb.KeyState.Live:
                    continue
                if rec is not newest and rec.value == recs[pos + 1].value:
                    # The next version holds the same bytes, so this one adds nothing. This also
                    # drops a second copy of one record, which can sit in both a log and a table.
                    continue
                if rec is newest:
                    status = STATUS_LIVE
                elif key_live:
                    status = STATUS_SUPERSEDED
                else:
                    status = STATUS_REMOVED
                obj = self._decode_object(key[2:], rec, status)
                if obj is not None:
                    yield obj

    def _decode_object(self, key, rec, status):
        try:
            obj_id = decode_value(key)
            kind_token, rev, deleted, pos = read_header(rec.value)
            kind = self.kinds.get(kind_token)
            if kind is None:
                raise Db8Error(f'kind token {kind_token} not in indexIds.db')
            r = _Reader(rec.value, pos, self.tokens.get(kind, []))
            if r.byte() != MARKER_OBJECT_BEGIN:
                raise Db8Error('body does not start with an object')
            body = r.object_body()
            if r.pos != len(rec.value):
                raise Db8Error(f'{len(rec.value) - r.pos} bytes after the body')
        except Db8Error as exc:
            self.errors.append(('objects.db', key, str(exc)))
            return None
        return Db8Object(obj_id, kind, kind_token, rev, deleted, body, rec.seq,
                         str(rec.origin_file), status)


def obj_key(key):
    """The object or kind id a part key holds (a serialized string), or its hex if it is not one."""
    try:
        value = decode_value(key)
    except Db8Error:
        return key.hex()
    return value if isinstance(value, str) else str(value)
