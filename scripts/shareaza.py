"""Readers for Shareaza's library (Library1.dat, Library2.dat, Library.dat) and download (.sd) files.

Both are MFC CArchive streams written by Shareaza 2.7.10.2, whose source is SVN revision 9696 of
https://sourceforge.net/p/shareaza/code/ (trunk/shareaza). Each reader follows the load branch of the
Serialize function it names, including the guards for older format versions. Readers take bytes and raise
ShareazaFormatError; the library reader attaches what it read before the error.
"""

import struct
from datetime import datetime, timedelta, timezone

SOURCE = 'https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/'
LIBRARY_SER_VERSION = 29     # Library.h
DOWNLOAD_SER_VERSION = 42    # Download.h
TRISTATE = {0: 'Unknown', 1: 'No', 2: 'Yes'}   # Shareaza.idl TRI_UNKNOWN, TRI_FALSE, TRI_TRUE
_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


class ShareazaFormatError(ValueError):
    """The bytes do not fit the layout being read. .partial holds what was read before it."""

    def __init__(self, message, partial=None):
        super().__init__(message)
        self.partial = partial


class _Archive:
    """The CArchive primitives Shareaza uses, little endian."""

    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise ShareazaFormatError(f'read of {size} bytes at offset {self.pos} passes the end ({len(self.data)})')
        chunk = self.data[self.pos:self.pos + size]
        self.pos += size
        return chunk

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack('<H', self.take(2))[0]

    def u32(self):
        return struct.unpack('<I', self.take(4))[0]

    def i32(self):
        return struct.unpack('<i', self.take(4))[0]

    def u64(self):
        return struct.unpack('<Q', self.take(8))[0]

    def count(self):
        """CArchive::ReadCount: a WORD, widened to a DWORD then a QWORD by all-ones escapes."""
        value = self.u16()
        if value != 0xFFFF:
            return value
        value = self.u32()
        return self.u64() if value == 0xFFFFFFFF else value

    def string(self):
        """CString as MFC stores it: a length with escapes, and a 0xFFFE marker before UTF-16 text."""
        unicode = False
        length = self.u8()
        if length == 0xFF:
            length = self.u16()
            if length == 0xFFFE:
                unicode = True
                length = self.u8()
                if length == 0xFF:
                    length = self.u16()
            if length == 0xFFFF:
                length = self.u32()
                if length == 0xFFFFFFFF:
                    length = self.u64()
        if unicode:
            return self.take(length * 2).decode('utf-16-le', 'replace')
        return self.take(length).decode('cp1252', 'replace')

    def filetime(self):
        return filetime(self.u64())

    def hash(self, size):
        """SerializeIn for a hash with BasicValidation (Hashes/Compatibility.hpp): a uint32 valid flag, then
        the bytes only when it is set."""
        return self.take(size).hex() if self.u32() else ''


def filetime(value):
    """A Windows FILETIME as an aware UTC datetime, '' for 0."""
    if not value:
        return ''
    try:
        return _EPOCH + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def _xml(ar):
    """CXMLElement::Serialize (XML.cpp): name, value, attributes, child elements. Returns a flat text form."""
    name = ar.string()
    value = ar.string()
    parts = []
    for _ in range(ar.count()):
        attribute = ar.string()
        parts.append(f'{attribute}={ar.string()}')
    children = [_xml(ar) for _ in range(ar.count())]
    text = name + (f' [{"; ".join(parts)}]' if parts else '') + (f' {value}' if value else '')
    return '; '.join([text] + children)


def _library_file(ar, version):
    """CLibraryFile::Serialize (SharedFile.cpp), load branch."""
    record = {'name': ar.string(), 'index': ar.u32()}
    record['size'] = ar.u64() if version >= 17 else ar.u32()
    record['time'] = ar.filetime()
    record['shared'] = ar.i32() if version >= 5 else (0 if ar.u8() else 1)
    record['virtual_size'] = 0
    if version >= 21:
        record['virtual_size'] = ar.u64()
        if record['virtual_size'] > 0:
            ar.u64()
    record['sha1'] = ar.hash(20)
    record['tiger'] = ar.hash(24) if version >= 8 else ''
    record['md5'] = ar.hash(16) if version >= 11 else ''
    record['ed2k'] = ar.hash(16) if version >= 11 else ''
    record['bth'] = ar.hash(20) if version >= 26 else ''
    if version >= 4:
        ar.i32()                                    # m_bVerify
    record['schema'] = ar.string()
    record['metadata'] = ''
    metadata_auto = False
    if record['schema']:
        if version < 27:
            metadata_auto = bool(ar.u32())
            if not metadata_auto:
                ar.u64()
        record['metadata'] = _xml(ar)
    record['rating'], record['comments'], record['share_tags'] = 0, '', ''
    if version >= 13:
        record['rating'] = ar.i32()
        record['comments'] = ar.string()
        if version >= 16:
            record['share_tags'] = ar.string()
        if version >= 27:
            ar.u32()
            ar.u64()
        elif metadata_auto and (record['rating'] or record['comments']):
            ar.u64()
    record['hits'] = ar.u32()
    record['uploads'] = ar.u32()
    if version >= 14:
        ar.u32()                                    # m_bCachedPreview
    if version >= 20:
        ar.u32()                                    # m_bBogus
    record['sources'] = []
    if version >= 2:
        for _ in range(ar.count()):                 # CSharedSource::Serialize
            url = ar.string()
            if version >= 10:
                seen = ar.filetime()
            else:
                ar.u32()
                seen = ''
            record['sources'].append((url, seen))
    return record


