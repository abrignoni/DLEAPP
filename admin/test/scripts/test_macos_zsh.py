"""Pin the zsh file readers in scripts/macos_zsh.py.

ZSHRC_ZWC is a .zwc written by /bin/zsh 5.9 on macOS (zcompile -R .zshrc) for a one-line
.zshrc; zcompile -t on it lists 'zwc file (read) for zsh-5.9' and '.zshrc'. The expected values
below are written out, never read back from the code. The compiled-copy rule is pinned against
what zsh 5.9 did when started as a login shell with each arrangement of files.
"""
import base64
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_zsh  # pylint: disable=wrong-import-position

ZSHRC_ZWC = base64.b64decode(
    'BwYFBAC4AAA1LjkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAAAAGYAAAAAAAAAMAAAAAgAAAAA'
    'AAAALnpzaHJjABRBAgAAAiQAAIMAAABEAAAAAQAAAHUAAACGAAAAAAAAANuUAwDb3AQAGQAAAAAAAABwcmludACeLnpz'
    'aHJjIENPTVBJTEVELWNvcHmeAJ6MWkRPVERJUi8uLi8uLi9ydW4ubG9nngBzcgQFBgcCuAAANS45AAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAABmAAAAAAAAADAAAAAIAAAAAC56c2hyYwAAAAACQQAAJAIAAACD'
    'AAAARAAAAAEAAAB1AAAAhgAAAAAAA5TbAATc2wAAABkAAAAAcHJpbnQAni56c2hyYyBDT01QSUxFRC1jb3B5ngCejFpE'
    'T1RESVIvLi4vLi4vcnVuLmxvZ54Ac3I=')
ENTRY = {'name': '.zshrc', 'tail': '.zshrc', 'load': '', 'wordcode_bytes': 48,
         'strings': ['print', '".zshrc COMPILED-copy"', '"$ZDOTDIR/../../run.log"']}


class ReadZwcTest(unittest.TestCase):
    def test_file_written_by_zsh_59(self):
        self.assertEqual(len(ZSHRC_ZWC), 368)
        self.assertEqual(macos_zsh.read_zwc(ZSHRC_ZWC), {
            'version': '5.9', 'byte_order': 'little-endian', 'mode': 'read',
            'second_copy': 'same entries', 'entries': [ENTRY]})

    def test_byte_swapped_copy_reads_alone(self):
        swapped = macos_zsh.read_zwc(ZSHRC_ZWC[184:])
        self.assertEqual(swapped['byte_order'], 'big-endian')
        self.assertEqual(swapped['second_copy'], 'absent')
        self.assertEqual(swapped['entries'], [ENTRY])

    def test_changed_second_copy_is_reported(self):
        data = bytearray(ZSHRC_ZWC)
        at = data.index(b'COMPILED', 184)
        data[at:at + 8] = b'Compiled'
        self.assertEqual(macos_zsh.read_zwc(bytes(data))['second_copy'], 'different entries')

    def test_not_a_zwc_raises(self):
        for data in (b'', b'print hello\n' * 10, ZSHRC_ZWC[:40]):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                macos_zsh.read_zwc(data)


class DecodeTest(unittest.TestCase):
    def test_tokens_and_meta(self):
        # 0x85 String ($), 0x9e Dnull ("), 0x83 Meta then 0xbf for byte 0x9f
        self.assertEqual(macos_zsh.decode_zsh_string(b'\x9e\x85HOME\x9e'), '"$HOME"')
        self.assertEqual(macos_zsh.decode_zsh_string(b'stra\xc3\x83\xbfe'), 'straße')
        self.assertEqual(macos_zsh.decode_zsh_string(b'a\xa1b\xa2c'), 'abc')


class CompiledCopySelectedTest(unittest.TestCase):
    """Each case is an arrangement zsh 5.9 was run against; the expected result is what it ran."""

    ZWC = {'entries': [{'tail': '.zshrc'}]}

    def test_newer_compiled_copy_runs(self):
        self.assertEqual(macos_zsh.compiled_copy_selected(100, 160, self.ZWC, '.zshrc'),
                         (True, 'compiled copy not older than plaintext'))

    def test_equal_times_run_the_compiled_copy(self):
        self.assertEqual(macos_zsh.compiled_copy_selected(100, 100, self.ZWC, '.zshrc'),
                         (True, 'compiled copy not older than plaintext'))

    def test_older_compiled_copy_is_ignored(self):
        self.assertEqual(macos_zsh.compiled_copy_selected(160, 100, self.ZWC, '.zshrc'),
                         (False, 'compiled copy older than plaintext'))

    def test_compiled_copy_runs_after_plaintext_deleted(self):
        self.assertEqual(macos_zsh.compiled_copy_selected(None, 100, self.ZWC, '.zshrc'),
                         (True, 'plaintext absent'))

    def test_copy_compiled_from_another_file_is_ignored(self):
        other = {'entries': [{'tail': 'other.zsh'}]}
        self.assertEqual(macos_zsh.compiled_copy_selected(100, 160, other, '.zshrc'),
                         (False, 'compiled copy holds no entry named .zshrc'))

    def test_sub_second_difference_is_ignored(self):
        self.assertEqual(macos_zsh.compiled_copy_selected(100.9, 100.1, self.ZWC, '.zshrc')[0], True)


class HistoryTest(unittest.TestCase):
    def test_extended_plain_continued_and_metafied_lines(self):
        data = (b': 1790263753:0;echo one\n'
                b': 1790263754:12;for i in 1 2\\\ndo echo $i\\\ndone\n'
                b': 1790263755:0;echo stra\xc3\x83\xbfe\n'
                b'plain command\n'
                b'\\: a colon command\n')
        self.assertEqual(macos_zsh.read_history(data), [
            {'line': 1, 'start': 1790263753, 'elapsed': 0, 'command': 'echo one'},
            {'line': 2, 'start': 1790263754, 'elapsed': 12, 'command': 'for i in 1 2\ndo echo $i\ndone'},
            {'line': 5, 'start': 1790263755, 'elapsed': 0, 'command': 'echo straße'},
            {'line': 6, 'start': None, 'elapsed': None, 'command': 'plain command'},
            {'line': 7, 'start': None, 'elapsed': None, 'command': ': a colon command'},
        ])

    def test_empty_file(self):
        self.assertEqual(macos_zsh.read_history(b''), [])


class SessionTest(unittest.TestCase):
    def test_saved_time(self):
        self.assertEqual(macos_zsh.session_saved_time(
            b'echo Restored session: "$(/bin/date -r 1790259397)"\n'), 1790259397)
        self.assertIsNone(macos_zsh.session_saved_time(b'export FOO=1\n'))


if __name__ == '__main__':
    unittest.main()
