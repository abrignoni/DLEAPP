"""Pin what Safari Tabs and Safari Tab Snapshots read from SafariTabs.db and the TabSnapshots folder.

SafariTabs.db keeps tabs as rows of its bookmarks table: a row of type 0 is a tab or a bookmark
and a row of type 1 is a folder (a tab group, a profile, a special list). A tab's times and state
sit in two plists, extra_attributes and local_attributes. Safari caches a page snapshot per tab
in a TabSnapshots folder under the same Library folder, indexed by Metadata.db, whose uuid is
the tab's external_uuid and whose filename names the image.

Pinned here: which rows are reported and with what; that a snapshot is linked through the
recorded uuid, inside the same Library folder only, and shown only when the file begins with
the PNG signature; that a plist holding a date Python cannot represent is still read; and that
a store held under Users/ and again under System/Volumes/Data/Users/ is read as one.

Every value here is written for the test. The CREATE TABLE statements are the text Safari
wrote on the tested macOS 15.4 database, less the columns no test reads; the expected rows are
written out, never read back from the module.
"""
import datetime
import pathlib
import plistlib
import sqlite3
import struct
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import safaribrowsing  # pylint: disable=wrong-import-position

LIBRARY = 'Users/someone/Library/Containers/com.apple.Safari/Data/Library'
DATA_LIBRARY = f'System/Volumes/Data/{LIBRARY}'
OTHER_LIBRARY = 'Users/another/Library/Containers/com.apple.Safari/Data/Library'
TABS = 'Safari/SafariTabs.db'
SNAPSHOTS = 'Caches/com.apple.Safari/TabSnapshots'

BOOKMARKS = (
    'CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT,special_id INTEGER DEFAULT 0,'
    'parent INTEGER, type INTEGER,title TEXT,url TEXT COLLATE NOCASE,num_children INTEGER DEFAULT 0,'
    'order_index INTEGER NOT NULL,external_uuid TEXT UNIQUE,last_modified REAL DEFAULT NULL,'
    'deleted INTEGER DEFAULT 0,extra_attributes BLOB DEFAULT NULL,local_attributes BLOB DEFAULT NULL,'
    'date_closed REAL DEFAULT NULL, subtype INTEGER DEFAULT 0)')
OLD_BOOKMARKS = (
    'CREATE TABLE bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT,parent INTEGER, type INTEGER,'
    'title TEXT,url TEXT COLLATE NOCASE,order_index INTEGER NOT NULL)')
WINDOW_GROUPS = (
    'CREATE TABLE windows_tab_groups (id INTEGER PRIMARY KEY,active_tab_id INTEGER DEFAULT NULL,'
    'tab_group_id INTEGER NOT NULL,window_id INTEGER NOT NULL)')
SNAPSHOT_METADATA = (
    'CREATE TABLE snapshot_metadata (uuid TEXT PRIMARY KEY NOT NULL,date_created REAL DEFAULT 0,'
    'filename TEXT NOT NULL,url TEXT NOT NULL)')

VIEWED = datetime.datetime(2023, 3, 8, 20, 26, 40)
CLOSED = datetime.datetime(2023, 3, 8, 20, 30, 0)
VIEWED_UTC = VIEWED.replace(tzinfo=datetime.timezone.utc)
CLOSED_UTC = CLOSED.replace(tzinfo=datetime.timezone.utc)
# 700000000 seconds after 2001-01-01 is 2023-03-08 20:26:40 UTC.
CREATED = 700000000.0
PNG = b'\x89PNG\r\n\x1a\n' + b'image bytes'


def _extra(**more):
    return plistlib.dumps({'DateLastViewed': VIEWED, 'DeviceIdentifier': 'DEVICE-A', **more})


def _local(index, **more):
    return plistlib.dumps({'DateClosed': CLOSED, 'WindowUUID': 'WINDOW-1', 'TabIndex': index,
                           'OpenedFromLink': index == 1, 'SessionState': b'1234', **more})


