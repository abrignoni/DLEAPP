"""Pin the Notarization Tickets artifact in scripts/artifacts/macosNotarizationTickets.py.

Every database below is built by the test with the table definitions the two public macOS
images carry; no row comes from a real device. Expected times are written out as literals.
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

from scripts.artifacts import macosNotarizationTickets as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
HASHES = 'CREATE TABLE hashes (  id INTEGER PRIMARY KEY AUTOINCREMENT,  hash BLOB,  hash_type INTEGER,  ticket_id INTEGER,  FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE)'
TICKETS_15 = 'CREATE TABLE tickets (  id INTEGER PRIMARY KEY AUTOINCREMENT,  hash BLOB,  hash_type INTEGER,  timestamp INTEGER,  flags INTEGER, last_access INTEGER)'
TICKETS_11 = 'CREATE TABLE tickets (  id INTEGER PRIMARY KEY AUTOINCREMENT,  hash BLOB,  hash_type INTEGER,  timestamp INTEGER,  flags INTEGER)'
A, B, C, D, P = (bytes([n]) * 20 for n in (0xA1, 0xB2, 0xC3, 0xD4, 0x5E))


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
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.image = os.path.join(self.root, 'image')

    def database(self, relative, statements):
        path = os.path.join(self.image, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with sqlite3.connect(path) as db:
            for statement, *rows in statements:
                if rows:
                    db.executemany(statement, rows)
                else:
                    db.execute(statement)
        db.close()
        return path

    def run_artifact(self, extra=()):
        return artifact.macosNotarizationTickets.__wrapped__(Context(self.image, walk(self.image) + list(extra)))

    def test_one_row_per_hash_with_its_ticket_and_names(self):
        tickets = [(TICKETS_15,), (HASHES,),
                   ('INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?)', (7, A, 2, 1760896254, 0, 1765316688),
                    (9, P, 1, 1764713041, 0, 1766613918), (12, C, 2, 1764713041, 0, 0)),
                   ('INSERT INTO hashes VALUES (?, ?, ?, ?)', (1, A, 2, 7), (2, B, 2, 7), (3, P, 1, 9),
                    (4, C, 2, 9), (5, D, 2, 99))]
        execpolicy = [('CREATE TABLE policy_scan_cache (pk INTEGER PRIMARY KEY, cdhash TEXT, bundle_id TEXT)',),
                      ('CREATE TABLE executable_measurements_v2 (pk INTEGER PRIMARY KEY, cdhash TEXT, bundle_identifier TEXT)',),
                      # Stored upper case here, and matched all the same.
                      ('INSERT INTO policy_scan_cache VALUES (?, ?, ?)', (1, B.hex().upper(), 'com.example.app'),
                       # The same bundle ID in both tables is listed once.
                       (2, A.hex(), 'com.example.tool'), (3, C.hex(), None)),
                      ('INSERT INTO executable_measurements_v2 VALUES (?, ?, ?)', (1, A.hex(), 'com.example.tool'),
                       (2, A.hex(), 'NOT_A_BUNDLE'), (3, D.hex(), ''))]
        for root in ('', 'System/Volumes/Data/'):
            self.database(root + 'private/var/db/SystemPolicyConfiguration/Tickets', tickets)
            self.database(root + 'private/var/db/SystemPolicyConfiguration/ExecPolicy', execpolicy)
        headers, rows, source = self.run_artifact()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Ticket Timestamp (UTC)', 'Last Access (UTC)', 'Ticket ID', 'Hash', 'Hash Type (as stored)',
                          'Ticket Hash', 'Ticket Hash Type (as stored)', 'Ticket Flags (as stored)',
                          'Bundle IDs (ExecPolicy)', 'Source File'])
        both = ('System/Volumes/Data/private/var/db/SystemPolicyConfiguration/Tickets\n'
                'private/var/db/SystemPolicyConfiguration/Tickets')
        t7 = datetime(2025, 10, 19, 17, 50, 54, tzinfo=UTC)
        t9 = datetime(2025, 12, 2, 22, 4, 1, tzinfo=UTC)
        self.assertEqual(rows, [
            (t7, datetime(2025, 12, 9, 21, 44, 48, tzinfo=UTC), 7, A.hex(), 2, A.hex(), 2, 0, 'NOT_A_BUNDLE\ncom.example.tool', both),
            (t7, datetime(2025, 12, 9, 21, 44, 48, tzinfo=UTC), 7, B.hex(), 2, A.hex(), 2, 0, 'com.example.app', both),
            (t9, datetime(2025, 12, 24, 22, 5, 18, tzinfo=UTC), 9, P.hex(), 1, P.hex(), 1, 0, '', both),
            (t9, datetime(2025, 12, 24, 22, 5, 18, tzinfo=UTC), 9, C.hex(), 2, P.hex(), 1, 0, '', both),
            # A ticket that lists no hash still gets a row, and a last access of 0 is blank.
            (t9, '', 12, '', '', C.hex(), 2, 0, '', both),
            # A hash whose ticket is gone keeps its row, with the ticket columns blank.
            ('', '', 99, D.hex(), 2, '', '', '', '', both)])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.image, r + f) for r in ('', 'System/Volumes/Data/')
                                                            for f in ('private/var/db/SystemPolicyConfiguration/Tickets',
                                                                      'private/var/db/SystemPolicyConfiguration/ExecPolicy')))
        self.assertEqual(self.logged, [])

    def test_older_layout_without_execpolicy(self):
        self.database('private/var/db/SystemPolicyConfiguration/Tickets',
                      [(TICKETS_11,), (HASHES,), ('INSERT INTO tickets VALUES (?, ?, ?, ?, ?)', (2, A, 2, 1595488104, 0)),
                       ('INSERT INTO hashes VALUES (?, ?, ?, ?)', (1, A, 2, 2))])
        _, rows, source = self.run_artifact()
        self.assertEqual(rows, [(datetime(2020, 7, 23, 7, 8, 24, tzinfo=UTC), '', 2, A.hex(), 2, A.hex(), 2, 0, '',
                                 'private/var/db/SystemPolicyConfiguration/Tickets')])
        self.assertEqual(source, os.path.join(self.image, 'private/var/db/SystemPolicyConfiguration/Tickets'))

    def test_a_copy_without_the_tables_is_logged(self):
        self.database('private/var/db/SystemPolicyConfiguration/Tickets', [('CREATE TABLE settings (name TEXT, value TEXT)',)])
        # A copy whose tables hold no row is not listed as a source.
        self.database('b/var/db/SystemPolicyConfiguration/Tickets', [(TICKETS_15,), (HASHES,)])
        # A seeker can hand back a directory; it is not read.
        folder = os.path.join(self.image, 'c/var/db/SystemPolicyConfiguration/Tickets')
        os.makedirs(folder)
        _, rows, source = self.run_artifact([folder])
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ['Notarization Tickets: no tickets and hashes tables in '
                                       'private/var/db/SystemPolicyConfiguration/Tickets'])

    def test_declared_paths(self):
        patterns = artifact.__artifacts_v2__['macosNotarizationTickets']['paths']
        for path in ('p2/Macintosh HD - Data/private/var/db/SystemPolicyConfiguration/Tickets',
                     'System/Volumes/Data/private/var/db/SystemPolicyConfiguration/Tickets-wal',
                     'private/var/db/SystemPolicyConfiguration/ExecPolicy', 'r/var/db/SystemPolicyConfiguration/ExecPolicy-shm'):
            self.assertTrue(any(fnmatch.fnmatch(path, p) for p in patterns), path)
        self.assertEqual(artifact.macosNotarizationTickets.__name__, 'macosNotarizationTickets')


if __name__ == '__main__':
    unittest.main()
