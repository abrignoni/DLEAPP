"""Pin how macosHomeKit reads core.sqlite beside datastore.sqlite."""
import json
import os
import pathlib
import plistlib
import sqlite3
import sys
import tempfile
import unittest
import uuid
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosHomeKit
# pylint: enable=wrong-import-position

HOME = uuid.UUID('11111111-1111-4111-8111-111111111111')
USER = uuid.UUID('22222222-2222-4222-8222-222222222222')
ROOM = uuid.UUID('33333333-3333-4333-8333-333333333333')
ACCESSORY = uuid.UUID('44444444-4444-4444-8444-444444444444')
ACTION_SET = uuid.UUID('55555555-5555-4555-8555-555555555555')


def _handle_archive(text):
    uid = plistlib.UID
    return plistlib.dumps({
        '$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': {'root': uid(1)},
        '$objects': ['$null', {'HMD.URI': uid(2), '$class': uid(4)}, {'prefixedURI': uid(3), '$class': uid(5)}, text,
                     {'$classname': 'HMDAccountHandle', '$classes': ['HMDAccountHandle', 'NSObject']},
                     {'$classname': 'HMDURI', '$classes': ['HMDURI', 'NSObject']}]}, fmt=plistlib.PlistFormat.FMT_BINARY)


def _write_core(path):
    db = sqlite3.connect(path)
    db.executescript('''
        CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER, Z_NAME TEXT, Z_SUPER INTEGER, Z_MAX INTEGER);
        CREATE TABLE ZMKFHOME (Z_PK INTEGER, Z_ENT INTEGER, ZMODELID BLOB, ZNAME TEXT, ZOWNER INTEGER);
        CREATE TABLE ZMKFUSER (Z_PK INTEGER, Z_ENT INTEGER, ZMODELID BLOB, ZHOME INTEGER, ZOWNEDHOME INTEGER,
                               ZUSERID TEXT, ZPRIVILEGE INTEGER, ZREMOTEACCESSALLOWED INTEGER, ZACCOUNTHANDLE BLOB);
        CREATE TABLE ZMKFROOM (Z_PK INTEGER, Z_ENT INTEGER, ZMODELID BLOB, ZHOME INTEGER, ZNAME TEXT);
        CREATE TABLE ZMKFACCESSORY (Z_PK INTEGER, Z_ENT INTEGER, ZMODELID BLOB, ZHOME INTEGER, ZROOM INTEGER,
                                    ZCONFIGUREDNAME TEXT, ZPROVIDEDNAME TEXT, ZMANUFACTURER TEXT, ZMODEL TEXT,
                                    ZSERIALNUMBER TEXT, ZFIRMWAREVERSION TEXT, ZPASSWORD TEXT);
        CREATE TABLE ZMKFACTIONSET (Z_PK INTEGER, Z_ENT INTEGER, ZMODELID BLOB, ZHOME INTEGER, ZNAME TEXT,
                                    ZTYPE TEXT);
    ''')
    db.executemany('INSERT INTO Z_PRIMARYKEY VALUES (?, ?, 0, 1)',
                   [(10, 'MKFHome'), (11, 'MKFUser'), (12, 'MKFRoom'), (21, 'MKFHAPAccessory'), (13, 'MKFActionSet')])
    db.execute('INSERT INTO ZMKFHOME VALUES (1, 10, ?, ?, 1)', (HOME.bytes, 'Synthetic Home'))
    db.execute('INSERT INTO ZMKFUSER VALUES (1, 11, ?, 1, 1, ?, 3, 1, ?)',
               (USER.bytes, 'mailto:owner@example.invalid', _handle_archive('mailto:owner@example.invalid')))
    db.execute('INSERT INTO ZMKFROOM VALUES (1, 12, ?, 1, ?)', (ROOM.bytes, 'Synthetic Room'))
    db.execute('INSERT INTO ZMKFACCESSORY VALUES (1, 21, ?, 1, 1, NULL, ?, ?, ?, ?, ?, ?)',
               (ACCESSORY.bytes, 'Sensor', 'Maker', 'M1', 'SERIAL0', '1.0', 'planted-secret'))
    db.execute('INSERT INTO ZMKFACTIONSET VALUES (1, 13, ?, 1, ?, ?)',
               (ACTION_SET.bytes, 'Good Morning', 'HMActionSetTypeWakeUp'))
    db.commit()
    db.close()


