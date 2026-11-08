"""Pin scripts/artifacts/qbittorrent.py on BT_backup files and a log built here (made-up values)."""
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

import bencoding

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import qbittorrent as qbt  # pylint: disable=wrong-import-position

HASH = 'ab' * 20


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class QbittorrentTest(unittest.TestCase):
    def test_torrents_and_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            backup = pathlib.Path(tmp, 'Users', 'lab', 'AppData', 'Local', 'qBittorrent', 'BT_backup')
            backup.mkdir(parents=True)
            resume = {b'added_time': 1700000000, b'completed_time': 0, b'last_download': 0, b'last_upload': 1700000100,
                      b'total_downloaded': 0, b'total_uploaded': 1234, b'active_time': 5, b'seeding_time': 0,
                      b'paused': 1, b'name': b'item', b'info-hash': bytes.fromhex(HASH), b'save_path': b'C:\\dl',
                      b'qBt-name': b'', b'qBt-category': b'cat', b'qBt-tags': [b't1', b't2'], b'qBt-comment': b'',
                      b'comment': b'own comment', b'qBt-sslPrivateKey': b'NEVER SHOWN',
                      b'trackers': [[b'http://tracker.invalid/announce']]}
            (backup / f'{HASH}.fastresume').write_bytes(bencoding.bencode(resume))
            (backup / f'{HASH}.torrent').write_bytes(bencoding.bencode(
                {b'info': {b'name': b'item', b'files': [{b'length': 3, b'path': [b'a.txt']},
                                                         {b'length': 4, b'path': [b'sub', b'b.bin']}]}}))
            (backup / 'queue').write_bytes(b'cd' * 20 + b'\n' + HASH.encode() + b'\n')
            (backup / 'broken.fastresume').write_bytes(b'not bencode')
            logs = backup.parent / 'logs'
            logs.mkdir()
            (logs / 'qbittorrent.log').write_text('(N) 2026-01-02T03:04:05 - Added new torrent. Torrent: "item"\n'
                                                  '(W) 2026-01-02T03:04:06 - Something odd\nnot a log line\n',
                                                  encoding='utf-8')
            files = [str(p) for p in backup.iterdir()]
            context = FakeContext(tmp, files)
            with mock.patch.object(qbt, 'logfunc') as log:
                headers, rows, _source = qbt.qbittorrentTorrents.__wrapped__(context)
            self.assertEqual(len(headers), len(rows[0]))
            self.assertEqual(rows, [(datetime.fromtimestamp(1700000000, timezone.utc), '', '',
                                     datetime.fromtimestamp(1700000100, timezone.utc), 'item', HASH, 'C:\\dl', 'cat',
                                     't1, t2', 0, 1234, 5, 0, 'Yes', 2, 'http://tracker.invalid/announce',
                                     'item/a.txt\nitem/sub/b.bin', 7, 'own comment', 'lab')])
            self.assertNotIn('NEVER SHOWN', repr(rows))
            self.assertIn('broken.fastresume did not decode', log.call_args_list[0].args[0])
            _headers, log_rows, _source = qbt.qbittorrentLog.__wrapped__(
                FakeContext(tmp, [str(logs / 'qbittorrent.log')]))
            self.assertEqual(log_rows, [('2026-01-02 03:04:05', 'Normal', 'Added new torrent. Torrent: "item"', 'item',
                                         'qbittorrent.log', 'lab'),
                                        ('2026-01-02 03:04:06', 'Warning', 'Something odd', '', 'qbittorrent.log', 'lab')])


if __name__ == '__main__':
    unittest.main()
