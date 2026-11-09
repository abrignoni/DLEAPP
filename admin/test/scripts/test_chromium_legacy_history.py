"""Pin the readers of chromiumLegacyHistory on synthetic databases built with Chromium's own schemas.

Media History tables: chrome/browser/media/history/*_table.cc at chromium
afa7a1c77c10c66e16e0e097dfb62a8b01915f52 (91.0.4472.0). Archived History and History Index:
chrome/browser/history/ at 9dae4a37862398cd103d2d0b3d25ce1d540eac0b (29.0.1547.0). The History
Index pages table is FTS3 with the ICU tokenizer, so the test builds its content table directly,
as FTS3 lays it out.
"""
import datetime
import pathlib
import sqlite3
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts.chromiumLegacyHistory import (_IndexNames, read_archived_visits,
                                                     read_history_index, read_playbacks,
                                                     read_sessions, windows_seconds)

UTC = datetime.timezone.utc
# 2026-11-09 00:13:16 UTC as whole seconds and as microseconds since 1601-01-01.
SECONDS = 13438656796
MICROS = SECONDS * 1_000_000


def _media_db():
    db = sqlite3.connect(':memory:')
    db.executescript('''
        CREATE TABLE origin(id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT NOT NULL UNIQUE,
            last_updated_time_s INTEGER, has_media_engagement INTEGER, media_engagement_visits INTEGER,
            media_engagement_playbacks INTEGER, media_engagement_last_playback_time REAL,
            media_engagement_has_high_score INTEGER, aggregate_watchtime_audio_video_s INTEGER DEFAULT 0);
        CREATE TABLE playback(id INTEGER PRIMARY KEY AUTOINCREMENT, origin_id INTEGER NOT NULL, url TEXT,
            watch_time_s INTEGER, has_video INTEGER, has_audio INTEGER, last_updated_time_s BIGINT NOT NULL);
        CREATE TABLE playbackSession(id INTEGER PRIMARY KEY AUTOINCREMENT, origin_id INTEGER NOT NULL,
            url TEXT NOT NULL UNIQUE, duration_ms INTEGER, position_ms INTEGER,
            last_updated_time_s BIGINT NOT NULL, title TEXT, artist TEXT, album TEXT, source_title TEXT);
        CREATE TABLE sessionImage(session_id INTEGER NOT NULL, image_id INTEGER NOT NULL, width INTEGER,
            height INTEGER);
        CREATE TABLE mediaImage(id INTEGER PRIMARY KEY AUTOINCREMENT, playback_origin_id INTEGER NOT NULL,
            url TEXT NOT NULL, mime_type TEXT);
    ''')
    db.execute("INSERT INTO origin (origin, last_updated_time_s) VALUES ('https://a.test', ?)", (SECONDS,))
    db.executemany('INSERT INTO playback (origin_id, url, watch_time_s, has_video, has_audio, '
                   'last_updated_time_s) VALUES (1, ?, ?, ?, ?, ?)',
                   [('https://a.test/v', 15, 1, 1, SECONDS + 5), ('https://a.test/a', 20, 0, 1, SECONDS)])
    db.execute("INSERT INTO playbackSession (origin_id, url, duration_ms, position_ms, last_updated_time_s, "
               "title, artist, album, source_title) VALUES (1, 'https://a.test/v', 40008, 13477, ?, "
               "'T', 'Ar', 'Al', 'a.test')", (SECONDS,))
    db.executemany("INSERT INTO mediaImage (playback_origin_id, url, mime_type) VALUES (1, ?, 'image/png')",
                   [('https://a.test/1.png',), ('https://a.test/2.png',)])
    db.executemany('INSERT INTO sessionImage VALUES (1, ?, ?, ?)', [(1, 96, 96), (2, 0, 0)])
    return db


class MediaHistoryTest(unittest.TestCase):
    def test_seconds_since_1601(self):
        self.assertEqual(windows_seconds(SECONDS), datetime.datetime(2026, 11, 9, 0, 13, 16, tzinfo=UTC))
        self.assertEqual(windows_seconds(0), '')
        self.assertEqual(windows_seconds(None), '')

    def test_playbacks_are_one_row_each_in_time_order(self):
        rows = read_playbacks(_media_db())
        self.assertEqual([r[1] for r in rows], ['https://a.test/a', 'https://a.test/v'])
        self.assertEqual(rows[0][2:6], (20, 'No', 'Yes', 'https://a.test'))
        self.assertEqual(rows[1][0], datetime.datetime(2026, 11, 9, 0, 13, 21, tzinfo=UTC))

    def test_session_values_and_artwork(self):
        (row,) = read_sessions(_media_db())
        self.assertEqual(row[1:8], ('https://a.test/v', 'T', 'Ar', 'Al', 'a.test', 40.008, 13.477))
        self.assertEqual(row[8], 'https://a.test/1.png (96x96)\nhttps://a.test/2.png')
        self.assertEqual(row[9], 'https://a.test')

    def test_a_database_without_the_tables_gives_none(self):
        db = sqlite3.connect(':memory:')
        self.assertIsNone(read_playbacks(db))
        self.assertIsNone(read_sessions(db))


