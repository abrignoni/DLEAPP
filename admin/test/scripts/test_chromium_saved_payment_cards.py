"""Pin how Chromium Saved Payment Cards (scripts/artifacts/chromiumAutofill.py) reads User Confirmed on the
current schema and on one from before is_user_confirmed replaced origin."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import chromiumAutofill as autofill
# pylint: enable=wrong-import-position


class UserConfirmedTest(unittest.TestCase):
    def test_current_schema(self):
        present = {'is_user_confirmed'}
        self.assertEqual(autofill._user_confirmed(1, None, present), 'Yes')  # pylint: disable=protected-access
        self.assertEqual(autofill._user_confirmed(0, None, present), 'No')  # pylint: disable=protected-access
        self.assertEqual(autofill._user_confirmed(None, None, present), '')  # pylint: disable=protected-access

    def test_older_schema_reads_origin_as_the_migration_does(self):
        present = {'origin'}
        self.assertEqual(autofill._user_confirmed(None, 'Chrome settings', present), 'Yes')  # pylint: disable=protected-access
        self.assertEqual(autofill._user_confirmed(None, 'https://example.invalid/', present), 'No')  # pylint: disable=protected-access
        self.assertEqual(autofill._user_confirmed(None, None, set()), '')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
