"""Signal Desktop's encryptedKey unwraps for each safeStorage scheme Signal writes.

The blobs are built here by a writer that follows Chromium 128.0.6613.84's
os_crypt code, not by the module under test: macOS
(components/os_crypt/sync/os_crypt_mac.mm) uses prefix "v10" and 1003 PBKDF2
iterations; Linux with a keyring (components/os_crypt/sync/os_crypt_linux.cc)
uses prefix "v11" and 1 iteration. With no keyring, Signal keeps the key in the
clear instead of wrapping it (getSQLKey, Signal Desktop v8.33.0
app/main.main.ts).
"""

import json
import os
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import signal_desktop  # pylint: disable=wrong-import-position

try:
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA1
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Util.Padding import pad
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False

DB_KEY = "0123456789abcdef" * 4
SECRET = "synthetic-keyring-secret"


def chromium_wrap(prefix, password, iterations, plaintext=DB_KEY):
    """Wrap plaintext the way Chromium's OSCrypt EncryptString does."""
    kek = PBKDF2(password, b"saltysalt", dkLen=16, count=iterations, hmac_hash_module=SHA1)
    cipher = AES.new(kek, AES.MODE_CBC, b" " * 16)
    return (prefix + cipher.encrypt(pad(plaintext.encode(), 16))).hex()


@unittest.skipUnless(HAVE_CRYPTO, "PyCryptodome is not installed")
class UnwrapTests(unittest.TestCase):

    def test_macos_keychain_credential(self):
        blob = chromium_wrap(b"v10", SECRET, 1003)
        self.assertEqual(signal_desktop.unwrap_encrypted_key(blob, SECRET), DB_KEY)

    def test_linux_keyring_secret(self):
        blob = chromium_wrap(b"v11", SECRET, 1)
        self.assertEqual(signal_desktop.unwrap_encrypted_key(blob, SECRET), DB_KEY)

    def test_wrong_secret_does_not_unwrap(self):
        for blob in (chromium_wrap(b"v10", SECRET, 1003), chromium_wrap(b"v11", SECRET, 1)):
            self.assertIsNone(signal_desktop.unwrap_encrypted_key(blob, "wrong"))

    def test_v11_is_not_tried_at_the_macos_iteration_count(self):
        blob = chromium_wrap(b"v11", SECRET, 1003)
        self.assertIsNone(signal_desktop.unwrap_encrypted_key(blob, SECRET))


@unittest.skipUnless(HAVE_CRYPTO, "PyCryptodome is not installed")
class ResolveTests(unittest.TestCase):
    """resolve_database_key over a profile folder, as the artifacts call it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.profile = os.path.join(self._tmp.name, ".config", "Signal")
        os.makedirs(self.profile)

    def tearDown(self):
        self._tmp.cleanup()

    def _profile(self, config_values, secret=None):
        config = os.path.join(self.profile, "config.json")
        with open(config, "w", encoding="utf-8") as handle:
            json.dump(config_values, handle)
        files = [config]
        if secret is not None:
            secret_path = os.path.join(self._tmp.name, "signal_password.txt")
            with open(secret_path, "w", encoding="utf-8") as handle:
                handle.write(secret)
            files.append(secret_path)
        return files

    def test_linux_keyring_profile_opens_with_the_secret(self):
        key, how = signal_desktop.resolve_database_key(
            self._profile({"encryptedKey": chromium_wrap(b"v11", SECRET, 1)}, SECRET))
        self.assertEqual(key, DB_KEY)
        self.assertIn("signal_password.txt", how)

    def test_linux_profile_without_keyring_opens_with_nothing_supplied(self):
        key, how = signal_desktop.resolve_database_key(
            self._profile({"key": DB_KEY, "safeStorageBackend": "basic_text"}))
        self.assertEqual(key, DB_KEY)
        self.assertIn("plaintext", how)

    def test_linux_keyring_profile_without_secret_reports_what_to_supply(self):
        key, reason = signal_desktop.resolve_database_key(
            self._profile({"encryptedKey": chromium_wrap(b"v11", SECRET, 1)}))
        self.assertIsNone(key)
        self.assertIn("libsecret or kwallet", reason)

    def test_wrong_secret_reports_it(self):
        key, reason = signal_desktop.resolve_database_key(
            self._profile({"encryptedKey": chromium_wrap(b"v11", SECRET, 1)}, "wrong"))
        self.assertIsNone(key)
        self.assertIn("did not unwrap", reason)


if __name__ == "__main__":
    unittest.main()
