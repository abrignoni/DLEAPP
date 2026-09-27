"""Pin the .DS_Store reader in scripts/macos_dsstore.py and the Trash Put Back artifact.

Every .DS_Store below is built by the test from Wim Lewis's description of the format; no
record comes from a real device.
"""
import fnmatch
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_dsstore  # pylint: disable=wrong-import-position
from scripts.artifacts import macosTrash as artifact  # pylint: disable=wrong-import-position


def record(name, code, kind, value):
    out = struct.pack('>I', len(name)) + name.encode('utf-16-be') + code.encode() + kind.encode()
    if kind in ('long', 'shor'):
        return out + struct.pack('>I', value)
    if kind == 'bool':
        return out + bytes([value])
    if kind == 'type':
        return out + value.encode()
    if kind in ('comp', 'dutc'):
        return out + struct.pack('>Q', value)
    if kind == 'blob':
        return out + struct.pack('>I', len(value)) + value
    if kind == 'ustr':
        return out + struct.pack('>I', len(value)) + value.encode('utf-16-be')
    return out + b'????'


def leaf(*records):
    return struct.pack('>II', 0, len(records)) + b''.join(records)


def internal(pairs, rightmost):
    return struct.pack('>II', rightmost, len(pairs)) + b''.join(struct.pack('>I', child) + rec for child, rec in pairs)


def store(nodes, root=2, declared=None, header=b'\x00\x00\x00\x01'):
    """A .DS_Store file: block 0 the allocator, block 1 the B-tree master, nodes from block 2."""
    body = bytearray(0x1000 * (len(nodes) + 1))
    addresses = [0x800 | 11, 0x20 | 5] + [(0x1000 * (i + 1)) | 12 for i in range(len(nodes))]
    body[0:32] = b'Bud1' + struct.pack('>III', 0x800, 0x800, 0x800) + bytes(16)
    if declared is None:
        declared = sum(struct.unpack_from('>I', n, 4)[0] for n in nodes)
    body[0x20:0x34] = struct.pack('>IIIII', root, 0, declared, len(nodes), 0x1000)
    info = struct.pack('>II', len(addresses), 0) + b''.join(struct.pack('>I', a) for a in addresses)
    info += bytes(4 * (256 - len(addresses))) + struct.pack('>I', 1) + b'\x04DSDB' + struct.pack('>I', 1)
    info += bytes(4 * 32)
    body[0x800:0x800 + len(info)] = info
    for i, node in enumerate(nodes):
        body[0x1000 * (i + 1):0x1000 * (i + 1) + len(node)] = node
    return header + bytes(body)


ILOC = bytes.fromhex('00000041000000 2effffffffffff0000'.replace(' ', ''))


class ReaderTest(unittest.TestCase):
    def test_every_data_type_in_one_leaf(self):
        data = store([leaf(record('.', 'vSrn', 'long', 1), record('.', 'lsvt', 'shor', 12), record('.', 'dscl', 'bool', 1),
                           record('.', 'vstl', 'type', 'Nlsv'), record('.', 'lg1S', 'comp', 2 ** 40),
                           record('.', 'moDD', 'dutc', 0x0000_D9E6_0000_0000), record('a.jpg', 'Iloc', 'blob', ILOC),
                           record('a.jpg', 'ptbL', 'ustr', 'Users/u/Desktop/'), record('a.jpg', 'ptbN', 'ustr', 'a.jpg'))])
        records, declared = macos_dsstore.read_ds_store(data)
        self.assertEqual(declared, 9)
        self.assertEqual(records, [('.', 'vSrn', 'long', 1), ('.', 'lsvt', 'shor', 12), ('.', 'dscl', 'bool', 1),
                                   ('.', 'vstl', 'type', 'Nlsv'), ('.', 'lg1S', 'comp', 2 ** 40),
                                   ('.', 'moDD', 'dutc', 0x0000_D9E6_0000_0000), ('a.jpg', 'Iloc', 'blob', ILOC),
                                   ('a.jpg', 'ptbL', 'ustr', 'Users/u/Desktop/'), ('a.jpg', 'ptbN', 'ustr', 'a.jpg')])

    def test_an_internal_node_is_walked_in_order(self):
        # Block 2 is the root: its one record sits between the leaf in block 3 and the
        # rightmost leaf in block 4.
        data = store([internal([(3, record('m', 'ptbN', 'ustr', 'm'))], 4),
                      leaf(record('a', 'ptbN', 'ustr', 'a'), record('b', 'ptbN', 'ustr', 'b')),
                      leaf(record('x', 'ptbN', 'ustr', 'x'))], declared=4)
        records, declared = macos_dsstore.read_ds_store(data)
        self.assertEqual([r[0] for r in records], ['a', 'b', 'm', 'x'])
        self.assertEqual(declared, 4)

    def test_malformed_files_raise(self):
        good = store([leaf(record('a', 'ptbN', 'ustr', 'a'))])
        cases = {
            'no header': b'\x00\x00\x00\x01Nope' + good[8:],
            'offsets disagree': good[:16] + struct.pack('>I', 0x900) + good[20:],
            'unknown type': store([leaf(record('a', 'ptbN', 'xxxx', 'a'))]),
            'node loop': store([internal([(2, record('m', 'ptbN', 'ustr', 'm'))], 2)]),
            'runs past its block': store([struct.pack('>II', 0, 1) + struct.pack('>I', 5000)]),
            'block past the end': store([leaf(record('a', 'ptbN', 'ustr', 'a'))])[:0x1004],
            'too short': good[:20],
        }
        for label, data in cases.items():
            with self.assertRaises(macos_dsstore.DSStoreError, msg=label):
                macos_dsstore.read_ds_store(data)


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


