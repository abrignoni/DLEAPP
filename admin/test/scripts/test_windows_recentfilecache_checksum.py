"""Pin the RecentFileCache.bcf checksum check in scripts/artifacts/windowsRecentFileCache.py against the two sample
files Eric Zimmerman's RecentFileCacheParser tests assert valid (admin/test/data/recentfilecache/README.md)."""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsRecentFileCache as rfc  # pylint: disable=wrong-import-position

DATA = REPO_ROOT / 'admin' / 'test' / 'data' / 'recentfilecache'


class ChecksumTest(unittest.TestCase):
    def test_the_reference_samples_match(self):
        for name, stored in (('RecentFileCache.bcf', 0xF4637B64), ('RecentFileCache_2.bcf', 0xE5918E10)):
            data = (DATA / name).read_bytes()
            self.assertEqual(struct.unpack_from('<I', data, 0x10)[0], stored, name)
            self.assertEqual(rfc.checksum_matches(data), 'Yes', name)

    def test_a_changed_byte_does_not_match(self):
        data = bytearray((DATA / 'RecentFileCache.bcf').read_bytes())
        data[-3] ^= 0x01
        self.assertEqual(rfc.checksum_matches(bytes(data)), 'No')

    def test_a_file_too_short_for_the_header_is_blank(self):
        self.assertEqual(rfc.checksum_matches(b'\xfe\xff\xee\xff' + bytes(8)), '')


if __name__ == '__main__':
    unittest.main()
