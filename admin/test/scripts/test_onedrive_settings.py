"""Pin scripts/onedrive_settings.py on synthetic OneDrive item lists.

The .dat records are built at the offsets of OneDriveExplorer's DAT_FILE_v2b, DAT_FILE_v36,
DAT_FOLDER_v29_v2c and DAT_FOLDER_v2d_v36 layouts; the SQLite tables carry the column names the
client writes. No corpus bytes are used.
"""
import pathlib
import sqlite3
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import onedrive_settings as od  # pylint: disable=wrong-import-position

LAYOUT = {
    0x2b: {'record': 1080, 'ids': 16, 'volume': 152, 'hash': 176, 'last': None, 'size': 200, 'fname': 208,
           'fstatus': 729, 'dname': 176, 'dstatus': 740},
    0x36: {'record': 1232, 'ids': 24, 'volume': 160, 'hash': 184, 'last': 208, 'size': 216, 'fname': 224,
           'fstatus': 745, 'dname': 184, 'dstatus': 748},
}


def _record(version, kind, rid, parent, name, volume=0, index=0, size=0, digest=b'', status=0, last=0):
    spots = LAYOUT[version]
    record = bytearray(spots['record'])
    record[0] = kind
    record[spots['ids']:spots['ids'] + len(rid)] = rid
    record[spots['ids'] + 39:spots['ids'] + 39 + len(parent)] = parent
    struct.pack_into('<QQ', record, spots['volume'], volume, index)
    encoded = name.encode('utf-16-le')
    if kind == od.FILE:
        record[spots['hash']:spots['hash'] + len(digest)] = digest
        struct.pack_into('<Q', record, spots['size'], size)
        record[spots['fname']:spots['fname'] + len(encoded)] = encoded
        struct.pack_into('<H', record, spots['fstatus'], status)
        if spots['last'] is not None:
            struct.pack_into('<I', record, spots['last'], last)
    else:
        record[spots['dname']:spots['dname'] + len(encoded)] = encoded
        record[spots['dstatus']] = status
    return bytes(record)


def _dat(version, records, trailing=b''):
    header = bytearray(od.DAT_HEADER_SIZE)
    struct.pack_into('<I', header, 0, version)
    return bytes(header) + b''.join(records) + trailing


class DatTest(unittest.TestCase):
    def _items(self, version):
        data = _dat(version, [
            _record(version, od.FOLDER, b'AAAA!2', b'AAAA!1', 'Docs', volume=0x1122334455667788,
                    index=(3 << 48) | 500, status=7),
            _record(version, od.FILE, b'AAAA!3', b'AAAA!2', 'plan.docx', volume=0x1122334455667788,
                    index=(5 << 48) | 501, size=1234, digest=bytes(range(20)), status=8, last=1600000000),
            bytes([3]) + bytes(LAYOUT[version]['record'] - 1),
        ], trailing=b'\x00' * 10)
        return od.read_dat(data)

    def test_version_2b_fields(self):
        items, counts, trailing = self._items(0x2b)
        self.assertEqual(counts, {2: 1, 1: 1, 3: 1})
        self.assertEqual(trailing, 10)
        folder, item = items[0], items[1]
        self.assertEqual((folder.name, folder.status, folder.item_index), ('Docs', 7, (3 << 48) | 500))
        self.assertEqual((item.name, item.size, item.status, item.local_hash), ('plan.docx', 1234, 8, bytes(range(20))))
        self.assertIsNone(item.last_change)
        self.assertEqual((item.resource_id, item.parent_id), ('AAAA!3', 'AAAA!2'))
        self.assertEqual(od.paths(items)[id(item)], 'Docs\\plan.docx')

    def test_version_36_fields(self):
        items, _counts, _trailing = self._items(0x36)
        item = items[1]
        self.assertEqual((item.name, item.size, item.status, item.last_change), ('plan.docx', 1234, 8, 1600000000))
        self.assertEqual(item.volume_id, 0x1122334455667788)

    def test_an_unknown_version_is_refused(self):
        with self.assertRaises(ValueError):
            od.read_dat(_dat(0x37, []))
        self.assertIsNone(od.dat_version(b'\x2b\x00'))

    def test_a_parent_loop_ends_the_path(self):
        items = [od.Item(od.FOLDER, 'a', 'b', 'A'), od.Item(od.FOLDER, 'b', 'a', 'B')]
        built = od.paths(items)
        self.assertEqual(built[id(items[0])], 'B\\A')
        self.assertEqual(built[id(items[1])], 'A\\B')


class SyncEngineTest(unittest.TestCase):
    def test_reads_the_columns_a_schema_has(self):
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE od_ClientFile_Records (resourceID TEXT, parentResourceID TEXT, fileName TEXT, '
                   'fileStatus INTEGER, size INTEGER, localHashDigest BLOB, localHashAlgorithm INTEGER, '
                   'volumeID INTEGER, itemIndex INTEGER, lastChange INTEGER)')
        db.execute('CREATE TABLE od_ClientFolder_Records (resourceID TEXT, parentResourceID TEXT, folderName TEXT, '
                   'folderStatus INTEGER, volumeID INTEGER, itemIndex INTEGER)')
        db.execute("INSERT INTO od_ClientFile_Records VALUES ('B!3', 'B!2', 'a.pdf', 8, 10, x'0102', 4, 9, 7, 1700000000)")
        db.execute("INSERT INTO od_ClientFolder_Records VALUES ('B!2', 'B!1', 'Docs', 7, 9, 6)")
        items = od.read_sync_engine(db)
        files = [item for item in items if item.kind == od.FILE]
        self.assertEqual(len(items), 2)
        self.assertEqual((files[0].name, files[0].hash_algorithm, files[0].last_change), ('a.pdf', 4, 1700000000))
        self.assertIsNone(files[0].disk_created)
        self.assertEqual(od.paths(items)[id(files[0])], 'Docs\\a.pdf')

    def test_a_database_without_the_tables_gives_nothing(self):
        self.assertEqual(od.read_sync_engine(sqlite3.connect(':memory:')), [])


if __name__ == '__main__':
    unittest.main()
