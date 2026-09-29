"""Pin how the Login Sessions (logind) and Power Events (logind) artifacts read systemd-logind's lines in auth.log
and secure, and how Login Sessions (logind, journal) and Power Events (logind, journal) read its entries in the
systemd journal (files written with journal_writer.py)."""
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
from scripts.artifacts import linuxLogind
# pylint: enable=wrong-import-position

UTC = timezone.utc


class FieldsTest(unittest.TestCase):
    def test_the_session_forms(self):
        cases = {
            "New session '42' of user 'alex' with class 'user' and type 'tty'.": ('new', '42', 'alex', 'user', 'tty'),
            "New session 'c3' of user 'gdm' with class 'greeter' and type 'wayland'.":
                ('new', 'c3', 'gdm', 'greeter', 'wayland'),
            'New session 7 of user john.doe.': ('new', '7', 'john.doe', '', ''),
            'New session c1 of user gdm.': ('new', 'c1', 'gdm', '', ''),
            'Session 42 logged out. Waiting for processes to exit.': ('logged out', '42', '', '', ''),
            'Removed session c1.': ('removed', 'c1', '', '', ''),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxLogind.session_fields(message), expected)

    def test_other_messages_are_not_sessions(self):
        for message in ('New seat seat0.',
                        'Watching system buttons on /dev/input/event0 (Power Button)',
                        "New session '42' of user 'alex' with class 'user'.",
                        'New session 42 of user alex',
                        'Session 42 logged out.',
                        'Removed session 42',
                        'System is powering down.'):
            with self.subTest(message=message):
                self.assertIsNone(linuxLogind.session_fields(message))

    def test_lines_are_counted_by_kind(self):
        counts = Counter()
        rows = linuxLogind.session_rows(
            b"2026-09-28T05:00:00.000001-04:00 host systemd-logind[610]: New session '9' of user 'alex' with class "
            b"'user' and type 'tty'.\n"
            b'2026-09-28T05:00:01Z host systemd-logind[610]: New seat seat0.\n'
            b'2026-09-28T05:00:02Z host sshd[3]: Accepted publickey for alex\n'
            b'not syslog\n'
            b'2026-02-30T05:00:03Z host systemd-logind[610]: Removed session 9.\n', counts)
        self.assertEqual(rows, [
            (datetime(2026, 9, 28, 9, 0, 0, 1, tzinfo=UTC), '2026-09-28T05:00:00.000001-04:00', 'host', '610', 'new',
             '9', 'alex', 'user', 'tty', 1),
            ('', '2026-02-30T05:00:03Z', 'host', '610', 'removed', '9', '', '', '', 5)])
        self.assertEqual(counts, {'systemd-logind lines in other forms, not reported': 1,
                                  'lines from other programs, not reported': 1,
                                  'lines in neither syslog file format, not reported': 1,
                                  'RFC 3339 times that are not a calendar date, Time (UTC) left blank': 1})


