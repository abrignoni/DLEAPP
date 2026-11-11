"""The volume status database /private/var/db/volinfo.database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosVolumeStatusDatabase": {
        "name": "Volume Status Database",
        "description": (
            'Records of /private/var/db/volinfo.database, the volume status database '
            'vsdbutil(8) manipulates: one row per record with the volume UUID, the status '
            'flags as stored, and whether the permissions bit is set.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "File System (macOS)",
        "notes": (
            "The layout is from Apple's published vsdbutil source (diskdev_cmds-757, "
            'vsdbutil.tproj/vsdbutil_main.c, struct VSDBEntry): 47-byte records, each a '
            '36-character volume UUID, a colon, a space, 8 hex digits of status flags and a '
            'newline. The file is read the way that source reads it: record by record from '
            'the start, stopping at the first record without those separators; the bytes '
            'from that record to the end of the file are counted in the run log and not '
            'reported. A file whose first record has the 16-character key of the older '
            'layout (struct VSDBEntry64, which vsdbutil converts when it opens the file) is '
            'logged and not read; neither of the two corpus images that hold the file has '
            "that layout, so that branch has run only on test bytes. Record is the record's "
            'position in the file. Status Flags is the 8 characters as stored; a byte that '
            'is not ASCII shows as a replacement character. Permissions is enabled when bit '
            '0x00000001 is set and disabled when it is not, the words vsdbutil -c prints; '
            'the source names that bit VOLUME_USEPERMISSIONS and defines no other. '
            'Permissions is blank when the flags are not hex digits. Volume UUID is not '
            'matched to a volume name or a device here. From the same source, not from a '
            'run: vsdbutil -a sets the bit and -d clears it, each appending a record at the '
            'end of the file when the UUID has none; -i does what -a does for every mounted '
            'hfs and apfs volume; -x removes a record and moves the later ones up. The '
            'launchd job com.apple.vsdbutil published beside it is declared to run vsdbutil '
            '-i while the file does not exist; whether it runs on a given system is not '
            "established, and evidencelocker_macos14 holds that job's property list and no "
            'file. diskarbitrationd (DiskArbitration-535.0.10, vsdb.c, DASupport.m and '
            'DAMount.c) reads the file and adds owners or noowners to the mount options of '
            'a volume whose UUID has a record; later code there can put other options ahead '
            'of it. It runs vsdbutil -a or -d when a client asks it to (DAPrivate.c). '
            'hfs.util (hfs-715.100.10, hfs_util/hfsutil_main.c) has its own database code '
            'that can write records; its record has a 37-byte key and is 48 bytes long, and '
            'a file holding such a record is not read from that record on, with the bytes '
            'counted in the run log. No corpus file holds one. Whether any program outside '
            'this published source writes the file is not established. Measured on a '
            'private macOS 27.2 system (build 26B123) on 11 November 2026 with two newly '
            'created disk images, one HFS+ and one APFS: mounting them added no record; '
            'vsdbutil -a on one and diskutil enableOwnership on the other each added one '
            'record with flags 00000001; vsdbutil -d and diskutil disableOwnership rewrote '
            "that record's flags to 00000000 in place; both records were still in the file "
            'after the images were ejected; vsdbutil -x removed them and the file returned '
            "to its starting bytes. The file's modification time moved when a record was "
            'added, when its flags changed and when it was removed, and did not move on '
            "vsdbutil -c. That system's own records are not published. A record says the "
            'database holds an ownership setting for a volume with that UUID. In the '
            'published source a record is written by vsdbutil -a, -d or -i and by hfs.util; '
            'a record alone does not show who or what asked for it. It carries no time of '
            'its own, a record stays after the volume is ejected, and a volume with no '
            'record may still have been mounted. What wrote the records on the public '
            'images is not established. File Modified (UTC) is the modification time the '
            "input records for the file: the volume's time on a raw image, a zip member's "
            'NTFS (0x000a) or extended timestamp (0x5455) field or, in a CLBX zip, the '
            "member's metadata record, or a tar member's time; it is blank otherwise, and "
            'for a folder input, whose times are those of the copy. It is the same on every '
            'record of a file: the time the file last changed, not the time any one record '
            'was written. On the public MacBook Pro logical extraction (macOS 15.4, corpus '
            'key mvs2026_macbookpro_macos15) the file held 6 records; File Modified (UTC) '
            'held one value on all 6 rows, Status Flags held 00000001 on all 6 rows and '
            'Permissions held enabled on all 6 rows. That extraction holds the file under '
            'private/var/db and again under System/Volumes/Data/private/var/db with the '
            'same bytes and the same recorded modification time, so it is read once and the '
            'run log names both. Files that differ in bytes or in recorded time are each '
            'read, one after the other with Record starting again at 1; the table has no '
            "column naming the file, the run log and the report's source line name them, "
            'and no corpus image has that case. On dleapp_macos_bigsur (macOS 11.2.1, raw '
            'image) the file held 6 records; File Modified (UTC) held one value on all 6 '
            'rows, Status Flags held 00000001 on all 6 rows and Permissions held enabled on '
            'all 6 rows. On evidencelocker_macos14 (macOS 14.6.1, raw image) private/var/db '
            'holds files and no volinfo.database. On magnet2021_macos_bigsur (macOS 11.2.1, '
            'zip) private/var/db is an empty folder entry, so that zip does not show '
            'whether the system had the file. Neither yields a row.'
        ),
        "paths": ('*/var/db/volinfo.database',),
        "output_types": "standard",
        "artifact_icon": "hard-drive",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 6 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 | 6 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows",
        },
    },
}

import hashlib
import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'Volume Status Database'
# struct VSDBEntry in vsdbutil_main.c (diskdev_cmds-757): a 36-character volume UUID, ':',
# a space, 8 hex digits of status flags and a newline.
_KEY = 36
_RECORD = _KEY + 2 + 8 + 1
# struct VSDBEntry64, the older layout vsdbutil converts when it opens one: a 16-character key.
_OLD_KEY = 16
_OLD_RECORD = _OLD_KEY + 2 + 8 + 1
_USE_PERMISSIONS = 0x00000001  # VOLUME_USEPERMISSIONS, the one status bit the source defines
_HEX = frozenset(b'0123456789ABCDEFabcdef')
# Seekers whose recorded modification time is the evidence's own: a raw image's volume
# times, and the times a zip or tar recorded for its member. A folder input records the
# times of the copy on the examiner's disk.
_EVIDENCE_TIMES = ('FileSeekerRaw', 'FileSeekerZip', 'FileSeekerTar')


def _framed(record, key):
    """True when record has the separators the source checks: ':' and a space after the key
    and a newline at the end."""
    return (len(record) == key + 11 and record[key:key + 1] == b':'
            and record[key + 1:key + 2] == b' ' and record[-1:] == b'\n')


def parse_database(data):
    """(records, unread, layout) from the bytes of a volume status database.

    records is a list of (position, volume UUID, status flags as stored, permissions), read
    the way vsdbutil reads the file: fixed 47-byte records from the start, stopping at the
    first one that lacks its separators. permissions is 'enabled' or 'disabled' from bit
    0x00000001 of the flags, the words vsdbutil -c prints, and '' when the flags are not 8
    hex digits. unread is the number of bytes after the last record read. layout is
    'current', 'old' for a file whose first record has the 16-character key of the older
    layout (not read), or 'empty'.
    """
    if not data:
        return [], 0, 'empty'
    if not _framed(data[:_RECORD], _KEY) and _framed(data[:_OLD_RECORD], _OLD_KEY):
        return [], len(data), 'old'
    records, offset = [], 0
    while offset + _RECORD <= len(data):
        record = data[offset:offset + _RECORD]
        if not _framed(record, _KEY):
            break
        flags = record[_KEY + 2:_KEY + 10]
        permissions = ''
        if all(byte in _HEX for byte in flags):
            permissions = 'enabled' if int(flags, 16) & _USE_PERMISSIONS else 'disabled'
        records.append((len(records) + 1, record[:_KEY].decode('ascii', 'replace'),
                        flags.decode('ascii', 'replace'), permissions))
        offset += _RECORD
    return records, len(data) - offset, 'current'


def _modified(context, path):
    """The modification time the seeker recorded for a staged file, as a UTC datetime, when
    that time is the evidence's; '' otherwise."""
    seeker = context.get_seeker() if hasattr(context, 'get_seeker') else None
    if type(seeker).__name__ not in _EVIDENCE_TIMES:
        return ''
    info = getattr(seeker, 'file_infos', {}).get(path)
    value = getattr(info, 'modification_date', None)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return ''
    return datetime.fromtimestamp(value, timezone.utc)


