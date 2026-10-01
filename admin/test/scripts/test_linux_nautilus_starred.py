"""Pin the Starred Files (GNOME Files) artifact (scripts/artifacts/linuxNautilusStarred.py).

ROWS are the four file resources of ubuntu2604_arm64_nautilusstars as tinysparql 3.11.0 stored them for Nautilus
50.2.2 (Resource ID and Uri, nrl:added, nrl:modified, and whether a nautilus:File row holds nautilus:starred), put in
test tables that have the columns the artifact reads.
"""
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxNautilusStarred as ns
# pylint: enable=wrong-import-position

BASE = 'file:///home/parallels/Documents/dleapp-star-known-20261001/'
ROWS = (
    (67, BASE + 'star-alpha.txt', 1790868337, 2, False),
    (68, BASE + 'star-bravo.txt', 1790868345, 7, True),
    (69, BASE + 'sub', 1790868350, 4, True),
    (70, BASE + 'star-alpha-renamed.txt', 1790868378, 6, True),
)


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def make_store(path, rows=ROWS, tables=True):
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE Resource (ID INTEGER NOT NULL PRIMARY KEY, Uri TEXT NOT NULL, UNIQUE (Uri))')
    db.execute('CREATE TABLE "rdfs:Resource" (ID INTEGER NOT NULL PRIMARY KEY, "rdfs:comment" TEXT, "rdfs:label" TEXT, '
               '"nrl:added" INTEGER, "nrl:modified" INTEGER)')
    if tables:
        db.execute('CREATE TABLE "nautilus:File" (ID INTEGER NOT NULL PRIMARY KEY, "nautilus:starred" INTEGER)')
    db.execute('INSERT INTO Resource (ID, Uri) VALUES (66, ?)', ('https://gitlab.gnome.org/GNOME/nautilus#',))
    db.execute('INSERT INTO "rdfs:Resource" (ID, "nrl:added", "nrl:modified") VALUES (66, 1790691338, 1)')
    for rid, uri, added, modified, starred in rows:
        db.execute('INSERT INTO Resource (ID, Uri) VALUES (?, ?)', (rid, uri))
        db.execute('INSERT INTO "rdfs:Resource" (ID, "nrl:added", "nrl:modified") VALUES (?, ?, ?)', (rid, added, modified))
        if starred and tables:
            db.execute('INSERT INTO "nautilus:File" VALUES (?, 1)', (rid,))
    db.commit()
    db.close()


class Helpers(unittest.TestCase):
    def test_uri_path(self):
        self.assertEqual(ns.uri_path('file:///home/u/My%20File%20%C3%A9.txt'), '/home/u/My File é.txt')
        self.assertEqual(ns.uri_path('file:///home/u/a%23b'), '/home/u/a#b')
        self.assertEqual(ns.uri_path('file:'), 'file:')

    def test_added_time(self):
        self.assertEqual(ns.added_time(1790868337), utc(1790868337))
        self.assertEqual(utc(1790868337).isoformat(), '2026-10-01T15:25:37+00:00')
        for value in ('2026-10-01T15:25:37.5Z', None, True, 1.5, 10 ** 30):
            self.assertIsNone(ns.added_time(value), value)


class StoreRows(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, 'meta.db')

    def rows(self):
        db = sqlite3.connect(self.path)
        counts = Counter()
        try:
            return ns.starred_rows(db, counts), counts
        finally:
            db.close()

    def test_known_rows(self):
        make_store(self.path)
        got, counts = self.rows()
        tail = 'dleapp-star-known-20261001/'
        self.assertEqual(got, [
            (utc(1790868337), '/home/parallels/Documents/' + tail + 'star-alpha.txt', 'No', 2),
            (utc(1790868345), '/home/parallels/Documents/' + tail + 'star-bravo.txt', 'Yes', 7),
            (utc(1790868350), '/home/parallels/Documents/' + tail + 'sub', 'Yes', 4),
            (utc(1790868378), '/home/parallels/Documents/' + tail + 'star-alpha-renamed.txt', 'Yes', 6),
        ])
        self.assertEqual(counts, Counter())

    def test_order_text_time_and_false_flag(self):
        make_store(self.path, rows=[(70, 'file:///b', 200, 3, True), (69, 'file:///a', 100, 2, False),
                                    (71, 'file:///c', '2026-10-01T15:25:37.5Z', None, True),
                                    (72, 'smb://host/share/x', 50, 1, True)])
        db = sqlite3.connect(self.path)
        db.execute('UPDATE "nautilus:File" SET "nautilus:starred" = 0 WHERE ID = 70')
        db.commit()
        db.close()
        got, counts = self.rows()
        self.assertEqual([(r[1], r[2], r[3]) for r in got], [('/a', 'No', 2), ('/b', 'No', 3), ('/c', 'Yes', '')])
        self.assertEqual(got[2][0], '')
        self.assertEqual(counts['added times not stored as whole seconds, left blank'], 1)

    def test_store_without_the_tables(self):
        make_store(self.path, tables=False)
        self.assertEqual(self.rows()[0], None)


class ArtifactRun(unittest.TestCase):
    def run_artifact(self, files, root):
        context = mock.Mock()
        context.get_files_found.return_value = files
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, root)
        logged = []
        with mock.patch.object(ns, 'logfunc', logged.append):
            result = ns.linuxNautilusStarredFiles.__wrapped__(context)
        return result, logged

    def test_rows_and_located(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = os.path.join(tmp, 'home', 'u', '.local', 'share', 'nautilus', 'tags')
            other = os.path.join(tmp, 'home', 'v', '.local', 'share', 'nautilus', 'tags')
            os.makedirs(good)
            os.makedirs(other)
            make_store(os.path.join(good, 'meta.db'))
            make_store(os.path.join(other, 'meta.db'), tables=False)
            sidecar = os.path.join(good, 'meta.db-wal')
            with open(sidecar, 'wb') as handle:
                handle.write(b'')
            (headers, data, located), logged = self.run_artifact(
                [sidecar, os.path.join(other, 'meta.db'), os.path.join(good, 'meta.db'), good], tmp)
        self.assertEqual(headers, (('First Added', 'datetime'), 'Path', 'Starred', 'Change Sequence'))
        self.assertEqual(len(data), 4)
        self.assertEqual(located, os.path.join(good, 'meta.db'))
        self.assertEqual(logged, ['Starred Files (GNOME Files): 1 stores without the starred-files tables, not reported'])

    def test_empty_store_is_not_located(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'meta.db')
            make_store(path, rows=())
            (_, data, located), logged = self.run_artifact([path], tmp)
        self.assertEqual((data, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
