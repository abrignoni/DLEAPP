"""Reader for the Windows BITS job store (qmgr.db and its ESE log files), for DLEAPP.

Author: @AlexisBrignoni, Claude.

The Background Intelligent Transfer Service keeps its queue in
ProgramData\\Microsoft\\Network\\Downloader\\qmgr.db, an ESE database with a Jobs table
and a Files table, each holding a GUID Id column and a Blob column. The record layouts
inside the blobs are read here from ANSSI's MIT licensed bits_parser, bits/structs.py at
bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357
(https://github.com/ANSSI-FR/bits_parser/blob/bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357/bits/structs.py),
and FireEye's Apache-2.0 BitsParser at 0a2b51eeec79c5e181d8fc526d5715552299c45f
(https://github.com/fireeye/BitsParser/blob/0a2b51eeec79c5e181d8fc526d5715552299c45f/BitsParser.py),
which applies those structures to qmgr.db. No code is copied from either.

A job blob begins with one of the job marker GUIDs BitsParser lists (L41-L47), then the job
type, priority and state, a 32-bit value, the job's GUID, the name, the description, the two
strings ANSSI calls cmd and args, and the owner SID, each a 32-bit count of UTF-16 code units
and the text, then a 32-bit value ANSSI reads as the notify flags and a block ANSSI calls the
access token, which runs to the transfer marker GUID (L36). After that marker come a 32-bit
count of the job's file GUIDs, the GUIDs, the marker again, the error count and the errors,
three 32-bit values, three FILETIMEs, 14 further bytes and two more FILETIMEs (structs.py
L78-L126 and L151-L183). ANSSI gives an error entry as 25 bytes; the Windows 10 1709 image
tested stores 25 bytes and the later builds tested store 21, so both sizes are tried and the
one that leaves the first two FILETIMEs in range is kept. When both do, or neither does, the
times and errors are left out.

A file blob begins with the file marker GUID (L40), then the local file name, the remote
name and the temporary file name as counted UTF-16LE strings, two 64-bit numbers, one byte,
and the drive and volume strings (structs.py L131-L148).

Records are read from the Jobs and Files tables with ESE's deleted flag. A Blob stored apart
from its record, flagged by the tagged-data flag 0x04, is read from the table's long value
tree, whose entries are keyed by the long value ID (big-endian) alone, holding the total
size, or followed by a big-endian byte offset, holding a piece of the value; BitsParser's ESE
module keys the tree the same way (ese/ese.py at the commit above, L486-L561). Records no
longer in the tables, and older copies, are found by searching the database file and its ESE
logs for the marker GUIDs.
"""

import re
import struct
import uuid
from datetime import datetime, timedelta, timezone

from scripts.vendor import impacket_ese

JOB_MARKERS = tuple(bytes.fromhex(value) for value in (
    'a15609e143afc94292e66f9856eba7f6', '9f95d44c6470f24b84d7476a7e62699f',
    'f11926a93203bf4c9427898818958831', 'c133bcddfb5aaf4db8a12268b39d01ad',
    'd057568f2c013e4ead2cf4a5d7656faf', '5067419457031d46a4cc5dd9990706e4'))
FILE_MARKER = bytes.fromhex('e4cf9e5146d99743b73e268513051ab2')
TRANSFER_MARKER = bytes.fromhex('36da56776f515a43acac44a248fff34d')
ERROR_SIZES = (21, 25)
_MARKER_PATTERN = re.compile(b'|'.join(re.escape(m) for m in JOB_MARKERS + (FILE_MARKER,)))
_SID = re.compile(r'^S-1-\d+(-\d+)*$')
# Largest value of BG_JOB_TYPE, BG_JOB_PRIORITY and BG_JOB_STATE (see the notes).
_LAST_TYPE, _LAST_PRIORITY, _LAST_STATE = 2, 3, 8
_TAGGED_SEPARATED = 0x04
_MAX_STRING = 32768
_MAX_TOKEN = 65536
_MAX_ITEMS = 4096
# FILETIMEs from 1970-01-01 to 2100-01-01: a value outside means the fields around it were
# misread.
_FILETIME_MIN = 116444736000000000
_FILETIME_MAX = 157469184000000000
# ESE record layout of both tables: one fixed column (Id, a GUID), no variable columns.
_RECORD_HEADER = b'\x01\x7f'
# In a Files record, what sits between the Id and the blob when the blob is stored inline:
# the fixed-column null bitmap, the tagged-column entry (column 256 at offset 4) and the
# tagged-data flag byte.
_INLINE_FILE_PREFIX = b'\xfe\x00\x01\x04\x00\x01'


