"""Pin the Google Drive for desktop artifacts in scripts/artifacts/googleDriveFS.py.

Every database below is built by the test with the columns a DriveFS profile carries; no row comes
from a real account. Expected values are literals.
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

from scripts.artifacts import googleDriveFS as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
DRIVEFS = 'Users/pat/Library/Application Support/Google/DriveFS/'
ACCOUNT = '100200300400500600700'
ITEMS = ('CREATE TABLE items (stable_id INTEGER PRIMARY KEY NOT NULL, id TEXT UNIQUE NOT NULL, proto BLOB, '
         'trashed BOOLEAN NOT NULL, starred BOOLEAN NOT NULL, is_owner BOOLEAN NOT NULL, mime_type TEXT NOT NULL, '
         'is_folder BOOLEAN NOT NULL, modified_date INTEGER, shared_with_me_date INTEGER, viewed_by_me_date INTEGER, '
         'file_size INTEGER, is_tombstone BOOLEAN NOT NULL, local_title TEXT)')
PARENTS = 'CREATE TABLE stable_parents (item_stable_id INTEGER NOT NULL, parent_stable_id INTEGER NOT NULL, local_title_hash INTEGER NOT NULL)'
SHORTCUTS = 'CREATE TABLE shortcut_details (shortcut_stable_id INTEGER PRIMARY KEY NOT NULL, target_stable_id INTEGER NOT NULL, target_mime_type TEXT NOT NULL)'
ITEM_ROW = ('INSERT INTO items (stable_id, id, trashed, starred, is_owner, mime_type, is_folder, modified_date, '
            'shared_with_me_date, viewed_by_me_date, file_size, is_tombstone, local_title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)')
FOLDER, DOC, SHORTCUT = 'application/vnd.google-apps.folder', 'application/vnd.google-apps.document', 'application/vnd.google-apps.shortcut'
MIRROR = ('CREATE TABLE mirror_item (local_stable_id INTEGER PRIMARY KEY, stable_id INTEGER, inode INTEGER, volume TEXT, '
          'parent_local_stable_id INTEGER, local_filename TEXT, cloud_filename TEXT, local_mtime_ms INTEGER, cloud_mtime_ms INTEGER, '
          'local_md5_checksum TEXT, cloud_md5_checksum TEXT, local_size INTEGER, cloud_size INTEGER, local_type INTEGER, '
          'cloud_type INTEGER, local_version INTEGER, cloud_version INTEGER, storage_policy INTEGER, shared INTEGER, '
          'read_only INTEGER, target_version INTEGER, is_root INTEGER)')
MIRROR_ROW = ('INSERT INTO mirror_item (local_stable_id, inode, volume, parent_local_stable_id, local_filename, cloud_filename, '
              'local_mtime_ms, cloud_mtime_ms, local_md5_checksum, cloud_md5_checksum, local_size, cloud_size, shared, is_root) '
              'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
ROOTS = ('CREATE TABLE roots (root_id INTEGER PRIMARY KEY, metadata BLOB, media_id TEXT, title TEXT, root_path TEXT, '
         'account_token TEXT, sync_type INTEGER, destination INTEGER, medium INTEGER, state INTEGER, one_shot INTEGER, '
         'is_my_drive INTEGER, doc_id TEXT, last_seen_absolute_path TEXT)')
MEDIA = ('CREATE TABLE media (media_id TEXT PRIMARY KEY, name TEXT, last_mount_point TEXT, fs_type INTEGER, '
         'device_type INTEGER, capacity INTEGER, ignored INTEGER)')
VOLUME = '2EB8446E-FC09-483F-942F-B96C359EF8B7'


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root) for name in names)


class DriveFSCase(unittest.TestCase):
    """Setup and database building shared by the test classes below."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged = []
        for module in (artifact, sys.modules['scripts.macos_plists']):
            patcher = patch.object(module, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def database(self, relative, statements):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with sqlite3.connect(path) as db:
            for statement, *rows in statements:
                if rows:
                    db.executemany(statement, rows)
                else:
                    db.execute(statement)
        db.close()
        return path


class ArtifactTest(DriveFSCase):
    def run_items(self, extra=()):
        return artifact.googleDriveItems.__wrapped__(Context(self.root, walk(self.root) + list(extra)))

    def run_mirrored(self, extra=()):
        return artifact.googleDriveMirroredItems.__wrapped__(Context(self.root, walk(self.root) + list(extra)))

    def metadata(self, relative, extra_items=()):
        return self.database(relative, [
            (ITEMS,), (PARENTS,), (SHORTCUTS,),
            (ITEM_ROW,
             (101, '0Aroot', 0, 0, 1, FOLDER, 1, 1764624670658, None, None, 0, 'My Drive'),
             (102, '1shared', 0, 0, 0, FOLDER, 1, 1765227815673, 1764624817097, 1764625469221, 0, 'Shared Folder'),
             (103, '1pdf', 1, 1, 1, 'application/pdf', 0, 1764625246000, 0, 1764625567338, 787954, 'form.pdf'),
             (104, '1doc', 0, 0, 0, DOC, 0, 1765487388350, 1765315336510, 1765391357496, 2311, 'Notes.gdoc'),
             (107, '1link', 0, 0, 1, SHORTCUT, 0, 1765317928147, None, 1765317928147, 0, 'Notes.gdoc'),
             *extra_items),
            ('INSERT INTO stable_parents VALUES (?, ?, 0)', (103, 102), (104, 102), (107, 101), (108, 999)),
            ('INSERT INTO shortcut_details VALUES (?, ?, ?)', (107, 104, DOC))])

    def test_items(self):
        where = DRIVEFS + ACCOUNT + '/metadata_sqlite_db'
        self.metadata(where, [(108, '1orphan', 0, 0, 1, 'text/plain', 0, 1765000000000, None, None, 5, 'lost.txt')])
        headers, rows, source = self.run_items()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Modified (UTC)', 'Viewed by Me (UTC)', 'Shared with Me (UTC)', 'Name', 'Path', 'MIME Type',
                          'Folder (as stored)', 'Size (as stored)', 'Owned by Account (as stored)', 'Trashed (as stored)',
                          'Starred (as stored)', 'Shortcut Target', 'Drive ID', 'Account ID', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2025, 12, 1, 21, 31, 10, 658000, tzinfo=UTC), '', '', 'My Drive', 'My Drive', FOLDER, 1, 0, 1, 0, 0,
             '', '0Aroot', ACCOUNT, where),
            # A shared_with_me_date of 0 is blank, like a NULL one.
            (datetime(2025, 12, 1, 21, 40, 46, tzinfo=UTC), datetime(2025, 12, 1, 21, 46, 7, 338000, tzinfo=UTC), '',
             'form.pdf', 'Shared Folder/form.pdf', 'application/pdf', 0, 787954, 1, 1, 1, '', '1pdf', ACCOUNT, where),
            # Its parent is not in items.
            (datetime(2025, 12, 6, 5, 46, 40, tzinfo=UTC), '', '', 'lost.txt', '(stable_id 999)/lost.txt', 'text/plain', 0, 5,
             1, 0, 0, '', '1orphan', ACCOUNT, where),
            (datetime(2025, 12, 8, 21, 3, 35, 673000, tzinfo=UTC), datetime(2025, 12, 1, 21, 44, 29, 221000, tzinfo=UTC),
             datetime(2025, 12, 1, 21, 33, 37, 97000, tzinfo=UTC), 'Shared Folder', 'Shared Folder', FOLDER, 1, 0, 0, 0, 0,
             '', '1shared', ACCOUNT, where),
            (datetime(2025, 12, 9, 22, 5, 28, 147000, tzinfo=UTC), datetime(2025, 12, 9, 22, 5, 28, 147000, tzinfo=UTC), '',
             'Notes.gdoc', 'My Drive/Notes.gdoc', SHORTCUT, 0, 0, 1, 0, 0, 'Notes.gdoc', '1link', ACCOUNT, where),
            (datetime(2025, 12, 11, 21, 9, 48, 350000, tzinfo=UTC), datetime(2025, 12, 10, 18, 29, 17, 496000, tzinfo=UTC),
             datetime(2025, 12, 9, 21, 22, 16, 510000, tzinfo=UTC), 'Notes.gdoc', 'Shared Folder/Notes.gdoc', DOC, 0, 2311, 0,
             0, 0, '', '1doc', ACCOUNT, where)])
        self.assertEqual(source, os.path.join(self.root, where))
        self.assertEqual(self.logged, [])

    def test_items_in_both_databases_and_copies(self):
        folder = DRIVEFS + ACCOUNT + '/'
        self.metadata(folder + 'metadata_sqlite_db')
        # The mirror database holds one item the same and one with a different title.
        self.database(folder + 'mirror_metadata_sqlite.db', [
            (ITEMS,), (PARENTS,),
            (ITEM_ROW, (5, '0Aroot', 0, 0, 1, FOLDER, 1, 1764624670658, None, None, 0, 'My Drive'),
             (6, '1doc', 0, 0, 0, DOC, 0, 1765487388350, 1765315336510, 1765391357496, 2311, 'Notes'))])
        # A byte-identical copy under System/Volumes/Data is not read again.
        copy = os.path.join(self.root, 'System/Volumes/Data', folder)
        os.makedirs(copy)
        shutil.copy(os.path.join(self.root, folder, 'metadata_sqlite_db'), copy)
        # A database without an items table, and a sidecar, are not item databases.
        self.database('Users/sam/Library/Application Support/Google/DriveFS/1/metadata_sqlite_db', [('CREATE TABLE other (a)',)])
        with open(os.path.join(self.root, folder, 'metadata_sqlite_db-wal'), 'wb'):
            pass
        _, rows, _ = self.run_items()
        both = f'{folder}metadata_sqlite_db\n{folder}mirror_metadata_sqlite.db'
        self.assertEqual([(r[3], r[4], r[-1]) for r in rows if r[12] in ('0Aroot', '1doc')], [
            ('My Drive', 'My Drive', both),
            ('Notes.gdoc', 'Shared Folder/Notes.gdoc', folder + 'metadata_sqlite_db'),
            ('Notes', 'Notes', folder + 'mirror_metadata_sqlite.db')])
        self.assertEqual(sorted(self.logged), sorted([
            'Google Drive Items: 1 byte-identical copy(ies) under System/Volumes/Data not read again',
            'Google Drive Items: no items table in Users/sam/Library/Application Support/Google/DriveFS/1/metadata_sqlite_db']))

    def test_mirrored_items(self):
        folder = DRIVEFS + ACCOUNT + '/'
        self.database(folder + 'mirror_sqlite.db', [
            (MIRROR,), ('CREATE TABLE root_config (root_id INTEGER PRIMARY KEY, root_state INTEGER, local_stable_id INTEGER, '
                        'item_id TEXT, is_my_drive INTEGER)',),
            (MIRROR_ROW, (1, 428598, VOLUME, -1, 'Work', 'Work', 1765316828105, 1765317030598, '', '', 0, 0, 0, 1),
             (2, 477000, VOLUME, 1, 'Notes.gdoc', 'Notes', 1765487388350, 1765487388350, '5db6350f5eee4601fca6a9c9cce79a24',
              '', 183, 2311, 1, 0),
             # A second root that no root_preference row for this account names.
             (3, 11, 'OTHER-VOLUME', -1, 'Photos', 'Photos', 1765000000000, 0, '', 'aa', 0, 0, 0, 1),
             (4, 12, 'OTHER-VOLUME', 3, 'cat.jpg', 'cat.jpg', 1765000001000, 1765000002000, 'bb', 'bb', 10, 10, 0, 0)),
            ('INSERT INTO root_config VALUES (?, ?, ?, NULL, 0)', (1, 1, 1), (2, 1, 3))])
        self.database(DRIVEFS + 'root_preference_sqlite.db', [
            (ROOTS,), (MEDIA,),
            ('INSERT INTO roots (root_id, media_id, title, root_path, account_token, last_seen_absolute_path) VALUES (?, ?, ?, ?, ?, ?)',
             (1, VOLUME, 'Work', 'Users/pat/Documents/Work', ACCOUNT, '/Users/pat/Documents/Work'),
             (2, 'OTHER-VOLUME', 'Photos', 'Photos', '999', '/Volumes/Other/Photos')),
            ('INSERT INTO media (media_id, name, last_mount_point) VALUES (?, ?, ?)', (VOLUME, 'Macintosh HD - Data', '/'))])
        headers, rows, source = self.run_mirrored()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Local Modified (UTC)', 'Cloud Modified (UTC)', 'Local Name', 'Cloud Name', 'Local Path', 'Local MD5',
                          'Cloud MD5', 'Local Size', 'Cloud Size', 'Shared (as stored)', 'Volume', 'Inode (as stored)',
                          'Account ID', 'Source File'])
        where = folder + 'mirror_sqlite.db'
        self.assertEqual(rows, [
            # The root of another account keeps its own name as the top of the path, and its volume ID as stored.
            (datetime(2025, 12, 6, 5, 46, 40, tzinfo=UTC), '', 'Photos', 'Photos', 'Photos', '', 'aa', 0, 0, 0,
             'OTHER-VOLUME', 11, ACCOUNT, where),
            (datetime(2025, 12, 6, 5, 46, 41, tzinfo=UTC), datetime(2025, 12, 6, 5, 46, 42, tzinfo=UTC), 'cat.jpg', 'cat.jpg',
             'Photos/cat.jpg', 'bb', 'bb', 10, 10, 0, 'OTHER-VOLUME', 12, ACCOUNT, where),
            (datetime(2025, 12, 9, 21, 47, 8, 105000, tzinfo=UTC), datetime(2025, 12, 9, 21, 50, 30, 598000, tzinfo=UTC),
             'Work', 'Work', '/Users/pat/Documents/Work', '', '', 0, 0, 0, 'Macintosh HD - Data', 428598, ACCOUNT, where),
            (datetime(2025, 12, 11, 21, 9, 48, 350000, tzinfo=UTC), datetime(2025, 12, 11, 21, 9, 48, 350000, tzinfo=UTC),
             'Notes.gdoc', 'Notes', '/Users/pat/Documents/Work/Notes.gdoc', '5db6350f5eee4601fca6a9c9cce79a24', '', 183, 2311,
             1, 'Macintosh HD - Data', 477000, ACCOUNT, where)])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.root, p) for p in
                                                            (where, DRIVEFS + 'root_preference_sqlite.db')))

    def test_mirrored_items_without_preferences(self):
        folder = DRIVEFS + ACCOUNT + '/'
        self.database(folder + 'mirror_sqlite.db', [
            (MIRROR,), (MIRROR_ROW, (1, 1, VOLUME, -1, 'Work', 'Work', 1765316828105, 0, '', '', 0, 0, 0, 1),
                        (2, 2, VOLUME, 1, 'a.txt', 'a.txt', 1765316829105, 0, 'cc', '', 1, 1, 0, 0))])
        self.database('Users/sam/Library/Application Support/Google/DriveFS/2/mirror_sqlite.db', [('CREATE TABLE other (a)',)])
        _, rows, source = self.run_mirrored()
        self.assertEqual([(r[4], r[10]) for r in rows], [('Work', VOLUME), ('Work/a.txt', VOLUME)])
        self.assertEqual(source, os.path.join(self.root, folder + 'mirror_sqlite.db'))
        self.assertEqual(self.logged, [
            'Google Drive Mirrored Items: no mirror_item table in Users/sam/Library/Application Support/Google/DriveFS/2/mirror_sqlite.db'])

    def test_mirrored_root_without_an_absolute_path(self):
        folder = DRIVEFS + ACCOUNT + '/'
        self.database(folder + 'mirror_sqlite.db', [
            (MIRROR,), ('CREATE TABLE root_config (root_id INTEGER PRIMARY KEY, root_state INTEGER, local_stable_id INTEGER, '
                        'item_id TEXT, is_my_drive INTEGER)',),
            (MIRROR_ROW, (1, 1, VOLUME, -1, 'Work', 'Work', 1765316828105, 0, '', '', 0, 0, 0, 1),
             (2, 2, VOLUME, 1, 'a.txt', 'a.txt', 1765316829105, 0, 'cc', '', 1, 1, 0, 0)),
            ('INSERT INTO root_config VALUES (1, 1, 1, NULL, 0)',)])
        self.database(DRIVEFS + 'root_preference_sqlite.db', [
            (ROOTS,), (MEDIA,),
            ('INSERT INTO roots (root_id, media_id, title, root_path, account_token, last_seen_absolute_path) VALUES (?, ?, ?, ?, ?, ?)',
             (1, VOLUME, 'Work', 'Users/pat/Documents/Work', ACCOUNT, ''))])
        _, rows, _ = self.run_mirrored()
        # The root keeps its own name; root_path is not turned into an absolute path.
        self.assertEqual([r[4] for r in rows], ['Work', 'Work/a.txt'])

    def test_paths_with_a_loop(self):
        self.assertEqual(artifact._paths(1, {1: [2], 2: [1]}, {1: 'a', 2: 'b'}), ['b/a'])  # pylint: disable=protected-access
        self.assertEqual(artifact._paths(1, {1: [2, 3]}, {1: 'a', 2: 'b', 3: 'c'}), ['b/a', 'c/a'])  # pylint: disable=protected-access

    def test_declared_paths(self):
        items = artifact.__artifacts_v2__['googleDriveItems']['paths']
        mirrored = artifact.__artifacts_v2__['googleDriveMirroredItems']['paths']
        for member in (DRIVEFS + ACCOUNT + '/metadata_sqlite_db', DRIVEFS + ACCOUNT + '/mirror_metadata_sqlite.db-wal',
                       'Users/pat/AppData/Local/Google/DriveFS/' + ACCOUNT + '/metadata_sqlite_db'):
            self.assertTrue(any(fnmatch.fnmatch(member, pattern) for pattern in items), member)
        for member in (DRIVEFS + ACCOUNT + '/mirror_sqlite.db', DRIVEFS + 'root_preference_sqlite.db'):
            self.assertTrue(any(fnmatch.fnmatch(member, pattern) for pattern in mirrored), member)
        self.assertFalse(any(fnmatch.fnmatch(DRIVEFS + 'metadata_sqlite_db', pattern) for pattern in items))


