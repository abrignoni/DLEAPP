"""Internet Explorer Favorites (.url files) and legacy cookie text files for DLEAPP.

Author: @AlexisBrignoni, Claude.

A Favorites entry is an Internet shortcut, an INI-style .url file; a legacy Internet Explorer cookie file is a text
file of nine-line records. See the notes for how each field was established.
"""

import configparser
import os
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)

__artifacts_v2__ = {
    "ieFavorites": {
        "name": "Internet Explorer Favorites",
        "description": "Internet shortcut (.url) files in Favorites folders: the shortcut's name and URL, with the "
                       "file's times where the extraction gives them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Internet Explorer",
        "notes": "One row per .url file with an [InternetShortcut] section in a folder named Favorites or a folder below it, read with Python's configparser as text decoded as UTF-8, or as Windows-1252 when it is not UTF-8. URL is the [InternetShortcut] URL value: on the known data (corpus key windows11_arm_url_known_20261104) a shortcut written into the Favorites folder with WScript.Shell's CreateShortcut held the TargetPath it was given there. Name is the file name without .url. Icon File (as stored) is [InternetShortcut] IconFile and Feed URL (as stored) is [MonitoredItem] FeedUrl, both as stored: of the 41 tested files, 7 had an IconFile and 4, all on cfreds_leakage_win7, a FeedUrl; what they are used for was not established. IDList, IconIndex and the {000214A0-0000-0000-C000-000000000046} section's Prop3 value are not shown. Created (UTC) and Modified (UTC) are the created and modified times the tool's image reader reports for the file, as in DPAPI Master Key Files; they are blank for a folder or archive input, whose copy's times are not the evidence's (the known data is a zip). Folder is the file's folder from Favorites down, and User the profile folder after Users or Documents and Settings in its path. On the tested images: cfreds_hacking_case_winxp 6 files in 2 folders, cfreds_leakage_win7 25 in 5, szechuan_win10 and hexordia_mvs2025_win11 4 each, pc_mus_001_win11 1. A row records that a shortcut file is in a Favorites folder, not who made it or when it was used.",
        "paths": ('*/Favorites/*.url',),
        "output_types": ["standard"],
        "artifact_icon": "bookmark",
        "sample_data": {
            "windows11_arm_url_known_20261104": "Windows 11 build 26200 (ARM64) | 1 row",
            "cfreds_hacking_case_winxp": "Windows XP | 6 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 25 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
        },
    },
    "ieCookieFiles": {
        "name": "Internet Explorer Cookie Files",
        "description": "Records of Internet Explorer's legacy cookie text files: each cookie's name, value, site and "
                       "path, with its creation and expiry times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Internet Explorer",
        "notes": "One row per cookie record of a .txt file in a Cookies folder or its Low folder, Internet Explorer's legacy cookie files. A record is the lines before a line holding only '*', and a record with fewer than 8 lines is not shown; on the tested images the rows equal the number of '*' lines (44 and 344). The lines are read in the order the jaraco.windows reader gives them (https://github.com/jaraco/jaraco.windows/blob/26c631178124b716ba25740efe55beb23f717030/jaraco/windows/msie.py#L39-L55): name, value, site and path, flags, the low and high halves of the expiry time, and the low and high halves of the creation time. Expires (UTC) and Created (UTC) are those halves joined into FILETIMEs and read as UTC: on cfreds_hacking_case_winxp the user's Cookies index.dat names 24 cookie files, and for all 24 the latest Expires in the file equalled the expiry the index.dat record holds, and for 22 the latest Created equalled the record's modification time, which the libyal specification gives as UTC (https://github.com/libyal/libmsiecf/blob/a99a703d190d62f6c21b6225cf84ce80037e45d5/documentation/MSIE%20Cache%20File%20(index.dat)%20format.asciidoc?plain=1#L1026); the record's location held the site and path line of every record in its file. Name and Value are the first two lines in that reader's order; nothing in the tested data shows which of the two is the name. Site and Path are the third line split at its first '/'. Flags (as stored) is the fourth line as stored; its meaning was not established (1024, 1536 and 1600 on cfreds_hacking_case_winxp, 13 distinct values on cfreds_leakage_win7). Cookie File is the file's name and User the profile folder after Users or Documents and Settings in its path. On cfreds_hacking_case_winxp 24 files gave 44 rows and on cfreds_leakage_win7 125 files gave 344; cfreds_leakage_win7 holds no user Cookies index.dat to compare with. The Cookies index.dat itself is read by Internet Explorer Cookie Index (index.dat). A row records a cookie Internet Explorer kept, not that anyone chose to keep it.",
        "paths": ('*/Cookies/*.txt', '*/Cookies/Low/*.txt'),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "cfreds_hacking_case_winxp": "Windows XP | 44 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 344 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no cookie text files)",
        },
    },
}


