"""Pin how the Cron Log artifacts read the lines Debian's cron and crontab write to syslog and the systemd
journal. The journal files are written with journal_writer.py."""
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


BOOT_1 = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')
BOOT_2 = bytes.fromhex('00112233445566778899aabbccddeeff')
T0 = 1790000000


def journal_bytes(entries, boot=BOOT_1):
    """A journal file of (realtime seconds, monotonic seconds, [(field, value)], boot or None[, sequence number])
    entries."""
    writer = jw.JournalWriter(boot_id=boot)
    for realtime, monotonic, fields, entry_boot, *seqnum in entries:
        writer.add_entry([(name, value.encode()) for name, value in fields], int(realtime * 1000000),
                         int(monotonic * 1000000), seqnum=seqnum[0] if seqnum else None, boot_id=entry_boot)
    return writer.bytes()


def journal(entries, boot=BOOT_1):
    return systemd_journal.JournalFile(journal_bytes(entries, boot))


def syslog_entry(ident, message, pid='77', host='vm'):
    fields = [('_TRANSPORT', 'syslog'), ('SYSLOG_FACILITY', '9')]
    if ident is not None:
        fields.append(('SYSLOG_IDENTIFIER', ident))
    if pid is not None:
        fields.append(('SYSLOG_PID', pid))
    if host is not None:
        fields.append(('_HOSTNAME', host))
    return fields + [('MESSAGE', message)]


class JournalRowsTest(unittest.TestCase):
    def test_programs_forms_and_counts(self):
        t = T0
        entries = [
            (t + 3, 3, syslog_entry('CRON', '(alex) CMD (/usr/bin/true a)', pid='90'), None),
            (t + 1, 1, syslog_entry('cron', '(CRON) INFO (Running @reboot jobs)', pid='12'), None),
            (t + 2, 2, syslog_entry('CRON', 'pam_unix(cron:session): session opened for user alex(uid=1000) by '
                                    'alex(uid=0)', pid='90'), None),
            (t + 4, 4, syslog_entry('crontab', '(alex) LIST (alex)', pid='5', host=None), None),
            (t + 5, 5, syslog_entry('/USR/SBIN/CRON', '(root) CMD (x)', pid=None), None),
            (t + 6, 6, syslog_entry('anacron', "Job `cron.daily' started"), None),
            (t + 7, 7, syslog_entry('crond', '(root) CMD (x)'), None),
            (t + 8, 8, [('_TRANSPORT', 'kernel'), ('MESSAGE', '(root) CMD (x)')], None),
            (t + 9, 9, syslog_entry(None, '(root) CMD (x)'), None),
        ]
        counts = Counter()
        rows = linuxCron.journal_cron_rows([('var/log/journal/m/system.journal', journal(entries))], counts)
        at = lambda s: datetime.fromtimestamp(t + s, UTC)
        self.assertEqual(rows, [
            (at(1), 'vm', 'cron', '12', 'CRON', 'INFO', 'Running @reboot jobs', BOOT_1.hex(),
             'var/log/journal/m/system.journal'),
            (at(3), 'vm', 'CRON', '90', 'alex', 'CMD', '/usr/bin/true a', BOOT_1.hex(), 'var/log/journal/m/system.journal'),
            (at(4), '', 'crontab', '5', 'alex', 'LIST', 'alex', BOOT_1.hex(), 'var/log/journal/m/system.journal'),
            (at(5), 'vm', '/USR/SBIN/CRON', '', 'root', 'CMD', 'x', BOOT_1.hex(), 'var/log/journal/m/system.journal')])
        self.assertEqual(counts, {linux_syslog.JOURNAL_OTHER: 4, linuxCron.JOURNAL_OTHER_FORM: 1})

    def test_the_first_value_of_a_repeated_field_is_read(self):
        entry = [('_TRANSPORT', 'syslog'), ('SYSLOG_IDENTIFIER', 'CRON'), ('SYSLOG_IDENTIFIER', 'systemd'),
                 ('MESSAGE', '(alex) CMD (first)'), ('MESSAGE', '(bob) CMD (second)'),
                 ('SYSLOG_PID', '7'), ('SYSLOG_PID', '8'), ('_HOSTNAME', 'one'), ('_HOSTNAME', 'two')]
        rows = linuxCron.journal_cron_rows([('a', journal([(T0, 1, entry, None)]))], Counter())
        self.assertEqual([r[1:7] for r in rows], [('one', 'CRON', '7', 'alex', 'CMD', 'first')])

    def test_order_across_files_and_boots_and_an_entry_in_two_files(self):
        t = T0
        # the same entry in two files keeps its sequence number
        shared = (t + 5, 5, syslog_entry('CRON', '(alex) CMD (shared)'), BOOT_1, 50)
        first = journal([(t + 9, 9, syslog_entry('CRON', '(alex) CMD (late)'), BOOT_1), shared])
        # the same time, time since boot and message in another boot is another entry
        second = journal([shared, (t + 5, 6, syslog_entry('CRON', '(alex) CMD (other boot)'), BOOT_2),
                          (t + 5, 5, syslog_entry('CRON', '(alex) CMD (shared)'), BOOT_2),
                          (t + 5, 4, syslog_entry('CRON', '(alex) CMD (same boot, earlier)'), BOOT_1)])
        counts = Counter()
        rows = linuxCron.journal_cron_rows([('a.journal', first), ('b.journal', second)], counts)
        self.assertEqual([(r[6], r[7], r[8]) for r in rows], [
            ('shared', BOOT_2.hex(), 'b.journal'),
            ('other boot', BOOT_2.hex(), 'b.journal'),
            ('same boot, earlier', BOOT_1.hex(), 'b.journal'),
            ('shared', BOOT_1.hex(), 'a.journal'),
            ('late', BOOT_1.hex(), 'a.journal')])
        self.assertEqual(counts, {linux_syslog.JOURNAL_REPEATED: 1})

    def test_two_entries_of_one_file_with_the_same_time_and_message_are_both_read(self):
        writer = jw.JournalWriter(boot_id=BOOT_1)
        for seqnum in (7, 8):
            writer.add_entry([(n, v.encode()) for n, v in syslog_entry('CRON', '(a) CMD (twice)')], T0 * 1000000, 1000000,
                             seqnum=seqnum)
        counts = Counter()
        rows = linuxCron.journal_cron_rows([('a', systemd_journal.JournalFile(writer.bytes()))], counts)
        self.assertEqual(([r[6] for r in rows], counts), (['twice', 'twice'], Counter()))

    def test_equal_time_boot_and_monotonic_keep_sequence_order(self):
        writer = jw.JournalWriter(boot_id=BOOT_1)
        for seqnum, detail in ((9, 'nine'), (3, 'three')):
            writer.add_entry([(n, v.encode()) for n, v in syslog_entry('CRON', f'(a) CMD ({detail})')],
                             T0 * 1000000, 1000000, seqnum=seqnum)
        rows = linuxCron.journal_cron_rows([('a', systemd_journal.JournalFile(writer.bytes()))], Counter())
        self.assertEqual([r[6] for r in rows], ['three', 'nine'])

    def test_times_that_cannot_be_shown_are_blank(self):
        self.assertEqual(linux_syslog.journal_time(0), '')
        self.assertEqual(linux_syslog.journal_time(253402300800000000), '')
        self.assertEqual(linux_syslog.journal_time(253402300799999999), datetime(9999, 12, 31, 23, 59, 59, 999999, UTC))
        self.assertEqual(linux_syslog.journal_time(1), datetime(1970, 1, 1, 0, 0, 0, 1, UTC))

    def test_a_file_with_an_unknown_incompatible_flag_is_not_read(self):
        data = bytearray(journal_bytes([(T0, 1, syslog_entry('CRON', '(a) CMD (x)'), None)]))
        data[12] |= 0x40
        counts = Counter()
        rows = linuxCron.journal_cron_rows([('a', systemd_journal.JournalFile(bytes(data)))], counts)
        self.assertEqual((rows, dict(counts)),
                         ([], {'journal files not read: their incompatible flags are unknown to the reader': 1}))


