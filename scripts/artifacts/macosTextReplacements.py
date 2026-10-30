__artifacts_v2__ = {
    "macosTextReplacements": {
        "name": "Keyboard Text Replacements (macOS)",
        "description": "Text replacement shortcuts and the phrases they expand to, from each user's "
                       "Library/KeyboardServices/TextReplacements.db, with the CloudKit record times "
                       "and the ModifiedByDevice value from each entry's CloudKit record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Keyboard (macOS)",
        "notes": "Reads ZTEXTREPLACEMENTENTRY in each user's Library/KeyboardServices/TextReplacements.db "
                 "and its -wal. Timestamp is ZTIMESTAMP, which the store's own Core Data model "
                 "(Z_MODELCACHE) declares as a date attribute (attribute type 900), read as seconds since "
                 "2001-01-01 UTC. What it marks is not established: it travels with the entry, so the "
                 "same Unique Name and Timestamp appear on hc_ios18_7 and hc_ios26, whose extraction "
                 "folders carry different device identifiers, and on ctf2020_ios12 one entry's Timestamp "
                 "falls in 1989 while its CloudKit times fall in March 2020. CloudKit Record Created, "
                 "CloudKit Record Modified and Modified By Device are the RecordCtime, RecordMtime and "
                 "ModifiedByDevice entries of ZREMOTERECORDINFO, an NSKeyedArchiver archive of the "
                 "entry's CloudKit record whose RecordType was TextReplacementEntry and whose zone was "
                 "TextReplacements on every tested row; they are named from the archive's own keys, and "
                 "no Apple documentation of those keys was found. Unique Name is ZUNIQUENAME, which "
                 "equalled the CloudKit record name (RecordID) on every tested row. Modified By Device is "
                 "reported as stored and is not a stable record of which device last changed the entry: "
                 "on hickman_ios15 and iphone11_ios17 the entry had the same Unique Name, Timestamp and "
                 "CloudKit times as on hickman_ios13 and hickman_ios14 and a different Modified By Device "
                 "value, and the same held for one entry on felix23_ios16 and felix_ios17. Was Deleted "
                 "(as stored) is ZWASDELETED and held 0 on every tested row; ZNEEDSSAVETOCLOUD held 0 on "
                 "every tested row and is not reported. User is the folder after Users in the source "
                 "path, or root for a store under private/var/root. When a logical extraction holds the "
                 "same file under Users/ and under System/Volumes/Data/Users/ or "
                 "System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read again and the run "
                 "log counts it. A TextReplacements.db in a Library nested inside another one, such as an "
                 "app's Containers/<id>/Data/Library, is not read and is named in the run log. On the "
                 "tested extractions: 1 row on magnet2021_macos_bigsur (three copies of one file) and 1 "
                 "row on mvs2026_macbookpro_macos15 (two copies). The mvs2026_macbookpro_macos15 row had "
                 "the same Unique Name, Timestamp and CloudKit times as the row on the iPhone image "
                 "iphone14plus_ios18. The examples above (ctf2020_ios12 and the HC, Hickman and Felix "
                 "images) are iOS images, tested with iLEAPP's twin of this artifact. Not read: the "
                 "ZTRCLOUDKITSYNCSTATE table (a pull flag and a change token) and each user's "
                 "Library/Preferences/com.apple.textInput.keyboardServices.textReplacement.plist, which "
                 "holds CloudKit sync state.",
        "paths": ('*/Library/KeyboardServices/TextReplacements.db*',),
        "output_types": "standard",
        "artifact_icon": "keyboard",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 1 row",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 row",
        },
    }
}

import os
import plistlib

from scripts.ilapfuncs import artifact_processor, does_table_exist_in_db, get_sqlite_db_records, logfunc
from scripts.macos_plists import (fold_view_rows, mac_absolute_utc, resolve_keyed_archive, unique_sources,
                                  user_from_path)

_LABEL = 'Keyboard Text Replacements'
_FOLDER = '/Library/KeyboardServices/'
_QUERY = ('SELECT ZTIMESTAMP, ZSHORTCUT, ZPHRASE, ZWASDELETED, ZUNIQUENAME, ZREMOTERECORDINFO '
          'FROM ZTEXTREPLACEMENTENTRY ORDER BY ZTIMESTAMP, Z_PK')


def _in_a_home_library(relative):
    """True when KeyboardServices is in a home folder's own Library, not in a Library nested
    inside another one, such as an app's Containers/<id>/Data/Library."""
    path = '/' + str(relative).replace('\\', '/').lstrip('/')
    index = path.find(_FOLDER)
    return index >= 0 and 'Library' not in path[:index].split('/')


def _record_fields(blob):
    """RecordCtime, RecordMtime and ModifiedByDevice from the CloudKit record's system fields,
    which are keyed archive entries at the archive's $top level; '' for each one absent."""
    if not isinstance(blob, (bytes, bytearray)) or not bytes(blob).startswith(b'bplist00'):
        return '', '', ''
    try:
        archive = plistlib.loads(bytes(blob))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError, RecursionError):
        return '', '', ''
    if not isinstance(archive, dict) or '$objects' not in archive:
        return '', '', ''
    values = [resolve_keyed_archive(archive, root=key) for key in ('RecordCtime', 'RecordMtime', 'ModifiedByDevice')]
    created, modified, device = (value if value is not None else '' for value in values)
    return created, modified, device if isinstance(device, str) else ''


@artifact_processor
def macosTextReplacements(context):
    data_headers = (
        ('Timestamp', 'datetime'), ('CloudKit Record Created', 'datetime'),
        ('CloudKit Record Modified', 'datetime'), 'Shortcut', 'Phrase', 'Was Deleted (as stored)',
        'Modified By Device (as stored)', 'Unique Name', 'User', 'Source File')
    databases = []
    for path in context.get_files_found():
        if os.path.basename(str(path)) != 'TextReplacements.db':
            continue
        if not _in_a_home_library(context.get_relative_path(path)):
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} is not in a home folder\'s '
                    'Library/KeyboardServices, not read')
            continue
        databases.append(path)
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)

    data_list, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'ZTEXTREPLACEMENTENTRY'):
            logfunc(f'{_LABEL}: no ZTEXTREPLACEMENTENTRY table in {relative}')
            continue
        read.append(path)
        user = user_from_path(relative)
        for row in get_sqlite_db_records(path, _QUERY):
            created, modified, device = _record_fields(row['ZREMOTERECORDINFO'])
            data_list.append((
                mac_absolute_utc(row['ZTIMESTAMP']), created, modified, row['ZSHORTCUT'] or '',
                row['ZPHRASE'] or '', '' if row['ZWASDELETED'] is None else str(row['ZWASDELETED']),
                device, row['ZUNIQUENAME'] or '', user, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
