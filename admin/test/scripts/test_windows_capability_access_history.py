"""Pin the rows scripts/artifacts/windowsCapabilityAccessHistory.py reads.

The database is built here with the tables CapabilityAccessManager.db carries, and
times are written as FILETIME values computed from the expected datetimes.
"""
import datetime
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsCapabilityAccessHistory as cam  # pylint: disable=wrong-import-position

_UTC = datetime.timezone.utc
_FOLDER = 'ProgramData/Microsoft/Windows/CapabilityAccessManager'
_SCHEMA = (
    'CREATE TABLE NonPackagedUsageHistory(ID INTEGER PRIMARY KEY NOT NULL,LastUsedTimeStart INTEGER NOT '
    'NULL,LastUsedTimeStop INTEGER NOT NULL,AccessBlocked INTEGER NOT NULL,Capability INTEGER NOT NULL,'
    'FileID INTEGER NOT NULL,ProgramID INTEGER NOT NULL,BinaryFullPath INTEGER NOT NULL,UserSid INTEGER '
    'NOT NULL)',
    'CREATE TABLE PackagedUsageHistory(ID INTEGER PRIMARY KEY NOT NULL,LastUsedTimeStart INTEGER NOT NULL,'
    'LastUsedTimeStop INTEGER NOT NULL,AccessBlocked INTEGER NOT NULL,Capability INTEGER NOT NULL,'
    'PackageFamilyName INTEGER NOT NULL,UserSid INTEGER NOT NULL)',
    'CREATE TABLE NonPackagedIdentityRelationship(ID INTEGER PRIMARY KEY NOT NULL,BinaryFullPath INTEGER '
    'NOT NULL,FileID INTEGER NOT NULL,ProgramID INTEGER NOT NULL,LastObservedTime INTEGER NOT NULL)',
    'CREATE TABLE Capabilities(ID INTEGER PRIMARY KEY NOT NULL,StringValue TEXT COLLATE NOCASE NOT NULL)',
    'CREATE TABLE PackageFamilyNames(ID INTEGER PRIMARY KEY NOT NULL,StringValue TEXT COLLATE NOCASE NOT NULL)',
    'CREATE TABLE BinaryFullPaths(ID INTEGER PRIMARY KEY NOT NULL,StringValue TEXT COLLATE NOCASE NOT NULL)',
    'CREATE TABLE Users(ID INTEGER PRIMARY KEY NOT NULL,StringValue TEXT COLLATE NOCASE NOT NULL)',
    'CREATE TABLE FileIDs(ID INTEGER PRIMARY KEY NOT NULL,StringValue TEXT COLLATE NOCASE NOT NULL)',
    'CREATE TABLE ProgramIDs(ID INTEGER PRIMARY KEY NOT NULL,StringValue TEXT COLLATE NOCASE NOT NULL)',
)
_SID = 'S-1-5-21-1-2-3-1001'
_FILE_ID = '0000' + '1' * 40
_PROGRAM_ID = '0006' + '2' * 40
_EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'


def _when(day, hour, minute, second=0, micro=0):
    return datetime.datetime(2023, 1, day, hour, minute, second, micro, tzinfo=_UTC)


