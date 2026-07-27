"""Cover the macOS keychain reader's key derivation and its known limits.

A keychain's DbBlob stores the PBKDF2 salt but not the digest or the iteration
count that were used with it, so the reader has to carry them. Only SHA-1 with
1000 rounds is confirmed, and it opens everything `security create-keychain`
writes. That is also why the reader looked healthy for so long: every keychain
built for testing uses that set.

It does not open a real login.keychain-db, and the cause is unresolved. These
tests therefore do two jobs: check the derivation works for every parameter set
the reader declares, and pin the fact that SHA-256/10000 is deliberately absent,
so a future change has to bring evidence rather than repeat an earlier guess.
See `_KDF_PARAMETERS` for what that evidence has to be.

The synthetic-DbBlob tests need no keychain and run on the Linux CI runners. The
live-keychain test exercises the whole path — table walk, key unwrap, SSGP
decrypt — and skips where `security` is unavailable.
"""
import hashlib
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_keychain  # pylint: disable=wrong-import-position

# The DbBlob fields _database_key() unpacks, in order.
_DB_BLOB = struct.Struct("> 8s I I 16s I 8s 20s 8s 20s")

HAS_CRYPTO = macos_keychain.crypto_available()
HAS_SECURITY = sys.platform == 'darwin' and shutil.which('security') is not None


def _synthesize_db_blob(password, digest, rounds, db_key):
    """Build the bytes of a DbBlob that `password` unlocks under these parameters.

    Mirrors what securityd writes: PBKDF2 over the blob's salt gives the master
    key, and 3DES-CBC under it and the blob IV encrypts the database key.
    """
    from Crypto.Cipher import DES3  # pylint: disable=import-outside-toplevel

    salt = bytes(range(20))
    iv = bytes(range(100, 108))
    master = hashlib.pbkdf2_hmac(digest, password.encode('utf-8'), salt, rounds, 24)
    pad = 8 - (len(db_key) % 8)
    ciphertext = DES3.new(master, DES3.MODE_CBC, iv).encrypt(db_key + bytes([pad]) * pad)

    start_crypto = _DB_BLOB.size
    total_len = start_crypto + len(ciphertext)
    header = _DB_BLOB.pack(
        struct.pack('> I I', macos_keychain._COMMON_BLOB_MAGIC, 0),  # pylint: disable=protected-access
        start_crypto, total_len, b'\x00' * 16, 0, b'\x00' * 8, salt, iv, b'\x00' * 20)
    return header + ciphertext


@unittest.skipUnless(HAS_CRYPTO, 'PyCryptodome is not installed')
class TestDatabaseKeyDerivation(unittest.TestCase):
    """_database_key() has to open a DbBlob under either published parameter set."""

    PASSWORD = 'throwaway-test-password'
    DB_KEY = bytes(range(1, 25))

    def _round_trip(self, digest, rounds, password=None):
        blob = _synthesize_db_blob(self.PASSWORD, digest, rounds, self.DB_KEY)
        # Offset the blob so a hardcoded base address can't accidentally pass.
        data = b'\xaa' * 64 + blob
        return macos_keychain._database_key(data, 64, password or self.PASSWORD)  # pylint: disable=protected-access

    def test_confirmed_parameters(self):
        """SHA-1 / 1000: the set `security create-keychain` writes."""
        self.assertEqual(self._round_trip('sha1', 1000), self.DB_KEY)

    def test_sha256_is_deliberately_not_declared(self):
        """Pins the open question so nobody re-adds SHA-256 without evidence.

        A sweep once appeared to show a real login.keychain-db using SHA-256 at
        10000 rounds, but it judged candidates by 3DES padding alone, which a
        wrong key satisfies about 1 time in 256. Adding it here on that basis
        would be guessing. When someone confirms a parameter set properly --
        by checking that the resulting database key unwraps the keychain's
        symmetric keys, not just that padding validated -- this test is the
        thing to change.
        """
        self.assertNotIn(('sha256', 10000), macos_keychain._KDF_PARAMETERS)  # pylint: disable=protected-access
        self.assertIsNone(self._round_trip('sha256', 10000))

    def test_every_declared_parameter_set_is_reachable(self):
        """Nothing may be listed in _KDF_PARAMETERS that the reader cannot open."""
        for digest, rounds in macos_keychain._KDF_PARAMETERS:  # pylint: disable=protected-access
            with self.subTest(digest=digest, rounds=rounds):
                self.assertEqual(self._round_trip(digest, rounds), self.DB_KEY)

    def test_wrong_password_yields_nothing(self):
        for digest, rounds in macos_keychain._KDF_PARAMETERS:  # pylint: disable=protected-access
            with self.subTest(digest=digest, rounds=rounds):
                self.assertIsNone(self._round_trip(digest, rounds, password='not-the-password'))

    def test_undeclared_parameters_are_not_opened(self):
        """Confirms the tests above pass because of the table, not by chance."""
        self.assertIsNone(self._round_trip('sha512', 7))


