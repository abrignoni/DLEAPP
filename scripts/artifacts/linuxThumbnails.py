"""Thumbnails in the freedesktop thumbnail cache, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "freedesktopThumbnails": {
        "name": "Thumbnail Cache (freedesktop)",
        "description": "Thumbnails and failure entries in the freedesktop thumbnail cache (.cache/thumbnails, or "
                       "the older .thumbnails): for each, the image, the original file's URI and modified time as "
                       "it records them, the thumbnail file's modified time, and the program it names as its "
                       "writer.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "One row per file the paths match in a size folder (normal, large, x-large or xx-large), or in "
                 "the fail folder or a program's folder under it, of a .cache/thumbnails or .thumbnails folder. "
                 "The thumbnail standard puts each user's thumbnails in $XDG_CACHE_HOME/thumbnails, or "
                 "$HOME/.cache/thumbnails when that variable is not set, with those size folders for thumbnails of "
                 "at most 128, 256, 512 and 1024 pixels and a fail folder for failures (Reference: "
                 "freedesktop.org, 'Thumbnail Managing Standard', "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L183-L242); "
                 "up to version 0.7.0 it put them in .thumbnails in the home folder (Reference: freedesktop.org, "
                 "'Thumbnail Managing Standard 0.7.0', "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/2ab7c028955d71ca05f8fbb6d2acaca382f3b4ed/thumbnail/thumbnail-spec.sgml#L166-L182). "
                 "A file the paths match outside those folders is counted in the run log and not reported: on "
                 "dleapp_macos_bigsur 19 files in a .thumbnails folder under /System/Library/Desktop "
                 "Pictures/Solid Colors match, none in a size folder. A cache under an XDG_CACHE_HOME whose folder "
                 "is not named .cache is not read, nor is a shared thumbnail repository, which the standard keeps "
                 "in a .sh_thumbnails folder beside the files it covers (Reference: freedesktop.org, 'Thumbnail "
                 "Managing Standard', "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L759-L771). "
                 "Rows are in the order of their paths. Original URI is the thumbnail's Thumb::URI key, the URI of "
                 "the original file, and Original Modified (UTC) its Thumb::MTime key, the original's modification "
                 "time in seconds since 1970, both of which the standard requires (Reference: freedesktop.org, "
                 "'Thumbnail Managing Standard', "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L311-L323); "
                 "Original Path is the path of a file: URI that names no host or localhost, percent-decoded as "
                 "UTF-8 with any byte that is not UTF-8 shown as \\xNN, and blank for any other URI, including one "
                 "that cannot be parsed. Software is the Software key, which the standard defines as the name of "
                 "the program that wrote the thumbnail (Reference: "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L349-L355). "
                 "Where one of these keys is in more than one text chunk, the first is shown (for Thumb::MTime, "
                 "the first that can be read as seconds since 1970). The standard names a thumbnail after the MD5 "
                 "hash of its URI (Reference: freedesktop.org, 'Thumbnail Managing Standard', "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L469-L478): "
                 "Name Matches URI is Yes when the file name is the MD5 of the shown Thumb::URI's stored bytes, No "
                 "when it is not (for example a thumbnail saved under another name), and blank when the PNG holds "
                 "no Thumb::URI. Other Keys lists, as key=value one per line, every text chunk not shown in "
                 "another column, such as the optional Thumb::Size, Thumb::Mimetype and Thumb::Image::Width and "
                 "Height the standard defines (Reference: "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L325-L337, "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/thumbnail/thumbnail-spec.xml#L383-L407), "
                 "a second chunk with a key already shown, or a Thumb::MTime that cannot be read as seconds since "
                 "1970. Text chunks are read from tEXt and zTXt as Latin-1 and from iTXt as UTF-8, where any byte "
                 "that is not UTF-8 is shown as \\xNN. Thumbnail is the file itself and Thumbnail Pixels the width "
                 "and height its IHDR chunk gives. Check names what could not be read or did not verify, and "
                 "reading goes on where it can: a file that is not a PNG; a file that ends inside a chunk, where "
                 "reading stops and what came before is still reported; a chunk whose CRC does not match, which is "
                 "still read, as is the rest of the file; and a chunk that cannot be decoded. Compressed text is "
                 "read up to 1 MiB: a text longer than that once decompressed is cut there, and one whose "
                 "compressed stream ends early is shown as far as it goes, both named in Check. Thumbnail Written "
                 "(UTC) is the modified time the extraction recorded for the thumbnail file. GNOME's thumbnail "
                 "factory, whose Software value GNOME::ThumbnailFactory every thumbnail Nautilus wrote on the "
                 "tested VM carries, writes a thumbnail to a temporary file and renames it into place (Reference: "
                 "GNOME, 'gnome-desktop-thumbnail.c', "
                 "https://gitlab.gnome.org/GNOME/gnome-desktop/-/blob/c214a5f3ff96d6add49bd88372c0c449bcab1967/libgnome-desktop/gnome-desktop-thumbnail.c#L1274-L1360), "
                 "so for its thumbnails that time is when the thumbnail was last written. It writes Thumb::URI, "
                 "Thumb::MTime and Software GNOME::ThumbnailFactory, and Thumb::Image::Width and Height only when "
                 "the thumbnailer supplies them (same lines), and a failure entry as a 1 by 1 transparent PNG in "
                 "fail/gnome-thumbnail-factory (Reference: "
                 "https://gitlab.gnome.org/GNOME/gnome-desktop/-/blob/c214a5f3ff96d6add49bd88372c0c449bcab1967/libgnome-desktop/gnome-desktop-thumbnail.c#L160, "
                 "https://gitlab.gnome.org/GNOME/gnome-desktop/-/blob/c214a5f3ff96d6add49bd88372c0c449bcab1967/libgnome-desktop/gnome-desktop-thumbnail.c#L814-L829, "
                 "https://gitlab.gnome.org/GNOME/gnome-desktop/-/blob/c214a5f3ff96d6add49bd88372c0c449bcab1967/libgnome-desktop/gnome-desktop-thumbnail.c#L1363-L1370, "
                 "https://gitlab.gnome.org/GNOME/gnome-desktop/-/blob/c214a5f3ff96d6add49bd88372c0c449bcab1967/libgnome-desktop/gnome-desktop-thumbnail.c#L1532-L1550). "
                 "Measured with the known steps of ubuntu2604_arm64_thumbnails: Nautilus 50.2.2, opened on a "
                 "folder of six known files, wrote within a second a large thumbnail for each of the four images, "
                 "a failure entry for a file that was not an image and nothing for a text file, although the files "
                 "had only been written by a script and never opened in an application; so a thumbnail shows that "
                 "a program made one for that URI, not that a person opened the file. When one image was rewritten "
                 "while the folder was shown, Nautilus rewrote its thumbnail 2.4 seconds later with the new "
                 "Thumb::MTime. Moving one image to the Trash through Nautilus, another through gio trash, and "
                 "deleting a third with rm left all three thumbnails in place, so a thumbnail can outlive its "
                 "original. On GNOME, gnome-settings-daemon deletes thumbnails whose last access (or, failing "
                 "that, modification) is older than the org.gnome.desktop.thumbnail-cache maximum-age setting, and "
                 "the oldest when the cache passes maximum-size, two minutes after it starts and then daily "
                 "(Reference: GNOME, 'gsd-housekeeping-manager.c', "
                 "https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/0037c5aab6ea7141640c1919d2fae7a604c61551/plugins/housekeeping/gsd-housekeeping-manager.c#L98-L176, "
                 "https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/0037c5aab6ea7141640c1919d2fae7a604c61551/plugins/housekeeping/gsd-housekeeping-manager.c#L257-L299, "
                 "https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/0037c5aab6ea7141640c1919d2fae7a604c61551/plugins/housekeeping/gsd-housekeeping-manager.c#L316-L326, "
                 "https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/0037c5aab6ea7141640c1919d2fae7a604c61551/plugins/housekeeping/gsd-housekeeping-manager.c#L389-L397); "
                 "the defaults are 180 days and 512 MB (Reference: GNOME, "
                 "'org.gnome.desktop.thumbnail-cache.gschema.xml', "
                 "https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/0b3ea8e1a25ecfc33e9f6af1b1db93c4032b84e6/schemas/org.gnome.desktop.thumbnail-cache.gschema.xml.in#L4-L11), "
                 "which the tested VM kept. So a missing thumbnail is not evidence that a file was never shown. On "
                 "ubuntu2604_arm64_thumbnails there are 6 rows: the 4 large thumbnails and the failure entry "
                 "Nautilus wrote and the x-large thumbnail the known steps wrote with GNOME's thumbnail factory "
                 "directly. On all 6 rows, Software is GNOME::ThumbnailFactory, Name Matches URI is Yes, and Other "
                 "Keys and Check are blank. Of the other tested images, dleapp_macos_bigsur holds the 19 files "
                 "named above, and none of the remaining sixteen has a member the declared paths match.",
        "paths": ("*/.cache/thumbnails/*.png", "*/.thumbnails/*.png"),
        "output_types": "standard",
        "artifact_icon": "photo",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (19 matched files outside a size folder)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 6 rows",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import hashlib
import os
import re
import struct
import zlib
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import unquote_to_bytes, urlsplit

from scripts.ilapfuncs import artifact_processor, check_in_media, logfunc
from scripts.linux_links import recorded_time, seeker_of

SIGNATURE = b'\x89PNG\r\n\x1a\n'
TEXT_LIMIT = 1 << 20
SIZE_FOLDERS = ('normal', 'large', 'x-large', 'xx-large', 'fail')
SHOWN_KEYS = ('Thumb::URI', 'Thumb::MTime', 'Software')
MD5_NAME = re.compile(r'^[0-9a-f]{32}$')


def png_text(data):
    """(keys, width, height, problems) for a PNG: its text chunks (tEXt, zTXt and iTXt) as (key, text, stored bytes)
    in file order, the width and height its IHDR chunk gives (None when there is none), and what could not be read.
    tEXt and zTXt text is Latin-1 and iTXt text UTF-8, as the PNG standard defines them; a byte of iTXt text that is not
    UTF-8 is shown as \\xNN."""
    keys, problems = [], []
    width = height = None
    if not data.startswith(SIGNATURE):
        return keys, width, height, ['not a PNG file']
    i = len(SIGNATURE)
    while i < len(data):
        if i + 8 > len(data):
            problems.append('the file ends inside a chunk header')
            break
        length, kind = struct.unpack('>I4s', data[i:i + 8])
        start = i
        body = data[i + 8:i + 8 + length]
        crc = data[i + 8 + length:i + 12 + length]
        if len(body) < length or len(crc) < 4:
            problems.append(f'the file ends inside the {kind.decode("latin-1")} chunk at offset {i}')
            break
        if zlib.crc32(kind + body) != struct.unpack('>I', crc)[0]:
            problems.append(f'the CRC of the {kind.decode("latin-1")} chunk at offset {i} does not match')
        i += 12 + length
        try:
            if kind == b'IHDR' and length >= 8:
                width, height = struct.unpack('>II', body[:8])
            elif kind == b'tEXt':
                key, _sep, value = body.partition(b'\0')
                keys.append((key.decode('latin-1'), value.decode('latin-1'), value))
            elif kind == b'zTXt':
                key, _sep, rest = body.partition(b'\0')
                value = _inflate(rest[1:], kind, start, problems)
                keys.append((key.decode('latin-1'), value.decode('latin-1'), value))
            elif kind == b'iTXt':
                key, _sep, rest = body.partition(b'\0')
                compressed, _method = rest[0], rest[1]
                _language, _sep, rest = rest[2:].partition(b'\0')
                _translated, _sep, text = rest.partition(b'\0')
                text = _inflate(text, kind, start, problems) if compressed else text
                keys.append((key.decode('latin-1'), text.decode('utf-8', errors='backslashreplace'), text))
            elif kind == b'IEND':
                break
        except (IndexError, ValueError, zlib.error) as exc:
            problems.append(f'the {kind.decode("latin-1")} chunk at offset {start} could not be read ({exc})')
    return keys, width, height, problems


def _inflate(data, kind, offset, problems):
    """Decompress a compressed text chunk, keeping at most TEXT_LIMIT bytes. A text cut at that limit, or a compressed
    stream that ends before its end marker, is added to problems, so part of a text is never shown as all of it."""
    inflater = zlib.decompressobj()
    text = inflater.decompress(data, TEXT_LIMIT)
    name = kind.decode('latin-1')
    if not inflater.eof and inflater.unconsumed_tail:
        problems.append(f'the text of the {name} chunk at offset {offset} is longer than {TEXT_LIMIT} bytes and was '
                        'cut there')
    elif not inflater.eof:
        problems.append(f'the compressed text of the {name} chunk at offset {offset} ends early')
    return text


def original_path(uri):
    """The path a file: URI names, percent-decoded as UTF-8 with other bytes shown as \\xNN; '' for another URI."""
    try:
        parts = urlsplit(uri)
    except ValueError:
        return ''
    if parts.scheme.lower() != 'file' or parts.netloc.lower() not in ('', 'localhost'):
        return ''
    return unquote_to_bytes(parts.path).decode('utf-8', errors='backslashreplace')


def cache_folder(relative):
    """The part of a thumbnail's path from its size folder on (normal, large, x-large, xx-large or fail/<program>),
    or '' when the file does not sit in one."""
    parts = relative.replace('\\', '/').split('/')
    for index in range(len(parts) - 1, 0, -1):
        if parts[index - 1] in ('thumbnails', '.thumbnails') and parts[index] in SIZE_FOLDERS:
            return '/'.join(parts[index:-1])
    return ''


def split_keys(keys):
    """The first chunk of each shown key, as key: (text, stored bytes), and every other chunk as key=value lines, one
    per line. A Thumb::MTime that cannot be read as seconds since 1970 is left with the other chunks, so no stored
    value drops out of the row."""
    shown, others = {}, []
    for key, text, raw in keys:
        if key in SHOWN_KEYS and key not in shown and (key != 'Thumb::MTime' or _time(text) != ''):
            shown[key] = (text, raw)
        else:
            others.append(f'{key}={text}')
    return shown, '\n'.join(others)


def _time(value):
    """A Thumb::MTime value, seconds since 1970, as a UTC time; '' for anything else."""
    if value.isdigit():
        try:
            return datetime.fromtimestamp(int(value), timezone.utc)
        except (OverflowError, OSError, ValueError):
            return ''
    return ''


@artifact_processor
def freedesktopThumbnails(context):
    data_headers = (('Thumbnail Written (UTC)', 'datetime'), ('Original Modified (UTC)', 'datetime'),
                    ('Thumbnail', 'media'), 'Original Path', 'Original URI', 'Cache Folder', 'Software',
                    'Thumbnail Pixels', 'Name Matches URI', 'Other Keys', 'Check', 'Source File')
    seeker = seeker_of(context)
    counts = Counter()
    data_list = []
    read = []
    for path in sorted((str(p) for p in context.get_files_found()), key=context.get_relative_path):
        if os.path.isdir(path):
            continue
        relative = context.get_relative_path(path)
        folder = cache_folder(relative)
        if not folder:
            counts['matched files outside a size folder of the cache, not reported'] += 1
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        keys, width, height, problems = png_text(data)
        shown, others = split_keys(keys)
        uri = shown.get('Thumb::URI', ('', b''))[0]
        stem = os.path.basename(relative)[:-4]
        if 'Thumb::URI' not in shown:
            matches = ''
        elif MD5_NAME.match(stem):
            matches = 'Yes' if hashlib.md5(shown['Thumb::URI'][1]).hexdigest() == stem else 'No'
        else:
            matches = 'No'
        media = check_in_media(path, os.path.basename(relative))
        data_list.append((recorded_time(seeker, path, None), _time(shown.get('Thumb::MTime', ('', b''))[0]), media,
                          original_path(uri), uri, folder, shown.get('Software', ('', b''))[0],
                          f'{width} x {height}' if width is not None else '', matches, others,
                          '; '.join(problems), relative))
        read.append(path)
    if counts:
        logfunc('Thumbnail Cache (freedesktop): ' + ', '.join(f'{count} {what}' for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
