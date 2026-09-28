"""Pin how the SSH Server Log artifact reads sshd's lines in auth.log and secure."""
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import sshServerLog
# pylint: enable=wrong-import-position

UTC = timezone.utc


class TimeTest(unittest.TestCase):
    def test_rfc3339_times_are_converted_with_their_own_offset(self):
        self.assertEqual(sshServerLog.utc_time('2026-09-28T02:45:33.123456-04:00'),
                         datetime(2026, 9, 28, 6, 45, 33, 123456, tzinfo=UTC))
        self.assertEqual(sshServerLog.utc_time('2026-01-10T09:00:00.5+04:00'),
                         datetime(2026, 1, 10, 5, 0, 0, 500000, tzinfo=UTC))
        self.assertEqual(sshServerLog.utc_time('2026-03-01T00:00:00Z'), datetime(2026, 3, 1, tzinfo=UTC))
        self.assertEqual(sshServerLog.utc_time('2026-09-28T00:10:00-00:30'),
                         datetime(2026, 9, 28, 0, 40, tzinfo=UTC))

    def test_a_time_with_no_year_or_zone_is_not_converted(self):
        self.assertEqual(sshServerLog.utc_time('Feb  6 15:16:30'), '')

    def test_a_stamp_that_is_not_a_calendar_date_is_blank_and_counted(self):
        counts = Counter()
        rows = sshServerLog.log_rows(b'2026-02-30T01:02:03.000001+00:00 host sshd[1]: Server listening\n', counts)
        self.assertEqual(rows[0][0], '')
        self.assertEqual(counts, {'RFC 3339 times that are not a calendar date, Time (UTC) left blank': 1})


LOG = (b'2026-09-28T02:45:33.123456-04:00 ubuntu sshd-session[4021]: Accepted publickey for alex from 10.0.0.2 '
       b'port 52110 ssh2: ED25519 SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA\n'
       b'2026-09-28T02:45:34.000001-04:00 ubuntu sudo[4100]:     alex : TTY=pts/0 ; COMMAND=/bin/true\n'
       b'Feb  6 15:16:32 victoria sshd[2085]: Failed password for invalid user ulysses from 192.0.2.9 port 4242 ssh2\n'
       b'\n'
       b'Feb  6 15:16:40 victoria last message repeated 2 times\n'
       b'2026-09-28T02:46:00Z ubuntu sshd: Received signal 15; terminating.\r\n')


class LogRowsTest(unittest.TestCase):
    def test_only_sshd_lines_are_rows_and_the_rest_are_counted(self):
        counts = Counter()
        rows = sshServerLog.log_rows(LOG, counts)
        self.assertEqual(rows, [
            (datetime(2026, 9, 28, 6, 45, 33, 123456, tzinfo=UTC), '2026-09-28T02:45:33.123456-04:00', 'ubuntu',
             'sshd-session', '4021', 'Accepted publickey for alex from 10.0.0.2 port 52110 ssh2: ED25519 '
             'SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA', 1),
            ('', 'Feb  6 15:16:32', 'victoria', 'sshd', '2085',
             'Failed password for invalid user ulysses from 192.0.2.9 port 4242 ssh2', 3),
            (datetime(2026, 9, 28, 2, 46, tzinfo=UTC), '2026-09-28T02:46:00Z', 'ubuntu', 'sshd', '',
             'Received signal 15; terminating.', 6)])
        self.assertEqual(counts, {'lines from other programs, not reported': 1,
                                  'lines in neither syslog file format, not reported': 1})

    def test_text_that_is_not_utf8_shows_the_replacement_character(self):
        rows = sshServerLog.log_rows(b'Feb  6 15:16:32 victoria sshd[1]: Invalid user caf\xe9 from 192.0.2.9\n', Counter())
        self.assertEqual(rows[0][5], 'Invalid user caf� from 192.0.2.9')