def _write_datastore(path, uuids):
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE record (type TEXT, uuid TEXT, parent_uuid TEXT, encoding INTEGER, record BLOB, '
               'data BLOB)')
    db.executemany('INSERT INTO record VALUES (?, ?, NULL, 0, NULL, NULL)',
                   [('HMDHomeModel', str(u).upper()) for u in uuids])
    db.commit()
    db.close()


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def _run(datastore_uuids=None):
    with tempfile.TemporaryDirectory() as root:
        folder = os.path.join(root, 'Users', 'examiner', 'Library', 'HomeKit')
        os.makedirs(folder)
        files = [os.path.join(folder, 'core.sqlite')]
        _write_core(files[0])
        if datastore_uuids is not None:
            files.append(os.path.join(folder, 'datastore.sqlite'))
            _write_datastore(files[1], datastore_uuids)
        with mock.patch.object(macosHomeKit, 'logfunc'):
            _headers, rows, source = macosHomeKit.macosHomeKit.__wrapped__(FakeContext(files, root))
        return rows, [os.path.relpath(p, root) for p in source.split('\n') if p]


class CoreStoreTest(unittest.TestCase):
    def test_core_rows_when_no_datastore_record_carries_them(self):
        rows, source = _run()
        by_type = {row[2]: row for row in rows}
        self.assertEqual(sorted(by_type), ['MKFActionSet', 'MKFHAPAccessory', 'MKFHome', 'MKFRoom', 'MKFUser'])
        home = str(HOME).upper()
        self.assertEqual(by_type['MKFHome'][3:6], ('Synthetic Home', home, ''))
        self.assertEqual(json.loads(by_type['MKFHome'][6]), {'ZOWNER.ZUSERID': 'mailto:owner@example.invalid'})
        self.assertEqual(json.loads(by_type['MKFUser'][6]),
                         {'ZACCOUNTHANDLE': 'mailto:owner@example.invalid', 'ZPRIVILEGE': 3,
                          'ZREMOTEACCESSALLOWED': 1, 'ZUSERID': 'mailto:owner@example.invalid'})
        accessory = by_type['MKFHAPAccessory']
        self.assertEqual(accessory[3:6], ('Sensor', str(ACCESSORY).upper(), home))
        self.assertEqual(json.loads(accessory[6]), {'ZFIRMWAREVERSION': '1.0', 'ZMANUFACTURER': 'Maker',
                                                    'ZMODEL': 'M1', 'ZSERIALNUMBER': 'SERIAL0'})
        self.assertEqual(json.loads(by_type['MKFActionSet'][6]), {'ZTYPE': 'HMActionSetTypeWakeUp'})
        for row in rows:
            self.assertEqual(row[:2], ('', ''))
            self.assertNotIn('planted-secret', json.dumps(row))
            self.assertEqual(row[-1], os.path.join('Users', 'examiner', 'Library', 'HomeKit', 'core.sqlite'))
        self.assertEqual(source, [os.path.join('Users', 'examiner', 'Library', 'HomeKit', 'core.sqlite')])

    def test_a_uuid_the_datastore_holds_is_not_reported_again(self):
        rows, source = _run(datastore_uuids=[HOME])
        types = [row[2] for row in rows]
        self.assertEqual(types.count('HMDHomeModel'), 1)
        self.assertNotIn('MKFHome', types)
        self.assertEqual(len([t for t in types if t.startswith('MKF')]), 4)
        self.assertEqual(len(source), 2)


if __name__ == '__main__':
    unittest.main()
