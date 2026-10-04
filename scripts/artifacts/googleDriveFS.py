"""Google Drive for desktop (DriveFS) items, mirrored items, accounts, account authorizations,
synced folders and volumes, for DLEAPP.

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
            'Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) metadata_sqlite_db '
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
            'extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) mirror_sqlite.db holds 2 items: '
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
    "googleDriveAccounts": {
        "name": "Google Drive Accounts",
        "description": "Account IDs that Google Drive for desktop's experiments.db lists or that name an account "
                       'folder with a metadata database, with the name, email address and photo URL of the '
                       "account's driveway_account record where one is read.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Google Drive",
        "notes": (
            'Reads experiments.db in each Google Drive for desktop (DriveFS) folder, which is '
            'Library/Application Support/Google/DriveFS on the tested Mac, and the '
            'driveway_account record in the properties table of the metadata_sqlite_db and '
            'mirror_metadata_sqlite.db in each account folder. Amged Wageh documents that the '
            'PhenotypeValues table of experiments.db lists under its account_ids key the IDs of '
            'the accounts that have logged in, including accounts that have since logged out, '
            "that a folder named after each account's ID is created when the account logs in, and "
            "that the account's folder is deleted when it logs out (Reference: Amged Wageh, "
            "'DriveFS Sleuth: Your Ultimate Google Drive File Stream Investigator!', "
            'https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980). '
            'The account IDs are the field 1 strings of the account_ids value and the names of '
            'the account folders that hold a metadata database. Each account ID of a DriveFS '
            'folder gives one row, or one row per distinct name, email address and photo URL when '
            'its databases give differing ones, and a folder with two differing copies of '
            'experiments.db gives its rows once for each copy. Listed in account_ids is Yes or No '
            "when the folder's experiments.db was read, and blank when it was not. Account "
            'Database Found is Yes when a metadata database in a folder named after the ID was '
            'read and No when not; an ID with Listed in account_ids Yes and Account Database '
            "Found No fits the post's description of an account that logged out, and an "
            'extraction that left the folder out gives the same row. Name and Photo URL are '
            'fields 3 and 5 of field 1 of field 2 of the driveway_account record, as DriveFS '
            'Sleuth reads them (Reference: Amged Wageh, DriveFS Sleuth, '
            'https://github.com/AmgdGocha/DriveFS-Sleuth/blob/839e27193fa650750ec6eaccb785b32c55c6ac11/src/drivefs_sleuth/utils.py#L216-L222). '
            'Email is field 8 of the same message; no source for that field was found, and on the '
            'MacBook Pro it holds the address that the drive_fs logs pair with the account ID on '
            'every line that pairs the two, 12 lines, while field 2 of that message holds the '
            'account ID itself. A database with no driveway_account record gives Name, Email and '
            'Photo URL blank, as does a record that does not parse, which is also logged. When '
            'metadata_sqlite_db and mirror_metadata_sqlite.db hold the same values the account is '
            "one row, and Source File lists both databases and the experiments.db that the row's "
            'other columns come from. experiments.db last_sync (UTC) is the last_sync value of '
            "the folder's experiments.db, stored as decimal text and read as Unix seconds in UTC, "
            'as DriveFS Sleuth reads it (Reference: Amged Wageh, DriveFS Sleuth, '
            'https://github.com/AmgdGocha/DriveFS-Sleuth/blob/839e27193fa650750ec6eaccb785b32c55c6ac11/src/drivefs_sleuth/utils.py#L81-L88 '
            'and '
            'https://github.com/AmgdGocha/DriveFS-Sleuth/blob/839e27193fa650750ec6eaccb785b32c55c6ac11/src/drivefs_sleuth/setup.py#L326); '
            'the post describes it as the last syncing date between all the currently logged-in '
            'accounts. It is stored once per DriveFS folder, so every row of one folder holds the '
            'same value. On the public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) it reads 24 December 2025 21:48:51 UTC, and the line of '
            "drive_fs_6.txt timed 2025-12-24T21:48:51.472Z logs 'ShouldSync: More than four hours "
            "since last sync.' from phenotype_impl.cc, followed by lines that create packages for "
            'drive_fs_ph and apps.drive.cello.desktop, the two packages experiments.db registers, '
            "and schedule a sync, while a line timed 2025-12-24T21:48:54.474Z logs 'ShouldSync: "
            "Last sync was only 3 seconds ago'. Whether the value also marks when files last "
            'synced was not established. On the MacBook Pro experiments.db lists one account ID, '
            'the name of the one account folder, and the driveway_account records of both '
            'metadata databases give the same name, email address and photo URL, so the artifact '
            'gives 1 row. The other PhenotypeValues keys are not reported. dleapp_macos_bigsur, '
            'the four registered Windows disk images and windows11_arm_parallels hold no DriveFS '
            'folder.'
        ),
        "paths": ('*/DriveFS/experiments.db*', '*/DriveFS/*/metadata_sqlite_db*',
                  '*/DriveFS/*/mirror_metadata_sqlite.db*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "googleDriveAuthorizations": {
        "name": "Google Drive Account Authorizations",
        "description": "Lines in Google Drive for desktop's drive_fs logs that record an account as authorized, "
                       'with the logged time, email address and account ID.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Google Drive",
        "notes": (
            'Reads the drive_fs logs, drive_fs.txt and drive_fs_N.txt, in the Logs folder of each '
            'Google Drive for desktop (DriveFS) folder, which is Library/Application '
            'Support/Google/DriveFS on the tested Mac. Amged Wageh names these as the most '
            "important of the app's logs and uses them to resolve account IDs to email addresses "
            "(Reference: Amged Wageh, 'DriveFS Sleuth: Your Ultimate Google Drive File Stream "
            "Investigator!', "
            'https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980). '
            'One row is reported per line that names StartAccountAuthComplete and reads '
            "'Authorized as' followed by an address and a numeric account ID in parentheses. Time "
            '(UTC) is the time at the start of the line, which the log writes with a trailing Z '
            'and which is read as UTC; Email and Account ID are taken from the line as logged, '
            "and Line is the line's number in its file. On the public MacBook Pro logical "
            'extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) each of the 12 drive_fs logs '
            'holds one such line, so the artifact gives 12 rows, from 9 December 2025 21:45:36 to '
            '24 December 2025 22:05:34 UTC. Email and Account ID hold one value on every row '
            "there, the address and the ID of the DriveFS folder's one account, and every line of "
            "those logs that DriveFS Sleuth's pattern for an address followed by an account ID in "
            'parentheses finds is one of the 12 (Reference: Amged Wageh, DriveFS Sleuth, '
            'https://github.com/AmgdGocha/DriveFS-Sleuth/blob/839e27193fa650750ec6eaccb785b32c55c6ac11/src/drivefs_sleuth/utils.py#L34-L44). '
            "Read as UTC, the line of drive_fs_6.txt timed 2025-12-24T21:48:51.472Z, 'ShouldSync: "
            "More than four hours since last sync.', falls in the same second as the last_sync "
            'value of experiments.db read as Unix seconds, which the Google Drive Accounts '
            'artifact reports. A line naming StartAccountAuthComplete in another form is counted '
            'in the run log and not reported. The rows cover only the logs in the extraction; on '
            'the MacBook Pro the oldest of them begins on 9 December 2025, so nothing here shows '
            'when the app first authorized the account. A byte-identical copy of a log under '
            'System/Volumes/Data is not read again, as 12 copies on the MacBook Pro are, and a '
            'line that two differing copies both hold is one row whose Source File lists both. '
            'The other lines of the drive_fs logs, and the other logs in the folder, are not '
            'reported. dleapp_macos_bigsur, the four registered Windows disk images and '
            'windows11_arm_parallels hold no DriveFS folder.'
        ),
        "paths": ('*/DriveFS/Logs/drive_fs*.txt',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "googleDriveSyncedFolders": {
        "name": "Google Drive Synced Folders",
        "description": "Sync roots (folders or storage devices) in the roots table of Google Drive for desktop's "
                       'root_preference_sqlite.db, with their title, paths, volume, destination and one_shot '
                       'flag as stored, and account ID.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Google Drive",
        "notes": (
            'Reads the roots table of root_preference_sqlite.db in each Google Drive for desktop '
            '(DriveFS) folder, which is Library/Application Support/Google/DriveFS on the tested '
            'Mac. Amged Wageh describes the table as holding an entry for each storage device '
            'configured to be synced and each mirrored folder, with an incremental root_id, the '
            "item's name in title, its path in root_path and last_seen_absolute_path, and in "
            "account_token the ID of the account it syncs to (Reference: Amged Wageh, 'DriveFS "
            "Sleuth: Your Ultimate Google Drive File Stream Investigator!', "
            'https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980). '
            'One row is reported per root, in root_id order; Title, Root Path, Last Seen Absolute '
            'Path, Account ID and Root ID are title, root_path, last_seen_absolute_path, '
            'account_token and root_id as stored. Destination (as stored) is destination, which '
            'the post reads as 1 for a root synced to Drive and 2 for one synced to Photos, a '
            'root synced to both having a row for each. One Shot (as stored) is one_shot, which '
            "the post reads as 1 when the 'Remember my choice for this device.' option was not "
            'selected and 0 for a permanent configuration, adding that the row of a device with '
            'one_shot 1 is deleted when the device is unplugged. Volume is the name the media '
            "table records for the root's media_id, blank when media has no row for it, and Media "
            'ID is media_id as stored; the post says the media_id of a storage device is the same '
            'GUID the Windows registry stores for it. Max Root ID (as stored) is the max_root_id '
            "value of the database's max_ids table, which the post says tracks the number of "
            'roots added, so that a max_root_id greater than the number of roots means some roots '
            'were removed or their configuration was modified. A database whose roots table holds '
            'no row gives no row, whatever max_ids holds. On the public MacBook Pro logical '
            'extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) the table holds 1 root, the '
            "folder Documents/Work in the user's home folder, with destination 1, one_shot 0, the "
            'Macintosh HD - Data volume, the one account ID of the DriveFS folder and a '
            'max_root_id of 1; mirror_sqlite.db names the same root_id for that folder. '
            'sync_type, medium, state, is_my_drive, doc_id and the metadata column are not '
            'reported, since no source for their values was found. dleapp_macos_bigsur, the four '
            'registered Windows disk images and windows11_arm_parallels hold no DriveFS folder.'
        ),
        "paths": ('*/DriveFS/root_preference_sqlite.db*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "folder",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "googleDriveVolumes": {
        "name": "Google Drive Volumes",
        "description": "Volumes in the media table of Google Drive for desktop's root_preference_sqlite.db, with "
                       'their name, last mount point, capacity and ignored flag as stored, and media ID.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Google Drive",
        "notes": (
            'Reads the media table of root_preference_sqlite.db in each Google Drive for desktop '
            '(DriveFS) folder, which is Library/Application Support/Google/DriveFS on the tested '
            'Mac. Amged Wageh describes the table as tracking whether each connected storage '
            'device should be synced, the app ignoring a device whose ignored is 1, and as '
            "recording the device's name, its last mount point (a drive letter on Windows) and "
            'its size in bytes in capacity, which is -1 for, for example, a mobile device whose '
            'data the user did not allow the app to access; he adds that media_id is a GUID the '
            'registry also stores for the device, so that it can be matched to the roots table '
            "and used for USB forensics (Reference: Amged Wageh, 'DriveFS Sleuth: Your Ultimate "
            "Google Drive File Stream Investigator!', "
            'https://amgedwageh.medium.com/drivefs-sleuth-investigating-google-drive-file-streams-disk-artifacts-0b5ea637c980). '
            "One row is reported per media row, in the table's rowid order; Name, Last Mount "
            'Point, Capacity (as stored), Ignored (as stored) and Media ID are name, '
            'last_mount_point, capacity, ignored and media_id as stored. File System Type (as '
            'stored) and Device Type (as stored) are fs_type and device_type; no source for their '
            'values was found. On the public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) the table holds 13 volumes, and Ignored (as stored) holds one '
            'value, 0, on every row. They are Preboot, VM, Update, Macintosh HD and home, last '
            'mounted under /System/Volumes; Macintosh HD - Data, last mounted at /; two named '
            'Install Google Drive with different capacities, one named qual and one named bkp, '
            'last mounted under /Volumes; and three named bkp@snap- followed by a number, last '
            'mounted under /Volumes/.timemachine. home and the three snapshots have a capacity of '
            '0 and a media_id beginning nouuid--, and none has a capacity of -1. Only one of the '
            '13, Macintosh HD - Data, is the volume of a root in the roots table; the other 12 '
            'are the volume of no root. dleapp_macos_bigsur, the four registered Windows disk '
            'images and windows11_arm_parallels hold no DriveFS folder.'
        ),
        "paths": ('*/DriveFS/root_preference_sqlite.db*',),
        "output_types": ["html", "tsv", "lava"],
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
import re
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_biome import fields as _fields, first as _first, text as _text
from scripts.macos_plists import canonical_relative, unique_sources
from scripts.macos_powerlog import merge_sources

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_ITEM_DATABASES = ('metadata_sqlite_db', 'mirror_metadata_sqlite.db')
_EXPERIMENTS = 'experiments.db'
_PREFERENCES = 'root_preference_sqlite.db'
_LOG_NAME = re.compile(r'drive_fs(?:_\d+)?\.txt')
_AUTHORIZED = re.compile(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z\S*\s+\[[^\]]*\]\s+\S+:'
                         r'StartAccountAuthComplete Authorized as (\S+) \((\d+)\)\s*')
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


def _seconds(value):
    """Unix seconds, stored as a number or as decimal text, as a UTC datetime; blank otherwise."""
    if isinstance(value, (bytes, bytearray)):
        value = bytes(value).decode('ascii', 'replace')
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if isinstance(value, bool) or not isinstance(value, int) or value == 0:
        return ''
    try:
        return _UNIX_EPOCH + timedelta(seconds=value)
    except OverflowError:
        return ''


def _experiments(path, relative):
    """(account IDs, last_sync) from the PhenotypeValues table of experiments.db. account_ids
    holds each ID as a field 1 string; the IDs are None when the key is absent or unreadable."""
    if not does_table_exist_in_db(path, 'PhenotypeValues'):
        logfunc(f'Google Drive Accounts: no PhenotypeValues table in {relative}')
        return None, ''
    stored = {row['key']: row['value'] for row in get_sqlite_db_records(
        path, "SELECT Key AS key, Value AS value FROM PhenotypeValues "
              "WHERE Key IN ('account_ids', 'last_sync')")}
    ids = None
    listed = stored.get('account_ids')
    if isinstance(listed, (bytes, bytearray)):
        try:
            ids = [_text(value) for value in _fields(bytes(listed)).get(1, [])]
        except ValueError as error:
            logfunc(f'Google Drive Accounts: account_ids in {relative} not read: {error}')
    return ids, _seconds(stored.get('last_sync'))


def _identity(path, relative):
    """(name, email, photo URL) from the driveway_account record in the properties table of an
    account's metadata database: its field 2, then field 1, holds them at fields 3, 8 and 5."""
    if not does_table_exist_in_db(path, 'properties'):
        return '', '', ''
    stored = get_sqlite_db_records(path, "SELECT value FROM properties WHERE property = 'driveway_account'")
    value = stored[0]['value'] if stored else None
    if not isinstance(value, (bytes, bytearray)):
        return '', '', ''
    try:
        message = bytes(value)
        for number in (2, 1):
            message = _first(_fields(message), number)
            if not isinstance(message, (bytes, bytearray)):
                raise ValueError(f'no message in field {number}')
        found = _fields(bytes(message))
    except ValueError as error:
        logfunc(f'Google Drive Accounts: driveway_account in {relative} not read: {error}')
        return '', '', ''
    return tuple(_text(_first(found, number)) for number in (3, 8, 5))


