"""Pin the Siri Analytics Events artifact (scripts/artifacts/macosSiriAnalytics.py).

The database is built for the test with the columns the artifact reads from SiriAnalytics.db. The macOS 11 schema
has no assistant_id/record_id columns; macOS 14 added them. The values are made up.
"""
import datetime
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosSiriAnalytics as sa
# pylint: enable=wrong-import-position

SCHEMA_11 = '''
CREATE TABLE 'events' ('stream_uid' TEXT, 'delivery_stream' INTEGER DEFAULT 0, 'type' INTEGER,
    'timestamp' INTEGER, 'context_data' BLOB, 'context_data_type' INTEGER, 'date_created' REAL,
    'status' INTEGER DEFAULT 0);
'''
SCHEMA_14 = SCHEMA_11.replace("'status' INTEGER DEFAULT 0);",
                              "'status' INTEGER DEFAULT 0, 'assistant_id' TEXT, 'record_id' TEXT);")

# stream_uid, type, timestamp, context_data, context_data_type, date_created, status, assistant_id, record_id
ROWS = [
    ('A1', 102, 400, b'{"systemBuild":"20B50"}', 2, 1606921632.5, 1, 'AST-1', 'REC-1'),
    ('A1', 901, 500, b'{"connectionType":"MPTCP"}', 2, 1606921643.0, 0, 'AST-1', 'REC-2'),
    ('B2', 4307, 600, None, 0, 1606921750.0, 1, 'AST-1', 'REC-3'),
]


def build(path, rows=None, schema=SCHEMA_11, table=True):
    rows = ROWS if rows is None else rows
    database = sqlite3.connect(path)
    if not table:
        database.execute('CREATE TABLE other (x INTEGER)')
        database.commit()
        database.close()
        return
    database.executescript(schema)
    has_ids = 'assistant_id' in schema
    if has_ids:
        database.executemany(
            "INSERT INTO events (stream_uid, type, timestamp, context_data, context_data_type, date_created, "
            "status, assistant_id, record_id) VALUES (?,?,?,?,?,?,?,?,?)", rows)
    else:
        database.executemany(
            "INSERT INTO events (stream_uid, type, timestamp, context_data, context_data_type, date_created, "
            "status) VALUES (?,?,?,?,?,?,?)", [r[:7] for r in rows])
    database.commit()
    database.close()


class UnixUtcTest(unittest.TestCase):
    def test_unix_utc(self):
        self.assertEqual(sa._unix_utc(0), '')      # pylint: disable=protected-access
        self.assertEqual(sa._unix_utc(None), '')   # pylint: disable=protected-access
        self.assertEqual(sa._unix_utc('x'), '')    # pylint: disable=protected-access
        self.assertEqual(sa._unix_utc(1606921632.5),  # pylint: disable=protected-access
                         datetime.datetime(2020, 12, 2, 15, 7, 12, 500000, tzinfo=datetime.timezone.utc))

    def test_context_text(self):
        self.assertEqual(sa._context_text(None), '')             # pylint: disable=protected-access
        self.assertEqual(sa._context_text(b'{"a":1}'), '{"a":1}')  # pylint: disable=protected-access


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, *top, **kw):
        folder = os.path.join(self.folder.name, *top, 'Library', 'Assistant')
        os.makedirs(folder)
        path = os.path.join(folder, 'SiriAnalytics.db')
        build(path, **kw)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(sa, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'):
            result = sa.macosSiriAnalytics.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows_macos11(self):
        path = self.database('Users', 'a')  # SCHEMA_11: no assistant_id/record_id
        (headers, rows, located), _ = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        utc = datetime.timezone.utc
        self.assertEqual(len(headers), 10)
        self.assertEqual(headers[0], ('Date Created (UTC)', 'datetime'))
        self.assertEqual(rows, [
            (datetime.datetime(2020, 12, 2, 15, 7, 12, 500000, tzinfo=utc), '', 'A1', '', '102', '1', '2',
             '{"systemBuild":"20B50"}', 'a', rel),
            (datetime.datetime(2020, 12, 2, 15, 7, 23, tzinfo=utc), '', 'A1', '', '901', '0', '2',
             '{"connectionType":"MPTCP"}', 'a', rel),
            (datetime.datetime(2020, 12, 2, 15, 9, 10, tzinfo=utc), '', 'B2', '', '4307', '1', '0', '', 'a', rel)])
        self.assertEqual(located, path)

    def test_rows_macos14_carries_the_ids(self):
        path = self.database('Users', 'a', schema=SCHEMA_14)
        (_, rows, _located), _ = self.run_artifact([path])
        # Assistant ID (col 1) and Record ID (col 3) are populated from the macOS 14 columns
        self.assertEqual([(r[1], r[3]) for r in rows], [('AST-1', 'REC-1'), ('AST-1', 'REC-2'), ('AST-1', 'REC-3')])

    def test_two_differing_views_fold(self):
        own = self.database('Users', 'a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(own, self.folder.name))
        os.makedirs(os.path.dirname(view))
        # view differs on the first row (different payload) but holds row B2 identically
        view_rows = [('A1', 102, 400, b'{"systemBuild":"XYZ"}', 2, 1606921632.5, 1, 'AST-1', 'REC-1')] + ROWS[2:]
        build(view, rows=view_rows)
        (_, rows, _located), _ = self.run_artifact([view, own])
        # A1/102 differs between the copies, so it stays two rows
        self.assertEqual(sum(1 for r in rows if (r[2], r[4]) == ('A1', '102')), 2)
        # B2/4307 is identical in both copies, so fold_view_rows collapses it to one row
        self.assertEqual(sum(1 for r in rows if (r[2], r[4]) == ('B2', '4307')), 1)

    def test_identical_views_are_read_once(self):
        own = self.database('Users', 'a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(own, self.folder.name))
        os.makedirs(os.path.dirname(view))
        with open(own, 'rb') as handle:
            copy = handle.read()
        with open(view, 'wb') as handle:
            handle.write(copy)
        (_, rows, located), _ = self.run_artifact([view, own])
        self.assertEqual(len(rows), 3)       # one copy's worth of rows, the byte-identical view skipped
        self.assertNotIn('\n', located)      # located names a single database, not both copies

    def test_a_database_without_the_events_table_is_skipped(self):
        path = self.database('Users', 'a', table=False)
        (_, rows, located), logged = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(logged, [f'Siri Analytics Events: no events table read from {rel}'])

    def test_a_decoy_named_file_is_ignored(self):
        path = self.database('Users', 'a')
        decoy = os.path.join(os.path.dirname(path), 'Other.db')
        build(decoy)
        (_, rows, located), _ = self.run_artifact([decoy, path])
        self.assertEqual(len(rows), 3)  # only SiriAnalytics.db is read
        self.assertNotIn('Other.db', located)

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
