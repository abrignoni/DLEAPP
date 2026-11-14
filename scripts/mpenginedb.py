"""Reader for Microsoft Defender's mpenginedb.db (the store its engine calls MetaVault), for DLEAPP.

Author: @AlexisBrignoni, Claude.

What this file does, and what it takes from others
--------------------------------------------------
The database is SQLite with every page and every WAL frame body encrypted by RC4 with one
fixed 256-byte key, restarted for each page, which makes the keystream the same for every
page. Page 1 leaves bytes 16 to 23 (page size, versions, reserved bytes and payload
fractions) in the clear. The WAL frame headers are in the clear and SQLite's WAL checksums
run over the stored, encrypted, bytes. All of this was documented by Mato Vlajcic, Luka
Bracun and Dino Bezic of Protokol-7 in "Defender's hidden flight recorder: decrypting
mpenginedb.db" (2026-11-10,
https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html),
and their parser https://github.com/Protokol-7/mpenginedb_parser (commit
883961c31c0919f0778aff447406a301c9c45933) holds the key as a built-in constant, which is the
KEY below. Their parser is not vendored and was not run here, but this module follows it as
well as the write-up: the page codec (including how page 1 is split around bytes 16 to 23) and
the FILETIME bounds below match theirs, and the WAL replay was checked against SQLite's own
recovery of a plaintext rebuild of the same WAL (see the notes of the artifact that uses this
module).

The 256 key bytes are copied from that repository, which is licensed as follows:

    MIT License. Copyright (c) 2026 Protokol-7. Permission is hereby granted, free of charge,
    to any person obtaining a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions: The above copyright notice and this permission
    notice shall be included in all copies or substantial portions of the Software. THE
    SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
    BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

The key is not assumed. read_database() decrypts only when page 1 comes out as a SQLite
header and its b-tree header reads as a table b-tree page, and it says so when it does not.
The write-up measured the key on one engine build; this module does not claim it holds on
any other, and a file it cannot decrypt is returned with no database and the reason.

The evidence is never written to: both files are read into memory, and the decrypted copy is
written to a temporary folder that Database removes whole, so the -wal and -shm files SQLite
makes beside a database whose header says WAL go with it.
"""

import os
import pathlib
import shutil
import sqlite3
import struct
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

KEY = bytes.fromhex(
    '1e87781b8dbaa844ce69702c0c78b786a3f623b738f5edf9af83530fb3fc54fa'
    'a21eb9cf1331fd0f0da954f687cb9e18279697900e53fb317c9cbce48e23d053'
    '71ecc15951b8f3649d7ca33ed68dc9047e82c9baad9799d0d458cb847ca9ffbe'
    '3c8a775233557dde13a8b14087cc1bc8f10f6ecdd083a959cff84a9d1d50755e'
    '3e191818af23e2293558766d2c07e25712b2ca0b535ed8f6c56ce73d24bdd029'
    '1771861a54b4c285a9a3db7aca6d224aeacd621db9f2a22ed1e9e11d75bed7dc'
    '0ecb0a8e68a2ff1263408dc808dffd164b116774cd0b9b8d05411ed6262e429b'
    'a495676b8398db2f35d3c1b9ced52636f2765e1a95cb7ca4c3ddabddbff38253')
MAGIC = b'SQLite format 3\x00'
_WAL_MAGICS = (0x377F0682, 0x377F0683)
_TABLE_PAGE_TYPES = (0x05, 0x0D)
_BTREE_TYPES = (0x02, 0x05, 0x0A, 0x0D)
_PAGE_SIZES = tuple(1 << n for n in range(9, 17))


@dataclass
class Result:
    """What read_database() found. plain is the decrypted database (WAL applied) as bytes, or
    None when the file was not read; reason says why, in words fit for the run log."""
    plain: bytes = None
    reason: str = ''
    page_size: int = 0
    pages_in_file: int = 0
    pages_after_wal: int = 0
    wal_present: bool = False
    wal_frames: int = 0
    wal_valid_frames: int = 0
    wal_applied_frames: int = 0
    wal_notes: list = field(default_factory=list)


def rc4_keystream(key, count):
    """The first count bytes of the RC4 keystream for key."""
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) & 255
        state[i], state[j] = state[j], state[i]
    i = j = 0
    out = bytearray(count)
    for n in range(count):
        i = (i + 1) & 255
        j = (j + state[i]) & 255
        state[i], state[j] = state[j], state[i]
        out[n] = state[(state[i] + state[j]) & 255]
    return bytes(out)


def _xor(data, stream):
    return bytes(a ^ b for a, b in zip(data, stream))


def decrypt_page(data, page_number, keystream, page_size):
    """One page, or one WAL frame body, back to plaintext. Page 1 keeps bytes 16 to 23 as
    stored and the bytes either side of them are decrypted from the start of the keystream."""
    if page_number != 1:
        return _xor(data, keystream)
    return (_xor(data[:16], keystream[:16]) + data[16:24]
            + _xor(data[24:], keystream[:page_size - 24]))


