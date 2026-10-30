"""Pin the bitmap layouts scripts/artifacts/macosQuickLook.py renders from a QuickLook thumbnails.data.

Every pixel is invented: two pixels per bitmap, opaque red and half-transparent green. The
layouts are written from the CGBitmapInfo fields of Apple's CoreGraphics CGImage.h, and the
keyed archives are built with plistlib, never read back from the reader.
"""
# pylint: disable=protected-access
import io
import pathlib
import plistlib
import struct
import sys
import unittest

from PIL import Image

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosQuickLook as quicklook  # pylint: disable=wrong-import-position

RED, GREEN = (255, 0, 0, 255), (0, 255, 0, 128)


def _pixels(png):
    return list(Image.open(io.BytesIO(png)).convert('RGBA').getdata())


def _bitmap(order, premultiplied=True, depth=8, little=False):
    """Two pixels, components in the given order (letters of RGBAX), as stored."""
    out = b''
    for colour in (RED, GREEN):
        values = dict(zip('RGBA', colour))
        if premultiplied:
            values.update({c: (values[c] * values['A'] + 127) // 255 for c in 'RGB'})
        if 'X' in order:
            values['A'] = 255
        values['X'] = 0
        if depth == 8:
            word = bytes(values[c] for c in order)
            out += word[::-1] if little else word
        else:
            fmt = '<H' if little else '>H'
            out += b''.join(struct.pack(fmt, values[c] * 257) for c in order)
    return out


def _layout(info, depth=8):
    return {'w': 2, 'h': 1, 'bpc': depth, 'bpp': depth * 4, 'bpr': 8 * depth // 8, 'i': info}


def _keyed_archive(root_fields, classname):
    """An NSKeyedArchiver plist whose root object carries root_fields directly."""
    objects = ['$null', dict(root_fields, **{'$class': plistlib.UID(2)}),
               {'$classname': classname, '$classes': [classname, 'NSObject']}]
    return plistlib.dumps({'$version': 100000, '$archiver': 'NSKeyedArchiver',
                           '$top': {'root': plistlib.UID(1)}, '$objects': objects}, fmt=plistlib.PlistFormat.FMT_BINARY)


class RenderTest(unittest.TestCase):
    def _render(self, data, info, depth=8):
        return quicklook._render(data, _layout(info, depth), 0, len(data))

    def test_rgba_premultiplied(self):
        png, reason = self._render(_bitmap('RGBA'), 1)
        self.assertIsNone(reason)
        self.assertEqual(_pixels(png), [RED, (0, 255, 0, 128)])

    def test_argb_premultiplied(self):
        png, _ = self._render(_bitmap('ARGB'), 2)
        self.assertEqual(_pixels(png), [RED, (0, 255, 0, 128)])

    def test_xrgb_is_opaque(self):
        png, _ = self._render(_bitmap('XRGB', premultiplied=False), 6)
        self.assertEqual(_pixels(png), [RED, (0, 255, 0, 255)])

    def test_32_bit_little_endian_premultiplied_first(self):
        png, _ = self._render(_bitmap('ARGB', little=True), 0x2002)
        self.assertEqual(_pixels(png), [RED, (0, 255, 0, 128)])

    def test_16_bit_components_both_byte_orders(self):
        for info, little in ((1, False), (0x3001, False), (0x1001, True)):
            png, reason = self._render(_bitmap('RGBA', depth=16, little=little), info, depth=16)
            self.assertIsNone(reason, info)
            self.assertEqual(_pixels(png), [RED, (0, 255, 0, 128)], info)

    def test_float_components_are_not_rendered(self):
        png, reason = self._render(b'\x00' * 16, 0x1101, depth=16)
        self.assertIsNone(png)
        self.assertIn('0x1101', reason)

    def test_bitmap_past_the_data_is_not_rendered(self):
        data = _bitmap('RGBA')
        png, reason = quicklook._render(data, _layout(1), 4, len(data))
        self.assertIsNone(png)
        self.assertIn('does not fit', reason)


class LayoutTest(unittest.TestCase):
    def test_bitmap_format_archive(self):
        blob = _keyed_archive({'w': 2, 'h': 1, 'bpc': 8, 'bpp': 32, 'bpr': 8, 'i': 0x2002, 'cs': 15},
                              'QLTBitmapFormat')
        row = {'bitmapFormat': blob, 'width': 2, 'height': 1, 'bitspercomponent': None,
               'bitsperpixel': None, 'bytesperrow': None, 'bitmapinfo': None}
        self.assertEqual(quicklook._layout(row),
                         {'w': 2, 'h': 1, 'bpc': 8, 'bpp': 32, 'bpr': 8, 'i': 0x2002, 'cs': 15})

    def test_older_columns(self):
        row = {'bitmapFormat': None, 'width': 2, 'height': 1, 'bitspercomponent': 8,
               'bitsperpixel': 32, 'bytesperrow': 8, 'bitmapinfo': 0x2002}
        layout = quicklook._layout(row)
        self.assertEqual(layout, {'w': 2, 'h': 1, 'bpc': 8, 'bpp': 32, 'bpr': 8, 'i': 0x2002})
        png, reason = quicklook._render(_bitmap('ARGB', little=True), layout, 0, 8)
        self.assertIsNone(reason)
        self.assertEqual(_pixels(png), [RED, (0, 255, 0, 128)])

    def test_no_layout_is_not_rendered(self):
        row = {'bitmapFormat': None, 'width': 2, 'height': 1, 'bitspercomponent': None,
               'bitsperpixel': None, 'bytesperrow': None, 'bitmapinfo': None}
        png, reason = quicklook._render(b'\x00' * 8, quicklook._layout(row), 0, 8)
        self.assertIsNone(png)
        self.assertEqual(reason, 'no bitmap layout')

    def test_unreadable_archive_is_empty(self):
        self.assertEqual(quicklook._archive_values(b'not a plist'), {})


if __name__ == '__main__':
    unittest.main()
