"""macOS MobileBluetooth LE device tables, current and read from the write-ahead log.
Every value here is made up."""

import os
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosMobileBluetooth as artifact  # pylint: disable=wrong-import-position

SCHEMA = ('CREATE TABLE {}(Uuid TEXT, Name TEXT, NameOrigin INT, Address TEXT, ResolvedAddress TEXT, '
          'LastSeenTime INT, LastConnectionTime INT, GATTServiceChangeConfig INT, Tags TEXT, '
          'iCloudIdentifier TEXT)')


def write_live(path, table, steps):
    """A WAL-mode database copied with its -wal and -shm while its writer holds the log open
    and uncheckpointed. steps is a list of SQL statement lists, each committed on its own."""
    with tempfile.TemporaryDirectory() as scratch:
        original = os.path.join(scratch, os.path.basename(path))
        con = sqlite3.connect(original)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA wal_autocheckpoint=0')
        con.execute(SCHEMA.format(table))
        con.commit()
        for statements in steps:
            for sql in statements:
                con.execute(sql)
            con.commit()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for suffix in ('', '-wal', '-shm'):
            shutil.copyfile(original + suffix, path + suffix)
        con.close()


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def row(table, uuid, name, seen, connected=0, icloud='ic-1'):
    return (f"INSERT INTO {table} VALUES ('{uuid}', '{name}', 1, 'AA:BB:CC:00:00:0{uuid[-1]}', "
            f"'', {seen}, {connected}, 0, '', '{icloud}')")


class MobileBluetoothTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='macbt_')
        self.addCleanup(shutil.rmtree, self.root, True)
        patcher = patch.object(artifact, 'logfunc', lambda *a, **k: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _files(self):
        return sorted(os.path.join(folder, name) for folder, _, names in os.walk(self.root)
                      for name in names)

    def test_a_device_only_the_log_holds_is_listed_and_an_earlier_version_is_not(self):
        db = os.path.join(self.root, 'Library', 'Bluetooth',
                          'com.apple.MobileBluetooth.ledevices.other.db')
        write_live(db, 'OtherDevices', [
            [row('OtherDevices', 'u-1', 'Keyboard', 10), row('OtherDevices', 'u-2', 'Speaker', 20)],
            ["UPDATE OtherDevices SET LastSeenTime = 30 WHERE Uuid = 'u-1'"],
            ["DELETE FROM OtherDevices WHERE Uuid = 'u-2'"],
        ])
        headers, rows, source = artifact.macosBluetoothOtherLE.__wrapped__(Context(self.root, self._files()))
        self.assertEqual(headers[-2:], ('Record State', 'Read From'))
        self.assertTrue(all(len(r) == len(headers) for r in rows))
        by_state = {(r[2], r[-2]): r for r in rows}
        self.assertEqual(sorted(by_state), [('u-1', 'Current'), ('u-2', 'Not in current state')])
        self.assertEqual(by_state[('u-1', 'Current')][0], 30)
        removed = by_state[('u-2', 'Not in current state')]
        self.assertEqual((removed[0], removed[3]), (20, 'Speaker'))
        self.assertTrue(removed[-1].startswith('com.apple.MobileBluetooth.ledevices.other.db-wal, committed'))
        self.assertEqual(source, db)

    def test_paired_rows_carry_the_icloud_identifier(self):
        db = os.path.join(self.root, 'Library', 'Bluetooth',
                          'com.apple.MobileBluetooth.ledevices.paired.db')
        write_live(db, 'PairedDevices', [[row('PairedDevices', 'u-3', 'Mouse', 5, 2, 'ic-9')]])
        headers, rows, _source = artifact.macosBluetoothPairedLE.__wrapped__(Context(self.root, self._files()))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [(5, 2, 'u-3', 'Mouse', 1, 'AA:BB:CC:00:00:03', '', 'ic-9', 'Current', '')])

    def test_the_sidecars_are_not_read_as_databases(self):
        db = os.path.join(self.root, 'Library', 'Bluetooth',
                          'com.apple.MobileBluetooth.ledevices.paired.db')
        write_live(db, 'PairedDevices', [[row('PairedDevices', 'u-4', 'Pen', 1)]])
        self.assertEqual(len(self._files()), 3)
        _headers, rows, source = artifact.macosBluetoothPairedLE.__wrapped__(Context(self.root, self._files()))
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, db)


if __name__ == '__main__':
    unittest.main()
