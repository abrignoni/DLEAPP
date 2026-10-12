"""Pin the Personalization Portrait artifacts (scripts/artifacts/macosPersonalizationPortrait.py).

The database is built for the test with the columns the artifacts read from PPSQLDatabase.db on macOS 11. The
values are made up.
"""
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosPersonalizationPortrait as portrait
# pylint: enable=wrong-import-position

SCHEMA = '''
CREATE TABLE sources (id INTEGER PRIMARY KEY, bundle_id TEXT, group_id TEXT, doc_id TEXT, seconds_from_1970 REAL);
CREATE TABLE ne_records (id INTEGER PRIMARY KEY, name TEXT, category INTEGER, language TEXT, algorithm INTEGER,
    initial_score REAL, decay_rate REAL, sentiment_score REAL, impression_count INTEGER, occurrences_in_source INTEGER,
    is_remote INTEGER, is_sync_eligible INTEGER, extraction_os_build TEXT, source_id INTEGER);
CREATE TABLE tp_records (id INTEGER PRIMARY KEY, topic_id TEXT, algorithm INTEGER, initial_score REAL, decay_rate REAL,
    sentiment_score REAL, impression_count INTEGER, occurrences_in_source INTEGER, exact_match_in_source_text INTEGER,
    algorithm_result_position INTEGER, algorithm_result_count INTEGER, is_remote INTEGER, is_sync_eligible INTEGER,
    extraction_os_build TEXT, source_id INTEGER);
CREATE TABLE loc_records (id INTEGER PRIMARY KEY, cll_latitude_degrees REAL, cll_longitude_degrees REAL, clp_name TEXT,
    clp_subThoroughfare TEXT, clp_thoroughfare TEXT, clp_subLocality TEXT, clp_locality TEXT,
    clp_subAdministrativeArea TEXT, clp_administrativeArea TEXT, clp_postalCode TEXT, clp_ISOcountryCode TEXT,
    clp_country TEXT, lc_description TEXT, category INTEGER, algorithm INTEGER, initial_score REAL, decay_rate REAL,
    is_remote INTEGER, is_sync_eligible INTEGER, extraction_os_build TEXT, source_id INTEGER);
'''
T1 = 1700000000.5


def build(path, extra_entity=False, locations=True):
    database = sqlite3.connect(path)
    database.executescript(SCHEMA)
    database.execute("INSERT INTO sources VALUES (1, 'com.example.mail', 'group one', 'doc one', ?)", (T1,))
    database.execute("INSERT INTO sources VALUES (2, 'com.example.notes', NULL, 'doc two', 'soon')")
    database.execute("INSERT INTO ne_records VALUES (2, 'Second Name', 3, 'en', 6, 0.5, 0.0, -0.25, 2, 4, 1, 0, 'macOS-20D74', 2)")
    database.execute("INSERT INTO ne_records VALUES (1, 'First Name', 1, '', 2, 0.75, 0.1, 0.0, 1, 1, 0, 1, 'macOS-20C69', 1)")
    database.execute("INSERT INTO ne_records VALUES (3, 'No Source', 0, 'en', 4, 0.375, 0.0, 0.0, 1, 1, 0, 0, NULL, 99)")
    if extra_entity:
        database.execute("INSERT INTO ne_records VALUES (4, 'Only Here', 0, 'en', 4, 0.375, 0.0, 0.0, 1, 1, 0, 0, NULL, 1)")
    database.execute("INSERT INTO tp_records VALUES (1, 'Q42', 7, 0.26, 0.0, 0.0, 3, 1, 1, 2, 5, 0, 1, 'macOS-20D74', 1)")
    if locations:
        database.execute("INSERT INTO loc_records VALUES (1, 18.25, -66.5, 'A Place', '12', 'Main St', 'Old Town', 'City', "
                         "'County', 'State', '00901', 'US', 'United States', 'a place description', 5, 3, 0.33, 0.000385, "
                         "0, 0, 'macOS-20D74', 1)")
        database.execute("INSERT INTO loc_records VALUES (2, NULL, NULL, NULL, NULL, 'Main St', NULL, 'City', NULL, 'State', "
                         "NULL, NULL, 'United States', 'main st city', 0, 6, 0.22, 0.0, 0, 0, 'macOS-20D74', 2)")
    else:
        database.execute('DROP TABLE loc_records')
    database.commit()
    database.close()


def utc(*parts):
    return datetime(*parts, tzinfo=timezone.utc)


WHEN = utc(2023, 11, 14, 22, 13, 20, 500000)


