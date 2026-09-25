"""Pin knowledgeCAppMediaUsage in scripts/artifacts/macosKnowledgeC.py.

Every value below is authored for the test; none comes from a real device.
"""
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosKnowledgeC  # pylint: disable=wrong-import-position

# Mac Absolute Time counts seconds from 2001-01-01 UTC; written out, not read from the code.
START = int((datetime(2026, 5, 9, 4, 26, 40, tzinfo=timezone.utc)
             - datetime(2001, 1, 1, tzinfo=timezone.utc)).total_seconds())


def _store(path, with_keys):
    db = sqlite3.connect(path)
    keys = (', Z_DKAPPMEDIAUSAGEMETADATAKEY__URL TEXT, Z_DKAPPMEDIAUSAGEMETADATAKEY__MEDIAURL TEXT'
            if with_keys else '')
    db.executescript(f'''
        CREATE TABLE ZSTRUCTUREDMETADATA (Z_PK INTEGER PRIMARY KEY{keys});
        CREATE TABLE ZOBJECT (Z_PK INTEGER PRIMARY KEY, ZSTREAMNAME TEXT, ZVALUESTRING TEXT,
            ZSTARTDATE REAL, ZENDDATE REAL, ZSTRUCTUREDMETADATA INTEGER);
        INSERT INTO ZOBJECT VALUES (1, '/app/mediaUsage', 'com.example.player', {START}, {START + 90}, 1);
        INSERT INTO ZOBJECT VALUES (2, '/app/usage', 'com.example.other', {START}, {START + 5}, NULL);''')
    if with_keys:
        db.execute("INSERT INTO ZSTRUCTUREDMETADATA VALUES (1, 'https://page.example', 'https://media.example/a')")
    else:
        db.execute('INSERT INTO ZSTRUCTUREDMETADATA VALUES (1)')
    db.commit()
    db.close()


class Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return [str(f) for f in self.files]

    @staticmethod
    def get_relative_path(path):
        return 'Library/Application Support/Knowledge/' + pathlib.Path(path).name


class AppMediaUsageTest(unittest.TestCase):

    def run_on(self, with_keys):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(macosKnowledgeC, 'logfunc', lambda *_: None):
            path = pathlib.Path(directory)/'knowledgeC.db'
            _store(path, with_keys)
            before = path.read_bytes()
            result = macosKnowledgeC.knowledgeCAppMediaUsage.__wrapped__(Context([path]))
            self.assertEqual(before, path.read_bytes())
        return result

    def test_row_with_metadata(self):
        _headers, rows, source = self.run_on(True)
        self.assertEqual(rows, [(datetime(2026, 5, 9, 4, 26, 40, tzinfo=timezone.utc),
                                 datetime(2026, 5, 9, 4, 28, 10, tzinfo=timezone.utc),
                                 'com.example.player', 'https://page.example',
                                 'https://media.example/a', 90,
                                 'Library/Application Support/Knowledge/knowledgeC.db')])
        self.assertEqual(source, 'Library/Application Support/Knowledge/knowledgeC.db')

    def test_store_without_the_metadata_columns_keeps_its_rows(self):
        _headers, rows, _source = self.run_on(False)
        self.assertEqual([r[2:6] for r in rows], [('com.example.player', '', '', 90)])


if __name__ == '__main__':
    unittest.main()
