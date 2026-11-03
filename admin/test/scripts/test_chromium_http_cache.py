"""Pin scripts/chromium/http_cache.py: cache key split and HttpResponseInfo pickle read.

Keys follow the shapes in net/http/http_cache.cc (Chrome 65 and current). Pickles are
built field by field in the order HttpResponseInfo::InitFromPickle reads them; the
flags value of the current-release case is the one measured on Chrome 157 known data.
"""
import pathlib
import struct
import sys
import unittest
import zlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.chromium import http_cache as hc  # pylint: disable=wrong-import-position

HEADERS = b'HTTP/1.1 200\x00content-type: image/png\x00content-encoding: deflate\x00\x00'


def _pickle(flags, times, extra=None, headers=HEADERS):
    body = struct.pack('<i', flags)
    if extra is not None:
        body += struct.pack('<i', extra)
    body += struct.pack(f'<{len(times)}q', *times)
    body += struct.pack('<i', len(headers)) + headers + b'\x00' * (-len(headers) % 4)
    return struct.pack('<I', len(body)) + body


class SplitKeyTest(unittest.TestCase):
    def test_plain_and_upload_keys(self):
        self.assertEqual(hc.split_key('https://a.example/x'), ('', '', 'https://a.example/x'))
        self.assertEqual(hc.split_key('5/https://a.example/x'), ('5/', '', 'https://a.example/x'))

    def test_double_key_takes_url_after_last_space(self):
        key = '1/0/_dk_https://s.example https://s.example https://u.example/p?r=http://z'
        self.assertEqual(hc.split_key(key), ('1/0/', 'https://s.example https://s.example',
                                             'https://u.example/p?r=http://z'))

    def test_marker_and_unsourced_prefix_kept(self):
        self.assertEqual(hc.split_key('1/0/_dk_s_https://s https://f https://u')[1], 's_https://s https://f')
        self.assertEqual(hc.split_key('Range_1/0/_dk_https://s https://s https://u'),
                         ('Range_1/0/', 'https://s https://s', 'https://u'))

    def test_non_resource_key_kept_whole(self):
        self.assertEqual(hc.split_key('quicserverinfo:https://h.example:443'),
                         ('quicserverinfo:https://h.example:443', '', ''))


class ResponseInfoTest(unittest.TestCase):
    def test_version_3_without_extra_flags(self):
        parsed = hc.parse_response_info(_pickle(0x3, (100, 200)))
        self.assertEqual(parsed[:3], (100, 200, 'HTTP/1.1 200'))
        self.assertEqual(parsed[3]['content-type'], 'image/png')
        self.assertEqual(parsed[4], 0)

    def test_extra_flags_and_original_response_time(self):
        parsed = hc.parse_response_info(_pickle(0x8a476d03 - (1 << 32), (100, 200, 300), extra=0x6))
        self.assertEqual(parsed[:3], (100, 200, 'HTTP/1.1 200'))
        self.assertEqual(parsed[4], 0x6)

    def test_other_versions_and_short_pickles_refused(self):
        self.assertIsNone(hc.parse_response_info(_pickle(0x1, (100, 200))))
        whole = _pickle(0x3, (100, 200))
        self.assertIsNone(hc.parse_response_info(whole[:-4]))
        self.assertIsNone(hc.parse_response_info(b''))

    def test_stored_body(self):
        data = zlib.compress(b'picture')
        self.assertEqual(hc.stored_body(data, 0, 'deflate'), b'picture')
        self.assertEqual(hc.stored_body(b'raw', 0, ''), b'raw')

    @unittest.skipUnless(sys.version_info >= (3, 14), 'compression.zstd needs Python 3.14')
    def test_stored_body_zstd_on_disk(self):
        from compression import zstd  # pylint: disable=import-outside-toplevel,import-error
        data = zstd.compress(zlib.compress(b'picture'))
        flag = hc.RESPONSE_EXTRA_INFO_HAS_ZSTD_UNCOMPRESSED_BODY_SIZE
        self.assertEqual(hc.stored_body(data, flag, 'deflate'), b'picture')
        self.assertEqual(hc.stored_body(data, 0, ''), data)


if __name__ == '__main__':
    unittest.main()
