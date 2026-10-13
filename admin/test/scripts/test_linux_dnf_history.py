"""Pin the DNF5 Transaction History artifact (scripts/artifacts/linuxDnfHistory.py).

The database is built for the test with the libdnf5 transaction_history.sqlite tables the artifact joins. The
values are made up.
"""
import datetime
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
from scripts.artifacts import linuxDnfHistory as dnf
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
B = datetime.datetime(2023, 11, 14, 22, 13, 20, tzinfo=UTC)   # 1700000000
E = datetime.datetime(2023, 11, 14, 22, 13, 25, tzinfo=UTC)   # 1700000005
B2 = datetime.datetime(2023, 11, 14, 22, 15, 0, tzinfo=UTC)   # 1700000100 (a later transaction)
E2 = datetime.datetime(2023, 11, 14, 22, 15, 5, tzinfo=UTC)   # 1700000105

SCHEMA = '''
CREATE TABLE trans (id INTEGER PRIMARY KEY, dt_begin INTEGER, dt_end INTEGER, rpmdb_version_begin TEXT,
    rpmdb_version_end TEXT, releasever TEXT, user_id INTEGER, description TEXT, comment TEXT, state_id INTEGER);
CREATE TABLE trans_item (id INTEGER PRIMARY KEY, trans_id INTEGER, item_id INTEGER, repo_id INTEGER,
    action_id INTEGER, reason_id INTEGER, state_id INTEGER);
CREATE TABLE trans_item_action (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE trans_item_reason (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE trans_state (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE repo (id INTEGER PRIMARY KEY, repoid TEXT);
CREATE TABLE pkg_name (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE arch (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE rpm (item_id INTEGER, name_id INTEGER, epoch INTEGER, version TEXT, release TEXT, arch_id INTEGER);
CREATE TABLE comps_group (item_id INTEGER, groupid TEXT, name TEXT, translated_name TEXT, pkg_types INTEGER);
CREATE TABLE comps_environment (item_id INTEGER, environmentid TEXT, name TEXT, translated_name TEXT,
    pkg_types INTEGER);
'''


def build(path, dnf5=True):
    db = sqlite3.connect(path)
    if not dnf5:
        db.execute('CREATE TABLE other (x INTEGER)')
        db.commit(); db.close(); return
    db.executescript(SCHEMA)
    db.executemany('INSERT INTO trans_item_action VALUES (?,?)', [(1, 'Install'), (5, 'Remove')])
    db.executemany('INSERT INTO trans_item_reason VALUES (?,?)', [(1, 'Dependency'), (2, 'User'), (5, 'Group')])
    db.execute("INSERT INTO trans_state VALUES (2, 'Ok')")
    db.executemany('INSERT INTO repo VALUES (?,?)', [(1, 'updates'), (4, '@System')])
    db.execute("INSERT INTO arch VALUES (1, 'x86_64')")
    db.executemany('INSERT INTO pkg_name VALUES (?,?)', [(1, 'firefox'), (2, 'glib2')])
    db.executemany('INSERT INTO rpm VALUES (?,?,?,?,?,?)',
                   [(10, 1, 0, '1.0', '1.fc44', 1), (11, 2, 2, '2.0', '3', 1)])
    db.execute("INSERT INTO comps_group VALUES (12, 'core', 'Core', 'Core', 0)")
    db.execute("INSERT INTO comps_environment VALUES (13, 'server', 'Server', 'Server', 0)")
    db.executemany('INSERT INTO trans VALUES (?,?,?,?,?,?,?,?,?,?)', [
        (1, 1700000000, 1700000005, '', '', '44', 1000, 'dnf install -y firefox', '', 2),
        (2, 1700000100, 1700000105, '', '', '44', 1000, 'dnf -y remove glib2', '', 2)])
    db.executemany('INSERT INTO trans_item (id, trans_id, item_id, repo_id, action_id, reason_id, state_id) '
                   'VALUES (?,?,?,?,?,?,?)', [
                       (1, 1, 10, 1, 1, 2, 2),   # firefox, Install, User
                       (2, 1, 11, 4, 1, 1, 2),   # glib2 (epoch 2), Install, Dependency
                       (3, 1, 12, 1, 1, 5, 2),   # group core, Install, Group
                       (4, 1, 13, 1, 1, 2, 2),   # environment server, Install, User
                       (5, 1, 10, 1, 5, 2, 2),   # firefox, Remove, User
                       (6, 2, 11, 1, 5, 2, 2)])  # later transaction: glib2 Remove, User
    db.commit(); db.close()


class UnixUtc(unittest.TestCase):
    def test_unix_utc(self):
        self.assertEqual(dnf._unix_utc(0), '')      # pylint: disable=protected-access
        self.assertEqual(dnf._unix_utc(None), '')   # pylint: disable=protected-access
        self.assertEqual(dnf._unix_utc(1700000000), B)  # pylint: disable=protected-access


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, **kw):
        folder = os.path.join(self.folder.name, 'usr', 'lib', 'sysimage', 'libdnf5')
        os.makedirs(folder)
        path = os.path.join(folder, 'transaction_history.sqlite')
        build(path, **kw)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(dnf, 'logfunc') as log:
            result = dnf.linuxDnfHistory.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows(self):
        path = self.database()
        (headers, rows, located), _ = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 12)
        self.assertEqual((headers[0], headers[1]), (('Begin Time (UTC)', 'datetime'), ('End Time (UTC)', 'datetime')))
        self.assertEqual(rows, [
            (B, E, '1', 'dnf install -y firefox', '1000', 'Install', 'rpm', 'firefox-1.0-1.fc44.x86_64', 'User',
             'updates', 'Ok', rel),
            (B, E, '1', 'dnf install -y firefox', '1000', 'Install', 'rpm', 'glib2-2:2.0-3.x86_64', 'Dependency',
             '@System', 'Ok', rel),   # epoch 2 shown
            (B, E, '1', 'dnf install -y firefox', '1000', 'Install', 'group', 'core', 'Group', 'updates', 'Ok', rel),
            (B, E, '1', 'dnf install -y firefox', '1000', 'Install', 'environment', 'server', 'User', 'updates',
             'Ok', rel),
            (B, E, '1', 'dnf install -y firefox', '1000', 'Remove', 'rpm', 'firefox-1.0-1.fc44.x86_64', 'User',
             'updates', 'Ok', rel),
            (B2, E2, '2', 'dnf -y remove glib2', '1000', 'Remove', 'rpm', 'glib2-2:2.0-3.x86_64', 'User',
             'updates', 'Ok', rel)])   # later transaction sorts after, proving ascending order
        self.assertEqual(located, path)

    def test_not_a_dnf5_history_db(self):
        path = self.database(dnf5=False)
        (_, rows, located), logged = self.run_artifact([path])
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(len(logged), 1)
        self.assertIn('is not a DNF5 history database', logged[0])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
