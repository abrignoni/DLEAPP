"""Pin the QuickLook artifacts in scripts/artifacts/macosQuickLook.py.

Every database, archive and bitmap below is built by the test with the table definitions a
macOS 11 cache carries; no row comes from a real device. Expected values are literals.
"""
import fnmatch
import hashlib
import os
import pathlib
import plistlib
import shutil
import sqlite3
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosQuickLook as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
CACHE = 'private/var/folders/gh/abc/C/com.apple.quicklook.ThumbnailsAgent/com.apple.QuickLook.thumbnailcache/'
BASIC = 'CREATE TABLE basic_files (fileId INTEGER PRIMARY KEY, fsid INTEGER, version BLOB)'
THUMBS = ('CREATE TABLE thumbnails (file_id INTEGER, size REAL, icon_mode INTEGER, hit_count INTEGER, '
          'last_hit_date REAL, width INTEGER, height INTEGER, bitspercomponent INTEGER, bitsperpixel INTEGER, '
          'bytesperrow INTEGER, bitmapinfo INTEGER, bitmapdata_location INTEGER, bitmapdata_length INTEGER, '
          'plistbuffer_location INTEGER, plistbuffer_length INTEGER, flavor INTEGER, content_rect BLOB, '
          'badge_type INTEGER, icon_variant INTEGER, interpolation INTEGER, externalGeneratorDataHash INTEGER)')
CLOUD = ('CREATE TABLE thumbnails( docid integer not null, vol_uuid blob not null, last_hit_date integer not null, '
         'last_seen_path text not null, size integer, PRIMARY KEY (docid, vol_uuid))')
FILE_A, FILE_B, FILE_C = 12885210013, 12885210015, 12884948559
FSID = 72057611217797120


def decorated(file_id):
    """The file ID with the top bit set, as the signed integer SQLite stores."""
    return file_id - (1 << 63)


def version(file_id, generator, modified, size):
    """A QLThumbnailVersion archive as the basic_files rows carry it."""
    uid = plistlib.UID
    return plistlib.dumps({
        '$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': {'root': uid(1)},
        '$objects': ['$null', {'$class': uid(7), 'g': uid(2), 'vi': uid(4), 'm': uid(5), 'i': file_id, 'v': uid(3), 's': size},
                     generator, '928.2', b'\x9d\xb3\x04\x00', {'NS.time': modified, '$class': uid(6)},
                     {'$classname': 'NSDate', '$classes': ['NSDate', 'NSObject']},
                     {'$classname': 'QLThumbnailVersion', '$classes': ['QLThumbnailVersion', 'NSObject']}]},
        fmt=plistlib.PlistFormat.FMT_BINARY)


