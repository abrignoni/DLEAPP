"""File name entries left in the slack of NTFS directory index blocks ($I30), for DLEAPP.

Author: @AlexisBrignoni, Claude.

The structures read here are the ones the NTFS-3G project describes in include/ntfs-3g/layout.h
(INDEX_BLOCK, INDEX_HEADER, INDEX_ENTRY_HEADER, FILE_NAME_ATTR, FILE_NAME_TYPE_FLAGS), at commit
78414d93613532fd82f3a82aba5d4a1c32898781. Each directory's index allocation is staged by the raw image
seeker as ``<directory>:$I30``, and its index root is read from the volume's $MFT.
"""

__artifacts_v2__ = {
    "windowsNtfsIndexSlack": {
        "name": "NTFS $I30 Index Slack - Unlisted Entries",
        "description": "File name entries found in the unused space of NTFS directory index blocks ($I30) "
                       "whose file reference and name are not in that directory's entry lists now: the name, "
                       "the file reference, the times and sizes the entry held, and how that file's record "
                       "stands in the $MFT now.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per file name entry found in the slack of a directory's $I30 index allocation that is in "
                 "neither of that directory's entry lists now. NTFS keeps a directory's index as a tree: its root "
                 "in the $INDEX_ROOT attribute of the directory's $MFT record, and, once it has grown, index "
                 "blocks in an $INDEX_ALLOCATION attribute. Each block's index header gives where its entry list "
                 "ends (index_length) and how much of the block the list may use (allocated_size), and the space "
                 "between the two can still hold entries the list no longer includes (Reference: NTFS-3G "
                 "2022.10.3, "
                 "https://github.com/tuxera/ntfs-3g/blob/78414d93613532fd82f3a82aba5d4a1c32898781/include/ntfs-3g/layout.h, "
                 "INDEX_ROOT, INDEX_BLOCK, INDEX_HEADER, INDEX_ENTRY_HEADER and FILE_NAME_ATTR). The raw image "
                 "seeker stages each index allocation as stored, under the directory's name followed by :$I30, "
                 "through the vendored reader's directory_index() (qnxprobe 1.63 or later); the block size is "
                 "taken from the header of the first block that starts INDX and each block's update sequence array "
                 "is applied before it is read. In that space an entry is looked for at every 8-byte step and "
                 "taken when it is a file name's: its key length is the length of a file name of the number of "
                 "characters it states, its own length is that key and its header rounded up to 8 bytes, with room "
                 "for a sub-node number at most, and its name space is one of the four. The live entries are those "
                 "of the entry lists of the allocation's blocks and of the directory's index root, read from the "
                 "same volume's $MFT in the record the entries name as their parent, taken by its number, or in an "
                 "in-use record that extends it. A slack entry is left out when its parent reference names another "
                 "record than the live entries do, when it is identical in every field but its length to a live "
                 "entry, when it is a second copy of an entry already taken, and when its file reference and name "
                 "are a live entry (the NTFS $I30 Index Slack - Copies of Live Entries artifact reports those); "
                 "the first three are counted in the run log. When neither entry list holds an entry there is no "
                 "live entry to compare a parent with, and the slack entries are taken as found. File Name, Name "
                 "Space, the file and parent references, Record Changed, Created, Modified, Accessed, Data Size, "
                 "Allocated Size and File Attributes are read from the entry as it lies in the slack, Name Space "
                 "and File Attributes decoded to names and a zero time left blank; the four times are its "
                 "last_mft_change_time, creation_time, last_data_change_time and last_access_time read as UTC "
                 "FILETIMEs. They are the values the entry held when it was last written, not the time it left the "
                 "list: an index entry holds no such time. Directory is the directory's path inside its volume; "
                 "the volume is the first segment of Source File. In Index Now says what of the entry the index "
                 "still lists: File, under another name when the same file reference is a live entry under another "
                 "name; Name, under another file reference when the name is a live entry of another file "
                 "reference; and No when neither is. MFT Record Now compares the $MFT record of the file "
                 "reference's number with its sequence number: Same sequence, in use, with this name when that "
                 "record still holds the name under the same parent record; Same sequence, in use; Same sequence, "
                 "not in use; Sequence one higher, not in use; Another sequence; or No record. Where an entry's "
                 "first 8 bytes read as the last 8 bytes of an end entry (length 16, no key, the end flag), which "
                 "is consistent with the end of an entry list having been written across them, the file reference "
                 "is gone: such a row has File Record and File Sequence blank and Reference overwritten in In "
                 "Index Now and MFT Record Now, and is left out, counted, when its name is a live entry. Index "
                 "Offset is the entry's byte offset in the index allocation. With no $MFT for the volume the index "
                 "roots are not read and the MFT Record Now column is blank. A row shows that an entry with that "
                 "name and that parent record was written in that directory's index allocation and is in neither "
                 "entry list now. It does not say why; the USN records matched below are of deletions and renames. "
                 "Run on pc_mus_001_win11, lonewolf_win10, szechuan_win10 and af_case2_win10, whose volumes gave "
                 "13,158, 5,505, 5,347 and 5,313 index allocations: 11,859, 8,101, 486 and 2,024 rows. Every block "
                 "read was 4,096 bytes; 28, 8, 3 and 3 allocations were empty and 1,304, 805, 431 and 474 blocks "
                 "did not start INDX, none read. Left out as identical to a live entry were 46,194, 46,737, 31,193 "
                 "and 16,461 entries, as second copies 18,528, 17,027, 7,846 and 29,708, and as overwritten "
                 "references whose name is live 921, 205, 111 and 177; none named another record as its parent, "
                 "and every index root was read. In 365, 92, 7 and 22 allocations neither entry list held a file "
                 "name entry, the directories being empty now; their 2,262, 499, 79 and 226 slack entries named "
                 "one parent record in each allocation, and that record held an empty $I30 index root. In Index "
                 "Now was No on 9,172, 6,587, 345 and 1,289 rows, File, under another name on 27, 87, 62 and 26, "
                 "and Name, under another file reference on 2,045, 1,272, 72 and 654. Reference overwritten was on "
                 "615, 155, 7 and 55 rows. MFT Record Now was Another sequence on 2,919, 7,206, 386 and 1,603 "
                 "rows, Sequence one higher, not in use on 5,213, 239, 1 and 2, Same sequence, in use on 3,109, "
                 "501, 85 and 364, Same sequence, in use, with this name on 0, 0, 7 and 0, and No record on 3, 0, "
                 "0 and 0: on those 7 rows of szechuan_win10 the $MFT record still holds the name though neither "
                 "entry list does, which was not explained. The rows were compared with the USN Journal artifact's "
                 "rows for the same volumes, a separate store that also records names and references: of the "
                 "7,191, 6,109, 199 and 1,054 rows whose Name Space is not DOS, 5,478, 3,740, 126 and 804 have a "
                 "USN record with the same file record, sequence and name, and 5,478, 3,740, 119 and 804 of those "
                 "have one with a reason of FILE_DELETE, RENAME_OLD_NAME or HARD_LINK_CHANGE. The remaining rows "
                 "have no such record among the USN Journal artifact's rows. Not read: indexes other than $I30. "
                 "Not exercised on real data: an index block size other than 4,096 bytes, a block whose update "
                 "sequence does not check, an entry that names another record as its parent, an index root that "
                 "cannot be read, and a volume with no $MFT; the last four are exercised with constructed input in "
                 "admin/test/scripts/test_windows_ntfs_index_slack.py.",
        "paths": ('*:$I30', '*/$MFT'),
        "output_types": "standard",
        "artifact_icon": "folder-minus",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 11859 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2024 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 8101 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 486 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 185 rows",
        },
    },
    "windowsNtfsIndexSlackCopies": {
        "name": "NTFS $I30 Index Slack - Copies of Live Entries",
        "description": "Copies, found in the unused space of NTFS directory index blocks ($I30), of entries "
                       "that are still in that directory but hold other values now: the times and sizes the "
                       "copy held beside the modified time and size the entry holds now.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per file name entry found in the slack of a directory's $I30 index allocation whose file "
                 "reference and name are still a live entry of that directory, but with other values. The NTFS "
                 "$I30 Index Slack - Unlisted Entries artifact's notes say how the index allocations are staged, "
                 "how an entry is found in the slack and which entries are live (Reference: NTFS-3G 2022.10.3, "
                 "https://github.com/tuxera/ntfs-3g/blob/78414d93613532fd82f3a82aba5d4a1c32898781/include/ntfs-3g/layout.h, "
                 "INDEX_ROOT, INDEX_BLOCK, INDEX_HEADER, INDEX_ENTRY_HEADER and FILE_NAME_ATTR). An entry "
                 "identical to the live entry in every field but its length is left out and counted in the run "
                 "log, as is a second copy of an entry already taken. Modified, Record Changed, Created, Accessed, "
                 "Data Size, Allocated Size and File Attributes are the fields of the copy in the slack, the times "
                 "read as UTC FILETIMEs; Modified Now and Data Size Now are the last_data_change_time and "
                 "data_size of the live entry of the same file reference and name. A copy is one the entry lists "
                 "do not use. The artifact does not say when it was written, and its values are not always the "
                 "older ones: Modified was later than Modified Now on some rows of every image. Index Offset is "
                 "the copy's byte offset in the index allocation. Run on pc_mus_001_win11, lonewolf_win10, "
                 "szechuan_win10 and af_case2_win10: 54,791, 34,191, 32,238 and 35,976 rows. Modified differed "
                 "from Modified Now on 10,253, 13,125, 14,552 and 10,604 rows, earlier on 6,279, 2,792, 4,595 and "
                 "614 of them and later on 3,974, 10,333, 9,957 and 9,990. On 44,306, 21,041, 17,588 and 25,345 "
                 "rows Modified and Data Size both equalled the live entry's, so the copy differs in another "
                 "field. The 54,791 rows of pc_mus_001_win11 are above the 50,000-row limit of an HTML page, so "
                 "that table is left off its page and is in the other outputs. Not read: indexes other than $I30. "
                 "Not exercised on real data: an index block size other than 4,096 bytes.",
        "paths": ('*:$I30', '*/$MFT'),
        "output_types": "standard",
        "artifact_icon": "clock",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 54791 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 35976 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 34191 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 32238 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 1163 rows",
        },
    },
}

