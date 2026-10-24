"""Pin scripts/artifacts/macosAuthKit.py.

The databases below are built for the test with the two authorization.db schemas measured on
real files (db_version 8 on macOS 15.4, db_version 4 on macOS 11.2.1 and 14.6.1) and the
devicelist.db and privateEmails.db schemas measured on macOS 15.4. Every identifier, name and
value is invented; none comes from a real device.
"""
import fnmatch
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import macosAuthKit as akd  # pylint: disable=wrong-import-position

_AKD = pathlib.Path('Library', 'Application Support', 'com.apple.akd')

_AUTH_V8 = (
    'CREATE TABLE authorized_teams (team_id TEXT PRIMARY KEY, uid TEXT, '
    'authorizedAppListVersion TEXT, private_email TEXT)',
    'CREATE TABLE authorized_applications (client_id TEXT PRIMARY KEY, team_id TEXT, scopes TEXT, '
    'credential_state INTEGER, authorizedAppListVersion TEXT, transfer_state TEXT, '
    'primary_client_id TEXT, origin TEXT, creation_date INTEGER NOT NULL DEFAULT 0, client_name TEXT)',
    'CREATE TABLE version (authorizedAppListVersion TEXT PRIMARY KEY, db_version INTEGER)',
    'CREATE TABLE authorized_primary_applications (client_id TEXT PRIMARY KEY, app_name TEXT, '
    'app_developer_name TEXT, adam_id TEXT)',
)
_AUTH_V4 = (
    'CREATE TABLE authorized_teams (team_id TEXT PRIMARY KEY, uid TEXT, authorizedAppListVersion TEXT)',
    'CREATE TABLE authorized_applications (client_id TEXT PRIMARY KEY, team_id TEXT, scopes TEXT, '
    'credential_state INTEGER, authorizedAppListVersion TEXT, transfer_state TEXT, '
    'primary_client_id TEXT, origin TEXT)',
    'CREATE TABLE version (authorizedAppListVersion TEXT PRIMARY KEY, db_version INTEGER)',
)
_DEVICES = (
    'CREATE TABLE device_list (mid TEXT PRIMARY KEY, name TEXT, serial_number TEXT, model TEXT, '
    'os TEXT, os_version TEXT, dc TEXT, clcg TEXT, clbg TEXT, clhs TEXT, dec TEXT, '
    'circle_status INTEGER, build_number TEXT, trusted INTEGER, last_updated_date DOUBLE, '
    'additional_info BLOB, altDSID TEXT, services TEXT, last_cache_updated_date DOUBLE)',
    'CREATE TABLE deleted_device_list (mid TEXT PRIMARY KEY, reason INTEGER, '
    'last_updated_date DOUBLE, altDSID TEXT, deleted_date DOUBLE)',
    'CREATE TABLE version (db_version INTEGER PRIMARY KEY)',
)
_EMAILS = (
    'CREATE TABLE version (privateEmailListVersion TEXT PRIMARY KEY, db_version INTEGER, '
    'protocol_version INTEGER)',
    'CREATE TABLE emails (client_key TEXT PRIMARY KEY, email TEXT)',
)

T1 = 1700000000.5
T2 = 1700003600.25


def utc(seconds):
    """The whole seconds the core converter keeps."""
    return datetime.fromtimestamp(int(seconds), timezone.utc)


def build(path, schema, inserts):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    for statement in schema:
        connection.execute(statement)
    for statement, values in inserts:
        connection.execute(statement, values)
    connection.commit()
    connection.close()
    return path


def auth_v8(path):
    return build(path, _AUTH_V8, [
        ('INSERT INTO authorized_teams VALUES (?, ?, ?, ?)', ('TEAM000001', 'uid.one', None, 'relay@example.test')),
        ('INSERT INTO authorized_teams VALUES (?, ?, ?, ?)', ('TEAM000002', 'uid.two', None, None)),
        ('INSERT INTO authorized_applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
         ('com.example.app', 'TEAM000001', 'email,name', 1, 'v', 'NULL', 'NULL', '0', T1, 'Example App')),
        ('INSERT INTO authorized_applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
         ('com.example.web', 'TEAM000001', 'email', 1, 'v', 'NULL', 'com.example.app', '0', T2, 'Example Web')),
        ('INSERT INTO authorized_applications (client_id, team_id, scopes, credential_state) '
         'VALUES (?, ?, ?, ?)', ('com.example.nodate', 'TEAM000001', 'name', 2)),
        ('INSERT INTO authorized_primary_applications VALUES (?, ?, ?, ?)',
         ('com.example.app', 'Example', 'Example Developer', '100000001')),
    ])


