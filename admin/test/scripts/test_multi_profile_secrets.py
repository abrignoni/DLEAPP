"""Several Signal or Threema profiles and several Exodus wallets on one computer.

Each profile is read with its own key, and every secret given is tried on every profile,
because the examiner cannot tell which secret belongs to which profile.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TEST_DIR = pathlib.Path(__file__).resolve().parent
for entry in (REPO_ROOT, TEST_DIR):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from scripts import signal_desktop  # noqa: E402  pylint: disable=wrong-import-position
from scripts import threema_desktop as td  # noqa: E402  pylint: disable=wrong-import-position
from scripts.context import Context  # noqa: E402  pylint: disable=wrong-import-position

KEY_A = "a" * 64
KEY_B = "b" * 64


class FolderContext:
    """The parts of the artifact context these readers use, over a temporary folder."""

    def __init__(self, folder, files):
        self.folder = pathlib.Path(folder)
        self.files = [str(path) for path in files]

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.folder))

    @staticmethod
    def get_app_secret(name):
        return Context.get_app_secret(name)

    @staticmethod
    def get_seeker():
        return None

    @staticmethod
    def get_source_file_path(path):
        return path


def write(path, data=b"x"):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return str(path)


class TestSignalProfiles(unittest.TestCase):
    """ signal_desktop.profiles and open_database over two profiles. """

    def setUp(self):
        self.addCleanup(Context.set_app_secret, "signal", None)
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

    def _profile(self, user, config=b'{"key": null}', data=b"not sqlite"):
        base = self.root / "Users" / user / "AppData" / "Roaming" / "Signal"
        return [write(base / "sql" / "db.sqlite", data), write(base / "config.json", config)]

    def test_each_profile_is_its_own_group(self):
        """ Two users' profiles split apart; a credential file goes to both. """
        first = self._profile("alice")
        second = self._profile("bob")
        credential = write(self.root / "signal_db_key.txt", KEY_A)
        groups = signal_desktop.profiles(None, first + second + [credential])
        self.assertEqual(len(groups), 2)
        self.assertEqual({tuple(sorted(group)) for group in groups},
                         {tuple(sorted(first + [credential])),
                          tuple(sorted(second + [credential]))})

    def test_no_database_keeps_every_file_together(self):
        """ The reason nothing opened still comes from the profile's files. """
        config = write(self.root / "Signal" / "config.json", b"{}")
        self.assertEqual(signal_desktop.profiles(None, [config]), [[config]])

    def test_a_volume_view_copy_is_read_once(self):
        """ The same profile under System/Volumes/Data with the same bytes is one profile. """
        first = self._profile("alice")
        view = [write(str(path).replace(str(self.root), str(self.root / "System/Volumes/Data")),
                      pathlib.Path(path).read_bytes()) for path in first]
        context = FolderContext(self.root, first + view)
        groups = signal_desktop.profiles(context, first + view)
        self.assertEqual(len(groups), 1)

    def test_every_supplied_key_is_tried_on_each_profile(self):
        """ The second key opens the profile the first key does not. """
        Context.set_app_secret("signal", (KEY_A, KEY_B))
        first = self._profile("alice")
        tried = []

        def decrypt(_path, key_hex, output_path, log=None):  # pylint: disable=unused-argument
            tried.append(key_hex)
            return output_path if key_hex == KEY_B else None

        with mock.patch.object(signal_desktop, "decrypt_database", side_effect=decrypt), \
                mock.patch.object(signal_desktop.sqlite3, "connect", return_value="connection"):
            connection, how = signal_desktop.open_database(first)
        signal_desktop._decrypted_cache.clear()  # pylint: disable=protected-access
        self.assertEqual(tried, [KEY_A, KEY_B])
        self.assertEqual(connection, "connection")
        self.assertIn("--signal-key", how)

    def test_no_key_that_opens_says_how_many_were_tried(self):
        Context.set_app_secret("signal", (KEY_A, KEY_B))
        first = self._profile("alice")
        with mock.patch.object(signal_desktop, "decrypt_database", return_value=None):
            connection, reason = signal_desktop.open_database(first)
        self.assertIsNone(connection)
        self.assertIn("any of the 2 candidate keys", reason)


try:
    from test_threema_keystorage import build_keystorage
    HAVE_THREEMA_DEPS = td.threema_keystorage.deps_available()
except ImportError:  # pragma: no cover
    HAVE_THREEMA_DEPS = False


