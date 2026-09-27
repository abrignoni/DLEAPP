"""Google Drive for desktop (DriveFS) items and mirrored items, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "googleDriveItems": {
        "name": "Google Drive Items",
        "description": "Files and folders in each Google Drive for desktop (DriveFS) account's two metadata "
                       'databases, with their path, ownership, sharing and trash flags, and the stored modified, '
                       'viewed and shared-with-me dates.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Google Drive",
        "notes": (
            (
            (
            (
            'Reads the items table of the two metadata databases, metadata_sqlite_db and '
            'mirror_metadata_sqlite.db, in each account folder of a Google Drive for desktop '
            '(DriveFS) folder, which is Library/Application Support/Google/DriveFS on the tested '
            'Mac. Amged Wageh documents %LocalAppData%\\Google\\DriveFS as the default folder on '
            "Windows, an account folder named after each account's ID, and metadata_sqlite_db as "
            "the database of synced, deleted and shared items (Reference: Amged Wageh, 'DriveFS "
            "Sleuth: Your Ultimate Google Drive File Stream Investigator!', "
            'https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980). '
            'One row is reported per item in each database; an item that both databases hold with '
            'the same values is reported once, and Source File lists both. On the public MacBook '
            'Pro logical extraction (macOS 15.4, not a registered corpus key) metadata_sqlite_db '
            'holds 9 items and mirror_metadata_sqlite.db holds 6, all 6 with an ID the first also '
            'holds; 3 of them give the same values in every reported column, and the other 3 '
            'store the title of a Google document, a spreadsheet and a shortcut without the .gdoc '
            'or .gsheet extension that metadata_sqlite_db stores, so the two databases give 12 '
            'rows. Modified (UTC), Viewed by Me (UTC) and Shared with Me (UTC) are modified_date, '
            'viewed_by_me_date and shared_with_me_date, which the post describes as the last '
            'modification date, the last date the item was viewed and the sharing date, read as '
            'Unix milliseconds in UTC, as DriveFS Sleuth reads the first two (Reference: Amged '
            'Wageh, DriveFS Sleuth, '
            'https://github.com/AmgdGocha/DriveFS-Sleuth/blob/839e27193fa650750ec6eaccb785b32c55c6ac11/src/drivefs_sleuth/synced_files_tree.py#L42-L46). '
            'Read that way every date on the MacBook Pro falls between 1 and 12 December 2025, '
            'and the modified date of the Work folder, which mirror_sqlite.db holds as a mirrored '
            'root, equals the cloud modification time mirror_sqlite.db records for it, to the '
            'millisecond. A shared_with_me_date of 0 is shown blank; the post says the field is 0 '
            'for an item not shared, and on the MacBook Pro it is 0 on the 5 items of '
            'metadata_sqlite_db without a sharing date. Name is local_title as stored. Path joins '
            "the names of the item's parents, taken from stable_parents, down to the item; an "
            'item with no parent is the top of its own path, and a parent that is not in items is '
            'written as (stable_id N). On the MacBook Pro the items with no parent are My Drive, '
            "whose ID is the root_id the database's properties table records, the folder that "
            "mirror_sqlite.db's machine_root table names, and the 3 items with a sharing date "
            'that no other item contains. Owned by Account (as stored) is is_owner, which the '
            'post reads as 1 for an item the account owns and 0 for one shared with it; on the '
            'MacBook Pro it is 0 on exactly the 4 items of metadata_sqlite_db with a sharing '
            'date. Trashed (as stored) is trashed, which the post reads as 1 for an item in the '
            'Trash, and Starred (as stored) is starred; Trashed and Starred both hold 0 on every '
            'row of the MacBook Pro. Size (as stored) is file_size; on the MacBook Pro the Google '
            "document's is 2311, the cloud size mirror_sqlite.db records for the document, while "
            'its local .gdoc file is 183 bytes. Shortcut Target is the name of the item '
            "shortcut_details names as a shortcut's target; the shortcut on the MacBook Pro has "
            'is_owner 1 and file_size 0, as the post describes for shortcuts. Drive ID is id, '
            "which the post calls the item's URL ID. Account ID is the name of the account "
            'folder; on the MacBook Pro it is the one account ID experiments.db lists in '
            'account_ids, so Account ID holds one value there. When a logical extraction holds '
            'the same database under Users/ and under System/Volumes/Data/Users/, a second copy '
            'whose database and -wal file are both byte-identical to the first is not read again '
            'and is counted in the run log, as 2 copies on the MacBook Pro are. The deleted_items '
            'table, which holds no row on the MacBook Pro, item_properties, is_tombstone, labels '
            'and the cached file contents in content_cache are not reported. dleapp_macos_bigsur, '
            'the four registered Windows disk images and windows11_arm_parallels hold no DriveFS '
            'folder.'
        )
        )
        )
        ),
        "paths": ('*/DriveFS/*/metadata_sqlite_db*', '*/DriveFS/*/mirror_metadata_sqlite.db*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "cloud",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "googleDriveMirroredItems": {
        "name": "Google Drive Mirrored Items",
        "description": 'Items in the local folders Google Drive for desktop mirrors, with their local path, '
                       'local and cloud names, sizes and MD5 hashes, the volume, and the stored local and cloud '
                       'modification times.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Google Drive",
        "notes": (
            (
            (
            (
            'Reads the mirror_item table of mirror_sqlite.db in each account folder of a Google '
            'Drive for desktop (DriveFS) folder. Amged Wageh describes that table as the list of '
            'mirrored items, with their local and cloud names, local and cloud modification '
            'times, sizes, MD5 hash, whether the item is shared, a volume ID matching media_id in '
            'root_preference_sqlite.db, and the parent of each item (Reference: Amged Wageh, '
            "'DriveFS Sleuth: Your Ultimate Google Drive File Stream Investigator!', "
            'https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980). '
            'One row is reported per mirrored item. Local Modified (UTC) and Cloud Modified (UTC) '
            'are local_mtime_ms and cloud_mtime_ms read as Unix milliseconds in UTC. Local Path '
            "joins local_filename from the item's root down to the item, following "
            "parent_local_stable_id; the root's own name is replaced by the folder "
            'root_preference_sqlite.db, in the DriveFS folder, records as last_seen_absolute_path '
            "for the root that mirror_sqlite.db's root_config names, when that roots row names "
            "the same account. Volume is the name root_preference_sqlite.db's media table records "
            "for the item's volume ID, or the ID as stored. On the public MacBook Pro logical "
            'extraction (macOS 15.4, not a registered corpus key) mirror_sqlite.db holds 2 items: '
            "the folder Documents/Work in the user's home folder, the only root, and one Google "
            'document file in it. The extraction holds that file at the Local Path recorded, 183 '
            'bytes, the Local Size recorded, and the MD5 of its bytes is the Local MD5 recorded. '
            'Its Local Name ends in .gdoc and its Cloud Name does not, and its Local Modified and '
            'Cloud Modified are the same instant, 11 December 2025 21:09:48.350 UTC. Cloud MD5 is '
            "empty on both rows, and Volume holds one value on both rows, the Data volume's name. "
            'Shared (as stored) is shared, which the post says is set to 1 for a mirrored item '
            'that is shared; it is 1 on the document and 0 on the folder. Inode (as stored) is '
            'inode as stored; it was not compared with a file system here, since the MacBook Pro '
            'extraction is a logical one. Account ID is the name of the account folder. Account '
            'ID and Source File each hold one value on the MacBook Pro, where 1 byte-identical '
            'copy of mirror_sqlite.db under System/Volumes/Data is not read again. The versions, '
            'storage policy and other columns of mirror_item, and the pending uploads, pending '
            'deletes and relation tables of mirror_sqlite.db, are not reported. '
            'dleapp_macos_bigsur, the four registered Windows disk images and '
            'windows11_arm_parallels hold no DriveFS folder.'
        )
        )
        )
        ),
        "paths": ('*/DriveFS/*/mirror_sqlite.db*', '*/DriveFS/root_preference_sqlite.db*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import unique_sources
from scripts.macos_powerlog import merge_sources

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_ITEM_DATABASES = ('metadata_sqlite_db', 'mirror_metadata_sqlite.db')
_ITEM_COLUMNS = ('stable_id', 'id', 'local_title', 'mime_type', 'is_folder', 'is_owner', 'trashed',
                 'starred', 'modified_date', 'viewed_by_me_date', 'shared_with_me_date', 'file_size')
_MIRROR_COLUMNS = ('local_stable_id', 'parent_local_stable_id', 'local_filename', 'cloud_filename',
                   'local_mtime_ms', 'cloud_mtime_ms', 'local_md5_checksum', 'cloud_md5_checksum',
                   'local_size', 'cloud_size', 'shared', 'volume', 'inode', 'is_root')
_DEPTH = 256


def _databases(context, names):
    """Staged copies of the databases with these file names (not sidecars or directories)."""
    return [str(path) for path in context.get_files_found()
            if os.path.basename(str(path)) in names and not os.path.isdir(str(path))]


def _columns(path, table):
    return {row['name'] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}


def _select(path, table, columns, order=''):
    """Rows of table with each wanted column, NULL for a column the table does not have."""
    present = _columns(path, table)
    fields = ', '.join(f'"{name}"' if name in present else f'NULL AS "{name}"' for name in columns)
    return get_sqlite_db_records(path, f'SELECT {fields} FROM "{table}" {order}')


def _ms(value):
    """Unix milliseconds as a UTC datetime; blank for no value and for 0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value == 0:
        return ''
    try:
        return _UNIX_EPOCH + timedelta(milliseconds=value)
    except OverflowError:
        return ''


