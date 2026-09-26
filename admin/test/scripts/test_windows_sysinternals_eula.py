"""Pin profile naming and value rendering in windowsSysinternalsEula.py."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsSysinternalsEula as eula  # pylint: disable=wrong-import-position


class ProfileTest(unittest.TestCase):
    def test_user_service_and_default_hives(self):
        self.assertEqual(eula.profile_of('lba0/Users/IEUser/NTUSER.DAT'), 'IEUser')
        self.assertEqual(eula.profile_of('p3/Windows/ServiceProfiles/LocalService/NTUSER.DAT'),
                         'LocalService')
        self.assertEqual(eula.profile_of('p3\\Windows\\System32\\config\\DEFAULT'), 'DEFAULT')

    def test_hive_at_the_root(self):
        self.assertEqual(eula.profile_of('NTUSER.DAT'), '')


class StoredValueTest(unittest.TestCase):
    def test_numbers_and_strings_are_unchanged(self):
        self.assertEqual(eula.stored_value(1), 1)
        self.assertEqual(eula.stored_value(0), 0)
        self.assertEqual(eula.stored_value('1'), '1')

    def test_binary_is_hex_and_multi_string_is_joined(self):
        self.assertEqual(eula.stored_value(b'\x01\x00\x00\x00'), '01000000')
        self.assertEqual(eula.stored_value(['a', 'b']), 'a; b')


if __name__ == '__main__':
    unittest.main()
