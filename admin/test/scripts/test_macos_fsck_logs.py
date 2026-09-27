"""fsck runs from the fsck logs macOS keeps in private/var/log and a user's Library/Logs."""

import fnmatch
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts.artifacts import macosFsckLogs

LOG = 'private/var/log'
HFS = (
    '\n'
    '/dev/rdisk2: fsck_hfs started at Fri Sep 12 14:59:27 2025\n'
    '/dev/rdisk2: /dev/rdisk2: ** /dev/rdisk2 (NO WRITE)\n'
    '/dev/rdisk2:    Executing fsck_hfs (version hfs-683.100.9).\n'
    'QUICKCHECK ONLY; FILESYSTEM CLEAN\n'
    '/dev/rdisk2: fsck_hfs completed at Fri Sep 12 14:59:27 2025\n'
    '\n'
    '\n'
    'fsck_hfs started at Mon Dec  1 16:21:06 2025\n'
    '** /dev/rdisk3s2 (NO WRITE)\n'
    'fsck_hfs completed at Mon Dec  1 16:21:07 2025\n'
    '\n')


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class FsckLogsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, text):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        return path

    def _run(self, files):
        with mock.patch.object(macosFsckLogs, 'logfunc', self.logs.append):
            return macosFsckLogs.macosFsckLogs.__wrapped__(FakeContext(self.root, files))

    def test_runs_with_and_without_a_device_prefix(self):
        path = self._write(f'{LOG}/fsck_hfs.log', HFS)
        headers, rows, source = self._run([path])
        self.assertEqual(headers, ('Started (as written)', 'Completed (as written)', 'Device', 'Program',
                                   'Messages', 'Source File'))
        where = f'{LOG}/fsck_hfs.log'
        self.assertEqual(rows, [
            ('Fri Sep 12 14:59:27 2025', 'Fri Sep 12 14:59:27 2025', '/dev/rdisk2', 'fsck_hfs',
             '/dev/rdisk2: /dev/rdisk2: ** /dev/rdisk2 (NO WRITE)\n'
             '/dev/rdisk2:    Executing fsck_hfs (version hfs-683.100.9).\n'
             'QUICKCHECK ONLY; FILESYSTEM CLEAN', where),
            ('Mon Dec  1 16:21:06 2025', 'Mon Dec  1 16:21:07 2025', '', 'fsck_hfs',
             '** /dev/rdisk3s2 (NO WRITE)', where),
        ])
        self.assertEqual(source, path)

    def test_unclosed_runs_stray_completions_and_stray_lines(self):
        path = self._write(f'{LOG}/fsck_apfs.log', (
            'left over before any run\n'
            '/dev/rdisk1s1: fsck_apfs started at Mon Feb 15 10:58:24 2021\n'
            '/dev/rdisk1s1: ** QUICKCHECK ONLY; FILESYSTEM CLEAN\n'
            '/dev/rdisk1s2: fsck_apfs started at Mon Feb 15 10:58:25 2021\n'
            '/dev/rdisk1s2: fsck_apfs completed at Mon Feb 15 10:58:26 2021\n'
            'stray after a completed run\n'
            '/dev/rdisk1s3: fsck_apfs completed at Mon Feb 15 10:58:27 2021\n'))
        _headers, rows, _source = self._run([path])
        self.assertEqual([row[:5] for row in rows], [
            ('', '', '', '', 'left over before any run'),
            ('Mon Feb 15 10:58:24 2021', '', '/dev/rdisk1s1', 'fsck_apfs',
             '/dev/rdisk1s1: ** QUICKCHECK ONLY; FILESYSTEM CLEAN'),
            ('Mon Feb 15 10:58:25 2021', 'Mon Feb 15 10:58:26 2021', '/dev/rdisk1s2', 'fsck_apfs', ''),
            ('', '', '', '', 'stray after a completed run'),
            ('', 'Mon Feb 15 10:58:27 2021', '/dev/rdisk1s3', 'fsck_apfs', ''),
        ])

    def test_a_completion_for_another_device_does_not_close_the_run(self):
        path = self._write(f'{LOG}/fsck_apfs.log', (
            '/dev/rdisk5s1: fsck_apfs started at Mon Feb 15 10:58:24 2021\n'
            '/dev/rdisk6s1: fsck_apfs completed at Mon Feb 15 10:58:25 2021\n'))
        _headers, rows, _source = self._run([path])
        self.assertEqual([row[:4] for row in rows], [
            ('Mon Feb 15 10:58:24 2021', '', '/dev/rdisk5s1', 'fsck_apfs'),
            ('', 'Mon Feb 15 10:58:25 2021', '/dev/rdisk6s1', 'fsck_apfs')])

    def test_the_error_log_and_a_file_with_no_run_are_not_read(self):
        error = self._write(f'{LOG}/fsck_apfs_error.log', (
            'dev=/dev/rdisk1 uuid=00000000-0000-0000-0000-000000000000 result=65\n'
            'fsck_apfs completed at Wed Feb 17 11:33:11 2021\n'))
        other = self._write(f'{LOG}/fsck_exfat.log', 'nothing in the fsck form\n')
        _headers, rows, source = self._run([error, other])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn(f'fsck Logs: no fsck run in {LOG}/fsck_exfat.log', self.logs)

    def test_two_views_of_one_log_give_each_run_once_from_the_fuller_copy(self):
        earlier = HFS
        later = HFS + ('/dev/rdisk4s2: fsck_hfs started at Tue Dec  9 16:43:15 2025\n'
                       '/dev/rdisk4s2: fsck_hfs completed at Tue Dec  9 16:43:15 2025\n')
        first = self._write(f'{LOG}/fsck_hfs.log', later)
        second = self._write(f'System/Volumes/Data/{LOG}/fsck_hfs.log', earlier)
        _headers, rows, source = self._run([first, second])
        self.assertEqual([(row[2], row[5]) for row in rows], [
            ('/dev/rdisk2', f'{LOG}/fsck_hfs.log'),
            ('', f'{LOG}/fsck_hfs.log'),
            ('/dev/rdisk4s2', f'{LOG}/fsck_hfs.log')])
        self.assertEqual(source, first)
        self.assertIn('fsck Logs: 2 runs the other view of the same log also holds not reported again',
                      self.logs)

    def test_of_two_equal_copies_the_one_at_the_root_is_cited(self):
        second = self._write(f'System/Volumes/Data/{LOG}/fsck_hfs.log', HFS)
        first = self._write(f'{LOG}/fsck_hfs.log', HFS)
        _headers, rows, source = self._run([second, first])
        self.assertEqual([row[5] for row in rows], [f'{LOG}/fsck_hfs.log'] * 2)
        self.assertEqual(source, first)

    def test_logs_in_different_folders_are_both_reported(self):
        first = self._write(f'Macintosh HD - Data/{LOG}/fsck_hfs.log', HFS)
        second = self._write('Users/alice/Library/Logs/fsck_hfs.log', HFS)
        _headers, rows, _source = self._run([first, second])
        self.assertEqual(len(rows), 4)

    def test_an_unreadable_file_is_logged(self):
        path = self._write(f'{LOG}/fsck_hfs.log', HFS)
        with mock.patch.object(macosFsckLogs, 'open', side_effect=PermissionError, create=True):
            _headers, rows, _source = self._run([path])
        self.assertEqual(rows, [])
        self.assertIn(f'fsck Logs: could not read {LOG}/fsck_hfs.log', self.logs)

    def test_paths_reach_the_mac_logs_and_not_a_windows_file(self):
        patterns = macosFsckLogs.__artifacts_v2__['macosFsckLogs']['paths']
        def matched(path):
            return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        self.assertTrue(matched('/case/p2/Macintosh HD - Data/private/var/log/fsck_apfs.log'))
        self.assertTrue(matched('/case/p2/Macintosh HD - Data/Users/alice/Library/Logs/fsck_hfs.log'))
        self.assertFalse(matched('/case/lba0/Windows/Logs/fsck.log'))
        self.assertFalse(matched('/case/p2/Macintosh HD - Data/Users/alice/Documents/fsck_hfs.log'))


if __name__ == '__main__':
    unittest.main()