class JournalArtifactTest(unittest.TestCase):
    def test_rows_name_their_file_and_unreadable_files_are_counted(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'var', 'log', 'journal', 'm')
            os.makedirs(folder)
            files = []
            for name, data in (
                    ('system.journal', journal_bytes([(T0 + 2, 2, syslog_entry('CRON', '(alex) CMD (b)'), None)])),
                    ('system@x.journal~', journal_bytes([(T0 + 1, 1, syslog_entry('CRON', '(alex) CMD (a)'), None),
                                                          (T0 + 3, 3, syslog_entry('sshd', 'x'), None)])),
                    ('user-1000.journal', journal_bytes([(T0, 1, syslog_entry('sshd', 'x'), None)])),
                    ('broken.journal', b'not a journal')):
                path = os.path.join(folder, name)
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            files.append(folder)
            with mock.patch.object(linuxCron, 'logfunc') as log:
                headers, rows, source = linuxCron.linuxCronJournal.__wrapped__(FakeContext(files, root))
        self.assertEqual(headers, (('Time (UTC)', 'datetime'), 'Hostname', 'Program', 'Process ID', 'User', 'Event',
                                   'Detail', 'Boot ID', 'Source File'))
        rel = os.path.join('var', 'log', 'journal', 'm')
        self.assertEqual([(r[6], r[8]) for r in rows], [('a', os.path.join(rel, 'system@x.journal~')),
                                                        ('b', os.path.join(rel, 'system.journal'))])
        self.assertEqual(source.split('\n'), [os.path.join(folder, 'system@x.journal~'),
                                              os.path.join(folder, 'system.journal')])
        self.assertEqual(log.call_args.args[0], 'Cron Log (journal): 2 entries of other programs, '
                                                '1 journal files not read (JournalError)')

    def test_nothing_logged_when_every_entry_is_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'system.journal')
            with open(path, 'wb') as handle:
                handle.write(journal_bytes([(T0, 1, syslog_entry('CRON', '(alex) CMD (b)'), None)]))
            with mock.patch.object(linuxCron, 'logfunc') as log:
                _headers, rows, source = linuxCron.linuxCronJournal.__wrapped__(FakeContext([path], root))
        self.assertEqual((len(rows), source, log.called), (1, path, False))


if __name__ == '__main__':
    unittest.main()
