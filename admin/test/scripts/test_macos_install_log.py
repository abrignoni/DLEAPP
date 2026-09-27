"""macOS install log entries from private/var/log/install.log and its rotated copies."""

import datetime
import fnmatch
import gzip
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts.artifacts import macosInstallLog

UTC = datetime.timezone.utc
LOG = 'private/var/log'


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class InstallLogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, text, compress=False):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = text.encode('utf-8')
        with open(path, 'wb') as handle:
            handle.write(gzip.compress(data) if compress else data)
        return path

    def _run(self, files):
        with mock.patch.object(macosInstallLog, 'logfunc', self.logs.append):
            return macosInstallLog.macosInstallLog.__wrapped__(FakeContext(self.root, files))

    def test_offset_lines_zoneless_lines_and_continuations(self):
        path = self._write(f'{LOG}/install.log', (
            'text before the first entry\n'
            'Dec  2 14:39:21 localhost OSInstaller[47]: Waiting for reboot\n'
            '2020-12-02 07:16:45-08 Mac installd[430]: Installed "VMware Tools" (11.1.5)\n'
            '\t{\n'
            '\t}\n'
            '2021-02-15 10:59:37-05 Mac system_installd[440]: Installed "MRTConfigData" (1.73)\n'
            '2021-02-15 21:29:37+05:30 Mac Installer Progress[56]: \n'))
        headers, rows, source = self._run([path])
        self.assertEqual(headers, (('Timestamp (UTC)', 'datetime'), 'Time as Written', 'Host', 'Process',
                                   'PID', 'Message', 'Source File'))
        where = f'{LOG}/install.log'
        self.assertEqual(rows, [
            ('', '', '', '', '', 'text before the first entry', where),
            ('', 'Dec  2 14:39:21', 'localhost', 'OSInstaller', 47, 'Waiting for reboot', where),
            (datetime.datetime(2020, 12, 2, 15, 16, 45, tzinfo=UTC), '2020-12-02 07:16:45-08', 'Mac',
             'installd', 430, 'Installed "VMware Tools" (11.1.5)\n\t{\n\t}', where),
            (datetime.datetime(2021, 2, 15, 15, 59, 37, tzinfo=UTC), '2021-02-15 10:59:37-05', 'Mac',
             'system_installd', 440, 'Installed "MRTConfigData" (1.73)', where),
            (datetime.datetime(2021, 2, 15, 15, 59, 37, tzinfo=UTC), '2021-02-15 21:29:37+05:30', 'Mac',
             'Installer Progress', 56, '', where),
        ])
        self.assertEqual(source, path)

    def test_rotated_copies_are_read_oldest_first_and_gunzipped(self):
        live = self._write(f'{LOG}/install.log', '2021-02-03 10:00:00-05 Mac installd[3]: third\n')
        newest = self._write(f'{LOG}/install.log.0.gz', '2021-02-02 10:00:00-05 Mac installd[2]: second\n',
                             compress=True)
        checkpoint = self._write(f'{LOG}/install.log.T1612364400',
                                 '2021-02-02 12:00:00-05 Mac installd[9]: checkpoint\n')
        oldest = self._write(f'{LOG}/install.log.1.gz', '2021-02-01 10:00:00-05 Mac installd[1]: first\n',
                             compress=True)
        other = self._write(f'{LOG}/install.log.old', '2021-02-04 10:00:00-05 Mac installd[4]: other\n')
        bare = self._write(f'{LOG}/install.log.gz', '2021-02-05 10:00:00-05 Mac installd[6]: bare\n',
                           compress=True)
        _headers, rows, source = self._run([live, newest, checkpoint, oldest, other, bare])
        self.assertEqual([row[5] for row in rows], ['first', 'second', 'checkpoint', 'third'])
        self.assertEqual(source.split('\n'), [oldest, newest, checkpoint, live])

    def test_two_views_of_one_log_folder_give_each_entry_once(self):
        earlier = ('2025-12-24 09:00:00-05 Mac installd[5]: same second\n'
                   '2025-12-24 09:00:00-05 Mac installd[5]: same second\n'
                   '2025-12-24 09:00:01-05 Mac installd[5]: shared\n')
        later = earlier + '2025-12-25 20:50:24-05 Mac installd[5]: appended\n'
        first = self._write(f'{LOG}/install.log', earlier)
        second = self._write(f'System/Volumes/Data/{LOG}/install.log', later)
        _headers, rows, source = self._run([first, second])
        self.assertEqual([(row[5], row[6]) for row in rows], [
            ('same second', f'System/Volumes/Data/{LOG}/install.log'),
            ('same second', f'System/Volumes/Data/{LOG}/install.log'),
            ('shared', f'System/Volumes/Data/{LOG}/install.log'),
            ('appended', f'System/Volumes/Data/{LOG}/install.log')])
        self.assertEqual(source, second)
        self.assertIn('Install Log: 3 entries held by both views of one log folder reported once', self.logs)

    def test_an_entry_only_the_smaller_view_holds_is_kept_after_the_larger_views(self):
        first = self._write(f'{LOG}/install.log',
                            '2025-12-25 09:00:00-05 Mac installd[5]: newer\n'
                            '2025-12-25 09:00:01-05 Mac installd[5]: newest\n')
        second = self._write(f'System/Volumes/Data/{LOG}/install.log',
                             '2025-12-24 09:00:00-05 Mac installd[5]: only here\n')
        _headers, rows, source = self._run([first, second])
        self.assertEqual([row[5] for row in rows], ['newer', 'newest', 'only here'])
        self.assertEqual(source.split('\n'), [first, second])

    def test_logs_in_different_folders_are_both_reported(self):
        text = '2021-02-15 10:59:37-05 Mac installd[5]: Installed "X" (1)\n'
        first = self._write(f'Macintosh HD - Data/{LOG}/install.log', text)
        second = self._write(f'Other Volume/{LOG}/install.log', text)
        _headers, rows, _source = self._run([first, second])
        self.assertEqual(len(rows), 2)

    def test_an_unreadable_file_is_logged_and_gives_no_rows(self):
        path = os.path.join(self.root, LOG, 'install.log.0.gz')
        os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as handle:
            handle.write(b'\x1f\x8bnot gzip data')
        _headers, rows, source = self._run([path])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn(f'Install Log: could not read {LOG}/install.log.0.gz', self.logs)

    def test_a_file_with_no_install_log_line_is_logged_and_not_read(self):
        path = self._write(f'{LOG}/install.log', 'Setup started.\nStep 1 of 3\n')
        _headers, rows, source = self._run([path])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn(f'Install Log: no install log line in {LOG}/install.log', self.logs)

    def test_paths_reach_the_mac_log_folder_and_not_a_windows_installer_log(self):
        patterns = macosInstallLog.__artifacts_v2__['macosInstallLog']['paths']
        def matched(path):
            return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        self.assertTrue(matched('/case/p2/Macintosh HD - Data/private/var/log/install.log'))
        self.assertTrue(matched('/case/p2/Macintosh HD - Data/private/var/log/install.log.0.gz'))
        self.assertFalse(matched('/case/lba0/Users/IEUser/AppData/Local/Temp/VSD6D8B.tmp/install.log'))


if __name__ == '__main__':
    unittest.main()
