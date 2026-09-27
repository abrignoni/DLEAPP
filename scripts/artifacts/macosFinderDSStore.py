__artifacts_v2__ = {
    "macosDSStoreEntries": {
        "name": "Finder .DS_Store Entries",
        "description": 'Names recorded in .DS_Store files, with the structure codes recorded for each and its '
                       'moDD date, lg1S size, comment and put-back values.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": (
            'Reads each .DS_Store file the declared path matches, with the .DS_Store reader Trash '
            "Put Back uses, written from Wim Lewis's notes on the format, which describe the file "
            'as holding records that give attributes of the files in its folder or of the folder '
            "itself, named '.' (Reference: Wim Lewis, 'DS_Store Format', DSStoreFormat.pod in "
            'Mac-Finder-DSStore 1.00, '
            'https://cpan.metacpan.org/authors/id/W/WI/WIML/Mac-Finder-DSStore-1.00.tar.gz). One '
            'row is reported per name in each file, and Structure Codes lists the codes recorded '
            'for it, as stored. The public MacBook Pro logical extraction (macOS 15.4 build '
            '24E248, not a registered corpus key) holds 150 .DS_Store files, the files of 75 '
            'folders each present both at its own path and under System/Volumes/Data; 69 of those '
            "folders are under the Stocks app's container tmp folder, 23 copies of the same three "
            'folders, each inside a folder named 20240516_control_minus_topic_48d. The counts '
            'below for that extraction take each folder once. Comment is the cmmt value, which '
            "Lewis describes as a file's Spotlight Comments, also stored in an extended "
            'attribute, adding that this copy may be historical; neither public image carries '
            'one, so that reading is not exercised. Put Back Name and Put Back Location are the '
            'ptbN and ptbL values described under Trash Put Back; on the public MacBook Pro '
            "extraction they also appear outside the Trash, for data.py in the user's Downloads "
            "folder's .DS_Store. Logical Size is lg1S, or logS where lg1S is absent, which Lewis "
            "describes as appearing to contain the logical size in bytes of the directory's "
            'contents: on the public MacBook Pro extraction lg1S equals the summed size of every '
            'file beneath the named folder on 112 of the 114 records whose named folder the '
            'extraction holds, and the other 2 are in one of the 23 Stocks copies, whose two '
            'subfolders hold only their own .DS_Store in the extraction while those of the other '
            '22 copies hold the recorded sizes. Neither public image carries logS, so that '
            'reading is not exercised. moDD (UTC) is moDD, or modD where moDD is absent; on the '
            'public images every name with either code has both, so that fallback is not '
            'exercised, and the two held the same 8 bytes for all 186 such names on the public '
            'MacBook Pro extraction. Lewis describes both as dutc timestamps, counts of 1/65536 '
            "seconds since 1904, typically the same as the directory's modification date. On that "
            'extraction they are stored instead as 8-byte blobs, read as a little-endian double '
            'of seconds since 2001-01-01 in UTC on this evidence: its Trash .DS_Store gives '
            'Asphalt.app 2025-11-26 19:42:09.982, the second recorded in both Timestamp (UTC) and '
            "Mod Time (UTC) of the Gatekeeper Scan Cache row for that app's bundle ID, and the 10 "
            'distinct values read this way fall between May 2024 and November 2025, those in the '
            'Stocks copies all in May 2024. A dutc value is read as the count Lewis describes, '
            "taken as UTC because Lewis says the type probably corresponds to Apple's UTCDateTime "
            "structure, whose epoch Apple's DateTimeUtils.h (CarbonCore framework, macOS SDK) "
            'gives as January 1, 1904; no public image carries one, so that reading is not '
            'exercised. A name here is not evidence the item is still in the folder: on '
            "dleapp_macos_bigsur the Desktop/Memes 3 folder's .DS_Store names IMG_0188.JPG, which "
            'that folder does not hold, and a file of that name is in the iCloud Drive Trash. On '
            'dleapp_macos_bigsur moDD (UTC), Logical Size and Comment are empty on all 19 rows, '
            'because none of its six files carries those codes, and Comment is empty on all 62 '
            'rows of the public MacBook Pro extraction. A row that more than one file holds with '
            'the same values is reported once, and Source File lists every file that holds it; on '
            "the public MacBook Pro extraction that joins each file's two copies, and the "
            'identical files of the 23 Stocks copies.'
        ),
        "paths": ('*/.DS_Store',),
        "output_types": ["standard"],
        "artifact_icon": "folder",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 19 rows",
        },
    },
}

import math
import os
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_dsstore import DSStoreError, read_ds_store
from scripts.macos_powerlog import merge_sources

_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
_DUTC_EPOCH = datetime(1904, 1, 1, tzinfo=timezone.utc)


def _stores(context):
    """Staged .DS_Store files (not directories, not ._.DS_Store AppleDouble files)."""
    return sorted({str(path) for path in context.get_files_found()
                   if os.path.basename(str(path)) == '.DS_Store' and not os.path.isdir(str(path))})


def _date(kind, value):
    """A moDD or modD value as a UTC datetime: an 8-byte blob holding a little-endian double
    of seconds since 2001-01-01, or a dutc count of 1/65536 seconds since 1904-01-01. Any
    other shape is returned as stored (hexadecimal for bytes)."""
    try:
        if kind == 'blob' and isinstance(value, bytes) and len(value) == 8:
            seconds = struct.unpack('<d', value)[0]
            if math.isfinite(seconds):
                return _MAC_EPOCH + timedelta(seconds=seconds)
        elif kind == 'dutc' and isinstance(value, int):
            return _DUTC_EPOCH + timedelta(seconds=value / 65536)
    except OverflowError:
        pass
    return value.hex() if isinstance(value, bytes) else value


@artifact_processor
def macosDSStoreEntries(context):
    data_headers = (('moDD (UTC)', 'datetime'), 'Item Name', 'Logical Size', 'Comment',
                    'Put Back Name', 'Put Back Location', 'Structure Codes', 'Source File')
    records, read = [], []
    for path in _stores(context):
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                entries, declared = read_ds_store(handle.read())
        except OSError as error:
            logfunc(f'Finder .DS_Store Entries: {relative} could not be opened: {error.strerror}')
            continue
        except DSStoreError as error:
            logfunc(f'Finder .DS_Store Entries: {relative} could not be read: {error}')
            continue
        if declared != len(entries):
            logfunc(f'Finder .DS_Store Entries: {relative} declares {declared} records and '
                    f'{len(entries)} were read')
        items = {}
        for name, code, kind, value in entries:
            items.setdefault(name, {})[code] = (kind, value)
        if items:
            read.append(path)
        for name, codes in items.items():
            dated = codes.get('moDD') or codes.get('modD')
            size = codes.get('lg1S') or codes.get('logS')
            text = {code: value for code, (kind, value) in codes.items() if kind == 'ustr'}
            records.append(((_date(*dated) if dated else '', name,
                             size[1] if size and size[0] == 'comp' else '',
                             text.get('cmmt', ''), text.get('ptbN', ''), text.get('ptbL', ''),
                             ', '.join(sorted(codes))), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)
