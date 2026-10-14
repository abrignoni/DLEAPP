"""Pin the NTFS $LogFile File Name Changes artifact (scripts/artifacts/windowsNtfsLogFile.py).

A small $LogFile is written here in the layout the artifact reads: two restart pages, then record pages with
their update sequence arrays, each record at the offset its own log sequence number names. The names, times
and numbers are made up.
"""
import datetime
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsNtfsLogFile as lf
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
PAGE, DATA_OFFSET, HEADER, BITS = 4096, 64, 48, 44
T_CREATED = datetime.datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)
T_MODIFIED = datetime.datetime(2024, 5, 2, 11, 0, 0, tzinfo=UTC)
T_CHANGED = datetime.datetime(2024, 5, 3, 12, 0, 0, tzinfo=UTC)
T_ACCESSED = datetime.datetime(2024, 5, 4, 13, 0, 0, tzinfo=UTC)


def ticks(moment):
    return int((moment - datetime.datetime(1601, 1, 1, tzinfo=UTC)).total_seconds()) * 10_000_000


def entry(record, sequence, parent, parent_sequence, name, space=1, size=1234, allocated=4096, attributes=0x20):
    """An index entry whose key is a file name (INDEX_ENTRY_HEADER then FILE_NAME_ATTR)."""
    text = name.encode('utf-16-le')
    key = struct.pack('<QqqqqqqIIBB', parent | parent_sequence << 48, ticks(T_CREATED), ticks(T_MODIFIED),
                      ticks(T_CHANGED), ticks(T_ACCESSED), allocated, size, attributes, 0, len(name), space) + text
    return struct.pack('<QHHHH', record | sequence << 48, 16 + len(key), len(key), 0, 0) + key


def client(redo, undo, redo_data=b'', undo_data=b''):
    """A record's client data: the operation header (40 bytes), then the redo and the undo data."""
    head = struct.pack('<HHHHHH', redo, undo, 40, len(redo_data), 40 + len(redo_data), len(undo_data))
    return head.ljust(40, b'\0') + redo_data + undo_data


def protect(page, array=40):
    """Set a page's update sequence array at an offset: the last two bytes of each sector go to the array."""
    page = bytearray(page)
    struct.pack_into('<HH', page, 4, array, 9)
    page[array:array + 2] = b'\x07\x00'
    for sector in range(1, 9):
        end = sector * 512
        page[array + 2 * sector:array + 2 + 2 * sector] = page[end - 2:end]
        page[end - 2:end] = b'\x07\x00'
    return bytes(page)