OTHER = '111222333444555666777'
PHENOTYPE = 'CREATE TABLE PhenotypeValues(Key TEXT PRIMARY KEY NOT NULL, Value BLOB NOT NULL)'
PROPERTIES = 'CREATE TABLE properties (property TEXT PRIMARY KEY, value)'
AUTHORIZED = ('{} [12345:CrBrowserMain] client.cc:1027:StartAccountAuthComplete Authorized as {} ({})\n')


def varint(value):
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def field(number, payload):
    """One protobuf field: a varint for an int, length-delimited bytes otherwise."""
    if isinstance(payload, int):
        return varint(number << 3) + varint(payload)
    return varint(number << 3 | 2) + varint(len(payload)) + payload


def driveway(account, name, email, photo):
    inner = field(1, 1) + field(2, account.encode()) + field(3, name.encode()) + field(5, photo.encode()) + field(8, email.encode())
    return field(1, 0) + field(2, field(1, inner) + field(3, field(1, field(1, 15000000000)))) + field(5, 0)


class AccountsTest(DriveFSCase):
    def run_accounts(self):
        return artifact.googleDriveAccounts.__wrapped__(Context(self.root, walk(self.root)))

    def experiments(self, folder, account_ids, last_sync=b'1766612931'):
        rows = [('account_ids', account_ids)] if account_ids is not None else []
        rows.append(('last_sync', last_sync))
        rows.append(('registered_package/drive_fs_ph', b'\n\x0bdrive_fs_ph'))
        return self.database(folder + 'experiments.db', [(PHENOTYPE,), ('INSERT INTO PhenotypeValues VALUES (?, ?)', *rows)])

    def account_database(self, relative, prop, value):
        return self.database(relative, [(ITEMS,), (PROPERTIES,),
                                        ('INSERT INTO properties VALUES (?, ?)', (prop, value), ('cache_type', 0))])

    def test_accounts(self):
        pat = driveway(ACCOUNT, 'Pat Doe', 'pat@example.com', 'https://example.com/pat.png')
        self.experiments(DRIVEFS, field(1, ACCOUNT.encode()) + field(1, OTHER.encode()))
        folder = DRIVEFS + ACCOUNT + '/'
        self.account_database(folder + 'metadata_sqlite_db', 'driveway_account', pat)
        self.account_database(folder + 'mirror_metadata_sqlite.db', 'driveway_account', pat)
        # A byte-identical copy of experiments.db under System/Volumes/Data is not read again.
        copy = os.path.join(self.root, 'System/Volumes/Data', DRIVEFS)
        os.makedirs(copy)
        shutil.copy(os.path.join(self.root, DRIVEFS, 'experiments.db'), copy)
        # Another user's DriveFS folder: no experiments.db, an account database present only under
        # System/Volumes/Data, and no driveway_account record in it (a record named account is not read).
        sam = 'Users/sam/Library/Application Support/Google/DriveFS/'
        record = field(1, field(3, b'Sam Roe') + field(5, b'https://example.com/sam.png') + field(8, b'sam@example.com'))
        self.account_database('System/Volumes/Data/' + sam + '222333444555666777888/metadata_sqlite_db', 'account', record)
        headers, rows, source = self.run_accounts()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['experiments.db last_sync (UTC)', 'Account ID', 'Name', 'Email', 'Photo URL',
                          'Listed in account_ids', 'Account Database Found', 'Source File'])
        synced = datetime(2025, 12, 24, 21, 48, 51, tzinfo=UTC)
        self.assertEqual(rows, [
            (synced, ACCOUNT, 'Pat Doe', 'pat@example.com', 'https://example.com/pat.png', 'Yes', 'Yes',
             f'{folder}metadata_sqlite_db\n{folder}mirror_metadata_sqlite.db\n{DRIVEFS}experiments.db'),
            # Listed and without an account database.
            (synced, OTHER, '', '', '', 'Yes', 'No', DRIVEFS + 'experiments.db'),
            # No driveway_account record: blank; no experiments.db leaves Listed blank.
            ('', '222333444555666777888', '', '', '', '', 'Yes',
             'System/Volumes/Data/' + sam + '222333444555666777888/metadata_sqlite_db')])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.root, p) for p in (
            DRIVEFS + 'experiments.db', folder + 'metadata_sqlite_db', folder + 'mirror_metadata_sqlite.db',
            'System/Volumes/Data/' + sam + '222333444555666777888/metadata_sqlite_db')))
        self.assertEqual(self.logged, [
            'Google Drive Accounts (experiments.db): 1 byte-identical copy(ies) under System/Volumes/Data not read again'])

    def test_differing_records_give_a_row_each(self):
        self.experiments(DRIVEFS, field(1, ACCOUNT.encode()))
        folder = DRIVEFS + ACCOUNT + '/'
        self.account_database(folder + 'metadata_sqlite_db', 'driveway_account',
                              driveway(ACCOUNT, 'Pat Doe', 'pat@example.com', 'https://example.com/pat.png'))
        # The same account message with extra fields elsewhere in the record is one row; a different name is another.
        self.account_database(folder + 'mirror_metadata_sqlite.db', 'driveway_account',
                              driveway(ACCOUNT, 'Pat Doe', 'pat@example.com', 'https://example.com/pat.png') + field(9, b'extra'))
        _, rows, _ = self.run_accounts()
        self.assertEqual([(row[2], row[-1]) for row in rows], [
            ('Pat Doe', f'{folder}metadata_sqlite_db\n{folder}mirror_metadata_sqlite.db\n{DRIVEFS}experiments.db')])
        self.account_database('System/Volumes/Data/' + folder + 'metadata_sqlite_db', 'driveway_account',
                              driveway(ACCOUNT, 'Pat Roe', 'pat@example.com', 'https://example.com/pat.png'))
        _, rows, _ = self.run_accounts()
        self.assertEqual([(row[2], row[-1]) for row in rows], [
            ('Pat Doe', f'{folder}metadata_sqlite_db\n{folder}mirror_metadata_sqlite.db\n{DRIVEFS}experiments.db'),
            ('Pat Roe', f'System/Volumes/Data/{folder}metadata_sqlite_db\n{DRIVEFS}experiments.db')])

    def test_accounts_joined_across_views_and_unreadable_records(self):
        # experiments.db under Users/, its account database only under System/Volumes/Data/: one folder.
        self.experiments(DRIVEFS, field(1, ACCOUNT.encode()), last_sync=b'not a number')
        self.account_database('System/Volumes/Data/' + DRIVEFS + ACCOUNT + '/metadata_sqlite_db', 'driveway_account',
                              b'\x12\x02\x08\x01')
        sam = 'Users/sam/Library/Application Support/Google/DriveFS/'
        self.experiments(sam, b'\x0a\x05ab', last_sync=b'1766612931')
        self.account_database(sam + OTHER + '/metadata_sqlite_db', 'driveway_account',
                              driveway(OTHER, 'Sam Roe', 'sam@example.com', 'https://example.com/sam.png'))
        _, rows, _ = self.run_accounts()
        self.assertEqual([row[:7] for row in rows], [
            ('', ACCOUNT, '', '', '', 'Yes', 'Yes'),
            (datetime(2025, 12, 24, 21, 48, 51, tzinfo=UTC), OTHER, 'Sam Roe', 'sam@example.com',
             'https://example.com/sam.png', '', 'Yes')])
        self.assertEqual(sorted(self.logged), sorted([
            f'Google Drive Accounts: account_ids in {sam}experiments.db not read: field runs past the end of the message',
            f'Google Drive Accounts: driveway_account in System/Volumes/Data/{DRIVEFS}{ACCOUNT}/metadata_sqlite_db not '
            'read: no message in field 1']))


    def test_accounts_from_two_differing_copies_of_experiments(self):
        self.experiments(DRIVEFS, field(1, ACCOUNT.encode()))
        self.experiments('System/Volumes/Data/' + DRIVEFS, field(1, ACCOUNT.encode()), last_sync=b'1766612000')
        self.account_database(DRIVEFS + ACCOUNT + '/metadata_sqlite_db', 'driveway_account',
                              driveway(ACCOUNT, 'Pat Doe', 'pat@example.com', 'https://example.com/pat.png'))
        _, rows, _ = self.run_accounts()
        where = DRIVEFS + ACCOUNT + '/metadata_sqlite_db'
        self.assertEqual([(row[0], row[1], row[-1]) for row in rows], [
            (datetime(2025, 12, 24, 21, 48, 51, tzinfo=UTC), ACCOUNT, f'{where}\n{DRIVEFS}experiments.db'),
            (datetime(2025, 12, 24, 21, 33, 20, tzinfo=UTC), ACCOUNT, f'{where}\nSystem/Volumes/Data/{DRIVEFS}experiments.db')])

