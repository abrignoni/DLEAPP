"""Pin how the Linux login artifacts read glibc's utmp and lastlog records."""
import gzip
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxLogins
# pylint: enable=wrong-import-position

WHEN = datetime(2026, 9, 28, 6, 0, 41, 526766, tzinfo=timezone.utc)
SECONDS = int(WHEN.timestamp())


def utmp64(kind=7, pid=241632, line=b'pts/0', ident=b'ts/0', user=b'parallels', host=b'10.211.55.2',
           seconds=SECONDS, micro=526766, address=bytes([10, 211, 55, 2]) + bytes(12)):
    """A 400-byte record, the layout glibc uses where ut_session and ut_tv are 64-bit (AArch64)."""
    return struct.pack('<h2xi32s4s32s256s4sqqq16s20s4x', kind, pid, line, ident, user, host, bytes(4), 0,
                       seconds, micro, address, bytes(20))


def utmp32(kind=7, pid=241632, line=b'pts/0', ident=b'ts/0', user=b'parallels', host=b'10.211.55.2',
           seconds=SECONDS, micro=526766, address=bytes([10, 211, 55, 2]) + bytes(12)):
    """A 384-byte record, the layout glibc uses where they are 32-bit (x86)."""
    return struct.pack('<h2xi32s4s32s256s4siIi16s20s', kind, pid, line, ident, user, host, bytes(4), 0,
                       seconds, micro, address, bytes(20))


