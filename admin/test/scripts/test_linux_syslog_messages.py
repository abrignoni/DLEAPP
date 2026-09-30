"""Pin how the Syslog Messages artifact reads syslog files. Every file here is constructed for the test."""
import fnmatch
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxSyslog as ls
# pylint: enable=wrong-import-position

SYSLOG = (b'2026-09-29T20:07:47.123456-04:00 host1 CRON[1234]: (root) CMD (true)\n'
          b'\n'
          b'2026-09-29T20:07:48+00:00 host1 kernel: usb 1-1: new device\n'
          b'not a syslog line at all\n'
          b'2026-02-30T01:02:03Z host1 app[9]: bad date\n')
MESSAGES = b'Sep 29 20:07:47 host2 sshd[77]: Accepted publickey\r\nSep  1 01:02:03 host2 systemd: Started x\n'


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class SyslogMessagesTest(unittest.TestCase):
    def test_paths(self):
        patterns = ls.__artifacts_v2__['linuxSyslogMessages']['paths']
        for member in ('var/log/syslog', 'var/log/syslog.1', 'var/log/syslog.2.gz', 'var/log/messages',
                       'var/log/messages-20260927', 'var/log/kern.log.3.gz', 'var/log/daemon.log', 'var/log/user.log.1',
                       'var/log/debug', 'var/log/debug.1'):
            self.assertEqual(sum(fnmatch.fnmatch('x/' + member, p) for p in patterns), 1, member)
        for member in ('var/log/auth.log', 'var/log/secure', 'var/log/cron', 'var/log/mail.log', 'var/log/syslogd.conf',
                       'var/log/installer/syslog.x', 'var/log/messages.bak', 'var/log/debugfs/x'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in patterns), member)

    def test_rows_times_and_counts(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            syslog = write('var/log/syslog', SYSLOG)
            rotated = write('var/log/syslog.2.gz', gzip.compress(b'2026-09-28T00:00:00Z host1 app: old line\n'))
            messages = write('var/log/messages', MESSAGES)
            broken = write('var/log/kern.log.1.gz', b'not gzip')
            empty = write('var/log/daemon.log', b'')
            paths = [messages, rotated, syslog, broken, empty, os.path.join(root, 'var', 'log')]
            with mock.patch.object(ls, 'logfunc') as log:
                headers, rows, source = ls.linuxSyslogMessages.__wrapped__(FakeContext(paths, root))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(names, ['Time (UTC)', 'Time as Recorded', 'Hostname', 'Program', 'Process ID', 'Message',
                                 'Line', 'Source File'])
        self.assertEqual([r[-1] for r in rows], ['var/log/messages'] * 2 + ['var/log/syslog'] * 3
                         + ['var/log/syslog.2.gz'])
        self.assertEqual(rows[0], ('', 'Sep 29 20:07:47', 'host2', 'sshd', '77', 'Accepted publickey', 1,
                                   'var/log/messages'))
        self.assertEqual(rows[1][3:6], ('systemd', '', 'Started x'))
        self.assertEqual(rows[2][0], datetime(2026, 9, 30, 0, 7, 47, 123456, timezone.utc))
        self.assertEqual((rows[2][3], rows[2][4], rows[2][6]), ('CRON', '1234', 1))
        self.assertEqual((rows[3][3], rows[3][4], rows[3][5], rows[3][6]), ('kernel', '', 'usb 1-1: new device', 3))
        self.assertEqual((rows[4][0], rows[4][1], rows[4][6]), ('', '2026-02-30T01:02:03Z', 5))
        self.assertEqual(rows[5][0], datetime(2026, 9, 28, tzinfo=timezone.utc))
        self.assertEqual(source.split('\n'), [empty, messages, syslog, rotated])
        log.assert_called_once_with('Syslog Messages: 1 RFC 3339 times that are not a calendar date, Time (UTC) left '
                                    'blank, 1 files that could not be read, 1 lines in neither syslog file format, '
                                    'not reported')


if __name__ == '__main__':
    unittest.main()