class PowerFieldsTest(unittest.TestCase):
    def test_the_power_forms(self):
        cases = {
            'System is powering down.': ('shutdown', '', ''),
            'System is rebooting.': ('shutdown', '', ''),
            'System is halting.': ('shutdown', '', ''),
            'System is rebooting with kexec.': ('shutdown', '', ''),
            'System userspace is rebooting.': ('shutdown', '', ''),
            'System is performing factory reset.': ('shutdown', '', ''),
            'System is shutting down.': ('shutdown', '', ''),
            'System is rebooting (Kernel update).': ('shutdown', '', 'Kernel update'),
            'System is rebooting (back (soon)). Really.).': ('shutdown', '', 'back (soon)). Really.'),
            'System is rebooting with kexec (x).': ('shutdown', '', 'x'),
            'System is powering down. (maintenance window)': ('shutdown', '', 'maintenance window'),
            'The system will reboot at Mon 2026-09-28 10:24:47 EDT!': ('warning', 'Mon 2026-09-28 10:24:47 EDT', ''),
            'The system will power off at Wed 2026-08-12 16:30:47 +04!': ('warning', 'Wed 2026-08-12 16:30:47 +04', ''),
            'The system will power off now!': ('warning', 'now', ''),
            'The system will suspend and later hibernate at Tue 2026-09-29 01:00:00 UTC!':
                ('warning', 'Tue 2026-09-29 01:00:00 UTC', ''),
            'Running in dry run, suppressing action.': ('dry run', '', ''),
            'Creating /run/nologin, blocking further logins...': ('logins blocked', '', ''),
            'System shutdown has been cancelled': ('shutdown cancelled', '', ''),
            'New seat seat0.': ('seat started', '', ''),
            'New seat seat-usb1.': ('seat started', '', ''),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxLogind.power_fields(message), expected)

    def test_other_messages_are_not_power_lines(self):
        for message in ('Watching system buttons on /dev/input/event0 (Power Button)',
                        "New session '42' of user 'alex' with class 'user' and type 'tty'.",
                        'Removed session 42.',
                        'Power key pressed short.',
                        'Lid closed.',
                        'Powering off...',
                        'System is docked.',
                        'System is rebooting',
                        'System is rebooting (x)',
                        'The system is going down for reboot at Mon 2026-09-28 10:24:47 EDT!',
                        'The system shutdown has been cancelled',
                        'System shutdown has been cancelled.',
                        'Running in dry run, suppressing action',
                        'Removed seat seat0.',
                        'New seat seat0'):
            with self.subTest(message=message):
                self.assertIsNone(linuxLogind.power_fields(message))

    def test_lines_are_counted_by_kind(self):
        counts = Counter()
        rows = linuxLogind.power_rows(
            b'2026-09-28T10:28:26.590222-04:00 host systemd-logind[1046]: System is rebooting (Kernel update).\n'
            b"2026-09-28T10:28:26Z host systemd-logind[1046]: New session '9' of user 'alex' with class 'user' and "
            b"type 'tty'.\n"
            b'2026-09-28T10:28:27Z host sshd[3]: Accepted publickey for alex\n'
            b'not syslog\n'
            b'Sep 28 10:28:28 host systemd-logind[1046]: Running in dry run, suppressing action.\n', counts)
        self.assertEqual(rows, [
            (datetime(2026, 9, 28, 14, 28, 26, 590222, tzinfo=UTC), '2026-09-28T10:28:26.590222-04:00', 'host', '1046',
             'shutdown', '', 'Kernel update', 'System is rebooting (Kernel update).', 1),
            ('', 'Sep 28 10:28:28', 'host', '1046', 'dry run', '', '', 'Running in dry run, suppressing action.', 5)])
        self.assertEqual(counts, {'systemd-logind lines in other forms, not reported': 1,
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


class ArtifactTest(unittest.TestCase):
    def test_rows_name_their_file_and_line(self):
        auth = ('2026-09-28T09:00:00.000001+00:00 host sshd[1]: Accepted publickey for alex\n'
                "2026-09-28T09:00:01.000001+00:00 host systemd-logind[610]: New session '4' of user 'alex' with class "
                "'user' and type 'tty'.\n"
                'Feb  6 15:16:32 box systemd-logind[88]: Session c2 logged out. Waiting for processes to exit.\n')
        with tempfile.TemporaryDirectory() as root:
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
            with mock.patch.object(linuxLogind, 'logfunc') as log:
                headers, rows, source = linuxLogind.linuxLogindSessions.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        per_file = [(datetime(2026, 9, 28, 9, 0, 1, 1, tzinfo=UTC), '610', 'new', '4', 'alex', 'user', 'tty', 2),
                    ('', '88', 'logged out', 'c2', '', '', '', 3)]
        self.assertEqual([(r[0], *r[3:10]) for r in rows],
                         [row for name in ('auth.log', 'secure') for row in per_file])
        self.assertEqual([r[10] for r in rows],
                         [os.path.join('var', 'log', n) for n in ('auth.log', 'auth.log', 'secure', 'secure')])
        self.assertEqual((rows[1][1], rows[1][2]), ('Feb  6 15:16:32', 'box'))
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'Login Sessions (logind): 1 files that could not be read, '
                                                '2 lines from other programs, not reported, '
                                                '1 lines in neither syslog file format, not reported')


    def test_power_rows_name_their_file_and_line(self):
        auth = ('2026-09-28T14:23:47.373514+00:00 host systemd-logind[1046]: The system will reboot at Mon 2026-09-28 '
                '10:24:47 EDT!\n'
                "2026-09-28T14:23:48+00:00 host systemd-logind[1046]: New session '4' of user 'alex' with class 'user' "
                "and type 'tty'.\n"
                'Feb  6 15:16:32 box systemd-logind[88]: New seat seat0.\n')
        with tempfile.TemporaryDirectory() as root:
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
            with mock.patch.object(linuxLogind, 'logfunc') as log:
                headers, rows, source = linuxLogind.linuxLogindPower.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        per_file = [(datetime(2026, 9, 28, 14, 23, 47, 373514, tzinfo=UTC), '1046', 'warning',
                     'Mon 2026-09-28 10:24:47 EDT', '', 'The system will reboot at Mon 2026-09-28 10:24:47 EDT!', 1),
                    ('', '88', 'seat started', '', '', 'New seat seat0.', 3)]
        self.assertEqual([(r[0], *r[3:9]) for r in rows],
                         [row for name in ('auth.log', 'secure') for row in per_file])
        self.assertEqual([r[9] for r in rows],
                         [os.path.join('var', 'log', n) for n in ('auth.log', 'auth.log', 'secure', 'secure')])
        self.assertEqual((rows[1][1], rows[1][2]), ('Feb  6 15:16:32', 'box'))
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'Power Events (logind): 1 files that could not be read, '
                                                '1 lines in neither syslog file format, not reported, '
                                                '2 systemd-logind lines in other forms, not reported')


