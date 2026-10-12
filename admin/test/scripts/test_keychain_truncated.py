"""A classic keychain's deleted and out-of-range records are skipped, not crashed on.

Apple marks a deleted record number with a free-list link (low bit set) or zero; the Magnet 2021 CTF macOS
login.keychain-db holds 27 of these, and following one read a garbage record header that made the reader raise
struct.error and lose every keychain in the extraction. These tests build a small 'kych'-shaped buffer and pin that a
deleted record number is skipped silently, a live record whose body runs past the end is skipped and counted, a
string length running past the end is still clamped (the reader's long-standing lenient behaviour), and none of it
raises.
"""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import Keychains as kc
# pylint: enable=wrong-import-position

_ATOM = 4


def reader(buf):
    """A _KeychainReader over buf with no file and no schema read."""
    r = kc._KeychainReader.__new__(kc._KeychainReader)  # pylint: disable=protected-access
    r.buf = buf
    r.skipped = 0
    return r


class LeafTest(unittest.TestCase):
    def test_u32_in_range_and_past_end(self):
        r = reader(struct.pack(">I", 0x01020304) + b"\x00\x00")
        self.assertEqual(r._u32(0), 0x01020304)  # pylint: disable=protected-access
        with self.assertRaises(kc._KeychainFormatError):  # pylint: disable=protected-access
            r._u32(3)  # 3+4 > 6  # pylint: disable=protected-access
        with self.assertRaises(kc._KeychainFormatError):  # pylint: disable=protected-access
            r._u32(-1)  # pylint: disable=protected-access

    def test_string_length_past_end_is_clamped(self):
        # length says 100 bytes but only 3 follow: the reader returns the 3, as it always has
        buf = struct.pack(">I", 100) + b"abc"
        self.assertEqual(reader(buf)._string(0), b"abc")  # pylint: disable=protected-access

    def test_creator_is_read_as_four_bytes_not_a_string(self):
        # read as a string, the creator's own four bytes became a length and pulled in everything after it
        header = kc._RECORD_HEADER_ATOMS * _ATOM  # pylint: disable=protected-access
        record = (struct.pack(">I", 0) + b"\x00" * (header - _ATOM)
                  + struct.pack(">I", header + _ATOM) + b"abcd" + b"x" * 64)
        item = reader(record)._record(0, ("crtr",))  # pylint: disable=protected-access
        self.assertEqual(item["crtr"], "abcd")

    def test_string_position_past_end_raises(self):
        with self.assertRaises(kc._KeychainFormatError):  # pylint: disable=protected-access
            reader(b"\x00\x00")._string(0)  # pylint: disable=protected-access


class RecordWalkTest(unittest.TestCase):
    """A table whose record-number list mixes live, deleted and out-of-range entries."""

    def _one_attr_record(self):
        # a 6-atom header, one attribute offset pointing at the string after it, then 'svc'
        header = kc._RECORD_HEADER_ATOMS * _ATOM  # pylint: disable=protected-access
        attr_rel = header + _ATOM
        return (struct.pack(">I", 0) + b"\x00" * (header - _ATOM)
                + struct.pack(">I", attr_rel) + struct.pack(">I", 3) + b"svc")

    def _reader_with_entries(self, entries, record, pad=0):
        """A reader whose generic-password table lists `entries` (record-number offsets, table-relative) and
        places `record` at the first entry. `pad` extra bytes follow, so an entry can point at an even in-range
        base whose record body still runs past the end."""
        table_header = kc._TABLE_HEADER_SIZE  # pylint: disable=protected-access
        rec0 = table_header + _ATOM * len(entries)
        size = rec0 + len(record) + pad
        buf = bytearray(size)
        struct.pack_into(">I", buf, 6 * _ATOM, len(entries))
        for i, off in enumerate(entries):
            struct.pack_into(">I", buf, table_header + _ATOM * i, off)
        buf[rec0:rec0 + len(record)] = record
        r = reader(bytes(buf))
        r.tables = {kc._REC_GENERIC_PASSWORD: 0}  # pylint: disable=protected-access
        return r, rec0

    def test_deleted_record_numbers_are_skipped_silently(self):
        # a live record, a free-list link (odd), and a zero: only the live one is read, none counted
        r, rec0 = self._reader_with_entries([0, 29, 0], self._one_attr_record())
        buf = bytearray(r.buf)
        struct.pack_into(">I", buf, kc._TABLE_HEADER_SIZE, rec0)  # pylint: disable=protected-access
        r.buf = bytes(buf)
        items = list(r._records(kc._REC_GENERIC_PASSWORD, ("svce",)))  # pylint: disable=protected-access
        self.assertEqual([i["svce"] for i in items], [b"svc"])
        self.assertEqual(r.skipped, 0)

    def test_a_live_record_past_the_end_is_skipped_and_counted(self):
        r, rec0 = self._reader_with_entries([0, 0], self._one_attr_record())
        buf = bytearray(r.buf)
        bad_base = (len(buf) - 8) & ~1    # even (a live slot), base in range, header runs past the end
        struct.pack_into(">I", buf, kc._TABLE_HEADER_SIZE, rec0)  # pylint: disable=protected-access
        struct.pack_into(">I", buf, kc._TABLE_HEADER_SIZE + _ATOM, bad_base)  # pylint: disable=protected-access
        r.buf = bytes(buf)
        items = list(r._records(kc._REC_GENERIC_PASSWORD, ("svce",)))  # pylint: disable=protected-access
        self.assertEqual([i["svce"] for i in items], [b"svc"])
        self.assertEqual(r.skipped, 1)

    def test_an_absent_relation_yields_nothing(self):
        r = reader(b"")
        r.tables = {}
        self.assertEqual(list(r._records(kc._REC_GENERIC_PASSWORD, ("svce",))), [])  # pylint: disable=protected-access


if __name__ == "__main__":
    unittest.main()
