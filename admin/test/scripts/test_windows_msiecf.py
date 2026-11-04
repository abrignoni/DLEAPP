"""Pin scripts/windows_msiecf.py on an index.dat built here byte by byte (made-up values)."""
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_msiecf as msiecf  # pylint: disable=wrong-import-position


def url_record(location, filename, primary, secondary, last_checked, hits, directory=0, blocks=2):
    record = bytearray(blocks * 128)
    record[0:4] = b'URL '
    struct.pack_into('<IQQI', record, 4, blocks, secondary, primary, 0x3A1B2C3D)
    struct.pack_into('<II', record, 32, 1234, 0)
    struct.pack_into('<I', record, 52, 104)
    record[56] = directory
    name_at = 104 + ((len(location) + 1 + 7) // 8) * 8
    struct.pack_into('<IIII', record, 60, name_at, 0x41, name_at + 16, 6)
    struct.pack_into('<II', record, 80, last_checked, hits)
    record[104:104 + len(location)] = location
    record[name_at:name_at + len(filename)] = filename
    record[name_at + 16:name_at + 22] = b'HTTP/1'
    return bytes(record)


def index_dat(records):
    data = bytearray(0x4000)
    data[0:28] = b'Client UrlCache MMF Ver 5.2\x00'
    struct.pack_into('<I', data, 72, 1)
    data[80:88] = b'ABCD1234'
    for offset, raw, allocated in records:
        if len(data) < offset + len(raw):
            data.extend(b'\x00' * (offset + len(raw) - len(data)))
        data[offset:offset + len(raw)] = raw
        if allocated:
            for block in range(len(raw) // 128):
                index = (offset - 0x4000) // 128 + block
                data[0x250 + index // 8] |= 1 << (index % 8)
    return bytes(data)


class ReaderTest(unittest.TestCase):
    def test_records_fields_and_allocation(self):
        first = url_record(b'http://example.invalid/a', b'a[1].htm', 0x01D0000000000000, 0x01C0000000000000,
                           0x5A2E3B21, 3)
        second = url_record(b'http://example.invalid/b', b'b[1].htm', 1, 2, 0, 0)
        version, directories, records = msiecf.parse(index_dat([(0x4000, first, True), (0x4100, second, False)]))
        self.assertEqual((version, directories), ('5.2', ['ABCD1234']))
        self.assertEqual([(r['offset'], r['allocated'], r['location'], r['filename'], r['hits']) for r in records],
                         [(0x4000, True, 'http://example.invalid/a', 'a[1].htm', 3),
                          (0x4100, False, 'http://example.invalid/b', 'b[1].htm', 0)])
        self.assertEqual((records[0]['primary'], records[0]['secondary'], records[0]['size'], records[0]['data']),
                         (0x01D0000000000000, 0x01C0000000000000, 1234, b'HTTP/1'))

    def test_a_record_partly_allocated_is_skipped(self):
        raw = index_dat([(0x4000, url_record(b'http://x.invalid/', b'x', 1, 1, 0, 0), True)])
        raw = bytearray(raw)
        raw[0x250] = 0x02
        self.assertEqual(msiecf.parse(bytes(raw))[2], [])

    def test_fat_datetime(self):
        # 2004-08-20 10:54:20: date (24 << 9) | (8 << 5) | 20, time (10 << 11) | (54 << 5) | 10
        value = ((10 << 11) | (54 << 5) | 10) << 16 | ((24 << 9) | (8 << 5) | 20)
        self.assertEqual(msiecf.fat_datetime(value), (2004, 8, 20, 10, 54, 20))
        self.assertIsNone(msiecf.fat_datetime(0))
        self.assertIsNone(msiecf.fat_datetime(0xFFFFFFFF))

    def test_other_versions_and_files_are_refused(self):
        with self.assertRaises(msiecf.MsiecfError):
            msiecf.parse(b'Client UrlCache MMF Ver 4.7\x00' + b'\x00' * 0x4000)
        with self.assertRaises(msiecf.MsiecfError):
            msiecf.parse(b'\x00' * 0x4000)


if __name__ == '__main__':
    unittest.main()
