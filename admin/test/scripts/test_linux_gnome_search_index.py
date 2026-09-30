"""Pin how the GNOME search index artifact reads a tinysparql store. Every store here is constructed for the test."""
import datetime
import fnmatch
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxGnomeSearchIndex as gsi
# pylint: enable=wrong-import-position

G = 'http://tracker.api.gnome.org/ontology/v3/tracker#'
UTC = datetime.timezone.utc


def build_store(path, version=32):
    db = sqlite3.connect(path)
    db.create_function('SparqlTimeSort', 1, lambda v: v, deterministic=True)
    db.create_collation('TRACKER', lambda a, b: (a > b) - (a < b))
    fs = G + 'FileSystem'
    db.executescript(f'''
        CREATE TABLE Resource (ID INTEGER PRIMARY KEY, Uri TEXT UNIQUE, BlankNode INTEGER);
        CREATE TABLE "{fs}_rdfs:Resource" (ID INTEGER PRIMARY KEY, "nrl:added" INTEGER, "nrl:modified" INTEGER);
        CREATE TABLE "{fs}_nfo:FileDataObject" (ID INTEGER PRIMARY KEY, "nfo:fileLastAccessed" INTEGER,
            "nfo:fileCreated" INTEGER, "nfo:fileSize" INTEGER, "nfo:fileName" TEXT COLLATE TRACKER,
            "nfo:fileLastModified" INTEGER);
        CREATE INDEX "{fs}_nfo:FileDataObject_nfo:fileLastModified" ON "{fs}_nfo:FileDataObject"
            (SparqlTimeSort("nfo:fileLastModified"));
        CREATE INDEX "{fs}_nfo:FileDataObject_nfo:fileName" ON "{fs}_nfo:FileDataObject" ("nfo:fileName");
        CREATE TABLE "{fs}_nie:DataObject" (ID INTEGER PRIMARY KEY, "nie:url" TEXT, "nie:byteSize" INTEGER);
        CREATE TABLE "{fs}_nie:DataObject_nie:interpretedAs" (ID INTEGER, "nie:interpretedAs" INTEGER);
        CREATE TABLE "{fs}_nfo:Folder" (ID INTEGER PRIMARY KEY);
        CREATE TABLE "{fs}_nie:InformationElement" (ID INTEGER PRIMARY KEY, "nie:mimeType" TEXT);
        CREATE TABLE "{fs}_nie:InformationElement_nie:isStoredAs" (ID INTEGER, "nie:isStoredAs" INTEGER);
    ''')
    for graph in ('Documents', 'Pictures'):
        db.executescript(f'''
            CREATE TABLE "{G}{graph}_nie:InformationElement" (ID INTEGER PRIMARY KEY, "nie:mimeType" TEXT);
            CREATE TABLE "{G}{graph}_nie:InformationElement_nie:isStoredAs" (ID INTEGER, "nie:isStoredAs" INTEGER);
        ''')
    files = [  # id, url, name, size, modified, accessed, created, added
        (1, 'file:///home/a', 'a', 4096, 1790000000, 1790000100, '2026-09-21T14:13:20.500000Z', 1790000200),
        (2, 'file:///home/a/My%20Notes.txt', 'My Notes.txt', 12, '2026-09-21T14:13:20.123456Z', 1790000300,
         '2026-09-21T14:13:20.123456Z', 1790000400),
        (3, 'file:///home/a/p.jpg', 'p.jpg', 99, '2026-09-21T10:13:20.250000-04:00', 1790000500,
         '2026-09-21T14:13:20Z', None),
        (4, 'file:///home/a/raw.bin', 'raw.bin', 7, 1767323045, 1767323045, 'not a time', 1790000600),
        (5, None, None, None, 1790000700, 1790000700, None, 1790000700),
    ]
    for fid, url, name, size, modified, accessed, created, added in files:
        db.execute('INSERT INTO Resource VALUES (?, ?, 0)', (fid, url or 'file:///home/a/tmp-new'))
        db.execute(f'INSERT INTO "{fs}_rdfs:Resource" VALUES (?, ?, 1)', (fid, added))
        db.execute(f'INSERT INTO "{fs}_nfo:FileDataObject" VALUES (?, ?, ?, ?, ?, ?)',
                   (fid, accessed, created, size, name, modified))
        if url:
            db.execute(f'INSERT INTO "{fs}_nie:DataObject" VALUES (?, ?, ?)', (fid, url, size))
    db.execute(f'INSERT INTO "{fs}_nfo:Folder" VALUES (100)')
    db.execute(f'INSERT INTO "{fs}_nie:InformationElement" VALUES (100, "inode/directory")')
    db.execute(f'INSERT INTO "{fs}_nie:InformationElement_nie:isStoredAs" VALUES (100, 1)')
    db.execute(f'INSERT INTO "{fs}_nie:DataObject_nie:interpretedAs" VALUES (1, 100)')
    db.execute(f'INSERT INTO "{G}Documents_nie:InformationElement" VALUES (200, "text/plain")')
    db.execute(f'INSERT INTO "{G}Documents_nie:InformationElement_nie:isStoredAs" VALUES (200, 2)')
    db.execute(f'INSERT INTO "{G}Pictures_nie:InformationElement" VALUES (300, "image/jpeg")')
    db.execute(f'INSERT INTO "{G}Pictures_nie:InformationElement_nie:isStoredAs" VALUES (300, 3)')
    db.execute(f'INSERT INTO "{G}Documents_nie:InformationElement" VALUES (301, NULL)')
    db.execute(f'INSERT INTO "{G}Documents_nie:InformationElement_nie:isStoredAs" VALUES (301, 4)')
    db.execute(f'PRAGMA user_version = {version}')
    db.commit()
    db.close()


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def at(seconds, micro=0):
    return datetime.datetime.fromtimestamp(seconds, UTC).replace(microsecond=micro)


