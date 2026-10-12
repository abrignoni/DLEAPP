"""Pin the Recents (CoreRecents) artifact (scripts/artifacts/macosRecents.py).

The database is built for the test with the tables of the Recents database on macOS 11. The values are made up.
"""
import os
import pathlib
import plistlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosRecents as recents
# pylint: enable=wrong-import-position

SCHEMA = '''
CREATE TABLE recents (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, display_name TEXT, bundle_identifier TEXT,
    sending_address TEXT, original_source TEXT, dates TEXT NOT NULL, last_date INTEGER, weight FLOAT,
    record_hash TEXT NOT NULL, count INTEGER, group_kind INTEGER);
CREATE TABLE contacts (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, recent_id INTEGER, display_name TEXT, kind TEXT,
    address TEXT);
CREATE TABLE metadata (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, recent_id INTEGER, key TEXT, value,
    UNIQUE (recent_id, key));
'''
T1, T2 = 1700000000123, 1700000600000


def binary(value):
    return plistlib.dumps(value, fmt=plistlib.FMT_BINARY)  # pylint: disable=no-member


def build(path, with_metadata=True):
    database = sqlite3.connect(path)
    database.executescript(SCHEMA)
    database.execute("INSERT INTO recents VALUES (1, 'Lab Person', 'com.apple.mail', 'me@example.com', 'source one', "
                     "?, ?, NULL, 'h1', 2, 0)", (f'{T2}, {T1},bad,', T2))
    database.execute("INSERT INTO recents VALUES (2, 'A Place', 'com.apple.Maps', NULL, NULL, ?, NULL, 10.0, 'h2', 1, 3)",
                     (str(T1),))
    database.execute("INSERT INTO recents VALUES (4, NULL, 'com.example.none', NULL, NULL, '', 'x', NULL, 'h4', 0, 0)")
    database.execute("INSERT INTO contacts VALUES (1, 1, 'Second Person', 'email', 'second@example.com')")
    database.execute("INSERT INTO contacts VALUES (2, 1, 'First Person', 'phone', '+15555550100')")
    database.execute("INSERT INTO contacts VALUES (3, 2, 'A Place', 'map-location', 'place-id')")
    database.execute("INSERT INTO contacts VALUES (5, 99, 'Orphan', 'email', 'orphan@example.com')")
    if with_metadata:
        rows = [(2, 'longitude', binary(-66.5)), (2, 'latitude', binary(18.25)), (2, 'handle', binary(b'\x01\xff')),
                (2, 'flag', binary(True)), (1, 'givenName', binary('Lab')), (1, 'plain', 'text'), (1, 'raw', b'\x00\x01'),
                (1, 'none', None)]
        database.executemany('INSERT INTO metadata (recent_id, key, value) VALUES (?, ?, ?)', rows)
    else:
        database.execute('DROP TABLE metadata')
    database.commit()
    database.close()


def utc(*parts):
    return datetime(*parts, tzinfo=timezone.utc)


class Dates(unittest.TestCase):
    def test_milliseconds(self):
        self.assertEqual(recents.utc_from_milliseconds(T1), utc(2023, 11, 14, 22, 13, 20, 123000))
        self.assertEqual(recents.utc_from_milliseconds(' 1700000000123 '), utc(2023, 11, 14, 22, 13, 20, 123000))
        for value in ('x', '', None, '1e400', float('inf')):
            self.assertEqual(recents.utc_from_milliseconds(value), '', value)

    def test_list(self):
        self.assertEqual(recents.all_dates(f'{T2}, {T1},bad,, nan'),
                         ('2023-11-14 22:23:20.000 | 2023-11-14 22:13:20.123', 2))
        self.assertEqual(recents.all_dates(f'{T1}:{T2}:x'), ('2023-11-14 22:13:20.123 | 2023-11-14 22:23:20.000', 1))
        self.assertEqual(recents.all_dates(None), ('', 0))
        self.assertEqual(recents.all_dates(''), ('', 0))


