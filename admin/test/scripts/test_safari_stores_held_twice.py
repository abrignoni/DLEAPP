"""Pin how the Safari plist and CloudTabs.db artifacts read a file an extraction holds twice.

A logical extraction of a Mac can hold one user's Safari files under Users/ and again under
System/Volumes/Data/Users/. For Bookmarks.plist, TopSites.plist, RecentlyClosedTabs.plist and
LastSession.plist a second copy with the same bytes is read once, from Users/, and copies that
differ are both read. CloudTabs.db is read as one store: a tab both copies hold with the same
values is reported once, and a tab only one copy holds is still reported. Two users are never
read as one, whatever their files hold.

Every value here is written for the test. cloud_tabs and cloud_tab_devices use the CREATE TABLE
text Safari wrote on the tested images; the expected rows are written out, never read back from
the module.
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

USER = 'Users/someone/Library/Safari'
DATA_VIEW = 'System/Volumes/Data/Users/someone/Library/Safari'
OTHER_USER = 'Users/another/Library/Safari'


def _utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


def _bookmarks(*leaves):
    return {'WebBookmarkType': 'WebBookmarkTypeList', 'Title': '', 'Children': [
        {'WebBookmarkType': 'WebBookmarkTypeList', 'Title': 'BookmarksBar', 'Children': [
            {'WebBookmarkType': 'WebBookmarkTypeLeaf', 'URIDictionary': {'title': title},
             'URLString': url, 'WebBookmarkUUID': uuid} for title, url, uuid in leaves]}]}


def _top_sites(*sites):
    return {'TopSites': [{'TopSiteTitle': title, 'TopSiteURLString': url, 'TopSiteIsBuiltIn': built_in}
                         for title, url, built_in in sites]}


def _window(*tabs):
    # 700000000 seconds after 2001-01-01 is 2023-03-08 20:26:40 UTC.
    return {'WindowUUID': 'WINDOW-1', 'DateClosed': datetime.datetime(2023, 3, 9, 1, 2, 3),
            'IsPrivateWindow': False,
            'TabStates': [{'TabTitle': title, 'TabURL': url, 'TabUUID': uuid, 'TabIndex': index,
                           'LastVisitTime': 700000000.0, 'SessionState': b'12345'}
                          for index, (title, url, uuid) in enumerate(tabs)]}


def _closed(*tabs):
    return {'ClosedTabOrWindowPersistentStates': [{'PersistentState': _window(*tabs)}]}


def _session(*tabs):
    return {'SessionWindows': [_window(*tabs)]}


ONE = ('One', 'https://one.example/', 'UUID-1')
TWO = ('Two', 'https://two.example/', 'UUID-2')


def _tab(title, url, uuid, index, source):
    return (title, url, datetime.datetime(2023, 3, 9, 1, 2, 3), _utc(2023, 3, 8, 20, 26, 40),
            'WINDOW-1', uuid, index, 'No', 5, source)


# artifact, file name, run-log label, the plist with one entry and with two, and the rows each
# gives for a source file, less that source file.
PLISTS = (
    (safaribrowsing.safariBookmarks, 'Bookmarks.plist', 'Safari Bookmarks',
     _bookmarks(ONE), _bookmarks(ONE, TWO),
     [('BookmarksBar', 'One', 'https://one.example/', 'UUID-1')],
     [('BookmarksBar', 'One', 'https://one.example/', 'UUID-1'),
      ('BookmarksBar', 'Two', 'https://two.example/', 'UUID-2')]),
    (safaribrowsing.safariTopSites, 'TopSites.plist', 'Safari Top Sites',
     _top_sites(('One', 'https://one.example/', True)),
     _top_sites(('One', 'https://one.example/', True), ('Two', 'https://two.example/', False)),
     [('One', 'https://one.example/', 'Yes', '')],
     [('One', 'https://one.example/', 'Yes', ''), ('Two', 'https://two.example/', 'No', '')]),
    (safaribrowsing.safariRecentlyClosedTabs, 'RecentlyClosedTabs.plist',
     'Safari Recently Closed Tabs', _closed(ONE), _closed(ONE, TWO),
     [_tab(*ONE, 0, None)[:-1]], [_tab(*ONE, 0, None)[:-1], _tab(*TWO, 1, None)[:-1]]),
    (safaribrowsing.safariLastSession, 'LastSession.plist', 'Safari Last Session',
     _session(ONE), _session(ONE, TWO),
     [_tab(*ONE, 0, None)[:-1]], [_tab(*ONE, 0, None)[:-1], _tab(*TWO, 1, None)[:-1]]),
)

CLOUD_TABLES = (
    'CREATE TABLE cloud_tab_devices (device_uuid TEXT PRIMARY KEY NOT NULL,system_fields BLOB NOT NULL,'
    'device_name TEXT,has_duplicate_device_name BOOLEAN DEFAULT 0,is_ephemeral_device BOOLEAN DEFAULT 0,'
    'last_modified REAL NOT NULL)',
    'CREATE TABLE cloud_tabs (tab_uuid TEXT PRIMARY KEY NOT NULL,system_fields BLOB NOT NULL,'
    'device_uuid TEXT NOT NULL,position BLOB NOT NULL,title TEXT,url TEXT NOT NULL,'
    'is_showing_reader BOOLEAN DEFAULT 0,is_pinned BOOLEAN DEFAULT 0,'
    'reader_scroll_position_page_index INTEGER,scene_id TEXT,FOREIGN KEY(device_uuid) REFERENCES '
    'cloud_tab_devices(device_uuid) ON DELETE CASCADE)',
)
CLOUD_TABS = (('TAB-1', 'One', 'https://one.example/'), ('TAB-2', 'Two', 'https://two.example/'))
THIRD_TAB = ('TAB-3', 'Three', 'https://three.example/')


def _cloud_row(tab, source, title=None):
    uuid, stored_title, url = tab
    return (title or stored_title, url, None, 'A phone', '', 'DEVICE-1', _utc(2023, 3, 8, 20, 26, 40), '',
            '', '', '', uuid, source)


class SafariStoresHeldTwiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _plist(self, folder, name, value):
        path = self.root / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps(value))
        self.files.append(str(path))
        return path.read_bytes()

    def _cloud(self, folder, tabs=CLOUD_TABS, retitle=None):
        path = self.root / folder / 'CloudTabs.db'
        path.parent.mkdir(parents=True, exist_ok=True)
        database = sqlite3.connect(path)
        for statement in CLOUD_TABLES:
            database.execute(statement)
        database.execute('INSERT INTO cloud_tab_devices (device_uuid, system_fields, device_name, '
                         "last_modified) VALUES ('DEVICE-1', x'00', 'A phone', 700000000.0)")
        database.executemany(
            'INSERT INTO cloud_tabs (tab_uuid, system_fields, device_uuid, position, title, url) '
            "VALUES (?, x'00', 'DEVICE-1', x'00', ?, ?)",
            [(uuid, (retitle or {}).get(uuid, title), url) for uuid, title, url in tabs])
        database.commit()
        database.close()
        self.files.append(str(path))

    def _run(self, processor):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(safaribrowsing, 'logfunc') as log:
            _headers, rows, source = processor.__wrapped__(context)
        return rows, source, [call.args[0] for call in log.call_args_list]

    def test_a_plist_with_the_same_bytes_under_both_views_is_read_once(self):
        for processor, name, label, one, _two, one_rows, _two_rows in PLISTS:
            with self.subTest(name):
                self.files = []
                first = self._plist(USER, name, one)
                second = self._plist(DATA_VIEW, name, one)
                self.assertEqual(first, second)
                rows, source, log = self._run(processor)
                self.assertEqual(rows, [row + (f'{USER}/{name}',) for row in one_rows])
                self.assertEqual(source, f'{USER}/{name}')
                self.assertEqual(log[0], f'{label}: 1 byte-identical copy(ies) under '
                                         'System/Volumes/Data not read again')

    def test_plists_that_differ_between_the_views_are_both_read(self):
        for processor, name, _label, one, two, one_rows, two_rows in PLISTS:
            with self.subTest(name):
                self.files = []
                first = self._plist(USER, name, one)
                second = self._plist(DATA_VIEW, name, two)
                self.assertNotEqual(first, second)
                rows, source, log = self._run(processor)
                self.assertEqual(sorted(rows, key=lambda row: (row[-1], row[1])),
                                 [row + (f'{DATA_VIEW}/{name}',) for row in two_rows]
                                 + [row + (f'{USER}/{name}',) for row in one_rows])
                self.assertEqual(sorted(source.split('\n')), [f'{DATA_VIEW}/{name}', f'{USER}/{name}'])
                self.assertEqual(len(log), 1)

    def test_two_users_with_the_same_plist_bytes_are_both_read(self):
        for processor, name, _label, one, _two, one_rows, _two_rows in PLISTS:
            with self.subTest(name):
                self.files = []
                first = self._plist(USER, name, one)
                second = self._plist(OTHER_USER, name, one)
                self.assertEqual(first, second)
                rows, source, log = self._run(processor)
                self.assertEqual(sorted(rows, key=lambda row: row[-1]),
                                 [row + (f'{OTHER_USER}/{name}',) for row in one_rows]
                                 + [row + (f'{USER}/{name}',) for row in one_rows])
                self.assertEqual(sorted(source.split('\n')), [f'{OTHER_USER}/{name}', f'{USER}/{name}'])
                self.assertEqual(len(log), 1)

    def test_a_plist_held_only_under_the_data_volume_view_is_read(self):
        for processor, name, _label, one, _two, one_rows, _two_rows in PLISTS:
            with self.subTest(name):
                self.files = []
                self._plist(DATA_VIEW, name, one)
                rows, source, _log = self._run(processor)
                self.assertEqual(rows, [row + (f'{DATA_VIEW}/{name}',) for row in one_rows])
                self.assertEqual(source, f'{DATA_VIEW}/{name}')

    def test_the_two_views_inside_a_wrapper_folder_are_read_as_one(self):
        # An archive can hold the whole tree inside one top folder.
        for processor, name, label, one, _two, one_rows, _two_rows in PLISTS:
            with self.subTest(name):
                self.files = []
                self._plist(f'export/{USER}', name, one)
                self._plist(f'export/{DATA_VIEW}', name, one)
                rows, source, log = self._run(processor)
                self.assertEqual(rows, [row + (f'export/{USER}/{name}',) for row in one_rows])
                self.assertEqual(source, f'export/{USER}/{name}')
                self.assertEqual(log[0], f'{label}: 1 byte-identical copy(ies) under '
                                         'System/Volumes/Data not read again')
        self.files = []
        self._cloud(f'export/{USER}')
        self._cloud(f'export/{DATA_VIEW}')
        rows, _source, _log = self._run(safaribrowsing.safariCloudTabs)
        self.assertEqual(rows, [_cloud_row(tab, f'export/{USER}/CloudTabs.db') for tab in CLOUD_TABS])

    def test_a_plist_that_cannot_be_opened_is_not_taken_for_a_repeat(self):
        # A folder with the plist's name cannot be opened as a file, under either view.
        for folder in (USER, DATA_VIEW):
            path = self.root / folder / 'TopSites.plist'
            path.mkdir(parents=True)
            self.files.append(str(path))
        rows, source, log = self._run(safaribrowsing.safariTopSites)
        self.assertEqual(rows, [])
        self.assertEqual(source, '')
        self.assertEqual([line.split(" '")[0] for line in log],
                         ['Safari: could not parse plist', 'Safari: could not parse plist',
                          'Safari Top Sites: 0 entr(ies) across 0 TopSites.plist file(s).'])

    def test_cloud_tabs_held_under_both_views_are_reported_once(self):
        self._cloud(USER)
        self._cloud(DATA_VIEW)
        rows, source, log = self._run(safaribrowsing.safariCloudTabs)
        user_file = f'{USER}/CloudTabs.db'
        self.assertEqual(rows, [_cloud_row(tab, user_file) for tab in CLOUD_TABS])
        self.assertEqual(source, f'{user_file}\n{DATA_VIEW}/CloudTabs.db')
        self.assertEqual(log, ['Safari iCloud Tabs: 2 tab(s) across 2 CloudTabs.db file(s); '
                               '2 tab(s) held by a second copy of a store were not reported again.'])

    def test_a_cloud_tab_only_one_copy_holds_or_that_differs_is_still_reported(self):
        # The first copy holds tabs 1 and 2. The second holds tab 1 unchanged, tab 2 under another
        # title, and a third tab.
        self._cloud(USER)
        self._cloud(DATA_VIEW, tabs=CLOUD_TABS + (THIRD_TAB,), retitle={'TAB-2': 'Two, later'})
        rows, _source, log = self._run(safaribrowsing.safariCloudTabs)
        user_file, data_file = f'{USER}/CloudTabs.db', f'{DATA_VIEW}/CloudTabs.db'
        self.assertEqual(rows, [
            _cloud_row(CLOUD_TABS[0], user_file), _cloud_row(CLOUD_TABS[1], user_file),
            _cloud_row(CLOUD_TABS[1], data_file, title='Two, later'), _cloud_row(THIRD_TAB, data_file)])
        self.assertEqual(log, ['Safari iCloud Tabs: 4 tab(s) across 2 CloudTabs.db file(s); '
                               '1 tab(s) held by a second copy of a store were not reported again.'])

    def test_cloud_tabs_of_two_users_are_both_reported(self):
        self._cloud(USER)
        self._cloud(OTHER_USER)
        rows, source, log = self._run(safaribrowsing.safariCloudTabs)
        other_file, user_file = f'{OTHER_USER}/CloudTabs.db', f'{USER}/CloudTabs.db'
        self.assertEqual(rows, [_cloud_row(tab, other_file) for tab in CLOUD_TABS]
                         + [_cloud_row(tab, user_file) for tab in CLOUD_TABS])
        self.assertEqual(source, f'{other_file}\n{user_file}')
        self.assertEqual(log, ['Safari iCloud Tabs: 4 tab(s) across 2 CloudTabs.db file(s); '
                               '0 tab(s) held by a second copy of a store were not reported again.'])

    def test_a_cloud_tabs_database_with_no_tab_is_still_named_as_read(self):
        self._cloud(USER, tabs=())
        rows, source, _log = self._run(safaribrowsing.safariCloudTabs)
        self.assertEqual(rows, [])
        self.assertEqual(source, f'{USER}/CloudTabs.db')


if __name__ == '__main__':
    unittest.main()
