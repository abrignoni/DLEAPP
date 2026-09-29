"""Pin the SQLite Shell History artifact (scripts/artifacts/sqliteShellHistory.py).

MAC_KNOWN is the history file of sqlite_history_known_macos byte for byte: two sessions of Apple's /usr/bin/sqlite3
3.54.0, which links libedit. UBUNTU_S1 is the history file of ubuntu2604_arm64_sqlitehist after its first step: one
session of sqlite3 3.46.1 linked with GNU readline 8.3.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import sqliteShellHistory as sq
from scripts.artifacts import pythonReplHistory as ph
from scripts import libedit_history
# pylint: enable=wrong-import-position

MAC_KNOWN = bytes.fromhex(
    '5f486953744f72595f56325f0a6372656174655c3034307461626c655c303430706c61636573286e616d655c303430746578742c5c3034'
    '306e6f74655c30343074657874293b0a696e736572745c303430696e746f5c303430706c616365735c30343076616c7565735c30343028'
    '27436166c3a95c3034304c756e61272c5c3034302774776f5c3034305c30343073706163657327293b0a73656c6563745c3034306e616d'
    '655c30343066726f6d5c303430706c616365735c30343077686572655c3034306e6f74655c3034306c696b655c30343027255c31333425'
    '275c3034306f725c3034306e616d655c3034303d5c30343027c3bc273b0a2e686561646572735c3034306f6e0a73656c6563745c303430'
    '274d315c303430646f6e65273b0a2e717569740a73656c6563745c30343034323b0a2e717569740a')
UBUNTU_S1 = (b"create table notes(id integer primary key, body text);\ninsert into notes(body) values ('dleapp known "
             b"alpha');\nselect count(*)\n  from notes;\n.tables\n.output /dev/null\nselect 'caf\xc3\xa9 \xe2\x9c\x93';\n"
             b".quit\n")


def read(data):
    counts = Counter()
    form, lines = sq.history_lines(data, counts)
    return form, lines, counts


class KnownFileTest(unittest.TestCase):
    def test_the_mac_libedit_file(self):
        form, lines, counts = read(MAC_KNOWN)
        self.assertEqual(form, 'libedit')
        self.assertEqual(lines, [
            ('create table places(name text, note text);', 2),
            ("insert into places values ('Café Luna', 'two  spaces');", 3),
            ("select name from places where note like '%\\%' or name = 'ü';", 4),
            ('.headers on', 5), ("select 'M1 done';", 6), ('.quit', 7), ('select 42;', 8), ('.quit', 9)])
        self.assertEqual(counts, Counter())

    def test_the_ubuntu_readline_file(self):
        form, lines, counts = read(UBUNTU_S1)
        self.assertEqual(form, 'plain')
        self.assertEqual([text for text, _n in lines][2:4], ['select count(*)', '  from notes;'])
        self.assertEqual(lines[6], ("select 'café ✓';", 7))
        self.assertEqual(len(lines), 8)
        self.assertEqual(counts, Counter())


class PlainTest(unittest.TestCase):
    def test_crlf_empty_and_carriage_return_only_lines(self):
        form, lines, counts = read(b'a\r\n\r\n\nb\n')
        self.assertEqual((form, lines), ('plain', [('a', 1), ('b', 4)]))
        self.assertEqual(counts, Counter({sq.EMPTY: 2}))

    def test_a_last_line_with_no_newline_is_reported_and_counted(self):
        _form, lines, counts = read(b'a\nb')
        self.assertEqual(lines, [('a', 1), ('b', 2)])
        self.assertEqual(counts, Counter({sq.UNTERMINATED: 1}))
        _form, lines, counts = read(b'a\nb\r')
        self.assertEqual(lines[-1], ('b\r', 2))

    def test_timestamp_lines_only_when_the_file_starts_with_one(self):
        _form, lines, counts = read(b'#1790000000\nselect 1;\n#1790000001\n#x\n')
        self.assertEqual(lines, [('select 1;', 2), ('#x', 4)])
        self.assertEqual(counts, Counter({sq.TIMESTAMPS: 2}))
        _form, lines, counts = read(b'select 1;\n#123\n')
        self.assertEqual(lines, [('select 1;', 1), ('#123', 2)])
        self.assertEqual(counts, Counter())

    def test_invalid_utf8_is_kept_escaped(self):
        self.assertEqual(read(b'\xff\n')[1], [('\\xff', 1)])

    def test_an_empty_file(self):
        self.assertEqual(read(b''), ('plain', [], Counter()))


class LibeditTest(unittest.TestCase):
    def test_only_the_exact_cookie_line_makes_it_libedit(self):
        self.assertEqual(read(b'_HiStOrY_V2_ extra\nselect\\0401;\n')[:2],
                         ('plain', [('_HiStOrY_V2_ extra', 1), ('select\\0401;', 2)]))

    def test_empty_lines_carriage_returns_and_no_final_newline(self):
        form, lines, counts = read(b'_HiStOrY_V2_\na\\040b\n\nx\\ty\r\nlast')
        self.assertEqual((form, lines), ('libedit', [('a b', 2), ('x\ty\r', 4), ('last', 5)]))
        self.assertEqual(counts, Counter({sq.EMPTY: 1}))

    def test_a_cookie_only_file_gives_nothing(self):
        self.assertEqual(read(b'_HiStOrY_V2_\n'), ('libedit', [], Counter()))

    def test_an_escape_the_decoder_rejects_is_reported_undecoded(self):
        _form, lines, counts = read(b'_HiStOrY_V2_\nbad\\M!\n')
        self.assertEqual(lines, [('bad\\M!', 2)])
        self.assertEqual(counts, Counter({sq.UNDECODED: 1}))

    def test_the_python_artifact_uses_the_same_decoder(self):
        self.assertIs(ph.unvis, libedit_history.unvis)
        self.assertIs(sq.unvis, libedit_history.unvis)
        self.assertEqual(ph.LIBEDIT_COOKIE, b'_HiStOrY_V2_')


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):
    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            paths = []
            for rel, data in (('home/a/.sqlite_history', UBUNTU_S1), ('Users/b/.sqlite_history', MAC_KNOWN),
                              ('home/c/.sqlite_history', b'\n\n')):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path))
                with open(path, 'wb') as handle:
                    handle.write(data)
                paths.append(path)
            paths.append(os.path.join(root, 'home'))
            with mock.patch.object(sq, 'logfunc') as log:
                headers, rows, source = sq.sqliteShellHistory.__wrapped__(FakeContext(paths, root))
        self.assertEqual(headers, ('Entry', 'Line', 'File Format', 'Source File'))
        self.assertEqual(len(rows), 16)
        self.assertEqual(rows[0], ('create table places(name text, note text);', 2, 'libedit', 'Users/b/.sqlite_history'))
        self.assertEqual(rows[8], ('create table notes(id integer primary key, body text);', 1, 'plain',
                                   'home/a/.sqlite_history'))
        self.assertEqual(source.split('\n'), [os.path.join(root, 'Users', 'b', '.sqlite_history'),
                                              os.path.join(root, 'home', 'a', '.sqlite_history')])
        log.assert_called_once_with('SQLite Shell History: 2 ' + sq.EMPTY)

    def test_an_unreadable_file_is_counted(self):
        with tempfile.TemporaryDirectory() as root:
            missing = os.path.join(root, 'home', 'x', '.sqlite_history')
            with mock.patch.object(sq, 'logfunc') as log:
                _headers, rows, source = sq.sqliteShellHistory.__wrapped__(FakeContext([missing], root))
        self.assertEqual((rows, source), ([], ''))
        log.assert_called_once_with('SQLite Shell History: 1 files that could not be read')


if __name__ == '__main__':
    unittest.main()
