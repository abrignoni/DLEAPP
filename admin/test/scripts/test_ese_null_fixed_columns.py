"""Pin that the ESE reader (scripts/vendor/impacket_ese.py) returns None for a fixed column whose bit is set in the
record's fixed-column null bitmap, and the stored value when the bit is clear, whatever bytes the column holds."""
import pathlib
import struct
import sys
import unittest
from collections import OrderedDict

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.vendor import impacket_ese
# pylint: enable=wrong-import-position

FILL = b'*'  # chRECFill, the byte ESE fills reorganised record space with


def columns(*specs):
    out = OrderedDict()
    for identifier, name, coltype, size in specs:
        out[name.encode()] = {'Record': {'Identifier': identifier, 'ColumnType': coltype, 'SpaceUsage': size,
                                         'CodePage': 1200}}
    return out


COLUMNS = columns((1, 'IsDeleted', impacket_ese.JET_coltypBit, 1),
                  (2, 'IsFolder', impacket_ese.JET_coltypBit, 1),
                  (3, 'Updated', impacket_ese.JET_coltypLongLong, 8),
                  (4, 'Count', impacket_ese.JET_coltypLong, 4))


def record(fixed_data, null_ids, last_fixed=4):
    """A record with no variable or tagged columns: header, fixed data, null bitmap."""
    bitmap = bytearray((last_fixed + 7) // 8)
    for identifier in null_ids:
        bitmap[(identifier - 1) // 8] |= 1 << ((identifier - 1) % 8)
    end_of_fixed = 4 + len(fixed_data) + len(bitmap)
    return struct.pack('<BBH', last_fixed, 127, end_of_fixed) + fixed_data + bytes(bitmap)


def decode(tag):
    reader = impacket_ese.ESENT_DB.__new__(impacket_ese.ESENT_DB)
    cursor = {'TableData': {'Columns': COLUMNS}}
    return reader._ESENT_DB__tagToRecord(cursor, tag)  # pylint: disable=protected-access


class NullFixedColumnTest(unittest.TestCase):
    def test_a_set_null_bit_gives_none_even_over_zero_bytes(self):
        rec = decode(record(bytes(14), null_ids=(1, 3)))
        self.assertIsNone(rec[b'IsDeleted'])
        self.assertIsNone(rec[b'Updated'])
        self.assertEqual((rec[b'IsFolder'], rec[b'Count']), (0, 0))

    def test_a_clear_null_bit_gives_the_bytes_even_when_they_are_fill(self):
        rec = decode(record(FILL * 14, null_ids=()))
        self.assertEqual(rec[b'IsDeleted'], 0x2A)
        self.assertEqual(rec[b'Updated'], struct.unpack('<Q', FILL * 8)[0])

    def test_the_offsets_of_later_columns_do_not_move_past_a_null_one(self):
        rec = decode(record(b'\x2a\xff' + struct.pack('<Q', 133214089042238679) + struct.pack('<l', 7),
                            null_ids=(1,)))
        self.assertEqual((rec[b'IsDeleted'], rec[b'IsFolder'], rec[b'Updated'], rec[b'Count']),
                         (None, 0xFF, 133214089042238679, 7))

    def test_a_ninth_fixed_column_uses_the_second_bitmap_byte(self):
        specs = [(i, f'C{i}', impacket_ese.JET_coltypUnsignedByte, 1) for i in range(1, 10)]
        global COLUMNS  # pylint: disable=global-statement
        saved, COLUMNS = COLUMNS, columns(*specs)
        try:
            rec = decode(record(bytes(range(1, 10)), null_ids=(9,), last_fixed=9))
        finally:
            COLUMNS = saved
        self.assertEqual([rec[f'C{i}'.encode()] for i in range(1, 10)], [1, 2, 3, 4, 5, 6, 7, 8, None])


if __name__ == '__main__':
    unittest.main()
