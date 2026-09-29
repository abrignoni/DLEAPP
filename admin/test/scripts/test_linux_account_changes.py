"""Pin how the Account Changes artifacts read the shadow account tools' lines in auth.log and secure and their entries
in the systemd journal (journal files written with journal_writer.py)."""
import os
import pathlib
import re
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
from scripts.artifacts import linuxAccountChanges
# pylint: enable=wrong-import-position

UTC = timezone.utc
VALUES = {'A': 'acct', 'G': 'grp', 'B': 'caller', '-': 'x1', 'X': 'group grp/1001, new name: grp2'}


def written(fmt, roles):
    """The message a program writes with fmt, each placeholder filled with the value for its role; a
    placeholder straight after another is gpasswd's suffix, " in <file>"."""
    parts = re.split(r'(%l?[sdu])', fmt.rstrip('\n'))
    out = []
    for index, part in enumerate(parts):
        if index % 2 == 0:
            out.append(part)
        elif part != '%s':
            out.append('7')
        elif index > 1 and parts[index - 1] == '':
            out.append(' in /etc/group')
        else:
            out.append(VALUES[roles[index // 2]])
    return ''.join(out)


class FormatTest(unittest.TestCase):
    def test_every_format_names_its_account_group_and_caller(self):
        for fmt, roles in linuxAccountChanges._FORMATS:  # pylint: disable=protected-access
            expected = (VALUES['A'] if 'A' in roles else '', VALUES['G'] if 'G' in roles or 'X' in roles else '',
                        VALUES['B'] if 'B' in roles else '')
            with self.subTest(fmt=fmt):
                self.assertEqual(linuxAccountChanges.named(written(fmt, roles)), expected)

    def test_lines_as_the_two_releases_write_them(self):
        cases = {
            'new user: name=bob, UID=1001, GID=1001, home=/home/bob, shell=/bin/bash, from=/dev/pts/0': ('bob', '', ''),
            'new user: name=bob, UID=1001, GID=1001, home=/home/bob, shell=/bin/sh': ('bob', '', ''),
            "add 'bob' to group 'sudo'": ('bob', 'sudo', ''),
            "add `bob' to shadow group `sudo'": ('bob', 'sudo', ''),
            "removed group 'bob' owned by 'bob'": ('bob', 'bob', ''),
            "change user `svc' password": ('svc', '', ''),
            "change user 'bob' shell from '/bin/sh' to '/bin/bash'": ('bob', '', ''),
            "password for 'root' changed by 'bob'": ('root', '', 'bob'),
            'passwd: can\'t view or modify password information for bob': ('bob', '', ''),
            'user bob added by root to group staff in /etc/gshadow': ('bob', 'staff', 'root'),
            'add member bob to group staff by root': ('bob', 'staff', 'root'),
            'changed password expiry for bob': ('bob', '', ''),
            'group changed in /etc/gshadow (group staff, new name: crew)': ('', 'staff', ''),
            'failed to change /etc/passwd (group staff/50, new gid: 60)': ('', 'staff', ''),
            'failed to add user bob to /etc/passwd': ('bob', '', ''),
            "delete 'bob' from group 'sudo'": ('bob', 'sudo', ''),
            "delete `bob' from shadow group `sudo'": ('bob', 'sudo', ''),
            "removed group `bob' owned by `bob'": ('bob', 'bob', ''),
            "change user name 'bob' to 'rob'": ('bob', '', ''),
            "change user 'bob' inactive from '-1' to '30'": ('bob', '', ''),
            "change user `bob' UID from `1001' to `1500'": ('bob', '', ''),
            "change 'bob' to 'rob' in group 'staff'": ('bob', 'staff', ''),
            "change admin `bob' to `rob' in shadow group `staff'": ('bob', 'staff', ''),
            "group 'staff' removed from /etc/group": ('', 'staff', ''),
            "remove group `staff'": ('', 'staff', ''),
            "change group `staff' to `crew'": ('', 'staff', ''),
            "change GID for `crew' to 60": ('', 'crew', ''),
            'group added to /etc/group: name=staff, GID=50': ('', 'staff', ''),
            'group added to /etc/gshadow: name=staff': ('', 'staff', ''),
            'new group: name=staff, GID=50': ('', 'staff', ''),
            "failed adding user 'bob', exit code: 12": ('bob', '', ''),
            'failed to reset the tallylog entry of user "bob"': ('bob', '', ''),
            'password of group staff removed by root in /etc/group': ('', 'staff', 'root'),
            'members of group staff set by root to bob,rob': ('', 'staff', 'root'),
            'root failed to add user bob to group staff in /etc/group': ('bob', 'staff', 'root'),
            'root failed to set the administrators of group staff to bob': ('', 'staff', 'root'),
            'change the password for group staff by root': ('', 'staff', 'root'),
            'remove member bob from group staff by root': ('bob', 'staff', 'root'),
            'set administrators of staff to bob,rob': ('', 'staff', ''),
            "changed user `bob' shell to `/bin/zsh'": ('bob', '', ''),
            "can't change shell for 'bob'": ('bob', '', ''),
            'failed to remove group staff from /etc/gshadow': ('', 'staff', ''),
            'incorrect password for bob': ('bob', '', ''),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxAccountChanges.named(message), expected)

    def test_one_form_names_a_user_or_a_group_by_program(self):
        message = "failed to prepare the new /etc/group entry 'bob'"
        self.assertEqual(linuxAccountChanges.named(message, 'useradd'), ('bob', '', ''))
        self.assertEqual(linuxAccountChanges.named(message, 'usermod'), ('', 'bob', ''))

    def test_a_trailing_line_feed_dropped_or_escaped(self):
        for message in ("delete user 'bob'", "delete user 'bob'#012", "delete user 'bob'\n"):
            self.assertEqual(linuxAccountChanges.named(message), ('bob', '', ''))

    def test_messages_that_name_nobody(self):
        for message in ('failed to unlock /etc/passwd', 'cannot open /etc/group',
                        'pam_unix(passwd:chauthtok): password changed for bob', "delete user 'bob' now"):
            self.assertEqual(linuxAccountChanges.named(message), ('', '', ''))

    def test_every_format_has_one_role_per_placeholder(self):
        for fmt, roles in linuxAccountChanges._FORMATS:  # pylint: disable=protected-access
            self.assertEqual(len(re.findall(r'%l?[sdu]', fmt)), len(roles), fmt)
        with self.assertRaises(ValueError):
            linuxAccountChanges._pattern('add %s to %s', 'A')  # pylint: disable=protected-access


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
                '2026-09-28T09:00:01.000001+00:00 host useradd[20]: new user: name=bob, UID=1001, GID=1001, '
                'home=/home/bob, shell=/bin/bash, from=/dev/pts/0\n'
                '2026-09-28T09:00:02.000001+00:00 host usermod[21]: add \'bob\' to group \'sudo\'\n'
                '2026-09-28T09:00:02.500001+00:00 host useradd[24]: failed to prepare the new /etc/group entry \'bob\'\n'
                '2026-09-28T09:00:03.000001+00:00 host passwd[22]: pam_unix(passwd:chauthtok): password changed for bob\n'
                'Feb  6 15:16:32 box chage[23]: changed password expiry for bob\n')
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
            with mock.patch.object(linuxAccountChanges, 'logfunc') as log:
                headers, rows, source = linuxAccountChanges.linuxAccountChanges.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        per_file = [(datetime(2026, 9, 28, 9, 0, 1, 1, tzinfo=UTC), 'useradd', '20', 'bob', '', '', 2),
                    (datetime(2026, 9, 28, 9, 0, 2, 1, tzinfo=UTC), 'usermod', '21', 'bob', 'sudo', '', 3),
                    (datetime(2026, 9, 28, 9, 0, 2, 500001, tzinfo=UTC), 'useradd', '24', 'bob', '', '', 4),
                    (datetime(2026, 9, 28, 9, 0, 3, 1, tzinfo=UTC), 'passwd', '22', '', '', '', 5),
                    ('', 'chage', '23', 'bob', '', '', 6)]
        self.assertEqual([(r[0], r[3], r[4], r[6], r[7], r[8], r[9], r[10]) for r in rows],
                         [row + (os.path.join('var', 'log', name),) for name in ('auth.log', 'secure') for row in per_file])
        self.assertEqual(rows[4][1], 'Feb  6 15:16:32')
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'Account Changes: 1 files that could not be read, '
                                                '2 lines from other programs, not reported, '
                                                '1 lines in neither syslog file format, not reported')


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
    def test_entries_of_the_shadow_programs_and_counts(self):
        entries = [(T0 + 2, 'useradd', "new user: name=acct, UID=1001, GID=1001, home=/home/acct, shell=/bin/sh, from=/dev/pts/0",
                    '51'),
                   (T0 + 1, 'groupadd', "group added to /etc/group: name=grp, GID=1001", '50'),
                   (T0 + 3, 'sshd', "new user: name=acct, UID=1001", '9'),
                   (T0 + 4, 'Useradd', "new user: name=acct, UID=1001", '9')]
        counts = Counter()
        rows = linuxAccountChanges.journal_change_rows([('j', systemd_journal.JournalFile(journal_bytes(entries)))], counts)
        expected = [(entries[1][2], 'groupadd', '50'), (entries[0][2], 'useradd', '51')]
        self.assertEqual([(r[4], r[2], r[3]) for r in rows], expected)
        self.assertEqual([r[5:8] for r in rows], [linuxAccountChanges.named(m, p) for m, p, _pid in expected])
        self.assertEqual([(r[0], r[1], r[8], r[9]) for r in rows],
                         [(datetime.fromtimestamp(T0 + s, UTC), 'vm', BOOT.hex(), 'j') for s in (1, 2)])
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 2})

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (('system.journal', journal_bytes([(T0, 'userdel', 'delete user \'acct\'', '7')])),
                               ('user-1000.journal', journal_bytes([(T0, 'su', 'x', '1')])),
                               ('broken.journal', b'not a journal')):
                files.append(os.path.join(folder, name))
                with open(files[-1], 'wb') as handle:
                    handle.write(data)
            files.append(folder)
            with mock.patch.object(linuxAccountChanges, 'logfunc') as log:
                headers, rows, source = linuxAccountChanges.linuxAccountChangesJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(headers, (('Time (UTC)', 'datetime'), 'Hostname', 'Program', 'Process ID', 'Message', 'Account',
                                   'Group', 'Run By', 'Boot ID', 'Source File'))
        self.assertEqual([(r[2], r[3], r[4], r[-2], r[-1]) for r in rows],
                         [('userdel', '7', "delete user 'acct'", BOOT.hex(), os.path.join('var', 'log', 'journal', 'm', 'system.journal'))])
        self.assertEqual(source, os.path.join(folder, 'system.journal'))
        self.assertEqual(log.call_args.args[0], 'Account Changes (journal): 1 entries of other programs, '
                                                '1 journal files not read (JournalError)')

    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 'userdel', "delete user 'acct'", '7')]))
            with mock.patch.object(linuxAccountChanges, 'logfunc') as log:
                _headers, rows, source = linuxAccountChanges.linuxAccountChangesJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


if __name__ == '__main__':
    unittest.main()
