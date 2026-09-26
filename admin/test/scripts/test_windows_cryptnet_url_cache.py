"""Pin the MetaData reader in scripts/artifacts/windowsCryptnetUrlCache.py.

The MetaData file below follows the layout AbdulRhman Alfaifi's CryptnetURLCacheParser
documents: 12 unknown bytes, the URL size at 0x0C, a FILETIME at 0x10, a FILETIME at
0x58, the E-Tag size at 0x64 and the file size at 0x70, then the URL and E-Tag in
UTF-16LE. Expected values are written out, never read back from the reader.
"""
import hashlib
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsCryptnetUrlCache as cache  # pylint: disable=wrong-import-position

URL = 'http://example.test/tool.exe'
ETAG = '"abc123"'
# FILETIME counts 100 ns from 1601-01-01 UTC, 11644473600 s before 1970-01-01:
# 132139579870000000 is Unix 1569484387, 2019-09-26 07:53:07 UTC.
DOWNLOADED, LAST_MODIFIED = 132139579870000000, 131713000000000000


def metadata(url=URL, etag=ETAG, size=4096):
    url_raw = (url + '\0').encode('utf-16-le')
    etag_raw = (etag + '\0').encode('utf-16-le') if etag else b''
    head = bytearray(116)
    struct.pack_into('<I', head, 0, 112)
    struct.pack_into('<I', head, 12, len(url_raw))
    struct.pack_into('<Q', head, 16, DOWNLOADED)
    struct.pack_into('<Q', head, 88, LAST_MODIFIED)
    struct.pack_into('<I', head, 100, len(etag_raw))
    struct.pack_into('<I', head, 112, size)
    return bytes(head) + url_raw + etag_raw


class ParseTest(unittest.TestCase):
    def test_fields(self):
        fields = cache.parse_metadata(metadata())
        self.assertEqual(fields, {'downloaded': DOWNLOADED, 'last_modified': LAST_MODIFIED,
                                  'file_size': 4096, 'url': URL, 'etag': '"abc123"'})

    def test_empty_etag(self):
        self.assertEqual(cache.parse_metadata(metadata(etag=''))['etag'], '')

    def test_short_or_overrunning_files_are_refused(self):
        with self.assertRaises(ValueError):
            cache.parse_metadata(bytes(100))
        with self.assertRaises(ValueError):
            cache.parse_metadata(metadata()[:-4])

    def test_filetime(self):
        self.assertEqual(cache.filetime_utc(DOWNLOADED),
                         datetime(2019, 9, 26, 7, 53, 7, tzinfo=timezone.utc))
        self.assertEqual(cache.filetime_utc(0), '')


class PathTest(unittest.TestCase):
    def test_cache_parts_and_profile(self):
        rel = 'p4/Windows/ServiceProfiles/LocalService/AppData/LocalLow/Microsoft/CryptnetUrlCache/MetaData/AB12'
        self.assertEqual(cache.cache_parts(rel),
                         ('/p4/windows/serviceprofiles/localservice/appdata/locallow/microsoft/'
                          'cryptneturlcache/', 'metadata', 'AB12'))
        self.assertEqual(cache.profile_folder(rel), 'p4/Windows/ServiceProfiles/LocalService')
        self.assertIsNone(cache.cache_parts(rel.rsplit('/', 1)[0]))
        self.assertIsNone(cache.cache_parts('Users/a/AppData/LocalLow/Microsoft/CryptnetUrlCache/x/y/z'))


class _Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_metadata_pairs_with_content_of_the_same_name(self):
        content = b'MZ\x90\x00' + bytes(4092)
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, 'Users', 'someone', 'AppData', 'LocalLow', 'Microsoft',
                                'CryptnetUrlCache')
            os.makedirs(os.path.join(base, 'MetaData'))
            os.makedirs(os.path.join(base, 'content'))
            meta_path = os.path.join(base, 'MetaData', 'AB12')
            content_path = os.path.join(base, 'content', 'ab12')
            with open(meta_path, 'wb') as handle:
                handle.write(metadata())
            with open(content_path, 'wb') as handle:
                handle.write(content)
            context = _Context(root, [meta_path, content_path, base])
            _, rows, sources = cache.windowsCryptnetUrlCache.__wrapped__(context)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[1:4], (URL, 4096, '"abc123"'))
        self.assertEqual(row[5:8], ('Users/someone', 'AB12', 4096))
        self.assertEqual(row[8], hashlib.sha256(content).hexdigest())
        self.assertEqual(row[9], '4D5A900000000000')
        self.assertEqual(sources.split('\n'), [meta_path, content_path])


if __name__ == '__main__':
    unittest.main()
