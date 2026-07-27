"""Cover the macOS keychain reader's key derivation and its failure semantics.

A keychain's DbBlob stores the PBKDF2 salt but not the digest or the iteration
count, so the reader carries them. They are fixed in securityd: HMAC-SHA1, 1000
rounds, 24 bytes, unconditional. `test_other_parameters_are_not_opened` exists
because an earlier investigation talked itself into believing real login
keychains used SHA-256/10000, on the strength of a padding check a wrong key
passes about 1 time in 256.

The distinction these tests protect is the one that investigation got wrong: a
None from the reader means "this password did not open this keychain", not "the
examiner mistyped". A login keychain can hold a password that differs from the
account password, and a live macOS host will not reveal it.

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

    def test_securityd_parameters(self):
        """The values securityd uses, which are fixed and never negotiated."""
        self.assertEqual(macos_keychain._KDF_DIGEST, 'sha1')  # pylint: disable=protected-access
        self.assertEqual(macos_keychain._KDF_ROUNDS, 1000)  # pylint: disable=protected-access
        self.assertEqual(self._round_trip('sha1', 1000), self.DB_KEY)

    def test_wrong_password_yields_nothing(self):
        self.assertIsNone(self._round_trip('sha1', 1000, password='not-the-password'))

    def test_other_parameters_are_not_opened(self):
        """Confirms the test above passes because of the parameters, not by chance.

        SHA-256/10000 is called out because a sweep once appeared to identify it
        as what real login keychains use. It does not: that sweep scored
        candidates by 3DES padding alone, which a wrong key satisfies about 1
        time in 256, and the resulting key unwrapped 0 of 80 symmetric keys on a
        real keychain. Apple's securityd derives the master key with HMAC-SHA1
        at 1000 rounds unconditionally.
        """
        for digest, rounds in (('sha256', 10000), ('sha512', 7), ('sha1', 1001)):
            with self.subTest(digest=digest, rounds=rounds):
                self.assertIsNone(self._round_trip(digest, rounds))


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
