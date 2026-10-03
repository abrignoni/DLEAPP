"""Pin the UserChoice hash check of scripts/artifacts/windowsDefaultAppChoices.py.

The expected hashes were computed by a separate implementation, kept outside DLEAPP, and are written here as literals.
"""
import importlib.util
import os
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
_SPEC = importlib.util.spec_from_file_location(
    'windowsDefaultAppChoices', REPO_ROOT / 'scripts' / 'artifacts' / 'windowsDefaultAppChoices.py')
module = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(module)

SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
WRITTEN = datetime(2026, 10, 3, 14, 5, 59, 999000, tzinfo=timezone.utc)


class ChoiceHashTest(unittest.TestCase):
    def test_texts(self):
        self.assertEqual(module.choice_hash('abc'), 'S0uiSASHgHM=')
        self.assertEqual(module.choice_hash('abcd'), 'ovd/qDTm6P8=')
        self.assertEqual(module.choice_hash('A Mixed CASE text'), 'K6CubfdFsgM=')
        self.assertEqual(module.choice_hash('a mixed case text'), 'K6CubfdFsgM=')

    def test_a_text_under_eight_bytes_has_no_hash(self):
        self.assertEqual(module.choice_hash(''), '')

    def test_user_choice_hash(self):
        self.assertEqual(module.user_choice_hash('.pdf', SID, 'AcroExch.Document.DC', WRITTEN), 'lQ2CPHVQWY4=')
        self.assertEqual(module.user_choice_hash('http', SID, 'ChromeHTML', WRITTEN), 'YJ6StSpfFK4=')
        self.assertEqual(module.user_choice_hash('.txt', SID[:-1] + '2', 'txtfile', WRITTEN), 'iTSN9RrhiKY=')

    def test_only_the_minute_counts(self):
        start = WRITTEN.replace(second=0, microsecond=0)
        self.assertEqual(module.user_choice_hash('.pdf', SID, 'AcroExch.Document.DC', start), 'lQ2CPHVQWY4=')
        self.assertEqual(module.user_choice_hash('.pdf', SID, 'AcroExch.Document.DC', WRITTEN + timedelta(minutes=1)),
                         'IpJJ+4WV2Rk=')


class HashCheckTest(unittest.TestCase):
    def test_match_and_mismatch(self):
        self.assertEqual(module.hash_check('UserChoice', '.pdf', SID, 'AcroExch.Document.DC', WRITTEN, 'lQ2CPHVQWY4='),
                         'Matches')
        self.assertEqual(module.hash_check('userchoice', '.pdf', SID, 'Other.ProgId', WRITTEN, 'lQ2CPHVQWY4='),
                         'Does not match')

    def test_blank_when_not_checked(self):
        for args in (('UserChoiceLatest', '.pdf', SID, 'AcroExch.Document.DC', WRITTEN, 'lQ2CPHVQWY4='),
                     ('UserChoice', '.pdf', '', 'AcroExch.Document.DC', WRITTEN, 'lQ2CPHVQWY4='),
                     ('UserChoice', '.pdf', SID, '', WRITTEN, 'lQ2CPHVQWY4='),
                     ('UserChoice', '.pdf', SID, 'AcroExch.Document.DC', WRITTEN, ''),
                     ('UserChoice', '.pdf', SID, 'AcroExch.Document.DC', '', 'lQ2CPHVQWY4=')):
            self.assertEqual(module.hash_check(*args), '', args)


class VolumeTest(unittest.TestCase):
    def test_a_users_hive_and_the_software_hive_of_one_volume_share_a_volume(self):
        root = os.path.join('report', 'data', 'p3', 'x')
        ntuser = os.path.join(root, 'Users', 'Alex', 'NTUSER.DAT')
        software = os.path.join(root, 'Windows', 'System32', 'config', 'SOFTWARE')
        other = os.path.join('report', 'data', 'p4', 'x', 'Windows', 'System32', 'config', 'SOFTWARE')
        self.assertEqual(module._volume(ntuser, 3), module._volume(software, 4))  # pylint: disable=protected-access
        self.assertNotEqual(module._volume(ntuser, 3), module._volume(other, 4))  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
