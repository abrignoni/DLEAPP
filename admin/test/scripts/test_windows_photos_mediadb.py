"""Pin the Photos Library artifacts (scripts/artifacts/windowsPhotosMediaDb.py).

The databases are built for the test with the table and column names of the MediaDb.v1.sqlite on lonewolf_win10;
every value is made up.
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
from scripts.artifacts import windowsPhotosMediaDb as pm
# pylint: enable=wrong-import-position

CREATED = 131672110623676131          # 2018-04-03 06:37:42 UTC
T_CREATED = datetime(2018, 4, 3, 6, 37, 42, 367613, tzinfo=timezone.utc)
SCHEMA = (
    'CREATE TABLE Source(Source_Id INTEGER PRIMARY KEY, Source_Type INTEGER, Source_UserName TEXT);'
    'CREATE TABLE Folder(Folder_Id INTEGER PRIMARY KEY, Folder_ParentFolderId INTEGER, Folder_SourceId INTEGER, '
    'Folder_Path TEXT, Folder_DisplayName TEXT, Folder_DateCreated INTEGER, Folder_DateModified INTEGER, '
    'Folder_StorageProviderFileId TEXT, Folder_ItemCount INTEGER);'
    'CREATE TABLE CameraManufacturer(CameraManufacturer_Id INTEGER PRIMARY KEY, CameraManufacturer_Text TEXT);'
    'CREATE TABLE CameraModel(CameraModel_Id INTEGER PRIMARY KEY, CameraModel_Text TEXT);'
    'CREATE TABLE ItemTags(ItemTags_Id INTEGER PRIMARY KEY, ItemTags_ItemId INTEGER, ItemTags_TagId INTEGER);'
    'CREATE TABLE Item(Item_Id INTEGER PRIMARY KEY, Item_SourceId INTEGER, Item_MediaType INTEGER, Item_DateTaken '
    'INTEGER, Item_Width INTEGER, Item_Height INTEGER, Item_DateCreated INTEGER, Item_DateModified INTEGER, '
    'Item_ParentFolderId INTEGER, Item_FileName TEXT, Item_FileSize INTEGER, Item_Latitude REAL, Item_Longitude REAL, '
    'Item_CameraManufacturerId INTEGER, Item_CameraModelId INTEGER, Item_DateIngested INTEGER, '
    'Item_StorageProviderFileId TEXT);'
    "INSERT INTO Source VALUES (10, 1, NULL), (20, 5, 'made-up@example.com');"
    "INSERT INTO Folder VALUES (1, NULL, 10, 'C:\\Users\\u\\Pictures', 'Pictures', %d, %d, '-', 2), "
    "(2, 1, 20, NULL, NULL, NULL, 0, 'ID!7', NULL);"
    "INSERT INTO CameraManufacturer VALUES (4, 'Made-up Maker'); INSERT INTO CameraModel VALUES (9, 'Model Z');"
    'INSERT INTO ItemTags VALUES (1, 2, 5), (2, 2, 6), (3, 99, 5);'
    "INSERT INTO Item VALUES (2, 10, 1, %d, 800, 600, %d, %d, 1, 'second.jpg', 1234, 40.5, -74.25, 4, 9, %d, 'ID!9'), "
    "(1, 20, 3, NULL, NULL, NULL, 0, -5, 2, 'first.png', NULL, NULL, NULL, NULL, 77, %d, NULL);"
) % (CREATED, CREATED + 10 ** 7, CREATED - 144 * 10 ** 9, CREATED, CREATED + 2 * 10 ** 7, CREATED + 6 * 10 ** 8,
     CREATED)
ITEMS = [
    ('', '', '', T_CREATED, 'first.png', '', '', '', '', 3, '', '', '', '', 5, 'made-up@example.com', '', 0, 1),
    (T_CREATED, T_CREATED.replace(second=44), '2018-04-03 02:37:42', T_CREATED.replace(minute=38), 'second.jpg',
     'C:\\Users\\u\\Pictures', 1234, 800, 600, 1, 40.5, -74.25, 'Made-up Maker', 'Model Z', 1, '', 'ID!9', 2, 2)]
FOLDERS = [
    (T_CREATED, T_CREATED.replace(second=43), 'C:\\Users\\u\\Pictures', 'Pictures', 2, '', 1, '', '-', 1),
    ('', '', '', '', '', 1, 5, 'made-up@example.com', 'ID!7', 2)]


def database(script=SCHEMA):
    db = sqlite3.connect(':memory:')
    db.executescript(script)
    return db


class FakeSeeker:
    def __init__(self, found):
        self.found, self.asked = found, []

    def search(self, pattern):
        self.asked.append(pattern)
        return self.found.get(pattern, [])


class FakeContext:
    def __init__(self, paths, root, found=None):
        self.paths, self.root, self.seeker = paths, root, FakeSeeker(found or {})

    def get_seeker(self):
        return self.seeker

    def set_files_found(self, paths):
        self.paths = paths

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class Values(unittest.TestCase):
    def test_times(self):
        self.assertEqual(pm.filetime(CREATED), T_CREATED)
        for other in (0, -1, None, '1', 1.5, True, 10 ** 30):
            self.assertEqual(pm.filetime(other), '', other)
        self.assertEqual(pm.stored_clock(CREATED), '2018-04-03 06:37:42')
        self.assertEqual(pm.stored_clock(None), '')

    def test_media_pattern(self):
        base = 'p4/Users/b/AppData/Local/Packages/x/LocalState/MediaDb.v1.sqlite'
        self.assertEqual(pm.media_pattern(base, 'C:\\Users\\u\\Pictures', 'a [1]*?.jpg'),
                         '*/p4/Users/u/Pictures/a [[]1][*][?].jpg')
        self.assertEqual(pm.media_pattern('Users/b/x.sqlite', 'D:\\Photos\\', 'a.jpg'), '*/Photos/a.jpg')
        self.assertEqual(pm.media_pattern('p4/users/b/x.sqlite', 'C:\\', 'a.jpg'), '*/p4/a.jpg')
        for folder, name in (('', 'a.jpg'), ('\\\\server\\share', 'a.jpg'), ('C:', 'a.jpg'), ('C:\\Users', '')):
            self.assertIsNone(pm.media_pattern(base, folder, name), folder)
        self.assertIsNone(pm.media_pattern('export/MediaDb.v1.sqlite', 'C:\\Users\\u', 'a.jpg'))

    def test_user(self):
        self.assertEqual(pm._user('p4/Users/someone/AppData/Local/x/MediaDb.v1.sqlite'), 'someone')  # pylint: disable=protected-access
        self.assertEqual(pm._user('p4/users/Other/x'), 'Other')  # pylint: disable=protected-access
        self.assertEqual(pm._user('export/Users'), '')  # pylint: disable=protected-access
        self.assertEqual(pm._user('a/b/c'), '')  # pylint: disable=protected-access


class Tables(unittest.TestCase):
    def test_items(self):
        self.assertEqual(pm.item_rows(database()), ITEMS)

    def test_folders(self):
        self.assertEqual(pm.folder_rows(database()), FOLDERS)

    def test_a_version_without_some_columns_and_tables(self):
        db = database('CREATE TABLE Item(Item_Id INTEGER PRIMARY KEY, Item_FileName TEXT, Item_ParentFolderId INTEGER);'
                      "INSERT INTO Item VALUES (5, 'only.jpg', 3);"
                      'CREATE TABLE Folder(Folder_Id INTEGER PRIMARY KEY); INSERT INTO Folder VALUES (3);')
        self.assertEqual(pm.item_rows(db), [('', '', '', '', 'only.jpg') + ('',) * 12 + (0, 5)])
        self.assertEqual(pm.folder_rows(db), [('',) * 9 + (3,)])

    def test_no_table_or_no_id_column(self):
        self.assertIsNone(pm.item_rows(database('CREATE TABLE Other(x);')))
        self.assertIsNone(pm.folder_rows(database('CREATE TABLE Other(x);')))
        self.assertIsNone(pm.item_rows(database('CREATE TABLE Item(Item_FileName TEXT);')))


class Processors(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.root = folder.name
        self.paths = []
        self.context = None
        self.checked = None
        empty = SCHEMA[:SCHEMA.index('INSERT INTO Source')]
        for user, script in (('b', SCHEMA), ('a', 'CREATE TABLE Other(x);'), ('c', None), ('d', empty)):
            path = os.path.join(self.root, 'C', 'Users', user, 'AppData', 'Local', 'Packages',
                                'Microsoft.Windows.Photos_8wekyb3d8bbwe', 'LocalState', 'MediaDb.v1.sqlite')
            os.makedirs(os.path.dirname(path))
            if script is None:
                with open(path, 'wb') as handle:
                    handle.write(b'not a database, but long enough to be read as a file header')
            else:
                db = sqlite3.connect(path)
                db.executescript(script)
                db.close()
            self.paths += [path, path + '-wal']
        self.good = self.paths[0]
        other = os.path.join(os.path.dirname(self.good), 'Other.sqlite')
        db = sqlite3.connect(other)
        db.executescript(SCHEMA)
        db.close()
        self.paths.append(other)

    def run_one(self, processor, found=None):
        self.context = FakeContext(self.paths[::-1], self.root, found)
        with mock.patch.object(pm, 'logfunc') as log, \
                mock.patch.object(pm, 'check_in_media', side_effect=lambda path, name='': 'ref:' + name) as checked:
            headers, data, located = processor.__wrapped__(self.context)
        self.checked = checked
        return headers, data, located, [call[0][0] for call in log.call_args_list]

    def test_items(self):
        pattern = '*/C/Users/u/Pictures/second.jpg'
        headers, data, located, logged = self.run_one(pm.photosMediaDbItems, {pattern: ['/staged/second.jpg', '/staged/other.jpg']})
        relative = 'C/Users/b/AppData/Local/Packages/Microsoft.Windows.Photos_8wekyb3d8bbwe/LocalState/MediaDb.v1.sqlite'
        self.assertEqual(len(headers), 22)
        self.assertEqual(headers[2:5], ('Date Taken (As Stored)', ('Date Ingested (UTC)', 'datetime'), ('Media', 'media')))
        self.assertEqual(data, [ITEMS[0][:4] + ('',) + ITEMS[0][4:] + ('b', relative),
                                ITEMS[1][:4] + ('ref:second.jpg',) + ITEMS[1][4:] + ('b', relative)])
        self.assertEqual(located, self.good)
        self.assertEqual(self.context.seeker.asked, [pattern])
        self.checked.assert_called_once_with('/staged/second.jpg', name='second.jpg')
        self.assertIn('/staged/second.jpg', self.context.paths)
        self.assertEqual(len(logged), 3)
        self.assertIn('C/Users/a/', logged[0])
        self.assertIn('does not have the table this artifact reads', logged[0])
        self.assertIn('1 of 2 items of C/Users/b/', logged[1])
        self.assertIn('could not read C/Users/c/', logged[2])

    def test_items_whose_files_are_not_in_the_extraction(self):
        data = self.run_one(pm.photosMediaDbItems)[1]
        self.assertEqual([row[4] for row in data], ['', ''])
        self.checked.assert_not_called()
        self.assertNotIn('/staged/second.jpg', self.context.paths)

    def test_folders(self):
        headers, data, located, logged = self.run_one(pm.photosMediaDbFolders)
        self.assertEqual(len(headers), 12)
        self.assertEqual([row[:10] for row in data], FOLDERS)
        self.assertEqual({row[10] for row in data}, {'b'})
        self.assertEqual(located, self.good)
        self.assertEqual(len(logged), 2)


if __name__ == '__main__':
    unittest.main()