import os
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import (FILE_ATTRIBUTES, decode_flags, filetime, iter_mft, mft_record_size,
                                  split_reference)

_LABEL = 'NTFS $I30 Index Slack - Unlisted Entries'
_COPIES_LABEL = 'NTFS $I30 Index Slack - Copies of Live Entries'
_SECTOR = 512                                   # the stride of the update sequence array
_INDEX_HEADER = 0x18                            # INDEX_BLOCK.index
_ROOT_HEADER = 0x10                             # INDEX_ROOT.index
_INDEX_ROOT = 0x90
_ENTRY_HEADER = 16                              # INDEX_ENTRY_HEADER
_NAME_FIXED = 66                                # FILE_NAME_ATTR up to the name
_LAST_ENTRY = 2                                 # INDEX_ENTRY_END
_NAME_SPACES = {0: 'POSIX', 1: 'Win32', 2: 'DOS', 3: 'Win32 and DOS'}   # FILE_NAME_TYPE_FLAGS
_RECORD_MASK = 0xFFFFFFFFFFFF
# The last 8 bytes of an index end entry (length 16, key length 0, flags INDEX_ENTRY_END, reserved 0),
# read as a file reference: what an entry's first 8 bytes hold once NTFS has written the end of the
# entry list across them.
_END_ENTRY_TAIL = 0x0000000200000010
_FILE_LISTED = 'File, under another name'
_NAME_LISTED = 'Name, under another file reference'


