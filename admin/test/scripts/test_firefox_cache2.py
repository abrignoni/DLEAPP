"""Pin scripts/firefox_cache2.py and the Firefox Cache Entries artifact.

FIREFOX_ENTRY is an entry file Firefox 159.0.1 wrote on windows11_arm_firefox_cache2_known_20261108 for a local test
URL, so the metadata hash is checked against Firefox's own bytes, not against this reader. The other entries are built
here following CacheFileMetadata.cpp, with made-up values.
"""
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox_cache2 as c2  # pylint: disable=wrong-import-position
from scripts.artifacts import firefoxCache  # pylint: disable=wrong-import-position

FIREFOX_ENTRY = bytes.fromhex(
    "7b226b64223a202263616368652d6a736f6e227dde009f851cd600000004000000016af006146af006144a1f9d196af0"
    "142400000049000000004f5e706172746974696f6e4b65793d253238687474702532433132372e302e302e312532392c"
    "3a687474703a2f2f3132372e302e302e313a383736362f6b642d646174612e6a736f6e007374726f6e676c792d667261"
    "6d6564003100726571756573742d6d6574686f640047455400726573706f6e73652d6865616400485454502f312e3020"
    "323030204f4b0d0a5365727665723a2042617365485454502f302e3620507974686f6e2f332e31312e390d0a44617465"
    "3a2053756e2c203038204e6f7620323032362030353a31383a313220474d540d0a436f6e74656e742d547970653a2061"
    "70706c69636174696f6e2f6a736f6e0d0a436f6e74656e742d4c656e6774683a2032300d0a43616368652d436f6e7472"
    "6f6c3a206d61782d6167653d333630300d0a4c6173742d4d6f6469666965643a205361742c203037204e6f7620323032"
    "362031323a30303a303020474d540d0a006f726967696e616c2d726573706f6e73652d68656164657273005365727665"
    "723a2042617365485454502f302e3620507974686f6e2f332e31312e390d0a446174653a2053756e2c203038204e6f76"
    "20323032362030353a31383a313220474d540d0a436f6e74656e742d547970653a206170706c69636174696f6e2f6a73"
    "6f6e0d0a436f6e74656e742d4c656e6774683a2032300d0a43616368652d436f6e74726f6c3a206d61782d6167653d33"
    "3630300d0a4c6173742d4d6f6469666965643a205361742c203037204e6f7620323032362031323a30303a303020474d"
    "540d0a00637469640031006e65742d726573706f6e73652d74696d652d6f6e73746172740036006e65742d726573706f"
    "6e73652d74696d652d6f6e73746f700036000000000400000014"
)


def build(body, key, elements, version=4, fetched=1700000000, modified=1700000001, expiration=1700003600,
          fetch_count=2, encrypted=False, corrupt=False):
    """An entry file laid out as CacheFileMetadata writes it."""
    chunks = len(body) // c2.CHUNK_SIZE + (1 if len(body) % c2.CHUNK_SIZE else 0)
    header = struct.pack('>8I', version, fetch_count, fetched, modified, 0, expiration, len(key), 0)
    rest = b'\0\0' * chunks + header + key + b'\0' + b''.join(k + b'\0' + v + b'\0' for k, v in elements)
    block = struct.pack('>I', c2.cache_hash(rest)) + rest
    if corrupt:
        block = block[:-1] + bytes([block[-1] ^ 1])
    if version >= 4:
        trailer = struct.pack('>II', version, len(body) | (0x80000000 if encrypted else 0))
    else:
        trailer = struct.pack('>I', len(body))
    return body + block + trailer


PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                    '1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')


