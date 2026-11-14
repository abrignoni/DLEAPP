"""Pin how the Chromium artifacts find Opera GX and 360 Safe Browser on Windows.

Opera GX keeps its user data folder in AppData/Roaming/Opera Software/Opera GX Stable and 360 Safe
Browser in AppData/Roaming/360se6/User Data, as on windows11_arm_operagx_360se_known_20261107. Every
artifact pattern for an Opera Stable store must have its Opera GX sibling, and its 360 sibling except
for History and Bookmarks, which 360 writes as 360History and 360Bookmarks, not SQLite or JSON. The expected values are
written out, never read back from the code.
"""
import ast
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.chromium import browser_profiles  # pylint: disable=wrong-import-position

GX = 'Users/lab/AppData/Roaming/Opera Software/Opera GX Stable'
SE = 'Users/lab/AppData/Roaming/360se6/User Data'
OPERA = 'Opera Software/Opera Stable/'


def artifact_paths():
    """Every path pattern of every artifact module that names an Opera Stable store."""
    out = []
    for path in sorted((REPO_ROOT / 'scripts' / 'artifacts').glob('*.py')):
        text = path.read_text(encoding='utf-8')
        if OPERA not in text:
            continue
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == '__artifacts_v2__':
                for key, fields in ast.literal_eval(node.value).items():
                    paths = fields['paths']
                    out.append((path.name, key, (paths,) if isinstance(paths, str) else tuple(paths or ())))
    return out


class LocateTest(unittest.TestCase):
    def test_opera_gx_profile(self):
        self.assertEqual(browser_profiles.locate(f'{GX}/Default/History'),
                         ('Opera GX', 'Default', 'lab', f'{GX}/Default', 'History'))

    def test_360_profile(self):
        self.assertEqual(browser_profiles.locate(f'{SE}/Default/Network/Cookies'),
                         ('360 Safe Browser', 'Default', 'lab', f'{SE}/Default', 'Network/Cookies'))

    def test_opera_stable_is_unchanged(self):
        self.assertEqual(browser_profiles.locate('Users/lab/AppData/Roaming/Opera Software/Opera Stable/History')[:2],
                         ('Opera', 'Opera Stable'))


class PathsTest(unittest.TestCase):
    def test_every_opera_pattern_has_its_siblings(self):
        checked = 0
        for module, key, paths in artifact_paths():
            for pattern in paths:
                if OPERA not in pattern:
                    continue
                checked += 1
                self.assertIn(pattern.replace(OPERA, 'Opera Software/Opera GX Stable/'), paths, (module, key))
                sibling = pattern.replace(OPERA, '360se6/User Data/')
                store = pattern.split(OPERA, 1)[1].removeprefix('*/')
                if store in ('History*', 'Bookmarks*', 'AccountBookmarks*'):
                    self.assertNotIn(sibling, paths, (module, key))
                else:
                    self.assertIn(sibling, paths, (module, key))
        self.assertEqual(checked, 98)


if __name__ == '__main__':
    unittest.main()
