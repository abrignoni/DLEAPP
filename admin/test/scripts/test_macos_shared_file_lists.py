"""Pin scripts/artifacts/macosSharedFileLists.py, including .sfl4 files.

The archives below are built for the test with the layout measured on real .sfl3 and .sfl4
files (an NSKeyedArchiver binary plist whose root holds items and properties, each item a
dictionary of Bookmark, CustomItemProperties, uuid and visibility, with Name on some
items). Every name, path and value is invented; none comes from a real device.
"""
import fnmatch
import pathlib
import plistlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import macosSharedFileLists as sfl  # pylint: disable=wrong-import-position

_FOLDER = pathlib.Path('Library', 'Application Support', 'com.apple.sharedfilelist')
_RECENTS = _FOLDER/'com.apple.LSSharedFileList.ApplicationRecentDocuments'


def _item(type_code, body):
    return struct.pack('<II', len(body), type_code) + body + b'\0' * (-len(body) % 4)


def bookmark(path=None, url=None, volume_name=None, volume_path=None, created=None):
    """A minimal 'book' bookmark carrying the items the artifact reads."""
    blob = bytearray()
    entries = []

    def add(item_id, data):
        entries.append((item_id, len(blob) + 4))
        blob.extend(data)

    if path is not None:
        offsets = []
        for part in path.strip('/').split('/'):
            offsets.append(len(blob) + 4)
            blob.extend(_item(0x0101, part.encode()))
        add(0x1004, _item(0x0601, b''.join(struct.pack('<I', o) for o in offsets)))
    if url is not None:
        add(0x1003, _item(0x0101, url.encode()))
    if volume_path is not None:
        add(0x2002, _item(0x0101, volume_path.encode()))
    if volume_name is not None:
        add(0x2010, _item(0x0101, volume_name.encode()))
    if created is not None:
        seconds = (created - datetime(2001, 1, 1, tzinfo=timezone.utc)).total_seconds()
        add(0x1040, _item(0x0400, struct.pack('>d', seconds)))
    toc_offset = len(blob) + 4
    toc = struct.pack('<IIIII', 12 * len(entries) + 8, 0xFFFFFFFE, 1, 0, len(entries))
    toc += b''.join(struct.pack('<III', i, o, 0) for i, o in entries)
    body = struct.pack('<I', toc_offset) + bytes(blob) + toc
    header_size = 48
    header = struct.pack('<4sIII', b'book', header_size + len(body), 0x10040000, header_size)
    return header + b'\0' * (header_size - len(header)) + body


def keyed_archive(root):
    """root archived the way NSKeyedArchiver writes dictionaries, arrays and strings."""
    objects = ['$null']
    classes = {}

    def class_uid(name, parents):
        if name not in classes:
            objects.append({'$classname': name, '$classes': [name] + parents})
            classes[name] = plistlib.UID(len(objects) - 1)
        return classes[name]

    def encode(value):
        if isinstance(value, (bool, int, float)):
            return value
        index = len(objects)
        objects.append(None)
        if isinstance(value, dict):
            keys = [encode(k) for k in value]
            values = [encode(v) for v in value.values()]
            objects[index] = {'NS.keys': keys, 'NS.objects': values,
                              '$class': class_uid('NSDictionary', ['NSObject'])}
        elif isinstance(value, list):
            objects[index] = {'NS.objects': [encode(v) for v in value],
                              '$class': class_uid('NSArray', ['NSObject'])}
        else:
            objects[index] = value
        return plistlib.UID(index)

    top = encode(root)
    return plistlib.dumps({'$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': {'root': top},
                           '$objects': objects}, fmt=plistlib.PlistFormat.FMT_BINARY, sort_keys=False)


def shared_list(*entries):
    items = []
    for name, mark, props in entries:
        item = {'uuid': '00000000-0000-4000-8000-000000000000', 'visibility': 0,
                'Bookmark': mark, 'CustomItemProperties': props}
        if name is not None:
            item['Name'] = name
        items.append(item)
    return keyed_archive({'items': items, 'properties': {
        'com.apple.LSSharedFileList.AppIdentifier': 'com.example.editor',
        'com.apple.LSSharedFileList.MaxAmount': 10}})


