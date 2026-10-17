"""Google Backup and Sync and the older Google Drive desktop client (the client before Drive for
desktop): synced items, cloud listing, pending changes, external devices, settings and the sync
log, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "googleBackupSyncItems": {
        "name": "Google Backup and Sync Items",
        "description": "Files and folders the legacy Google Drive desktop client (Backup and Sync) recorded "
                       "in snapshot.db, each local entry beside the cloud entry it maps to: the local and "
                       "cloud paths, modified times, sizes and checksums, and the cloud flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Google Drive",
        "notes": "Reads snapshot.db, with its -wal, in each profile folder of the legacy Google Drive desktop "
                 "client under AppData/Local/Google/Drive on Windows (the client Google replaced with Drive for desktop, which Google Drive Items "
                 "reads); the path pattern also matches a Library/Application Support/Google/Drive folder on "
                 "macOS, which was not tested. The -wal is load-bearing: on lonewolf_win10 the database holds 274 cloud and 274 "
                 "local entries without it and 277 of each with it. One row per entry of the mapping table, "
                 "which pairs a local entry (inode and volume) with a cloud entry (doc_id), and one row for any "
                 "local or cloud entry no mapping names; on lonewolf_win10 all 277 local and 277 cloud entries "
                 "were mapped, so there were 277 rows. A mapping row that names neither a local nor a cloud entry is counted in "
                 "the run log and not reported; none did on the tested image. Local Path is built from local_relations, child to "
                 "parent, up to an entry with no parent, whose file name holds the full path of a synced "
                 "folder as stored (beginning \\\\?\\ on the tested image); Cloud Path is built the same way "
                 "from cloud_relations up to an entry with no parent, which was 'root' or the name "
                 "of a backed-up folder on the tested image, and when an entry has more than one parent each "
                 "path is given on its own line. Modified (UTC) is local_entry.modified and Cloud Modified "
                 "(UTC) cloud_entry.modified, both read as Unix seconds: on lonewolf_win10, for the 25 files "
                 "that local_entry names and that were still in the image, local_entry.modified equalled the "
                 "file's NTFS last-modified time to the second, and Size and MD5 equalled the file's size and "
                 "MD5 hash, on all 25 (246 file entries named files no longer in the image). On the 271 rows "
                 "where both were present, Cloud Modified equalled Modified; the other 6 rows, the folders, have "
                 "no Modified, and 3 of them have no Cloud Modified either. Cloud Checksum equalled MD5 on 270, the 270 "
                 "rows where both were present. Cloud Created (UTC) is cloud_entry.created, read as Unix "
                 "seconds as plaso reads it "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/sqlite_plugins/gdrive.py#L171-L187); "
                 "Cloud Created (UTC) held no value on any row of lonewolf_win10. Is Folder is "
                 "local_entry.is_folder. Document Type, Shared, Removed and ACL Role are cloud_entry.doc_type, "
                 "shared, removed and acl_role as stored. Google publishes no definition that was found; plaso's formatter maps doc_type 0 to FOLDER, 1 to FILE and 6 to DOCUMENT and shared 0 and 1 to Private and Shared (https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/data/formatters/generic.yaml#L463-L481), a mapping not applied here, and no definition of removed or acl_role was found. On lonewolf_win10 "
                 "Document Type was 0 on the 6 folder rows, 1 on 270 file rows and 6 on one row whose local "
                 "file name ends .gdoc, Shared was 1 on one row, and Removed and ACL Role held 0 on every "
                 "row that has them (the three synced-folder roots have neither), so Removed and ACL Role are "
                 "identical on every row there. Doc ID is the cloud "
                 "entry's doc_id (resource_id in the older schema), and Inode and Volume the local entry's "
                 "key, as stored; Volume held one value on every row of lonewolf_win10. Not reported: "
                 "pre_mapping (no rows on the tested image), volume_info (one row describing the synced "
                 "volume), and original_size, original_checksum, resource_type and down_sample_status, which "
                 "held no value or 0 on every row. The older schema the Google Drive client used before "
                 "Backup and Sync (resource_id, inode_number and url) is read by the same code: tested only "
                 "on plaso's public test snapshot.db (a copy, set from WAL to rollback journal mode so it opens"
                 " without its -shm), not on a corpus image: its 11 entries gave 11 rows, and for the "
                 "two entries plaso's own test checks, the times read as Unix seconds equalled the times that "
                 "test expects "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/tests/parsers/sqlite_plugins/gdrive.py#L35-L58). cfreds_leakage_win7 carries the older "
                 "Google Drive client's sync_log.log but no snapshot.db. A row records what the client held "
                 "in its snapshot when the database was last written; it does not say who created or "
                 "changed the file.",
        "paths": ('*/Google/Drive/*snapshot.db*',),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Drive 1.20 | 0 rows (no "
                                   "snapshot.db in the profile folder)",
            "lonewolf_win10": "Windows 10 Education build 16299, Backup and Sync 3.40 | 277 rows",
        },
    },
    "googleBackupSyncCloudGraph": {
        "name": "Google Backup and Sync Cloud Graph",
        "description": "The cloud listing the legacy Google Drive desktop client (Backup and Sync) kept in "
                       "cloud_graph.db: each cloud item's path, modified and created times, size, checksum, "
                       "version and change stamp, and its flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Google Drive",
        "notes": "Reads cloud_graph_entry and cloud_relations in cloud_graph/cloud_graph.db, with its -wal when "
                 "present, in each profile folder of the legacy Google Drive desktop client, one row per "
                 "cloud_graph_entry. Cloud Path is built from cloud_relations as Google Backup and Sync Items "
                 "builds it. Modified (UTC) and Created (UTC) are modified and created read as Unix seconds, "
                 "as for the snapshot's cloud entries; Created (UTC) held no value on any row of "
                 "lonewolf_win10. On lonewolf_win10 the database held 280 entries: all 277 snapshot.db cloud "
                 "entries, 274 of them with the same file name, modified time, size and checksum, and 3 "
                 "entries the snapshot does not hold, two of them with Shared 1 and ACL Role 2. So this "
                 "listing can name cloud items the snapshot does not hold. Size and Checksum are "
                 "size and checksum as stored. Document Type, Shared, Removed and ACL Role are doc_type, "
                 "shared, removed and acl_role as stored, read as Google Backup and Sync Items describes. "
                 "Removed held 0 on every row that has it. Version and Change Stamp are version and change_stamp as stored. "
                 "Doc ID is doc_id. Not reported: is_zombie, download_restricted and last_changed_locally, "
                 "which held 0 on every row of lonewolf_win10, original_size, original_checksum and "
                 "down_sample_status, and the changestamp table (one value). cfreds_leakage_win7 carries "
                 "cloud_graph/dict_2.db, a different table layout (a metadata table and one cloud_dict row "
                 "holding a text value), which is not read.",
        "paths": ('*/Google/Drive/*cloud_graph.db*',),
        "output_types": ["standard"],
        "artifact_icon": "cloud",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Drive 1.20 | 0 rows (no "
                                   "cloud_graph.db)",
            "lonewolf_win10": "Windows 10 Education build 16299, Backup and Sync 3.40 | 280 rows",
        },
    },
    "googleBackupSyncPendingChanges": {
        "name": "Google Backup and Sync Pending Changes",
        "description": "File system changes the legacy Google Drive desktop client (Backup and Sync) held in "
                       "its change buffer databases: the direction, the action, the full path and the "
                       "change's state as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Google Drive",
        "notes": "Reads fschanges and change_buffer_entries in the databases under TempData/<folder>/"
                 "change_buffer/ in each profile folder of the legacy Google Drive desktop client, one row per "
                 "fschanges row, joined to the change_buffer_entries row whose fschange names it. Direction "
                 "and Action are direction and action as stored (UPLOAD and DELETE on every row of "
                 "lonewolf_win10). Full Path, Is Folder, Doc ID and Parent Doc ID are full_path, is_folder, "
                 "doc_id and parent_doc_id as stored; Doc ID and Parent Doc ID held no value on any row of "
                 "lonewolf_win10. State and Failure Count are change_buffer_entries.state and failure_count "
                 "as stored, with no published definition found; State held 1 and Failure Count 0 on every row of "
                 "lonewolf_win10. Change ID is fschanges.identifier. No column held a wall-clock time on the "
                 "tested image: fschanges.modified and local_modified and change_buffer_entries.next_retry_time "
                 "held no value, and change_buffer_entries.time held fractional numbers between 700,000 and "
                 "900,000, too small to be Unix seconds, so it is not reported. On lonewolf_win10 two change buffer "
                 "databases were present, one with 5 rows and one empty, so 5 rows; a row records a change "
                 "the client queued, not that it reached Google's servers. Not reported: the other "
                 "fschanges columns; on lonewolf_win10 inode, name, name_hint, entry and hash varied by row and "
                 "the rest held no value or one value on every row.",
        "paths": ('*/Google/Drive/*/change_buffer/*.db*',),
        "output_types": ["standard"],
        "artifact_icon": "upload-cloud",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Drive 1.20 | 0 rows (no change "
                                   "buffer database)",
            "lonewolf_win10": "Windows 10 Education build 16299, Backup and Sync 3.40 | 5 rows",
        },
    },
    "googleBackupSyncExternalDevices": {
        "name": "Google Backup and Sync External Devices",
        "description": "External devices the legacy Google Drive desktop client (Backup and Sync) recorded "
                       "in device_db.db: the device's label and device ID, and the device's type, discovery "
                       "action and upload time as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Google Drive",
        "notes": "Reads external_devices in device_db.db in each profile folder of the legacy Google Drive "
                 "desktop client, one row per device. Label and Device ID are label and device_id as stored; "
                 "on lonewolf_win10 the one device ID is a Windows device path. USB Type, Discovery Action and "
                 "Upload Time are usb_type, device_discovery_action and upload_time as stored, with no "
                 "published definition found; Upload Time held no value on the tested row, and its epoch is not "
                 "established, so it is not converted. Doc ID and Parent Device ID are doc_id and "
                 "parent_device_id as stored. Doc ID and Parent Device ID held no value on the tested row. This table has no column for "
                 "when the device was seen; upload_time is its only time column. The other tables, device_files, pending_files and "
                 "device_upload_info, held no rows on lonewolf_win10 and are not read. A row records that the "
                 "client listed the device; it does not establish that any file was copied from it.",
        "paths": ('*/Google/Drive/*device_db.db*',),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Drive 1.20 | 0 rows (no "
                                   "device_db.db)",
            "lonewolf_win10": "Windows 10 Education build 16299, Backup and Sync 3.40 | 1 row",
        },
    },
    "googleBackupSyncSettings": {
        "name": "Google Backup and Sync Settings",
        "description": "The settings the legacy Google Drive desktop client (Backup and Sync) kept in "
                       "sync_config.db and global.db, among them the account email (user_email), the local sync "
                       "folder and the backed-up folders, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Google Drive",
        "notes": "Reads the data table of sync_config.db (entry_key, data_key, data_value) in each profile "
                 "folder, and the global_preferences (preference_type, preference_value) and username_mapping "
                 "(username, directory_path) tables of global.db beside the profile folders, of the legacy "
                 "Google Drive desktop client, one row per table row, as stored except the two pickle values described below. Key, Data Key and "
                 "Value are the stored columns; for global.db rows Key is the table name and Data Key the "
                 "preference type or user name. On lonewolf_win10 sync_config.db held 37 rows, among them "
                 "user_email, local_sync_root_path, highest_app_version and the root_config rows naming each "
                 "folder the client synced, and global.db 3 preference rows and no user name rows, so 40 rows. "
                 "Two sync_config.db values (feature_switch and tango_storage) are base64 text whose bytes "
                 "begin 0x80 0x02, the start of a Python pickle; they are reported by length and not decoded,"
                 " because decoding a pickle runs code. No published definition of the other "
                 "keys was found; their meaning is not established here beyond their names.",
        "paths": ('*/Google/Drive/*sync_config.db*', '*/Google/Drive/global.db*'),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Drive 1.20 | 0 rows (no "
                                   "sync_config.db or global.db)",
            "lonewolf_win10": "Windows 10 Education build 16299, Backup and Sync 3.40 | 40 rows",
        },
    },
    "googleBackupSyncLog": {
        "name": "Google Backup and Sync Log",
        "description": "The entries of sync_log.log, the log of the legacy Google Drive desktop client "
                       "(Backup and Sync): the time, level, process, thread, source code location and message "
                       "of each entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Google Drive",
        "notes": "Reads every file whose name contains sync_log.log under the profile folders "
                 "of the legacy Google Drive desktop client, one row per log entry. An entry begins "
                 "with a line of the form '<date> <time>,<milliseconds> <offset> <level> pid=<number> "
                 "<thread number>:<thread name> <source>:<line> <message>', the form plaso's parser reads "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/gdrive_synclog.py#L51-L94), "
                 "and every line that does not begin that way is part of the entry above it, kept in Message "
                 "on a line of its own, as written. Lines before the first entry of a file, if any, are kept "
                 "as one row with no time. Time as Recorded is the date, time and UTC offset "
                 "as written; Time (UTC) is that time converted with the written offset. Level, Process "
                 "ID, Thread and Source are the level, the pid number, the thread number and name, and the "
                 "source file or module with its line number, as written. Line is the line number of the "
                 "entry's first line and Source File the file. On lonewolf_win10 (Backup and Sync build "
                 "3.40) the 28,340 lines gave 18,880 entries, and on cfreds_leakage_win7 (Google Drive build "
                 "1.20) the 2,171 lines gave 2,000; on both every line was the start of an entry or a line "
                 "inside one, and no line came before the first entry. The messages are the client's own "
                 "diagnostic text and are not interpreted here: a message naming a file records what the "
                 "client logged about it, not that a person acted on the file.",
        "paths": ('*/Google/Drive/*sync_log.log*',),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Drive 1.20 | 2000 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, Backup and Sync 3.40 | 18880 rows",
        },
    },
}

import base64
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

_SIDECAR = re.compile(r'-(wal|shm|journal)$')


def _databases(context, name):
    """The staged paths of a database file, without its sidecars, in path order."""
    found = []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or _SIDECAR.search(path):
            continue
        if name is None or os.path.basename(path) == name:
            found.append(path)
    return found


def _columns(db, table):
    """The column names of a table, or an empty list when the table is absent."""
    try:
        return [row[1] for row in db.execute(f'PRAGMA table_info("{table}")')]
    except Exception:  # pylint: disable=broad-exception-caught
        return []


def _rows(db, query):
    try:
        return db.execute(query).fetchall()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logfunc(f'Google Backup and Sync: query failed ({exc})')
        return []


def unix_time(value):
    """A Unix seconds value as an aware UTC datetime, or '' when absent or out of range."""
    if value in (None, ''):
        return ''
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return ''


def build_paths(names, parents, key, separator):
    """Every path from an entry up its parent links to an entry with no parent.

    names: {key: file name}; parents: {key: [parent keys]}. A loop or a parent
    with no entry ends the walk there. Returns a list of paths, one per route.
    """
    paths = []

    def walk(current, tail, seen):
        if current not in names or current in seen:
            paths.append(separator.join(reversed(tail)))
            return
        tail = tail + [names[current] or '']
        ups = parents.get(current) or []
        if not ups:
            paths.append(separator.join(reversed(tail)))
            return
        for up in ups:
            walk(up, tail, seen | {current})

    walk(key, [], frozenset())
    return paths


def _separator(names):
    """Backslash when the roots are Windows paths, otherwise a slash."""
    return '\\' if any('\\' in (name or '') for name in names.values()) else '/'


def _cloud_tree(db, entry_table, id_column, child_column, parent_column):
    names = {row[0]: row[1] for row in _rows(db, f'SELECT {id_column}, filename FROM {entry_table}')}
    parents = defaultdict(list)
    for child, parent in _rows(db, f'SELECT {child_column}, {parent_column} FROM cloud_relations'):
        parents[child].append(parent)
    return names, parents


def snapshot_rows(path, relative):
    """The rows of one snapshot.db, for either schema."""
    db = open_sqlite_db_readonly(path)
    if db is None:
        return []
    try:
        cloud_cols = _columns(db, 'cloud_entry')
        local_cols = _columns(db, 'local_entry')
        if not cloud_cols and not local_cols:
            logfunc(f'Google Backup and Sync Items: {relative} has no cloud_entry or local_entry table')
            return []
        cloud_id = 'doc_id' if 'doc_id' in cloud_cols else 'resource_id'
        inode = 'inode' if 'inode' in local_cols else 'inode_number'
        has_volume = 'volume' in local_cols
        rel_cols = _columns(db, 'cloud_relations')
        child_c = 'child_doc_id' if 'child_doc_id' in rel_cols else 'child_resource_id'
        parent_c = 'parent_doc_id' if 'parent_doc_id' in rel_cols else 'parent_resource_id'

        def pick(cols, name):
            return name if name in cols else 'NULL'

        cloud = {}
        for entry in _rows(db, f'SELECT {cloud_id}, filename, {pick(cloud_cols, "modified")}, '
                             f'{pick(cloud_cols, "created")}, {pick(cloud_cols, "size")}, '
                             f'{pick(cloud_cols, "checksum")}, {pick(cloud_cols, "doc_type")}, '
                             f'{pick(cloud_cols, "shared")}, {pick(cloud_cols, "removed")}, '
                             f'{pick(cloud_cols, "acl_role")} FROM cloud_entry'):
            cloud[entry[0]] = entry[1:]
        volume = 'volume' if has_volume else "''"
        local = {}
        for entry in _rows(db, f'SELECT {inode}, {volume}, filename, {pick(local_cols, "modified")}, '
                             f'{pick(local_cols, "size")}, {pick(local_cols, "checksum")}, '
                             f'{pick(local_cols, "is_folder")} FROM local_entry'):
            local[(entry[0], entry[1])] = entry[2:]
        lrel = _columns(db, 'local_relations')
        lparents = defaultdict(list)
        if 'child_volume' in lrel:
            query = 'SELECT child_inode, child_volume, parent_inode, parent_volume FROM local_relations'
            for c_inode, c_vol, p_inode, p_vol in _rows(db, query):
                lparents[(c_inode, c_vol)].append((p_inode, p_vol))
        elif lrel:
            for c_inode, p_inode in _rows(db, 'SELECT child_inode_number, parent_inode_number '
                                              'FROM local_relations'):
                lparents[(c_inode, '')].append((p_inode, ''))
        mcols = _columns(db, 'mapping')
        pairs = []
        if mcols:
            m_inode = 'inode' if 'inode' in mcols else 'inode_number'
            m_id = 'doc_id' if 'doc_id' in mcols else 'resource_id'
            m_vol = 'volume' if 'volume' in mcols else "''"
            pairs = _rows(db, f'SELECT {m_inode}, {m_vol}, {m_id} FROM mapping')
        cnames, cparents = _cloud_tree(db, 'cloud_entry', cloud_id, child_c, parent_c) if rel_cols else ({}, {})
    finally:
        db.close()

    lnames = {key: value[0] for key, value in local.items()}
    lsep = _separator({k: v for k, v in lnames.items() if k not in lparents})

    def row(local_key, doc_id):
        lval = local.get(local_key) if local_key is not None else None
        cval = cloud.get(doc_id) if doc_id is not None else None
        local_path = '\n'.join(build_paths(lnames, lparents, local_key, lsep)) if lval else ''
        cloud_path = '\n'.join(build_paths(cnames, cparents, doc_id, '/')) if cval else ''
        _, l_mod, l_size, l_sum, l_folder = lval if lval else ('', None, '', '', '')
        _name, c_mod, c_created, c_size, c_sum, doc_type, shared, removed, acl = (
            cval if cval else ('', None, None, '', '', '', '', '', ''))
        return (unix_time(l_mod), unix_time(c_mod), unix_time(c_created), local_path, cloud_path,
                '' if l_folder is None else l_folder, '' if l_size is None else l_size, l_sum or '',
                '' if c_size is None else c_size, c_sum or '', '' if doc_type is None else doc_type,
                '' if shared is None else shared, '' if removed is None else removed,
                '' if acl is None else acl, doc_id or '',
                '' if local_key is None else local_key[0], '' if local_key is None else local_key[1],
                relative)

    rows = []
    unmatched = 0
    mapped_local, mapped_cloud = set(), set()
    for m_inode, m_vol, doc_id in pairs:
        key = (m_inode, m_vol)
        mapped_local.add(key)
        mapped_cloud.add(doc_id)
        if key not in local and doc_id not in cloud:
            unmatched += 1
            continue
        rows.append(row(key if key in local else None, doc_id if doc_id in cloud else None))
    for key in local:
        if key not in mapped_local:
            rows.append(row(key, None))
    for doc_id in cloud:
        if doc_id not in mapped_cloud:
            rows.append(row(None, doc_id))
    if unmatched:
        logfunc(f'Google Backup and Sync Items: {relative}: {unmatched} mapping row(s) name neither a local '
                f'nor a cloud entry and are not reported')
    return rows


@artifact_processor
def googleBackupSyncItems(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Cloud Modified (UTC)', 'datetime'),
                    ('Cloud Created (UTC)', 'datetime'), 'Local Path', 'Cloud Path', 'Is Folder', 'Size',
                    'MD5', 'Cloud Size', 'Cloud Checksum', 'Document Type (as stored)', 'Shared (as stored)',
                    'Removed (as stored)', 'ACL Role (as stored)', 'Doc ID', 'Inode', 'Volume',
                    'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'snapshot.db'):
        sources.append(path)
        data_list.extend(snapshot_rows(path, context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(sources)


def cloud_graph_rows(path, relative):
    db = open_sqlite_db_readonly(path)
    if db is None:
        return []
    try:
        cols = _columns(db, 'cloud_graph_entry')
        if not cols:
            logfunc(f'Google Backup and Sync Cloud Graph: {relative} has no cloud_graph_entry table')
            return []

        def pick(name):
            return name if name in cols else 'NULL'

        entries = _rows(db, f'SELECT doc_id, filename, {pick("modified")}, {pick("created")}, '
                            f'{pick("size")}, {pick("checksum")}, {pick("doc_type")}, {pick("shared")}, '
                            f'{pick("removed")}, {pick("acl_role")}, {pick("version")}, '
                            f'{pick("change_stamp")} FROM cloud_graph_entry')
        names = {e[0]: e[1] for e in entries}
        parents = defaultdict(list)
        if _columns(db, 'cloud_relations'):
            for child, parent in _rows(db, 'SELECT child_doc_id, parent_doc_id FROM cloud_relations'):
                parents[child].append(parent)
    finally:
        db.close()

    def blank(value):
        return '' if value is None else value

    return [(unix_time(e[2]), unix_time(e[3]), '\n'.join(build_paths(names, parents, e[0], '/')),
             blank(e[4]), blank(e[5]), blank(e[6]), blank(e[7]), blank(e[8]), blank(e[9]), blank(e[10]),
             blank(e[11]), e[0], relative) for e in entries]


@artifact_processor
def googleBackupSyncCloudGraph(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Created (UTC)', 'datetime'), 'Cloud Path', 'Size',
                    'Checksum', 'Document Type (as stored)', 'Shared (as stored)', 'Removed (as stored)',
                    'ACL Role (as stored)', 'Version', 'Change Stamp', 'Doc ID', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'cloud_graph.db'):
        sources.append(path)
        data_list.extend(cloud_graph_rows(path, context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(sources)


def pending_change_rows(path, relative):
    db = open_sqlite_db_readonly(path)
    if db is None:
        return []
    try:
        cols = _columns(db, 'fschanges')
        if not cols:
            return []

        def pick(name):
            return f'f.{name}' if name in cols else 'NULL'

        join = ''
        state = failures = 'NULL'
        if {'fschange', 'state'} <= set(_columns(db, 'change_buffer_entries')):
            join = 'LEFT JOIN change_buffer_entries b ON b.fschange = f.identifier'
            state, failures = 'b.state', 'b.failure_count'
        rows = _rows(db, f'SELECT {pick("direction")}, {pick("action")}, {pick("full_path")}, '
                         f'{pick("is_folder")}, {pick("doc_id")}, {pick("parent_doc_id")}, {state}, '
                         f'{failures}, f.identifier FROM fschanges f {join} ORDER BY f.identifier')
    finally:
        db.close()
    return [tuple('' if v is None else v for v in r) + (relative,) for r in rows]


@artifact_processor
def googleBackupSyncPendingChanges(context):
    data_headers = ('Direction', 'Action', 'Full Path', 'Is Folder', 'Doc ID', 'Parent Doc ID',
                    'State (as stored)', 'Failure Count', 'Change ID', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, None):
        if not path.endswith('.db'):
            continue
        sources.append(path)
        data_list.extend(pending_change_rows(path, context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def googleBackupSyncExternalDevices(context):
    data_headers = ('Label', 'Device ID', 'USB Type (as stored)', 'Discovery Action (as stored)',
                    'Upload Time (as stored)', 'Doc ID', 'Parent Device ID', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, 'device_db.db'):
        sources.append(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            cols = _columns(db, 'external_devices')
            if not cols:
                continue
            fields = [c if c in cols else 'NULL' for c in ('label', 'device_id', 'usb_type',
                                                           'device_discovery_action', 'upload_time',
                                                           'doc_id', 'parent_device_id')]
            rows = _rows(db, f'SELECT {", ".join(fields)} FROM external_devices')
        finally:
            db.close()
        relative = context.get_relative_path(path)
        data_list.extend(tuple('' if v is None else v for v in r) + (relative,) for r in rows)
    return data_headers, data_list, '\n'.join(sources)


def setting_value(value):
    """A stored setting value; a base64 pickle is described, never decoded."""
    if value is None:
        return ''
    text = str(value)
    if text.startswith('gAJ'):
        try:
            if base64.b64decode(text[:4])[:2] == b'\x80\x02':
                return f'(base64 Python pickle, {len(text)} characters, not decoded)'
        except ValueError:
            pass
    return text


@artifact_processor
def googleBackupSyncSettings(context):
    data_headers = ('Key', 'Data Key', 'Value', 'Source File')
    data_list, sources = [], []
    for path in _databases(context, None):
        name = os.path.basename(path)
        if name not in ('sync_config.db', 'global.db'):
            continue
        sources.append(path)
        relative = context.get_relative_path(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            if name == 'sync_config.db':
                for key, data_key, value in _rows(db, 'SELECT entry_key, data_key, data_value FROM data'):
                    data_list.append((key or '', data_key or '', setting_value(value), relative))
            else:
                for kind, value in _rows(db, 'SELECT preference_type, preference_value '
                                             'FROM global_preferences'):
                    data_list.append(('global_preferences', kind or '', setting_value(value), relative))
                for user, directory in _rows(db, 'SELECT username, directory_path FROM username_mapping'):
                    data_list.append(('username_mapping', user or '', directory or '', relative))
        finally:
            db.close()
    return data_headers, data_list, '\n'.join(sources)


_ENTRY = re.compile(r'(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})[,.](?P<ms>\d{3}) '
                    r'(?P<offset>[+-]\d{4}) (?P<level>[A-Za-z]+) pid=(?P<pid>\d+) '
                    r'(?P<thread>\d+:\S+)\s+(?P<source>\S+:\d+) ?(?P<message>.*)$')


def entry_time(match):
    """The entry's local time with its offset, as an aware UTC datetime."""
    offset = match.group('offset')
    text = f"{match.group('date')}T{match.group('time')}.{match.group('ms')}{offset[:3]}:{offset[3:]}"
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return ''


