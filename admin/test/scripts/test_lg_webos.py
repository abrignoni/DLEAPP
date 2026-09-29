"""Pin how the LG webOS artifacts read the TV's download history, preferences, Local Storage and apps.

Every value here is made up for the test.
"""
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import lgWebos
# pylint: enable=wrong-import-position


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def make_db(path, statements):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as con:
        for sql, *args in statements:
            con.execute(sql, *args)
    con.close()
    return path


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))
    return path


class DecodeTest(unittest.TestCase):
    def test_utf16le_bytes_decode_and_other_bytes_become_hex(self):
        self.assertEqual(lgWebos.decode_value('hello'.encode('utf-16-le')), ('hello', 'UTF-16LE'))
        self.assertEqual(lgWebos.decode_value(b'\x01\x02\x03'), ('010203', 'hex'))
        self.assertEqual(lgWebos.decode_value(b'\x00\xd8'), ('00d8', 'hex'))

    def test_history_fields_are_blank_when_not_an_object(self):
        self.assertEqual(lgWebos.history_fields('null'), ('',) * len(lgWebos.HISTORY_FIELDS))
        self.assertEqual(lgWebos.history_fields('[1, 2]'), ('',) * len(lgWebos.HISTORY_FIELDS))
        fields = lgWebos.history_fields(json.dumps({'url': 'http://example.test/a.ipk', 'httpStatus': 200,
                                                    'errorText': None}))
        self.assertEqual(fields[0], 'http://example.test/a.ipk')
        self.assertEqual(fields[lgWebos.HISTORY_FIELDS.index('httpStatus')], 200)
        self.assertEqual(fields[lgWebos.HISTORY_FIELDS.index('errorText')], '')


class ArtifactTest(unittest.TestCase):
    def test_download_history_and_preferences(self):
        with tempfile.TemporaryDirectory() as root:
            dl = make_db(os.path.join(root, 'vol', 'var', 'luna', 'data', 'downloadhistory.db'), [
                ('CREATE TABLE DownloadHistory (ticket INTEGER PRIMARY KEY, owner TEXT, interface TEXT, '
                 'state TEXT, history TEXT)',),
                ('INSERT INTO DownloadHistory VALUES (1, ?, ?, ?, ?)',
                 ('com.example.installer', 'wifi', 'completed',
                  json.dumps({'url': 'http://example.test/a.ipk', 'destPath': '/tmp/', 'destFile': 'a.ipk',
                              'amountReceived': 10, 'amountTotal': 10}))),
                ('INSERT INTO DownloadHistory VALUES (0, ?, ?, ?, ?)', ('system', 'init', 'null', 'null'))])
            prefs = make_db(os.path.join(root, 'vol', 'var', 'luna', 'preferences', 'systemprefs.db'), [
                ('CREATE TABLE Preferences (key TEXT, value TEXT)',),
                ('INSERT INTO Preferences VALUES (?, ?)', ('timeZone', '"Etc/UTC"')),
                ('INSERT INTO Preferences VALUES (?, ?)', ('locale', 'en-US'))])
            context = FakeContext([dl, dl + '-journal', prefs], root)
            _h, rows, source = lgWebos.lgWebosDownloadHistory.__wrapped__(context)
            self.assertEqual([r[:4] for r in rows], [(0, 'system', 'init', 'null'),
                                                    (1, 'com.example.installer', 'wifi', 'completed')])
            self.assertEqual(rows[1][4:7], ('http://example.test/a.ipk', '/tmp/', 'a.ipk'))
            self.assertEqual(source, dl)
            _h, rows, _source = lgWebos.lgWebosSystemPreferences.__wrapped__(context)
            self.assertEqual(rows, [('locale', 'en-US'), ('timeZone', '"Etc/UTC"')])

    def test_local_storage_rows_name_the_origin(self):
        with tempfile.TemporaryDirectory() as root:
            store = make_db(os.path.join(root, 'vol', 'var', 'lib', 'wam', 'Default', 'Local Storage',
                                         'file_com.example.app_0.localstorage'), [
                ('CREATE TABLE ItemTable (key TEXT UNIQUE, value BLOB NOT NULL)',),
                ('INSERT INTO ItemTable VALUES (?, ?)', ('theme', 'dark'.encode('utf-16-le'))),
                ('INSERT INTO ItemTable VALUES (?, ?)', ('odd', b'\x01\x02\x03'))])
            journal = write(store + '-journal', b'')
            with open(store, 'rb') as handle:
                backup = write(store + '.bak', handle.read())
            with mock.patch.object(lgWebos, 'logfunc') as log:
                headers, rows, _source = lgWebos.lgWebosLocalStorage.__wrapped__(
                    FakeContext([store, journal, backup], root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([r[:4] for r in rows], [('file_com.example.app_0', 'theme', 'dark', 'UTF-16LE'),
                                                 ('file_com.example.app_0', 'odd', '010203', 'hex')])
        self.assertEqual(log.call_args.args[0],
                         'LG webOS Web App Local Storage: 1 values that are not UTF-16LE, reported as hex')

    def test_installed_apps_skip_nested_and_firmware_copies(self):
        with tempfile.TemporaryDirectory() as root:
            info = json.dumps({'id': 'com.example.app', 'title': 'Example', 'version': '1.0.0',
                               'vendor': 'Example Vendor', 'type': 'web'})
            base = os.path.join(root, 'media', 'cryptofs', 'apps', 'usr', 'palm', 'applications')
            files = [write(os.path.join(base, 'com.example.app', 'appinfo.json'), info),
                     write(os.path.join(base, 'com.example.app', 'resources', 'en', 'appinfo.json'), '{"title":"x"}'),
                     write(os.path.join(root, 'media', 'system', 'apps', 'usr', 'palm', 'applications',
                                        'com.example.sys', 'appinfo.json'), '{"id": "com.example.sys"}'),
                     write(os.path.join(root, 'rootfs', 'usr', 'share', 'test_data', 'media', 'cryptofs', 'apps', 'usr',
                                        'palm', 'applications', 'com.example.test', 'appinfo.json'), info),
                     write(os.path.join(base, 'com.example.bad', 'appinfo.json'), '[1, 2]')]
            with mock.patch.object(lgWebos, 'logfunc') as log:
                headers, rows, _source = lgWebos.lgWebosInstalledApps.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [('com.example.app', 'Example', '1.0.0', 'Example Vendor', 'web', 'cryptofs/apps'),
                                ('com.example.sys', '', '', '', '', 'system/apps')])
        self.assertEqual(log.call_args.args[0], 'LG webOS Installed Apps: 1 appinfo.json files inside a usr folder '
                                                '(firmware copies such as test data), not reported, 1 appinfo.json '
                                                'files that are not a JSON object')


if __name__ == '__main__':
    unittest.main()
