"""Pin the shell link reader's header times and TrackerDataBlock fields (scripts/windows_lnk.py), and the two Recent folders.

The links are built here byte by byte. The version 1 UUID is RFC 9562's test vector (appendix A.1), whose timestamp the
RFC gives as Tuesday, February 22, 2022 2:22:22.000000 PM GMT-05:00.
"""
import fnmatch
import os
import pathlib
import struct
import sys
import tempfile
import unittest
import uuid
from unittest import mock
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.windows_lnk import parse_lnk, tracker_columns, uuid_v1_parts  # noqa: E402  pylint: disable=wrong-import-position

CLSID = bytes.fromhex('0114020000000000c000000000000046')
EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
RFC_V1 = 'c232ab00-9414-11ec-b3c8-9f6bdeced846'
VOLUME = '6f1b8b47-3c2e-4f6a-9d21-5a0e7c4b1f93'
BIRTH_FILE = 'a1d2c3e4-1111-11ee-8222-000c29aabbcc'


def filetime(when, extra_ticks=0):
    """The FILETIME of a whole-second UTC time plus some 100-nanosecond ticks."""
    return int((when - EPOCH).total_seconds()) * 10_000_000 + extra_ticks


def link(times=(0, 0, 0), tracker=None):
    header = struct.pack('<I', 0x4C) + CLSID + struct.pack('<II', 0, 0x20) + struct.pack('<QQQ', *times)
    header += struct.pack('<IIIH', 0, 0, 1, 0) + b'\x00' * 10
    assert len(header) == 76
    extra = b''
    if tracker:
        machine, ids = tracker
        extra = struct.pack('<IIII', 0x60, 0xA0000003, 0x58, 0) + machine.ljust(16, b'\x00')
        extra += b''.join(uuid.UUID(i).bytes_le for i in ids)
        assert len(extra) == 0x60
    return header + extra + b'\x00\x00\x00\x00'


class TrackerTest(unittest.TestCase):
    def test_droid_identifiers_and_machine(self):
        parsed = parse_lnk(link(tracker=(b'TESTPC', (VOLUME, RFC_V1, VOLUME, BIRTH_FILE))))
        self.assertEqual(parsed['machine_id'], 'TESTPC')
        self.assertEqual((parsed['droid_volume'], parsed['droid_file'], parsed['birth_droid_volume'], parsed['birth_droid_file']),
                         (VOLUME, RFC_V1, VOLUME, BIRTH_FILE))
        self.assertEqual(tracker_columns(parsed),
                         (VOLUME, RFC_V1, datetime(2022, 2, 22, 19, 22, 22, tzinfo=timezone.utc), '9f:6b:de:ce:d8:46',
                          VOLUME, BIRTH_FILE))

    def test_no_tracker_block(self):
        parsed = parse_lnk(link())
        self.assertEqual(parsed['machine_id'], '')
        self.assertEqual(tracker_columns(parsed), ('', '', '', '', '', ''))

    def test_only_version_1_rfc_uuids_give_a_time_and_node(self):
        self.assertEqual(uuid_v1_parts('9e7d2a40-6c1b-4f7e-b6a3-0d5c8e2f1a47'), ('', ''))   # version 4
        self.assertEqual(uuid_v1_parts('1b4e28ba-2fa1-11d2-083f-0016d3cca427'), ('', ''))   # version 1 bits, NCS variant
        self.assertEqual(uuid_v1_parts('not a uuid'), ('', ''))
        self.assertEqual(uuid_v1_parts(''), ('', ''))
        self.assertEqual(uuid_v1_parts(None), ('', ''))
        when, node = uuid_v1_parts(BIRTH_FILE)
        self.assertEqual(node, '00:0c:29:aa:bb:cc')
        self.assertEqual(when.tzinfo, timezone.utc)


class HeaderTimeTest(unittest.TestCase):
    def test_times_are_cut_to_whole_microseconds(self):
        base = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        parsed = parse_lnk(link((filetime(base, 1234567), filetime(base, 9), filetime(base, 9_999_999))))
        self.assertEqual(parsed['target_created'], datetime(2024, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc))
        self.assertEqual(parsed['target_accessed'], base)
        self.assertEqual(parsed['target_modified'], datetime(2024, 1, 2, 3, 4, 5, 999999, tzinfo=timezone.utc))

    def test_zero_time_is_blank(self):
        parsed = parse_lnk(link())
        self.assertEqual((parsed['target_created'], parsed['target_accessed'], parsed['target_modified']), ('', '', ''))


class _Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return path


class RecentFoldersTest(unittest.TestCase):
    def test_each_folder_has_its_own_artifact(self):
        from scripts.artifacts import windowsLnk  # pylint: disable=import-outside-toplevel
        recent = windowsLnk.__artifacts_v2__['windowsLnkRecent']['paths']
        office = windowsLnk.__artifacts_v2__['windowsLnkOfficeRecent']['paths']
        windows_link = 'root/p2/Users/u/AppData/Roaming/Microsoft/Windows/Recent/a.lnk'
        office_link = 'root/p2/Users/u/AppData/Roaming/Microsoft/Office/Recent/b.LNK'
        old_profile = 'root/p2/Documents and Settings/u/Application Data/Microsoft/Office/Recent/c.lnk'
        self.assertTrue(any(fnmatch.fnmatchcase(windows_link, p) for p in recent))
        self.assertFalse(any(fnmatch.fnmatchcase(windows_link, p) for p in office))
        xp_link = 'root/p1/Documents and Settings/u/Recent/d.lnk'
        self.assertTrue(any(fnmatch.fnmatchcase(xp_link, p) for p in recent))
        self.assertFalse(any(fnmatch.fnmatchcase(xp_link, p) for p in office))
        self.assertFalse(windowsLnk._office_recent(xp_link[len('root/'):]))  # pylint: disable=protected-access
        for member in (office_link, old_profile):
            self.assertTrue(any(fnmatch.fnmatchcase(member, p) for p in office), member)
            # the XP Recent pattern's wildcard reaches the Office folder; the artifact leaves it
            self.assertTrue(windowsLnk._office_recent(member[len('root/'):]), member)  # pylint: disable=protected-access
        self.assertFalse(any(fnmatch.fnmatchcase(office_link, p) for p in recent))
        self.assertFalse(any(fnmatch.fnmatchcase('root/p2/Users/u/AppData/Roaming/Microsoft/Office/Recent/index.dat',
                                                 p) for p in office))

    def test_office_links_are_read_and_a_file_that_is_not_a_link_is_counted(self):
        from scripts.artifacts import windowsLnk  # pylint: disable=import-outside-toplevel
        with tempfile.TemporaryDirectory() as folder:
            good = os.path.join(folder, 'b.LNK')
            bad = os.path.join(folder, 'a.lnk')
            with open(good, 'wb') as handle:
                handle.write(link())
            with open(bad, 'wb') as handle:
                handle.write(b'not a link')
            with mock.patch.object(windowsLnk, 'logfunc') as log:
                headers, rows, source = windowsLnk.windowsLnkOfficeRecent.__wrapped__(_Context([good, bad]))
        self.assertEqual(headers[-1], 'Source File')
        self.assertEqual([row[-1] for row in rows], [good])
        self.assertEqual(len(rows[0]), len(headers))
        self.assertEqual(source, good)
        log.assert_called_once_with('Office Recent Shell Links: 1 file(s) named .lnk did not read as a shell link '
                                    'and were not reported')


if __name__ == '__main__':
    unittest.main()
