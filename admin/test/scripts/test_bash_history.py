"""Pin how the bash history artifact reads .bash_history files."""
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import bashHistory
# pylint: enable=wrong-import-position

WHEN = datetime(2026, 9, 28, 6, 45, 30, tzinfo=timezone.utc)
HISTORY = (b'ls -la\n'
           b'# a comment typed at the prompt\n'
           b'#1 note\n'
           b'\n'
           b'#1790577930\n'
           b'echo one\n'
           b'for f in *; do\n'
           b'  echo "$f"\n'
           b'#1790577931\n'
           b'exit\n')


class ParseTest(unittest.TestCase):
    def test_a_stamp_dates_every_line_up_to_the_next(self):
        counts = Counter()
        rows = bashHistory.history_rows(HISTORY, counts)
        self.assertEqual(rows, [('ls -la', '', 1), ('# a comment typed at the prompt', '', 2), ('#1 note', '', 3),
                                ('echo one', WHEN, 6), ('for f in *; do', WHEN, 7), ('  echo "$f"', WHEN, 8),
                                ('exit', datetime(2026, 9, 28, 6, 45, 31, tzinfo=timezone.utc), 10)])
        self.assertEqual(counts, {'empty lines, not reported': 1})

    def test_the_final_line_end_is_not_an_empty_line(self):
        counts = Counter()
        self.assertEqual(bashHistory.history_rows(b'ls\n', counts), [('ls', '', 1)])
        self.assertEqual(counts, {})

    def test_crlf_line_ends_are_not_part_of_the_command(self):
        rows = bashHistory.history_rows(HISTORY.replace(b'\n', b'\r\n'), Counter())
        self.assertEqual([r[0] for r in rows][-1], 'exit')
        self.assertEqual(rows[3][1], WHEN)

    def test_text_that_is_not_utf8_shows_the_replacement_character(self):
        self.assertEqual(bashHistory.history_rows(b'echo caf\xe9\n', Counter()), [('echo caf�', '', 1)])

    def test_a_stamp_outside_the_dates_a_report_can_hold_is_blank(self):
        self.assertEqual(bashHistory.history_rows(b'#99999999999999999999\nls\n', Counter()), [('ls', '', 2)])


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_each_file_is_read_and_named(self):
        with tempfile.TemporaryDirectory() as root:
            files = []
            for relative, data in ((os.path.join('root', '.bash_history'), b'whoami\n'),
                                   (os.path.join('home', 'parallels', '.bash_history'), HISTORY),
                                   (os.path.join('home', 'empty', '.bash_history'), b'')):
                path = os.path.join(root, relative)
                os.makedirs(os.path.dirname(path))
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            with mock.patch.object(bashHistory, 'logfunc') as log:
                _headers, rows, source = bashHistory.bashHistory.__wrapped__(FakeContext(files, root))
            source = [os.path.relpath(path, root) for path in source.split('\n')]
        parallels = os.path.join('home', 'parallels', '.bash_history')
        self.assertEqual([(row[0], row[-1]) for row in rows[:1]], [('ls -la', parallels)])
        self.assertEqual(rows[-1], ('whoami', '', 1, os.path.join('root', '.bash_history')))
        self.assertEqual(len(rows), 8)
        self.assertEqual(source, [parallels, os.path.join('root', '.bash_history')])
        self.assertIn('1 empty lines, not reported', log.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
