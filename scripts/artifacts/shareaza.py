"""Shareaza library files, library folders and unfinished downloads, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Formats are read by scripts/shareaza.py, which follows the Shareaza 2.7.10.2 source it names.
"""

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import user_from_path
from scripts.shareaza import TRISTATE, ShareazaFormatError, read_download, read_library

__artifacts_v2__ = {
    "shareazaLibraryFiles": {
        "name": "Shareaza Library Files",
        "description": "Files in Shareaza's library, read from Library1.dat and Library2.dat: name, folder, size and "
                       "hashes, whether the file was still in a library folder or kept as a ghost record after it "
                       "left one, and the upload counts, rating and comments Shareaza kept for it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Shareaza",
        "notes": "Files are read as Shareaza 2.7.10.2 reads them, following its source at SVN revision 9696 (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/). The known data (windows11_arm_shareaza_known_20261108) is Shareaza 2.7.10.2 x64 on Windows 11 ARM64, with every network, auto-connect and the firewall exception switched off in its settings; it opened no socket in the run kept. User is the account folder name taken from the file path. Shareaza keeps its library in two files and saves to them in turn, writing the time of the save in the first 8 bytes after the save completes (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Library.cpp#l407); when it starts it reads the copy with the later time and falls back to the other (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Library.cpp#l274). Both copies are read here and a row is reported once, with Found In naming the copies that hold it; the older Library.dat, which has no save time, is read too. The library files sit in the Data folder of Shareaza's user folder, by default AppData\\\\Roaming\\\\Shareaza (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Settings.cpp#l640); a user folder moved elsewhere is matched only if it is still named Shareaza. A file that stops parsing is logged with the offset, and the rows read before it are kept. One row per file record: files in a library folder (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFolder.cpp#l332) and ghost records (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/LibraryMaps.cpp#l820). Status is Ghost for a record kept after its file left the library folders: with the CreateGhosts setting on, its default (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Settings.cpp#l161), Shareaza keeps a file that disappears from a folder scan as a ghost (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFolder.cpp#l555), records the time it became one and, when the file had no rating or comment, sets its comment to Ghost File (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFile.cpp#l1250, #l1294). Ghost records keep the name, size and hashes but no folder. On the known data the file deleted with Shareaza closed came back as a Ghost row with Comments Ghost File and the time Shareaza scanned the folder after it started; the file still in the folder was the In library folder row. File Modified (UTC) is the file's last write time as Shareaza recorded it at its last scan (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFile.cpp#l1198); on the known data it matched the test file's last write time. Became Ghost (UTC) is the same field for a ghost, overwritten with the time it became one. Added to History (UTC) is the time in Shareaza's recent-files list, which it adds to when its library builder adds a file (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/LibraryBuilder.cpp#l679) and prunes after 3 days or 32 entries by default (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/LibraryHistory.cpp#l180, https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Settings.cpp#l167); a ghost is removed from it (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFile.cpp#l1294). It was blank on the ghost row of the known data. SHA-1, Tiger Tree Root, MD5, eD2K and BitTorrent Info Hash are shown in hexadecimal (Shareaza shows SHA-1 and Tiger in base32); on the known data SHA-1, MD5 and eD2K matched hashes computed from the test files, Tiger was not recomputed, and BitTorrent Info Hash was empty on both rows because neither file came from a torrent. Shared (as stored) is the file's own sharing value: Unknown means it follows its folder, Yes and No override it (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFile.cpp#l268; values in https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Shareaza.idl#l39). Folder Shared (as stored) is the folder's value, blank for a ghost. On the known data Shared was Unknown and Folder Shared Yes on the row in a folder. Search Hits, Uploads, Rating, Comments (other than Ghost File), Share Tags, Metadata and Sources were zero or empty on both rows of the known data, which never connected: Share Tags, Metadata and Sources were empty on all rows, so these columns are source-verified only. Library Index is Shareaza's own number for the file. Thumbnails in Shareaza.db3 and hash trees in TigerTree.dat are not read. A row records a file Shareaza had in its library, not that it was shared on a network or that anyone downloaded it.",
        "paths": ('*/Shareaza/Data/Library1.dat', '*/Shareaza/Data/Library2.dat', '*/Shareaza/Data/Library.dat'),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "windows11_arm_shareaza_known_20261108": "Windows 11 build 26200 (ARM64), Shareaza 2.7.10.2 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Shareaza files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no Shareaza files matched)",
        },
    },
    "shareazaLibraryFolders": {
        "name": "Shareaza Library Folders",
        "description": "Folders in Shareaza's library and whether each was set to be shared, read from Library1.dat "
                       "and Library2.dat.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Shareaza",
        "notes": "Files are read as Shareaza 2.7.10.2 reads them, following its source at SVN revision 9696 (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/). The known data (windows11_arm_shareaza_known_20261108) is Shareaza 2.7.10.2 x64 on Windows 11 ARM64, with every network, auto-connect and the firewall exception switched off in its settings; it opened no socket in the run kept. User is the account folder name taken from the file path. Shareaza keeps its library in two files and saves to them in turn, writing the time of the save in the first 8 bytes after the save completes (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Library.cpp#l407); when it starts it reads the copy with the later time and falls back to the other (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Library.cpp#l274). Both copies are read here and a row is reported once, with Found In naming the copies that hold it; the older Library.dat, which has no save time, is read too. The library files sit in the Data folder of Shareaza's user folder, by default AppData\\\\Roaming\\\\Shareaza (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Settings.cpp#l640); a user folder moved elsewhere is matched only if it is still named Shareaza. A file that stops parsing is logged with the offset, and the rows read before it are kept. One row per library folder (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/SharedFolder.cpp#l332), with Found In naming each copy and its save time. Shareaza adds its download, collection and torrent folders to a new library itself (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Library.cpp#l320), so those rows do not show that a user added them. Shared (as stored) is the folder's sharing value (Yes, No, or Unknown, https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Shareaza.idl#l39). On the known data the three folders were the download folder set by the test script and the Collections and Torrents folders Shareaza created: Shared (as stored) held Yes on all 3 rows, Found In held the same two copies on all 3 rows, and User held one value on all rows.",
        "paths": ('*/Shareaza/Data/Library1.dat', '*/Shareaza/Data/Library2.dat', '*/Shareaza/Data/Library.dat'),
        "output_types": ["standard"],
        "artifact_icon": "folder",
        "sample_data": {
            "windows11_arm_shareaza_known_20261108": "Windows 11 build 26200 (ARM64), Shareaza 2.7.10.2 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Shareaza files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no Shareaza files matched)",
        },
    },
    "shareazaDownloads": {
        "name": "Shareaza Unfinished Downloads",
        "description": "Downloads Shareaza had not finished, one per .sd file: file name, size and the hashes it was "
                       "looking for.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Shareaza",
        "notes": "Files are read as Shareaza 2.7.10.2 reads them, following its source at SVN revision 9696 (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/). The known data (windows11_arm_shareaza_known_20261108) is Shareaza 2.7.10.2 x64 on Windows 11 ARM64, with every network, auto-connect and the firewall exception switched off in its settings; it opened no socket in the run kept. User is the account folder name taken from the file path. One row per .sd file found anywhere in the extraction, since the folder is a setting (by default AppData\\\\Local\\\\Shareaza\\\\Incomplete, https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Settings.cpp#l646; the file is named after the download, https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Download.cpp#l857). Only files that start with SDL and a format version from 11 to 42 are read (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/Download.cpp#l966); others, including older versions Shareaza reads another way, are logged and skipped. .sd.sav copies are not matched. Only the first fields are read: the file name, size and the hashes the download is looking for (https://sourceforge.net/p/shareaza/code/9696/tree/trunk/shareaza/DownloadBase.cpp#l68). The sources, the parts already downloaded, torrent data and whether the download was paused come later in the file and are not read. On the known data the one row matched the magnet link the test script passed: the file name, 60000 bytes and its SHA-1; Tiger Tree Root, MD5, eD2K and BitTorrent Info Hash were empty because the link carried only a SHA-1. User was empty because the test folder was not under a Users folder. A row records a download Shareaza had queued, not that any data was received.",
        "paths": ('*.sd',),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "windows11_arm_shareaza_known_20261108": "Windows 11 build 26200 (ARM64), Shareaza 2.7.10.2 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Shareaza files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no Shareaza files matched)",
        },
    },
}