class ReaderTest(unittest.TestCase):
    def test_firefox_written_entry(self):
        entry = c2.read_entry(FIREFOX_ENTRY)
        self.assertEqual((entry.version, entry.fetch_count, entry.data_size), (4, 1, 20))
        self.assertEqual(c2.split_key(entry.key),
                         ('O^partitionKey=%28http%2C127.0.0.1%29,', 'http://127.0.0.1:8766/kd-data.json'))
        self.assertEqual(entry.expiration - entry.last_fetched, 3600)
        self.assertEqual(c2.response_head(entry.elements)[0], 'HTTP/1.0 200 OK')
        self.assertEqual(FIREFOX_ENTRY[:entry.data_size], b'{"kd": "cache-json"}')

    def test_a_changed_byte_fails_the_hash(self):
        damaged = bytearray(FIREFOX_ENTRY)
        damaged[40] ^= 1
        with self.assertRaisesRegex(c2.Cache2Error, 'hash'):
            c2.read_entry(bytes(damaged))

    def test_version_3_single_word_trailer(self):
        entry = c2.read_entry(build(b'abc', b'a,:http://x.invalid/', [(b'request-method', b'GET')], version=3))
        self.assertEqual((entry.version, entry.data_size, entry.elements['request-method']), (3, 3, b'GET'))

    def test_encrypted_and_short_entries_are_refused(self):
        with self.assertRaises(c2.EncryptedEntry):
            c2.read_entry(build(b'abc', b'a,:http://x.invalid/', [], encrypted=True))
        with self.assertRaises(c2.Cache2Error):
            c2.read_entry(b'')

    def test_split_key(self):
        self.assertEqual(c2.split_key('a,~1700000000,:http://x.invalid/p?q=1'),
                         ('a,~1700000000,', 'http://x.invalid/p?q=1'))
        self.assertEqual(c2.split_key('O^a=1,,2,:http://x.invalid/'), ('O^a=1,,2,', 'http://x.invalid/'))
        self.assertEqual(c2.split_key(':http://x.invalid/'), ('', 'http://x.invalid/'))

    def test_alt_data(self):
        self.assertEqual(c2.alt_data_offset({'alt-data': b'1;3,script'}), (3, 'script'))
        self.assertEqual(c2.alt_data_offset({'alt-data': b'2;3,script'}), (None, ''))
        self.assertEqual(c2.alt_data_offset({}), (None, ''))


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ArtifactTest(unittest.TestCase):
    def test_rows(self):
        head = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Encoding: gzip\r\n'
        image_head = b'HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n'
        with tempfile.TemporaryDirectory() as tmp:
            entries = pathlib.Path(tmp, 'Users', 'lab', 'AppData', 'Local', 'Mozilla', 'Firefox', 'Profiles',
                                   'abcd.default-release', 'cache2', 'entries')
            entries.mkdir(parents=True)
            (entries / 'A').write_bytes(build(b'xyz' + b'JSBYTES', b'a,:http://x.invalid/t.txt',
                                              [(b'request-method', b'GET'), (b'response-head', head),
                                               (b'alt-data', b'1;3,script')], expiration=0xFFFFFFFF))
            (entries / 'B').write_bytes(build(PNG, b'O^p=1,:http://x.invalid/i.png',
                                              [(b'request-method', b'GET'), (b'response-head', image_head),
                                               (b'peer-ip-address', b'192.0.2.1')]))
            (entries / 'E').write_bytes(build(b'<!doctype html><svg xmlns="http://www.w3.org/2000/svg"></svg>',
                                              b'a,:http://x.invalid/s.svg',
                                              [(b'response-head', b'HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\n')]))
            (entries / 'C').write_bytes(build(b'abc', b'a,:http://x.invalid/', [], encrypted=True))
            (entries / 'D').write_bytes(b'')
            files = [str(p) for p in entries.iterdir()] + [str(entries.parent / 'index')]
            with mock.patch.object(firefoxCache, 'check_in_embedded_media', return_value='MEDIA') as media, \
                    mock.patch.object(firefoxCache, 'logfunc') as log:
                headers, rows, source = firefoxCache.firefoxCache.__wrapped__(FakeContext(tmp, files))
            self.assertEqual(len(headers), len(rows[0]))
            t = lambda v: datetime.fromtimestamp(v, timezone.utc)  # pylint: disable=unnecessary-lambda-assignment
            self.assertEqual(rows, [
                (t(1700000000), t(1700000001), '', 'http://x.invalid/t.txt', 'x.invalid', 'GET', '200', 'text/plain',
                 'gzip', 3, '', 2, 'a,', 'script', '', 'entries', 'abcd.default-release', 'lab'),
                (t(1700000000), t(1700000001), t(1700003600), 'http://x.invalid/i.png', 'x.invalid', 'GET', '200',
                 'image/jpeg', '', len(PNG), 'MEDIA', 2, 'O^p=1,', '', '192.0.2.1', 'entries', 'abcd.default-release',
                 'lab'),
                (t(1700000000), t(1700000001), t(1700003600), 'http://x.invalid/s.svg', 'x.invalid', '', '200',
                 'image/svg+xml', '', 61, 'MEDIA', 2, 'a,', '', '', 'entries', 'abcd.default-release', 'lab')])
            # The bytes decide the media type: a PNG sent as image/jpeg is checked in as a PNG; bytes the
            # sniffer reads as something other than media (an SVG read as HTML) keep the stored type.
            self.assertEqual([call.kwargs['force_type'] for call in media.call_args_list], ['image/png', 'image/svg+xml'])
            self.assertEqual(source, str(entries))
            logged = ' '.join(call.args[0] for call in log.call_args_list)
            self.assertIn('1 entry file(s) not read: encrypted at rest', logged)
            self.assertIn('1 entry file(s) not read: shorter than a trailer', logged)


if __name__ == '__main__':
    unittest.main()
