"""Firefox IndexedDB reader cases; every buffer and key is built by hand for the test."""

import json
import pathlib
import sqlite3
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox_indexeddb as idb  # pylint: disable=wrong-import-position

BASE = 0xFFFF0000


def pair(tag, data=0):
    return struct.pack('<Q', (tag << 32) | data)


def word(value):
    return struct.pack('<Q', value)


def latin1(text):
    raw = text.encode('latin-1')
    return pair(BASE + 4, len(raw) | (1 << 31)) + raw + b'\x00' * ((-len(raw)) & 7)


def utf16(text):
    raw = text.encode('utf-16-le')
    return pair(BASE + 4, len(text)) + raw + b'\x00' * ((-len(raw)) & 7)


def snappy_literals(data):
    """A valid raw Snappy stream made only of literals, from the format description."""
    out, size = bytearray(), len(data)
    while True:
        byte = size & 0x7F
        size >>= 7
        out.append(byte | (0x80 if size else 0))
        if not size:
            break
    for start in range(0, len(data), 60):
        chunk = data[start:start + 60]
        out.append((len(chunk) - 1) << 2)
        out += chunk
    return bytes(out)


HEADER = pair(0xFFF10000, 2)
END = pair(BASE + 0x13)


class CloneReaderTest(unittest.TestCase):

    def test_object_with_each_ported_type(self):
        buffer = (HEADER + pair(BASE + 8)                        # object
                  + latin1('n') + pair(BASE + 3, 0xFFFFFFFF)       # n: -1
                  + latin1('s') + utf16('é✓')                      # s: two-byte string
                  + latin1('d') + struct.pack('<d', 1.5)           # d: 1.5
                  + latin1('a') + pair(BASE + 7, 2)                # a: [true, null]
                  + pair(BASE + 3, 0) + pair(BASE + 2, 1) + pair(BASE + 3, 1) + pair(BASE) + END
                  + latin1('t') + pair(BASE + 5) + struct.pack('<d', 86400000.0)
                  + latin1('m') + pair(BASE + 0x11) + latin1('k') + pair(BASE + 3, 7) + END
                  + latin1('z') + pair(BASE + 0x12) + pair(BASE + 3, 9) + END
                  + latin1('b') + pair(BASE + 0x1F) + word(3) + b'\x01\x02\x03' + b'\x00' * 5
                  + latin1('o') + pair(BASE + 8) + latin1('x') + pair(BASE + 3, 1)
                  + pair(BASE)                                     # legacy null ends the object
                  + latin1('r') + pair(BASE + 0xD, 0)             # back reference to the object
                  + END)
        value, trailing = idb.clone_value(buffer)
        self.assertEqual(trailing, 0)
        self.assertEqual(value, {'n': -1, 's': 'é✓', 'd': 1.5, 'a': [True, None],
                                 't': {'$date': '1970-01-02T00:00:00Z'},
                                 'm': {'$map': [['k', 7]]}, 'z': {'$set': [9]},
                                 'b': {'$arraybuffer': '010203'}, 'o': {'x': 1},
                                 'r': {'$backref': 0}})

    def test_dom_tags_and_invalid_back_references_stop_decoding(self):
        with self.assertRaises(idb.NotDecoded) as blob:
            idb.clone_value(HEADER + pair(BASE + 8) + latin1('f') + pair(0xFFFF8001, 0) + END)
        self.assertEqual(str(blob.exception), 'SCTAG_DOM_BLOB')
        with self.assertRaises(idb.NotDecoded) as typed:
            idb.clone_value(HEADER + pair(BASE + 0x20, 1) + word(0))
        self.assertEqual(str(typed.exception), 'SCTAG_TYPED_ARRAY_OBJECT')
        with self.assertRaises(ValueError):
            idb.clone_value(HEADER + pair(BASE + 0xD, 5))
        with self.assertRaises(ValueError):
            idb.clone_value(HEADER + pair(BASE + 8) + latin1('open'))