@artifact_processor
def googleDriveAccounts(context):
    data_headers = (('experiments.db last_sync (UTC)', 'datetime'), 'Account ID', 'Name', 'Email',
                    'Photo URL', 'Listed in account_ids', 'Account Database Found', 'Source File')
    folders, read = {}, []
    experiments, _skipped = unique_sources(context, _databases(context, (_EXPERIMENTS,)), sidecars=('-wal',),
                                           label='Google Drive Accounts (experiments.db)')
    for path in experiments:
        relative = context.get_relative_path(path)
        ids, last_sync = _experiments(path, relative)
        if ids is None and last_sync == '':
            continue
        read.append(path)
        folder = canonical_relative(os.path.dirname(relative.replace('\\', '/')))
        folders.setdefault(folder, []).append((ids, last_sync, relative))
    found = {}
    databases, _skipped = unique_sources(context, _databases(context, _ITEM_DATABASES), sidecars=('-wal',),
                                         label='Google Drive Accounts (account databases)')
    for path in databases:
        relative = context.get_relative_path(path)
        account_folder = os.path.dirname(relative.replace('\\', '/'))
        key = (canonical_relative(os.path.dirname(account_folder)), os.path.basename(account_folder))
        found.setdefault(key, []).append((_identity(path, relative), relative))
        read.append(path)
    data_list = []
    for folder in sorted(set(folders) | {folder for folder, _account in found}):
        listed_here = {value for ids, _last, _rel in folders.get(folder, []) for value in ids or []}
        accounts = sorted(listed_here | {account for place, account in found if place == folder})
        for ids, last_sync, source in folders.get(folder) or [(None, '', '')]:
            for account in accounts:
                listed = '' if ids is None else ('Yes' if account in ids else 'No')
                held = found.get((folder, account))
                if not held:
                    data_list.append((last_sync, account, '', '', '', listed, 'No', source))
                    continue
                records = [((last_sync, account) + identity + (listed, 'Yes'), relative)
                           for identity, relative in held]
                for values, sources in merge_sources(records):
                    data_list.append(values + ('\n'.join(sources + ([source] if source else [])),))
    return data_headers, data_list, '\n'.join(read)


