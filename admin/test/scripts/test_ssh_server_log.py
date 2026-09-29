"""Pin how the SSH Server Log artifacts read sshd's lines in auth.log and secure and its entries in the systemd
journal (journal files written with journal_writer.py)."""
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
sys.path.insert(0, str(REPO_ROOT / 'admin' / 'test' / 'scripts'))

# pylint: disable=wrong-import-position
import journal_writer as jw
from scripts import linux_syslog, systemd_journal
from scripts.artifacts import sshServerLog
# pylint: enable=wrong-import-position

UTC = timezone.utc


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


BOOT = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')
T0 = 1790000000


def journal_bytes(entries):
    """A journal file of (realtime seconds, SYSLOG_IDENTIFIER, MESSAGE, SYSLOG_PID) entries."""
    writer = jw.JournalWriter(boot_id=BOOT)
    for n, (realtime, ident, message, pid) in enumerate(entries, 1):
        writer.add_entry([('_TRANSPORT', b'syslog'), ('_HOSTNAME', b'vm'), ('SYSLOG_IDENTIFIER', ident.encode()),
                          ('SYSLOG_PID', pid.encode()), ('MESSAGE', message.encode())], int(realtime * 1000000), n * 1000000)
    return writer.bytes()


class JournalTest(unittest.TestCase):
    def test_sshd_entries_and_counts(self):
        entries = [(T0 + 2, 'sshd-session', 'Accepted publickey for alex from 10.0.0.2 port 52110 ssh2: ED25519 '
                    'SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA', '4021'),
                   (T0 + 1, 'sshd', 'Server listening on 0.0.0.0 port 22.', '900'),
                   (T0 + 3, 'sshd-auth', 'Invalid user bob from 192.0.2.9 port 4242', '4030'),
                   (T0 + 4, 'sudo', 'alex : TTY=pts/0 ; COMMAND=/bin/true', '4100'),
                   (T0 + 5, 'SSHD', 'Failed password for root from 192.0.2.9 port 1 ssh2', '1')]
        counts = Counter()
        rows = sshServerLog.journal_log_rows([('j', systemd_journal.JournalFile(journal_bytes(entries)))], counts)
        at = lambda s: datetime.fromtimestamp(T0 + s, UTC)
        self.assertEqual([(r[0], r[1], r[2], r[3], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[13], r[14]) for r in rows], [
            (at(1), 'vm', 'sshd', '900', '', '', '', '', '', '', '', BOOT.hex(), 'j'),
            (at(2), 'vm', 'sshd-session', '4021', 'Accepted', 'publickey', 'alex', '', '10.0.0.2', '52110', 'ED25519',
             BOOT.hex(), 'j'),
            (at(3), 'vm', 'sshd-auth', '4030', '', '', 'bob', 'Yes', '192.0.2.9', '4242', '', BOOT.hex(), 'j')])
        self.assertEqual(rows[1][12], 'SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA')
        self.assertEqual(rows[0][4], 'Server listening on 0.0.0.0 port 22.')
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 2})

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (('system.journal', journal_bytes([(T0, 'sshd', 'Server listening on :: port 22.', '9')])),
                               ('user-1000.journal', journal_bytes([(T0, 'su', 'x', '1')])),
                               ('broken.journal', b'not a journal')):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            files.append(folder)
            with mock.patch.object(sshServerLog, 'logfunc') as log:
                headers, rows, source = sshServerLog.sshServerLogJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), 15)
        self.assertEqual(headers[-2:], ('Boot ID', 'Source File'))
        self.assertEqual([(r[2], r[3], r[4], r[-2], r[-1]) for r in rows],
                         [('sshd', '9', 'Server listening on :: port 22.', BOOT.hex(),
                           os.path.join('var', 'log', 'journal', 'm', 'system.journal'))])
        self.assertEqual(source, os.path.join(folder, 'system.journal'))
        self.assertEqual(log.call_args.args[0], 'SSH Server Log (journal): 1 entries of other programs, '
                                                '1 journal files not read (JournalError)')

    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 'sshd', 'Server listening on :: port 22.', '9')]))
            with mock.patch.object(sshServerLog, 'logfunc') as log:
                _headers, rows, source = sshServerLog.sshServerLogJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


if __name__ == '__main__':
    unittest.main()
