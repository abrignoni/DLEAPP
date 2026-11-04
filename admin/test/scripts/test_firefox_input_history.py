"""Pin scripts.firefox.input_history on a places database built here (made-up values)."""
import pathlib
import sqlite3
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox  # pylint: disable=wrong-import-position


class InputHistoryTest(unittest.TestCase):
    def test_rows_joined_to_places(self):
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        db.executescript('''
            CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT, title TEXT, last_visit_date INTEGER);
            CREATE TABLE moz_inputhistory (place_id INTEGER NOT NULL, input LONGVARCHAR NOT NULL,
                                           use_count INTEGER, PRIMARY KEY (place_id, input));
            INSERT INTO moz_places VALUES (5, 'http://example.invalid/a', 'A', 1793797638209000);
            INSERT INTO moz_inputhistory VALUES (5, 'ex', 1.9), (9, 'gone', 1);''')
        rows = list(firefox.input_history(db))
        self.assertEqual([row[1:] for row in rows],
                         [('ex', 'http://example.invalid/a', 'A', 1.9, 5), ('gone', None, None, 1, 9)])
        self.assertEqual(rows[0][0].year, 2026)

    def test_no_table_gives_no_rows(self):
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        db.execute('CREATE TABLE moz_places (id INTEGER PRIMARY KEY)')
        self.assertEqual(list(firefox.input_history(db)), [])


if __name__ == '__main__':
    unittest.main()