@artifact_processor
def macosVolumeStatusDatabase(context):
    data_headers = (('File Modified (UTC)', 'datetime'), 'Record', 'Volume UUID',
                    'Status Flags', 'Permissions')
    found = sorted(str(path) for path in context.get_files_found() if os.path.isfile(str(path)))
    if not found:
        return data_headers, [], ''
    # An extraction can hold the one file under more than one folder view. Files with the
    # same bytes and the same recorded modification time are read once and named in the log.
    copies = {}
    for path in found:
        with open(path, 'rb') as handle:
            data = handle.read()
        key = (hashlib.sha256(data).digest(), _modified(context, path))
        copies.setdefault(key, (data, []))[1].append(path)
    data_list = []
    for (_digest, modified), (data, paths) in copies.items():
        relatives = [context.get_relative_path(path) for path in paths]
        named = ', '.join(relatives)
        if len(paths) > 1:
            logfunc(f'{_LABEL}: {len(paths)} files with the same bytes and modification time '
                    f'read once: {named}')
        records, unread, layout = parse_database(data)
        if len(copies) > 1:
            logfunc(f'{_LABEL}: {len(records)} record(s) read from {named}')
        if layout == 'empty':
            logfunc(f'{_LABEL}: {named} is empty (0 bytes)')
        elif layout == 'old':
            logfunc(f'{_LABEL}: {named} ({len(data)} bytes) starts with a record in the older '
                    '16-character-key layout; not read')
        elif unread:
            logfunc(f'{_LABEL}: {named}: {unread} byte(s) after record {len(records)} did not '
                    'read as a record; not reported')
        for position, uuid, flags, permissions in records:
            data_list.append((modified, position, uuid, flags, permissions))
    return data_headers, data_list, '\n'.join(found)
