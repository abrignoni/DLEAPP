"""Pin the ExecPolicy reading in scripts/artifacts/macosExecPolicy.py.

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

from scripts.artifacts import macosExecPolicy as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
CONFIG = 'private/var/db/SystemPolicyConfiguration'
# 2025-12-09 21:44:51 UTC and neighbours, as Unix seconds.
T0 = 1765316691


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def exec_policy(path, newer=True, targets=(), measurements=(), cache=(), provenance=()):
    """An ExecPolicy with the tables the artifacts read. newer adds the columns and the
    provenance table a macOS 15 copy has and a macOS 11 copy lacks."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE scan_targets_v2 (  path TEXT NOT NULL,  responsible_path TEXT,  "
                "is_library INTEGER,  is_used INTEGER,  timestamp INTEGER NOT NULL DEFAULT "
                "(strftime('%s','now')),  measured_timestamp INTEGER,  deferral_count INTEGER,  "
                "PRIMARY KEY (path))")
    con.execute("CREATE TABLE executable_measurements_v2 (  is_signed INTEGER,  file_identifier "
                "TEXT NOT NULL,  bundle_identifier TEXT,  bundle_version TEXT,  team_identifier "
                "TEXT,  signing_identifier TEXT,  cdhash TEXT NOT NULL,  main_executable_hash "
                "TEXT,  executable_timestamp INTEGER,  file_size INTEGER,  is_library INTEGER,  "
                "is_used INTEGER,  responsible_file_identifier TEXT,  is_valid INTEGER,  "
                "is_quarantined INTEGER,  timestamp INTEGER NOT NULL DEFAULT "
                "(strftime('%s','now')),  reported_timestamp INTEGER,  PRIMARY KEY (cdhash))")
    extra = ', top_policy_match INTEGER, matched_rule_name TEXT' if newer else ''
    con.execute('CREATE TABLE policy_scan_cache (  pk INTEGER PRIMARY KEY AUTOINCREMENT,  '
                'volume_uuid TEXT NOT NULL,  object_id INTEGER,  fs_type_name TEXT NOT NULL,  '
                'bundle_id TEXT NOT NULL,  cdhash TEXT,  team_identifier TEXT,  '
                'signing_identifier TEXT,  policy_match INTEGER,  malware_result INTEGER,  '
                'flags INTEGER,  mod_time INTEGER,  timestamp INTEGER NOT NULL,  '
                f'revocation_check_time INTEGER,  scan_version INTEGER{extra},  '
                'UNIQUE(volume_uuid, object_id, fs_type_name))')
    if newer:
        con.execute('CREATE TABLE provenance_tracking (  pk INTEGER PRIMARY KEY,  url TEXT NOT '
                    'NULL,  bundle_id TEXT,  cdhash TEXT,  team_identifier TEXT,  '
                    'signing_identifier TEXT,  flags INTEGER,  timestamp INTEGER NOT NULL,  '
                    'link_pk INTEGER)')
    con.executemany('INSERT INTO scan_targets_v2 (path, responsible_path, is_library, is_used, '
                    'timestamp, measured_timestamp, deferral_count) VALUES (?, ?, ?, ?, ?, ?, 0)',
                    targets)
    con.executemany('INSERT INTO executable_measurements_v2 (timestamp, reported_timestamp, '
                    'executable_timestamp, file_identifier, responsible_file_identifier, '
                    'bundle_identifier, bundle_version, team_identifier, signing_identifier, '
                    'cdhash, main_executable_hash, file_size, is_signed, is_valid, '
                    'is_quarantined, is_library, is_used) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', measurements)
    if newer:
        con.executemany('INSERT INTO policy_scan_cache (timestamp, mod_time, revocation_check_time, '
                        'bundle_id, signing_identifier, team_identifier, cdhash, policy_match, '
                        'top_policy_match, matched_rule_name, malware_result, flags, fs_type_name, '
                        'volume_uuid, object_id, scan_version) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)', cache)
        con.executemany('INSERT INTO provenance_tracking (timestamp, url, bundle_id, '
                        'signing_identifier, team_identifier, cdhash, flags, pk, link_pk) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', provenance)
    else:
        con.executemany('INSERT INTO policy_scan_cache (timestamp, mod_time, revocation_check_time, '
                        'bundle_id, signing_identifier, team_identifier, cdhash, policy_match, '
                        'malware_result, flags, fs_type_name, volume_uuid, object_id, scan_version) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)', cache)
    con.commit()
    con.close()


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root) for name in names)


