"""File names added to and deleted from NTFS directory indexes, read from the $LogFile, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The structures read here are the ones the NTFS-3G project describes in include/ntfs-3g/logfile.h
(RESTART_PAGE_HEADER, RESTART_AREA, RECORD_PAGE_HEADER, LOG_RECORD), include/ntfs-3g/layout.h
(INDEX_ENTRY_HEADER, FILE_NAME_ATTR, FILE_NAME_TYPE_FLAGS) and ntfsprogs/ntfsrecover.[ch] (the operation
numbers, and the first 34 blocks of a version 2 log and first 4 of a version 1 log that it treats as
special), at commit 78414d93613532fd82f3a82aba5d4a1c32898781.
Parent paths come from the $MFT of the same volume.
"""

__artifacts_v2__ = {
    "windowsNtfsLogFile": {
        "name": "NTFS $LogFile File Name Changes",
        "description": "File names added to and deleted from NTFS directory indexes, read from the log "
                       "records of each volume's $LogFile: the name, the file and parent directory "
                       "references, and the times and sizes the directory entry held.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per log record of a volume's $LogFile that adds an entry to an NTFS index or deletes "
                 "one, where the entry it carries is a file name's. The layout is the one the NTFS-3G project "
                 "describes (Reference: NTFS-3G 2022.10.3, "
                 "https://github.com/tuxera/ntfs-3g/blob/78414d93613532fd82f3a82aba5d4a1c32898781/include/ntfs-3g/logfile.h "
                 "for the restart page, restart area, record page and log record, "
                 "https://github.com/tuxera/ntfs-3g/blob/78414d93613532fd82f3a82aba5d4a1c32898781/include/ntfs-3g/layout.h "
                 "for the index entry header and the file name attribute, and "
                 "https://github.com/tuxera/ntfs-3g/blob/78414d93613532fd82f3a82aba5d4a1c32898781/ntfsprogs/ntfsrecover.h "
                 "for the operation numbers). Logs of major version 1 and 2 are read and any other major version "
                 "is named in the run log and not read. ntfsrecover.c treats the first 34 blocks of a version 2 "
                 "log as special, and the first 4 of a version 1 log, and this artifact does the same "
                 "(https://github.com/tuxera/ntfs-3g/blob/78414d93613532fd82f3a82aba5d4a1c32898781/ntfsprogs/ntfsrecover.c). "
                 "A record is taken where a log sequence number names the offset it sits at: the restart area "
                 "gives the number of sequence bits, and the remaining low bits of the number, times 8, are the "
                 "byte offset. One of those special blocks, after the two restart pages, is treated as a copy of a "
                 "page that belongs elsewhere, and its place is taken from its page header as ntfsrecover.c takes "
                 "it: the last log sequence number there in a version 2 log, the file offset there in a version 1 "
                 "log. A record found a second time is reported once. A record's data that runs past its page is "
                 "continued in the next page, except for a record in a special block, which is counted in the run "
                 "log and not reported. Operation is Added for a record whose redo operation is AddIndexEntryRoot "
                 "(12) or AddIndexEntryAllocation (14), read from its redo data, and Deleted for one whose redo "
                 "operation is DeleteIndexEntryRoot (13) or DeleteIndexEntryAllocation (15) and whose undo "
                 "operation is an add, read from its undo data; the words in parentheses say whether the entry was "
                 "in the directory's index root or its index allocation. File Name, Name Space, the file and "
                 "parent references, Created, Modified, Record Changed, Accessed, Data Size, Allocated Size and "
                 "File Attributes are the fields of the file name the entry holds: the four times are its "
                 "creation_time, last_data_change_time, last_mft_change_time and last_access_time read as UTC "
                 "FILETIMEs. A log record holds no time of its own, so none of the four is the time of the "
                 "operation; Record Changed leads the row as one of the entry's four times, not as the time of the "
                 "operation. LSN is the record's log sequence number and Transaction ID its transaction_id, as "
                 "stored; the rows of a file are in LSN order. Parent Path is the path the same volume's $MFT "
                 "gives for the parent reference, and is blank when no $MFT was found beside the log that $MFT no "
                 "longer holds a directory under that record and sequence number, or the directory's own path to "
                 "the root cannot be resolved from that $MFT. A row is a change to a directory index, not a file "
                 "event: a file's creation, deletion and rename each change an index, a file with a short name has "
                 "two entries, and the entry of a name can be removed and added again. An index entry whose key is "
                 "not a file name is counted in the run log and not reported, as are a record page whose update "
                 "sequence does not check, a record whose data runs into such a page, and a record in a special "
                 "block whose data continues past its page. Run on pc_mus_001_win11, lonewolf_win10 and "
                 "szechuan_win10, each with two volumes whose logs are version 2.0, and af_case2_win10, one volume "
                 "whose log is version 1.1: 16,492, 14,353, 2,308 and 2,744 rows. Across the seven logs 240 index "
                 "entries were not a file name, each with a key of 4, 8, 12 or 16 bytes, every delete record "
                 "carried an add as its undo operation, and 78 records in special blocks of the six version 2.0 "
                 "logs continued past their page and were not reported. The rows were compared with the USN "
                 "Journal artifact's rows for the same volume, a separate store that also records names and "
                 "references. On the larger volume of pc_mus_001_win11, of the rows whose Name Space is not DOS, "
                 "4,992 of 4,993 Added rows and 5,127 of 5,127 Deleted rows have a USN record with the same file "
                 "record, sequence and name, and 4,920 and 5,125 of those have a USN record of that name with a "
                 "reason of FILE_CREATE, RENAME_NEW_NAME or HARD_LINK_CHANGE for Added, or FILE_DELETE, "
                 "RENAME_OLD_NAME or HARD_LINK_CHANGE for Deleted; on the larger volume of lonewolf_win10 the same "
                 "figures are 3,777 of 3,783 and 4,053 of 4,058, then 3,772 and 4,048. Parent Path was blank on "
                 "7,998, 868, 63 and 187 rows of the four images. Not read: every other log operation, among them "
                 "the ones that write file records and attributes, and the restart pages' tables. Not exercised on "
                 "real data: a log of a major version other than 1 and 2, a log page size other than 4,096 bytes, "
                 "a record page that does not check, and a log whose $MFT is missing; the first, as version 3.0, "
                 "and the last two were tested with constructed input.",
        "paths": ('*/$LogFile', '*/$MFT'),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, log version 2.0 | 16492 rows",
            "af_case2_win10": "Windows 10 1809 build 17763, log version 1.1 | 2744 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, log version 2.0 | 14353 rows",
            "szechuan_win10": "Windows 10 2004 build 19041, log version 2.0 | 2308 rows",
        },
    },
}