def _blank(value):
    return '' if value is None else value


def _account(relative):
    """The name of the folder that holds the database: the account ID folder in DriveFS."""
    return os.path.basename(os.path.dirname(relative.replace('\\', '/')))


def _paths(node, parents, names):
    """Every path from a top item down to node, names joined by '/'. An ancestor with no name
    is written as (stable_id N); a loop or a chain deeper than _DEPTH ends the path there."""
    found, stack = [], [(node, (names.get(node, f'(stable_id {node})'),), {node})]
    while stack:
        current, trail, seen = stack.pop()
        ups = [up for up in parents.get(current, []) if up not in seen]
        if not ups or len(trail) >= _DEPTH:
            found.append('/'.join(reversed(trail)))
            continue
        for up in sorted(ups, reverse=True):
            stack.append((up, trail + (names.get(up, f'(stable_id {up})'),), seen | {up}))
    return sorted(set(found))


@artifact_processor
def googleDriveItems(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Viewed by Me (UTC)', 'datetime'),
                    ('Shared with Me (UTC)', 'datetime'), 'Name', 'Path', 'MIME Type',
                    'Folder (as stored)', 'Size (as stored)', 'Owned by Account (as stored)',
                    'Trashed (as stored)', 'Starred (as stored)', 'Shortcut Target', 'Drive ID',
                    'Account ID', 'Source File')
    paths, _skipped = unique_sources(context, _databases(context, _ITEM_DATABASES),
                                     sidecars=('-wal',), label='Google Drive Items')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'items'):
            logfunc(f'Google Drive Items: no items table in {relative}')
            continue
        rows = _select(path, 'items', _ITEM_COLUMNS, 'ORDER BY modified_date, stable_id')
        if not rows:
            continue
        read.append(path)
        names = {row['stable_id']: row['local_title'] for row in rows}
        parents = {}
        if does_table_exist_in_db(path, 'stable_parents'):
            for row in get_sqlite_db_records(
                    path, 'SELECT item_stable_id, parent_stable_id FROM stable_parents'):
                parents.setdefault(row['item_stable_id'], []).append(row['parent_stable_id'])
        targets = {}
        if does_table_exist_in_db(path, 'shortcut_details'):
            targets = {row['shortcut_stable_id']: row['target_stable_id'] for row in
                       get_sqlite_db_records(path, 'SELECT shortcut_stable_id, target_stable_id '
                                                   'FROM shortcut_details')}
        account = _account(relative)
        for row in rows:
            target = targets.get(row['stable_id'])
            records.append(((_ms(row['modified_date']), _ms(row['viewed_by_me_date']),
                             _ms(row['shared_with_me_date']), _blank(row['local_title']),
                             '\n'.join(_paths(row['stable_id'], parents, names)),
                             _blank(row['mime_type']), _blank(row['is_folder']),
                             _blank(row['file_size']), _blank(row['is_owner']),
                             _blank(row['trashed']), _blank(row['starred']),
                             '' if target is None else names.get(target, f'(stable_id {target})'),
                             _blank(row['id']), account), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)


def _roots(path, account):
    """({root_id: last_seen_absolute_path}, {media_id: volume name}) from the
    root_preference_sqlite.db beside an account folder, keeping only the roots whose
    account_token is this account and that record a last_seen_absolute_path."""
    if not (os.path.isfile(path) and does_table_exist_in_db(path, 'roots')):
        return {}, {}
    volumes = {}
    if does_table_exist_in_db(path, 'media'):
        volumes = {row['media_id']: row['name'] for row in _select(path, 'media', ('media_id', 'name'))}
    roots = {}
    for row in _select(path, 'roots', ('root_id', 'last_seen_absolute_path', 'account_token')):
        if str(row['account_token']) == account and row['last_seen_absolute_path']:
            roots[row['root_id']] = row['last_seen_absolute_path']
    return roots, volumes


@artifact_processor
def googleDriveMirroredItems(context):
    data_headers = (('Local Modified (UTC)', 'datetime'), ('Cloud Modified (UTC)', 'datetime'),
                    'Local Name', 'Cloud Name', 'Local Path', 'Local MD5', 'Cloud MD5',
                    'Local Size', 'Cloud Size', 'Shared (as stored)', 'Volume', 'Inode (as stored)',
                    'Account ID', 'Source File')
    paths, _skipped = unique_sources(context, _databases(context, ('mirror_sqlite.db',)),
                                     sidecars=('-wal',), label='Google Drive Mirrored Items')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'mirror_item'):
            logfunc(f'Google Drive Mirrored Items: no mirror_item table in {relative}')
            continue
        rows = _select(path, 'mirror_item', _MIRROR_COLUMNS, 'ORDER BY local_mtime_ms, local_stable_id')
        if not rows:
            continue
        read.append(path)
        account = _account(relative)
        preference = os.path.join(os.path.dirname(os.path.dirname(path)), 'root_preference_sqlite.db')
        roots, volumes = _roots(preference, account)
        if roots:
            read.append(preference)
        top = {}
        if does_table_exist_in_db(path, 'root_config'):
            for row in _select(path, 'root_config', ('root_id', 'local_stable_id')):
                if row['root_id'] in roots:
                    top[row['local_stable_id']] = roots[row['root_id']]
        names = {row['local_stable_id']: row['local_filename'] for row in rows}
        parents = {row['local_stable_id']: [row['parent_local_stable_id']] for row in rows
                   if row['parent_local_stable_id'] in names}
        for row in rows:
            local_path = []
            for chain in _paths(row['local_stable_id'], parents, names):
                # A chain starts at its root item; a root whose folder is known is replaced by it.
                first = _top(row['local_stable_id'], parents)
                if first in top:
                    rest = chain.split('/', 1)[1] if '/' in chain else ''
                    local_path.append(top[first] + ('/' + rest if rest else ''))
                else:
                    local_path.append(chain)
            records.append(((_ms(row['local_mtime_ms']), _ms(row['cloud_mtime_ms']),
                             _blank(row['local_filename']), _blank(row['cloud_filename']),
                             '\n'.join(local_path), _blank(row['local_md5_checksum']),
                             _blank(row['cloud_md5_checksum']), _blank(row['local_size']),
                             _blank(row['cloud_size']), _blank(row['shared']),
                             volumes.get(row['volume'], _blank(row['volume'])),
                             _blank(row['inode']), account), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)


def _top(node, parents):
    """The item at the top of node's chain of parents."""
    seen = {node}
    while parents.get(node) and parents[node][0] not in seen:
        node = parents[node][0]
        seen.add(node)
    return node
