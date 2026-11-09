"""Folder listings kept by the Office Backstage view (BackstageInAppNavCache), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "officeBackstageCache": {
        "name": "Office Backstage Folder Cache",
        "description": "Folders and files the Office Backstage view (File > Open) listed, one row per item in each cached folder listing, with the time Office last listed that folder and each item's modified time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-09",
        "last_update_date": "2026-11-09",
        "requirements": "none",
        "category": "Microsoft Office",
        "notes": "Reads the .json files in each location folder of BackstageInAppNavCache under %LOCALAPPDATA%\\Microsoft\\Office\\<version>, the cache Office keeps of the folder listings shown in its Backstage view. No Microsoft documentation of the store was found; the fields were described by David Cowen (http://www.learndfir.com/2018/10/18/daily-blog-510-office-2016-backstage-artifacts/) and are read by Arsenal Recon's BackstageParser (https://github.com/ArsenalRecon/BackstageParser/blob/cf09c312d663428a2c02511f00f4683921014ddd/BackstageParser.py) and kacos2000's Backstage.ps1 (https://github.com/kacos2000/Other/blob/935fe3f030fc493df04e7809ecd73241f7522774/OfficeFileCache/Backstage.ps1). What follows was measured on windows11_arm_office_backstage_known_20261109, made with Office LTSC 2024 (16.0.17932.21056, not activated, no Microsoft account) by listing local folders in Word and Excel under File > Open > This PC; see its README. Each file is UTF-16LE JSON without a byte-order mark holding one folder listing: ContainerUrl, the folder; LastReadOn; and Folders and Files, each entry with Url, DisplayName, Author, LastModified and SharingLevelDescription among other fields. The file is named by the SHA-256 of ContainerUrl plus a trailing backslash, encoded UTF-16LE, in upper-case hexadecimal (6 of 6 files); the run log counts files whose name does not match. There is one file per folder and it is rewritten each time the folder is listed, so it holds the last listing only. Listed is LastReadOn read as a Windows FILETIME (UTC). On the known data it equalled the cache file's last-modified time, to the millisecond on the four files whose millisecond time was recorded and to the second on the other two, and the time a step listed the folder, with one exception: a folder left on screen was listed again ten minutes later with nothing done in Office, so Listed is the last time Office listed the folder, not necessarily the time a user opened it. Item Modified is the entry's LastModified read as a FILETIME (UTC). On the known data 10 of the 11 items still on disk at the end equalled the last-write time Windows reported; the other, a folder, held its time 6 ms before a file written into it changed it again, with Listed 1.6 s later, so the item values can be read before the time Listed records. Files holds every file in the folder, not only the kinds the app opens: a folder listed by Word recorded a .xlsx, a .txt and a .png, and a listing made by Excel kept a .docx. The record does not say which Office app made a listing. Entries outlive the files they name: the listing of a folder deleted after it was listed stayed in the cache, with its file, after the parent folder was listed again without it. A file deleted from a folder was gone from that folder's listing once the folder was listed again. Name is the entry's DisplayName and Path its Url, as stored; Listed Folder is ContainerUrl as stored. A listing with no folders or files gives one row with Item Type '(none listed)' and no item, so the folder still shows as listed. User is the folder name after Users in the path the file was found under; on the known data User held one value on all 13 rows, one Windows user. Location is the name of the folder the cache file sits in, as stored; on the known data Location held MyComputer on all 13 rows, the only location the local listings used. Listings of OneDrive, SharePoint or other places added with a Microsoft account, and the Author and Sharing values such listings may carry, were not exercised: Author and Sharing held no value on any of the 13 rows. Not reported: LCID (1033 on every file), FetchedUrl, RetryAfter, ContainerIsDefaultDrive, ContainerResourceId, Metadata (FolderCreationAllowed and FileCreationAllowed, true on every file), and each entry's ResourceId, RootResourceId, ThumbnailUrl, OneNoteItem, RemoteItem and IsDefaultDrive, all empty or false on every local entry. Browsing in the Save As pane was not exercised. MruServiceCache, the other stores under the same Office folder (winword.exe_Rules, excel.exe_Rules, WebServiceCache, TeachingCallout, SmartLookupCache, AddInClassifierCache) and Office's registry keys are not read. A file that is not a JSON object gives no row and is counted in the run log.",
        "paths": ("*/Users/*/AppData/Local/Microsoft/Office/*/BackstageInAppNavCache/*/*.json",),
        "output_types": "standard",
        "artifact_icon": "folder",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "windows11_arm_office_backstage_known_20261109": "Windows 11 build 26200 (ARM64), Office LTSC 2024 16.0.17932.21056 | 13 rows",
        },
    },
}

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
NO_ITEMS = '(none listed)'


def filetime(value):
    """A Windows FILETIME (100 ns since 1601) as an aware UTC datetime. 0 and anything that is not a whole number
    give ''."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _FILETIME_EPOCH + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def decode(data):
    """The JSON object a cache file holds. Office writes UTF-16LE without a byte-order mark; a BOM, UTF-8 or
    UTF-16BE text is also accepted. Returns None when the bytes are not a JSON object."""
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        encodings = ('utf-16',)
    elif data[1:2] == b'\x00':
        encodings = ('utf-16-le', 'utf-8-sig')
    elif data[:1] == b'\x00':
        encodings = ('utf-16-be',)
    else:
        encodings = ('utf-8-sig', 'utf-16-le')
    for encoding in encodings:
        try:
            value = json.loads(data.decode(encoding))
        except (UnicodeDecodeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


def expected_name(container):
    """The cache file name Office gives a listing: the SHA-256 of the folder path plus a trailing backslash,
    encoded UTF-16LE, in upper-case hexadecimal."""
    return hashlib.sha256((container + '\\').encode('utf-16-le')).hexdigest().upper()


def user_of(relative):
    """The folder name after the Users segment of an evidence-relative path, or ''."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() == 'users':
            return parts[index + 1]
    return ''


def text(value):
    return value if isinstance(value, str) else ('' if value is None else str(value))


def listing_rows(record, user, location, counts):
    """Rows for one cache file: one per entry in Folders and Files, or one with no item when both are empty."""
    container = text(record.get('ContainerUrl'))
    listed = filetime(record.get('LastReadOn'))
    rows = []
    for key, kind in (('Folders', 'Folder'), ('Files', 'File')):
        items = record.get(key)
        if items is None:
            continue
        if not isinstance(items, list):
            counts[f'cache files whose {key} is not a list'] += 1
            continue
        for item in items:
            if not isinstance(item, dict):
                counts[f'{key} entries that are not an object'] += 1
                continue
            rows.append((listed, filetime(item.get('LastModified')), user, kind, text(item.get('DisplayName')),
                         text(item.get('Url')), container, text(item.get('Author')),
                         text(item.get('SharingLevelDescription')), location))
    if not rows:
        rows.append((listed, '', user, NO_ITEMS, '', '', container, '', '', location))
    return rows


@artifact_processor
def officeBackstageCache(context):
    data_headers = (('Listed', 'datetime'), ('Item Modified', 'datetime'), 'User', 'Item Type', 'Name', 'Path',
                    'Listed Folder', 'Author', 'Sharing', 'Location')
    data_list = []
    read = []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or not path.lower().endswith('.json'):
            continue
        try:
            with open(path, 'rb') as handle:
                record = decode(handle.read())
        except OSError:
            counts['cache files that could not be read'] += 1
            continue
        if record is None:
            counts['cache files that are not a JSON object'] += 1
            continue
        relative = context.get_relative_path(path)
        location = os.path.basename(os.path.dirname(path))
        container = record.get('ContainerUrl')
        stem = os.path.splitext(os.path.basename(path))[0]
        if isinstance(container, str) and container and expected_name(container) != stem.upper():
            counts['cache files whose name is not the hash of their ContainerUrl'] += 1
        data_list.extend(listing_rows(record, user_of(relative), location, counts))
        read.append(path)
    if counts:
        logfunc('Office Backstage Folder Cache: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
