"""NTFS metadata readers for DLEAPP: the master file table ($MFT), the volume's
security descriptors ($Secure:$SDS), the USN change journal
($Extend/$UsnJrnl:$J) and the Zone.Identifier stream a file can carry.

Author: @AlexisBrignoni, Claude.

Every layout here comes from a published description, cited where it is used,
and none is ported from another tool's code:

- $MFT records, attribute headers, $STANDARD_INFORMATION, $FILE_NAME and the
  $Secure:$SDS entries: the Linux-NTFS project's NTFS documentation (Richard
  Russon and Yuval Fledel), https://github.com/flatcap/ntfs-docs at commit
  641edd36dc5f6b62c2aae6658c5a60a4d6d3fe29. qnxprobe reads NTFS from the same
  documentation.
- USN_RECORD_V2 and USN_RECORD_V3, their reason and source flags: Microsoft's
  Win32 API documentation, https://github.com/MicrosoftDocs/sdk-api at commit
  a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021,
  sdk-api-src/content/winioctl/ns-winioctl-usn_record_v2.md and _v3.md.
- File attribute flags: https://github.com/MicrosoftDocs/win32 at commit
  e103fa4e8810bd8d42c4777e17081e24dbe62dbd,
  desktop-src/FileIO/file-attribute-constants.md lines 53 to 74.
- URLZONE values: Wine's include/urlmon.idl, https://github.com/wine-mirror/wine
  at commit 4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf, lines 1458 to 1470.

The readers take bytes or a file handle and return plain values, so the
artifacts decide what to report and the tests can drive them without a report.
Nothing here writes anywhere.
"""

import os
import re
import struct
from datetime import datetime, timedelta, timezone

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_FILETIME_EPOCH_TICKS = 116444736000000000
_REFERENCE_MASK = 0xFFFFFFFFFFFF                # low 48 bits: the record number

ROOT_RECORD = 5                                 # the root directory's MFT record


