__artifacts_v2__ = {
    "macosQuickLookThumbnails": {
        "name": "QuickLook Thumbnails",
        "description": 'Thumbnails in the QuickLook cache, rendered, with the file ID, size and modification '
                       "date recorded for each file, its generator, and the cache's last hit time and hit count.",
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
            'on dleapp_macos_bigsur; a basic_files row that no thumbnail names gets a row of its '
            'own, 3 there. On dleapp_macos_bigsur neither the tables of index.sqlite nor its '
            "version archives hold a file's name or path. File ID is basic_files.fileId: on "
            'dleapp_macos_bigsur all 15 are the inode number of a file on the Data volume, found '
            'by walking the image, and 2 of the 12 thumbnailed files are now in the iCloud Drive '
            'Trash. File Modified and File Size are the m and s values of the QLThumbnailVersion '
            'archive in basic_files.version, and on dleapp_macos_bigsur all 15 equal, to the '
            'second and to the byte, the modification time and size of the file the File ID '
            "resolves to; Arsenal Recon read the date and size values of the older layout's files "
            "table as the file's last modified date and its size in bytes. Generator is the "
            "archive's g, the bundle identifier of a qlgenerator on every row of "
            "dleapp_macos_bigsur, and Version (as stored) is its v, 928.1 on the PDF generator's "
            "rows there and 928.2 on the image generator's; what v versions is not established. "
            'Last Hit is thumbnails.last_hit_date read as seconds since 2001-01-01 in UTC on this '
            'evidence: on dleapp_macos_bigsur the latest, 2021-02-19 19:28:21, is the '
            "modification time of that cache's index.sqlite-wal to the second, and every Last Hit "
            'falls after the File Modified of its file. What a hit is, and so what Last Hit and '
            'Hit Count (as stored) record, is not established. Thumbnail is the bitmap at '
            'bitmapdata_location, bitmapdata_length bytes long, in thumbnails.data, which Mari '
            'DeGrazia describes as a raw bitmap that needs those values and the width and height '
            "to be read (Reference: Mari DeGrazia, 'Quicklook thumbnails.data parser', "
            'http://az4n6.blogspot.com/2016/10/quicklook-thumbnailsdata-parser.html), written out '
            'as a PNG. It is read only when bitspercomponent is 8, bitsperpixel 32 and bitmapinfo '
            '0x2002, which is kCGImageByteOrder32Little with kCGImageAlphaPremultipliedFirst in '
            "Apple's CoreGraphics CGImage.h: blue, green, red and alpha bytes, with colour "
            'premultiplied by alpha, which is divided back out; a bitmap of any other layout, or '
            'one that does not fit its stated size or thumbnails.data, is not rendered and the '
            'run log counts it. All 24 on dleapp_macos_bigsur are that layout; for the 12 '
            'thumbnails 64 pixels wide, the red and blue channels as decoded correlate with the '
            'image the File ID resolves to better than with the two swapped on 11, and equally on '
            'the 12th, whose source has the same red and blue value in every pixel. Thumbnail '
            'Size (as stored) is thumbnails.size, 16 or 64 on dleapp_macos_bigsur, where each '
            "thumbnailed file has one of each, and Width and Height are the bitmap's size in "
            'pixels, the same as each other on every row of dleapp_macos_bigsur, where every '
            'thumbnail is square. Volume ID (as stored) is basic_files.fsid, which holds one '
            'value on every row of dleapp_macos_bigsur; what it encodes is not established. The '
            'second cache on dleapp_macos_bigsur, under private/var/folders/zz, holds no row. The '
            'provider_files and missing_remote_thumbnails tables, which record iCloud Drive items '
            'by item ID without a thumbnail, are not reported, and a cache that has the older '
            'files table instead of basic_files is logged and not read; no public image carries '
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
# CGBitmapInfo: premultiplied alpha first (2) in 32-bit little-endian words (2 << 12).
_BGRA_PREMULTIPLIED = 0x2002


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


def _version(blob):
    """The QLThumbnailVersion archive of a basic_files row as {key: value}, or None."""
    try:
        archive = plistlib.loads(blob)
        objects = archive['$objects']
        root = objects[archive['$top']['root'].data]
    except (plistlib.InvalidFileException, KeyError, IndexError, TypeError, AttributeError, ValueError):
        return None
    values = {}
    for key, value in root.items():
        if isinstance(value, plistlib.UID):
            value = objects[value.data] if value.data < len(objects) else None
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


def _render(data, row):
    """PNG bytes of one thumbnail's bitmap, or the reason it is not rendered."""
    width, height, per_row = row['width'], row['height'], row['bytesperrow']
    location, length = row['bitmapdata_location'], row['bitmapdata_length']
    if (row['bitspercomponent'], row['bitsperpixel'], row['bitmapinfo']) != (8, 32, _BGRA_PREMULTIPLIED):
        return None, 'a bitmap layout other than 8-bit BGRA with premultiplied alpha'
    if not all(isinstance(v, int) and v > 0 for v in (width, height, per_row, length)) or \
            not isinstance(location, int) or location < 0:
        return None, 'no bitmap size or location'
    if per_row < width * 4 or length < per_row * (height - 1) + width * 4 or location + length > len(data):
        return None, 'a bitmap that does not fit its stated size or thumbnails.data'
    pixels = bytearray()
    for y in range(height):
        start = location + y * per_row
        for x in range(width):
            blue, green, red, alpha = data[start + x * 4:start + x * 4 + 4]
            if 0 < alpha < 255:
                red, green, blue = (min(255, (c * 255 + alpha // 2) // alpha) for c in (red, green, blue))
            pixels += bytes((red, green, blue, alpha))
    return _png(width, height, bytes(pixels)), None


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
            version = _version(row['version']) or {}
            files[row['fileId']] = (row['fsid'], version)
        columns = ('file_id', 'size', 'hit_count', 'last_hit_date', 'width', 'height', 'bitspercomponent',
                   'bitsperpixel', 'bytesperrow', 'bitmapinfo', 'bitmapdata_location', 'bitmapdata_length')
        thumbs = get_sqlite_db_records(path, f'SELECT {_select(path, "thumbnails", columns)} FROM thumbnails '
                                             'ORDER BY last_hit_date, file_id, size')
        skipped, seen = {}, set()
        for row in thumbs:
            file_id = row['file_id'] & _ID_MASK if isinstance(row['file_id'], int) else row['file_id']
            seen.add(file_id)
            fsid, version = files.get(file_id, ('', {}))
            image, reason = _render(data, row)
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
