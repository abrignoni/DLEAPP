"""Pin the record counting in scripts/artifacts/chromiumIndexedDb.py.

Keys are built with the reader's own prefix encoder for database 1, object store 1:
index id 1 holds the object store data and index id 3 the external object entries, as
in Chromium's IndexedDB LevelDB coding scheme. Expected values are written out.
"""
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import chromiumIndexedDb as art  # pylint: disable=wrong-import-position
from scripts.vendor.ccl import ccl_chromium_indexeddb as idb  # pylint: disable=wrong-import-position
from scripts.vendor.ccl import ccl_leveldb  # pylint: disable=wrong-import-position

LIVE = ccl_leveldb.KeyState.Live
DELETED = ccl_leveldb.KeyState.Deleted
DATA = idb.IndexedDb.make_prefix(1, 1, 1)
EXTERNAL = idb.IndexedDb.make_prefix(1, 1, 3)
OTHER_STORE = idb.IndexedDb.make_prefix(1, 2, 1)


def _db(records):
    return SimpleNamespace(_fetched_records=[SimpleNamespace(key=k, user_key=k, seq=q, state=s)
                                             for k, q, s in records])


def _ldb(key, seq, live):
    """A record as read from an .ldb table file: the raw key ends in the sequence and type."""
    raw = key + ((seq << 8) | (1 if live else 0)).to_bytes(8, 'little')
    return SimpleNamespace(key=raw, user_key=key, seq=seq, state=LIVE if live else DELETED)


class CountTest(unittest.TestCase):
    def test_newest_record_decides(self):
        states = art._newest_states(_db([  # pylint: disable=protected-access
            (DATA + b'a', 1, LIVE), (DATA + b'a', 5, DELETED),   # put then deleted
            (DATA + b'b', 2, DELETED), (DATA + b'b', 6, LIVE),   # deleted then put again
            (DATA + b'c', 3, LIVE),
            (EXTERNAL + b'c', 4, LIVE),
            (OTHER_STORE + b'x', 7, LIVE)]))
        self.assertEqual(art._store_counts(states, 1, 1), (2, 1, 1))  # pylint: disable=protected-access
        self.assertEqual(art._store_counts(states, 1, 2), (1, 0, 0))  # pylint: disable=protected-access

    def test_table_file_versions_merge_on_the_user_key(self):
        db = SimpleNamespace(_fetched_records=[
            _ldb(DATA + b'a', 1, True), _ldb(DATA + b'a', 4, False),
            _ldb(DATA + b'b', 2, True), _ldb(DATA + b'b', 3, True)])
        states = art._newest_states(db)  # pylint: disable=protected-access
        self.assertEqual(art._store_counts(states, 1, 1), (1, 1, 0))  # pylint: disable=protected-access

    def test_deleted_external_entry_not_counted(self):
        states = art._newest_states(_db([(EXTERNAL + b'c', 1, LIVE), (EXTERNAL + b'c', 2, DELETED)]))  # pylint: disable=protected-access
        self.assertEqual(art._store_counts(states, 1, 1), (0, 0, 0))  # pylint: disable=protected-access

    def test_origin_folder_filter(self):
        self.assertTrue(art._is_origin_folder('IndexedDB/https_www.example.com_0.indexeddb.leveldb'))  # pylint: disable=protected-access
        self.assertFalse(art._is_origin_folder('IndexedDB/https_www.example.com_0.indexeddb.blob'))  # pylint: disable=protected-access
        self.assertFalse(art._is_origin_folder('Storage/ext/x/def/IndexedDB/a.indexeddb.leveldb'))  # pylint: disable=protected-access


# The buckets table as quota_database.cc creates it at schema 11, and schema 10 with its
# type column, which the 10 to 11 migration drops (chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4).
_V11 = ('CREATE TABLE buckets(id INTEGER PRIMARY KEY AUTOINCREMENT, storage_key TEXT NOT NULL, '
        'host TEXT NOT NULL, name TEXT NOT NULL, use_count INTEGER NOT NULL, last_accessed INTEGER NOT NULL, '
        'last_modified INTEGER NOT NULL, expiration INTEGER NOT NULL, quota INTEGER NOT NULL, '
        'persistent INTEGER NOT NULL, durability INTEGER NOT NULL)')