class HelperTest(unittest.TestCase):
    # pylint: disable=protected-access
    def test_unix_time(self):
        self.assertEqual(artifact._unix_time(T0), datetime(2025, 12, 9, 21, 44, 51, tzinfo=UTC))
        self.assertEqual(artifact._unix_time(0), '')
        self.assertEqual(artifact._unix_time(None), '')
        self.assertEqual(artifact._unix_time('soon'), 'soon')
        self.assertEqual(artifact._unix_time(True), True)
        self.assertEqual(artifact._unix_time(10 ** 20), 10 ** 20)


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

    def newer_pair(self, **tables):
        # The same database under both firmlinked paths, with an empty -wal beside one.
        for prefix in ('', 'System/Volumes/Data/'):
            exec_policy(os.path.join(self.image, prefix + CONFIG, 'ExecPolicy'), **tables)
        pathlib.Path(self.image, CONFIG, 'ExecPolicy-wal').write_bytes(b'')

    BOTH = 'System/Volumes/Data/' + CONFIG + '/ExecPolicy\n' + CONFIG + '/ExecPolicy'

    def test_scan_targets(self):
        self.newer_pair(targets=[('/Applications/Example.app', '/Applications/Example.app/Contents/MacOS/Example',
                                  0, 1, T0, 0),
                                 ('/Library/Tool', None, 1, 0, T0 - 60, T0 + 3600)])
        headers, rows, source = self.run_artifact(artifact.macosExecPolicyScanTargets)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Timestamp (UTC)', 'Measured Timestamp (UTC)', 'Path', 'Responsible Path',
                          'Is Library (as stored)', 'Is Used (as stored)', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2025, 12, 9, 21, 43, 51, tzinfo=UTC), datetime(2025, 12, 9, 22, 44, 51, tzinfo=UTC),
             '/Library/Tool', '', 1, 0, self.BOTH),
            # A measured timestamp of 0 is left blank.
            (datetime(2025, 12, 9, 21, 44, 51, tzinfo=UTC), '', '/Applications/Example.app',
             '/Applications/Example.app/Contents/MacOS/Example', 0, 1, self.BOTH)])
        self.assertEqual(len(source.split('\n')), 2)
        # The empty -wal beside one copy is not read as a database of its own.
        self.assertEqual(self.logged, [])
        # Both copies hold an empty scan cache: no rows, and no copy cited.
        _, rows, source = self.run_artifact(artifact.macosGatekeeperScanCache)
        self.assertEqual((rows, source), ([], ''))

    def test_measurements(self):
        self.newer_pair(measurements=[(T0, T0 + 86400, T0 - 86400, 'Example.app', 'Example.app/Contents/MacOS/Example',
                                       'com.example.app', '1.2', 'TEAM1', 'com.example.app', 'aa11', 'bb22',
                                       1024, 1, 1, 1, 0, 1)])
        headers, rows, _ = self.run_artifact(artifact.macosExecPolicyMeasurements)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Timestamp (UTC)', 'Reported Timestamp (UTC)', 'Executable Timestamp (UTC)',
                          'File Identifier', 'Responsible File Identifier', 'Bundle ID', 'Bundle Version',
                          'Team ID', 'Signing ID', 'CDHash', 'Main Executable Hash', 'File Size',
                          'Is Signed (as stored)', 'Is Valid (as stored)', 'Is Quarantined (as stored)',
                          'Is Library (as stored)', 'Is Used (as stored)', 'Source File'])
        self.assertEqual(rows, [(datetime(2025, 12, 9, 21, 44, 51, tzinfo=UTC), datetime(2025, 12, 10, 21, 44, 51, tzinfo=UTC),
                                 datetime(2025, 12, 8, 21, 44, 51, tzinfo=UTC), 'Example.app',
                                 'Example.app/Contents/MacOS/Example', 'com.example.app', '1.2', 'TEAM1',
                                 'com.example.app', 'aa11', 'bb22', 1024, 1, 1, 1, 0, 1, self.BOTH)])

    def test_scan_cache_across_layouts(self):
        # A macOS 15 layout under the usual path, and a macOS 11 layout (no top_policy_match or
        # matched_rule_name column, no provenance table) in a second extraction.
        exec_policy(os.path.join(self.image, CONFIG, 'ExecPolicy'), cache=[
            (T0, T0 + 5, T0 + 9, 'com.example.app', 'com.example.app', 'TEAM1', 'aa11', 9, 2, None, 1, 544,
             'apfs', 'VOL-1', 424348)])
        exec_policy(os.path.join(self.image, 'old', CONFIG, 'ExecPolicy'), newer=False, cache=[
            (T0 - 100, T0 - 100, T0 - 100, 'NOT_A_BUNDLE', None, 'TEAM2', 'cc33', 4, 0, 512, 'hfs', 'VOL-2', 19)])
        headers, rows, source = self.run_artifact(artifact.macosGatekeeperScanCache)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Timestamp (UTC)', 'Mod Time (UTC)', 'Revocation Check Time (UTC)', 'Bundle ID',
                          'Signing ID', 'Team ID', 'CDHash', 'Policy Match (as stored)',
                          'Top Policy Match (as stored)', 'Matched Rule Name', 'Malware Result (as stored)',
                          'Flags (as stored)', 'File System', 'Volume UUID', 'Object ID', 'Source File'])
        at = datetime(2025, 12, 9, 21, 43, 11, tzinfo=UTC)
        self.assertEqual(rows, [
            (at, at, at, 'NOT_A_BUNDLE', '', 'TEAM2', 'cc33', 4, '', '', 0, 512, 'hfs', 'VOL-2', 19,
             'old/' + CONFIG + '/ExecPolicy'),
            (datetime(2025, 12, 9, 21, 44, 51, tzinfo=UTC), datetime(2025, 12, 9, 21, 44, 56, tzinfo=UTC),
             datetime(2025, 12, 9, 21, 45, 0, tzinfo=UTC), 'com.example.app', 'com.example.app', 'TEAM1',
             'aa11', 9, 2, '', 1, 544, 'apfs', 'VOL-1', 424348, CONFIG + '/ExecPolicy')])
        self.assertEqual(len(source.split('\n')), 2)
        # Provenance: the older copy has no table, which is logged; the newer copy's is empty.
        # A copy that yields no rows is not cited as a source.
        _, rows, source = self.run_artifact(artifact.macosExecPolicyProvenance)
        self.assertEqual((rows, source), ([], ''))
        for function in (artifact.macosExecPolicyScanTargets, artifact.macosExecPolicyMeasurements):
            _, rows, source = self.run_artifact(function)
            self.assertEqual((rows, source), ([], ''), function.__name__)
        self.assertEqual(self.logged, ['ExecPolicy: no provenance_tracking table in old/' + CONFIG + '/ExecPolicy'])

    def test_provenance_links(self):
        self.newer_pair(provenance=[
            (T0, '/Applications/Example.app', 'com.example.app', 'com.example.app', 'TEAM1', 'aa11', 2,
             8292375719185805725, 0),
            (T0 + 20, '/Users/a/Library/Helper', 'NOT_A_BUNDLE', None, None, None, 2, -3355586806939820755,
             8292375719185805725),
            # A link key that names no row of this copy.
            (T0 + 30, '/tmp/other', 'NOT_A_BUNDLE', None, None, None, 2, 5, 7),
            # A row whose own key is 0: a Link PK of 0 must still mean no link.
            (T0 + 40, '/tmp/zero', 'NOT_A_BUNDLE', None, None, None, 2, 0, 5)])
        headers, rows, _ = self.run_artifact(artifact.macosExecPolicyProvenance)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Timestamp (UTC)', 'Path', 'Bundle ID', 'Signing ID', 'Team ID', 'CDHash',
                          'Flags (as stored)', 'PK', 'Link PK', 'Linked Path', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2025, 12, 9, 21, 44, 51, tzinfo=UTC), '/Applications/Example.app', 'com.example.app',
             'com.example.app', 'TEAM1', 'aa11', 2, 8292375719185805725, 0, '', self.BOTH),
            (datetime(2025, 12, 9, 21, 45, 11, tzinfo=UTC), '/Users/a/Library/Helper', 'NOT_A_BUNDLE', '', '', '', 2,
             -3355586806939820755, 8292375719185805725, '/Applications/Example.app', self.BOTH),
            (datetime(2025, 12, 9, 21, 45, 21, tzinfo=UTC), '/tmp/other', 'NOT_A_BUNDLE', '', '', '', 2, 5, 7, '',
             self.BOTH),
            (datetime(2025, 12, 9, 21, 45, 31, tzinfo=UTC), '/tmp/zero', 'NOT_A_BUNDLE', '', '', '', 2, 0, 5, '/tmp/other',
             self.BOTH)])

    def test_a_row_only_one_copy_holds_is_kept_with_its_copy(self):
        exec_policy(os.path.join(self.image, CONFIG, 'ExecPolicy'), targets=[('/A', None, 0, 1, T0, 0)])
        exec_policy(os.path.join(self.image, 'System/Volumes/Data', CONFIG, 'ExecPolicy'),
                    targets=[('/A', None, 0, 1, T0, 0), ('/B', None, 0, 1, T0 + 1, T0 + 2)])
        _, rows, _ = self.run_artifact(artifact.macosExecPolicyScanTargets)
        self.assertEqual([(r[2], r[-1]) for r in rows],
                         [('/A', self.BOTH), ('/B', 'System/Volumes/Data/' + CONFIG + '/ExecPolicy')])

    def test_declared_paths(self):
        for key in ('macosExecPolicyScanTargets', 'macosExecPolicyMeasurements', 'macosGatekeeperScanCache',
                    'macosExecPolicyProvenance'):
            for path in ('Macintosh HD - Data/' + CONFIG + '/ExecPolicy', 'r/' + CONFIG + '/ExecPolicy-wal',
                         'r/System/Volumes/Data/' + CONFIG + '/ExecPolicy'):
                self.assertTrue(any(fnmatch.fnmatch(path, p) for p in artifact.__artifacts_v2__[key]['paths']),
                                (key, path))
            self.assertEqual(key, getattr(artifact, key).__name__)


if __name__ == '__main__':
    unittest.main()