import os
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import FILE_ATTRIBUTES, decode_flags, filetime, mft_index, split_reference

_LABEL = 'NTFS $LogFile File Name Changes'
_SECTOR = 512                                   # the stride of the update sequence array
_SPECIAL_BLOCKS = {1: 4, 2: 34}                 # blocks kept apart, by major version (ntfsrecover.c)
_ADD_ROOT, _DELETE_ROOT, _ADD_ALLOCATION, _DELETE_ALLOCATION = 12, 13, 14, 15
_ADDS = (_ADD_ROOT, _ADD_ALLOCATION)
_DELETES = (_DELETE_ROOT, _DELETE_ALLOCATION)
_NAME_SPACES = {0: 'POSIX', 1: 'Win32', 2: 'DOS', 3: 'Win32 and DOS'}   # FILE_NAME_TYPE_FLAGS
_ENTRY_HEADER = 16                              # INDEX_ENTRY_HEADER
_NAME_FIXED = 66                                # FILE_NAME_ATTR up to the name
_MAX_CLIENT_DATA = 0x100000


def fix_up(page):
    """A log page with its update sequence array applied, or None when the array does not fit the page or a
    sector does not end in the page's sequence number."""
    offset, count = struct.unpack_from('<HH', page, 4)
    if count < 2 or offset + 2 * count > len(page) or (count - 1) * _SECTOR > len(page):
        return None
    number = page[offset:offset + 2]
    fixed = bytearray(page)
    for index in range(1, count):
        end = index * _SECTOR
        if fixed[end - 2:end] != number:
            return None
        fixed[end - 2:end] = page[offset + 2 * index:offset + 2 * index + 2]
    return bytes(fixed)


