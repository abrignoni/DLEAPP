"""Reader for the Remote Desktop client's bitmap cache files (Cache????.bin), for DLEAPP.

Author: @AlexisBrignoni, Claude.

The layout is read from ANSSI's bmc-tools, bmc-tools.py at
5a4cad32be78b3b874aeec910cb478e04ba3501e
(https://github.com/ANSSI-FR/bmc-tools/blob/5a4cad32be78b3b874aeec910cb478e04ba3501e/bmc-tools.py);
no code is copied. A file begins with the eight bytes RDP8bmp and a NUL, then a 32-bit value
bmc-tools logs as the header version (L8, L48-L51). Tiles follow one after another: two
32-bit values bmc-tools calls key1 and key2, a 16-bit width and a 16-bit height (L63), then
width times height pixels of four bytes each (L64-L66), the first three of which bmc-tools
keeps (L143-L155) and writes into its BMP files with blue first (L370). Here those three bytes
are read as blue, green and red, and the rows as running from the top of the tile.

Pages lay tiles out in the order the file stores them, a fixed number to a row, each in a
64 by 64 cell; the part of a cell a smaller tile does not cover is filled with magenta.
PNG files are written with zlib, 8-bit RGB, one unfiltered scanline per row.
"""

import struct
import zlib
from collections import namedtuple

HEADER = b'RDP8bmp\x00'
CELL = 64
FILL = b'\xff\x00\xff'
Tile = namedtuple('Tile', 'index offset key width height pixels')
_TILE_HEADER = struct.Struct('<IIHH')


def read_cache(data):
    """(header version, tiles, stop) for the bytes of a Cache????.bin file.

    The version is None when the file does not begin with the header. stop is None when the
    tiles run exactly to the end of the file, and otherwise (offset, reason) for the first
    tile header that could not be read.
    """
    if data[:len(HEADER)] != HEADER or len(data) < len(HEADER) + 4:
        return None, [], None
    version, = struct.unpack_from('<I', data, len(HEADER))
    tiles, offset = [], len(HEADER) + 4
    view = memoryview(data)
    while offset < len(data):
        if offset + _TILE_HEADER.size > len(data):
            return version, tiles, (offset, 'a tile header runs past the end of the file')
        _, _, width, height = _TILE_HEADER.unpack_from(data, offset)
        if not (0 < width <= CELL and 0 < height <= CELL):
            return version, tiles, (offset, f'a tile header gives {width} by {height} pixels')
        end = offset + _TILE_HEADER.size + 4 * width * height
        if end > len(data):
            return version, tiles, (offset, "a tile's pixels run past the end of the file")
        tiles.append(Tile(len(tiles), offset, bytes(view[offset:offset + 8]), width, height,
                          view[offset + _TILE_HEADER.size:end]))
        offset = end
    return version, tiles, None


def tile_rgb(pixels):
    """Rows of 8-bit red, green and blue from a tile's stored blue, green, red, other."""
    pixels = bytes(pixels)
    rgb = bytearray(len(pixels) // 4 * 3)
    rgb[0::3] = pixels[2::4]
    rgb[1::3] = pixels[1::4]
    rgb[2::3] = pixels[0::4]
    return bytes(rgb)


def page_rgb(tiles, columns):
    """(width, height, rows of RGB) laying (width, height, rgb) tiles out columns to a row."""
    rows = (len(tiles) + columns - 1) // columns
    width, height = columns * CELL, rows * CELL
    canvas = bytearray(FILL * (width * height))
    for number, (tile_width, tile_height, rgb) in enumerate(tiles):
        left, top = (number % columns) * CELL, (number // columns) * CELL
        span = tile_width * 3
        for row in range(tile_height):
            start = ((top + row) * width + left) * 3
            canvas[start:start + span] = rgb[row * span:(row + 1) * span]
    return width, height, bytes(canvas)


def _chunk(kind, body):
    return (struct.pack('>I', len(body)) + kind + body
            + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF))


def png(width, height, rgb):
    """A PNG of 8-bit RGB rows running from the top."""
    stride = width * 3
    raw = b''.join(b'\x00' + rgb[row * stride:(row + 1) * stride] for row in range(height))
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(raw, 6)) + _chunk(b'IEND', b''))
