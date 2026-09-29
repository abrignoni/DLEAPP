"""Pin how the Chromium artifacts find Chromium installed as a snap or as a Flatpak.

The snap keeps its user data folder in ~/snap/chromium/common/chromium and Flathub's Chromium in
~/.var/app/org.chromium.Chromium/config/chromium, as on ubuntu2604_arm64_chromium. Both must be
located as Chromium with the home folder's name as the user, and every artifact that reads a
~/.config/chromium store must read the same store under both folders. The expected values are
written out, never read back from the code.
"""
import ast
import fnmatch
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.chromium import browser_profiles  # pylint: disable=wrong-import-position

SNAP = 'home/parallels/snap/chromium/common/chromium'
FLATPAK = 'home/parallels/.var/app/org.chromium.Chromium/config/chromium'
PREFIXES = ('*/snap/chromium/common/chromium/', '*/.var/app/org.chromium.Chromium/config/chromium/')


def artifact_paths():
    """{artifact key: paths} for every chromium* artifact module."""
    out = {}
    for path in sorted((REPO_ROOT / 'scripts' / 'artifacts').glob('chromium*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        block = next(ast.literal_eval(n.value) for n in tree.body
                     if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == '__artifacts_v2__')
        out.update({key: fields['paths'] for key, fields in block.items()})
    return out


class LocateTest(unittest.TestCase):
    def test_snap_profile(self):
        self.assertEqual(browser_profiles.locate(f'{SNAP}/Default/History'),
                         ('Chromium', 'Default', 'parallels', f'{SNAP}/Default', 'History'))

    def test_flatpak_profile(self):
        self.assertEqual(browser_profiles.locate(f'{FLATPAK}/Profile 1/Network/Cookies'),
                         ('Chromium', 'Profile 1', 'parallels', f'{FLATPAK}/Profile 1', 'Network/Cookies'))
        self.assertEqual(browser_profiles.locate(f'{FLATPAK}/Default/Sessions/Session_1')[4], 'Sessions/Session_1')

    def test_other_flatpak_apps_and_snap_folders_are_not_chromium(self):
        self.assertIsNone(browser_profiles.locate('home/u/.var/app/com.google.Chrome/config/chrome/Default/History'))
        self.assertIsNone(browser_profiles.locate('home/u/snap/chromium/3535/Default/History'))

    def test_a_home_config_profile_is_unchanged(self):
        self.assertEqual(browser_profiles.locate('home/u/.config/chromium/Default/History'),
                         ('Chromium', 'Default', 'u', 'home/u/.config/chromium/Default', 'History'))


class PathsTest(unittest.TestCase):
    def test_every_config_chromium_pattern_has_both_siblings(self):
        paths = artifact_paths()
        self.assertEqual(len(paths), 15)
        counted = 0
        for key, patterns in paths.items():
            for pattern in patterns:
                if pattern.startswith('*/.config/chromium/'):
                    rest = pattern[len('*/.config/chromium/'):]
                    for prefix in PREFIXES:
                        self.assertIn(prefix + rest, patterns, key)
                    counted += 1
        self.assertEqual(counted, 23)

    def test_the_known_stores_match(self):
        paths = artifact_paths()
        for base in (SNAP, FLATPAK):
            for key, name in (('chromiumWebVisits', 'Default/History'), ('chromiumTopSites', 'Default/Top Sites'),
                              ('chromiumSessionTabs', 'Default/Sessions/Session_13435174440828972'),
                              ('chromiumCookies', 'Default/Cookies'), ('chromiumExtensions', 'Default/Preferences')):
                staged = f'/tmp/report/data/{base}/{name}'
                self.assertTrue(any(fnmatch.fnmatchcase(staged, p) for p in paths[key]), (key, base))

    def test_profile_stores_reads_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            files = []
            for base in (SNAP, FLATPAK):
                path = root / base / 'Default' / 'History'
                path.parent.mkdir(parents=True)
                path.write_bytes(base.encode())
                files.append(str(path))
            context = SimpleNamespace(get_files_found=lambda: list(files),
                                      get_relative_path=lambda p: pathlib.Path(p).relative_to(root).as_posix())
            with mock.patch.object(macos_plists, 'logfunc'):
                stores = browser_profiles.profile_stores(context, {'History'}, 'Test')
        self.assertEqual([(s.browser, s.profile, s.user, s.container) for s in stores],
                         [('Chromium', 'Default', 'parallels', f'{FLATPAK}/Default'),
                          ('Chromium', 'Default', 'parallels', f'{SNAP}/Default')])


if __name__ == '__main__':
    unittest.main()
