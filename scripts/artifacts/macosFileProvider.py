"""macOS File Provider synced items, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosFileProviderItems": {
        "name": "File Provider Items",
        "description": "Files and folders a macOS File Provider extension (such as OneDrive, "
                       "iCloud Drive or another cloud provider) has in its per-domain database, "
                       "with the reconstructed path, size, dates and sync flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "File Provider (macOS)",
        "notes": "One row per FP_snapshot record in each "
                 "Library/Application Support/FileProvider/<domain>/database/db, the SQLite "
                 "database a File Provider extension keeps for one sync domain. macOS registers a "
                 "provider (OneDrive, iCloud Drive, WeChat and others) as a File Provider domain, "
                 "and each domain's db lists the items it syncs. The database is opened read-only; "
                 "its -wal sidecar is read alongside it. Name is the record's filename and Path is "
                 "rebuilt by following parent_id from the record up to the "
                 "NSFileProviderRootContainerItemIdentifier root, so the top element of a path is "
                 "the provider's own root folder (for example OneDrive); a path whose chain does "
                 "not reach the root is shown from as far up as it resolves and marked with a "
                 "leading ellipsis. Domain is the db's folder name, the File Provider domain "
                 "identifier. Item ID is the record's id. Kind (as stored) is metadata_kind, which "
                 "on the tested extraction was 1 for the folders that parent other rows and 0 for "
                 "leaf files; it is reported as stored rather than as a decoded label. Size is "
                 "metadata_size. Created, Modified and Last Used (UTC) are metadata_creation_date, "
                 "metadata_content_modification_date and metadata_last_used_date, each a Unix "
                 "epoch, left blank when the column is null; Last Used is null on most rows. "
                 "Uploaded and Shared are decoration_is_uploaded and decoration_is_shared, shown "
                 "Yes for 1 and No for 0; Shared was 0 on every row of the tested extraction and "
                 "Uploaded varied. metadata_physical_size held one value across all rows and is "
                 "not reported, and decoration_preformatted_owner_name and "
                 "decoration_preformatted_most_recent_editor_name were null on every row and are "
                 "not reported; they are named here so a reader knows they were considered. Column "
                 "names are the database's own. The item content itself is not read. Validated "
                 "locally against a private macOS extraction; row counts and values are not "
                 "published. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user, as on the extraction this was built against.",
        "paths": ('*/Library/Application Support/FileProvider/*/database/db',
                  '*/Library/Application Support/FileProvider/*/database/db-wal',
                  '*/Library/Application Support/FileProvider/*/database/db-shm'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "cloud",
        "sample_data": {},
    },
}

import os
import sqlite3
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import user_from_path

_ROOT = 'NSFileProviderRootContainerItemIdentifier'


def _s(value):
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode('utf-8', 'replace')
    return '' if value is None else str(value)


def _utc(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value == 0:
        return ''
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _flag(value):
    if value in (0, 1):
        return 'Yes' if value else 'No'
    return _s(value)


def _paths_for(rows):
    """{id: full path} by following parent_id to the root, guarding against cycles."""
    name = {rid: nm for rid, nm, _parent in rows}
    parent = {rid: pid for rid, _nm, pid in rows}
    resolved = {}
    for rid in name:
        parts = []
        seen = set()
        current = rid
        reached_root = False
        while current in name and current not in seen:
            seen.add(current)
            parts.append(name[current])
            nxt = parent.get(current)
            if nxt == _ROOT or nxt is None or nxt == '':
                reached_root = True
                break
            current = nxt
        path = '/'.join(reversed(parts))
        resolved[rid] = ('/' + path) if reached_root else ('.../' + path)
    return resolved


@artifact_processor
def macosFileProviderItems(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'),
                    ('Last Used (UTC)', 'datetime'), 'Name', 'Path', 'Kind (as stored)', 'Size',
                    'Uploaded', 'Shared', 'Item ID', 'Domain', 'User', 'Source File')
    data_list = []
    read = []
    for path in context.get_files_found():
        path = str(path)
        if os.path.basename(path) != 'db' or os.path.dirname(path).rsplit('/', 1)[-1] != 'database':
            continue
        database = open_sqlite_db_readonly(path)
        if database is None:
            continue
        relative = context.get_relative_path(path)
        domain = os.path.dirname(os.path.dirname(relative).replace('\\', '/')).rsplit('/', 1)[-1]
        user = user_from_path(relative)
        try:
            rows = database.execute(
                'SELECT id, filename, parent_id, metadata_kind, metadata_size, '
                'metadata_creation_date, metadata_content_modification_date, '
                'metadata_last_used_date, decoration_is_uploaded, decoration_is_shared '
                'FROM FP_snapshot').fetchall()
        except sqlite3.Error as exc:
            logfunc(f'File Provider Items: could not read FP_snapshot in {relative}: {exc}')
            database.close()
            continue
        database.close()
        catalog = [(_s(r[0]), _s(r[1]), _s(r[2])) for r in rows]
        paths = _paths_for(catalog)
        for row in rows:
            item_id = _s(row[0])
            data_list.append((
                _utc(row[5]), _utc(row[6]), _utc(row[7]), _s(row[1]), paths.get(item_id, ''),
                _s(row[3]), _s(row[4]), _flag(row[8]), _flag(row[9]), item_id, domain, user,
                relative))
        read.append(path)
    return data_headers, data_list, '\n'.join(read)
