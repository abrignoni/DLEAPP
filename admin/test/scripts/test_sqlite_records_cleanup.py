"""get_sqlite_db_records closes its connection before returning the rows."""
import contextlib
import gc
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
from scripts import ilapfuncs  # pylint: disable=wrong-import-position


class RecordsCleanupTests(unittest.TestCase):
    """Connections are closed without waiting for garbage collection."""
    def setUp(self):
        # Cleanups run last in, first out, so the folder goes after the connections.
        temp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(temp.cleanup)
        self.path = str(pathlib.Path(temp.name) / 'synthetic.sqlite')
        with contextlib.closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE sample (value INTEGER)')
            db.executemany('INSERT INTO sample VALUES (?)', [(1,), (2,)])
            db.commit()
        self.opened = []
        real_open = ilapfuncs.open_sqlite_db_readonly
        def tracked(path):
            db = real_open(path)
            if db is not None:
                self.opened.append(db)
            return db
        patch = mock.patch.object(ilapfuncs, 'open_sqlite_db_readonly', tracked)
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(self.cleanup_connections)

    def records(self, query, attach_query=None):
        """Read the synthetic database through the public helper."""
        return ilapfuncs.get_sqlite_db_records(self.path, query, attach_query)

    def cleanup_connections(self):
        """Release captured connections even when a regression assertion fails."""
        for db in self.opened:
            db.close()

    def assert_closed(self):
        """A closed connection rejects further SQL."""
        self.assertTrue(self.opened)
        for db in self.opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute('SELECT 1')

    def test_rows_keep_named_access_and_connection_closes(self):
        """The list of rows outlives the connection."""
        rows = self.records('SELECT value FROM sample ORDER BY value')
        self.assertIsInstance(rows, list)
        self.assertEqual([r['value'] for r in rows], [1, 2])
        self.assert_closed()

    def test_empty_query_closes(self):
        """An empty result also releases the connection."""
        self.assertEqual(self.records('SELECT * FROM sample WHERE 0'), [])
        self.assert_closed()

    def test_failed_query_closes(self):
        """An invalid query is logged and its connection is closed."""
        with mock.patch.object(ilapfuncs, 'logfunc') as log:
            self.assertEqual(self.records('SELECT * FROM absent'), [])
            self.assertTrue(log.called)
        self.assert_closed()

    def test_failed_attach_closes(self):
        """An invalid attachment releases the connection."""
        with mock.patch.object(ilapfuncs, 'logfunc'):
            self.assertEqual(self.records('SELECT 1', 'INVALID SQL'), [])
        self.assert_closed()

    def test_logging_failure_still_closes(self):
        """Even an exception from logging must release the database."""
        with mock.patch.object(ilapfuncs, 'logfunc', side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):
                self.records('INVALID SQL')
        self.assert_closed()

    def test_repeated_reads_do_not_depend_on_garbage_collection(self):
        """Repeated queries release handles with the collector disabled."""
        enabled = gc.isenabled()
        gc.disable()
        try:
            for _ in range(1000):
                self.assertEqual(len(self.records('SELECT * FROM sample')), 2)
            self.assert_closed()
        finally:
            if enabled:
                gc.enable()


if __name__ == '__main__':
    unittest.main()