# id, parent, type, title, url, order_index, external_uuid, deleted, extra_attributes, local_attributes
ROOT = (1, None, 1, 'Root', None, 0, 'ROOT', 0, None, None)
GROUP = (2, 1, 1, 'Cars', None, 0, 'GROUP', 0, None, None)
GROUP_LIST = (3, 2, 1, 'TopScopedBookmarkList', None, 0, 'LIST', 0, None, None)
FIRST = (4, 2, 0, 'One', 'https://one.example/', 1, 'TAB-1', 0, _extra(), _local(0))
SECOND = (5, 2, 0, 'Two', 'https://two.example/', 2, 'TAB-2', 0, _extra(), _local(1))
SCOPED = (6, 3, 0, 'Kept', 'https://kept.example/', 0, 'TAB-3', 1, None, None)
ROWS = (ROOT, GROUP, GROUP_LIST, FIRST, SECOND, SCOPED)


class SafariTabsTest(unittest.TestCase):
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

    def _tabs(self, library, rows=ROWS, active=4, old=False, tables=True):
        database = sqlite3.connect(self._path(f'{library}/{TABS}'))
        if not tables:
            database.execute('CREATE TABLE generations (generation INTEGER NOT NULL)')
        elif old:
            database.execute(OLD_BOOKMARKS)
            database.executemany('INSERT INTO bookmarks (id, parent, type, title, url, order_index) '
                                 'VALUES (?,?,?,?,?,?)', [row[:6] for row in rows])
        else:
            database.execute(BOOKMARKS)
            database.execute(WINDOW_GROUPS)
            database.executemany(
                'INSERT INTO bookmarks (id, parent, type, title, url, order_index, external_uuid, deleted, '
                'extra_attributes, local_attributes) VALUES (?,?,?,?,?,?,?,?,?,?)', rows)
            if active is not None:
                database.execute('INSERT INTO windows_tab_groups VALUES (1, ?, 2, 1)', (active,))
        database.commit()
        database.close()

    def _snapshots(self, library, rows, columns=True):
        database = sqlite3.connect(self._path(f'{library}/{SNAPSHOTS}/Metadata.db'))
        if columns:
            database.execute(SNAPSHOT_METADATA)
            database.executemany('INSERT INTO snapshot_metadata VALUES (?,?,?,?)', rows)
        else:
            database.execute('CREATE TABLE snapshot_metadata (uuid TEXT PRIMARY KEY NOT NULL)')
        database.commit()
        database.close()

    def _image(self, library, name, data=PNG):
        self._path(f'{library}/{SNAPSHOTS}/{name}').write_bytes(data)

    def _run(self, processor):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())

        def checked_in(path, name):
            return f'media of {pathlib.Path(path).relative_to(self.root).as_posix()} named {name}'

        with mock.patch.object(safaribrowsing, 'logfunc') as log, \
                mock.patch.object(safaribrowsing, 'check_in_media', side_effect=checked_in):
            headers, rows, source = processor.__wrapped__(context)
        return headers, rows, source, [call.args[0] for call in log.call_args_list]

    def test_a_tab_row_shows_its_plist_values_folders_and_snapshot(self):
        self._tabs(LIBRARY)
        self._snapshots(LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/')])
        self._image(LIBRARY, 'TAB-1.png')
        headers, rows, source, log = self._run(safaribrowsing.safariTabs)
        self.assertEqual(headers, (
            ('Last Viewed', 'datetime'), ('Date Closed', 'datetime'), 'Title', 'URL', 'Folder',
            'Active Tab', 'Window UUID', 'Tab Index', 'Opened From Link', 'Session State Size (bytes)',
            'Deleted', 'Tab UUID', 'Device Identifier', ('Snapshot', 'media'), 'Source File'))
        tabs_file = f'{LIBRARY}/{TABS}'
        self.assertEqual(rows, [
            (VIEWED_UTC, CLOSED_UTC, 'One', 'https://one.example/', 'Root/Cars', 'Yes', 'WINDOW-1', 0,
             'No', 4, 'No', 'TAB-1', 'DEVICE-A',
             f'media of {LIBRARY}/{SNAPSHOTS}/TAB-1.png named TAB-1.png', tabs_file),
            (VIEWED_UTC, CLOSED_UTC, 'Two', 'https://two.example/', 'Root/Cars', '', 'WINDOW-1', 1,
             'Yes', 4, 'No', 'TAB-2', 'DEVICE-A', '', tabs_file),
            # A row with no attribute plists, under a folder inside the group, marked deleted.
            (None, None, 'Kept', 'https://kept.example/', 'Root/Cars/TopScopedBookmarkList', '', '', '',
             '', '', 'Yes', 'TAB-3', '', '', tabs_file)])
        self.assertEqual(source, tabs_file)
        self.assertEqual(log, [
            'Safari Tabs: 3 tab(s) across 1 SafariTabs.db file(s); 0 tab(s) held by a second copy of a '
            'store were not reported again; 0 attribute value(s) were not a plist dictionary and were '
            'not read.'])

    def test_a_snapshot_is_shown_only_for_a_png_file_named_by_the_metadata(self):
        self._tabs(LIBRARY)
        # TAB-1's file is not a PNG; TAB-2's metadata names a file that is not in the folder; a file
        # named after TAB-3 has no metadata row.
        self._snapshots(LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/'),
                                  ('TAB-2', CREATED, 'TAB-2.png', 'https://two.example/')])
        self._image(LIBRARY, 'TAB-1.png', b'not an image')
        self._image(LIBRARY, 'TAB-3.png')
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabs)
        self.assertEqual([row[13] for row in rows], ['', '', ''])
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabSnapshots)
        self.assertEqual([(row[3], row[2], row[5]) for row in rows],
                         [('TAB-1', '', 'TAB-1.png'), ('TAB-2', '', 'TAB-2.png')])

    def test_a_snapshot_is_linked_inside_its_own_library_folder_only(self):
        # Two users hold a tab with the same UUID; only the first has a snapshot.
        self._tabs(LIBRARY)
        self._tabs(OTHER_LIBRARY)
        self._snapshots(LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/')])
        self._image(LIBRARY, 'TAB-1.png')
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabs)
        self.assertEqual(sorted((row[-1], row[11], row[13] != '') for row in rows), [
            (f'{OTHER_LIBRARY}/{TABS}', 'TAB-1', False), (f'{OTHER_LIBRARY}/{TABS}', 'TAB-2', False),
            (f'{OTHER_LIBRARY}/{TABS}', 'TAB-3', False),
            (f'{LIBRARY}/{TABS}', 'TAB-1', True), (f'{LIBRARY}/{TABS}', 'TAB-2', False),
            (f'{LIBRARY}/{TABS}', 'TAB-3', False)])

    def test_snapshots_are_listed_with_whether_their_tab_is_in_the_database(self):
        self._tabs(LIBRARY)
        self._snapshots(LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/'),
                                  ('GONE', CREATED + 100, 'GONE.png', 'https://gone.example/')])
        self._image(LIBRARY, 'TAB-1.png')
        self._image(LIBRARY, 'GONE.png')
        # A second user's snapshots, with no SafariTabs.db to compare with.
        self._snapshots(OTHER_LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/')])
        headers, rows, source, log = self._run(safaribrowsing.safariTabSnapshots)
        self.assertEqual(headers, (('Created', 'datetime'), 'URL', ('Snapshot', 'media'), 'Tab UUID',
                                   'Listed In SafariTabs.db', 'File Name', 'Source File'))
        created = datetime.datetime(2023, 3, 8, 20, 26, 40, tzinfo=datetime.timezone.utc)
        later = datetime.datetime(2023, 3, 8, 20, 28, 20, tzinfo=datetime.timezone.utc)
        metadata, other = f'{LIBRARY}/{SNAPSHOTS}/Metadata.db', f'{OTHER_LIBRARY}/{SNAPSHOTS}/Metadata.db'
        self.assertEqual(rows, [
            (created, 'https://one.example/', '', 'TAB-1', '', 'TAB-1.png', other),
            (later, 'https://gone.example/', f'media of {LIBRARY}/{SNAPSHOTS}/GONE.png named GONE.png',
             'GONE', 'No', 'GONE.png', metadata),
            (created, 'https://one.example/', f'media of {LIBRARY}/{SNAPSHOTS}/TAB-1.png named TAB-1.png',
             'TAB-1', 'Yes', 'TAB-1.png', metadata)])
        self.assertEqual(source, f'{other}\n{metadata}')
        self.assertEqual(log, ['Safari Tab Snapshots: 3 snapshot(s) across 2 Metadata.db file(s); '
                               '0 snapshot(s) held by a second copy of a store were not reported again.'])

    def test_stores_held_under_both_views_are_read_as_one(self):
        for library in (LIBRARY, DATA_LIBRARY):
            self._tabs(library)
            self._snapshots(library, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/')])
        # The image is held only under System/Volumes/Data/.
        self._image(DATA_LIBRARY, 'TAB-1.png')
        _headers, rows, source, log = self._run(safaribrowsing.safariTabs)
        self.assertEqual([(row[11], row[-1]) for row in rows],
                         [('TAB-1', f'{LIBRARY}/{TABS}'), ('TAB-2', f'{LIBRARY}/{TABS}'),
                          ('TAB-3', f'{LIBRARY}/{TABS}')])
        self.assertEqual(rows[0][13], f'media of {DATA_LIBRARY}/{SNAPSHOTS}/TAB-1.png named TAB-1.png')
        self.assertEqual(source, f'{LIBRARY}/{TABS}\n{DATA_LIBRARY}/{TABS}')
        self.assertIn('3 tab(s) across 2 SafariTabs.db file(s); 3 tab(s) held by a second copy', log[0])
        _headers, rows, source, log = self._run(safaribrowsing.safariTabSnapshots)
        self.assertEqual([(row[3], row[4], row[-1]) for row in rows],
                         [('TAB-1', 'Yes', f'{LIBRARY}/{SNAPSHOTS}/Metadata.db')])
        self.assertIn('1 snapshot(s) across 2 Metadata.db file(s); 1 snapshot(s) held by a second', log[0])

    def test_an_image_held_under_both_views_is_taken_from_the_copy_under_users(self):
        for library in (LIBRARY, DATA_LIBRARY):
            self._tabs(library)
            self._snapshots(library, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/')])
            self._image(library, 'TAB-1.png')
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabs)
        self.assertEqual(rows[0][13], f'media of {LIBRARY}/{SNAPSHOTS}/TAB-1.png named TAB-1.png')

    def test_a_folder_that_names_itself_as_parent_does_not_loop(self):
        loop = (2, 2, 1, 'Loop', None, 0, 'GROUP', 0, None, None)
        self._tabs(LIBRARY, rows=(loop, FIRST), active=None)
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabs)
        self.assertEqual([(row[2], row[4]) for row in rows], [('One', 'Loop')])

    def test_a_record_only_one_copy_holds_is_still_reported(self):
        self._tabs(LIBRARY)
        third = (7, 2, 0, 'Three', 'https://three.example/', 3, 'TAB-4', 0, _extra(), _local(2))
        self._tabs(DATA_LIBRARY, rows=ROWS + (third,), active=5)
        self._snapshots(LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/')])
        self._snapshots(DATA_LIBRARY, [('TAB-1', CREATED, 'TAB-1.png', 'https://one.example/'),
                                       ('TAB-4', CREATED, 'TAB-4.png', 'https://three.example/')])
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabs)
        # The active tab differs in the second copy, so tabs 1 and 2 differ there and are reported
        # from both; the unchanged third row is reported once.
        self.assertEqual([(row[11], row[5], row[-1].startswith('System/')) for row in rows], [
            ('TAB-1', 'Yes', False), ('TAB-2', '', False), ('TAB-3', '', False),
            ('TAB-1', '', True), ('TAB-2', 'Yes', True), ('TAB-4', '', True)])
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabSnapshots)
        self.assertEqual(sorted((row[3], row[4], row[-1].startswith('System/')) for row in rows),
                         [('TAB-1', 'Yes', False), ('TAB-4', 'Yes', True)])

    def test_a_plist_with_a_date_python_cannot_hold_is_still_read(self):
        # A binary plist whose LastAccessDate is 63,114,076,800 seconds before 2001, a date
        # before year 1 that plistlib refuses.
        marker = datetime.datetime(2001, 1, 2)
        blob = plistlib.dumps({'DateClosed': CLOSED, 'WindowUUID': 'WINDOW-9', 'TabIndex': 7,
                               'LastAccessDate': marker}, fmt=getattr(plistlib, 'FMT_BINARY'))
        stored = b'\x33' + struct.pack('>d', 86400.0)
        self.assertEqual(blob.count(stored), 1)
        blob = blob.replace(stored, b'\x33' + struct.pack('>d', -63114076800.0))
        with self.assertRaises(Exception):
            plistlib.loads(blob)
        self.assertEqual(safaribrowsing._loads_plist(blob),  # pylint: disable=protected-access
                         {'DateClosed': CLOSED, 'WindowUUID': 'WINDOW-9', 'TabIndex': 7,
                          'LastAccessDate': -63114076800.0})
        row = (4, 2, 0, 'One', 'https://one.example/', 1, 'TAB-1', 0, _extra(), blob)
        self._tabs(LIBRARY, rows=(ROOT, GROUP, row))
        _headers, rows, _source, log = self._run(safaribrowsing.safariTabs)
        self.assertEqual([(row[1], row[6], row[7]) for row in rows], [(CLOSED_UTC, 'WINDOW-9', 7)])
        self.assertIn('0 attribute value(s) were not a plist dictionary', log[0])

    def test_an_attribute_value_that_is_not_a_plist_dictionary_is_counted(self):
        row = (4, 2, 0, 'One', 'https://one.example/', 1, 'TAB-1', 0, b'not a plist', plistlib.dumps([1, 2]))
        self._tabs(LIBRARY, rows=(ROOT, GROUP, row))
        _headers, rows, _source, log = self._run(safaribrowsing.safariTabs)
        self.assertEqual([(row[0], row[2], row[6], row[11]) for row in rows], [(None, 'One', '', 'TAB-1')])
        self.assertIn('2 attribute value(s) were not a plist dictionary and were not read.', log[0])

    def test_a_database_with_fewer_columns_or_none_of_the_tables(self):
        self._tabs(LIBRARY, old=True)
        _headers, rows, _source, _log = self._run(safaribrowsing.safariTabs)
        self.assertEqual([(row[2], row[4], row[5], row[10], row[11]) for row in rows],
                         [('One', 'Root/Cars', '', '', ''), ('Two', 'Root/Cars', '', '', ''),
                          ('Kept', 'Root/Cars/TopScopedBookmarkList', '', '', '')])
        self.files = []
        self._tabs(LIBRARY.replace('someone', 'third'), tables=False)
        self._snapshots(LIBRARY.replace('someone', 'third'), [], columns=False)
        third = LIBRARY.replace('someone', 'third')
        _headers, rows, source, log = self._run(safaribrowsing.safariTabs)
        self.assertEqual((rows, source), ([], f'{third}/{TABS}'))
        self.assertEqual(log[:2], [
            f'Safari Tab Snapshots: {third}/{SNAPSHOTS}/Metadata.db lacks the snapshot_metadata columns '
            'and was not read.',
            f'Safari Tabs: {third}/{TABS} lacks the bookmarks columns and was not read.'])
        _headers, rows, source, _log = self._run(safaribrowsing.safariTabSnapshots)
        self.assertEqual((rows, source), ([], f'{third}/{SNAPSHOTS}/Metadata.db'))

    def test_a_metadata_database_outside_a_tab_snapshots_folder_is_not_read(self):
        database = sqlite3.connect(self._path(f'{LIBRARY}/Caches/Other/Metadata.db'))
        database.execute(SNAPSHOT_METADATA)
        database.execute("INSERT INTO snapshot_metadata VALUES ('X', 1.0, 'X.png', 'https://x.example/')")
        database.commit()
        database.close()
        _headers, rows, source, _log = self._run(safaribrowsing.safariTabSnapshots)
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
