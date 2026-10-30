__artifacts_v2__ = {
    "macosQuickLookThumbnails": {
        "name": "QuickLook Thumbnails",
        "description": 'Thumbnails in the QuickLook cache, rendered where the bitmap layout is decoded, with the '
                       'file ID, size and modification '
                       "date recorded for each file, its generator, and the cache's last hit time and hit count.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": (
            (
            (
            (
            (
            (
            'Reads the basic_files and thumbnails tables of index.sqlite and the bitmaps in '
            'thumbnails.data in each com.apple.QuickLook.thumbnailcache folder. Howard Oakley '
            'describes these as the cache in /var/folders on the Data volume of the thumbnails '
            'QuickLook makes, with a type-specific qlgenerator plugin, for Finder windows '
            "(Reference: Howard Oakley, 'A quick look at QuickLook and its problems', "
            'https://eclecticlight.co/2024/04/05/a-quick-look-at-quicklook-and-its-problems/). '
            'Arsenal Recon recorded an entry created on macOS 10.9 when a folder was opened in '
            'the Finder and the file itself was not (Reference: Lodrina Cherne, Arsenal Recon, '
            "'Quick Look Cache Parsing', "
            'https://arsenalrecon.com/insights/quick-look-cache-parsing), so a row is not by '
            'itself evidence that the file was opened. One row is reported per thumbnail, joined '
            "to the basic_files row whose fileId is the thumbnail's file_id with the top bit of "
            'the 64-bit value cleared, which finds a basic_files row for 24 of the 24 thumbnails '
            'on dleapp_macos_bigsur and 134 of the 134 on adams_macbookpro_macos26; a basic_files '
            'row that no thumbnail names gets a row of its own, 3 on dleapp_macos_bigsur and none '
            'on adams_macbookpro_macos26. On dleapp_macos_bigsur neither the tables of index.sqlite nor its '
            "version archives hold a file's name or path. File ID is basic_files.fileId: on "
            'dleapp_macos_bigsur all 15 are the inode number of a file on the Data volume, found '
            'by walking the image, and 2 of the 12 thumbnailed files are now in the iCloud Drive '
            'Trash. File Modified and File Size are the m and s values of the QLThumbnailVersion '
            'archive in basic_files.version, and on dleapp_macos_bigsur all 15 equal, to the '
            'second and to the byte, the modification time and size of the file the File ID '
            "resolves to; Arsenal Recon read the date and size values of the older layout's files "
            "table as the file's last modified date and its size in bytes. Generator is the "
            "archive's g, the bundle identifier of a qlgenerator on every row of "
            "dleapp_macos_bigsur and on 1 of the 134 on adams_macbookpro_macos26, where the other "
            '133 name a com.apple.quicklook.thumbnail extension (Audiovisual, Font, Image, Office '
            "or Text). Version (as stored) is its v: 928.1 on the PDF generator's rows of "
            "dleapp_macos_bigsur and 928.2 on the image generator's, and on "
            "adams_macbookpro_macos26 1018.3.2 on the PDF generator's row and 1 on every extension "
            "row; what v versions is not established. "
            'Last Hit is thumbnails.last_hit_date read as seconds since 2001-01-01 in UTC on this '
            'evidence: on dleapp_macos_bigsur the latest, 2021-02-19 19:28:21, is the '
            "modification time of that cache's index.sqlite-wal to the second, and every Last Hit "
            'falls after the File Modified of its file; on adams_macbookpro_macos26 all 134 fall on '
            'or after the File Modified of their file and before the acquisition start its '
            'acquisition log records. What a hit is, and so what Last Hit and '
            'Hit Count (as stored) record, is not established. Thumbnail is the bitmap at '
            'bitmapdata_location, bitmapdata_length bytes long, in thumbnails.data, which Mari '
            'DeGrazia describes as a raw bitmap that needs those values and the width and height '
            "to be read (Reference: Mari DeGrazia, 'Quicklook thumbnails.data parser', "
            'http://az4n6.blogspot.com/2016/10/quicklook-thumbnailsdata-parser.html), written out '
            'as a PNG. Its layout is read from the bitspercomponent, bitsperpixel, bytesperrow and '
            'bitmapinfo columns of thumbnails, which dleapp_macos_bigsur has, or from the '
            'QLTBitmapFormat keyed archive in the bitmapFormat column (its w, h, bpc, bpp, bpr and '
            'i), which replaces those columns on adams_macbookpro_macos26. bitmapinfo and i are read '
            "as a CGBitmapInfo value using Apple's CoreGraphics CGImage.h: the CGImageAlphaInfo in "
            'the low five bits, the component type in bit 8 and the byte order in bits 12 to 14. '
            'Integer layouts of 8 bits per component in 32-bit pixels and 16 bits per component in '
            '64-bit pixels are rendered, with colour premultiplied by alpha divided back out; a float '
            'layout, any other layout, and a bitmap that does not fit its stated size or '
            'thumbnails.data are not rendered and the run log counts them, and the row is still '
            'reported. All 24 on dleapp_macos_bigsur are 0x2002, kCGImageByteOrder32Little with '
            'kCGImageAlphaPremultipliedFirst: blue, green, red and alpha bytes. For the 12 thumbnails '
            '64 pixels wide there, the red and blue channels as decoded correlate with the image the '
            'File ID resolves to better than with the two swapped on 11, and equally on the 12th, '
            'whose source has the same red and blue value in every pixel. On '
            'adams_macbookpro_macos26, 131 of the 134 are 0x2002, one is 0x1 '
            '(kCGImageAlphaPremultipliedLast: red, green, blue and alpha) at 8 bits per component, '
            'one is 0x1 at 16 bits per component, read most significant byte first, and one is '
            '0x1101, half-float components, which is not rendered. Every rendered 8-bit thumbnail on '
            "both images matched Pillow's raw decoder for its layout (BGRa for 0x2002, RGBa for 0x1) "
            'within one level per channel, and the 16-bit one matched an independent decode within '
            'one level per channel. The colour space the archive names (cs) is not applied, and '
            'values are written to the PNG without colour conversion; on adams_macbookpro_macos26 cs '
            'is the integer 15 on 132 rows, 16 on one and an embedded colour profile on one, and what '
            'the integers stand for is not established. Thumbnail '
            'Size (as stored) is thumbnails.size, 16 or 64 on dleapp_macos_bigsur, where each '
            "thumbnailed file has one of each, and Width and Height are the bitmap's size in "
            'pixels, the same as each other on every row of dleapp_macos_bigsur, where every '
            'thumbnail is square. Volume ID (as stored) is basic_files.fsid, which holds one '
            'value on every row of dleapp_macos_bigsur; what it encodes is not established. The '
            'second cache under private/var/folders/zz holds no row on dleapp_macos_bigsur or on '
            'adams_macbookpro_macos26. The '
            'provider_files and missing_remote_thumbnails tables, which record file-provider items '
            'by item ID without a thumbnail, are not reported. A cache that has the older files '
            'table instead of basic_files is logged and not read; neither image run here carries '
            'one. A row that more than one copy of a cache holds with the same values is reported '
            'once, and Source File lists every copy.'
        )
        )
        )
        )
        )
        ),
        "paths": ('*/com.apple.QuickLook.thumbnailcache/index.sqlite*',
                  '*/com.apple.QuickLook.thumbnailcache/thumbnails.data'),
        "output_types": ["standard"],
        "artifact_icon": "image",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 27 rows",
            "adams_macbookpro_macos26": "macOS 26.2 build 25C56 | 134 rows",
        },
    },
    "macosQuickLookCloudThumbnails": {
        "name": "QuickLook Cloud Thumbnails",
        "description": "Rows of the QuickLook cache's cloudthumbnails.db: the last seen path, document ID, "
                       'volume UUID, a stored size and the last hit time.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": (
            (
            (
            (
            (
            (
            'Reads the thumbnails table of cloudthumbnails.db in each '
            'com.apple.QuickLook.thumbnailcache folder, the folder the QuickLook Thumbnails '
            'artifact reads. No published description of this database was found, so every column '
            'is reported as stored with the units measured here. Last Hit is last_hit_date read '
            'as Unix seconds in UTC on this evidence: on dleapp_macos_bigsur both rows read as '
            '2021-01-17 20:17:45, which read from 2001-01-01 would be in 2052, and fall within a '
            'second of the one missing_remote_thumbnails date that day in the index.sqlite beside '
            'it. What a hit is, and so what Last Hit records, is not established. Last Seen Path '
            'is last_seen_path as stored; on dleapp_macos_bigsur both are iCloud Drive '
            "placeholder files ending in .icloud in the Downloads folder of the user's iCloud "
            'Drive. Doc ID is docid as stored, and what it identifies is not established. Volume '
            'UUID is vol_uuid written as a UUID; on dleapp_macos_bigsur it holds one value on '
            'every row, the Volume UUID the Gatekeeper Scan Cache records on its 52 APFS rows '
            'there. Size (as stored) is size, and what it counts is not established: on '
            'dleapp_macos_bigsur neither value equals the size of the file at Last Seen Path. A '
            'row that more than one copy of the database holds with the same values is reported '
            'once, and Source File lists every copy.'
        )
        )
        )
        )
        )
        ),
        "paths": ('*/com.apple.QuickLook.thumbnailcache/cloudthumbnails.db*',),
        "output_types": ["standard"],
        "artifact_icon": "cloud",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
        },
    },
}

