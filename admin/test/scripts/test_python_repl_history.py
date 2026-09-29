"""Pin the Python REPL History artifact (scripts/artifacts/pythonReplHistory.py).

PLAIN is the .python_history of ubuntu2604_arm64_pyhistory byte for byte, written on the lab VM by Python 3.14.4's
interactive interpreter (its new REPL and, for one session, the basic REPL on GNU readline). LIBEDIT is the
.python_history of python_history_known_macos byte for byte, written by the Command Line Tools' Python 3.9.6, whose
readline module is linked to libedit. Every statement in both was typed for the known data.
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
from scripts.artifacts import pythonReplHistory as ph
# pylint: enable=wrong-import-position

PLAIN = (b'import os\ndef add(a, b):\n    return a + b\n    \nprint(add(40, 2))\nos.getcwd()\n'
         b'y = [n * 2 for n in range(3)]\nfor n in y:\n    print(n)\n    \nz = "basic repl"\nprint(len(y))\n'
         b'class Point:\r\n    x = 0\r\n    \nmarker = "p5 before the kill"\n')
LIBEDIT = (b'_HiStOrY_V2_\ns\\040=\\040"two\\040\\040spaces\\040and\\040a\\040tabhere"\n'
           b'p\\040=\\040"C:\\134\\134temp\\134\\134new"\nword\\040=\\040"caf\xc3\xa9"\ndef\\040twice(n):\n'
           b'\\040\\040\\040\\040return\\040n\\040*\\0402\ntwice(21)\n')


def entries_of(data, counts=None):
    return ph.history_entries(data, Counter() if counts is None else counts)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ReaderTest(unittest.TestCase):
    def test_plain_sample(self):
        counts = Counter()
        form, entries = entries_of(PLAIN, counts)
        self.assertEqual(form, 'plain')
        self.assertEqual(entries, [('import os', 1, 1), ('def add(a, b):', 2, 2), ('    return a + b', 3, 3),
                                   ('    ', 4, 4), ('print(add(40, 2))', 5, 5), ('os.getcwd()', 6, 6),
                                   ('y = [n * 2 for n in range(3)]', 7, 7), ('for n in y:', 8, 8),
                                   ('    print(n)', 9, 9), ('    ', 10, 10), ('z = "basic repl"', 11, 11),
                                   ('print(len(y))', 12, 12), ('class Point:\n    x = 0\n    ', 13, 15),
                                   ('marker = "p5 before the kill"', 16, 16)])
        self.assertEqual(counts, Counter())

    def test_libedit_sample(self):
        counts = Counter()
        form, entries = entries_of(LIBEDIT, counts)
        self.assertEqual(form, 'libedit')
        self.assertEqual(entries, [('s = "two  spaces and a tabhere"', 2, 2), ('p = "C:\\\\temp\\\\new"', 3, 3),
                                   ('word = "caf\u00e9"', 4, 4), ('def twice(n):', 5, 5),
                                   ('    return n * 2', 6, 6), ('twice(21)', 7, 7)])
        self.assertEqual(counts, Counter())

    def test_unvis_octal(self):
        self.assertEqual(ph.unvis(b'a\\040b\\011c\\134d\\\\e'), b'a b\tc\\d\\e')
        self.assertEqual(ph.unvis(b'\\1x\\12y\\1234'), b'\x01x\ny\x534')
        self.assertEqual(ph.unvis(b'\\777'), b'\xff')

    def test_unvis_named_and_other_forms(self):
        self.assertEqual(ph.unvis(b'\\n\\r\\b\\a\\v\\t\\f\\s\\E'), b'\n\r\b\x07\x0b\t\x0c \x1b')
        self.assertEqual(ph.unvis(b'\\x41\\x4g\\xFf'), b'A\x04g\xff')
        self.assertEqual(ph.unvis(b'\\^A\\^?\\M-a\\M^A'), b'\x01\x7f\xe1\x81')
        self.assertEqual(ph.unvis(b'a\\$b\\\nc\\!d\\9'), b'ab' + b'c!d9')

    def test_unvis_end_of_line(self):
        self.assertEqual(ph.unvis(b'a\\1'), b'a\x01')
        self.assertEqual(ph.unvis(b'a\\x4'), b'a\x04')
        self.assertEqual(ph.unvis(b'a\\'), b'a')
        self.assertEqual(ph.unvis(b'a\\^'), b'a')

    def test_unvis_rejected(self):
        for line in (b'\\\xc3', b'\\M+', b'\\xg', b'\\ '):
            self.assertIsNone(ph.unvis(line), line)

    def test_rejected_libedit_line_is_reported_as_stored_and_counted(self):
        counts = Counter()
        self.assertEqual(entries_of(b'_HiStOrY_V2_\nok\\040\nbad\\M+\\040\n', counts)[1],
                         [('ok ', 2, 2), ('bad\\M+\\040', 3, 3)])
        self.assertEqual(counts, Counter({'libedit lines holding an escape its decoder rejects, reported undecoded': 1}))

    def test_libedit_escapes_are_not_decoded_in_a_plain_file(self):
        self.assertEqual(entries_of(b'a\\040b\n')[1], [('a\\040b', 1, 1)])

    def test_cookie_only_on_the_first_line(self):
        form, entries = entries_of(b'x\n_HiStOrY_V2_\n')
        self.assertEqual((form, entries), ('plain', [('x', 1, 1), ('_HiStOrY_V2_', 2, 2)]))

    def test_empty_lines_are_counted_and_the_final_newline_is_not(self):
        counts = Counter()
        self.assertEqual(entries_of(b'\na\n\n\nb\n', counts)[1], [('a', 2, 2), ('b', 5, 5)])
        self.assertEqual(counts, Counter({'empty lines, which are no entry': 3}))

    def test_file_without_a_final_newline(self):
        self.assertEqual(entries_of(b'a\nb')[1], [('a', 1, 1), ('b', 2, 2)])

    def test_continued_entry_ended_by_an_empty_line(self):
        counts = Counter()
        self.assertEqual(entries_of(b'a\r\n\nb\n', counts)[1], [('a', 1, 2), ('b', 3, 3)])
        self.assertEqual(counts, Counter())

    def test_continued_entry_ended_by_the_end_of_the_file(self):
        counts = Counter()
        self.assertEqual(entries_of(b'x\na\r\nb\r\n', counts)[1], [('x', 1, 1), ('a\nb', 2, 3)])
        self.assertEqual(counts, Counter())

    def test_continued_entry_cut_off_at_the_end_of_the_file(self):
        counts = Counter()
        self.assertEqual(entries_of(b'x\na\r\nb\r', counts)[1], [('x', 1, 1), ('a\nb', 2, 3)])
        self.assertEqual(counts, Counter({'entries whose last line ends in a carriage return at the end of the file': 1}))

    def test_continued_entry_with_no_text_is_no_entry(self):
        counts = Counter()
        self.assertEqual(entries_of(b'\r\n\nb\n\r\n\r', counts)[1], [('b', 3, 3)])
        self.assertEqual(counts, Counter({'continued entries with no text, which are no entry': 2,
                                          'entries whose last line ends in a carriage return at the end of the file': 1}))

    def test_bytes_that_are_not_utf8_are_shown_as_escapes(self):
        self.assertEqual(entries_of(b'caf\xe9\n')[1], [('caf\\xe9', 1, 1)])
        self.assertEqual(entries_of(b'_HiStOrY_V2_\nx\\377\n')[1], [('x\\xff', 2, 2)])

    def test_empty_file(self):
        for data in (b'', b'\n', b'_HiStOrY_V2_\n'):
            self.assertEqual(entries_of(data)[1], [], data)


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.logged = []
        patcher = mock.patch.object(ph, 'logfunc', self.logged.append)
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

    def run_artifact(self):
        return ph.pythonReplHistory.__wrapped__(FakeContext(self.paths, self.root))

    def test_headers(self):
        headers, _rows, _source = self.run_artifact()
        self.assertEqual(headers, ('Entry', 'First Line', 'Last Line', 'File Format', 'Source File'))

    def test_rows_in_file_order_per_file_and_problems_logged(self):
        linux = self.add('home/u/.python_history', PLAIN)
        mac = self.add('Users/v/.python_history', LIBEDIT)
        self.add('home/empty/.python_history', b'')
        self.add('home/cut/.python_history', b'a\r\n\nb\r')
        folder = os.path.join(self.root, 'home', 'dir', '.python_history')
        os.makedirs(folder)
        self.paths.append(folder)
        _headers, rows, source = self.run_artifact()
        self.assertEqual(len(rows), 6 + 2 + 14)
        self.assertEqual(rows[5], ('twice(21)', 7, 7, 'libedit', 'Users/v/.python_history'))
        self.assertEqual(rows[6:8], [('a', 1, 2, 'plain', 'home/cut/.python_history'),
                                     ('b', 3, 3, 'plain', 'home/cut/.python_history')])
        self.assertEqual(rows[20], ('class Point:\n    x = 0\n    ', 13, 15, 'plain', 'home/u/.python_history'))
        cut = os.path.join(self.root, 'home', 'cut', '.python_history')
        self.assertEqual(source.split('\n'), [mac, cut, linux])
        self.assertEqual(self.logged, ['Python REPL History: 1 entries whose last line ends in a carriage return '
                                       'at the end of the file'])

    def test_unreadable_file_is_counted(self):
        path = self.add('home/u/.python_history', PLAIN)
        with mock.patch('builtins.open', side_effect=OSError('denied')):
            _headers, rows, source = self.run_artifact()
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ['Python REPL History: 1 files that could not be read'])
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