def _libraries(context, name):
    """Each library file read, grouped by its Data folder: {data folder: [(file name, result)]}."""
    found = sorted(str(f) for f in context.get_files_found()
                   if os.path.isfile(str(f)) and os.path.basename(str(f)).lower() in
                   ('library1.dat', 'library2.dat', 'library.dat'))
    groups, sources = {}, []
    for path in found:
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{name}: {relative} not read ({exc})')
            continue
        base = os.path.basename(path)
        try:
            result = read_library(data, has_header=base.lower() != 'library.dat')
            if not result['complete']:
                logfunc(f'{name}: {relative} has bytes after the archive end')
        except ShareazaFormatError as exc:
            result = exc.partial
            logfunc(f'{name}: {relative} stopped ({exc}); keeping the {len(result["files"])} files, '
                    f'{len(result["ghosts"])} ghosts and {len(result["folders"])} folders read before it')
        groups.setdefault(os.path.dirname(path), []).append((base, result, user_from_path(relative)))
        sources.append(path)
    return groups, sources


def _copy_label(base, result):
    saved = result['saved']
    return f'{base} (saved {saved:%Y-%m-%d %H:%M:%S} UTC)' if saved else base


@artifact_processor
def shareazaLibraryFiles(context):
    data_headers = (('File Modified (UTC)', 'datetime'), ('Became Ghost (UTC)', 'datetime'),
                    ('Added to History (UTC)', 'datetime'), 'Status', 'File Name', 'Folder',
                    ('File Size (bytes)', 'number'), ('SHA-1', 'hash'), ('Tiger Tree Root', 'hash'), ('MD5', 'hash'),
                    ('eD2K', 'hash'), ('BitTorrent Info Hash', 'hash'), 'Shared (as stored)',
                    'Folder Shared (as stored)', ('Search Hits', 'number'), ('Uploads', 'number'),
                    ('Rating', 'number'), 'Comments', 'Share Tags', 'Metadata', 'Sources', ('Library Index', 'number'),
                    'Found In', 'User')
    groups, sources = _libraries(context, 'Shareaza Library Files')
    data_list = []
    for _folder, copies in sorted(groups.items()):
        rows = {}
        for base, result, user in copies:
            for status, records in (('In library folder', result['files']), ('Ghost', result['ghosts'])):
                for record in records:
                    key = (status, record['index'], record['sha1'], record['name'])
                    entry = rows.setdefault(key, {'record': record, 'status': status, 'copies': [], 'user': user,
                                                  'history': ''})
                    entry['copies'].append(base)
                    if record['index'] in result['history'] and not entry['history']:
                        entry['history'] = result['history'][record['index']]
        for entry in rows.values():
            record, ghost = entry['record'], entry['status'] == 'Ghost'
            folder_shared = record['folder_shared']
            data_list.append((
                '' if ghost else record['time'], record['time'] if ghost else '', entry['history'],
                entry['status'], record['name'], record['folder'], record['size'], record['sha1'], record['tiger'],
                record['md5'], record['ed2k'], record['bth'], TRISTATE.get(record['shared'], record['shared']),
                '' if folder_shared is None else TRISTATE.get(folder_shared, folder_shared),
                record['hits'], record['uploads'], record['rating'], record['comments'], record['share_tags'],
                record['metadata'],
                '\n'.join(f'{url} (seen {seen:%Y-%m-%d %H:%M:%S} UTC)' if seen else url
                          for url, seen in record['sources']),
                record['index'], ', '.join(sorted(entry['copies'])), entry['user']))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def shareazaLibraryFolders(context):
    data_headers = ('Folder', 'Shared (as stored)', 'Found In', 'User')
    groups, sources = _libraries(context, 'Shareaza Library Folders')
    data_list = []
    for _folder, copies in sorted(groups.items()):
        rows = {}
        for base, result, user in copies:
            for folder in result['folders']:
                entry = rows.setdefault((folder['path'], folder['shared']), {'copies': [], 'user': user})
                entry['copies'].append(_copy_label(base, result))
        for (path, shared), entry in rows.items():
            data_list.append((path, TRISTATE.get(shared, shared), '; '.join(sorted(entry['copies'])), entry['user']))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def shareazaDownloads(context):
    data_headers = ('File Name', ('File Size (bytes)', 'number'), ('SHA-1', 'hash'), ('Tiger Tree Root', 'hash'),
                    ('MD5', 'hash'), ('eD2K', 'hash'), ('BitTorrent Info Hash', 'hash'), 'Download File',
                    ('Format Version', 'number'), 'User')
    data_list, sources = [], []
    for path in sorted(str(f) for f in context.get_files_found() if str(f).lower().endswith('.sd')):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                record = read_download(handle.read())
        except (OSError, ShareazaFormatError) as exc:
            logfunc(f'Shareaza Unfinished Downloads: {relative} not read ({exc})')
            continue
        data_list.append((record['name'], record['size'], record['sha1'], record['tiger'], record['md5'],
                          record['ed2k'], record['bth'], os.path.basename(path), record['version'],
                          user_from_path(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
