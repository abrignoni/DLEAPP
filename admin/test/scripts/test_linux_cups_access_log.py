"""Pin the CUPS Access Log artifact (scripts/artifacts/linuxCupsAccessLog.py).

The lines have the layout CUPS 2.4.16 wrote on ubuntu2604_arm64_cups. The values are made up.
"""
import gzip
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
from scripts.artifacts import linuxCupsAccessLog as access
# pylint: enable=wrong-import-position

JOB = b'localhost - - [07/Oct/2026:21:37:52 -0400] "POST /printers/PDF HTTP/1.1" 200 271 Create-Job successful-ok'
ADMIN = (b'10.0.1.2 - known user [08/Oct/2026:01:02:03.000004 +0530] "POST /admin/ HTTP/1.1" 200 1954 '
         b'CUPS-Add-Modify-Printer successful-ok')
PAGE = b'localhost - - [08/Oct/2026:09:00:00 +0000] "GET /admin/conf/cupsd.conf HTTP/1.0" 401 0 - -'


def utc(*parts):
    return datetime(*parts, tzinfo=timezone.utc)


class RequestUtc(unittest.TestCase):
    def test_offsets_west_and_east(self):
        self.assertEqual(access.request_utc('07', 'Oct', '2026', '21', '37', '52', None, '-04', '00'),
                         utc(2026, 10, 8, 1, 37, 52))
        self.assertEqual(access.request_utc('08', 'Oct', '2026', '01', '02', '03', '000004', '+05', '30'),
                         utc(2026, 10, 7, 19, 32, 3, 4))

    def test_minutes_carry_their_own_sign_west_of_utc(self):
        self.assertEqual(access.request_utc('01', 'Jan', '2026', '00', '00', '00', None, '-03', '-30'),
                         utc(2026, 1, 1, 3, 30))
        self.assertEqual(access.request_utc('01', 'Jan', '2026', '00', '00', '00', None, '+00', '-30'),
                         utc(2026, 1, 1, 0, 30))

    def test_every_month_cups_writes(self):
        for number, month in enumerate(('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov',
                                        'Dec'), 1):
            self.assertEqual(access.request_utc('02', month, '2026', '03', '04', '05', None, '+00', '00'),
                             utc(2026, number, 2, 3, 4, 5))

    def test_not_a_time(self):
        self.assertEqual(access.request_utc('02', 'Okt', '2026', '03', '04', '05', None, '+00', '00'), '')
        self.assertEqual(access.request_utc('31', 'Feb', '2026', '03', '04', '05', None, '+00', '00'), '')
        self.assertEqual(access.request_utc('01', 'Jan', '0001', '00', '00', '00', None, '+05', '00'), '')


class AccessRows(unittest.TestCase):
    def test_rows(self):
        counts = Counter()
        rows = access.access_rows(b'\n'.join((JOB, ADMIN, b'', PAGE + b'\r', b'')), counts)
        self.assertEqual(rows, [
            (utc(2026, 10, 8, 1, 37, 52), '07/Oct/2026:21:37:52 -0400', 'localhost', '', 'POST', '/printers/PDF',
             '1.1', '200', '271', 'Create-Job', 'successful-ok', 1),
            (utc(2026, 10, 7, 19, 32, 3, 4), '08/Oct/2026:01:02:03.000004 +0530', '10.0.1.2', 'known user', 'POST',
             '/admin/', '1.1', '200', '1954', 'CUPS-Add-Modify-Printer', 'successful-ok', 2),
            (utc(2026, 10, 8, 9), '08/Oct/2026:09:00:00 +0000', 'localhost', '', 'GET', '/admin/conf/cupsd.conf',
             '1.0', '401', '0', '', '', 4)])
        self.assertEqual(counts, Counter())

    def test_a_line_with_signed_zone_minutes(self):
        counts = Counter()
        rows = access.access_rows(JOB.replace(b'21:37:52 -0400', b'21:37:52 -03-30'), counts)
        self.assertEqual([row[:2] for row in rows], [(utc(2026, 10, 8, 1, 7, 52), '07/Oct/2026:21:37:52 -03-30')])
        self.assertEqual(counts, Counter())

    def test_lines_in_no_form_are_counted(self):
        counts = Counter()
        rows = access.access_rows(b'not a request\n' + JOB + b' extra\n' + JOB[:-3] + b'\n \n' + JOB, counts)
        self.assertEqual([row[-1] for row in rows], [3, 5])
        self.assertEqual(counts, Counter({access.NOT_REQUEST: 2}))

    def test_a_time_that_is_no_time_keeps_its_row(self):
        counts = Counter()
        rows = access.access_rows(JOB.replace(b'07/Oct', b'31/Feb') + b'\n' + b'\xff' + JOB, counts)
        self.assertEqual([(row[0], row[1], row[2]) for row in rows],
                         [('', '31/Feb/2026:21:37:52 -0400', 'localhost'),
                          (utc(2026, 10, 8, 1, 37, 52), '07/Oct/2026:21:37:52 -0400', '\\xfflocalhost')])
        self.assertEqual(counts, Counter({access.NO_TIME: 1}))


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.logs = os.path.join(self.folder.name, 'var', 'log', 'cups')
        os.makedirs(self.logs)

    def write(self, name, data):
        path = os.path.join(self.logs, name)
        with (gzip.open if name.endswith('.gz') else open)(path, 'wb') as handle:
            handle.write(data)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(access, 'logfunc') as log:
            result = access.cupsAccessLog.__wrapped__(context)
        return result, [call.args[0] for call in log.call_args_list]

    def test_rotations_and_what_is_not_read(self):
        current = self.write('access_log', JOB + b'\n')
        older = self.write('access_log.2.gz', ADMIN + b'\nnoise\n')
        empty = self.write('access_log.1', b'')
        broken = os.path.join(self.logs, 'access_log.3.gz')
        with open(broken, 'wb') as handle:
            handle.write(b'not gzip')
        (headers, rows, located), logged = self.run_artifact([older, self.logs, broken, empty, current])
        self.assertEqual(len(headers), 13)
        self.assertEqual(headers[0], ('Time (UTC)', 'datetime'))
        self.assertEqual([(row[9], row[11], row[12]) for row in rows],
                         [('Create-Job', 1, os.path.join('var', 'log', 'cups', 'access_log')),
                          ('CUPS-Add-Modify-Printer', 1, os.path.join('var', 'log', 'cups', 'access_log.2.gz'))])
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(located, current + '\n' + older)
        self.assertEqual(logged, ['CUPS Access Log: 1 files that could not be read, 1 ' + access.NOT_REQUEST])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