class KeyDecoderTest(unittest.TestCase):

    def test_number_string_array_date_and_binary_keys(self):
        one = b'\x10\xbf\xf0'                         # 1.0, trailing zero bytes trimmed
        self.assertEqual(idb.decode_key(one), 1)
        minus_two = b'\x10' + struct.pack('>Q', (-0xC000000000000000) & 0xFFFFFFFFFFFFFFFF)
        self.assertEqual(idb.decode_key(minus_two), -2)
        self.assertEqual(idb.decode_key(b'\x30\x62\x63'), 'ab')
        self.assertEqual(idb.decode_key(b'\x30\x80\x83\x00'), 'Ă')   # two-byte form for U+0102
        self.assertEqual(idb.decode_key(b'\x80\x62\x00\x10\xbf\xf0' + b'\x00' * 6 + b'\x00'), ['a', 1])
        self.assertEqual(idb.decode_key(b'\x20\xc0\x59\x00\x00\x00\x00\x00\x00'),
                         {'$date': '1970-01-01T00:00:00.100000Z'})
        self.assertEqual(idb.decode_key(b'\x40\x01\x02'), {'$binary': '0001'})
        for bad in (b'', b'\x99'):
            with self.assertRaises(ValueError):
                idb.decode_key(bad)
        with self.assertRaises(TypeError):
            idb.decode_key(12345)


class ReadIndexedDBTest(unittest.TestCase):

    def test_store_rows_status_and_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store = (root/'Users'/'tester'/'Library'/'Application Support'/'Firefox'/'Profiles'/
                     'ab12.default-release'/'storage'/'default'/'https+++example.test'/'idb'/'1234abcd.sqlite')
            store.parent.mkdir(parents=True)
            db = sqlite3.connect(store)
            db.executescript('''CREATE TABLE database(name TEXT, origin TEXT, version INTEGER);
                CREATE TABLE object_store(id INTEGER PRIMARY KEY, auto_increment INTEGER, name TEXT, key_path TEXT);
                CREATE TABLE object_data(object_store_id INTEGER, key BLOB, index_data_values BLOB,
                    file_ids TEXT, data BLOB);
                INSERT INTO database VALUES('chat', 'https://example.test', 1);
                INSERT INTO object_store VALUES(1, 0, 'messages', 'id');''')
            good = snappy_literals(HEADER + pair(BASE + 8) + latin1('id') + pair(BASE + 3, 5) + END)
            blob = snappy_literals(HEADER + pair(0xFFFF8001, 0))
            db.execute('INSERT INTO object_data VALUES(1, ?, NULL, NULL, ?)', (b'\x10\xc0\x14', good))
            db.execute('INSERT INTO object_data VALUES(1, ?, NULL, ?, ?)', (b'\x10\xc0\x18', '1', blob))
            db.execute('INSERT INTO object_data VALUES(1, ?, NULL, ?, ?)', (b'\x10\xc0\x1c', '2', (1 << 32) | 0))
            db.commit()
            db.close()

            class Context:
                def get_files_found(self):
                    return [str(store)]

                def get_relative_path(self, path):
                    return str(pathlib.Path(path).relative_to(root))
            with patch.object(idb, 'logfunc') as logged:
                rows, _ = idb.read_indexeddb(Context(), 'Firefox IndexedDB')
            self.assertEqual([row[5] for row in rows],
                             ['Decoded', 'Not decoded: SCTAG_DOM_BLOB', 'Not decoded: stored in a file'])
            first = rows[0]
            self.assertEqual(first[:5], ('https://example.test', 'chat', 'messages', '5', '{"id":5}'))
            self.assertEqual(json.loads(first[3]), json.loads(first[4])['id'])
            self.assertEqual((first[7], first[8]), ('ab12.default-release', 'tester'))
            self.assertEqual(rows[1][6], '1')
            self.assertTrue(any('SCTAG_DOM_BLOB' in str(call) for call in logged.call_args_list))


if __name__ == '__main__':
    unittest.main()
