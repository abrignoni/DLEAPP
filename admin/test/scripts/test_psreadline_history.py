"""Pin the PSReadLine history reader in scripts/artifacts/windowsPSReadLine.py.

The input text is built the way PSReadLine writes a history file: each command's line
breaks are replaced with a backtick and a line feed, then the command is written with
WriteLine, which ends it with CR LF on Windows (PSReadLine 2.0.0, History.cs lines 342
and 343). The expected values are written out, never read back from the code.
"""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsPSReadLine as psrl  # pylint: disable=wrong-import-position


class ReadHistoryTest(unittest.TestCase):
    def test_one_command_per_line(self):
        text = 'Get-Process\r\ncd C:\\Temp\r\n'
        self.assertEqual(psrl.read_history(text),
                         [(1, 'Get-Process', 1), (2, 'cd C:\\Temp', 1)])

    def test_backtick_joins_a_command_spanning_lines(self):
        text = 'Get-ChildItem |`\nWhere-Object Length -gt 0\r\nexit\r\n'
        self.assertEqual(psrl.read_history(text),
                         [(1, 'Get-ChildItem |\nWhere-Object Length -gt 0', 2), (3, 'exit', 1)])

    def test_blank_line_is_dropped_outside_a_command_and_kept_inside_one(self):
        text = 'first\r\n   \r\nsecond`\n\r\nthird\r\n'
        self.assertEqual(psrl.read_history(text),
                         [(1, 'first', 1), (3, 'second\n', 2), (5, 'third', 1)])

    def test_trailing_backtick_at_end_of_file_is_kept(self):
        self.assertEqual(psrl.read_history('whoami\r\nnet user`\n'),
                         [(1, 'whoami', 1), (2, 'net user`', 1)])
        self.assertEqual(psrl.read_history('a`\nb`\n'), [(1, 'a\nb`', 2)])

    def test_file_without_final_line_break(self):
        self.assertEqual(psrl.read_history('a\nb'), [(1, 'a', 1), (2, 'b', 1)])

    def test_empty_file(self):
        self.assertEqual(psrl.read_history(''), [])


class DecodeTest(unittest.TestCase):
    def test_utf8_with_and_without_mark(self):
        self.assertEqual(psrl.decode_history('dir C:\\Tëst\r\n'.encode('utf-8')),
                         'dir C:\\Tëst\r\n')
        self.assertEqual(psrl.decode_history(b'\xef\xbb\xbfdir\r\n'), 'dir\r\n')

    def test_utf16_by_mark(self):
        self.assertEqual(psrl.decode_history('dir\r\n'.encode('utf-16')), 'dir\r\n')


class NamesTest(unittest.TestCase):
    def test_host_name_from_file_name(self):
        self.assertEqual(psrl.host_name('ConsoleHost_history.txt'), 'ConsoleHost')
        self.assertEqual(psrl.host_name('Visual Studio Code Host_history.txt'),
                         'Visual Studio Code Host')
        self.assertEqual(psrl.host_name('notes.txt'), 'notes.txt')

    def test_profile_folder(self):
        tail = '/AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt'
        self.assertEqual(psrl.profile_folder('lba0/Users/IEUser' + tail), 'lba0/Users/IEUser')
        self.assertEqual(
            psrl.profile_folder('C/Windows/System32/config/systemprofile' + tail.replace('/', '\\')),
            'C/Windows/System32/config/systemprofile')
        self.assertEqual(psrl.profile_folder('extract/other/ConsoleHost_history.txt'),
                         'extract/other')


if __name__ == '__main__':
    unittest.main()
