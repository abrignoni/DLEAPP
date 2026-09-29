"""Pin the Thumbnail Cache (freedesktop) artifact (scripts/artifacts/linuxThumbnails.py).

GNOME_LARGE and GNOME_FAIL are two thumbnails GNOME's thumbnail factory (gnome-desktop 44.5, run by Nautilus 50.2.2)
wrote on the lab VM for the known steps of ubuntu2604_arm64_thumbnails: the large thumbnail of a known file named
'café 1.png' and the failure entry for a known file that is not a PNG. The other PNGs are built here, with correct
CRCs unless a test breaks one on purpose.
"""
import hashlib
import os
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxThumbnails as th
# pylint: enable=wrong-import-position

GNOME_LARGE = bytes.fromhex(
    '89504e470d0a1a0a0000000d4948445200000100000000c00806000000ebedbd660000002074455874536f66747761726500'
    '474e4f4d453a3a5468756d626e61696c466163746f72796f4455e000000017744558745468756d623a3a4d54696d65003137'
    '393036353136313328a1674a00000050744558745468756d623a3a5552490066696c653a2f2f2f686f6d652f706172616c6c'
    '656c732f646c656170702d7468756d62732d6b6e6f776e2d32303236303932392f636166254333254139253230312e706e67'
    'a63b97590000024549444154789cedd401110010000031e7041145544d09f25b88ad7dcf1b40d21c409600204c0010260008'
    '1300840900c204006102803001409800204c00102600081300840900c204006102803001409800204c001026000813008409'
    '00c204006102803001409800204c00102600081300840900c204006102803001409800204c00102600081300840900c20400'
    '6102803001409800204c00102600081300840900c204006102803001409800204c00102600081300840900c2040061028030'
    '01409800204c00102600081300840900c204006102803001409800204c00102600081300840900c204006102803001409800'
    '204c00102600081300840900c204006102803001409800204c00102600081300840900c204006102803001409800204c0010'
    '2600081300840900c204006102803001409800204c00102600081300840900c204006102803001409800204c001026000813'
    '00840900c204006102803001409800204c00102600081300840900c204006102803001409800204c00102600081300840900'
    'c204006102803001409800204c00102600081300840900c204006102803001409800204c00102600081300840900c2040061'
    '02803001409800204c00102600081300840900c204006102803001409800204c00102600081300840900c204006102803001'
    '409800204c00102600081300840900c204006102803001409800204c00102600081300840900c20400610280300140980020'
    '4c00102600081300840900c204006102803001409800204c00102600081300840900c20400611f888903827b6cef5b000000'
    '0049454e44ae426082')
GNOME_FAIL = bytes.fromhex(
    '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000002074455874536f66747761726500'
    '474e4f4d453a3a5468756d626e61696c466163746f72796f4455e000000017744558745468756d623a3a4d54696d65003137'
    '393036353136313328a1674a00000049744558745468756d623a3a5552490066696c653a2f2f2f686f6d652f706172616c6c'
    '656c732f646c656170702d7468756d62732d6b6e6f776e2d32303236303932392f62726f6b656e2e706e676d2a46bc000000'
    '0b49444154789c6362000200000f0003dbe248b80000000049454e44ae426082')
CAFE_URI = 'file:///home/parallels/dleapp-thumbs-known-20260929/caf%C3%A9%201.png'
BROKEN_URI = 'file:///home/parallels/dleapp-thumbs-known-20260929/broken.png'


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))


def png(texts=(), width=2, height=3, extra=()):
    """A small PNG with the given (kind, body) text chunks after IHDR."""
    out = th.SIGNATURE + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    for kind, body in texts:
        out += chunk(kind, body)
    for kind, body in extra:
        out += chunk(kind, body)
    return out + chunk(b'IDAT', zlib.compress(b'\0' * (1 + 4 * width) * height)) + chunk(b'IEND', b'')


