"""Pin the mpenginedb.db reader (scripts/mpenginedb.py) and the artifacts built on it.

Every database below is made by the test with sqlite3 and encrypted with the codec the reader
reverses; no record comes from a real machine.
"""
import os
import pathlib
import shutil
import sqlite3
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import mpenginedb as reader  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsDefenderMpEngineDb as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
PS = 4096
SCANS = 'ProgramData/Microsoft/Windows Defender/Scans'
OTHER_KEY = bytes(range(255, -1, -1))
SCHEMAS = (
    'CREATE TABLE BmProcessInfo(ID INTEGER PRIMARY KEY NOT NULL, PPIDHash INTEGER NOT NULL, '
    'ProcessStartTime INTEGER NOT NULL, PID INTEGER NOT NULL, ImageFileName NVARCHAR, '
    'CommandLineArgs NVARCHAR)',
    'CREATE INDEX BmPid ON BmProcessInfo(PPIDHash)',
    'CREATE TABLE BackupProcessInfo(ID INTEGER PRIMARY KEY NOT NULL, Key INTEGER NULL, '
    'FilePath NVARCHAR NULL, FirstStartTime INTEGER NULL, NextUSN INTEGER NULL, '
    'AutomaticRemovalPolicy INTEGER NULL, ImpactedCBPNameSpaces NVARCHAR NULL, '
    'InstanceTimeStamp INTEGER NULL)',
    'CREATE TABLE FileHashes(ID INTEGER PRIMARY KEY NOT NULL, Key INTEGER NULL, VSN INTEGER NULL, '
    'FileID INTEGER NULL, USN INTEGER NULL, InstanceTimeStamp INTEGER NULL, SHA1 BLOB NULL, '
    'MD5 BLOB NULL, SHA256 BLOB NULL)',
)
# 2031-06-15 08:30:12 UTC as a FILETIME (an invented time)
FT_BASE = (datetime(2031, 6, 15, 8, 30, 12, tzinfo=UTC) - datetime(1601, 1, 1, tzinfo=UTC)).total_seconds()
FT_BASE = int(FT_BASE) * 10_000_000