def devices(path, extra=False):
    rows = [
        ('INSERT INTO device_list VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
         ('mid-phone', 'Test Phone', 'SERIAL0001', 'iPhone0,0', 'iOS', '1.0', '1', '1', '0', '2', '2', 0,
          'BUILD1', 1, T1, b'{"phones":[{"imei":"000000000000001","slotID":1}]}', 'alt-1',
          'icloud', T2)),
    ]
    if extra:
        rows.append(
            ('INSERT INTO device_list (mid, name, trusted, last_updated_date, additional_info) '
             'VALUES (?, ?, ?, ?, ?)', ('mid-mac', 'Test Mac', 0, T2, b'{}')))
    rows.append(('INSERT INTO deleted_device_list VALUES (?, ?, ?, ?, ?)', ('mid-gone', 3, T1, 'alt-1', T2)))
    return build(path, _DEVICES, rows)


class Context:
    """The two calls the artifact makes, over a temporary tree."""

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class PathsTest(unittest.TestCase):
    """The declared globs, matched the way the seekers match them (synthetic root/ prefix)."""

    def matches(self, artifact, relative):
        return [p for p in akd.__artifacts_v2__[artifact]['paths']
                if fnmatch.fnmatchcase('root/' + relative, p)]

    def test_each_database_and_its_sidecars_match_once(self):
        for artifact, name in (('macosAuthKitAuthorizedApps', 'authorization.db'),
                               ('macosAppleAccountDevices', 'devicelist.db'),
                               ('macosAppleAccountDeletedDevices', 'devicelist.db'),
                               ('macosAuthKitPrivateEmails', 'privateEmails.db')):
            for suffix in ('', '-wal', '-shm'):
                relative = str(pathlib.Path('Users', 'alice')/_AKD/(name + suffix))
                with self.subTest(artifact=artifact, relative=relative):
                    self.assertEqual(len(self.matches(artifact, relative)), 1)

    def test_other_folders_do_not_match(self):
        for relative in ('Users/alice/Library/Application Support/com.apple.akd.old/authorization.db',
                         'Users/alice/Library/Caches/com.apple.akd/Cache.db',
                         'Users/alice/Library/Application Support/com.apple.akd/other.db'):
            with self.subTest(relative=relative):
                self.assertEqual(self.matches('macosAuthKitAuthorizedApps', relative), [])


