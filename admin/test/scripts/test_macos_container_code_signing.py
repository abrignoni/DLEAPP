"""Pin the Container Manager Code Signing artifact (scripts/artifacts/macosContainerCodeSigning.py).

The database is built for the test with the columns the artifact reads from containers.sqlite3 on macOS 11. The
values are made up.
"""
import os
import pathlib
import plistlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosContainerCodeSigning as cm
# pylint: enable=wrong-import-position

SCHEMA = '''
CREATE TABLE code_signing_info (id INTEGER PRIMARY KEY, code_signing_id_text TEXT, invalid INTEGER NOT NULL DEFAULT 0,
    placeholder INTEGER NOT NULL DEFAULT 0, registered_by_caller INTEGER NOT NULL DEFAULT 0);
CREATE TABLE code_signing_data (id INTEGER PRIMARY KEY, cs_info_id INTEGER, data BLOB);
CREATE TABLE child_bundles (id INTEGER PRIMARY KEY, child_code_signing_id_text TEXT, parent_id INTEGER);
'''


def ent_blob(entitlements):
    # sort_keys=False keeps the written order so the module's own sorted() is exercised, not plistlib's.
    wrapped = {'com.apple.MobileContainerManager.Entitlements': entitlements}
    return plistlib.dumps(wrapped, fmt=plistlib.FMT_BINARY, sort_keys=False)  # pylint: disable=no-member


def build(path, data_rows=None, info_rows=None, children=True):
    database = sqlite3.connect(path)
    database.executescript(SCHEMA)
    rows = info_rows if info_rows is not None else [
        (1, 'com.example.app', 0, 0, 1),
        (2, 'com.example.helper', 1, 1, 0),
        (3, 'com.example.nodata', 0, 0, 1),
        (4, 'com.example.lone', 1, 0, 0),  # invalid != placeholder, and no code_signing_data row of its own
    ]
    database.executemany('INSERT INTO code_signing_info VALUES (?,?,?,?,?)', rows)
    data = data_rows if data_rows is not None else [
        (1, 1, ent_blob({'com.apple.application-identifier': 'ABCDE12345.com.example.app',
                         'com.apple.security.app-sandbox': True, 'Ubiquity Container Identifiers': ['x']})),
        (2, 2, ent_blob({'com.apple.security.app-sandbox': False})),
        (3, 3, b'not a plist'),
    ]
    database.executemany('INSERT INTO code_signing_data VALUES (?,?,?)', data)
    if children:
        database.execute("INSERT INTO child_bundles VALUES (1, 'com.example.app.extension', 1)")
        database.execute("INSERT INTO child_bundles VALUES (2, 'com.example.app.widget', 1)")
    database.commit()
    database.close()


class EntitlementsTest(unittest.TestCase):
    def test_reads_the_inner_dict(self):
        self.assertEqual(cm.entitlements(ent_blob({'a': True})), {'a': True})

    def test_not_a_plist_or_wrong_shape(self):
        self.assertEqual(cm.entitlements(b'not a plist'), {})
        self.assertEqual(cm.entitlements(None), {})
        self.assertEqual(cm.entitlements(plistlib.dumps({'other': 1}, fmt=plistlib.FMT_BINARY)), {})  # pylint: disable=no-member
        self.assertEqual(cm.entitlements(plistlib.dumps({'com.apple.MobileContainerManager.Entitlements': [1]}, fmt=plistlib.FMT_BINARY)), {})  # pylint: disable=no-member


