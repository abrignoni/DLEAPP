__artifacts_v2__ = {
    "oneDriveSyncedItems": {
        "name": "OneDrive Synced Items",
        "description": "Files and folders the OneDrive sync client on Windows lists for an account "
                       "configured in the client, from the item list in its settings folder: name, path within the "
                       "OneDrive folder, size, the stored local hash, the NTFS file reference and "
                       "volume serial of the local copy, and, where the store has them, its "
                       "change and disk times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "OneDrive (Desktop)",
        "notes": "One row per file or folder record in the item list the OneDrive sync client keeps "
                 "in AppData\\Local\\Microsoft\\OneDrive\\settings\\<account folder> on Windows: the "
                 "<account id>.dat file and SyncEngineDatabase.db (its od_ClientFile_Records and "
                 "od_ClientFolder_Records tables); the tested images held one, the other, or both. No "
                 "Microsoft documentation of either format was found. The .dat record layouts, the version each applies to, and the "
                 "units of the time fields follow Brian Maloney's OneDriveExplorer (MIT), "
                 "https://github.com/Beercow/OneDriveExplorer/blob/dfec646a87911db8083749f2d625cfeb92fc84a1/OneDriveExplorer/ode/helpers/structures "
                 "(DAT_FILE_v2b, DAT_FILE_v36, DAT_FOLDER_v29_v2c, DAT_FOLDER_v2d_v36), "
                 "https://github.com/Beercow/OneDriveExplorer/blob/dfec646a87911db8083749f2d625cfeb92fc84a1/OneDriveExplorer/ode/parsers/dat.py "
                 "and "
                 "https://github.com/Beercow/OneDriveExplorer/blob/dfec646a87911db8083749f2d625cfeb92fc84a1/OneDriveExplorer/ode/parsers/sqlite_db.py. "
                 "Only .dat versions 0x2b and 0x36, the two on the tested images, are read; a file of "
                 "another version is logged and skipped. Records other than files (type 0x01) and folders "
                 "(0x02) are counted in the log and not reported. "
                 "MFT Entry and MFT Sequence are the low 48 and high 16 bits of the stored itemIndex. On "
                 "lonewolf_win10 (.dat 0x2b, 25 files and 4 folders), the $MFT record at each of the 29 "
                 "entries had that sequence number and a file name attribute equal to the row's Name. Volume "
                 "Serial is the low 32 bits of the stored volumeID, in hexadecimal; it equalled the low 32 "
                 "bits of the serial number in the boot sector of the NTFS volume holding the user's profile "
                 "on 29 of 29 rows of lonewolf_win10 and 3 of 4 rows of pc_mus_001_win11, whose fourth row, a "
                 "folder record, stores a zero volumeID and leaves the column blank. These two columns name where the local copy was "
                 "when the client wrote the record; they were not checked on SyncEngineDatabase.db, whose "
                 "only tested copy is on a logical image (hexordia_mvs2025_win11) without $MFT. "
                 "Path is built from the names of the folder records of the same store, following each "
                 "parentResourceID, and is relative to the account's OneDrive folder; a chain stops at a "
                 "parent the store holds no folder record for. On lonewolf_win10, 28 of the 29 paths exist "
                 "under the user's OneDrive folder on the image; the other is a folder under which the image "
                 "holds no file. Size (bytes) is size as stored; it equalled the size of the file on disk on "
                 "all 25 files on lonewolf_win10. "
                 "Local Hash (as stored) is the stored 20-byte localHashDigest in hexadecimal, blank when "
                 "all 20 bytes are zero. On .dat 0x2b "
                 "its first 16 bytes equalled the first 16 bytes of the SHA-1 of the file on disk on 25 of 25 "
                 "files on lonewolf_win10, and its last 4 bytes did not; what those 4 bytes hold is not "
                 "established. OneDriveExplorer reads the digest as SHA-1 when localHashAlgorithm is 4 "
                 "(sqlite_db.py, compute_hash). On .dat 0x36 and SyncEngineDatabase.db it was not checked "
                 "against content: the one file on pc_mus_001_win11 is not present under the user's OneDrive "
                 "folder on the image, and on hexordia_mvs2025_win11 the local copy is the stored size and all "
                 "zero bytes; both stores held the same 20 bytes for that file, which has the same size on "
                 "both. Hash Algorithm (as stored) is localHashAlgorithm, which only SyncEngineDatabase.db "
                 "holds. "
                 "Last Change is lastChange read as Unix seconds, the unit OneDriveExplorer converts it with; "
                 ".dat 0x2b has no such field. Disk Creation Time and Disk Last Access Time are "
                 "diskCreationTime and diskLastAccessTime, read the same way, which only SyncEngineDatabase.db "
                 "holds. None of the three was checked against another record of the same event. "
                 "Status (as stored) is fileStatus or folderStatus as stored; OneDriveExplorer gives the "
                 "values no meaning, and none is given here. Resource ID is resourceID as stored. Store names "
                 "the store and, for a .dat, its version; Account Folder is the folder under settings "
                 "(Personal or Business followed by a number); User comes from the path. "
                 "Not read: SafeDelete.db, KFM.db, SettingsDatabase.db, OCSI.db and FileSyncFSCache.db (no "
                 "file or deletion rows on the tested images), CxP.db (on hexordia_mvs2025_win11, 2,071 cxp_state "
                 "rows sharing one cxp_name), the .ini and .json settings files, the "
                 "<account id>_screenshot.dat file, the sync client on macOS, and the item's media, sharing "
                 "and permission fields. The OneDrive Accounts artifact reads the client's registry values. "
                 "On each tested image Store, Account Folder and User held one value on every row (one store, Personal, one user), and Volume Serial (low 32 bits) held one value on all 29 rows of lonewolf_win10. Last Change, Disk Creation Time, Disk Last Access Time and Hash Algorithm (as stored) held no value on any row of lonewolf_win10, whose .dat 0x2b has none of those fields; Disk Creation Time, Disk Last Access Time and Hash Algorithm (as stored) held none on pc_mus_001_win11 (.dat 0x36). Last Change was filled on 1 of 4 rows on pc_mus_001_win11 and hexordia_mvs2025_win11, the one file; folder records have no such field. Name and Path were identical on every row of those two images, whose items all sit at the top of the OneDrive folder.",
        "paths": ('*/Users/*/AppData/Local/Microsoft/OneDrive/settings/*/*.dat',
                  '*/Users/*/AppData/Local/Microsoft/OneDrive/settings/*/SyncEngineDatabase.db*'),
        "output_types": "standard",
        "artifact_icon": "cloud",
        "sample_data": {
            "lonewolf_win10": "Windows 10 Education build 16299, OneDrive .dat version 0x2b | 29 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, OneDrive .dat version 0x36 and an empty SyncEngineDatabase.db | 4 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100, OneDrive SyncEngineDatabase.db schema version 32 | 4 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, is_sqlite_sidecar, logfunc, open_sqlite_db_readonly
from scripts.onedrive_settings import (DAT_VERSIONS, FILE, dat_version, paths, read_dat,
                                       read_sync_engine)
from scripts.windows_registry import user_from_path

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_DAT_NAME = re.compile(r'^[0-9a-f]{16}\.dat$|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.dat$',
                       re.IGNORECASE)


def _unix(value):
    """Unix seconds as a UTC datetime, '' for none or zero."""
    if not isinstance(value, int) or value <= 0:
        return ''
    try:
        return _EPOCH + timedelta(seconds=value)
    except OverflowError:
        return ''


def _account_folder(relative):
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() == 'settings' and index > 0 and parts[index - 1].lower() == 'onedrive':
            return parts[index + 1] if index + 2 < len(parts) else ''
    return ''


def _rows(items, store, relative):
    built = paths(items)
    account, user = _account_folder(relative), user_from_path(relative)
    rows = []
    for item in items:
        index = item.item_index if isinstance(item.item_index, int) else None
        volume = item.volume_id if isinstance(item.volume_id, int) else None
        local_hash = item.local_hash.hex() if isinstance(item.local_hash, bytes) and any(item.local_hash) else ''
        rows.append((_unix(item.last_change), _unix(item.disk_created), _unix(item.disk_accessed),
                     'File' if item.kind == FILE else 'Folder', item.name or '', built[id(item)],
                     item.size if item.kind == FILE and item.size is not None else '',
                     local_hash, item.hash_algorithm if item.hash_algorithm is not None else '',
                     item.status if item.status is not None else '',
                     index & 0xFFFFFFFFFFFF if index else '', index >> 48 if index else '',
                     f'{volume & 0xFFFFFFFF:08X}' if volume else '',
                     item.resource_id or '', store, account, user))
    return rows


@artifact_processor
def oneDriveSyncedItems(context):
    label = 'OneDrive Synced Items'
    data_list, sources = [], []
    for found in sorted(str(path) for path in context.get_files_found()):
        if not os.path.isfile(found) or is_sqlite_sidecar(found):
            continue
        relative = context.get_relative_path(found)
        name = os.path.basename(found)
        if name.lower() == 'syncenginedatabase.db':
            db = open_sqlite_db_readonly(found)
            if db is None:
                continue
            try:
                items = read_sync_engine(db)
            finally:
                db.close()
            data_list.extend(_rows(items, 'SyncEngineDatabase.db', relative))
            sources.append(found)
            logfunc(f'{label}: {len(items)} items in {relative}')
        elif _DAT_NAME.match(name):
            with open(found, 'rb') as handle:
                data = handle.read()
            version = dat_version(data)
            if version not in DAT_VERSIONS:
                logfunc(f'{label}: {relative}: version {version!r} is not one this artifact reads')
                continue
            items, counts, trailing = read_dat(data)
            data_list.extend(_rows(items, f'.dat version 0x{version:02x}', relative))
            sources.append(found)
            other = {f'0x{kind:02x}': count for kind, count in sorted(counts.items()) if kind not in (1, 2)}
            logfunc(f'{label}: {len(items)} items in {relative}; other record types {other or "none"}; '
                    f'{trailing} trailing bytes')
    data_headers = (('Last Change', 'datetime'), ('Disk Creation Time', 'datetime'),
                    ('Disk Last Access Time', 'datetime'), 'Type', 'Name', 'Path', ('Size (bytes)', 'number'),
                    'Local Hash (as stored)', 'Hash Algorithm (as stored)', 'Status (as stored)',
                    ('MFT Entry', 'number'), ('MFT Sequence', 'number'), 'Volume Serial (low 32 bits)',
                    'Resource ID', 'Store', 'Account Folder', 'User')
    return data_headers, data_list, '\n'.join(sources)
