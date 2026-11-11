"""Items in the iCloud Drive (CloudDocs) client database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosICloudDriveItems": {
        "name": "iCloud Drive Items",
        "description": "Items in each user's iCloud Drive client database (CloudDocs client.db): "
                       "file name, the path rebuilt from the parent entries it stores, the stored "
                       "item type and size, zone and app library, the device name the server.db devices table "
                       "gives for the item's version_device, "
                       "with the stored birth, modification and last used times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": "Reads each user's client.db under ~/Library/Application "
                 "Support/CloudDocs/session/db, one row per client_items row. Version "
                 "Modified (UTC), Item Birth Time (UTC) and Last Used (UTC) are "
                 "version_mtime, item_birthtime and item_lastusedtime read as Unix "
                 "seconds, and a stored 0 is reported blank; read that way the Item Birth "
                 "Time values on dleapp_macos_bigsur fall between 1 January 2020 and 19 "
                 "February 2021, where the 2001 epoch would place them in 2051 and 2052. "
                 "Last Used is blank on 56 of the 72 rows there. File Name is "
                 "item_filename. Path joins the item's name to the names of the items its "
                 "item_parent_id chain reaches in the same table, outermost first; a "
                 "parent the table does not hold ends the chain, so Path can start below "
                 "the top of the zone. Item Type, Size, User Visible and Trash Put-Back "
                 "Path are item_type, version_size, item_user_visible and "
                 "item_trash_put_back_path as stored; on dleapp_macos_bigsur the 47 rows "
                 "of type 0 and the 2 of type 4 store no size, and 2 rows carry a put-back "
                 "path. Zone is the zone_name of the client_zones row and App Library the "
                 "app_library_name of the app_libraries row the item names. Zone and App "
                 "Library held the same text on 56 of the 72 rows on dleapp_macos_bigsur "
                 "and were identical on every row of the public MacBook Pro logical "
                 "extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15). On the MacBook Pro "
                 "version_mtime is 0 on 27 of the 42 items, so Version Modified is blank "
                 "on those rows, Trash Put-Back Path is empty on every row, and the Users/ and "
                 "System/Volumes/Data/Users/ copies hold a byte-identical client.db with "
                 "different -wal files, and both are read; each of the 42 items is in both and is reported once, with both files in Source File. "
                 "Version Device is the name in the devices table of the server.db beside client.db whose key "
                 "equals the item's version_device as stored; the stored number is shown when no such row or "
                 "file is there, and no tested image exercised that case. This module cites no Apple "
                 "documentation for either column, so that the named device wrote the version is "
                 "what the column name says, not something a source establishes. Every non-null version_device "
                 "on the tested images resolved to a name: 23 of 72 rows on dleapp_macos_bigsur (3 device names), "
                 "10 of 42 on mvs2026_macbookpro_macos15 (2) and 4 of 30 on magnet2021_macos_bigsur (2); Version "
                 "Device held no value on the other rows, whose version_device is null. The server_items and devices "
                 "tables of server.db are reported by the iCloud Drive Server Items and iCloud Drive Devices "
                 "artifacts. All rows on each image come from one user, so User holds "
                 "one value there. When a logical extraction holds the same file under "
                 "Users/ and under System/Volumes/Data/Users/, a second copy whose database and "
                 "-wal file are both byte-identical to the first is not read again, and is "
                 "counted in the run log."
                 " Copies of one file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ "
                 "are all read; a row identical in every other column in more than one copy is reported as "
                 "often as the copy holding it most often holds it, normally once, and its Source File "
                 "lists each file that held it, one per line.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 72 rows",
                           "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 30 rows",
                           "mvs2026_macbookpro_macos15": "macOS 15.4 | 42 rows",
                           "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
                           "adams_macbookpro_macos26": "macOS 26.2 | 40 rows",
                       },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/client.db*',
                  '*/Library/Application Support/CloudDocs/session/db/server.db*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "cloud",
    },
    "macosICloudDriveServerItems": {
        "name": "iCloud Drive Server Items",
        "description": "Rows of the server_items table of each user's CloudDocs server.db on macOS: file name, path, type, size and stored times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": (
            "Reads each user's server.db under ~/Library/Application Support/CloudDocs/session/db, one row per "
            "server_items row. The column names are the table's own and no Apple documentation of the table is "
            'cited, so what a row shows about the server beyond its name is not established. Item Birth Time '
            '(UTC), Version Modified (UTC) and Last Used (UTC) are item_birthtime, version_mtime and '
            'item_lastusedtime read as Unix seconds, the reading the iCloud Drive Items artifact uses for the '
            'same column names in client.db, and a stored 0 is reported blank. File Name is item_filename and '
            "Version Name is version_name. Path joins the item's name to the names of the items its "
            'item_parent_id chain reaches in the same zone of the same table, outermost first; a parent the '
            'table does not hold ends the chain. Item Type, Item State, Size, Quota Used, Child Count and '
            'Recursive Child Count are item_type, item_state, version_size, quota_used, child_count and '
            'recursive_child_count as stored, and a stored null is reported blank. The unit of version_size is '
            'not sourced; the Size header follows the iCloud Drive Items artifact. Zone is the zone_name of the'
            ' server_zones row whose rowid equals zone_rowid, and the stored number when there is no such row, '
            'which no tested image exercised. Version Device is the name in the devices table of the same '
            'database whose key equals version_device, and the stored number when there is no such row, which '
            'no tested image exercised; it held no value on the rows whose version_device is null (12 of 16, 20'
            ' of 43, 5 of 15 and 9 of 13). The other columns of the table, among them signatures, sharing '
            'fields and Finder tags, are not reported. On the four tested images with rows every File Name in '
            'this table was also a File Name of the iCloud Drive Items artifact, so no tested image holds a '
            'server_items row whose file name client_items lacks. Item State held one value on every row of '
            'each of those images (0). Last Used held no value on any row of the Magnet macOS 11.2.1 image. '
            'User is the folder after Users in the path, root for a file under private/var/root, and blank '
            'otherwise. User held one value on every row of each tested image. A copy of the database under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ whose database and -wal file are both '
            'byte-identical to one already read is not read again and the run log counts it. A row identical in'
            ' every other column in copies that differ is reported as often as the copy holding it most often '
            'holds it, normally once, with each file in Source File, one per line. No row on the tested images '
            'was folded this way.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 16 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 43 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 15 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 13 rows",
        },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/server.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "cloud",
    },
    "macosICloudDriveDevices": {
        "name": "iCloud Drive Devices",
        "description": "Rows of the devices table of each user's CloudDocs server.db on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": (
            "Reads each user's server.db under ~/Library/Application Support/CloudDocs/session/db, one row per "
            'row of its devices table: Device Name is name and Key is key, as stored. The table is what the '
            "iCloud Drive artifacts use to name an item's version_device. What puts a device in the table and "
            'whether a row is ever removed is not established, so a row shows the name was recorded, not when '
            'or how that device was used. The four tested images with rows held 2 or 3. User is the folder '
            'after Users in the path, root for a file under private/var/root, and blank otherwise. User held '
            'one value on every row of each tested image. A copy of the database under System/Volumes/Data/ or '
            'System/Volumes/Update/mnt1/ whose database and -wal file are both byte-identical to one already '
            'read is not read again and the run log counts it. A row identical in every other column in copies '
            'that differ is reported as often as the copy holding it most often holds it, normally once, with '
            'each file in Source File, one per line. No row on the tested images was folded this way.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 2 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 2 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 2 rows",
        },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/server.db*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "monitor",
    },
    "macosICloudDriveBootHistory": {
        "name": "iCloud Drive Boot History",
        "description": "Rows of the boot_history table of each user's CloudDocs client.db on macOS: a date with the os and br values stored beside it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": (
            "Reads each user's client.db under ~/Library/Application Support/CloudDocs/session/db, one row per "
            'row of its boot_history table. Date (UTC) is date read as Unix seconds. OS, BR, Bird Schema, DB '
            'Schema and Device ID are os, br, bird_schema, db_schema and device_id as stored. No Apple '
            'documentation of the table is cited: on the tested images os held text in the form of a macOS '
            'build number, and what a row records, a start of the iCloud Drive daemon or of the Mac, is not '
            'established. On the tested images each row of a table held a different os value, so the table is '
            'not shown to add a row per start. What device_id identifies is not established. The device_id '
            'column is absent from the table on the two macOS 11.2.1 images, so Device ID held no value on any '
            'row there. Bird Schema and DB Schema are identical on every row of every tested image, the same '
            'number in both. Bird Schema and DB Schema each held one value on every row of the Big Sur E01 '
            'image and two values across the 3 rows of the Magnet image. server.db holds a server_boot_history '
            'table of the same shape, which is not read. client_downloads and client_uploads are reported by '
            'the iCloud Drive Downloads and iCloud Drive Uploads artifacts. client_sync_up and '
            'client_unapplied_table are not reported: their columns are not sourced, and client_sync_up held at'
            ' most one row per zone on the tested images. The telemetry_events, item_recursive_properties, '
            'completed_db_fixups, backup_detector, client_state and server_state tables and the other tables of'
            ' the two databases are not read. User is the folder after Users in the path, root for a file under'
            ' private/var/root, and blank otherwise. User held one value on every row of each tested image. A '
            'copy of the database under System/Volumes/Data/ or System/Volumes/Update/mnt1/ whose database and '
            '-wal file are both byte-identical to one already read is not read again and the run log counts it.'
            ' A row identical in every other column in copies that differ is reported as often as the copy '
            'holding it most often holds it, normally once, with each file in Source File, one per line. On the'
            ' two logical images every row was folded this way.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 3 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 row",
            "adams_macbookpro_macos26": "macOS 26.2 | 1 row",
        },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/client.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "power",
    },
    "macosICloudDriveDocumentAccess": {
        "name": "iCloud Drive Document Access",
        "description": "Rows of the client_document_access table of each user's CloudDocs client.db on macOS, with the item each row names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": (
            "Reads each user's client.db under ~/Library/Application Support/CloudDocs/session/db, one row per "
            'row of its client_document_access table. Modify Access Time (UTC) and Access Time (UTC) are '
            'modify_access_time and access_time read as Unix seconds, with a stored 0 reported blank; what sets'
            " either value is not sourced here, so the names are the table's and not a finding about who opened"
            ' or changed a document. File Name and Path come from the client_items row whose rowid equals '
            'item_rowid, the way the iCloud Drive Items artifact builds them, and are blank when no such row '
            'exists, which did not happen on the tested images. Properties is properties as stored and Item Row'
            ' ID is item_rowid. Of the tested images only the two macOS 11.2.1 ones hold the table: client.db '
            'on the macOS 15.4 and 26.2 images has no such table, and the run log says so. Access Time held no '
            'value on any row of the Magnet macOS 11.2.1 image, and Properties held one value on every row of '
            'that image (0). User is the folder after Users in the path, root for a file under '
            'private/var/root, and blank otherwise. User held one value on every row of each tested image. A '
            'copy of the database under System/Volumes/Data/ or System/Volumes/Update/mnt1/ whose database and '
            '-wal file are both byte-identical to one already read is not read again and the run log counts it.'
            ' A row identical in every other column in copies that differ is reported as often as the copy '
            'holding it most often holds it, normally once, with each file in Source File, one per line. On the'
            ' Magnet image every row was folded this way.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 4 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 23 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (client.db has no client_document_access table)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (client.db has no client_document_access table)",
        },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/client.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
    },
    "macosICloudDriveDownloads": {
        "name": "iCloud Drive Downloads",
        "description": "Rows of the client_downloads table of each user's CloudDocs client.db on macOS, with the client_items row whose rowid equals each row's throttle_id.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": (
            "Reads each user's client.db under ~/Library/Application Support/CloudDocs/session/db, one row per "
            "row of its client_downloads table. The item is the client_items row whose rowid equals the row's "
            'throttle_id: no source is cited for that link, and on the tested images every row (3 download rows'
            ' and 12 upload rows) matched a client_items row in the same zone whose version_size equals the '
            "row's transfer_size, a size one item only held in its image. File Name and Path come from that "
            'row, the way the iCloud Drive Items artifact builds them, and are blank when there is none; no '
            'tested row lacked a match, so the blank case was not exercised. Throttle ID is throttle_id as '
            'stored. Last Try, Next Retry and Expires are last_try_stamp, next_retry_stamp and expire_stamp, '
            "and Request Time is the table's request stamp. A stamp above 10**14 is read as Unix nanoseconds "
            'and a smaller one as Unix seconds. A stored 0 is reported blank, and so is a stamp that is not a '
            'number or that does not convert to a date under this reading, such as a value in milliseconds; no '
            'tested row held one. Last Try is the first column because it is the only stamp every tested row '
            'holds. Transfer Size, Throttle State and Retry Count are transfer_size, throttle_state and '
            'retry_count as stored. Transfer Queue and Transfer Stage are transfer_queue and transfer_stage: '
            'both held text or no value on the tested rows and are shown as stored, and a value stored as data '
            'would be shown as a byte count, which no tested row exercised. Transfer Record and Error show a '
            'byte count when the column holds data and are not decoded. Zone is the zone_name of the '
            'client_zones row whose rowid equals zone_rowid, and the stored number when there is no such row, '
            "which no tested image exercised. What a row's presence or its transfer_queue value says about "
            'whether a transfer is pending, started, finished or failed is not sourced here. Request Time is '
            'download_request_stamp, Priority is download_priority, Kind is download_kind, Error is '
            'download_error and Unit Count Completed is unit_count_completed. The app_library_rowid, '
            "transfer_operation and download_etag columns are not reported. The table's unique key is "
            'throttle_id with download_kind and download_etag, so the schema allows more than one row for one '
            'item; each tested throttle_id had one row. The Big Sur E01 image held 1 row and the macOS 26.2 '
            'image 2; the table held no rows on the other two images with a client.db. The stamp reading is '
            'taken from the values and not from a source. The request stamp was a 10-digit value read as '
            'seconds on the macOS 11.2.1 row and a 19-digit value read as nanoseconds on the macOS 26.2 rows, '
            'while the other stamps were 19-digit values on every row. Read that way Request Time falls within '
            'six minutes before Last Try on the macOS 11.2.1 row and within a millisecond before it on the '
            'macOS 26.2 rows, and Expires is 1,024 seconds after Last Try on all 3 rows. Next Retry and Error '
            'held no value on any row, so the Error output was not exercised. Transfer Stage and Transfer '
            'Record (byte count) held no value on the one row of the Big Sur E01 image, and Transfer Record '
            '(byte count) held a count on the 2 macOS 26.2 rows. Throttle State, Retry Count, Priority, Unit '
            'Count Completed and Zone each held one value on all 3 rows. Kind held one value on the macOS '
            '11.2.1 row and another on both macOS 26.2 rows; what the Kind numbers stand for is not sourced. '
            'User is the folder after Users in the path, root for a file under private/var/root, and blank '
            'otherwise. User held one value on every row of each tested image. A copy of the database under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ whose database and -wal file are both '
            'byte-identical to one already read is not read again and the run log counts it. A row identical in'
            ' every other column in copies that differ is reported as often as the copy holding it most often '
            'holds it, normally once, with each file in Source File, one per line. The two images with rows '
            'each hold one copy of client.db, so no row was folded and folding was not exercised for this '
            'artifact.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (client_downloads holds no rows)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (client_downloads holds no rows)",
            "adams_macbookpro_macos26": "macOS 26.2 | 2 rows",
        },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/client.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "download-cloud",
    },
    "macosICloudDriveUploads": {
        "name": "iCloud Drive Uploads",
        "description": "Rows of the client_uploads table of each user's CloudDocs client.db on macOS, with the client_items row whose rowid equals each row's throttle_id.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "iCloud Drive (macOS)",
        "notes": (
            "Reads each user's client.db under ~/Library/Application Support/CloudDocs/session/db, one row per "
            "row of its client_uploads table. The item is the client_items row whose rowid equals the row's "
            'throttle_id: no source is cited for that link, and on the tested images every row (3 download rows'
            ' and 12 upload rows) matched a client_items row in the same zone whose version_size equals the '
            "row's transfer_size, a size one item only held in its image. File Name and Path come from that "
            'row, the way the iCloud Drive Items artifact builds them, and are blank when there is none; no '
            'tested row lacked a match, so the blank case was not exercised. Throttle ID is throttle_id as '
            'stored. Last Try, Next Retry and Expires are last_try_stamp, next_retry_stamp and expire_stamp, '
            "and Request Time is the table's request stamp. A stamp above 10**14 is read as Unix nanoseconds "
            'and a smaller one as Unix seconds. A stored 0 is reported blank, and so is a stamp that is not a '
            'number or that does not convert to a date under this reading, such as a value in milliseconds; no '
            'tested row held one. Last Try is the first column because it is the only stamp every tested row '
            'holds. Transfer Size, Throttle State and Retry Count are transfer_size, throttle_state and '
            'retry_count as stored. Transfer Queue and Transfer Stage are transfer_queue and transfer_stage: '
            'both held text or no value on the tested rows and are shown as stored, and a value stored as data '
            'would be shown as a byte count, which no tested row exercised. Transfer Record and Error show a '
            'byte count when the column holds data and are not decoded. Zone is the zone_name of the '
            'client_zones row whose rowid equals zone_rowid, and the stored number when there is no such row, '
            "which no tested image exercised. What a row's presence or its transfer_queue value says about "
            'whether a transfer is pending, started, finished or failed is not sourced here. Request Time is '
            'upload_request_stamp, Priority is upload_priority and Error is upload_error. client_uploads has no'
            ' kind and no unit-count column on any tested image, so this artifact has no Kind or Unit Count '
            'Completed column, and on the macOS 26.2 image it has no upload_request_stamp column either, so '
            'Request Time would be blank there; that table held no rows. The app_library_rowid and '
            'transfer_operation columns are not reported. Only the Big Sur E01 image held rows, 12 of them. The'
            ' stamp reading is taken from the values and not from a source. No upload row held a request stamp '
            'to compare; under this reading Expires is 3,600 seconds after Last Try on all 12 rows, and the '
            'iCloud Drive Downloads artifact gives the request and last-try comparison for the download rows. '
            'On the 12 rows Request Time, Next Retry, Transfer Stage, Transfer Record (byte count) and Error '
            'held no value on any row, so the Error and Transfer Record outputs were not exercised, and '
            'Transfer Queue, Throttle State, Retry Count, Priority and Zone each held one value on every row. '
            'User is the folder after Users in the path, root for a file under private/var/root, and blank '
            'otherwise. User held one value on every row of each tested image. A copy of the database under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ whose database and -wal file are both '
            'byte-identical to one already read is not read again and the run log counts it. A row identical in'
            ' every other column in copies that differ is reported as often as the copy holding it most often '
            'holds it, normally once, with each file in Source File, one per line. The two images with rows '
            'each hold one copy of client.db, so no row was folded and folding was not exercised for this '
            'artifact.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (client_uploads holds no rows)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 12 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (client_uploads holds no rows)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (client_uploads holds no rows)",
        },
        "paths": ('*/Library/Application Support/CloudDocs/session/db/client.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "upload-cloud",
    },
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_LABEL = 'iCloud Drive Items'
_ITEM_COLUMNS = ('item_id', 'item_parent_id', 'item_filename', 'item_type', 'version_size',
                 'version_mtime', 'item_birthtime', 'item_lastusedtime', 'zone_rowid',
                 'app_library_rowid', 'item_trash_put_back_path', 'item_user_visible',
                 'version_device')


def _text(value):
    return '' if value is None else str(value)


def _unix_utc(seconds):
    """Unix seconds as an aware UTC datetime; '' for 0 or anything not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds == 0:
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _select(path, table, names):
    if not does_table_exist_in_db(path, table):
        return []
    columns = ', '.join(name if name == 'rowid' or does_column_exist_in_db(path, table, name)
                        else f'NULL AS {name}' for name in names)
    return get_sqlite_db_records(path, f'SELECT {columns} FROM {table} ORDER BY rowid') or []


