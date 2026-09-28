"""Pin how the Cron Log artifact reads the lines Debian's cron and crontab write to syslog."""
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
from scripts.artifacts import linuxCron
# pylint: enable=wrong-import-position

UTC = timezone.utc


class FieldsTest(unittest.TestCase):
    def test_the_log_it_form(self):
        cases = {
            '(parallels) CMD (/usr/bin/true dleapp-known-cron-minute)':
                ('parallels', 'CMD', '/usr/bin/true dleapp-known-cron-minute'),
            '(parallels) CMD (/usr/bin/cat > /dev/null 100% done )': ('parallels', 'CMD', '/usr/bin/cat > /dev/null 100% done '),
            '(root) CMD ([ -x /usr/lib/x ] && (echo a) || true)': ('root', 'CMD', '[ -x /usr/lib/x ] && (echo a) || true'),
            '(parallels) BEGIN EDIT (parallels)': ('parallels', 'BEGIN EDIT', 'parallels'),
            '(CRON) info (No MTA installed, discarding output)': ('CRON', 'info', 'No MTA installed, discarding output'),
            '(*system*) RELOAD (/etc/crontab)': ('*system*', 'RELOAD', '/etc/crontab'),
            '(alice) INSECURE MODE (mode 0600 expected) (crontabs/alice)':
                ('alice', 'INSECURE MODE (mode 0600 expected)', 'crontabs/alice'),
            '(bob) INSECURE MODE (group/other writable) (/etc/cron.d/x)':
                ('bob', 'INSECURE MODE (group/other writable)', '/etc/cron.d/x'),
            '() CMD (x)': ('', 'CMD', 'x'),
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(linuxCron.cron_fields(message), expected)

    def test_other_messages(self):
        for message in ('pam_unix(cron:session): session opened for user root(uid=0) by root(uid=0)',
                        '(CRON) INFO', '(root) CMD (x) trailing', "Job `cron.daily' started", 'CMD (x)',
                        '(ro(ot) CMD (x)', '(root) C(M)D (x)'):
            with self.subTest(message=message):
                self.assertIsNone(linuxCron.cron_fields(message))


class RowsTest(unittest.TestCase):
    def test_programs_forms_and_counts(self):
        counts = Counter()
        rows = linuxCron.cron_rows(
            b'2026-09-28T13:09:01.695784-04:00 host CRON[336917]: (parallels) CMD (/usr/bin/true a)\n'
            b'2026-09-28T13:09:01.686052-04:00 host CRON[336911]: pam_unix(cron:session): session opened for user '
            b'parallels(uid=1000) by parallels(uid=0)\n'
            b'2026-09-28T13:15:01.814046-04:00 host cron[1032]: (parallels) RELOAD (crontabs/parallels)\n'
            b'2026-09-28T13:15:20.577665-04:00 host crontab[338133]: (parallels) DELETE (parallels)\n'
            b'Mar 10 06:25:01 box /USR/SBIN/CRON[2436]: (root) CMD (test -x /usr/sbin/anacron)\n'
            b'Mar 10 06:20:17 box /usr/sbin/cron[2255]: (CRON) STARTUP (fork ok)\n'
            b"2026-09-28T13:30:01.000001-04:00 host anacron[5]: Job `cron.daily' started\n"
            b'2026-09-28T13:30:01.000001-04:00 host crond[6]: (root) CMD (x)\n'
            b'not syslog\n', counts)
        self.assertEqual(rows, [
            (datetime(2026, 9, 28, 17, 9, 1, 695784, tzinfo=UTC), '2026-09-28T13:09:01.695784-04:00', 'host', 'CRON',
             '336917', 'parallels', 'CMD', '/usr/bin/true a', 1),
            (datetime(2026, 9, 28, 17, 15, 1, 814046, tzinfo=UTC), '2026-09-28T13:15:01.814046-04:00', 'host', 'cron',
             '1032', 'parallels', 'RELOAD', 'crontabs/parallels', 3),
            (datetime(2026, 9, 28, 17, 15, 20, 577665, tzinfo=UTC), '2026-09-28T13:15:20.577665-04:00', 'host', 'crontab',
             '338133', 'parallels', 'DELETE', 'parallels', 4),
            ('', 'Mar 10 06:25:01', 'box', '/USR/SBIN/CRON', '2436', 'root', 'CMD', 'test -x /usr/sbin/anacron', 5),
            ('', 'Mar 10 06:20:17', 'box', '/usr/sbin/cron', '2255', 'CRON', 'STARTUP', 'fork ok', 6)])
        self.assertEqual(counts, {'cron and crontab lines in other forms, not reported': 1,
                                  'lines from other programs, not reported': 2,
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
        text = ('2026-09-28T09:00:00.000001+00:00 host systemd[1]: Started x.\n'
                '2026-09-28T09:01:01.000001+00:00 host CRON[77]: (alex) CMD (/usr/bin/true)\n')
        with tempfile.TemporaryDirectory() as root:
            logs = os.path.join(root, 'var', 'log')
            os.makedirs(logs)
            files = []
            for name, data in (('syslog.1', text.encode()), ('syslog', text.encode()), ('cron.log', b'not syslog\n'),
                               ('syslog.2.gz', b'\x1f\x8b\x08\x00broken'), ('syslog.3.gz', b'not gzip\n')):
                path = os.path.join(logs, name)
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            files.append(logs)
            with mock.patch.object(linuxCron, 'logfunc') as log:
                headers, rows, source = linuxCron.linuxCronLog.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([(r[0], r[3], r[4], r[5], r[6], r[7], r[8], r[9]) for r in rows],
                         [(datetime(2026, 9, 28, 9, 1, 1, 1, tzinfo=UTC), 'CRON', '77', 'alex', 'CMD', '/usr/bin/true', 2,
                           os.path.join('var', 'log', name)) for name in ('syslog', 'syslog.1')])
        self.assertEqual(source.split('\n'), [os.path.join(logs, 'syslog'), os.path.join(logs, 'syslog.1')])
        self.assertEqual(log.call_args.args[0], 'Cron Log: 2 files that could not be read, '
                                                '2 lines from other programs, not reported, '
                                                '1 lines in neither syslog file format, not reported')


    def test_nothing_logged_when_every_line_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'syslog')
            with open(path, 'wb') as handle:
                handle.write(b'2026-09-28T09:01:01.000001+00:00 host CRON[77]: (alex) CMD (/usr/bin/true)\n')
            with mock.patch.object(linuxCron, 'logfunc') as log:
                _headers, rows, source = linuxCron.linuxCronLog.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


if __name__ == '__main__':
    unittest.main()
