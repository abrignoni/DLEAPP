"""Pin the BITS queue reading in scripts/bits_qmgr.py and scripts/artifacts/windowsBitsJobs.py.

Every record and page below is built by the test from the layouts the reader documents; no
value comes from a real device. Expected values are written out, never read back from the
code.
"""
import fnmatch
import pathlib
import sqlite3
import struct
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import bits_qmgr as bq  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsBitsJobs as artifact  # pylint: disable=wrong-import-position

# The six job markers, the file marker and the transfer marker, written out rather than taken
# from the reader.
JOB_MARKERS = [bytes.fromhex(value) for value in (
    'a15609e143afc94292e66f9856eba7f6', '9f95d44c6470f24b84d7476a7e62699f',
    'f11926a93203bf4c9427898818958831', 'c133bcddfb5aaf4db8a12268b39d01ad',
    'd057568f2c013e4ead2cf4a5d7656faf', '5067419457031d46a4cc5dd9990706e4')]
FILE_MARKER = bytes.fromhex('e4cf9e5146d99743b73e268513051ab2')
TRANSFER = bytes.fromhex('36da56776f515a43acac44a248fff34d')
# What sits between a Files record's Id and its blob when the blob is stored in the record.
INLINE = bytes.fromhex('fe0001040001')

JOB_ID = uuid.UUID('11111111-2222-3333-4444-555555555555')
OLD_JOB_ID = uuid.UUID('12121212-3434-5656-7878-909090909090')
FILE_ID = uuid.UUID('66666666-7777-8888-9999-aaaaaaaaaaaa')
OLD_FILE_ID = uuid.UUID('abababab-cdcd-efef-0101-232323232323')
OWNER = 'S-1-5-21-1111-2222-3333-1001'
# 2026-01-02 03:04:05 UTC, an hour later, and 90 days after that, as FILETIMEs.
CREATED = 134117966450000000
MODIFIED = 134118002450000000
EXPIRES = 134195762450000000
TIMES = (CREATED, MODIFIED, MODIFIED, MODIFIED, EXPIRES)
WHEN = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
LATER = datetime(2026, 1, 2, 4, 4, 5, tzinfo=timezone.utc)
UNKNOWN_SIZE = 0xFFFFFFFFFFFFFFFF


