"""Firefox session store reader cases; every block and state is built by hand for the test."""

import fnmatch
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox_session as fs  # pylint: disable=wrong-import-position


def literal_block(data):
    """An LZ4 block made of one literal-only sequence, as the block format describes it."""
    count = len(data)
    token = min(count, 15) << 4
    out = bytearray([token])
    if count >= 15:
        rest = count - 15
        while rest >= 255:
            out.append(255)
            rest -= 255
        out.append(rest)
    return bytes(out) + data


def mozlz4(data):
    return fs.MOZLZ4_MAGIC + len(data).to_bytes(4, 'little') + literal_block(data)


def ms(year, month, day):
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)


class Lz4BlockTest(unittest.TestCase):

    def test_literals_overlapping_match_and_long_lengths(self):
        self.assertEqual(fs.lz4_block_decompress(b'\x50hello', 5), b'hello')
        # 3 literals, then offset 3 with match code 5 (9 bytes) copying over itself.
        block = b'\x35abc\x03\x00' + b'\x50hello'
        self.assertEqual(fs.lz4_block_decompress(block, 17), b'abc' * 4 + b'hello')
        long = bytes(range(256)) + bytes(24)          # 280 bytes: 15, then 255, then 10
        self.assertEqual(literal_block(long)[:3], b'\xf0\xff\x0a')
        self.assertEqual(fs.lz4_block_decompress(literal_block(long), 280), long)
        # match length 19 + 1 extension byte of 3 = 22 bytes from a 1-byte offset
        self.assertEqual(fs.lz4_block_decompress(b'\x1fa\x01\x00\x03' + b'\x50hello', 28),
                         b'a' * 23 + b'hello')

    def test_malformed_blocks_are_refused(self):
        for block, size in ((b'\x35abc\x00\x00\x50hello', 17),     # offset 0
                            (b'\x35abc\x09\x00\x50hello', 17),     # offset before the output
                            (b'\x50hel', 5),                       # truncated literals
                            (b'\x35abc\x03', 17),                  # truncated offset
                            (b'\xf0', 20),                         # truncated length
                            (b'\x50hello', 6),                     # shorter than declared
                            (b'\x35abc\x03\x00\x50hello', 10)):    # past the declared size
            with self.assertRaises(ValueError):
                fs.lz4_block_decompress(block, size)
        with self.assertRaises(TypeError):
            fs.lz4_block_decompress(4096, 4096)

    def test_mozlz4_header(self):
        self.assertEqual(fs.mozlz4_decompress(mozlz4(b'{"a":1}')), b'{"a":1}')
        self.assertEqual(fs.mozlz4_decompress(fs.MOZLZ4_MAGIC + bytes(4)), b'')
        with self.assertRaises(ValueError):
            fs.mozlz4_decompress(b'mozLz41\x00' + bytes(4) + b'\x00')


def tab(url, accessed, index=1, **extra):
    state = {'entries': [{'url': url + '/1', 'title': 'one', 'hasUserInteraction': False},
                         {'url': url + '/2', 'title': 'two', 'originalURI': url + '/0'}],
             'index': index, 'lastAccessed': accessed, 'userContextId': 0, 'hidden': False}
    state.update(extra)
    return state


STATE = {
    'session': {'lastUpdate': ms(2026, 3, 1)},
    'windows': [{'tabs': [tab('https://open.test', ms(2026, 2, 1), index=2, groupId='g1', pinned=True)],
                 'groups': [{'id': 'g1', 'name': 'Research'}],
                 '_closedTabs': [{'closedAt': ms(2026, 2, 2), 'state': tab('https://closed.test', ms(2026, 2, 1))}],
                 'closedGroups': [{'name': 'Old group', 'closedAt': ms(2026, 2, 3),
                                   'tabs': [{'closedAt': ms(2026, 2, 3),
                                             'state': tab('https://group.test', ms(2026, 1, 1))}]}]}],
    '_closedWindows': [{'closedAt': ms(2026, 2, 4),
                        'tabs': [tab('https://closedwin.test', ms(2026, 1, 2))],
                        '_closedTabs': [{'closedAt': ms(2026, 1, 3),
                                         'state': tab('https://closedwintab.test', ms(2026, 1, 1))}]}],
    'savedGroups': [{'name': 'Saved', 'closedAt': ms(2026, 2, 5),
                     'tabs': [{'state': tab('https://saved.test', ms(2026, 1, 4))}]}],
    'lastSessionState': {'session': {'lastUpdate': ms(2025, 12, 1)},
                         'windows': [{'tabs': [tab('https://last.test', ms(2025, 11, 1))]}],
                         'lastSessionState': {'windows': [{'tabs': [tab('https://nested.test', 1)]}]}},
}


