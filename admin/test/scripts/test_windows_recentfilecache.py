"""Pin the RecentFileCache.bcf artifact (scripts/artifacts/windowsRecentFileCache.py).

The files are written here in the layout the artifact reads: the signature, the 16 bytes before the first entry,
then each entry's character count, its UTF-16 path and a two-byte terminator. The paths are made up.
"""
import datetime
import os
import pathlib
import struct
import zlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsRecentFileCache as rfc
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
PATHS = ['c:\\tools\\first.exe', 'c:\\users\\someone\\downloads\\second program.exe']


def bcf(paths, signature=b'\xfe\xff\xee\xff'):
    """A RecentFileCache.bcf holding paths, with the CRC-32 of the rest of the file at 0x10."""
    body = b''.join(struct.pack('<i', len(p)) + p.encode('utf-16-le') + b'\0\0' for p in paths)
    head = signature + bytes(12)
    return head + struct.pack('<I', zlib.crc32(head + body) & 0xFFFFFFFF) + body


class Entries(unittest.TestCase):
    def test_entries(self):
        self.assertEqual(rfc.entries(bcf(PATHS)), (PATHS, ''))
        self.assertEqual(rfc.entries(bcf([])), ([], ''))

    def test_damaged_files(self):
        self.assertEqual(rfc.entries(bcf(PATHS, signature=b'NOPE')),
                         ([], 'does not start with the RecentFileCache signature'))
        whole = bcf(PATHS)
        second = 0x14 + 4 + 2 * len(PATHS[0]) + 2
        self.assertEqual(rfc.entries(whole[:-6]),
                         (PATHS[:1], f'has an entry at offset {second} that runs past the end of the file'))
        self.assertEqual(rfc.entries(whole + b'\x01\x00'),
                         (PATHS, f'ends inside the length of an entry at offset {len(whole)}'))
        unterminated = bytearray(whole)
        unterminated[second - 2:second] = b'x\0'
        self.assertEqual(rfc.entries(bytes(unterminated)),
                         ([], 'has an entry at offset 20 that is not followed by its terminator'))
        negative = whole[:0x14] + struct.pack('<i', -3) + whole[0x18:]
        self.assertEqual(rfc.entries(negative)[1], 'has an entry at offset 20 that runs past the end of the file')
        last = len(whole) - 2 - 2 * len(PATHS[1]) - 4
        self.assertEqual(rfc.entries(whole[:-2]),
                         (PATHS[:1], f'has an entry at offset {last} that runs past the end of the file'))
        minus_one = whole[:0x14] + struct.pack('<i', -1) + whole[0x18:]
        self.assertEqual(rfc.entries(minus_one), ([], 'has an entry at offset 20 that runs past the end of the file'))


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def run_artifact(self, files, seeker=None):
        found = []
        for relative, data in files.items():
            path = os.path.join(self.folder.name, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as handle:
                handle.write(data)
            found.append(path)
        context = mock.Mock()
        context.get_files_found.return_value = found + [self.folder.name]
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        context.get_seeker.return_value = seeker(found) if seeker else None
        with mock.patch.object(rfc, 'logfunc') as log:
            result = rfc.windowsRecentFileCache.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_rows_with_the_time_the_seeker_recorded(self):
        member = 'C/Windows/AppCompat/Programs/RecentFileCache.bcf'
        when = datetime.datetime(2015, 3, 25, 15, 15, 52, tzinfo=UTC)

        def seeker(found):
            return mock.Mock(file_infos={found[0]: mock.Mock(modification_date=when.timestamp())})

        (headers, rows, located), logged = self.run_artifact({member: bcf(PATHS)}, seeker)
        self.assertEqual(headers, (('File Last Written', 'datetime'), 'Program Path', 'Entry', 'File Checksum Matches'))
        self.assertEqual(rows, [(when, PATHS[0], 1, 'Yes'), (when, PATHS[1], 2, 'Yes')])
        self.assertEqual(located, os.path.join(self.folder.name, member))
        self.assertEqual(logged, [])

    def test_no_seeker_and_a_damaged_file(self):
        member = 'C/Windows/AppCompat/Programs/RECENTFILECACHE.BCF'
        (_, rows, located), logged = self.run_artifact({member: bcf(PATHS)[:-6], 'C/other.txt': b'x'})
        self.assertEqual(rows, [('', PATHS[0], 1, 'No')])
        self.assertEqual(located, os.path.join(self.folder.name, member))
        self.assertEqual(len(logged), 2)
        self.assertIn('runs past the end of the file; 1 entries read before it', logged[0])
        self.assertIn('holds a CRC-32 at 0x10 that does not match its contents', logged[1])

    def test_a_file_with_no_entries_names_no_source(self):
        (_, rows, located), logged = self.run_artifact({'C/RecentFileCache.bcf': bcf([], signature=b'NOPE')})
        self.assertEqual((rows, located), ([], ''))
        self.assertIn('does not start with the RecentFileCache signature; 0 entries read before it', logged[0])


if __name__ == '__main__':
    unittest.main()