def filetime(value):
    """A FILETIME as a UTC datetime, or '' for zero or an out-of-range value."""
    if not _FILETIME_MIN <= value <= _FILETIME_MAX:
        return ''
    return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value // 10)


def guid_text(raw):
    return str(uuid.UUID(bytes_le=bytes(raw)))


def _counted_text(data, offset):
    """(text, next offset) for a 32-bit UTF-16 code unit count and its text."""
    count, = struct.unpack_from('<I', data, offset)
    end = offset + 4 + 2 * count
    if count > _MAX_STRING or end > len(data):
        raise ValueError('text length out of range')
    text = data[offset + 4:end].decode('utf-16-le')
    if count:
        if not text.endswith('\x00'):
            raise ValueError('text not terminated')
        text = text[:-1]
    if '\x00' in text or not all(char.isprintable() or char in '\t\r\n' for char in text):
        raise ValueError('not text')
    return text, end


def parse_job(data, offset=0):
    """A job record starting at a job marker, as a dict, or None when it does not parse."""
    try:
        return _parse_job(data, offset)
    except (ValueError, struct.error, UnicodeDecodeError):
        return None


def _parse_job(data, offset):
    if data[offset:offset + 16] not in JOB_MARKERS:
        raise ValueError('no job marker')
    position = offset + 16
    job_type, priority, state, unknown = struct.unpack_from('<IIII', data, position)
    position += 16
    if job_type > _LAST_TYPE or priority > _LAST_PRIORITY or state > _LAST_STATE:
        raise ValueError('type, priority or state out of range')
    job = {'marker': data[offset:offset + 16], 'type': job_type, 'priority': priority,
           'state': state, 'unknown': unknown, 'job_id': bytes(data[position:position + 16])}
    if not any(job['job_id']):
        raise ValueError('no job id')
    position += 16
    for name in ('name', 'description', 'program', 'parameters', 'owner'):
        job[name], position = _counted_text(data, position)
    if not _SID.match(job['owner']):
        raise ValueError('owner is not a SID')
    job['flags'], = struct.unpack_from('<I', data, position)
    position += 4
    transfer = data.find(TRANSFER_MARKER, position, position + _MAX_TOKEN)
    if transfer < 0 or _MARKER_PATTERN.search(data, position, transfer):
        raise ValueError('no transfer marker before the next record')
    position = transfer + 16
    count, = struct.unpack_from('<I', data, position)
    position += 4
    if count > _MAX_ITEMS or position + 16 * count + 16 > len(data):
        raise ValueError('file count out of range')
    job['file_ids'] = [bytes(data[position + 16 * i:position + 16 * (i + 1)]) for i in range(count)]
    position += 16 * count
    if data[position:position + 16] != TRANSFER_MARKER:
        raise ValueError('no second transfer marker')
    position += 16
    job['times'], job['errors'], job['error_size'], job['end'] = _job_tail(data, position)
    return job


def _job_tail(data, position):
    """(five FILETIMEs, error codes, error entry size, end) after the second transfer marker.

    Times are () and the errors are not read when neither error entry size leaves the first
    two FILETIMEs in range.
    """
    count, = struct.unpack_from('<I', data, position)
    if count > _MAX_ITEMS:
        return (), [], None, position
    fits = []
    for size in ERROR_SIZES:
        start = position + 4 + size * count
        try:
            first = struct.unpack_from('<QQQ', data, start + 12)
            second = struct.unpack_from('<QQ', data, start + 12 + 24 + 14)
        except struct.error:
            continue
        if all(_FILETIME_MIN <= value <= _FILETIME_MAX for value in first[:2]):
            fits.append((size, first + second, start + 12 + 24 + 14 + 16))
    if len({times for _, times, _ in fits}) != 1:
        return (), [], None, position
    size, times, end = fits[0]
    errors = [struct.unpack_from('<I', data, position + 4 + size * i + 4)[0] for i in range(count)]
    return times, errors, (size if count else None), end


def parse_file(data, offset=0):
    """A file record starting at the file marker, as a dict, or None when it does not parse."""
    try:
        if data[offset:offset + 16] != FILE_MARKER:
            return None
        position = offset + 16
        record = {}
        for name in ('local_name', 'remote_name', 'temporary_name'):
            record[name], position = _counted_text(data, position)
        if not record['local_name'] or not record['remote_name']:
            return None
        record['size_1'], record['size_2'] = struct.unpack_from('<QQ', data, position)
        position += 17
        for name in ('drive', 'volume'):
            record[name], position = _counted_text(data, position)
        record['end'] = position
        return record
    except (ValueError, struct.error, UnicodeDecodeError):
        return None