class AuthorizationsTest(DriveFSCase):
    def run_authorizations(self):
        return artifact.googleDriveAuthorizations.__wrapped__(Context(self.root, walk(self.root)))

    def log(self, relative, lines):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.writelines(lines)
        return path

    def test_authorizations(self):
        logs = DRIVEFS + 'Logs/'
        self.log(logs + 'drive_fs.txt', [
            '2025-12-24T22:05:34.100ZI [12345:CrBrowserMain] client.cc:990:RefreshAccountTokens Refreshing\n',
            AUTHORIZED.format('2025-12-24T22:05:34.659ZI', 'pat@example.com', ACCOUNT),
            '2025-12-24T22:05:35.000ZE [12345:CrBrowserMain] client.cc:1027:StartAccountAuthComplete Failed\n'])
        first_log = [AUTHORIZED.format('2025-12-09T21:45:36.347ZI', 'pat@example.com', ACCOUNT),
                     AUTHORIZED.format('2025-12-10T16:39:47ZI', 'sam@example.com', OTHER)]
        self.log(logs + 'drive_fs_1.txt', first_log)
        # Not a drive_fs log.
        self.log(logs + 'finder_ext.txt', [AUTHORIZED.format('2025-12-01T00:00:00.000ZI', 'x@example.com', '1')])
        # A byte-identical copy is not read again; a copy that grew is read, and its shared lines are one row.
        shutil.copytree(os.path.join(self.root, logs), os.path.join(self.root, 'System/Volumes/Data', logs),
                        ignore=shutil.ignore_patterns('drive_fs_1.txt'))
        grown = 'System/Volumes/Data/' + logs + 'drive_fs_1.txt'
        self.log(grown, first_log + [AUTHORIZED.format('2025-12-11T09:00:00.5ZI', 'pat@example.com', ACCOUNT)])
        headers, rows, source = self.run_authorizations()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Email', 'Account ID', 'Line', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2025, 12, 9, 21, 45, 36, 347000, tzinfo=UTC), 'pat@example.com', ACCOUNT, 1,
             f'{logs}drive_fs_1.txt\n{grown}'),
            (datetime(2025, 12, 10, 16, 39, 47, tzinfo=UTC), 'sam@example.com', OTHER, 2, f'{logs}drive_fs_1.txt\n{grown}'),
            (datetime(2025, 12, 11, 9, 0, 0, 500000, tzinfo=UTC), 'pat@example.com', ACCOUNT, 3, grown),
            (datetime(2025, 12, 24, 22, 5, 34, 659000, tzinfo=UTC), 'pat@example.com', ACCOUNT, 2, logs + 'drive_fs.txt')])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.root, p) for p in (
            logs + 'drive_fs.txt', logs + 'drive_fs_1.txt', grown)))
        self.assertEqual(sorted(self.logged), sorted([
            'Google Drive Account Authorizations: 1 byte-identical copy(ies) under System/Volumes/Data not read again',
            'Google Drive Account Authorizations: 1 StartAccountAuthComplete line(s) not in the form read here, not reported']))


