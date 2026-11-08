"""eMule known files, unfinished downloads, download list, search history and settings, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Formats are read by scripts/emule.py, which follows the eMule 0.72a source pinned there.
"""

import os
from datetime import datetime, timezone

from scripts.emule import (EmuleFormatError, ini_values, parse_file_link, read_download_overview, read_known_met,
                           read_part_met, read_preferences_dat, read_utf16_lines)
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import user_from_path

__artifacts_v2__ = {
    "emuleKnownFiles": {
        "name": "eMule Known Files",
        "description": "Files eMule hashed and kept in known.met: name, size and eD2K hash, when eMule last found "
                       "the file among its shared files, and the upload counts it kept for the file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "eMule",
        "notes": "Files are read as eMule 0.72a reads them (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Packets.cpp#L443-L537 for the tag format). The known data (windows11_arm_emule_known_20261108) is eMule 0.72a on Windows 11 ARM64, never connected to eD2K or Kad. Nothing in these files names the program that wrote them; other eD2K clients may use the same file names, and only eMule 0.72a was tested. Matched in eMule's config folder under any folder named eMule (eMule keeps it under AppData\\\\Local\\\\eMule, ProgramData\\\\eMule or its own install folder, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L2947-L2958); a config folder under another name is not matched. User is the account folder name taken from the file path; User held one value on all rows of the known data, which has one profile. One row per record in known.met (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/KnownFileList.cpp#L87-L107). eMule adds a record when it hashes a file it shares and when a download completes (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/PartFile.cpp#L2953); 0.72a does not remove a record because its file is gone: it replaces a record when a file with the same hash is hashed or completed again (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/KnownFileList.cpp#L273-L312), and drops some tags once a file has not been seen for 31 days (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/KnownFile.cpp#L820-L821, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Opcodes.h#L131), so a row does not show the file is still on disk or still shared. Last Shared (UTC) is FT_LASTSHARED: eMule sets it when it adds the file to its shared list (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/SharedFileList.cpp#L720) and writes the current time when it has none (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/KnownFile.cpp#L807-L816). On the known data Last Shared (UTC) held one value on all 3 rows, the second the last eMule session started, not the earlier session that hashed the files. File Modified (UTC) is the record's date, the file's last write time when eMule hashed it (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/KnownFile.cpp#L476-L478, adjusted for daylight saving only when the AdjustNTFSDaylightFileTime setting is on, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L372); on the known data File Modified (UTC) held one value on all 3 rows, as the three test files were written in the same second, and it equalled each file's NTFS last write time. eD2K Hash is the record's MD4 file hash; on the known data all 3 matched hashes computed independently from the shared files. AICH Hash (as stored) is the FT_AICH_HASH string, shown as stored and not checked. Uploaded (bytes), Upload Requests, Accepted Uploads and Kad Source Publish (UTC) are FT_ATTRANSFERRED with FT_ATTRANSFERREDHI, FT_ATREQUESTED, FT_ATACCEPTED and FT_KADLASTPUBLISHSRC, which eMule writes only when not zero (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/KnownFile.cpp#L849-L883). On the known data Uploaded (bytes), Upload Requests, Accepted Uploads and Kad Source Publish (UTC) were empty on all 3 rows because no peer ever connected, so these four columns are source-verified only. known2_64.met (AICH hash sets) and cancelled.met (hashes of cancelled downloads, salted with a seed in the file) are not read. A row records a file eMule hashed, not who put it in a shared folder or that anyone downloaded it.",
        "paths": ('*/eMule/config/known.met',),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no eMule files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no eMule files matched)",
        },
    },
    "emuleDownloads": {
        "name": "eMule Unfinished Downloads",
        "description": "Downloads eMule had not finished, one per <n>.part.met in its temp folder: file name, size, "
                       "eD2K hash, bytes downloaded and whether the download was paused.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "eMule",
        "notes": "Files are read as eMule 0.72a reads them (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Packets.cpp#L443-L537 for the tag format). The known data (windows11_arm_emule_known_20261108) is eMule 0.72a on Windows 11 ARM64, never connected to eD2K or Kad. Nothing in these files names the program that wrote them; other eD2K clients may use the same file names, and only eMule 0.72a was tested. User is the account folder name taken from the file path; User held one value on all rows of the known data, which has one profile. One row per <n>.part.met file found anywhere in the extraction, since the temp folder is a setting (by default Temp in an eMule folder in the user's or the public Downloads folder, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L2947-L2958 and #L2999). The file is read as SavePartFile writes it, versions 0xE0 and 0xE2 (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/PartFile.cpp#L1204-L1206); the older layouts eMule still imports (0xE1, the eDonkey style and Shareaza's) are logged and skipped. .part.met.bak copies are not read. Part File Modified (UTC) is the record's date, the .part file's last write time when eMule saved the record (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/PartFile.cpp#L1176-L1180); on the known data it equalled the .part file's last write time, the moment the download was added, because no data arrived. It is not an added time. Last Seen Complete (UTC) is FT_LASTSEENCOMPLETE, written only when set (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/PartFile.cpp#L1252), and Downloaded (bytes) is FT_TRANSFERRED, written only when not zero (#L1222) and shown as 0 when absent, as eMule reads it. Paused is Yes when FT_STATUS is not zero, the rule eMule uses when it reads the file (#L844); eMule writes it only for a paused download (#L1238). Category (as stored) is the FT_CATEGORY value (#L815, #L1259), eMule's download category number, 0 when absent. On the known data the one row had no Last Seen Complete, 0 bytes downloaded, Paused No and Category 0, as the download had no source; a paused, partly downloaded or categorised download was not tested. Temp Folder Set By names the user whose eMule preferences.ini lists the folder holding the file as TempDir or TempDirs, compared without drive letters; it is blank when no preferences.ini found names that folder, as for a .part.met copied elsewhere. The .part file itself is not read. A row records a download eMule had queued, not that any data was received.",
        "paths": ('*.part.met', '*/eMule/config/preferences.ini'),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no eMule files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no eMule files matched)",
        },
    },
    "emuleDownloadList": {
        "name": "eMule Download List",
        "description": "The list of unfinished downloads eMule writes to downloads.txt in its config folder, and the "
                       "previous copy in downloads.bak: part file, eD2K link and the time the list was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "eMule",
        "notes": "Files are read as eMule 0.72a reads them. The known data (windows11_arm_emule_known_20261108) is eMule 0.72a on Windows 11 ARM64, never connected to eD2K or Kad. Nothing in these files names the program that wrote them; other eD2K clients may use the same file names, and only eMule 0.72a was tested. Matched in eMule's config folder under any folder named eMule (eMule keeps it under AppData\\\\Local\\\\eMule, ProgramData\\\\eMule or its own install folder, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L2947-L2958); a config folder under another name is not matched. User is the account folder name taken from the file path; User held one value on all rows of the known data, which has one profile. One row per line of downloads.txt and of downloads.bak, the copy eMule keeps of the previous list. eMule writes the list at startup and when a download is added or removed (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/DownloadQueue.cpp#L160, #L336, #L698; format at #L1621-L1650): a Date line, the temp folder when there is only one, then each unfinished download's part file and eD2K link. Written (local, as stored) is that Date line as stored, written in the computer's local time and locale format with no time zone; on the known data (a computer set to UTC-5) both values were five hours behind, to within two seconds, the UTC times the test script logged for the matching steps (the download being added, then the next eMule start), and downloads.txt held the later time. File Name, File Size (bytes) and eD2K Hash are split out of the eD2K link. Temp Folder is the Directory line, blank when eMule had more than one temp folder. On the known data both files held the same one download. The list sits in the config folder, apart from the temp folder. A row records a download that was in eMule's queue when the list was written, not that data was received.",
        "paths": ('*/eMule/config/downloads.txt', '*/eMule/config/downloads.bak'),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no eMule files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no eMule files matched)",
        },
    },
    "emuleSearchHistory": {
        "name": "eMule Search History",
        "description": "Search text eMule saved from its search box into AC_SearchStrings.dat, the list it offers back "
                       "as suggestions.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "eMule",
        "notes": "Files are read as eMule 0.72a reads them. The known data (windows11_arm_emule_known_20261108) is eMule 0.72a on Windows 11 ARM64, never connected to eD2K or Kad. Nothing in these files names the program that wrote them; other eD2K clients may use the same file names, and only eMule 0.72a was tested. Matched in eMule's config folder under any folder named eMule (eMule keeps it under AppData\\\\Local\\\\eMule, ProgramData\\\\eMule or its own install folder, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L2947-L2958); a config folder under another name is not matched. User is the account folder name taken from the file path; User held one value on all rows of the known data, which has one profile. One row per line of AC_SearchStrings.dat, the list eMule saves for its search box suggestions (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/CustomAutoComplete.cpp#L310-L319). eMule adds the text when Start is clicked, before the search runs (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/SearchParamsWnd.cpp#L657-L659): on the known data the search was refused because eMule was not connected, and the text was saved anyway, so a row does not show that a search ran or returned anything. Position is the line number. eMule inserts new text at the top and moves reused text there (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/CustomAutoComplete.cpp#L112-L131), so Position 1 is the most recently used; the known data held one entry, so the order is source-verified only. The file holds no times. StoredSearches.met, which keeps search results, was empty on the known data and is not read.",
        "paths": ('*/eMule/config/AC_SearchStrings.dat',),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no eMule files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no eMule files matched)",
        },
    },
    "emuleSettings": {
        "name": "eMule Settings",
        "description": "eMule's user hash, nickname, download and temp folders, and the folders it was set to share.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "eMule",
        "notes": "Files are read as eMule 0.72a reads them. The known data (windows11_arm_emule_known_20261108) is eMule 0.72a on Windows 11 ARM64, never connected to eD2K or Kad. Nothing in these files names the program that wrote them; other eD2K clients may use the same file names, and only eMule 0.72a was tested. Matched in eMule's config folder under any folder named eMule (eMule keeps it under AppData\\\\Local\\\\eMule, ProgramData\\\\eMule or its own install folder, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L2947-L2958); a config folder under another name is not matched. User is the account folder name taken from the file path; User held one value on all rows of the known data, which has one profile. Rows from three files in each config folder. User Hash is the 16-byte hash in preferences.dat after its version byte (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.h#L78-L83), the identifier eMule sends other clients in its hello packet (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/BaseClient.cpp#L914-L916); eMule sets bytes 5 and 14 of a hash it creates to 0x0E and 0x6F (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L1484-L1493), as on the known data, and a file without them is still reported and the run log says so. Nickname, Incoming Folder and Temp Folder are the Nick, IncomingDir, TempDir and TempDirs values in the eMule section of preferences.ini (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L1525-L1532); no other key in that file is reported. Shared Folder is one row per line of shareddir.dat (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L1457-L1467), which lists the folders set to share; eMule also reads an older file without a byte order mark as ANSI text, decoded here as UTF-8 or else Windows-1252. On the known data the rows matched what the test script set: one temp folder and one shared folder. eMule's incoming folder and single shared files are shared too and are not listed in shareddir.dat. Not read: cryptkey.dat (eMule's own RSA key), clients.met (credits of other clients) and emfriends.met (friends), both empty on the known data, server.met (the server list), statistics.ini and the rest of preferences.ini.",
        "paths": ('*/eMule/config/preferences.dat', '*/eMule/config/preferences.ini', '*/eMule/config/shareddir.dat'),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 5 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no eMule files matched)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no eMule files matched)",
        },
    },
}