class HelperTest(unittest.TestCase):
    def test_tracker_time(self):
        self.assertEqual(gsi.tracker_time(1790000000), at(1790000000))
        self.assertEqual(gsi.tracker_time('2026-09-21T14:13:20.123456Z'), at(1790000000, 123456))
        self.assertEqual(gsi.tracker_time('2026-09-21T10:13:20.250000-04:00'), at(1790000000, 250000))
        self.assertEqual(gsi.tracker_time('2026-09-21T10:13:20-04:00'), at(1790000000))
        for value in (1790000000, '2026-09-21T14:13:20.123456Z', '2026-09-21T10:13:20.250000-04:00'):
            self.assertEqual(gsi.tracker_time(value).utcoffset(), datetime.timedelta(0), value)
        self.assertIsNone(gsi.tracker_time('2026-09-21T14:13:20'))
        self.assertIsNone(gsi.tracker_time('not a time'))
        self.assertIsNone(gsi.tracker_time(None))

    def test_url_path(self):
        self.assertEqual(gsi.url_path('file:///home/a/My%20Notes%23.txt'), '/home/a/My Notes#.txt')
        self.assertEqual(gsi.url_path('urn:fileid:x'), 'urn:fileid:x')
        self.assertEqual(gsi.url_path(None), '')

    def test_paths(self):
        pattern = gsi.__artifacts_v2__['linuxGnomeSearchIndexFiles']['paths']
        for member in ('home/a/.cache/tracker3/files/meta.db', 'home/a/.cache/tracker3/files/meta.db-wal'):
            self.assertTrue(any(fnmatch.fnmatch('x/' + member, p) for p in pattern), member)
        for member in ('home/a/.cache/tracker/meta.db', 'home/a/.cache/tracker3/files/errors/abc'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in pattern), member)


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, version=32):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'home', 'a', '.cache', 'tracker3', 'files')
            os.makedirs(folder)
            store = os.path.join(folder, 'meta.db')
            build_store(store, version)
            wal = os.path.join(folder, 'meta.db-wal')
            open(wal, 'wb').close()
            with mock.patch.object(gsi, 'logfunc') as log:
                result = gsi.linuxGnomeSearchIndexFiles.__wrapped__(FakeContext([wal, store, folder], root))
        return result, log, store

    def test_rows(self):
        (headers, rows, source), log, store = self.run_artifact()
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(names, ['Indexed', 'File Modified', 'File Accessed', 'File Created', 'Type', 'Path', 'Name',
                                 'Size', 'MIME Type', 'Metadata Graphs', 'Source File'])
        src = 'home/a/.cache/tracker3/files/meta.db'
        self.assertEqual(rows, [
            (at(1790000200), at(1790000000), at(1790000100), at(1790000000, 500000), 'Folder', '/home/a', 'a',
             4096, '', '', src),
            (at(1790000400), at(1790000000, 123456), at(1790000300), at(1790000000, 123456), 'File',
             '/home/a/My Notes.txt', 'My Notes.txt', 12, 'text/plain', 'Documents', src),
            ('', at(1790000000, 250000), at(1790000500), at(1790000000), 'File', '/home/a/p.jpg', 'p.jpg', 99,
             'image/jpeg', 'Pictures', src),
            (at(1790000600), at(1767323045), at(1767323045), '', 'File', '/home/a/raw.bin', 'raw.bin', 7, '',
             'Documents', src),
            (at(1790000700), at(1790000700), at(1790000700), '', 'File', '/home/a/tmp-new', '', '', '', '', src),
        ])
        self.assertEqual(source, store)
        log.assert_called_once_with('Search Index Files (GNOME): 1 rows with no nie:url, path taken from the '
                                    'resource URI, 1 times that could not be read, left blank')

    def test_older_layout_not_read(self):
        (_headers, rows, source), log, _store = self.run_artifact(version=31)
        self.assertEqual((rows, source), ([], ''))
        log.assert_called_once_with('Search Index Files (GNOME): home/a/.cache/tracker3/files/meta.db is database '
                                    'version 31, which keeps each graph in its own file; not read')


if __name__ == '__main__':
    unittest.main()