class Seconds(unittest.TestCase):
    def test_values(self):
        self.assertEqual(portrait.utc_from_seconds(T1), WHEN)
        self.assertEqual(portrait.utc_from_seconds(1700000000), utc(2023, 11, 14, 22, 13, 20))
        self.assertEqual(portrait.utc_from_seconds('1700000000.5'), WHEN)
        for value in (None, 'soon', b'1700000000', True, float('inf'), float('nan'), 1e30):
            self.assertEqual(portrait.utc_from_seconds(value), '', value)


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, *top, **options):
        folder = os.path.join(self.folder.name, *top, 'Library', 'PersonalizationPortrait')
        os.makedirs(folder)
        path = os.path.join(folder, 'PPSQLDatabase.db')
        build(path, **options)
        return path

    def run_artifact(self, function, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(portrait, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc') as shared:
            result = function.__wrapped__(context)
        return result, [call.args[0] for call in shared.call_args_list + log.call_args_list]

    def test_named_entities(self):
        path = self.database('Users', 'a')
        decoy = os.path.join(os.path.dirname(path), 'OtherPPSQLDatabase.db')
        build(decoy)
        sidecar = path + '-wal'
        with open(sidecar, 'wb'):
            pass
        (headers, rows, located), logged = self.run_artifact(portrait.macosPortraitNamedEntities, [decoy, sidecar, path])
        relative = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 18)
        self.assertEqual(headers[0], ('Source Time (UTC)', 'datetime'))
        self.assertEqual(rows, [
            (WHEN, 'com.example.mail', 'group one', 'doc one', 'First Name', 1, '', 2, 0.75, 0.1, 0.0, 1, 1, 0, 1,
             'macOS-20C69', 1, relative),
            ('', 'com.example.notes', None, 'doc two', 'Second Name', 3, 'en', 6, 0.5, 0.0, -0.25, 2, 4, 1, 0,
             'macOS-20D74', 2, relative),
            ('', None, None, None, 'No Source', 0, 'en', 4, 0.375, 0.0, 0.0, 1, 1, 0, 0, None, 3, relative)])
        self.assertEqual((located, logged), (path, []))

    def test_topics(self):
        path = self.database('Users', 'a')
        (headers, rows, located), _ = self.run_artifact(portrait.macosPortraitTopics, [path])
        self.assertEqual(len(headers), 19)
        self.assertEqual(rows, [(WHEN, 'com.example.mail', 'group one', 'doc one', 'Q42', 7, 0.26, 0.0, 0.0, 3, 1, 1, 2, 5,
                                 0, 1, 'macOS-20D74', 1, os.path.relpath(path, self.folder.name))])
        self.assertEqual(located, path)

    def test_locations(self):
        path = self.database('Users', 'a')
        (headers, rows, _), _ = self.run_artifact(portrait.macosPortraitLocations, [path])
        relative = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 26)
        self.assertEqual(headers[4:6], ('Latitude', 'Longitude'))
        self.assertEqual(rows, [
            (WHEN, 'com.example.mail', 'group one', 'doc one', 18.25, -66.5, 'A Place', '12', 'Main St', 'Old Town', 'City',
             'County', 'State', '00901', 'US', 'United States', 'a place description', 5, 3, 0.33, 0.000385, 0, 0,
             'macOS-20D74', 1, relative),
            ('', 'com.example.notes', None, 'doc two', None, None, None, None, 'Main St', None, 'City', None, 'State', None,
             None, 'United States', 'main st city', 0, 6, 0.22, 0.0, 0, 0, 'macOS-20D74', 2, relative)])

    def test_two_views_two_users_and_a_database_that_cannot_be_read(self):
        first = self.database('Users', 'a')
        same = self.database('System', 'Volumes', 'Data', 'Users', 'a')
        other_user = self.database('Users', 'b')
        differs = self.database('System', 'Volumes', 'Data', 'Users', 'b', extra_entity=True)
        broken = self.database('Users', 'c', locations=False)
        found = [broken, differs, other_user, same, first]
        (_, rows, located), logged = self.run_artifact(portrait.macosPortraitNamedEntities, found)
        relative = lambda p: os.path.relpath(p, self.folder.name)
        self.assertEqual([(row[4], row[-1]) for row in rows], [
            ('First Name', relative(differs) + '\n' + relative(other_user)),
            ('Second Name', relative(differs) + '\n' + relative(other_user)),
            ('No Source', relative(differs) + '\n' + relative(other_user)),
            ('Only Here', relative(differs)),
            ('First Name', relative(first)), ('Second Name', relative(first)), ('No Source', relative(first)),
            ('First Name', relative(broken)), ('Second Name', relative(broken)), ('No Source', relative(broken))])
        self.assertEqual(located, differs + '\n' + first + '\n' + other_user + '\n' + broken)
        self.assertEqual(len(logged), 1)
        self.assertIn('1 byte-identical copy(ies)', logged[0])
        (_, rows, located), logged = self.run_artifact(portrait.macosPortraitLocations, found)
        self.assertEqual(len(rows), 4)
        self.assertEqual(located, differs + '\n' + first + '\n' + other_user)
        self.assertEqual(logged[1:], ['Personalization Portrait - Locations: 1 databases that could not be read '
                                      '(OperationalError)'])

    def test_a_database_that_does_not_open_and_one_with_no_rows(self):
        empty = self.database('Users', 'a')
        database = sqlite3.connect(empty)
        database.execute('DELETE FROM tp_records')
        database.commit()
        database.close()
        closed = self.database('Users', 'b')
        opener = portrait.open_sqlite_db_readonly
        with mock.patch.object(portrait, 'open_sqlite_db_readonly', side_effect=lambda p: None if p == closed else opener(p)):
            (_, rows, located), logged = self.run_artifact(portrait.macosPortraitTopics, [closed, empty])
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(logged, ['Personalization Portrait - Topics: 1 databases that could not be opened'])

    def test_nothing_found(self):
        for function in (portrait.macosPortraitNamedEntities, portrait.macosPortraitTopics, portrait.macosPortraitLocations):
            (_, rows, located), logged = self.run_artifact(function, [])
            self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