def counted(text):
    """A 32-bit UTF-16 code unit count, then the text and its terminating NUL."""
    raw = (text + '\x00').encode('utf-16-le')
    return struct.pack('<I', len(raw) // 2) + raw


def error_entry(code, size):
    """An error entry: four bytes, the 32-bit code, then padding to the entry's size."""
    return struct.pack('<II', 0, code) + bytes(size - 8)


def job(name='Font Download', job_id=JOB_ID, owner=OWNER, state=0, job_type=0, priority=2,
        description='', program='', parameters='', flags=3, token=bytes(40),
        file_ids=(FILE_ID,), errors=(), error_size=21, times=TIMES, marker=JOB_MARKERS[0]):
    return (marker + struct.pack('<IIII', job_type, priority, state, 0) + job_id.bytes_le
            + b''.join(counted(value) for value in (name, description, program, parameters, owner))
            + struct.pack('<I', flags) + token + TRANSFER
            + struct.pack('<I', len(file_ids)) + b''.join(f.bytes_le for f in file_ids) + TRANSFER
            + struct.pack('<I', len(errors)) + b''.join(error_entry(c, error_size) for c in errors)
            + struct.pack('<III', 0, 600, 1209600) + struct.pack('<QQQ', *times[:3]) + bytes(14)
            + struct.pack('<QQ', *times[3:]))


def file_record(local='C:\\Users\\tester\\AppData\\Local\\Temp\\setup.exe',
                remote='https://example.com/setup.exe',
                temporary='C:\\Users\\tester\\AppData\\Local\\Temp\\BIT1A2B.tmp',
                transferred=1024, total=4096, drive='C:\\',
                volume='\\\\?\\Volume{01234567-89ab-cdef-0123-456789abcdef}\\'):
    return (FILE_MARKER + counted(local) + counted(remote) + counted(temporary)
            + struct.pack('<QQ', transferred, total) + b'\x00' + counted(drive) + counted(volume))


def inline_file(file_id=FILE_ID, **fields):
    """A Files record's bytes from its Id on: the Id, the inline prefix, then the blob."""
    return file_id.bytes_le + INLINE + file_record(**fields)


class JobRecordTest(unittest.TestCase):
    def test_fields_read_in_order(self):
        record = bq.parse_job(job(description='Fonts', state=4, errors=(0x80072EE7,)))
        self.assertEqual(
            {key: record[key] for key in ('type', 'priority', 'state', 'job_id', 'name',
                                          'description', 'program', 'parameters', 'owner',
                                          'flags', 'file_ids', 'times', 'errors', 'error_size')},
            {'type': 0, 'priority': 2, 'state': 4, 'job_id': JOB_ID.bytes_le,
             'name': 'Font Download', 'description': 'Fonts', 'program': '', 'parameters': '',
             'owner': OWNER, 'flags': 3, 'file_ids': [FILE_ID.bytes_le], 'times': TIMES,
             'errors': [0x80072EE7], 'error_size': 21})

    def test_notify_command_line(self):
        record = bq.parse_job(job(program='C:\\Windows\\System32\\cmd.exe',
                                  parameters='/c start notepad.exe'))
        self.assertEqual((record['program'], record['parameters']),
                         ('C:\\Windows\\System32\\cmd.exe', '/c start notepad.exe'))

    def test_25_byte_error_entries(self):
        record = bq.parse_job(job(errors=(0x80200010, 0x80072EE7), error_size=25))
        self.assertEqual((record['errors'], record['error_size'], record['times']),
                         ([0x80200010, 0x80072EE7], 25, TIMES))

    def test_no_errors(self):
        record = bq.parse_job(job())
        self.assertEqual((record['errors'], record['error_size'], record['times']),
                         ([], None, TIMES))

    def test_times_left_out_when_no_entry_size_fits(self):
        record = bq.parse_job(job(times=(0, 0, 0, 0, 0), errors=(5,)))
        self.assertEqual((record['name'], record['times'], record['errors']),
                         ('Font Download', (), []))

    def test_times_left_out_when_the_second_is_out_of_range(self):
        record = bq.parse_job(job(times=(CREATED, 0, 0, 0, 0), errors=(5,)))
        self.assertEqual((record['times'], record['errors']), ((), []))

    def test_times_left_out_when_both_entry_sizes_fit(self):
        # Each half of this FILETIME is itself the high half of a 2026 FILETIME, so reading
        # the entry as 25 bytes, four bytes further on, also lands on in-range times.
        both = 0x01DC7B4F01DC7B4F
        record = bq.parse_job(job(times=(CREATED, both, both, both, both), errors=(5,))
                              + bytes(8))
        self.assertEqual((record['times'], record['errors'], record['error_size']),
                         ((), [], None))

    def test_each_job_marker(self):
        for marker in JOB_MARKERS:
            with self.subTest(marker=marker.hex()):
                self.assertEqual(bq.parse_job(job(marker=marker))['job_id'], JOB_ID.bytes_le)

    def test_empty_text_with_a_count_of_zero(self):
        data = bytearray(job())
        offset = 16 + 16 + 16 + len(counted('Font Download'))
        self.assertEqual(data[offset:offset + 6], bytes.fromhex('010000000000'))
        data[offset:offset + 6] = struct.pack('<I', 0)
        self.assertEqual(bq.parse_job(bytes(data))['description'], '')

    def test_rejected(self):
        cases = {
            'state out of range': job(state=9),
            'type out of range': job(job_type=3),
            'priority out of range': job(priority=4),
            'no job id': job(job_id=uuid.UUID(int=0)),
            'owner not a SID': job(owner='S-1-5-21-1111-22\t'),
            'another record before the transfer marker': job(token=bytes(8) + FILE_MARKER),
            'not a job marker': FILE_MARKER + job()[16:],
        }
        for label, data in cases.items():
            with self.subTest(label):
                self.assertIsNone(bq.parse_job(data))

    def test_text_must_be_terminated(self):
        data = bytearray(job())
        offset = 16 + 16 + 16
        self.assertEqual(data[offset:offset + 4], struct.pack('<I', 14))
        data[offset + 4 + 26:offset + 4 + 28] = 'x'.encode('utf-16-le')
        self.assertIsNone(bq.parse_job(bytes(data)))

    def test_second_transfer_marker_required(self):
        data = job()
        cut = data.rfind(TRANSFER)
        self.assertIsNone(bq.parse_job(data[:cut] + bytes(16) + data[cut + 16:]))


class FileRecordTest(unittest.TestCase):
    def test_fields(self):
        record = bq.parse_file(file_record())
        self.assertEqual(
            {key: value for key, value in record.items() if key != 'end'},
            {'local_name': 'C:\\Users\\tester\\AppData\\Local\\Temp\\setup.exe',
             'remote_name': 'https://example.com/setup.exe',
             'temporary_name': 'C:\\Users\\tester\\AppData\\Local\\Temp\\BIT1A2B.tmp',
             'size_1': 1024, 'size_2': 4096, 'drive': 'C:\\',
             'volume': '\\\\?\\Volume{01234567-89ab-cdef-0123-456789abcdef}\\'})
        self.assertEqual(record['end'], len(file_record()))

    def test_extended_length_local_name(self):
        record = bq.parse_file(file_record(local='\\\\?\\C:\\Windows\\Temp\\update.cab'))
        self.assertEqual(record['local_name'], '\\\\?\\C:\\Windows\\Temp\\update.cab')

    def test_local_and_remote_names_required(self):
        self.assertIsNone(bq.parse_file(file_record(local='')))
        self.assertIsNone(bq.parse_file(file_record(remote='')))

    def test_not_a_file_record(self):
        self.assertIsNone(bq.parse_file(job()))


class FindRecordsTest(unittest.TestCase):
    def test_records_in_order_with_inline_file_ids(self):
        bare = file_record(remote='https://example.com/b.cab')
        data = b'page' + inline_file() + bytes(10) + bare + job()
        found = list(bq.find_records(data))
        self.assertEqual([(offset, kind) for offset, kind, _ in found],
                         [(26, 'file'), (26 + len(file_record()) + 10, 'file'),
                          (26 + len(file_record()) + 10 + len(bare), 'job')])
        self.assertEqual([record.get('file_id') for _, kind, record in found if kind == 'file'],
                         [FILE_ID.bytes_le, None])

    def test_file_id_needs_the_whole_prefix(self):
        data = FILE_ID.bytes_le + bytes.fromhex('fe0001040002') + file_record()
        self.assertEqual([record['file_id'] for _, _, record in bq.find_records(data)], [None])

    def test_a_marker_followed_by_zeros_reports_nothing(self):
        data = JOB_MARKERS[0] + bytes(2000) + job(name='Next Job')
        self.assertEqual([record['name'] for _, _, record in bq.find_records(data)], ['Next Job'])


class ValueTest(unittest.TestCase):
    def test_filetime(self):
        self.assertEqual(bq.filetime(CREATED), WHEN)
        self.assertEqual(bq.filetime(116444736000000000),
                         datetime(1970, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(bq.filetime(0), '')
        self.assertEqual(bq.filetime(157469184000000001), '')

    def test_guid_text(self):
        self.assertEqual(bq.guid_text(JOB_ID.bytes_le), '11111111-2222-3333-4444-555555555555')


# ESE page and tag flags as the reader uses them: a leaf page, a tag flagged deleted, and a tag
# whose key begins with the page's common key.
LEAF_PAGE, DELETED, COMMON = 0x2, 0x2, 0x4


class FakePage:  # pylint: disable=too-few-public-methods
    def __init__(self, leaf, tags, common=b''):
        self.record = {'PageFlags': LEAF_PAGE if leaf else 0}
        self._tags = [(0, common)] + list(tags)

    def iterDataTagNums(self):  # pylint: disable=invalid-name
        return range(1, len(self._tags))

    def getTag(self, number):  # pylint: disable=invalid-name
        return self._tags[number]


class FakeEse:  # pylint: disable=too-few-public-methods
    def __init__(self, tables, pages):
        self.tables, self.pages, self.read = tables, pages, []

    def openTable(self, name):  # pylint: disable=invalid-name
        if name not in self.tables:
            return None
        table, root = self.tables[name]
        return {'TableData': table, 'FatherDataPageNumber': root}

    def getPage(self, number):  # pylint: disable=invalid-name
        self.read.append(number)
        return self.pages[number]


def record_leaf(record_id, value, item_flags=0x01, column=256):
    """A leaf tag holding one Jobs or Files record: the key (0x7F and the Id), then the
    record: its header, the offset of the tagged columns, the Id, the null bitmap, the entry
    for the tagged column at offset 4, the item flag byte and the value."""
    key = b'\x7f' + record_id.bytes_le
    entry = (b'\x01\x7f' + struct.pack('<H', 21) + record_id.bytes_le + b'\xfe'
             + struct.pack('<HH', column, 4) + bytes([item_flags]) + value)
    return struct.pack('<H', len(key)) + key + entry


def branch(child):
    return struct.pack('<H', 1) + b'\x7f' + struct.pack('<I', child)


def lv_catalog(root):
    """A long value catalog entry: the data definition header, then the fixed part (father
    page ID, type 4 for a long value, identifier), the root page and the space usage."""
    return {'EntryData': bytes(4) + struct.pack('<LHL', 0, 4, 0) + struct.pack('<LL', root, 0)}


class TableTest(unittest.TestCase):
    def setUp(self):
        self.stored = job(name='Stored Apart', job_id=OLD_JOB_ID)
        half = len(self.stored) // 2
        lv_id = struct.pack('>I', 42)
        self.pages = {
            10: FakePage(False, [(0, branch(11)), (DELETED, branch(13)), (0, branch(12))]),
            11: FakePage(True, [(0x1, record_leaf(JOB_ID, job())),
                                (0x1 | DELETED, struct.pack('<H', 17) + b'\x7f' + bytes(16) + b'\x00')]),
            12: FakePage(True, [(0x1, record_leaf(OLD_JOB_ID, struct.pack('<I', 42), 0x05))]),
            13: FakePage(True, [(0, record_leaf(uuid.UUID(int=13), job(name='Not Read')))]),
            20: FakePage(True, [
                (0, struct.pack('<H', 4) + lv_id + struct.pack('<II', 1, len(self.stored))),
                (COMMON, struct.pack('<HH', 4, 4) + struct.pack('>I', 0) + self.stored[:half]),
                (0, struct.pack('<H', 8) + lv_id + struct.pack('>I', half) + self.stored[half:]),
            ], common=lv_id),
            30: FakePage(True, [(0x1, record_leaf(FILE_ID, file_record())),
                                (0x1, b'\x00\x00' + b'\x01\x02' + bytes(30)),
                                (0x1, record_leaf(OLD_FILE_ID, b'xx', column=257))]),
        }
        self.ese = FakeEse({'Jobs': ({'LongValues': {'lv': lv_catalog(20)}}, 10),
                            'Files': ({'LongValues': {}}, 30)}, self.pages)
        self.db = object.__new__(bq.QmgrDatabase)
        self.db._db = self.ese  # pylint: disable=protected-access

    def test_jobs_inline_separated_and_deleted(self):
        self.assertEqual(self.db.records('Jobs'), [
            (JOB_ID.bytes_le, job(), False),
            (None, None, True),
            (OLD_JOB_ID.bytes_le, self.stored, False),
        ])

    def test_branch_flagged_deleted_not_followed(self):
        self.db.records('Jobs')
        self.assertNotIn(13, self.ese.read)

    def test_other_layouts_kept_for_counting(self):
        self.assertEqual(self.db.records('Files'), [
            (FILE_ID.bytes_le, file_record(), False),
            (None, None, False),
            (OLD_FILE_ID.bytes_le, None, False),
        ])

    def test_long_value_piece_flagged_deleted_not_used(self):
        tags = self.pages[20]._tags  # pylint: disable=protected-access
        tags[3] = (DELETED, tags[3][1])
        self.assertEqual(self.db.records('Jobs')[2], (OLD_JOB_ID.bytes_le, None, False))

    def test_missing_long_value_piece(self):
        del self.pages[20]._tags[3]  # pylint: disable=protected-access
        self.assertEqual(self.db.records('Jobs')[2], (OLD_JOB_ID.bytes_le, None, False))

    def test_table_absent(self):
        self.assertEqual(self.db.records('Other'), [])


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class FakeQmgr:  # pylint: disable=too-few-public-methods
    tables = {}

    def __init__(self, path):
        self.path = path

    def records(self, name):
        return self.tables[name]


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target, value in (('logfunc', self.logged.append), ('QmgrDatabase', FakeQmgr)):
            patcher = patch.object(artifact, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.live_job = job(state=1)
        self.old_job = job(name='Old Job', job_id=OLD_JOB_ID, state=4, file_ids=(OLD_FILE_ID,),
                           errors=(0x80072EE7,))
        FakeQmgr.tables = {'Jobs': [(JOB_ID.bytes_le, self.live_job, False), (None, None, True)],
                           'Files': [(FILE_ID.bytes_le, file_record(), False)]}
        folder = self.root/'ProgramData'/'Microsoft'/'Network'/'Downloader'
        folder.mkdir(parents=True)
        self.folder = folder
        self.files = [folder/name for name in ('qmgr.db', 'edb.log', 'edbres00001.jrs',
                                               'qmgr.jfm', 'edb.chk')]
        self.files[0].write_bytes(bytes(64) + self.live_job + bytes(8) + inline_file())
        self.files[1].write_bytes(
            job(state=0) + bytes(8) + self.old_job + inline_file(
                OLD_FILE_ID, remote='https://example.com/old.cab', total=UNKNOWN_SIZE)
            + bytes(4) + file_record(remote='https://example.com/other.cab',
                                     transferred=1 << 63) + JOB_MARKERS[1] + bytes(600))
        self.files[2].write_bytes(bytes(4096))
        self.files[3].write_bytes(job(name='Not Searched', job_id=uuid.UUID(int=7)))
        self.files[4].write_bytes(bytes(16))

    def run_both(self, files=None):
        context = Context(self.root, files or self.files)
        return (artifact.bitsJobs.__wrapped__(context),
                artifact.bitsJobFiles.__wrapped__(context))

    def test_job_rows(self):
        (headers, rows, sources), _ = self.run_both()
        self.assertEqual(headers[:2], (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime')))
        self.assertEqual([row[2:] for row in rows], [
            ('Font Download', '11111111-2222-3333-4444-555555555555', 'Connecting (1)',
             'Download (0)', 'Normal (2)', OWNER, '', '', '', 3, 1,
             '66666666-7777-8888-9999-aaaaaaaaaaaa', '', 'Live', 'qmgr.db', 1),
            ('Font Download', '11111111-2222-3333-4444-555555555555', 'Queued (0)',
             'Download (0)', 'Normal (2)', OWNER, '', '', '', 3, 1,
             '66666666-7777-8888-9999-aaaaaaaaaaaa', '', 'Recovered', 'edb.log', 1),
            ('Old Job', '12121212-3434-5656-7878-909090909090', 'Error (4)', 'Download (0)',
             'Normal (2)', OWNER, '', '', '', 3, 1, 'abababab-cdcd-efef-0101-232323232323',
             '0x80072EE7', 'Recovered', 'edb.log', 1),
        ])
        self.assertEqual({row[:2] for row in rows}, {(WHEN, LATER)})
        self.assertEqual(sources.splitlines(), [str(self.files[i]) for i in (1, 2, 0)])

    def test_file_rows(self):
        _, (headers, rows, _) = self.run_both()
        self.assertEqual(headers[:5], ('Remote Name', 'Local Name', 'Temporary Name',
                                       'Bytes Transferred', 'Bytes Total'))
        local = 'C:\\Users\\tester\\AppData\\Local\\Temp\\setup.exe'
        temporary = 'C:\\Users\\tester\\AppData\\Local\\Temp\\BIT1A2B.tmp'
        volume = '\\\\?\\Volume{01234567-89ab-cdef-0123-456789abcdef}\\'
        self.assertEqual(rows, [
            ('https://example.com/old.cab', local, temporary, 1024, '',
             'abababab-cdcd-efef-0101-232323232323', '12121212-3434-5656-7878-909090909090',
             'Old Job', 'C:\\', volume, 'Recovered', 'edb.log', 1),
            ('https://example.com/other.cab', local, temporary, '9223372036854775808', 4096,
             '', '', '', 'C:\\', volume, 'Recovered', 'edb.log', 1),
            ('https://example.com/setup.exe', local, temporary, 1024, 4096,
             '66666666-7777-8888-9999-aaaaaaaaaaaa', '11111111-2222-3333-4444-555555555555',
             'Font Download', 'C:\\', volume, 'Live', 'qmgr.db', 1),
        ])

    def test_rows_fit_sqlite(self):
        (jobs, files) = self.run_both()
        with sqlite3.connect(':memory:') as db:
            for (headers, rows, _) in (jobs, files):
                db.execute(f'create table t{len(headers)} ({", ".join(f"c{i}" for i in range(len(headers)))})')
                db.executemany(f'insert into t{len(headers)} values ({", ".join("?" * len(headers))})',
                               [tuple(str(v) if isinstance(v, datetime) else v for v in row)
                                for row in rows])

    def test_run_log(self):
        self.run_both()
        prefix = 'BITS Jobs: ProgramData/Microsoft/Network/Downloader/'
        self.assertEqual([line for line in self.logged if line.startswith('BITS Jobs:')], [
            prefix + 'qmgr.db: Jobs table records: 1 live, 1 flagged deleted, 0 not read',
            prefix + 'qmgr.db: Files table records: 1 live, 0 flagged deleted, 0 not read',
            prefix + 'edb.log: 2 job and 2 file records found',
            prefix + 'qmgr.db: 1 job and 1 file records found',
        ])

    def test_tables_unreadable(self):
        def fail(path):
            raise Exception(f'bad page in {pathlib.Path(path).name}')  # pylint: disable=broad-exception-raised
        with patch.object(artifact, 'QmgrDatabase', fail):
            (_, rows, _), _ = self.run_both()
        self.assertEqual([row[15] for row in rows], ['Recovered'] * 3)
        self.assertIn('BITS Jobs: could not read the tables of '
                      'ProgramData/Microsoft/Network/Downloader/qmgr.db: bad page in qmgr.db',
                      self.logged)

    def test_two_downloader_folders(self):
        other = self.root/'Windows.old'/'ProgramData'/'Microsoft'/'Network'/'Downloader'
        other.mkdir(parents=True)
        (other/'edb.log').write_bytes(job(name='Older Windows', job_id=uuid.UUID(int=9)))
        (_, rows, _), _ = self.run_both(self.files + [other/'edb.log'])
        self.assertEqual({(row[2], row[16]) for row in rows}, {
            ('Font Download', 'ProgramData/Microsoft/Network/Downloader/edb.log'),
            ('Font Download', 'ProgramData/Microsoft/Network/Downloader/qmgr.db'),
            ('Old Job', 'ProgramData/Microsoft/Network/Downloader/edb.log'),
            ('Older Windows', 'Windows.old/ProgramData/Microsoft/Network/Downloader/edb.log'),
        })

    def test_copies_counted_across_files(self):
        self.files[2].write_bytes(self.old_job)
        (_, rows, _), _ = self.run_both()
        old = [row for row in rows if row[2] == 'Old Job']
        self.assertEqual([(row[16], row[17]) for row in old], [('edb.log\nedbres00001.jrs', 2)])

    def test_declared_paths(self):
        for key in ('bitsJobs', 'bitsJobFiles'):
            patterns = artifact.__artifacts_v2__[key]['paths']
            for name in ('qmgr.db', 'edb00001.log', 'edbres00002.jrs'):
                path = f'x/ProgramData/Microsoft/Network/Downloader/{name}'
                self.assertTrue(any(fnmatch.fnmatch(path, p) for p in patterns), (key, name))


if __name__ == '__main__':
    unittest.main()
