"""Cookies from the .binarycookies stores in Library/Cookies and Library/HTTPStorages folders."""

import datetime
import fnmatch
import os
import pathlib
import plistlib
import struct
import tempfile
import unittest
from unittest import mock

from scripts import macos_plists
from scripts.artifacts import macosBinaryCookies

UTC = datetime.timezone.utc
EPOCH = datetime.datetime(2001, 1, 1, tzinfo=UTC)


def _seconds(when):
    return (when - EPOCH).total_seconds()


def record(domain, name, path, value, flags=0, created=None, expires=None, extra=None):
    """One cookie record laid out as the dtformats specification describes it."""
    strings = b''.join(text.encode('utf-8') + b'\x00' for text in (domain, name, path, value))
    offsets, position = [], 56
    for text in (domain, name, path, value):
        offsets.append(position)
        position += len(text.encode('utf-8')) + 1
    tail = plistlib.dumps(extra, fmt=plistlib.PlistFormat.FMT_BINARY) if extra else b''
    size = 56 + len(strings) + len(tail)
    header = struct.pack('<4I4I8x2d', size, 0, flags, 0, *offsets,
                         _seconds(expires or datetime.datetime(2026, 1, 1, tzinfo=UTC)),
                         _seconds(created or datetime.datetime(2025, 1, 1, tzinfo=UTC)))
    return header + strings + tail


def page(records, signature=b'\x00\x00\x01\x00'):
    table = 8 + 4 * len(records)
    offsets, position = [], table
    for item in records:
        offsets.append(position)
        position += len(item)
    return signature + struct.pack(f'<I{len(records)}I', len(records), *offsets) + b''.join(records) + b'\x00' * 4


