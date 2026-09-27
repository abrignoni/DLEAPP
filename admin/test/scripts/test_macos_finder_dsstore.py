"""Pin the Finder .DS_Store Entries artifact in scripts/artifacts/macosFinderDSStore.py.

Every .DS_Store below is built by the test from Wim Lewis's description of the format; no
record comes from a real device. Expected dates are written out as literals.
"""
import fnmatch
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from admin.test.scripts.test_macos_trash import leaf, record, store  # pylint: disable=wrong-import-position
from scripts.artifacts import macosFinderDSStore as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
# 2025-11-26 19:42:09.982 UTC as a little-endian double of seconds since 2001-01-01.
MODD = struct.pack('<d', 785878929.982)


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root) for name in names)


class HelperTest(unittest.TestCase):
    # pylint: disable=protected-access
    def test_date(self):
        self.assertEqual(artifact._date('blob', MODD), datetime(2025, 11, 26, 19, 42, 9, 982000, tzinfo=UTC))
        # A dutc value counts 1/65536 seconds from 1904-01-01.
        self.assertEqual(artifact._date('dutc', 65536 * 86400), datetime(1904, 1, 2, tzinfo=UTC))
        self.assertEqual(artifact._date('blob', b'\x01\x02\x03'), '010203')
        self.assertEqual(artifact._date('blob', struct.pack('<d', float('nan'))), struct.pack('<d', float('nan')).hex())
        self.assertEqual(artifact._date('blob', struct.pack('<d', 1e300)), struct.pack('<d', 1e300).hex())
        self.assertEqual(artifact._date('long', 5), 5)


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged = []
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.image = os.path.join(self.root, 'image')

    def put(self, relative, data):
        path = os.path.join(self.image, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)

    def run_artifact(self, extra=()):
        return artifact.macosDSStoreEntries.__wrapped__(Context(self.image, walk(self.image) + list(extra)))

    def test_one_row_per_name_from_both_copies(self):
        data = store([leaf(record('.', 'vSrn', 'long', 1),
                           record('Old.dmg', 'Iloc', 'blob', bytes(16)),
                           record('Old.dmg', 'cmmt', 'ustr', 'from Bob'),
                           record('Old.dmg', 'ptbL', 'ustr', 'System/Volumes/Data/Users/u/Downloads/'),
                           record('Old.dmg', 'ptbN', 'ustr', 'Old.dmg'),
                           record('Project', 'lg1S', 'comp', 8536443172),
                           record('Project', 'modD', 'blob', MODD),
                           record('Project', 'moDD', 'blob', MODD),
                           record('Project', 'ph1S', 'comp', 8318304256),
                           record('Scans', 'modD', 'blob', MODD))])
        self.put('Users/u/Documents/.DS_Store', data)
        self.put('System/Volumes/Data/Users/u/Documents/.DS_Store', data)
        # An AppleDouble file beside a store is not read as one.
        self.put('Users/u/Documents/._.DS_Store', b'\x00\x05\x16\x07')
        headers, rows, source = self.run_artifact()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['moDD (UTC)', 'Item Name', 'Logical Size', 'Comment', 'Put Back Name', 'Put Back Location',
                          'Structure Codes', 'Source File'])
        both = 'System/Volumes/Data/Users/u/Documents/.DS_Store\nUsers/u/Documents/.DS_Store'
        at = datetime(2025, 11, 26, 19, 42, 9, 982000, tzinfo=UTC)
        self.assertEqual(rows, [
            ('', '.', '', '', '', '', 'vSrn', both),
            ('', 'Old.dmg', '', 'from Bob', 'Old.dmg', 'System/Volumes/Data/Users/u/Downloads/', 'Iloc, cmmt, ptbL, ptbN', both),
            (at, 'Project', 8536443172, '', '', '', 'lg1S, moDD, modD, ph1S', both),
            # modD stands in when moDD is absent.
            (at, 'Scans', '', '', '', '', 'modD', both)])
        self.assertEqual(len(source.split('\n')), 2)
        self.assertEqual(self.logged, [])

    def test_older_codes_and_a_dutc_date(self):
        # Stored out of order, so Structure Codes has to be sorted to read 'logS, moDD'.
        self.put('Volume/.DS_Store', store([leaf(record('Photos', 'moDD', 'dutc', 65536 * 86400),
                                                  record('Photos', 'logS', 'comp', 4096),
                                                  # A size or comment stored as another type is not reported.
                                                  record('Odd', 'lg1S', 'blob', b'\x01'),
                                                  record('Odd', 'cmmt', 'blob', b'\x02'))]))
        _, rows, _ = self.run_artifact()
        self.assertEqual(rows, [(datetime(1904, 1, 2, tzinfo=UTC), 'Photos', 4096, '', '', '', 'logS, moDD', 'Volume/.DS_Store'),
                                ('', 'Odd', '', '', '', '', 'cmmt, lg1S', 'Volume/.DS_Store')])

    def test_unreadable_and_incomplete_files_are_logged(self):
        self.put('a/.DS_Store', b'\x00\x00\x00\x01Nope' + bytes(64))
        self.put('b/.DS_Store', store([leaf(record('x', 'Iloc', 'blob', bytes(16)))], declared=2))
        self.put('c/.DS_Store', store([leaf()]))
        # A seeker can hand back a directory, or a path that cannot be opened.
        os.makedirs(os.path.join(self.image, 'dir/.DS_Store'))
        _, rows, source = self.run_artifact([os.path.join(self.image, 'dir/.DS_Store'),
                                             os.path.join(self.image, 'm/.DS_Store')])
        self.assertEqual(rows, [('', 'x', '', '', '', '', 'Iloc', 'b/.DS_Store')])
        self.assertEqual(source, os.path.join(self.image, 'b/.DS_Store'))
        self.assertEqual(self.logged[:2], ['Finder .DS_Store Entries: a/.DS_Store could not be read: no Bud1 header',
                                           'Finder .DS_Store Entries: b/.DS_Store declares 2 records and 1 were read'])
        self.assertEqual(len(self.logged), 3)
        self.assertTrue(self.logged[2].startswith('Finder .DS_Store Entries: m/.DS_Store could not be opened: '), self.logged[2])

    def test_declared_paths(self):
        patterns = artifact.__artifacts_v2__['macosDSStoreEntries']['paths']
        for path in ('Macintosh HD - Data/Users/u/Desktop/.DS_Store', 'r/.DS_Store', 'Untitled/.Trashes/501/.DS_Store'):
            self.assertTrue(any(fnmatch.fnmatch(path, p) for p in patterns), path)
        self.assertEqual(artifact.macosDSStoreEntries.__name__, 'macosDSStoreEntries')


if __name__ == '__main__':
    unittest.main()
