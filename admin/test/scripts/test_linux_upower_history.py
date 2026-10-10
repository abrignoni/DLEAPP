"""Pin the UPower Power Source History artifact (scripts/artifacts/linuxUpowerHistory.py).

RATE is in the form UPower 1.91.1 wrote on the lab VM for ubuntu2604_arm64_upower: a time, a value with three
decimals and a state, separated by tabs. The values were made for the test.
"""
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
from scripts.artifacts import linuxUpowerHistory as up
# pylint: enable=wrong-import-position

RATE = b'1790764844\t0.000\tunknown\n1790765000\t21.619\tcharging\n1790766000\t0.000\tfully-charged\n'
T0 = datetime(2026, 9, 30, 10, 40, 44, tzinfo=timezone.utc)


def rows(data, counts=None):
    return up.history_rows(data, Counter() if counts is None else counts)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class FileName(unittest.TestCase):
    def test_the_five_kinds(self):
        self.assertEqual(up.file_kind('history-rate-bq40z651-100.dat'), ('Rate', 'W', 'bq40z651-100'))
        self.assertEqual(up.file_kind('history-charge-bq40z651-100.dat'), ('Charge', '%', 'bq40z651-100'))
        self.assertEqual(up.file_kind('history-voltage-generic_id.dat'), ('Voltage', 'V', 'generic_id'))
        self.assertEqual(up.file_kind('history-time-full-a-b-c.dat'), ('Time to full', 's', 'a-b-c'))
        self.assertEqual(up.file_kind('history-time-empty-x.dat'), ('Time to empty', 's', 'x'))

    def test_an_id_that_starts_like_a_kind_stays_in_the_id(self):
        self.assertEqual(up.file_kind('history-rate-time-full-1.dat'), ('Rate', 'W', 'time-full-1'))

    def test_other_names(self):
        for name in ('history-rate-.dat', 'history-rate.dat', 'history-time-x.dat', 'history-speed-x.dat',
                     'rate-x.dat', 'history-rate-x.txt', 'History-rate-x.dat', 'history-.dat', ''):
            self.assertIsNone(up.file_kind(name), name)


class Lines(unittest.TestCase):
    def test_file_order_and_fields(self):
        self.assertEqual(rows(RATE), [(T0, 0.0, 'unknown', 1),
                                      (datetime(2026, 9, 30, 10, 43, 20, tzinfo=timezone.utc), 21.619, 'charging', 2),
                                      (datetime(2026, 9, 30, 11, 0, tzinfo=timezone.utc), 0.0, 'fully-charged', 3)])

    def test_a_last_line_without_a_newline_is_read(self):
        self.assertEqual(rows(RATE[:-1]), rows(RATE))

    def test_empty_lines_keep_the_numbering(self):
        self.assertEqual([r[3] for r in rows(b'\n' + RATE.replace(b'\n', b'\n\n'))], [2, 4, 6])

    def test_lines_that_are_not_three_fields(self):
        counts = Counter()
        data = b'1790764844\t1.000\n1790764844\t1.000\tcharging\textra\n1790764844 1.000 charging\n' + RATE
        self.assertEqual([r[3] for r in rows(data, counts)], [4, 5, 6])
        self.assertEqual(counts, {'lines that are not a time, a value and a state, not reported': 3})

    def test_a_time_that_is_not_a_whole_number(self):
        counts = Counter()
        self.assertEqual(rows(b'17907.5\t1.000\tcharging\nsoon\t1.000\tcharging\n\t1.000\tcharging\n', counts), [])
        self.assertEqual(sum(counts.values()), 3)

    def test_a_time_no_date_can_hold(self):
        counts = Counter()
        self.assertEqual(rows(b'99999999999999999\t1.000\tcharging\n', counts), [('', 1.0, 'charging', 1)])
        self.assertEqual(counts, {'times outside the range of a date, left blank': 1})

    def test_a_negative_time_is_before_1970(self):
        self.assertEqual(rows(b'-60\t1.000\tcharging\n')[0][0], datetime(1969, 12, 31, 23, 59, tzinfo=timezone.utc))

    def test_values(self):
        got = rows(b'1\t3,727\tcharging\n1\t-2.500\tcharging\n1\t12\tcharging\n1\tnan\tcharging\n1\t\tcharging\n')
        self.assertEqual([r[1] for r in got], ['3,727', -2.5, 12.0, 'nan', ''])

    def test_a_state_is_as_stored(self):
        self.assertEqual([r[2] for r in rows(b'1\t0.000\tpending-charge\n1\t0.000\tSomething else\n1\t0.000\t\n')],
                         ['pending-charge', 'Something else', ''])

    def test_bytes_that_are_not_utf8(self):
        self.assertEqual(rows(b'1\t0.000\tch\xffrging\n')[0][2], 'ch\\xffrging')

    def test_only_a_line_feed_ends_a_line(self):
        got = rows(b'1\t0.000\tcharging\r\n2\t0.000\tdis\x0ccharging\n')
        self.assertEqual([(r[2], r[3]) for r in got], [('charging\r', 1), ('dis\x0ccharging', 2)])

    def test_an_empty_file(self):
        self.assertEqual(rows(b''), [])


class Processor(unittest.TestCase):
    def run_on(self, files):
        with tempfile.TemporaryDirectory() as root:
            paths = []
            for name, data in files.items():
                path = os.path.join(root, 'var', 'lib', 'upower', name)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                paths.append(path)
            paths.append(os.path.join(root, 'var', 'lib', 'upower', 'history-rate-gone.dat'))
            paths.append(os.path.join(root, 'var', 'lib', 'upower'))
            with mock.patch.object(up, 'logfunc') as log:
                headers, data, located = up.linuxUpowerHistory.__wrapped__(FakeContext(paths, root))
            return headers, data, [os.path.relpath(p, root) for p in located.split('\n') if p], log

    def test_rows_of_two_files(self):
        headers, data, located, log = self.run_on({
            'history-voltage-bq40z651-100.dat': b'1790764844\t12.584\tdischarging\n',
            'history-rate-bq40z651-100.dat': RATE,
            'history-charge-empty-one.dat': b'',
            'history-notes.dat': RATE})
        self.assertEqual(headers, (('Timestamp (UTC)', 'datetime'), 'Reading', 'Value', 'Unit', 'State', 'Device ID',
                                   'Line'))
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0], (T0, 'Rate', 0.0, 'W', 'unknown', 'bq40z651-100', 1))
        self.assertEqual(data[3], (T0, 'Voltage', 12.584, 'V', 'discharging', 'bq40z651-100', 1))
        self.assertEqual(located, [os.path.join('var', 'lib', 'upower', 'history-rate-bq40z651-100.dat'),
                                   os.path.join('var', 'lib', 'upower', 'history-voltage-bq40z651-100.dat')])
        message = log.call_args[0][0]
        self.assertIn('1 files not named for one of the five readings, not read', message)
        self.assertIn('1 files that could not be read', message)

    def test_nothing_found(self):
        with mock.patch.object(up, 'logfunc') as log:
            self.assertEqual(up.linuxUpowerHistory.__wrapped__(FakeContext([], '/'))[1:], ([], ''))
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