def _checksum(data, s0, s1, big_endian):
    """SQLite's WAL checksum (sqlite.org/fileformat2.html, 'Checksum Algorithm')."""
    words = struct.unpack(('>' if big_endian else '<') + '%dI' % (len(data) // 4), data)
    for i in range(0, len(words), 2):
        s0 = (s0 + words[i] + s1) & 0xFFFFFFFF
        s1 = (s1 + words[i + 1] + s0) & 0xFFFFFFFF
    return s0, s1


def _wal_frames(wal):
    """(header info, frames) of a WAL held as stored. Each frame is (index, page number,
    commit size, valid, body). A frame is valid when its salts equal the header's and the
    checksum chain, computed over the stored bytes, holds up to and including it."""
    magic, version, wal_page_size, _seq, salt1, salt2, c1, c2 = struct.unpack('>8I', wal[:32])
    big = bool(magic & 1)
    s0, s1 = _checksum(wal[:24], 0, 0, big)
    header = {'magic': magic, 'version': version, 'page_size': wal_page_size, 'salt': (salt1, salt2),
              'header_checksum_ok': (s0, s1) == (c1, c2)}
    frames, chain, offset = [], header['header_checksum_ok'], 32
    while wal_page_size and offset + 24 + wal_page_size <= len(wal):
        number, commit, f1, f2, k1, k2 = struct.unpack('>6I', wal[offset:offset + 24])
        body = wal[offset + 24:offset + 24 + wal_page_size]
        valid = False
        if chain and number >= 1 and (f1, f2) == (salt1, salt2):
            t0, t1 = _checksum(wal[offset:offset + 8], s0, s1, big)
            t0, t1 = _checksum(body, t0, t1, big)
            if (t0, t1) == (k1, k2):
                valid, s0, s1 = True, t0, t1
        chain = valid
        frames.append((len(frames) + 1, number, commit, valid, body))
        offset += 24 + wal_page_size
    return header, frames


def _looks_like_a_database(pages):
    """True when page 1 reads as a table b-tree page after its 100-byte header and at least
    half of up to the next 16 pages open with a b-tree page type byte."""
    if not pages or len(pages[0]) < 101 or pages[0][100] not in _TABLE_PAGE_TYPES:
        return False
    rest = [page for page in pages[1:17] if page]
    return not rest or sum(1 for page in rest if page[0] in _BTREE_TYPES) * 2 >= len(rest)


def read_database(db_bytes, wal_bytes=None, key=KEY):
    """Decrypt the database, then replay the committed frames of its WAL over it.

    Frames are taken in order up to the last valid commit frame and the later version of a
    page wins, which is how SQLite reads a WAL. The size after the replay is the commit size
    of that frame. Frames after the chain breaks, uncommitted frames and frames from an
    older generation of the WAL (other salts) are not applied.
    """
    result = Result()
    if len(db_bytes) < 512 or _xor(db_bytes[:16], rc4_keystream(key, 16)) != MAGIC:
        result.reason = 'page 1 does not decrypt to a SQLite header with the key this reader holds'
        return result
    page_size = struct.unpack('>H', db_bytes[16:18])[0]
    page_size = 65536 if page_size == 1 else page_size
    if page_size not in _PAGE_SIZES:
        result.reason = f'the clear page-size field of page 1 reads {page_size}, not a SQLite page size'
        return result
    keystream = rc4_keystream(key, page_size)
    count = len(db_bytes) // page_size
    pages = [decrypt_page(db_bytes[n * page_size:(n + 1) * page_size], n + 1, keystream, page_size)
             for n in range(count)]
    if not _looks_like_a_database(pages):
        result.reason = ('page 1 decrypts to a SQLite header but its b-tree header, or the first '
                         'pages after it, do not read as b-tree pages')
        return result
    result.page_size, result.pages_in_file, result.pages_after_wal = page_size, count, count
    if len(db_bytes) % page_size:
        result.wal_notes.append(f'{len(db_bytes) % page_size} byte(s) after the last whole page '
                                'of the database file were not read')
    if wal_bytes and len(wal_bytes) >= 32:
        result.wal_present = True
        magic = struct.unpack('>I', wal_bytes[:4])[0]
        if magic not in _WAL_MAGICS:
            result.wal_notes.append(f'WAL magic {magic:08x} is not a SQLite WAL; not applied')
        else:
            header, frames = _wal_frames(wal_bytes)
            result.wal_frames = len(frames)
            result.wal_valid_frames = sum(1 for frame in frames if frame[3])
            if header['page_size'] != page_size:
                result.wal_notes.append(f"WAL page size {header['page_size']} differs from the "
                                        f'database page size {page_size}; not applied')
            elif header['version'] != 3007000:
                result.wal_notes.append(f"WAL format version {header['version']} is not 3007000; not applied")
            elif not header['header_checksum_ok']:
                result.wal_notes.append('WAL header checksum does not match; not applied')
            else:
                last = max([f[0] for f in frames if f[3] and f[2]] or [0])
                size = frames[last - 1][2] if last else 0
                for _index, number, _commit, valid, body in frames[:last]:
                    # A page past the final committed size does not exist once the WAL is applied.
                    if not valid or number > size:
                        continue
                    while len(pages) < number:
                        pages.append(bytes(page_size))
                    pages[number - 1] = decrypt_page(body, number, keystream, page_size)
                    result.wal_applied_frames += 1
                if size:
                    del pages[size:]
                    while len(pages) < size:
                        pages.append(bytes(page_size))
                result.pages_after_wal = len(pages)
    plain = bytearray(b''.join(pages))
    plain[28:32] = struct.pack('>I', len(pages))
    result.plain = bytes(plain)
    return result


def shm_summary(shm_bytes):
    """(frames in the WAL index, database size in pages) from the first copy of the WAL index
    header of an -shm file, or None when it is too short or its version field is not SQLite's.
    Read as bytes; SQLite never opens the file."""
    if not shm_bytes or len(shm_bytes) < 32:
        return None
    version, _unused, _change, _init, _big, _page, max_frame, pages = struct.unpack(
        '<IIIBBHII', shm_bytes[:24])
    return (max_frame, pages) if version == 3007000 else None


_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
# A FILETIME outside 1980-01-01 to 2107-01-01 is not read as a time. The same bounds are the
# ones Protokol-7's parser uses; no row on the seven corpus images that holds the file was
# measured to need a wider range for the columns this reader converts.
_FILETIME_MIN, _FILETIME_MAX = 119600064000000000, 159793632000000000


def filetime(value):
    """A 100-nanosecond count since 1601-01-01 UTC as an aware datetime, or '' when the value
    is not an integer or is 0 or lies outside 1980 to 2107. Sub-microsecond digits are dropped."""
    if isinstance(value, bool) or not isinstance(value, int):
        return ''
    if not _FILETIME_MIN <= value < _FILETIME_MAX:
        return ''
    return _FILETIME_EPOCH + timedelta(microseconds=value // 10)


class Database:
    """A decrypted copy of one mpenginedb.db, open read-only for the length of a with block.
    The copy is a temporary file that is removed on exit; the evidence is not touched."""

    def __init__(self, plain):
        self.plain, self.path, self.folder, self.connection = plain, None, None, None

    def __enter__(self):
        self.folder = tempfile.mkdtemp(prefix='mpenginedb_')
        self.path = os.path.join(self.folder, 'mpenginedb.db')
        with open(self.path, 'wb') as out:
            out.write(self.plain)
        self.connection = sqlite3.connect(pathlib.Path(self.path).as_uri() + '?mode=ro', uri=True)
        return self

    def __exit__(self, *_exc):
        if self.connection is not None:
            self.connection.close()
        shutil.rmtree(self.folder, ignore_errors=True)
        return False

    def table_columns(self, table):
        """The column names of table in the order the schema gives them, [] when it is absent."""
        try:
            return [row[1] for row in self.connection.execute(f'PRAGMA table_info("{table}")')]
        except sqlite3.DatabaseError:
            return []

    def count(self, table):
        """What SELECT count(*) says for table, or None when the query fails. SQLite may answer
        it from an index, so it can differ from the number of rows the table itself holds."""
        try:
            return self.connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        except sqlite3.DatabaseError:
            return None

    def rows(self, table, wanted):
        """(rows, error, missing) for the wanted columns of table. rows are dicts in the order
        the table's b-tree gives them; a wanted column the table does not have comes back None
        and is listed in missing. A table whose pages stop reading part-way returns the rows
        read before the error, and error holds the error text; it is '' on a clean read."""
        try:
            present = [row[1] for row in self.connection.execute(f'PRAGMA table_info("{table}")')]
        except sqlite3.DatabaseError as exc:
            return [], f'the schema could not be read: {exc}', list(wanted)
        if not present:
            return [], 'table not present', list(wanted)
        missing = [name for name in wanted if name not in present]
        select = ', '.join(f'"{name}"' if name in present else f'NULL AS "{name}"' for name in wanted)
        rows, error = [], ''
        try:
            # NOT INDEXED keeps SQLite on the table's own b-tree. A query that asks only for
            # indexed columns would otherwise walk an index, which can disagree with the table
            # when pages of the two come from different moments (see read_database).
            cursor = self.connection.execute(f'SELECT {select} FROM "{table}" NOT INDEXED')
            while True:
                row = cursor.fetchone()
                if row is None:
                    break
                rows.append(dict(zip(wanted, row)))
        except sqlite3.DatabaseError as exc:
            error = str(exc)
        return rows, error, missing