@unittest.skipUnless(HAS_SECURITY and HAS_CRYPTO, 'needs macOS `security` and PyCryptodome')
class TestLiveKeychainRoundTrip(unittest.TestCase):
    """End-to-end against a keychain macOS itself wrote.

    `security create-keychain` writes the legacy parameter set, so this covers
    the whole pipeline rather than the current-parameters branch specifically.
    """

    PASSWORD = 'throwaway-test-password'
    SERVICE = 'DLEAPP Test Safe Storage'
    SECRET = 'not-a-real-secret-0123456789'

    @classmethod
    def setUpClass(cls):
        cls.workdir = tempfile.mkdtemp()
        cls.path = os.path.join(cls.workdir, 'dleapp-test.keychain-db')
        run = lambda *args: subprocess.run(args, check=True, capture_output=True)  # noqa: E731
        try:
            run('security', 'create-keychain', '-p', cls.PASSWORD, cls.path)
            run('security', 'unlock-keychain', '-p', cls.PASSWORD, cls.path)
            run('security', 'add-generic-password', '-s', cls.SERVICE,
                '-a', 'DLEAPP Test', '-w', cls.SECRET, cls.path)
        except (subprocess.CalledProcessError, OSError) as exc:
            shutil.rmtree(cls.workdir, ignore_errors=True)
            raise unittest.SkipTest(f'could not build a test keychain: {exc}')

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['security', 'delete-keychain', cls.path],
                       check=False, capture_output=True)
        shutil.rmtree(cls.workdir, ignore_errors=True)

    def test_recognized_as_a_keychain(self):
        self.assertTrue(macos_keychain.is_keychain(self.path))

    def test_recovers_the_stored_item(self):
        self.assertEqual(
            macos_keychain.find_generic_password(self.path, self.PASSWORD, self.SERVICE),
            self.SECRET)

    def test_wrong_password_yields_nothing(self):
        self.assertIsNone(
            macos_keychain.find_generic_password(self.path, 'wrong-password', self.SERVICE))

    def test_unknown_service_yields_nothing(self):
        self.assertIsNone(
            macos_keychain.find_generic_password(self.path, self.PASSWORD, 'No Such Service'))


class TestIsKeychain(unittest.TestCase):
    """is_keychain() gates the whole reader, so it must not guess."""

    def test_rejects_a_non_keychain_file(self):
        with tempfile.NamedTemporaryFile(suffix='.db') as handle:
            handle.write(b'SQLite format 3\x00')
            handle.flush()
            self.assertFalse(macos_keychain.is_keychain(handle.name))

    def test_rejects_a_missing_file(self):
        self.assertFalse(macos_keychain.is_keychain('/nonexistent/login.keychain-db'))


if __name__ == '__main__':
    unittest.main()
