"""Pin how the Recently Used Files (GTK) artifact reads recently-used.xbel as GLib writes it."""
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
from scripts.artifacts import linuxRecentFiles
# pylint: enable=wrong-import-position

UTC = timezone.utc
HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<xbel version="1.0"\n'
        '      xmlns:bookmark="http://www.freedesktop.org/standards/desktop-bookmarks"\n'
        '      xmlns:mime="http://www.freedesktop.org/standards/shared-mime-info"\n>\n')


def app(name, exec_, modified, count):
    return (f'          <bookmark:application name="{name}" exec="{exec_}" modified="{modified}" '
            f'count="{count}"/>\n')


def bookmark(href, times, inner):
    added, modified, visited = times
    return (f'  <bookmark href="{href}" added="{added}" modified="{modified}" visited="{visited}">\n{inner}'
            '  </bookmark>\n')


def meta(body, owner='http://freedesktop.org'):
    return f'    <info>\n      <metadata owner="{owner}">\n{body}      </metadata>\n    </info>\n'


class TimeTest(unittest.TestCase):
    def test_iso_times(self):
        cases = {
            '2026-09-28T16:14:19.567190Z': datetime(2026, 9, 28, 16, 14, 19, 567190, tzinfo=UTC),
            '2026-09-28T16:14:19Z': datetime(2026, 9, 28, 16, 14, 19, tzinfo=UTC),
            '2026-09-28T18:14:19+02:00': datetime(2026, 9, 28, 16, 14, 19, tzinfo=UTC),
            '2026-09-28T21:44:19.5+0530': datetime(2026, 9, 28, 16, 14, 19, 500000, tzinfo=UTC),
            '2026-09-28T12:14:19-04': datetime(2026, 9, 28, 16, 14, 19, tzinfo=UTC),
            '2026-09-28T16:14:19.123456789Z': datetime(2026, 9, 28, 16, 14, 19, 123456, tzinfo=UTC),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(linuxRecentFiles.xbel_time(value), expected)

    def test_other_forms_are_not_times(self):
        for value in (None, '', '2026-09-28T16:14:19', '2026-13-01T00:00:00Z', '2026-09-28 16:14:19Z',
                      '2026-09-28T16:14:19Z trailing', '1790577930', '0001-01-01T00:00:00+01:00'):
            with self.subTest(value=value):
                self.assertIsNone(linuxRecentFiles.xbel_time(value))

    def test_seconds_times(self):
        self.assertEqual(linuxRecentFiles.seconds_time('1790577930'), datetime(2026, 9, 28, 6, 45, 30, tzinfo=UTC))
        self.assertEqual(linuxRecentFiles.seconds_time('-5'), datetime(1969, 12, 31, 23, 59, 55, tzinfo=UTC))
        for value in (None, '', 'abc', '12.5', '99999999999999999999'):
            with self.subTest(value=value):
                self.assertIsNone(linuxRecentFiles.seconds_time(value))


class LocalPathTest(unittest.TestCase):
    def test_paths(self):
        cases = {
            'file:///home/alex/alpha%20notes.txt': '/home/alex/alpha notes.txt',
            'file:///home/alex/caf%C3%A9.txt': '/home/alex/café.txt',
            'FILE:///x': '/x',
            'file://localhost/x/y': '/x/y',
            'file:/x/y': '/x/y',
            'file:///bad%FF.txt': '/bad�.txt',
            'file://otherhost/x': '',
            'file://otherhost': '',
            'file:x': '',
            'https://www.example.org/a%20b.html': '',
            '': '',
        }
        for uri, expected in cases.items():
            with self.subTest(uri=uri):
                self.assertEqual(linuxRecentFiles.local_path(uri), expected)


T1 = ('2026-09-28T16:14:19.567190Z', '2026-09-28T16:14:50.607555Z', '2026-09-28T16:14:19.567191Z')
T2 = ('2026-09-28T16:14:28.929895Z', '2026-09-28T16:14:28.929899Z', '2026-09-28T16:14:28.929895Z')


def dt(value):
    return linuxRecentFiles.xbel_time(value)


class RowsTest(unittest.TestCase):
    def test_rows_follow_the_file(self):
        text = HEAD + bookmark(
            'file:///home/alex/alpha%20notes.txt', T1,
            meta('        <mime:mime-type type="text/plain"/>\n        <bookmark:applications>\n'
                 + app('Known GTK3', "&apos;known-gtk3 %u&apos;", '2026-09-28T16:14:50.607554Z', 2)
                 + app('Known GTK4', "&apos;known-gtk4 %u&apos;", '2026-09-28T16:14:45.956388Z', 1)
                 + '        </bookmark:applications>\n')) + bookmark(
            'file:///home/alex/gamma.png', T2,
            '    <title>Gamma &amp; Title</title>\n    <desc>A description</desc>\n'
            + meta('        <mime:mime-type type="image/png"/>\n        <bookmark:groups>\n'
                   '          <bookmark:group>one</bookmark:group>\n          <bookmark:group>two</bookmark:group>\n'
                   '        </bookmark:groups>\n        <bookmark:applications>\n'
                   + app('Viewer', "&apos;viewer %f&apos;", '2026-09-28T16:14:28.929898Z', 1)
                   + '        </bookmark:applications>\n        <bookmark:private/>\n')) + '</xbel>'
        counts = Counter()
        rows = linuxRecentFiles.recent_rows(text.encode(), counts)
        shared = (dt(T1[0]), dt(T1[1]), '/home/alex/alpha notes.txt', 'file:///home/alex/alpha%20notes.txt',
                  '', '', 'text/plain')
        self.assertEqual(rows, [
            (dt('2026-09-28T16:14:50.607554Z'), *shared, 'Known GTK3', "'known-gtk3 %u'", '2', '', 'no'),
            (dt('2026-09-28T16:14:45.956388Z'), *shared, 'Known GTK4', "'known-gtk4 %u'", '1', '', 'no'),
            (dt('2026-09-28T16:14:28.929898Z'), dt(T2[0]), dt(T2[1]), '/home/alex/gamma.png',
             'file:///home/alex/gamma.png', 'Gamma & Title', 'A description', 'image/png', 'Viewer', "'viewer %f'",
             '1', 'one, two', 'yes')])
        self.assertEqual(counts, Counter())

    def test_other_shapes(self):
        text = HEAD + bookmark(
            'https://www.example.org/a.html', ('2026-09-28T16:14:41Z', 'not a time', '2026-09-28T16:14:41'),
            meta('        <mime:mime-type type="text/html"/>\n', owner='http://example.org/other')
            + meta('        <bookmark:applications>\n'
                   '          <bookmark:application name="Old" exec="old %u" timestamp="1790577930" count="3"/>\n'
                   '          <bookmark:application name="Bad" exec="bad %u" modified="yesterday"/>\n'
                   '          <bookmark:application name="None" exec="none %u"/>\n'
                   '        </bookmark:applications>\n')) + (
            '  <bookmark href="file:///home/alex/bare.txt">\n  </bookmark>\n'
            '  <folder><bookmark href="file:///home/alex/nested.txt"/></folder>\n</xbel>')
        counts = Counter()
        rows = linuxRecentFiles.recent_rows(text.encode(), counts)
        times = (dt('2026-09-28T16:14:41Z'), '')
        shared = ('', 'https://www.example.org/a.html', '', '', '')
        self.assertEqual(rows, [
            (datetime(2026, 9, 28, 6, 45, 30, tzinfo=UTC), *times, *shared, 'Old', 'old %u', '3', '', 'no'),
            ('', *times, *shared, 'Bad', 'bad %u', '', '', 'no'),
            ('', *times, *shared, 'None', 'none %u', '', '', 'no'),
            ('', '', '', '/home/alex/bare.txt', 'file:///home/alex/bare.txt', '', '', '', '', '', '', '', 'no')])
        self.assertEqual(counts, {'bookmark modified times in another form, left blank': 1,
                                  'application times in another form, left blank': 1,
                                  'bookmark elements not directly in the xbel element, not reported': 1})

    def test_repeated_elements_read_as_glib_reads_them(self):
        text = HEAD + bookmark(
            'file:///home/alex/two.txt', T2,
            '    <title>First</title>\n    <title>Second</title>\n    <desc>One</desc>\n    <desc>Two</desc>\n'
            '    <info>\n      <metadata owner="http://freedesktop.org">\n'
            '        <mime:mime-type type="text/plain"/>\n        <bookmark:private/>\n'
            '        <bookmark:groups><bookmark:group>a</bookmark:group></bookmark:groups>\n'
            '      </metadata>\n      <metadata owner="http://freedesktop.org">\n'
            '        <mime:mime-type type="text/x-other"/>\n'
            '        <bookmark:groups><bookmark:group>b</bookmark:group></bookmark:groups>\n'
            '        <bookmark:applications>\n'
            '          <bookmark:application name="Both" exec="both %u" modified="2026-09-28T16:14:28.929898Z" '
            'timestamp="1790577930" count="5"/>\n'
            '        </bookmark:applications>\n      </metadata>\n    </info>\n') + '</xbel>'
        counts = Counter()
        rows = linuxRecentFiles.recent_rows(text.encode(), counts)
        self.assertEqual(rows, [(dt('2026-09-28T16:14:28.929898Z'), dt(T2[0]), dt(T2[1]),
                                 '/home/alex/two.txt', 'file:///home/alex/two.txt', 'Second', 'Two', 'text/x-other',
                                 'Both', 'both %u', '5', 'a, b', 'yes')])
        self.assertEqual(counts, Counter())

    def test_not_an_xbel_file(self):
        for data in (b'', b'not xml', b'<?xml version="1.0"?><other/>', HEAD.encode() + b'<bookmark'):
            with self.subTest(data=data[:20]):
                self.assertIsNone(linuxRecentFiles.recent_rows(data, Counter()))


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_rows_name_their_file(self):
        one = HEAD + bookmark('file:///home/alex/a.txt', T1, meta(
            '        <bookmark:applications>\n' + app('A', 'a %u', T1[1], 1) + '        </bookmark:applications>\n')) + '</xbel>'
        two = HEAD + bookmark('file:///home/bo/b.txt', T2, meta(
            '        <bookmark:applications>\n' + app('B', 'b %u', T2[1], 4) + '        </bookmark:applications>\n')) + '</xbel>'
        empty = HEAD + '</xbel>'
        with tempfile.TemporaryDirectory() as root:
            files = []
            for rel, text in (('home/bo/.local/share/recently-used.xbel', two),
                              ('home/alex/.local/share/recently-used.xbel', one),
                              ('home/old/.recently-used.xbel', empty),
                              ('home/cy/.local/share/recently-used.xbel', 'broken <xbel')):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write(text)
                files.append(path)
            files.append(os.path.join(root, 'home', 'bo', '.local', 'share'))
            files.append(os.path.join(root, 'home', 'gone', '.recently-used.xbel'))
            with mock.patch.object(linuxRecentFiles, 'logfunc') as log:
                headers, rows, source = linuxRecentFiles.linuxRecentFiles.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([(r[8], r[10], r[13]) for r in rows],
                         [('A', '1', os.path.join('home', 'alex', '.local', 'share', 'recently-used.xbel')),
                          ('B', '4', os.path.join('home', 'bo', '.local', 'share', 'recently-used.xbel'))])
        self.assertEqual(source.split('\n'), [os.path.join(root, 'home', 'alex', '.local', 'share', 'recently-used.xbel'),
                                              os.path.join(root, 'home', 'bo', '.local', 'share', 'recently-used.xbel')])
        self.assertEqual(log.call_args.args[0], 'Recently Used Files (GTK): 1 files that are not XML with an xbel root '
                                                'element, not reported, 1 files that could not be read')


if __name__ == '__main__':
    unittest.main()
