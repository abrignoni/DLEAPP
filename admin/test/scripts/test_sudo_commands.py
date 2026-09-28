"""Pin how the sudo Commands artifact reads sudo's lines in auth.log and secure."""
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
from scripts import linux_syslog
from scripts.artifacts import sudoCommands
# pylint: enable=wrong-import-position

UTC = timezone.utc


def rows_of(text):
    counts = Counter()
    entries = sudoCommands.sudo_entries(linux_syslog.program_lines(text.encode(), ('sudo', 'sudo-rs'), counts), counts)
    return [(e['first'], e['last'], e['user'], sudoCommands.command_fields(e['body'])) for e in entries], counts


class FieldsTest(unittest.TestCase):
    def test_sudo_rs_commands_with_and_without_a_terminal(self):
        rows, counts = rows_of(
            '2026-09-28T05:00:00.000001-04:00 host sudo: alex : TTY=/dev/pts/1 ; PWD=/home/alex ; USER=root ; '
            'COMMAND=/usr/bin/id -u\n'
            '2026-09-28T05:00:01.000001-04:00 host sudo: alex :  PWD=/home/alex ; USER=root ; COMMAND=/usr/bin/dmesg \n')
        self.assertEqual(rows, [(1, 1, 'alex', ('', '/dev/pts/1', '/home/alex', 'root', '', '/usr/bin/id -u', '')),
                                (2, 2, 'alex', ('', '', '/home/alex', 'root', '', '/usr/bin/dmesg ', ''))])
        self.assertEqual(counts, {})

    def test_a_refusal_carries_its_reason_and_the_padded_user_is_trimmed(self):
        rows, _counts = rows_of(
            "Feb  6 15:16:32 box sudo:     root : a password is required ; TTY=pts/0 ; PWD=/root ; USER=nobody ; "
            "GROUP=adm ; COMMAND=/usr/bin/printf 'two words'\n"
            'Feb  6 15:16:33 box sudo:     root : authentication failure : unable to read ; TTY=pts/0 ; PWD=/root ; '
            'USER=root ; COMMAND=/bin/ls\n')
        self.assertEqual(rows, [(1, 1, 'root', ('a password is required', 'pts/0', '/root', 'nobody', 'adm',
                                                "/usr/bin/printf 'two words'", '')),
                                (2, 2, 'root', ('authentication failure : unable to read', 'pts/0', '/root', 'root', '',
                                                '/bin/ls', ''))])

    def test_the_other_fields_and_an_exit_status(self):
        fields = sudoCommands.command_fields('HOST=box ; TTY=pts/0 ; CHROOT=/srv ; PWD=/ ; USER=root ; TSID=000001 ; '
                                             'ENV=A=1 B=2 ; COMMAND=/bin/true ; SIGNAL=TERM ; EXIT=143')
        self.assertEqual(fields, ('', 'pts/0', '/', 'root', '', '/bin/true',
                                  'HOST=box ; CHROOT=/srv ; TSID=000001 ; ENV=A=1 B=2 ; SIGNAL=TERM ; EXIT=143'))
        self.assertEqual(sudoCommands.command_fields('TTY=pts/0 ; PWD=/ ; USER=root ; COMMAND=/bin/false ; EXIT=1')[5:],
                         ('/bin/false', 'EXIT=1'))

    def test_command_is_found_only_at_a_field_boundary(self):
        self.assertEqual(sudoCommands.command_fields('TTY=pts/0 ; PWD=/srv/COMMAND=dir ; USER=root ; COMMAND=/bin/ls'),
                         ('', 'pts/0', '/srv/COMMAND=dir', 'root', '', '/bin/ls', ''))

    def test_unknown_and_repeated_fields_go_to_other_fields(self):
        self.assertEqual(sudoCommands.command_fields('TTY=pts/0 ; odd text ; TTY=pts/1 ; PWD=/ ; USER=root ; COMMAND=/bin/ls'),
                         ('', 'pts/0', '/', 'root', '', '/bin/ls', 'odd text ; TTY=pts/1'))

    def test_a_message_without_a_command_field_is_none(self):
        self.assertIsNone(sudoCommands.command_fields('unable to resolve host box: Name or service not known'))


def original_sudo_parts(user, message):
    """The lines the original sudo writes for one message, split the way its do_syslog_sudo() does."""
    parts, fmt = [], '%8s : %s'
    while message:
        limit = 960 - (len(fmt) - 5 + len(user))
        if len(message) > limit:
            cut = message.rfind(' ', 0, limit)
            cut = limit if cut < 0 else cut
            parts.append(fmt % (user, message[:cut]))
            message = message[cut:].lstrip(' ')
        else:
            parts.append(fmt % (user, message))
            message = ''
        fmt = '%8s : (command continued) %s'
    return parts


