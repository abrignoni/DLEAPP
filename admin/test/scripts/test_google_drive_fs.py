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


class ArtifactTest(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
