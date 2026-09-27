"""Records in WebKitCache folders, written here the way WTF::Persistence::Encoder writes them."""

import datetime
import fnmatch
import hashlib
import os
import pathlib
import struct
import tempfile
import unittest
from unittest import mock

from scripts import macos_plists
from scripts.artifacts import macosWebKitCache

UTC = datetime.timezone.utc
SALTS = {'bool': 3, 'u32': 11, 'u64': 13, 'i16': 103, 'i64': 19, 'f64': 29, 'data': 101}
FORMATS = {'bool': '<?', 'u32': '<I', 'u64': '<Q', 'i16': '<h', 'i64': '<q', 'f64': '<d'}
CACHE = 'Users/alice/Library/Containers/com.apple.Safari/Data/Library/Caches/com.apple.Safari/WebKitCache/Version 17'
NAME = 'A28C6ED72A90EE17C5319B04C4799C2B273EF9CF'


class Encoder:
    def __init__(self):
        self.out = bytearray()
        self.sha1 = hashlib.sha1()

    def _add(self, raw, salt):
        self.sha1.update(struct.pack('<I', salt))
        self.sha1.update(raw)
        self.out += raw

    def number(self, kind, value):
        self._add(struct.pack(FORMATS[kind], value), SALTS[kind])

    def fixed(self, raw):
        self._add(raw, SALTS['data'])

    def string(self, text, wide=False):
        if text is None:
            self.number('u32', 0xFFFFFFFF)
            return
        self.number('u32', len(text))
        self.number('bool', not wide)
        self.fixed(text.encode('utf-16-le') if wide else text.encode('latin-1'))

    def checksum(self):
        self.out += self.sha1.digest()


def response_header(url, status=200, mime='text/html', version='HTTP/2.0', headers=(('Date', 'x'),), null=False):
    encoder = Encoder()
    encoder.number('bool', null)
    if not null:
        encoder.string(url)
        encoder.string(mime)
        encoder.number('i64', 1234)
        encoder.string(None)
        encoder.string('')
        encoder.string(version)
        encoder.number('u64', len(headers))
        for name, value in headers:
            encoder.string(name)
            encoder.string(value)
        encoder.number('i16', status)
    encoder.out += b'rest of the response, not read'
    return bytes(encoder.out)


