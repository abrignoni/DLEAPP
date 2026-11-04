"""Pin the record counting in scripts/artifacts/chromiumIndexedDb.py.

Keys are built with the reader's own prefix encoder for database 1, object store 1:
index id 1 holds the object store data and index id 3 the external object entries, as
in Chromium's IndexedDB LevelDB coding scheme. Expected values are written out.
"""
import pathlib
import sys
import unittest
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import chromiumIndexedDb as art  # pylint: disable=wrong-import-position
from scripts.ccl import ccl_chromium_indexeddb as idb  # pylint: disable=wrong-import-position
from scripts.ccl import ccl_leveldb  # pylint: disable=wrong-import-position

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


if __name__ == '__main__':
    unittest.main()
