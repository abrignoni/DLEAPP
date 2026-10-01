"""Pin what the Safari plist artifacts report from the shapes Safari's plists were found in.

RecentlyClosedTabs.plist lists entries under ClosedTabOrWindowPersistentStates. On the tested
macOS 11.2.1 file every entry's PersistentState was a window holding TabStates. On the tested
macOS 15.4 file some entries were a window and others held one tab's own keys with no
TabStates, and LastVisitTime was a date value where the macOS 11.2.1 LastSession.plist holds a
number. Both entry shapes are reported, a stored date is kept, a number is read as Mac
Absolute Time in seconds, and Private Window is blank when the window has no IsPrivateWindow
key. A plist that holds no entry is still named as read.

Every value here is written for the test; the expected rows are written out, never read back
from the module.
"""
import datetime
import pathlib
import plistlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import safaribrowsing  # pylint: disable=wrong-import-position

FOLDER = 'Users/someone/Library/Safari'
CLOSED = f'{FOLDER}/RecentlyClosedTabs.plist'
SESSION = f'{FOLDER}/LastSession.plist'

WINDOW_CLOSED = datetime.datetime(2023, 3, 9, 1, 2, 3)
TAB_CLOSED = datetime.datetime(2023, 3, 9, 1, 0, 0)
VISITED = datetime.datetime(2023, 3, 8, 20, 26, 40)
VISITED_UTC = datetime.datetime(2023, 3, 8, 20, 26, 40, tzinfo=datetime.timezone.utc)
# 700000000 seconds after 2001-01-01 is 2023-03-08 20:26:40 UTC.
VISITED_NUMBER = 700000000.0


def _tab(uuid, **more):
    return {'TabTitle': f'Title {uuid}', 'TabURL': f'https://{uuid.lower()}.example/', 'TabUUID': uuid,
            'TabIndex': 0, **more}


def _row(uuid, closed, visited, window, private, size, source):
    return (f'Title {uuid}', f'https://{uuid.lower()}.example/', closed, visited, window, uuid, 0,
            private, size, '', source)


class SafariPlistRowsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _plist(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps(value))
        self.files.append(str(path))

    def _run(self, processor):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(safaribrowsing, 'logfunc') as log:
            _headers, rows, source = processor.__wrapped__(context)
        return rows, source, [call.args[0] for call in log.call_args_list]

    def test_a_closed_tab_entry_and_a_closed_window_entry_are_both_reported(self):
        self._plist(CLOSED, {'ClosedTabOrWindowPersistentStates': [
            {'PersistentStateType': 0,
             'PersistentState': _tab('ALONE', WindowUUID='WINDOW-9', DateClosed=TAB_CLOSED,
                                     LastVisitTime=VISITED)},
            {'PersistentStateType': 1,
             'PersistentState': {'WindowUUID': 'WINDOW-1', 'DateClosed': WINDOW_CLOSED,
                                 'IsPrivateWindow': True,
                                 'TabStates': [_tab('INSIDE', WindowUUID='WINDOW-1',
                                                    LastVisitTime=VISITED_NUMBER, SessionState=b'123')]}},
        ]})
        rows, source, log = self._run(safaribrowsing.safariRecentlyClosedTabs)
        self.assertEqual(rows, [
            _row('ALONE', TAB_CLOSED, VISITED_UTC, 'WINDOW-9', '', '', CLOSED),
            _row('INSIDE', WINDOW_CLOSED, VISITED_UTC, 'WINDOW-1', 'Yes', 3, CLOSED)])
        self.assertEqual(source, CLOSED)
        self.assertEqual(log, ['Safari Recently Closed Tabs: 2 tab(s) across 1 file(s); 0 entr(ies) '
                               "held neither TabStates nor a tab's own keys and were not reported."])

    def test_an_entry_that_is_neither_a_window_nor_a_tab_is_counted_not_reported(self):
        self._plist(CLOSED, {'ClosedTabOrWindowPersistentStates': [
            {'PersistentStateType': 7, 'PersistentState': {'Something': 'else'}},
            {'PersistentStateType': 0, 'PersistentState': _tab('ALONE')},
        ]})
        rows, _source, log = self._run(safaribrowsing.safariRecentlyClosedTabs)
        self.assertEqual(rows, [_row('ALONE', None, None, '', '', '', CLOSED)])
        self.assertEqual(log, ['Safari Recently Closed Tabs: 1 tab(s) across 1 file(s); 1 entr(ies) '
                               "held neither TabStates nor a tab's own keys and were not reported."])

    def test_a_last_visit_time_is_read_as_a_stored_date_or_as_seconds_since_2001(self):
        self._plist(SESSION, {'SessionWindows': [{'WindowUUID': 'WINDOW-1', 'IsPrivateWindow': False,
                                                  'TabStates': [
            _tab('DATE', LastVisitTime=VISITED, DateClosed=TAB_CLOSED),
            _tab('NUMBER', LastVisitTime=VISITED_NUMBER, DateClosed=TAB_CLOSED, SessionState=b'1234567'),
            _tab('NEITHER', DateClosed=TAB_CLOSED)]}]})
        rows, _source, _log = self._run(safaribrowsing.safariLastSession)
        self.assertEqual(rows, [
            _row('DATE', TAB_CLOSED, VISITED_UTC, 'WINDOW-1', 'No', '', SESSION),
            _row('NUMBER', TAB_CLOSED, VISITED_UTC, 'WINDOW-1', 'No', 7, SESSION),
            _row('NEITHER', TAB_CLOSED, None, 'WINDOW-1', 'No', '', SESSION)])

    def test_private_window_is_blank_when_the_window_does_not_say(self):
        self._plist(SESSION, {'SessionWindows': [
            {'WindowUUID': 'WINDOW-1', 'DateClosed': WINDOW_CLOSED, 'TabStates': [_tab('UNSAID')]},
            {'WindowUUID': 'WINDOW-2', 'DateClosed': WINDOW_CLOSED, 'IsPrivateWindow': True,
             'TabStates': [_tab('PRIVATE')]},
            {'WindowUUID': 'WINDOW-3', 'DateClosed': WINDOW_CLOSED, 'IsPrivateWindow': False,
             'TabStates': [_tab('OPEN', DateClosed=TAB_CLOSED)]}]})
        rows, _source, _log = self._run(safaribrowsing.safariLastSession)
        self.assertEqual(rows, [
            _row('UNSAID', WINDOW_CLOSED, None, 'WINDOW-1', '', '', SESSION),
            _row('PRIVATE', WINDOW_CLOSED, None, 'WINDOW-2', 'Yes', '', SESSION),
            _row('OPEN', TAB_CLOSED, None, 'WINDOW-3', 'No', '', SESSION)])

    def test_a_top_site_without_the_built_in_key_shows_a_blank(self):
        name = f'{FOLDER}/TopSites.plist'
        self._plist(name, {'TopSites': [
            {'TopSiteTitle': 'Shipped', 'TopSiteURLString': 'https://one.example/', 'TopSiteIsBuiltIn': True},
            {'TopSiteTitle': 'Not shipped', 'TopSiteURLString': 'https://two.example/', 'TopSiteIsBuiltIn': False},
            {'TopSiteURLString': 'https://three.example/'}]})
        rows, _source, _log = self._run(safaribrowsing.safariTopSites)
        self.assertEqual(rows, [('Shipped', 'https://one.example/', 'Yes', '', name),
                                ('Not shipped', 'https://two.example/', 'No', '', name),
                                ('', 'https://three.example/', '', '', name)])

    def test_a_bookmark_shows_the_folders_above_it_and_other_nodes_are_left_out(self):
        name = f'{FOLDER}/Bookmarks.plist'

        def leaf(title, uuid):
            return {'WebBookmarkType': 'WebBookmarkTypeLeaf', 'URIDictionary': {'title': title},
                    'URLString': f'https://{uuid.lower()}.example/', 'WebBookmarkUUID': uuid}

        def folder(title, *children):
            return {'WebBookmarkType': 'WebBookmarkTypeList', 'Title': title, 'Children': list(children)}

        self._plist(name, folder(
            '',
            {'WebBookmarkType': 'WebBookmarkTypeProxy', 'Title': 'History', 'WebBookmarkUUID': 'PROXY'},
            folder('BookmarksBar', leaf('Top', 'TOP'), folder('Work', leaf('Deep', 'DEEP'))),
            folder('BookmarksMenu'),
            folder('com.apple.ReadingList', leaf('Later', 'LATER'))))
        rows, _source, _log = self._run(safaribrowsing.safariBookmarks)
        self.assertEqual(rows, [
            ('BookmarksBar', 'Top', 'https://top.example/', 'TOP', name),
            ('BookmarksBar/Work', 'Deep', 'https://deep.example/', 'DEEP', name),
            ('com.apple.ReadingList', 'Later', 'https://later.example/', 'LATER', name)])

    def test_a_plist_that_holds_no_entry_is_still_named_as_read(self):
        empty = ((safaribrowsing.safariBookmarks, 'Bookmarks.plist',
                  {'WebBookmarkType': 'WebBookmarkTypeList', 'Children': []}),
                 (safaribrowsing.safariTopSites, 'TopSites.plist', {'TopSites': []}),
                 (safaribrowsing.safariRecentlyClosedTabs, 'RecentlyClosedTabs.plist',
                  {'ClosedTabOrWindowPersistentStates': []}),
                 (safaribrowsing.safariLastSession, 'LastSession.plist', {'SessionWindows': []}))
        for processor, name, value in empty:
            with self.subTest(name):
                self.files = []
                self._plist(f'{FOLDER}/{name}', value)
                rows, source, _log = self._run(processor)
                self.assertEqual(rows, [])
                self.assertEqual(source, f'{FOLDER}/{name}')


if __name__ == '__main__':
    unittest.main()
