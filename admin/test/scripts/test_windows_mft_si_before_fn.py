"""Pin the folder classifier of MFT SI Created Earlier Than FN Created (scripts/artifacts/windowsMft.py).
The paths are made up in the shapes the MFT artifact reports."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts.windowsMft import folder_class
# pylint: enable=wrong-import-position


class FolderClassTest(unittest.TestCase):
    def test_each_folder(self):
        cases = {
            '/Windows/WinSxS/amd64_x/a.dll': 'Windows\\WinSxS',
            '/Windows/winsxs/b.dll': 'Windows\\WinSxS',
            '/Windows/System32/c.dll': 'Windows (other)',
            '/Windows': 'Windows (other)',
            '/Program Files/App/d.exe': 'Program Files',
            '/Program Files (x86)/App/e.exe': 'Program Files',
            '/ProgramData/App/f.dat': 'ProgramData',
            '/Users/pat/Desktop/g.txt': 'Users',
            '/Documents and Settings/pat/h.txt': 'Users',
            '/kd/i.txt': 'Other',
            '/': 'Other',
            '': '',
        }
        for path, expected in cases.items():
            self.assertEqual(folder_class(path), expected, path)


if __name__ == '__main__':
    unittest.main()
