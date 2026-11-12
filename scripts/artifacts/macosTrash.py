__artifacts_v2__ = {
    "macosTrashPutBack": {
        "name": "Trash Put Back",
        "description": "Put Back records in the .DS_Store file of a Trash folder: the item's name "
                       "in the Trash and the name and location the Finder records for putting it "
                       "back.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Finder and Dock (macOS)",
        "notes": (
            'Reads the .DS_Store file in a folder named .Trash and in a subfolder of a .Trashes '
            'folder. Topher Kessler describes /Users/username/.Trash as holding the files on the '
            'boot disk that a user account threw away, and a .Trashes folder at the root of every '
            'drive as holding the files on that drive moved to the Trash (Reference: Topher '
            "Kessler, 'Trash problems in OS X? Reset it!', "
            'https://www.cnet.com/tech/computing/trash-problems-in-os-x-reset-it/). '
            "dleapp_macos_bigsur also holds a .Trash folder in iCloud Drive's Library/Mobile "
            'Documents/com~apple~CloudDocs folder. evidencelocker_macos14 holds a .Trashes folder, '
            "and the .DS_Store one folder below it gave 1 row. The file is read with DLEAPP's own .DS_Store reader, "
            "written from Wim Lewis's notes on the format (Reference: Wim Lewis, 'DS_Store "
            "Format', DSStoreFormat.pod in Mac-Finder-DSStore 1.00, "
            'https://cpan.metacpan.org/authors/id/W/WI/WIML/Mac-Finder-DSStore-1.00.tar.gz); on '
            'all 156 .DS_Store files of the two public images (6 on dleapp_macos_bigsur and 150 '
            'on the public MacBook Pro extraction) it returned the same records as the ds_store '
            'Python library, version 1.3.3, and read as many records as each file declares. '
            "Jonathon Poling describes the entry added to a Trash's .DS_Store for a file moved to "
            'the Trash as denoting the full path on disk where the file resided before being '
            'moved, and as part of how the Put Back feature works (Reference: Jonathon Poling, '
            "'Mac Dumpster Diving - Identifying Deleted File References in the Trash (.DS_Store) "
            "Files - Part 1', "
            'https://ponderthebits.com/2017/01/mac-dumpster-diving-identifying-deleted-file-references-in-the-trash-ds_store-files-part-1/), '
            "and Nicole Ibrahim's parser names the ptbL structure Trash Put Back Location and "
            'ptbN Trash Put Back Name (Reference: Nicole Ibrahim, DSStoreParser README, '
            'https://github.com/nicoleibrahim/DSStoreParser/blob/51871cbb400376f790dca8fa001cad72e45534ad/README.md#L101-L102). '
            'Item Name is the name a record carries, Put Back Name its ptbN value and Put Back '
            'Location its ptbL value, as stored, and only names with a ptbL or ptbN record are '
            'reported. On the 5 rows of the two public images every location is stored without a '
            'leading slash and begins System/Volumes/Data/, and Item Name and Put Back Name are '
            'identical on all 5 rows. Whether an item is still in the Trash is not checked here: '
            'on dleapp_macos_bigsur the iCloud Drive Trash folder holds IMG_0163.JPG, which has a '
            'row, and IMG_0188.JPG, which has none, and on the public MacBook Pro logical '
            'extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15) 3 of the 4 rows '
            "name items the user's Trash folder no longer holds, none of them in the Downloads "
            'folder its row names, while GoogleDrive.dmg is in that Trash with no row. Poling '
            'reported in 2017 that entries remained after an item was put back and reappeared '
            'after the Trash was emptied, until a restart; that is not tested here. When a '
            'logical extraction holds the file under Users and under System/Volumes/Data/Users, a '
            'row both copies hold is reported once and Source File lists both.'
        ),
        "paths": ('*/.Trash/.DS_Store', '*/.Trashes/*/.DS_Store'),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
        },
    },
    "macosTrashFiles": {
        "name": "Trash Files",
        "description": "Files under any folder named .Trash or .Trashes in a macOS input, with the size and "
                       "times the input records for each, listed without staging the files.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Trash (macOS)",
        "notes": (
            'One row per file under a folder named .Trash or .Trashes, at any depth, so a trashed folder is '
            "listed file by file and a .Trash folder inside a user's iCloud Drive folder is included. The "
            'folders are matched by name only. A folder has no row of its own, so a trashed folder that holds '
            'no file is not shown. From a disk image only regular files are listed, so a symbolic link has no '
            'row; a zip, tar or folder input lists a link as a row, and no link was under a Trash folder in the'
            " two zip images. The files are listed with the seeker's peek(), which reads none of a file's "
            'content here and stages nothing, so a trashed file is not copied into the report and is not in its'
            ' data folder; each file listed is named in the run log, and the located-at list gives the reported'
            " files' paths in the evidence. A single-file input cannot be listed this way, and the artifact "
            "says so in the run log. Path In Trash is the file's path below the .Trash or .Trashes folder and "
            'Trash Folder is the path of that folder; the split is at the last such folder in the path. Under a'
            ' .Trashes folder, Path In Trash starts with the folder directly below it, a numeric name on '
            'evidencelocker_macos14, whose meaning is not established here. The .DS_Store files the Trash Put '
            'Back artifact reads, the one directly in a .Trash folder and the one in a folder directly below a '
            '.Trashes folder, are left out. File Size and the four times are what the input records for the '
            "file, as DLEAPP's seeker reads them, and a time stored as 0 is shown blank. Time Source names "
            "where the seeker took the times: 'file system' on the three disk images and 'NTFS extra field', "
            'the extra field of the zip entry, on the two logical zip images. On a zip input, Modified (no '
            "zone, as stored) is the zip entry's own date and time, which carries no zone. A folder input gives"
            ' no times; tar, folder, FAT and exFAT inputs were not in the tested images. No column here is '
            'recorded as the time a file was moved to the Trash, and whether any of the four times changes when'
            " a file is moved to the Trash was not tested. No hash is computed. Note holds the seeker's message"
            ' when a zip, tar or folder entry could not be opened; from a disk image it is always blank, '
            'because no bytes are read. User is the folder after Users in the Trash Folder path, root under '
            'private/var/root, otherwise blank. When an input holds one file at the same path at the top of the'
            ' extraction and under System/Volumes/Data/ or System/Volumes/Update/mnt1/, with the same size, '
            'modified and created times, the copy with the shortest path is reported and the others are counted'
            ' in the run log: 2 on magnet2021_macos_bigsur and 54 on mvs2026_macbookpro_macos15. The copies are'
            ' matched on path, size and those two times; their content is not compared. Note held no value on '
            'any row of the five tested images. Changed (UTC) held no value on any row of the two zip images, '
            'and Modified (no zone, as stored) held no value on any row of the three disk images. Time Source '
            'and Trash Folder each held one value on every row of each tested image. User held no value on any '
            'row of evidencelocker_macos14, whose 1,839 rows are all under one .Trashes folder at the top of a '
            'volume, and User held one value on every row of each other image. Modified (UTC) and Created (UTC)'
            ' are identical on both rows of dleapp_macos_bigsur, on 1,838 of the 1,839 rows of '
            'evidencelocker_macos14 and on 52 of the 54 rows of mvs2026_macbookpro_macos15. On '
            'evidencelocker_macos14 1,837 of the 1,839 rows share one Modified (UTC) value, so they fall on one'
            ' instant on a timeline.'
        ),
        "paths": None,
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 1 row",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 1839 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 54 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 1 row",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_dsstore import DSStoreError, read_ds_store
from scripts.macos_plists import canonical_relative
from scripts.macos_powerlog import merge_sources
from scripts.search_files import PeekUnsupported


def _stores(context):
    """Staged .DS_Store files (not directories)."""
    return sorted({str(path) for path in context.get_files_found()
                   if os.path.basename(str(path)) == '.DS_Store' and not os.path.isdir(str(path))})


@artifact_processor
def macosTrashPutBack(context):
    data_headers = ('Item Name', 'Put Back Name', 'Put Back Location', 'Source File')
    records, read = [], []
    for path in _stores(context):
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                entries, declared = read_ds_store(handle.read())
        except OSError as error:
            logfunc(f'Trash Put Back: {relative} could not be opened: {error.strerror}')
            continue
        except DSStoreError as error:
            logfunc(f'Trash Put Back: {relative} could not be read: {error}')
            continue
        if declared != len(entries):
            logfunc(f'Trash Put Back: {relative} declares {declared} records and {len(entries)} were read')
        items = {}
        for name, code, kind, value in entries:
            if code in ('ptbL', 'ptbN') and kind == 'ustr':
                items.setdefault(name, {})[code] = value
        if items:
            read.append(path)
        for name, fields in items.items():
            records.append(((name, fields.get('ptbN', ''), fields.get('ptbL', '')), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)


_TRASH_PATTERNS = ('*/.Trash/*', '*/.Trashes/*')


def _instant(value):
    """Unix seconds as an aware UTC datetime, or '' when there is none."""
    if value in (None, ''):
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError, TypeError):
        return ''


def _trash_user(folder):
    """The folder after Users in a path inside the evidence, root under private/var/root, or ''."""
    parts = folder.split('/')
    for index, part in enumerate(parts[:-1]):
        if part == 'Users':
            return parts[index + 1]
        if part == 'private' and parts[index + 1:index + 3] == ['var', 'root']:
            return 'root'
    return ''


def _trash_parts(path):
    """(trash folder, path below it) for a member path, split at its last .Trash or .Trashes folder."""
    parts = path.replace('\\', '/').split('/')
    for index in range(len(parts) - 2, -1, -1):
        if parts[index] in ('.Trash', '.Trashes'):
            return '/'.join(parts[:index + 1]), '/'.join(parts[index + 1:])
    return '', path


@artifact_processor
def macosTrashFiles(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Created (UTC)', 'datetime'), ('Accessed (UTC)', 'datetime'),
                    ('Changed (UTC)', 'datetime'), 'Modified (no zone, as stored)', 'Path In Trash',
                    'File Size (bytes)', 'Time Source', 'Note', 'Trash Folder', 'User')
    data_list, sources = [], []
    seeker = context.get_seeker()
    if seeker is None or not hasattr(seeker, 'peek'):
        logfunc('Trash Files: this input gives no way to list a file without staging it')
        return data_headers, data_list, ''
    items = {}
    for pattern in _TRASH_PATTERNS:
        try:
            peeked = seeker.peek(pattern, 0)
        except PeekUnsupported as exc:
            logfunc(f'Trash Files: {exc}')
            return data_headers, data_list, ''
        for item in peeked:
            items.setdefault(str(item.path).replace('\\', '/'), item)
    views, repeats = set(), 0
    # Shortest path first, so the copy at the top of the extraction is the one reported.
    for path in sorted(items, key=lambda value: (len(value), value)):
        item = items[path]
        folder, below = _trash_parts(path)
        if not folder:
            continue
        # The .DS_Store files the Trash Put Back artifact reads: .Trash/.DS_Store and .Trashes/<folder>/.DS_Store.
        parts = below.split('/')
        in_trashes = folder == '.Trashes' or folder.endswith('/.Trashes')
        if parts[-1] == '.DS_Store' and len(parts) == (2 if in_trashes else 1):
            continue
        times = getattr(item.info, 'times', None)
        view_key = (canonical_relative(path), item.size, getattr(times, 'modified', None),
                    getattr(times, 'created', None))
        if view_key in views:
            repeats += 1
            continue
        views.add(view_key)
        data_list.append((
            _instant(getattr(times, 'modified', None)), _instant(getattr(times, 'created', None)),
            _instant(getattr(times, 'accessed', None)), _instant(getattr(times, 'changed', None)),
            getattr(times, 'modified_no_zone', None) or '', below, item.size, getattr(times, 'source', '') or '',
            item.note or '', folder, _trash_user(folder)))
        sources.append(path)
    if repeats:
        logfunc(f'Trash Files: {repeats} file(s) held again at the same path in another view of the volume '
                '(System/Volumes/Data or System/Volumes/Update/mnt1), with the same size, modified and created '
                'times, are reported once')
    order = sorted(range(len(data_list)), key=lambda index: (data_list[index][9], data_list[index][5]))
    return data_headers, [data_list[index] for index in order], '\n'.join(sources[index] for index in order)