def find_records(data):
    """Every job and file record the marker GUIDs lead to: (offset, 'job' or 'file', record)."""
    for match in _MARKER_PATTERN.finditer(data):
        offset = match.start()
        if match.group() == FILE_MARKER:
            record = parse_file(data, offset)
            if record is not None:
                prefix = data[offset - 6:offset]
                record['file_id'] = (bytes(data[offset - 22:offset - 6])
                                     if offset >= 22 and prefix == _INLINE_FILE_PREFIX else None)
                yield offset, 'file', record
        else:
            record = parse_job(data, offset)
            if record is not None:
                yield offset, 'job', record


class QmgrDatabase:
    """The live Jobs and Files records of one qmgr.db."""

    def __init__(self, path):
        self._db = impacket_ese.ESENT_DB(path)

    def _table(self, name):
        """(catalog data, root page) of a table, or (None, None).

        openTable hands back a shared dict, so both values are read at once.
        """
        cursor = self._db.openTable(name)
        if cursor is None:
            return None, None
        return cursor['TableData'], cursor['FatherDataPageNumber']

    def _leaves(self, page_number, seen=None):
        """(page, tag flags, tag data) of every leaf tag under a tree's root page.

        Leaf tags flagged deleted are included, and the caller reads the flag; branch tags
        flagged deleted are not followed.
        """
        seen = set() if seen is None else seen
        if page_number in seen:
            return
        seen.add(page_number)
        page = self._db.getPage(page_number)
        leaf = page.record['PageFlags'] & impacket_ese.FLAGS_LEAF
        for number in page.iterDataTagNums():
            flags, data = page.getTag(number)
            if leaf:
                yield page, flags, data
            elif not flags & impacket_ese.TAG_DEFUNCT:
                child = impacket_ese.ESENT_BRANCH_ENTRY(flags, data)['ChildPageNumber']
                yield from self._leaves(child, seen)

    def _long_values(self, table):
        """{key: value} of a table's long value tree, without the entries flagged deleted."""
        values = {}
        for entry in table['LongValues'].values():
            header = impacket_ese.ESENT_DATA_DEFINITION_HEADER(entry['EntryData'])
            root = impacket_ese.ESENT_CATALOG_DATA_DEFINITION_ENTRY(
                entry['EntryData'][len(header):])['FatherDataPageNumber']
            for page, flags, data in self._leaves(root):
                if flags & impacket_ese.TAG_DEFUNCT:
                    continue
                position, common = 0, b''
                if flags & impacket_ese.TAG_COMMON:
                    size, = struct.unpack_from('<H', data, 0)
                    common = page.getTag(0)[1][:size]
                    position = 2
                size, = struct.unpack_from('<H', data, position)
                position += 2
                values[common + data[position:position + size]] = data[position + size:]
        return values

    @staticmethod
    def _long_value(values, reference):
        """The bytes a long value reference points to, or None when they are not all there."""
        key = reference[::-1]
        root = values.get(key)
        if root is None or len(root) < 8:
            return None
        _, total = struct.unpack_from('<II', root, 0)
        pieces = bytearray()
        while len(pieces) < total:
            piece = values.get(key + struct.pack('>I', len(pieces)))
            if not piece:
                return None
            pieces.extend(piece)
        return bytes(pieces[:total])

    def records(self, name):
        """(Id, blob, flagged deleted) of each record in the Jobs or Files table.

        A record flagged deleted carries ESE's fNDDeleted node flag, which ESE reads as not
        present (see the notes). The Id is None when the record does not have the two-column
        layout both tables use, and the blob is None when it cannot be read; both are kept so
        they can be counted.
        """
        table, root = self._table(name)
        if table is None:
            return []
        values = None
        out = []
        for _, flags, data in self._leaves(root):
            deleted = bool(flags & impacket_ese.TAG_DEFUNCT)
            leaf = impacket_ese.ESENT_LEAF_ENTRY(flags, data)['EntryData']
            if leaf[:2] != _RECORD_HEADER or len(leaf) < 26:
                out.append((None, None, deleted))
                continue
            record_id = bytes(leaf[4:20])
            tagged, = struct.unpack_from('<H', leaf, 2)
            column, start = struct.unpack_from('<HH', leaf, tagged)
            start = tagged + (start & 0x3fff)
            if column != 256 or start >= len(leaf):
                out.append((record_id, None, deleted))
                continue
            item_flags, value = leaf[start], bytes(leaf[start + 1:])
            if item_flags & _TAGGED_SEPARATED:
                values = self._long_values(table) if values is None else values
                value = self._long_value(values, value[:4]) if len(value) >= 4 else None
            out.append((record_id, value, deleted))
        return out
