"""Readers for eMule's .met files, AC_SearchStrings.dat, shareddir.dat and preferences.dat.

Each reader follows the eMule 0.72a source it names (commit ac3d52eafd88e9f6d9e0c2204c6dbead18db750b of
https://github.com/irwir/eMule). Readers take bytes and raise EmuleFormatError when the bytes do not fit
the layout, so a caller decides what to log.
"""

import struct

SOURCE = 'https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/'

# Tag types, opcodes.h
TAGTYPE_HASH = 0x01
TAGTYPE_STRING = 0x02
TAGTYPE_UINT32 = 0x03
TAGTYPE_FLOAT32 = 0x04
TAGTYPE_BOOL = 0x05
TAGTYPE_BOOLARRAY = 0x06
TAGTYPE_BLOB = 0x07
TAGTYPE_UINT16 = 0x08
TAGTYPE_UINT8 = 0x09
TAGTYPE_UINT64 = 0x0B
TAGTYPE_STR1 = 0x11
TAGTYPE_STR16 = 0x20

# File tag names, opcodes.h
FT_FILENAME = 0x01
FT_FILESIZE = 0x02
FT_LASTSEENCOMPLETE = 0x05
FT_TRANSFERRED = 0x08
FT_GAPSTART = 0x09
FT_GAPEND = 0x0A
FT_STATUS = 0x14
FT_CATEGORY = 0x53
FT_KADLASTPUBLISHSRC = 0x21
FT_AICH_HASH = 0x27
FT_LASTSHARED = 0x34
FT_ATTRANSFERRED = 0x50
FT_ATREQUESTED = 0x51
FT_ATACCEPTED = 0x52
FT_ATTRANSFERREDHI = 0x54
FT_FILESIZE_HI = 0x3A

MET_HEADER = 0x0E
MET_HEADER_I64TAGS = 0x0F
PARTFILE_VERSION = 0xE0
PARTFILE_VERSION_LARGEFILE = 0xE2
PREFFILE_VERSION = 0x14
MAX_PARTS = 0x4000000000 // 9728000 + 1  # MAX_EMULE_FILE_SIZE / PARTSIZE + 1, FileIdentifier.cpp


class EmuleFormatError(ValueError):
    """The bytes do not fit the eMule layout being read."""


class _Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise EmuleFormatError(f'read of {size} bytes at offset {self.pos} passes the end ({len(self.data)})')
        chunk = self.data[self.pos:self.pos + size]
        self.pos += size
        return chunk

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack('<H', self.take(2))[0]

    def u32(self):
        return struct.unpack('<I', self.take(4))[0]

    def u64(self):
        return struct.unpack('<Q', self.take(8))[0]


def decode_string(raw):
    """eMule's string rule for files it reads with bOptUTF8 false (SafeFile.cpp, CFileDataIO::ReadString):
    UTF-8 when the bytes start with a UTF-8 byte order mark, else the computer's ANSI code page, which the
    file does not record. Without a mark this returns UTF-8 when the bytes are valid UTF-8 (true of plain
    ASCII) and Windows-1252 otherwise."""
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw[3:].decode('utf-8', 'replace')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1252', 'replace')