def _library_folder(ar, version, result):
    """CLibraryFolder::Serialize (SharedFolder.cpp), load branch."""
    path = ar.string()
    shared = ar.i32() if version >= 5 else (0 if ar.u8() else 1)
    if version >= 3:
        ar.u32()                                    # m_bExpanded
    result['folders'].append({'path': path, 'shared': shared})
    for _ in range(ar.count()):
        _library_folder(ar, version, result)
    for _ in range(ar.count()):
        record = _library_file(ar, version)
        record['folder'] = path
        record['folder_shared'] = shared
        result['files'].append(record)


def _album(ar, version, root):
    """CAlbumFolder::Serialize (AlbumFolder.cpp), load branch. Read only to reach what follows."""
    ar.string()                                     # schema URI, or an unused string for the root
    if ar.count():
        _xml(ar)
    if version >= 19:
        ar.hash(20)
    if version >= 24:
        ar.hash(16)
    ar.string()
    ar.u32()
    ar.u32()
    if version >= 9:
        ar.string()
    for _ in range(ar.count()):
        _album(ar, version, False)
    for _ in range(ar.count()):
        ar.u32()
    return root


def read_library(data, has_header=True):
    """A library file, as CLibrary::Load and CLibrary::Serialize (Library.cpp) read it.

    Library1.dat and Library2.dat start with the FILETIME of the save (written after the archive); the older
    Library.dat has no such header. Returns a dict: saved, version, folders, files (in a library folder),
    ghosts (CLibraryMaps::Serialize2, LibraryMaps.cpp), history (CLibraryHistory, index to added time),
    complete (the archive ended exactly at the end of the file)."""
    result = {'saved': '', 'version': None, 'folders': [], 'files': [], 'ghosts': [], 'history': {},
              'complete': False}
    ar = _Archive(data)
    try:
        if has_header:
            result['saved'] = ar.filetime()
        version = ar.i32()
        if version < 1 or version > LIBRARY_SER_VERSION:
            raise ShareazaFormatError(f'library version {version} is not 1 to {LIBRARY_SER_VERSION}')
        result['version'] = version
        if version >= 29:
            ar.u32()                                # CLibraryDictionary word count
        ar.u32()                                    # CLibraryMaps next index
        if version >= 28:
            ar.u32()
            ar.u32()
            ar.u32()
        for _ in range(ar.count()):
            _library_folder(ar, version, result)
        if version >= 6:
            _album(ar, version, True)
        for _ in range(ar.count()):                 # CLibraryRecent::Serialize (LibraryHistory.cpp)
            added = ar.filetime()
            result['history'][ar.u32()] = added
        if version > 22 and ar.string():
            ar.string()
            ar.u32()
            ar.take(20)
        if version >= 18:
            for _ in range(ar.count()):
                record = _library_file(ar, version)
                record['folder'] = ''
                record['folder_shared'] = None
                result['ghosts'].append(record)
    except ShareazaFormatError as exc:
        raise ShareazaFormatError(str(exc), result) from exc
    result['complete'] = ar.pos == len(data)
    return result


def read_download(data):
    """The front of a .sd file: the SDL marker and version (CDownload::Serialize, Download.cpp), then
    CDownloadBase::Serialize (DownloadBase.cpp). Nothing after the base fields is read."""
    if data[:3] != b'SDL':
        raise ShareazaFormatError('no SDL marker')
    ar = _Archive(data, 3)
    version = ar.i32()
    if version < 11 or version > DOWNLOAD_SER_VERSION:
        raise ShareazaFormatError(f'download version {version} is not 11 to {DOWNLOAD_SER_VERSION}')
    record = {'version': version, 'name': ar.string()}
    if version >= 29:
        if version >= 33:
            ar.string()                             # search keyword; 2.7.10.2 writes an empty string
        record['size'] = ar.u64()
    else:
        record['size'] = ar.u32()
    record['sha1'] = ar.hash(20)
    ar.u32()
    record['tiger'] = ar.hash(24)
    ar.u32()
    record['md5'], record['ed2k'], record['bth'] = '', '', ''
    if version >= 22:
        record['md5'] = ar.hash(16)
        ar.u32()
    if version >= 13:
        record['ed2k'] = ar.hash(16)
        ar.u32()
    if version >= 37:
        record['bth'] = ar.hash(20)
        ar.u32()
    return record
