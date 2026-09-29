"""Pin the wget HSTS Hosts artifact (scripts/artifacts/wgetHsts.py).

STORE is the lab VM's ~/.wget-hsts from ubuntu2604_arm64_wgethsts byte for byte, as wget 1.25.0 wrote it after the
known steps; both hosts in it were fetched for the known data.
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
from scripts.artifacts import wgetHsts as wh
# pylint: enable=wrong-import-position

STORE = (b'# HSTS 1.0 Known Hosts database for GNU Wget.\n# Edit at your own risk.\n'
         b'# <hostname>\t<port>\t<incl. subdomains>\t<created>\t<max-age>\n'
         b'ubuntu.com\t0\t0\t1790669145\t15724800\ngithub.com\t0\t1\t1790669150\t31536000\n')


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def rows_of(data, counts=None):
    return wh.store_rows(data, Counter() if counts is None else counts)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ReaderTest(unittest.TestCase):
    def test_store(self):
        counts = Counter()
        self.assertEqual(rows_of(STORE, counts), [
            (utc(1790669145), 'ubuntu.com', 0, 'No', 15724800, utc(1790669145 + 15724800), 4),
            (utc(1790669150), 'github.com', 0, 'Yes', 31536000, utc(1790669150 + 31536000), 5)])
        self.assertEqual(counts, Counter())

    def test_scan_line_as_sscanf_reads_it(self):
        self.assertEqual(wh.scan_line(b'  a.b  8443 2 -5 +7 trailing\r'), ('a.b', 8443, 2, -5, 7))
        self.assertEqual(wh.scan_line(b'a\t1\t0\t2\t3'), ('a', 1, 0, 2, 3))
        for line in (b'', b'   ', b'# a 0 0 1 1', b'  #x'):
            self.assertIsNone(wh.scan_line(line), line)
        for line in (b'a 0 0 1', b'a 0 x 1 1', b'a 0 0 12abc 1', b'a - 0 1 1', b'a 2147483648 0 1 1',
                     b'a 0 0 9223372036854775808 1', b'a 0 0 1 -9223372036854775809'):
            self.assertIs(wh.scan_line(line), False, line)

    def test_every_c_space_separates_and_the_64_bit_maximum_fits(self):
        self.assertEqual(wh.scan_line(b'a\r0\v0\f9223372036854775807\t-9223372036854775808'),
                         ('a', 0, 0, 9223372036854775807, -9223372036854775808))
        self.assertEqual(wh.scan_line(b'b 2147483647 -2147483648 1 1'), ('b', 2147483647, -2147483648, 1, 1))

    def test_host_of_more_than_255_bytes_is_not_read(self):
        self.assertEqual(wh.scan_line(b'h' * 255 + b' 0 0 1 1')[0], 'h' * 255)
        self.assertIs(wh.scan_line(b'h' * 256 + b' 0 0 1 1'), False)
        self.assertIs(wh.scan_line('é'.encode() * 128 + b' 0 0 1 1'), False)

    def test_host_bytes_that_are_not_utf8(self):
        self.assertEqual(wh.scan_line(b'caf\xe9.test 0 0 1 1')[0], 'caf\\xe9.test')

    def test_subdomains_and_counts(self):
        counts = Counter()
        rows = rows_of(b'# c\na 0 -3 10 20\nb 0 0 10\n\nc 443 1 99999999999999 1\n', counts)
        self.assertEqual([(r[1], r[2], r[3], r[6]) for r in rows], [('a', 0, 'Yes', 2), ('c', 443, 'Yes', 5)])
        self.assertEqual(rows[1][0], '')
        self.assertEqual(counts, Counter({'lines wget does not read, not reported': 1,
                                          'times outside the range of a date, left blank': 1}))


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.logged = []
        patcher = mock.patch.object(wh, 'logfunc', self.logged.append)
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
        return wh.wgetHsts.__wrapped__(FakeContext(self.paths, self.root))

    def test_headers(self):
        self.assertEqual(self.run_artifact()[0], (('Created (UTC)', 'datetime'), 'Host', 'Port', 'Include Subdomains',
                                                  'Max-Age (s)', ('Expires (UTC)', 'datetime'), 'Line',
                                                  'Source File'))

    def test_rows_per_file_and_problems_logged(self):
        one = self.add('home/u/.wget-hsts', STORE)
        root = self.add('root/.wget-hsts', b'x 0 0 1\nroot.test 0 0 5 5\n')
        self.add('home/v/.wget-hsts', b'# only comments\n')
        folder = os.path.join(self.root, 'home', 'dir', '.wget-hsts')
        os.makedirs(folder)
        self.paths.append(folder)
        _h, rows, source = self.run_artifact()
        self.assertEqual([(r[1], r[7]) for r in rows], [('ubuntu.com', 'home/u/.wget-hsts'),
                                                        ('github.com', 'home/u/.wget-hsts'),
                                                        ('root.test', 'root/.wget-hsts')])
        self.assertEqual(source.split('\n'), [one, root])
        self.assertEqual(self.logged, ['wget HSTS Hosts: 1 lines wget does not read, not reported'])

    def test_unreadable_file_is_counted(self):
        path = self.add('home/u/.wget-hsts', STORE)
        with mock.patch('builtins.open', side_effect=OSError('denied')):
            _h, rows, source = self.run_artifact()
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ['wget HSTS Hosts: 1 files that could not be read'])
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