def pixels(png):
    """(width, height, rows of RGBA tuples) of a PNG this module wrote (filter 0 on every row)."""
    width, height = struct.unpack('>II', png[16:24])
    data, offset = b'', 8
    while offset < len(png):
        length = struct.unpack('>I', png[offset:offset + 4])[0]
        if png[offset + 4:offset + 8] == b'IDAT':
            data += png[offset + 8:offset + 8 + length]
        offset += 12 + length
    raw = zlib.decompress(data)
    rows = []
    for y in range(height):
        line = raw[y * (1 + width * 4):(y + 1) * (1 + width * 4)]
        assert line[0] == 0
        rows.append([tuple(line[1 + x * 4:5 + x * 4]) for x in range(width)])
    return width, height, rows


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
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.logged, self.media = [], []
        for name, target in (('logfunc', self.logged.append), ('check_in_embedded_media', self.check_in)):
            patcher = patch.object(artifact, name, target)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.image = os.path.join(self.root, 'image')

    def check_in(self, source, data, name='', force_type=None, force_extension=None):
        # The real check-in keys a media item on the SHA-1 of its data, so identical copies share one.
        self.media.append((os.path.relpath(source, self.image), data, name, force_type, force_extension))
        return 'media:' + hashlib.sha1(data).hexdigest()

    def database(self, relative, statements):
        path = os.path.join(self.image, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with sqlite3.connect(path) as db:
            for statement, *rows in statements:
                if rows:
                    db.executemany(statement, rows)
                else:
                    db.execute(statement)
        db.close()

    def put(self, relative, data):
        path = os.path.join(self.image, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)

    def run_thumbnails(self, extra=()):
        return artifact.macosQuickLookThumbnails.__wrapped__(Context(self.image, walk(self.image) + list(extra)))

    def test_thumbnails_joined_to_their_files_and_rendered(self):
        # A 2 x 2 bitmap, stored B, G, R, A with the colour premultiplied by alpha, then 8 bytes
        # of padding, and a second bitmap whose layout is not read.
        bitmap = bytes((0, 0, 255, 255, 255, 0, 0, 255, 0, 128, 0, 255, 32, 32, 64, 128))
        data = bytes(8) + bitmap + bytes(8) + bytes(16)
        row = (THUMBS.split(' (')[0].replace('CREATE TABLE', 'INSERT INTO') +
               ' (file_id, size, hit_count, last_hit_date, width, height, bitspercomponent, bitsperpixel, '
               'bytesperrow, bitmapinfo, bitmapdata_location, bitmapdata_length) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        index = [(BASIC,), (THUMBS,),
                 ('INSERT INTO basic_files VALUES (?, ?, ?)',
                  (FILE_A, FSID, version(FILE_A, 'com.apple.qlgenerator.image', 634496585.0, 347407)),
                  (FILE_B, FSID, b'not a plist'),
                  (FILE_C, FSID, version(FILE_C, 'com.apple.qlgenerator.pdf', 607052949.0, 846528))),
                 (row, (decorated(FILE_A), 64.0, 3, 635455701.06487, 2, 2, 8, 32, 8, 0x2002, 8, 16),
                  (decorated(FILE_B), 16.0, 1, 635455527.366853, 2, 2, 8, 32, 8, 0x2001, 32, 16),
                  # A thumbnail whose file has no basic_files row, and one past the end of the data.
                  (decorated(99), 16.0, 1, 635455600.0, 2, 2, 8, 32, 8, 0x2002, 40, 16))]
        for root in ('', 'System/Volumes/Data/'):
            self.database(root + CACHE + 'index.sqlite', index)
            self.put(root + CACHE + 'thumbnails.data', data)
        headers, rows, source = self.run_thumbnails()
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Last Hit (UTC)', 'File Modified (UTC)', 'Thumbnail', 'File ID', 'File Size', 'Generator',
                          'Version (as stored)', 'Thumbnail Size (as stored)', 'Width', 'Height', 'Hit Count (as stored)',
                          'Volume ID (as stored)', 'Source File'])
        both = 'System/Volumes/Data/' + CACHE + 'index.sqlite\n' + CACHE + 'index.sqlite'
        IMAGE = 'media:' + hashlib.sha1(self.media[0][1]).hexdigest() if self.media else None
        self.assertEqual(rows, [
            (datetime(2021, 2, 19, 19, 25, 27, 366853, tzinfo=UTC), '', '', FILE_B, '', '', '', 16.0, 2, 2, 1, FSID, both),
            (datetime(2021, 2, 19, 19, 26, 40, tzinfo=UTC), '', '', 99, '', '', '', 16.0, 2, 2, 1, '', both),
            (datetime(2021, 2, 19, 19, 28, 21, 64870, tzinfo=UTC), datetime(2021, 2, 8, 17, 3, 5, tzinfo=UTC), IMAGE,
             FILE_A, 347407, 'com.apple.qlgenerator.image', '928.2', 64.0, 2, 2, 3, FSID, both),
            # A file versioned without a thumbnail still gets a row.
            ('', datetime(2020, 3, 28, 1, 49, 9, tzinfo=UTC), '', FILE_C, 846528, 'com.apple.qlgenerator.pdf', '928.2',
             '', '', '', '', FSID, both)])
        # Identical copies check the image in twice under one name; the report keeps one.
        self.assertEqual({(m[0].split('com.apple.QuickLook')[1], m[2], m[3], m[4]) for m in self.media},
                         {('.thumbnailcache/thumbnails.data', f'{FILE_A}_64.png', 'image/png', 'png')})
        width, height, image = pixels(self.media[0][1])
        self.assertEqual((width, height), (2, 2))
        # Red, blue, green, and a half-transparent pixel whose colour is divided back out of alpha.
        self.assertEqual(image, [[(255, 0, 0, 255), (0, 0, 255, 255)], [(0, 128, 0, 255), (128, 64, 64, 128)]])
        self.assertEqual(sorted(source.split('\n')), sorted(os.path.join(self.image, r + CACHE + f) for r in ('', 'System/Volumes/Data/')
                                                            for f in ('index.sqlite', 'thumbnails.data')))
        self.assertEqual(sorted(self.logged), sorted(
            f'QuickLook Thumbnails: 1 thumbnail(s) in {r}{CACHE}index.sqlite not rendered: {reason}'
            for r in ('', 'System/Volumes/Data/')
            for reason in ('a bitmap layout other than 8-bit BGRA with premultiplied alpha',
                           'a bitmap that does not fit its stated size or thumbnails.data')))

    def test_older_layout_and_empty_caches(self):
        self.database('a/' + CACHE + 'index.sqlite', [('CREATE TABLE files (folder TEXT, file_name TEXT, fs_id TEXT, version BLOB)',)])
        # A cache with the tables and no row is not listed as a source.
        self.database('b/' + CACHE + 'index.sqlite', [(BASIC,), (THUMBS,)])
        folder = os.path.join(self.image, 'c/' + CACHE + 'index.sqlite')
        os.makedirs(folder)
        _, rows, source = self.run_thumbnails([folder])
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, [f'QuickLook Thumbnails: no basic_files and thumbnails tables in a/{CACHE}index.sqlite'])

    def test_cloud_thumbnails(self):
        volume = bytes.fromhex('0a81f3b151d93335b3e3169c3640360d')
        self.database(CACHE + 'cloudthumbnails.db', [(CLOUD,), ('INSERT INTO thumbnails VALUES (?, ?, ?, ?, ?)',
                                                              (4, volume, 1610914665.889392, '/Users/u/Library/Mobile Documents/b.pdf.icloud', 80381),
                                                              (3, volume, 1610914665.96485, '/Users/u/Library/Mobile Documents/a.pdf.icloud', 37905))])
        self.database('x/' + CACHE + 'cloudthumbnails.db', [('CREATE TABLE other (a TEXT)',)])
        headers, rows, source = artifact.macosQuickLookCloudThumbnails.__wrapped__(Context(self.image, walk(self.image)))
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Last Hit (UTC)', 'Last Seen Path', 'Doc ID', 'Volume UUID', 'Size (as stored)', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2021, 1, 17, 20, 17, 45, 889392, tzinfo=UTC), '/Users/u/Library/Mobile Documents/b.pdf.icloud', 4,
             '0A81F3B1-51D9-3335-B3E3-169C3640360D', 80381, CACHE + 'cloudthumbnails.db'),
            (datetime(2021, 1, 17, 20, 17, 45, 964850, tzinfo=UTC), '/Users/u/Library/Mobile Documents/a.pdf.icloud', 3,
             '0A81F3B1-51D9-3335-B3E3-169C3640360D', 37905, CACHE + 'cloudthumbnails.db')])
        self.assertEqual(source, os.path.join(self.image, CACHE + 'cloudthumbnails.db'))
        self.assertEqual(self.logged, [f'QuickLook Cloud Thumbnails: no thumbnails table in x/{CACHE}cloudthumbnails.db'])

    def test_declared_paths(self):
        meta = artifact.__artifacts_v2__
        for key, names in (('macosQuickLookThumbnails', ('index.sqlite', 'index.sqlite-wal', 'thumbnails.data')),
                           ('macosQuickLookCloudThumbnails', ('cloudthumbnails.db', 'cloudthumbnails.db-wal'))):
            for name in names:
                for prefix in ('p2/Macintosh HD - Data/' + CACHE, 'private/var/folders/xy/z/C/com.apple.QuickLook.thumbnailcache/'):
                    self.assertTrue(any(fnmatch.fnmatch(prefix + name, p) for p in meta[key]['paths']), prefix + name)
        self.assertEqual((artifact.macosQuickLookThumbnails.__name__, artifact.macosQuickLookCloudThumbnails.__name__),
                         ('macosQuickLookThumbnails', 'macosQuickLookCloudThumbnails'))


if __name__ == '__main__':
    unittest.main()
