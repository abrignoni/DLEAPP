"""Pin the Screen Time History (GNOME Shell) artifact (scripts/artifacts/linuxGnomeScreenTime.py).

KNOWN is the first four entries of the history on ubuntu2604_arm64_screentime, byte for byte as GNOME Shell 50.1
wrote them (JSON.stringify, no spaces). The rejection cases follow the loader in js/misc/timeLimitsManager.js at
50.1, lines 645 to 672.
"""
import json
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
from scripts.artifacts import linuxGnomeScreenTime as st
# pylint: enable=wrong-import-position

KNOWN = (b'[{"oldState":0,"newState":1,"wallTimeSecs":1789574007},{"oldState":1,"newState":0,"wallTimeSecs":1789574348},'
         b'{"oldState":0,"newState":1,"wallTimeSecs":1789574912},{"oldState":1,"newState":0,"wallTimeSecs":1789575220}]')


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def rows(data):
    counts = Counter()
    return st.history_rows(data, counts), counts


class HistoryRows(unittest.TestCase):
    def test_known_entries(self):
        got, counts = rows(KNOWN)
        self.assertEqual(got, [
            (utc(1789574007), 'Inactive', 'Active', 341),
            (utc(1789574348), 'Active', 'Inactive', 564),
            (utc(1789574912), 'Inactive', 'Active', 308),
            (utc(1789575220), 'Active', 'Inactive', ''),
        ])
        self.assertEqual(counts, Counter())
        self.assertEqual(utc(1789574007).isoformat(), '2026-09-16T15:53:27+00:00')

    def test_file_order_is_kept(self):
        data = json.dumps([{'oldState': 1, 'newState': 0, 'wallTimeSecs': 200},
                           {'oldState': 0, 'newState': 1, 'wallTimeSecs': 100}]).encode()
        got, counts = rows(data)
        self.assertEqual([r[0] for r in got], [utc(200), utc(100)])
        self.assertEqual(got[0][3], -100)
        self.assertEqual(counts['files with an entry that fails the checks GNOME Shell 50.1 applies when loading, reported as stored'], 1)

    def test_whole_float_time_and_state(self):
        got, counts = rows(b'[{"oldState":0.0,"newState":1.0,"wallTimeSecs":1789574007.0}]')
        self.assertEqual(got, [(utc(1789574007), 'Inactive', 'Active', '')])
        self.assertEqual(counts, Counter())

    def test_values_outside_the_format(self):
        data = json.dumps([
            {'oldState': 2, 'newState': True, 'wallTimeSecs': 1.5},
            {'oldState': '1', 'newState': None, 'wallTimeSecs': 'x'},
            {'oldState': 1, 'newState': 0, 'wallTimeSecs': 2 ** 53},
            {'oldState': 1, 'newState': 0, 'wallTimeSecs': True},
            {'newState': 1},
        ]).encode()
        got, counts = rows(data)
        self.assertEqual([r[1:3] for r in got], [('Unknown (2)', 'Unknown (true)'), ('Unknown ("1")', 'Unknown (null)'),
                                                 ('Active', 'Inactive'), ('Active', 'Inactive'),
                                                 ('', 'Active')])
        self.assertEqual([r[0] for r in got], [''] * 5)
        self.assertEqual([r[3] for r in got], [''] * 5)
        self.assertEqual(counts['times that are not a whole number of seconds in range, left blank'], 5)
        self.assertEqual(counts['files with an entry that fails the checks GNOME Shell 50.1 applies when loading, reported as stored'], 1)

    def test_entries_that_are_not_objects(self):
        got, counts = rows(b'[1, {"oldState":0,"newState":1,"wallTimeSecs":10}, [], null]')
        self.assertEqual(got, [(utc(10), 'Inactive', 'Active', '')])
        self.assertEqual(counts['entries that are not JSON objects, not reported'], 3)
        self.assertEqual(counts['files with an entry that fails the checks GNOME Shell 50.1 applies when loading, reported as stored'], 1)

    def test_not_an_array(self):
        for data in (b'{"oldState":0}', b'not json', b'\xff\xfe', b'NaN', b'[NaN]', b''):
            got, _ = rows(data)
            self.assertIsNone(got, data)

    def test_empty_array(self):
        self.assertEqual(rows(b'[]'), ([], Counter()))


class FirstRejected(unittest.TestCase):
    def check(self, history, expected):
        self.assertEqual(st.first_rejected(history), expected, history)

    def test_accepts_the_known_history(self):
        self.check(json.loads(KNOWN), None)

    def test_each_loader_check(self):
        good = {'oldState': 0, 'newState': 1, 'wallTimeSecs': 100}
        self.check([good, dict(good, oldState=1, newState=0, wallTimeSecs=100)], None)
        self.check([good, 'x'], 1)
        self.check([good, None], 1)
        for member in ('oldState', 'newState', 'wallTimeSecs'):
            entry = dict(good)
            del entry[member]
            self.check([entry], 0)
        self.check([dict(good, oldState=2)], 0)
        self.check([dict(good, newState='1')], 0)
        self.check([dict(good, oldState=True)], 0)
        self.check([dict(good, newState=0)], 0)
        self.check([dict(good, wallTimeSecs='100')], 0)
        self.check([dict(good, wallTimeSecs=100.5)], 0)
        self.check([dict(good, wallTimeSecs=2 ** 53)], 0)
        self.check([dict(good, wallTimeSecs=2 ** 53 - 1)], None)
        self.check([good, dict(good, oldState=1, newState=0, wallTimeSecs=99)], 1)


class ArtifactRun(unittest.TestCase):
    def test_rows_source_file_and_located_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, 'home', 'u', '.local', 'share', 'gnome-shell')
            os.makedirs(folder)
            good = os.path.join(folder, 'session-active-history.json')
            with open(good, 'wb') as handle:
                handle.write(KNOWN)
            other = os.path.join(tmp, 'home', 'v', '.local', 'share', 'gnome-shell')
            os.makedirs(other)
            bad = os.path.join(other, 'session-active-history.json')
            with open(bad, 'wb') as handle:
                handle.write(b'{}')
            empty = os.path.join(tmp, 'home', 'w', 'session-active-history.json')
            os.makedirs(os.path.dirname(empty))
            with open(empty, 'wb') as handle:
                handle.write(b'[]')
            context = mock.Mock()
            context.get_files_found.return_value = [bad, good, empty, folder]
            context.get_relative_path.side_effect = lambda p: os.path.relpath(p, tmp)
            logged = []
            with mock.patch.object(st, 'logfunc', logged.append):
                headers, data, located = st.linuxGnomeScreenTimeHistory.__wrapped__(context)
        self.assertEqual(headers[0], ('Time', 'datetime'))
        self.assertEqual(len(data), 4)
        self.assertEqual({r[-1] for r in data}, {os.path.join('home', 'u', '.local', 'share', 'gnome-shell',
                                                              'session-active-history.json')})
        self.assertEqual(located, good)
        self.assertEqual(logged, ['Screen Time History (GNOME Shell): 1 files that are not a JSON array, not reported'])


if __name__ == '__main__':
    unittest.main()
