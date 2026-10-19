"""Simple Cache entry reading; every entry is built by hand for the test."""

import hashlib
import os
import pathlib
import struct
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.chromium import simple_cache  # pylint: disable=wrong-import-position

KEY = b'1/0/_dk_https://example.test https://example.test https://example.test/a.png'
HEADERS = b'HTTP/1.1 200 OK\x00content-type: image/png\x00\x00'


def entry(body, stream1_field, stream1_magic=simple_cache.SIMPLE_EOF_MAGIC, key_sha256=False):
    """An entry file: header, key, body, stream 1 EOF, stream 0 pickle, [key SHA-256], stream 0 EOF."""
    stream0 = struct.pack('<Iiqq', 0, 0, 0, 0) + struct.pack('<I', len(HEADERS)) + HEADERS
    out = struct.pack('<QIII', simple_cache.SIMPLE_HEADER_MAGIC, 5, len(KEY), 0) + b'\x00' * 4
    out += KEY + body
    out += struct.pack('<QIII', stream1_magic, 1, 0, stream1_field) + b'\x00' * 4
    out += stream0
    if key_sha256:
        out += hashlib.sha256(KEY).digest()
    flags = 3 if key_sha256 else 1
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, flags, 0, len(stream0)) + b'\x00' * 4
    return out


class ReadEntryTest(unittest.TestCase):

    def read(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, '0123456789abcdef_0')
            with open(path, 'wb') as handle:
                handle.write(data)
            found = simple_cache.read_entry(path)
            return found, found.read_body() if found else None

    def test_body_size_comes_from_the_layout(self):
        body = b'\x89PNG\r\n\x1a\n' + bytes(range(40))
        for field, sha in ((0, False), (len(body), False), (0, True)):
            with self.subTest(stream1_stream_size=field, key_sha256=sha):
                found, read = self.read(entry(body, field, key_sha256=sha))
                self.assertEqual(found.body_size, len(body))
                self.assertEqual(read, body)

    def test_no_stream1_record_means_no_body(self):
        found, read = self.read(entry(b'abc', 3, stream1_magic=0))
        self.assertEqual(found.body_size, 0)
        self.assertEqual(read, b'')


if __name__ == '__main__':
    unittest.main()