def fix_up(block):
    """An index block with its update sequence array applied, or None when the array does not fit the
    block or a sector does not end in the block's sequence number."""
    offset, count = struct.unpack_from('<HH', block, 4)
    if count < 2 or offset + 2 * count > len(block) or (count - 1) * _SECTOR > len(block):
        return None
    number = block[offset:offset + 2]
    fixed = bytearray(block)
    for index in range(1, count):
        end = index * _SECTOR
        if fixed[end - 2:end] != number:
            return None
        fixed[end - 2:end] = block[offset + 2 * index:offset + 2 * index + 2]
    return bytes(fixed)


def block_size(data):
    """The size of the index blocks of an index allocation, from the first block that starts "INDX": its
    index header's allocated_size and the 24 bytes of the block in front of that header. None when no
    block starts "INDX" at a 512-byte step, or the size is not a power of two from 512 to 65,536 bytes that
    divides the allocation."""
    for offset in range(0, len(data) - _INDEX_HEADER - 12 + 1, _SECTOR):
        if data[offset:offset + 4] == b'INDX':
            size = _INDEX_HEADER + struct.unpack_from('<I', data, offset + _INDEX_HEADER + 8)[0]
            if 512 <= size <= 65536 and not size & (size - 1) and not len(data) % size and not offset % size:
                return size
            return None
    return None