def _path(item_id, items):
    """The item's name with the names of the parent entries it stores, outermost first."""
    names = []
    seen = set()
    current = item_id
    while current in items and current not in seen:
        seen.add(current)
        parent, name = items[current]
        names.append(_text(name))
        current = parent
    return '/'.join(reversed(names))


def _devices(path):
    """{key: name} of the devices table in the server.db beside a client.db; {} when there is none."""
    server = os.path.join(os.path.dirname(path), 'server.db')
    if not os.path.isfile(server) or not does_table_exist_in_db(server, 'devices'):
        return {}
    return {row[0]: row[1] for row in get_sqlite_db_records(server, 'SELECT key, name FROM devices')}


def _rows(path):
    devices = _devices(path)
    zones = {row[0]: row[1] for row in _select(path, 'client_zones', ('rowid', 'zone_name'))}
    libraries = {row[0]: row[1] for row in _select(
        path, 'app_libraries', ('rowid', 'app_library_name'))}
    records = _select(path, 'client_items', _ITEM_COLUMNS)
    items = {row[0]: (row[1], row[2]) for row in records if row[0] is not None}
    for (item_id, _parent, name, item_type, size, mtime, birth, last_used, zone, library,
         put_back, visible, device) in records:
        yield (_unix_utc(birth), _unix_utc(mtime), _unix_utc(last_used), _text(name),
               _path(item_id, items), _text(item_type), _text(size), _text(zones.get(zone, zone)),
               _text(libraries.get(library, library)), _text(devices.get(device, device)),
               _text(put_back), _text(visible))