class FlagTest(unittest.TestCase):
    # pylint: disable=protected-access
    def test_flag(self):
        self.assertEqual(cm._flag(1), 'Yes')
        self.assertEqual(cm._flag(0), 'No')
        self.assertEqual(cm._flag(None), '')  # neither truthy nor 0: blank, not 'No'

    def test_entitlement_flag(self):
        self.assertEqual(cm._entitlement_flag({'k': True}, 'k'), 'Yes')
        self.assertEqual(cm._entitlement_flag({'k': False}, 'k'), 'No')
        self.assertEqual(cm._entitlement_flag({'k': 5}, 'k'), '5')
        self.assertEqual(cm._entitlement_flag({}, 'k'), '')  # key absent is blank, not str(value)


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, *top, **kw):
        folder = os.path.join(self.folder.name, *top, 'Library', 'ContainerManager')
        os.makedirs(folder)
        path = os.path.join(folder, 'containers.sqlite3')
        build(path, **kw)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(cm, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'):
            result = cm.macosContainerCodeSigning.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows(self):
        path = self.database('Users', 'a')
        wal = path + '-wal'
        with open(wal, 'wb'):
            pass
        (headers, rows, located), _ = self.run_artifact([wal, path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 9)
        self.assertEqual(headers[0], 'Code Signing ID')
        self.assertEqual(rows, [
            ('com.example.app', 'ABCDE12345.com.example.app', 'Yes',
             'Ubiquity Container Identifiers | com.apple.application-identifier | com.apple.security.app-sandbox',
             'No', 'No', 'Yes', 'com.example.app.extension | com.example.app.widget', rel),
            ('com.example.helper', '', 'No', 'com.apple.security.app-sandbox', 'Yes', 'Yes', 'No', '', rel),
            ('com.example.nodata', '', '', '', 'No', 'No', 'Yes', '', rel),
            # com.example.lone has no code_signing_data row (kept by the LEFT JOIN) and invalid != placeholder
            ('com.example.lone', '', '', '', 'Yes', 'No', 'No', '', rel)])
        self.assertEqual(located, path)

    def test_two_differing_views_fold_and_a_bad_database_is_counted(self):
        own = self.database('Users', 'a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(own, self.folder.name))
        os.makedirs(os.path.dirname(view))
        build(view, data_rows=[(1, 1, ent_blob({'com.apple.security.app-sandbox': True})), (2, 2, b'x'), (3, 3, b'y')])
        empty = self.database('Users', 'b')
        bad = sqlite3.connect(empty)
        bad.execute('DROP TABLE code_signing_info')
        bad.commit()
        bad.close()
        (_, rows, _located), logged = self.run_artifact([view, empty, own])
        # own and view differ on com.example.app (view row 1 has no application-identifier), so it stays two rows
        self.assertEqual(sum(1 for r in rows if r[0] == 'com.example.app'), 2)
        # com.example.nodata is identical in both copies, so fold_view_rows collapses it to one row
        self.assertEqual(sum(1 for r in rows if r[0] == 'com.example.nodata'), 1)
        self.assertEqual(logged, ['Container Manager Code Signing: 1 databases with no code-signing table '
                                  '(OperationalError)'])

    def test_identical_views_are_read_once(self):
        own = self.database('Users', 'a')
        view = os.path.join(self.folder.name, 'System', 'Volumes', 'Data', os.path.relpath(own, self.folder.name))
        os.makedirs(os.path.dirname(view))
        with open(own, 'rb') as handle:
            copy = handle.read()
        with open(view, 'wb') as handle:
            handle.write(copy)
        (_, rows, located), _ = self.run_artifact([view, own])
        self.assertEqual(len(rows), 4)  # one copy's worth of rows, the byte-identical view skipped
        self.assertNotIn('\n', located)  # located names a single database, not both copies

    def test_empty_but_valid_database_is_not_listed(self):
        path = self.database('Users', 'a', info_rows=[], data_rows=[], children=False)
        (_, rows, located), logged = self.run_artifact([path])
        self.assertEqual((rows, located, logged), ([], '', []))

    def test_a_decoy_named_file_is_ignored(self):
        path = self.database('Users', 'a')
        decoy = os.path.join(os.path.dirname(path), 'notcontainers.sqlite3')
        build(decoy)
        (_, rows, located), _ = self.run_artifact([decoy, path])
        self.assertEqual(len(rows), 4)  # only the real containers.sqlite3 is read
        self.assertNotIn('notcontainers.sqlite3', located)

    def test_a_database_that_does_not_open(self):
        path = self.database('Users', 'a')
        with mock.patch.object(cm, 'open_sqlite_db_readonly', side_effect=lambda p: None):
            (_, rows, located), logged = self.run_artifact([path])
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(logged, ['Container Manager Code Signing: 1 databases that could not be opened'])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
