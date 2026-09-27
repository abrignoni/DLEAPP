"""Entries in the Spotlight shortcuts files macOS keeps for each user."""

import datetime
import fnmatch
import os
import pathlib
import plistlib
import tempfile
import unittest
from unittest import mock

from scripts import macos_plists
from scripts.artifacts import macosSpotlightShortcuts

UTC = datetime.timezone.utc
V3 = 'Users/alice/Library/Group Containers/group.com.apple.spotlight/com.apple.spotlight.Shortcuts.v3'
OLD = 'Users/bob/Library/Application Support/com.apple.spotlight.Shortcuts'


def entry(name, url, used):
    return {'DISPLAY_NAME': name, 'LAST_USED': used, 'URL': url}


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class SpotlightShortcutsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # The report sits under an examiner's own Users folder, as it often does on a Mac, so a
        # user read from the staged path instead of the path in the extraction would show.
        self.root = os.path.join(self._tmp.name, 'Users', 'examiner', 'report')
        os.makedirs(self.root)
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def _plist(self, relative, value, fmt=plistlib.PlistFormat.FMT_XML):
        return self._write(relative, plistlib.dumps(value, fmt=fmt, sort_keys=False))

    def _run(self, files):
        with mock.patch.object(macosSpotlightShortcuts, 'logfunc', self.logs.append), \
                mock.patch.object(macos_plists, 'logfunc', self.logs.append):
            return macosSpotlightShortcuts.macosSpotlightShortcuts.__wrapped__(FakeContext(self.root, files))

    def test_entries_are_rows_in_file_order(self):
        path = self._plist(V3, {
            'term': entry('Terminal', '/System/Applications/Utilities/Terminal.app',
                          datetime.datetime(2025, 12, 12, 20, 45, 7)),
            'chro': entry('Google Chrome', '/Applications/Google Chrome.app',
                          datetime.datetime(2025, 12, 9, 21, 39, 54)),
        })
        headers, rows, source = self._run([path])
        self.assertEqual(headers[0], ('Last Used (UTC)', 'datetime'))
        self.assertEqual(rows, [
            (datetime.datetime(2025, 12, 12, 20, 45, 7, tzinfo=UTC), 'term', 'Terminal',
             '/System/Applications/Utilities/Terminal.app', '', 'alice', V3),
            (datetime.datetime(2025, 12, 9, 21, 39, 54, tzinfo=UTC), 'chro', 'Google Chrome',
             '/Applications/Google Chrome.app', '', 'alice', V3),
        ])
        self.assertEqual(source, path)
        self.assertEqual(self.logs, ['Spotlight Shortcuts: 2 entr(ies).'])

    def test_a_binary_file_with_another_key_and_odd_values_is_reported_as_stored(self):
        path = self._plist(OLD, {
            '': {'DISPLAY_NAME': 'Settings', 'URL': 'x-apple.systempreferences:', 'IDENTIFIER': 'com.example',
                 'EXTRA': b'\x01\x02', 'WHEN': datetime.datetime(2020, 1, 2, 3, 4, 5)},
            'bare': {'LAST_USED': datetime.datetime(2021, 5, 6, 7, 8, 9)},
        }, fmt=plistlib.PlistFormat.FMT_BINARY)
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows, [('', '', 'Settings', 'x-apple.systempreferences:',
                                 'IDENTIFIER: com.example\nEXTRA: 0102\nWHEN: 2020-01-02T03:04:05+00:00',
                                 'bob', OLD),
                                (datetime.datetime(2021, 5, 6, 7, 8, 9, tzinfo=UTC), 'bare', '', '', '', 'bob', OLD)])

    def test_values_that_are_not_entries_and_files_that_are_not_plists_are_counted(self):
        good = self._plist(V3, {'a': entry('A', '/A.app', datetime.datetime(2024, 1, 1)), 'note': 'not an entry'})
        bad = self._write(OLD, b'not a property list')
        listed = self._plist('Users/carol/Library/Application Support/com.apple.spotlight/'
                             'com.apple.spotlight.Shortcuts', ['a', 'list'])
        empty = self._plist('Users/dan/Library/Application Support/com.apple.spotlight/'
                            'com.apple.spotlight.Shortcuts.v3', {})
        _headers, rows, source = self._run([good, bad, listed, empty])
        self.assertEqual([row[1] for row in rows], ['a'])
        self.assertEqual(source, good)
        self.assertIn('Spotlight Shortcuts: 2 files that are not a property list holding a dictionary, '
                      '1 top-level values that are not an entry dictionary', self.logs)

    def test_a_byte_identical_second_capture_is_read_once(self):
        value = {'a': entry('A', '/A.app', datetime.datetime(2024, 1, 1))}
        first = self._plist(V3, value)
        second = self._plist('System/Volumes/Data/' + V3, value)
        _headers, rows, source = self._run([second, first])
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, first)

    def test_a_differing_second_capture_reports_a_shared_entry_once(self):
        shared = entry('A', '/A.app', datetime.datetime(2024, 1, 1))
        first = self._plist(V3, {'a': shared})
        second = self._plist('System/Volumes/Data/' + V3,
                             {'a': shared, 'b': entry('B', '/B.app', datetime.datetime(2024, 2, 2))})
        _headers, rows, source = self._run([first, second])
        self.assertEqual([(row[1], row[6]) for row in rows], [('a', V3), ('b', 'System/Volumes/Data/' + V3)])
        self.assertEqual(source.split('\n'), [first, second])
        self.assertIn('Spotlight Shortcuts: 1 entries the other capture of the same file also holds, '
                      'not reported again', self.logs)

    def test_the_same_entry_for_two_users_is_reported_for_each(self):
        value = {'a': entry('A', '/A.app', datetime.datetime(2024, 1, 1))}
        alice = self._plist(V3, value)
        bob = self._plist(V3.replace('alice', 'bob'), value)
        _headers, rows, _source = self._run([alice, bob])
        self.assertEqual(sorted(row[5] for row in rows), ['alice', 'bob'])

    def test_paths_reach_each_location_and_nothing_else(self):
        patterns = macosSpotlightShortcuts.__artifacts_v2__['macosSpotlightShortcuts']['paths']
        def matched(path):
            return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        for relative in (OLD, V3,
                         'Users/a/Library/Application Support/com.apple.spotlight/com.apple.spotlight.Shortcuts',
                         'Users/a/Library/Application Support/com.apple.spotlight/com.apple.spotlight.Shortcuts.v3'):
            self.assertTrue(matched('/case/' + relative), relative)
        for relative in ('Users/a/Library/Preferences/com.apple.spotlight.plist',
                         'Users/a/Library/Application Support/com.apple.spotlight/appList.dat'):
            self.assertFalse(matched('/case/' + relative), relative)


if __name__ == '__main__':
    unittest.main()
