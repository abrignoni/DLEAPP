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
DISTANT_FUTURE = 63113904000.0
SOURCE = 'Library/Application Support/Knowledge/knowledgeC.db'


def _store(path, with_keys, event_entity=True, end=None):
    db = sqlite3.connect(path)
    keys = (', Z_DKAPPMEDIAUSAGEMETADATAKEY__URL TEXT, Z_DKAPPMEDIAUSAGEMETADATAKEY__MEDIAURL TEXT'
            if with_keys else '')
    end = START + 90 if end is None else end
    entity_name = 'Event' if event_entity else 'Other'
    db.executescript(f'''
        CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME TEXT);
        INSERT INTO Z_PRIMARYKEY VALUES (11, '{entity_name}');
        CREATE TABLE ZSOURCE (Z_PK INTEGER PRIMARY KEY, ZDEVICEID TEXT, ZBUNDLEID TEXT);
        INSERT INTO ZSOURCE VALUES (1, 'source-device', 'com.example.source');
        CREATE TABLE ZSTRUCTUREDMETADATA (Z_PK INTEGER PRIMARY KEY{keys});
        CREATE TABLE ZOBJECT (Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, ZSTREAMNAME TEXT,
            ZVALUESTRING TEXT, ZSTARTDATE REAL, ZENDDATE REAL, ZLOCALCREATIONDATE REAL,
            ZSECONDSFROMGMT INTEGER, ZSOURCE INTEGER, ZSTRUCTUREDMETADATA INTEGER);
        INSERT INTO ZOBJECT VALUES (1, 11, '/app/mediaUsage', 'com.example.player', {START},
            {end}, {START + 100}, -18000, 1, 1);
        INSERT INTO ZOBJECT VALUES (2, 11, '/app/usage', 'com.example.other', {START},
            {START + 5}, {START + 5}, -18000, NULL, NULL);
        INSERT INTO ZOBJECT VALUES (3, 12, '/app/mediaUsage', 'com.example.notanevent', {START},
            {START + 5}, {START + 5}, -18000, NULL, NULL);''')
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

    def run_on(self, with_keys, **store_options):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(macosKnowledgeC, 'logfunc', lambda *_: None):
            path = pathlib.Path(directory)/'knowledgeC.db'
            _store(path, with_keys, **store_options)
            before = path.read_bytes()
            result = macosKnowledgeC.knowledgeCAppMediaUsage.__wrapped__(Context([path]))
            self.assertEqual(before, path.read_bytes())
        return result

    def test_row_with_metadata(self):
        _headers, rows, source = self.run_on(True)
        self.assertEqual(rows, [(datetime(2026, 5, 9, 4, 26, 40, tzinfo=timezone.utc),
                                 datetime(2026, 5, 9, 4, 28, 10, tzinfo=timezone.utc),
                                 datetime(2026, 5, 9, 4, 28, 20, tzinfo=timezone.utc),
                                 'com.example.player', 'https://page.example',
                                 'https://media.example/a', 90, '-05:00', 'source-device',
                                 SOURCE)])
        self.assertEqual(source, SOURCE)

    def test_store_without_the_metadata_columns_keeps_its_rows(self):
        _headers, rows, _source = self.run_on(False)
        self.assertEqual([r[3:7] for r in rows], [('com.example.player', '', '', 90)])

    def test_open_ended_event_has_no_end_or_duration(self):
        headers, rows, _source = self.run_on(True, end=DISTANT_FUTURE)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(rows[0][names.index('End Time')], '')
        self.assertEqual(rows[0][names.index('Duration (s)')], '')

    def test_store_without_an_event_entity_yields_no_rows(self):
        _headers, rows, source = self.run_on(True, event_entity=False)
        self.assertEqual(rows, [])
        self.assertEqual(source, '')


if __name__ == '__main__':
    unittest.main()