def file_name_entry(data):
    """An index entry whose key is a file name, as (file reference, parent reference, created, modified,
    record changed, accessed, allocated size, data size, attributes, name space, name), or None when the
    data is not one: shorter than an entry header and a file name, a key length that is not the length of
    a file name of the stated number of characters, a key that runs past the data, or a name space above 3."""
    if len(data) < _ENTRY_HEADER + _NAME_FIXED:
        return None
    reference, _length, key_length = struct.unpack_from('<QHH', data, 0)
    characters, space = data[_ENTRY_HEADER + 64], data[_ENTRY_HEADER + 65]
    if key_length != _NAME_FIXED + 2 * characters or space > 3 or _ENTRY_HEADER + key_length > len(data):
        return None
    (parent, created, modified, changed, accessed, allocated, size,
     attributes) = struct.unpack_from('<QqqqqqqI', data, _ENTRY_HEADER)
    start = _ENTRY_HEADER + _NAME_FIXED
    name = data[start:start + 2 * characters].decode('utf-16-le', 'replace')
    return (reference, parent, created, modified, changed, accessed, allocated, size, attributes, space, name)


class LogFile:
    """The log records of one $LogFile, in the order of the pages that hold their headers."""

    def __init__(self, data):
        self.data = data
        self.counts = {}
        self.problem = ''
        self.major = self.minor = 0
        if data[:4] != b'RSTR' or len(data) < 4096:
            self.problem = 'does not start with a restart page'
            return
        restart = fix_up(data[:4096]) or data[:4096]
        self.page_size, area, self.minor, self.major = struct.unpack_from('<IHhh', restart, 20)
        if area + 40 > len(restart):
            self.problem = 'the restart area lies outside the restart page'
            return
        self.sequence_bits, = struct.unpack_from('<I', restart, area + 16)
        self.header_length, self.data_offset = struct.unpack_from('<HH', restart, area + 36)
        if self.major not in _SPECIAL_BLOCKS:
            self.problem = f'log version {self.major}.{self.minor} is not read'
        elif (self.page_size < 1024 or self.page_size % _SECTOR or not 3 < self.sequence_bits < 64
              or self.header_length < 48 or not 0 < self.data_offset < self.page_size - self.header_length):
            self.problem = 'the restart area holds values a log cannot have'
        else:
            self.special = _SPECIAL_BLOCKS[self.major]
            self.pages = len(data) // self.page_size
            self._fixed = {}

    def _count(self, what, number=1):
        self.counts[what] = self.counts.get(what, 0) + number

    def _page(self, number):
        if number not in self._fixed:
            raw = self.data[number * self.page_size:(number + 1) * self.page_size]
            self._fixed[number] = fix_up(raw) if raw[:4] == b'RCRD' else None
            if raw[:4] == b'RCRD' and self._fixed[number] is None:
                self._count('record pages whose update sequence does not check, not read')
        return self._fixed[number]

    def _offset_of(self, lsn):
        """The byte offset in the file that a log sequence number names: its low bits, in units of 8 bytes."""
        return ((lsn << self.sequence_bits) & 0xFFFFFFFFFFFFFFFF) >> (self.sequence_bits - 3)

    def records(self):
        """(lsn, transaction id, client data) for each record found. A record starts where the 8 bytes at an
        8-byte step are a log sequence number that names that very offset. A block kept apart is treated as
        a copy of a page that belongs elsewhere in the file, and its place is taken from its own page
        header the way ntfsrecover.c takes it: the file offset there in a version 1 log, the last log
        sequence number there in a version 2 log."""
        seen = set()
        for number in range(2, self.pages):
            page = self._page(number)
            if page is None:
                continue
            apart = number < self.special
            base = number * self.page_size
            if apart:
                place, = struct.unpack_from('<q', page, 8)
                if place <= 0:
                    continue
                if self.major >= 2:
                    place = self._offset_of(place)
                base = place // self.page_size * self.page_size
            for offset in range(self.data_offset, self.page_size - self.header_length + 1, 8):
                lsn, = struct.unpack_from('<q', page, offset)
                if lsn <= 0 or self._offset_of(lsn) != base + offset:
                    continue
                length, = struct.unpack_from('<I', page, offset + 24)
                if not 32 <= length <= _MAX_CLIENT_DATA:
                    self._count('record headers with a data length a record cannot have, passed over')
                    continue
                if lsn in seen:
                    self._count('records found a second time in another page, reported once')
                    continue
                seen.add(lsn)
                if apart and offset + self.header_length + length > self.page_size:
                    # the page that follows a copy kept apart is not the block after it
                    self._count('records in a block kept apart whose data continues past its page, not reported')
                    continue
                data = self._client_data(number, page, offset, length)
                if data is None:
                    self._count('records whose data runs into a page that does not check, not reported')
                    continue
                transaction, = struct.unpack_from('<I', page, offset + 36)
                yield lsn, transaction, data

    def _client_data(self, number, page, offset, length):
        start = offset + self.header_length
        data = bytearray(page[start:start + length])
        while len(data) < length:
            number = number + 1 if number + 1 < self.pages else self.special
            page = self._page(number)
            if page is None:
                return None
            data += page[self.data_offset:self.data_offset + length - len(data)]
        return bytes(data)


