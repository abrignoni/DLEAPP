"""Pin how the GVfs metadata artifacts read a tree and a journal. TREE is the home tree and JOURNAL a home
journal that gvfsd-metadata 1.60.0 wrote on a lab VM for known steps, stored zlib-compressed and base64-encoded."""
import base64
import os
import pathlib
import sys
import tempfile
import unittest
import zlib
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxGvfsMetadata as gm
# pylint: enable=wrong-import-position

TREE = zlib.decompress(base64.b64decode(
    'eNq7JZWbWpLIyAACZ0L9MoBUABArgPgrI2U7gBQTEDsDsU5eYmlJZk5psW5mcn6ebkF+cWZJZn4eQ0pOamJBgW52Xn55HkhbAhCnMDAwFgD1t+uDTQabMQmI5wDFOyBCDCD6DJDfA+K45CeX5qbmlRQzuKQWZ5fkF0DUgBy2AYj/AJkTGP5q3g5ILErMyUnNKVYIzkgsSk1RcMvPSUktKmZAqH8AoRiXgAio49LL0oohLtQ1MjAyM7A0NmCAARagshAgBrqbcQXEDMYokFYg3gLluwAxMGwYd0D5wDBizAHiIyB+sm5ufllqil5JRQlDcWkSQyKYlQQmsQBGqBk1hgaW5jpmJuY45OdYWFjqmBqZIIuDqBNo/LMgMgkYiwzpibm5iQwMABqlUbg='))
JOURNAL = zlib.decompress(base64.b64decode(
    'eNrt0b1Kw1AYgOHT2qWDF6DegTRNqSCIblYpuHToULAOaROjNT+lOf0ZxUEnQRE6CQ6Cqzo5iIOLg5Ozg1fiYE6aitAl1dH3gRMSkrz5OHmfb/ndTkrkZ4uPQhyKUDZc1dzm8726aD09nAq95De7ruXJQDcdy2i3Nbu3G2gHnt/3tGKhuFxYWSroRl4OpIgfiO4Jw2nvGSpTDVc9t3G3HTfPUsmajZ9NZz+QYiTte5aQfV+d11U/e7KzELcvfj9vw5LRuNG8lbXXj7m4OUz/bd6Kam7dtI7i3mXCGZuTM9qG637vqXzr3MpxcyZhU3P9nmVG5WmmUNSx9HJeGoy/mZm2EL4frtr66vF13LhKOEXQbejm5H6YljP6abVwlT8X7eG4m5m2O1IWAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP6lLxOi7xw='))
AFTER = zlib.decompress(base64.b64decode(
    'eNp1kj9Lw0AYxi/RwUUEx04ZHJsaa/8iKEhxFp3E6dpcm9hLLuQutZM4OAiKODgILv0ADiIiOAgdFRydnPwADo4ODj7XpHXRg1+ee957krwvyVsuYIoaRK/uyfMAooCl/d7jQwEyDXZAG5TAussZjSJbspYIXRLSRPk8kbYPa0dC+soXIclC3VDsTwz3pRq9iRyBY0KMi63blbnFtGaCezBE/TotEa2f8DfaNEQrCVioJGkw2VUiSjO6+VcIejbu1i7Pyps0ppwzLq1tj8bMtTYEd1ksySRvYCZjATytXrm7WXedXlum/dpFp1hx6ssOGS+d7wP0bbxkzzgAeob3zHvgFHzoZ0IxqnEOvrRv2YHoMbeg+orIpEnoaNccXf9YeqYpyGDJqVfzlVL1n/NhrVbPl4ulcd3MZDbdm/M6e5j2953dp4+s37yZAzNtkcSkiV+BsEj6HB9QeTFjpEODgCL4A+oWan8='))
K = '/Documents/dleapp-gvfs-known-20260930'


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class TreeTest(unittest.TestCase):
    def test_rows(self):
        base = 2841189768
        self.assertEqual(gm.tree_rows(TREE), [
            ('/', 'nautilus-icon-position', '1097,647', 2841189767 + base),
            ('/Desktop/Parallels Shared Folders', 'nautilus-icon-position', '889,524', 16591323 + base),
            (K, None, None, 1 + base),
            (K + '/a.txt', 'dleapp-known', 'beta', 1 + base),
            (K + '/b.txt', None, None, 1 + base),
            (K + '/c-moved.txt', 'dleapp-known', 'gamma', 1 + base),
            (K + '/sub', None, None, 1 + base)])

    def test_list_value_and_merged_keys(self):
        rows = {(r[0], r[1]): r[2] for r in gm.tree_rows(AFTER)}
        self.assertEqual(rows[(K + '/b.txt', 'dleapp-list')], ['three', 'four'])
        self.assertEqual(rows[(K + '/a.txt', 'dleapp-second')], 'epsilon')

    def test_key_outside_the_key_table(self):
        root = int.from_bytes(TREE[16:20], 'big')
        metadata = int.from_bytes(TREE[root + 8:root + 12], 'big')
        damaged = bytearray(TREE)
        damaged[metadata + 4:metadata + 8] = (99).to_bytes(4, 'big')
        with self.assertRaises(gm.GvfsError):
            gm.tree_rows(bytes(damaged))

    def test_entry_pointing_back_is_refused(self):
        root = int.from_bytes(TREE[16:20], 'big')
        children = int.from_bytes(TREE[root + 4:root + 8], 'big')
        looped = bytearray(TREE)
        looped[children + 8:children + 12] = children.to_bytes(4, 'big')
        with self.assertRaises(gm.GvfsError):
            gm.tree_rows(bytes(looped))

    def test_bad_trees(self):
        for data in (b'', b'not a tree', TREE[:40], TREE[:6] + bytes([2]) + TREE[7:]):
            with self.assertRaises((gm.GvfsError, ValueError)):
                gm.tree_rows(data)


