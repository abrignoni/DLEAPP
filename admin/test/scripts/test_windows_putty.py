"""Tests for windowsPutty.py: name unescaping, host key value names, fingerprints and the three artifacts.

Every value is made up, except two session names taken from the known data. The expected RSA and ECDSA
blobs are written out byte by byte from RFC 4253 and RFC 5656. The Ed25519 point is built the way the module
builds it, so that test checks the framing only. The registry is a stand-in object tree.
"""

import base64
import hashlib
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsPutty as putty  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position


def _fp(blob):
    return 'SHA256:' + base64.b64encode(hashlib.sha256(blob).digest()).decode('ascii').rstrip('=')


class NameTest(unittest.TestCase):

    def test_unescape(self):
        self.assertEqual(putty.unescape('kd%20putty%20lab'), 'kd putty lab')
        self.assertEqual(putty.unescape('kd.second%2Asession'), 'kd.second*session')
        self.assertEqual(putty.unescape('%2Ehidden%5Cname%3F%25'), '.hidden\\name?%')
        self.assertEqual(putty.unescape('caf%C3%A9'), 'café')
        self.assertEqual(putty.unescape('caf%E9'), 'café')              # not UTF-8: read as Latin-1
        self.assertEqual(putty.unescape('100%'), '100%')
        self.assertEqual(putty.unescape('a%zzb'), 'a%zzb')

    def test_host_key_name(self):
        self.assertEqual(putty.host_key_name('ssh-ed25519@22:127.0.0.1'), ('ssh-ed25519', 22, '127.0.0.1'))
        self.assertEqual(putty.host_key_name('rsa2@2222:fixture%20host.test'), ('rsa2', 2222, 'fixture host.test'))
        self.assertEqual(putty.host_key_name('ecdsa-sha2-nistp256@22:fe80::1'), ('ecdsa-sha2-nistp256', 22, 'fe80::1'))
        self.assertEqual(putty.host_key_name('oldstyle.fixture.test'), ('', '', 'oldstyle.fixture.test'))
        self.assertEqual(putty.host_key_name('rsa2@abc:host'), ('', '', 'rsa2@abc:host'))


class FingerprintTest(unittest.TestCase):

    def test_rsa(self):
        modulus = 0xC1 << 2040                                              # high bit set: a leading 00 byte
        blob = (b'\x00\x00\x00\x07ssh-rsa' + b'\x00\x00\x00\x03\x01\x00\x01'
                + b'\x00\x00\x01\x01\x00' + modulus.to_bytes(256, 'big'))
        stored = f'0x10001,0x{modulus:x}'
        self.assertEqual(putty.public_key_blob('rsa2', stored), blob)
        self.assertEqual(putty.fingerprint('rsa2', stored), _fp(blob))

    def test_ed25519(self):
        x, y = 0x1235, 0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20
        point = bytearray(y.to_bytes(32, 'little'))
        point[31] |= 0x80                                                    # x is odd
        blob = b'\x00\x00\x00\x0bssh-ed25519' + b'\x00\x00\x00\x20' + bytes(point)
        self.assertEqual(putty.public_key_blob('ssh-ed25519', f'0x{x:x},0x{y:x}'), blob)
        even = putty.public_key_blob('ssh-ed25519', f'0x{x - 1:x},0x{y:x}')
        self.assertEqual(even[-1], 0x01)

    def test_ecdsa(self):
        x, y = 0x11 << 240, 0x22
        blob = (b'\x00\x00\x00\x13ecdsa-sha2-nistp256' + b'\x00\x00\x00\x08nistp256' + b'\x00\x00\x00\x41\x04'
                + x.to_bytes(32, 'big') + y.to_bytes(32, 'big'))
        stored = f'nistp256,0x{x:x},0x{y:x}'
        self.assertEqual(putty.public_key_blob('ecdsa-sha2-nistp256', stored), blob)
        wide = putty.public_key_blob('ecdsa-sha2-nistp521', 'nistp521,0x1,0x2')
        self.assertEqual(len(wide), 4 + 19 + 4 + 8 + 4 + 1 + 66 + 66)
        self.assertIsNone(putty.public_key_blob('ecdsa-sha2-nistp256', 'nistp384,0x1,0x2'))

    def test_forms_not_handled(self):
        for key_type, stored in (('ssh-dss', '0x1,0x2,0x3,0x4'), ('ssh-ed448', '0x1,0x2'), ('', '0x1,0x2'),
                                 ('rsa2', '0x10001'), ('rsa2', 'zz,yy'), ('ssh-ed25519', '0x1,0x' + 'f' * 80),
                                 ('ecdsa-sha2-nistp256', 'nistp256,0x' + 'f' * 80 + ',0x1'), ('rsa2', '')):
            self.assertEqual(putty.fingerprint(key_type, stored), '', (key_type, stored))


class _Value:

    def __init__(self, name, value):
        self._name, self._value = name, value

    def name(self):
        return self._name

    def value(self):
        if isinstance(self._value, Exception):
            raise self._value
        return self._value


