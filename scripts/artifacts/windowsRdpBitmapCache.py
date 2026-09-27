"""Remote Desktop client bitmap cache (Cache????.bin) for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Cache????.bin files in a profile's AppData\\Local\\Microsoft\\Terminal Server
Client\\Cache folder with scripts/rdp_bitmap_cache.py: one row per cache file, one row per tile
with the tile as an image, and one row per page of tiles laid out in the order the file stores
them.
"""

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc
from scripts.rdp_bitmap_cache import page_rgb, png, read_cache, tile_rgb
from scripts.windows_registry import user_from_path

__artifacts_v2__ = {
    "rdpBitmapCacheFiles": {
        "name": "RDP Bitmap Cache Files",
        "description": 'Remote Desktop client bitmap cache files (Cache????.bin and .bmc) in a'
                        ' user profile, with their recorded times, tile counts and whether each'
                        ' was read.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Windows",
        "notes": "Lists the files ending in .bin or .bmc in a profile's "
                  'AppData\\Local\\Microsoft\\Terminal Server Client\\Cache folder. The '
                  'Cache????.bin files are read with scripts/rdp_bitmap_cache.py, which follows'
                  " ANSSI's bmc-tools, a parser its README calls an RDP Bitmap Cache parser for"
                  ' the bcache*.bmc and cache????.bin files in Windows user profiles '
                  '(https://github.com/ANSSI-FR/bmc-tools/blob/5a4cad32be78b3b874aeec910cb478e04ba3501e/README.md?plain=1#L2-L4);'
                  ' no code is copied from its CeCILL-2.1 licensed bmc-tools.py. Microsoft '
                  'documents the Remote Desktop Connection setting that caches bitmaps on the '
                  'local computer, bitmapcachepersistenable '
                  '(https://github.com/MicrosoftDocs/SupportArticles-docs/blob/899bff3bc0ce59244c9258bd55bdddbf2d94a705/support/windows-server/remote/remote-desktop-protocol-settings.md?plain=1#L209-L211),'
                  ' as a client-side cache of bitmaps rendered in the session '
                  '(https://github.com/MicrosoftDocs/windowsserverdocs/blob/62d7b049a49a912c16c87e0e8e429492ffea24f9/WindowsServerDocs/administration/performance-tuning/role/remote-desktop/session-hosts.md?plain=1#L164).'
                  ' The .bmc files are listed and not read. A Cache????.bin file begins with '
                  'the bytes RDP8bmp and a NUL, then a 32-bit value bmc-tools logs as the '
                  'header version '
                  '(https://github.com/ANSSI-FR/bmc-tools/blob/5a4cad32be78b3b874aeec910cb478e04ba3501e/bmc-tools.py#L48-L51),'
                  ' shown as Header Version, and the tiles follow (see RDP Bitmap Cache Tiles).'
                  ' Tiles is the number of tiles read and Pages the number of pages RDP Bitmap '
                  'Cache Pages makes of them. Read says whether the tiles ran exactly to the '
                  'end of the file or where reading stopped, and a file without the header is '
                  'listed as not read. Created (UTC) and Modified (UTC) are the times the '
                  "image's file system records for the file; they are left blank for a folder "
                  "or archive input, whose copy's times are not the evidence's. Apart from the "
                  'pixels, a Cache????.bin file holds only its header and, for each tile, two '
                  'key values, a width and a height, so these two times are the only times the '
                  'three RDP Bitmap Cache artifacts report, and nothing in the cache names a '
                  'server or a session. Tested on the four Windows images: only '
                  'pc_mus_001_win11 has the folder, holding Cache0000.bin, Cache0001.bin and '
                  'Cache0002.bin, each with Header Version 6 and 6,400 tiles running exactly to'
                  ' the end of the file, and a bcache24.bmc of 0 bytes. User held one value on '
                  'every row there. af_case2_win10, lonewolf_win10 and szechuan_win10 have no '
                  'Terminal Server Client folder.',
        "paths": ('*/AppData/Local/Microsoft/Terminal Server Client/Cache/*',),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Terminal Server Client folder)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Terminal Server Client folder)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Terminal Server Client folder)",
            "dleapp_macos_bigsur": ("macOS 11.2.1 build 20D74 | 0 rows (no member matches "
                                    "the declared paths)"),
        },
    },
    "rdpBitmapCacheTiles": {
        "name": "RDP Bitmap Cache Tiles",
        "description": 'Tiles of the Remote Desktop client bitmap cache (Cache????.bin), one '
                        'row per tile with the tile as an image.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Windows",
        "notes": 'One row per tile of each Cache????.bin file listed by RDP Bitmap Cache '
                  "Files, with the tile as a PNG image. The layout is read from ANSSI's "
                  'bmc-tools, bmc-tools.py at commit 5a4cad32be78b3b874aeec910cb478e04ba3501e '
                  '(https://github.com/ANSSI-FR/bmc-tools/blob/5a4cad32be78b3b874aeec910cb478e04ba3501e/bmc-tools.py),'
                  " cited below by line; no code is copied. After the file's 12-byte header, "
                  'each tile is two 32-bit values bmc-tools calls key1 and key2, a 16-bit width'
                  ' and a 16-bit height (L63), then width times height pixels of 4 bytes '
                  '(L64-L66), of which bmc-tools keeps the first three (L143-L155) and writes '
                  'them into its BMP files with blue first (L370). The image here takes those '
                  'three bytes as blue, green and red, with the rows running from the top: read'
                  ' that way, the tested tiles show upright text and window parts. Reading '
                  'stops at a tile header whose width or height is 0 or above 64, or whose '
                  'pixels run past the end of the file; on the tested image all three files '
                  "were read to their last byte. Tile Index is the tile's position in its file "
                  'from 0, the number bmc-tools puts in the names of the files it exports '
                  '(L331). Page is the page of RDP Bitmap Cache Pages that holds the tile. Key '
                  "(as stored) is the tile's first 8 bytes in hexadecimal; 113 of the 9,340 "
                  'keys in the three tested files were stored with more than one image, so a '
                  "key does not identify one image across files. Offset is where the tile's "
                  'header begins in the file, and User the profile folder the file sits in. The'
                  ' cache does not record which server or session a tile came from. On '
                  'pc_mus_001_win11, Width was 64 on every row, and Height was 64 on 18,601 '
                  'rows and 56 on 599. User held one value on every row there. bmc-tools v3.05 '
                  'at the commit above exported 6,400 tiles from each of the three files, and '
                  'each of the 19,200 was identical, pixel for pixel, to the tile here. The '
                  'three files overlap: Cache0000.bin and Cache0001.bin hold the same key and '
                  'pixels at the same index for 4,848 tiles, and Cache0002.bin does so with '
                  'each of the other two for 3,071; the 19,200 tiles hold 9,443 distinct '
                  'images.',
        "paths": ('*/AppData/Local/Microsoft/Terminal Server Client/Cache/*',),
        "output_types": ["standard"],
        "artifact_icon": "image",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Terminal Server Client folder)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Terminal Server Client folder)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 19200 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Terminal Server Client folder)",
            "dleapp_macos_bigsur": ("macOS 11.2.1 build 20D74 | 0 rows (no member matches "
                                    "the declared paths)"),
        },
    },
    "rdpBitmapCachePages": {
        "name": "RDP Bitmap Cache Pages",
        "description": 'Pages of Remote Desktop client bitmap cache tiles, up to 256 to an '
                        'image in the order each Cache????.bin file stores them.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Windows",
        "notes": 'One row per page of up to 256 tiles of a Cache????.bin file, as a PNG image:'
                  ' the tiles in the order the file stores them, Tile Index 0 first, 16 to a '
                  'row, each in a 64 by 64 cell, so a page is 1,024 pixels wide and 64 pixels '
                  'high for each row of tiles it holds. The part of a cell a tile does not '
                  "cover, and the cells after a file's last tile, are filled with magenta (red "
                  '255, green 0, blue 255), so a tile 56 pixels high has a magenta strip under '
                  "it. First Tile and Last Tile are the Tile Index values of the page's first "
                  "and last tiles, and Tiles how many it holds. The order is the file's, not "
                  "the screen's: on the tested image some neighbouring tiles continue each "
                  "other's text and others are unrelated. RDP Bitmap Cache Tiles gives the "
                  'layout, its source and the tests. On pc_mus_001_win11 the three files made '
                  '25 pages each, Tiles was 256 on every row, and User held one value on every '
                  'row; 48 of the 75 page images are distinct, since the files overlap.',
        "paths": ('*/AppData/Local/Microsoft/Terminal Server Client/Cache/*',),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Terminal Server Client folder)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Terminal Server Client folder)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 75 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Terminal Server Client folder)",
            "dleapp_macos_bigsur": ("macOS 11.2.1 build 20D74 | 0 rows (no member matches "
                                    "the declared paths)"),
        },
    },
}

