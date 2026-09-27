"""Pin the System Policy reading in scripts/artifacts/macosSystemPolicy.py.

Every database below is built by the test with the table layouts the artifacts read; no value
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

from scripts.artifacts import macosSystemPolicy as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
CONFIG = 'private/var/db/SystemPolicyConfiguration'


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def kext_policy(path, history=(), policy=()):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.execute('CREATE TABLE kext_load_history_v3 ( path TEXT PRIMARY KEY, team_id TEXT, '
                'bundle_id TEXT, boot_uuid TEXT, created_at TEXT, last_seen TEXT, flags INTEGER , '
                'cdhash TEXT)')
    con.execute('CREATE TABLE kext_policy ( team_id TEXT, bundle_id TEXT, allowed BOOLEAN, '
                'developer_name TEXT, flags INTEGER, PRIMARY KEY (team_id, bundle_id) )')
    con.executemany('INSERT INTO kext_load_history_v3 VALUES (?, ?, ?, ?, ?, ?, ?, ?)', history)
    con.executemany('INSERT INTO kext_policy VALUES (?, ?, ?, ?, ?)', policy)
    con.commit()
    con.close()


def system_policy(path, objects=()):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.execute('CREATE TABLE authority (id INTEGER PRIMARY KEY AUTOINCREMENT, version INTEGER, '
                'type INTEGER, requirement TEXT, allow INTEGER, disabled INTEGER, expires FLOAT, '
                'priority REAL, label TEXT, filter_unsigned TEXT, flags INTEGER, ctime FLOAT, '
                'mtime FLOAT, user TEXT, remarks TEXT)')
    con.execute("INSERT INTO authority (id, type, allow, label, flags) "
                "VALUES (16, 3, 1, 'Notarized Developer ID', 2)")
    con.execute('CREATE TABLE object (id INTEGER PRIMARY KEY, type INTEGER NOT NULL, hash CDHASH '
                'NOT NULL, allow INTEGER NOT NULL, expires FLOAT NOT NULL DEFAULT (5000000), '
                'authority INTEGER NOT NULL, path TEXT NULL, ctime FLOAT, mtime FLOAT, remarks TEXT)')
    con.executemany('INSERT INTO object (id, type, hash, allow, expires, authority, path, ctime, mtime, '
                    'remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', objects)
    con.commit()
    con.close()


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root) for name in names)


class HelperTest(unittest.TestCase):
    # pylint: disable=protected-access
    def test_text_time(self):
        self.assertEqual(artifact._text_time('2020-12-02 15:16:17'), datetime(2020, 12, 2, 15, 16, 17, tzinfo=UTC))
        self.assertEqual(artifact._text_time('2020-12-02T15:16:17Z'), '2020-12-02T15:16:17Z')
        self.assertEqual(artifact._text_time(None), '')

    def test_julian_time(self):
        # 2440587.5 is 1970-01-01 00:00 UTC; half a day later is noon.
        self.assertEqual(artifact._julian_time(2440587.5), datetime(1970, 1, 1, tzinfo=UTC))
        self.assertEqual(artifact._julian_time(2440588.0), datetime(1970, 1, 1, 12, tzinfo=UTC))
        self.assertEqual(artifact._julian_time(2461011.5), datetime(2025, 12, 2, tzinfo=UTC))
        self.assertEqual(artifact._julian_time(5000000), '')
        self.assertEqual(artifact._julian_time(5000000.0), '')
        self.assertEqual(artifact._julian_time(None), '')
        self.assertEqual(artifact._julian_time('soon'), 'soon')

    def test_hex(self):
        self.assertEqual(artifact._hex(bytes.fromhex('d01045ef')), 'd01045ef')
        self.assertEqual(artifact._hex('d01045ef'), 'd01045ef')
        self.assertEqual(artifact._hex(None), '')


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged = []
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.image = os.path.join(self.root, 'image')

    def run_artifact(self, function):
        return function.__wrapped__(Context(self.image, walk(self.image)))

    def test_kext_load_history_and_policy(self):
        history = [('/Library/Extensions/A.kext', 'TEAM1', 'com.example.a', 'BOOT-1', '2020-12-02 15:16:17',
                    '2021-02-19 19:53:28', 53, 'aa11')]
        # The same database under both firmlinked paths: one row, both copies listed.
        for prefix in ('', 'System/Volumes/Data/'):
            kext_policy(os.path.join(self.image, prefix + CONFIG, 'KextPolicy'), history,
                        [('TEAM1', 'com.example.a', 1, 'Example, Inc.', 1)])
        pathlib.Path(self.image, CONFIG, 'KextPolicy-wal').write_bytes(b'')
        headers, rows, source = self.run_artifact(artifact.macosKextLoadHistory)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Created (UTC)', 'Last Seen (UTC)', 'Path', 'Bundle ID', 'Team ID', 'Boot UUID',
                          'Flags (as stored)', 'CDHash', 'Source File'])
        both = 'System/Volumes/Data/' + CONFIG + '/KextPolicy\n' + CONFIG + '/KextPolicy'
        self.assertEqual(rows, [(datetime(2020, 12, 2, 15, 16, 17, tzinfo=UTC), datetime(2021, 2, 19, 19, 53, 28, tzinfo=UTC),
                                 '/Library/Extensions/A.kext', 'com.example.a', 'TEAM1', 'BOOT-1', 53, 'aa11', both)])
        self.assertEqual(len(source.split('\n')), 2)
        headers, rows, _ = self.run_artifact(artifact.macosKextPolicy)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Team ID', 'Bundle ID', 'Developer Name', 'Allowed (as stored)', 'Flags (as stored)', 'Source File'])
        self.assertEqual(rows, [('TEAM1', 'com.example.a', 'Example, Inc.', 1, 1, both)])
        # The empty -wal beside one copy is not read as a database of its own.
        self.assertEqual(self.logged, [])

    def test_gatekeeper_assessments(self):
        system_policy(os.path.join(self.image, 'private/var/db/SystemPolicy'), [
            (1, 3, bytes.fromhex('d01045ef100835fbdc4c79d8'), 1, 2461012.0, 16, '/Users/a/Downloads/x.dmg',
             2461011.5, 2461011.75, None),
            (2, 1, bytes.fromhex('0102'), 0, 5000000, 16, None, 2461010.5, 2461010.5, 'note')])
        # A database with no object table is logged and skipped.
        other = os.path.join(self.image, 'x', 'private', 'var', 'db')
        os.makedirs(other)
        con = sqlite3.connect(os.path.join(other, 'SystemPolicy'))
        con.execute('CREATE TABLE feature (id INTEGER)')
        con.commit()
        con.close()
        headers, rows, _ = self.run_artifact(artifact.macosGatekeeperAssessments)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Created (UTC)', 'Modified (UTC)', 'Expires (UTC)', 'Path', 'Type (as stored)', 'Type Name',
                          'Allow (as stored)', 'Authority ID', 'Authority Label', 'Hash', 'Remarks', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2025, 12, 1, tzinfo=UTC), datetime(2025, 12, 1, tzinfo=UTC), '', '', 1, 'kAuthorityExecute', 0, 16,
             'Notarized Developer ID', '0102', 'note', 'private/var/db/SystemPolicy'),
            (datetime(2025, 12, 2, tzinfo=UTC), datetime(2025, 12, 2, 6, tzinfo=UTC), datetime(2025, 12, 2, 12, tzinfo=UTC),
             '/Users/a/Downloads/x.dmg', 3, 'kAuthorityOpenDoc', 1, 16, 'Notarized Developer ID',
             'd01045ef100835fbdc4c79d8', '', 'private/var/db/SystemPolicy')])
        self.assertEqual(self.logged, ['SystemPolicy: no object table in x/private/var/db/SystemPolicy'])

    def test_declared_paths(self):
        cases = {'macosKextLoadHistory': ['Macintosh HD - Data/' + CONFIG + '/KextPolicy', 'r/' + CONFIG + '/KextPolicy-wal'],
                 'macosKextPolicy': ['r/System/Volumes/Data/' + CONFIG + '/KextPolicy'],
                 'macosGatekeeperAssessments': ['Macintosh HD - Data/private/var/db/SystemPolicy', 'r/' + CONFIG + '/SystemPolicy',
                                                'r/private/var/db/SystemPolicy-journal']}
        for key, paths in cases.items():
            for path in paths:
                self.assertTrue(any(fnmatch.fnmatch(path, p) for p in artifact.__artifacts_v2__[key]['paths']), (key, path))
            self.assertEqual(key, getattr(artifact, key).__name__)


if __name__ == '__main__':
    unittest.main()
