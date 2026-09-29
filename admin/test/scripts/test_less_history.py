"""Pin the less History and less Marks artifacts (scripts/artifacts/lessHistory.py).

L1 and L3 are the lab VM's ~/.local/state/lesshst as less 668 wrote it after known steps L1 and L3 of
ubuntu2604_arm64_lesshst, byte for byte; every search, command and mark in them was made for the known data.
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
from scripts.artifacts import lessHistory as lh
# pylint: enable=wrong-import-position

ALPHA = '/home/parallels/dleapp-less-known/alpha.txt'
L1 = ('.less-history-file:\n.search\n"alpha known\n.shell\n"echo dleapp-shell-one\n.mark\n'
      f'm a 1 1594 {ALPHA}\nm b 1 2862 {ALPHA}\nm \' 1 2862 {ALPHA}\n').encode()
L3 = ('.less-history-file:\n.search\n"alpha known\n"row 042\n"alpha known\n.shell\n"echo dleapp-shell-one\n.shell\n'
      f'"wc -l\n.mark\nm \' 1 784 {ALPHA}\n').encode()
SHELL = 'Shell or pipe command'


def rows_of(data, counts=None):
    return lh.history_rows(data, Counter() if counts is None else counts)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ReaderTest(unittest.TestCase):
    def test_l1(self):
        counts = Counter()
        entries, marks = rows_of(L1, counts)
        self.assertEqual(entries, [('Search', 'alpha known', 3), (SHELL, 'echo dleapp-shell-one', 5)])
        self.assertEqual(marks, [('a', ALPHA, 1594, 1, 7), ('b', ALPHA, 2862, 1, 8), ("'", ALPHA, 2862, 1, 9)])
        self.assertEqual(counts, Counter())

    def test_l3_repeated_search_and_second_shell_header(self):
        entries, marks = rows_of(L3)
        self.assertEqual(entries, [('Search', 'alpha known', 3), ('Search', 'row 042', 4), ('Search', 'alpha known', 5),
                                   (SHELL, 'echo dleapp-shell-one', 7), (SHELL, 'wc -l', 9)])
        self.assertEqual(marks, [("'", ALPHA, 784, 1, 11)])

    def test_not_a_history_file(self):
        for data in (b'', b'\n', b'.search\n"x\n', b' .less-history-file:\n"x\n'):
            counts = Counter()
            self.assertIsNone(rows_of(data, counts), data)
            self.assertEqual(counts, Counter({'files that do not begin with .less-history-file:, not read': 1}))

    def test_empty_entries_are_counted(self):
        counts = Counter()
        self.assertEqual(rows_of(b'.less-history-file:\n.search\n"\n"a\n.shell\n"\n', counts)[0], [('Search', 'a', 4)])
        self.assertEqual(counts, Counter({'empty entries, which less does not load, not reported': 2}))

    def test_first_line_may_carry_more(self):
        self.assertEqual(rows_of(b'.less-history-file: extra\r\n.search\r\n"x\r\n')[0], [('Search', 'x', 3)])

    def test_carriage_return_ends_a_line(self):
        self.assertEqual(rows_of(b'.less-history-file:\n.search\n"ab\rcd\n')[0], [('Search', 'ab', 3)])

    def test_entries_outside_a_section_and_other_lines(self):
        counts = Counter()
        data = b'.less-history-file:\n"before\n.mark\n"in marks\nhello\n\n.search\n"s\n.bogus\n"after bogus\n'
        self.assertEqual(rows_of(data, counts)[0], [('Search', 's', 8), ('Search', 'after bogus', 10)])
        self.assertEqual(counts, Counter({'entries outside a .search or .shell section, not reported': 2,
                                          'other lines, passed over': 2}))

    def test_marks(self):
        counts = Counter()
        data = (b'.less-history-file:\n.search\nm Z 3 10 /x y/z\nm# 0 0 /a\nmq5 7/b\nm 1 2 3 /c\nm a -1 5 /d\n'
                b'm a 1 x /e\nm\nm b\nm c 2147483648 1 /f\nm d 2147483647 9223372036854775808 /g\n'
                b'm e 2147483647 9223372036854775807 /h\n')
        self.assertEqual(rows_of(data, counts)[1], [
            ('Z', '/x y/z', 10, 3, 3), ('#', '/a', 0, 0, 4), ('q', '/b', 7, 5, 5), ('a', '-1 5 /d', 0, 0, 7),
            ('a', 'x /e', 0, 1, 8), ('b', '', 0, 0, 10), ('e', '/h', 9223372036854775807, 2147483647, 13)])
        self.assertEqual(counts, Counter({'mark lines less cannot read back, not reported': 4}))

    def test_mark_file_kept_as_stored(self):
        self.assertEqual(lh.parse_mark('m a 1 2 /p q \t'), ('a', 1, 2, '/p q \t'))

    def test_bytes_that_are_not_utf8(self):
        entries, marks = rows_of(b'.less-history-file:\n.search\n"caf\xe9\n.mark\nm a 1 2 /t\xe9st\n')
        self.assertEqual((entries[0][1], marks[0][1]), ('caf\\xe9', '/t\\xe9st'))

    def test_empty_file_after_the_first_line(self):
        self.assertEqual(rows_of(b'.less-history-file:\n'), ([], []))


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.logged = []
        patcher = mock.patch.object(lh, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = []

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, relative, data):
        path = os.path.join(self.root, *relative.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        self.paths.append(path)
        return path

    def test_headers(self):
        context = FakeContext([], self.root)
        self.assertEqual(lh.lessHistory.__wrapped__(context)[0], ('Entry', 'Kind', 'Line', 'Source File'))
        self.assertEqual(lh.lessMarks.__wrapped__(context)[0],
                         ('Mark', 'File', 'Byte Position', 'Screen Line', 'Line', 'Source File'))

    def test_rows_per_file_and_problems_logged(self):
        one = self.add('home/u/.local/state/lesshst', L1)
        three = self.add('home/v/.lesshst', L3)
        self.add('home/w/.lesshst', b'garbage')
        self.add('home/x/.lesshst', b'.less-history-file:\n.search\n')
        folder = os.path.join(self.root, 'home', 'dir', '.lesshst')
        os.makedirs(folder)
        self.paths.append(folder)
        _h, rows, source = lh.lessHistory.__wrapped__(FakeContext(self.paths, self.root))
        self.assertEqual([(r[0], r[2], r[3]) for r in rows],
                         [('alpha known', 3, 'home/u/.local/state/lesshst'),
                          ('echo dleapp-shell-one', 5, 'home/u/.local/state/lesshst'),
                          ('alpha known', 3, 'home/v/.lesshst'), ('row 042', 4, 'home/v/.lesshst'),
                          ('alpha known', 5, 'home/v/.lesshst'), ('echo dleapp-shell-one', 7, 'home/v/.lesshst'),
                          ('wc -l', 9, 'home/v/.lesshst')])
        self.assertEqual(source.split('\n'), [one, three])
        _h, marks, source = lh.lessMarks.__wrapped__(FakeContext(self.paths, self.root))
        self.assertEqual([(r[0], r[2], r[5]) for r in marks],
                         [('a', 1594, 'home/u/.local/state/lesshst'), ('b', 2862, 'home/u/.local/state/lesshst'),
                          ("'", 2862, 'home/u/.local/state/lesshst'), ("'", 784, 'home/v/.lesshst')])
        self.assertEqual(source.split('\n'), [one, three])
        self.assertEqual(self.logged, [
            'less History: 1 files that do not begin with .less-history-file:, not read',
            'less Marks: 1 files that do not begin with .less-history-file:, not read'])

    def test_unreadable_file_is_counted(self):
        path = self.add('home/u/.lesshst', L1)
        with mock.patch('builtins.open', side_effect=OSError('denied')):
            _h, rows, source = lh.lessHistory.__wrapped__(FakeContext(self.paths, self.root))
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ['less History: 1 files that could not be read'])
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