class HomeLibraryTest(unittest.TestCase):
    def test_home_and_root_libraries_are_read(self):
        for relative in ('Users/alice/Library/Application Support/com.apple.akd/devicelist.db',
                         'System/Volumes/Data/Users/alice/Library/Application Support/com.apple.akd/devicelist.db',
                         'private/var/root/Library/Application Support/com.apple.akd/devicelist.db',
                         'Library/Application Support/com.apple.akd/devicelist.db'):
            with self.subTest(relative=relative):
                self.assertTrue(akd._in_a_home_library(relative))  # pylint: disable=protected-access

    def test_a_library_nested_in_another_is_not(self):
        relative = ('Users/alice/Library/Containers/com.example.app/Data/Library/Application Support/'
                    'com.apple.akd/devicelist.db')
        self.assertFalse(akd._in_a_home_library(relative))  # pylint: disable=protected-access


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target in (akd, macos_plists):
            patcher = patch.object(target, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def home(self, user, name, view=()):
        return self.root.joinpath(*view, 'Users', user, _AKD, name)

    def decoy(self, name):
        return self.root/'Users'/'alice'/'Library'/'Containers'/'com.example.decoy'/'Data'/_AKD/name

    def test_authorized_apps_both_schemas_users_views_and_decoy(self):
        alice = auth_v8(self.home('alice', 'authorization.db'))
        alice_view = auth_v8(self.home('alice', 'authorization.db', ('System', 'Volumes', 'Data')))
        bob = build(self.home('bob', 'authorization.db'), _AUTH_V4, [
            ('INSERT INTO authorized_teams VALUES (?, ?, ?)', ('TEAM000003', 'uid.three', None)),
            ('INSERT INTO authorized_applications VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
             ('com.example.old', 'TEAM000003', 'email', 1, 'v', 'NULL', 'NULL', '0')),
        ])
        decoy = auth_v8(self.decoy('authorization.db'))
        headers, rows, source = akd.macosAuthKitAuthorizedApps.__wrapped__(
            Context(self.root, [alice, alice_view, bob, decoy]))
        self.assertEqual(len(headers), 16)
        alice_file = str(pathlib.Path('Users', 'alice')/_AKD/'authorization.db')
        bob_file = str(pathlib.Path('Users', 'bob')/_AKD/'authorization.db')
        self.assertEqual(sorted(rows, key=lambda r: (r[14], r[7], r[2])), [
            (utc(T1), 'Example App', 'com.example.app', 'Example', 'Example Developer', '100000001',
             'NULL', 'TEAM000001', 'uid.one', 'relay@example.test', 'email,name', '1', 'NULL', '0',
             'alice', alice_file),
            ('', '', 'com.example.nodate', '', '', '', '', 'TEAM000001', 'uid.one', 'relay@example.test',
             'name', '2', '', '', 'alice', alice_file),
            (utc(T2), 'Example Web', 'com.example.web', 'Example', 'Example Developer', '100000001',
             'com.example.app', 'TEAM000001', 'uid.one', 'relay@example.test', 'email', '1', 'NULL', '0',
             'alice', alice_file),
            ('', '', '', '', '', '', '', 'TEAM000002', 'uid.two', '', '', '', '', '', 'alice', alice_file),
            ('', '', 'com.example.old', '', '', '', 'NULL', 'TEAM000003', 'uid.three', '', 'email', '1',
             'NULL', '0', 'bob', bob_file),
        ])
        self.assertEqual(sorted(source.split('\n')), sorted([str(alice), str(bob)]))
        self.assertTrue(any('com.example.decoy' in line and 'not read' in line for line in self.logged))
        self.assertTrue(any('byte-identical' in line for line in self.logged))

    def test_devices_deleted_devices_and_users(self):
        alice = devices(self.home('alice', 'devicelist.db'), extra=True)
        bob = devices(self.home('bob', 'devicelist.db'))
        decoy = devices(self.decoy('devicelist.db'))
        context = Context(self.root, [alice, bob, decoy])
        headers, rows, _source = akd.macosAppleAccountDevices.__wrapped__(context)
        self.assertEqual(len(headers), 22)
        self.assertEqual(sorted((r[2], r[20]) for r in rows),
                         [('Test Mac', 'alice'), ('Test Phone', 'alice'), ('Test Phone', 'bob')])
        phone = next(r for r in rows if r[2] == 'Test Phone' and r[20] == 'alice')
        self.assertEqual(phone[:12], (utc(T1), utc(T2), 'Test Phone', 'iPhone0,0', 'iOS', '1.0', 'BUILD1',
                                      'SERIAL0001', '000000000000001', 'Yes', '0', 'icloud'))
        mac = next(r for r in rows if r[2] == 'Test Mac')
        self.assertEqual((mac[0], mac[1], mac[8], mac[9], mac[19]), (utc(T2), '', '', 'No', '{}'))
        headers, rows, _source = akd.macosAppleAccountDeletedDevices.__wrapped__(context)
        self.assertEqual(len(headers), 7)
        self.assertEqual(sorted(r[5] for r in rows), ['alice', 'bob'])
        self.assertEqual({r[:5] for r in rows}, {(utc(T2), utc(T1), '3', 'mid-gone', 'alt-1')})

    def test_private_emails(self):
        path = build(self.home('alice', 'privateEmails.db'), _EMAILS, [
            ('INSERT INTO emails VALUES (?, ?)', ('key-1', 'alias@example.test')),
        ])
        headers, rows, source = akd.macosAuthKitPrivateEmails.__wrapped__(Context(self.root, [path]))
        self.assertEqual(headers, ('Email', 'Client Key', 'User', 'Source File'))
        self.assertEqual(rows, [('alias@example.test', 'key-1', 'alice',
                                 str(pathlib.Path('Users', 'alice')/_AKD/'privateEmails.db'))])
        self.assertEqual(source, str(path))

    def test_missing_table_is_logged_and_not_cited(self):
        path = build(self.home('alice', 'devicelist.db'), ('CREATE TABLE version (db_version INTEGER)',), [])
        _headers, rows, source = akd.macosAppleAccountDevices.__wrapped__(Context(self.root, [path]))
        self.assertEqual((rows, source), ([], ''))
        self.assertTrue(any('no device_list table' in line for line in self.logged))


if __name__ == '__main__':
    unittest.main()