class LoginFieldsTest(unittest.TestCase):
    def fields(self, message):
        return sshServerLog.login_fields(message)

    def test_an_accepted_key_login_carries_the_key(self):
        self.assertEqual(self.fields('Accepted publickey for alex from 10.0.0.2 port 52110 ssh2: ED25519 '
                                     'SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA'),
                         ('Accepted', 'publickey', 'alex', '', '10.0.0.2', '52110', 'ED25519',
                          'SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA'))

    def test_a_certificate_login_carries_the_certificate_key_not_the_ca(self):
        self.assertEqual(self.fields('Accepted publickey for alex from 2001:db8::5 port 22 ssh2: ED25519-CERT '
                                     'SHA256:certkey ID alex@corp (serial 7) CA ED25519 SHA256:cakey'),
                         ('Accepted', 'publickey', 'alex', '', '2001:db8::5', '22', 'ED25519-CERT', 'SHA256:certkey'))

    def test_hostbased_extra_text_after_a_comma_is_not_the_fingerprint(self):
        self.assertEqual(self.fields('Accepted hostbased for alex from 10.0.0.2 port 22 ssh2: RSA SHA256:hostkey, '
                                     'client user "alex", client host "box"')[6:], ('RSA', 'SHA256:hostkey'))

    def test_a_method_without_a_key_carries_no_key(self):
        self.assertEqual(self.fields('Accepted keyboard-interactive/pam for alex from 10.0.0.2 port 22 ssh2'),
                         ('Accepted', 'keyboard-interactive/pam', 'alex', '', '10.0.0.2', '22', '', ''))
        self.assertEqual(self.fields('Accepted password for alex from 10.0.0.2 port 22 ssh2: some info'),
                         ('Accepted', 'password', 'alex', '', '10.0.0.2', '22', '', ''))

    def test_failed_and_invalid_users(self):
        self.assertEqual(self.fields('Failed none for invalid user ulysses from 192.0.2.9 port 4242 ssh2'),
                         ('Failed', 'none', 'ulysses', 'Yes', '192.0.2.9', '4242', '', ''))
        self.assertEqual(self.fields('Failed password for invalid user a from b from 192.0.2.9 port 1 ssh2')[2:6],
                         ('a from b', 'Yes', '192.0.2.9', '1'))

    def test_invalid_user_with_and_without_a_port(self):
        self.assertEqual(self.fields('Invalid user ulysses from 192.0.2.9 port 4242'),
                         ('', '', 'ulysses', 'Yes', '192.0.2.9', '4242', '', ''))
        self.assertEqual(self.fields('Invalid user ulysses from 192.0.2.9'),
                         ('', '', 'ulysses', 'Yes', '192.0.2.9', '', '', ''))
        self.assertEqual(self.fields('Invalid user  from 192.0.2.9 port 22')[2], '')

    def test_a_relayed_message_and_a_repeated_one_are_read_inside(self):
        self.assertEqual(self.fields('Postponed publickey for alex from 10.0.0.2 port 22 ssh2 [preauth]'),
                         ('Postponed', 'publickey', 'alex', '', '10.0.0.2', '22', '', ''))
        self.assertEqual(self.fields('Partial keyboard-interactive/pam for alex from 10.0.0.2 port 22 ssh2 [postauth]'),
                         ('Partial', 'keyboard-interactive/pam', 'alex', '', '10.0.0.2', '22', '', ''))
        self.assertEqual(self.fields('message repeated 3 times: [ Failed password for root from 192.0.2.9 port '
                                     '5555 ssh2]'),
                         ('Failed', 'password', 'root', '', '192.0.2.9', '5555', '', ''))
        self.assertEqual(self.fields('message repeated 2 times: [Invalid user oracle from 192.0.2.9 port 1]'),
                         ('', '', 'oracle', 'Yes', '192.0.2.9', '1', '', ''))

    def test_a_protocol_1_login_is_not_split(self):
        self.assertEqual(self.fields('Accepted rsa for root from 192.0.2.9 port 1022'), ('',) * 8)

    def test_other_messages_carry_no_login_fields(self):
        for message in ('Connection closed by authenticating user alex 10.0.0.2 port 22 [preauth]',
                        'pam_unix(sshd:session): session opened for user alex(uid=1000) by alex(uid=0)',
                        'Server listening on 0.0.0.0 port 22.'):
            self.assertEqual(self.fields(message), ('',) * 8)


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_rotations_are_read_and_each_row_names_its_file(self):
        with tempfile.TemporaryDirectory() as root:
            logs = os.path.join(root, 'var', 'log')
            os.makedirs(logs)
            files = []
            for name, data in (('auth.log.2.gz', gzip.compress(LOG[:200])), ('auth.log.1', b'not a syslog line\n'),
                               ('auth.log', LOG), ('auth.log.3.gz', gzip.compress(LOG)[:40])):
                path = os.path.join(logs, name)
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            files.append(logs)
            with mock.patch.object(sshServerLog, 'logfunc') as log:
                headers, rows, source = sshServerLog.sshServerLog.__wrapped__(FakeContext(files, root))
            self.assertEqual(len(headers), len(rows[0]))
            self.assertEqual([(row[-1], row[-2], row[6]) for row in rows],
                             [(os.path.join('var', 'log', 'auth.log'), 1, 'Accepted'),
                              (os.path.join('var', 'log', 'auth.log'), 3, 'Failed'),
                              (os.path.join('var', 'log', 'auth.log'), 6, ''),
                              (os.path.join('var', 'log', 'auth.log.2.gz'), 1, 'Accepted')])
            self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'auth.log.2.gz')])
            self.assertEqual(log.call_args.args[0], 'SSH Server Log: 1 files that could not be read, '
                                                    '1 lines from other programs, not reported, '
                                                    '3 lines in neither syslog file format, not reported')


if __name__ == '__main__':
    unittest.main()
