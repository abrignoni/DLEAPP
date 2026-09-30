"""Pin the folders the Telegram Desktop artifacts match: macOS and Windows, and both Linux spellings."""
import fnmatch
import importlib
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

MODULES = ('telegramAccounts', 'telegramActivity', 'telegramCache', 'telegramLogs')
ROOTS = ('Users/u/Library/Application Support/Telegram Desktop', 'Users/u/AppData/Roaming/Telegram Desktop',
         'home/u/.local/share/TelegramDesktop', 'home/u/.TelegramDesktop',
         'home/u/.var/app/org.telegram.desktop/data/TelegramDesktop')
MEMBERS = ('tdata/key_datas', 'tdata/D877F783D5D3EF8Cs', 'tdata/D877F783D5D3EF8C/maps', 'log.txt')


class TelegramDesktopPathsTest(unittest.TestCase):
    def test_each_root_matches_like_the_macos_one(self):
        for module in MODULES:
            blocks = importlib.import_module(f'scripts.artifacts.{module}').__artifacts_v2__
            for key, block in blocks.items():
                expected = {m for m in MEMBERS
                            if any(fnmatch.fnmatch(f'x/{ROOTS[0]}/{m}', p) for p in block['paths'])}
                self.assertTrue(expected, key)
                for root in ROOTS:
                    got = {m for m in MEMBERS if any(fnmatch.fnmatch(f'x/{root}/{m}', p) for p in block['paths'])}
                    self.assertEqual(got, expected, (key, root))
                    for m in MEMBERS:
                        hits = sum(fnmatch.fnmatch(f'x/{root}/{m}', p) for p in block['paths'])
                        self.assertLessEqual(hits, 1, (key, root, m))

    def test_a_folder_that_only_ends_in_the_name_is_not_matched(self):
        for module in MODULES:
            for key, block in importlib.import_module(f'scripts.artifacts.{module}').__artifacts_v2__.items():
                for root in ('home/u/NotTelegramDesktop', 'home/u/.local/share/TelegramDesktopX'):
                    self.assertFalse(any(fnmatch.fnmatch(f'x/{root}/{m}', p) for m in MEMBERS for p in block['paths']),
                                     (key, root))


if __name__ == '__main__':
    unittest.main()