class SessionRowsTest(unittest.TestCase):

    def test_every_scope_times_positions_and_groups(self):
        rows = list(fs.session_rows(STATE))
        scopes = [row[3] for row in rows]
        self.assertEqual(scopes, [s for s in ('Open tab', 'Closed tab', 'Tab in closed group',
                                              'Tab in closed window', 'Closed tab in closed window',
                                              'Tab in saved group', 'Last session: Open tab')
                                  for _ in range(2)])
        self.assertNotIn('nested', ' '.join(row[8] for row in rows))   # one level only
        first, second = rows[0], rows[1]
        self.assertEqual(first[0], datetime(2026, 2, 1, tzinfo=timezone.utc))
        self.assertEqual((first[1], first[2]), ('', datetime(2026, 3, 1, tzinfo=timezone.utc)))
        self.assertEqual([r[7] for r in (first, second)], ['No', 'Yes'])
        self.assertEqual(second[8:12], ('https://open.test/2', 'two', 'https://open.test/0', ''))
        self.assertEqual(first[11:16], ('False', '0', 'True', 'False', 'Research'))
        by_scope = {row[3]: row for row in rows}
        self.assertEqual(by_scope['Closed tab'][1], datetime(2026, 2, 2, tzinfo=timezone.utc))
        self.assertEqual(by_scope['Tab in closed window'][1], datetime(2026, 2, 4, tzinfo=timezone.utc))
        self.assertEqual(by_scope['Closed tab in closed window'][1], datetime(2026, 1, 3, tzinfo=timezone.utc))
        self.assertEqual(by_scope['Tab in closed group'][15], 'Old group')
        self.assertEqual(by_scope['Tab in saved group'][1:5:3], (datetime(2026, 2, 5, tzinfo=timezone.utc), ''))
        self.assertEqual(by_scope['Last session: Open tab'][2], datetime(2025, 12, 1, tzinfo=timezone.utc))

    def test_malformed_parts_yield_nothing_rather_than_fail(self):
        self.assertEqual(list(fs.session_rows({'windows': 'x', '_closedWindows': [1, None],
                                               'savedGroups': [{'tabs': [{'state': 'x'}]}]})), [])


class ReadSessionStoreTest(unittest.TestCase):

    def test_files_profiles_and_unreadable_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            profile = root/'Users'/'tester'/'Library'/'Application Support'/'Firefox'/'Profiles'/'ab12.default-release'
            (profile/'sessionstore-backups').mkdir(parents=True)
            one = {'windows': [{'tabs': [tab('https://a.test', ms(2026, 1, 1))]}]}
            (profile/'sessionstore.jsonlz4').write_bytes(mozlz4(json.dumps(one).encode()))
            (profile/'sessionstore-backups'/'recovery.js').write_text(json.dumps(one), encoding='utf-8')
            (profile/'sessionstore-backups'/'upgrade.jsonlz4-20260101').write_bytes(b'\x00junk')
            files = [str(p) for p in profile.rglob('*') if p.is_file()]

            class Context:
                def get_files_found(self):
                    return files

                def get_relative_path(self, path):
                    return str(pathlib.Path(path).relative_to(root))
            with patch.object(fs, 'logfunc') as logged:
                rows, source = fs.read_session_store(Context(), 'Firefox Session Store')
            self.assertEqual(sorted((row[16], row[17], row[18]) for row in rows),
                             [('recovery.js', 'ab12.default-release', 'tester')] * 2
                             + [('sessionstore.jsonlz4', 'ab12.default-release', 'tester')] * 2)
            self.assertEqual(len(source.split('\n')), 2)
            self.assertTrue(any('upgrade.jsonlz4-20260101 was not read (neither mozLz4 nor JSON)' in str(c)
                                for c in logged.call_args_list))


class PatternTest(unittest.TestCase):

    def test_each_session_file_matches_one_pattern_on_every_platform(self):
        from scripts.artifacts import firefoxBrowser  # pylint: disable=import-outside-toplevel
        patterns = firefoxBrowser.__artifacts_v2__['firefoxSessionStore']['paths']
        profiles = ('/case/Users/a/Library/Application Support/Firefox/Profiles/p/',
                    '/case/Users/a/AppData/Roaming/Mozilla/Firefox/Profiles/p/',
                    '/case/home/a/.mozilla/firefox/p/',
                    '/case/Users/a/Desktop/Old Firefox Data/p/')
        names = ('sessionstore.jsonlz4', 'sessionstore.js', 'sessionstore-backups/previous.jsonlz4',
                 'sessionstore-backups/recovery.jsonlz4', 'sessionstore-backups/recovery.baklz4',
                 'sessionstore-backups/upgrade.jsonlz4-20260101000000')
        for profile in profiles:
            for name in names:
                with self.subTest(path=profile + name):
                    self.assertEqual(sum(fnmatch.fnmatchcase(profile + name, p) for p in patterns), 1)
        self.assertFalse(any(fnmatch.fnmatchcase('/case/Users/a/Desktop/Backups/p/sessionstore.jsonlz4', p)
                             for p in patterns))


if __name__ == '__main__':
    unittest.main()
