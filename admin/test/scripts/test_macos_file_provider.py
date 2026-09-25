"""Pin the File Provider reader in scripts/artifacts/macosFileProvider.py.

A synthetic FP_snapshot database is built with a known tree; every value is authored.
"""
import datetime
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosFileProvider  # pylint: disable=wrong-import-position

CREATED = datetime.datetime(2026, 3, 4, 5, 6, 7, tzinfo=datetime.timezone.utc)


class Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return [str(f) for f in self.files]

    @staticmethod
    def get_relative_path(path):
        p = str(path).replace('\\', '/')
        return p[p.index('Users/'):] if 'Users/' in p else p


def _build(path):
    db = sqlite3.connect(path)
    db.execute('''CREATE TABLE FP_snapshot (id, filename, parent_id, metadata_kind, metadata_size,
        metadata_creation_date, metadata_content_modification_date, metadata_last_used_date,
        decoration_is_uploaded, decoration_is_shared, metadata_physical_size,
        decoration_preformatted_owner_name)''')
    ts = int(CREATED.timestamp())
    rows = [
        ('1', 'OneDrive', 'NSFileProviderRootContainerItemIdentifier', 1, 96, ts, ts, None, 1, 0, 0, None),
        ('2', 'Bilder', '1', 1, 64, ts, ts, None, 1, 0, 0, None),
        ('3', 'note.txt', '2', 0, 1234, ts, ts, ts, 0, 0, 0, None),
        ('9', 'orphan.txt', 'missing-parent', 0, 5, ts, ts, None, 1, 0, 0, None),
    ]
    db.executemany('INSERT INTO FP_snapshot VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    db.commit()
    db.close()


class FileProviderTest(unittest.TestCase):

    def run_it(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(macosFileProvider, 'logfunc', lambda *_: None):
            db = (pathlib.Path(directory) / 'Users' / 'tester' / 'Library' / 'Application Support'
                  / 'FileProvider' / 'E3CDB961-DOMAIN' / 'database' / 'db')
            db.parent.mkdir(parents=True)
            _build(db)
            before = db.read_bytes()
            headers, rows, source = macosFileProvider.macosFileProviderItems.__wrapped__(
                Context([db]))
            self.assertEqual(before, db.read_bytes())
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        return names, [dict(zip(names, r)) for r in rows], source

    def test_paths_kind_flags_and_dates(self):
        _names, rows, source = self.run_it()
        by_id = {r['Item ID']: r for r in rows}
        self.assertEqual(by_id['1']['Path'], '/OneDrive')
        self.assertEqual(by_id['2']['Path'], '/OneDrive/Bilder')
        self.assertEqual(by_id['3']['Path'], '/OneDrive/Bilder/note.txt')
        self.assertEqual(by_id['9']['Path'], '.../orphan.txt')
        self.assertEqual(by_id['3']['Created (UTC)'], CREATED)
        self.assertEqual(by_id['1']['Last Used (UTC)'], '')
        self.assertEqual(by_id['3']['Last Used (UTC)'], CREATED)
        self.assertEqual((by_id['1']['Kind (as stored)'], by_id['3']['Kind (as stored)']), ('1', '0'))
        self.assertEqual((by_id['1']['Uploaded'], by_id['3']['Uploaded']), ('Yes', 'No'))
        self.assertEqual(by_id['3']['Shared'], 'No')
        self.assertEqual(by_id['3']['Domain'], 'E3CDB961-DOMAIN')
        self.assertEqual(by_id['3']['User'], 'tester')
        self.assertTrue(source.endswith('/database/db'))

    def test_no_owner_column_leaks(self):
        names, _rows, _source = self.run_it()
        self.assertNotIn('Owner (as stored)', names)
        self.assertNotIn('Physical Size', names)


if __name__ == '__main__':
    unittest.main()
