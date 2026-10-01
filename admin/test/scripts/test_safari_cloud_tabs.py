"""Pin what the Safari iCloud Tabs and iCloud Tab Devices artifacts read from CloudTabs.db.

The tested macOS 11.2.1 database has no cloud_tabs.last_viewed_time and no
cloud_tab_devices.device_type_identifier column; the tested macOS 15.4 database has both, and
holds a device that no tab names. Both layouts are read: a column the database lacks shows a
blank, a device with no tab is listed by Safari iCloud Tab Devices with a tab count of 0, and a
database held under Users/ and again under System/Volumes/Data/Users/ is read as one store.

Every value here is written for the test. The two CREATE TABLE statements of each layout are
the text Safari wrote on the tested images; the expected rows are written out, never read back
from the module.
"""
import datetime
import pathlib
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

USER = 'Users/someone/Library/Safari/CloudTabs.db'
DATA_VIEW = 'System/Volumes/Data/Users/someone/Library/Safari/CloudTabs.db'
OTHER_USER = 'Users/another/Library/Safari/CloudTabs.db'

OLD_TABLES = (
    'CREATE TABLE cloud_tab_devices (device_uuid TEXT PRIMARY KEY NOT NULL,system_fields BLOB NOT NULL,'
    'device_name TEXT,has_duplicate_device_name BOOLEAN DEFAULT 0,is_ephemeral_device BOOLEAN DEFAULT 0,'
    'last_modified REAL NOT NULL)',
    'CREATE TABLE cloud_tabs (tab_uuid TEXT PRIMARY KEY NOT NULL,system_fields BLOB NOT NULL,'
    'device_uuid TEXT NOT NULL,position BLOB NOT NULL,title TEXT,url TEXT NOT NULL,'
    'is_showing_reader BOOLEAN DEFAULT 0,is_pinned BOOLEAN DEFAULT 0,'
    'reader_scroll_position_page_index INTEGER,scene_id TEXT)',
)
NEW_TABLES = (
    'CREATE TABLE cloud_tab_devices (device_uuid TEXT PRIMARY KEY NOT NULL,system_fields BLOB NOT NULL,'
    'device_name TEXT,device_type_identifier TEXT,has_duplicate_device_name BOOLEAN DEFAULT 0,'
    'is_ephemeral_device BOOLEAN DEFAULT 0,last_modified REAL NOT NULL)',
    'CREATE TABLE cloud_tabs (tab_uuid TEXT PRIMARY KEY NOT NULL,system_fields BLOB NOT NULL,'
    'device_uuid TEXT NOT NULL,position BLOB NOT NULL,title TEXT,url TEXT NOT NULL,'
    'is_showing_reader BOOLEAN DEFAULT 0,is_pinned BOOLEAN DEFAULT 0,'
    'reader_scroll_position_page_index INTEGER,scene_id TEXT,last_viewed_time REAL DEFAULT 0)',
)

# 700000000 seconds after 2001-01-01 is 2023-03-08 20:26:40 UTC.
MODIFIED = datetime.datetime(2023, 3, 8, 20, 26, 40, tzinfo=datetime.timezone.utc)
LATER = datetime.datetime(2023, 3, 8, 20, 28, 20, tzinfo=datetime.timezone.utc)
VIEWED = datetime.datetime(2023, 3, 8, 20, 25, 0, tzinfo=datetime.timezone.utc)

# device_uuid, device_name, device_type_identifier, has_duplicate_device_name, is_ephemeral_device,
# last_modified
PHONE = ('DEVICE-1', 'A phone', 'type.phone', 0, 1, 700000000.0)
LAPTOP = ('DEVICE-2', 'A laptop', 'type.laptop', 1, 0, 700000100.0)
# tab_uuid, device_uuid, title, url, is_showing_reader, is_pinned, page index, last_viewed_time
SEEN_TAB = ('TAB-1', 'DEVICE-1', 'One', 'https://one.example/', 1, 1, 3, 699999900.0)
UNSEEN_TAB = ('TAB-2', 'DEVICE-1', 'Two', 'https://two.example/', 0, 0, None, 0)


class SafariCloudTabsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _database(self, relative, devices=(PHONE, LAPTOP), tabs=(SEEN_TAB, UNSEEN_TAB), new=True,
                  tables=True):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        database = sqlite3.connect(path)
        if not tables:
            database.execute('CREATE TABLE metadata (key TEXT NOT NULL UNIQUE, value)')
        elif new:
            for statement in NEW_TABLES:
                database.execute(statement)
            database.executemany(
                "INSERT INTO cloud_tab_devices VALUES (?, x'00', ?, ?, ?, ?, ?)", devices)
            database.executemany(
                "INSERT INTO cloud_tabs VALUES (?, x'00', ?, x'00', ?, ?, ?, ?, ?, NULL, ?)", tabs)
        else:
            for statement in OLD_TABLES:
                database.execute(statement)
            database.executemany(
                "INSERT INTO cloud_tab_devices VALUES (?, x'00', ?, ?, ?, ?)",
                [device[:2] + device[3:] for device in devices])
            database.executemany(
                "INSERT INTO cloud_tabs VALUES (?, x'00', ?, x'00', ?, ?, ?, ?, ?, NULL)",
                [tab[:7] for tab in tabs])
        database.commit()
        database.close()
        self.files.append(str(path))

    def _run(self, processor):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(safaribrowsing, 'logfunc') as log:
            headers, rows, source = processor.__wrapped__(context)
        return headers, rows, source, [call.args[0] for call in log.call_args_list]

    def test_a_tab_shows_when_it_was_last_viewed_and_its_device_type(self):
        self._database(USER)
        headers, rows, source, _log = self._run(safaribrowsing.safariCloudTabs)
        self.assertEqual(headers, (
            'Tab Title', 'URL', ('Last Viewed', 'datetime'), 'Device Name', 'Device Type', 'Device UUID',
            ('Device Last Modified', 'datetime'), 'Ephemeral Device', 'Pinned', 'Showing Reader',
            'Reader Scroll Page', 'Tab UUID', 'Source File'))
        self.assertEqual(rows, [
            ('One', 'https://one.example/', VIEWED, 'A phone', 'type.phone', 'DEVICE-1', MODIFIED, 'Yes',
             'Yes', 'Yes', 3, 'TAB-1', USER),
            # A stored last_viewed_time of 0 shows a blank.
            ('Two', 'https://two.example/', None, 'A phone', 'type.phone', 'DEVICE-1', MODIFIED, 'Yes',
             '', '', '', 'TAB-2', USER)])
        self.assertEqual(source, USER)

    def test_a_database_without_the_two_newer_columns_shows_blanks_for_them(self):
        self._database(USER, new=False)
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabs)
        self.assertEqual([(row[0], row[2], row[4], row[9]) for row in rows],
                         [('One', None, '', 'Yes'), ('Two', None, '', '')])
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual(rows, [(LATER, 'A laptop', '', 'DEVICE-2', 0, 'No', 'Yes', USER),
                                (MODIFIED, 'A phone', '', 'DEVICE-1', 2, 'Yes', 'No', USER)])

    def test_every_device_is_listed_with_its_tab_count_even_with_no_tab(self):
        self._database(USER)
        headers, rows, source, log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual(headers, (
            ('Last Modified', 'datetime'), 'Device Name', 'Device Type', 'Device UUID', 'Tabs',
            'Ephemeral Device', 'Duplicate Device Name', 'Source File'))
        self.assertEqual(rows, [
            (LATER, 'A laptop', 'type.laptop', 'DEVICE-2', 0, 'No', 'Yes', USER),
            (MODIFIED, 'A phone', 'type.phone', 'DEVICE-1', 2, 'Yes', 'No', USER)])
        self.assertEqual(source, USER)
        self.assertEqual(log, ['Safari iCloud Tab Devices: 2 device(s) across 1 CloudTabs.db file(s); '
                               '0 device(s) held by a second copy of a store were not reported again.'])

    def test_a_tab_whose_device_row_is_missing_shows_blank_device_columns(self):
        self._database(USER, devices=(LAPTOP,))
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabs)
        self.assertEqual([row[3:7] for row in rows], [('', '', '', None), ('', '', '', None)])
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual([(row[1], row[4]) for row in rows], [('A laptop', 0)])

    def test_a_device_with_no_stored_flag_shows_a_blank_not_a_no(self):
        self._database(USER, devices=(('DEVICE-3', 'A tablet', None, None, None, 700000000.0),), tabs=())
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual(rows, [(MODIFIED, 'A tablet', '', 'DEVICE-3', 0, '', '', USER)])

    def test_devices_held_under_both_views_are_reported_once(self):
        self._database(USER)
        self._database(DATA_VIEW)
        _headers, rows, source, log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual([(row[1], row[-1]) for row in rows], [('A laptop', USER), ('A phone', USER)])
        self.assertEqual(source, f'{USER}\n{DATA_VIEW}')
        self.assertEqual(log, ['Safari iCloud Tab Devices: 2 device(s) across 2 CloudTabs.db file(s); '
                               '2 device(s) held by a second copy of a store were not reported again.'])

    def test_a_device_only_one_copy_holds_or_that_differs_is_still_reported(self):
        # The second copy holds the phone unchanged, no laptop, and no second tab, so the phone's
        # tab count differs there.
        self._database(USER)
        self._database(DATA_VIEW, devices=(PHONE,), tabs=(SEEN_TAB,))
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual([(row[1], row[4], row[-1]) for row in rows],
                         [('A laptop', 0, USER), ('A phone', 2, USER), ('A phone', 1, DATA_VIEW)])

    def test_devices_of_two_users_are_both_reported(self):
        self._database(USER)
        self._database(OTHER_USER)
        _headers, rows, _source, _log = self._run(safaribrowsing.safariCloudTabDevices)
        self.assertEqual(sorted((row[1], row[-1]) for row in rows),
                         [('A laptop', OTHER_USER), ('A laptop', USER), ('A phone', OTHER_USER),
                          ('A phone', USER)])

    def test_a_database_without_the_tables_is_named_and_logged_not_read(self):
        self._database(USER, tables=False)
        for processor, label in ((safaribrowsing.safariCloudTabs, 'Safari iCloud Tabs'),
                                 (safaribrowsing.safariCloudTabDevices, 'Safari iCloud Tab Devices')):
            with self.subTest(label):
                _headers, rows, source, log = self._run(processor)
                self.assertEqual(rows, [])
                self.assertEqual(source, USER)
                self.assertEqual(log[0], f'{label}: {USER} lacks cloud_tabs or cloud_tab_devices and '
                                         'was not read.')


if __name__ == '__main__':
    unittest.main()