def filetime(value):
    """A FILETIME (100 ns ticks since 1601-01-01 UTC) as an aware datetime, or ''
    for zero or a value outside what datetime can hold."""
    if not value:
        return ''
    try:
        return _UNIX_EPOCH + timedelta(microseconds=(value - _FILETIME_EPOCH_TICKS) // 10)
    except (OverflowError, ValueError):
        return ''


def split_reference(reference):
    """(record number, sequence number) from a 64-bit NTFS file reference, whose
    low 48 bits are the record and top 16 the sequence (file_reference.html)."""
    return reference & _REFERENCE_MASK, reference >> 48


# ---- flag tables ---------------------------------------------------------------

# File attribute flags, MicrosoftDocs/win32 file-attribute-constants.md lines 53 to 74.
# 0x00040000 is documented twice there, as FILE_ATTRIBUTE_EA and as
# FILE_ATTRIBUTE_RECALL_ON_OPEN, so it is named as both.
FILE_ATTRIBUTES = (
    (0x00000001, 'Read-only'),
    (0x00000002, 'Hidden'),
    (0x00000004, 'System'),
    (0x00000010, 'Directory'),
    (0x00000020, 'Archive'),
    (0x00000040, 'Device'),
    (0x00000080, 'Normal'),
    (0x00000100, 'Temporary'),
    (0x00000200, 'Sparse file'),
    (0x00000400, 'Reparse point'),
    (0x00000800, 'Compressed'),
    (0x00001000, 'Offline'),
    (0x00002000, 'Not content indexed'),
    (0x00004000, 'Encrypted'),
    (0x00008000, 'Integrity stream'),
    (0x00010000, 'Virtual'),
    (0x00020000, 'No scrub data'),
    (0x00040000, 'EA or recall on open'),
    (0x00080000, 'Pinned'),
    (0x00100000, 'Unpinned'),
    (0x00400000, 'Recall on data access'),
)

# USN_REASON_* flags, ns-winioctl-usn_record_v2.md lines 194 to 463. Each is
# named after its constant.
USN_REASONS = (
    (0x00000001, 'DATA_OVERWRITE'),
    (0x00000002, 'DATA_EXTEND'),
    (0x00000004, 'DATA_TRUNCATION'),
    (0x00000010, 'NAMED_DATA_OVERWRITE'),
    (0x00000020, 'NAMED_DATA_EXTEND'),
    (0x00000040, 'NAMED_DATA_TRUNCATION'),
    (0x00000100, 'FILE_CREATE'),
    (0x00000200, 'FILE_DELETE'),
    (0x00000400, 'EA_CHANGE'),
    (0x00000800, 'SECURITY_CHANGE'),
    (0x00001000, 'RENAME_OLD_NAME'),
    (0x00002000, 'RENAME_NEW_NAME'),
    (0x00004000, 'INDEXABLE_CHANGE'),
    (0x00008000, 'BASIC_INFO_CHANGE'),
    (0x00010000, 'HARD_LINK_CHANGE'),
    (0x00020000, 'COMPRESSION_CHANGE'),
    (0x00040000, 'ENCRYPTION_CHANGE'),
    (0x00080000, 'OBJECT_ID_CHANGE'),
    (0x00100000, 'REPARSE_POINT_CHANGE'),
    (0x00200000, 'STREAM_CHANGE'),
    (0x00400000, 'TRANSACTED_CHANGE'),
    (0x00800000, 'INTEGRITY_CHANGE'),
    (0x80000000, 'CLOSE'),
)

# USN_SOURCE_* flags, ns-winioctl-usn_record_v2.md lines 464 to 538.
USN_SOURCES = (
    (0x00000001, 'DATA_MANAGEMENT'),
    (0x00000002, 'AUXILIARY_DATA'),
    (0x00000004, 'REPLICATION_MANAGEMENT'),
    (0x00000008, 'CLIENT_REPLICATION_MANAGEMENT'),
)

# URLZONE, wine-mirror/wine include/urlmon.idl lines 1462 to 1466.
URL_ZONES = {
    0: 'URLZONE_LOCAL_MACHINE',
    1: 'URLZONE_INTRANET',
    2: 'URLZONE_TRUSTED',
    3: 'URLZONE_INTERNET',
    4: 'URLZONE_UNTRUSTED',
}


def decode_flags(value, table):
    """The names of the set bits, ' | ' joined, with any bit the table does not
    name given as hex so that nothing set is dropped. '' when no bit is set."""
    names = [name for bit, name in table if value & bit]
    known = 0
    for bit, _name in table:
        known |= bit
    unknown = value & ~known
    if unknown:
        names.append(f'0x{unknown:08X}')
    return ' | '.join(names)


# ---- $MFT ---------------------------------------------------------------------
#
# concepts/file_record.html: a record opens with 'FILE', the update sequence
# array's offset and length at 0x04 and 0x06, the sequence number at 0x10, the
# first attribute's offset at 0x14, flags at 0x16 (0x01 in use, 0x02 directory),
# the real and allocated record size at 0x18 and 0x1C, and the base record's
# reference at 0x20, which is zero for a base record. concepts/attribute_header.html
# gives each attribute's type at 0x00, length at 0x04, non-resident flag at 0x08,
# name length and offset at 0x09 and 0x0A, and then either a resident value's
# length and offset at 0x10 and 0x14, or a non-resident attribute's starting VCN
# at 0x10 and real size at 0x30.

_ATTR_STANDARD_INFORMATION = 0x10
_ATTR_ATTRIBUTE_LIST = 0x20
_ATTR_FILE_NAME = 0x30
_ATTR_DATA = 0x80
_ATTR_END = 0xFFFFFFFF
_RECORD_IN_USE = 0x0001
_RECORD_DIRECTORY = 0x0002
_NAMESPACE_DOS = 2


class MftRecord:
    """One MFT record's header and the attributes the artifacts read from it.

    ``names`` holds one (parent reference, namespace, name, four FILETIMEs) per
    $FILE_NAME, ``data_size`` the unnamed $DATA's real size (None when the record
    holds no first extent of it), ``streams`` [(name, size)] for named $DATA.
    The four times of $STANDARD_INFORMATION are FILETIMEs in the order the
    attribute stores them: created, altered, MFT changed, read.
    """

    __slots__ = ('number', 'sequence', 'in_use', 'is_dir', 'base', 'std_times',
                 'security_id', 'names', 'data_size', 'streams', 'has_attribute_list')

    def __init__(self, number, sequence, flags, base):
        self.number = number
        self.sequence = sequence
        self.in_use = bool(flags & _RECORD_IN_USE)
        self.is_dir = bool(flags & _RECORD_DIRECTORY)
        self.base = base
        self.std_times = None
        self.security_id = None
        self.names = []
        self.data_size = None
        self.streams = []
        self.has_attribute_list = False

    def best_name(self):
        """The (parent reference, name, times) a listing shows: a long name
        before its DOS 8.3 alias (concepts/filename_namespace.html), and the
        first $FILE_NAME the record holds among equals."""
        ranked = sorted(self.names, key=lambda item: item[1] == _NAMESPACE_DOS)
        return ranked[0] if ranked else None

    def link_names(self):
        """Every name but the DOS 8.3 aliases: one per hard link."""
        return [item for item in self.names if item[1] != _NAMESPACE_DOS]


def _apply_fixup(record):
    """The record with its update sequence array put back, or None when a
    sector's last two bytes do not carry the sequence number, which is a torn
    write (concepts/fixup.html). The array covers the record in equal strides."""
    if len(record) < 0x30:
        return None
    offset, count = struct.unpack_from('<HH', record, 4)
    if count < 2 or offset + count * 2 > len(record):
        return None
    stride = len(record) // (count - 1)
    if stride < 2:
        return None
    fixed = bytearray(record)
    check = record[offset:offset + 2]
    for index in range(1, count):
        end = index * stride
        if fixed[end - 2:end] != check:
            return None
        fixed[end - 2:end] = record[offset + index * 2:offset + index * 2 + 2]
    return bytes(fixed)


def parse_mft_record(record, number):
    """An MftRecord from one record's bytes, or None when it is not a record
    (no 'FILE' signature, or a failed fixup)."""
    if record[:4] != b'FILE':
        return None
    fixed = _apply_fixup(record)
    if fixed is None:
        return None
    sequence, _links, first, flags, used = struct.unpack_from('<HHHHI', fixed, 0x10)
    base = struct.unpack_from('<Q', fixed, 0x20)[0]
    out = MftRecord(number, sequence, flags, base)
    limit = min(used or len(fixed), len(fixed))
    position = first
    while position + 16 <= limit:
        kind, length = struct.unpack_from('<II', fixed, position)
        if kind == _ATTR_END or length < 16 or position + length > limit:
            break
        _read_attribute(out, fixed, position, kind, length)
        position += length
    return out


def _read_attribute(out, record, position, kind, length):
    non_resident = record[position + 8]
    name_length, name_offset = struct.unpack_from('<BH', record, position + 9)
    name = ''
    if name_length:
        start = position + name_offset
        name = record[start:start + name_length * 2].decode('utf-16-le', 'replace')
    if non_resident:
        if kind == _ATTR_ATTRIBUTE_LIST:
            out.has_attribute_list = True
        elif kind == _ATTR_DATA and length >= 0x38:
            start_vcn = struct.unpack_from('<Q', record, position + 0x10)[0]
            real_size = struct.unpack_from('<Q', record, position + 0x30)[0]
            if start_vcn == 0:              # later extents carry no size
                _add_data(out, name, real_size)
        return
    value_length, value_offset = struct.unpack_from('<IH', record, position + 0x10)
    value = record[position + value_offset:position + value_offset + value_length]
    if kind == _ATTR_STANDARD_INFORMATION and len(value) >= 32:
        out.std_times = struct.unpack_from('<QQQQ', value, 0)
        if len(value) >= 0x38:              # NTFS 3.0 and later (standard_information.html)
            out.security_id = struct.unpack_from('<I', value, 0x34)[0]
    elif kind == _ATTR_FILE_NAME and len(value) >= 0x42:
        parent = struct.unpack_from('<Q', value, 0)[0]
        times = struct.unpack_from('<QQQQ', value, 8)
        name_chars, namespace = value[0x40], value[0x41]
        text = value[0x42:0x42 + name_chars * 2].decode('utf-16-le', 'replace')
        out.names.append((parent, namespace, text, times))
    elif kind == _ATTR_ATTRIBUTE_LIST:
        out.has_attribute_list = True
    elif kind == _ATTR_DATA:
        _add_data(out, name, len(value))


def _add_data(out, name, size):
    if name:
        out.streams.append((name, size))
    else:
        out.data_size = size


def mft_record_size(handle):
    """The size of one record, from the allocated size in record 0's header
    (0x1C), falling back to 1024, the size nearly every volume uses."""
    handle.seek(0)
    head = handle.read(0x20)
    if len(head) >= 0x20 and head[:4] == b'FILE':
        size = struct.unpack_from('<I', head, 0x1C)[0]
        if size in (1024, 2048, 4096):
            return size
    return 1024


def iter_mft(handle):
    """(record number, MftRecord or None) for every record of a $MFT file, in
    order, reading one megabyte at a time."""
    size = mft_record_size(handle)
    handle.seek(0)
    number = 0
    per_read = max(1, (1 << 20) // size)
    while True:
        block = handle.read(size * per_read)
        if not block:
            return
        for index in range(len(block) // size):
            yield number, parse_mft_record(block[index * size:(index + 1) * size], number)
            number += 1


class MftIndex:
    """The directory tree an $MFT describes, and the extension records that
    hold the overflow of other records.

    Only what a path needs is kept for each directory, and each extension
    record whole, since they are few: the index costs a fraction of the $MFT,
    and a listing of every record is made by reading the file a second time and
    handing each record to ``fold``.

    A record whose attributes outgrew it keeps the rest in extension records,
    each naming its base record in its header. ``fold`` adds their names,
    streams and the first extent of an unnamed $DATA to the base record, so a
    file reads the same whichever record its attributes landed in.

    Paths are resolved through each name's parent reference. A reference
    carries the sequence number its parent had when the name was written, and a
    parent whose record now carries another has been reused for something else,
    so the name is not filed under it. NTFS increments the sequence number when
    it frees a record (concepts/file_record.html, "Sequence Number"), so a
    parent that is itself deleted, and not yet reused, carries its reference's
    sequence number plus one, and is followed.
    """

    def __init__(self, handle):
        self.directories = {}               # number -> (sequence, in use, names)
        self.extensions = {}                # base number -> [MftRecord]
        self.records = 0
        pending = []
        for _number, record in iter_mft(handle):
            if record is None:
                continue
            self.records += 1
            if record.base & _REFERENCE_MASK:
                self.extensions.setdefault(record.base & _REFERENCE_MASK, []).append(record)
            elif record.is_dir:
                pending.append(record)
        for record in pending:
            self.fold(record)
            self.directories[record.number] = (
                record.sequence, record.in_use,
                [(name[0], name[1], name[2]) for name in record.names])
        self._paths = {ROOT_RECORD: ''}

    def fold(self, record):
        """Add to a base record what its extension records hold. Returns it."""
        for extension in self.extensions.get(record.number, ()):
            wanted = extension.base >> 48
            if wanted and wanted != record.sequence and not (
                    not record.in_use and record.sequence == (wanted + 1) & 0xFFFF):
                continue                    # written for an earlier use of the record
            record.names.extend(extension.names)
            record.streams.extend(extension.streams)
            if record.data_size is None and extension.data_size is not None:
                record.data_size = extension.data_size
        return record

    def parent_matches(self, reference):
        """The number of the directory a parent reference names, or None when
        that record is not a directory or has been reused since."""
        number, sequence = split_reference(reference)
        parent = self.directories.get(number)
        if parent is None:
            return None
        current, in_use, _names = parent
        if not sequence or current == sequence:
            return number
        if not in_use and current == (sequence + 1) & 0xFFFF:
            return number
        return None

    def directory_path(self, reference):
        """The path of the directory a parent reference names, '' for the root,
        or None when the chain does not reach the root."""
        number = self.parent_matches(reference)
        return None if number is None else self._path_of(number, 0)

    def _path_of(self, number, depth):
        if number in self._paths:
            return self._paths[number]
        entry = self.directories.get(number)
        if entry is None or depth > 256:
            return None
        self._paths[number] = None          # a cycle ends here
        names = sorted(entry[2], key=lambda item: item[1] == _NAMESPACE_DOS)
        if not names:
            return None
        parent = self.parent_matches(names[0][0])
        above = None if parent is None else self._path_of(parent, depth + 1)
        path = None if above is None else (f'{above}/{names[0][2]}' if above else names[0][2])
        self._paths[number] = path
        return path

    def path_of_name(self, name):
        """The full path of one $FILE_NAME entry, or None when its parent chain
        does not reach the root."""
        above = self.directory_path(name[0])
        if above is None:
            return None
        return f'{above}/{name[2]}' if above else name[2]


_INDEX_CACHE = {}


def mft_index(path):
    """The MftIndex of a $MFT file, built once per run and shared: the $MFT and
    USN journal artifacts both need the directory tree, and building it is a
    full read of the file."""
    try:
        stat = os.stat(path)
    except OSError:
        return None
    key = (path, stat.st_size, stat.st_mtime_ns)
    if key not in _INDEX_CACHE:
        _INDEX_CACHE.clear()                # one volume's tree at a time
        with open(path, 'rb') as handle:
            _INDEX_CACHE[key] = MftIndex(handle)
    return _INDEX_CACHE[key]


# ---- $Secure:$SDS -------------------------------------------------------------
#
# files/secure.html: the stream is a run of entries, each a 20-byte header (hash
# at 0x00, security id at 0x04, the entry's own offset in the stream at 0x08,
# its length at 0x10) and a self-relative security descriptor, padded to 16
# bytes. The stream keeps a second copy of each 256 KiB block in the next one.
# attributes/security_descriptor.html: the descriptor's owner SID offset is at
# 0x04, and a SID is a revision byte, a count of sub-authorities, a 48-bit
# big-endian identifier authority and that many 32-bit little-endian
# sub-authorities.

def sid_string(data, offset):
    """A SID at offset as S-1-..., or '' when the bytes cannot hold one."""
    if offset <= 0 or offset + 8 > len(data):
        return ''
    revision, count = data[offset], data[offset + 1]
    if revision != 1 or offset + 8 + count * 4 > len(data):
        return ''
    authority = int.from_bytes(data[offset + 2:offset + 8], 'big')
    subs = struct.unpack_from(f'<{count}I', data, offset + 8)
    return 'S-1-' + '-'.join(str(v) for v in (authority,) + subs)


def sds_owners(data):
    """{security id: owner SID} for every entry of a $Secure:$SDS stream. An
    entry is taken only when the offset it records is the offset it sits at,
    which is what tells an entry from the bytes between entries."""
    owners = {}
    position = 0
    while position + 20 <= len(data):
        _hash, security_id, own_offset, length = struct.unpack_from('<IIQI', data, position)
        if length < 20 or own_offset != position or position + length > len(data):
            position += 16                  # entries sit on 16-byte boundaries
            continue
        if security_id not in owners:
            descriptor = data[position + 20:position + length]
            if len(descriptor) >= 20:
                owner_offset = struct.unpack_from('<I', descriptor, 4)[0]
                owner = sid_string(descriptor, owner_offset)
                if owner:
                    owners[security_id] = owner
        position += (length + 15) & ~15
    return owners


# ---- $UsnJrnl:$J --------------------------------------------------------------
#
# ns-winioctl-usn_record_v2.md gives the fields in order: RecordLength (DWORD),
# MajorVersion and MinorVersion (WORD), FileReferenceNumber and
# ParentFileReferenceNumber (DWORDLONG), Usn (LONGLONG), TimeStamp (a FILETIME
# in UTC), Reason, SourceInfo, SecurityId and FileAttributes (DWORD),
# FileNameLength and FileNameOffset (WORD), FileName. _v3.md is the same with
# the two references widened to 128-bit FILE_ID_128 values. The documentation
# says to step by RecordLength and find the name by FileNameOffset rather than
# by a fixed size, and both are read that way here. Version 4 records describe
# changed ranges of a file and carry no name or time; they are counted, not
# reported.

_USN_V2 = struct.Struct('<IHHQQqqIIIIHH')
_USN_V3 = struct.Struct('<IHH16s16sqqIIIIHH')
_NOT_ZERO = re.compile(rb'[^\x00]')


class UsnRecord:
    """One USN_RECORD_V2 or V3, as stored."""

    __slots__ = ('offset', 'version', 'file_reference', 'parent_reference', 'usn',
                 'timestamp', 'reason', 'source_info', 'security_id', 'attributes', 'name')

    def __init__(self, offset, version, fields):
        self.offset = offset
        self.version = version
        (self.file_reference, self.parent_reference, self.usn, self.timestamp,
         self.reason, self.source_info, self.security_id, self.attributes,
         self.name) = fields


def _usn_reference(raw):
    """A V3 128-bit file id as an int. On NTFS the top 64 bits are zero and the
    rest is the 64-bit reference a V2 record carries."""
    return int.from_bytes(raw, 'little')


def iter_usn(data, counts=None):
    """Every USN_RECORD_V2 and V3 in a $J stream's bytes, in order.

    Stretches of zeros (the unused end of a page, or the front of a journal
    copied with its hole) are skipped to the next non-zero byte. Bytes that do
    not open a record whose length, version and name fit are passed over eight
    at a time, the records' alignment, so a damaged record costs itself and not
    the rest. ``counts``, when a dict, receives 'v4' (range records passed
    over) and 'unparsed' (bytes passed over that were not zero).
    """
    if counts is None:
        counts = {}
    counts.setdefault('v4', 0)
    counts.setdefault('unparsed', 0)
    position, end = 0, len(data)
    while position + 8 <= end:
        length = struct.unpack_from('<I', data, position)[0]
        if length == 0:
            found = _NOT_ZERO.search(data, position)
            if found is None:
                return
            position = found.start() & ~7
            if struct.unpack_from('<I', data, position)[0] == 0:
                position += 8
            continue
        major = struct.unpack_from('<H', data, position + 4)[0]
        record = _read_usn(data, position, length, major)
        if record is None:
            if major == 4 and length % 8 == 0 and position + length <= end and length >= 8:
                counts['v4'] += 1
                position += length
                continue
            counts['unparsed'] += 8
            position += 8
            continue
        yield record
        position += length


def _read_usn(data, position, length, major):
    if length % 8 or position + length > len(data):
        return None
    if major == 2 and length >= _USN_V2.size:
        fields = _USN_V2.unpack_from(data, position)
        file_ref, parent_ref = fields[3], fields[4]
    elif major == 3 and length >= _USN_V3.size:
        fields = _USN_V3.unpack_from(data, position)
        file_ref, parent_ref = _usn_reference(fields[3]), _usn_reference(fields[4])
    else:
        return None
    usn, stamp, reason, source, security, attributes, name_length, name_offset = fields[5:]
    if name_offset + name_length > length or name_length % 2:
        return None
    start = position + name_offset
    name = data[start:start + name_length].decode('utf-16-le', 'replace')
    return UsnRecord(position, major, (file_ref, parent_ref, usn, stamp, reason, source,
                                       security, attributes, name))


# ---- Zone.Identifier ----------------------------------------------------------

def read_zone_identifier(data):
    """[(section, key, value)] for every key=value line of a Zone.Identifier
    stream, in order, the text decoded by its byte order mark and otherwise as
    UTF-8 with anything undecodable replaced."""
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        text = data.decode('utf-16', 'replace')
    else:
        text = data.decode('utf-8-sig', 'replace')
    section, out = '', []
    for line in text.splitlines():
        line = line.strip().strip('\x00')
        if not line or line.startswith((';', '#')):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            continue
        key, sep, value = line.partition('=')
        if sep:
            out.append((section, key.strip(), value.strip()))
    return out