class Log:
    """A $LogFile under construction: records are laid one after another from the first ordinary block."""

    def __init__(self, major=2, pages=40):
        self.major, self.special = major, 34 if major >= 2 else 4
        self.bodies = [bytearray(PAGE) for _ in range(pages)]
        self.where = self.special * PAGE + DATA_OFFSET

    @staticmethod
    def lsn(offset, cycle=1):
        return cycle << (64 - BITS) | offset >> 3

    def add(self, data, transaction=9, at=None):
        """Lay a record down at the current place (or at a byte offset), crossing pages as a log does."""
        if at is not None:
            self.where = at
        lsn = self.lsn(self.where)
        stream = struct.pack('<qqqIIII', lsn, 0, 0, len(data), 0, 1, transaction).ljust(HEADER, b'\0') + data
        position = self.where
        struct.pack_into('<q', self.bodies[position // PAGE], 8, lsn)      # the page header's last LSN
        while stream:
            page, inside = divmod(position, PAGE)
            piece = stream[:PAGE - inside]
            self.bodies[page][inside:inside + len(piece)] = piece
            stream = stream[len(piece):]
            position = (page + 1) * PAGE + DATA_OFFSET
        self.where = (self.where + HEADER + len(data) + 7) & ~7
        if PAGE - self.where % PAGE < HEADER:
            self.where = (self.where // PAGE + 1) * PAGE + DATA_OFFSET
        return lsn

    def build(self, minor=0):
        restart = bytearray(PAGE)
        restart[0:4] = b'RSTR'
        struct.pack_into('<IIHhh', restart, 16, PAGE, PAGE, 48, minor, self.major)
        struct.pack_into('<I', restart, 48 + 16, BITS)
        struct.pack_into('<HH', restart, 48 + 36, HEADER, DATA_OFFSET)
        out = [protect(restart, 30), protect(restart, 30)]
        for body in self.bodies[2:]:
            if any(body):
                body[0:4] = b'RCRD'
                out.append(protect(body))
            else:
                out.append(b'\xff' * PAGE)
        return b''.join(out)


class Reader(unittest.TestCase):
    def changes(self, data):
        log = lf.LogFile(data)
        return list(lf.name_changes(log)), log

    def test_add_and_delete(self):
        log = Log()
        added = log.add(client(14, 15, redo_data=entry(100, 3, 50, 2, 'report.docx')), transaction=7)
        deleted = log.add(client(13, 12, undo_data=entry(101, 4, 5, 5, 'OLD~1.TXT', space=2)), transaction=8)
        log.add(client(27, 1))                                         # another operation: not a name change
        log.add(client(14, 15, redo_data=struct.pack('<QHHHH', 0, 24, 4, 0, 0) + b'\1\0\0\0' * 2))   # another index
        rows, read = self.changes(log.build())
        self.assertEqual([(r[0], r[1], r[2]) for r in rows],
                         [(added, 7, 'Added (index allocation)'), (deleted, 8, 'Deleted (index root)')])
        self.assertEqual(rows[0][3], (100 | 3 << 48, 50 | 2 << 48, ticks(T_CREATED), ticks(T_MODIFIED),
                                      ticks(T_CHANGED), ticks(T_ACCESSED), 4096, 1234, 0x20, 1, 'report.docx'))
        self.assertEqual(rows[1][3][-2:], (2, 'OLD~1.TXT'))
        self.assertEqual(read.counts, {'index entries that are not a file name, not reported': 1})
        self.assertEqual((read.major, read.minor), (2, 0))

    def test_root_add_and_allocation_delete_labels(self):
        log = Log()
        log.add(client(12, 13, redo_data=entry(7, 1, 5, 5, 'a')))
        log.add(client(15, 14, undo_data=entry(8, 1, 5, 5, 'b')))
        log.add(client(15, 0, undo_data=entry(9, 1, 5, 5, 'c')))      # a delete whose undo is not an add
        rows, _ = self.changes(log.build())
        self.assertEqual([r[2] for r in rows], ['Added (index root)', 'Deleted (index allocation)'])

    def test_record_crossing_a_page(self):
        log = Log()
        log.add(client(27, 1), at=34 * PAGE + PAGE - 200)             # leaves 112 bytes before the page ends
        lsn = log.add(client(14, 15, redo_data=entry(200, 1, 60, 1, 'crosses the page boundary.txt')))
        self.assertEqual(lsn, Log.lsn(34 * PAGE + PAGE - 112))        # its header fits, its data does not
        rows, _ = self.changes(log.build())
        self.assertEqual([(r[0], r[3][-1]) for r in rows], [(lsn, 'crosses the page boundary.txt')])

    def test_name_over_a_sector_end(self):
        log = Log()
        name = 'a name that lies over the end of a sector'
        log.add(client(14, 15, redo_data=entry(210, 1, 60, 1, name)), at=34 * PAGE + 288)   # name at 458 to 540
        rows, _ = self.changes(log.build())
        self.assertEqual([r[3][-1] for r in rows], [name])

    def test_header_with_a_length_a_record_cannot_have(self):
        log = Log()
        log.add(b'\0' * 8)                                            # less than an operation header
        lsn = log.add(client(14, 15, redo_data=entry(220, 1, 5, 5, 'after.txt')))
        rows, read = self.changes(log.build())
        self.assertEqual([r[0] for r in rows], [lsn])
        self.assertEqual(read.counts, {'record headers with a data length a record cannot have, passed over': 1})

    def test_version_1_keeps_four_blocks_apart(self):
        log = Log(major=1)
        self.assertEqual(log.where, 4 * PAGE + DATA_OFFSET)
        lsn = log.add(client(14, 15, redo_data=entry(300, 1, 5, 5, 'one.txt')))
        rows, read = self.changes(log.build(minor=1))
        self.assertEqual([r[0] for r in rows], [lsn])
        self.assertEqual((read.major, read.minor, read.special), (1, 1, 4))

    def test_copy_in_a_block_kept_apart(self):
        log = Log()
        lsn = log.add(client(14, 15, redo_data=entry(400, 1, 5, 5, 'twice.txt')))
        log.bodies[2][:] = log.bodies[34]                             # the same page, copied to block 2
        only_copy = Log()
        only_copy.add(client(14, 15, redo_data=entry(401, 1, 5, 5, 'copy only.txt')))
        only_copy.bodies[3][:] = only_copy.bodies[34]
        only_copy.bodies[34][:] = bytes(PAGE)
        rows, read = self.changes(log.build())
        self.assertEqual([r[0] for r in rows], [lsn])
        self.assertEqual(read.counts, {'records found a second time in another page, reported once': 1})
        rows, _ = self.changes(only_copy.build())
        self.assertEqual([r[3][-1] for r in rows], ['copy only.txt'])

    def test_version_1_copy_is_placed_by_its_file_offset(self):
        log = Log(major=1)
        lsn = log.add(client(14, 15, redo_data=entry(410, 1, 5, 5, 'old log.txt')))
        log.bodies[2][:] = log.bodies[4]
        struct.pack_into('<q', log.bodies[2], 8, 4 * PAGE)             # a version 1 header holds the file offset
        log.bodies[4][:] = bytes(PAGE)
        rows, _ = self.changes(log.build(minor=1))
        self.assertEqual([r[0] for r in rows], [lsn])
        struct.pack_into('<q', log.bodies[2], 8, 9 * PAGE)             # placed elsewhere: the LSN no longer fits
        rows, _ = self.changes(log.build(minor=1))
        self.assertEqual(rows, [])

    def test_record_in_a_copy_that_continues_past_its_page(self):
        log = Log()
        log.add(client(27, 1), at=34 * PAGE + PAGE - 200)
        log.add(client(14, 15, redo_data=entry(420, 1, 5, 5, 'runs past the page of a copy.txt')))
        log.bodies[2][:] = log.bodies[34]
        log.bodies[34][:] = bytes(PAGE)
        log.bodies[35][:] = bytes(PAGE)
        rows, read = self.changes(log.build())
        self.assertEqual(rows, [])
        self.assertEqual(read.counts,
                         {'records in a block kept apart whose data continues past its page, not reported': 1})

    def test_record_running_into_a_page_that_does_not_check(self):
        log = Log()
        log.add(client(27, 1), at=34 * PAGE + PAGE - 200)
        log.add(client(14, 15, redo_data=entry(430, 1, 5, 5, 'runs into a page that is damaged.txt')))
        data = bytearray(log.build())
        data[35 * PAGE + 510:35 * PAGE + 512] = b'\x99\x99'
        rows, read = self.changes(bytes(data))
        self.assertEqual(rows, [])
        self.assertEqual(read.counts, {'record pages whose update sequence does not check, not read': 1,
                                       'records whose data runs into a page that does not check, not reported': 1})

    def test_page_that_does_not_check_is_not_read(self):
        log = Log()
        log.add(client(14, 15, redo_data=entry(500, 1, 5, 5, 'lost.txt')))
        data = bytearray(log.build())
        data[34 * PAGE + 510:34 * PAGE + 512] = b'\x99\x99'           # the first sector's sequence number
        rows, read = self.changes(bytes(data))
        self.assertEqual(rows, [])
        self.assertEqual(read.counts, {'record pages whose update sequence does not check, not read': 1})

    def test_record_at_an_offset_its_lsn_does_not_name(self):
        log = Log()
        log.add(client(14, 15, redo_data=entry(600, 1, 5, 5, 'moved.txt')))
        log.bodies[35][:] = log.bodies[34]                            # the same bytes one page on: stale
        rows, _ = self.changes(log.build())
        self.assertEqual(len(rows), 1)

    def test_files_that_are_not_a_log(self):
        self.assertIn('restart page', lf.LogFile(b'\0' * 8192).problem)
        self.assertIn('restart page', lf.LogFile(b'RSTR').problem)
        self.assertEqual(lf.LogFile(Log(major=3).build()).problem, 'log version 3.0 is not read')

    def test_entries_that_are_not_file_names(self):
        good = entry(1, 1, 5, 5, 'name')
        self.assertIsNotNone(lf.file_name_entry(good))
        self.assertIsNone(lf.file_name_entry(good[:60]))                                  # too short
        self.assertIsNone(lf.file_name_entry(good[:10] + struct.pack('<H', 70) + good[12:]))   # key length
        self.assertIsNone(lf.file_name_entry(good[:81] + b'\x04' + good[82:]))            # name space 4
        self.assertIsNone(lf.file_name_entry(good[:-2]))                                  # key past the data


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def run_artifact(self, files):
        paths = []
        for relative, data in files.items():
            path = os.path.join(self.folder.name, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as handle:
                handle.write(data)
            paths.append(path)
        rows = []
        result = mock.Mock()
        result.add_row.side_effect = rows.append
        context = mock.Mock()
        context.get_files_found.return_value = paths
        context.get_seeker.return_value = None
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        context.create_artifact_result.return_value = result
        with mock.patch.object(lf, 'logfunc') as log, mock.patch.object(lf, 'mft_index', return_value=None):
            lf.windowsNtfsLogFile.__wrapped__(context)
        return rows, result, [c.args[0] for c in log.call_args_list], context

    def test_rows(self):
        log = Log()
        second = log.add(client(13, 12, undo_data=entry(101, 4, 5, 5, 'gone.txt', space=3)), transaction=8)
        first = Log.lsn(34 * PAGE + DATA_OFFSET)
        self.assertEqual(second, first)
        later = log.add(client(14, 15, redo_data=entry(100, 3, 50, 2, 'report.docx', attributes=0x22)), transaction=7)
        rows, result, logged, context = self.run_artifact({'vol/$LogFile': log.build(), 'vol/notes.txt': b'x'})
        headers = context.create_artifact_result.call_args.kwargs['headers']
        self.assertEqual(headers[:5], (('Record Changed', 'datetime'), ('Created', 'datetime'),
                                       ('Modified', 'datetime'), ('Accessed', 'datetime'), 'Operation'))
        self.assertEqual(len(headers), 18)
        self.assertEqual(rows, [
            (T_CHANGED, T_CREATED, T_MODIFIED, T_ACCESSED, 'Deleted (index root)', 'gone.txt', '', second, 8,
             101, 4, 5, 5, 1234, 4096, 'Archive', 'Win32 and DOS', 'vol/$LogFile'),
            (T_CHANGED, T_CREATED, T_MODIFIED, T_ACCESSED, 'Added (index allocation)', 'report.docx', '', later, 7,
             100, 3, 50, 2, 1234, 4096, 'Hidden | Archive', 'Win32', 'vol/$LogFile')])
        result.set_source_path.assert_called_once_with(os.path.join(self.folder.name, 'vol/$LogFile'))
        self.assertEqual(logged, ['NTFS $LogFile File Name Changes: no $MFT beside vol/$LogFile, so parent paths '
                                  'are blank'])

    def test_not_a_log_and_empty_log(self):
        rows, result, logged, _ = self.run_artifact({'a/$LogFile': b'\0' * 8192, 'b/$LogFile': Log().build()})
        self.assertEqual(rows, [])
        result.set_source_path.assert_called_once_with('')
        self.assertEqual(len(logged), 3)
        self.assertIn('a/$LogFile does not start with a restart page', logged[0])
        self.assertIn('no file name changes read from b/$LogFile', logged[2])


T_NOW = datetime.datetime(2019, 1, 1, 0, 0, 0, tzinfo=UTC)


def attribute(kind, value, non_resident=False):
    """A resident attribute: a 24-byte header then its value, padded to 8 bytes."""
    length = (24 + len(value) + 7) & ~7
    head = struct.pack('<IIBBHHHIH', kind, length, 1 if non_resident else 0, 0, 24, 0, 0, len(value), 24)
    return head.ljust(24, b'\0') + value.ljust(length - 24, b'\0')


def name_value(parent, parent_sequence, name, space=1):
    text = name.encode('utf-16-le')
    return struct.pack('<QqqqqqqIIBB', parent | parent_sequence << 48, 1, 2, 3, 4, 0, 0, 0, 0, len(name), space) + text


def mft_record(number, sequence, attributes, flags=1, base=0, array=48):
    """The start of an MFT record as a log record holds it: the header, then the attributes and an end mark."""
    body = b''.join(attributes) + struct.pack('<I', 0xFFFFFFFF)
    head = struct.pack('<4sHHqHHHHIIQHHI', b'FILE', array, 3, 0, sequence, 1, 56, flags, 56 + len(body), 1024,
                       base, 0, 0, number)
    return head.ljust(56, b'\0') + body


SI_TIMES = (ticks(T_CREATED), ticks(T_MODIFIED), ticks(T_CHANGED), ticks(T_ACCESSED))
SI = attribute(0x10, struct.pack('<qqqq', *SI_TIMES) + bytes(40))


class FileRecords(unittest.TestCase):
    def test_file_record(self):
        record = mft_record(900, 7, [SI, attribute(0x30, name_value(50, 2, 'SHORT~1.TXT', space=2)),
                                     attribute(0x30, name_value(50, 2, 'a long name.txt')),
                                     attribute(0x80, b'content')], flags=3)
        self.assertEqual(lf.logged_file_record(record),
                         (900, 7, 3, 0, SI_TIMES, [(50 | 2 << 48, 2, 'SHORT~1.TXT'), (50 | 2 << 48, 1, 'a long name.txt')]))

    def test_records_that_are_not_read(self):
        good = mft_record(1, 1, [SI])
        self.assertIsNone(lf.logged_file_record(good[:40]))
        self.assertIsNone(lf.logged_file_record(b'BAAD' + good[4:]))
        self.assertIsNone(lf.logged_file_record(mft_record(1, 1, [SI], array=42)))        # the older header layout
        cut = mft_record(2, 1, [SI, attribute(0x30, name_value(5, 5, 'cut off.txt'))])
        self.assertEqual(lf.logged_file_record(cut[:56 + len(SI) + 30])[4:], (SI_TIMES, []))   # the name is not whole
        self.assertEqual(lf.logged_file_record(cut[:56 + len(SI) + 4])[4:], (SI_TIMES, []))    # cut inside a header
        longer = bytearray(mft_record(5, 1, [SI]))
        struct.pack_into('<I', longer, 56 + 4, 4000)                               # an attribute past the data
        self.assertEqual(lf.logged_file_record(bytes(longer))[4:], (None, []))
        spill = struct.pack('<IIBBHHHIH', 0x10, 32, 0, 0, 24, 0, 0, 72, 24).ljust(24, b'\0') + bytes(8)
        self.assertEqual(lf.logged_file_record(mft_record(6, 1, [spill, attribute(0x80, b'\x01' * 64)]))[4:], (None, []))
        non_resident = mft_record(3, 1, [attribute(0x10, struct.pack('<qqqq', *SI_TIMES) + bytes(40), True)])
        self.assertEqual(lf.logged_file_record(non_resident)[4:], (None, []))
        self.assertEqual(lf.logged_file_record(mft_record(4, 1, [SI], base=77 | 3 << 48))[3], 77 | 3 << 48)

    def test_new_file_records(self):
        log = Log()
        first = log.add(client(2, 0, redo_data=mft_record(900, 7, [SI])), transaction=5)
        log.add(client(2, 0, redo_data=b'not a record at all, only bytes that fill the payload out ..'))
        log.add(client(3, 2, undo_data=mft_record(901, 1, [SI])))                    # a deallocation
        read = lf.LogFile(log.build())
        self.assertEqual([(lsn, tr, rec[0]) for lsn, tr, rec in lf.new_file_records(read)], [(first, 5, 900)])
        self.assertEqual(read.counts, {'file record initialisations whose data is not read as a file record, not reported': 1})

    def test_state_now(self):
        states = {10: (4, True, (111, 2, 3, 4)), 11: (4, False, None), 12: (5, False, (9, 9, 9, 9)),
                  13: (9, True, (9, 9, 9, 9)), 14: (5, True, (9, 9, 9, 9)), 15: (0, False, (9, 9, 9, 9))}
        self.assertEqual(lf.state_now(states, 10, 4), ('Same sequence, in use', 111))
        self.assertEqual(lf.state_now(states, 11, 4), ('Same sequence, not in use', None))
        self.assertEqual(lf.state_now(states, 12, 4), ('Sequence one higher, not in use', None))
        self.assertEqual(lf.state_now(states, 13, 4), ('Another sequence', None))
        self.assertEqual(lf.state_now(states, 14, 4), ('Another sequence', None))    # one higher but in use
        self.assertEqual(lf.state_now(states, 15, 0xFFFF), ('Sequence one higher, not in use', None))
        self.assertEqual(lf.state_now(states, 99, 4), ('No record', None))


class RecordsArtifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def run_artifact(self, files, states=None, paths_of=None):
        found = []
        for relative, data in files.items():
            path = os.path.join(self.folder.name, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as handle:
                handle.write(data)
            found.append(path)
        rows = []
        result = mock.Mock()
        result.add_row.side_effect = rows.append
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_seeker.return_value = None
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        context.create_artifact_result.return_value = result
        index = None
        if paths_of is not None:
            index = mock.Mock()
            index.directory_path.side_effect = paths_of.get
        with mock.patch.object(lf, 'logfunc') as log, mock.patch.object(lf, 'mft_index', return_value=index), \
             mock.patch.object(lf, 'record_states', return_value=states):
            lf.windowsNtfsLogFileRecords.__wrapped__(context)
        return rows, result, [c.args[0] for c in log.call_args_list], context

    def log(self):
        log = Log()
        lsns = [
            log.add(client(2, 0, redo_data=mft_record(900, 7, [
                SI, attribute(0x30, name_value(50, 2, 'KEPT~1.TXT', space=2)),
                attribute(0x30, name_value(50, 2, 'kept and changed.txt'))])), transaction=5),
            log.add(client(2, 0, redo_data=mft_record(901, 3, [SI, attribute(0x30, name_value(5, 5, 'folder'))],
                                                      flags=3)), transaction=6),
            log.add(client(2, 0, redo_data=mft_record(902, 1, [attribute(0x30, name_value(60, 1, 'ONLY~1.DOS',
                                                                                         space=2))])), transaction=7),
            log.add(client(2, 0, redo_data=mft_record(903, 2, [attribute(0x80, b'')], base=900 | 7 << 48)),
                    transaction=8)]
        return log.build(), lsns

    def test_rows_beside_the_mft(self):
        data, lsns = self.log()
        states = {900: (7, True, (ticks(T_NOW), 2, 3, 4)), 901: (3, True, SI_TIMES), 902: (2, False, None)}
        rows, result, logged, context = self.run_artifact(
            {'vol/$LogFile': data, 'vol/$MFT': b'x'}, states, {50 | 2 << 48: 'Users/someone', 5 | 5 << 48: ''})
        headers = context.create_artifact_result.call_args.kwargs['headers']
        self.assertEqual(headers[:6], (('SI Created', 'datetime'), ('SI Modified', 'datetime'),
                                       ('SI Record Changed', 'datetime'), ('SI Accessed', 'datetime'),
                                       ('SI Created Now', 'datetime'), 'Created Differs'))
        self.assertEqual(len(headers), 18)
        log_file = 'vol/$LogFile'
        self.assertEqual(rows, [
            (T_CREATED, T_MODIFIED, T_CHANGED, T_ACCESSED, T_NOW, 'Yes', 'kept and changed.txt', '/Users/someone',
             'File', 'Same sequence, in use', lsns[0], 5, 900, 7, 50, 2, '', log_file),
            (T_CREATED, T_MODIFIED, T_CHANGED, T_ACCESSED, T_CREATED, 'No', 'folder', '/', 'Directory',
             'Same sequence, in use', lsns[1], 6, 901, 3, 5, 5, '', log_file),
            ('', '', '', '', '', '', 'ONLY~1.DOS', '', 'File', 'Sequence one higher, not in use', lsns[2], 7, 902, 1,
             60, 1, '', log_file),
            ('', '', '', '', '', '', '', '', 'Extension record', 'No record', lsns[3], 8, 903, 2, '', '', 900,
             log_file)])
        result.set_source_path.assert_called_once_with(os.path.join(self.folder.name, 'vol/$LogFile'))
        self.assertEqual(logged, [])

    def test_rows_without_an_mft(self):
        data, lsns = self.log()
        rows, _, logged, _ = self.run_artifact({'vol/$LogFile': data})
        self.assertEqual(rows[0], (T_CREATED, T_MODIFIED, T_CHANGED, T_ACCESSED, '', '', 'kept and changed.txt', '',
                                   'File', '', lsns[0], 5, 900, 7, 50, 2, '', 'vol/$LogFile'))
        self.assertEqual(len(rows), 4)
        self.assertEqual(logged, ['NTFS $LogFile File Records Created: no $MFT beside vol/$LogFile, so the columns '
                                  'that come from it are blank'])

    def test_not_a_log_and_nothing_in_a_log(self):
        rows, result, logged, _ = self.run_artifact({'a/$LogFile': b'\0' * 8192, 'b/$LogFile': Log().build()})
        self.assertEqual(rows, [])
        result.set_source_path.assert_called_once_with('')
        self.assertIn('a/$LogFile does not start with a restart page', logged[0])
        self.assertIn('no file record initialisations read from b/$LogFile', logged[-1])


if __name__ == '__main__':
    unittest.main()
