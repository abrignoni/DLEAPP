"""Pin how the Linux package artifacts read apt's history.log and dpkg.log."""
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxPackages
# pylint: enable=wrong-import-position

HISTORY = (b'stray line before any transaction\n'
           b'Commandline: orphan\n'
           b'\n'
           b'Start-Date: 2026-08-31  14:47:35\n'
           b'Commandline: apt install openssh-server\n'
           b'Requested-By: parallels (1000)\n'
           b'Comment: a note\n'
           b'Install: openssh-server:arm64 (1:10.2p1-1), ncurses-term:arm64 (6.5-1, automatic)\n'
           b'Upgrade: libc6:arm64 (2.42-1, 2.43-1)\n'
           b'Remove: nano:arm64 (8.4-1)\n'
           b'Purge: vim-tiny:arm64 (2:9.1-1)\n'
           b'Disappeared: oldpkg, gonepkg (1.0)\n'
           b'Error: Sub-process /usr/bin/dpkg returned an error code (1)\n'
           b'End-Date: 2026-08-31  14:47:37\n'
           b'\n'
           b'Start-Date: 2026-09-01  09:00:00\n'
           b'Commandline: apt install broken\n'
           b'Install: broken (1.0, good:arm64 (2.0)\n'
           b'Reinstall: good:arm64 (2.0)\n'
           b'Downgrade: down:arm64 (3.0, 2.0)\n'
           b'\n'
           b'Start-Date: 2026-09-02  10:00:00\n'
           b'Commandline: apt update\n'
           b'End-Date: 2026-09-02  10:00:05\n')


class HistoryTest(unittest.TestCase):
    def rows(self, data=HISTORY):
        transactions, counts = linuxPackages.history_transactions(data)
        return [linuxPackages.history_rows(t, counts) for t in transactions], transactions, counts

    def test_each_package_entry_is_a_row_with_its_versions(self):
        rows, _transactions, _counts = self.rows()
        self.assertEqual(rows[0], [('Install', 'openssh-server:arm64', '', '1:10.2p1-1', ''),
                                   ('Install', 'ncurses-term:arm64', '', '6.5-1', 'yes'),
                                   ('Upgrade', 'libc6:arm64', '2.42-1', '2.43-1', ''),
                                   ('Remove', 'nano:arm64', '8.4-1', '', ''),
                                   ('Purge', 'vim-tiny:arm64', '2:9.1-1', '', ''),
                                   ('Disappeared', 'oldpkg', '', '', ''),
                                   ('Disappeared', 'gonepkg', '1.0', '', '')])

    def test_a_list_that_does_not_read_is_counted_and_the_rest_is_kept(self):
        rows, transactions, counts = self.rows()
        self.assertEqual(rows[1], [('Reinstall', 'good:arm64', '', '2.0', ''),
                                   ('Downgrade', 'down:arm64', '3.0', '2.0', '')])
        self.assertNotIn('End-Date', transactions[1])
        self.assertEqual(counts['Install lists that do not read as whole package entries, not reported'], 1)

    def test_lines_outside_a_transaction_are_counted(self):
        _rows, _transactions, counts = self.rows()
        self.assertEqual(counts['history lines that are not a tag and a value, not reported'], 1)
        self.assertEqual(counts['history lines before the first Start-Date, not reported'], 1)

    def test_a_repeated_tag_keeps_the_first(self):
        transactions, counts = linuxPackages.history_transactions(
            b'Start-Date: 2026-01-01  00:00:00\nCommandline: first\nCommandline: second\n')
        self.assertEqual(transactions[0]['Commandline'], 'first')
        self.assertEqual(counts['history tags repeated within one transaction, the first kept'], 1)

    def test_package_lists(self):
        self.assertEqual(linuxPackages.package_entries('a:arm64 (1.0), b (2.0, automatic)'),
                         [('a:arm64', '1.0'), ('b', '2.0, automatic')])
        self.assertEqual(linuxPackages.package_entries('x, y'), [('x', None), ('y', None)])
        self.assertIsNone(linuxPackages.package_entries('a (1.0) b (2.0)'))
        self.assertIsNone(linuxPackages.package_entries('a (1.0), , b (2.0)'))
        self.assertIsNone(linuxPackages.package_entries('a (1.0), )'))

    def test_text_that_is_not_utf8_shows_the_replacement_character(self):
        transactions, _counts = linuxPackages.history_transactions(b'Start-Date: 2026-01-01  00:00:00\nCommandline: caf\xe9\n')
        self.assertEqual(transactions[0]['Commandline'], 'caf\ufffd')

    def test_crlf_line_ends_are_not_part_of_a_value(self):
        transactions, _counts = linuxPackages.history_transactions(HISTORY.replace(b'\n', b'\r\n'))
        self.assertEqual(transactions[0]['End-Date'], '2026-08-31  14:47:37')