import os
import plistlib
import struct
import zlib
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import (artifact_processor, check_in_embedded_media, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_powerlog import merge_sources

_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
# thumbnails.file_id is basic_files.fileId with the top bit of the 64-bit value set.
_ID_MASK = (1 << 63) - 1
# CGImage.h: CGImageAlphaInfo in the low five bits of the bitmap info, the component type in
# bit 8 (float when set), the byte order in bits 12 to 14 and the pixel format in bits 16 to 19.
# Component positions for each alpha value read here; X is an ignored byte.
_ALPHA_ORDER = {1: 'RGBA', 2: 'ARGB', 3: 'RGBA', 4: 'ARGB', 5: 'RGBX', 6: 'XRGB'}
_PREMULTIPLIED = {1, 2}
_ORDER_DEFAULT, _ORDER_16_LITTLE, _ORDER_32_LITTLE, _ORDER_16_BIG, _ORDER_32_BIG = 0, 0x1000, 0x2000, 0x3000, 0x4000


def _databases(context, name):
    """Staged copies of one file by name (not its sidecars or directories)."""
    return sorted({str(path) for path in context.get_files_found()
                   if os.path.basename(str(path)) == name and not os.path.isdir(str(path))})


def _blank(value):
    return '' if value is None else value


def _time(epoch, value):
    """Seconds since epoch as a UTC datetime; blank for no value and for 0; the stored value
    when it is not a number or out of range."""
    if value is None or value == 0:
        return ''
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    try:
        return epoch + timedelta(seconds=value)
    except (OverflowError, ValueError):
        return value


def _select(path, table, columns):
    """A SELECT list of columns, with NULL standing in for a column this copy lacks."""
    present = {row['name'] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}
    return ', '.join(column if column in present else f'NULL AS {column}' for column in columns)


def _archive_values(blob):
    """The root object of a keyed archive (QLThumbnailVersion, QLTBitmapFormat or an NSDictionary)
    as {key: value}, dates as UTC datetimes; {} when unreadable."""
    try:
        archive = plistlib.loads(bytes(blob))
        objects = archive['$objects']
        root = objects[archive['$top']['root'].data]
    except (plistlib.InvalidFileException, KeyError, IndexError, TypeError, AttributeError, ValueError):
        return {}
    if not isinstance(root, dict):
        return {}
    if 'NS.keys' in root and 'NS.objects' in root:
        # An NSDictionary root: resolve its keys and values.
        keys = [objects[k.data] if isinstance(k, plistlib.UID) and k.data < len(objects) else k
                for k in root['NS.keys']]
        root = dict(zip(keys, root['NS.objects']))
    values = {}
    for key, value in root.items():
        if key == '$class':
            continue
        if isinstance(value, plistlib.UID):
            value = objects[value.data] if value.data < len(objects) else None
        if value == '$null':
            value = None
        if isinstance(value, dict) and 'NS.time' in value:
            value = _time(_MAC_EPOCH, value['NS.time'])
        values[key] = value
    return values


def _png(width, height, rgba):
    """An RGBA image as PNG bytes, with the standard library."""
    rows = b''.join(b'\x00' + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    header = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(rows, 9))
            + chunk(b'IEND', b''))


