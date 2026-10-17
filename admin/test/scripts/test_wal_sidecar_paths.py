"""The keychain-2.db and Signal db.sqlite patterns stage the database's -wal beside it.

Both stores are WAL-mode SQLite. A pattern that names the database alone leaves the
write-ahead log in the evidence, so the database is read without the records committed
only to the log. These tests pin that each pattern also matches the -wal, and that the
readers still pick only the database itself from what was staged.
"""
import fnmatch
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import signal_desktop
from scripts.artifacts import Keychains, signalAccount, signalContacts, signalMessages
# pylint: enable=wrong-import-position

KEYCHAIN = "/case/Users/u/Library/Keychains/0000-UUID/keychain-2.db"
SIGNAL = "/case/Users/u/Library/Application Support/Signal/sql/db.sqlite"


def matches(paths, candidate):
    return any(fnmatch.fnmatchcase(candidate, pattern) for pattern in paths)


class WalSidecarPaths(unittest.TestCase):
    def test_keychain_pattern_stages_the_log(self):
        paths = Keychains.__artifacts_v2__["keychainLocalItems"]["paths"]
        self.assertTrue(matches(paths, KEYCHAIN))
        self.assertTrue(matches(paths, KEYCHAIN + "-wal"))

    def test_keychain_reader_keeps_only_the_database(self):
        staged = [KEYCHAIN, KEYCHAIN + "-wal", KEYCHAIN + "-shm"]
        self.assertEqual(Keychains._local_items_dbs(staged), [KEYCHAIN])  # pylint: disable=protected-access

    def test_signal_patterns_stage_the_log(self):
        for module in (signalAccount, signalContacts, signalMessages):
            for name, spec in module.__artifacts_v2__.items():
                with self.subTest(artifact=name):
                    self.assertTrue(matches(spec["paths"], SIGNAL))
                    self.assertTrue(matches(spec["paths"], SIGNAL + "-wal"))

    def test_signal_reader_keeps_only_the_database(self):
        staged = [SIGNAL + "-wal", SIGNAL, SIGNAL + "-shm"]
        self.assertEqual(list(signal_desktop.database_files(staged)), [SIGNAL])


if __name__ == "__main__":
    unittest.main()
