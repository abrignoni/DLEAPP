"""Pin the Apport Crash Reports artifact (scripts/artifacts/linuxApportCrashReports.py).

REPORT has the fields and layout of a report Apport 2.34.1 wrote on the lab VM for ubuntu2604_arm64_apport, cut
down; the values were made for the test.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxApportCrashReports as ap
# pylint: enable=wrong-import-position

REPORT = (b'ProblemType: Crash\nArchitecture: arm64\nDate: Tue Oct  6 11:38:57 2026\nDependencies:\n libc6 2.43\n'
          b' libgcc-s1 16\nDistroRelease: Ubuntu 26.04\nExecutablePath: /usr/bin/sleep\n'
          b'ExecutableTimestamp: 1776343279\nPackage: coreutils 9.7\nProcCmdline: sleep 31337\n'
          b'ProcCwd: /home/user/known\nProcEnviron:\n LANG=C.UTF-8\n SHELL=/bin/bash\nSignal: 11\n'
          b'SignalName: SIGSEGV\nSourcePackage: coreutils\nUname: Linux 7.0.0-34-generic aarch64\n_HooksRun: no\n'
          b'CoreDump: base64\n H4sICAAAAAAC/0NvcmVEdW1wAA==\n AAAA\n')
ROW = ('2026-10-06 11:38:57', 'Crash', '/usr/bin/sleep', 'sleep 31337', '11', 'SIGSEGV', 'coreutils 9.7',
       'coreutils', '/home/user/known', 'Ubuntu 26.04', 'arm64', 'Linux 7.0.0-34-generic aarch64', '1000',
       datetime(2026, 4, 16, 12, 41, 19, tzinfo=timezone.utc), 'Yes', 'Dependencies, ProcEnviron, _HooksRun')


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class Fields(unittest.TestCase):
    def test_a_report(self):
        fields, binary, skipped = ap.report_fields(REPORT)
        self.assertEqual((binary, skipped, len(fields)), (['CoreDump'], 0, 16))
        self.assertEqual(fields['Dependencies'], 'libc6 2.43\nlibgcc-s1 16')
        self.assertEqual(fields['ProcEnviron'], 'LANG=C.UTF-8\nSHELL=/bin/bash')
        self.assertEqual(fields['Date'], 'Tue Oct  6 11:38:57 2026')

    def test_values_join_as_apport_joins_them(self):
        fields = ap.report_fields(b'A:\n \n  x\n \n =\nB: one\n two\n\n\nC:  padded \t\nD: a: b\nE:\nF: \n \n')[0]
        self.assertEqual(fields, {'A': ' x\n\n=', 'B': 'one\ntwo', 'C': 'padded', 'D': 'a: b', 'E': '', 'F': ''})

    def test_a_last_line_without_a_newline(self):
        self.assertEqual(ap.report_fields(b'A: 1\nB:\n x')[0], {'A': '1', 'B': 'x'})

    def test_base64_only_when_it_is_the_whole_first_line(self):
        fields, binary, _ = ap.report_fields(b'A: base64\n AAAA\nB: base64 x\n y\nC:  base64 \n AAAA\nD: 1\n')
        self.assertEqual((fields, binary), ({'B': 'base64 x\ny', 'D': '1'}, ['A', 'C']))

    def test_a_line_that_starts_no_field_is_skipped_with_its_continuation(self):
        fields, binary, skipped = ap.report_fields(b' orphan\nA: 1\nno colon here\n lost\nB: 2\nagain\n')
        self.assertEqual((fields, binary, skipped), ({'A': '1', 'B': '2'}, [], 2))

    def test_bytes_that_are_not_utf8_or_ascii(self):
        self.assertEqual(ap.report_fields(b'K\xe9y: v\xff\n')[0], {'K\\xe9y': 'v\\xff'})
        self.assertEqual(ap.report_fields(b'K\xc3\xa9y: caf\xc3\xa9\n')[0], {'K\\xc3\\xa9y': 'caf\u00e9'})

    def test_only_a_line_feed_ends_a_line(self):
        self.assertEqual(ap.report_fields(b'A: x\x0cy\rz\nB: 1\n')[0], {'A': 'x\x0cy\rz', 'B': '1'})

    def test_nothing(self):
        self.assertEqual(ap.report_fields(b''), ({}, [], 0))


class Columns(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(ap.report_date('Mon Jan 15 03:04:05 2024'), '2024-01-15 03:04:05')
        self.assertEqual(ap.report_date('Sun Dec  1 23:59:59 2019'), '2019-12-01 23:59:59')
        for other in ('2024-01-15 03:04:05', 'Mon Foo 15 03:04:05 2024', 'Mon Jan 15 03:04:05 2024 UTC', ''):
            self.assertEqual(ap.report_date(other), other)

    def test_user_in_the_file_name(self):
        self.assertEqual(ap.file_user('_usr_bin_sleep.1000.crash'), '1000')
        self.assertEqual(ap.file_user('_opt_a.b_c.0.crash'), '0')
        for name in ('sleep.crash', '_usr_bin_sleep.user.crash', 'crash', '_usr_bin_sleep.-1.crash'):
            self.assertEqual(ap.file_user(name), '', name)

    def test_executable_time(self):
        self.assertEqual(ap.executable_time('0'), datetime(1970, 1, 1, tzinfo=timezone.utc))
        for other in ("Error: Executable '/x' not found", '', '-5', '1.5', '9' * 30):
            self.assertEqual(ap.executable_time(other), '', other)


class Processor(unittest.TestCase):
    def run_on(self, files):
        with tempfile.TemporaryDirectory() as root:
            paths = []
            for name, data in files.items():
                path = os.path.join(root, 'var', 'crash', name)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                paths.append(path)
            paths += [os.path.join(root, 'var', 'crash', 'gone.0.crash'), os.path.join(root, 'var', 'crash')]
            with mock.patch.object(ap, 'logfunc') as log:
                headers, data, located = ap.linuxApportCrashReports.__wrapped__(FakeContext(paths[::-1], root))
            return headers, data, [os.path.basename(p) for p in located.split('\n') if p], log

    def test_reports(self):
        headers, data, located, log = self.run_on({
            '_usr_bin_sleep.1000.crash': REPORT, 'empty.0.crash': b'\n', 'not_a_report.0.crash': b'just text\n',
            'pkg.0.crash': (b'ProblemType: Package\nPackage: made-up 1.0\nErrorMessage: failed\nno colon\n'
                            b'Screenshot: base64\n AAAA\n')})
        self.assertEqual(len(headers), 17)
        self.assertEqual(headers[13], ('Executable Modified (UTC)', 'datetime'))
        self.assertEqual(data[0], ROW + (os.path.join('var', 'crash', '_usr_bin_sleep.1000.crash'),))
        self.assertEqual(data[1], ('', 'Package', '', '', '', '', 'made-up 1.0', '', '', '', '', '', '0', '', 'No',
                                   'ErrorMessage, Screenshot', os.path.join('var', 'crash', 'pkg.0.crash')))
        self.assertEqual(len(data), 2)
        self.assertEqual(located, ['_usr_bin_sleep.1000.crash', 'pkg.0.crash'])
        message = log.call_args[0][0]
        self.assertIn('1 files that could not be read', message)
        self.assertIn('2 files that hold no field, not reported', message)
        self.assertIn('2 lines that start no field, skipped', message)

    def test_nothing_found(self):
        with mock.patch.object(ap, 'logfunc') as log:
            self.assertEqual(ap.linuxApportCrashReports.__wrapped__(FakeContext([], '/'))[1:], ([], ''))
        log.assert_not_called()

    def test_a_clean_report_adds_nothing_to_the_log(self):
        log = self.run_on({'_usr_bin_sleep.1000.crash': REPORT})[3]
        self.assertEqual(log.call_args[0][0], 'Apport Crash Reports: 1 files that could not be read')


if __name__ == '__main__':
    unittest.main()