@artifact_processor
def macosICloudDriveItems(context):
    data_headers = (('Item Birth Time (UTC)', 'datetime'), ('Version Modified (UTC)', 'datetime'),
                    ('Last Used (UTC)', 'datetime'), 'File Name', 'Path', 'Item Type (as stored)',
                    'Size (bytes, as stored)', 'Zone', 'App Library', 'Version Device',
                    'Trash Put-Back Path (as stored)', 'User Visible (as stored)', 'User',
                    'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'client.db']
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'client_items'):
            logfunc(f'{_LABEL}: no client_items table read from {relative}')
            continue
        read.append(path)
        found = [row + (user_from_path(relative), relative) for row in _rows(path)]
        if not found:
            logfunc(f'{_LABEL}: no items in {relative}')
        data_list.extend(found)
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


def _databases(context, name, table, label):
    """Each distinct database of that name that holds the table."""
    found = [p for p in context.get_files_found() if os.path.basename(str(p)) == name]
    paths, _skipped = unique_sources(context, found, sidecars=('-wal',), label=label)
    usable = []
    for path in paths:
        relative = context.get_relative_path(path)
        if does_table_exist_in_db(path, table):
            usable.append(path)
        else:
            logfunc(f'{label}: no {table} table read from {relative}')
    return usable


