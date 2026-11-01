"""Pin how the code editor extension artifacts read extensions.json and .obsolete."""
import pathlib
import sys
import unittest
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import editorExtensions
# pylint: enable=wrong-import-position

# Entries shaped as Visual Studio Code 1.144.0 and VSCodium 1.143.17232 wrote them on
# ubuntu2604_arm64_editorext_known_20261101.
GALLERY = {
    'identifier': {'id': 'editorconfig.editorconfig', 'uuid': 'f60a60a6-95ba-42d4-b41c-3d24c1b89588'},
    'version': '0.18.2',
    'location': {'$mid': 1, 'path': '/home/u/.vscode/extensions/editorconfig.editorconfig-0.18.2', 'scheme': 'file'},
    'relativeLocation': 'editorconfig.editorconfig-0.18.2',
    'metadata': {'installedTimestamp': 1793561138292, 'pinned': True, 'source': 'gallery', 'updated': True,
                 'isPreReleaseVersion': False, 'publisherDisplayName': 'EditorConfig', 'targetPlatform': 'undefined'},
}
VSIX = {
    'identifier': {'id': 'mechatroner.rainbow-csv'},
    'version': '3.24.1',
    'location': {'$mid': 1, 'path': '/home/u/.vscode/extensions/mechatroner.rainbow-csv-3.24.1', 'scheme': 'file'},
    'relativeLocation': 'mechatroner.rainbow-csv-3.24.1',
    'metadata': {'installedTimestamp': 1793561142358, 'pinned': True, 'source': 'vsix'},
}


class ExtensionRowsTest(unittest.TestCase):
    def test_rows_keep_values_as_stored_and_blank_absent_keys(self):
        counts = Counter()
        rows = editorExtensions.extension_rows([GALLERY, VSIX], counts)
        self.assertEqual(rows, [
            (datetime(2026, 11, 1, 19, 25, 38, 292000, tzinfo=timezone.utc), 'editorconfig.editorconfig', '0.18.2',
             'gallery', 'true', 'true', 'false', 'EditorConfig', 'undefined', 'editorconfig.editorconfig-0.18.2'),
            (datetime(2026, 11, 1, 19, 25, 42, 358000, tzinfo=timezone.utc), 'mechatroner.rainbow-csv', '3.24.1',
             'vsix', 'true', '', '', '', '', 'mechatroner.rainbow-csv-3.24.1'),
        ])
        self.assertEqual(counts, Counter())

    def test_entries_the_editor_would_reject_are_counted_not_reported(self):
        counts = Counter()
        bad = [{'identifier': {'id': 'a.b'}, 'location': '', 'version': '1.0.0'},
               {'identifier': {'id': 'a.b'}, 'location': '/x', 'version': ''},
               {'identifier': 'a.b', 'location': '/x', 'version': '1.0.0'},
               'not an entry']
        self.assertEqual(editorExtensions.extension_rows(bad, counts), [])
        self.assertEqual(counts, {'entries without an identifier, location and version': 4})

    def test_a_file_that_is_not_a_list_gives_no_rows(self):
        counts = Counter()
        self.assertEqual(editorExtensions.extension_rows({'addons': []}, counts), [])
        self.assertEqual(counts, {'files whose top level is not a list': 1})

    def test_folder_falls_back_to_the_location_path_and_bad_times_are_blank(self):
        counts = Counter()
        entry = dict(VSIX, relativeLocation=None, metadata={'installedTimestamp': 'soon'})
        row = editorExtensions.extension_rows([entry], counts)[0]
        self.assertEqual((row[0], row[-1]), ('', 'mechatroner.rainbow-csv-3.24.1'))
        self.assertEqual(counts, {'install times that are not numbers, left blank': 1})

    def test_no_metadata_still_reports_the_identifier_and_version(self):
        entry = {'identifier': {'id': 'a.b'}, 'location': '/home/u/.vscode/extensions/a.b-1.0.0', 'version': '1.0.0'}
        self.assertEqual(editorExtensions.extension_rows([entry], Counter()),
                         [('', 'a.b', '1.0.0', '', '', '', '', '', '', 'a.b-1.0.0')])


if __name__ == '__main__':
    unittest.main()
