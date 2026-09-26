"""Pin the NTFS metadata readers in scripts/windows_ntfs.py and the three artifacts
built on them.

The USN records are built here field by field in the order Microsoft documents
USN_RECORD_V2 and USN_RECORD_V3, so they test the reading of that layout rather
than an image; the Windows-written journals the artifact was run against are
named in its notes. The Zone.Identifier bytes are the 26 bytes resident in
record 12938 of the public Windows XP $MFT sample in omerbenamram/mft. The $MFT
and $Secure:$SDS tests read the NTFS fixture the raw image seeker tests use, and
the paths are compared against qnxprobe's own walk of the same volume, a second
implementation, never against values read back from the code under test.
"""
import gzip
import io
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import scripts.raw_image as raw_image  # pylint: disable=wrong-import-position
from scripts import windows_ntfs as wn  # pylint: disable=wrong-import-position
from scripts.artifacts.windowsMft import mft_rows  # pylint: disable=wrong-import-position
from scripts.artifacts.windowsZoneIdentifier import zone_row  # pylint: disable=wrong-import-position

FIXTURE = REPO_ROOT / 'admin' / 'test' / 'data' / 'raw_images' / 'ntfs-streams.img.gz'

# 2021-01-01 00:00:00 UTC as a FILETIME: (1609459200 + 11644473600) * 10**7
NEW_YEAR_2021 = 132539328000000000


def usn_v2(name, file_ref, parent_ref, usn, stamp, reason, attributes, source=0):
    """A USN_RECORD_V2 in the documented field order, padded to eight bytes."""
    encoded = name.encode('utf-16-le')
    length = (60 + len(encoded) + 7) & ~7
    head = struct.pack('<IHHQQqqIIIIHH', length, 2, 0, file_ref, parent_ref, usn, stamp,
                       reason, source, 0, attributes, len(encoded), 60)
    return (head + encoded).ljust(length, b'\x00')


def usn_v3(name, file_ref, parent_ref, usn, stamp, reason, attributes):
    """A USN_RECORD_V3: the V2 fields with 128-bit file references."""
    encoded = name.encode('utf-16-le')
    length = (76 + len(encoded) + 7) & ~7
    head = struct.pack('<IHH16s16sqqIIIIHH', length, 3, 0, file_ref.to_bytes(16, 'little'),
                       parent_ref.to_bytes(16, 'little'), usn, stamp, reason, 0, 0,
                       attributes, len(encoded), 76)
    return (head + encoded).ljust(length, b'\x00')


