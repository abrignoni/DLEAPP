"""Pin the readers in scripts/artifacts/macosSavedState.py.

Every value below is authored for the test; none comes from a real device. The fixtures build
their own keyed archives and encrypt them the way the artifact's notes describe.
"""
import fnmatch
import pathlib
import plistlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

from Crypto.Cipher import AES

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosSavedState as saved  # pylint: disable=wrong-import-position

KEY_MENU, KEY_WINDOW, KEY_APP = b'm' * 16, b'w' * 16, b'a' * 16
APP_WINDOW = 0xFFFFFFFF


def keyed_archive(top):
    """An NSKeyedArchiver-shaped plist holding `top`, a dict of top-level values."""
    objects = ['$null']
    classes = {}

    def class_uid(name):
        if name not in classes:
            objects.append({'$classname': name, '$classes': [name, 'NSObject']})
            classes[name] = plistlib.UID(len(objects) - 1)
        return classes[name]

    def add(value):
        index = len(objects)
        objects.append(None)
        if isinstance(value, dict):
            objects[index] = {'NS.keys': [add(k) for k in value],
                              'NS.objects': [add(v) for v in value.values()],
                              '$class': class_uid('NSDictionary')}
        elif isinstance(value, list):
            objects[index] = {'NS.objects': [add(v) for v in value], '$class': class_uid('NSArray')}
        elif isinstance(value, bytes):
            objects[index] = {'NS.data': value, '$class': class_uid('NSMutableData')}
        else:
            objects[index] = value
        return plistlib.UID(index)

    top_uids = {key: add(value) for key, value in top.items()}
    return plistlib.dumps({'$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': top_uids,
                           '$objects': objects}, fmt=plistlib.PlistFormat.FMT_BINARY)


def record(window_id, key, identifier, archive, first=0):
    """One data.data record: header, then the AES-128-CBC ciphertext of the plaintext layout."""
    plain = (struct.pack('>II', first, len(identifier)) + identifier
             + b'rchv' + struct.pack('>I', len(archive)) + archive)
    plain += bytes(-len(plain) % 16)
    ciphertext = AES.new(key, AES.MODE_CBC, iv=bytes(16)).encrypt(plain)
    return b'NSCR1000' + struct.pack('>II', window_id, 16 + len(ciphertext)) + ciphertext


def tab_contents(*lines):
    """A Tab Contents v2 list: each text item followed by its 24-byte descriptor."""
    items = []
    for line in lines:
        items += [line, bytes(8) + struct.pack('<I', len(line)) + bytes(12)]
    return items


def terminal_archive(title, tabs):
    return keyed_archive({'TTWindowState': {'Window Settings': tabs, 'ShowsTabBar': False},
                          'NSTitle': title, 'NSClassName': 'TTWindow'})


def tab(text_items, selected=True, directory='file://example-host/Users/tester', restorable=True):
    return {'TabSelected': selected, 'Tab Session ID': 'SESSION-1',
            'Tab Working Directory URL String': directory,
            'Tab Scrollback Restorable': restorable, 'Tab Contents v2': text_items}


WINDOWS = [
    {'NSIsMainMenuBar': True, 'NSWindowID': 1, 'NSDataKey': KEY_MENU},
    {'NSTitle': 'tester — -zsh — 80×24', 'NSWindowID': 2, 'NSDataKey': KEY_WINDOW},
    {'NSIsGlobal': True, 'NSWindowID': APP_WINDOW, 'NSDataKey': KEY_APP, 'CFBundleVersion': '1'},
]