def name_entry(data, position, end):
    """The index entry at a position, as (entry length, file reference, parent reference, created,
    modified, record changed, accessed, allocated size, data size, attributes, name space, name), when it
    is a file name's and lies whole before ``end``; otherwise None. An entry is a file name's when its key
    length is the length of a file name of the number of characters it states, its own length is that key
    and its header rounded up to 8 bytes, with room for a sub-node number at most, and its name space is
    one of the four."""
    if position + _ENTRY_HEADER + _NAME_FIXED > end:
        return None
    reference, length, key_length = struct.unpack_from('<QHH', data, position)
    characters, space = data[position + _ENTRY_HEADER + 64], data[position + _ENTRY_HEADER + 65]
    whole = (_ENTRY_HEADER + key_length + 7) & ~7
    if (not characters or key_length != _NAME_FIXED + 2 * characters or space > 3
            or length not in (whole, whole + 8) or position + length > end):
        return None
    (parent, created, modified, changed, accessed, allocated, size,
     attributes) = struct.unpack_from('<QqqqqqqI', data, position + _ENTRY_HEADER)
    start = position + _ENTRY_HEADER + _NAME_FIXED
    name = data[start:start + 2 * characters].decode('utf-16-le', 'replace')
    return (length, reference, parent, created, modified, changed, accessed, allocated, size, attributes,
            space, name)


def listed(data, header, limit):
    """The file name entries of the entry list an index header describes, up to its end entry."""
    entries = []
    first, used = struct.unpack_from('<II', data, header)
    end = min(header + used, limit)
    position = header + first
    while position + _ENTRY_HEADER <= end:
        length, _key, flags = struct.unpack_from('<HHH', data, position + 8)
        if length < _ENTRY_HEADER or position + length > end or flags & _LAST_ENTRY:
            break
        entry = name_entry(data, position, end)
        if entry is not None:
            entries.append(entry)
        position += length
    return entries, end


def read_index(data, counts):
    """(live, slack) for one index allocation: ``live`` the entries of its blocks' entry lists, and ``slack``
    [(offset in the allocation, entry)] for each file name entry found past the end of a block's entry
    list, looked for at every 8-byte step. Blocks that are not read are counted in ``counts``."""
    live, slack = [], []

    def count(what):
        counts[what] = counts.get(what, 0) + 1

    size = block_size(data)
    if size is None:
        count('index allocations with no index block, not read')
        return live, slack
    for base in range(0, len(data), size):
        raw = data[base:base + size]
        if raw[:4] != b'INDX':
            count('index blocks that do not start INDX, not read')
            continue
        block = fix_up(raw)
        if block is None:
            count('index blocks whose update sequence does not check, not read')
            continue
        entries, end_live = listed(block, _INDEX_HEADER, size)
        live.extend(entries)
        allocated, = struct.unpack_from('<I', block, _INDEX_HEADER + 8)
        end_block = min(_INDEX_HEADER + allocated, size)
        position = (max(end_live, _INDEX_HEADER) + 7) & ~7
        while position + _ENTRY_HEADER + _NAME_FIXED <= end_block:
            entry = name_entry(block, position, end_block)
            if entry is None:
                position += 8
            else:
                slack.append((base + position, entry))
                position += entry[0]
    return live, slack


