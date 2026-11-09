"""Pin the Office Backstage Folder Cache artifact (scripts/artifacts/officeBackstageCache.py).

The records are built in the shape Office LTSC 2024 wrote on windows11_arm_office_backstage_known_20261109: UTF-16LE
JSON without a byte-order mark, named by the SHA-256 of the folder path plus a backslash, encoded UTF-16LE.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import officeBackstageCache as ob
# pylint: enable=wrong-import-position

LISTED = 134386796210690000      # 2026-11-09 06:33:41.069 UTC
MODIFIED = 134386795359172310    # 2026-11-09 06:32:15.917231 UTC
CACHE = 'Users/{user}/AppData/Local/Microsoft/Office/16.0/BackstageInAppNavCache/MyComputer'


def entry(url, name, modified=MODIFIED, **extra):
    item = {'Url': url, 'DisplayName': name, 'Author': '', 'ResourceId': '', 'RootResourceId': '',
            'LastModified': modified, 'SharingLevelDescription': '', 'OneNoteItem': False, 'RemoteItem': False,
            'ThumbnailUrl': '', 'IsDefaultDrive': False}
    item.update(extra)
    return item


def record(container, folders=(), files=(), listed=LISTED):
    return {'LCID': 1033, 'ContainerUrl': container, 'FetchedUrl': '', 'LastReadOn': listed, 'RetryAfter': 0,
            'ContainerIsDefaultDrive': False, 'ContainerResourceId': '',
            'Metadata': {'FolderCreationAllowed': True, 'FileCreationAllowed': True},
            'Folders': list(folders), 'Files': list(files)}


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def write(root, relative, data):
    path = os.path.join(root, *relative.split('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return path


def cache_file(root, user, rec, name=None):
    name = name or ob.expected_name(rec['ContainerUrl'])
    return write(root, f'{CACHE.format(user=user)}/{name}.json', json.dumps(rec).encode('utf-16-le'))


class HelpersTest(unittest.TestCase):
    def test_filetime(self):
        self.assertEqual(ob.filetime(MODIFIED), datetime(2026, 11, 9, 6, 32, 15, 917231, tzinfo=timezone.utc))
        for value in (0, -1, None, '134386795359172310', True, 1.5):
            self.assertEqual(ob.filetime(value), '')

    def test_expected_name_is_the_hash_measured_on_the_known_data(self):
        # 03CE9E23... is the cache file name Office gave C:\kd_backstage\Documents on the known data.
        self.assertEqual(ob.expected_name('C:\\kd_backstage\\Documents'),
                         '03CE9E2398AC2774F51A54B5730371C60A27186FEC57C6D453DFDFD370DA3047')
        self.assertEqual(ob.expected_name('C:\\x'),
                         hashlib.sha256('C:\\x\\'.encode('utf-16-le')).hexdigest().upper())

    def test_decode_accepts_the_written_encoding_and_others(self):
        rec = record('C:\\d')
        for data in (json.dumps(rec).encode('utf-16-le'), b'\xff\xfe' + json.dumps(rec).encode('utf-16-le'),
                     json.dumps(rec).encode('utf-8'), json.dumps(rec).encode('utf-16-be')):
            self.assertEqual(ob.decode(data), rec)
        self.assertIsNone(ob.decode(b'not json'))
        self.assertIsNone(ob.decode('[1, 2]'.encode('utf-16-le')))

    def test_user_of_reads_the_segment_after_users(self):
        self.assertEqual(ob.user_of('x/Users/kd/AppData/Local/f.json'), 'kd')
        self.assertEqual(ob.user_of('x\\USERS\\kd\\f.json'), 'kd')
        self.assertEqual(ob.user_of('x/home/kd/f.json'), '')


class RowsTest(unittest.TestCase):
    def test_one_row_per_folder_and_file(self):
        counts = Counter()
        rec = record('C:\\d', folders=[entry('C:\\d\\sub', 'sub')], files=[entry('C:\\d\\a.docx', 'a.docx'),
                                                                           entry('C:\\d\\b.png', 'b.png')])
        rows = ob.listing_rows(rec, 'kd', 'MyComputer', counts)
        self.assertEqual([r[3:6] for r in rows], [('Folder', 'sub', 'C:\\d\\sub'), ('File', 'a.docx', 'C:\\d\\a.docx'),
                                                 ('File', 'b.png', 'C:\\d\\b.png')])
        self.assertEqual(rows[0][0], datetime(2026, 11, 9, 6, 33, 41, 69000, tzinfo=timezone.utc))
        self.assertEqual(rows[0][1], datetime(2026, 11, 9, 6, 32, 15, 917231, tzinfo=timezone.utc))
        self.assertEqual({r[2] for r in rows}, {'kd'})
        self.assertEqual({r[6] for r in rows}, {'C:\\d'})
        self.assertFalse(counts)

    def test_an_empty_listing_keeps_one_row(self):
        rows = ob.listing_rows(record('C:\\empty'), 'kd', 'MyComputer', Counter())
        self.assertEqual(rows, [(ob.filetime(LISTED), '', 'kd', ob.NO_ITEMS, '', '', 'C:\\empty', '', '',
                                 'MyComputer')])

    def test_author_and_sharing_are_reported_as_stored(self):
        rec = record('C:\\d', files=[entry('C:\\d\\a.docx', 'a.docx', Author='kd author',
                                           SharingLevelDescription='Shared')])
        row = ob.listing_rows(rec, 'kd', 'loc', Counter())[0]
        self.assertEqual(row[7:10], ('kd author', 'Shared', 'loc'))

    def test_malformed_entries_are_counted_not_fatal(self):
        counts = Counter()
        rec = record('C:\\d', files=['x', entry('C:\\d\\a', 'a')])
        rec['Folders'] = 'nope'
        rows = ob.listing_rows(rec, 'kd', 'loc', counts)
        self.assertEqual([r[4] for r in rows], ['a'])
        self.assertEqual(counts, Counter({'cache files whose Folders is not a list': 1,
                                          'Files entries that are not an object': 1}))


class ProcessorTest(unittest.TestCase):
    def run_artifact(self, files):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        found = [f(root) for f in files]
        found.append(os.path.dirname(found[0]))   # the seekers also return matched folders
        headers, rows, source = ob.officeBackstageCache.__wrapped__(FakeContext(found, root))
        return root, headers, rows, source

    def test_two_users_keep_their_own_rows_and_name_check_is_logged(self):
        a = record('C:\\a', files=[entry('C:\\a\\1.docx', '1.docx')])
        b = record('C:\\b', folders=[entry('C:\\b\\s', 's')])
        logged = []
        original = ob.logfunc
        ob.logfunc = logged.append
        self.addCleanup(setattr, ob, 'logfunc', original)
        root, headers, rows, source = self.run_artifact([
            lambda r: cache_file(r, 'one', a),
            lambda r: cache_file(r, 'two', b),
            lambda r: cache_file(r, 'two', a, name='0' * 64),
            lambda r: write(r, CACHE.format(user='two') + '/broken.json', b'{'),
        ])
        self.assertEqual(headers[0], ('Listed', 'datetime'))
        self.assertEqual(sorted((r[2], r[4]) for r in rows), [('one', '1.docx'), ('two', '1.docx'), ('two', 's')])
        self.assertEqual(len(source.split('\n')), 3)
        self.assertTrue(all(p.startswith(root) for p in source.split('\n')))
        self.assertEqual(logged, ['Office Backstage Folder Cache: 1 cache files that are not a JSON object, '
                                  '1 cache files whose name is not the hash of their ContainerUrl'])


if __name__ == '__main__':
    unittest.main()
