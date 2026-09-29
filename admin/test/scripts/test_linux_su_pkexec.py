"""Pin how the User Switches (su) and pkexec Commands artifacts read su's and pkexec's lines in auth.log and secure,
and how User Switches (su, journal) reads su's entries in the systemd journal (files written with journal_writer.py)."""
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
from scripts.artifacts import linuxPkexec, linuxSu
# pylint: enable=wrong-import-position

UTC = timezone.utc


class SuFieldsTest(unittest.TestCase):
    def test_the_switch_forms(self):
        cases = {
            '(to parallels) root on none': ('succeeded', 'root', 'parallels', 'none'),
            '(to root) alice on pts/0': ('succeeded', 'alice', 'root', 'pts/0'),
            'FAILED SU (to root) alice on pts/1': ('failed', 'alice', 'root', 'pts/1'),
            '(to root)  on tty2': ('succeeded', '', 'root', 'tty2'),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxSu.switch_fields(message), expected)

    def test_other_messages_are_not_switches(self):
        for message in ('pam_unix(su:session): session opened for user root(uid=0) by alice(uid=1000)',
                        'pam_unix(su:account): expired password for user alice (root enforced)',
                        'FAILED RUNUSER (to root) alice on pts/0',
                        'Successful su for root by alice',
                        'FAILED su for root by alice',
                        '+ pts/0 alice:root',
                        '- pts/0 alice:root',
                        '(to root) alice on',
                        '(to root) alice on pts/0 extra'):
            with self.subTest(message=message):
                self.assertIsNone(linuxSu.switch_fields(message))

    def test_lines_are_counted_by_kind(self):
        counts = Counter()
        rows = linuxSu.switch_rows(
            b'2026-08-31T18:34:16.317532+04:00 host su[1246]: FAILED SU (to parallels) root on none\n'
            b'2026-08-31T18:34:16.317365+04:00 host su: pam_pwquality(su:chauthtok): user aborted password change\n'
            b'2026-08-31T18:34:17Z host sudo: alice : TTY=pts/0 ; PWD=/ ; USER=root ; COMMAND=/bin/true\n'
            b'not syslog\n'
            b'Sep  6 20:58:24 host su: (to parallels) root on none\n', counts)
        self.assertEqual(rows, [
            (datetime(2026, 8, 31, 14, 34, 16, 317532, tzinfo=UTC), '2026-08-31T18:34:16.317532+04:00', 'host', '1246',
             'failed', 'root', 'parallels', 'none', 1),
            ('', 'Sep  6 20:58:24', 'host', '', 'succeeded', 'root', 'parallels', 'none', 5)])
        self.assertEqual(counts, {'su lines in other forms, not reported': 1,
                                  'lines from other programs, not reported': 1,
                                  'lines in neither syslog file format, not reported': 1})


