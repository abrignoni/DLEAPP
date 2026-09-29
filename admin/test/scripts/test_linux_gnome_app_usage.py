"""Pin the Application Usage (GNOME Shell) artifact (scripts/artifacts/linuxGnomeAppUsage.py).

KNOWN_LINES are the three lines for the known applications of ubuntu2604_arm64_appstate, byte for byte as GNOME Shell
50.1 wrote them on the lab VM (the capture's other entries are left out). OLD is built in the form GNOME Shell 3.0 to
3.30.2 wrote, from that writer's format strings (src/shell-app-usage.c at 3.30.2).
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
from scripts.artifacts import linuxGnomeAppUsage as au
# pylint: enable=wrong-import-position

HEAD = b'<?xml version="1.0"?>\n<application-state>\n  <context id="">\n'
TAIL = b'  </context>\n</application-state>\n'
KNOWN_LINES = (b'    <application id="org.gnome.Characters.desktop" score="3" last-seen="1790660626"/>\n'
               b'    <application id="org.gnome.Calculator.desktop" score="35" last-seen="1790660213"/>\n'
               b'    <application id="org.gnome.baobab.desktop" score="13" last-seen="1790659480"/>\n')
NEW = HEAD + KNOWN_LINES + TAIL
OLD = (b'<?xml version="1.0"?>\n<application-state>\n  <context id="">\n'
       b'    <application id="gedit.desktop" open-window-count="2" score="12857.5" last-seen="1540000000"/>\n'
       b'    <application id="org.gnome.Nautilus.desktop" open-window-count="0" score="7" last-seen="1540000100"/>\n'
       b'  </context>  <context id="activity">\n'
       b'    <application id="gedit.desktop" open-window-count="1" score="3" last-seen="1530000000"/>\n'
       b'  </context>\n</application-state>\n')


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def rows_of(data, counts=None):
    return au.usage_rows(data, Counter() if counts is None else counts)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ReaderTest(unittest.TestCase):
    def test_known_lines(self):
        self.assertEqual(rows_of(NEW), [(utc(1790660626), 'org.gnome.Characters.desktop', '3', ''),
                                        (utc(1790660213), 'org.gnome.Calculator.desktop', '35', ''),
                                        (utc(1790659480), 'org.gnome.baobab.desktop', '13', '')])

    def test_old_form_with_open_windows_and_two_contexts(self):
        counts = Counter()
        self.assertEqual(rows_of(OLD, counts), [(utc(1540000000), 'gedit.desktop', '12857.5', '2'),
                                                (utc(1540000100), 'org.gnome.Nautilus.desktop', '7', '0'),
                                                (utc(1530000000), 'gedit.desktop', '3', '1')])
        self.assertEqual(counts, Counter())

    def test_last_seen(self):
        self.assertEqual(au.last_seen_time('1790660626'), utc(1790660626))
        for value in ('0', '00', '', None, '-5', '12.5', ' 12', 'abc', '99999999999999999999'):
            self.assertIsNone(au.last_seen_time(value), value)

    def test_zero_and_missing_last_seen_are_blank_and_not_counted(self):
        counts = Counter()
        data = HEAD + b'    <application id="a.desktop" score="0" last-seen="0"/>\n' \
                      b'    <application id="b.desktop" score="1"/>\n' + TAIL
        self.assertEqual(rows_of(data, counts), [('', 'a.desktop', '0', ''), ('', 'b.desktop', '1', '')])
        self.assertEqual(counts, Counter())

    def test_last_seen_that_is_not_a_time_is_blank_and_counted(self):
        counts = Counter()
        data = HEAD + b'    <application id="a.desktop" score="1" last-seen="soon"/>\n' \
                      b'    <application id="b.desktop" score="2" last-seen="99999999999999999999"/>\n' + TAIL
        self.assertEqual(rows_of(data, counts), [('', 'a.desktop', '1', ''), ('', 'b.desktop', '2', '')])
        self.assertEqual(counts, Counter({'last-seen values that are not a whole number of seconds, left blank': 2}))

    def test_application_without_id_is_counted(self):
        counts = Counter()
        data = HEAD + b'    <application score="4" last-seen="1790660626"/>\n' \
                      b'    <application id="" score="5"/>\n' + KNOWN_LINES + TAIL
        self.assertEqual(len(rows_of(data, counts)), 3)
        self.assertEqual(counts, Counter({'application elements without an id, not reported': 2}))

    def test_escaped_id_is_read_as_written_before_escaping(self):
        data = HEAD + b'    <application id="a&amp;b &lt;c&gt;.desktop" score="1" last-seen="1790660626"/>\n' + TAIL
        self.assertEqual(rows_of(data)[0][1], 'a&b <c>.desktop')

    def test_application_outside_a_context_is_read_and_other_elements_counted(self):
        counts = Counter()
        data = (b'<application-state><application id="x.desktop" score="2" last-seen="1790660626"/>'
                b'<context id=""><extra/><application id="y.desktop" score="3" last-seen="1790660000"><more/>'
                b'</application></context></application-state>')
        self.assertEqual([row[1] for row in rows_of(data, counts)], ['x.desktop', 'y.desktop'])
        self.assertEqual(counts, Counter({'elements other than context and application, passed over': 2}))

    def test_not_this_file(self):
        for data in (b'', b'not xml', b'<?xml version="1.0"?>\n<xbel version="1.0"/>', NEW[:-30]):
            self.assertIsNone(rows_of(data), data[:20])

    def test_order(self):
        rows = [('', 'b', '1', ''), (utc(5), 'z', '1', ''), (utc(9), 'a', '1', ''), (utc(5), 'c', '1', ''),
                ('', 'a', '1', '')]
        self.assertEqual([r[1] for r in sorted(rows, key=au.row_order)], ['a', 'c', 'z', 'a', 'b'])


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.logged = []
        patcher = mock.patch.object(au, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = []

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, relative, data):
        path = os.path.join(self.root, *relative.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        self.paths.append(path)
        return path

    def run_artifact(self):
        return au.linuxGnomeAppUsage.__wrapped__(FakeContext(self.paths, self.root))

    def test_headers(self):
        headers, _rows, _source = self.run_artifact()
        self.assertEqual(headers, (('Last Seen (UTC)', 'datetime'), 'Application ID', 'Score', 'Open Windows',
                                   'Source File'))

    def test_rows_per_user_sorted_and_problems_logged(self):
        suffix = '/.local/share/gnome-shell/application_state'
        known = self.add('home/u' + suffix, NEW)
        old = self.add('root' + suffix, OLD)
        self.add('home/empty' + suffix, HEAD + TAIL)
        self.add('home/bad' + suffix, b'garbage')
        folder = os.path.join(self.root, 'home', 'dir', '.local', 'share', 'gnome-shell', 'application_state')
        os.makedirs(folder)
        self.paths.append(folder)
        _headers, rows, source = self.run_artifact()
        self.assertEqual([(r[1], r[4]) for r in rows],
                         [('org.gnome.Characters.desktop', 'home/u' + suffix),
                          ('org.gnome.Calculator.desktop', 'home/u' + suffix),
                          ('org.gnome.baobab.desktop', 'home/u' + suffix),
                          ('org.gnome.Nautilus.desktop', 'root' + suffix),
                          ('gedit.desktop', 'root' + suffix),
                          ('gedit.desktop', 'root' + suffix)])
        self.assertEqual(rows[4][2:4], ('12857.5', '2'))
        self.assertEqual(source.split('\n'), [known, old])
        self.assertEqual(self.logged, ['Application Usage (GNOME Shell): 1 files that are not XML with an '
                                       'application-state root element, not reported'])

    def test_unreadable_file_is_counted(self):
        path = self.add('home/u/.local/share/gnome-shell/application_state', NEW)
        with mock.patch('builtins.open', side_effect=OSError('denied')):
            _headers, rows, source = self.run_artifact()
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ['Application Usage (GNOME Shell): 1 files that could not be read'])
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
