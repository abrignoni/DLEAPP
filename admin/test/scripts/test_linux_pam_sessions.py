"""Pin how the PAM Sessions artifact reads pam_unix's session lines in auth.log and secure."""
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
from scripts.artifacts import linuxPamSessions
# pylint: enable=wrong-import-position

UTC = timezone.utc


class FieldsTest(unittest.TestCase):
    def test_the_two_opened_forms_and_the_closed_form(self):
        cases = {
            'pam_unix(sshd:session): session opened for user alex(uid=1000) by alex(uid=0)':
                ('sshd', 'opened', 'alex', '1000', 'alex', '0'),
            'pam_unix(su:session): session opened for user bob(uid=1001) by (uid=1000)':
                ('su', 'opened', 'bob', '1001', '', '1000'),
            'pam_unix(login:session): session opened for user root by LOGIN(uid=0)':
                ('login', 'opened', 'root', '', 'LOGIN', '0'),
            'pam_unix(cron:session): session opened for user root by (uid=0)':
                ('cron', 'opened', 'root', '', '', '0'),
            'pam_unix(cron:session): session closed for user root': ('cron', 'closed', 'root', '', '', ''),
            'pam_unix(gdm-password:session): session opened for user alex(uid=getpwnam error) by alex(uid=0)':
                ('gdm-password', 'opened', 'alex', 'getpwnam error', 'alex', '0'),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxPamSessions.session_fields(message), expected)

    def test_other_messages_are_not_sessions(self):
        for message in ('pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=h',
                        'pam_systemd(sshd:session): New sd-bus connection (system-bus-pam-systemd-1) opened.',
                        'pam_unix(su:session): session opened for user bob',
                        'session opened for user bob(uid=1001) by alex(uid=1000)'):
            with self.subTest(message=message):
                self.assertIsNone(linuxPamSessions.session_fields(message))

    def test_lines_are_counted_by_kind(self):
        counts = Counter()
        rows = linuxPamSessions.session_rows(
            b'2026-09-28T05:00:00.000001-04:00 host su[9]: pam_unix(su:session): session opened for user bob(uid=1001) '
            b'by (uid=1000)\n'
            b'2026-09-28T05:00:01Z host su[9]: pam_unix(su:session): session opened for user bob\n'
            b'2026-09-28T05:00:02Z host sshd[3]: Accepted publickey for alex\n'
            b'not syslog\n'
            b'2026-02-30T05:00:03Z host sudo: pam_unix(sudo:session): session closed for user root\n', counts)
        self.assertEqual(rows, [
            (datetime(2026, 9, 28, 9, 0, 0, 1, tzinfo=UTC), '2026-09-28T05:00:00.000001-04:00', 'host', 'su', '9',
             'su', 'opened', 'bob', '1001', '', '1000', 1),
            ('', '2026-02-30T05:00:03Z', 'host', 'sudo', '', 'sudo', 'closed', 'root', '', '', '', 5)])
        self.assertEqual(counts, {'pam_unix session lines in no known form, not reported': 1,
                                  'lines that are not pam_unix session lines, not reported': 1,
                                  'lines in neither syslog file format, not reported': 1,
                                  'RFC 3339 times that are not a calendar date, Time (UTC) left blank': 1})


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
                '2026-09-28T09:00:01.000001+00:00 host sshd-session[4]: pam_unix(sshd:session): session opened for user '
                'alex(uid=1000) by alex(uid=0)\n'
                'Feb  6 15:16:32 box CRON[5]: pam_unix(cron:session): session closed for user root\n')
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
            with mock.patch.object(linuxPamSessions, 'logfunc') as log:
                headers, rows, source = linuxPamSessions.linuxPamSessions.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        per_file = [(datetime(2026, 9, 28, 9, 0, 1, 1, tzinfo=UTC), 'sshd-session', '4', 'sshd', 'opened', 'alex', '1000',
                     'alex', '0', 2),
                    ('', 'CRON', '5', 'cron', 'closed', 'root', '', '', '', 3)]
        self.assertEqual([(r[0], *r[3:12]) for r in rows],
                         [row for name in ('auth.log', 'secure') for row in per_file])
        self.assertEqual([r[12] for r in rows], [os.path.join('var', 'log', n) for n in ('auth.log', 'auth.log', 'secure', 'secure')])
        self.assertEqual(rows[1][1], 'Feb  6 15:16:32')
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'auth.log'), os.path.join(logs, 'secure')])
        self.assertEqual(log.call_args.args[0], 'PAM Sessions: 1 files that could not be read, '
                                                '1 lines in neither syslog file format, not reported, '
                                                '2 lines that are not pam_unix session lines, not reported')


if __name__ == '__main__':
    unittest.main()