_COLUMNS = 16
_PAGE_TILES = _COLUMNS * _COLUMNS


def _instant(value):
    """A FileInfo time (seconds since 1970, UTC) as an aware datetime, or ''."""
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _cache_files(context):
    """(path, file name) of each file found, in path order."""
    for path in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isfile(path):
            yield path, os.path.basename(path)


def _read(path):
    """(header version, tiles, stop) of a cache file; raises OSError when it cannot be read."""
    with open(path, 'rb') as handle:
        return read_cache(handle.read())


def _status(stop):
    return ('read to the end of the file' if stop is None
            else f'reading stopped at offset {stop[0]:,}: {stop[1]}')


def _caches(context, label):
    """[(path, file name, user, tiles)] for each Cache????.bin read, in path order."""
    caches = []
    for path, name in _cache_files(context):
        if not name.lower().endswith('.bin'):
            continue
        relative = context.get_relative_path(path)
        try:
            version, tiles, stop = _read(path)
        except OSError as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        if version is None:
            logfunc(f'{label}: {relative}: no RDP8bmp header, not read')
            continue
        logfunc(f'{label}: {relative}: header version {version}, {len(tiles):,} tiles, '
                f'{_status(stop)}')
        caches.append((path, name, user_from_path(relative), tiles))
    return caches


