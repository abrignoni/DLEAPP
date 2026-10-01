"""Pin how Safari Recently Closed Tabs and Safari Last Session show a tab's cached snapshot.

A tab in RecentlyClosedTabs.plist or LastSession.plist carries a TabUUID. Safari's TabSnapshots
folder holds a Metadata.db whose uuid is a tab's UUID and whose filename names the image. On
the tested images the plist sat in the user's Library/Safari and the TabSnapshots folder in
Safari's container under the same Library, so the snapshot is looked for beside the plist's
Library folder and in that container, never in another user's folders, and is shown only when
the file begins with the PNG signature.

Every value here is written for the test; the expected rows are written out, never read back
from the module.
"""
import datetime
import pathlib
import plistlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import safaribrowsing  # pylint: disable=wrong-import-position

HOME = 'Users/someone'
DATA_HOME = f'System/Volumes/Data/{HOME}'
OTHER_HOME = 'Users/another'
CONTAINER = 'Library/Containers/com.apple.Safari/Data'
SNAPSHOTS = 'Library/Caches/com.apple.Safari/TabSnapshots'
CLOSED = 'Library/Safari/RecentlyClosedTabs.plist'
SESSION = 'Library/Safari/LastSession.plist'

SNAPSHOT_METADATA = (
    'CREATE TABLE snapshot_metadata (uuid TEXT PRIMARY KEY NOT NULL,date_created REAL DEFAULT 0,'
    'filename TEXT NOT NULL,url TEXT NOT NULL)')
PNG = b'\x89PNG\r\n\x1a\n' + b'image bytes'
WHEN = datetime.datetime(2023, 3, 9, 1, 2, 3)


def _tab(uuid):
    return {'TabTitle': uuid, 'TabURL': f'https://{uuid.lower()}.example/', 'TabUUID': uuid, 'TabIndex': 0}


def _closed(*uuids):
    return {'ClosedTabOrWindowPersistentStates': [
        {'PersistentStateType': 1,
         'PersistentState': {'WindowUUID': 'WINDOW-1', 'DateClosed': WHEN, 'IsPrivateWindow': False,
                             'TabStates': [_tab(uuid) for uuid in uuids[:-1]]}},
        {'PersistentStateType': 0, 'PersistentState': {**_tab(uuids[-1]), 'DateClosed': WHEN}}]}


def _session(*uuids):
    return {'SessionWindows': [{'WindowUUID': 'WINDOW-1', 'DateClosed': WHEN, 'IsPrivateWindow': False,
                                'TabStates': [_tab(uuid) for uuid in uuids]}]}


class SafariPlistTabSnapshotsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _path(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        self.files.append(str(path))
        return path

    def _plist(self, relative, value):
        self._path(relative).write_bytes(plistlib.dumps(value))

    def _snapshots(self, folder, uuids, images=None, data=PNG):
        """A Metadata.db naming <uuid>.png for each uuid, and the image files in `images`."""
        database = sqlite3.connect(self._path(f'{folder}/{SNAPSHOTS}/Metadata.db'))
        database.execute(SNAPSHOT_METADATA)
        database.executemany('INSERT INTO snapshot_metadata VALUES (?, 700000000.0, ?, ?)',
                             [(uuid, f'{uuid}.png', f'https://{uuid.lower()}.example/') for uuid in uuids])
        database.commit()
        database.close()
        for uuid in uuids if images is None else images:
            self._path(f'{folder}/{SNAPSHOTS}/{uuid}.png').write_bytes(data)

    def _shown(self, processor):
        """(Tab UUID, Snapshot, Source File) of each row."""
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())

        def checked_in(path, name):
            return f'media of {pathlib.Path(path).relative_to(self.root).as_posix()} named {name}'

        with mock.patch.object(safaribrowsing, 'logfunc'), \
                mock.patch.object(safaribrowsing, 'check_in_media', side_effect=checked_in):
            headers, rows, _source = processor.__wrapped__(context)
        self.assertEqual(headers[-2:], (('Snapshot', 'media'), 'Source File'))
        return [(row[5], row[-2], row[-1]) for row in rows]

    def test_a_closed_tab_shows_the_snapshot_in_safaris_container(self):
        self._plist(f'{HOME}/{CLOSED}', _closed('IN-WINDOW', 'NO-SNAPSHOT', 'ALONE'))
        self._snapshots(f'{HOME}/{CONTAINER}', ['IN-WINDOW', 'ALONE'])
        folder = f'{HOME}/{CONTAINER}/{SNAPSHOTS}'
        self.assertEqual(self._shown(safaribrowsing.safariRecentlyClosedTabs), [
            ('IN-WINDOW', f'media of {folder}/IN-WINDOW.png named IN-WINDOW.png', f'{HOME}/{CLOSED}'),
            ('NO-SNAPSHOT', '', f'{HOME}/{CLOSED}'),
            ('ALONE', f'media of {folder}/ALONE.png named ALONE.png', f'{HOME}/{CLOSED}')])

    def test_a_session_tab_shows_the_snapshot_beside_its_own_library_folder(self):
        self._plist(f'{HOME}/{SESSION}', _session('FIRST', 'SECOND'))
        self._snapshots(HOME, ['SECOND'])
        self.assertEqual(self._shown(safaribrowsing.safariLastSession), [
            ('FIRST', '', f'{HOME}/{SESSION}'),
            ('SECOND', f'media of {HOME}/{SNAPSHOTS}/SECOND.png named SECOND.png', f'{HOME}/{SESSION}')])

    def test_a_plist_inside_the_container_finds_the_container_snapshots(self):
        self._plist(f'{HOME}/{CONTAINER}/{SESSION}', _session('FIRST'))
        self._snapshots(f'{HOME}/{CONTAINER}', ['FIRST'])
        self.assertEqual(self._shown(safaribrowsing.safariLastSession), [
            ('FIRST', f'media of {HOME}/{CONTAINER}/{SNAPSHOTS}/FIRST.png named FIRST.png',
             f'{HOME}/{CONTAINER}/{SESSION}')])

    def test_another_users_snapshot_is_never_shown(self):
        for home in (HOME, OTHER_HOME):
            self._plist(f'{home}/{CLOSED}', _closed('SHARED', 'ALONE'))
            self._plist(f'{home}/{SESSION}', _session('SHARED'))
        self._snapshots(f'{OTHER_HOME}/{CONTAINER}', ['SHARED', 'ALONE'])
        for processor in (safaribrowsing.safariRecentlyClosedTabs, safaribrowsing.safariLastSession):
            with self.subTest(processor.__name__):
                shown = self._shown(processor)
                self.assertEqual(sorted({(source.split('/')[1], snapshot != '') for _uuid, snapshot, source in shown}),
                                 [('another', True), ('someone', False)])

    def test_a_file_that_is_not_a_png_or_is_not_there_is_not_shown(self):
        self._plist(f'{HOME}/{CLOSED}', _closed('NOT-IMAGE', 'MISSING'))
        self._snapshots(f'{HOME}/{CONTAINER}', ['NOT-IMAGE', 'MISSING'], images=['NOT-IMAGE'], data=b'not an image')
        self.assertEqual([snapshot for _uuid, snapshot, _source in self._shown(safaribrowsing.safariRecentlyClosedTabs)],
                         ['', ''])

    def test_a_plist_held_under_both_views_shows_the_image_under_users_once(self):
        for home in (HOME, DATA_HOME):
            self._plist(f'{home}/{SESSION}', _session('FIRST'))
            self._snapshots(f'{home}/{CONTAINER}', ['FIRST'])
        self.assertEqual(self._shown(safaribrowsing.safariLastSession), [
            ('FIRST', f'media of {HOME}/{CONTAINER}/{SNAPSHOTS}/FIRST.png named FIRST.png', f'{HOME}/{SESSION}')])


if __name__ == '__main__':
    unittest.main()