class JournalTest(unittest.TestCase):
    def test_rows(self):
        rows, claimed = gm.journal_rows(JOURNAL)
        start = 1790818189
        self.assertEqual(claimed, 9)
        self.assertEqual([(row[0] - start,) + row[1:] for row in rows], [
            (0, 'Set', K + '/a.txt', 'dleapp-known', 'alpha', ''),
            (3, 'Set list', K + '/b.txt', 'dleapp-list', ['one', 'two'], ''),
            (6, 'Set', K + '/a.txt', 'dleapp-known', 'beta', ''),
            (9, 'Unset', K + '/b.txt', 'dleapp-list', '', ''),
            (15, 'Set', K + '/c.txt', 'dleapp-known', 'gamma', ''),
            (15, 'Copy', K + '/c-moved.txt', '', '', K + '/c.txt'),
            (15, 'Remove', K + '/c.txt', '', '', ''),
            (18, 'Set', K + '/sub/d.txt', 'dleapp-known', 'delta', ''),
            (18, 'Remove', K + '/sub/d.txt', '', '', '')])

    def test_stops_at_first_bad_checksum(self):
        rows, _ = gm.journal_rows(JOURNAL)
        sizes, pos = [], 20
        for _ in rows:
            size = int.from_bytes(JOURNAL[pos:pos + 4], 'big')
            sizes.append(pos)
            pos += size
        damaged = bytearray(JOURNAL)
        damaged[sizes[4] + 20] ^= 0xff
        rows, claimed = gm.journal_rows(bytes(damaged))
        self.assertEqual((len(rows), claimed), (4, 9))

    def test_tree_name(self):
        self.assertEqual(gm.JOURNAL_NAME.match('uuid-1234-ab-0123abcd.log').group(1), 'uuid-1234-ab')
        self.assertIsNone(gm.JOURNAL_NAME.match('home'))


class ArtifactTest(unittest.TestCase):
    def test_both_artifacts(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'home', 'a', '.local', 'share', 'gvfs-metadata')
            os.makedirs(folder)
            paths = {}
            damaged = bytearray(JOURNAL)
            damaged[20 + int.from_bytes(JOURNAL[20:24], 'big') + 30] ^= 0xff
            for name, data in (('home', TREE), ('home-2e0d32bb.log', JOURNAL), ('notes.txt', b'plain'),
                               ('label-USB-0badf00d.log', bytes(damaged)),
                               ('root', b'\xda\x1ameta\x01\x00broken')):
                paths[name] = os.path.join(folder, name)
                with open(paths[name], 'wb') as handle:
                    handle.write(data)
            found = [paths['root'], paths['notes.txt'], paths['home-2e0d32bb.log'], paths['home'], folder,
                     paths['label-USB-0badf00d.log']]
            with mock.patch.object(gm, 'logfunc') as log:
                theaders, trows, tsource = gm.linuxGvfsMetadata.__wrapped__(FakeContext(found, root))
                jheaders, jrows, jsource = gm.linuxGvfsMetadataJournal.__wrapped__(FakeContext(found, root))
        src = 'home/a/.local/share/gvfs-metadata/'
        self.assertEqual(theaders, ('Tree', 'Path', 'Key', 'Value', 'Last Changed (as GVfs reads it)', 'Source File'))
        self.assertEqual(trows[0], ('home', '/', 'nautilus-icon-position', '1097,647', '2150-01-25 06:45:35', src + 'home'))
        self.assertEqual(trows[2], ('home', K, '', '', '2060-01-13 03:22:49', src + 'home'))
        self.assertEqual(len(trows), 7)
        self.assertEqual(tsource, paths['home'])
        names = [h[0] if isinstance(h, tuple) else h for h in jheaders]
        self.assertEqual(names, ['Time', 'Tree', 'Operation', 'Path', 'Key', 'Value', 'Source Path', 'Source File'])
        self.assertEqual([r[1:] for r in jrows][1], ('home', 'Set list', K + '/b.txt', 'dleapp-list', 'one\ntwo', '',
                                                     src + 'home-2e0d32bb.log'))
        self.assertEqual(jrows[0][0].timestamp(), 1790818189)
        self.assertEqual(jsource.split('\n'), [paths['home-2e0d32bb.log'], paths['label-USB-0badf00d.log']])
        self.assertEqual([r[1] for r in jrows], ['home'] * 9 + ['label-USB'])
        self.assertEqual([c.args[0] for c in log.call_args_list],
                         [f'GVfs Metadata: could not read {src}root: file shorter than a tree header',
                          'GVfs Metadata Journal: 8 entries after the first that failed its checks, not read'])


if __name__ == '__main__':
    unittest.main()
