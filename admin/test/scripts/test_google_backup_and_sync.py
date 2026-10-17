"""Pin the rows of the legacy Google Drive desktop client (Backup and Sync) artifacts on synthetic stores."""
import datetime
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import googleBackupAndSync as gbs
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc


def make_db(path, statements):
    connection = sqlite3.connect(path)
    for statement in statements:
        connection.execute(statement)
    connection.commit()
    connection.close()


NEW_SCHEMA = [
    'CREATE TABLE cloud_entry (doc_id TEXT NOT NULL, filename TEXT, modified INTEGER, created INTEGER, '
    'acl_role INTEGER, doc_type INTEGER, removed INTEGER, size INTEGER, checksum TEXT, shared INTEGER, '
    'resource_type TEXT, original_size INTEGER, original_checksum TEXT, down_sample_status INTEGER, '
    'PRIMARY KEY (doc_id))',
    'CREATE TABLE cloud_relations (child_doc_id TEXT NOT NULL, parent_doc_id TEXT NOT NULL)',
    'CREATE TABLE local_entry (inode INTEGER NOT NULL, volume TEXT NOT NULL, filename TEXT, modified INTEGER, '
    'checksum TEXT, size INTEGER, is_folder INTEGER, PRIMARY KEY (inode, volume))',
    'CREATE TABLE local_relations (child_inode INTEGER NOT NULL, child_volume TEXT NOT NULL, '
    'parent_inode INTEGER NOT NULL, parent_volume TEXT NOT NULL)',
    'CREATE TABLE mapping (inode INTEGER NOT NULL, volume TEXT NOT NULL, doc_id TEXT NOT NULL)',
    "INSERT INTO cloud_entry (doc_id, filename, doc_type) VALUES ('root', 'root', 0)",
    "INSERT INTO cloud_entry VALUES ('F1', 'Folder', 1000, NULL, 0, 0, 0, NULL, NULL, 0, NULL, NULL, NULL, 0)",
    "INSERT INTO cloud_entry VALUES ('D1', 'a.txt', 1600000000, 1500000000, 0, 1, 0, 5, 'abc', 1, NULL, NULL, "
    "NULL, 0)",
    "INSERT INTO cloud_entry VALUES ('C1', 'cloud only.txt', 1600000100, NULL, 0, 1, 0, 7, 'def', 0, NULL, "
    "NULL, NULL, 0)",
    "INSERT INTO cloud_relations VALUES ('F1', 'root')",
    "INSERT INTO cloud_relations VALUES ('D1', 'F1')",
    "INSERT INTO cloud_relations VALUES ('D1', 'root')",
    "INSERT INTO cloud_relations VALUES ('C1', 'root')",
    "INSERT INTO local_entry VALUES (1, 'v', '\\\\?\\C:\\Users\\u\\Google Drive', NULL, NULL, NULL, 1)",
    "INSERT INTO local_entry VALUES (2, 'v', 'Folder', 1000, NULL, NULL, 1)",
    "INSERT INTO local_entry VALUES (3, 'v', 'a.txt', 1600000000, 'abc', 5, 0)",
    "INSERT INTO local_entry VALUES (4, 'v', 'local only.txt', 1600000200, 'ghi', 9, 0)",
    "INSERT INTO local_relations VALUES (2, 'v', 1, 'v')",
    "INSERT INTO local_relations VALUES (3, 'v', 2, 'v')",
    "INSERT INTO local_relations VALUES (4, 'v', 1, 'v')",
    "INSERT INTO mapping VALUES (1, 'v', 'root')",
    "INSERT INTO mapping VALUES (2, 'v', 'F1')",
    "INSERT INTO mapping VALUES (3, 'v', 'D1')",
    "INSERT INTO mapping VALUES (99, 'v', 'missing')",
]

