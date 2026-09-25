"""Pin the Threema Desktop key-storage unwrap in scripts/threema_keystorage.py.

Every value below is synthetic. The synthetic writer uses the reference argon2-cffi
and PyNaCl libraries and the documented protobuf field numbers and two-byte layer
version headers, so a round-trip proves the reader inverts a correctly-built file.
There is no real Threema profile in these tests.
"""
import os
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import threema_keystorage as tk  # pylint: disable=wrong-import-position

try:
    from argon2.low_level import Type, hash_secret_raw
    from nacl.secret import SecretBox
    _DEPS = True
except ImportError:
    _DEPS = False

# Small Argon2id cost so the tests run fast; the reader uses whatever the file stores.
TEST_MEMORY_KIB = 8 * 1024
TEST_ITERATIONS = 1
TEST_PARALLELISM = 1


def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _len_field(number, data):
    return _varint((number << 3) | 2) + _varint(len(data)) + data


def _varint_field(number, value):
    return _varint((number << 3) | 0) + _varint(value)


def build_keystorage(password, database_key, identity, salt,
                     memory_kib=TEST_MEMORY_KIB, iterations=TEST_ITERATIONS,
                     parallelism=TEST_PARALLELISM):
    """A synthetic keystorage.bin: password + Argon2id -> secretbox -> inner db key."""
    inner = _len_field(1, _len_field(1, identity.encode())) + _len_field(3, database_key)
    intermediate = _len_field(1, struct.pack('<H', 3) + inner)          # plaintext_inner
    derived = hash_secret_raw(password.encode(), salt, time_cost=iterations,
                              memory_cost=memory_kib, parallelism=parallelism,
                              hash_len=32, type=Type.ID, version=0x13)
    blob = bytes(SecretBox(derived).encrypt(struct.pack('<H', 1) + intermediate))
    argon = (_len_field(2, salt) + _varint_field(3, memory_kib * 1024)
             + _varint_field(4, iterations) + _varint_field(5, parallelism))
    return struct.pack('<H', 1) + _len_field(1, blob) + _len_field(2, argon)


@unittest.skipUnless(_DEPS, 'argon2-cffi and PyNaCl are required')
class KeystorageUnwrapTest(unittest.TestCase):

    def setUp(self):
        self.db_key = os.urandom(32)
        self.keystorage = build_keystorage('correct horse', self.db_key, 'ABCD1234', os.urandom(16))

    def test_correct_password_recovers_key_and_identity(self):
        key, identity = tk.unwrap_database_key(self.keystorage, 'correct horse')
        self.assertEqual(key, self.db_key)
        self.assertEqual(identity, 'ABCD1234')

    def test_password_may_be_bytes(self):
        key, _identity = tk.unwrap_database_key(self.keystorage, b'correct horse')
        self.assertEqual(key, self.db_key)

    def test_wrong_password_raises(self):
        with self.assertRaises(tk.ThreemaKeystorageError):
            tk.unwrap_database_key(self.keystorage, 'wrong password')


class KeystorageParseTest(unittest.TestCase):
    """Parsing needs no crypto packages."""

    def test_parse_outer_reads_cost_parameters(self):
        keystorage = struct.pack('<H', 1) + _len_field(1, b'x' * 205) + _len_field(
            2, _len_field(2, b's' * 16) + _varint_field(3, 512 * 1024 * 1024)
            + _varint_field(4, 7) + _varint_field(5, 1))
        (salt_len, memory_bytes, iterations, parallelism), blob = tk.parse_outer(keystorage)
        self.assertEqual((salt_len, memory_bytes, iterations, parallelism),
                         (16, 512 * 1024 * 1024, 7, 1))
        self.assertEqual(len(blob), 205)

    def test_truncated_and_garbage_are_rejected(self):
        for junk in (b'', b'\x01\x00', b'\x01\x00garbagegarbage'):
            with self.subTest(size=len(junk)), self.assertRaises(tk.ThreemaKeystorageError):
                tk.parse_outer(junk)

    def test_missing_packages_give_a_clear_message(self):
        saved = (tk._ARGON2_AVAILABLE, tk._NACL_AVAILABLE)  # pylint: disable=protected-access
        tk._ARGON2_AVAILABLE = False  # pylint: disable=protected-access
        tk._NACL_AVAILABLE = False  # pylint: disable=protected-access
        try:
            self.assertFalse(tk.deps_available())
            with self.assertRaises(tk.ThreemaKeystorageError) as caught:
                tk.unwrap_database_key(b'\x01\x00' + _len_field(1, b'x' * 40)
                                       + _len_field(2, _len_field(2, b's' * 16)
                                                    + _varint_field(3, 1024)
                                                    + _varint_field(4, 1)
                                                    + _varint_field(5, 1)), 'pw')
            self.assertIn('argon2-cffi', str(caught.exception))
        finally:
            (tk._ARGON2_AVAILABLE, tk._NACL_AVAILABLE) = saved  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