BOOT = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')
T0 = 1790000000


def journal_bytes(entries):
    """A journal file of (realtime seconds, SYSLOG_IDENTIFIER, MESSAGE, _PID, SYSLOG_PID or None) entries, sent the way
    systemd-logind sends them, over the journal's own transport."""
    writer = jw.JournalWriter(boot_id=BOOT)
    for n, (realtime, ident, message, pid, syslog_pid) in enumerate(entries, 1):
        fields = [('_TRANSPORT', b'journal'), ('_HOSTNAME', b'vm'), ('SYSLOG_IDENTIFIER', ident.encode()),
                  ('MESSAGE', message.encode()), ('_PID', pid.encode())]
        if syslog_pid is not None:
            fields.append(('SYSLOG_PID', syslog_pid.encode()))
        writer.add_entry(fields, int(realtime * 1000000), n * 1000000)
    return writer.bytes()


class SessionsJournalTest(unittest.TestCase):
    def test_session_entries_and_counts(self):
        entries = [(T0 + 2, 'systemd-logind', "New session '4' of user 'alex' with class 'user' and type 'tty'.", '700', None),
                   (T0 + 1, 'systemd-logind', 'New session c1 of user gdm.', '700', None),
                   (T0 + 3, 'systemd-logind', 'Session 4 logged out. Waiting for processes to exit.', '700', '9'),
                   (T0 + 4, 'systemd-logind', 'Removed session 4.', '700', None),
                   (T0 + 5, 'systemd-logind', 'System is rebooting.', '700', None),
                   (T0 + 6, 'Systemd-Logind', 'Removed session 5.', '700', None),
                   (T0 + 7, 'sshd', 'Removed session 5.', '800', None)]
        counts = Counter()
        rows = linuxLogind.journal_session_rows([('j', systemd_journal.JournalFile(journal_bytes(entries)))], counts)
        at = lambda s: datetime.fromtimestamp(T0 + s, UTC)
        self.assertEqual(rows, [(at(1), 'vm', '700', 'new', 'c1', 'gdm', '', '', BOOT.hex(), 'j'),
                                (at(2), 'vm', '700', 'new', '4', 'alex', 'user', 'tty', BOOT.hex(), 'j'),
                                (at(3), 'vm', '700', 'logged out', '4', '', '', '', BOOT.hex(), 'j'),
                                (at(4), 'vm', '700', 'removed', '4', '', '', '', BOOT.hex(), 'j')])
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 2, 'systemd-logind entries in other forms, not reported': 1})

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (('system.journal', journal_bytes([(T0, 'systemd-logind', 'Removed session 4.', '700', None)])),
                               ('user-1000.journal', journal_bytes([(T0, 'su', 'x', '1', None)])),
                               ('broken.journal', b'not a journal')):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            files.append(folder)
            with mock.patch.object(linuxLogind, 'logfunc') as log:
                headers, rows, source = linuxLogind.linuxLogindSessionsJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(headers, (('Time (UTC)', 'datetime'), 'Hostname', 'Process ID', 'Session Event', 'Session',
                                   'User', 'Class', 'Type', 'Boot ID', 'Source File'))
        self.assertEqual([r[1:] for r in rows], [('vm', '700', 'removed', '4', '', '', '', BOOT.hex(),
                                                  os.path.join('var', 'log', 'journal', 'm', 'system.journal'))])
        self.assertEqual(source, os.path.join(folder, 'system.journal'))
        self.assertEqual(log.call_args.args[0], 'Login Sessions (logind, journal): 1 entries of other programs, '
                                                '1 journal files not read (JournalError)')

    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 'systemd-logind', 'Removed session 4.', '700', None)]))
            with mock.patch.object(linuxLogind, 'logfunc') as log:
                _headers, rows, source = linuxLogind.linuxLogindSessionsJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))