class UtmpLayoutTest(unittest.TestCase):
    def test_the_two_layouts_are_the_sizes_glibc_gives_them(self):
        self.assertEqual([layout.size for layout in linuxLogins._UTMP_LAYOUTS], [400, 384])  # pylint: disable=protected-access

    def test_a_400_byte_record_is_read(self):
        rows, counts = linuxLogins.utmp_records(utmp64())
        self.assertEqual(rows, [(WHEN, 'USER_PROCESS', 'parallels', 'pts/0', '10.211.55.2', '10.211.55.2',
                                 241632, 'ts/0')])
        self.assertEqual(counts, {})

    def test_a_384_byte_record_is_read_the_same(self):
        self.assertEqual(linuxLogins.utmp_records(utmp32())[0], linuxLogins.utmp_records(utmp64())[0])

    def test_when_both_sizes_divide_the_file_the_records_decide(self):
        # 24 records of 400 bytes are 9,600 bytes, which is also 25 records of 384.
        data = utmp64() * 24
        self.assertEqual(linuxLogins.utmp_layout(data).size, 400)
        self.assertEqual(len(linuxLogins.utmp_records(data)[0]), 24)
        self.assertEqual(linuxLogins.utmp_layout(utmp32() * 25).size, 384)

    def test_a_file_of_empty_records_both_sizes_fit_is_not_read(self):
        self.assertIsNone(linuxLogins.utmp_records(bytes(9600)))

    def test_records_that_read_as_empty_do_not_vote(self):
        # Two 400-byte USER_PROCESS records in 24 records (9,600 bytes, also 25 records of 384).
        # Read as 384-byte records, records 5, 6 and 7 begin inside empty 400-byte records, so
        # their ut_type is 0; each is given a plausible ut_tv in bytes the 400-byte layout reads
        # as ut_host. Counted, those three would outvote the two real records.
        data = bytearray(utmp64() * 2 + bytes(400 * 22))
        for record in (5, 6, 7):
            struct.pack_into('<I', data, 384 * record + 340, SECONDS)
        self.assertEqual(linuxLogins.utmp_layout(bytes(data)).size, 400)
        self.assertEqual(len(linuxLogins.utmp_records(bytes(data))[0]), 2)

    def test_empty_undefined_and_trailing_bytes_are_counted_not_reported(self):
        data = utmp64(kind=0, user=b'', line=b'', ident=b'', host=b'', seconds=0, micro=0, address=bytes(16)) \
            + utmp64(kind=12) + utmp64() + b'\x07\x00\x00'
        rows, counts = linuxLogins.utmp_records(data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(counts, {'EMPTY records, not reported': 1,
                                  'records of a type glibc does not define, not reported': 1,
                                  'bytes after the last whole record, not read': 3})

    def test_every_type_glibc_defines_is_named(self):
        names = [linuxLogins.utmp_records(utmp64(kind=kind))[0][0][1] for kind in range(1, 10)]
        self.assertEqual(names, ['RUN_LVL', 'BOOT_TIME', 'NEW_TIME', 'OLD_TIME', 'INIT_PROCESS', 'LOGIN_PROCESS',
                                 'USER_PROCESS', 'DEAD_PROCESS', 'ACCOUNTING'])

    def test_addresses(self):
        v6 = bytes.fromhex('fdb22c26f4e400000000000000000001')
        self.assertEqual(linuxLogins.utmp_records(utmp64(address=v6))[0][0][5], 'fdb2:2c26:f4e4::1')
        self.assertEqual(linuxLogins.utmp_records(utmp64(address=bytes(16)))[0][0][5], '')

    def test_a_zero_time_is_blank(self):
        self.assertEqual(linuxLogins.utmp_records(utmp64(seconds=0, micro=0))[0][0][0], '')

    def test_a_time_outside_the_dates_a_report_can_hold_is_blank(self):
        for seconds in (2 ** 62, -(2 ** 62), 10 ** 13):
            self.assertEqual(linuxLogins.utmp_records(utmp64(seconds=seconds))[0][0][0], '', seconds)

    def test_text_that_is_not_utf8_shows_the_replacement_character(self):
        self.assertEqual(linuxLogins.utmp_records(utmp64(user=b'caf\xe9'))[0][0][2], 'caf�')


class RotationTest(unittest.TestCase):
    def test_a_gzip_rotation_reads_like_the_file(self):
        data = utmp64() + utmp64(kind=6, user=b'LOGIN', host=b'', address=bytes(16))
        with tempfile.TemporaryDirectory() as folder:
            plain = os.path.join(folder, 'wtmp.1')
            packed = os.path.join(folder, 'wtmp.1.gz')
            with open(plain, 'wb') as handle:
                handle.write(data)
            with gzip.open(packed, 'wb') as handle:
                handle.write(data)
            self.assertEqual(linuxLogins._read(packed), linuxLogins._read(plain))  # pylint: disable=protected-access


def lastlog(size, records):
    """A lastlog file of `size`-byte records, {uid: (seconds, line, host)} filled in."""
    form = '<q32s256s' if size == 296 else '<I32s256s'
    count = max(records) + 1
    return b''.join(struct.pack(form, *records[uid]) if uid in records else bytes(size) for uid in range(count))


class LastlogTest(unittest.TestCase):
    def test_the_two_layouts_are_the_sizes_glibc_gives_them(self):
        self.assertEqual([layout.size for layout in linuxLogins._LASTLOG_LAYOUTS], [296, 292])  # pylint: disable=protected-access

    def test_the_file_size_picks_the_layout(self):
        self.assertEqual(linuxLogins.lastlog_layout(lastlog(296, {1000: (SECONDS, b'pts/0', b'h')})).size, 296)
        self.assertEqual(linuxLogins.lastlog_layout(lastlog(292, {1000: (SECONDS, b'pts/0', b'h')})).size, 292)

    def test_when_both_sizes_divide_the_file_the_records_decide(self):
        # 73 records of 296 bytes are 21,608 bytes, which is also 74 records of 292.
        data = lastlog(296, {72: (SECONDS, b'pts/0', b'10.211.55.2'), 5: (SECONDS, b'tty1', b'')})
        self.assertEqual(len(data), 21608)
        self.assertEqual(linuxLogins.lastlog_layout(data).size, 296)

    def test_a_field_with_bytes_after_its_first_nul_does_not_vote(self):
        # 73 records of 296 bytes (21,608 bytes, also 74 of 292), one of them UID 71's. Read as
        # 292-byte records, record 72 begins on UID 71's ll_line, so its ll_time is the text 'pts/'
        # (796,095,600, a time in 1995) and its ll_line holds '0', NUL bytes and then the start of
        # ll_host. Only the text check keeps that record from tying the vote.
        data = lastlog(296, {71: (SECONDS, b'pts/0', b'10.211.55.2')}) + bytes(296)
        self.assertEqual(len(data), 21608)
        self.assertEqual(struct.unpack_from('<I', data, 292 * 72)[0], 796095600)
        self.assertEqual(linuxLogins.lastlog_layout(data).size, 296)


class PasswdTest(unittest.TestCase):
    def test_names_by_uid(self):
        text = (b'root:x:0:0:root:/root:/bin/bash\n# a comment\n+nis::0:0:::\n'
                b'parallels:x:1000:1000:Parallels,,,:/home/parallels:/bin/bash\n'
                b'toor:x:0:0::/root:/bin/sh\nbroken:x:notanumber:0::/:/bin/sh\nshort:x:5\n')
        self.assertEqual(linuxLogins.passwd_names(text), {0: ['root', 'toor'], 1000: ['parallels']})


class FakeContext:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return path


class ArtifactTest(unittest.TestCase):
    def test_wtmp_reads_every_rotation_and_counts_a_file_it_cannot_read(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log')
            os.makedirs(folder)
            files = []
            for name, data in (('wtmp', utmp64() * 2), ('wtmp.1.gz', utmp64(kind=6, user=b'LOGIN')),
                               ('wtmp.2', bytes(9600))):
                path = os.path.join(folder, name)
                with (gzip.open if name.endswith('.gz') else open)(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            with mock.patch.object(linuxLogins, 'logfunc') as log_lines:
                _headers, rows, source = linuxLogins.linuxWtmp.__wrapped__(FakeContext(files))
        self.assertEqual([(row[1], os.path.basename(row[-1])) for row in rows],
                         [('USER_PROCESS', 'wtmp'), ('USER_PROCESS', 'wtmp'), ('LOGIN_PROCESS', 'wtmp.1.gz')])
        self.assertEqual([os.path.basename(path) for path in source.split('\n')], ['wtmp', 'wtmp.1.gz'])
        self.assertIn('1 files no single utmp record layout fits, not read', log_lines.call_args.args[0])

    def test_btmp_reads_the_records_su_and_gdm_write_and_counts_an_empty_file(self):
        su = utmp64(kind=6, pid=1246, line=b'', ident=b'', user=b'target', host=b'', address=bytes(16))
        gdm = utmp64(kind=7, pid=2520, line=b'seat0', ident=b'', user=b'typed name', host=b'local', address=bytes(16))
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log')
            os.makedirs(folder)
            files = []
            for name, data in (('btmp', b''), ('btmp.1', su + gdm)):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            with mock.patch.object(linuxLogins, 'logfunc') as log_lines:
                headers, rows, source = linuxLogins.linuxBtmp.__wrapped__(FakeContext(files))
        self.assertEqual(headers, linuxLogins.linuxWtmp.__wrapped__(FakeContext([]))[0])
        self.assertEqual([row[1:8] for row in rows],
                         [('LOGIN_PROCESS', 'target', '', '', '', 1246, ''),
                          ('USER_PROCESS', 'typed name', 'seat0', 'local', '', 2520, '')])
        self.assertEqual({os.path.basename(row[-1]) for row in rows}, {'btmp.1'})
        self.assertEqual(os.path.basename(source), 'btmp.1')
        self.assertEqual(log_lines.call_args.args[0], 'Failed Login Records (btmp): 1 empty files, holding no records')

    def test_an_empty_wtmp_is_counted_as_empty_not_as_a_layout_failure(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'wtmp')
            open(path, 'wb').close()
            with mock.patch.object(linuxLogins, 'logfunc') as log_lines:
                _headers, rows, source = linuxLogins.linuxWtmp.__wrapped__(FakeContext([path]))
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(log_lines.call_args.args[0], 'Login Records (wtmp): 1 empty files, holding no records')

    def run_lastlog(self, with_passwd, uid=1000, extra=b''):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, 'var', 'log'))
            os.makedirs(os.path.join(root, 'etc'))
            log = os.path.join(root, 'var', 'log', 'lastlog')
            with open(log, 'wb') as handle:
                handle.write(lastlog(296, {uid: (SECONDS, b'pts/0', b'fdb2:2c26:f4e4::1')}) + extra)
            files = [log]
            if with_passwd:
                accounts = os.path.join(root, 'etc', 'passwd')
                with open(accounts, 'wb') as handle:
                    handle.write(b'parallels:x:1000:1000::/home/parallels:/bin/bash\n')
                files.append(accounts)
            with mock.patch.object(linuxLogins, 'logfunc') as log_lines:
                _headers, rows, source = linuxLogins.linuxLastlog.__wrapped__(FakeContext(files))
        return rows, source, log_lines

    def test_lastlog_names_the_account_from_passwd_beside_it(self):
        rows, source, _log = self.run_lastlog(True)
        self.assertEqual([row[1:5] for row in rows], [('parallels', 1000, 'pts/0', 'fdb2:2c26:f4e4::1')])
        self.assertEqual(rows[0][0], datetime(2026, 9, 28, 6, 0, 41, tzinfo=timezone.utc))
        self.assertTrue(source.endswith('passwd'))

    def test_a_uid_passwd_does_not_list_is_reported_without_a_name(self):
        rows, _source, _log = self.run_lastlog(True, uid=1001)
        self.assertEqual([row[1:3] for row in rows], [('', 1001)])

    def test_lastlog_without_passwd_is_read_and_says_so(self):
        rows, _source, log = self.run_lastlog(False)
        self.assertEqual([row[1:3] for row in rows], [('', 1000)])
        self.assertIn('lastlog files with no etc/passwd beside them', log.call_args.args[0])

    def test_lastlog_bytes_after_the_last_whole_record_are_counted(self):
        rows, _source, log = self.run_lastlog(True, extra=b'\x01\x02\x03')
        self.assertEqual([row[1:3] for row in rows], [('parallels', 1000)])
        self.assertIn('3 bytes after the last whole record, not read', log.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
