"""Pin the Biome sync and Biome Sets readers in scripts/artifacts/macosBiomeSets.py.

Every store below is built by the test with values authored for it; none comes from a device.
"""
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import macosBiomeSets  # pylint: disable=wrong-import-position

T1 = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _ld(number, data):
    return _varint((number << 3) | 2) + _varint(len(data)) + data


def _micro(moment):
    return int(moment.timestamp() * 1_000_000)


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


def _instance_layout(path, items):
    """A Set.db with the instance/provenance layout: items are (time, content bytes)."""
    db = sqlite3.connect(path)
    db.executescript('CREATE TABLE content (content_hash integer, content blob);'
                     'CREATE TABLE provenance (provenance_row_id integer, content_hash integer);'
                     'CREATE TABLE instance (source_item_id_hash integer, provenance_row_id integer, '
                     'modified integer);')
    for number, (moment, blob) in enumerate(items, start=1):
        db.execute('INSERT INTO content VALUES (?, ?)', (number, blob))
        db.execute('INSERT INTO provenance VALUES (?, ?)', (number, number))
        db.execute('INSERT INTO instance VALUES (?, ?, ?)', (number, number, _micro(moment)))
    db.execute('INSERT INTO provenance VALUES (99, NULL)')
    db.commit()
    db.close()


def _provenance_layout(path, items, deleted=0):
    """A Set.db with the metacontent_provenance layout, plus deleted rows with no content."""
    db = sqlite3.connect(path)
    db.executescript('CREATE TABLE content (content_hash integer, content blob);'
                     'CREATE TABLE metacontent_provenance (source_item_id_hash integer, content_hash integer, '
                     'written_date integer, deleted_date integer);')
    for number, (moment, blob) in enumerate(items, start=1):
        db.execute('INSERT INTO content VALUES (?, ?)', (number, blob))
        db.execute('INSERT INTO metacontent_provenance VALUES (?, ?, ?, NULL)', (number, number, _micro(moment)))
    for number in range(deleted):
        db.execute('INSERT INTO metacontent_provenance VALUES (?, NULL, ?, ?)', (100 + number, _micro(T1), _micro(T2)))
    db.commit()
    db.close()


class BiomeSetsTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target in (macosBiomeSets, macos_plists):
            patcher = patch.object(target, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _set(self, view, store, name='Set.db'):
        folder = self.root/view/'Library'/'Biome'/'sets'/'Default'/store/'Database'
        folder.mkdir(parents=True, exist_ok=True)
        return folder/name

    def _rows(self, processor, files):
        headers, rows, _ = processor.__wrapped__(Context(self.root, files))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        for row in rows:
            self.assertEqual(len(row), len(names), 'a row and its headers differ in length')
        return [dict(zip(names, row)) for row in rows]

    def test_installed_apps_instance_layout(self):
        """Fields 1 and 3, the instance time in microseconds, and other fields as stored."""
        path = self._set('Users/tester', 'App.InstalledApp')
        _instance_layout(path, [(T1, _ld(1, b'com.example.app') + _ld(3, b'Example') + _ld(5, b'Old Name'))])
        rows = self._rows(macosBiomeSets.macosBiomeSetsInstalledApps, [path])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Record Time (UTC)'], T1)
        self.assertEqual(rows[0]['Bundle ID'], 'com.example.app')
        self.assertEqual(rows[0]['App Name'], 'Example')
        self.assertEqual(rows[0]['Other Fields (as stored)'], '5: Old Name')
        self.assertEqual(rows[0]['User'], 'tester')

    def test_contacts_provenance_layout_counts_deleted_items(self):
        """The newer layout uses written_date; deleted rows are counted, not reported."""
        path = self._set('Users/tester', 'Contacts.Contact')
        blob = _ld(1, b'Given') + _ld(3, b'Family') + _ld(8, _ld(1, b'\x00\x01sub'))
        _provenance_layout(path, [(T2, blob)], deleted=2)
        rows = self._rows(macosBiomeSets.macosBiomeSetsContacts, [path])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Record Time (UTC)'], T2)
        self.assertEqual((rows[0]['Given Name'], rows[0]['Family Name']), ('Given', 'Family'))
        self.assertTrue(rows[0]['Other Fields (as stored)'].startswith('8.1: '))
        self.assertTrue(any('2 item(s) marked deleted' in line for line in self.logged))

    def test_findmy_owner_is_a_submessage(self):
        """Owner given and family names are fields 1 and 2 of field 2."""
        path = self._set('Users/tester', 'FindMy.Device')
        _instance_layout(path, [(T1, _ld(1, b'Test Phone') + _ld(2, _ld(1, b'Ann') + _ld(2, b'Lee')))])
        row = self._rows(macosBiomeSets.macosBiomeSetsFindMyDevices, [path])[0]
        self.assertEqual((row['Device Name'], row['Owner Given Name'], row['Owner Family Name']),
                         ('Test Phone', 'Ann', 'Lee'))
        self.assertEqual(row['Other Fields (as stored)'], '')

    def test_phrases_name_the_source_app_and_keep_field_3(self):
        """Source App comes from the store folder; field 3 is reported, not dropped."""
        path = self._set('Users/tester', 'App.Shortcut.Phrase/sourceIdentifier=com.example.notes')
        _instance_layout(path, [(T1, _ld(1, b'Make a note') + _ld(2, b'Make a ${x}') + _ld(3, b'extra')
                                 + _ld(4, b'app://intent'))])
        row = self._rows(macosBiomeSets.macosBiomeSetsShortcutPhrases, [path])[0]
        self.assertEqual(row['Source App'], 'com.example.notes')
        self.assertEqual((row['Phrase'], row['Phrase Template'], row['Field 3 (as stored)'], row['Intent URL']),
                         ('Make a note', 'Make a ${x}', 'extra', 'app://intent'))
        self.assertNotIn('Source File', row)

    def test_a_row_both_views_hold_is_reported_once(self):
        """Users/ and System/Volumes/Data/Users/ copies that differ still collapse shared rows."""
        items = [(T1, _ld(1, b'com.example.one') + _ld(3, b'One'))]
        first = self._set('Users/tester', 'App.InstalledApp')
        second = self._set('System/Volumes/Data/Users/tester', 'App.InstalledApp')
        _instance_layout(first, items)
        _instance_layout(second, items + [(T2, _ld(1, b'com.example.two') + _ld(3, b'Two'))])
        rows = self._rows(macosBiomeSets.macosBiomeSetsInstalledApps, [first, second])
        self.assertEqual(sorted(r['Bundle ID'] for r in rows), ['com.example.one', 'com.example.two'])

    def test_identical_items_in_one_store_are_not_merged(self):
        """Two instance rows with the same content and time in one store stay two rows."""
        path = self._set('Users/tester', 'App.InstalledApp')
        blob = _ld(1, b'com.example.same') + _ld(3, b'Same')
        db = sqlite3.connect(path)
        db.executescript('CREATE TABLE content (content_hash integer, content blob);'
                         'CREATE TABLE provenance (provenance_row_id integer, content_hash integer);'
                         'CREATE TABLE instance (source_item_id_hash integer, provenance_row_id integer, '
                         'modified integer);')
        db.execute('INSERT INTO content VALUES (1, ?)', (blob,))
        db.executemany('INSERT INTO provenance VALUES (?, 1)', [(1,), (2,)])
        db.executemany('INSERT INTO instance VALUES (?, ?, ?)', [(11, 1, _micro(T1)), (12, 2, _micro(T1))])
        db.commit()
        db.close()
        self.assertEqual(len(self._rows(macosBiomeSets.macosBiomeSetsInstalledApps, [path])), 2)

    def test_device_sync_reports_values_as_stored(self):
        """A build string holding E is stored as a real number by the STRING column, as SQLite does."""
        folder = self.root/'Users'/'tester'/'Library'/'Biome'/'sync'
        folder.mkdir(parents=True)
        path = folder/'sync.db'
        db = sqlite3.connect(path)
        db.execute('CREATE TABLE DevicePeer (device_identifier STRING NOT NULL, ids_device_identifier STRING, '
                   'me BOOLEAN, name STRING, model STRING, platform INTEGER, last_sync_date INTEGER, '
                   'protocol_version INTEGER NOT NULL)')
        db.execute("INSERT INTO DevicePeer VALUES ('local-id', '', 1, '', '24E248', 4, NULL, 0)")
        db.execute("INSERT INTO DevicePeer VALUES ('peer-id', 'ids-1', 0, '', '23A344', 2, ?, 5)",
                   (T2.timestamp(),))
        db.commit()
        db.close()
        rows = self._rows(macosBiomeSets.macosBiomeDeviceSync, [path])
        local = next(r for r in rows if r['Device ID'] == 'local-id')
        peer = next(r for r in rows if r['Device ID'] == 'peer-id')
        self.assertEqual(local['Model (as stored)'], '2.4e+249')
        self.assertEqual((local['Me (as stored)'], local['Platform (as stored)'], local['Last Sync (UTC)']),
                         ('1', '4', ''))
        self.assertEqual(peer['Model (as stored)'], '23A344')
        self.assertEqual(peer['Last Sync (UTC)'], T2)
        self.assertEqual(peer['IDS Device ID'], 'ids-1')


if __name__ == '__main__':
    unittest.main()