def name_changes(log):
    """(lsn, transaction id, operation, entry) for each record of a log that adds an index entry or deletes
    one, where the entry it carries is a file name's. A delete carries the entry in its undo data."""
    for lsn, transaction, data in log.records():
        redo, undo, redo_offset, redo_length, undo_offset, undo_length = struct.unpack_from('<HHHHHH', data, 0)
        if redo in _ADDS:
            operation, start, length = 'Added', redo_offset, redo_length
            where = 'index root' if redo == _ADD_ROOT else 'index allocation'
        elif redo in _DELETES and undo in _ADDS:
            operation, start, length = 'Deleted', undo_offset, undo_length
            where = 'index root' if redo == _DELETE_ROOT else 'index allocation'
        else:
            continue
        entry = file_name_entry(data[start:start + length])
        if entry is None:
            log._count('index entries that are not a file name, not reported')  # pylint: disable=protected-access
            continue
        yield lsn, transaction, f'{operation} ({where})', entry


def _member(context, infos, path):
    info = infos.get(path)
    return info.source_path if info else context.get_relative_path(path)


@artifact_processor
def windowsNtfsLogFile(context):
    data_headers = (('Record Changed', 'datetime'), ('Created', 'datetime'), ('Modified', 'datetime'),
                    ('Accessed', 'datetime'), 'Operation', 'File Name', 'Parent Path', 'LSN',
                    'Transaction ID', 'File Record', 'File Sequence', 'Parent Record', 'Parent Sequence',
                    'Data Size', 'Allocated Size', 'File Attributes', 'Name Space', 'Source File')
    results = context.create_artifact_result(headers=data_headers)
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    logs, tables = [], {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        member = _member(context, infos, path)
        if member.endswith('/$MFT') or member == '$MFT':
            tables[os.path.dirname(path)] = path
        elif member.endswith('/$LogFile') or member == '$LogFile':
            logs.append((path, member))
    sources = []
    for path, member in logs:
        try:
            with open(path, 'rb') as handle:
                log = LogFile(handle.read())
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {member}: {type(exc).__name__}')
            continue
        if log.problem:
            logfunc(f'{_LABEL}: {member} {log.problem}')
            continue
        table = tables.get(os.path.dirname(path))
        index = mft_index(table) if table else None
        if index is None:
            logfunc(f'{_LABEL}: no $MFT beside {member}, so parent paths are blank')
        relative = context.get_relative_path(path)
        rows = 0
        for lsn, transaction, operation, entry in sorted(name_changes(log), key=lambda item: item[0]):
            (reference, parent, created, modified, changed, accessed, allocated, size, attributes, space,
             name) = entry
            file_record, file_sequence = split_reference(reference)
            parent_record, parent_sequence = split_reference(parent)
            parent_path = ''
            if index is not None:
                found = index.directory_path(parent)
                parent_path = '' if found is None else '/' + found
            results.add_row((filetime(changed), filetime(created), filetime(modified), filetime(accessed),
                             operation, name, parent_path, lsn, transaction, file_record, file_sequence,
                             parent_record, parent_sequence, size, allocated,
                             decode_flags(attributes, FILE_ATTRIBUTES), _NAME_SPACES[space], relative))
            rows += 1
        if log.counts:
            logfunc(f'{_LABEL}: {member} (log version {log.major}.{log.minor}): '
                    + '; '.join(f'{count:,} {what}' for what, count in sorted(log.counts.items())))
        if rows:
            sources.append(path)
        else:
            logfunc(f'{_LABEL}: no file name changes read from {member}')
    results.set_source_path('\n'.join(sources))
    return results
