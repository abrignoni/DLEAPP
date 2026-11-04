"""Pin how the long name of a file entry shell item is read from its 0xbeef0004 extension block, in
scripts/windows_lnk.py and in windowsShellbags.py. The blocks are built here in the layout libyal libfwsi documents
("Windows Shell Item format" at 996128afc64961dbfddf17b176ceff21c499b7d3, section "File entry extension block
(0xbeef0004)"): the long name starts at the long name offset stored at byte 16 of the block, and where that is depends
on the block version (20 for version 3, 38 for 7, 42 for 8, 46 for 9). Every name here is made up."""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import windows_lnk
from scripts.artifacts import windowsShellbags
# pylint: enable=wrong-import-position

SHORT = b'LONGFI~1.TXT\x00\x00'
LONG = 'Long file name.txt'


def beef0004(version, long_name=LONG, localized=b'', offset=None):
    """A 0xbeef0004 block of the given version, ending with the first extension block offset."""
    body = bytearray(struct.pack('<II', 0x12345678, 0x9ABCDEF0))  # creation and last access FAT times
    after = bytearray()
    if version >= 7:
        after += b'\x00\x00' + struct.pack('<Q', 0x0001000000001234) + b'\x00' * 8
    after += struct.pack('<H', 0)                                   # localized name offset
    if version >= 9:
        after += b'\x00' * 4
    if version >= 8:
        after += b'\x00' * 4
    name_at = 8 + len(body) + 2 + len(after)
    tail = long_name.encode('utf-16-le') + b'\x00\x00' + localized
    block = body + struct.pack('<H', name_at if offset is None else offset) + after + tail
    return block, name_at


def file_entry(version, **kwargs):
    """A file entry shell item (class 0x32) with an 8.3 name and one 0xbeef0004 block."""
    head = bytearray(b'\x00\x00\x32\x00') + struct.pack('<IIH', 1024, 0x12345678, 0x20) + SHORT
    block, _name_at = beef0004(version, **kwargs)
    first_block = len(head)
    ext = struct.pack('<HHI', 8 + len(block) + 2, version, 0xBEEF0004) + block + struct.pack('<H', first_block)
    item = head + ext
    struct.pack_into('<H', item, 0, len(item))
    return bytes(item)


class Beef0004LongNameTest(unittest.TestCase):
    readers = (('windows_lnk', windows_lnk._beef_longname),             # pylint: disable=protected-access
               ('windowsShellbags', windowsShellbags._beef_longname))   # pylint: disable=protected-access

    def test_layout_puts_the_name_where_libfwsi_says(self):
        for version, expected in ((3, 20), (7, 38), (8, 42), (9, 46)):
            self.assertEqual(beef0004(version)[1], expected)

    def test_long_name_is_read_from_the_stored_offset_for_each_version(self):
        for version in (3, 7, 8, 9):
            item = file_entry(version)
            for label, reader in self.readers:
                with self.subTest(reader=label, version=version):
                    self.assertEqual(reader(item), LONG)

    def test_shell_item_names_use_the_long_name(self):
        for version in (3, 7, 8, 9):
            item = file_entry(version)
            with self.subTest(version=version):
                self.assertEqual(windows_lnk._shell_item_name(item), LONG)    # pylint: disable=protected-access
                self.assertEqual(windowsShellbags._shell_item(item)[0], LONG)  # pylint: disable=protected-access

    def test_trailing_localized_name_is_not_appended(self):
        item = file_entry(9, localized=b'@shell32.dll,-21781\x00')
        for label, reader in self.readers:
            with self.subTest(reader=label):
                self.assertEqual(reader(item), LONG)

    def test_offset_outside_the_block_falls_back_to_the_short_name(self):
        item = file_entry(9, offset=0x7FFF)
        for label, reader in self.readers:
            with self.subTest(reader=label):
                self.assertIsNone(reader(item))
        self.assertEqual(windows_lnk._shell_item_name(item), 'LONGFI~1.TXT')  # pylint: disable=protected-access

    def test_version_below_3_has_no_long_name(self):
        old = bytearray(file_entry(9))
        struct.pack_into('<H', old, old.find(b'\x04\x00\xef\xbe') - 2, 2)
        for label, reader in self.readers:
            with self.subTest(reader=label):
                self.assertIsNone(reader(old))


if __name__ == '__main__':
    unittest.main()
