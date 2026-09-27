"""Records in /var/run/utmpx, written here in the utmpx32 layout Libc writes on a 64-bit Mac."""

import datetime
import fnmatch
import os
import pathlib
import struct
import tempfile
import unittest
from unittest import mock

from scripts import macos_plists
from scripts.artifacts import macosUtmpx

UTC = datetime.timezone.utc
RUN = 'private/var/run/utmpx'
LAYOUT = struct.Struct('<256s4s32sih2xii256s64s')


def rec(kind, user=b'', ident=b'', line=b'', pid=0, seconds=0, micro=0, host=b''):
    return LAYOUT.pack(user, ident, line, pid, kind, seconds, micro, host, b'')


SIGNATURE = rec(10, user=b'utmpx-1.00')


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class UtmpxTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def _run(self, files):
        with mock.patch.object(macosUtmpx, 'logfunc', self.logs.append), \
                mock.patch.object(macos_plists, 'logfunc', self.logs.append):
            return macosUtmpx.macosUtmpx.__wrapped__(FakeContext(self.root, files))

    def test_each_record_after_the_signature_is_a_row(self):
        path = self._write(RUN, SIGNATURE
                           + rec(2, pid=1, seconds=1765554499, micro=373291)
                           + rec(7, b'alice', b'/\x00\x01\x01', b'console', 166, 1765554574, 522093)
                           + rec(8, b'bob', b's000', b'ttys000', 1303, 1765572307, 657957, b'remote.example')
                           + rec(11, seconds=1765572400, micro=5))
        headers, rows, source = self._run([path])
        self.assertEqual(headers[0], ('Time (UTC)', 'datetime'))
        self.assertEqual(rows, [
            (datetime.datetime(2025, 12, 12, 15, 48, 19, 373291, tzinfo=UTC), 'BOOT_TIME', '', '', 1, '',
             '00000000', RUN),
            (datetime.datetime(2025, 12, 12, 15, 49, 34, 522093, tzinfo=UTC), 'USER_PROCESS', 'alice', 'console',
             166, '', '2f000101', RUN),
            (datetime.datetime(2025, 12, 12, 20, 45, 7, 657957, tzinfo=UTC), 'DEAD_PROCESS', 'bob', 'ttys000',
             1303, 'remote.example', '73303030', RUN),
            (datetime.datetime(2025, 12, 12, 20, 46, 40, 5, tzinfo=UTC), 'SHUTDOWN_TIME', '', '', 0, '',
             '00000000', RUN),
        ])
        self.assertEqual(source, path)
        self.assertEqual(self.logs, ['Current Logins (utmpx): 4 record(s).'])

    def test_empty_records_are_counted_and_an_unknown_type_is_kept_as_its_number(self):
        path = self._write(RUN, SIGNATURE + rec(0) + rec(42, seconds=86400))
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows, [(datetime.datetime(1970, 1, 2, tzinfo=UTC), '42', '', '', 0, '', '00000000', RUN)])
        self.assertIn('Current Logins (utmpx): 1 EMPTY records, not reported', self.logs)

    def test_a_file_without_the_signature_record_is_not_read(self):
        wrong_user = self._write(RUN, rec(10, user=b'utmpx-2.00') + rec(2, seconds=1))
        wrong_type = self._write('System/Volumes/Data/' + RUN, rec(2, user=b'utmpx-1.00') + rec(2, seconds=1))
        short = self._write('other/var/run/utmpx', b'utmpx-1.00\x00')
        longer = self._write('another/var/run/utmpx', rec(10, user=b'utmpx-1.001') + rec(2, seconds=1))
        _headers, rows, source = self._run([wrong_user, wrong_type, short, longer])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn('Current Logins (utmpx): 4 files with no utmpx-1.00 signature record, not read', self.logs)

    def test_a_file_holding_only_the_signature_gives_no_row_and_no_source(self):
        path = self._write(RUN, SIGNATURE)
        _headers, rows, source = self._run([path])
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logs, ['Current Logins (utmpx): 0 record(s).'])

    def test_text_ends_at_its_first_nul_and_a_time_of_microseconds_only_is_kept(self):
        path = self._write(RUN, SIGNATURE + rec(4, b'alice\x00old', b'', b'tty\x00x', 9, 0, 7))
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows, [(datetime.datetime(1970, 1, 1, 0, 0, 0, 7, tzinfo=UTC), 'NEW_TIME', 'alice', 'tty',
                                 9, '', '00000000', RUN)])

    def test_bytes_after_the_last_whole_record_are_counted(self):
        path = self._write(RUN, SIGNATURE + rec(2, seconds=1) + b'\x01' * 100)
        _headers, rows, _source = self._run([path])
        self.assertEqual(len(rows), 1)
        self.assertIn('Current Logins (utmpx): 100 bytes after the last whole record, not read', self.logs)

    def test_a_byte_identical_second_capture_is_read_once(self):
        data = SIGNATURE + rec(2, seconds=1)
        first = self._write(RUN, data)
        second = self._write('System/Volumes/Data/' + RUN, data)
        _headers, rows, source = self._run([second, first])
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, first)

    def test_a_differing_second_capture_reports_a_shared_record_once(self):
        boot = rec(2, seconds=1)
        first = self._write(RUN, SIGNATURE + boot)
        second = self._write('System/Volumes/Data/' + RUN, SIGNATURE + boot + rec(7, b'alice', b's000', b'ttys000', 5, 2))
        _headers, rows, source = self._run([first, second])
        self.assertEqual([(row[1], row[7]) for row in rows], [('BOOT_TIME', RUN), ('USER_PROCESS', 'System/Volumes/Data/' + RUN)])
        self.assertEqual(source.split('\n'), [first, second])
        self.assertIn('Current Logins (utmpx): 1 records the other capture of the same file also holds, '
                      'not reported again', self.logs)

    def test_paths_reach_the_file_with_or_without_private(self):
        patterns = macosUtmpx.__artifacts_v2__['macosUtmpx']['paths']
        def matched(path):
            return sum(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        self.assertEqual(matched('/case/private/var/run/utmpx'), 1)
        self.assertEqual(matched('/case/var/run/utmpx'), 1)
        self.assertEqual(matched('/case/private/var/run/utmpx.lock'), 0)


if __name__ == '__main__':
    unittest.main()