def record(salt, url, kind='Resource', partition='example.com', stored=None, header=b'', body=b'', version=17,
           wide=False, spoil_checksum=False, inline=None):
    encoder = Encoder()
    encoder.number('u32', version)
    encoder.string(partition)
    encoder.string(kind)
    encoder.string(url, wide=wide)
    encoder.string(None)
    encoder.fixed(b'\x01' * 20)
    encoder.fixed(b'\x02' * 20)
    stamp = (stored or datetime.datetime(2025, 12, 1, 22, 36, 27, 57263, tzinfo=UTC)).timestamp()
    encoder.number('f64', stamp)
    encoder.fixed(hashlib.sha1(salt + header).digest())
    encoder.number('u64', len(header))
    encoder.fixed(hashlib.sha1(salt + body).digest())
    encoder.number('u64', len(body))
    encoder.number('bool', bool(body) if inline is None else inline)
    encoder.checksum()
    if spoil_checksum:
        encoder.out[-1] ^= 0xFF
    return bytes(encoder.out) + header + body


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class WebKitCacheTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []
        self.salt = b'\x10\x20\x30\x40\x50\x60\x70\x80'

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def _run(self, files):
        with mock.patch.object(macosWebKitCache, 'logfunc', self.logs.append), \
                mock.patch.object(macos_plists, 'logfunc', self.logs.append):
            return macosWebKitCache.macosWebKitCache.__wrapped__(FakeContext(self.root, files))

    def test_a_resource_and_a_subresources_record(self):
        salt = self._write(f'{CACHE}/salt', self.salt)
        url = 'https://m.media-amazon.com/images/I/51S.js'
        header = response_header(url, headers=(('Content-Type', 'application/x-javascript'), ('Date', 'Mon, 01 Dec 2025 22:36:26 GMT')),
                                 mime='application/x-javascript')
        resource = self._write(f'{CACHE}/Records/DEC366BD/Resource/{NAME}',
                               record(self.salt, url, header=header, body=b'body!'))
        page = self._write(f'{CACHE}/Records/DEC366BD/SubResources/{"B" * 40}',
                           record(self.salt, 'https://www.example.com/', kind='SubResources',
                                  header=response_header('https://www.example.com/'), inline=False))
        headers, rows, source = self._run([salt, resource, page])
        self.assertEqual(headers[0], ('Stored (UTC)', 'datetime'))
        self.assertEqual(rows, [
            (datetime.datetime(2025, 12, 1, 22, 36, 27, 57263, tzinfo=UTC), 'example.com', 'Resource', url, '200',
             'application/x-javascript', 'HTTP/2.0',
             'Content-Type: application/x-javascript\nDate: Mon, 01 Dec 2025 22:36:26 GMT', 5, 'record', 17,
             'com.apple.Safari', f'{CACHE}/Records/DEC366BD/Resource/{NAME}'),
            (datetime.datetime(2025, 12, 1, 22, 36, 27, 57263, tzinfo=UTC), 'example.com', 'SubResources',
             'https://www.example.com/', '', '', '', '', 0, 'blob file', 17, 'com.apple.Safari',
             f'{CACHE}/Records/DEC366BD/SubResources/{"B" * 40}'),
        ])
        self.assertEqual(source.split('\n'), [resource, page])

    def test_records_that_fail_their_checks_are_counted_and_left_out(self):
        salt = self._write(f'{CACHE}/salt', self.salt)
        spoiled = self._write(f'{CACHE}/Records/P/Resource/{"C" * 40}',
                              record(self.salt, 'https://a.example/', header=response_header('https://a.example/'),
                                     spoil_checksum=True))
        wrong_salt = self._write(f'{CACHE}/Records/P/Resource/{"D" * 40}',
                                 record(b'otherslt', 'https://b.example/', header=response_header('https://b.example/')))
        cut = self._write(f'{CACHE}/Records/P/Resource/{"E" * 40}', b'\x11\x00\x00\x00\x0a\x00')
        _headers, rows, source = self._run([salt, spoiled, wrong_salt, cut])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn('WebKit Network Cache: 1 records whose header hash did not match, 2 records whose metadata could '
                      'not be read or whose checksum did not match', self.logs)

    def test_without_a_salt_the_record_is_reported_and_counted(self):
        path = self._write(f'{CACHE}/Records/P/Resource/{NAME}',
                           record(self.salt, 'https://a.example/', header=response_header('https://a.example/')))
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows[0][3:5], ('https://a.example/', '200'))
        self.assertIn('WebKit Network Cache: 1 records with no readable salt file of at least 8 bytes beside them, '
                      'header hash not checked', self.logs)

    def test_a_salt_shorter_than_8_bytes_is_not_used(self):
        salt = self._write(f'{CACHE}/salt', self.salt[:7])
        path = self._write(f'{CACHE}/Records/P/Resource/{NAME}',
                           record(self.salt[:7], 'https://a.example/', header=response_header('https://a.example/')))
        _headers, rows, _source = self._run([salt, path])
        self.assertEqual(rows[0][3:5], ('https://a.example/', '200'))
        self.assertIn('WebKit Network Cache: 1 records with no readable salt file of at least 8 bytes beside them, '
                      'header hash not checked', self.logs)

    def test_only_the_first_8_bytes_of_the_salt_file_are_used(self):
        salt = self._write(f'{CACHE}/salt', self.salt + b'extra bytes')
        path = self._write(f'{CACHE}/Records/P/Resource/{NAME}',
                           record(self.salt, 'https://a.example/', header=response_header('https://a.example/')))
        _headers, rows, _source = self._run([salt, path])
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.logs, ['WebKit Network Cache: 1 record(s).'])

    def test_another_cache_version_keeps_the_key_and_leaves_the_response_out(self):
        salt = self._write(f'{CACHE}/salt', self.salt)
        path = self._write(f'{CACHE}/Records/P/Resource/{NAME}',
                           record(self.salt, 'https://a.example/', header=response_header('https://a.example/'), version=18))
        _headers, rows, _source = self._run([salt, path])
        self.assertEqual(rows[0][3:8] + rows[0][10:11], ('https://a.example/', '', '', '', '', 18))
        self.assertIn('WebKit Network Cache: 1 records of cache version 18, response not read', self.logs)

    def test_a_null_response_and_a_wide_url(self):
        salt = self._write(f'{CACHE}/salt', self.salt)
        path = self._write(f'{CACHE}/Records/P/Resource/{NAME}',
                           record(self.salt, 'https://a.example/été✓', header=response_header('', null=True),
                                  wide=True))
        _headers, rows, _source = self._run([salt, path])
        self.assertEqual(rows[0][3:8], ('https://a.example/été✓', '', '', '', ''))
        self.assertEqual(self.logs, ['WebKit Network Cache: 1 record(s).'])

    def test_a_byte_identical_copy_under_system_volumes_data_is_read_once(self):
        data = record(self.salt, 'https://a.example/', header=response_header('https://a.example/'))
        salts = [self._write(f'{CACHE}/salt', self.salt), self._write(f'System/Volumes/Data/{CACHE}/salt', self.salt)]
        first = self._write(f'{CACHE}/Records/P/Resource/{NAME}', data)
        second = self._write(f'System/Volumes/Data/{CACHE}/Records/P/Resource/{NAME}', data)
        _headers, rows, source = self._run(salts + [second, first])
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, first)

    def test_paths_reach_records_and_salt_but_not_blob_links(self):
        patterns = macosWebKitCache.__artifacts_v2__['macosWebKitCache']['paths']
        def matched(path):
            return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        self.assertTrue(matched(f'/case/{CACHE}/Records/DEC366BD/Resource/{NAME}'))
        self.assertTrue(matched(f'/case/{CACHE}/salt'))
        self.assertFalse(matched(f'/case/{CACHE}/Records/DEC366BD/Resource/{NAME}-blob'))
        self.assertFalse(matched(f'/case/{CACHE}/Blobs/{NAME}'))


if __name__ == '__main__':
    unittest.main()