DPKG = (b'2026-08-31 14:47:36 startup archives unpack\n'
        b'2026-08-31 14:47:36 install openssh-server:arm64 <none> 1:10.2p1-1\n'
        b'2026-08-31 14:47:36 status half-installed openssh-server:arm64 1:10.2p1-1\n'
        b'2026-08-31 14:47:36 upgrade libc6:arm64 2.42-1 2.43-1\n'
        b'2026-08-31 14:47:37 configure openssh-server:arm64 1:10.2p1-1 <none>\n'
        b'2026-08-31 14:47:37 trigproc man-db:arm64 2.13-1 <none>\n'
        b'2026-08-31 14:47:37 conffile /etc/ssh/sshd_config keep\n'
        b'2026-08-31 14:47:37 remove nano:arm64 8.4-1 <none>\n'
        b'2026-08-31 14:47:37 purge vim-tiny:arm64 2:9.1-1 <none>\n'
        b'2026-08-31 14:47:37 disappear gone:arm64 1.0 <none>\n'
        b'2026-08-31 14:47:37 install toofew:arm64 1.0\n'
        b'not a log line\n')


class DpkgTest(unittest.TestCase):
    def test_action_lines_are_rows_and_the_rest_is_counted(self):
        counts = Counter()
        rows = linuxPackages.dpkg_rows(DPKG, counts)
        self.assertEqual(rows, [('2026-08-31 14:47:36', 'install', 'openssh-server:arm64', '<none>', '1:10.2p1-1'),
                                ('2026-08-31 14:47:36', 'upgrade', 'libc6:arm64', '2.42-1', '2.43-1'),
                                ('2026-08-31 14:47:37', 'remove', 'nano:arm64', '8.4-1', '<none>'),
                                ('2026-08-31 14:47:37', 'purge', 'vim-tiny:arm64', '2:9.1-1', '<none>'),
                                ('2026-08-31 14:47:37', 'disappear', 'gone:arm64', '1.0', '<none>')])
        self.assertEqual(counts, {'startup lines, not reported': 1, 'status lines, not reported': 1,
                                  'configure lines, not reported': 1, 'trigproc lines, not reported': 1,
                                  'conffile lines, not reported': 1,
                                  'install lines that are not a package and two versions, not reported': 1,
                                  'dpkg.log lines that do not begin with a date and time, not reported': 1})


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def write(root, relative, data):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open if path.endswith('.gz') else open)(path, 'wb') as handle:
        handle.write(data)
    return path


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, function, members):
        with tempfile.TemporaryDirectory() as root:
            files = [write(root, relative, data) for relative, data in members]
            with mock.patch.object(linuxPackages, 'logfunc') as log_lines:
                _headers, rows, source = function.__wrapped__(FakeContext(files, root))
            source = [os.path.relpath(path, root) for path in source.split('\n')] if source else []
        return rows, source, log_lines

    def test_apt_rows_carry_their_transaction_and_file(self):
        rotated = os.path.join('var', 'log', 'apt', 'history.log.1.gz')
        current = os.path.join('var', 'log', 'apt', 'history.log')
        rows, source, log = self.run_artifact(linuxPackages.aptHistory, [(rotated, HISTORY), (current, HISTORY)])
        self.assertEqual(rows[0], ('2026-08-31  14:47:35', '2026-08-31  14:47:37', 'Install', 'openssh-server:arm64',
                                   '', '1:10.2p1-1', '', 'parallels (1000)', 'apt install openssh-server', 'a note',
                                   'Sub-process /usr/bin/dpkg returned an error code (1)', current))
        self.assertEqual(rows[7][:2], ('2026-09-01  09:00:00', ''))
        self.assertEqual([row[-1] for row in rows], [current] * 9 + [rotated] * 9)
        self.assertEqual(source, [current, rotated])
        self.assertIn('2 transactions with no package entry, not reported', log.call_args.args[0])

    def test_dpkg_rows_carry_their_file(self):
        # Handed over out of order; the rows still come file by file in path order.
        rows, source, log = self.run_artifact(linuxPackages.dpkgLog, [('var/log/dpkg.log.2.gz', DPKG),
                                                                      ('var/log/dpkg.log', DPKG)])
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0][-1], os.path.join('var', 'log', 'dpkg.log'))
        self.assertEqual(source, [os.path.join('var', 'log', 'dpkg.log'), os.path.join('var', 'log', 'dpkg.log.2.gz')])
        self.assertIn('2 status lines, not reported', log.call_args.args[0])

    def test_a_cut_apt_rotation_is_counted_not_fatal(self):
        with tempfile.TemporaryDirectory() as root:
            path = write(root, 'var/log/apt/history.log.1.gz', HISTORY)
            with open(path, 'r+b') as handle:
                handle.truncate(os.path.getsize(path) // 2)
            with mock.patch.object(linuxPackages, 'logfunc') as log:
                _headers, rows, _source = linuxPackages.aptHistory.__wrapped__(FakeContext([path], root))
        self.assertEqual(rows, [])
        self.assertIn('1 history files that could not be read', log.call_args.args[0])

    def test_a_cut_gzip_rotation_is_counted_not_fatal(self):
        with tempfile.TemporaryDirectory() as root:
            path = write(root, 'var/log/dpkg.log.3.gz', DPKG)
            with open(path, 'r+b') as handle:
                handle.truncate(os.path.getsize(path) // 2)
            good = write(root, 'var/log/dpkg.log', DPKG)
            with mock.patch.object(linuxPackages, 'logfunc') as log:
                _headers, rows, _source = linuxPackages.dpkgLog.__wrapped__(FakeContext([path, good], root))
        self.assertEqual(len(rows), 5)
        self.assertIn('1 dpkg.log files that could not be read', log.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