def read_tag(reader):
    """One tag, following CTag::CTag(CFileDataIO&, bool) in Packets.cpp. Returns (name, value) where name
    is an int for a one-byte tag name and bytes for a longer one."""
    tag_type = reader.u8()
    if tag_type & 0x80:
        tag_type &= 0x7F
        name = reader.u8()
    else:
        length = reader.u16()
        name = reader.u8() if length == 1 else reader.take(length)
    if tag_type == TAGTYPE_STRING:
        value = decode_string(reader.take(reader.u16()))
    elif TAGTYPE_STR1 <= tag_type <= TAGTYPE_STR16:
        value = decode_string(reader.take(tag_type - TAGTYPE_STR1 + 1))
    elif tag_type == TAGTYPE_UINT32:
        value = reader.u32()
    elif tag_type == TAGTYPE_UINT64:
        value = reader.u64()
    elif tag_type == TAGTYPE_UINT16:
        value = reader.u16()
    elif tag_type == TAGTYPE_UINT8:
        value = reader.u8()
    elif tag_type == TAGTYPE_FLOAT32:
        value = struct.unpack('<f', reader.take(4))[0]
    elif tag_type == TAGTYPE_HASH:
        value = reader.take(16)
    elif tag_type == TAGTYPE_BOOL:
        value = reader.take(1)
    elif tag_type == TAGTYPE_BOOLARRAY:
        value = reader.take(reader.u16() // 8 + 1)
    elif tag_type == TAGTYPE_BLOB:
        value = reader.take(reader.u32())
    else:
        # eMule reads nothing for an unknown type, so its position, and ours, is lost from here.
        raise EmuleFormatError(f'unknown tag type 0x{tag_type:02x} at offset {reader.pos}')
    return name, value


def _read_tags(reader):
    count = reader.u32()
    tags = {}
    gaps = {}
    for _ in range(count):
        name, value = read_tag(reader)
        if isinstance(name, bytes) and name[:1] in (bytes([FT_GAPSTART]), bytes([FT_GAPEND])):
            gaps.setdefault(name[1:], {})[name[0]] = value
        elif name not in tags:
            tags[name] = value
    return tags, gaps


def _read_hashset(reader):
    """CFileIdentifier::LoadMD4HashsetFromFile: the file hash, a part count and that many part hashes."""
    file_hash = reader.take(16)
    parts = reader.u16()
    if parts > MAX_PARTS:
        raise EmuleFormatError(f'{parts} part hashes is more than eMule accepts')
    reader.take(16 * parts)
    return file_hash


def _int(value):
    return value if isinstance(value, int) else None


def read_known_met(data):
    """known.met: KnownFileList.cpp LoadKnownFiles and KnownFile.cpp LoadFromFile. Yields one dict per
    record: modified (the uint32 date), hash, name, size, aich, last_shared, transferred, requests,
    accepts, kad_source_published."""
    reader = _Reader(data)
    header = reader.u8()
    if header not in (MET_HEADER, MET_HEADER_I64TAGS):
        raise EmuleFormatError(f'header 0x{header:02x} is not a known.met header')
    for _ in range(reader.u32()):
        modified = reader.u32()
        file_hash = _read_hashset(reader)
        tags, _gaps = _read_tags(reader)
        transferred = _int(tags.get(FT_ATTRANSFERRED))
        high = _int(tags.get(FT_ATTRANSFERREDHI))
        if transferred is not None and high is not None:
            transferred |= high << 32
        yield {
            'modified': modified, 'hash': file_hash, 'name': tags.get(FT_FILENAME),
            'size': _int(tags.get(FT_FILESIZE)), 'aich': tags.get(FT_AICH_HASH),
            'last_shared': _int(tags.get(FT_LASTSHARED)), 'transferred': transferred,
            'requests': _int(tags.get(FT_ATREQUESTED)), 'accepts': _int(tags.get(FT_ATACCEPTED)),
            'kad_source_published': _int(tags.get(FT_KADLASTPUBLISHSRC)),
        }


def read_part_met(data):
    """A download's <n>.part.met, as SavePartFile in PartFile.cpp writes it (versions 0xE0 and 0xE2:
    version, date, hashset, tags). The older layouts LoadPartFile still accepts (0xE1, the eDonkey style
    and Shareaza's) raise EmuleFormatError."""
    reader = _Reader(data)
    version = reader.u8()
    if version not in (PARTFILE_VERSION, PARTFILE_VERSION_LARGEFILE):
        raise EmuleFormatError(f'part.met version 0x{version:02x} is not one this reader handles')
    if version == PARTFILE_VERSION and len(data) >= 28 and struct.unpack_from('<I', data, 24)[0] == 0x01020000:
        raise EmuleFormatError('eDonkey "old part style" part.met is not handled')
    modified = reader.u32()
    file_hash = _read_hashset(reader)
    tags, gaps = _read_tags(reader)
    size = _int(tags.get(FT_FILESIZE))
    high = _int(tags.get(FT_FILESIZE_HI))
    if size is not None and high is not None:
        size |= high << 32
    return {
        'version': version, 'modified': modified, 'hash': file_hash, 'name': tags.get(FT_FILENAME),
        'size': size, 'transferred': _int(tags.get(FT_TRANSFERRED)), 'status': _int(tags.get(FT_STATUS)), 'category': _int(tags.get(FT_CATEGORY)),
        'last_seen_complete': _int(tags.get(FT_LASTSEENCOMPLETE)), 'aich': tags.get(FT_AICH_HASH),
        'gaps': len(gaps),
    }


def read_utf16_lines(data, allow_ansi=False):
    """AC_SearchStrings.dat (CustomAutoComplete.cpp SaveList, LoadList refuses a file without the mark) and
    shareddir.dat (Preferences.cpp SavePreferences and Init): a UTF-16LE byte order mark, then one item per
    CRLF-ended line. eMule also reads a shareddir.dat without the mark as ANSI text (allow_ansi), decoded
    here as decode_string does."""
    if data.startswith(b'\xff\xfe'):
        text = data[2:].decode('utf-16-le', 'replace')
    elif allow_ansi:
        text = decode_string(data)
    else:
        raise EmuleFormatError('no UTF-16LE byte order mark')
    return [line.strip(' \r\n') for line in text.split('\n') if line.strip(' \r\n')]


def read_preferences_dat(data):
    """preferences.dat: Preferences_Ext_Struct (Preferences.h), a version byte then the 16-byte user hash.
    Returns (version, user hash as hex, marked), where marked says whether byte 5 is 0x0E and byte 14 is
    0x6F, the values CPreferences::CreateUserHash sets (Preferences.cpp). The hash is returned either way."""
    if len(data) < 17:
        raise EmuleFormatError('shorter than a version byte and a user hash')
    user_hash = data[1:17]
    return data[0], user_hash.hex(), user_hash[5] == 0x0E and user_hash[14] == 0x6F


def read_download_overview(data):
    """downloads.txt and downloads.bak, as CDownloadQueue::ExportPartMetFilesOverview (DownloadQueue.cpp)
    writes them: a UTF-16LE mark, a Date line in the computer's local time and locale format, a Directory
    line when there is one temp folder, a header, then one tab-separated part file and eD2K link per
    line. Returns (date text, directory text, [(part file, link)])."""
    lines = read_utf16_lines(data)
    date = directory = ''
    entries = []
    for line in lines:
        if line.startswith('Date:'):
            date = line[5:].strip()
        elif line.startswith('Directory:'):
            directory = line[10:].strip()
        elif '\t' in line and 'ed2k://' in line.lower():
            part, link = line.split('\t', 1)
            entries.append((part.strip(), link.strip()))
    return date, directory, entries


def parse_file_link(link):
    """(name, size, hash) from an ed2k://|file|name|size|hash|... link, or None."""
    parts = link.split('|')
    if len(parts) < 5 or parts[1].lower() != 'file':
        return None
    try:
        size = int(parts[3])
    except ValueError:
        size = None
    return parts[2], size, parts[4].lower()


def ini_values(text, section, keys):
    """The first value of each key in [section] of an ini file's text, compared without case."""
    wanted = {key.lower(): key for key in keys}
    found, current = {}, None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            current = stripped[1:-1].strip().lower()
            continue
        if current != section.lower() or '=' not in stripped:
            continue
        key, value = stripped.split('=', 1)
        key = key.strip().lower()
        if key in wanted and wanted[key] not in found:
            found[wanted[key]] = value.strip()
    return found