class MetadataValue(unittest.TestCase):
    def test_values(self):
        self.assertEqual(recents.metadata_value(binary('Lab')), 'Lab')
        self.assertEqual(recents.metadata_value(binary(18.25)), '18.25')
        self.assertEqual(recents.metadata_value(binary(True)), 'True')
        self.assertEqual(recents.metadata_value(binary(b'\x01\xff')), '01ff')
        self.assertEqual(recents.metadata_value(binary({'a': [b'\x01', {'b': b'\x02'}], 'c': 3})),
                         "{'a': ['01', {'b': '02'}], 'c': 3}")
        self.assertEqual(recents.metadata_value(b'\x00\x01'), '0001')
        self.assertEqual(recents.metadata_value(b'bplist00'), '62706c6973743030')
        self.assertEqual(recents.metadata_value('text'), 'text')
        self.assertEqual(recents.metadata_value(7), '7')
        self.assertEqual(recents.metadata_value(None), '')


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, user, **options):
        folder = os.path.join(self.folder.name, 'Users', user, 'Library', 'Containers',
                              'com.apple.corerecents.recentsd', 'Data', 'Library', 'Recents')
        os.makedirs(folder)
        path = os.path.join(folder, 'Recents')
        build(path, **options)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(recents, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc') as shared:
            result = recents.macosRecents.__wrapped__(context)
        return result, [call.args[0] for call in shared.call_args_list + log.call_args_list]

    def test_rows(self):
        path = self.database('a')
        sidecar = path + '-wal'
        with open(sidecar, 'wb'):
            pass
        decoy = os.path.join(os.path.dirname(path), 'OtherRecents')
        build(decoy)
        (headers, rows, located), logged = self.run_artifact([sidecar, decoy, path])
        relative = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 17)
        self.assertEqual(headers[0], ('Last Date (UTC)', 'datetime'))
        details = 'givenName=Lab | plain=text | raw=0001 | none='
        place = 'longitude=-66.5 | latitude=18.25 | handle=01ff | flag=True'
        self.assertEqual(rows, [
            (utc(2023, 11, 14, 22, 23, 20), '2023-11-14 22:23:20.000 | 2023-11-14 22:13:20.123', 'com.apple.mail',
             'Lab Person', 'email', 'second@example.com', 'Second Person', 'me@example.com', 'source one', 2, None, 0,
             '', '', details, 1, relative),
            (utc(2023, 11, 14, 22, 23, 20), '2023-11-14 22:23:20.000 | 2023-11-14 22:13:20.123', 'com.apple.mail',
             'Lab Person', 'phone', '+15555550100', 'First Person', 'me@example.com', 'source one', 2, None, 0,
             '', '', details, 1, relative),
            ('', '2023-11-14 22:13:20.123', 'com.apple.Maps', 'A Place', 'map-location', 'place-id', 'A Place', None,
             None, 1, 10.0, 3, '18.25', '-66.5', place, 2, relative),
            ('', '', 'com.example.none', None, None, None, None, None, None, 0, None, 0, '', '', '', 4, relative)])
        self.assertEqual(located, path)
        self.assertEqual(logged, ['Recents (CoreRecents): 2 dates that are not a number, left out of Dates (UTC), '
                                  '1 last dates that are not a number, Last Date (UTC) left blank'])

    def test_two_users_and_a_database_that_cannot_be_read(self):
        first = self.database('a')
        second = self.database('b')
        broken = self.database('c', with_metadata=False)
        (_, rows, located), logged = self.run_artifact([broken, second, first])
        self.assertEqual([row[-1].split(os.sep)[1] for row in rows], ['a'] * 4 + ['b'] * 4)
        self.assertEqual(located, first + '\n' + second)
        self.assertEqual(logged, ['Recents (CoreRecents): 1 databases that could not be read (OperationalError), '
                                  '4 dates that are not a number, left out of Dates (UTC), '
                                  '2 last dates that are not a number, Last Date (UTC) left blank'])

    def test_the_same_file_under_the_data_volume_view_is_read_once(self):
        path = self.database('a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(path, self.folder.name))
        os.makedirs(os.path.dirname(view))
        with open(path, 'rb') as source, open(view, 'wb') as copy:
            copy.write(source.read())
        other = self.database('b')
        changed = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(other, self.folder.name))
        os.makedirs(os.path.dirname(changed))
        build(changed, with_metadata=True)
        database = sqlite3.connect(changed)
        database.execute('DELETE FROM recents WHERE ROWID > 1')
        database.commit()
        database.close()
        (_, rows, located), logged = self.run_artifact([view, changed, other, path])
        both = os.path.relpath(changed, self.folder.name) + '\n' + os.path.relpath(other, self.folder.name)
        self.assertEqual([row[-1] for row in rows],
                         [both] * 2 + [os.path.relpath(path, self.folder.name)] * 4
                         + [os.path.relpath(other, self.folder.name)] * 2)
        self.assertEqual(located, changed + '\n' + path + '\n' + other)
        self.assertEqual(len(logged), 2)
        self.assertIn('1 byte-identical copy(ies)', logged[0])

    def test_an_empty_database_and_one_that_does_not_open(self):
        empty = self.database('a')
        database = sqlite3.connect(empty)
        database.execute('DELETE FROM recents')
        database.commit()
        database.close()
        closed = self.database('b')
        opener = recents.open_sqlite_db_readonly
        with mock.patch.object(recents, 'open_sqlite_db_readonly', side_effect=lambda p: None if p == closed else opener(p)):
            (_, rows, located), logged = self.run_artifact([closed, empty])
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(logged, ['Recents (CoreRecents): 1 databases that could not be opened'])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