class PkexecFieldsTest(unittest.TestCase):
    def test_the_command_forms(self):
        cases = {
            'parallels: Executing command [USER=root] [TTY=unknown] [CWD=/home/parallels] [COMMAND=/usr/bin/true]':
                ('parallels', 'Executing command', 'root', 'unknown', '/home/parallels', '/usr/bin/true'),
            'alice: Error executing command as another user: Not authorized [USER=root] [TTY=/dev/pts/0] '
            '[CWD=/tmp] [COMMAND=/usr/bin/id -u]':
                ('alice', 'Error executing command as another user: Not authorized', 'root', '/dev/pts/0', '/tmp',
                 '/usr/bin/id -u'),
            'alice: Error executing command as another user: Request dismissed [USER=root] [TTY=unknown] '
            '[CWD=/home/alice] [COMMAND=/usr/bin/gparted]':
                ('alice', 'Error executing command as another user: Request dismissed', 'root', 'unknown',
                 '/home/alice', '/usr/bin/gparted'),
            'alice: The value for the SHELL variable was not found the /etc/shells file [USER=root] [TTY=unknown] '
            '[CWD=/] [COMMAND=/bin/sh]':
                ('alice', 'The value for the SHELL variable was not found the /etc/shells file', 'root', 'unknown', '/',
                 '/bin/sh'),
            'alice: The value for environment variable TERM contains suspicious content [USER=bob] [TTY=unknown] '
            '[CWD=/srv/my dir] [COMMAND=/usr/bin/env a]b]':
                ('alice', 'The value for environment variable TERM contains suspicious content', 'bob', 'unknown',
                 '/srv/my dir', '/usr/bin/env a]b'),
            'alice: Executing command [USER=root] [TTY=unknown] [CWD=/a] [COMMAND=/bin/echo b] [COMMAND=c]':
                ('alice', 'Executing command', 'root', 'unknown', '/a', '/bin/echo b] [COMMAND=c'),
            'alice: Executing command [USER=root] [TTY=unknown] [CWD=/] [COMMAND=/bin/echo [USER=a] [TTY=b] [CWD=c] '
            '[COMMAND=d]]':
                ('alice', 'Executing command', 'root', 'unknown', '/', '/bin/echo [USER=a] [TTY=b] [CWD=c] [COMMAND=d]'),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxPkexec.command_fields(message), expected)

    def test_other_messages_are_not_commands(self):
        for message in ('pam_unix(polkit-1:session): session opened for user root(uid=0) by alice(uid=1000)',
                        'alice: Executing command',
                        'alice: Executing command [USER=root] [TTY=unknown] [CWD=/]',
                        'Executing command [USER=root] [TTY=unknown] [CWD=/] [COMMAND=/bin/true]',
                        'alice: Executing command [USER=root] [TTY=unknown] [CWD=/] [COMMAND=/bin/true] trailing'):
            with self.subTest(message=message):
                self.assertIsNone(linuxPkexec.command_fields(message))

    def test_lines_are_counted_by_kind(self):
        counts = Counter()
        rows = linuxPkexec.command_rows(
            b'2026-09-06T20:57:31.470468-04:00 host pkexec: pam_unix(polkit-1:session): session opened for user '
            b'root(uid=0) by alice(uid=1000)\n'
            b'2026-09-06T20:57:31.473047-04:00 host pkexec[5088]: alice: Executing command [USER=root] [TTY=unknown] '
            b'[CWD=/home/alice] [COMMAND=/usr/bin/true -v]\n'
            b'2026-09-06T20:57:32Z host su[3]: (to root) alice on pts/0\n'
            b'not syslog\n', counts)
        self.assertEqual(rows, [
            (datetime(2026, 9, 7, 0, 57, 31, 473047, tzinfo=UTC), '2026-09-06T20:57:31.473047-04:00', 'host', '5088',
             'alice', 'Executing command', 'root', 'unknown', '/home/alice', '/usr/bin/true -v', 2)])
        self.assertEqual(counts, {'pkexec lines in other forms, not reported': 1,
                                  'lines from other programs, not reported': 1,
                                  'lines in neither syslog file format, not reported': 1})


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def stage(root, auth):
    logs = os.path.join(root, 'var', 'log')
    os.makedirs(logs)
    files = []
    for name, data in (('secure', auth.encode()), ('auth.log.1', b'not syslog\n'), ('auth.log', auth.encode()),
                       ('auth.log.2.gz', b'\x1f\x8b\x08\x00broken')):
        path = os.path.join(logs, name)
        with open(path, 'wb') as handle:
            handle.write(data)
        files.append(path)
    files.append(logs)
    return logs, files