def cookie_file(pages, trailer=True):
    data = b'cook' + struct.pack(f'>I{len(pages)}I', len(pages), *(len(item) for item in pages)) + b''.join(pages)
    data += b'\x00' * 8
    if trailer:
        data += plistlib.dumps({'NSHTTPCookieAcceptPolicy': 2}, fmt=plistlib.PlistFormat.FMT_BINARY)
    return data


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class BinaryCookiesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def _run(self, files):
        with mock.patch.object(macosBinaryCookies, 'logfunc', self.logs.append), \
                mock.patch.object(macos_plists, 'logfunc', self.logs.append):
            return macosBinaryCookies.macosBinaryCookies.__wrapped__(FakeContext(self.root, files))

    def test_records_with_and_without_a_trailing_property_list(self):
        created = datetime.datetime(2025, 11, 20, 18, 32, 20, tzinfo=UTC)
        accessed = datetime.datetime(2025, 12, 12, 22, 45, 34, 500000, tzinfo=UTC)
        path = self._write('Users/alice/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies',
                           cookie_file([page([
                               record('.example.com', 'sid', '/', 'abc', flags=0x5,
                                      created=datetime.datetime(2021, 2, 15, 20, 50, 27, tzinfo=UTC),
                                      expires=datetime.datetime(2022, 2, 15, 20, 50, 27, tzinfo=UTC)),
                               record('www.example.org', 'pref', '/app', 'x=1', flags=0x4200, created=created,
                                      extra={'AccessTime': _seconds(accessed),
                                             'StoragePartition': 'https://indeed.com'}),
                           ])]))
        headers, rows, source = self._run([path])
        self.assertEqual(headers[:3], (('Created (UTC)', 'datetime'), ('Expires (UTC)', 'datetime'),
                                       ('AccessTime (UTC)', 'datetime')))
        where = 'Users/alice/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies'
        self.assertEqual(rows, [
            (datetime.datetime(2021, 2, 15, 20, 50, 27, tzinfo=UTC), datetime.datetime(2022, 2, 15, 20, 50, 27, tzinfo=UTC),
             '', '.example.com', 'sid', '/', 'abc', 'true', 'true', '0x00000005', '', 'com.apple.Safari', where),
            (created, datetime.datetime(2026, 1, 1, tzinfo=UTC), accessed, 'www.example.org', 'pref', '/app', 'x=1',
             'false', 'false', '0x00004200', 'https://indeed.com', 'com.apple.Safari', where),
        ])
        self.assertEqual(source, path)

    def test_pages_and_records_that_do_not_fit_are_counted(self):
        good = record('a.example', 'n', '/', 'v')
        short = struct.pack('<I', 20) + b'\x00' * 16
        outside = bytearray(record('b.example', 'n', '/', 'v'))
        struct.pack_into('<I', outside, 28, 4000)
        path = self._write('Users/alice/Library/Cookies/Cookies.binarycookies', cookie_file([
            page([good, short, bytes(outside)]),
            page([good], signature=b'\x01\x02\x03\x04'),
        ]))
        _headers, rows, _source = self._run([path])
        self.assertEqual([row[3] for row in rows], ['a.example'])
        self.assertIn('Binary Cookies: skipped 1 pages without the page signature, 1 records shorter than 56 bytes, '
                      '1 records whose string offsets fall outside them', self.logs)

    def test_a_file_that_is_not_a_cookie_store_is_logged(self):
        text = self._write('Users/alice/Library/Cookies/Cookies.binarycookies', b'not a cookie file')
        wrong = self._write('Users/bob/Library/Cookies/Cookies.binarycookies',
                            b'kooc' + cookie_file([page([record('a.example', 'n', '/', 'v')])])[4:])
        _headers, rows, source = self._run([text, wrong])
        self.assertEqual((rows, source), ([], ''))
        for user in ('alice', 'bob'):
            self.assertIn(f'Binary Cookies: not a binary cookie file: Users/{user}/Library/Cookies/Cookies.binarycookies',
                          self.logs)

    def test_an_empty_store_gives_no_rows_and_is_not_cited(self):
        path = self._write('Users/alice/Library/Cookies/Cookies.binarycookies', cookie_file([]))
        _headers, rows, source = self._run([path])
        self.assertEqual((rows, source), ([], ''))

    def test_the_container_comes_from_the_path(self):
        data = cookie_file([page([record('a.example', 'n', '/', 'v')])])
        files = [self._write('Users/alice/Library/HTTPStorages/com.google.GoogleUpdater.binarycookies', data),
                 self._write('Users/alice/Library/Group Containers/group.x/Library/Cookies/Cookies.binarycookies', data),
                 self._write('Users/alice/Library/Cookies/Cookies.binarycookies', data)]
        _headers, rows, _source = self._run(files)
        self.assertEqual(sorted(row[11] for row in rows), ['', 'com.google.GoogleUpdater', 'group.x'])

    def test_a_byte_identical_copy_under_system_volumes_data_is_read_once(self):
        data = cookie_file([page([record('a.example', 'n', '/', 'v')])])
        first = self._write('Users/alice/Library/Cookies/Cookies.binarycookies', data)
        second = self._write('System/Volumes/Data/Users/alice/Library/Cookies/Cookies.binarycookies', data)
        _headers, rows, source = self._run([second, first])
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, first)

    def test_two_captures_of_one_store_give_each_record_once(self):
        older = record('a.example', 'NID', '/', 'old', created=datetime.datetime(2025, 12, 25, 8, 4, 52, tzinfo=UTC))
        newer = record('a.example', 'NID', '/', 'new', created=datetime.datetime(2025, 12, 25, 19, 5, 53, tzinfo=UTC))
        shared = record('b.example', 'sid', '/', 'same')
        first = self._write('Users/alice/Library/HTTPStorages/com.google.GoogleUpdater.binarycookies',
                            cookie_file([page([shared, newer])]))
        second = self._write('System/Volumes/Data/Users/alice/Library/HTTPStorages/com.google.GoogleUpdater.binarycookies',
                             cookie_file([page([shared, older])]))
        _headers, rows, source = self._run([second, first])
        self.assertEqual([(row[6], row[12].startswith('System/')) for row in rows],
                         [('same', False), ('new', False), ('old', True)])
        self.assertEqual(source.split('\n'), [first, second])
        self.assertIn('Binary Cookies: 1 record(s) the other capture of the same store also holds not reported again',
                      self.logs)

    def test_paths_reach_the_cookie_folders_only(self):
        patterns = macosBinaryCookies.__artifacts_v2__['macosBinaryCookies']['paths']
        def matched(path):
            return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        self.assertTrue(matched('/case/Users/a/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies'))
        self.assertTrue(matched('/case/private/var/root/Library/HTTPStorages/com.google.GoogleUpdater.binarycookies'))
        self.assertFalse(matched('/case/Users/a/Downloads/Cookies.binarycookies'))


if __name__ == '__main__':
    unittest.main()