def _log_time(stamp):
    """A logged ISO time with its trailing Z removed, as a UTC datetime; blank if not a date."""
    base, _dot, fraction = stamp.partition('.')
    try:
        moment = datetime.strptime(base, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return ''
    return moment.replace(microsecond=int((fraction + '000000')[:6]), tzinfo=timezone.utc)


@artifact_processor
def googleDriveAuthorizations(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Email', 'Account ID', 'Line', 'Source File')
    logs = [str(path) for path in context.get_files_found()
            if _LOG_NAME.fullmatch(os.path.basename(str(path))) and os.path.isfile(str(path))]
    paths, _skipped = unique_sources(context, logs, label='Google Drive Account Authorizations')
    records, read, unmatched = [], [], 0
    for path in paths:
        relative = context.get_relative_path(path)
        before = len(records)
        with open(path, encoding='utf-8', errors='replace') as handle:
            for number, line in enumerate(handle, 1):
                if 'StartAccountAuthComplete' not in line:
                    continue
                match = _AUTHORIZED.match(line)
                if not match:
                    unmatched += 1
                    continue
                records.append(((_log_time(match.group(1)), match.group(2), match.group(3), number),
                                relative))
        if len(records) > before:
            read.append(path)
    if unmatched:
        logfunc(f'Google Drive Account Authorizations: {unmatched} StartAccountAuthComplete line(s) '
                'not in the form read here, not reported')
    records.sort(key=lambda record: (str(record[0][0]), len(record[1]), record[1], record[0][3]))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)


def _volume_names(path):
    if not does_table_exist_in_db(path, 'media'):
        return {}
    return {row['media_id']: row['name'] for row in _select(path, 'media', ('media_id', 'name'))}


@artifact_processor
def googleDriveSyncedFolders(context):
    data_headers = ('Title', 'Last Seen Absolute Path', 'Root Path', 'Volume', 'Media ID',
                    'Destination (as stored)', 'One Shot (as stored)', 'Account ID', 'Root ID',
                    'Max Root ID (as stored)', 'Source File')
    paths, _skipped = unique_sources(context, _databases(context, (_PREFERENCES,)),
                                     sidecars=('-wal',), label='Google Drive Synced Folders')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'roots'):
            logfunc(f'Google Drive Synced Folders: no roots table in {relative}')
            continue
        rows = _select(path, 'roots', ('root_id', 'title', 'root_path', 'last_seen_absolute_path',
                                       'media_id', 'account_token', 'destination', 'one_shot'),
                       'ORDER BY root_id')
        if not rows:
            continue
        read.append(path)
        volumes = _volume_names(path)
        highest = ''
        if does_table_exist_in_db(path, 'max_ids'):
            stored = get_sqlite_db_records(path, "SELECT value FROM max_ids WHERE id_type = 'max_root_id'")
            highest = _blank(stored[0]['value']) if stored else ''
        for row in rows:
            records.append(((_blank(row['title']), _blank(row['last_seen_absolute_path']),
                             _blank(row['root_path']), volumes.get(row['media_id'], ''),
                             _blank(row['media_id']), _blank(row['destination']),
                             _blank(row['one_shot']), _blank(row['account_token']),
                             _blank(row['root_id']), highest), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def googleDriveVolumes(context):
    data_headers = ('Name', 'Last Mount Point', 'Capacity (as stored)', 'Ignored (as stored)',
                    'File System Type (as stored)', 'Device Type (as stored)', 'Media ID',
                    'Source File')
    paths, _skipped = unique_sources(context, _databases(context, (_PREFERENCES,)),
                                     sidecars=('-wal',), label='Google Drive Volumes')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'media'):
            logfunc(f'Google Drive Volumes: no media table in {relative}')
            continue
        rows = _select(path, 'media', ('name', 'last_mount_point', 'capacity', 'ignored', 'fs_type',
                                       'device_type', 'media_id'), 'ORDER BY rowid')
        if not rows:
            continue
        read.append(path)
        for row in rows:
            records.append((tuple(_blank(row[name]) for name in (
                'name', 'last_mount_point', 'capacity', 'ignored', 'fs_type', 'device_type',
                'media_id')), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)
