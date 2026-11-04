"""Pin the location classifier of Desktop, Taskbar and Startup Shell Links (scripts/artifacts/windowsLnk.py).
The paths are made up in the shapes found on the corpus images."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts.windowsLnk import link_location
# pylint: enable=wrong-import-position

PINS = 'AppData/Roaming/Microsoft/Internet Explorer/Quick Launch/User Pinned/TaskBar'


class LinkLocationTest(unittest.TestCase):
    def test_each_place(self):
        cases = {
            'C/Users/pat/Desktop/a.lnk': ('Desktop', 'pat'),
            'C/Users/pat/Desktop/sub/b.lnk': ('Desktop', 'pat'),
            'C/Users/Public/Desktop/c.lnk': ('Public desktop', ''),
            'C/Documents and Settings/pat/Desktop/d.lnk': ('Desktop', 'pat'),
            'C/Documents and Settings/All Users/Desktop/e.lnk': ('Public desktop', ''),
            f'C/Users/pat/{PINS}/f.lnk': ('Taskbar pinned', 'pat'),
            'C/Users/pat/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/g.lnk': ('Startup (User)', 'pat'),
            'C/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp/h.lnk': ('Startup (All users)', ''),
            'C/Documents and Settings/All Users/Start Menu/Programs/Startup/i.lnk': ('Startup (All users)', ''),
        }
        for path, expected in cases.items():
            self.assertEqual(link_location(path), expected, path)

    def test_other_folders_are_not_listed(self):
        for path in ('C/Users/pat/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/x.lnk',
                     'C/Users/pat/OneDrive/Desktop/y.lnk',
                     'C/Users/pat/AppData/Local/Microsoft/Windows/WinX/Group1/z.lnk',
                     'C/Users/pat/Links/Desktop.lnk'):
            self.assertIsNone(link_location(path), path)


if __name__ == '__main__':
    unittest.main()
