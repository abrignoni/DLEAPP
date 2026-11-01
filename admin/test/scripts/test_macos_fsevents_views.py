"""FSEvents pages under db/fseventsd, and the same file seen through two volume views.

A logical extraction of a Mac can hold private/var/db/fseventsd both at the root and under
System/Volumes/Data/. A byte-identical copy is read once; copies that differ are both read.
Pages are built here by hand; expected values are written out.
"""
import fnmatch
import gzip
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosFSEvents  # pylint: disable=wrong-import-position


def _page(records):
    body = b''.join(path.encode() + b'\x00' + struct.pack('<QI', event_id, flags)
                    for path, event_id, flags in records)
    return gzip.compress(b'1SLD' + struct.pack('<II', 0, 12 + len(body)) + body)


class _Result:
    def __init__(self):
        self.rows, self.source = [], None

    def add_row(self, row):
        self.rows.append(row)

    def set_source_path(self, source):
        self.source = source


class _Context:
    def __init__(self, paths, root):
        self.paths, self.root, self.result = paths, root, _Result()

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def create_artifact_result(self, headers=None):  # pylint: disable=unused-argument
        return self.result


class ViewsTest(unittest.TestCase):
    def test_paths_match_both_folders(self):
        patterns = macosFSEvents.__artifacts_v2__['macosFSEvents']['paths']
        for member in ('System/Volumes/Data/.fseventsd/0000000000000001',
                       'private/var/db/fseventsd/0000000000000001',
                       'System/Volumes/Data/private/var/db/fseventsd/0000000000000001'):
            self.assertTrue(any(fnmatch.fnmatch('root/' + member, p) for p in patterns), member)

    def test_an_identical_copy_is_read_once_and_a_different_one_is_read(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            same = _page([('a.txt', 1, 0x00800000)])
            root_view = write('private/var/db/fseventsd/0000000000000001', same)
            data_view = write('System/Volumes/Data/private/var/db/fseventsd/0000000000000001', same)
            root_other = write('private/var/db/fseventsd/0000000000000002', _page([('b.txt', 2, 0x00800000)]))
            data_other = write('System/Volumes/Data/private/var/db/fseventsd/0000000000000002',
                               _page([('c.txt', 3, 0x00800000)]))
            context = _Context([data_view, root_view, data_other, root_other], root)
            with mock.patch.object(macosFSEvents, 'logfunc'), \
                    mock.patch('scripts.macos_plists.logfunc') as shared_log:
                macosFSEvents.macosFSEvents.__wrapped__(context)
        self.assertEqual([(row[0], row[1], row[-1]) for row in context.result.rows], [
            (3, 'c.txt', 'System/Volumes/Data/private/var/db/fseventsd/0000000000000002'),
            (1, 'a.txt', 'private/var/db/fseventsd/0000000000000001'),
            (2, 'b.txt', 'private/var/db/fseventsd/0000000000000002'),
        ])
        self.assertEqual(context.result.source.split('\n'), [data_other, root_view, root_other])
        shared_log.assert_called_once_with(
            'FSEvents: 1 byte-identical copy(ies) under System/Volumes/Data or System/Volumes/Update/mnt1 '
            'not read again')


if __name__ == '__main__':
    unittest.main()
