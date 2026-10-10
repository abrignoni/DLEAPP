"""Pin the File Manager Bookmarks (GTK) artifact (scripts/artifacts/linuxGtkBookmarks.py).

KNOWN has the form of the file on ubuntu2604_arm64_gtkbookmarks: lines with and without a label, a percent escape, a
URI that is not a local file and a line that starts with a space.
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
from scripts.artifacts import linuxGtkBookmarks as gb
# pylint: enable=wrong-import-position

KNOWN = (b'file:///home/user/Documents Documents\nfile:///home/user/known/alpha\n'
         b'file:///home/user/known/beta%20two Beta custom label\nsftp://user@192.0.2.10/srv/share Lab share\n'
         b' file:///home/user/known/leading\nfile:///home/user/known/alpha Alpha again\n')
SKIPPED = 'lines that start with white space, not reported'


def rows(data, counts=None):
    return gb.bookmark_rows(data, Counter() if counts is None else counts)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class LocalPath(unittest.TestCase):
    def test_a_local_file_uri(self):
        self.assertEqual(gb.local_path('file:///home/user/a%20b/c%25d'), '/home/user/a b/c%d')
        self.assertEqual(gb.local_path('file:///'), '/')
        self.assertEqual(gb.local_path('file:///home/user/caf%C3%A9'), '/home/user/café')

    def test_escapes_that_are_not_utf8(self):
        self.assertEqual(gb.local_path('file:///a%FFb'), '/a\\xffb')

    def test_nothing_but_the_escapes_is_changed(self):
        self.assertEqual(gb.local_path('file:///a/b?x=1#frag+c'), '/a/b?x=1#frag+c')
        self.assertEqual(gb.local_path('file:///a/b%3Fc%23d%2'), '/a/b?c#d%2')

    def test_other_uris(self):
        for uri in ('sftp://user@host/srv', 'file://host/share/x', 'file:/home/user', 'smb://server/share',
                    'FILE:///home/user', '/home/user', ''):
            self.assertEqual(gb.local_path(uri), '', uri)


class Lines(unittest.TestCase):
    def test_known_file(self):
        counts = Counter()
        self.assertEqual(rows(KNOWN, counts), [
            ('file:///home/user/Documents', 'Documents', '/home/user/Documents', 1),
            ('file:///home/user/known/alpha', '', '/home/user/known/alpha', 2),
            ('file:///home/user/known/beta%20two', 'Beta custom label', '/home/user/known/beta two', 3),
            ('sftp://user@192.0.2.10/srv/share', 'Lab share', '', 4),
            ('file:///home/user/known/alpha', 'Alpha again', '/home/user/known/alpha', 6)])
        self.assertEqual(counts, {SKIPPED: 1})

    def test_a_last_line_without_a_newline(self):
        self.assertEqual(rows(KNOWN[:-1]), rows(KNOWN))

    def test_empty_lines_keep_the_numbering(self):
        counts = Counter()
        self.assertEqual([r[3] for r in rows(b'\n\nfile:///a\n\nfile:///b\n', counts)], [3, 5])
        self.assertEqual(counts, {})

    def test_white_space_first(self):
        counts = Counter()
        self.assertEqual(rows(b'\tfile:///a\n\rfile:///b\n\x0bfile:///c\n\x0cfile:///d\n \n', counts), [])
        self.assertEqual(counts, {SKIPPED: 5})

    def test_only_a_line_feed_ends_a_line_and_only_a_space_starts_the_label(self):
        self.assertEqual(rows(b'file:///a\tb c\r\n'), [('file:///a\tb', 'c\r', '/a\tb', 1)])
        self.assertEqual(rows(b'file:///a\x0cb\n')[0][3], 1)

    def test_a_label_keeps_its_spaces(self):
        self.assertEqual(rows(b'file:///a  two  spaces \n')[0][:2], ('file:///a', ' two  spaces '))
        self.assertEqual(rows(b'file:///a \n')[0][:2], ('file:///a', ''))

    def test_bytes_that_are_not_utf8(self):
        self.assertEqual(rows(b'file:///a\xff b\xfe\n')[0][:3], ('file:///a\\xff', 'b\\xfe', '/a\\xff'))

    def test_an_empty_file(self):
        self.assertEqual(rows(b''), [])


class Processor(unittest.TestCase):
    def test_two_homes(self):
        with tempfile.TemporaryDirectory() as root:
            first = os.path.join(root, 'home', 'a', '.config', 'gtk-3.0', 'bookmarks')
            second = os.path.join(root, 'home', 'b', '.gtk-bookmarks')
            empty = os.path.join(root, 'home', 'c', '.gtk-bookmarks')
            for path, data in ((first, KNOWN), (second, b'smb://server/share\n'), (empty, b'\n')):
                os.makedirs(os.path.dirname(path))
                with open(path, 'wb') as handle:
                    handle.write(data)
            paths = [second, empty, os.path.join(root, 'home', 'gone', '.gtk-bookmarks'), first, os.path.dirname(first)]
            with mock.patch.object(gb, 'logfunc') as log:
                headers, data, located = gb.linuxGtkBookmarks.__wrapped__(FakeContext(paths, root))
        self.assertEqual(headers, ('URI', 'Label', 'Local Path', 'Line', 'Source File'))
        self.assertEqual(len(data), 6)
        self.assertEqual(data[0], ('file:///home/user/Documents', 'Documents', '/home/user/Documents', 1,
                                   os.path.join('home', 'a', '.config', 'gtk-3.0', 'bookmarks')))
        self.assertEqual(data[5], ('smb://server/share', '', '', 1, os.path.join('home', 'b', '.gtk-bookmarks')))
        self.assertEqual(located.split('\n'), [first, second])
        message = log.call_args[0][0]
        self.assertIn('1 files that could not be read', message)
        self.assertIn('1 ' + SKIPPED, message)

    def test_nothing_found(self):
        with mock.patch.object(gb, 'logfunc') as log:
            self.assertEqual(gb.linuxGtkBookmarks.__wrapped__(FakeContext([], '/'))[1:], ([], ''))
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
