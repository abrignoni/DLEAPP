"""Pin the record reading in scripts/artifacts/macosVolumeStatusDatabase.py.

Every record below is written by the test; no volume UUID comes from a real device.
"""
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosVolumeStatusDatabase as artifact  # pylint: disable=wrong-import-position
from scripts.search_files import FileInfo  # pylint: disable=wrong-import-position

FILE = 'private/var/db/volinfo.database'
VIEW = 'System/Volumes/Data/' + FILE
UUID_A = '00000000-AAAA-4AAA-8AAA-000000000001'
UUID_B = '00000000-BBBB-4BBB-8BBB-000000000002'
UUID_C = '00000000-CCCC-3CCC-8CCC-000000000003'


def record(uuid, flags):
    return f'{uuid}: {flags}\n'.encode('ascii')


class FileSeekerZip:  # the name the artifact reads to trust recorded times
    def __init__(self):
        self.file_infos = {}


class FileSeekerDir:
    def __init__(self):
        self.file_infos = {}


class Context:
    def __init__(self, root, files, seeker=None):
        self.root = root
        self.files = files
        self.seeker = seeker

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        return self.seeker


class ParseDatabaseTest(unittest.TestCase):
    def test_records_are_47_bytes_and_keep_file_order(self):
        data = record(UUID_B, '00000001') + record(UUID_A, '00000000')
        self.assertEqual(len(data), 94)
        self.assertEqual(artifact.parse_database(data), ([
            (1, UUID_B, '00000001', 'enabled'),
            (2, UUID_A, '00000000', 'disabled'),
        ], 0, 'current'))

    def test_permissions_come_from_bit_one_only(self):
        data = record(UUID_A, '00000003') + record(UUID_B, '0000000a') + record(UUID_C, 'FFFFFFFE')
        self.assertEqual([row[2:] for row in artifact.parse_database(data)[0]],
                         [('00000003', 'enabled'), ('0000000a', 'disabled'),
                          ('FFFFFFFE', 'disabled')])

    def test_flags_that_are_not_hex_are_kept_as_stored_with_no_permissions(self):
        records, unread, layout = artifact.parse_database(record(UUID_A, '0000000G'))
        self.assertEqual(records, [(1, UUID_A, '0000000G', '')])
        self.assertEqual((unread, layout), (0, 'current'))

    def test_reading_stops_at_the_first_record_without_its_separators(self):
        bad = record(UUID_B, '00000001').replace(b': ', b'; ')
        data = record(UUID_A, '00000001') + bad + record(UUID_C, '00000001')
        records, unread, layout = artifact.parse_database(data)
        self.assertEqual([row[1] for row in records], [UUID_A])
        self.assertEqual((unread, layout), (94, 'current'))

    def test_a_short_tail_is_counted_not_read(self):
        records, unread, _layout = artifact.parse_database(record(UUID_A, '00000001') + b'0000')
        self.assertEqual((len(records), unread), (1, 4))

    def test_empty_and_older_layout(self):
        self.assertEqual(artifact.parse_database(b''), ([], 0, 'empty'))
        old = b'0123456789ABCDEF: 00000001\n'
        self.assertEqual(artifact.parse_database(old + old), ([], 54, 'old'))

    def test_bytes_that_are_no_layout_read_as_nothing(self):
        self.assertEqual(artifact.parse_database(b'x' * 60), ([], 60, 'current'))


class VolumeStatusDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        patcher = patch.object(artifact, 'logfunc')
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def run_artifact(self, paths, seeker=None):
        return artifact.macosVolumeStatusDatabase.__wrapped__(
            Context(self.root, list(paths), seeker))

    def logged(self, text):
        return any(text in str(call) for call in self.log.call_args_list)

    def test_one_row_per_record(self):
        path = self.write(FILE, record(UUID_A, '00000001') + record(UUID_C, '00000000'))
        headers, rows, source = self.run_artifact([path])
        self.assertEqual(headers[0], ('File Modified (UTC)', 'datetime'))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [('', 1, UUID_A, '00000001', 'enabled'),
                                ('', 2, UUID_C, '00000000', 'disabled')])
        self.assertNotIn('Source File', headers)
        self.assertEqual(source, path)

    def test_no_file_returns_no_rows_and_no_source(self):
        self.assertEqual(self.run_artifact([])[1:], ([], ''))

    def test_same_bytes_under_two_views_are_read_once_and_both_logged(self):
        data = record(UUID_A, '00000001')
        first, second = self.write(FILE, data), self.write(VIEW, data)
        _headers, rows, source = self.run_artifact([first, second])
        self.assertEqual(rows, [('', 1, UUID_A, '00000001', 'enabled')])
        self.assertEqual(source.split('\n'), sorted([first, second]))
        self.assertTrue(self.logged(f'read once: {VIEW}, {FILE}'))

    def test_copies_that_differ_are_both_read(self):
        first = self.write(FILE, record(UUID_A, '00000001'))
        second = self.write(VIEW, record(UUID_A, '00000000'))
        _headers, rows, _source = self.run_artifact([first, second])
        self.assertEqual(sorted((row[1], row[4]) for row in rows),
                         [(1, 'disabled'), (1, 'enabled')])
        self.assertTrue(self.logged(f'1 record(s) read from {FILE}'))
        self.assertTrue(self.logged(f'1 record(s) read from {VIEW}'))

    def test_same_bytes_with_different_recorded_times_stay_apart(self):
        data = record(UUID_A, '00000001')
        first, second = self.write(FILE, data), self.write(VIEW, data)
        seeker = FileSeekerZip()
        seeker.file_infos[first] = FileInfo(FILE, 0, 1700000000)
        seeker.file_infos[second] = FileInfo(VIEW, 0, 1700000060)
        _headers, rows, _source = self.run_artifact([first, second], seeker)
        self.assertEqual(sorted(row[0] for row in rows), [
            datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc),
            datetime(2023, 11, 14, 22, 14, 20, tzinfo=timezone.utc)])

    def test_file_modified_is_blank_for_a_folder_input(self):
        path = self.write(FILE, record(UUID_A, '00000001'))
        seeker = FileSeekerDir()
        seeker.file_infos[path] = FileInfo(FILE, 0, 1700000000)
        self.assertEqual(self.run_artifact([path], seeker)[1][0][0], '')

    def test_empty_old_and_unread_files_are_logged_and_still_named_as_source(self):
        empty = self.write(FILE, b'')
        _headers, rows, source = self.run_artifact([empty])
        self.assertEqual((rows, source), ([], empty))
        self.assertTrue(self.logged('is empty (0 bytes)'))
        old = self.write('a/' + FILE, b'0123456789ABCDEF: 00000001\n')
        self.assertEqual(self.run_artifact([old])[1], [])
        self.assertTrue(self.logged('older 16-character-key layout'))
        tail = self.write('b/' + FILE, record(UUID_A, '00000001') + b'zz')
        self.assertEqual(len(self.run_artifact([tail])[1]), 1)
        self.assertTrue(self.logged('2 byte(s) after record 1'))


if __name__ == '__main__':
    unittest.main()
