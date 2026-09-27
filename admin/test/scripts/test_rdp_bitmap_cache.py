"""Pin the RDP bitmap cache reading in scripts/rdp_bitmap_cache.py and
scripts/artifacts/windowsRdpBitmapCache.py.

Every cache file below is built by the test from the layout the reader documents; no value
comes from a real device. Expected values are written out, never read back from the code.
PNG files are checked with a small reader written here, not with the code under test.
"""
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import rdp_bitmap_cache as rbc  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsRdpBitmapCache as artifact  # pylint: disable=wrong-import-position

HEADER = b'RDP8bmp\x00' + struct.pack('<I', 6)
MAGENTA = (255, 0, 255)


def tile(key1, key2, width, height, colour):
    """A tile whose every pixel is colour (red, green, blue), stored blue, green, red, 0."""
    red, green, blue = colour
    return (struct.pack('<IIHH', key1, key2, width, height)
            + bytes((blue, green, red, 0)) * (width * height))


def read_png(data):
    """(width, height, rows of RGB) from a PNG this module's writer made: signature, IHDR for
    8-bit RGB, IDAT and IEND, each chunk's CRC checked, one filter-0 byte per row."""
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    position, chunks = 8, []
    while position < len(data):
        length, = struct.unpack_from('>I', data, position)
        kind = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        crc, = struct.unpack_from('>I', data, position + 8 + length)
        assert crc == zlib.crc32(kind + body) & 0xFFFFFFFF, kind
        chunks.append((kind, body))
        position += 12 + length
    assert [kind for kind, _ in chunks] == [b'IHDR', b'IDAT', b'IEND']
    width, height, depth, colour, _, _, _ = struct.unpack('>IIBBBBB', chunks[0][1])
    assert (depth, colour) == (8, 2)
    raw = zlib.decompress(chunks[1][1])
    stride = width * 3 + 1
    assert len(raw) == stride * height
    assert all(raw[row * stride] == 0 for row in range(height))
    return width, height, b''.join(raw[row * stride + 1:(row + 1) * stride] for row in range(height))


class ReadCacheTest(unittest.TestCase):
    def test_tiles_in_order(self):
        data = HEADER + tile(1, 2, 64, 64, (10, 20, 30)) + tile(3, 4, 64, 56, (40, 50, 60))
        version, tiles, stop = rbc.read_cache(data)
        self.assertEqual((version, stop), (6, None))
        self.assertEqual([(t.index, t.offset, t.key, t.width, t.height) for t in tiles],
                         [(0, 12, bytes.fromhex('0100000002000000'), 64, 64),
                          (1, 12 + 12 + 16384, bytes.fromhex('0300000004000000'), 64, 56)])
        self.assertEqual(bytes(tiles[1].pixels[:4]), bytes((60, 50, 40, 0)))

    def test_not_a_cache(self):
        self.assertEqual(rbc.read_cache(b'BM' + bytes(40)), (None, [], None))
        self.assertEqual(rbc.read_cache(b''), (None, [], None))
        self.assertEqual(rbc.read_cache(b'RDP8bmp\x00\x06'), (None, [], None))

    def test_header_only(self):
        self.assertEqual(rbc.read_cache(HEADER), (6, [], None))

    def test_stops(self):
        good = tile(1, 2, 2, 2, (1, 2, 3))
        cases = {
            'a tile header runs past the end of the file': HEADER + good + b'\x01\x02',
            'a tile header gives 65 by 64 pixels': HEADER + good + tile(5, 6, 65, 64, (0, 0, 0)),
            'a tile header gives 0 by 64 pixels': HEADER + good + struct.pack('<IIHH', 5, 6, 0, 64),
            "a tile's pixels run past the end of the file": HEADER + good + tile(5, 6, 2, 2, (0, 0, 0))[:-1],
        }
        for reason, data in cases.items():
            with self.subTest(reason):
                version, tiles, stop = rbc.read_cache(data)
                self.assertEqual((version, len(tiles), stop), (6, 1, (12 + len(good), reason)))


