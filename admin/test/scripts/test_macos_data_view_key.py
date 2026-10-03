"""Pin how macos_plists reads a file a Mac logical extraction holds under both Data views.

macOS firmlinks expose the Data volume's folders at the root and under
System/Volumes/Data/, so an extraction can hold one file twice. When the extraction's tree
sits inside a top folder (a zip whose members start export/Users/... and
export/System/Volumes/Data/Users/...), the path an artifact receives starts with that
folder, and the two views must still be read as one. The same holds for a copied root kept
deeper in the tree. Folder names that only look like the prefix must be left alone.

Every expected value is written out here, never read back from the code under test.
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
from scripts.macos_plists import canonical_relative  # pylint: disable=wrong-import-position

VIEW = 'System/Volumes/Data/'
MNT1 = 'System/Volumes/Update/mnt1/'
PLIST = 'Users/someone/Library/Safari/TopSites.plist'
PROFILE = 'Users/someone/Library/Application Support/Google/Chrome/Default'
SKIPPED_ONE = 'Test Label: 1 byte-identical copy(ies) under System/Volumes/Data or System/Volumes/Update/mnt1 not read again'


class CanonicalRelativeTest(unittest.TestCase):
    def test_the_data_view_at_the_root_is_removed(self):
        self.assertEqual(canonical_relative(VIEW + PLIST), PLIST)
        self.assertEqual(canonical_relative(PLIST), PLIST)

    def test_the_data_view_inside_a_wrapper_folder_is_removed(self):
        self.assertEqual(canonical_relative('export/' + VIEW + PLIST), 'export/' + PLIST)
        self.assertEqual(canonical_relative('export/' + PLIST), 'export/' + PLIST)
        self.assertEqual(canonical_relative('case 7/files/' + VIEW + PLIST), 'case 7/files/' + PLIST)

    def test_backslashes_and_a_leading_separator_are_read_the_same_way(self):
        self.assertEqual(canonical_relative('export\\System\\Volumes\\Data\\Users\\someone\\a.plist'),
                         'export/Users/someone/a.plist')
        self.assertEqual(canonical_relative('/export/' + VIEW + PLIST), 'export/' + PLIST)
        self.assertEqual(canonical_relative('\\System\\Volumes\\Data\\Users\\someone\\a.plist'),
                         'Users/someone/a.plist')

    def test_every_data_view_segment_is_removed(self):
        # A copied root kept inside a home folder, seen through the extraction's own Data view.
        self.assertEqual(canonical_relative(VIEW + 'Users/a/old/' + VIEW + PLIST), 'Users/a/old/' + PLIST)
        self.assertEqual(canonical_relative('Users/a/old/' + VIEW + PLIST), 'Users/a/old/' + PLIST)
        self.assertEqual(canonical_relative(VIEW + VIEW + PLIST), PLIST)

    def test_the_update_mnt1_view_is_removed(self):
        self.assertEqual(canonical_relative(MNT1 + PLIST), PLIST)
        self.assertEqual(canonical_relative(MNT1 + VIEW + PLIST), PLIST)
        self.assertEqual(canonical_relative('export/' + MNT1 + PLIST), 'export/' + PLIST)
        self.assertEqual(canonical_relative(MNT1 + 'Volumes/Macintosh HD - Data/x.plist'),
                         'Volumes/Macintosh HD - Data/x.plist')

    def test_names_that_only_look_like_the_update_view_are_kept(self):
        for path in ('System/Volumes/Update/x.plist',
                     'System/Volumes/Update/mnt10/x.plist',
                     'System/Volumes/Update/mnt1',
                     'MySystem/Volumes/Update/mnt1/x.plist',
                     'export/system/volumes/update/mnt1/x.plist'):
            self.assertEqual(canonical_relative(path), path)

    def test_names_that_only_look_like_the_prefix_are_kept(self):
        for path in ('MySystem/Volumes/Data/x.plist',
                     'export/MySystem/Volumes/Data/x.plist',
                     'System/Volumes/Database/x.plist',
                     'System/Volumes/DataX/x.plist',
                     'System/Volumes/Preboot/x.plist',
                     'System/Library/Templates/Data/Volumes/x.plist',
                     'export/System/Volumes/Data',
                     'export/system/volumes/data/x.plist',
                     'Volumes/Data/x.plist'):
            self.assertEqual(canonical_relative(path), path)


class UniqueSourcesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

    def _write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def _unique(self, paths, sidecars=()):
        context = SimpleNamespace(
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(macos_plists, 'logfunc') as log:
            kept, skipped = macos_plists.unique_sources(context, paths, sidecars=sidecars, label='Test Label')
        return kept, skipped, [call.args[0] for call in log.call_args_list]

    def test_the_two_views_at_the_root_are_read_once(self):
        plain = self._write(PLIST, b'one')
        copy = self._write(VIEW + PLIST, b'one')
        self.assertEqual(self._unique([copy, plain]), ([plain], 1, [SKIPPED_ONE]))

    def test_the_two_views_inside_a_wrapper_folder_are_read_once(self):
        plain = self._write('export/' + PLIST, b'one')
        copy = self._write('export/' + VIEW + PLIST, b'one')
        self.assertEqual(self._unique([copy, plain]), ([plain], 1, [SKIPPED_ONE]))

    def test_the_two_views_two_folders_deep_are_read_once(self):
        plain = self._write('case 7/files/' + PLIST, b'one')
        copy = self._write('case 7/files/' + VIEW + PLIST, b'one')
        self.assertEqual(self._unique([copy, plain]), ([plain], 1, [SKIPPED_ONE]))

    def test_the_root_data_and_update_mnt1_views_are_read_once(self):
        plain = self._write(PLIST, b'one')
        data = self._write(VIEW + PLIST, b'one')
        mnt1 = self._write(MNT1 + PLIST, b'one')
        kept, skipped, log = self._unique([mnt1, data, plain])
        self.assertEqual((kept, skipped), ([plain], 2))
        self.assertEqual(log, ['Test Label: 2 byte-identical copy(ies) under System/Volumes/Data or '
                               'System/Volumes/Update/mnt1 not read again'])

    def test_an_update_mnt1_copy_that_differs_is_read(self):
        plain = self._write(PLIST, b'one')
        mnt1 = self._write(MNT1 + PLIST, b'two')
        self.assertEqual(self._unique([mnt1, plain]), ([plain, mnt1], 0, []))

    def test_views_that_differ_inside_a_wrapper_folder_are_both_read(self):
        plain = self._write('export/' + PLIST, b'one')
        copy = self._write('export/' + VIEW + PLIST, b'two')
        self.assertEqual(self._unique([copy, plain]), ([plain, copy], 0, []))

    def test_a_sidecar_that_differs_inside_a_wrapper_folder_keeps_both(self):
        plain = self._write('export/Users/someone/store.db', b'database')
        copy = self._write('export/' + VIEW + 'Users/someone/store.db', b'database')
        self._write('export/' + VIEW + 'Users/someone/store.db-wal', b'wal')
        self.assertEqual(self._unique([copy, plain], sidecars=('-wal',)), ([plain, copy], 0, []))
        self._write('export/Users/someone/store.db-wal', b'wal')
        self.assertEqual(self._unique([copy, plain], sidecars=('-wal',)), ([plain], 1, [SKIPPED_ONE]))

    def test_a_file_held_only_under_the_data_view_of_a_wrapper_folder_is_read(self):
        copy = self._write('export/' + VIEW + PLIST, b'one')
        self.assertEqual(self._unique([copy]), ([copy], 0, []))

    def test_two_users_with_the_same_bytes_are_both_read(self):
        first = self._write('export/Users/a/Library/x.plist', b'one')
        second = self._write('export/Users/b/Library/x.plist', b'one')
        self.assertEqual(self._unique([second, first]), ([first, second], 0, []))

    def test_two_wrapper_folders_with_the_same_bytes_are_each_read_once(self):
        paths = [self._write(top + view + PLIST, b'one') for top in ('one/', 'two/') for view in ('', VIEW)]
        kept, skipped, log = self._unique(paths)
        self.assertEqual(kept, [str(self.root / ('one/' + PLIST)), str(self.root / ('two/' + PLIST))])
        self.assertEqual(skipped, 2)
        self.assertEqual(log, ['Test Label: 2 byte-identical copy(ies) under System/Volumes/Data or System/Volumes/Update/mnt1 not read again'])

    def test_a_copied_root_seen_through_both_views_is_read_once_and_apart_from_the_live_file(self):
        live = self._write(PLIST, b'live')
        self._write(VIEW + PLIST, b'live')
        old = self._write('Users/a/old/' + PLIST, b'old')
        for relative in ('Users/a/old/' + VIEW + PLIST, VIEW + 'Users/a/old/' + PLIST,
                         VIEW + 'Users/a/old/' + VIEW + PLIST):
            self._write(relative, b'old')
        paths = [str(p) for p in self.root.rglob('TopSites.plist')]
        self.assertEqual(len(paths), 6)
        kept, skipped, _log = self._unique(paths)
        self.assertEqual((kept, skipped), ([live, old], 4))

    def test_the_views_of_a_copied_root_that_differ_are_each_read_once(self):
        first = self._write('Users/a/old/' + PLIST, b'first')
        second = self._write('Users/a/old/' + VIEW + PLIST, b'second')
        self._write(VIEW + 'Users/a/old/' + PLIST, b'first')
        self._write(VIEW + 'Users/a/old/' + VIEW + PLIST, b'second')
        paths = [str(p) for p in self.root.rglob('TopSites.plist')]
        self.assertEqual(len(paths), 4)
        kept, skipped, _log = self._unique(paths)
        self.assertEqual((kept, skipped), ([first, second], 2))

    def test_the_views_are_matched_on_the_evidence_path_not_the_staged_one(self):
        # Staged under names that say nothing about the view, as a renamed colliding copy is.
        plain = self._write('staged/one/TopSites.plist', b'one')
        copy = self._write('staged/two/TopSites.plist', b'one')
        other = self._write('staged/three/TopSites.plist', b'one')
        evidence = {plain: PLIST, copy: VIEW + PLIST, other: 'Users/else/Library/Safari/TopSites.plist'}
        context = SimpleNamespace(get_relative_path=lambda p: evidence[p])
        with mock.patch.object(macos_plists, 'logfunc'):
            kept, skipped = macos_plists.unique_sources(context, [plain, copy, other], label='Test Label')
        self.assertEqual((sorted(kept), skipped), (sorted([plain, other]), 1))

    def test_folders_that_only_look_like_the_prefix_are_both_read(self):
        paths = [self._write(relative, b'one') for relative in
                 ('x.plist', 'MySystem/Volumes/Data/x.plist',
                  'Database/x.plist', 'System/Volumes/Database/x.plist')]
        kept, skipped, log = self._unique(paths)
        self.assertEqual((sorted(kept), skipped, log), (sorted(paths), 0, []))


class WrappedProfileStoresTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

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

    def test_a_profile_under_both_views_of_a_wrapper_folder_is_read_once(self):
        for base in ('export/' + PROFILE, 'export/' + VIEW + PROFILE):
            self._write(f'{base}/History', b'history bytes')
            self._write(f'{base}/History-journal', b'journal bytes')
        stores, log = self._stores({'History'})
        self.assertEqual([(s.relative, s.container, s.user) for s in stores],
                         [(f'export/{PROFILE}/History', f'export/{PROFILE}', 'someone')])
        self.assertEqual(log, [SKIPPED_ONE])

    def test_copies_that_differ_inside_a_wrapper_folder_share_a_container(self):
        self._write(f'export/{PROFILE}/History', b'history bytes')
        self._write(f'export/{VIEW}{PROFILE}/History', b'other history bytes')
        stores, log = self._stores({'History'})
        self.assertEqual([(s.relative, s.container) for s in stores],
                         [(f'export/{VIEW}{PROFILE}/History', f'export/{PROFILE}'),
                          (f'export/{PROFILE}/History', f'export/{PROFILE}')])
        self.assertEqual(log, [])


if __name__ == '__main__':
    unittest.main()
