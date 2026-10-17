"""Pin how chromiumBounceTracking and edgeWebAssistHistory read DIPS and WebAssistDatabase.

Author: @AlexisBrignoni, Claude.

Every database here is synthetic, built with the CREATE TABLE text of the DIPS schema
versions 8 and 11 and of WebAssistDatabase version 5 as found in tested profiles. The
expected values are written out, never read back from the code under test.
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
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import chromiumBounceTracking as dips  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
EDGE = 'C/Users/{user}/AppData/Local/Microsoft/Edge/User Data/{profile}'
CHROME_MAC = 'Users/{user}/Library/Application Support/Google/Chrome/{profile}'
# 2024-11-04 15:33:34.623 UTC as a Chromium time and as Unix seconds.
WEBKIT = 13375208014623000
WHEN = datetime.datetime(2024, 11, 4, 15, 33, 34, 623000, tzinfo=UTC)
UNIX = 1730734414

V8 = '''
CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
CREATE TABLE bounces(site TEXT PRIMARY KEY NOT NULL,first_site_storage_time INTEGER,
  last_site_storage_time INTEGER,first_user_interaction_time INTEGER,
  last_user_interaction_time INTEGER,first_stateful_bounce_time INTEGER,
  last_stateful_bounce_time INTEGER,first_bounce_time INTEGER,last_bounce_time INTEGER,
  first_web_authn_assertion_time INTEGER,last_web_authn_assertion_time INTEGER);
INSERT INTO meta VALUES ('version', '8');
'''
V11 = '''
CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
CREATE TABLE bounces(site TEXT PRIMARY KEY NOT NULL,first_user_activation_time INTEGER,
  last_user_activation_time INTEGER,first_bounce_time INTEGER,last_bounce_time INTEGER,
  first_web_authn_assertion_time INTEGER,last_web_authn_assertion_time INTEGER);
INSERT INTO meta VALUES ('version', '11');
'''
WEBASSIST = '''
CREATE TABLE navigation_history ( url VARCHAR NOT NULL PRIMARY KEY, id INTEGER, title VARCHAR,
  metadata VARCHAR, last_visited_time INTEGER NOT NULL DEFAULT 0, num_visits INTEGER NOT NULL
  DEFAULT 1, product_entity_id VARCHAR, locale VARCHAR, titledata VARCHAR, urldata VARCHAR,
  page_profile VARCHAR);
CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
INSERT INTO meta VALUES ('version', '5');
'''


class BounceTrackingTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _db(self, folder, name, script, rows=()):
        path = self.root / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.executescript(script)
            for statement, values in rows:
                db.execute(statement, values)
        db.close()
        self.files.append(str(path))
        return path

    def _run(self, function):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(dips, 'logfunc') as log, \
                mock.patch('scripts.chromium.browser_profiles.logfunc'), \
                mock.patch('scripts.macos_plists.logfunc'):
            result = getattr(dips, function).__wrapped__(context)
        return result, [call.args[0] for call in log.call_args_list]

    def test_version_8_maps_interaction_to_activation_and_keeps_old_columns(self):
        folder = EDGE.format(user='jdoe', profile='Default')
        self._db(folder, 'DIPS', V8, [(
            'INSERT INTO bounces VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            ('example.com', WEBKIT - 1, WEBKIT + 1, WEBKIT, WEBKIT + 2, None, None, None, None,
             None, None))])
        (headers, rows, source), _log = self._run('chromiumBounceTracking')
        self.assertEqual(len(headers), len(rows[0]))
        micro = datetime.timedelta(microseconds=1)
        self.assertEqual(rows, [(
            WHEN + 2 * micro, WHEN, '', '', '', '', WHEN + micro, WHEN - micro, '', '',
            'example.com', '8', 'Microsoft Edge', 'Default', 'jdoe', f'{folder}/DIPS')])
        self.assertEqual(source, str(self.root / folder / 'DIPS'))

    def test_version_11_leaves_the_dropped_columns_blank(self):
        folder = CHROME_MAC.format(user='jdoe', profile='Profile 1')
        self._db(folder, 'DIPS', V11, [(
            'INSERT INTO bounces VALUES (?,?,?,?,?,?,?)',
            ('tracker.example', None, None, WEBKIT, WEBKIT, WEBKIT, WEBKIT))])
        (_headers, rows, _source), _log = self._run('chromiumBounceTracking')
        self.assertEqual(rows, [(
            '', '', WHEN, WHEN, '', '', '', '', WHEN, WHEN, 'tracker.example', '11',
            'Google Chrome', 'Profile 1', 'jdoe', f'{folder}/DIPS')])

    def test_a_second_view_of_one_mac_profile_is_read_once(self):
        folder = CHROME_MAC.format(user='jdoe', profile='Default')
        for prefix in ('', 'System/Volumes/Data/'):
            self._db(prefix + folder, 'DIPS', V11, [(
                'INSERT INTO bounces VALUES (?,?,?,?,?,?,?)',
                ('example.com', WEBKIT, WEBKIT, None, None, None, None))])
        (_headers, rows, _source), _log = self._run('chromiumBounceTracking')
        self.assertEqual(len(rows), 1)

    def test_a_dips_file_outside_a_browser_profile_is_not_read(self):
        self._db('C/Users/jdoe/AppData/Local/Microsoft/Olk/EBWebView/Default', 'DIPS', V11,
                 [('INSERT INTO bounces VALUES (?,?,?,?,?,?,?)',
                   ('example.com', WEBKIT, WEBKIT, None, None, None, None))])
        (_headers, rows, source), _log = self._run('chromiumBounceTracking')
        self.assertEqual((rows, source), ([], ''))

    def test_webassist_rows(self):
        folder = EDGE.format(user='jdoe', profile='Default')
        self._db(folder, 'WebAssistDatabase', WEBASSIST, [(
            'INSERT INTO navigation_history VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            ('https://example.com/', 0, 'Example', 'about example', UNIX, 3, None, 'en-us',
             'example', 'example com', None))])
        (headers, rows, _source), _log = self._run('edgeWebAssistHistory')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [(
            datetime.datetime(2024, 11, 4, 15, 33, 34, tzinfo=UTC), 'https://example.com/',
            'Example', 3, 'about example', 'en-us', '5', 'Microsoft Edge', 'Default', 'jdoe',
            f'{folder}/WebAssistDatabase')])

    def test_the_paths_match_profile_stores_and_their_logs(self):
        block = dips.__artifacts_v2__
        def hits(artifact, relative):
            return [p for p in block[artifact]['paths'] if fnmatch.fnmatchcase('root/' + relative, p)]
        edge = EDGE.format(user='u', profile='Default')
        self.assertEqual(len(hits('chromiumBounceTracking', edge + '/DIPS')), 1)
        self.assertEqual(len(hits('chromiumBounceTracking', edge + '/DIPS-wal')), 1)
        self.assertEqual(len(hits('edgeWebAssistHistory', edge + '/WebAssistDatabase')), 1)
        self.assertEqual(hits('edgeWebAssistHistory',
                              CHROME_MAC.format(user='u', profile='Default') + '/WebAssistDatabase'), [])
        self.assertEqual(hits('chromiumBounceTracking',
                              'C/Users/u/AppData/Local/Microsoft/Olk/EBWebView/Default/DIPS'), [])


if __name__ == '__main__':
    unittest.main()