class MftTable:
    """What a volume's $MFT gives these artifacts: how each record stands now, the names an in-use record
    holds, and the entries of a directory's index root."""

    def __init__(self, path):
        self.path = path
        self.states = {}                    # number -> (sequence, in use, {(parent record, name)})
        self.extensions = {}                # base record number -> [the records that extend it]
        with open(path, 'rb') as handle:
            self.record_size = mft_record_size(handle)
            for number, record in iter_mft(handle):
                if record is not None:
                    held = frozenset((name[0] & _RECORD_MASK, name[2]) for name in record.names) \
                        if record.in_use else frozenset()
                    self.states[number] = (record.sequence, record.in_use, held)
                    if record.base & _RECORD_MASK and record.in_use:
                        self.extensions.setdefault(record.base & _RECORD_MASK, []).append(
                            (number, record.base >> 48))

    def root_entries(self, number):
        """The file name entries of the entry list in a directory's $INDEX_ROOT attribute named $I30, looked
        for in its record and then in the in-use records that extend this use of it, or None when none
        holds one."""
        sequence = self.states.get(number, (None,))[0]
        holders = [number] + [holder for holder, wanted in self.extensions.get(number, [])
                              if wanted in (0, sequence)]
        for holder in holders:
            entries = self._root_in(holder)
            if entries is not None:
                return entries
        return None

    def _root_in(self, number):
        try:
            with open(self.path, 'rb') as handle:
                handle.seek(number * self.record_size)
                raw = handle.read(self.record_size)
        except OSError:
            return None
        record = fix_up(raw) if raw[:4] == b'FILE' and len(raw) == self.record_size else None
        if record is None:
            return None
        position, = struct.unpack_from('<H', record, 20)
        limit = min(struct.unpack_from('<I', record, 24)[0], len(record))
        while position + 24 <= limit:
            kind, length = struct.unpack_from('<II', record, position)
            if kind == 0xFFFFFFFF or length < 24 or position + length > limit:
                break
            name_length, name_offset = struct.unpack_from('<BH', record, position + 9)
            name = record[position + name_offset:position + name_offset + 2 * name_length]
            if kind == _INDEX_ROOT and not record[position + 8] and name == '$I30'.encode('utf-16-le'):
                size, start = struct.unpack_from('<IH', record, position + 16)
                value = record[position + start:position + start + size]
                if position + start + size > position + length or len(value) < _ROOT_HEADER + 16:
                    return None
                return listed(value, _ROOT_HEADER, len(value))[0]
            position += length
        return None

    def state_now(self, reference, parent, name):
        """How the record of a file reference's number stands against its sequence number, and whether an
        in-use record of the same sequence number still holds that name under that parent record."""
        number, sequence = split_reference(reference)
        current = self.states.get(number)
        if current is None:
            return 'No record'
        now, in_use, held = current
        if now == sequence:
            if not in_use:
                return 'Same sequence, not in use'
            if (parent & _RECORD_MASK, name) in held:
                return 'Same sequence, in use, with this name'
            return 'Same sequence, in use'
        if not in_use and now == (sequence + 1) & 0xFFFF:
            return 'Sequence one higher, not in use'
        return 'Another sequence'


def _member(context, infos, path):
    info = infos.get(path)
    return info.source_path if info else context.get_relative_path(path)


def classify(live, slack, counts):
    """Sort the slack entries of one index against its live ones. Returns (unlisted, copies):
    ``unlisted`` [(offset, entry, what of it the index still lists)] for an entry whose file
    reference and name are no entry of the index now, and ``copies`` [(offset, entry, live entry)] for
    one whose file reference and name are, with other times, sizes or attributes. An entry identical to a
    live one, a repeat of an entry already taken, and one that names another directory as its parent are
    counted and left out."""
    unlisted, copies = [], []

    def count(what):
        counts[what] = counts.get(what, 0) + 1

    whole = {entry[1:] for entry in live}
    by_name = {(entry[1], entry[11]): entry for entry in live}
    references = {entry[1] for entry in live}
    names = {entry[11] for entry in live}
    parents = {entry[2] & _RECORD_MASK for entry in live}
    seen = set()
    for offset, entry in slack:
        # An entry of this directory names it as its parent. With no live entry to say which record
        # that is, an entry is taken as it is found.
        if parents and entry[2] & _RECORD_MASK not in parents:
            count('entries in slack that name another directory as parent, not reported')
        elif entry[1:] in whole:
            count('entries in slack identical to an entry of the index, not reported')
        elif entry[1:] in seen:
            count('entries in slack found more than once in an index, reported once')
        elif entry[1] == _END_ENTRY_TAIL and entry[11] in names:
            # its file reference is gone, so it cannot be told from a copy of the entry of that name
            count('entries in slack with an overwritten file reference whose name is an entry of the '
                  'index, not reported')
        else:
            seen.add(entry[1:])
            now = by_name.get((entry[1], entry[11]))
            if now is not None:
                copies.append((offset, entry, now))
            else:
                unlisted.append((offset, entry, _FILE_LISTED if entry[1] in references
                                 else _NAME_LISTED if entry[11] in names else 'No'))
    return unlisted, copies


