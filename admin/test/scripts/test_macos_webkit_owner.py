"""Pin the owner the macOS WebKit statistics artifacts read from a store's path. Paths are invented."""
# pylint: disable=protected-access
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosWebkitResourceLoadStatistics as itp  # pylint: disable=wrong-import-position

_TAIL = 'WebsiteData/ResourceLoadStatistics/observations.db'


class OwnerTest(unittest.TestCase):
    def test_sandboxed_container(self):
        self.assertEqual(itp._owner(f'Users/alice/Library/Containers/com.example.app/Data/Library/WebKit/{_TAIL}'),
                         ('alice', 'com.example.app'))

    def test_app_webkit_folder(self):
        self.assertEqual(itp._owner(f'Users/alice/Library/WebKit/com.example.player/{_TAIL}'),
                         ('alice', 'com.example.player'))

    def test_default_store_has_no_owner(self):
        self.assertEqual(itp._owner(f'Users/alice/Library/WebKit/{_TAIL}'), ('alice', ''))

    def test_data_volume_view(self):
        self.assertEqual(itp._owner(f'System/Volumes/Data/Users/alice/Library/WebKit/com.example.player/{_TAIL}'),
                         ('alice', 'com.example.player'))


if __name__ == '__main__':
    unittest.main()
