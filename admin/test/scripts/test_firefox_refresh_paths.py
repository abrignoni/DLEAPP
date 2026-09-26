"""Firefox artifacts read the profile copy Firefox's Refresh leaves on the Desktop.

Refresh copies the old profile folder, under its own name, into a Desktop folder named from
the resetBackupDirectory string ('Old %S Data' in the en-US source). The folder names below
are written out for the test; the German one is how that string reads in a German build.
"""
import ast
import fnmatch
import pathlib
import re
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox  # pylint: disable=wrong-import-position

MODULES = ('firefoxBrowser.py', 'firefoxSettings.py')
CONTAINERS = ('Users/tester/Desktop/Old Firefox Data', 'Users/tester/Desktop/Alte Firefox-Daten',
              'C:/Users/tester/Desktop/Old Firefox Data')


def _paths():
    found = {}
    for name in MODULES:
        tree = ast.parse((REPO_ROOT/'scripts'/'artifacts'/name).read_text(encoding='utf-8'))
        for node in tree.body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == '__artifacts_v2__':
                for key, info in ast.literal_eval(node.value).items():
                    found[key] = info['paths']
    return found


def _matches(patterns, path):
    return any(re.match(fnmatch.translate(p), path) for p in patterns)


class FirefoxRefreshPathsTest(unittest.TestCase):

    def test_every_artifact_matches_a_refresh_copy(self):
        paths = _paths()
        self.assertEqual(len(paths), 13)
        for key, patterns in paths.items():
            store = patterns[0].split('Profiles/*/', 1)[1].rstrip('*').replace('*', 'https+++example.test')
            for container in CONTAINERS:
                with self.subTest(artifact=key, container=container):
                    self.assertTrue(_matches(patterns, f'/case/{container}/ab12cd34.default-release/{store}'))
            with self.subTest(artifact=key, container='not Firefox'):
                self.assertFalse(_matches(patterns, f'/case/Users/tester/Desktop/Backups/x/{store}'))

    def test_profile_and_user_come_from_the_refresh_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'places.sqlite'
            db = sqlite3.connect(path)
            db.executescript('''CREATE TABLE moz_places(id INTEGER, url TEXT, title TEXT);
                CREATE TABLE moz_historyvisits(id INTEGER, place_id INTEGER, visit_date INTEGER,
                    visit_type INTEGER, from_visit INTEGER);
                INSERT INTO moz_places VALUES(1, 'https://refresh.test', 'Refresh');
                INSERT INTO moz_historyvisits VALUES(1, 1, 1704067200000000, 1, 0);''')
            db.commit()
            db.close()
            relative = 'Users/tester/Desktop/Old Firefox Data/ab12cd34.default-release/places.sqlite'

            class Context:
                @staticmethod
                def get_files_found():
                    return [path]

                @staticmethod
                def get_relative_path(_path):
                    return relative

            rows, _source = firefox.read_artifact(Context, 'places.sqlite', firefox.visits, 'Test')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][-2:], ('ab12cd34.default-release', 'tester'))
        self.assertNotIn(relative, rows[0])


if __name__ == '__main__':
    unittest.main()