def _utc(value):
    """A uint32 POSIX time eMule stored; 0 and 0xFFFFFFFF (time_t -1 cut to 32 bits) are no time."""
    if not isinstance(value, int) or value in (0, 0xFFFFFFFF):
        return ''
    return datetime.fromtimestamp(value, timezone.utc)


def _value(value):
    return '' if value is None else value


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _found(context, *names):
    wanted = {name.lower() for name in names}
    return sorted(str(f) for f in context.get_files_found()
                  if os.path.isfile(str(f)) and os.path.basename(str(f)).lower() in wanted)


def _folder_key(path):
    """A folder path without its drive or root, lower case, / separated, for comparing a setting with a
    path inside the extraction."""
    value = path.replace('\\', '/').strip().rstrip('/')
    if len(value) >= 2 and value[1] == ':':
        value = value[2:]
    return value.strip('/').lower()


@artifact_processor
def emuleKnownFiles(context):
    data_headers = (('Last Shared (UTC)', 'datetime'), ('File Modified (UTC)', 'datetime'), 'File Name',
                    ('File Size (bytes)', 'number'), ('eD2K Hash', 'hash'), 'AICH Hash (as stored)',
                    ('Uploaded (bytes)', 'number'), ('Upload Requests', 'number'), ('Accepted Uploads', 'number'),
                    ('Kad Source Publish (UTC)', 'datetime'), 'User')
    data_list, sources = [], []
    for path in _found(context, 'known.met'):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        count = 0
        try:
            for record in read_known_met(_read(path)):
                data_list.append((
                    _utc(record['last_shared']), _utc(record['modified']), _value(record['name']),
                    _value(record['size']), record['hash'].hex(), _value(record['aich']),
                    _value(record['transferred']), _value(record['requests']), _value(record['accepts']),
                    _utc(record['kad_source_published']), user))
                count += 1
        except (OSError, EmuleFormatError) as exc:
            logfunc(f'eMule Known Files: {relative} stopped after {count} records ({exc})')
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def emuleDownloads(context):
    data_headers = (('Part File Modified (UTC)', 'datetime'), ('Last Seen Complete (UTC)', 'datetime'),
                    'File Name', ('File Size (bytes)', 'number'), ('eD2K Hash', 'hash'),
                    ('Downloaded (bytes)', 'number'), 'Paused', ('Category (as stored)', 'number'), 'Part File',
                    'Temp Folder Set By')
    temp_owners = {}
    for path in _found(context, 'preferences.ini'):
        relative = context.get_relative_path(path)
        try:
            text = _read(path).decode('utf-8-sig', 'replace')
        except OSError:
            continue
        values = ini_values(text, 'eMule', ('TempDir', 'TempDirs'))
        folders = [values.get('TempDir', '')] + values.get('TempDirs', '').split('|')
        for folder in folders:
            key = _folder_key(folder)
            if key:
                temp_owners.setdefault(key, set()).add(user_from_path(relative) or relative)
    data_list, sources = [], []
    for path in sorted(str(f) for f in context.get_files_found() if str(f).lower().endswith('.part.met')):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            record = read_part_met(_read(path))
        except (OSError, EmuleFormatError) as exc:
            logfunc(f'eMule Unfinished Downloads: {relative} not read ({exc})')
            continue
        folder = _folder_key(os.path.dirname(relative.replace('\\', '/')))
        owners = sorted(owner for key, names in temp_owners.items() for owner in names
                        if key and (folder == key or folder.endswith('/' + key)))
        status = record['status']
        data_list.append((
            _utc(record['modified']), _utc(record['last_seen_complete']), _value(record['name']),
            _value(record['size']), record['hash'].hex(), record['transferred'] or 0,
            'Yes' if status else 'No', record['category'] or 0, os.path.basename(path), ', '.join(owners)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def emuleDownloadList(context):
    data_headers = ('Written (local, as stored)', 'List File', 'Part File', 'File Name', ('File Size (bytes)', 'number'),
                    ('eD2K Hash', 'hash'), 'eD2K Link', 'Temp Folder', 'User')
    data_list, sources = [], []
    for path in _found(context, 'downloads.txt', 'downloads.bak'):
        relative = context.get_relative_path(path)
        try:
            written, directory, entries = read_download_overview(_read(path))
        except (OSError, EmuleFormatError) as exc:
            logfunc(f'eMule Download List: {relative} not read ({exc})')
            continue
        for part, link in entries:
            name, size, file_hash = parse_file_link(link) or ('', '', '')
            data_list.append((written, os.path.basename(path), part, name, _value(size), file_hash, link, directory,
                              user_from_path(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def emuleSearchHistory(context):
    data_headers = (('Position', 'number'), 'Search Text', 'User')
    data_list, sources = [], []
    for path in _found(context, 'AC_SearchStrings.dat'):
        relative = context.get_relative_path(path)
        try:
            items = read_utf16_lines(_read(path))
        except (OSError, EmuleFormatError) as exc:
            logfunc(f'eMule Search History: {relative} not read ({exc})')
            continue
        user = user_from_path(relative)
        for index, item in enumerate(items, 1):
            data_list.append((index, item, user))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def emuleSettings(context):
    data_headers = ('Setting', 'Value', 'Source File', 'User')
    data_list, sources = [], []
    folders = {}
    for path in _found(context, 'preferences.dat', 'preferences.ini', 'shareddir.dat'):
        folders.setdefault(os.path.dirname(path), {})[os.path.basename(path).lower()] = path
    for _folder, files in sorted(folders.items()):
        any_path = next(iter(files.values()))
        user = user_from_path(context.get_relative_path(any_path))
        rows = []
        path = files.get('preferences.dat')
        if path:
            try:
                version, user_hash, marked = read_preferences_dat(_read(path))
                rows.append(('User Hash', user_hash, 'preferences.dat'))
                if not marked or version != 0x14:
                    logfunc(f'eMule Settings: {context.get_relative_path(path)} version 0x{version:02x}, '
                            f'eMule marker bytes {"present" if marked else "absent"}')
                sources.append(path)
            except (OSError, EmuleFormatError) as exc:
                logfunc(f'eMule Settings: {context.get_relative_path(path)} not read ({exc})')
        path = files.get('preferences.ini')
        if path:
            try:
                values = ini_values(_read(path).decode('utf-8-sig', 'replace'), 'eMule',
                                    ('Nick', 'IncomingDir', 'TempDir', 'TempDirs'))
            except OSError as exc:
                logfunc(f'eMule Settings: {context.get_relative_path(path)} not read ({exc})')
                values = {}
            for key, label in (('Nick', 'Nickname'), ('IncomingDir', 'Incoming Folder'), ('TempDir', 'Temp Folder')):
                if values.get(key):
                    rows.append((label, values[key], 'preferences.ini'))
            for extra in values.get('TempDirs', '').split('|'):
                if extra.strip():
                    rows.append(('Temp Folder', extra.strip(), 'preferences.ini'))
            if values:
                sources.append(path)
        path = files.get('shareddir.dat')
        if path:
            try:
                for folder in read_utf16_lines(_read(path), allow_ansi=True):
                    rows.append(('Shared Folder', folder, 'shareddir.dat'))
                sources.append(path)
            except (OSError, EmuleFormatError) as exc:
                logfunc(f'eMule Settings: {context.get_relative_path(path)} not read ({exc})')
        data_list.extend(row + (user,) for row in rows)
    return data_headers, data_list, '\n'.join(sources)
