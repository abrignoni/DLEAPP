"""Pin the Taskband Favorites reader of scripts/artifacts/windowsTaskbandPins.py. The items are built here from
the libfwsi shell item and extension block layouts and the libfwps property store layout, in the shapes measured
on the known-data VM; the names, ids and time are made up."""
import datetime
import pathlib
import struct
import sys
import unittest
import uuid

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsTaskbandPins as tb
# pylint: enable=wrong-import-position

STAMP = 134382479518592406
USER_PINNED = '1f3427c8-5c10-4210-aa03-2ee45287d668'   # the User Pinned folder root
APPS_FOLDER = '4234d49b-0245-4df3-b780-3893943456e1'   # the Applications folder root
WHEN = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(microseconds=STAMP // 10)


def utf16z(text):
    return text.encode('utf-16-le') + b'\x00\x00'


def block(kind, body):
    """An extension block: size, version 0, signature 0xbeefXXXX, body, and the first extension block offset."""
    return struct.pack('<HHI', 8 + len(body) + 2, 0, 0xBEEF0000 | kind) + body + b'\x00\x00'


def text_block(kind, text):
    return block(kind, b'\x02\x00' + utf16z(text))


def name_block(name):
    """A 0xbeef0004 block whose long name sits at the offset stored at byte 16."""
    # creation and access FAT times, the long name offset (from the block's start: 8-byte header, 8 bytes of
    # times, the 2-byte offset and 20 bytes of other fields), then the name
    body = struct.pack('<II', 0, 0) + struct.pack('<H', 8 + 8 + 2 + 20) + b'\x00' * 20 + utf16z(name)
    return block(0x04, body)


def with_offset(item_head, blocks):
    """A shell item: a size, the head, the blocks, each block ending with the offset of the first block."""
    first = 2 + len(item_head)
    fixed = b''
    for raw in blocks:
        fixed += raw[:-2] + struct.pack('<H', first)
    body = item_head + fixed
    return struct.pack('<H', 2 + len(body)) + body


def root_item(guid):
    return struct.pack('<H', 20) + b'\x1f\x80' + uuid.UUID(guid).bytes_le


def file_item(short, blocks, kind=0x32):
    head = bytes([kind, 0]) + b'\x00' * 10 + short.encode('ascii') + b'\x00'
    if len(head) % 2:
        head += b'\x00'
    return with_offset(head, blocks)


def property_set(format_id, records):
    body = b''
    for prop_id, text in records:
        count = len(text) + 1
        value = struct.pack('<HHI', 0x1F, 0, count) + utf16z(text)
        record = struct.pack('<IIB', 0, prop_id, 0) + value
        body += struct.pack('<I', len(record)) + record[4:]
    body += b'\x00\x00\x00\x00'
    return struct.pack('<I', 24 + len(body)) + b'1SPS' + uuid.UUID(format_id).bytes_le + body


def apps_item(app_id, name, blocks):
    sets = (property_set('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3', [(5, app_id)])
            + property_set('b725f130-47ef-101a-a5f1-02608c9eebac', [(10, name)]) + b'\x00\x00\x00\x00')
    head = b'\x00\x00' + struct.pack('<H', 0) + b'APPS' + b'\x00' * 8 + struct.pack('<I', len(sets)) + sets
    return with_offset(head, blocks)


def id_list(*items):
    return b''.join(items) + b'\x00\x00'


def favorites(*lists):
    out = b''
    for raw in lists:
        out += b'\x00' + struct.pack('<I', len(raw)) + raw
    return out + b'\xff'


SHORTCUT = id_list(root_item(USER_PINNED), file_item('TASKBAR', [name_block('TaskBar')], 0x31),
                   file_item('SHORTC~1.LNK', [name_block('Shortcut One.lnk'), block(0x2B, struct.pack('<Q', STAMP)),
                                              text_block(0x1D, '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\one.exe'),
                                              text_block(0x1D, 'second.copy'),
                                              text_block(0x1E, 'UserPinned')]))
PACKAGED = id_list(root_item(APPS_FOLDER),
                   apps_item('Vendor.App_abc!App', 'Some App', [text_block(0x1D, 'Vendor.App_abc!App'),
                                                                text_block(0x1E, 'SystemPinned')]))


class FavoritesFramingTest(unittest.TestCase):
    def test_reads_every_pin_and_stops_at_the_final_ff(self):
        entries, problem = tb.favorites_entries(favorites(SHORTCUT, PACKAGED))
        self.assertEqual((entries, problem), ([SHORTCUT, PACKAGED], ''))

    def test_a_wrong_separator_stops_and_is_reported(self):
        raw = bytearray(favorites(SHORTCUT, PACKAGED))
        raw[1 + 4 + len(SHORTCUT)] = 0x07
        entries, problem = tb.favorites_entries(bytes(raw))
        self.assertEqual(entries, [SHORTCUT])
        self.assertIn('0x07', problem)

    def test_a_length_past_the_end_is_reported(self):
        raw = favorites(SHORTCUT)[:-10]
        entries, problem = tb.favorites_entries(raw)
        self.assertEqual(entries, [])
        self.assertIn('past the end', problem)

    def test_missing_final_byte_is_reported(self):
        self.assertEqual(tb.favorites_entries(favorites(SHORTCUT)[:-1]), ([SHORTCUT], 'value ends without the final 0xff'))

    def test_empty_value(self):
        self.assertEqual(tb.favorites_entries(b''), ([], ''))


class PinTest(unittest.TestCase):
    def test_shortcut_pin(self):
        kind, folders, shortcut, app_id, pin_type, stamp, name = tb.read_pin(SHORTCUT)
        self.assertEqual((kind, folders, shortcut, pin_type, name), ('Shortcut', ['TaskBar'], 'Shortcut One.lnk',
                                                                     'UserPinned', ''))
        self.assertEqual(app_id, '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\one.exe')   # the first 0xbeef001d
        self.assertEqual(stamp, WHEN)

    def test_packaged_pin_reads_the_property_store(self):
        kind, folders, shortcut, app_id, pin_type, stamp, name = tb.read_pin(PACKAGED)
        self.assertEqual((kind, folders, shortcut, app_id, pin_type, stamp, name),
                         ('Packaged app', [], '', 'Vendor.App_abc!App', 'SystemPinned', '', 'Some App'))

    def test_unknown_root_is_other(self):
        other = id_list(root_item('20d04fe0-3aea-1069-a2d8-08002b30309d'), file_item('X', [text_block(0x1E, 'X')]))
        self.assertEqual(tb.read_pin(other)[0], 'Other ({20d04fe0-3aea-1069-a2d8-08002b30309d})')

    def test_overrunning_item_is_unreadable(self):
        self.assertIsNone(tb.read_pin(b'\xff\x00\x1f\x80'))


if __name__ == '__main__':
    unittest.main()
