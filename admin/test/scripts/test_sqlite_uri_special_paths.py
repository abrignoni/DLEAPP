"""SQLite URIs built from a path keep working when the path holds '#' or '?'.

A URI such as f"file:{path}?mode=ro" ends the path at the first '#' (fragment) or
'?' (query). For a folder named "case #12" SQLite then opens "case " instead: with
the query cut off it creates that file, finds no tables, and the artifact reports
nothing. Each reader below must percent-quote the path, so it reads the synthetic
database it was given and leaves no stray file next to the folder.
"""
# pylint: disable=protected-access

import os
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import signal_desktop  # pylint: disable=wrong-import-position
from scripts import threema_desktop  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsSearchDb  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsThumbcache  # pylint: disable=wrong-import-position

STORE = 'SystemIndex_1_PropertyStore'
PROPERTIES = (
    (1, 'System.ItemNameDisplay', 'synthetic.txt'),
    (2, 'System.ItemPathDisplay', 'C:\\Synthetic\\synthetic.txt'),
    (3, 'System.ThumbnailCacheId', 0x1122334455667788),
)


def _write_windows_db(path):
    with sqlite3.connect(path) as db:
        db.execute(f'CREATE TABLE "{STORE}_Metadata" (Id INTEGER, Name TEXT)')
        db.execute(f'CREATE TABLE "{STORE}" (WorkId INTEGER, ColumnId INTEGER, Value)')
        for column_id, name, value in PROPERTIES:
            db.execute(f'INSERT INTO "{STORE}_Metadata" VALUES (?, ?)', (column_id, name))
            db.execute(f'INSERT INTO "{STORE}" VALUES (1, ?, ?)', (column_id, value))
    db.close()


def _write_plain_db(path):
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE synthetic (value TEXT)')
        db.execute("INSERT INTO synthetic VALUES ('row')")
    db.close()


class SpecialCharacterPathTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        # "case " is where an unquoted URI for "case #1?x/..." lands.
        self.folder = os.path.join(self.root, 'case #1?x')
        os.makedirs(self.folder)
        self.stray = os.path.join(self.root, 'case ')

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def assert_no_stray(self):
        self.assertFalse(os.path.exists(self.stray), 'the URI was cut at # or ?')

    def test_windows_search_db_reads_rows(self):
        path = os.path.join(self.folder, 'Windows.db')
        _write_windows_db(path)
        rows = windowsSearchDb._read_windows_db(path)
        self.assertEqual(len(rows), 1)
        self.assert_no_stray()

    def test_thumbcache_db_map_reads_rows(self):
        path = os.path.join(self.folder, 'Windows.db')
        _write_windows_db(path)
        mapping = windowsThumbcache._db_map(path)
        self.assertEqual(mapping, {0x1122334455667788: ('C:\\Synthetic\\synthetic.txt', 'synthetic.txt')})
        self.assert_no_stray()

    def _rows(self, connection):
        try:
            return connection.execute('SELECT value FROM synthetic').fetchall()
        finally:
            connection.close()

    def test_signal_desktop_opens_plaintext_db(self):
        path = os.path.join(self.folder, 'db.sqlite')
        _write_plain_db(path)
        connection, _ = signal_desktop.open_database([path])
        self.assertIsNotNone(connection)
        self.assertEqual(self._rows(connection), [('row',)])
        self.assert_no_stray()

    def test_signal_desktop_opens_cached_copy(self):
        source = os.path.join(self.folder, 'db.sqlite')
        cached = os.path.join(self.folder, 'decrypted.db')
        _write_plain_db(cached)
        with open(source, 'wb') as handle:
            handle.write(os.urandom(4096))
        real = os.path.realpath(source)
        signal_desktop._decrypted_cache[real] = cached
        try:
            connection, _ = signal_desktop.open_database([source])
        finally:
            signal_desktop._decrypted_cache.pop(real, None)
        self.assertIsNotNone(connection)
        self.assertEqual(self._rows(connection), [('row',)])
        self.assert_no_stray()

    def test_threema_desktop_opens_plaintext_db(self):
        path = os.path.join(self.folder, 'threema.sqlite')
        _write_plain_db(path)
        connection, _ = threema_desktop.open_database(path, [path])
        self.assertIsNotNone(connection)
        self.assertEqual(self._rows(connection), [('row',)])
        self.assert_no_stray()


if __name__ == '__main__':
    unittest.main()
