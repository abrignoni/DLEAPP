"""Pin the HomeKit Entities artifact (scripts/artifacts/macosHomeKit.py).

The database is built for the test with the columns the artifact reads from datastore.sqlite's record table, and
the record/data blobs are small NSKeyedArchiver property lists built here. The values are made up.
"""
import json
import os
import pathlib
import plistlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosHomeKit as hk
from scripts.macos_plists import mac_absolute_utc
# pylint: enable=wrong-import-position


def data_archive(fields):
    """An NSKeyedArchiver archive (bytes) whose root is a dict of the given str->(str|bytes) fields."""
    objects = ['$null', {}]
    root = objects[1]
    for key, value in fields.items():
        objects.append(value)
        root[key] = plistlib.UID(len(objects) - 1)
    archive = {'$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': {'root': plistlib.UID(1)},
               '$objects': objects}
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)  # pylint: disable=no-member


def record_archive(mtime_cocoa, ctime_cocoa):
    """An NSKeyedArchiver archive (bytes) carrying RecordMtime and RecordCtime NSDate objects."""
    objects = ['$null',
               {'$class': plistlib.UID(3), 'NS.time': mtime_cocoa},
               {'$class': plistlib.UID(3), 'NS.time': ctime_cocoa},
               {'$classname': 'NSDate', '$classes': ['NSDate', 'NSObject']}]
    archive = {'$version': 100000, '$archiver': 'NSKeyedArchiver',
               '$top': {'RecordMtime': plistlib.UID(1), 'RecordCtime': plistlib.UID(2)}, '$objects': objects}
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)  # pylint: disable=no-member


# type, uuid, parent_uuid, encoding, record(mtime,ctime), data fields
ROWS = [
    ('HMDRoomModel', 'U-ROOM', 'U-HOME', 1, (620000000.0, 620000000.0),
     {'name': 'Office', '_t': 'HMDRoomModel', 'blob': b'bplist00\x00rest'}),
    ('HMDHomeModel', 'U-HOME', None, 1, (610000000.0, 600000000.0),
     {'name': 'My Home', 'userID': 'person@example.com', 'raw': b'\x01\x02\x03\x04\x05'}),
    ('HMDCloudLegacyModelObject', 'U-CLOUD', 'U-HOME', 7, (630000000.0, 630000000.0), None),
]


def build(path, rows=None, table=True):
    rows = ROWS if rows is None else rows
    database = sqlite3.connect(path)
    if not table:
        database.execute('CREATE TABLE other (x INTEGER)')
        database.commit()
        database.close()
        return
    database.execute('CREATE TABLE record (type TEXT, uuid TEXT, parent_uuid TEXT, encoding INTEGER NOT NULL, '
                     'record BLOB NOT NULL, data BLOB NOT NULL)')
    for row_type, uuid, parent, encoding, (mtime, ctime), fields in rows:
        rec = record_archive(mtime, ctime)
        data = data_archive(fields) if fields is not None else b'notbplist'
        database.execute('INSERT INTO record VALUES (?,?,?,?,?,?)', (row_type, uuid, parent, encoding, rec, data))
    database.commit()
    database.close()


class HelperTest(unittest.TestCase):
    # pylint: disable=protected-access
    def test_sanitize(self):
        self.assertEqual(hk._sanitize(b'bplist00xx'), '<bplist>')          # pylint: disable=protected-access
        self.assertEqual(hk._sanitize(b'\x01\x02\x03'), '<3 bytes>')       # pylint: disable=protected-access
        self.assertEqual(hk._sanitize({'a': 1, '_t': 'x'}), {'a': 1})      # internal key dropped
        self.assertEqual(hk._sanitize([True, None, 'x']), [True, None, 'x'])

    def test_archive_rejects_non_bplist(self):
        self.assertIsNone(hk._archive(b'notbplist'))                        # pylint: disable=protected-access
        self.assertIsNone(hk._archive(None))                                # pylint: disable=protected-access


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, *top, **kw):
        folder = os.path.join(self.folder.name, *top, 'Library', 'HomeKit')
        os.makedirs(folder)
        path = os.path.join(folder, 'datastore.sqlite')
        build(path, **kw)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(hk, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'):
            result = hk.macosHomeKit.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows(self):
        path = self.database('Users', 'a')
        (headers, rows, located), _ = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 9)
        self.assertEqual((headers[0], headers[1]), (('Record Modified (UTC)', 'datetime'),
                                                    ('Record Created (UTC)', 'datetime')))
        # Room: name decoded, nested bplist marked, dates from the record blob
        self.assertEqual(rows[0], (mac_absolute_utc(620000000.0), mac_absolute_utc(620000000.0), 'HMDRoomModel',
                                   'Office', 'U-ROOM', 'U-HOME', '{"blob": "<bplist>", "name": "Office"}', 'a', rel))
        # Home: separate mtime/ctime, Apple ID in Details, raw bytes marked, no parent
        self.assertEqual(rows[1][:6], (mac_absolute_utc(610000000.0), mac_absolute_utc(600000000.0), 'HMDHomeModel',
                                       'My Home', 'U-HOME', ''))
        self.assertEqual(json.loads(rows[1][6]), {'name': 'My Home', 'userID': 'person@example.com',
                                                  'raw': '<5 bytes>'})
        # encoding != 1: Name and Details blank, but the row and its dates are still reported
        self.assertEqual(rows[2][2:7], ('HMDCloudLegacyModelObject', '', 'U-CLOUD', 'U-HOME', ''))
        self.assertEqual(located, path)

    def test_two_differing_views_fold(self):
        own = self.database('Users', 'a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(own, self.folder.name))
        os.makedirs(os.path.dirname(view))
        differing = [('HMDHomeModel', 'U-HOME', None, 1, (610000000.0, 600000000.0),
                      {'name': 'Different'})] + ROWS[0:1] + ROWS[2:]
        build(view, rows=differing)
        (_, rows, _located), _ = self.run_artifact([view, own])
        self.assertEqual(sum(1 for r in rows if r[2] == 'HMDHomeModel'), 2)   # differ -> two rows
        self.assertEqual(sum(1 for r in rows if r[2] == 'HMDRoomModel'), 1)   # identical -> folded to one

    def test_identical_views_are_read_once(self):
        own = self.database('Users', 'a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(own, self.folder.name))
        os.makedirs(os.path.dirname(view))
        with open(own, 'rb') as handle:
            copy = handle.read()
        with open(view, 'wb') as handle:
            handle.write(copy)
        (_, rows, located), _ = self.run_artifact([view, own])
        self.assertEqual(len(rows), 3)       # one copy's worth of rows, the byte-identical view skipped
        self.assertNotIn('\n', located)      # located names a single database, not both copies

    def test_no_record_table_is_skipped(self):
        path = self.database('Users', 'a', table=False)
        (_, rows, located), logged = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(logged, [f'HomeKit Entities: no record table read from {rel}'])

    def test_decoy_named_file_ignored(self):
        path = self.database('Users', 'a')
        decoy = os.path.join(os.path.dirname(path), 'datastore3.sqlite')
        build(decoy)
        (_, rows, located), _ = self.run_artifact([decoy, path])
        self.assertEqual(len(rows), 3)
        self.assertNotIn('datastore3.sqlite', located)

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