class ImageTest(unittest.TestCase):
    def test_tile_rgb_swaps_blue_and_red(self):
        self.assertEqual(rbc.tile_rgb(bytes((1, 2, 3, 4, 5, 6, 7, 8))), bytes((3, 2, 1, 7, 6, 5)))

    def test_png_round_trip(self):
        rgb = bytes(range(2 * 3 * 3))
        self.assertEqual(read_png(rbc.png(3, 2, rgb)), (3, 2, rgb))

    def test_page_layout_and_fill(self):
        red, green = bytes((255, 0, 0)), bytes((0, 255, 0))
        width, height, rgb = rbc.page_rgb([(64, 64, red * 4096), (64, 56, green * 3584),
                                           (64, 64, red * 4096)], 2)
        self.assertEqual((width, height), (128, 128))

        def pixel(x, y):
            start = (y * width + x) * 3
            return tuple(rgb[start:start + 3])
        self.assertEqual([pixel(0, 0), pixel(63, 63), pixel(64, 0), pixel(127, 55),
                          pixel(64, 56), pixel(127, 63), pixel(0, 64), pixel(64, 64)],
                         [(255, 0, 0), (255, 0, 0), (0, 255, 0), (0, 255, 0),
                          MAGENTA, MAGENTA, (255, 0, 0), MAGENTA])


class Context:
    def __init__(self, root, files, seeker=None):
        self.root, self.files, self.seeker = root, files, seeker

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()

    def get_seeker(self):
        return self.seeker


class FileInfo:  # pylint: disable=too-few-public-methods
    def __init__(self, created, modified):
        self.creation_date, self.modification_date = created, modified


