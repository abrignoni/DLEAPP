"""Pin which registry entries make_test_data.py may record a baseline for.

A baseline is committed as admin/test/results/<corpus>.json and carries the
corpus key, row counts, column names and digests. module_output.baseline_refusal
refuses an entry whose allow_public_metadata is false or null (terms not
established), and allows one where it is true or not recorded. The registry is
synthetic.
"""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from admin.scripts import module_output  # noqa: E402  pylint: disable=wrong-import-position

REGISTRY = {'samples': {
    'closed_key': {'private': True, 'allow_fixtures': False, 'allow_public_metadata': False,
                   'privacy_basis': 'synthetic: provider designated private'},
    'unsettled_key': {'private': None, 'allow_fixtures': False, 'allow_public_metadata': None,
                      'privacy_basis': 'synthetic: terms not established'},
    'citable_key': {'private': True, 'allow_fixtures': False, 'allow_public_metadata': True,
                    'privacy_basis': 'synthetic: key citable, content private'},
    'undesignated_key': {'match': {'zip': 'x.zip'}},
}}


class TestBaselineRefusal(unittest.TestCase):

    def test_false_and_null_are_refused(self):
        for name in ('closed_key', 'unsettled_key'):
            with self.subTest(name=name):
                refusal = module_output.baseline_refusal(REGISTRY, name)
                self.assertIn(f"'{name}'", refusal or '')
                self.assertIn(f'admin/test/results/{name}.json', refusal)

    def test_true_and_absent_are_allowed(self):
        self.assertIsNone(module_output.baseline_refusal(REGISTRY, 'citable_key'))
        self.assertIsNone(module_output.baseline_refusal(REGISTRY, 'undesignated_key'))

    def test_an_unregistered_key_is_left_to_corpus_zip(self):
        self.assertIsNone(module_output.baseline_refusal(REGISTRY, 'missing_key'))


if __name__ == '__main__':
    unittest.main()
