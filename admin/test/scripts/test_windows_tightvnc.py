"""Tests for windowsTightVnc.py: the password decoding and the artifact's rows.

Every value is made up, except one vector: the 8-byte form of the password "password" that VNC write-ups
commonly quote (not sourced here). The stored values are made with PyCryptodome's DES and the key written
out as literal bytes, so the test does not take the key from the module. The registry is a stand-in object
tree.
"""

import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

from Crypto.Cipher import DES

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsTightVnc as tight  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

# 23, 82, 107, 6, 35, 78, 88, 7 with the bits of each byte reversed.
BIT_REVERSED_KEY = bytes((0xE8, 0x4A, 0xD6, 0x60, 0xC4, 0x72, 0x1A, 0xE0))
WHEN = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def stored(password):
    return DES.new(BIT_REVERSED_KEY, DES.MODE_ECB).encrypt(password.encode('latin-1').ljust(8, b'\x00'))


class DecodeTest(unittest.TestCase):

    def test_round_trip(self):
        for password in ('fixture1', 'short', 'a', '', 'café'):
            self.assertEqual(tight.decode_password(stored(password)), password)

    def test_a_commonly_quoted_vector(self):
        self.assertEqual(stored('password').hex(), 'dbd83cfd727a1458')
        self.assertEqual(tight.decode_password(bytes.fromhex('dbd83cfd727a1458')), 'password')

    def test_values_that_are_not_one_block(self):
        for value in (b'', b'\x00' * 7, b'\x00' * 9, 'text', 5, None):
            self.assertEqual(tight.decode_password(value), '')


class _Value:

    def __init__(self, name, value):
        self._name, self._value = name, value

    def name(self):
        return self._name

    def value(self):
        return self._value


class _Key:

    def __init__(self, values):
        self._values = [_Value(name, value) for name, value in values.items()]

    def values(self):
        return self._values

    def timestamp(self):
        return WHEN


class _Hive:

    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


class _Context:

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):

    def _run(self, keys):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'Windows', 'System32', 'config')
            os.makedirs(folder)
            files = []
            for name in ('SOFTWARE', 'SOFTWARE.LOG1', 'SYSTEM'):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(b'x')
            with mock.patch.object(tight, 'open_hive', lambda _path, _context=None: _Hive(keys)), \
                    mock.patch.object(tight, 'key_written_utc', lambda key: key.timestamp()), \
                    mock.patch.object(tight, 'logfunc', lambda *_a, **_k: None):
                headers, rows, sources = tight.windowsTightVncServer.__wrapped__(_Context(root, files))
            return headers, rows, [os.path.relpath(s, root).replace(os.sep, '/') for s in sources.split('\n') if s]

    def test_rows(self):
        full = _Key({'Password': stored('fixture1'), 'PasswordViewOnly': stored('view'),
                     'ControlPassword': stored('control'), 'UseVncAuthentication': 1,
                     'UseControlAuthentication': 0, 'RfbPort': 5901, 'IpAccessControl': '0.0.0.0-255.255.255.255:0',
                     'Unreported': 7})
        headers, rows, sources = self._run({'TightVNC\\Server': full,
                                            'Wow6432Node\\TightVNC\\Server': _Key({'Password': b'\x01\x02'})})
        self.assertEqual(sources, ['Windows/System32/config/SOFTWARE'])
        self.assertEqual(len(headers), 18)
        self.assertEqual(rows[0], (
            WHEN, 'fixture1', 'view', 'control', stored('fixture1').hex(), stored('view').hex(),
            stored('control').hex(), 1, 0, '', 5901, '', '', '', '', '0.0.0.0-255.255.255.255:0', '',
            'TightVNC\\Server'))
        self.assertEqual(rows[1], (WHEN, '', '', '', '0102', '', '', '', '', '', '', '', '', '', '', '', '',
                                   'Wow6432Node\\TightVNC\\Server'))

    def test_no_key(self):
        _headers, rows, sources = self._run({})
        self.assertEqual((rows, sources), ([], []))


if __name__ == '__main__':
    unittest.main()