class ImageSeeker:  # pylint: disable=too-few-public-methods
    """Stands in for the disk image seeker, which is the one with a stream_list."""
    stream_list = ()

    def __init__(self, infos):
        self.file_infos = infos


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        # The report folder sits under an examiner's own Users folder, as it does on a Mac,
        # so a user taken from the staged path instead of the evidence path shows.
        self.root = pathlib.Path(self.tmp.name)/'Users'/'examiner'/'report'
        self.root.mkdir(parents=True)
        self.logged, self.media = [], []
        patchers = (patch.object(artifact, 'logfunc', self.logged.append),
                    patch.object(artifact, 'check_in_embedded_media', self.check_in))
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        cache = self.root/'Users'/'tester'/'AppData'/'Local'/'Microsoft'/'Terminal Server Client'/'Cache'
        cache.mkdir(parents=True)
        self.files = [cache/'Cache0000.bin', cache/'Cache0001.bin', cache/'bcache24.bmc',
                      cache/'desktop.ini']
        tiles = [tile(i, 100 + i, 64, 64 if i % 2 else 56, (i % 256, 2 * i % 256, 3 * i % 256))
                 for i in range(257)]
        self.files[0].write_bytes(HEADER + b''.join(tiles))
        self.files[1].write_bytes(HEADER + tile(9, 9, 2, 2, (1, 1, 1)) + b'\x00\x01')
        self.files[2].write_bytes(b'')
        self.files[3].write_bytes(b'[.ShellClassInfo]')

    def check_in(self, source, data, name='', force_type=None, force_extension=None):
        self.media.append((pathlib.Path(source).name, name, force_type, force_extension, data))
        return f'ref-{len(self.media)}'

    def test_tile_rows(self):
        headers, rows, sources = artifact.rdpBitmapCacheTiles.__wrapped__(
            Context(self.root, self.files))
        self.assertEqual(headers[0], ('Tile', 'media'))
        self.assertEqual(len(rows), 258)
        self.assertEqual(rows[0], ('ref-1', 'tester', 'Cache0000.bin', 0, 1, 64, 56,
                                   '0000000064000000', 12))
        self.assertEqual(rows[256][2:6], ('Cache0000.bin', 256, 2, 64))
        self.assertEqual(rows[257], ('ref-258', 'tester', 'Cache0001.bin', 0, 1, 2, 2,
                                     '0900000009000000', 12))
        source, name, kind, extension, data = self.media[1]
        self.assertEqual((source, name, kind, extension),
                         ('Cache0000.bin', 'Cache0000.bin_0001.png', 'image/png', 'png'))
        width, height, rgb = read_png(data)
        self.assertEqual((width, height, rgb[:3], len(rgb)), (64, 64, bytes((1, 2, 3)), 64 * 64 * 3))
        self.assertEqual(sources.splitlines(), [str(self.files[0]), str(self.files[1])])
        relative = 'Users/tester/AppData/Local/Microsoft/Terminal Server Client/Cache/'
        self.assertEqual(self.logged, [
            f'RDP Bitmap Cache Tiles: {relative}Cache0000.bin: header version 6, 257 tiles, '
            'read to the end of the file',
            f'RDP Bitmap Cache Tiles: {relative}Cache0001.bin: header version 6, 1 tiles, '
            'reading stopped at offset 40: a tile header runs past the end of the file'])

    def test_page_rows(self):
        _, rows, _ = artifact.rdpBitmapCachePages.__wrapped__(Context(self.root, self.files))
        self.assertEqual([row[1:] for row in rows], [
            ('tester', 'Cache0000.bin', 1, 0, 255, 256),
            ('tester', 'Cache0000.bin', 2, 256, 256, 1),
            ('tester', 'Cache0001.bin', 1, 0, 0, 1)])
        names = [name for _, name, _, _, _ in self.media]
        self.assertEqual(names, ['Cache0000.bin_page001.png', 'Cache0000.bin_page002.png',
                                 'Cache0001.bin_page001.png'])
        width, height, rgb = read_png(self.media[0][4])
        self.assertEqual((width, height), (1024, 1024))
        self.assertEqual(tuple(rgb[(56 * 1024) * 3:(56 * 1024) * 3 + 3]), MAGENTA)
        width, height, _ = read_png(self.media[1][4])
        self.assertEqual((width, height), (1024, 64))

    def test_file_rows_with_times_from_a_disk_image(self):
        created, modified = 1767323045, 1767326645
        seeker = ImageSeeker({str(self.files[0]): FileInfo(created, modified),
                              str(self.files[2]): FileInfo(created, created)})
        headers, rows, _ = artifact.rdpBitmapCacheFiles.__wrapped__(
            Context(self.root, self.files, seeker))
        self.assertEqual(headers[:2], (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime')))
        when = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        later = datetime(2026, 1, 2, 4, 4, 5, tzinfo=timezone.utc)
        self.assertEqual(rows, [
            (when, later, 'tester', 'Cache0000.bin', 12 + 257 * 12 + 128 * 16384 + 129 * 14336,
             6, 257, 2, 'read to the end of the file'),
            ('', '', 'tester', 'Cache0001.bin', 12 + 12 + 16 + 2, 6, 1, 1,
             'reading stopped at offset 40: a tile header runs past the end of the file'),
            (when, when, 'tester', 'bcache24.bmc', 0, '', '', '', 'not read (.bmc cache)'),
        ])

    def test_no_times_from_a_folder_or_archive(self):
        class FolderSeeker:  # pylint: disable=too-few-public-methods
            file_infos = {}
        seeker = FolderSeeker()
        seeker.file_infos = {str(self.files[0]): FileInfo(1767323045, 1767326645)}
        _, rows, _ = artifact.rdpBitmapCacheFiles.__wrapped__(Context(self.root, self.files, seeker))
        self.assertEqual(rows[0][:2], ('', ''))

    def test_a_file_without_the_header(self):
        self.files[1].write_bytes(b'not a cache')
        _, rows, _ = artifact.rdpBitmapCacheFiles.__wrapped__(Context(self.root, self.files))
        self.assertEqual(rows[1][5:], ('', '', '', 'no RDP8bmp header, not read'))
        self.logged.clear()
        _, rows, _ = artifact.rdpBitmapCacheTiles.__wrapped__(Context(self.root, self.files))
        self.assertEqual({row[2] for row in rows}, {'Cache0000.bin'})
        self.assertIn('RDP Bitmap Cache Tiles: Users/tester/AppData/Local/Microsoft/Terminal '
                      'Server Client/Cache/Cache0001.bin: no RDP8bmp header, not read', self.logged)

    def test_declared_paths(self):
        import fnmatch  # pylint: disable=import-outside-toplevel
        for key in ('rdpBitmapCacheFiles', 'rdpBitmapCacheTiles', 'rdpBitmapCachePages'):
            patterns = artifact.__artifacts_v2__[key]['paths']
            path = 'x/Users/a/AppData/Local/Microsoft/Terminal Server Client/Cache/Cache0000.bin'
            self.assertTrue(any(fnmatch.fnmatch(path, p) for p in patterns), key)


if __name__ == '__main__':
    unittest.main()
