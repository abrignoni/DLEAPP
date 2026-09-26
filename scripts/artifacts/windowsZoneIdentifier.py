"""Zone.Identifier alternate data streams on NTFS, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The stream is text of key=value lines under a [ZoneTransfer] section. The raw
image seeker lists a stream as the member ``<file>:<stream>``, which only a
pattern naming the stream reaches, so this artifact is handed the streams and
never the files they are attached to.
"""

__artifacts_v2__ = {
    "windowsZoneIdentifier": {
        "name": "Zone.Identifier Streams",
        "description": "The Zone.Identifier alternate data stream of each file that carries "
                       "one: the file it is attached to, its ZoneId with that zone's URLZONE "
                       "name, and the other values the stream holds, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per Zone.Identifier stream, read from a raw image or E01 through the "
                 "raw image seeker, which names a stream <file>:<stream>, or from a folder or "
                 "archive holding a file whose name ends in :Zone.Identifier. File is the path "
                 "of the file the stream is attached to. The stream is decoded by its byte order "
                 "mark and otherwise as UTF-8; each key=value line is read. ZoneId, HostUrl and "
                 "ReferrerUrl are those keys' values as stored, blank where the stream has no "
                 "such key, and Other Values holds every other key as key=value, prefixed with "
                 "its section when that is not ZoneTransfer. Zone names ZoneId 0 to 4 after the "
                 "URLZONE constants (Reference: Wine include/urlmon.idl, "
                 "https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/include/urlmon.idl#L1458-L1470;"
                 " Microsoft's own URLZONE page could not be fetched from the build environment "
                 "to cross-check) and is blank for any other value. File Created and File "
                 "Modified are the $STANDARD_INFORMATION created and modified times of the file "
                 "the stream is attached to, as the raw image reader reports them, since NTFS "
                 "keeps no times for a stream; they are blank for a folder or archive input, "
                 "whose copy's times are not the evidence's. The reader hands them over as "
                 "floating-point seconds, so they can differ by a microsecond from the same "
                 "file's SI times in the MFT artifact, which reads the FILETIME itself. What wrote a stream, and whether "
                 "the file still holds what it held when the stream was written, is not "
                 "recorded in it. Tested on the NTFS fixture written by mkntfs and ntfs-3g that "
                 "the raw image seeker tests read (admin/test/data/raw_images/ntfs-streams.img.gz),"
                 " which holds two such streams: 2 rows, both ZoneId 3. No Windows-written "
                 "Zone.Identifier stream has been run through this artifact; the one real "
                 "stream at hand, 26 bytes resident in a deleted record of a public Windows XP "
                 "$MFT sample, is decoded by the unit test.",
        "paths": ('*:Zone.Identifier',),
        "output_types": "standard",
        "artifact_icon": "world-download",
    }
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import URL_ZONES, read_zone_identifier

_LABEL = 'Zone.Identifier'
_SUFFIX = ':Zone.Identifier'
_NAMED = ('ZoneId', 'HostUrl', 'ReferrerUrl')


def _instant(value):
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def zone_row(values):
    """(ZoneId, Zone, HostUrl, ReferrerUrl, Other Values) from the parsed lines."""
    named, other = {}, []
    for section, key, value in values:
        if section == 'ZoneTransfer' and key in _NAMED and key not in named:
            named[key] = value
        else:
            prefix = '' if section == 'ZoneTransfer' else f'[{section}] '
            other.append(f'{prefix}{key}={value}')
    zone_id = named.get('ZoneId', '')
    try:
        zone = URL_ZONES.get(int(zone_id), '')
    except ValueError:
        zone = ''
    return (zone_id, zone, named.get('HostUrl', ''), named.get('ReferrerUrl', ''),
            '; '.join(other))


@artifact_processor
def windowsZoneIdentifier(context):
    data_headers = (('File Created', 'datetime'), ('File Modified', 'datetime'), 'File',
                    'ZoneId', 'Zone', 'HostUrl', 'ReferrerUrl', 'Other Values')
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    # Only the raw image seeker lists streams, and only its times are the
    # evidence's: a folder or archive gives the times of the copy.
    from_image = hasattr(seeker, 'stream_list')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        info = infos.get(path)
        member = info.source_path if info else context.get_relative_path(path)
        if not member.endswith(_SUFFIX):
            continue
        try:
            with open(path, 'rb') as handle:
                raw = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {member}: {type(exc).__name__}')
            continue
        created = modified = ''
        if from_image and info:
            created, modified = _instant(info.creation_date), _instant(info.modification_date)
        data_list.append((created, modified, member[:-len(_SUFFIX)])
                         + zone_row(read_zone_identifier(raw)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