class ArchivedHistoryTest(unittest.TestCase):
    def test_visits_join_their_url_row(self):
        db = sqlite3.connect(':memory:')
        db.executescript('''
            CREATE TABLE urls(id INTEGER PRIMARY KEY, url LONGVARCHAR, title LONGVARCHAR,
                visit_count INTEGER DEFAULT 0 NOT NULL, typed_count INTEGER DEFAULT 0 NOT NULL,
                last_visit_time INTEGER NOT NULL, hidden INTEGER DEFAULT 0 NOT NULL,
                favicon_id INTEGER DEFAULT 0 NOT NULL);
            CREATE TABLE visits(id INTEGER PRIMARY KEY, url INTEGER NOT NULL, visit_time INTEGER NOT NULL,
                from_visit INTEGER, transition INTEGER DEFAULT 0 NOT NULL, segment_id INTEGER,
                is_indexed BOOLEAN, visit_duration INTEGER DEFAULT 0 NOT NULL);
            CREATE TABLE visit_source(id INTEGER PRIMARY KEY, source INTEGER NOT NULL);
        ''')
        db.execute("INSERT INTO urls VALUES (1, 'https://a.test/', 'A', 2, 1, ?, 0, 0)", (MICROS + 10_000_000,))
        db.execute('INSERT INTO visits VALUES (1, 1, ?, 0, 805306374, 0, 1, 2500000)', (MICROS,))
        db.execute('INSERT INTO visits VALUES (2, 1, ?, 0, 805306369, 0, 1, 0)', (MICROS + 1,))
        db.execute('INSERT INTO visit_source VALUES (2, 0)')
        first, second = read_archived_visits(db)
        self.assertEqual(first[0], datetime.datetime(2026, 11, 9, 0, 13, 16, tzinfo=UTC))
        self.assertEqual(first[1], datetime.datetime(2026, 11, 9, 0, 13, 26, tzinfo=UTC))
        self.assertEqual(first[2:8], ('https://a.test/', 'A', 'AUTO_TOPLEVEL (6)', 'CHAIN_START, CHAIN_END',
                                      'BROWSED (no visit_source row)', 2.5))
        self.assertEqual(first[8:], (2, 1, 1))
        self.assertEqual(second[4], 'TYPED (1)')
        self.assertEqual(second[6], 'SYNCED (0)')

    def test_no_visits_table_gives_none(self):
        self.assertIsNone(read_archived_visits(sqlite3.connect(':memory:')))


class HistoryIndexTest(unittest.TestCase):
    def test_content_table_joined_to_info(self):
        db = sqlite3.connect(':memory:')
        db.execute("CREATE TABLE 'pages_content'(docid INTEGER PRIMARY KEY, 'c0url', 'c1title', 'c2body')")
        db.execute('CREATE TABLE info(time INTEGER NOT NULL)')
        db.execute("INSERT INTO pages_content VALUES (2, 'https://a.test/b', 'B', 'second body')")
        db.execute("INSERT INTO pages_content VALUES (1, 'https://a.test/a', 'A', 'first body')")
        db.execute('INSERT INTO info (rowid, time) VALUES (1, ?)', (MICROS,))
        db.execute('INSERT INTO info (rowid, time) VALUES (2, ?)', (MICROS + 1_000_000,))
        rows = read_history_index(db)
        self.assertEqual([r[1:] for r in rows], [('https://a.test/a', 'A', 'first body', 1),
                                                 ('https://a.test/b', 'B', 'second body', 2)])
        self.assertEqual(rows[0][0], datetime.datetime(2026, 11, 9, 0, 13, 16, tzinfo=UTC))

    def test_no_content_table_gives_none(self):
        self.assertIsNone(read_history_index(sqlite3.connect(':memory:')))

    def test_index_file_names(self):
        names = _IndexNames()
        self.assertIn('History Index 2013-06', names)
        self.assertNotIn('History Index 2013-06-journal', names)
        self.assertNotIn('History', names)
        self.assertNotIn('Archived History', names)


if __name__ == '__main__':
    unittest.main()
