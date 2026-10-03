"""Pin the folder views the macOS modules with their own path patterns fold together.

A logical extraction of a Mac can hold a file at the root, under System/Volumes/Data/ and
again under System/Volumes/Update/mnt1/. These modules key a file or folder by its path
with those runs removed, through a pattern of their own. Expected values are written out.
"""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_powerlog  # pylint: disable=wrong-import-position
from scripts.artifacts import (macosBinaryCookies, macosFsckLogs,  # pylint: disable=wrong-import-position
                               macosInstallLog, macosSystemInfo, safaribrowsing)

PATTERNS = {
    'macosBinaryCookies': macosBinaryCookies._FIRMLINK,  # pylint: disable=protected-access
    'macosFsckLogs': macosFsckLogs._FIRMLINK,  # pylint: disable=protected-access
    'macosInstallLog': macosInstallLog._FIRMLINK,  # pylint: disable=protected-access
    'macosSystemInfo': macosSystemInfo._FIRMLINK,  # pylint: disable=protected-access
    'safaribrowsing': safaribrowsing._DATA_VOLUME,  # pylint: disable=protected-access
}


class ModuleViewPatternTest(unittest.TestCase):
    def test_each_view_folds_to_the_root_path(self):
        for name, pattern in PATTERNS.items():
            for path, expected in (('Users/a/x.plist', 'Users/a/x.plist'),
                                   ('System/Volumes/Data/Users/a/x.plist', 'Users/a/x.plist'),
                                   ('System/Volumes/Update/mnt1/Users/a/x.plist', 'Users/a/x.plist'),
                                   ('System/Volumes/Update/mnt1/System/Volumes/Data/Users/a/x.plist',
                                    'Users/a/x.plist'),
                                   ('export/System/Volumes/Update/mnt1/Users/a/x.plist',
                                    'export/Users/a/x.plist')):
                with self.subTest(module=name, path=path):
                    self.assertEqual(pattern.sub(r'\1', path, count=1), expected)

    def test_lookalike_folders_are_kept(self):
        for name, pattern in PATTERNS.items():
            for path in ('System/Volumes/Update/x.plist', 'System/Volumes/Update/mnt10/x.plist',
                         'MySystem/Volumes/Update/mnt1/x.plist', 'System/Volumes/Database/x.plist'):
                with self.subTest(module=name, path=path):
                    self.assertEqual(pattern.sub(r'\1', path, count=1), path)

    def test_powerlog_folder_reads_each_view_as_private_var(self):
        for path in ('/case/private/var/db/powerlog/Library/BatteryLife/CurrentPowerlog.PLSQL',
                     '/case/System/Volumes/Data/private/var/db/powerlog/Library/BatteryLife/CurrentPowerlog.PLSQL',
                     '/case/System/Volumes/Update/mnt1/private/var/db/powerlog/Library/BatteryLife/'
                     'CurrentPowerlog.PLSQL',
                     '/case/System/Volumes/Update/mnt1/System/Volumes/Data/private/var/db/powerlog/Library/'
                     'BatteryLife/Archives/powerlog_2021.PLSQL.gz'):
            with self.subTest(path=path):
                self.assertEqual(macos_powerlog.powerlog_folder(path),
                                 '/case/private/var/db/powerlog/Library/BatteryLife')


if __name__ == '__main__':
    unittest.main()
