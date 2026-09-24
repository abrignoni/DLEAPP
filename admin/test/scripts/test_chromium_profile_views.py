"""Pin how browser_profiles.profile_stores treats one profile held under two Mac views.

A logical extraction of a Mac can hold a Chrome profile under Users/ and under
System/Volumes/Data/Users/. A store whose second copy is byte-identical, journal included,
must come back once, under Users/; copies that differ must both come back; and the two views
of one profile must share one container, so a join between two stores of that profile still
finds its partner. The expected values are written out, never read back from the code.
"""
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

PROFILE = 'Users/someone/Library/Application Support/Google/Chrome/Default'
DATA_VIEW = 'System/Volumes/Data/Users/someone/Library/Application Support/Google/Chrome/Default'
WINDOWS = 'Users/someone/AppData/Local/Google/Chrome/User Data/Default'


class ProfileViewsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files.append(str(path))

    def _stores(self, names):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(macos_plists, 'logfunc') as log:
            stores = browser_profiles.profile_stores(context, names, 'Test Label')
        return stores, [call.args[0] for call in log.call_args_list]

    def test_identical_copies_under_both_views_are_read_once(self):
        for base in (PROFILE, DATA_VIEW):
            self._write(f'{base}/History', b'history bytes')
            self._write(f'{base}/History-journal', b'journal bytes')
        stores, log = self._stores({'History'})
        self.assertEqual([(s.relative, s.container, s.user) for s in stores],
                         [(f'{PROFILE}/History', PROFILE, 'someone')])
        self.assertEqual(log, ['Test Label: 1 byte-identical copy(ies) under '
                               'System/Volumes/Data not read again'])

    def test_copies_that_differ_are_both_read_and_share_a_container(self):
        self._write(f'{PROFILE}/History', b'history bytes')
        self._write(f'{DATA_VIEW}/History', b'other history bytes')
        stores, log = self._stores({'History'})
        self.assertEqual([(s.relative, s.container) for s in stores],
                         [(f'{DATA_VIEW}/History', PROFILE), (f'{PROFILE}/History', PROFILE)])
        self.assertEqual(log, [])

    def test_a_journal_that_differs_keeps_both_copies(self):
        for base in (PROFILE, DATA_VIEW):
            self._write(f'{base}/History', b'history bytes')
        self._write(f'{PROFILE}/History-journal', b'journal bytes')
        self._write(f'{DATA_VIEW}/History-journal', b'a different journal')
        stores, log = self._stores({'History'})
        self.assertEqual([s.relative for s in stores], [f'{DATA_VIEW}/History', f'{PROFILE}/History'])
        self.assertEqual(log, [])

    def test_a_windows_profile_is_unchanged(self):
        self._write(f'{WINDOWS}/History', b'history bytes')
        stores, log = self._stores({'History'})
        self.assertEqual(
            [(s.relative, s.browser, s.profile, s.user, s.container, s.name) for s in stores],
            [(f'{WINDOWS}/History', 'Google Chrome', 'Default', 'someone', WINDOWS, 'History')])
        self.assertEqual(log, [])


if __name__ == '__main__':
    unittest.main()
