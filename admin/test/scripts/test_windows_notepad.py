"""Pin how scripts/windows_notepad.py and the windowsNotepad* artifacts read Notepad state files.

Author: @AlexisBrignoni, Claude.

Every file here is synthetic, written by the small encoder below from the layout
Notepad-State-Library documents (README.md at commit ce53f9d6): "NP", LEB128 integers,
UTF-16LE text counted in code units, and a CRC-32 stored most significant byte first.
The expected values are written out, never read back from the code under test.
"""
import datetime
import hashlib
import pathlib
import sys
import tempfile
import unittest
import uuid
import zlib
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_notepad as notepad  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsNotepad as artifact  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
PACKAGE = 'C/Users/{user}/AppData/Local/Packages/Microsoft.WindowsNotepad_8wekyb3d8bbwe/LocalState'
TAB_A = '1a2b3c4d-0000-4000-8000-000000000001'
TAB_B = '9f8e7d6c-0000-4000-8000-000000000002'
WINDOW = '5e5e5e5e-0000-4000-8000-000000000003'
# 2024-11-04 15:33:34 UTC as a FILETIME.
FILETIME = 133752080140000000


def leb(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def text(value):
    return leb(len(value)) + value.encode('utf-16-le')


def crc(block):
    return (zlib.crc32(block) & 0xFFFFFFFF).to_bytes(4, 'big')


def config(word_wrap=1):
    return bytes([word_wrap, 0, 0]) + leb(2) + b'\x01\x00'


def file_tab(path, content, timestamp=0, saved=b'', unsaved=0, chunks=b''):
    body = (leb(1) + text(path) + leb(len(saved)) + b'\x05\x01' + leb(timestamp)
            + (hashlib.sha256(saved).digest() if saved else bytes(32))
            + b'\x00\x01' + leb(3) + leb(3) + config() + text(content) + bytes([unsaved]))
    return b'NP' + leb(0) + body + crc(body) + chunks


def no_file_tab(content, chunks=b''):
    body = leb(0) + b'\x01' + leb(0) + leb(0) + config(0) + text(content) + b'\x01'
    return b'NP' + leb(0) + body + crc(body) + chunks


def chunk(position, deleted, added):
    body = leb(position) + leb(deleted) + leb(len(added)) + added.encode('utf-16-le')
    return body + crc(body)


def state_file(bin_size):
    body = leb(0) + leb(11) + b'\x00' + leb(bin_size) + leb(0) + leb(0) + config()
    return b'NP' + body + crc(body)


def window(sequence, tabs, active, slack=b''):
    middle = b'\x00' + leb(len(tabs)) + b''.join(uuid.UUID(t).bytes_le for t in tabs) + leb(active)
    middle += b''.join(v.to_bytes(4, 'little') for v in (40, 50, 840, 650, 800, 600)) + b'\x00'
    body = leb(sequence) + leb(len(middle) + 2) + middle
    return b'NP' + body + crc(body) + slack


class ReaderTest(unittest.TestCase):
    def test_a_file_tab(self):
        data = file_tab('C:\\notes.txt', 'draft', FILETIME, saved=b'old', unsaved=1)
        tab = notepad.parse_tab(data)
        self.assertEqual((tab['type_flag'], tab['file_path'], tab['saved_length'], tab['encoding'],
                          tab['line_ending'], tab['timestamp'], tab['content'], tab['unsaved_flag'],
                          tab['selection_start'], tab['options'], tab['crc_ok']),
                         (1, 'C:\\notes.txt', 3, 5, 1, FILETIME, 'draft', 1, 3, b'\x01\x00', True))

    def test_a_changed_byte_fails_the_crc(self):
        data = bytearray(file_tab('C:\\notes.txt', 'draft'))
        data[-6] ^= 0x01
        self.assertFalse(notepad.parse_tab(bytes(data))['crc_ok'])

    def test_chunks_are_read_and_applied(self):
        data = no_file_tab('abcd', chunk(4, 0, 'E') + chunk(1, 2, 'XY'))
        tab = notepad.parse_tab(data)
        self.assertEqual([(c['position'], c['deleted'], c['added'], c['text'], c['crc_ok'])
                          for c in tab['chunks']], [(4, 0, 1, 'E', True), (1, 2, 2, 'XY', True)])
        self.assertEqual(notepad.apply_chunks(tab['content'], tab['chunks']), 'aXYdE')

    def test_a_chunk_past_the_text_is_not_applied(self):
        tab = notepad.parse_tab(no_file_tab('ab', chunk(9, 1, 'x')))
        self.assertIsNone(notepad.apply_chunks(tab['content'], tab['chunks']))

    def test_a_short_file_raises(self):
        data = file_tab('C:\\notes.txt', 'draft')
        with self.assertRaises(notepad.NotepadError):
            notepad.parse_tab(data[:20])
        with self.assertRaises(notepad.NotepadError):
            notepad.parse_tab(b'XX' + data[2:])

    def test_a_state_file(self):
        tab = notepad.parse_tab(state_file(241))
        self.assertEqual((tab['type_flag'], tab['bin_size'], tab['crc_ok']), (11, 241, True))

    def test_a_window(self):
        found = notepad.parse_window(window(3, [TAB_A, TAB_B], 1, slack=b'\x00' * 7))
        self.assertEqual((found['sequence'], found['tabs'], found['active'], found['size'],
                          found['crc_ok'], found['slack']), (3, [TAB_A, TAB_B], 1, (800, 600), True, 7))


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files.append(str(path))

    def _run(self, function):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        with mock.patch.object(artifact, 'logfunc') as log:
            result = getattr(artifact, function).__wrapped__(context)
        return result, [call.args[0] for call in log.call_args_list]

    def _profile(self, user='jdoe'):
        base = PACKAGE.format(user=user)
        self._write(f'{base}/TabState/{TAB_A}.bin',
                    file_tab('C:\\notes.txt', 'draft', FILETIME, saved=b'old', unsaved=1,
                             chunks=chunk(5, 0, '!')))
        self._write(f'{base}/TabState/{TAB_A}.0.bin', state_file(10))
        self._write(f'{base}/TabState/{TAB_A}.1.bin', b'')
        self._write(f'{base}/TabState/{TAB_B}.bin', no_file_tab('never saved'))
        self._write(f'{base}/WindowState/{WINDOW}.0.bin', window(2, [TAB_B], 0))
        self._write(f'{base}/WindowState/{WINDOW}.1.bin', window(3, [TAB_B, TAB_A], 1))
        return base

    def test_tab_rows(self):
        base = self._profile()
        (headers, rows, source), _log = self._run('windowsNotepadTabs')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (datetime.datetime(2024, 11, 4, 15, 33, 34, tzinfo=UTC), 'File', 'C:\\notes.txt', 'draft',
             'draft!', 1, 1, 3, hashlib.sha256(b'old').hexdigest(), 'UTF-8 (5)', 'Windows (CRLF) (1)',
             3, 3, 1, 0, 0, '0100', 2, 'Yes', 'pass; unsaved buffer chunks 1 of 1 pass',
             f'{TAB_A}.0.bin pass; {TAB_A}.1.bin empty', TAB_A, 'jdoe', f'{base}/TabState/{TAB_A}.bin'),
            ('', 'No file', '', 'never saved', '', 0, 1, '', '', '', '', 0, 0, 0, 0, 0, '0100', 1, 'No',
             'pass', '', TAB_B, 'jdoe', f'{base}/TabState/{TAB_B}.bin'),
        ])
        self.assertEqual(len(source.split('\n')), 2)

    def test_window_rows(self):
        base = self._profile()
        (headers, rows, _source), _log = self._run('windowsNotepadWindows')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([row[:6] for row in rows], [
            (2, 'No', 1, TAB_B, 0, TAB_B),
            (3, 'Yes', 2, f'{TAB_B}\n{TAB_A}', 1, TAB_A)])
        self.assertEqual(rows[1][-1], f'{base}/WindowState/{WINDOW}.1.bin')

    def test_two_users_keep_their_own_window_positions(self):
        self._profile('alice')
        base = PACKAGE.format(user='bob')
        self._write(f'{base}/TabState/{TAB_A}.bin', file_tab('C:\\b.txt', ''))
        (_headers, rows, _source), _log = self._run('windowsNotepadTabs')
        self.assertEqual(sorted((row[-2], row[17]) for row in rows),
                         [('alice', 1), ('alice', 2), ('bob', '')])

    def test_a_damaged_tab_is_logged_and_left_out(self):
        base = PACKAGE.format(user='jdoe')
        self._write(f'{base}/TabState/{TAB_A}.bin', file_tab('C:\\notes.txt', 'draft')[:15])
        (_headers, rows, source), log = self._run('windowsNotepadTabs')
        self.assertEqual((rows, source), ([], ''))
        self.assertTrue(any(line.startswith('Windows Notepad Tabs: could not read') for line in log))


if __name__ == '__main__':
    unittest.main()