_V10 = _V11.replace('host TEXT NOT NULL, ', 'host TEXT NOT NULL, type INTEGER NOT NULL, ')


def _profile(tmp, schema, rows):
    """A staged profile holding WebStorage/QuotaManager and returning a Store for bucket folder 5."""
    web = os.path.join(tmp, 'Default', 'WebStorage')
    folder = os.path.join(web, '5', 'IndexedDB', 'indexeddb.leveldb')
    os.makedirs(folder)
    if schema is not None:
        db = sqlite3.connect(os.path.join(web, 'QuotaManager'))
        db.execute(schema)
        columns = '(id, storage_key, host, name, use_count, last_accessed, last_modified, expiration, quota, ' \
                  'persistent, durability' + (', type)' if 'type' in schema else ')')
        for bucket_id, key, name in rows:
            values = [bucket_id, key, 'h', name, 0, 0, 0, 0, 0, 0, 0] + ([0] if 'type' in schema else [])
            db.execute(f'INSERT INTO buckets {columns} VALUES ({",".join("?" * len(values))})', values)
        db.commit()
        db.close()
    relative = 'Users/u/AppData/Local/Google/Chrome/User Data/Default/WebStorage/5/IndexedDB/indexeddb.leveldb'
    return SimpleNamespace(path=folder, relative=relative, browser='Google Chrome', profile='Default', user='u',
                           container='c', name='WebStorage/5/IndexedDB/indexeddb.leveldb')


class BucketTest(unittest.TestCase):
    def test_folder_filter(self):
        self.assertEqual(art._bucket_id('WebStorage/17/IndexedDB/indexeddb.leveldb'), 17)  # pylint: disable=protected-access
        self.assertIsNone(art._bucket_id('WebStorage/17/IndexedDB/indexeddb.blob'))  # pylint: disable=protected-access
        self.assertIsNone(art._bucket_id('WebStorage/x/IndexedDB/indexeddb.leveldb'))  # pylint: disable=protected-access
        self.assertIsNone(art._bucket_id('WebStorage/17/CacheStorage/indexeddb.leveldb'))  # pylint: disable=protected-access
        self.assertTrue(art._is_store_folder('WebStorage/3/IndexedDB/indexeddb.leveldb'))  # pylint: disable=protected-access
        self.assertTrue(art._is_store_folder('IndexedDB/https_www.example.com_0.indexeddb.leveldb'))  # pylint: disable=protected-access
        self.assertFalse(art._is_store_folder('Storage/ext/x/def/WebStorage/3/IndexedDB/indexeddb.leveldb'))  # pylint: disable=protected-access

    def _columns(self, schema, rows):
        with tempfile.TemporaryDirectory() as tmp:
            store = _profile(tmp, schema, rows)
            return art._bucket_columns(store, 5, {}, 'test')  # pylint: disable=protected-access

    def test_partitioned_key_both_schemas(self):
        rows = [(5, 'https://embedded.example/^0https://top.example', '_default')]
        for schema in (_V10, _V11):
            self.assertEqual(self._columns(schema, rows), ('https://top.example', '5 (_default)'))

    def test_unpartitioned_named_bucket(self):
        self.assertEqual(self._columns(_V11, [(5, 'https://site.example/', 'drafts')]), ('', '5 (drafts)'))

    def test_other_attribute_kept_whole(self):
        key = 'https://site.example/^112345^267890'
        self.assertEqual(self._columns(_V11, [(5, key, '_default')]), (key, '5 (_default)'))

    def test_no_row_or_no_database(self):
        self.assertEqual(self._columns(_V11, [(4, 'https://site.example/', '_default')]), ('', '5 (no buckets row)'))
        self.assertEqual(self._columns(None, []), ('', '5 (no QuotaManager database)'))


if __name__ == '__main__':
    unittest.main()