def _profile_user(relative):
    """The folder after Users or Documents and Settings in a path within the extraction, or ''."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'documents and settings'):
            return parts[index + 1]
    return ''


def _instant(value):
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _filetime(high, low):
    try:
        value = (int(high) << 32) | int(low)
    except ValueError:
        return ''
    if not value:
        return ''
    try:
        return _FILETIME_ZERO + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def _text(raw):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1252', 'replace')


def cookie_records(text):
    """The nine-line records of a cookie text file, each ending with a line holding only '*'."""
    records, current = [], []
    for line in text.replace('\r\n', '\n').split('\n'):
        if line == '*':
            if current:
                records.append(current)
            current = []
        else:
            current.append(line)
    return [record for record in records if len(record) >= 8]


@artifact_processor
def ieFavorites(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'Name', 'URL',
                    'Icon File (as stored)', 'Feed URL (as stored)', 'Folder', 'User')
    data_list, sources = [], []
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    from_image = hasattr(seeker, 'stream_list')
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path) or not path.lower().endswith('.url'):
            continue
        relative = context.get_relative_path(path)
        parser = configparser.RawConfigParser(strict=False, interpolation=None)
        parser.optionxform = str
        try:
            with open(path, 'rb') as handle:
                parser.read_string(_text(handle.read()))
        except (OSError, configparser.Error) as exc:
            logfunc(f'Internet Explorer Favorites: {relative} was not read ({type(exc).__name__})')
            continue
        if not parser.has_section('InternetShortcut'):
            continue
        info = infos.get(path)
        created = modified = ''
        if from_image and info:
            created, modified = _instant(info.creation_date), _instant(info.modification_date)
        parts = relative.replace('\\', '/').split('/')
        lowered = [part.lower() for part in parts]
        start = len(lowered) - 1 - lowered[::-1].index('favorites')
        folder = '/'.join(parts[start:-1])
        data_list.append((created, modified, os.path.splitext(parts[-1])[0],
                          parser.get('InternetShortcut', 'URL', fallback=''),
                          parser.get('InternetShortcut', 'IconFile', fallback=''),
                          parser.get('MonitoredItem', 'FeedUrl', fallback=''), folder, _profile_user(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ieCookieFiles(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Expires (UTC)', 'datetime'), 'Name', 'Value', 'Site', 'Path',
                    'Flags (as stored)', 'Cookie File', 'User')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path) or not path.lower().endswith('.txt'):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                records = cookie_records(_text(handle.read()))
        except OSError as exc:
            logfunc(f'Internet Explorer Cookie Files: {relative} was not read ({type(exc).__name__})')
            continue
        rows = 0
        for record in records:
            name, value, where, flags, expire_low, expire_high, create_low, create_high = record[:8]
            site, _slash, rest = where.partition('/')
            data_list.append((_filetime(create_high, create_low), _filetime(expire_high, expire_low), name, value,
                              site, '/' + rest, flags, os.path.basename(relative.replace('\\', '/')),
                              _profile_user(relative)))
            rows += 1
        if rows:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