def _render(data, layout, location, length):
    """PNG bytes of one thumbnail's bitmap, or None and the reason it is not rendered.

    layout holds w, h, bpc, bpp, bpr and i (the CGBitmapInfo value)."""
    width, height, per_row = layout.get('w'), layout.get('h'), layout.get('bpr')
    bpc, bpp, info = layout.get('bpc'), layout.get('bpp'), layout.get('i')
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (bpc, bpp, info)):
        return None, 'no bitmap layout'
    alpha, order = info & 0x1F, info & 0x7000
    if info & 0x100 or info & 0xF0000 or alpha not in _ALPHA_ORDER:
        return None, f'a bitmap layout not decoded here (bitmap info {info:#x})'
    if (bpc, bpp) == (8, 32) and order in (_ORDER_DEFAULT, _ORDER_32_BIG, _ORDER_32_LITTLE):
        step = 1
    elif (bpc, bpp) == (16, 64) and order in (_ORDER_DEFAULT, _ORDER_16_BIG, _ORDER_16_LITTLE):
        step = 2
    else:
        return None, f'a bitmap layout not decoded here ({bpc} bits per component, {bpp} per pixel, ' \
                     f'bitmap info {info:#x})'
    if not all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in (width, height, per_row, length)) \
            or not isinstance(location, int) or location < 0:
        return None, 'no bitmap size or location'
    pixel = 4 * step
    if per_row < width * pixel or length < per_row * (height - 1) + width * pixel or location + length > len(data):
        return None, 'a bitmap that does not fit its stated size or thumbnails.data'
    names = _ALPHA_ORDER[alpha]
    if step == 1 and order == _ORDER_32_LITTLE:
        names = names[::-1]
    # Byte offset of the most significant byte of each component within a pixel.
    high = 0 if step == 1 or order != _ORDER_16_LITTLE else 1
    offset = {name: index * step + high for index, name in enumerate(names)}
    red_at, green_at, blue_at = offset['R'], offset['G'], offset['B']
    alpha_at = offset.get('A')
    pixels = bytearray()
    for y in range(height):
        start = location + y * per_row
        row = data[start:start + width * pixel]
        for x in range(0, width * pixel, pixel):
            red, green, blue = row[x + red_at], row[x + green_at], row[x + blue_at]
            value = 255 if alpha_at is None else row[x + alpha_at]
            if alpha in _PREMULTIPLIED and 0 < value < 255:
                red, green, blue = (min(255, (c * 255 + value // 2) // value) for c in (red, green, blue))
            pixels += bytes((red, green, blue, value))
    return _png(width, height, bytes(pixels)), None


def _layout(row):
    """The bitmap layout of a thumbnails row, from bitmapFormat or, in the older table, its columns."""
    if row['bitmapFormat'] is not None:
        return _archive_values(row['bitmapFormat'])
    return {'w': row['width'], 'h': row['height'], 'bpc': row['bitspercomponent'], 'bpp': row['bitsperpixel'],
            'bpr': row['bytesperrow'], 'i': row['bitmapinfo']}


@artifact_processor
def macosQuickLookThumbnails(context):
    data_headers = (('Last Hit (UTC)', 'datetime'), ('File Modified (UTC)', 'datetime'),
                    ('Thumbnail', 'media'), 'File ID', 'File Size', 'Generator',
                    'Version (as stored)', 'Thumbnail Size (as stored)', 'Width', 'Height',
                    'Hit Count (as stored)', 'Volume ID (as stored)', 'Source File')
    records, read = [], []
    for path in _databases(context, 'index.sqlite'):
        relative = context.get_relative_path(path)
        if not (does_table_exist_in_db(path, 'basic_files') and does_table_exist_in_db(path, 'thumbnails')):
            logfunc(f'QuickLook Thumbnails: no basic_files and thumbnails tables in {relative}')
            continue
        store = os.path.join(os.path.dirname(path), 'thumbnails.data')
        data = b''
        if os.path.isfile(store):
            with open(store, 'rb') as handle:
                data = handle.read()
        files = {}
        for row in get_sqlite_db_records(path, 'SELECT fileId, fsid, version FROM basic_files'):
            version = _archive_values(row['version'])
            files[row['fileId']] = (row['fsid'], version)
        columns = ('file_id', 'size', 'hit_count', 'last_hit_date', 'width', 'height', 'bitmapFormat',
                   'bitspercomponent', 'bitsperpixel', 'bytesperrow', 'bitmapinfo', 'bitmapdata_location',
                   'bitmapdata_length')
        thumbs = get_sqlite_db_records(path, f'SELECT {_select(path, "thumbnails", columns)} FROM thumbnails '
                                             'ORDER BY last_hit_date, file_id, size')
        skipped, seen = {}, set()
        for row in thumbs:
            file_id = row['file_id'] & _ID_MASK if isinstance(row['file_id'], int) else row['file_id']
            seen.add(file_id)
            fsid, version = files.get(file_id, ('', {}))
            image, reason = _render(data, _layout(row), row['bitmapdata_location'], row['bitmapdata_length'])
            media = ''
            if image:
                size = row['size']
                label = f'_{size:g}' if isinstance(size, (int, float)) and not isinstance(size, bool) else ''
                media = check_in_embedded_media(store, image, name=f'{file_id}{label}.png',
                                                force_type='image/png', force_extension='png') or ''
            else:
                skipped[reason] = skipped.get(reason, 0) + 1
            records.append(((_time(_MAC_EPOCH, row['last_hit_date']), _blank(version.get('m')), media,
                             file_id, _blank(version.get('s')), _blank(version.get('g')),
                             _blank(version.get('v')), _blank(row['size']), _blank(row['width']),
                             _blank(row['height']), _blank(row['hit_count']), _blank(fsid)), relative))
        # A file QuickLook versioned without a thumbnail still gets a row.
        for file_id, (fsid, version) in sorted(files.items()):
            if file_id not in seen:
                records.append((('', _blank(version.get('m')), '', file_id, _blank(version.get('s')),
                                 _blank(version.get('g')), _blank(version.get('v')), '', '', '', '',
                                 _blank(fsid)), relative))
        for reason, count in skipped.items():
            logfunc(f'QuickLook Thumbnails: {count} thumbnail(s) in {relative} not rendered: {reason}')
        if files or thumbs:
            read.append(path)
            if data:
                read.append(store)
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosQuickLookCloudThumbnails(context):
    data_headers = (('Last Hit (UTC)', 'datetime'), 'Last Seen Path', 'Doc ID', 'Volume UUID',
                    'Size (as stored)', 'Source File')
    records, read = [], []
    for path in _databases(context, 'cloudthumbnails.db'):
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'thumbnails'):
            logfunc(f'QuickLook Cloud Thumbnails: no thumbnails table in {relative}')
            continue
        rows = get_sqlite_db_records(
            path, 'SELECT docid, vol_uuid, last_hit_date, last_seen_path, size FROM thumbnails '
                  'ORDER BY last_hit_date, docid')
        if rows:
            read.append(path)
        for row in rows:
            volume = row['vol_uuid']
            if isinstance(volume, bytes) and len(volume) == 16:
                volume = '-'.join((volume[:4].hex(), volume[4:6].hex(), volume[6:8].hex(),
                                   volume[8:10].hex(), volume[10:].hex())).upper()
            records.append(((_time(_UNIX_EPOCH, row['last_hit_date']), _blank(row['last_seen_path']),
                             _blank(row['docid']), _blank(volume), _blank(row['size'])), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)
