"""Pin that a UTF-16 string that does not decode is read with U+FFFD instead of failing its record."""
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import Evtx.BinaryParser as evtx_binary  # noqa: E402  pylint: disable=wrong-import-position

from scripts import windows_evtx  # noqa: E402  pylint: disable=wrong-import-position

# A high surrogate (0xD801) with no low surrogate after it, then U+D7CF and '~'.
LONE_SURROGATE = b'\x01\xd8\xcf\xd7~\x00'


class FakeHeader:
    @staticmethod
    def chunk_count():
        return 1

    @staticmethod
    def is_dirty():
        return False

    @staticmethod
    def next_record_number():
        return 2

    @staticmethod
    def chunks(include_inactive=False):  # pylint: disable=unused-argument
        return [FakeChunk()]


class FakeRecord:
    @staticmethod
    def record_num():
        return 1

    @staticmethod
    def xml():
        return evtx_binary.Block(LONE_SURROGATE, 0).unpack_wstring(0, 3)


class FakeChunk:
    @staticmethod
    def records():
        return iter([FakeRecord()])


class FakeLog:
    @staticmethod
    def get_file_header():
        return FakeHeader()


class WstringReplacementTest(unittest.TestCase):
    def test_installed_once(self):
        installed = evtx_binary.Block.unpack_wstring
        self.assertTrue(getattr(installed, 'dleapp_records', False))
        windows_evtx._install_wstring_replacement()  # pylint: disable=protected-access
        self.assertIs(evtx_binary.Block.unpack_wstring, installed)
        self.assertFalse(getattr(getattr(installed, 'original'), 'dleapp_records', False))

    def test_python_evtx_alone_raises(self):
        block = evtx_binary.Block(LONE_SURROGATE, 0)
        with self.assertRaises(UnicodeDecodeError):
            getattr(evtx_binary.Block.unpack_wstring, 'original')(block, 0, 3)

    def test_a_string_that_does_not_decode_is_read_with_a_replacement_character(self):
        block = evtx_binary.Block(LONE_SURROGATE, 0)
        self.assertEqual(block.unpack_wstring(0, 3), '\ufffd\ud7cf~')

    def test_a_string_that_decodes_is_read_as_before(self):
        block = evtx_binary.Block('Password Policy'.encode('utf-16-le'), 0)
        self.assertEqual(block.unpack_wstring(0, 15), 'Password Policy')

    def test_the_run_log_counts_the_strings_read_with_replacement(self):
        lines = []
        with mock.patch.object(windows_evtx, 'logfunc', lines.append):
            for record in windows_evtx.log_records(FakeLog(), 'Label', 'vol/Security.evtx'):
                self.assertEqual(record.xml(), '\ufffd\ud7cf~')
        self.assertEqual(lines, ['Label: 1 UTF-16 string(s) in vol/Security.evtx did not decode and were read with '
                                 'U+FFFD in place of what did not'])


if __name__ == '__main__':
    unittest.main()
