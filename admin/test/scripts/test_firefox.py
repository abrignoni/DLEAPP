"""Firefox regression cases; fixtures are synthetic and contain no corpus data."""

import fnmatch
import hashlib
import json
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox  # pylint: disable=wrong-import-position
from scripts.artifacts import firefoxBrowser  # pylint: disable=wrong-import-position


class FirefoxTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)

    def places(self):
        self.db.executescript('''
            CREATE TABLE moz_places(id INTEGER PRIMARY KEY, url TEXT, title TEXT);
            INSERT INTO moz_places VALUES(1, 'https://example.test/a', '<Title>');
            INSERT INTO moz_places VALUES(2, 'https://example.test/b', 'Second');
            CREATE TABLE moz_historyvisits(id INTEGER, place_id INTEGER,
                visit_date INTEGER, visit_type INTEGER, from_visit INTEGER);
            INSERT INTO moz_historyvisits VALUES(10, 1, 1704067200123456, 2, 0);
            INSERT INTO moz_historyvisits VALUES(11, 2, 1704067201123456, 1, 10);
            INSERT INTO moz_historyvisits VALUES(12, 999, 1704067202123456, 999, 88);
        ''')

    def test_microseconds_and_invalid_timestamps(self):
        self.assertEqual(firefox.timestamp(1704067200123456),
                         datetime(2024, 1, 1, microsecond=123456, tzinfo=timezone.utc))
        for value in (None, 0, '', 'bad', 10**40, True, float('nan')):
            self.assertEqual(firefox.timestamp(value), '')

    def test_visits_keep_orphans_and_unknown_transitions(self):
        self.places()
        rows = list(firefox.visits(self.db))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1][-1], 'https://example.test/a')
        self.assertEqual(rows[2][3], None)
        self.assertEqual(rows[2][6], 'Unknown')
        self.assertIsNone(rows[0][7])  # old schema: no source field

    def annotations(self):
        self.places()
        self.db.executescript('''
            CREATE TABLE moz_anno_attributes(id INTEGER, name TEXT);
            INSERT INTO moz_anno_attributes VALUES(1, 'downloads/destinationFileURI');
            INSERT INTO moz_anno_attributes VALUES(2, 'downloads/metaData');
            CREATE TABLE moz_annos(id INTEGER, place_id INTEGER, anno_attribute_id INTEGER,
                content TEXT, dateAdded INTEGER, lastModified INTEGER);
        ''')
        for identifier, place, attr, value in (
                (1, 1, 1, 'file:///Downloads/sample.zip'),
                (2, 1, 2, json.dumps({'state': 1, 'endTime': 1704067200123, 'fileSize': 42})),
                (3, 2, 1, 'file:///Downloads/other.zip'),
                (4, 2, 2, '{bad json')):
            self.db.execute('INSERT INTO moz_annos VALUES(?,?,?,?,?,?)',
                            (identifier, place, attr, value, 1704067200222000, 1704067200333000))

    def test_download_annotations_not_multiplied_by_visits(self):
        self.annotations()
        self.db.execute('INSERT INTO moz_historyvisits VALUES(13, 1, 1704067203123456, 7, 0)')
        rows = list(firefox.downloads(self.db))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], datetime(2024, 1, 1, microsecond=123000, tzinfo=timezone.utc))
        self.assertEqual(rows[0][7:9], ('FINISHED', 42))
        self.assertEqual(rows[1][5], 'file:///Downloads/other.zip')
        self.assertEqual(rows[1][-2:], ('Invalid metadata JSON', '{bad json'))

    def test_download_missing_metadata_and_nonobject_json(self):
        self.annotations()
        self.db.execute('DELETE FROM moz_annos WHERE id=2')
        self.db.execute("UPDATE moz_annos SET content='[]' WHERE id=4")
        rows = list(firefox.downloads(self.db))
        self.assertEqual(rows[0][-2], 'No metadata annotation')
        self.assertEqual(rows[1][-2], 'Invalid metadata JSON')

    def test_cookie_schema_expiry_units(self):
        self.db.executescript('''CREATE TABLE moz_cookies(id INTEGER, lastAccessed INTEGER,
            creationTime INTEGER, expiry INTEGER, host TEXT, name TEXT, value TEXT);
            INSERT INTO moz_cookies VALUES(1,1704067200123456,1704067200000000,
                1704153600,'.example.test','name','value'); PRAGMA user_version=15;''')
        old = list(firefox.cookies(self.db))[0]
        self.assertEqual(old[3], datetime(2024, 1, 2, tzinfo=timezone.utc))
        self.assertEqual(old[2], '')
        self.db.executescript('UPDATE moz_cookies SET expiry=expiry*1000; PRAGMA user_version=16;')
        self.assertEqual(list(firefox.cookies(self.db))[0], old)
        self.db.executescript('ALTER TABLE moz_cookies ADD updateTime INTEGER;'
                             'UPDATE moz_cookies SET updateTime=1704067201000000;'
                             'PRAGMA user_version=17;')
        self.assertEqual(list(firefox.cookies(self.db))[0][2],
                         datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc))

    def test_bookmark_hierarchy_keeps_duplicate_urls(self):
        self.places()
        self.db.executescript('''CREATE TABLE moz_bookmarks(id INTEGER, type INTEGER, fk INTEGER,
            parent INTEGER, position INTEGER, title TEXT, dateAdded INTEGER, lastModified INTEGER,
            guid TEXT);
            INSERT INTO moz_bookmarks VALUES(1,2,NULL,0,0,'Root',0,0,'root');
            INSERT INTO moz_bookmarks VALUES(2,2,NULL,1,0,'Folder',0,0,'folder');
            INSERT INTO moz_bookmarks VALUES(3,1,1,2,0,'One',1704067200000000,0,'one');
            INSERT INTO moz_bookmarks VALUES(4,1,1,1,1,'Two',1704067200000000,0,'two');
            INSERT INTO moz_bookmarks VALUES(5,3,NULL,1,2,NULL,0,0,'separator');''')
        rows = list(firefox.bookmarks(self.db))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][6], 'Root / Folder')
        self.assertEqual(rows[1][6], 'Root')

    def test_folder_cycles_and_missing_parents(self):
        self.assertIn('[cycle: 1]', firefox.folder_path(
            {1: {'title': 'Loop', 'guid': 'loop', 'parent': 1}}, 1))
        self.assertEqual(firefox.folder_path({}, 8), '[missing: 8]')

    def test_form_history_aggregates_sources_without_duplicate_rows(self):
        self.db.executescript('''CREATE TABLE moz_formhistory(id INTEGER, guid TEXT,
            fieldname TEXT, value TEXT, timesUsed INTEGER, firstUsed INTEGER, lastUsed INTEGER);
            INSERT INTO moz_formhistory VALUES(1,'g','q','search',3,1704067200000000,1704067201000000);
            CREATE TABLE moz_sources(id INTEGER, source TEXT);
            INSERT INTO moz_sources VALUES(1,'https://a.test'),(2,'https://b.test');
            CREATE TABLE moz_history_to_sources(history_id INTEGER,source_id INTEGER);
            INSERT INTO moz_history_to_sources VALUES(1,1),(1,2);''')
        rows = list(firefox.form_history(self.db))
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0][-1]), ['https://a.test', 'https://b.test'])
        self.db.executescript('DROP TABLE moz_sources; DROP TABLE moz_history_to_sources;')
        self.assertEqual(list(firefox.form_history(self.db))[0][-1], '[]')

    def test_interactions_millisecond_dates_and_raw_metrics(self):
        self.places()
        self.assertEqual(list(firefox.interactions(self.db)), [])
        self.db.executescript('''CREATE TABLE moz_places_metadata(id INTEGER, place_id INTEGER,
            referrer_place_id INTEGER, created_at INTEGER, updated_at INTEGER,total_view_time INTEGER);
            INSERT INTO moz_places_metadata VALUES(5,2,1,1704067200123,1704067200456,333);''')
        row = list(firefox.interactions(self.db))[0]
        self.assertEqual(row[0].microsecond, 123000)
        self.assertEqual(row[1].microsecond, 456000)
        self.assertEqual(row[6:9], ('https://example.test/a', 333, None))

    def test_favicons_links_then_unlinked_root_icons(self):
        """Linked icons give one row per link; an unlinked icon gets its own row, page blank."""
        self.db.executescript('''
            CREATE TABLE moz_pages_w_icons(id INTEGER PRIMARY KEY, page_url TEXT, page_url_hash INTEGER);
            CREATE TABLE moz_icons(id INTEGER PRIMARY KEY, icon_url TEXT, fixed_icon_url_hash INTEGER,
                width INTEGER, root INTEGER, color INTEGER, expire_ms INTEGER, flags INTEGER, data BLOB);
            CREATE TABLE moz_icons_to_pages(page_id INTEGER, icon_id INTEGER, expire_ms INTEGER);
            INSERT INTO moz_pages_w_icons VALUES(1, 'https://example.test/page', 0);
            INSERT INTO moz_icons VALUES(7, 'https://cdn.example.test/icon.png', 0, 32, 0, NULL,
                1704067200123, 1, X'00010203');
            INSERT INTO moz_icons VALUES(8, 'https://example.test/favicon.ico', 0, 65535, 1, NULL, 0, 0, X'AA');
            INSERT INTO moz_icons_to_pages VALUES(1, 7, 1704153600000);
        ''')
        linked, root = list(firefox.favicons(self.db))
        self.assertEqual(linked[0], datetime(2024, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc))
        self.assertEqual(linked[1], datetime(2024, 1, 2, tzinfo=timezone.utc))
        self.assertEqual(linked[2:], ('https://example.test/page', 'https://cdn.example.test/icon.png',
                                      32, 0, 1, 4, 7))
        self.assertEqual(root, ('', '', '', 'https://example.test/favicon.ico', 65535, 1, 0, 1, 8))

    def test_snappy_raw_follows_the_format_description(self):
        """The spec's own example, a long literal, a 2-byte offset copy, and malformed streams."""
        self.assertEqual(firefox.snappy_raw_uncompress(b'\x07\x08xab\x01\x02'), b'xababab')
        long_literal = bytes(range(70))
        self.assertEqual(firefox.snappy_raw_uncompress(b'\x46\xf0\x45' + long_literal), long_literal)
        self.assertEqual(firefox.snappy_raw_uncompress(b'\x09\x08abc\x16\x03\x00'), b'abcabcabc')
        for bad in (b'\x07\x08xab\x01\x00',   # offset 0
                    b'\x08\x08xab\x01\x02',   # output shorter than declared
                    b'\x07\x08xa',              # truncated literal
                    b'\x80'):                    # truncated preamble
            with self.assertRaises(ValueError):
                firefox.snappy_raw_uncompress(bad)
        with self.assertRaises(TypeError):   # an integer is never read as a length to allocate
            firefox.snappy_raw_uncompress(4096)

    def test_local_storage_value_types(self):
        """Conversion 1 is UTF-8, 0 is raw UTF-16 code units; compression 1 is raw Snappy."""
        self.assertEqual(firefox.local_storage_value('héllo'.encode('utf-8'), 1, 0), 'héllo')
        self.assertEqual(firefox.local_storage_value(b'a\x00\x00\xd8', 0, 0), 'a\ufffd')
        self.assertEqual(firefox.local_storage_value(b'\x07\x08xab\x01\x02', 1, 1), 'xababab')
        for conversion, compression in ((2, 0), (1, 2)):
            with self.assertRaises(ValueError):
                firefox.local_storage_value(b'x', conversion, compression)
        with self.assertRaises(TypeError):
            firefox.local_storage_value(4096, 1, 0)

    def test_local_storage_reader_origin_profile_and_undecodable(self):
        """Origin comes from the database table, profile from the folder above storage."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store = (root/'Users'/'tester'/'storage'/'Library'/'Application Support'/'Firefox'/'Profiles'/
                     'ab12.default-release'/'storage'/'default'/'https+++example.test'/'ls'/'data.sqlite')
            store.parent.mkdir(parents=True)
            db = sqlite3.connect(store)
            db.executescript('''CREATE TABLE database(origin TEXT, usage INTEGER, last_vacuum_time INTEGER,
                    last_analyze_time INTEGER, last_vacuum_size INTEGER);
                CREATE TABLE data(key TEXT PRIMARY KEY, utf16_length INTEGER, conversion_type INTEGER,
                    compression_type INTEGER, last_access_time INTEGER, value BLOB);
                INSERT INTO database VALUES('https://example.test', 0, 0, 0, 0);''')
            db.execute('INSERT INTO data VALUES(?,?,?,?,?,?)', ('plain', 5, 1, 0, 0, b'hello'))
            db.execute('INSERT INTO data VALUES(?,?,?,?,?,?)', ('packed', 7, 1, 1, 0, b'\x07\x08xab\x01\x02'))
            db.execute('INSERT INTO data VALUES(?,?,?,?,?,?)', ('broken', 3, 1, 1, 0, b'\x03\x01\x00'))
            db.commit()
            db.close()

            class Context:
                def get_files_found(self):
                    return [str(store)]

                def get_relative_path(self, path):
                    return str(pathlib.Path(path).relative_to(root))
            with patch.object(firefox, 'logfunc') as logged:
                rows, _ = firefox.read_local_storage(Context(), 'Firefox Local Storage')
            by_key = {row[1]: row for row in rows}
            self.assertEqual(by_key['plain'][0], 'https://example.test')
            self.assertEqual(by_key['plain'][2], 'hello')
            self.assertEqual(by_key['packed'][2], 'xababab')
            self.assertEqual(by_key['broken'][2], '')
            self.assertEqual((by_key['plain'][7], by_key['plain'][8]), ('ab12.default-release', 'tester'))
            self.assertTrue(all(len(row) == 9 for row in rows))
            self.assertTrue(any('1 value(s) could not be decoded' in str(call) for call in logged.call_args_list))

    def test_patterns_match_profiles_and_sidecars_once(self):
        for artifact in firefoxBrowser.__artifacts_v2__.values():
            filename = artifact['paths'][0].split('Profiles/*/', 1)[1].rstrip('*').replace('*', 'https+++example.test')
            for prefix in ('root/Library/Application Support/Firefox/Profiles/p/',
                           'root/Users/A/AppData/Roaming/Mozilla/Firefox/Profiles/p/',
                           'root/home/a/.mozilla/firefox/p/'):
                for suffix in ('', '-wal', '-shm'):
                    self.assertEqual(sum(fnmatch.fnmatchcase(prefix+filename+suffix, pattern)
                                         for pattern in artifact['paths']), 1)

    def test_readonly_wal_and_profile_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root/'places.sqlite'
            writer = sqlite3.connect(path)
            try:
                writer.execute('PRAGMA journal_mode=WAL')
                writer.executescript('''CREATE TABLE moz_places(id INTEGER, url TEXT, title TEXT);
                    CREATE TABLE moz_historyvisits(id INTEGER,place_id INTEGER,visit_date INTEGER,
                        visit_type INTEGER,from_visit INTEGER);
                    INSERT INTO moz_places VALUES(1,'https://wal.test','WAL');
                    INSERT INTO moz_historyvisits VALUES(1,1,1704067200000000,1,0);''')
                paths = [path, pathlib.Path(str(path)+'-wal')]
                before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
                class Context:
                    @staticmethod
                    def get_files_found():
                        return paths + [path]

                    @staticmethod
                    def get_relative_path(_path):
                        return 'Library/Application Support/Firefox/Profiles/evidence/places.sqlite'

                rows, source = firefox.read_artifact(Context, 'places.sqlite', firefox.visits, 'Test')
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0][-2:], ('evidence', ''))
                self.assertNotIn('places.sqlite', repr(rows))
                self.assertEqual(source, str(path))
                self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths])
            finally:
                writer.close()

    def test_bad_store_does_not_stop_other_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            bad = root/'bad'/'places.sqlite'
            bad.parent.mkdir()
            bad.write_bytes(b'not sqlite')
            good = root/'good'/'places.sqlite'
            good.parent.mkdir()
            self.places()
            with sqlite3.connect(good) as target:
                self.db.backup(target)
            target.close()
            class Context:
                @staticmethod
                def get_files_found():
                    return [bad, good]

                @staticmethod
                def get_relative_path(path):
                    return str(pathlib.Path(path).relative_to(root))

            with patch('scripts.ilapfuncs.logfunc'), patch('scripts.firefox.logfunc') as log:
                rows, source = firefox.read_artifact(Context, 'places.sqlite', firefox.visits, 'Test')
                self.assertEqual(len(rows), 3)
                self.assertEqual(source, str(good))
                self.assertTrue(log.called)

    def test_identical_profiles_preserved_but_firmlink_copy_deduplicated(self):
        self.places()
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            suffix = 'Users/A/Library/Application Support/Firefox/Profiles/one/places.sqlite'
            paths = [root/suffix, root/('System/Volumes/Data/'+suffix),
                     root/suffix.replace('/one/', '/two/')]
            for path in paths:
                path.parent.mkdir(parents=True)
            with sqlite3.connect(paths[0]) as target:
                self.db.backup(target)
            target.close()
            for path in paths[1:]:
                shutil.copy2(paths[0], path)

            class Context:
                @staticmethod
                def get_files_found():
                    return paths

                @staticmethod
                def get_relative_path(path):
                    return str(pathlib.Path(path).relative_to(root))

            with patch('scripts.macos_plists.logfunc'):
                rows, _ = firefox.read_artifact(Context, 'places.sqlite', firefox.visits, 'Test')
            self.assertEqual(len(rows), 6)
            self.assertEqual({row[-2] for row in rows}, {'one', 'two'})
            self.assertEqual({row[-1] for row in rows}, {'A'})


if __name__ == '__main__':
    unittest.main()