class _Key:

    def __init__(self, name, values=(), subkeys=(), written=None):
        self._name, self._values, self._subkeys, self._written = name, list(values), list(subkeys), written

    def name(self):
        return self._name

    def timestamp(self):
        return self._written

    def values(self):
        return self._values

    def subkeys(self):
        return self._subkeys

    def value(self, name):
        for value in self._values:
            if value.name() == name:
                return value
        raise Registry.RegistryValueNotFoundException(name)

    def subkey(self, name):
        for key in self._subkeys:
            if key.name() == name:
                return key
        raise Registry.RegistryKeyNotFoundException(name)


class _Hive:

    def __init__(self, tree):
        self._tree = tree

    def open(self, path):
        if self._tree is None or path != 'Software\\SimonTatham\\PuTTY':
            raise Registry.RegistryKeyNotFoundException(path)
        return self._tree


class _Context:

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


WHEN = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
LATER = datetime(2026, 1, 3, 3, 4, 5, tzinfo=timezone.utc)


def _tree():
    session = _Key('fixture%20one', [_Value('HostName', 'user@fixture.test'), _Value('PortNumber', 2222),
                                     _Value('Protocol', 'ssh'), _Value('UserName', ''), _Value('ProxyMethod', 0),
                                     _Value('ProxyHost', 'proxy'), _Value('ProxyPort', 80),
                                     _Value('PortForwardings', 'L8080=inner.fixture.test:80'),
                                     _Value('LogType', 0), _Value('LogFileName', 'putty.log'),
                                     _Value('Colour0', '187,187,187')], written=WHEN)
    bare = _Key('Default%20Settings', [_Value('HostName', ''), _Value('RemoteCommand', OSError('unreadable'))],
                written=LATER)
    keys = _Key('SshHostKeys', [_Value('ssh-ed25519@22:fixture.test', '0x1234,0x22'),
                                _Value('ssh-dss@22:old.fixture.test', '0x1,0x2,0x3,0x4')], written=LATER)
    recent = _Key('Jumplist', [_Value('Recent sessions', ['fixture two', 'fixture one', '', ''])], written=WHEN)
    return _Key('PuTTY', subkeys=[_Key('Sessions', subkeys=[session, bare]), keys, recent])


class ArtifactTest(unittest.TestCase):

    def _run(self, function, hives):
        with tempfile.TemporaryDirectory() as root:
            files = []
            for profile in hives:
                folder = os.path.join(root, 'Users', profile)
                os.makedirs(folder)
                for name in ('NTUSER.DAT', 'ntuser.dat.LOG1'):
                    files.append(os.path.join(folder, name))
                    with open(files[-1], 'wb') as handle:
                        handle.write(b'x')

            def opened(path, _context=None):
                tree = hives[os.path.basename(os.path.dirname(path))]
                if isinstance(tree, Exception):
                    raise tree
                return _Hive(tree)

            with mock.patch.object(putty, 'open_hive', opened), \
                    mock.patch.object(putty, 'key_written_utc', lambda key: key.timestamp()), \
                    mock.patch.object(putty, 'logfunc', lambda *_a, **_k: None):
                headers, rows, sources = function.__wrapped__(_Context(root, files + files[:1]))
            return headers, rows, [os.path.relpath(s, root).replace(os.sep, '/') for s in sources.split('\n') if s]

    HIVES = {'fixture': None, 'empty': None, 'broken': None}

    def _hives(self):
        return {'fixture': _tree(), 'empty': None, 'broken': ValueError('not a hive')}

    def test_sessions(self):
        headers, rows, sources = self._run(putty.windowsPuttySessions, self._hives())
        self.assertEqual(sources, ['Users/fixture/NTUSER.DAT'])
        self.assertEqual(len(headers), 15)
        self.assertEqual(rows, [
            (WHEN, 'fixture one', 'user@fixture.test', 2222, 'ssh', '', 0, 'proxy', 80, '', '',
             'L8080=inner.fixture.test:80', 0, 'putty.log', 'fixture'),
            (LATER, 'Default Settings', '', '', '', '', '', '', '', '', '', '', '', '', 'fixture')])

    def test_host_keys(self):
        headers, rows, sources = self._run(putty.windowsPuttyHostKeys, self._hives())
        self.assertEqual(sources, ['Users/fixture/NTUSER.DAT'])
        self.assertEqual(len(headers), 7)
        self.assertEqual([row[1:4] for row in rows], [('fixture.test', 22, 'ssh-ed25519'),
                                                      ('old.fixture.test', 22, 'ssh-dss')])
        self.assertTrue(rows[0][4].startswith('SHA256:'))
        self.assertEqual(rows[1][4:], ('', '0x1,0x2,0x3,0x4', 'fixture'))
        self.assertEqual({row[0] for row in rows}, {LATER})

    def test_recent_sessions(self):
        headers, rows, sources = self._run(putty.windowsPuttyRecentSessions, self._hives())
        self.assertEqual(sources, ['Users/fixture/NTUSER.DAT'])
        self.assertEqual(len(headers), 4)
        self.assertEqual(rows, [(WHEN, 1, 'fixture two', 'fixture'), (WHEN, 2, 'fixture one', 'fixture')])

    def test_a_putty_key_with_no_subkeys(self):
        for function in (putty.windowsPuttySessions, putty.windowsPuttyHostKeys, putty.windowsPuttyRecentSessions):
            _headers, rows, sources = self._run(function, {'fixture': _Key('PuTTY')})
            self.assertEqual((rows, sources), ([], []))


if __name__ == '__main__':
    unittest.main()