class ValueTest(unittest.TestCase):
    def test_filetime(self):
        self.assertEqual(wn.filetime(NEW_YEAR_2021), datetime(2021, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(wn.filetime(NEW_YEAR_2021 + 12345678),
                         datetime(2021, 1, 1, 0, 0, 1, 234567, tzinfo=timezone.utc))
        self.assertEqual(wn.filetime(0), '')
        self.assertEqual(wn.filetime(0xFFFFFFFFFFFFFFFF), '')

    def test_split_reference(self):
        self.assertEqual(wn.split_reference((6 << 48) | 38), (38, 6))

    def test_flags_name_each_bit_and_keep_the_rest(self):
        self.assertEqual(wn.decode_flags(0x80000102, wn.USN_REASONS),
                         'DATA_EXTEND | FILE_CREATE | CLOSE')
        self.assertEqual(wn.decode_flags(0x04000100, wn.USN_REASONS), 'FILE_CREATE | 0x04000000')
        self.assertEqual(wn.decode_flags(0, wn.USN_SOURCES), '')
        self.assertEqual(wn.decode_flags(0x2020, wn.FILE_ATTRIBUTES),
                         'Archive | Not content indexed')

    def test_sid(self):
        # an owner offset of 0 means the descriptor names no owner
        data = (b'\x00' * 4 + bytes([1, 5]) + (5).to_bytes(6, 'big')
                + struct.pack('<5I', 21, 311151722, 437878493, 4115995562, 1000))
        self.assertEqual(wn.sid_string(data, 4), 'S-1-5-21-311151722-437878493-4115995562-1000')
        self.assertEqual(wn.sid_string(data, 0), '')
        self.assertEqual(wn.sid_string(data[:16], 4), '')


class NameTest(unittest.TestCase):
    def test_a_long_name_is_shown_before_its_dos_alias(self):
        record = wn.MftRecord(40, 1, 0x01, 0)
        times = (NEW_YEAR_2021,) * 4
        record.names = [((5 << 48) | 5, 2, 'LONGNA~1.TXT', times),
                        ((5 << 48) | 5, 1, 'LongName.txt', times),
                        ((7 << 48) | 7, 0, 'second link.txt', times)]
        self.assertEqual(record.best_name()[2], 'LongName.txt')
        self.assertEqual([name[2] for name in record.link_names()],
                         ['LongName.txt', 'second link.txt'])


class ParentTest(unittest.TestCase):
    """A parent reference is followed only while its sequence number still names
    the directory it was written for."""

    def test_reused_and_deleted_parents(self):
        index = wn.MftIndex(io.BytesIO(b''))
        index.directories = {
            5: (5, True, [((5 << 48) | 5, 3, '.')]),
            40: (3, True, [((5 << 48) | 5, 1, 'live')]),     # in use, sequence 3
            41: (4, False, [((5 << 48) | 5, 1, 'gone')]),    # freed at sequence 3, so now 4
        }
        self.assertEqual(index.directory_path((3 << 48) | 40), 'live')
        self.assertIsNone(index.directory_path((2 << 48) | 40))     # the record was reused
        self.assertEqual(index.directory_path((3 << 48) | 41), 'gone')
        self.assertIsNone(index.directory_path((2 << 48) | 41))     # a later use of the record
        self.assertEqual(index.directory_path(5), '')                # sequence 0: no check
        self.assertEqual(index.path_of_name(((3 << 48) | 40, 1, 'file.txt', ())), 'live/file.txt')


class UsnTest(unittest.TestCase):
    def test_records_zeros_range_records_and_junk(self):
        first = usn_v2('report.docx', (3 << 48) | 1234, (5 << 48) | 5, 4096, NEW_YEAR_2021,
                       0x80000102, 0x20, source=0x8)
        range_record = struct.pack('<IHH', 80, 4, 0).ljust(80, b'\x01')
        second = usn_v3('a.txt', (2 << 48) | 77, (5 << 48) | 5, 8192, NEW_YEAR_2021 + 10,
                        0x00000200, 0x20)
        data = first + b'\x00' * 4000 + range_record + b'\xff' * 8 + second + b'\x00' * 64
        counts = {}
        records = list(wn.iter_usn(data, counts))
        self.assertEqual(counts, {'v4': 1, 'unparsed': 8})
        self.assertEqual([r.name for r in records], ['report.docx', 'a.txt'])
        self.assertEqual([r.version for r in records], [2, 3])
        one, two = records
        self.assertEqual((one.file_reference, one.parent_reference, one.usn, one.reason,
                          one.source_info, one.attributes, one.offset),
                         ((3 << 48) | 1234, (5 << 48) | 5, 4096, 0x80000102, 0x8, 0x20, 0))
        self.assertEqual(wn.filetime(one.timestamp), datetime(2021, 1, 1, tzinfo=timezone.utc))
        self.assertEqual((two.file_reference, two.usn, two.reason), ((2 << 48) | 77, 8192, 0x200))

    def test_a_record_cut_short_is_not_read(self):
        record = usn_v2('cut.txt', 1, 5, 0, NEW_YEAR_2021, 0x100, 0x20)
        counts = {}
        self.assertEqual(list(wn.iter_usn(record[:40], counts)), [])
        # its zero fields are skipped as zeros; the rest is passed over eight at a time
        self.assertEqual(counts['unparsed'], 32)


class ZoneIdentifierTest(unittest.TestCase):
    def test_the_windows_xp_stream(self):
        values = wn.read_zone_identifier(b'[ZoneTransfer]\r\nZoneId=3\r\n')
        self.assertEqual(values, [('ZoneTransfer', 'ZoneId', '3')])
        self.assertEqual(zone_row(values), ('3', 'URLZONE_INTERNET', '', '', ''))

    def test_urls_other_keys_and_utf16(self):
        text = ('[ZoneTransfer]\r\nZoneId=3\r\nReferrerUrl=https://example.com/\r\n'
                'HostUrl=https://example.com/a.exe\r\nAppZoneId=4\r\n[Other]\r\nKey=v\r\n')
        for data in (text.encode('utf-8'), text.encode('utf-16')):
            row = zone_row(wn.read_zone_identifier(data))
            self.assertEqual(row, ('3', 'URLZONE_INTERNET', 'https://example.com/a.exe',
                                   'https://example.com/', 'AppZoneId=4; [Other] Key=v'))

    def test_an_unnamed_zone_is_left_blank(self):
        self.assertEqual(zone_row([('ZoneTransfer', 'ZoneId', '1000')])[:2], ('1000', ''))
        self.assertEqual(zone_row([]), ('', '', '', '', ''))


class FixtureTest(unittest.TestCase):
    """$MFT and $Secure:$SDS read out of the NTFS fixture through the raw image seeker."""

    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp(prefix='windows_ntfs_test_')
        image = os.path.join(cls.work, 'ntfs-streams.img')
        with gzip.open(FIXTURE, 'rb') as src, open(image, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        with mock.patch.object(raw_image, 'logfunc', lambda *_a, **_k: None):
            cls.seeker = raw_image.FileSeekerRaw(image, os.path.join(cls.work, 'data'))
            cls.mft = cls.seeker.search('*/$MFT')[0]
            cls.sds = cls.seeker.search('*/$Secure:$SDS')[0]
        with open(cls.sds, 'rb') as handle:
            cls.owners = wn.sds_owners(handle.read())
        with open(cls.mft, 'rb') as handle:
            cls.index = wn.MftIndex(handle)
            handle.seek(0)
            cls.rows = list(mft_rows(handle, cls.index, cls.owners))

    @classmethod
    def tearDownClass(cls):
        cls.seeker.cleanup()
        shutil.rmtree(cls.work, ignore_errors=True)

    def _by_path(self):
        return {row[8]: row for row in self.rows}

    def test_the_paths_are_the_ones_qnxprobe_walks(self):
        walked = {member[len('lba0'):].rstrip('/') for member in self.seeker.name_list}
        in_use = set()
        for row in self.rows:
            if row[10] == 'Yes' and row[8] != '/':
                in_use.add(row[8])
                in_use.update(link for link in row[19].split('; ') if link)
        self.assertEqual(in_use, walked)
        self.assertEqual(len(walked), 31)

    def test_deleted_files_resolve_through_their_deleted_directory(self):
        deleted = [row for row in self.rows if row[10] == 'No']
        self.assertEqual(len(deleted), 965)
        self.assertEqual(sum(1 for row in deleted if row[8].startswith('/holes/')), 964)
        self.assertEqual([row[8] for row in deleted if not row[8].startswith('/holes/')],
                         ['/holes'])

    def test_streams_links_and_the_root(self):
        rows = self._by_path()
        self.assertEqual(rows['/downloads/setup.exe'][13], 'Zone.Identifier (114 bytes)')
        self.assertEqual(rows['/linked_a.txt'][19], '/linked_b.txt')
        self.assertEqual(rows['/journal.bin'][13], '$J (2,859,008 bytes); $Max (32 bytes)')
        # five of its twelve streams are in extension records
        self.assertEqual(len(rows['/manystreams.txt'][13].split('; ')), 12)
        self.assertEqual(rows['/'][9], '.')
        self.assertEqual(rows['/folder'][12], '')                  # a directory has no size

    def test_owner_sids_come_from_the_volume_s_descriptors(self):
        self.assertEqual(set(self.owners.values()), {'S-1-5-32-544'})
        owned = [row for row in self.rows if row[14]]
        self.assertEqual(len(owned), 10)
        self.assertEqual({row[8] for row in owned if row[8].startswith('/$MFT')},
                         {'/$MFTMirr'})

    def test_a_copy_that_does_not_sit_at_its_own_offset_is_passed_over(self):
        with open(self.sds, 'rb') as handle:
            data = handle.read()
        moved = b'\x00' * 16 + data
        self.assertEqual(wn.sds_owners(moved), {})


if __name__ == '__main__':
    unittest.main()
