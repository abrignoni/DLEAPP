"""Pin how scripts/chromium/web_storage.py splits storage keys, decodes the metadata records and
locates the Local Storage and Service Worker folders. The expected values are written out, never
read back from the code.
"""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.chromium import browser_profiles  # pylint: disable=wrong-import-position
from scripts.chromium import web_storage  # pylint: disable=wrong-import-position


class StorageKeyTest(unittest.TestCase):
    def test_unpartitioned(self):
        self.assertEqual(web_storage.split_storage_key('https://example.com'),
                         ('https://example.com', '', ''))

    def test_top_level_site(self):
        self.assertEqual(web_storage.split_storage_key('https://a.example/^0https://b.example'),
                         ('https://a.example', 'https://b.example', ''))

    def test_nonce_is_kept_as_stored(self):
        self.assertEqual(web_storage.split_storage_key('https://a.example/^112345^267890'),
                         ('https://a.example', '', '^112345^267890'))

    def test_ancestor_chain_bit_is_kept_as_stored(self):
        self.assertEqual(web_storage.split_storage_key('https://a.example/^0https://b.example^31'),
                         ('https://a.example', '', '^0https://b.example^31'))


class ProtoTest(unittest.TestCase):
    def test_write_metadata(self):
        # last_modified = 13377000000000000 (field 1, varint), size_bytes = 300 (field 2, varint)
        value = bytes([0x08]) + _varint(13377000000000000) + bytes([0x10]) + _varint(300)
        fields = web_storage.proto_fields(value)
        self.assertEqual(fields, {1: 13377000000000000, 2: 300})
        self.assertEqual(str(browser_profiles.webkit_time(web_storage.signed64(fields[1]))),
                         '2024-11-25 09:20:00+00:00')

    def test_strings(self):
        value = bytes([0x12, 3]) + b'abc' + bytes([0x38]) + _varint(5)
        self.assertEqual(web_storage.proto_fields(value), {2: b'abc', 7: 5})

    def test_truncated(self):
        with self.assertRaises(web_storage.ProtoError):
            web_storage.proto_fields(bytes([0x12, 5]) + b'ab')

    def test_negative_int64(self):
        self.assertEqual(web_storage.signed64((1 << 64) - 1), -1)


class LocateTest(unittest.TestCase):
    def test_profile_folder(self):
        located = browser_profiles.locate(
            'C/Users/a/AppData/Local/Google/Chrome/User Data/Profile 2/Local Storage/leveldb')
        self.assertEqual(located[:3], ('Google Chrome', 'Profile 2', 'a'))
        self.assertEqual(located[4], web_storage.LOCAL_STORAGE)

    def test_opera_root_profile(self):
        located = browser_profiles.locate(
            'C/Users/a/AppData/Roaming/Opera Software/Opera Stable/Service Worker/Database')
        self.assertEqual(located[:3], ('Opera', 'Opera Stable', 'a'))
        self.assertEqual(located[4], web_storage.SERVICE_WORKER)

    def test_electron_folder_is_not_a_profile(self):
        self.assertIsNone(browser_profiles.locate('C/Users/a/AppData/Roaming/discord/Local Storage/leveldb'))


def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


if __name__ == '__main__':
    unittest.main()