def text(key, value):
    return (b'tEXt', key.encode('latin-1') + b'\0' + value.encode('latin-1'))


def itext(key, value, compressed=False):
    raw = value.encode('utf-8')
    return (b'iTXt', key.encode('latin-1') + b'\0' + bytes([1 if compressed else 0, 0]) + b'en\0\0' +
            (zlib.compress(raw) if compressed else raw))


def ztext(key, value):
    return (b'zTXt', key.encode('latin-1') + b'\0\0' + zlib.compress(value.encode('latin-1')))


def md5(text_bytes):
    return hashlib.md5(text_bytes).hexdigest()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


class FileInfo:
    def __init__(self, source_path, modification_date):
        self.source_path, self.modification_date = source_path, modification_date


class Seeker:
    def __init__(self):
        self.file_infos = {}


class FakeContext:
    def __init__(self, paths, root, seeker):
        self.paths, self.root, self.seeker = paths, root, seeker

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        return self.seeker


class PngTextTest(unittest.TestCase):
    def test_real_gnome_thumbnails(self):
        keys, width, height, problems = th.png_text(GNOME_LARGE)
        self.assertEqual([(k, v) for k, v, _raw in keys], [('Software', 'GNOME::ThumbnailFactory'),
                                                          ('Thumb::MTime', '1790651613'), ('Thumb::URI', CAFE_URI)])
        self.assertEqual((width, height, problems), (256, 192, []))
        keys, width, height, problems = th.png_text(GNOME_FAIL)
        self.assertEqual(dict((k, v) for k, v, _raw in keys)['Thumb::URI'], BROKEN_URI)
        self.assertEqual((width, height, problems), (1, 1, []))

    def test_ztxt_and_itxt(self):
        data = png([ztext('Thumb::Size', '1234'), itext('Thumb::URI', 'file:///tmp/é.png'),
                    itext('Description', 'compressed text', compressed=True)])
        keys, _w, _h, problems = th.png_text(data)
        self.assertEqual([(k, v) for k, v, _raw in keys], [('Thumb::Size', '1234'), ('Thumb::URI', 'file:///tmp/é.png'),
                                                          ('Description', 'compressed text')])
        self.assertEqual(keys[1][2], 'file:///tmp/é.png'.encode('utf-8'))
        self.assertEqual(problems, [])

    def test_damage(self):
        self.assertEqual(th.png_text(b'GIF89a')[3], ['not a PNG file'])
        good = png([text('Thumb::URI', 'file:///a')])
        broken = bytearray(good)
        broken[40] ^= 0xff
        self.assertTrue(any('CRC' in p for p in th.png_text(bytes(broken))[3]))
        self.assertTrue(any('ends inside' in p for p in th.png_text(good[:45])[3]))
        self.assertEqual(th.png_text(good[:37])[3], ['the file ends inside a chunk header'])

    def test_reading_goes_on_past_a_bad_crc_or_an_undecodable_chunk(self):
        good = png([text('Thumb::URI', 'file:///a'), (b'iTXt', b'K'), text('Software', 's')])
        broken = bytearray(good)
        broken[61] ^= 0xff  # the last byte of the first tEXt chunk's CRC
        keys, _w, _h, problems = th.png_text(bytes(broken))
        self.assertEqual([(k, v) for k, v, _raw in keys], [('Thumb::URI', 'file:///a'), ('Software', 's')])
        self.assertEqual(problems, ['the CRC of the tEXt chunk at offset 33 does not match',
                                    'the iTXt chunk at offset 65 could not be read (index out of range)'])

    def test_text_chunks_are_latin_1(self):
        data = png([(b'tEXt', b'Description\0caf\xe9')])
        self.assertEqual(th.png_text(data)[0], [('Description', 'caf\u00e9', b'caf\xe9')])

    def test_itxt_bytes_that_are_not_utf_8_are_shown(self):
        data = png([(b'iTXt', b'Title\0\0\0en\0\0caf\xff')])
        self.assertEqual(th.png_text(data)[0], [('Title', 'caf\\xff', b'caf\xff')])

    def test_text_after_iend_is_not_read(self):
        data = png([text('Thumb::URI', 'file:///a')]) + chunk(b'tEXt', b'Late\0value')
        self.assertEqual([k for k, _v, _raw in th.png_text(data)[0]], ['Thumb::URI'])

    def test_decompressed_text_is_capped(self):
        data = png([ztext('Big', 'x' * (th.TEXT_LIMIT + 10))])
        keys, _w, _h, problems = th.png_text(data)
        self.assertEqual(len(keys[0][1]), th.TEXT_LIMIT)
        self.assertEqual(problems, [f'the text of the zTXt chunk at offset 33 is longer than {th.TEXT_LIMIT} bytes and '
                                    'was cut there'])
        whole = png([ztext('Big', 'x' * th.TEXT_LIMIT)])
        keys, _w, _h, problems = th.png_text(whole)
        self.assertEqual((len(keys[0][1]), problems), (th.TEXT_LIMIT, []))

    def test_compressed_text_that_ends_early(self):
        stream = zlib.compress(('compressed text ' * 40).encode('latin-1'))[:-8]
        data = png([(b'zTXt', b'Short\0\0' + stream), (b'iTXt', b'Also\0\x01\0en\0\0' + stream)])
        keys, _w, _h, problems = th.png_text(data)
        self.assertEqual([k for k, _v, _raw in keys], ['Short', 'Also'])
        self.assertTrue(keys[0][1].startswith('compressed text'))
        self.assertEqual(len(problems), 2)
        self.assertTrue(all(p.endswith('ends early') for p in problems))
        self.assertIn('zTXt chunk at offset 33', problems[0])


