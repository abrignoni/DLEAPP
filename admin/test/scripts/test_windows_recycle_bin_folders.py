"""Pin Recycle Bin Folder Contents and the $I time conversion in scripts/artifacts/windowsRecycleBin.py, on a
Recycle Bin folder built here: a version 2 $I file (libyal dtformats layout) and the $R folder it names."""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsRecycleBin as rb  # pylint: disable=wrong-import-position

DELETED = 131673684178906250  # 2018-04-05 02:20:17.8906250 UTC


def i_file(path, size=0, filetime=DELETED):
    text = path.encode('utf-16-le') + b'\x00\x00'
    return struct.pack('<QQQI', 2, size, filetime, len(text) // 2) + text


class _Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return path


class FolderContentsTest(unittest.TestCase):
    def build(self, folder, with_i=True):
        sid = os.path.join(folder, 'C', '$Recycle.Bin', 'S-1-5-21-1')
        os.makedirs(os.path.join(sid, '$RAB12CD', 'sub'))
        files = []
        for name, data in (('top.txt', b'1234'), (os.path.join('sub', 'inner.bin'), b'xy')):
            path = os.path.join(sid, '$RAB12CD', name)
            with open(path, 'wb') as handle:
                handle.write(data)
            files.append(path)
        if with_i:
            path = os.path.join(sid, '$IAB12CD')
            with open(path, 'wb') as handle:
                handle.write(i_file('C:\\Users\\u\\Desktop\\Folder'))
            files.append(path)
        return files

    def test_rows_join_the_paired_i_file(self):
        with tempfile.TemporaryDirectory() as folder:
            _headers, rows, _source = rb.recycleBinFolderContents.__wrapped__(_Context(self.build(folder)))
        deleted = datetime(2018, 4, 5, 2, 20, 17, 890625, tzinfo=timezone.utc)
        self.assertEqual(sorted(rows), sorted([
            (deleted, 'C:\\Users\\u\\Desktop\\Folder\\top.txt', 'top.txt', 4, 'C:\\Users\\u\\Desktop\\Folder',
             '$RAB12CD', 'S-1-5-21-1'),
            (deleted, 'C:\\Users\\u\\Desktop\\Folder\\sub\\inner.bin', 'sub\\inner.bin', 2,
             'C:\\Users\\u\\Desktop\\Folder', '$RAB12CD', 'S-1-5-21-1')]))

    def test_without_an_i_file_the_folder_columns_are_blank(self):
        with tempfile.TemporaryDirectory() as folder:
            _headers, rows, _source = rb.recycleBinFolderContents.__wrapped__(
                _Context(self.build(folder, with_i=False)))
        self.assertEqual({row[:2] + row[4:5] for row in rows}, {('', '', '')})

    def test_a_path_outside_a_r_folder_is_not_a_content_row(self):
        self.assertIsNone(rb._recycle_parts('/x/$Recycle.Bin/S-1/$RABC.txt'))  # pylint: disable=protected-access
        self.assertIsNone(rb._recycle_parts('/x/Users/a/file.txt'))  # pylint: disable=protected-access

    def test_filetime_is_cut_to_whole_microseconds(self):
        # 2018-04-05 02:20:17.8906257 UTC; a float division gives .890626.
        self.assertEqual(rb._utc_from_filetime(DELETED + 7).microsecond, 890625)  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
