"""Pin the Dropbox desktop artifacts on a synthetic AppData tree laid out like a Windows install.

Every name, ID and time below is invented; the layout (key file, page encryption, protobuf field
numbers, icon.db pickles) follows what the artifacts' notes describe.
"""
# pylint: disable=protected-access
import base64
import ctypes
import ctypes.util
import hashlib
import hmac
import json
import os
import pathlib
import pickle
import sqlite3
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from Crypto.Cipher import AES
from scripts.artifacts import dropboxDesktop as dd
# pylint: enable=wrong-import-position

ROOT = b'\xff' * 16
FOLDER = bytes.fromhex('0123456789abcdef0000000000000010')
PHOTO = bytes.fromhex('0123456789abcdef0000000000000021')
GONE = bytes.fromhex('0123456789abcdef0000000000000007')
PNG = b'\x89PNG\r\n\x1a\n' + bytes(range(200))
DROPBOX = 'C:\\Users\\tester\\Dropbox'


def field(number, payload):
    if isinstance(payload, int):
        out, value = bytearray(), payload
        out += bytes([number << 3])
        while True:
            byte = value & 0x7f
            value >>= 7
            out.append(byte | (0x80 if value else 0))
            if not value:
                return bytes(out)
    length = len(payload)
    head = bytearray([(number << 3) | 2])
    while True:
        byte = length & 0x7f
        length >>= 7
        head.append(byte | (0x80 if length else 0))
        if not length:
            break
    return bytes(head) + payload


def node(key, parent, name, content=None):
    body = field(1, key) + field(2, parent) + field(3, name.encode()) + field(4, field(1, 1))
    if content is None:
        return body + field(6, b'')
    digest, size = content
    return body + field(5, field(1, field(1, digest) + field(2, size)))


def remote_value(inner, client_modified, server_time):
    return field(1, inner) + field(2, client_modified) + field(3, field(1, 1000) + field(2, server_time))


def local_value(inner, filetime):
    return field(1, inner) + field(2, field(1, filetime)) + field(3, 0x0001000000001234)


def write_key_file(path, user_key):
    head = struct.pack('<II', 0, len(user_key)) + user_key
    with open(path, 'wb') as handle:
        handle.write(head + hmac.new(dd._KS_HMAC_KEY, head, hashlib.md5).digest())


def make_reserved_db(path, rows):
    """A SQLite database with 12 reserved bytes per page, through SQLITE_FCNTL_RESERVE_BYTES."""
    name = ctypes.util.find_library('sqlite3')
    if not name:
        return False
    lib = ctypes.CDLL(name)
    handle = ctypes.c_void_p()
    if lib.sqlite3_open(path.encode(), ctypes.byref(handle)) != 0:
        return False
    try:
        reserve = ctypes.c_int(12)
        if lib.sqlite3_file_control(handle, b'main', 38, ctypes.byref(reserve)) != 0:
            return False
        statements = ['PRAGMA page_size=4096',
                      'CREATE TABLE config (key TEXT PRIMARY KEY NOT NULL, value BLOB)']
        statements += [f"INSERT INTO config VALUES ('{k}', '{v.replace(chr(39), chr(39) * 2)}')"
                       if isinstance(v, str) else f"INSERT INTO config VALUES ('{k}', {v})" for k, v in rows]
        for statement in statements:
            if lib.sqlite3_exec(handle, statement.encode(), None, None, None) != 0:
                return False
    finally:
        lib.sqlite3_close(handle)
    with open(path, 'rb') as stream:
        return stream.read(21)[20] == 12


