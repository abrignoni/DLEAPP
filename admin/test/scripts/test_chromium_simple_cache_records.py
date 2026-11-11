"""The Chromium Simple Cache Records artifact on a hand-built macOS tree; every value is made up.

The tree holds one cache under two spellings (Users and System/Volumes/Data/Users), which must be read once,
a second profile, which must add its own rows, and a folder with the same layout under another
application's name, which must add none.
"""

import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import chromiumCacheRecords as cache  # pylint: disable=wrong-import-position
from scripts.chromium import browser_profiles, simple_cache  # pylint: disable=wrong-import-position

RESPONSE = 13_400_000_000_000_000                       # base::Time microseconds, in 2025
REQUEST = RESPONSE - 250_000


def entry(key, headers, body):
    """An entry file: header, key, body, stream 1 EOF, stream 0 pickle, stream 0 EOF."""
    raw_headers = b'\x00'.join(headers) + b'\x00\x00'
    stream0 = struct.pack('<Iiqq', 0, 3, REQUEST, RESPONSE) + struct.pack('<I', len(raw_headers)) + raw_headers
    stream0 = struct.pack('<I', len(stream0) - 4) + stream0[4:]
    out = struct.pack('<QIII', simple_cache.SIMPLE_HEADER_MAGIC, 5, len(key), 0) + b'\x00' * 4
    out += key + body
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, 1, 0, 0) + b'\x00' * 4
    out += stream0
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, 1, 0, len(stream0)) + b'\x00' * 4
    return out


PNG = b'\x89PNG\r\n\x1a\n' + bytes(range(64))
PICTURE = entry(b'1/0/_dk_https://fixture.test https://fixture.test https://img.fixture.test/a.png',
                [b'HTTP/1.1 200 OK', b'content-type: image/png'], PNG)
PAGE = entry(b'1/0/https://fixture.test/page', [b'HTTP/1.1 404 Not Found', b'Content-Type: text/html; charset=utf-8'],
             b'<html></html>')
OTHER = entry(b'1/0/https://second.fixture.test/x', [b'HTTP/1.1 204 No Content'], b'')


class _Context:

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def _write(root, relative, files):
    folder = os.path.join(root, *relative.split('/'))
    os.makedirs(folder)
    written = []
    for name, data in files.items():
        written.append(os.path.join(folder, name))
        with open(written[-1], 'wb') as handle:
            handle.write(data)
    return written


class SimpleCacheRecordsTest(unittest.TestCase):

    def _run(self, trees):
        with tempfile.TemporaryDirectory() as root:
            files = []
            for relative, content in trees:
                files.extend(_write(root, relative, content))
            checked = []

            def check_in(source, body, **kwargs):
                checked.append((os.path.basename(source), body, kwargs.get('force_type')))
                return 'media-ref'

            with mock.patch.object(cache, 'check_in_embedded_media', check_in), \
                    mock.patch.object(cache, 'logfunc', lambda *_a, **_k: None):
                headers, rows, sources = cache.chromiumSimpleCacheRecords.__wrapped__(_Context(root, files))
            relative = [os.path.relpath(s, root).replace(os.sep, '/') for s in sources.split('\n') if s]
            return headers, rows, relative, checked

    def test_rows(self):
        main = {'0000000000000001_0': PICTURE, '0000000000000002_0': PAGE, '0000000000000003_s': b'sparse',
                '0000000000000004_0': b'not an entry', 'index': b'x'}
        default = 'Library/Caches/Google/Chrome/Default/Cache/Cache_Data'
        headers, rows, sources, checked = self._run([
            ('Users/fixture/' + default, main),
            ('System/Volumes/Data/Users/fixture/' + default, main),
            ('Users/fixture/Library/Caches/Google/Chrome/Profile 1/Cache/Cache_Data', {'0000000000000009_0': OTHER}),
            ('Users/fixture/Library/Caches/OtherApp/Default/Cache/Cache_Data', {'0000000000000001_0': PICTURE}),
            ('Users/fixture/Library/Caches/Google/Chrome/Default/Code Cache/js', {'0000000000000001_0': PICTURE}),
        ])
        self.assertEqual(len(headers), 14)
        self.assertEqual(len(rows), 3)                          # 2 + 1: the copy and the two decoys add none
        when = datetime(2025, 8, 18, 14, 13, 20, tzinfo=timezone.utc)
        picture = next(row for row in rows if row[2].endswith('a.png'))
        self.assertEqual(picture, (
            when, datetime(2025, 8, 18, 14, 13, 19, 750000, tzinfo=timezone.utc), 'https://img.fixture.test/a.png',
            'img.fixture.test', '200', 'image/png', len(PNG), 'media-ref',
            'https://fixture.test https://fixture.test', '1/0/', '0000000000000001_0',
            'Google Chrome', 'Default', 'fixture'))
        page = next(row for row in rows if row[2].endswith('/page'))
        self.assertEqual(page[4:9], ('404', 'text/html', 13, '', ''))
        other = next(row for row in rows if 'second' in row[2])
        self.assertEqual(other[4:8] + other[10:], ('204', '', 0, '', '0000000000000009_0', 'Google Chrome',
                                                    'Profile 1', 'fixture'))
        self.assertEqual(checked, [('0000000000000001_0', PNG, 'image/png')])
        self.assertEqual(sorted(sources), [
            'Users/fixture/Library/Caches/Google/Chrome/Default/Cache/Cache_Data/index',
            'Users/fixture/Library/Caches/Google/Chrome/Profile 1/Cache/Cache_Data/0000000000000009_0'])

    def test_chromium_root_and_no_cache(self):
        _headers, rows, sources, _checked = self._run([
            ('Users/fixture/Library/Caches/Chromium/Default/Cache/Cache_Data', {'0000000000000002_0': PAGE})])
        self.assertEqual([(row[11], row[12], row[13]) for row in rows], [('Chromium', 'Default', 'fixture')])
        self.assertEqual(len(sources), 1)
        _headers, rows, sources, _checked = self._run([
            ('Users/fixture/Library/Caches/Google/Chrome/Default/Cache/Cache_Data', {'index': b'x'})])
        self.assertEqual((rows, sources), ([], []))

    def test_cache_roots_are_located(self):
        self.assertEqual(
            browser_profiles.locate('Users/fixture/Library/Caches/Google/Chrome/Default/Cache/Cache_Data/a_0')[:3],
            ('Google Chrome', 'Default', 'fixture'))
        self.assertIsNone(browser_profiles.locate('Users/fixture/Library/Caches/OtherApp/Default/Cache/a_0'))


if __name__ == '__main__':
    unittest.main()