class Context:
    """The two calls the artifact makes, over a temporary tree."""

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class PathsTest(unittest.TestCase):
    """The declared globs, matched the way the seekers match them (synthetic root/ prefix)."""

    def matches(self, relative):
        candidate = 'root/' + relative
        return [p for p in sfl.__artifacts_v2__['macosSharedFileLists']['paths']
                if fnmatch.fnmatchcase(candidate, p)]

    def test_each_extension_matches_once(self):
        for extension in ('sfl2', 'sfl3', 'sfl4'):
            for relative in (f'Users/alice/{_FOLDER}/com.apple.LSSharedFileList.RecentDocuments.{extension}',
                             f'Users/alice/{_RECENTS}/com.example.editor.{extension}',
                             f'private/var/root/{_FOLDER}/com.apple.LSSharedFileList.FavoriteItems.{extension}'):
                with self.subTest(relative=relative):
                    self.assertEqual(len(self.matches(relative)), 1)

    def test_other_files_do_not_match(self):
        for relative in (f'Users/alice/{_FOLDER}/com.example.list.sfl',
                         f'Users/alice/{_FOLDER}/com.example.list.sfl4.bak',
                         'Users/alice/Library/Application Support/com.example.other/list.sfl4'):
            with self.subTest(relative=relative):
                self.assertEqual(self.matches(relative), [])


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target in (sfl, macos_plists):
            patcher = patch.object(target, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, relative, data):
        path = self.root/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_sfl4_rows_users_and_duplicate_views(self):
        created = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)
        alice = shared_list(
            ('report.txt', bookmark(path='/Users/alice/Documents/report.txt', volume_name='Macintosh HD',
                                    volume_path='/', created=created), {}),
            (None, bookmark(url='x-apple-tag://Example'),
             {'com.apple.LSSharedFileList.ItemIsHidden': True,
              'com.apple.LSSharedFileList.SpecialItemIdentifier': 'com.example.special'}))
        bob = shared_list(('notes.md', bookmark(path='/Users/bob/notes.md'), {}))
        older = shared_list(('old.txt', bookmark(path='/Users/alice/old.txt'), {}))
        files = [
            self.write(pathlib.Path('Users', 'alice')/_RECENTS/'com.example.editor.sfl4', alice),
            self.write(pathlib.Path('System', 'Volumes', 'Data', 'Users', 'alice')/_RECENTS/'com.example.editor.sfl4',
                       alice),
            self.write(pathlib.Path('Users', 'alice')/_RECENTS/'com.example.editor.sfl3', older),
            self.write(pathlib.Path('Users', 'bob')/_FOLDER/'com.apple.LSSharedFileList.RecentDocuments.sfl4', bob),
            self.write(pathlib.Path('Users', 'bob')/_FOLDER/'com.apple.LSSharedFileList.Broken.sfl4', b'not a plist'),
        ]
        headers, rows, source = sfl.macosSharedFileLists.__wrapped__(Context(self.root, files))
        self.assertEqual(len(headers), 12)
        alice_file = str(pathlib.Path('Users', 'alice')/_RECENTS/'com.example.editor.sfl4')
        older_file = str(pathlib.Path('Users', 'alice')/_RECENTS/'com.example.editor.sfl3')
        bob_file = str(pathlib.Path('Users', 'bob')/_FOLDER/'com.apple.LSSharedFileList.RecentDocuments.sfl4')
        self.assertEqual(sorted(rows, key=lambda r: (r[11], r[1])), sorted([
            ('com.example.editor.sfl4', 0, 'report.txt', '/Users/alice/Documents/report.txt', '',
             'Macintosh HD', '/', created, '', '', 'alice', alice_file),
            ('com.example.editor.sfl4', 1, '', '', 'x-apple-tag://Example', '', '', '',
             'com.example.special', 'Yes', 'alice', alice_file),
            ('com.example.editor.sfl3', 0, 'old.txt', '/Users/alice/old.txt', '', '', '', '', '', '',
             'alice', older_file),
            ('com.apple.LSSharedFileList.RecentDocuments.sfl4', 0, 'notes.md', '/Users/bob/notes.md', '',
             '', '', '', '', '', 'bob', bob_file),
        ], key=lambda r: (r[11], r[1])))
        self.assertEqual(sorted(source.split('\n')), sorted(str(f) for f in (files[0], files[2], files[3])))
        self.assertIn('Shared File Lists: could not read '
                      + str(pathlib.Path('Users', 'bob')/_FOLDER/'com.apple.LSSharedFileList.Broken.sfl4'),
                      self.logged)


if __name__ == '__main__':
    unittest.main()
