"""Pin the RPM Installed Packages artifact (scripts/artifacts/linuxRpmPackages.py).

The RPM header blobs are built here in the RPM header binary format the artifact parses, and stored in a
Packages table like the one rpmdb.sqlite keeps. The values are made up.
"""
import datetime
import os
import pathlib
import sqlite3
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxRpmPackages as rpm
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
B0 = datetime.datetime(2023, 11, 14, 22, 13, 20, tzinfo=UTC)   # 1700000000
B1 = datetime.datetime(2023, 11, 14, 22, 15, 0, tzinfo=UTC)    # 1700000100
BUILD = datetime.datetime(2020, 9, 13, 12, 26, 40, tzinfo=UTC)  # 1600000000

STR, INT32, INT64 = 6, 4, 5


def header(tags):
    """Build one RPM header blob: (nindex, hsize), index entries (tag,type,offset,count), then the data store."""
    store = b''
    index = b''
    for tag, vtype, value in tags:
        offset = len(store)
        if vtype == STR:
            data = value.encode('utf-8') + b'\x00'
        elif vtype == INT64:
            data = struct.pack('>Q', value)
        else:  # INT32
            data = struct.pack('>I', value)
        store += data
        index += struct.pack('>IIII', tag, vtype, offset, 1)
    return struct.pack('>II', len(tags), len(store)) + index + store


FIREFOX = header([
    (1000, STR, 'firefox'), (1003, INT32, 0), (1001, STR, '1.0'), (1002, STR, '1.fc44'), (1022, STR, 'x86_64'),
    (1008, INT32, 1700000100), (1006, INT32, 1600000000), (1009, INT32, 500), (1011, STR, 'Fedora Project'),
    (1014, STR, 'MIT'), (1016, STR, 'Applications'), (1044, STR, 'firefox-1.0-1.fc44.src.rpm'),
    (1004, STR, 'A web browser')])
GLIB2 = header([
    (1000, STR, 'glib2'), (1003, INT32, 2), (1001, STR, '2.0'), (1002, STR, '3'), (1022, STR, 'x86_64'),
    (1008, INT32, 1700000000), (1006, INT32, 1600000000), (1009, INT32, 900), (1011, STR, 'Fedora Project'),
    (1014, STR, 'LGPL-2.1'), (1016, STR, 'Libraries'), (1044, STR, 'glib2-2.0-3.src.rpm'), (1004, STR, 'A library')])
NONAME = header([(1001, STR, '1.0'), (1002, STR, '1')])  # no NAME -> skipped
# a gpg-pubkey key header: NAME but no ARCH and no VENDOR, and a build time
GPGKEY = header([(1000, STR, 'gpg-pubkey'), (1001, STR, '9570ff31'), (1002, STR, '5e3006fb'),
                 (1006, INT32, 1700000000), (1004, STR, 'gpg(Fedora)')])
# an rpm v6 package: size recorded in LONGSIZE (int64), no int32 SIZE
V6 = header([(1000, STR, 'bigpkg'), (1001, STR, '2.0'), (1002, STR, '1'), (1022, STR, 'aarch64'),
             (1008, INT32, 1700000050), (5009, INT64, 5_000_000_000)])


def build(path, blobs=(FIREFOX, GLIB2, NONAME), packages=True):
    db = sqlite3.connect(path)
    if packages:
        db.execute('CREATE TABLE Packages (hnum INTEGER PRIMARY KEY AUTOINCREMENT, blob BLOB NOT NULL)')
        db.executemany('INSERT INTO Packages (blob) VALUES (?)', [(b,) for b in blobs])
    else:
        db.execute('CREATE TABLE other (x INTEGER)')
    db.commit(); db.close()


class HeaderParse(unittest.TestCase):
    def test_parse_header(self):
        h = rpm.parse_header(GLIB2)
        self.assertEqual((h['NAME'], h['EPOCH'], h['VERSION'], h['RELEASE'], h['ARCH']),
                         ('glib2', 2, '2.0', '3', 'x86_64'))
        self.assertEqual((h['INSTALLTIME'], h['SIZE'], h['VENDOR']), (1700000000, 900, 'Fedora Project'))

    def test_too_short(self):
        self.assertEqual(rpm.parse_header(b'\x00\x00'), {})
        self.assertEqual(rpm.parse_header(None), {})

    def test_nevra_omits_zero_epoch(self):
        self.assertEqual(rpm._nevra(rpm.parse_header(FIREFOX)), 'firefox-1.0-1.fc44.x86_64')  # pylint: disable=protected-access

    def test_nevra_omits_absent_arch(self):  # a gpg-pubkey header has no ARCH: no trailing dot
        self.assertEqual(rpm._nevra(rpm.parse_header(GPGKEY)), 'gpg-pubkey-9570ff31-5e3006fb')  # pylint: disable=protected-access

    def test_longsize_int64(self):
        self.assertEqual(rpm.parse_header(V6)['LONGSIZE'], 5_000_000_000)


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def database(self, **kw):
        folder = os.path.join(self.folder.name, 'usr', 'lib', 'sysimage', 'rpm')
        os.makedirs(folder)
        path = os.path.join(folder, 'rpmdb.sqlite')
        build(path, **kw)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(rpm, 'logfunc') as log:
            result = rpm.linuxRpmPackages.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows(self):
        path = self.database()
        (headers, rows, located), logged = self.run_artifact([path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 10)
        self.assertEqual((headers[0], headers[1]), (('Install Time (UTC)', 'datetime'),
                                                    ('Build Time (UTC)', 'datetime')))
        self.assertEqual(rows, [   # sorted by install time: glib2 (earlier) then firefox; NONAME skipped
            (B0, BUILD, 'glib2-2:2.0-3.x86_64', 'Fedora Project', '900', 'LGPL-2.1', 'Libraries',
             'glib2-2.0-3.src.rpm', 'A library', rel),
            (B1, BUILD, 'firefox-1.0-1.fc44.x86_64', 'Fedora Project', '500', 'MIT', 'Applications',
             'firefox-1.0-1.fc44.src.rpm', 'A web browser', rel)])
        self.assertEqual(located, path)
        self.assertEqual(logged, [f'RPM Installed Packages: 1 header(s) skipped in {rel}'])

    def test_gpgkey_and_v6_rows(self):
        path = self.database(blobs=(GPGKEY, V6))
        (_, rows, _), _ = self.run_artifact([path])
        by_pkg = {r[2]: r for r in rows}
        # gpg-pubkey: no trailing dot, blank Vendor, blank Size (no SIZE/LONGSIZE)
        self.assertIn('gpg-pubkey-9570ff31-5e3006fb', by_pkg)
        self.assertEqual((by_pkg['gpg-pubkey-9570ff31-5e3006fb'][3], by_pkg['gpg-pubkey-9570ff31-5e3006fb'][4]),
                         ('', ''))
        # rpm v6 package: Size read from LONGSIZE
        self.assertEqual(by_pkg['bigpkg-2.0-1.aarch64'][4], '5000000000')

    def test_no_packages_table(self):
        path = self.database(packages=False)
        (_, rows, located), logged = self.run_artifact([path])
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(len(logged), 1)
        self.assertIn('has no Packages table', logged[0])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
