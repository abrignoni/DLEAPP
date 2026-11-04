"""Pin the INFO2 reader (scripts/artifacts/windowsRecycleBin.py) on files built here in the layout libyal dtformats
documents: a 20-byte header, then 800-byte (Windows 2000 and later) or 280-byte (Windows Me) entries. Every name
and value here is made up."""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsRecycleBin as artifact  # pylint: disable=wrong-import-position

from datetime import datetime, timezone  # pylint: disable=wrong-import-order,wrong-import-position

# 2004-08-25 16:18:25.237 UTC as a FILETIME, computed rather than typed
FILETIME_2004 = (int((datetime(2004, 8, 25, 16, 18, 25, tzinfo=timezone.utc)
                      - datetime(1601, 1, 1, tzinfo=timezone.utc)).total_seconds()) * 10_000_000
                 + 2_370_000)


def info2(names, entry_size=800):
    data = struct.pack('<IIIII', 5, len(names), len(names), entry_size, 5)
    for index, name in enumerate(names, start=1):
        entry = name.encode('latin-1').ljust(260, b'\x00')
        entry += struct.pack('<IIQI', index, 2, FILETIME_2004 + index, 4096 * index)
        if entry_size > 280:
            entry += name.encode('utf-16-le').ljust(520, b'\x00')
        data += entry
    return data


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class Info2Test(unittest.TestCase):
    def test_entries_of_800_bytes(self):
        size, count, entries = artifact.parse_info2(info2(['C:\\a\\one.exe', 'C:\\b\\two.txt']))
        self.assertEqual((size, count), (800, 2))
        self.assertEqual(entries[1], (2, 2, FILETIME_2004 + 2, 8192, 'C:\\b\\two.txt'))

    def test_entries_of_280_bytes_read_the_ascii_name(self):
        _size, _count, entries = artifact.parse_info2(info2(['C:\\me\\old.doc'], entry_size=280))
        self.assertEqual(entries[0][4], 'C:\\me\\old.doc')

    def test_a_file_that_does_not_fit_is_refused(self):
        self.assertIsNone(artifact.parse_info2(info2(['C:\\x.exe'], entry_size=512)))
        self.assertIsNone(artifact.parse_info2(info2(['C:\\x.exe'])[:-1]))
        self.assertIsNone(artifact.parse_info2(b'\x05\x00'))

    def test_rows_name_the_recycled_file_by_index(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(artifact, 'logfunc', lambda *a, **k: None):
            folder = os.path.join(root, 'RECYCLER', 'S-1-5-21-1-2-3-1003')
            os.makedirs(folder)
            files = []
            for name, data in (('INFO2', info2(['C:\\a\\one.exe', 'C:\\b\\two.txt'])), ('Dc1.exe', b'x'),
                               ('Dc2.doc', b'y'), ('desktop.ini', b'z')):
                path = os.path.join(folder, name)
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            headers, rows, source = artifact.recycleBinInfo2.__wrapped__(Context(root, files))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([r[5] for r in rows], ['Dc1.exe', ''])   # two.txt has no Dc2.txt
        self.assertEqual(rows[0][7], 'S-1-5-21-1-2-3-1003')
        self.assertEqual(rows[0][0].strftime('%Y-%m-%d %H:%M:%S.%f'), '2004-08-25 16:18:25.237000')
        self.assertTrue(source.endswith('INFO2'))


if __name__ == '__main__':
    unittest.main()