def _indexes(context):
    """([(member, path)] for the staged index allocations, {volume: $MFT path})."""
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    indexes, tables = [], {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        member = _member(context, infos, path).replace('\\', '/')
        if member.endswith('/$MFT') or member == '$MFT':
            tables[member.rpartition('/')[0]] = path
        elif member.endswith(':$I30'):
            indexes.append((member, path))
    return indexes, tables


def _classified(label, context, counts):
    """(volume, path inside it, staged path, unlisted, copies, table) for each index allocation that can
    be read, its slack sorted against the entry lists of its blocks and of the directory's index root."""
    indexes, tables = _indexes(context)
    opened = {}
    for member, path in indexes:
        volume, _, inside = member[:-len(':$I30')].partition('/')
        if volume not in opened:
            opened[volume] = MftTable(tables[volume]) if volume in tables else None
            if opened[volume] is None:
                logfunc(f'{label}: no $MFT found for {volume}, so its index roots are not read and the '
                        'columns that come from the $MFT are blank')
        table = opened[volume]
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{label}: could not read {member}: {type(exc).__name__}')
            continue
        live, slack = read_index(data, counts)
        # The directory is the record its entries name as their parent: the live ones, or with none the
        # slack ones when they agree.
        directory = {entry[2] & _RECORD_MASK for entry in live} or {entry[2] & _RECORD_MASK
                                                                   for _offset, entry in slack}
        if table is not None and slack:
            root = table.root_entries(next(iter(directory))) if len(directory) == 1 else None
            if root is None:
                counts['index allocations whose index root could not be read'] = (
                    counts.get('index allocations whose index root could not be read', 0) + 1)
            else:
                live = live + root
        unlisted, copies = classify(live, slack, counts)
        yield volume, inside, path, unlisted, copies, table


def _log(label, counts):
    if counts:
        logfunc(f'{label}: ' + '; '.join(f'{count:,} {what}' for what, count in sorted(counts.items())))


@artifact_processor
def windowsNtfsIndexSlack(context):
    data_headers = (('Record Changed', 'datetime'), ('Created', 'datetime'), ('Modified', 'datetime'),
                    ('Accessed', 'datetime'), 'File Name', 'Directory', 'In Index Now', 'MFT Record Now',
                    'File Record', 'File Sequence', 'Parent Record', 'Parent Sequence', 'Data Size',
                    'Allocated Size', 'File Attributes', 'Name Space', 'Index Offset', 'Source File')
    results = context.create_artifact_result(headers=data_headers)
    counts, sources, read = {}, [], 0
    for _volume, inside, path, unlisted, _copies, table in _classified(_LABEL, context, counts):
        read += 1
        relative = context.get_relative_path(path)
        for offset, entry, still in unlisted:
            (_length, reference, parent, created, modified, changed, accessed, allocated, size, attributes,
             space, name) = entry
            file_record, file_sequence = split_reference(reference)
            parent_record, parent_sequence = split_reference(parent)
            now = table.state_now(reference, parent, name) if table is not None else ''
            if reference == _END_ENTRY_TAIL:
                file_record = file_sequence = ''
                still = now = 'Reference overwritten'
            results.add_row((filetime(changed), filetime(created), filetime(modified), filetime(accessed),
                             name, '/' + inside, still, now,
                             file_record, file_sequence, parent_record, parent_sequence, size, allocated,
                             decode_flags(attributes, FILE_ATTRIBUTES), _NAME_SPACES[space], offset,
                             relative))
        if unlisted:
            sources.append(path)
    _log(_LABEL, counts)
    if read and not sources:
        logfunc(f'{_LABEL}: no unlisted entries found in the slack of {read:,} index allocations')
    results.set_source_path('\n'.join(sources))
    return results


@artifact_processor
def windowsNtfsIndexSlackCopies(context):
    data_headers = (('Modified', 'datetime'), ('Modified Now', 'datetime'), ('Record Changed', 'datetime'),
                    ('Created', 'datetime'), ('Accessed', 'datetime'), 'File Name', 'Directory', 'Data Size',
                    'Data Size Now', 'Allocated Size', 'File Attributes', 'File Record', 'File Sequence',
                    'Name Space', 'Index Offset', 'Source File')
    results = context.create_artifact_result(headers=data_headers)
    counts, sources, read = {}, [], 0
    for _volume, inside, path, _unlisted, copies, _table in _classified(_COPIES_LABEL, context, counts):
        read += 1
        relative = context.get_relative_path(path)
        for offset, entry, now in copies:
            (_length, reference, _parent, created, modified, changed, accessed, allocated, size, attributes,
             space, name) = entry
            file_record, file_sequence = split_reference(reference)
            results.add_row((filetime(modified), filetime(now[4]), filetime(changed), filetime(created),
                             filetime(accessed), name, '/' + inside, size, now[8], allocated,
                             decode_flags(attributes, FILE_ATTRIBUTES), file_record, file_sequence,
                             _NAME_SPACES[space], offset, relative))
        if copies:
            sources.append(path)
    _log(_COPIES_LABEL, counts)
    if read and not sources:
        logfunc(f'{_COPIES_LABEL}: no copies of live entries found in the slack of {read:,} index '
                'allocations')
    results.set_source_path('\n'.join(sources))
    return results