@unittest.skipUnless(HAVE_THREEMA_DEPS, "argon2-cffi and PyNaCl are needed")
class TestThreemaProfiles(unittest.TestCase):
    """ Each threema.sqlite is paired with the keystorage.bin beside it. """

    def setUp(self):
        for name in ("threema", "threema_password"):
            self.addCleanup(Context.set_app_secret, name, None)
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self._tmp.cleanup)
        root = pathlib.Path(self._tmp.name)
        self.key_a, self.key_b = os.urandom(32), os.urandom(32)
        self.db_a = write(root / "alice" / "data" / "threema.sqlite")
        self.ks_a = write(root / "alice" / "data" / "keystorage.bin",
                          build_keystorage("same", self.key_a, "AAAA1111", os.urandom(16)))
        self.db_b = write(root / "bob" / "data" / "threema.sqlite")
        self.ks_b = write(root / "bob" / "data" / "keystorage.bin",
                          build_keystorage("other", self.key_b, "BBBB2222", os.urandom(16)))
        self.files = [self.db_a, self.ks_a, self.db_b, self.ks_b]

    def test_each_database_gets_the_key_beside_it(self):
        """ Two passwords given; each database's candidates come from its own keystore. """
        Context.set_app_secret("threema_password", ("same", "other"))
        candidates_a, _ = td.candidate_keys(self.files, self.db_a)
        candidates_b, _ = td.candidate_keys(self.files, self.db_b)
        self.assertEqual([key for key, _ in candidates_a], [self.key_a.hex()])
        self.assertEqual([key for key, _ in candidates_b], [self.key_b.hex()])

    def test_the_same_password_on_two_profiles(self):
        """ One password for both profiles still gives each its own key. """
        root = pathlib.Path(self._tmp.name)
        write(root / "bob" / "data" / "keystorage.bin",
              build_keystorage("same", self.key_b, "BBBB2222", os.urandom(16)))
        Context.set_app_secret("threema_password", ("same",))
        self.assertEqual(td.resolve_database_key(self.files, self.db_b)[0], self.key_b.hex())

    def test_several_raw_keys_are_all_candidates(self):
        Context.set_app_secret("threema", (KEY_A, KEY_B))
        candidates, _ = td.candidate_keys([self.db_a], self.db_a)
        self.assertEqual([key for key, _ in candidates], [KEY_A, KEY_B])

    def test_open_tries_each_candidate(self):
        """ A key that does not authenticate is passed over for the next. """
        Context.set_app_secret("threema", (KEY_A, KEY_B))
        tried = []

        def decrypt(_path, key_hex, _output, **_kwargs):
            tried.append(key_hex)
            return (3, 3) if key_hex == KEY_B else (3, 0)

        with mock.patch("scripts.sqlcipher_decrypt.decrypt_sqlcipher_db", side_effect=decrypt), \
                mock.patch.object(td.sqlite3, "connect", return_value="connection"):
            connection, how = td.open_database(self.db_a, [self.db_a])
        td._decrypted_cache.clear()  # pylint: disable=protected-access
        self.assertEqual(tried, [KEY_A, KEY_B])
        self.assertEqual((connection, how), ("connection", "--threema-key"))


class TestNoReuseAcrossRuns(unittest.TestCase):
    """ The window runs several times in one process: a copy decrypted with one run's secret
    is not handed to a later run that gave no secret. """

    def setUp(self):
        for name in ("signal", "threema"):
            self.addCleanup(Context.set_app_secret, name, None)
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

    def test_threema(self):
        database = write(self.root / "data" / "threema.sqlite", b"not sqlite")
        Context.set_app_secret("threema", (KEY_A,))

        def decrypt(_path, _key, output, **_kwargs):
            write(output)
            return (1, 1)

        with mock.patch("scripts.sqlcipher_decrypt.decrypt_sqlcipher_db", side_effect=decrypt), \
                mock.patch.object(td.sqlite3, "connect", return_value="connection"):
            self.assertEqual(td.open_database(database, [database])[0], "connection")
            Context.set_app_secret("threema", None)
            connection, reason = td.open_database(database, [database])
        td._remove_decrypted_copies()  # pylint: disable=protected-access
        td._decrypted_cache.clear()  # pylint: disable=protected-access
        self.assertIsNone(connection)
        self.assertIn("needs the account password", reason)

    def test_signal(self):
        base = self.root / "Signal"
        files = [write(base / "sql" / "db.sqlite", b"not sqlite"),
                 write(base / "config.json", b'{"encryptedKey": "763130"}')]
        Context.set_app_secret("signal", (KEY_A,))
        with mock.patch.object(signal_desktop, "decrypt_database",
                               side_effect=lambda _p, _k, out, log=None: out), \
                mock.patch.object(signal_desktop.sqlite3, "connect", return_value="connection"):
            self.assertEqual(signal_desktop.open_database(files)[0], "connection")
            Context.set_app_secret("signal", None)
            connection, _reason = signal_desktop.open_database(files)
        signal_desktop._decrypted_cache.clear()  # pylint: disable=protected-access
        self.assertIsNone(connection)


class TestExodusPasswords(unittest.TestCase):
    """ Every supplied password is tried on every wallet. """

    def setUp(self):
        self.addCleanup(Context.set_app_secret, "exodus_password", None)

    def test_each_wallet_opens_with_its_own_password(self):
        from scripts.artifacts import exodusWallet  # pylint: disable=import-outside-toplevel
        ew = exodusWallet.ew
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            files = []
            for user in ("alice", "bob"):
                files.append(write(root / "Users" / user / "AppData" / "Roaming" / "Exodus"
                                   / "exodus.wallet" / "seed.seco", user))
            passwords = {b"alice": "pw-alice", b"bob": "pw-bob"}

            def payload(data, secret):
                if passwords[data] != secret:
                    raise ew.WrongPassphrase("wrong")
                return b"payload"

            Context.set_app_secret("exodus_password", ("pw-bob", "pw-alice"))
            with mock.patch.object(ew, "validate_container"), \
                    mock.patch.object(ew, "seco_store_payload", side_effect=payload), \
                    mock.patch.object(ew, "parse_seed_payload",
                                      return_value={"recognised": True, "verified": True,
                                                    "mnemonic": "m", "seed": b"\x01"}):
                _headers, rows, _source = exodusWallet.exodusWallet.__wrapped__(
                    FolderContext(root, files))
        self.assertEqual(sorted((row[1], row[2], row[3]) for row in rows),
                         [("alice", "User password (supplied)", "pw-alice"),
                          ("bob", "User password (supplied)", "pw-bob")])


if __name__ == "__main__":
    unittest.main()