class Context:
    """The two calls the artifacts make, over a temporary tree."""

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class HelperTest(unittest.TestCase):
    def test_application_name(self):
        self.assertEqual(saved.application_name('/x/com.example.App.savedState'), 'com.example.App')
        self.assertEqual(saved.application_name('/x/com.example.App.savedState/'), 'com.example.App')
        self.assertEqual(saved.application_name('/x/Other'), 'Other')

    def test_stored_text(self):
        self.assertEqual([saved.stored_text(v) for v in (True, False, None, 3, 'x')],
                         ['Yes', 'No', '', '3', 'x'])

    def test_titled_windows_and_keys(self):
        self.assertEqual(saved.titled_windows(WINDOWS + [{'NSTitle': 'no id'}, 'not a dict',
                                                         {'NSTitle': '', 'NSWindowID': 5}]),
                         [(2, 'tester — -zsh — 80×24'), ('', 'no id'), (5, '')])
        self.assertEqual(saved.titled_windows({'NSTitle': 'x'}), [])
        self.assertEqual(saved.data_keys(WINDOWS + [{'NSWindowID': 9, 'NSDataKey': b'short'},
                                                    {'NSWindowID': '10', 'NSDataKey': KEY_APP}]),
                         {1: KEY_MENU, 2: KEY_WINDOW, APP_WINDOW: KEY_APP})
        self.assertEqual(saved.data_keys(None), {})

    def test_split_records(self):
        one = record(2, KEY_WINDOW, b'_NSWindow', b'x')
        two = record(3, KEY_WINDOW, b'_NSWindow', b'y' * 40)
        records, problem = saved.split_records(one + two)
        self.assertEqual(problem, '')
        self.assertEqual([(offset, window) for offset, window, _ in records], [(0, 2), (len(one), 3)])
        self.assertEqual(records[1][2], two[16:])
        self.assertEqual(saved.split_records(one + two[:10])[1],
                         f'the 10 bytes at offset {len(one)} are too few for a record')
        self.assertEqual(saved.split_records(one + b'NSCR0006' + two[8:])[1],
                         f'the record at offset {len(one)} does not start with NSCR1000')
        self.assertEqual(saved.split_records(one + two[:-16])[1],
                         f'the record at offset {len(one)} gives a length of {len(two)}, past the end')
        self.assertEqual(saved.split_records(b'NSCR1000' + struct.pack('>II', 2, 15))[1],
                         'the record at offset 0 gives a length of 15, past the end')

    def test_decrypt_record(self):
        archive = keyed_archive({'NSTitle': 'x'})
        ciphertext = record(2, KEY_WINDOW, b'_NSWindow', archive, first=2)[16:]
        self.assertEqual(saved.decrypt_record(KEY_WINDOW, ciphertext),
                         ('_NSWindow', [('rchv', archive)]))
        self.assertIsNone(saved.decrypt_record(KEY_APP, ciphertext))
        self.assertIsNone(saved.decrypt_record(KEY_WINDOW, ciphertext[:-1]))
        self.assertIsNone(saved.decrypt_record(KEY_WINDOW, b''))
        overlong = AES.new(KEY_WINDOW, AES.MODE_CBC, iv=bytes(16)).encrypt(
            struct.pack('>II', 0, 1000) + b'A' * 8)
        self.assertIsNone(saved.decrypt_record(KEY_WINDOW, overlong))

    def test_decrypt_record_reads_every_value(self):
        plain = (struct.pack('>II', 0, 3) + b'Doc' + b'rchv' + struct.pack('>I', 2) + b'ab'
                 + b'surl' + struct.pack('>I', 1) + b'c')
        plain += bytes(-len(plain) % 16)
        ciphertext = AES.new(KEY_WINDOW, AES.MODE_CBC, iv=bytes(16)).encrypt(plain)
        self.assertEqual(saved.decrypt_record(KEY_WINDOW, ciphertext),
                         ('Doc', [('rchv', b'ab'), ('surl', b'c')]))

    def test_padding_and_an_overlong_value_end_the_values(self):
        for tail in (b'rchv' + struct.pack('>I', 99) + b'short', bytes(16)):
            plain = struct.pack('>II', 0, 3) + b'Doc' + b'kyds' + struct.pack('>I', 1) + b'k' + tail
            plain += bytes(-len(plain) % 16)
            ciphertext = AES.new(KEY_WINDOW, AES.MODE_CBC, iv=bytes(16)).encrypt(plain)
            self.assertEqual(saved.decrypt_record(KEY_WINDOW, ciphertext), ('Doc', [('kyds', b'k')]))

    def test_archive_of(self):
        archive = keyed_archive({'NSTitle': 'x'})
        self.assertEqual(saved.archive_of([('kyds', b'no'), ('rchv', archive)])['$archiver'],
                         'NSKeyedArchiver')
        self.assertIsNone(saved.archive_of([('rchv', b'not a plist')]))
        self.assertIsNone(saved.archive_of([('rchv', plistlib.dumps([1]))]))
        self.assertIsNone(saved.archive_of([('kyds', archive)]))

    def test_terminal_window(self):
        archive = plistlib.loads(terminal_archive('Title', [tab(tab_contents(b'a\n')), 'bad']))
        title, tabs = saved.terminal_window(archive)
        self.assertEqual((title, len(tabs), tabs[0]['Tab Session ID']), ('Title', 1, 'SESSION-1'))
        self.assertIsNone(saved.terminal_window(plistlib.loads(keyed_archive({'NSTitle': 'x'}))))
        self.assertEqual(saved.terminal_window(plistlib.loads(keyed_archive(
            {'TTWindowState': {'Window Settings': 'odd'}}))), ('', []))
        self.assertIsNone(saved.terminal_window(plistlib.loads(keyed_archive({'TTWindowState': 'x'}))))

    def test_saved_text(self):
        self.assertEqual(saved.saved_text(tab_contents(b'Last login\n', b'$ ls\n', b'\n')),
                         'Last login\n$ ls\n\n')
        self.assertEqual(saved.saved_text(tab_contents('café\n'.encode('utf-8'))), 'café\n')
        good = tab_contents(b'abc')
        self.assertIsNone(saved.saved_text(good[:1]))
        self.assertIsNone(saved.saved_text([b'abc', good[1][:23]]))
        self.assertIsNone(saved.saved_text([b'abcd', good[1]]))
        self.assertIsNone(saved.saved_text(['abc', good[1]]))
        self.assertIsNone(saved.saved_text([b'abc', 'x' * 24]))
        several = bytes(range(1, 25)) + bytes(8) + struct.pack('<I', 99) + bytes(12)
        self.assertEqual(saved.saved_text([b'$ styled\n', several] + tab_contents(b'\n')), '$ styled\n\n')
        self.assertIsNone(saved.saved_text([b'abc', b'']))
        self.assertIsNone(saved.saved_text([b'abc', good[1] + b'x']))
        self.assertIsNone(saved.saved_text([b'abc', several[:47]]))
        self.assertIsNone(saved.saved_text('abc'))
        self.assertEqual(saved.saved_text([]), '')


