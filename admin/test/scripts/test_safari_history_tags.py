"""Pin how the Safari History artifacts read History.db's tag tables and a store held twice.

history_tags holds one row per tag and history_items_to_tags links a tag to a history item.
Safari History shows an item's tags on each of its visits, and Safari History Tags lists one
row per link plus one row for a tag no link names. A logical extraction of a Mac can hold
one user's History.db under Users/ and again under System/Volumes/Data/Users/: a record both
copies hold is reported once, and a record only one copy holds is still reported. A Safari
profile keeps its own History.db in a Profiles/<UUID>/ folder, which the declared paths match
and which is read as a store of its own.

Every value here is written for the test. The two tag tables use the CREATE TABLE text
Safari wrote on the tested images; the expected rows are written out, never read back from
the module.
"""
import datetime
import fnmatch
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import safaribrowsing  # pylint: disable=wrong-import-position

USER = 'Users/someone/Library/Safari/History.db'
DATA_VIEW = 'System/Volumes/Data/Users/someone/Library/Safari/History.db'
OTHER_USER = 'Users/another/Library/Safari/History.db'
# Where Safari 27.0.1 on macOS 27.0.1 created a profile's database.
PROFILE = ('Users/someone/Library/Containers/com.apple.Safari/Data/Library/Safari/Profiles/'
           'C68764FA-9571-420D-A681-C0FF8270B269/History.db')
PROFILE_DATA_VIEW = 'System/Volumes/Data/' + PROFILE

BASE_TABLES = (
    'CREATE TABLE history_items (id INTEGER PRIMARY KEY, url TEXT NOT NULL UNIQUE, '
    'domain_expansion TEXT NULL, visit_count INTEGER NOT NULL)',
    'CREATE TABLE history_visits (id INTEGER PRIMARY KEY, history_item INTEGER NOT NULL, '
    'visit_time REAL NOT NULL, title TEXT NULL, load_successful BOOLEAN NOT NULL DEFAULT 1, '
    'http_non_get BOOLEAN NOT NULL DEFAULT 0, synthesized BOOLEAN NOT NULL DEFAULT 0, '
    'origin INTEGER NOT NULL DEFAULT 0)',
)
TAG_TABLES = (
    'CREATE TABLE history_tags (id INTEGER PRIMARY KEY,type INTEGER NOT NULL,level INTEGER NOT NULL,'
    'identifier TEXT NOT NULL,title TEXT NOT NULL,modification_timestamp REAL NOT NULL,'
    'item_count INTEGER NOT NULL DEFAULT 0)',
    'CREATE TABLE history_items_to_tags (history_item INTEGER NOT NULL,tag_id INTEGER NOT NULL,'
    'timestamp REAL NOT NULL,FOREIGN KEY(tag_id) REFERENCES history_tags(id) ON DELETE CASCADE,'
    'FOREIGN KEY(history_item) REFERENCES history_items(id) ON DELETE CASCADE,'
    'UNIQUE(history_item, tag_id) ON CONFLICT REPLACE)',
)

ITEMS = ((1, 'https://one.example/', 'one', 2), (2, 'https://two.example/', 'two', 1),
         (3, 'https://three.example/', 'three', 1))
# 700000000 seconds after 2001-01-01 is 2023-03-08 20:26:40 UTC.
VISITS = ((1, 1, 700000000.0, 'One'), (2, 1, 700000100.0, 'One again'),
          (3, 2, 700000200.0, 'Two'), (4, 3, 700000300.0, 'Three'))
# The stored item count of the first tag is higher than its links, and the third tag has a
# stored count above zero and no link at all.
TAGS = ((1, 1, 200, 'Q1001', 'Alpha', 700000205.5, 3), (2, 1, 200, 'Q1002', 'Beta', 700000110.0, 1),
        (3, 1, 200, 'Q1003', 'Gamma', 690000000.0, 2))
LINKS = ((1, 1, 700000010.0), (2, 1, 700000205.5), (1, 2, 700000110.0))


def _utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


class SafariHistoryTagsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _store(self, relative, visits=VISITS, links=LINKS, tag_tables=True):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        database = sqlite3.connect(path)
        for statement in BASE_TABLES + (TAG_TABLES if tag_tables else ()):
            database.execute(statement)
        database.executemany('INSERT INTO history_items VALUES (?,?,?,?)', ITEMS)
        database.executemany(
            'INSERT INTO history_visits (id, history_item, visit_time, title) VALUES (?,?,?,?)', visits)
        if tag_tables:
            database.executemany('INSERT INTO history_tags VALUES (?,?,?,?,?,?,?)', TAGS)
            database.executemany('INSERT INTO history_items_to_tags VALUES (?,?,?)', links)
        database.commit()
        database.close()
        self.files.append(str(path))

    def _run(self, processor):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(safaribrowsing, 'logfunc') as log:
            headers, rows, source = processor.__wrapped__(context)
        return headers, rows, source, [call.args[0] for call in log.call_args_list]

    def test_a_visit_shows_the_tags_of_its_item_in_link_order(self):
        self._store(USER)
        headers, rows, source, _log = self._run(safaribrowsing.safariHistory)
        self.assertEqual(headers[-3:], ('Tags', 'Tag Identifiers', 'Source File'))
        self.assertEqual(
            [(row[0], row[1], row[9], row[10]) for row in rows],
            [(_utc(2023, 3, 8, 20, 31, 40), 'https://three.example/', '', ''),
             (_utc(2023, 3, 8, 20, 30), 'https://two.example/', 'Alpha', 'Q1001'),
             (_utc(2023, 3, 8, 20, 28, 20), 'https://one.example/', 'Alpha; Beta', 'Q1001; Q1002'),
             (_utc(2023, 3, 8, 20, 26, 40), 'https://one.example/', 'Alpha; Beta', 'Q1001; Q1002')])
        self.assertEqual(source, USER)

    def test_tags_are_listed_per_link_and_once_when_no_link_names_them(self):
        self._store(USER)
        headers, rows, source, _log = self._run(safaribrowsing.safariHistoryTags)
        self.assertEqual(
            headers,
            (('Tag Modified', 'datetime'), ('Item Tagged', 'datetime'), 'Tag', 'Identifier', 'URL',
             'Item Count', 'Linked Items', 'Type', 'Level', 'Source File'))
        self.assertEqual(rows, [
            (_utc(2023, 3, 8, 20, 30, 5, 500000), _utc(2023, 3, 8, 20, 30, 5, 500000), 'Alpha',
             'Q1001', 'https://two.example/', 3, 2, 1, 200, USER),
            (_utc(2023, 3, 8, 20, 30, 5, 500000), _utc(2023, 3, 8, 20, 26, 50), 'Alpha', 'Q1001',
             'https://one.example/', 3, 2, 1, 200, USER),
            (_utc(2023, 3, 8, 20, 28, 30), _utc(2023, 3, 8, 20, 28, 30), 'Beta', 'Q1002',
             'https://one.example/', 1, 1, 1, 200, USER),
            (_utc(2022, 11, 13, 2, 40), None, 'Gamma', 'Q1003', '', 2, 0, 1, 200, USER)])
        self.assertEqual(source, USER)

    def test_a_store_without_the_tag_tables_still_reports_its_visits(self):
        self._store(USER, tag_tables=False)
        _headers, rows, source, _log = self._run(safaribrowsing.safariHistory)
        self.assertEqual([(row[1], row[9], row[10]) for row in rows],
                         [('https://three.example/', '', ''), ('https://two.example/', '', ''),
                          ('https://one.example/', '', ''), ('https://one.example/', '', '')])
        self.assertEqual(source, USER)
        _headers, rows, source, _log = self._run(safaribrowsing.safariHistoryTags)
        self.assertEqual(rows, [])
        self.assertEqual(source, USER)

    def test_a_store_held_under_both_views_is_reported_once(self):
        self._store(USER)
        self._store(DATA_VIEW)
        _headers, rows, source, log = self._run(safaribrowsing.safariHistory)
        self.assertEqual([row[-1] for row in rows], [USER] * 4)
        self.assertEqual(source, f'{USER}\n{DATA_VIEW}')
        self.assertEqual(log, ['Safari History: 4 visit(s) across 2 History.db file(s); 4 visit(s) '
                               'held by a second copy of a store were not reported again.'])
        _headers, rows, source, log = self._run(safaribrowsing.safariHistoryTags)
        self.assertEqual([row[-1] for row in rows], [USER] * 4)
        self.assertEqual(source, f'{USER}\n{DATA_VIEW}')
        self.assertEqual(log, ['Safari History Tags: 4 row(s) across 2 History.db file(s); 4 row(s) '
                               'held by a second copy of a store were not reported again.'])

    def test_a_record_only_the_second_copy_holds_is_still_reported(self):
        self._store(USER)
        self._store(DATA_VIEW, visits=VISITS + ((5, 3, 700000400.0, 'Three again'),),
                    links=LINKS + ((3, 2, 700000410.0),))
        _headers, rows, _source, _log = self._run(safaribrowsing.safariHistory)
        # The second copy tags item 3, so its two visits of that item differ from the first
        # copy's one and both are reported; the visits of items 1 and 2 are reported once.
        self.assertEqual(
            sorted((row[1], row[3], row[9], row[-1]) for row in rows),
            [('https://one.example/', 'One', 'Alpha; Beta', USER),
             ('https://one.example/', 'One again', 'Alpha; Beta', USER),
             ('https://three.example/', 'Three', '', USER),
             ('https://three.example/', 'Three', 'Beta', DATA_VIEW),
             ('https://three.example/', 'Three again', 'Beta', DATA_VIEW),
             ('https://two.example/', 'Two', 'Alpha', USER)])
        _headers, rows, _source, _log = self._run(safaribrowsing.safariHistoryTags)
        # Beta has two links in the second copy, so its Linked Items differs there and both of
        # that copy's Beta rows are reported beside the first copy's one.
        self.assertEqual(
            sorted((row[2], row[4], row[6], row[-1]) for row in rows),
            [('Alpha', 'https://one.example/', 2, USER),
             ('Alpha', 'https://two.example/', 2, USER),
             ('Beta', 'https://one.example/', 1, USER),
             ('Beta', 'https://one.example/', 2, DATA_VIEW),
             ('Beta', 'https://three.example/', 2, DATA_VIEW),
             ('Gamma', '', 0, USER)])

    def test_two_users_are_both_reported(self):
        self._store(USER)
        self._store(OTHER_USER)
        _headers, rows, source, _log = self._run(safaribrowsing.safariHistory)
        self.assertEqual(sorted(row[-1] for row in rows), [OTHER_USER] * 4 + [USER] * 4)
        self.assertEqual(source, f'{OTHER_USER}\n{USER}')
        _headers, rows, _source, _log = self._run(safaribrowsing.safariHistoryTags)
        self.assertEqual(sorted(row[-1] for row in rows), [OTHER_USER] * 4 + [USER] * 4)

    def test_the_declared_paths_match_a_profile_database_and_its_sidecars(self):
        for artifact in ('safariHistory', 'safariHistoryTags'):
            paths = safaribrowsing.__artifacts_v2__[artifact]['paths']

            def matched(name, paths=paths):
                return any(fnmatch.fnmatchcase(name, pattern) for pattern in paths)

            for name in (USER, DATA_VIEW, PROFILE, PROFILE + '-wal', PROFILE + '-shm',
                         PROFILE_DATA_VIEW):
                self.assertTrue(matched(name), (artifact, name))
            for name in ('Users/someone/Library/Containers/com.example.other/Data/Library/'
                         'NotSafari/Profiles/AAAA/History.db',
                         'Users/someone/Library/Safari/Profiles/AAAA/Other.db'):
                self.assertFalse(matched(name), (artifact, name))

    def test_a_profile_database_is_read_as_its_own_store(self):
        self._store(USER)
        self._store(PROFILE)
        self._store(PROFILE_DATA_VIEW)
        _headers, rows, source, log = self._run(safaribrowsing.safariHistory)
        self.assertEqual(sorted(row[-1] for row in rows), [PROFILE] * 4 + [USER] * 4)
        self.assertEqual(sorted(source.split('\n')), sorted([USER, PROFILE, PROFILE_DATA_VIEW]))
        self.assertEqual(log, ['Safari History: 8 visit(s) across 3 History.db file(s); 4 visit(s) '
                               'held by a second copy of a store were not reported again.'])
        _headers, rows, _source, log = self._run(safaribrowsing.safariHistoryTags)
        self.assertEqual(sorted(row[-1] for row in rows), [PROFILE] * 4 + [USER] * 4)
        self.assertEqual(log, ['Safari History Tags: 8 row(s) across 3 History.db file(s); 4 row(s) '
                               'held by a second copy of a store were not reported again.'])


if __name__ == '__main__':
    unittest.main()
