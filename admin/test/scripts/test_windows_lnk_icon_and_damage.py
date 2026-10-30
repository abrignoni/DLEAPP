"""Pin the shell link reader's icon location fields and its text mode copy check (scripts/windows_lnk.py), on links
built here in the [MS-SHLLINK] layout: a header, Unicode StringData, an IconEnvironmentDataBlock and a terminal
block."""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.windows_lnk import parse_lnk, text_mode_damaged
from scripts.artifacts import windowsLnk
# pylint: enable=wrong-import-position

CLSID = bytes.fromhex('0114020000000000c000000000000046')
HAS_ARGUMENTS, HAS_ICON, IS_UNICODE = 0x20, 0x40, 0x80


def string_data(text):
    return struct.pack('<H', len(text)) + text.encode('utf-16-le')


def link(icon=None, environment=None, arguments=None, created=0):
    flags = IS_UNICODE | (HAS_ICON if icon is not None else 0) | (HAS_ARGUMENTS if arguments is not None else 0)
    data = struct.pack('<I', 0x4C) + CLSID + struct.pack('<II', flags, 0x20) + struct.pack('<QQQ', created, 0, 0)
    data += struct.pack('<IIIH', 0, 0, 1, 0) + b'\x00' * 10
    if arguments is not None:
        data += string_data(arguments)
    if icon is not None:
        data += string_data(icon)
    if environment is not None:
        block = struct.pack('<II', 0x314, 0xA0000007) + environment.encode('latin-1').ljust(260, b'\x00')
        block += environment.encode('utf-16-le').ljust(520, b'\x00')
        data += block
    return data + b'\x00\x00\x00\x00'


class IconTest(unittest.TestCase):
    def test_both_icon_fields(self):
        parsed = parse_lnk(link(icon='C:\\Program Files\\App\\app.exe', environment='%ProgramFiles%\\App\\app.exe'))
        self.assertEqual(parsed['icon_location'], 'C:\\Program Files\\App\\app.exe')
        self.assertEqual(parsed['icon_environment'], '%ProgramFiles%\\App\\app.exe')
        self.assertTrue(parsed['ends_cleanly'])

    def test_no_icon(self):
        parsed = parse_lnk(link())
        self.assertEqual((parsed['icon_location'], parsed['icon_environment']), ('', ''))


class TextModeTest(unittest.TestCase):
    # A creation time whose bytes hold an LF (0x0A), so a text mode copy changes the header.
    ORIGINAL = link(arguments='-x', created=0x01D00A0A0A0A0A0A)

    def damaged(self):
        return self.ORIGINAL.replace(b'\n', b'\r\n')

    def test_a_text_mode_copy_is_found(self):
        self.assertIn(b'\n', self.ORIGINAL)
        self.assertFalse(text_mode_damaged(self.ORIGINAL))
        self.assertTrue(text_mode_damaged(self.damaged()))

    def test_a_link_that_ends_cleanly_is_not_damaged(self):
        # CR LF pairs that end with the terminal block at the end are left alone.
        self.assertFalse(text_mode_damaged(link(arguments='a\r\nb')))

    def test_bytes_that_are_no_link_are_not_damaged(self):
        self.assertFalse(text_mode_damaged(b'text\r\nmore\r\n'))

    def test_the_artifact_names_a_damaged_file_and_leaves_it_out(self):
        with tempfile.TemporaryDirectory() as folder:
            good = os.path.join(folder, 'a.lnk')
            bad = os.path.join(folder, 'b.lnk')
            for path, data in ((good, self.ORIGINAL), (bad, self.damaged())):
                with open(path, 'wb') as handle:
                    handle.write(data)

            class Context:
                @staticmethod
                def get_files_found():
                    return [good, bad]

                @staticmethod
                def get_relative_path(path):
                    return os.path.basename(path)
            with mock.patch.object(windowsLnk, 'logfunc') as log:
                _headers, rows, _source = windowsLnk.windowsLnkRecent.__wrapped__(Context())
        self.assertEqual([row[-1] for row in rows], ['a.lnk'])
        self.assertEqual([call.args[0] for call in log.call_args_list], [
            'Recent Shell Links: b.lnk reads as a whole shell link only with the CR byte before each LF removed, '
            'as a copy in text mode leaves a binary file, and was not reported',
            'Recent Shell Links: 1 file(s) named .lnk read as a whole shell link only with the CR byte before each '
            'LF removed, the state a copy in text mode leaves, and were not reported'])


if __name__ == '__main__':
    unittest.main()
