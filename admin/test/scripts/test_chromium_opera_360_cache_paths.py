"""Where Chromium Cache Records finds the Windows caches of Opera, Opera GX and 360 Safe Browser."""

import fnmatch
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts.chromiumCacheRecords import __artifacts_v2__  # pylint: disable=wrong-import-position
from scripts.chromium.browser_profiles import locate  # pylint: disable=wrong-import-position

PATTERNS = __artifacts_v2__['chromiumCacheRecords']['paths']
HOME = 'Users/examiner/AppData'
CACHES = {
    'Opera': f'{HOME}/Local/Opera Software/Opera Stable/Default/Cache/Cache_Data/index',
    'Opera GX': f'{HOME}/Local/Opera Software/Opera GX Stable/Default/Cache/Cache_Data/index',
    '360 Safe Browser': f'{HOME}/Roaming/360se6/User Data/Default/Cache/Cache_Data/index',
}


def declared(path):
    return any(fnmatch.fnmatchcase('extraction/' + path, pattern) for pattern in PATTERNS)


class OperaAnd360CachePathsTest(unittest.TestCase):

    def test_each_cache_is_declared_and_placed_in_its_browser(self):
        for browser, path in CACHES.items():
            with self.subTest(browser):
                self.assertTrue(declared(path))
                found, profile, user, _container, name = locate(path)
                self.assertEqual((found, profile, user, name),
                                 (browser, 'Default', 'examiner', 'Cache/Cache_Data/index'))

    def test_local_and_roaming_folders_of_one_profile_stay_apart(self):
        local = locate(f'{HOME}/Local/Opera Software/Opera Stable/Default/Cache/Cache_Data/index')
        roaming = locate(f'{HOME}/Roaming/Opera Software/Opera Stable/Default/History')
        self.assertEqual((local[0], local[1]), (roaming[0], roaming[1]))
        self.assertNotEqual(local[3], roaming[3])

    def test_other_folders_are_not_declared(self):
        for path in (f'{HOME}/Local/Opera Software/Opera Stable/Default/System Cache/Cache_Data/index',
                     f'{HOME}/Local/Other Software/Opera Stable/Default/Cache/Cache_Data/index',
                     f'{HOME}/Roaming/other360/User Data/Default/Cache/Cache_Data/index'):
            with self.subTest(path):
                self.assertFalse(declared(path))


if __name__ == '__main__':
    unittest.main()
