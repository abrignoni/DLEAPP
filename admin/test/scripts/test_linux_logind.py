"""Pin how the Login Sessions (logind) artifact reads systemd-logind's session lines in auth.log and secure."""
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


if __name__ == '__main__':
    unittest.main()