def _filetime(moment):
    delta = moment - datetime.datetime(1601, 1, 1, tzinfo=_UTC)
    return (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.path = self.root / _FOLDER / 'CapabilityAccessManager.db'
        self.path.parent.mkdir(parents=True)
        self.writer = None

    def tearDown(self):
        if self.writer is not None:
            self.writer.close()
        self._tmp.cleanup()

    def _build(self, skip=(), wal_rows=False):
        db = sqlite3.connect(self.path)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA wal_autocheckpoint=0')
        for statement in _SCHEMA:
            if not any(f'TABLE {name}(' in statement for name in skip):
                db.execute(statement)
        with db:
            db.executemany('INSERT INTO Capabilities VALUES (?, ?)', [(1, 'contacts'), (2, 'location')])
            db.execute('INSERT INTO PackageFamilyNames VALUES (1, ?)', ('Microsoft.WindowsCamera_8wekyb3d8bbwe',))
            db.execute('INSERT INTO Users VALUES (1, ?)', (_SID,))
            db.execute('INSERT INTO BinaryFullPaths VALUES (1, ?)', (_EDGE,))
            db.execute('INSERT INTO FileIDs VALUES (3, ?)', (_FILE_ID,))
            db.execute('INSERT INTO ProgramIDs VALUES (1, ?)', (_PROGRAM_ID,))
            if 'PackagedUsageHistory' not in skip:
                db.execute('INSERT INTO PackagedUsageHistory VALUES (51, ?, ?, 0, 2, 1, 1)',
                           (_filetime(_when(5, 3, 0)), _filetime(_when(5, 3, 1, 30))))
                # A later id with an earlier start, so start order and id order differ.
                db.execute('INSERT INTO PackagedUsageHistory VALUES (53, ?, ?, 0, 1, 1, 1)',
                           (_filetime(_when(4, 9, 0)), _filetime(_when(4, 9, 0))))
            if 'NonPackagedUsageHistory' not in skip:
                db.execute('INSERT INTO NonPackagedUsageHistory VALUES (2, ?, ?, 0, 2, 3, 1, 1, 1)',
                           (_filetime(_when(5, 2, 50, 24, 642954)), _filetime(_when(5, 2, 50, 29))))
            if 'NonPackagedIdentityRelationship' not in skip:
                db.execute('INSERT INTO NonPackagedIdentityRelationship VALUES (1, 1, 3, 1, ?)',
                           (_filetime(datetime.datetime(2022, 12, 4, 0, 40, 15, tzinfo=_UTC)),))
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        if wal_rows:
            # Written after the checkpoint and kept open, so these rows exist only in the WAL.
            with db:
                db.execute('INSERT INTO PackagedUsageHistory VALUES (52, ?, ?, 0, 1, 1, 1)',
                           (_filetime(_when(6, 17, 3, 37)), _filetime(_when(6, 17, 3, 37))))
            self.writer = db
        else:
            db.close()

    def _files(self):
        return [str(p) for p in sorted(self.path.parent.iterdir())]

    def _run(self, processor):
        logs = []
        with mock.patch.object(cam, 'logfunc', logs.append):
            result = processor.__wrapped__(FakeContext(self.root, self._files()))
        return result + (logs,)

    def test_history_rows_join_their_lookups_and_sort_by_start(self):
        self._build(wal_rows=True)
        self.assertTrue(any(p.endswith('-wal') for p in self._files()))
        headers, rows, source, logs = self._run(cam.capabilityAccessHistory)
        self.assertEqual(len(headers), len(rows[0]))
        relative = f'{_FOLDER}/CapabilityAccessManager.db'
        self.assertEqual(rows, [
            (_when(4, 9, 0), _when(4, 9, 0), 'contacts', 'Packaged',
             'Microsoft.WindowsCamera_8wekyb3d8bbwe', _SID, 0, '', '', 53, relative),
            (_when(5, 2, 50, 24, 642954), _when(5, 2, 50, 29), 'location', 'NonPackaged', _EDGE, _SID, 0,
             _FILE_ID, _PROGRAM_ID, 2, relative),
            (_when(5, 3, 0), _when(5, 3, 1, 30), 'location', 'Packaged',
             'Microsoft.WindowsCamera_8wekyb3d8bbwe', _SID, 0, '', '', 51, relative),
            (_when(6, 17, 3, 37), _when(6, 17, 3, 37), 'contacts', 'Packaged',
             'Microsoft.WindowsCamera_8wekyb3d8bbwe', _SID, 0, '', '', 52, relative),
        ])
        self.assertEqual(source.splitlines(), [str(self.path)])
        self.assertEqual(logs, [])

    def test_identity_rows(self):
        self._build()
        headers, rows, _source, logs = self._run(cam.capabilityAccessIdentities)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [(datetime.datetime(2022, 12, 4, 0, 40, 15, tzinfo=_UTC), _EDGE, _FILE_ID,
                                 _PROGRAM_ID, 1, f'{_FOLDER}/CapabilityAccessManager.db')])
        self.assertEqual(logs, [])

    def test_a_missing_table_is_logged_and_the_other_is_read(self):
        self._build(skip=('NonPackagedUsageHistory',))
        _headers, rows, _source, logs = self._run(cam.capabilityAccessHistory)
        self.assertEqual([(row[3], row[9]) for row in rows], [('Packaged', 53), ('Packaged', 51)])
        self.assertEqual(logs, [f'Capability Access History: {_FOLDER}/CapabilityAccessManager.db has no '
                                'NonPackagedUsageHistory table'])

    def test_a_sidecar_alone_is_not_read_as_the_database(self):
        sidecar = self.path.parent / 'CapabilityAccessManager.db-wal'
        sidecar.write_bytes(b'\x00' * 32)
        _headers, rows, source, logs = self._run(cam.capabilityAccessHistory)
        self.assertEqual((rows, source, logs), ([], '', []))


if __name__ == '__main__':
    unittest.main()