OLD_SCHEMA = [
    'CREATE TABLE cloud_entry (resource_id TEXT, filename TEXT, modified INTEGER, created INTEGER, '
    'acl_role INTEGER, doc_type INTEGER, removed INTEGER, url TEXT, size INTEGER, checksum TEXT, '
    'shared INTEGER, PRIMARY KEY (resource_id))',
    'CREATE TABLE cloud_relations (child_resource_id TEXT, parent_resource_id TEXT)',
    'CREATE TABLE local_entry (inode_number INTEGER, filename TEXT, modified INTEGER, checksum TEXT, '
    'size INTEGER, PRIMARY KEY (inode_number))',
    'CREATE TABLE local_relations (child_inode_number INTEGER, parent_inode_number INTEGER)',
    'CREATE TABLE mapping (inode_number INTEGER, resource_id TEXT)',
    "INSERT INTO cloud_entry (resource_id, filename, doc_type) VALUES ('folder:root', 'root', 0)",
    "INSERT INTO cloud_entry VALUES ('file:1', 'b.txt', 1390867885, 1390867884, 0, 1, 0, 'u', 3, 'x', 0)",
    "INSERT INTO cloud_relations VALUES ('file:1', 'folder:root')",
    "INSERT INTO local_entry VALUES (10, '/Users/u/Google Drive', NULL, NULL, NULL)",
    "INSERT INTO local_entry VALUES (11, 'b.txt', 1390867885, 'x', 3)",
    "INSERT INTO local_relations VALUES (11, 10)",
    "INSERT INTO mapping VALUES (10, 'folder:root')",
    "INSERT INTO mapping VALUES (11, 'file:1')",
]


class Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return 'rel/' + os.path.basename(path)


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def db(self, statements):
        path = os.path.join(self.tmp.name, 'snapshot.db')
        make_db(path, statements)
        return path

    def test_new_schema_pairs_local_and_cloud_and_keeps_unmapped_entries(self):
        rows = gbs.snapshot_rows(self.db(NEW_SCHEMA), 'rel/snapshot.db')
        by_doc = {row[14]: row for row in rows}
        self.assertEqual(len(rows), 5)  # 3 mapped, 1 local only, 1 cloud only; the dangling mapping is dropped
        file_row = by_doc['D1']
        self.assertEqual(file_row[0], datetime.datetime.fromtimestamp(1600000000, tz=UTC))
        self.assertEqual(file_row[2], datetime.datetime.fromtimestamp(1500000000, tz=UTC))
        self.assertEqual(file_row[3], '\\\\?\\C:\\Users\\u\\Google Drive\\Folder\\a.txt')
        self.assertEqual(file_row[4].split('\n'), ['root/Folder/a.txt', 'root/a.txt'])
        self.assertEqual(file_row[5:10], (0, 5, 'abc', 5, 'abc'))
        self.assertEqual(file_row[15:], (3, 'v', 'rel/snapshot.db'))
        self.assertEqual(by_doc['C1'][3], '')
        self.assertEqual(by_doc['C1'][4], 'root/cloud only.txt')
        local_only = [row for row in rows if row[14] == '']
        self.assertEqual(len(local_only), 1)
        self.assertTrue(local_only[0][3].endswith('Google Drive\\local only.txt'))
        self.assertEqual(local_only[0][1], '')

    def test_old_schema_reads_the_same_way(self):
        rows = gbs.snapshot_rows(self.db(OLD_SCHEMA), 'rel/snapshot.db')
        self.assertEqual(len(rows), 2)
        file_row = [row for row in rows if row[14] == 'file:1'][0]
        self.assertEqual(file_row[0], datetime.datetime(2014, 1, 28, 0, 11, 25, tzinfo=UTC))
        self.assertEqual(file_row[3], '/Users/u/Google Drive/b.txt')
        self.assertEqual(file_row[4], 'root/b.txt')
        self.assertEqual(file_row[5], '')

    def test_a_parent_loop_ends_the_walk(self):
        names = {'a': 'A', 'b': 'B'}
        parents = {'a': ['b'], 'b': ['a']}
        self.assertEqual(gbs.build_paths(names, parents, 'a', '/'), ['B/A'])

    def test_artifact_reads_each_snapshot_and_skips_sidecars(self):
        path = self.db(NEW_SCHEMA)
        headers, rows, source = gbs.googleBackupSyncItems.__wrapped__(Context([path, path + '-wal']))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(source, path)


class OtherStoresTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_cloud_graph_rows_carry_version_and_change_stamp(self):
        path = os.path.join(self.tmp.name, 'cloud_graph.db')
        make_db(path, [
            'CREATE TABLE cloud_graph_entry (doc_id TEXT, filename TEXT, modified INTEGER, created INTEGER, '
            'acl_role INTEGER, doc_type INTEGER, removed INTEGER, size INTEGER, checksum TEXT, '
            'change_stamp INTEGER, is_zombie INTEGER, shared INTEGER, version INTEGER)',
            'CREATE TABLE cloud_relations (child_doc_id TEXT, parent_doc_id TEXT)',
            "INSERT INTO cloud_graph_entry VALUES ('root', 'root', NULL, NULL, NULL, 0, NULL, NULL, NULL, 1, 0, "
            "0, 1)",
            "INSERT INTO cloud_graph_entry VALUES ('S', 'shared.pdf', 1600000000, NULL, 2, 1, 0, 10, 'c', 90, 0, "
            "1, 3)",
            "INSERT INTO cloud_relations VALUES ('S', 'root')",
        ])
        rows = gbs.cloud_graph_rows(path, 'rel')
        shared = [row for row in rows if row[11] == 'S'][0]
        self.assertEqual(shared[2], 'root/shared.pdf')
        self.assertEqual(shared[6], 1)
        self.assertEqual(shared[8], 2)
        self.assertEqual(shared[9:11], (3, 90))
        self.assertEqual(shared[1], '')

    def test_pending_changes_join_the_buffer_entry(self):
        path = os.path.join(self.tmp.name, 'change1.db')
        make_db(path, [
            'CREATE TABLE fschanges (identifier INTEGER PRIMARY KEY, direction TEXT, action TEXT, '
            'full_path TEXT, is_folder INTEGER, doc_id TEXT, parent_doc_id TEXT)',
            'CREATE TABLE change_buffer_entries (identifier INTEGER, state INTEGER, fschange INTEGER, '
            'failure_count INTEGER, time INTEGER)',
            "INSERT INTO fschanges VALUES (5, 'UPLOAD', 'DELETE', 'C:\\x\\y.txt', 0, NULL, NULL)",
            'INSERT INTO change_buffer_entries VALUES (4, 1, 5, 0, 700000)',
        ])
        self.assertEqual(gbs.pending_change_rows(path, 'rel'),
                         [('UPLOAD', 'DELETE', 'C:\\x\\y.txt', 0, '', '', 1, 0, 5, 'rel')])

    def test_a_pickled_setting_is_described_not_decoded(self):
        self.assertEqual(gbs.setting_value('gAJ9cQAu'), '(base64 Python pickle, 8 characters, not decoded)')
        self.assertEqual(gbs.setting_value('user@example.com'), 'user@example.com')
        self.assertEqual(gbs.setting_value(None), '')


class SyncLogTest(unittest.TestCase):
    LOG = ('stray line\n'
           '2018-03-27 19:46:51,819 -0400 INFO pid=9020 7832:MainThread      main.py:259 First\n'
           '  continued\x0bwith a vertical tab\n'
           '2018-03-27 19:46:52,000 +0530 ERROR pid=9020 12:Worker-1 common.sync:12 Second\n')

    def test_entries_lines_and_utc(self):
        counts = Counter()
        entries = gbs.log_entries(gbs.file_lines(self.LOG), counts)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0][6], 'stray line')
        self.assertEqual(entries[0][0], '')
        first = entries[1]
        self.assertEqual(first[0], datetime.datetime(2018, 3, 27, 23, 46, 51, 819000, tzinfo=UTC))
        self.assertEqual(first[1:6], ('2018-03-27 19:46:51,819 -0400', 'INFO', '9020', '7832:MainThread',
                                      'main.py:259'))
        self.assertEqual(first[6], 'First\n  continued\x0bwith a vertical tab')
        self.assertEqual(first[7], 2)
        self.assertEqual(entries[2][0], datetime.datetime(2018, 3, 27, 14, 16, 52, tzinfo=UTC))
        self.assertEqual(entries[2][7], 4)
        self.assertEqual(counts, Counter({'entries': 2, 'continuation lines': 1,
                                          'lines before the first entry': 1}))


if __name__ == '__main__':
    unittest.main()