class PowerJournalTest(unittest.TestCase):
    def test_power_entries_and_counts(self):
        entries = [(T0 + 2, 'systemd-logind', 'System is rebooting.', '700', None),
                   (T0 + 1, 'systemd-logind', 'The system will reboot now!', '700', '9'),
                   (T0 + 3, 'systemd-logind', 'New seat seat0.', '701', None),
                   (T0 + 4, 'systemd-logind', 'System is powering down (maintenance).', '701', None),
                   (T0 + 5, 'systemd-logind', 'Removed session 4.', '701', None),
                   (T0 + 6, 'sshd', 'System is rebooting.', '800', None),
                   (T0 + 7, 'Systemd-Logind', 'System is rebooting.', '700', None)]
        counts = Counter()
        rows = linuxLogind.journal_power_rows([('j', systemd_journal.JournalFile(journal_bytes(entries)))], counts)
        at = lambda s: datetime.fromtimestamp(T0 + s, UTC)
        self.assertEqual(rows, [
            (at(1), 'vm', '700', 'warning', 'now', '', 'The system will reboot now!', BOOT.hex(), 'j'),
            (at(2), 'vm', '700', 'shutdown', '', '', 'System is rebooting.', BOOT.hex(), 'j'),
            (at(3), 'vm', '701', 'seat started', '', '', 'New seat seat0.', BOOT.hex(), 'j'),
            (at(4), 'vm', '701', 'shutdown', '', 'maintenance', 'System is powering down (maintenance).', BOOT.hex(), 'j')])
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 2, 'systemd-logind entries in other forms, not reported': 1})

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (('system.journal', journal_bytes([(T0, 'systemd-logind', 'New seat seat0.', '700', None)])),
                               ('user-1000.journal', journal_bytes([(T0, 'su', 'x', '1', None)])),
                               ('broken.journal', b'not a journal')):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            files.append(folder)
            with mock.patch.object(linuxLogind, 'logfunc') as log:
                headers, rows, source = linuxLogind.linuxLogindPowerJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(headers, (('Time (UTC)', 'datetime'), 'Hostname', 'Process ID', 'Event', 'Scheduled For',
                                   'Wall Message', 'Message', 'Boot ID', 'Source File'))
        self.assertEqual([r[1:] for r in rows], [('vm', '700', 'seat started', '', '', 'New seat seat0.', BOOT.hex(),
                                                  os.path.join('var', 'log', 'journal', 'm', 'system.journal'))])
        self.assertEqual(source, os.path.join(folder, 'system.journal'))
        self.assertEqual(log.call_args.args[0], 'Power Events (logind, journal): 1 entries of other programs, '
                                                '1 journal files not read (JournalError)')

    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 'systemd-logind', 'New seat seat0.', '700', None)]))
            with mock.patch.object(linuxLogind, 'logfunc') as log:
                _headers, rows, source = linuxLogind.linuxLogindPowerJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


if __name__ == '__main__':
    unittest.main()
