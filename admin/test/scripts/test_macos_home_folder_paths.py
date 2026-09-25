"""macOS per-user globs must also match an acquisition rooted at one user's home folder.

A logical acquisition of a single user folder has no Users/<name> segment above Library/,
so a pattern written as */Users/*/Library/... can never match it. The macOS artifacts
anchor on */Library/... instead, and this test keeps it that way.
"""

import ast
import fnmatch
import os
import re
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ARTIFACTS = os.path.join(REPO, 'scripts', 'artifacts')

# Home-folder files read by the macOS artifacts, as a full-disk extraction and as an
# acquisition of the home folder alone would name them.
HOME_FILES = {
    'macosAppleIdAccounts': 'Library/Preferences/MobileMeAccounts.plist',
    'macosInternetAccounts': 'Library/Accounts/Accounts4.sqlite',
    'macosFinderRecents': 'Library/Preferences/com.apple.finder.plist',
    'macosDockItems': 'Library/Preferences/com.apple.dock.plist',
    'macosIpodDevices': 'Library/Preferences/com.apple.iPod.plist',
}


def _artifact_paths():
    found = {}
    for name in sorted(os.listdir(ARTIFACTS)):
        if not name.endswith('.py'):
            continue
        with open(os.path.join(ARTIFACTS, name), encoding='utf-8') as handle:
            tree = ast.parse(handle.read())
        for node in tree.body:
            if not (isinstance(node, ast.Assign)
                    and any(getattr(t, 'id', None) == '__artifacts_v2__' for t in node.targets)):
                continue
            try:
                block = ast.literal_eval(node.value)
            except ValueError:
                continue
            for key, info in block.items():
                paths = info.get('paths') or ()
                if isinstance(paths, str):
                    paths = (paths,)
                found[key] = tuple(paths)
    return found


def _matches(patterns, path):
    return any(re.match(fnmatch.translate(p), path) for p in patterns)


class MacosHomeFolderPaths(unittest.TestCase):

    def test_no_glob_requires_a_users_segment_before_library(self):
        offenders = [(key, pattern) for key, patterns in _artifact_paths().items()
                     for pattern in patterns if '/Users/*/Library/' in pattern]
        self.assertEqual(offenders, [])

    def test_home_files_match_both_layouts(self):
        paths = _artifact_paths()
        for key, relative in HOME_FILES.items():
            with self.subTest(artifact=key):
                self.assertIn(key, paths)
                self.assertTrue(_matches(paths[key], f'/case/extraction/Users/someone/{relative}'))
                self.assertTrue(_matches(paths[key], f'/case/mount/{relative}'))


if __name__ == '__main__':
    unittest.main()
