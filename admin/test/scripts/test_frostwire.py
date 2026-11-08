"""Pin the FrostWire artifacts.

The resume and torrent files are built here with the fields libtorrent 2.0 writes (the known data
windows11_arm_frostwire_known_20261108 has the same keys), with made-up values.
"""
import hashlib
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

import bencoding

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import frostwire  # pylint: disable=wrong-import-position

INFO = {b'name': b'one.bin', b'length': 1000, b'piece length': 16384, b'pieces': hashlib.sha1(b'x').digest()}
INFO_HASH = hashlib.sha1(bencoding.bencode(INFO)).digest()
RESUME = {
    b'file-format': b'libtorrent resume file', b'info-hash': INFO_HASH, b'name': b'one.bin',
    b'added_time': 1700000000, b'completed_time': 1700000100, b'last_download': 0, b'last_upload': 1700000200,
    b'total_downloaded': 1000, b'total_uploaded': 500, b'active_time': 60, b'seeding_time': 30, b'paused': 1,
    b'save_path': b'C:\\Users\\lab\\Documents\\FrostWire\\Torrent Data',
    b'trackers': [[b'http://192.0.2.1:6969/announce'], [b'http://192.0.2.2/announce']],
}
MULTI_INFO = {b'name': b'pack', b'piece length': 16384, b'pieces': b'',
              b'files': [{b'length': 10, b'path': [b'a.txt']}, {b'length': 20, b'path': [b'sub', b'b.txt']}]}
PROPS = ('#FrostWire properties file\n'
         'DEFAULT_TORRENT_DATA_DIR_SETTING=C\\:\\\\Users\\\\lab\\\\Documents\\\\FrostWire\\\\Torrent Data\n'
         'TORRENTS_DIR_SETTING=C\\:\\\\T\\u00e9st\\\\Torrents\n'
         'TORRENT_DATA_DIR_SETTING=C\\:\\\\not\\\\read\n')


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class FrostWireTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        root = pathlib.Path(self.tmp.name)
        self.files = []
        lt = root / 'Users' / 'lab' / '.frostwire5' / 'libtorrent'
        lt.mkdir(parents=True)
        (lt / f'{INFO_HASH.hex()}.resume').write_bytes(bencoding.bencode(RESUME))
        (lt / f'{INFO_HASH.hex()}.torrent').write_bytes(bencoding.bencode({b'info': INFO}))
        multi = {**RESUME, b'info': MULTI_INFO, b'name': b'pack', b'info-hash': b'\x00' * 20, b'paused': 0}
        (lt / ('ab' * 20 + '.resume')).write_bytes(bencoding.bencode(multi))
        (lt / 'broken.resume').write_bytes(b'not bencode')
        (root / 'Users' / 'lab' / '.frostwire5' / 'frostwire.props').write_text(PROPS, encoding='latin-1')
        linux = root / 'home' / 'tux' / '.frostwire5'
        linux.mkdir(parents=True)
        (linux / 'frostwire.props').write_text(PROPS, encoding='latin-1')
        self.files = [str(p) for p in lt.iterdir()] + [str(root / 'Users' / 'lab' / '.frostwire5' / 'frostwire.props'),
                                                       str(linux / 'frostwire.props')]
        self.context = FakeContext(self.tmp.name, self.files)

    def tearDown(self):
        self.tmp.cleanup()

    def test_torrents(self):
        with mock.patch.object(frostwire, 'logfunc') as log:
            headers, rows, sources = frostwire.frostwireTorrents.__wrapped__(self.context)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(headers), len(rows[0]))
        one = next(r for r in rows if r[4] == 'one.bin')
        self.assertEqual(one[0], datetime.fromtimestamp(1700000000, timezone.utc))
        self.assertEqual(one[2], '')
        self.assertEqual(one[5], INFO_HASH.hex())
        self.assertEqual(one[7:12], (1000, 500, 60, 30, 'Yes'))
        self.assertEqual(one[12], 'http://192.0.2.1:6969/announce\nhttp://192.0.2.2/announce')
        self.assertEqual((one[13], one[14], one[15]), ('one.bin', 1000, 'lab'))
        pack = next(r for r in rows if r[4] == 'pack')
        self.assertEqual(pack[5], 'ab' * 20)            # zero info-hash falls back to the file name
        self.assertEqual((pack[11], pack[13], pack[14]), ('No', 'pack/a.txt\npack/sub/b.txt', 30))
        self.assertTrue(any('broken.resume' in str(c) for c in log.call_args_list))
        self.assertEqual(len(sources.split('\n')), 2)

    def test_folders(self):
        with mock.patch.object(frostwire, 'logfunc'):
            _, rows, _ = frostwire.frostwireFolders.__wrapped__(self.context)
        lab = [r[:2] for r in rows if r[2] == 'lab']
        self.assertEqual(lab, [('Torrent Data Folder', 'C:\\Users\\lab\\Documents\\FrostWire\\Torrent Data'),
                               ('Torrents Folder', 'C:\\Tést\\Torrents')])
        self.assertEqual({r[2] for r in rows}, {'lab', 'tux'})
        self.assertNotIn('C:\\not\\read', str(rows))


if __name__ == '__main__':
    unittest.main()