class HelperTest(unittest.TestCase):
    def test_original_path(self):
        self.assertEqual(th.original_path(CAFE_URI), '/home/parallels/dleapp-thumbs-known-20260929/café 1.png')
        self.assertEqual(th.original_path('file://localhost/tmp/a%20b'), '/tmp/a b')
        self.assertEqual(th.original_path('file://server/share/a'), '')
        self.assertEqual(th.original_path('http://example.com/a.png'), '')
        self.assertEqual(th.original_path('trash:///a.png'), '')
        self.assertEqual(th.original_path('FILE:///tmp/x'), '/tmp/x')
        self.assertEqual(th.original_path('file:///tmp/%FF.png'), '/tmp/\\xff.png')
        self.assertEqual(th.original_path('file://LocalHost/tmp/x'), '/tmp/x')
        self.assertEqual(th.original_path('file://[bad/tmp/x'), '')

    def test_cache_folder(self):
        self.assertEqual(th.cache_folder('home/u/.cache/thumbnails/large/a.png'), 'large')
        self.assertEqual(th.cache_folder('home/u/.cache/thumbnails/fail/gnome-thumbnail-factory/a.png'),
                         'fail/gnome-thumbnail-factory')
        self.assertEqual(th.cache_folder('home/u/.thumbnails/normal/a.png'), 'normal')
        self.assertEqual(th.cache_folder('home/u/.cache/thumbnails/a.png'), '')
        self.assertEqual(th.cache_folder('home/u/.cache/thumbnails/other/a.png'), '')
        self.assertEqual(th.cache_folder('home/u/.cache/thumbnails/other/large/a.png'), '')

    def test_split_keys(self):
        keys = [('Thumb::URI', 'file:///a', b'file:///a'), ('Thumb::URI', 'file:///b', b'file:///b'),
                ('Thumb::MTime', '1.5', b'1.5'), ('Thumb::MTime', '1300000000', b'1300000000'), ('Size', '9', b'9')]
        shown, others = th.split_keys(keys)
        self.assertEqual(shown, {'Thumb::URI': ('file:///a', b'file:///a'),
                                 'Thumb::MTime': ('1300000000', b'1300000000')})
        self.assertEqual(others, 'Thumb::URI=file:///b\nThumb::MTime=1.5\nSize=9')
        self.assertEqual(th.split_keys([]), ({}, ''))

    def test_time(self):
        self.assertEqual(th._time('1790651613'), utc(1790651613))  # pylint: disable=protected-access
        for value in ('', 'abc', '-5', '1' * 13):
            self.assertEqual(th._time(value), '')  # pylint: disable=protected-access


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.seeker = Seeker()
        self.logged = []
        self.media = []
        for target, value in (('logfunc', self.logged.append),
                              ('check_in_media', lambda path, name: self.media.append((path, name)) or f'M:{name}')):
            patcher = mock.patch.object(th, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.paths = []
        cache = 'home/u/.cache/thumbnails/'
        self.add(cache + f'large/{md5(CAFE_URI.encode())}.png', GNOME_LARGE, 1790651647)
        self.add(cache + f'fail/gnome-thumbnail-factory/{md5(BROKEN_URI.encode())}.png', GNOME_FAIL, 1790651647)
        utf8 = 'file:///tmp/é.png'
        self.add(cache + f'normal/{md5(utf8.encode())}.png',
                 png([itext('Thumb::URI', utf8), text('Thumb::MTime', 'x'), ztext('Thumb::Size', '99'),
                      text('Software', 'Other Thumbnailer')]))
        self.add(cache + f'x-large/{"0" * 32}.png', png([text('Thumb::URI', 'file:///tmp/b.png')]))
        self.add(cache + 'xx-large/not-a-hash.png', png([text('Thumb::URI', 'file:///tmp/c.png')]))
        self.add(cache + f'normal/{"1" * 32}.png', png([text('Software', 'no uri')]))
        self.add(cache + f'normal/{"2" * 32}.png', b'GIF89a not a png')
        self.add('home/u/.thumbnails/normal/' + md5(b'file:///old/d.png') + '.png',
                 png([text('Thumb::URI', 'file:///old/d.png'), text('Thumb::MTime', '1300000000')]))
        self.add(cache + f'normal/{md5(b"file:///tmp/first.png")}.png',
                 png([text('Thumb::URI', 'file:///tmp/first.png'), text('Thumb::URI', 'file:///tmp/second.png'),
                      text('Thumb::MTime', '1790651613.5'), text('Thumb::MTime', '1790651600')]))
        self.add(cache + 'stray.png', png())
        folder = os.path.join(self.root, 'home', 'u', '.cache', 'thumbnails', 'dir.png')
        os.makedirs(folder)
        self.paths.append(folder)

    def add(self, relative, data, when=None):
        path = os.path.join(self.root, *relative.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        self.paths.append(path)
        if when is not None:
            self.seeker.file_infos[path] = FileInfo(relative, when)
        return path

    def tearDown(self):
        self.tmp.cleanup()

    def run_artifact(self, paths=None):
        return th.freedesktopThumbnails.__wrapped__(FakeContext(paths or self.paths, self.root, self.seeker))

    def rows(self):
        headers, rows, _source = self.run_artifact()
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        return [dict(zip(names, row)) for row in rows]

    def test_headers(self):
        headers, _rows, _source = self.run_artifact()
        self.assertEqual(headers, (('Thumbnail Written (UTC)', 'datetime'), ('Original Modified (UTC)', 'datetime'),
                                   ('Thumbnail', 'media'), 'Original Path', 'Original URI', 'Cache Folder', 'Software',
                                   'Thumbnail Pixels', 'Name Matches URI', 'Other Keys', 'Check', 'Source File'))

    def test_gnome_rows(self):
        rows = {r['Source File']: r for r in self.rows()}
        cafe = rows[f'home/u/.cache/thumbnails/large/{md5(CAFE_URI.encode())}.png']
        self.assertEqual((cafe['Thumbnail Written (UTC)'], cafe['Original Modified (UTC)']), (utc(1790651647), utc(1790651613)))
        self.assertEqual((cafe['Original Path'], cafe['Original URI'], cafe['Cache Folder'], cafe['Software']),
                         ('/home/parallels/dleapp-thumbs-known-20260929/café 1.png', CAFE_URI, 'large',
                          'GNOME::ThumbnailFactory'))
        self.assertEqual((cafe['Thumbnail Pixels'], cafe['Name Matches URI'], cafe['Other Keys'], cafe['Check']),
                         ('256 x 192', 'Yes', '', ''))
        self.assertEqual(cafe['Thumbnail'], f'M:{md5(CAFE_URI.encode())}.png')
        fail = rows[f'home/u/.cache/thumbnails/fail/gnome-thumbnail-factory/{md5(BROKEN_URI.encode())}.png']
        self.assertEqual((fail['Cache Folder'], fail['Thumbnail Pixels'], fail['Name Matches URI']),
                         ('fail/gnome-thumbnail-factory', '1 x 1', 'Yes'))

    def test_other_writers_and_checks(self):
        rows = {r['Source File']: r for r in self.rows()}
        other = rows[f'home/u/.cache/thumbnails/normal/{md5("file:///tmp/é.png".encode())}.png']
        self.assertEqual((other['Name Matches URI'], other['Original Modified (UTC)'], other['Other Keys'], other['Software'],
                          other['Thumbnail Written (UTC)']), ('Yes', '', 'Thumb::MTime=x\nThumb::Size=99',
                                                              'Other Thumbnailer', ''))
        twice = rows[f'home/u/.cache/thumbnails/normal/{md5(b"file:///tmp/first.png")}.png']
        self.assertEqual((twice['Original URI'], twice['Name Matches URI'], twice['Original Modified (UTC)'],
                          twice['Other Keys']),
                         ('file:///tmp/first.png', 'Yes', utc(1790651600),
                          'Thumb::URI=file:///tmp/second.png\nThumb::MTime=1790651613.5'))
        self.assertEqual(rows[f'home/u/.cache/thumbnails/x-large/{"0" * 32}.png']['Name Matches URI'], 'No')
        self.assertEqual(rows['home/u/.cache/thumbnails/xx-large/not-a-hash.png']['Name Matches URI'], 'No')
        self.assertEqual(rows[f'home/u/.cache/thumbnails/normal/{"1" * 32}.png']['Name Matches URI'], '')
        bad = rows[f'home/u/.cache/thumbnails/normal/{"2" * 32}.png']
        self.assertEqual((bad['Check'], bad['Thumbnail Pixels'], bad['Original URI']), ('not a PNG file', '', ''))
        old = rows['home/u/.thumbnails/normal/' + md5(b'file:///old/d.png') + '.png']
        self.assertEqual((old['Cache Folder'], old['Original Path'], old['Original Modified (UTC)']),
                         ('normal', '/old/d.png', utc(1300000000)))

    def test_rows_sorted_and_strays_counted(self):
        rows = self.rows()
        sources = [r['Source File'] for r in rows]
        self.assertEqual(sources, sorted(sources))
        self.assertEqual(len(rows), 9)
        self.assertEqual(self.logged, ['Thumbnail Cache (freedesktop): 1 matched files outside a size folder of the '
                                       'cache, not reported'])
        headers, reversed_rows, _source = self.run_artifact(list(reversed(self.paths)))
        self.assertEqual([r[-1] for r in reversed_rows], sources)
        self.assertEqual(len(headers), 12)

    def test_media_and_sources(self):
        _headers, rows, source = self.run_artifact()
        self.assertEqual(len(self.media), 9)
        self.assertEqual(sorted(source.split('\n')), sorted(path for path, _name in self.media))
        self.assertEqual(len(rows), 9)


if __name__ == '__main__':
    unittest.main()