def encrypt_pages(plain, key=reader.KEY):
    stream = reader.rc4_keystream(key, PS)
    return b''.join(reader.decrypt_page(plain[i:i + PS], i // PS + 1, stream, PS)
                    for i in range(0, len(plain), PS))


def encrypt_wal(plain_wal, key=reader.KEY, salt_override=None):
    """The plain WAL SQLite wrote, with every frame body encrypted and the checksums
    recomputed over the stored bytes, which is how the Defender WAL is laid out."""
    stream = reader.rc4_keystream(key, PS)
    magic = struct.unpack('>I', plain_wal[:4])[0]
    big = bool(magic & 1)
    header = bytearray(plain_wal[:32])
    s0, s1 = reader._checksum(bytes(header[:24]), 0, 0, big)  # pylint: disable=protected-access
    header[24:32] = struct.pack('>2I', s0, s1)
    out = bytearray(header)
    for offset in range(32, len(plain_wal) - 24 - PS + 1, 24 + PS):
        frame = bytearray(plain_wal[offset:offset + 24])
        number = struct.unpack('>I', frame[:4])[0]
        body = reader.decrypt_page(plain_wal[offset + 24:offset + 24 + PS], number, stream, PS)
        if salt_override:
            frame[8:16] = struct.pack('>2I', *salt_override)
        s0, s1 = reader._checksum(bytes(frame[:8]), s0, s1, big)  # pylint: disable=protected-access
        s0, s1 = reader._checksum(body, s0, s1, big)  # pylint: disable=protected-access
        frame[16:24] = struct.pack('>2I', s0, s1)
        out += bytes(frame) + body
    return bytes(out)


class Fixture:
    """A plain database and, when asked, the WAL of changes made after it."""

    def __init__(self, directory, rows_before, rows_after=()):
        self.path = os.path.join(directory, 'make.db')
        con = sqlite3.connect(self.path)
        con.execute(f'PRAGMA page_size={PS}')
        con.execute('PRAGMA journal_mode=WAL')
        for sql in SCHEMAS:
            con.execute(sql)
        con.executemany('INSERT INTO BmProcessInfo(PPIDHash, ProcessStartTime, PID, ImageFileName, '
                        'CommandLineArgs) VALUES (?,?,?,?,?)', rows_before)
        con.commit()
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        with open(self.path, 'rb') as handle:
            self.plain_before = handle.read()
        self.plain_wal = b''
        if rows_after:
            con.execute('PRAGMA wal_autocheckpoint=0')
            con.executemany('INSERT INTO BmProcessInfo(PPIDHash, ProcessStartTime, PID, ImageFileName, '
                            'CommandLineArgs) VALUES (?,?,?,?,?)', rows_after)
            con.commit()
            with open(self.path + '-wal', 'rb') as handle:
                self.plain_wal = handle.read()
        con.close()


ROWS_A = [(-5, FT_BASE, 100, '\\Device\\HarddiskVolume3\\Windows\\System32\\a.exe', 'a.exe /x'),
          (7, FT_BASE + 10_000_000, 200, '\\Device\\HarddiskVolume3\\Windows\\System32\\b.exe', None)]
ROWS_B = [(9, FT_BASE + 20_000_000, 300, '\\Device\\HarddiskVolume3\\Temp\\c.exe', 'c.exe')]


class ReaderTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def test_rc4_matches_the_published_test_vector(self):
        stream = reader.rc4_keystream(b'Key', 9)
        self.assertEqual(bytes(a ^ b for a, b in zip(b'Plaintext', stream)).hex().upper(),
                         'BBF316E8D940AF0AD3')

    def test_the_stored_key_is_256_bytes(self):
        self.assertEqual(len(reader.KEY), 256)

    def test_page_codec_is_its_own_inverse_and_leaves_page_1_bytes_16_to_23(self):
        fixture = Fixture(self.dir, ROWS_A)
        stored = encrypt_pages(fixture.plain_before)
        self.assertEqual(stored[16:24], fixture.plain_before[16:24])
        self.assertNotEqual(stored[:16], fixture.plain_before[:16])
        self.assertNotEqual(stored[PS:2 * PS], fixture.plain_before[PS:2 * PS])
        result = reader.read_database(stored)
        self.assertEqual(result.reason, '')
        self.assertEqual(result.plain[:100][:16], reader.MAGIC)
        self.assertEqual(result.plain[PS:], fixture.plain_before[PS:])

    def test_a_file_the_key_does_not_decrypt_is_refused_with_a_reason(self):
        fixture = Fixture(self.dir, ROWS_A)
        result = reader.read_database(encrypt_pages(fixture.plain_before, OTHER_KEY))
        self.assertIsNone(result.plain)
        self.assertIn('does not decrypt', result.reason)
        self.assertIsNone(reader.read_database(b'SQLite format 3\x00' + bytes(2000)).plain)
        self.assertIsNone(reader.read_database(b'').plain)

    def test_a_header_that_decrypts_over_garbage_pages_is_refused(self):
        fixture = Fixture(self.dir, ROWS_A)
        stored = bytearray(encrypt_pages(fixture.plain_before))
        stored[100:101] = bytes([stored[100] ^ 0xFF])
        result = reader.read_database(bytes(stored))
        self.assertIsNone(result.plain)
        self.assertIn('b-tree', result.reason)

    def test_wal_frames_are_replayed_over_the_database(self):
        fixture = Fixture(self.dir, ROWS_A, ROWS_B)
        result = reader.read_database(encrypt_pages(fixture.plain_before), encrypt_wal(fixture.plain_wal))
        self.assertEqual((result.wal_frames > 0, result.wal_valid_frames, result.wal_applied_frames),
                         (True, result.wal_frames, result.wal_frames))
        with reader.Database(result.plain) as database:
            rows, error, missing = database.rows('BmProcessInfo', ['PID', 'ImageFileName'])
        self.assertEqual((error, missing), ('', []))
        self.assertEqual([row['PID'] for row in rows], [100, 200, 300])

    def test_without_the_wal_only_the_database_file_is_read(self):
        fixture = Fixture(self.dir, ROWS_A, ROWS_B)
        result = reader.read_database(encrypt_pages(fixture.plain_before))
        with reader.Database(result.plain) as database:
            rows, _error, _missing = database.rows('BmProcessInfo', ['PID'])
        self.assertEqual([row['PID'] for row in rows], [100, 200])

    def test_frames_of_an_older_wal_generation_and_a_broken_chain_are_not_applied(self):
        fixture = Fixture(self.dir, ROWS_A, ROWS_B)
        wal = encrypt_wal(fixture.plain_wal)
        stored = encrypt_pages(fixture.plain_before)
        # Frames carrying other salts: stale, none applied.
        stale = bytearray(wal)
        for offset in range(32, len(stale) - 24 - PS + 1, 24 + PS):
            stale[offset + 8:offset + 16] = struct.pack('>2I', 1, 2)
        result = reader.read_database(stored, bytes(stale))
        self.assertEqual((result.wal_valid_frames, result.wal_applied_frames), (0, 0))
        # One byte changed in the first frame body: the chain breaks there.
        broken = bytearray(wal)
        broken[32 + 24 + 10] ^= 1
        result = reader.read_database(stored, bytes(broken))
        self.assertEqual((result.wal_valid_frames, result.wal_applied_frames), (0, 0))
        # A WAL header whose checksum does not hold is not applied and says so.
        bad_header = bytearray(wal)
        bad_header[24] ^= 1
        result = reader.read_database(stored, bytes(bad_header))
        self.assertEqual(result.wal_applied_frames, 0)
        self.assertTrue(any('header checksum' in note for note in result.wal_notes))

    def test_frames_after_the_last_commit_are_not_applied(self):
        fixture = Fixture(self.dir, ROWS_A, ROWS_B)
        wal = encrypt_wal(fixture.plain_wal)
        # Keep the committed frames, then append a copy of the first frame with a continuing chain
        # but no commit size: valid in the chain, uncommitted.
        frames = [wal[o:o + 24 + PS] for o in range(32, len(wal), 24 + PS)]
        self.assertGreaterEqual(len(frames), 1)
        count_before = len(frames)
        plain_frames = fixture.plain_wal
        extra = bytearray(plain_frames[32:32 + 24 + PS])
        extra[4:8] = struct.pack('>I', 0)
        rebuilt = encrypt_wal(plain_frames + bytes(extra))
        result = reader.read_database(encrypt_pages(fixture.plain_before), rebuilt)
        self.assertEqual(result.wal_frames, count_before + 1)
        self.assertEqual(result.wal_applied_frames, count_before)

    def test_a_frame_with_page_number_0_ends_the_chain_and_a_frame_past_the_final_size_is_skipped(self):
        fixture = Fixture(self.dir, ROWS_A, ROWS_B)
        wal = bytearray(encrypt_wal(fixture.plain_wal))
        stored = encrypt_pages(fixture.plain_before)
        first = reader.read_database(stored, bytes(wal))
        frames = first.wal_frames
        self.assertGreater(frames, 1)
        zero = bytearray(fixture.plain_wal)
        zero[32 + 24 + PS + 0:32 + 24 + PS + 4] = struct.pack('>I', 0)  # page number of frame 2
        result = reader.read_database(stored, encrypt_wal(bytes(zero)))
        self.assertEqual(result.wal_valid_frames, 1)
        self.assertEqual(result.wal_applied_frames, 0)  # no commit among the frames that count

    def test_a_wal_with_another_format_version_is_not_applied(self):
        fixture = Fixture(self.dir, ROWS_A, ROWS_B)
        plain = bytearray(fixture.plain_wal)
        plain[4:8] = struct.pack('>I', 3007001)
        result = reader.read_database(encrypt_pages(fixture.plain_before), encrypt_wal(bytes(plain)))
        self.assertEqual(result.wal_applied_frames, 0)
        self.assertTrue(any('format version' in note for note in result.wal_notes))

    def test_the_decrypted_copy_and_the_files_sqlite_makes_beside_it_are_all_removed(self):
        fixture = Fixture(self.dir, ROWS_A)
        self.assertEqual(fixture.plain_before[18:20], b'\x02\x02')  # the header says WAL, so SQLite makes sidecars
        result = reader.read_database(encrypt_pages(fixture.plain_before))
        with reader.Database(result.plain) as database:
            folder = database.folder
            database.rows('BmProcessInfo', ['PID'])
            self.assertTrue(os.path.isdir(folder))
        self.assertFalse(os.path.exists(folder))

    def test_a_schema_that_cannot_be_read_is_reported_not_called_a_missing_table(self):
        fixture = Fixture(self.dir, ROWS_A)
        plain = bytearray(reader.read_database(encrypt_pages(fixture.plain_before)).plain)
        plain[103:105] = b'\xff\xff'  # a cell count no page can hold, on the first b-tree page of sqlite_master
        with reader.Database(bytes(plain)) as database:
            rows, error, _missing = database.rows('BmProcessInfo', ['PID'])
        self.assertEqual(rows, [])
        self.assertNotEqual(error, 'table not present')
        self.assertNotEqual(error, '')

    def test_filetime(self):
        self.assertEqual(reader.filetime(FT_BASE), datetime(2031, 6, 15, 8, 30, 12, tzinfo=UTC))
        for value in (0, -1, 10, 2 ** 63, None, '140000000000000007', True, 119600063999999999):
            self.assertEqual(reader.filetime(value), '')

    def test_shm_summary_reads_the_first_header_copy(self):
        shm = struct.pack('<IIIBBHII', 3007000, 0, 5, 1, 0, PS, 612, 213) + bytes(100)
        self.assertEqual(reader.shm_summary(shm), (612, 213))
        self.assertIsNone(reader.shm_summary(b'short'))
        self.assertIsNone(reader.shm_summary(struct.pack('<IIIBBHII', 1, 0, 0, 1, 0, PS, 1, 1) + bytes(8)))

    def test_rows_reports_missing_columns_and_absent_tables(self):
        fixture = Fixture(self.dir, ROWS_A + ROWS_B * 40)
        result = reader.read_database(encrypt_pages(fixture.plain_before))
        with reader.Database(result.plain) as database:
            rows, error, missing = database.rows('BmProcessInfo', ['PID', 'NoSuchColumn'])
            self.assertEqual((len(rows), error, missing), (42, '', ['NoSuchColumn']))
            self.assertIsNone(rows[0]['NoSuchColumn'])
            self.assertEqual(database.rows('NoSuchTable', ['PID']), ([], 'table not present', ['PID']))
            self.assertEqual(database.count('BmProcessInfo'), 42)

    def test_a_read_that_stops_returns_the_rows_before_the_error_and_the_error(self):
        fixture = Fixture(self.dir, ROWS_A + ROWS_B * 150)
        result = reader.read_database(encrypt_pages(fixture.plain_before))
        plain = bytearray(result.plain)
        leaves = [n for n in range(1, len(plain) // PS)
                  if plain[n * PS] == 0x0D and struct.unpack('>H', plain[n * PS + 3:n * PS + 5])[0] > 0]
        self.assertGreaterEqual(len(leaves), 3)
        plain[leaves[-1] * PS + 3:leaves[-1] * PS + 5] = b'\xff\xff'
        with reader.Database(bytes(plain)) as database:
            rows, error, _missing = database.rows('BmProcessInfo', ['PID'])
        self.assertNotEqual(error, '')
        self.assertTrue(0 < len(rows) < 152)


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        patcher = patch.object(artifact, 'logfunc')
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def stage(self, fixture, with_wal=True, folder=SCANS, key=reader.KEY):
        base = os.path.join(self.root, folder)
        os.makedirs(base, exist_ok=True)
        files = []
        db = os.path.join(base, 'mpenginedb.db')
        with open(db, 'wb') as handle:
            handle.write(encrypt_pages(fixture.plain_before, key))
        files.append(db)
        if with_wal and fixture.plain_wal:
            with open(db + '-wal', 'wb') as handle:
                handle.write(encrypt_wal(fixture.plain_wal, key))
            files.append(db + '-wal')
        with open(db + '-shm', 'wb') as handle:
            handle.write(struct.pack('<IIIBBHII', 3007000, 0, 9, 1, 0, PS, 77, 88) + bytes(40))
        files.append(db + '-shm')
        return files

    def logged(self, text):
        return any(text in str(call) for call in self.log.call_args_list)

    def run_artifact(self, function, files):
        return function.__wrapped__(Context(self.root, files))

    def test_processes_rows_columns_times_and_source(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        files = self.stage(Fixture(directory, ROWS_A, ROWS_B))
        headers, rows, source = self.run_artifact(artifact.windowsDefenderMpEngineProcesses, files)
        self.assertEqual(headers[0], ('Process Start (UTC)', 'datetime'))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([(r[0], r[1], r[2], r[3]) for r in rows], [
            (datetime(2031, 6, 15, 8, 30, 12, tzinfo=UTC), 100,
             '\\Device\\HarddiskVolume3\\Windows\\System32\\a.exe', 'a.exe /x'),
            (datetime(2031, 6, 15, 8, 30, 13, tzinfo=UTC), 200,
             '\\Device\\HarddiskVolume3\\Windows\\System32\\b.exe', ''),
            (datetime(2031, 6, 15, 8, 30, 14, tzinfo=UTC), 300, '\\Device\\HarddiskVolume3\\Temp\\c.exe', 'c.exe')])
        self.assertEqual(sorted(source.split('\n')), sorted(files))
        self.assertTrue(self.logged('the -shm records 77 frames and a database of 88 pages'))

    def test_the_wal_is_what_adds_the_last_row(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        files = self.stage(Fixture(directory, ROWS_A, ROWS_B), with_wal=False)
        _headers, rows, _source = self.run_artifact(artifact.windowsDefenderMpEngineProcesses, files)
        self.assertEqual([row[1] for row in rows], [100, 200])

    def test_a_file_that_does_not_decrypt_returns_no_rows_and_still_names_its_path(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        files = self.stage(Fixture(directory, ROWS_A), key=OTHER_KEY)
        _headers, rows, source = self.run_artifact(artifact.windowsDefenderMpEngineProcesses, files)
        self.assertEqual(rows, [])
        self.assertEqual(sorted(source.split('\n')), sorted(files))
        self.assertTrue(self.logged('was not read'))

    def test_a_table_the_database_lacks_is_logged_and_the_others_still_read(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        files = self.stage(Fixture(directory, ROWS_A))
        _headers, rows, _source = self.run_artifact(artifact.windowsDefenderMpEngineFileInstances, files)
        self.assertEqual(rows, [])
        self.assertTrue(self.logged('no FileInstance table'))
        self.assertEqual(len(self.run_artifact(artifact.windowsDefenderMpEngineProcesses, files)[1]), 2)

    def test_hashes_are_written_as_hex_and_odd_times_are_left_blank(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        fixture = Fixture(directory, ROWS_A)
        con = sqlite3.connect(fixture.path)
        con.execute('INSERT INTO FileHashes(Key, VSN, FileID, USN, InstanceTimeStamp, SHA1, MD5, SHA256) '
                    'VALUES (1, -5, 300000000000007, 12, ?, ?, ?, ?)',
                    (FT_BASE, bytes(range(16)), bytes(range(20)), bytes(range(32))))
        con.execute('INSERT INTO FileHashes(Key, VSN, FileID, USN, InstanceTimeStamp) VALUES (2, 1, 2, 3, 5)')
        con.commit()
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        with open(fixture.path, 'rb') as handle:
            fixture.plain_before = handle.read()
        con.close()
        files = self.stage(fixture)
        headers, rows, _source = self.run_artifact(artifact.windowsDefenderMpEngineFileHashes, files)
        self.assertEqual(headers[0], ('Instance Time (UTC)', 'datetime'))
        self.assertEqual(rows[0][1:7], (-5, 300000000000007, 12, bytes(range(32)).hex(),
                                        bytes(range(16)).hex(), bytes(range(20)).hex()))
        self.assertEqual(rows[1][0], '')
        self.assertEqual(rows[1][4:7], ('', '', ''))
        self.assertTrue(self.logged('1 non-zero time value(s) in FileHashes'))

    def test_two_copies_are_each_read_and_the_row_count_is_the_sum(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        fixture = Fixture(directory, ROWS_A)
        files = self.stage(fixture, folder=SCANS) + self.stage(fixture, folder='other/' + SCANS)
        _headers, rows, _source = self.run_artifact(artifact.windowsDefenderMpEngineProcesses, files)
        self.assertEqual(len(rows), 4)

    def test_no_database_found(self):
        self.assertEqual(self.run_artifact(artifact.windowsDefenderMpEngineProcesses, [])[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
