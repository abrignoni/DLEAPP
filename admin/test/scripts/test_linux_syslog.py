"""Pin how scripts/linux_syslog.py reads the lines of a Linux syslog file."""
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import linux_syslog
# pylint: enable=wrong-import-position

UTC = timezone.utc


class TimeTest(unittest.TestCase):
    def test_rfc3339_times_are_converted_with_their_own_offset(self):
        self.assertEqual(linux_syslog.utc_time('2026-09-28T02:45:33.123456-04:00'),
                         datetime(2026, 9, 28, 6, 45, 33, 123456, tzinfo=UTC))
        self.assertEqual(linux_syslog.utc_time('2026-01-10T09:00:00.5+04:00'),
                         datetime(2026, 1, 10, 5, 0, 0, 500000, tzinfo=UTC))
        self.assertEqual(linux_syslog.utc_time('2026-03-01T00:00:00Z'), datetime(2026, 3, 1, tzinfo=UTC))
        self.assertEqual(linux_syslog.utc_time('2026-09-28T00:10:00-00:30'), datetime(2026, 9, 28, 0, 40, tzinfo=UTC))

    def test_a_time_with_no_year_or_zone_is_not_converted(self):
        self.assertEqual(linux_syslog.utc_time('Feb  6 15:16:30'), '')


LOG = (b'2026-09-28T02:45:33.123456-04:00 ubuntu sshd-session[4021]: Accepted publickey for alex\n'
       b'2026-09-28T02:45:34.000001-04:00 ubuntu sudo:     alex : TTY=pts/0 ; COMMAND=/bin/true\n'
       b'Feb  6 15:16:32 victoria sshd[2085]: Failed password\n'
       b'\n'
       b'Feb  6 15:16:40 victoria last message repeated 2 times\n'
       b'2026-02-30T01:02:03Z ubuntu sshd: impossible date\n'
       b'2026-09-28T02:46:00Z ubuntu sshd: caf\xe9\r\n')


class ProgramLinesTest(unittest.TestCase):
    def test_lines_of_the_named_programs_and_counts_for_the_rest(self):
        counts = Counter()
        rows = linux_syslog.program_lines(LOG, ('sshd', 'sshd-session'), counts)
        self.assertEqual(rows, [
            (1, datetime(2026, 9, 28, 6, 45, 33, 123456, tzinfo=UTC), '2026-09-28T02:45:33.123456-04:00', 'ubuntu',
             'sshd-session', '4021', 'Accepted publickey for alex'),
            (3, '', 'Feb  6 15:16:32', 'victoria', 'sshd', '2085', 'Failed password'),
            (6, '', '2026-02-30T01:02:03Z', 'ubuntu', 'sshd', '', 'impossible date'),
            (7, datetime(2026, 9, 28, 2, 46, tzinfo=UTC), '2026-09-28T02:46:00Z', 'ubuntu', 'sshd', '', 'caf�')])
        self.assertEqual(counts, {linux_syslog.OTHER_PROGRAMS: 1, linux_syslog.NOT_SYSLOG: 1, linux_syslog.BAD_DATE: 1})

    def test_the_message_keeps_its_leading_spaces_after_the_separator(self):
        rows = linux_syslog.program_lines(LOG, ('sudo',), Counter())
        self.assertEqual(rows[0][-1], '    alex : TTY=pts/0 ; COMMAND=/bin/true')


class ReadFileTest(unittest.TestCase):
    def test_gzip_rotations_are_decompressed(self):
        with tempfile.TemporaryDirectory() as root:
            plain, packed = os.path.join(root, 'auth.log'), os.path.join(root, 'auth.log.2.gz')
            with open(plain, 'wb') as handle:
                handle.write(LOG)
            with open(packed, 'wb') as handle:
                handle.write(gzip.compress(LOG))
            self.assertEqual((linux_syslog.read_file(plain), linux_syslog.read_file(packed)), (LOG, LOG))


if __name__ == '__main__':
    unittest.main()