def file_lines(text):
    """The lines of a text file split at line feeds only, as a line counter counts them."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def log_entries(lines, counts):
    """(time, time as recorded, level, pid, thread, source, message, line) per entry of a sync log."""
    entries = []
    current = None
    for number, raw in enumerate(lines, 1):
        text = raw.rstrip('\r\n')
        match = _ENTRY.match(text)
        if match:
            if current:
                entries.append(current)
            recorded = f"{match.group('date')} {match.group('time')},{match.group('ms')} {match.group('offset')}"
            current = [entry_time(match), recorded, match.group('level'), match.group('pid'),
                       match.group('thread'), match.group('source'), match.group('message'), number]
            counts['entries'] += 1
        elif current is not None:
            current[6] += '\n' + text
            counts['continuation lines'] += 1
        else:
            current = ['', '', '', '', '', '', text, number]
            counts['lines before the first entry'] += 1
    if current:
        entries.append(current)
    return [tuple(entry) for entry in entries]


@artifact_processor
def googleBackupSyncLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Level', 'Process ID', 'Thread', 'Source',
                    'Message', 'Line', 'Source File')
    data_list, sources = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8', errors='replace', newline='') as handle:
                text = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        sources.append(path)
        relative = context.get_relative_path(path)
        data_list.extend(entry + (relative,) for entry in log_entries(file_lines(text), counts))
    if counts:
        logfunc('Google Backup and Sync Log: ' + ', '.join(f'{n:,} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(sources)