class ArtifactTest(unittest.TestCase):
    def test_su_rows_name_their_file_and_line(self):
        auth = ('2026-09-28T09:00:00.000001+00:00 host sshd[1]: Accepted publickey for alex\n'
                '2026-09-28T09:00:01.000001+00:00 host su[610]: (to root) alex on pts/0\n'
                'Feb  6 15:16:32 box su: FAILED SU (to root) alex on pts/1\n')
        with tempfile.TemporaryDirectory() as root:
            logs, files = stage(root, auth)
            with mock.patch.object(linuxSu, 'logfunc') as log:
                headers, rows, source = linuxSu.linuxSu.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        per_file = [(datetime(2026, 9, 28, 9, 0, 1, 1, tzinfo=UTC), '610', 'succeeded', 'alex', 'root', 'pts/0', 2),
                    ('', '', 'failed', 'alex', 'root', 'pts/1', 3)]
        self.assertEqual([(r[0], *r[3:9]) for r in rows], [row for name in ('auth.log', 'secure') for row in per_file])
        self.assertEqual([r[9] for r in rows],
                         [os.path.join('var', 'log', n) for n in ('auth.log', 'auth.log', 'secure', 'secure')])
        self.assertEqual((rows[1][1], rows[1][2]), ('Feb  6 15:16:32', 'box'))
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'User Switches (su): 1 files that could not be read, '
                                                '2 lines from other programs, not reported, '
                                                '1 lines in neither syslog file format, not reported')

    def test_pkexec_rows_name_their_file_and_line(self):
        auth = ('2026-09-28T09:00:00.000001+00:00 host pkexec: pam_unix(polkit-1:session): session opened for user '
                'root(uid=0) by alex(uid=1000)\n'
                '2026-09-28T09:00:01.000001+00:00 host pkexec[611]: alex: Executing command [USER=root] [TTY=unknown] '
                '[CWD=/home/alex] [COMMAND=/usr/bin/true]\n'
                'Feb  6 15:16:32 box pkexec[88]: alex: Error executing command as another user: Not authorized '
                '[USER=root] [TTY=/dev/pts/2] [CWD=/] [COMMAND=/bin/sh]\n')
        with tempfile.TemporaryDirectory() as root:
            logs, files = stage(root, auth)
            with mock.patch.object(linuxPkexec, 'logfunc') as log:
                headers, rows, source = linuxPkexec.linuxPkexec.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        per_file = [(datetime(2026, 9, 28, 9, 0, 1, 1, tzinfo=UTC), '611', 'alex', 'Executing command', 'root',
                     'unknown', '/home/alex', '/usr/bin/true', 2),
                    ('', '88', 'alex', 'Error executing command as another user: Not authorized', 'root', '/dev/pts/2',
                     '/', '/bin/sh', 3)]
        self.assertEqual([(r[0], *r[3:11]) for r in rows], [row for name in ('auth.log', 'secure') for row in per_file])
        self.assertEqual([r[11] for r in rows],
                         [os.path.join('var', 'log', n) for n in ('auth.log', 'auth.log', 'secure', 'secure')])
        self.assertEqual((rows[1][1], rows[1][2]), ('Feb  6 15:16:32', 'box'))
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'pkexec Commands: 1 files that could not be read, '
                                                '1 lines in neither syslog file format, not reported, '
                                                '2 pkexec lines in other forms, not reported')


BOOT = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')
T0 = 1790000000


def journal_bytes(entries):
    """A journal file of (realtime seconds, SYSLOG_IDENTIFIER or None, MESSAGE, SYSLOG_PID or None) entries."""
    writer = jw.JournalWriter(boot_id=BOOT)
    for n, (realtime, ident, message, pid) in enumerate(entries, 1):
        fields = [('_TRANSPORT', b'syslog'), ('_HOSTNAME', b'vm'), ('MESSAGE', message.encode())]
        if ident is not None:
            fields.append(('SYSLOG_IDENTIFIER', ident.encode()))
        if pid is not None:
            fields.append(('SYSLOG_PID', pid.encode()))
        writer.add_entry(fields, int(realtime * 1000000), n * 1000000)
    return writer.bytes()


class SuJournalTest(unittest.TestCase):
    def test_switch_entries_and_counts(self):
        entries = [(T0 + 2, 'su', 'FAILED SU (to root) alice on pts/1', '31'),
                   (T0 + 1, 'su', '(to parallels) root on none', '30'),
                   (T0 + 3, 'su', 'pam_unix(su:session): session opened for user parallels(uid=1000) by (uid=0)', '30'),
                   (T0 + 4, 'su', '(to root) bob on tty2', None),
                   (T0 + 5, 'SU', '(to root) bob on tty2', '1'), (T0 + 6, '/bin/su', '(to root) bob on tty2', '1'),
                   (T0 + 7, 'runuser', '(to root) bob on tty2', '1'), (T0 + 8, None, '(to root) bob on tty2', '1')]
        counts = Counter()
        rows = linuxSu.journal_switch_rows([('j', systemd_journal.JournalFile(journal_bytes(entries)))], counts)
        at = lambda s: datetime.fromtimestamp(T0 + s, UTC)
        self.assertEqual(rows, [(at(1), 'vm', '30', 'succeeded', 'root', 'parallels', 'none', BOOT.hex(), 'j'),
                                (at(2), 'vm', '31', 'failed', 'alice', 'root', 'pts/1', BOOT.hex(), 'j'),
                                (at(4), 'vm', '', 'succeeded', 'bob', 'root', 'tty2', BOOT.hex(), 'j')])
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 4, 'su entries in other forms, not reported': 1})

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (('system.journal', journal_bytes([(T0, 'su', '(to root) bob on tty2', '9')])),
                               ('user-1000.journal', journal_bytes([(T0, 'sudo', 'x', '8')])),
                               ('broken.journal', b'not a journal')):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            files.append(folder)
            with mock.patch.object(linuxSu, 'logfunc') as log:
                headers, rows, source = linuxSu.linuxSuJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(headers, (('Time (UTC)', 'datetime'), 'Hostname', 'Process ID', 'Result', 'From User',
                                   'To User', 'Terminal', 'Boot ID', 'Source File'))
        self.assertEqual([r[1:] for r in rows], [('vm', '9', 'succeeded', 'bob', 'root', 'tty2', BOOT.hex(),
                                                  os.path.join('var', 'log', 'journal', 'm', 'system.journal'))])
        self.assertEqual(source, os.path.join(folder, 'system.journal'))
        self.assertEqual(log.call_args.args[0], 'User Switches (su, journal): 1 entries of other programs, '
                                                '1 journal files not read (JournalError)')


    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 'su', '(to root) bob on tty2', '9')]))
            with mock.patch.object(linuxSu, 'logfunc') as log:
                _headers, rows, source = linuxSu.linuxSuJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


