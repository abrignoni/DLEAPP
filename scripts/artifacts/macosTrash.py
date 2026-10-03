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
            'Documents/com~apple~CloudDocs folder, and no public image holds a .Trashes folder, '
            "so that path is not exercised. The file is read with DLEAPP's own .DS_Store reader, "
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
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_dsstore import DSStoreError, read_ds_store
from scripts.macos_powerlog import merge_sources


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