class PreferencesTest(DriveFSCase):
    def run_preferences(self):
        context = Context(self.root, walk(self.root))
        return (artifact.googleDriveSyncedFolders.__wrapped__(context), artifact.googleDriveVolumes.__wrapped__(context))

    def test_synced_folders_and_volumes(self):
        preferences = DRIVEFS + 'root_preference_sqlite.db'
        self.database(preferences, [
            (ROOTS,), (MEDIA,), ('CREATE TABLE max_ids (id_type TEXT PRIMARY KEY, value INTEGER NOT NULL)',),
            ('INSERT INTO roots VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, \'\', ?)',
             (4, 'USB-ID', 'KINGSTON', '', ACCOUNT, 2, 2, 2, 2, 1, '/Volumes/KINGSTON'),
             (1, VOLUME, 'Work', 'Users/pat/Documents/Work', ACCOUNT, 1, 1, 1, 2, 0, '/Users/pat/Documents/Work')),
            ('INSERT INTO media VALUES (?, ?, ?, ?, ?, ?, ?)',
             (VOLUME, 'Macintosh HD - Data', '/', 1, 2, 1000240963584, 0),
             ('nouuid--home', 'home', '/System/Volumes/Data/home', 7, 3, 0, 0),
             ('USB2', 'KINGSTON', '/Volumes/KINGSTON', 3, 9, -1, 1)),
            ("INSERT INTO max_ids VALUES ('max_root_id', 5)",)])
        # Another DriveFS folder with volumes and no roots table.
        other = 'Users/sam/Library/Application Support/Google/DriveFS/root_preference_sqlite.db'
        self.database(other, [(MEDIA,), ('INSERT INTO media VALUES (?, ?, ?, ?, ?, ?, ?)',
                                         ('D1', 'Data', '/', 1, 2, 500, 0))])
        (folder_headers, folders, folder_source), (volume_headers, volumes, volume_source) = self.run_preferences()
        self.assertEqual(list(folder_headers), [
            'Title', 'Last Seen Absolute Path', 'Root Path', 'Volume', 'Media ID', 'Destination (as stored)',
            'One Shot (as stored)', 'Account ID', 'Root ID', 'Max Root ID (as stored)', 'Source File'])
        self.assertEqual(folders, [
            ('Work', '/Users/pat/Documents/Work', 'Users/pat/Documents/Work', 'Macintosh HD - Data', VOLUME, 1, 0, ACCOUNT,
             1, 5, preferences),
            # A media_id with no media row leaves Volume blank.
            ('KINGSTON', '/Volumes/KINGSTON', '', '', 'USB-ID', 2, 1, ACCOUNT, 4, 5, preferences)])
        self.assertEqual(folder_source, os.path.join(self.root, preferences))
        self.assertEqual(list(volume_headers), [
            'Name', 'Last Mount Point', 'Capacity (as stored)', 'Ignored (as stored)', 'File System Type (as stored)',
            'Device Type (as stored)', 'Media ID', 'Source File'])
        # Volumes in the order the table stores them, not by media_id.
        self.assertEqual(volumes, [
            ('Macintosh HD - Data', '/', 1000240963584, 0, 1, 2, VOLUME, preferences),
            ('home', '/System/Volumes/Data/home', 0, 0, 7, 3, 'nouuid--home', preferences),
            ('KINGSTON', '/Volumes/KINGSTON', -1, 1, 3, 9, 'USB2', preferences),
            ('Data', '/', 500, 0, 1, 2, 'D1', other)])
        self.assertEqual(sorted(volume_source.split('\n')), sorted(os.path.join(self.root, p) for p in (preferences, other)))
        self.assertEqual(self.logged, [f'Google Drive Synced Folders: no roots table in {other}'])

    def test_empty_roots_table(self):
        self.database(DRIVEFS + 'root_preference_sqlite.db', [
            (ROOTS,), ('CREATE TABLE max_ids (id_type TEXT PRIMARY KEY, value INTEGER NOT NULL)',),
            ("INSERT INTO max_ids VALUES ('max_root_id', 3)",)])
        (_, folders, folder_source), _volumes = self.run_preferences()
        # No row, whatever max_ids holds.
        self.assertEqual((folders, folder_source), ([], ''))
        self.assertEqual(self.logged, [f'Google Drive Volumes: no media table in {DRIVEFS}root_preference_sqlite.db'])

    def test_declared_paths_of_the_account_artifacts(self):
        meta = artifact.__artifacts_v2__
        matches = {key: [member for member in (
            DRIVEFS + 'experiments.db', DRIVEFS + 'experiments.db-wal', DRIVEFS + ACCOUNT + '/metadata_sqlite_db',
            DRIVEFS + ACCOUNT + '/mirror_metadata_sqlite.db', DRIVEFS + 'Logs/drive_fs.txt', DRIVEFS + 'Logs/drive_fs_11.txt',
            DRIVEFS + 'Logs/finder_ext.txt', DRIVEFS + 'root_preference_sqlite.db',
            'Users/pat/AppData/Local/Google/DriveFS/Logs/drive_fs.txt')
            if any(fnmatch.fnmatch(member, pattern) for pattern in meta[key]['paths'])]
            for key in ('googleDriveAccounts', 'googleDriveAuthorizations', 'googleDriveSyncedFolders', 'googleDriveVolumes')}
        self.assertEqual(matches, {
            'googleDriveAccounts': [DRIVEFS + 'experiments.db', DRIVEFS + 'experiments.db-wal',
                                    DRIVEFS + ACCOUNT + '/metadata_sqlite_db', DRIVEFS + ACCOUNT + '/mirror_metadata_sqlite.db'],
            'googleDriveAuthorizations': [DRIVEFS + 'Logs/drive_fs.txt', DRIVEFS + 'Logs/drive_fs_11.txt',
                                          'Users/pat/AppData/Local/Google/DriveFS/Logs/drive_fs.txt'],
            'googleDriveSyncedFolders': [DRIVEFS + 'root_preference_sqlite.db'],
            'googleDriveVolumes': [DRIVEFS + 'root_preference_sqlite.db']})


if __name__ == '__main__':
    unittest.main()