class PkexecJournalTest(unittest.TestCase):
    CMD = 'parallels: Executing command [USER=root] [TTY=unknown] [CWD=/home/parallels] [COMMAND=/usr/bin/true a b]'

    def test_command_entries_and_counts(self):
        entries = [(T0 + 2, 'pkexec', 'bob: Error executing command as another user: Not authorized [USER=root] '
                    '[TTY=/dev/pts/0] [CWD=/tmp] [COMMAND=/bin/sh]', '41'),
                   (T0 + 1, 'pkexec', self.CMD, '40'),
                   (T0 + 3, 'pkexec', 'pam_unix(polkit-1:session): session opened for user root(uid=0) by '
                    'parallels(uid=1000)', None),
                   (T0 + 4, 'pkexec', self.CMD, None),
                   (T0 + 5, 'PKEXEC', self.CMD, '1'), (T0 + 6, '/usr/bin/pkexec', self.CMD, '1'),
                   (T0 + 7, 'sudo', self.CMD, '1'), (T0 + 8, None, self.CMD, '1')]
        counts = Counter()
        rows = linuxPkexec.journal_command_rows([('j', systemd_journal.JournalFile(journal_bytes(entries)))], counts)
        at = lambda s: datetime.fromtimestamp(T0 + s, UTC)
        cmd = ('parallels', 'Executing command', 'root', 'unknown', '/home/parallels', '/usr/bin/true a b')
        self.assertEqual(rows, [(at(1), 'vm', '40', *cmd, BOOT.hex(), 'j'),
                                (at(2), 'vm', '41', 'bob', 'Error executing command as another user: Not authorized',
                                 'root', '/dev/pts/0', '/tmp', '/bin/sh', BOOT.hex(), 'j'),
                                (at(4), 'vm', '', *cmd, BOOT.hex(), 'j')])
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 4, 'pkexec entries in other forms, not reported': 1})

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (('system.journal', journal_bytes([(T0, 'pkexec', self.CMD, '9')])),
                               ('user-1000.journal', journal_bytes([(T0, 'su', 'x', '8')])),
                               ('broken.journal', b'not a journal')):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            files.append(folder)
            with mock.patch.object(linuxPkexec, 'logfunc') as log:
                headers, rows, source = linuxPkexec.linuxPkexecJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(headers, (('Time (UTC)', 'datetime'), 'Hostname', 'Process ID', 'User', 'Message', 'Run As',
                                   'TTY', 'Working Directory', 'Command', 'Boot ID', 'Source File'))
        self.assertEqual([r[1:] for r in rows], [('vm', '9', 'parallels', 'Executing command', 'root', 'unknown',
                                                  '/home/parallels', '/usr/bin/true a b', BOOT.hex(),
                                                  os.path.join('var', 'log', 'journal', 'm', 'system.journal'))])
        self.assertEqual(source, os.path.join(folder, 'system.journal'))
        self.assertEqual(log.call_args.args[0], 'pkexec Commands (journal): 1 entries of other programs, '
                                                '1 journal files not read (JournalError)')

    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 'pkexec', self.CMD, '9')]))
            with mock.patch.object(linuxPkexec, 'logfunc') as log:
                _headers, rows, source = linuxPkexec.linuxPkexecJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


if __name__ == '__main__':
    unittest.main()