@artifact_processor
def rdpBitmapCacheFiles(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'User',
                    'Cache File', 'Size (bytes)', 'Header Version', 'Tiles', 'Pages', 'Read')
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    # Only a disk image gives the evidence's own times; a folder or archive gives the times
    # of the copy.
    from_image = hasattr(seeker, 'stream_list')
    data_list, sources = [], []
    for path, name in _cache_files(context):
        low = name.lower()
        if not low.endswith(('.bin', '.bmc')):
            continue
        relative = context.get_relative_path(path)
        version = count = pages = ''
        if low.endswith('.bmc'):
            status = 'not read (.bmc cache)'
        else:
            try:
                version, tiles, stop = _read(path)
            except OSError as exc:
                logfunc(f'RDP Bitmap Cache Files: could not read {relative}: {exc}')
                continue
            if version is None:
                version, status = '', 'no RDP8bmp header, not read'
            else:
                count, pages = len(tiles), -(-len(tiles) // _PAGE_TILES)
                status = _status(stop)
        info = infos.get(path)
        created = modified = ''
        if from_image and info:
            created, modified = _instant(info.creation_date), _instant(info.modification_date)
        data_list.append((created, modified, user_from_path(relative), name,
                          os.path.getsize(path), version, count, pages, status))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def rdpBitmapCacheTiles(context):
    data_headers = (('Tile', 'media'), 'User', 'Cache File', 'Tile Index', 'Page', 'Width',
                    'Height', 'Key (as stored)', 'Offset')
    data_list = []
    sources = []
    for path, name, user, tiles in _caches(context, 'RDP Bitmap Cache Tiles'):
        sources.append(path)
        for tile in tiles:
            image = png(tile.width, tile.height, tile_rgb(tile.pixels))
            media = check_in_embedded_media(path, image, name=f'{name}_{tile.index:04d}.png',
                                            force_type='image/png', force_extension='png')
            data_list.append((media or '', user, name, tile.index,
                              tile.index // _PAGE_TILES + 1, tile.width, tile.height,
                              tile.key.hex(), tile.offset))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def rdpBitmapCachePages(context):
    data_headers = (('Page Image', 'media'), 'User', 'Cache File', 'Page', 'First Tile',
                    'Last Tile', 'Tiles')
    data_list = []
    sources = []
    for path, name, user, tiles in _caches(context, 'RDP Bitmap Cache Pages'):
        sources.append(path)
        for start in range(0, len(tiles), _PAGE_TILES):
            group = tiles[start:start + _PAGE_TILES]
            width, height, rgb = page_rgb(
                [(t.width, t.height, tile_rgb(t.pixels)) for t in group], _COLUMNS)
            number = start // _PAGE_TILES + 1
            media = check_in_embedded_media(path, png(width, height, rgb),
                                            name=f'{name}_page{number:03d}.png',
                                            force_type='image/png', force_extension='png')
            data_list.append((media or '', user, name, number, group[0].index,
                              group[-1].index, len(group)))
    return data_headers, data_list, '\n'.join(sources)