def _zoned_path(key, items):
    """The item's name with the names of the parent entries its zone stores, outermost first."""
    names = []
    seen = set()
    current = key
    while current in items and current not in seen:
        seen.add(current)
        parent, name = items[current]
        names.append(_text(name))
        current = (key[0], parent)
    return '/'.join(reversed(names))


_SERVER_COLUMNS = ('zone_rowid', 'item_id', 'item_parent_id', 'item_filename', 'item_type', 'item_state',
                   'version_name', 'version_size', 'version_mtime', 'item_birthtime', 'item_lastusedtime',
                   'version_device', 'quota_used', 'child_count', 'recursive_child_count')


@artifact_processor
def macosICloudDriveServerItems(context):
    data_headers = (('Item Birth Time (UTC)', 'datetime'), ('Version Modified (UTC)', 'datetime'),
                    ('Last Used (UTC)', 'datetime'), 'File Name', 'Path', 'Version Name',
                    'Item Type (as stored)', 'Item State (as stored)', 'Size (bytes, as stored)', 'Zone',
                    'Version Device', 'Quota Used (as stored)', 'Child Count (as stored)',
                    'Recursive Child Count (as stored)', 'User', 'Source File')
    label = 'iCloud Drive Server Items'
    data_list, read = [], []
    for path in _databases(context, 'server.db', 'server_items', label):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        devices = {}
        if does_table_exist_in_db(path, 'devices'):
            devices = {row[0]: row[1] for row in get_sqlite_db_records(path, 'SELECT key, name FROM devices')}
        zones = {row[0]: row[1] for row in _select(path, 'server_zones', ('rowid', 'zone_name'))}
        records = _select(path, 'server_items', _SERVER_COLUMNS)
        items = {(row[0], bytes(row[1])): (bytes(row[2]) if row[2] is not None else None, row[3])
                 for row in records if row[1] is not None}
        for (zone, item_id, _parent, name, item_type, state, version_name, size, mtime, birth, last_used,
             device, quota, children, all_children) in records:
            item_path = _zoned_path((zone, bytes(item_id)), items) if item_id is not None else _text(name)
            data_list.append((_unix_utc(birth), _unix_utc(mtime), _unix_utc(last_used), _text(name), item_path,
                              _text(version_name), _text(item_type), _text(state), _text(size),
                              _text(zones.get(zone, zone)), _text(devices.get(device, device)), _text(quota),
                              _text(children), _text(all_children), user, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosICloudDriveDevices(context):
    data_headers = ('Device Name', 'Key', 'User', 'Source File')
    label = 'iCloud Drive Devices'
    data_list, read = [], []
    for path in _databases(context, 'server.db', 'devices', label):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for key, name in _select(path, 'devices', ('key', 'name')):
            data_list.append((_text(name), _text(key), user, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosICloudDriveBootHistory(context):
    data_headers = (('Date (UTC)', 'datetime'), 'OS (as stored)', 'BR (as stored)', 'Bird Schema', 'DB Schema',
                    'Device ID (as stored)', 'User', 'Source File')
    label = 'iCloud Drive Boot History'
    data_list, read = [], []
    for path in _databases(context, 'client.db', 'boot_history', label):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for date, os_name, build, bird, schema, device in _select(
                path, 'boot_history', ('date', 'os', 'br', 'bird_schema', 'db_schema', 'device_id')):
            data_list.append((_unix_utc(date), _text(os_name), _text(build), _text(bird), _text(schema),
                              _text(device), user, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosICloudDriveDocumentAccess(context):
    data_headers = (('Modify Access Time (UTC)', 'datetime'), ('Access Time (UTC)', 'datetime'), 'File Name',
                    'Path', 'Properties (as stored)', 'Item Row ID', 'User', 'Source File')
    label = 'iCloud Drive Document Access'
    data_list, read = [], []
    for path in _databases(context, 'client.db', 'client_document_access', label):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        records = _select(path, 'client_items', ('rowid', 'item_id', 'item_parent_id', 'item_filename'))
        items = {row[1]: (row[2], row[3]) for row in records if row[1] is not None}
        by_rowid = {row[0]: (row[1], row[3]) for row in records}
        for rowid, access, modify_access, properties in _select(
                path, 'client_document_access', ('item_rowid', 'access_time', 'modify_access_time', 'properties')):
            item_id, name = by_rowid.get(rowid, (None, None))
            data_list.append((_unix_utc(modify_access), _unix_utc(access), _text(name),
                              _path(item_id, items) if item_id is not None else '', _text(properties),
                              _text(rowid), user, relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


def _stamp_utc(value):
    """A stored stamp as an aware UTC datetime: Unix nanoseconds above 10**14, else Unix seconds; '' for 0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value == 0:
        return ''
    return _unix_utc(value / 1_000_000_000 if abs(value) > 10 ** 14 else value)


def _blob_text(value):
    """Text as stored, a byte count for data that is not text, '' for null."""
    if value is None:
        return ''
    if isinstance(value, (bytes, bytearray)):
        return f'({len(value)} bytes)'
    return str(value)


_QUEUE_HEADERS = (('Last Try (UTC)', 'datetime'), ('Request Time (UTC)', 'datetime'), ('Next Retry (UTC)', 'datetime'),
                  ('Expires (UTC)', 'datetime'), 'File Name', 'Path', 'Transfer Size (as stored)',
                  'Transfer Queue', 'Transfer Stage', 'Transfer Record (byte count)', 'Throttle State (as stored)',
                  'Retry Count', 'Priority (as stored)', 'Kind (as stored)', 'Error', 'Unit Count Completed',
                  'Zone', 'Throttle ID', 'User', 'Source File')

# Positions of Kind and Unit Count Completed, columns only client_downloads has.
_DOWNLOAD_ONLY = (13, 15)

def _queue_rows(path, table, kind, priority, request, error):
    """Rows of one transfer queue table; the item is the client_items row whose rowid is throttle_id."""
    zones = {row[0]: row[1] for row in _select(path, 'client_zones', ('rowid', 'zone_name'))}
    records = _select(path, 'client_items', ('rowid', 'item_id', 'item_parent_id', 'item_filename'))
    items = {row[1]: (row[2], row[3]) for row in records if row[1] is not None}
    by_rowid = {row[0]: (row[1], row[3]) for row in records}
    columns = ('throttle_id', 'zone_rowid', 'throttle_state', 'retry_count', 'last_try_stamp',
               'next_retry_stamp', 'expire_stamp', 'transfer_queue', 'transfer_size', 'transfer_record',
               'transfer_stage', kind, priority, request, error, 'unit_count_completed')
    for (throttle, zone, state, retries, last_try, next_retry, expire, queue, size, record, stage, kind_value,
         priority_value, requested, error_value, completed) in _select(path, table, columns):
        item_id, name = by_rowid.get(throttle, (None, None))
        yield (_stamp_utc(last_try), _stamp_utc(requested), _stamp_utc(next_retry), _stamp_utc(expire),
               _text(name), _path(item_id, items) if item_id is not None else '', _text(size),
               _blob_text(queue), _blob_text(stage), _blob_text(record), _text(state), _text(retries),
               _text(priority_value), _text(kind_value), _blob_text(error_value), _text(completed),
               _text(zones.get(zone, zone)), _text(throttle))


@artifact_processor
def macosICloudDriveDownloads(context):
    label = 'iCloud Drive Downloads'
    data_list, read = [], []
    for path in _databases(context, 'client.db', 'client_downloads', label):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for row in _queue_rows(path, 'client_downloads', 'download_kind', 'download_priority',
                               'download_request_stamp', 'download_error'):
            data_list.append(row + (user, relative))
    return _QUEUE_HEADERS, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosICloudDriveUploads(context):
    label = 'iCloud Drive Uploads'
    data_list, read = [], []
    for path in _databases(context, 'client.db', 'client_uploads', label):
        read.append(path)
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        for row in _queue_rows(path, 'client_uploads', 'upload_kind', 'upload_priority',
                               'upload_request_stamp', 'upload_error'):
            data_list.append(tuple(value for index, value in enumerate(row) if index not in _DOWNLOAD_ONLY)
                             + (user, relative))
    headers = tuple(header for index, header in enumerate(_QUEUE_HEADERS) if index not in _DOWNLOAD_ONLY)
    return headers, fold_view_rows(data_list), '\n'.join(read)