def encrypt_database(plain, key):
    """Written independently of the reader: AES-128-OFB per page, the nonce in the page tail."""
    page_size = struct.unpack('>H', plain[16:18])[0]
    reserved = plain[20]
    out = bytearray()
    for number in range(len(plain) // page_size):
        page = bytearray(plain[number * page_size:(number + 1) * page_size])
        nonce = os.urandom(12)
        page[page_size - 12:] = nonce
        iv = struct.pack('<I', number + 1) + nonce
        encrypted = bytearray(AES.new(key, AES.MODE_OFB, iv=iv).encrypt(bytes(page[:page_size - reserved])))
        encrypted += page[page_size - reserved:]
        if number == 0:
            encrypted[16:24] = page[16:24]
        out += encrypted
    return bytes(out)


def make_db(path, statements, rows=()):
    connection = sqlite3.connect(path)
    for statement in statements:
        connection.execute(statement)
    for sql, values in rows:
        connection.execute(sql, values)
    connection.commit()
    connection.close()


class Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return 'rel/' + os.path.basename(path)


class SyntheticTree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = os.path.join(self.tmp.name, 'Users', 'tester', 'AppData', 'Local', 'Dropbox')
        self.instance = os.path.join(base, 'instance1')
        os.makedirs(os.path.join(self.instance, 'sync'))
        self.files = []

        info = os.path.join(base, 'info.json')
        with open(info, 'w', encoding='utf-8') as handle:
            json.dump({'personal': {'path': DROPBOX, 'host': 1, 'is_team': False,
                                    'subscription_type': 'Basic'}}, handle)
        self.files.append(info)

        self.user_key = bytes(range(16))
        ks_path = os.path.join(self.instance, 'ks_Client1')
        write_key_file(ks_path, self.user_key)
        self.files.append(ks_path)

        nucleus = os.path.join(self.instance, 'sync', 'nucleus.sqlite3')
        folder = node(FOLDER, ROOT, 'Case Folder')
        photo = node(PHOTO, FOLDER, 'Photo.JPG', (b'\x11' * 32, 1234))
        make_db(nucleus, [f'CREATE TABLE {t} (key BLOB PRIMARY KEY, value BLOB NOT NULL) WITHOUT ROWID'
                          for t in ('local_tree', 'remote_tree', 'synced_tree', 'remote_tombstones')]
                + ['CREATE TABLE config (key INTEGER PRIMARY KEY, value BLOB NOT NULL)'],
                [('INSERT INTO remote_tree VALUES (?, ?)', (FOLDER, remote_value(folder, 1700000000, 1700000001))),
                 ('INSERT INTO remote_tree VALUES (?, ?)', (PHOTO, remote_value(photo, 1690000000, 1700000100))),
                 ('INSERT INTO local_tree VALUES (?, ?)', (PHOTO, local_value(photo, 133345312000000000))),
                 ('INSERT INTO synced_tree VALUES (?, ?)', (PHOTO, field(2, photo))),
                 ('INSERT INTO remote_tombstones VALUES (?, ?)',
                  (GONE, field(1, GONE) + field(2, field(1, 1000) + field(2, 1700000200))))])
        self.files.append(nucleus)

        local_photo = DROPBOX + '\\Case Folder\\Photo.JPG'
        history = os.path.join(self.instance, 'sync_history.db')
        make_db(history, ['CREATE TABLE sync_history (event_type TEXT NOT NULL, file_event_type TEXT, '
                          'direction TEXT, file_id TEXT, local_path TEXT, server_path TEXT, other_user INTEGER, '
                          'timestamp INTEGER NOT NULL)'],
                [('INSERT INTO sync_history VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  ('file', 'add', 'upload', base64.urlsafe_b64encode(PHOTO).decode().rstrip('='),
                   local_photo, '42:/Case Folder/Photo.JPG', 0, 1700000101))])
        self.files.append(history)

        icon = os.path.join(self.instance, 'icon.db')
        make_db(icon, ['CREATE TABLE path_icon_table (created_time INTEGER NOT NULL, file_mtime INTEGER, '
                       'file_path TEXT NOT NULL, image BLOB NOT NULL, PRIMARY KEY (file_path))'],
                [('INSERT INTO path_icon_table VALUES (?, ?, ?, ?)',
                  (1700000102, None, 'tpng' + local_photo.lower() + '_256', pickle.dumps(PNG, protocol=2)))])
        self.files.append(icon)

        self.config_ok = make_reserved_db(
            os.path.join(self.tmp.name, 'plain.sqlite'),
            [('email', 'tester@example.com'), ('account_id', 'dbid:AAAexample'),
             ('sync_root_account_uid', 1000), ('dropbox_path', DROPBOX), ('first_link_ts', 1690000000),
             ('SUCCESSFUL_STARTUP', '1.2.3'), ('oauth_refresh_token_v2', 'secret-value')])
        if self.config_ok:
            with open(os.path.join(self.tmp.name, 'plain.sqlite'), 'rb') as handle:
                plain = handle.read()
            config = os.path.join(self.instance, 'config.dbx')
            key = hashlib.pbkdf2_hmac('sha1', self.user_key, dd._KS_APP_KEY, 1066, 16)
            with open(config, 'wb') as handle:
                handle.write(encrypt_database(plain, key))
            self.files.append(config)
        self.media = mock.patch.object(dd, 'check_in_embedded_media', side_effect=self._media)
        self.media.start()
        self.addCleanup(self.media.stop)
        self.checked_in = []

    def _media(self, source, data, **_):
        self.checked_in.append((os.path.basename(source), data))
        return f'media-{len(self.checked_in)}'

    def test_key_file_and_bad_hmac(self):
        ks_path = os.path.join(self.instance, 'ks_Client1')
        self.assertEqual(dd.database_key(ks_path),
                         hashlib.pbkdf2_hmac('sha1', self.user_key, dd._KS_APP_KEY, 1066, 16))
        with open(ks_path, 'r+b') as handle:
            handle.seek(-1, 2)
            last = handle.read(1)
            handle.seek(-1, 2)
            handle.write(bytes([last[0] ^ 1]))
        self.assertIsNone(dd.database_key(ks_path))

    def test_linked_account_decrypts_and_leaves_credentials_out(self):
        if not self.config_ok:
            self.skipTest('libsqlite3 could not be loaded to write a reserved-bytes database')
        _, rows, source = dd.dropboxLinkedAccount.__wrapped__(Context(self.files))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[0], datetime.fromtimestamp(1690000000, tz=timezone.utc))
        self.assertEqual(row[2:8], ('tester@example.com', '', 'dbid:AAAexample', 1000, '', DROPBOX))
        self.assertEqual(row[8], '1.2.3')
        self.assertNotIn('secret-value', repr(rows))
        self.assertIn('config.dbx', source)
        self.assertIn('ks_Client1', source)

    def test_wrong_key_gives_no_row(self):
        if not self.config_ok:
            self.skipTest('libsqlite3 could not be loaded to write a reserved-bytes database')
        write_key_file(os.path.join(self.instance, 'ks_Client1'), b'\x00' * 16)
        _, rows, _ = dd.dropboxLinkedAccount.__wrapped__(Context(self.files))
        self.assertEqual(rows, [])

    def test_sync_history_row_carries_its_thumbnail(self):
        headers, rows, _ = dd.dropboxSyncHistory.__wrapped__(Context(self.files))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][headers.index(('Thumbnail', 'media'))], 'media-1')
        self.assertEqual(self.checked_in, [('icon.db', PNG)])
        self.assertEqual(rows[0][headers.index('Node Key')], PHOTO.hex())

    def test_engine_items_paths_kinds_tombstone_and_thumbnail(self):
        headers, rows, _ = dd.dropboxNucleusItems.__wrapped__(Context(self.files))
        by_key = {row[headers.index('Node Key')]: row for row in rows}
        self.assertEqual(set(by_key), {FOLDER.hex(), PHOTO.hex(), GONE.hex()})
        photo = by_key[PHOTO.hex()]
        self.assertEqual(photo[headers.index('Path')], '/Case Folder/Photo.JPG')
        self.assertEqual(photo[headers.index('Kind')], 'File')
        self.assertEqual(photo[headers.index('Size')], 1234)
        self.assertEqual(photo[headers.index(('Thumbnail', 'media'))], 'media-1')
        self.assertEqual(by_key[FOLDER.hex()][headers.index('Kind')], 'Folder')
        self.assertEqual(by_key[GONE.hex()][headers.index('Tombstone')], 'Yes')
        self.assertEqual(by_key[GONE.hex()][headers.index(('Tombstone Time (UTC)', 'datetime'))],
                         datetime.fromtimestamp(1700000200, tz=timezone.utc))

    def test_thumbnail_index_is_scoped_to_its_instance(self):
        other = os.path.join(self.tmp.name, 'Users', 'other', 'AppData', 'Local', 'Dropbox', 'instance1')
        self.assertEqual(dd._thumbnails(Context(self.files), other).media(
            DROPBOX + '\\Case Folder\\Photo.JPG'), '')

    def test_pickle_with_other_callable_is_refused(self):
        self.assertEqual(dd.thumbnail_bytes(pickle.dumps(PNG, protocol=2)), PNG)
        blob = b'\x80\x02cos\nsystem\nq\x00X\x04\x00\x00\x00trueq\x01\x85q\x02Rq\x03.'
        self.assertIsNone(dd.thumbnail_bytes(blob))


if __name__ == '__main__':
    unittest.main()