class ArtifactTest(unittest.TestCase):
    TRASH = 'Users/u/.Trash/.DS_Store'
    FIRM = 'System/Volumes/Data/Users/u/.Trash/.DS_Store'

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

    def run_artifact(self):
        return artifact.macosTrashPutBack.__wrapped__(Context(self.image, walk(self.image)))

    def test_put_back_rows_from_both_copies(self):
        data = store([leaf(record('a 10.53.21.jpg', 'Iloc', 'blob', ILOC),
                           record('a 10.53.21.jpg', 'ptbL', 'ustr', 'Users/u/Desktop/'),
                           record('a 10.53.21.jpg', 'ptbN', 'ustr', 'a.jpg'),
                           record('b.txt', 'ptbL', 'ustr', 'Users/u/Documents/'),
                           record('c.app', 'Iloc', 'blob', ILOC),
                           # A put-back code stored as some other data type is not read as text.
                           record('d.bin', 'ptbL', 'blob', b'Users/u/'))])
        self.put(self.TRASH, data)
        self.put(self.FIRM, data)
        headers, rows, source = self.run_artifact()
        self.assertEqual(headers, ('Item Name', 'Put Back Name', 'Put Back Location', 'Source File'))
        both = self.FIRM + '\n' + self.TRASH
        # A record with no put-back structure (c.app) or a non-text one (d.bin) is not reported;
        # a missing ptbN is blank.
        self.assertEqual(rows, [('a 10.53.21.jpg', 'a.jpg', 'Users/u/Desktop/', both),
                                ('b.txt', '', 'Users/u/Documents/', both)])
        self.assertEqual(source.split('\n'), sorted(os.path.join(self.image, p) for p in (self.FIRM, self.TRASH)))
        self.assertEqual(self.logged, [])

    def test_unreadable_and_incomplete_files_are_logged(self):
        self.put(self.TRASH, b'\x00\x00\x00\x01Nope' + bytes(64))
        self.put('Users/v/.Trash/.DS_Store', store([leaf(record('d', 'ptbN', 'ustr', 'd'))], declared=3))
        self.put('Users/w/.Trash/.DS_Store', store([leaf(record('e', 'Iloc', 'blob', ILOC))]))
        # A trashed item beside the stores is not read as one.
        self.put('Users/w/.Trash/e.jpg', b'\xff\xd8\xff\xe0')
        _, rows, source = self.run_artifact()
        self.assertEqual(rows, [('d', 'd', '', 'Users/v/.Trash/.DS_Store')])
        # Only the copy that yielded a row is cited.
        self.assertEqual(source, os.path.join(self.image, 'Users/v/.Trash/.DS_Store'))
        self.assertEqual(self.logged, [
            'Trash Put Back: Users/u/.Trash/.DS_Store could not be read: no Bud1 header',
            'Trash Put Back: Users/v/.Trash/.DS_Store declares 3 records and 1 were read'])

    def test_declared_paths(self):
        patterns = artifact.__artifacts_v2__['macosTrashPutBack']['paths']
        for path in ('Macintosh HD - Data/Users/u/.Trash/.DS_Store',
                     'r/Users/u/Library/Mobile Documents/com~apple~CloudDocs/.Trash/.DS_Store',
                     'Untitled/.Trashes/501/.DS_Store'):
            self.assertTrue(any(fnmatch.fnmatch(path, p) for p in patterns), path)
        for path in ('r/Users/u/Desktop/.DS_Store', 'r/Users/u/.Trash/a.jpg'):
            self.assertFalse(any(fnmatch.fnmatch(path, p) for p in patterns), path)
        self.assertEqual(artifact.macosTrashPutBack.__name__, 'macosTrashPutBack')


if __name__ == '__main__':
    unittest.main()
