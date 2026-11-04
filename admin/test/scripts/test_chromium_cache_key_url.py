"""The URL both Chromium cache readers take from an entry key.

Keys follow the shapes in net/http/http_cache.cc (see scripts/chromium/cache_key.py).
Every host is a reserved example name; no key here comes from evidence.
"""

import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# pylint: disable=wrong-import-position
from scripts.chromium import blockfile_cache, simple_cache
import test_discord_blockfile_cache as blockfile_fixture

TARGET = 'https://cdn.example.test/a.png'
REDIRECT = 'https://t.example.test/r?u=https://x.example.test/y&v=http://z.example.test/'

# (key, URL the reader must report)
KEYS = (
    (TARGET, TARGET),
    ('1/0/' + TARGET, TARGET),
    ('0/12345/https://up.example.test/upload', 'https://up.example.test/upload'),
    ('1/0/_dk_https://site.example.test https://site.example.test ' + TARGET, TARGET),
    ('1/0/_dk_s_https://site.example.test https://frame.example.test ' + TARGET, TARGET),
    (REDIRECT, REDIRECT),
    ('1/0/' + REDIRECT, REDIRECT),
    ('1/0/_dk_https://site.example.test https://site.example.test ' + REDIRECT, REDIRECT),
    ('quicserverinfo:https://h.example.test:443', ''),
)

HEADERS = b'HTTP/1.1 200 OK\x00content-type: image/png\x00\x00'


def simple_entry(key):
    """A Simple Cache *_0 file: header, key, empty body, stream 1 EOF, stream 0, stream 0 EOF."""
    key = key.encode()
    stream0 = struct.pack('<Iiqq', 0, 0, 0, 0) + struct.pack('<I', len(HEADERS)) + HEADERS
    out = struct.pack('<QIII', simple_cache.SIMPLE_HEADER_MAGIC, 5, len(key), 0) + b'\x00' * 4
    out += key
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, 1, 0, 0) + b'\x00' * 4
    out += stream0
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, 1, 0, len(stream0)) + b'\x00' * 4
    return out


class SimpleCacheKeyUrlTest(unittest.TestCase):

    def test_read_entry_reports_the_url_after_the_isolation_key(self):
        with tempfile.TemporaryDirectory() as folder:
            for index, (key, url) in enumerate(KEYS):
                with self.subTest(key=key):
                    path = os.path.join(folder, f'{index:016x}_0')
                    with open(path, 'wb') as handle:
                        handle.write(simple_entry(key))
                    found = simple_cache.read_entry(path)
                    self.assertEqual(found.key, key)
                    self.assertEqual(found.url, url)
                    self.assertEqual(found.key_prefix + found.url, key)


class BlockfileCacheKeyUrlTest(unittest.TestCase):

    def test_iter_entries_reports_the_url_after_the_isolation_key(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(blockfile_fixture, '_cache_key', lambda key: key.encode()):
            cache = blockfile_fixture.BlockfileCache(os.path.join(folder, 'Cache_Data'),
                                                     table_length=len(KEYS))
            for bucket, (key, _url) in enumerate(KEYS):
                cache.add(key, b'body', 'image/png', bucket=bucket)
            entries = {entry.key: entry for entry in blockfile_cache.iter_entries(cache.write())}
        self.assertEqual(sorted(entries), sorted(key for key, _url in KEYS))
        for key, url in KEYS:
            with self.subTest(key=key):
                self.assertEqual(entries[key].url, url)
                self.assertEqual(entries[key].key_prefix + entries[key].url, key)


if __name__ == '__main__':
    unittest.main()