class SplitTest(unittest.TestCase):
    def test_the_original_sudo_split_is_joined_with_a_space_only_where_it_broke_at_one(self):
        argument = 'x' * 2000
        message = f'a password is required ; PWD=/home/alex ; USER=root ; COMMAND=/usr/bin/printf {argument} end'
        parts = original_sudo_parts('alex', message)
        self.assertEqual([len(p) for p in parts[1:3]], [len('    alex : (command continued) ') + 933] * 2)
        text = ''.join(f'2026-09-28T05:15:14.53{i}-04:00 host sudo: {p}\n' for i, p in enumerate(parts))
        rows, counts = rows_of(text)
        self.assertEqual(rows, [(1, len(parts), 'alex', ('a password is required', '', '/home/alex', 'root', '',
                                                         f'/usr/bin/printf {argument} end', ''))])
        self.assertEqual(counts, {})

    def test_a_first_part_cut_inside_a_word_is_joined_directly(self):
        message = 'z' * 1000 + ' ; PWD=/ ; USER=root ; COMMAND=/bin/true'
        parts = original_sudo_parts('alex', message)
        self.assertEqual(len(parts[0]), len('    alex : ') + 953)
        rows, _counts = rows_of(''.join(f'2026-09-28T05:00:00Z host sudo: {p}\n' for p in parts))
        self.assertEqual(rows, [(1, 2, 'alex', ('z' * 1000, '', '/', 'root', '', '/bin/true', ''))])

    def test_a_sudo_rs_part_cut_at_the_end_of_the_file_is_reported_and_counted(self):
        rows, counts = rows_of('2026-09-28T05:00:00Z host sudo: alex : TTY=/dev/pts/1 ; PWD=/ ; USER=root ; '
                               'COMMAND=/usr/bin/echo a [...]\n')
        self.assertEqual(rows[0][3][5], '/usr/bin/echo a')
        self.assertEqual(counts, {'sudo-rs messages cut short with no part after them, reported as far as they go': 1})

    def test_a_sudo_rs_split_is_joined_exactly(self):
        text = ('2026-09-28T05:00:00Z host sudo: alex : TTY=/dev/pts/1 ; PWD=/ ; USER=root ; COMMAND=/usr/bin/echo aa [...]\n'
                '2026-09-28T05:00:00Z host sudo: [...]  bb [...]\n'
                '2026-09-28T05:00:00Z host sudo: [...]  cc\n')
        rows, counts = rows_of(text)
        self.assertEqual(rows, [(1, 3, 'alex', ('', '/dev/pts/1', '/', 'root', '', '/usr/bin/echo aa bb cc', ''))])
        self.assertEqual(counts, {})

    def test_parts_that_do_not_fit_are_counted(self):
        rows, counts = rows_of(
            '2026-09-28T05:00:00Z host sudo: alex : (command continued) orphan\n'
            '2026-09-28T05:00:00Z host sudo: [...] orphan\n'
            '2026-09-28T05:00:00Z host sudo: pam_unix(sudo:session): session opened for user root(uid=0) by alex(uid=1000)\n'
            '2026-09-28T05:00:00Z host sudo: alex : unable to resolve host box\n'
            '2026-09-28T05:00:00Z host sudo: Could not update session record file\n'
            '2026-09-28T05:00:00Z host sudo: alex : TTY=/dev/pts/1 ; PWD=/ ; USER=root ; COMMAND=/usr/bin/echo a [...]\n'
            '2026-09-28T05:00:01Z host sudo: bob : TTY=/dev/pts/2 ; PWD=/ ; USER=root ; COMMAND=/bin/true\n'
            "2026-09-28T05:00:02Z host sudo: carol : (command continued) not bob's\n")
        self.assertEqual([(r[0], r[1], r[2], r[3] and r[3][5]) for r in rows],
                         [(4, 4, 'alex', None), (6, 6, 'alex', '/usr/bin/echo a'), (7, 7, 'bob', '/bin/true')])
        self.assertEqual(counts, {'continuation lines with no line to continue, not reported': 3,
                                  'PAM lines, not reported': 1,
                                  'sudo lines that are not "<user> : <message>", not reported': 1,
                                  'sudo-rs messages cut short with no part after them, reported as far as they go': 1})


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_rows_name_their_file_and_lines(self):
        long_parts = original_sudo_parts('alex', 'a password is required ; PWD=/ ; USER=root ; COMMAND=/usr/bin/printf '
                                         + 'y' * 1200)
        auth = ('2026-09-28T09:00:00.000001+00:00 host sshd[1]: Accepted publickey for alex\n'
                '2026-09-28T09:00:01.000001+00:00 host sudo: alex :  PWD=/ ; USER=root ; COMMAND=/usr/bin/id \n'
                + ''.join(f'2026-09-28T09:00:02.00000{i}+00:00 host sudo: {p}\n' for i, p in enumerate(long_parts))
                + '2026-09-28T09:00:03.000001+00:00 host sudo: alex : unable to resolve host box\n'
                + '2026-09-28T09:00:04.000001+00:00 host sudo-rs: alex :  PWD=/ ; USER=root ; COMMAND=/usr/bin/true \n')
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
            with mock.patch.object(sudoCommands, 'logfunc') as log:
                headers, rows, source = sudoCommands.sudoCommands.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        last = str(4 + len(long_parts))
        auth_rows = [(datetime(2026, 9, 28, 9, 0, 1, 1, tzinfo=UTC), 'sudo', 'alex', '/usr/bin/id ', '2'),
                     (datetime(2026, 9, 28, 9, 0, 2, 0, tzinfo=UTC), 'sudo', 'alex', '/usr/bin/printf yyyy', f'3-{2 + len(long_parts)}'),
                     (datetime(2026, 9, 28, 9, 0, 4, 1, tzinfo=UTC), 'sudo-rs', 'alex', '/usr/bin/true ', last)]
        self.assertEqual([(r[0], r[3], r[4], r[10][:20], r[-2], r[-1]) for r in rows],
                         [row + (os.path.join('var', 'log', name),) for name in ('auth.log', 'secure') for row in auth_rows])
        self.assertEqual(rows[1][10], '/usr/bin/printf ' + 'y' * 1200)
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'sudo Commands: 1 files that could not be read, '
                                                '2 lines from other programs, not reported, '
                                                '1 lines in neither syslog file format, not reported, '
                                                '2 sudo messages with no COMMAND= field, not reported')


if __name__ == '__main__':
    unittest.main()
