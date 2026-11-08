"""Pin chromiumAppCache.read_groups on synthetic Index databases of schema versions 5 and 7.

The tables are created with the column lists of content/browser/appcache/appcache_database.cc at
Chromium 65.0.3325.181 (version 7) and without the two columns its version 7 upgrade adds (version 5).
"""
import datetime
import pathlib
import sqlite3
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts.chromiumAppCache import read_groups  # pylint: disable=wrong-import-position

GROUPS_V5 = 'group_id INTEGER PRIMARY KEY, origin TEXT, manifest_url TEXT, creation_time INTEGER, last_access_time INTEGER'
GROUPS_V7 = GROUPS_V5 + ', last_full_update_check_time INTEGER, first_evictable_error_time INTEGER'
# 2018-04-06 00:00:00 UTC in microseconds since 1601-01-01.
BASE = 13167446400000000


def _db(groups_columns):
    db = sqlite3.connect(':memory:')
    db.execute(f'CREATE TABLE Groups({groups_columns})')
    db.execute('CREATE TABLE Caches(cache_id INTEGER PRIMARY KEY, group_id INTEGER, online_wildcard INTEGER, '
               'update_time INTEGER, cache_size INTEGER)')
    db.execute('CREATE TABLE Entries(cache_id INTEGER, url TEXT, flags INTEGER, response_id INTEGER, '
               'response_size INTEGER)')
    db.execute('INSERT INTO Caches VALUES (10, 1, 0, ?, 30)', (BASE + 1_000_000,))
    db.executemany('INSERT INTO Entries VALUES (10, ?, ?, ?, ?)',
                   [('https://a.test/page', 1, 1, 10), ('https://a.test/app.manifest', 2, 2, 5),
                    ('https://a.test/app.js', 4, 3, 15)])
    return db


class AppCacheTest(unittest.TestCase):
    def test_version_7_reads_every_column(self):
        db = _db(GROUPS_V7)
        db.execute("INSERT INTO Groups VALUES (1, 'https://a.test/', 'https://a.test/app.manifest', ?, ?, ?, 0)",
                   (BASE, BASE + 2_000_000, BASE + 3_000_000))
        (row,) = read_groups(db)
        accessed, created, updated, checked, manifest, origin, masters, count, total, size = row
        self.assertEqual(created, datetime.datetime(2018, 4, 6, tzinfo=datetime.timezone.utc))
        self.assertEqual((updated - created).total_seconds(), 1)
        self.assertEqual((accessed - created).total_seconds(), 2)
        self.assertEqual((checked - created).total_seconds(), 3)
        self.assertEqual((manifest, origin, masters, count, total, size),
                         ('https://a.test/app.manifest', 'https://a.test/', 'https://a.test/page', 3, 30, 30))

    def test_version_5_has_no_full_update_check(self):
        db = _db(GROUPS_V5)
        db.execute("INSERT INTO Groups VALUES (1, 'https://a.test/', 'https://a.test/app.manifest', ?, ?)",
                   (BASE, BASE))
        (row,) = read_groups(db)
        self.assertEqual(row[3], '')
        self.assertEqual(row[7], 3)

    def test_a_database_without_the_tables_gives_none(self):
        self.assertIsNone(read_groups(sqlite3.connect(':memory:')))


if __name__ == '__main__':
    unittest.main()