class DeclaredPathsTest(unittest.TestCase):
    """Every file an artifact opens must match one of its own declared paths, or no seeker stages it."""

    def test_each_artifact_declares_the_files_it_reads(self):
        state = '/case/data/Users/tester/Library/Daemon Containers/C/Data/Library/Saved Application State'
        needed = {'macosSavedStateWindows': ['UUID.savedState/windows.plist', 'ApplicationMapping.plist'],
                  'macosTerminalSavedState': ['UUID.savedState/windows.plist', 'UUID.savedState/data.data',
                                              'ApplicationMapping.plist']}
        for key, files in needed.items():
            patterns = saved.__artifacts_v2__[key]['paths']
            for name in files:
                self.assertTrue(any(fnmatch.fnmatch(f'{state}/{name}', p) for p in patterns), (key, name))


class ApplicationMappingTest(unittest.TestCase):
    def test_mapping_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)/'ApplicationMapping.plist'
            path.write_bytes(plistlib.dumps([
                'LEADING',
                {'protected': {'hasPlatformStatus': False, 'signingIdentifier': 'com.example.Signed',
                               'teamIdentifier': 'TEAMID'}}, 'UUID-1',
                {'unprotected': {'bundleIdentifier': 'com.example.Bundle'}}, 'UUID-2',
                {'other': {'signingIdentifier': 'com.example.Other'}}, 'UUID-3',
                {'protected': {'signingIdentifier': 5}}, 'UUID-4',
                {'protected': {}, 'unprotected': {'bundleIdentifier': 'com.example.Second'}}, 'UUID-5',
                {'protected': 'flat'}, 'UUID-6',
                {'protected': {'signingIdentifier': 'com.example.Orphan'}},
                {'protected': {'signingIdentifier': 'com.example.First'},
                 'unprotected': {'bundleIdentifier': 'com.example.Ignored'}}, 'UUID-8',
                'UUID-7']))
            self.assertEqual(saved.application_mapping(path), {
                'UUID-1': 'com.example.Signed', 'UUID-2': 'com.example.Bundle',
                'UUID-5': 'com.example.Second', 'UUID-8': 'com.example.First'})
            path.write_bytes(plistlib.dumps({'UUID-1': 'x'}))
            self.assertIsNone(saved.application_mapping(path))
            path.write_bytes(b'not a plist')
            self.assertIsNone(saved.application_mapping(path))


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        patcher = patch.object(saved, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)

    def folder(self, relative, windows, data=None):
        folder = self.root/relative
        folder.mkdir(parents=True)
        (folder/'windows.plist').write_bytes(plistlib.dumps(windows, fmt=plistlib.PlistFormat.FMT_BINARY))
        files = [folder/'windows.plist']
        if data is not None:
            (folder/'data.data').write_bytes(data)
            files.append(folder/'data.data')
        return folder, files

    def test_windows_and_terminal_rows(self):
        state = pathlib.Path('Users', 'tester', 'Library', 'Saved Application State')
        old = record(2, KEY_WINDOW, b'_NSWindow',
                     terminal_archive('old title', [tab(tab_contents(b'first\n'))]))
        app = record(APP_WINDOW, KEY_APP, b'_NSApplication', keyed_archive({'NSWindowZOrder': [2]}))
        orphan = record(7, KEY_WINDOW, b'_NSWindow', b'x')
        new = record(2, KEY_WINDOW, b'_NSWindow', terminal_archive('new title', [
            tab(tab_contents(b'first\n', b'$ whoami\n')),
            tab([b'broken'], selected=False, directory='file://example-host/tmp', restorable=False)]))
        data = old + app + orphan + new
        terminal, terminal_files = self.folder(state/'com.apple.Terminal.savedState', WINDOWS, data)
        copy, copy_files = self.folder(pathlib.Path('System', 'Volumes', 'Data')/state/'com.apple.Terminal.savedState',
                                       WINDOWS, data)
        _other, other_files = self.folder(state/'com.example.Other.savedState', [{'NSWindowID': APP_WINDOW,
                                                                                  'NSDataKey': KEY_APP}], app)
        (self.root/state/'com.example.Dir.savedState'/'windows.plist').mkdir(parents=True)
        other_files.append(self.root/state/'com.example.Dir.savedState'/'windows.plist')
        _bad, bad_files = self.folder(state/'com.example.Bad.savedState', {'not': 'a list'})
        files = terminal_files + copy_files + other_files + bad_files

        headers, rows, source = saved.macosSavedStateWindows.__wrapped__(Context(self.root, files))
        self.assertEqual(headers, ('User', 'Application', 'Window ID', 'Window Title', 'State Folder'))
        self.assertEqual(rows, [('tester', 'com.apple.Terminal', 2, 'tester — -zsh — 80×24',
                                 str(state/'com.apple.Terminal.savedState'))])
        self.assertNotIn(str(copy), source)
        self.assertEqual(self.logged, [f'Saved Application State Windows: {state}/com.example.Bad.savedState/'
                                       'windows.plist is not a plist array'])

        self.logged.clear()
        headers, rows, source = saved.macosTerminalSavedState.__wrapped__(Context(self.root, files))
        self.assertEqual(headers[:4], ('User', 'Application', 'Window ID', 'Window Title'))
        by_header = [dict(zip(headers, row)) for row in rows]
        new_offset = len(old) + len(app) + len(orphan)
        self.assertEqual([(r['Window Title'], r['Tab'], r['Saved Text'], r['Latest Record'], r['Record Offset'])
                          for r in by_header],
                         [('old title', 1, 'first\n', 'No', 0),
                          ('new title', 1, 'first\n$ whoami\n', 'Yes', new_offset),
                          ('new title', 2, '', 'Yes', new_offset)])
        first, second = by_header[1], by_header[2]
        self.assertEqual((first['User'], first['Application'], first['Window ID']),
                         ('tester', 'com.apple.Terminal', 2))
        self.assertEqual((first['Tab Selected'], first['Working Directory URL'],
                          first['Tab Scrollback Restorable'], first['Tab Session ID']),
                         ('Yes', 'file://example-host/Users/tester', 'Yes', 'SESSION-1'))
        self.assertEqual((second['Tab Selected'], second['Working Directory URL'],
                          second['Tab Scrollback Restorable']),
                         ('No', 'file://example-host/tmp', 'No'))
        self.assertEqual(first['State Folder'], str(state/'com.apple.Terminal.savedState'))
        self.assertEqual(source.split('\n'), [str(terminal/'windows.plist'), str(terminal/'data.data')])
        self.assertEqual(self.logged, [
            f'Terminal Saved State: {state}/com.apple.Terminal.savedState/data.data: 1 record(s) for '
            'a window windows.plist holds no key for and 0 that did not decrypt, not read',
            f'Terminal Saved State: {state}/com.apple.Terminal.savedState/data.data: the Tab Contents '
            f'v2 of tab 2 in the record at offset {new_offset} does not follow the text and '
            'descriptor layout, so Saved Text is left blank',
        ])

    def test_folders_named_by_uuid_take_the_mapped_identifier(self):
        state = pathlib.Path('Users', 'tester', 'Library', 'Daemon Containers', 'CONTAINER', 'Data', 'Library',
                             'Saved Application State')
        (self.root/state).mkdir(parents=True)
        mapping = self.root/state/'ApplicationMapping.plist'
        mapping.write_bytes(plistlib.dumps([
            {'protected': {'signingIdentifier': 'com.apple.Terminal', 'teamIdentifier': ''}}, 'UUID-T',
            {'unprotected': {'bundleIdentifier': 'com.example.Editor'}}, 'UUID-E']))
        terminal_data = record(2, KEY_WINDOW, b'_NSWindow', terminal_archive('title', [tab(tab_contents(b'a'))]))
        _t, terminal = self.folder(state/'UUID-T.savedState', WINDOWS, terminal_data)
        _e, editor = self.folder(state/'UUID-E.savedState', [{'NSTitle': 'Report', 'NSWindowID': 3}])
        _u, unmapped = self.folder(state/'UUID-U.savedState', [{'NSTitle': 'Other', 'NSWindowID': 4}])
        other = pathlib.Path('Users', 'tester', 'Library', 'Saved Application State')
        (self.root/other).mkdir(parents=True)
        (self.root/other/'ApplicationMapping.plist').write_bytes(plistlib.dumps({'not': 'an array'}))
        _o, legacy = self.folder(other/'com.example.Legacy.savedState', [{'NSTitle': 'Legacy', 'NSWindowID': 5}])
        files = terminal + editor + unmapped + legacy + [mapping, self.root/other/'ApplicationMapping.plist']

        _headers, rows, source = saved.macosSavedStateWindows.__wrapped__(Context(self.root, files))
        self.assertEqual(sorted((row[1], row[3]) for row in rows), [
            ('UUID-U', 'Other'), ('com.apple.Terminal', 'tester — -zsh — 80×24'),
            ('com.example.Editor', 'Report'), ('com.example.Legacy', 'Legacy')])
        self.assertEqual({row[0] for row in rows}, {'tester'})
        self.assertEqual(source.split('\n').count(str(mapping)), 1)
        self.assertEqual(self.logged, [
            f'Saved Application State Windows: {other}/ApplicationMapping.plist is not a plist array, so the '
            'folders beside it keep their own names'])

        self.logged.clear()
        _headers, rows, source = saved.macosTerminalSavedState.__wrapped__(Context(self.root, files))
        self.assertEqual([(row[1], row[3], row[7]) for row in rows], [('com.apple.Terminal', 'title', 'a')])
        self.assertEqual(source.split('\n'), [str(self.root/state/'UUID-T.savedState'/'windows.plist'),
                                               str(self.root/state/'UUID-T.savedState'/'data.data'), str(mapping)])

    def test_a_mapping_is_cited_only_for_rows_it_named(self):
        state = pathlib.Path('Users', 'tester', 'Library', 'Saved Application State')
        (self.root/state).mkdir(parents=True)
        mapping = self.root/state/'ApplicationMapping.plist'
        mapping.write_bytes(plistlib.dumps([{'unprotected': {'bundleIdentifier': 'com.example.Quiet'}}, 'UUID-Q']))
        _q, quiet = self.folder(state/'UUID-Q.savedState', [{'NSWindowID': 1}])
        _n, named = self.folder(state/'com.example.Named.savedState', [{'NSTitle': 'x', 'NSWindowID': 2}])
        _headers, rows, source = saved.macosSavedStateWindows.__wrapped__(
            Context(self.root, quiet + named + [mapping]))
        self.assertEqual([row[1] for row in rows], ['com.example.Named'])
        self.assertNotIn(str(mapping), source.split('\n'))

    def test_copies_that_differ_are_both_read(self):
        state = pathlib.Path('Users', 'tester', 'Library', 'Saved Application State')
        _live, live = self.folder(state/'com.apple.Terminal.savedState', WINDOWS,
                                  record(2, KEY_WINDOW, b'_NSWindow', terminal_archive('a', [tab([])])))
        _copy, copy = self.folder(pathlib.Path('System', 'Volumes', 'Data')/state/'com.apple.Terminal.savedState',
                                  WINDOWS, record(2, KEY_WINDOW, b'_NSWindow', terminal_archive('b', [tab([])])))
        _headers, rows, _source = saved.macosTerminalSavedState.__wrapped__(Context(self.root, live + copy))
        self.assertEqual([row[3] for row in rows], ['a', 'b'])
        _headers, rows, _source = saved.macosSavedStateWindows.__wrapped__(Context(self.root, live + copy))
        self.assertEqual(len(rows), 1)

    def test_a_short_file_and_a_wrong_key(self):
        state = pathlib.Path('Users', 'tester', 'Library', 'Saved Application State')
        good = record(2, KEY_WINDOW, b'_NSWindow', terminal_archive('title', [tab(tab_contents(b'a'))]))
        stale = record(2, KEY_APP, b'_NSWindow', terminal_archive('stale', [tab(tab_contents(b'b'))]))
        _folder, files = self.folder(state/'com.apple.Terminal.savedState', WINDOWS, good + stale + b'NSCR')
        _headers, rows, _source = saved.macosTerminalSavedState.__wrapped__(Context(self.root, files))
        self.assertEqual([(row[3], row[7], row[10]) for row in rows], [('title', 'a', 'Yes')])
        self.assertEqual(self.logged, [
            f'Terminal Saved State: {state}/com.apple.Terminal.savedState/data.data: the 4 bytes at '
            f'offset {len(good) + len(stale)} are too few for a record; the rest is not read',
            f'Terminal Saved State: {state}/com.apple.Terminal.savedState/data.data: 0 record(s) for '
            'a window windows.plist holds no key for and 1 that did not decrypt, not read',
        ])


if __name__ == '__main__':
    unittest.main()
