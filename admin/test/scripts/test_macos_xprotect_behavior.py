"""Pin the XPdb reading in scripts/artifacts/macosXProtectBehavior.py.

Every database below is built by the test with the table layout the artifact reads; no value
comes from a real device. Expected times are written out as literals.
"""
import fnmatch
import os
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

from scripts.artifacts import macosXProtectBehavior as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
NEW = 'private/var/protected/xprotect/db/XPdb'
OLD = 'private/var/protected/xprotect/XPdb'
SCHEMA = ('CREATE TABLE events (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
          '    violated_rule TEXT,\n    exec_path TEXT,\n    exec_cdhash TEXT,\n'
          '    exec_signing_id TEXT,\n    exec_team_id TEXT,\n    exec_sha256 TEXT,\n'
          '    exec_is_notarized BOOLEAN,\n    responsible_path TEXT,\n'
          '    responsible_cdhash TEXT,\n    responsible_signing_id TEXT,\n'
          '    responsible_team_id TEXT,\n    responsible_sha256 TEXT,\n'
          '    responsible_is_notarized BOOLEAN,\n    reported BOOLEAN,\n'
          '    profile_hash INTEGER,\n'
          "    dt DATETIME NOT NULL DEFAULT (datetime('now')))")


def event(rule, dt, exec_path='/Applications/Example.app/Contents/MacOS/Example', notarized=1):
    return (rule, exec_path, 'aa11', 'com.example.tool', 'TEAM000001', 'bb22', notarized,
            '/Applications/Parent.app/Contents/MacOS/Parent', 'cc33', 'com.example.parent', '',
            'dd44', 0, 0, 1234567890123, dt)


def xpdb(path, events=(), version='4', with_settings=True, with_events=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    if with_settings:
        con.execute('CREATE TABLE settings ( name TEXT, value TEXT, PRIMARY KEY (name) )')
        con.execute("INSERT INTO settings VALUES ('databaseSchemaVersion', ?)", (version,))
    if with_events:
        con.execute(SCHEMA)
        con.executemany('INSERT INTO events (violated_rule, exec_path, exec_cdhash, '
                        'exec_signing_id, exec_team_id, exec_sha256, exec_is_notarized, '
                        'responsible_path, responsible_cdhash, responsible_signing_id, '
                        'responsible_team_id, responsible_sha256, responsible_is_notarized, '
                        'reported, profile_hash, dt) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', events)
    con.commit()
    con.close()


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class XProtectBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        patcher = patch.object(artifact, 'logfunc')
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def path(self, relative):
        return os.path.join(self.root, relative)

    def run_artifact(self, *relatives):
        files = [self.path(relative) for relative in relatives]
        files += [path + suffix for path in files for suffix in ('-wal', '-shm')
                  if os.path.exists(path + suffix)]
        return artifact.macosXProtectBehaviorEvents.__wrapped__(Context(self.root, files))

    def test_one_row_per_event_with_dt_read_as_utc(self):
        xpdb(self.path(NEW), [event('Rule.B', '2025-01-02 03:04:05'),
                              event('Rule.A', '2025-01-01 23:59:59', notarized=0)])
        headers, rows, source = self.run_artifact(NEW)
        self.assertEqual(headers[0], ('Event Time (UTC)', 'datetime'))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 2)
        first = rows[0]
        self.assertEqual(first[0], datetime(2025, 1, 1, 23, 59, 59, tzinfo=UTC))
        self.assertEqual(first[1:3], (2, 'Rule.A'))
        self.assertEqual(first[3:9], ('/Applications/Example.app/Contents/MacOS/Example',
                                      'com.example.tool', 'TEAM000001', 'aa11', 'bb22', 0))
        self.assertEqual(first[9:15], ('/Applications/Parent.app/Contents/MacOS/Parent',
                                       'com.example.parent', '', 'cc33', 'dd44', 0))
        self.assertEqual(first[15:], (0, 1234567890123, '4', NEW))
        self.assertEqual(rows[1][0], datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC))
        self.assertEqual(source, self.path(NEW))

    def test_dt_that_is_not_the_datetime_text_is_kept_as_stored(self):
        xpdb(self.path(NEW), [event('Rule.A', '2025-01-01T00:00:00Z')])
        _headers, rows, _source = self.run_artifact(NEW)
        self.assertEqual(rows[0][0], '2025-01-01T00:00:00Z')

    def test_earlier_path_is_read(self):
        xpdb(self.path(OLD), [event('Rule.A', '2024-06-01 10:00:00')])
        _headers, rows, _source = self.run_artifact(OLD)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][-1], OLD)

    def test_patterns_match_both_paths_and_not_the_bundle(self):
        patterns = artifact.__artifacts_v2__['macosXProtectBehaviorEvents']['paths']
        def hits(member):
            return [p for p in patterns if fnmatch.fnmatchcase('root/' + member, p)]
        self.assertEqual(len(hits(NEW)), 1)
        self.assertEqual(len(hits(NEW + '-wal')), 1)
        self.assertEqual(len(hits(OLD)), 1)
        self.assertEqual(len(hits('System/Volumes/Data/' + NEW)), 1)
        self.assertEqual(hits('private/var/protected/xprotect/XProtect.bundle/Contents/'
                              'Resources/gk.db'), [])

    def test_identical_copy_under_the_data_view_is_not_counted_twice(self):
        xpdb(self.path(NEW), [event('Rule.A', '2025-01-01 00:00:00'),
                              event('Rule.B', '2025-01-01 00:00:01')])
        os.makedirs(os.path.dirname(self.path('System/Volumes/Data/' + NEW)))
        shutil.copyfile(self.path(NEW), self.path('System/Volumes/Data/' + NEW))
        _headers, rows, source = self.run_artifact(NEW, 'System/Volumes/Data/' + NEW)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row[-1] for row in rows}, {NEW})
        self.assertEqual(source, self.path(NEW))

    def test_differing_copies_report_a_shared_event_once_with_both_files(self):
        xpdb(self.path(NEW), [event('Rule.A', '2025-01-01 00:00:00')])
        xpdb(self.path('System/Volumes/Data/' + NEW),
             [event('Rule.A', '2025-01-01 00:00:00'), event('Rule.B', '2025-01-01 00:00:01')])
        _headers, rows, _source = self.run_artifact(NEW, 'System/Volumes/Data/' + NEW)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][-1], f'{NEW}\nSystem/Volumes/Data/{NEW}')
        self.assertEqual(rows[1][-1], f'System/Volumes/Data/{NEW}')

    def test_missing_events_table_is_logged_and_yields_nothing(self):
        xpdb(self.path(NEW), with_events=False)
        _headers, rows, source = self.run_artifact(NEW)
        self.assertEqual((rows, source), ([], ''))
        self.assertTrue(any('no events table' in str(call) for call in self.log.call_args_list))

    def test_missing_settings_table_leaves_schema_version_blank(self):
        xpdb(self.path(NEW), [event('Rule.A', '2025-01-01 00:00:00')], with_settings=False)
        _headers, rows, _source = self.run_artifact(NEW)
        self.assertEqual(rows[0][-2], '')

    def test_empty_events_table_reports_its_path(self):
        xpdb(self.path(NEW))
        _headers, rows, source = self.run_artifact(NEW)
        self.assertEqual((rows, source), ([], self.path(NEW)))


if __name__ == '__main__':
    unittest.main()
