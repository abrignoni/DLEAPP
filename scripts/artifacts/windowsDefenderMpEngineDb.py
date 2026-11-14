"""Microsoft Defender's mpenginedb.db (MetaVault) in ProgramData\\Microsoft\\Windows Defender\\Scans, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsDefenderMpEngineProcesses": {
        "name": "Defender MpEngineDb Monitored Processes",
        "description": (
            'Processes listed in the BmProcessInfo table of mpenginedb.db: process start time, '
            'PID, image path and command line.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": (
            'Table BmProcessInfo. Process Start (UTC) is ProcessStartTime read as a FILETIME '
            '(100 ns since 1601-01-01 UTC): 2018-03-27 09:15:58 to 2018-04-06 12:51:09 on '
            'lonewolf_win10 and 2020-09-19 01:24:04 to 03:39:47 on szechuan_win10. It was not '
            "matched to an independent record of a process start here; Protokol-7's SQLECmd map "
            'reads it the same way. It is 0, and shown blank, on 11 rows of pc_mus_001_win11. '
            'PID is as stored and recurs (1,261 distinct values on 1,687 rows of '
            'lonewolf_win10). Image File Name is as stored: an NT device path starting \\Device\\ '
            'on 1,683 of 1,687 rows of lonewolf_win10, 266 of 268 of szechuan_win10 and 329 of '
            '332 of pc_mus_001_win11. Command Line is CommandLineArgs as stored and is empty on '
            '242, 39 and 102 rows of those three. PPIDHash is a signed 64-bit integer as '
            'stored; what it is a hash of is not established here, and it differs on every row '
            "of lonewolf_win10 and szechuan_win10. Record ID is the table's ID. Not reported: "
            'StructVersion, the MonitoringFlags_ columns, Flags and the HipsInjectionId, '
            'FolderGuardId and LsassReadMemId blobs, because no source here says what they '
            'hold. A row says a process was listed in this table; whether every process that '
            'ran has a row is not established here, and Protokol-7 say the file covers roughly '
            'the last two weeks. On pc_mus_001_win11 the table read as 332 rows with 318 '
            "distinct Record IDs, not in ascending order, and then stopped with 'database disk "
            "image is malformed' while SELECT count(*) says 327; a Record ID that occurs twice "
            'is reported twice, the 14 repeats are identical rows, the index lists 9 Record IDs '
            'the table read did not reach, and the cause is not established (see the WAL counts '
            'below). Rows: lonewolf_win10 1,687; szechuan_win10 268; pc_mus_001_win11 332. '
            'af_case2_win10, alihadi_threatsim_server2019, hexordia_mvs2025_win11 and '
            'ou_ransomware_server2022 hold the table with no rows. The file is the SQLite '
            'database that Protokol-7 (Mato Vlajcic, Luka Bracun and Dino Bezic, 2026-11-10, '
            'https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html) '
            'say Defender calls MetaVault, kept in ProgramData/Microsoft/Windows '
            'Defender/Scans. Their write-up says its pages and WAL frame bodies are encrypted '
            'with RC4 under one fixed 256-byte key restarted for every page, that bytes 16 to '
            '23 of page 1 and the WAL frame headers are in the clear, and that the WAL '
            'checksums run over the encrypted bytes. This module reads it that way with the key '
            'built into their parser (https://github.com/Protokol-7/mpenginedb_parser, MIT); '
            'the decryption and WAL replay follow their write-up and parser, and no file of '
            'theirs is vendored. It decrypts only when page 1 comes out as a SQLite header and '
            'reads as a table b-tree page and at least half of the next 16 pages start as '
            'b-tree pages, and otherwise logs why and reports nothing. The key decrypted the '
            'file on all seven corpus images found to hold it: Windows 10 1709, 1809 and 2004, '
            'Windows 11 22H2 and 24H2, and Windows Server 2019 and 2022. Where the Engine table '
            'has rows (five of the seven) its EngineVersion values, read as four 16-bit fields, '
            'run from 1.1.14104.0 to 1.1.19200.6; that reading is an inference from the values, '
            'not a sourced format. The write-up tested engine build 1.1.26100.4. The key also '
            'decrypted the file of a Windows 11 25H2 ARM64 lab VM running that build (known '
            'data, corpus keys windows11_arm_defender_mpenginedb_known_20261113 and the same '
            'name ending _baseline; README beside them), where all 480 WAL frames are readable '
            "and SQLite's integrity_check on the decrypted copy reads ok. No other build or "
            'architecture was tested, and the seven images are not known to be ARM. The WAL is '
            'replayed as SQLite reads one: frames in order up to the last commit frame, a frame '
            "counting only when its salts equal the WAL header's and the checksum chain, "
            'computed over the stored bytes, holds up to it, and the later copy of a page '
            'winning. The evidence is never written to: the decrypted copy is a temporary file '
            'opened read-only and removed with the files SQLite makes beside it. The run log '
            'gives, per database, the frames in the WAL, how many were readable and applied, '
            'and the frame and page counts the -shm records. Three of the seven images have a '
            'WAL. On lonewolf_win10 384 of 1,053 frames are readable and the -shm records 321; '
            'on szechuan_win10 896 of 1,001 are readable and the -shm records 896; on '
            'pc_mus_001_win11 4 of 679 are readable and the -shm records 612 frames and 213 '
            'pages, and 603 of the 679 frames are all zero bytes, the first of them frame 6. '
            "Rows are read from each table's own b-tree, never from an index; a table that "
            'stops reading part-way keeps the rows read and logs the error. Tables of the file '
            'that none of the six Defender MpEngineDb artifacts report: Engine and '
            'SQLiteGlobals (engine and schema version history), ScanInfo, File and '
            'RecordIdentifier (tables on the three Windows 10 images only, which the write-up '
            'does not describe), ProcessInfo (31 rows on two images), FileLowFiAsync (17 rows '
            'on four), RollingQueuesTables, ValueMapArray, SystemRegistryCache, AmsiFileCache '
            'and sqlite_stat1; every other table was empty or absent on all seven images.'
        ),
        "paths": ('*/Windows Defender/Scans/mpenginedb.db*',),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            'lonewolf_win10': 'Windows 10 Education (build 16299, version 1709) | 1687 rows',
            'szechuan_win10': 'Windows 10 2004 (build 19041) | 268 rows',
            'pc_mus_001_win11': 'Windows 11 22H2 (build 22621) | 332 rows',
            'szechuan_dc01_server2012r2': 'Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows',
            'cfreds_leakage_win7': 'Windows 7 Ultimate SP1 (build 7601) | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113': 'Windows 11 25H2 (build 26200), ARM64 | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113_baseline': 'Windows 11 25H2 (build 26200), ARM64 | 0 rows',
        },
    },
    "windowsDefenderMpEngineFileTracking": {
        "name": "Defender MpEngineDb File Tracking",
        "description": (
            'Rows of the BackupProcessInfo table of mpenginedb.db: the InstanceTimeStamp of '
            'each, the file path and the USN stored beside it.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": (
            'Table BackupProcessInfo, which Protokol-7 describe as files and processes tracked '
            'for ransomware rollback. Instance Time (UTC) is InstanceTimeStamp read as a '
            'FILETIME: 2022-12-30 19:24:25 to 2023-01-06 16:57:56 on pc_mus_001_win11 and '
            '2020-09-18 05:52:00 to 2020-09-19 03:37:34 on szechuan_win10. File Path is as '
            "stored, a Windows path. Next USN is as stored. Checked against this repository's "
            'USN Journal artifact on pc_mus_001_win11 and af_case2_win10, no row has a Next USN '
            "above the journal's last USN (0 of 1,938 and 0 of 577 rows), 841 of the 847 and "
            "379 of the 383 rows inside the journal's range have a Next USN equal to the USN of "
            'a record in it, and 1,091 and 194 rows lie below its first record; so on those '
            "rows it equals a USN of that volume's journal, and this does not show it to be the "
            'next USN of anything. First Start Time (as stored) is FirstStartTime, a signed '
            '64-bit integer; read as a FILETIME it lands in 1980 to 2107 on 132 of 1,938 rows '
            '(pc_mus_001_win11), 212 of 577 (af_case2_win10), 29 of 221 (szechuan_win10), 11 of '
            '38 (alihadi_threatsim_server2019) and 3 of 75 (hexordia_mvs2025_win11), so it is '
            "not read as a time here; Protokol-7's parser labels it a process start time when "
            'it falls in that range and an identifier otherwise, and this module cannot tell '
            'them apart. Known data (the VM above): two copies of Microsoft programs run by the '
            'test, whose process starts were logged as 02:40:41.6954098 and 02:40:41.7619054 '
            'UTC, each have one row whose First Start Time (as stored) equals that process '
            'start as a FILETIME to 100 ns, whose Instance Time (UTC) is 12.9 ms and 11.2 ms '
            'later, and whose Next USN (0x1370c1c80 and 0x1370c21a0) lies between the NTFS '
            "journal's next USN read before and after the actions (0x1370c12c8 and "
            '0x1370c3c90). A text file and a zip the test created, and a file it created and '
            'deleted two seconds later, have no row. Whether every in-range First Start Time is '
            "a process start was not tested. Record ID is the table's ID. Not reported: Key (an "
            'integer, not decoded), AutomaticRemovalPolicy (0 on every row of the five images) '
            'and ImpactedCBPNameSpaces (empty on every row). A row holds a file path and no '
            'process ID. Rows: af_case2_win10 577; alihadi_threatsim_server2019 38; '
            'hexordia_mvs2025_win11 75; szechuan_win10 221; pc_mus_001_win11 1,938, where '
            'SELECT count(*) says 1,913 (the table holds 25 more rows than that count; the '
            'cause is not established, see the WAL counts below). lonewolf_win10 and '
            'ou_ransomware_server2022 hold no rows. The file is the SQLite database that '
            'Protokol-7 (Mato Vlajcic, Luka Bracun and Dino Bezic, 2026-11-10, '
            'https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html) '
            'say Defender calls MetaVault, kept in ProgramData/Microsoft/Windows '
            'Defender/Scans. Their write-up says its pages and WAL frame bodies are encrypted '
            'with RC4 under one fixed 256-byte key restarted for every page, that bytes 16 to '
            '23 of page 1 and the WAL frame headers are in the clear, and that the WAL '
            'checksums run over the encrypted bytes. This module reads it that way with the key '
            'built into their parser (https://github.com/Protokol-7/mpenginedb_parser, MIT); '
            'the decryption and WAL replay follow their write-up and parser, and no file of '
            'theirs is vendored. It decrypts only when page 1 comes out as a SQLite header and '
            'reads as a table b-tree page and at least half of the next 16 pages start as '
            'b-tree pages, and otherwise logs why and reports nothing. The key decrypted the '
            'file on all seven corpus images found to hold it: Windows 10 1709, 1809 and 2004, '
            'Windows 11 22H2 and 24H2, and Windows Server 2019 and 2022. Where the Engine table '
            'has rows (five of the seven) its EngineVersion values, read as four 16-bit fields, '
            'run from 1.1.14104.0 to 1.1.19200.6; that reading is an inference from the values, '
            'not a sourced format. The write-up tested engine build 1.1.26100.4. The key also '
            'decrypted the file of a Windows 11 25H2 ARM64 lab VM running that build (known '
            'data, corpus keys windows11_arm_defender_mpenginedb_known_20261113 and the same '
            'name ending _baseline; README beside them), where all 480 WAL frames are readable '
            "and SQLite's integrity_check on the decrypted copy reads ok. No other build or "
            'architecture was tested, and the seven images are not known to be ARM. The WAL is '
            'replayed as SQLite reads one: frames in order up to the last commit frame, a frame '
            "counting only when its salts equal the WAL header's and the checksum chain, "
            'computed over the stored bytes, holds up to it, and the later copy of a page '
            'winning. The evidence is never written to: the decrypted copy is a temporary file '
            'opened read-only and removed with the files SQLite makes beside it. The run log '
            'gives, per database, the frames in the WAL, how many were readable and applied, '
            'and the frame and page counts the -shm records. Three of the seven images have a '
            'WAL. On lonewolf_win10 384 of 1,053 frames are readable and the -shm records 321; '
            'on szechuan_win10 896 of 1,001 are readable and the -shm records 896; on '
            'pc_mus_001_win11 4 of 679 are readable and the -shm records 612 frames and 213 '
            'pages, and 603 of the 679 frames are all zero bytes, the first of them frame 6. '
            "Rows are read from each table's own b-tree, never from an index; a table that "
            'stops reading part-way keeps the rows read and logs the error. Tables of the file '
            'that none of the six Defender MpEngineDb artifacts report: Engine and '
            'SQLiteGlobals (engine and schema version history), ScanInfo, File and '
            'RecordIdentifier (tables on the three Windows 10 images only, which the write-up '
            'does not describe), ProcessInfo (31 rows on two images), FileLowFiAsync (17 rows '
            'on four), RollingQueuesTables, ValueMapArray, SystemRegistryCache, AmsiFileCache '
            'and sqlite_stat1; every other table was empty or absent on all seven images.'
        ),
        "paths": ('*/Windows Defender/Scans/mpenginedb.db*',),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            'af_case2_win10': 'Windows 10 1809 (build 17763) | 577 rows',
            'alihadi_threatsim_server2019': 'Windows Server 2019 Standard (build 17763.3046) | 38 rows',
            'hexordia_mvs2025_win11': 'Windows 11 24H2 (build 26100.2033) | 75 rows',
            'szechuan_win10': 'Windows 10 2004 (build 19041) | 221 rows',
            'pc_mus_001_win11': 'Windows 11 22H2 (build 22621) | 1938 rows',
            'szechuan_dc01_server2012r2': 'Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113': 'Windows 11 25H2 (build 26200), ARM64 | 4951 rows',
            'windows11_arm_defender_mpenginedb_known_20261113_baseline': 'Windows 11 25H2 (build 26200), ARM64 | 4948 rows',
        },
    },
    "windowsDefenderMpEnginePathTags": {
        "name": "Defender MpEngineDb Path Tags",
        "description": (
            'Rows of the AttributePersistContext table of mpenginedb.db: the path, the context '
            'text stored with it, and the insert and expire times.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": (
            'Table AttributePersistContext. Insert Time (UTC) and Expire Time (UTC) are '
            'InsertTime and ExpireTime read as FILETIMEs: on pc_mus_001_win11 inserts run '
            '2023-01-05 15:52:25 to 2023-01-06 16:57:55 and expiries 2023-01-06 23:20:42 to '
            '2024-01-07 06:08:56. Expire Time (UTC) is earlier than Insert Time (UTC) on 1 row, '
            'on af_case2_win10 (by 30 seconds), and on no other row of the five images. File '
            'Path is FilePath as stored: text starting ENG: on 703 of 999 rows of '
            'pc_mus_001_win11 and 996 of 998 of ou_ransomware_server2022, a Windows path on '
            'most of the other rows, and other text on 5 rows of the five images. Context is as '
            'stored: 48 distinct values on pc_mus_001_win11, among them processed (653 rows), '
            'NewPECreatedNoCert (262), ExecutedPENoCert (14) and DroppedByBITS (9). Protokol-7 '
            'say these are tags Defender keeps for a path, name NewlyCreatedZip, '
            'BM_IsPotentialSideLoad, NewPECreatedNoCert, ExecutedPENoCert and '
            'MpTamperProtectionState among them, and warn that a Tamper Protection value is a '
            'last known state, not proof of what someone did. Known data (the VM above): a zip '
            'the test created at 02:40:41.63 UTC got a NewlyCreatedZip row (insert '
            '02:40:41.625006, expire 100 s later), and two copies of Microsoft programs it ran '
            'got ExecutedPENoCert rows (inserts 7.7 ms and 6.8 ms before the logged process '
            'starts, expire 24 h later) although Get-AuthenticodeSignature reads both as Valid, '
            'SignatureType Catalog, IsOSBinary True, so that tag is not shown to mean unsigned; '
            'a text file and a file created and deleted two seconds later got no row. The '
            "meaning of the other tags was not tested. Record ID is the table's ID. Not "
            'reported: Key. Rows: af_case2_win10 1; alihadi_threatsim_server2019 7; '
            'hexordia_mvs2025_win11 2; ou_ransomware_server2022 998; pc_mus_001_win11 999. '
            'lonewolf_win10 and szechuan_win10 hold the table with no rows. The file is the '
            'SQLite database that Protokol-7 (Mato Vlajcic, Luka Bracun and Dino Bezic, '
            '2026-11-10, '
            'https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html) '
            'say Defender calls MetaVault, kept in ProgramData/Microsoft/Windows '
            'Defender/Scans. Their write-up says its pages and WAL frame bodies are encrypted '
            'with RC4 under one fixed 256-byte key restarted for every page, that bytes 16 to '
            '23 of page 1 and the WAL frame headers are in the clear, and that the WAL '
            'checksums run over the encrypted bytes. This module reads it that way with the key '
            'built into their parser (https://github.com/Protokol-7/mpenginedb_parser, MIT); '
            'the decryption and WAL replay follow their write-up and parser, and no file of '
            'theirs is vendored. It decrypts only when page 1 comes out as a SQLite header and '
            'reads as a table b-tree page and at least half of the next 16 pages start as '
            'b-tree pages, and otherwise logs why and reports nothing. The key decrypted the '
            'file on all seven corpus images found to hold it: Windows 10 1709, 1809 and 2004, '
            'Windows 11 22H2 and 24H2, and Windows Server 2019 and 2022. Where the Engine table '
            'has rows (five of the seven) its EngineVersion values, read as four 16-bit fields, '
            'run from 1.1.14104.0 to 1.1.19200.6; that reading is an inference from the values, '
            'not a sourced format. The write-up tested engine build 1.1.26100.4. The key also '
            'decrypted the file of a Windows 11 25H2 ARM64 lab VM running that build (known '
            'data, corpus keys windows11_arm_defender_mpenginedb_known_20261113 and the same '
            'name ending _baseline; README beside them), where all 480 WAL frames are readable '
            "and SQLite's integrity_check on the decrypted copy reads ok. No other build or "
            'architecture was tested, and the seven images are not known to be ARM. The WAL is '
            'replayed as SQLite reads one: frames in order up to the last commit frame, a frame '
            "counting only when its salts equal the WAL header's and the checksum chain, "
            'computed over the stored bytes, holds up to it, and the later copy of a page '
            'winning. The evidence is never written to: the decrypted copy is a temporary file '
            'opened read-only and removed with the files SQLite makes beside it. The run log '
            'gives, per database, the frames in the WAL, how many were readable and applied, '
            'and the frame and page counts the -shm records. Three of the seven images have a '
            'WAL. On lonewolf_win10 384 of 1,053 frames are readable and the -shm records 321; '
            'on szechuan_win10 896 of 1,001 are readable and the -shm records 896; on '
            'pc_mus_001_win11 4 of 679 are readable and the -shm records 612 frames and 213 '
            'pages, and 603 of the 679 frames are all zero bytes, the first of them frame 6. '
            "Rows are read from each table's own b-tree, never from an index; a table that "
            'stops reading part-way keeps the rows read and logs the error. Tables of the file '
            'that none of the six Defender MpEngineDb artifacts report: Engine and '
            'SQLiteGlobals (engine and schema version history), ScanInfo, File and '
            'RecordIdentifier (tables on the three Windows 10 images only, which the write-up '
            'does not describe), ProcessInfo (31 rows on two images), FileLowFiAsync (17 rows '
            'on four), RollingQueuesTables, ValueMapArray, SystemRegistryCache, AmsiFileCache '
            'and sqlite_stat1; every other table was empty or absent on all seven images.'
        ),
        "paths": ('*/Windows Defender/Scans/mpenginedb.db*',),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            'af_case2_win10': 'Windows 10 1809 (build 17763) | 1 rows',
            'alihadi_threatsim_server2019': 'Windows Server 2019 Standard (build 17763.3046) | 7 rows',
            'hexordia_mvs2025_win11': 'Windows 11 24H2 (build 26100.2033) | 2 rows',
            'ou_ransomware_server2022': 'Windows Server 2022 Standard (build 20348.1850) | 998 rows',
            'pc_mus_001_win11': 'Windows 11 22H2 (build 22621) | 999 rows',
            'szechuan_win10': 'Windows 10 2004 (build 19041) | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113': 'Windows 11 25H2 (build 26200), ARM64 | 998 rows',
            'windows11_arm_defender_mpenginedb_known_20261113_baseline': 'Windows 11 25H2 (build 26200), ARM64 | 996 rows',
        },
    },
    "windowsDefenderMpEngineFileHashes": {
        "name": "Defender MpEngineDb File Hashes",
        "description": (
            "Rows of the FileHashes table of mpenginedb.db: a file's SHA-256, MD5 and SHA-1 "
            'with its NTFS file reference and USN.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": (
            'Table FileHashes. Instance Time (UTC) is InstanceTimeStamp read as a FILETIME: '
            '2023-01-03 22:43:32 to 2023-01-05 01:54:27 on pc_mus_001_win11 and 2020-09-18 '
            "05:53:30 on szechuan_win10. VSN is as stored (one value per image); Protokol-7's "
            'parser reads its low 32 bits as a volume serial, which was not compared with the '
            'volume here. File ID is as stored. On pc_mus_001_win11, for the 11 rows whose USN '
            "is a record of that image's USN Journal artifact, the record's file record number "
            'and sequence number equal the low 48 and top 16 bits of File ID on all 11, so File '
            "ID is an NTFS file reference there; 4 other rows lie below the journal's first "
            'record and none above its last. USN is as stored, and those 11 equal the USN of a '
            'record of that journal. SHA-256 is SHA256 as stored, 32 bytes on every row that '
            'has one. The columns the table names SHA1 and MD5 hold 16 and 20 bytes on all 22 '
            'rows that have a value, the sizes of an MD5 and a SHA-1 digest. Measured on '
            'pc_mus_001_win11 by hashing files of the image: for all 11 rows whose USN is a '
            "journal record, a file in the image has the row's SHA-256, with the column named "
            'SHA1 equal to its MD5 and the column named MD5 equal to its SHA-1; for 9 of the '
            'rows that file is at the path the journal gives, and for the other 2 the journal '
            'gives no parent path and it is one of the files of that name in the image. The '
            'headers say which digest each column was found to hold, and Protokol-7 describe '
            'the two columns as swapped. The matches are on one image, pc_mus_001_win11. Record '
            "ID is the table's ID. Not reported: Key, LSHASH, LSHASHS, CTPH (128 bytes on 14 of "
            'the 23 rows) and the CRC columns. Rows: alihadi_threatsim_server2019 7; '
            'pc_mus_001_win11 15 (1 without hashes); szechuan_win10 1. The file is the SQLite '
            'database that Protokol-7 (Mato Vlajcic, Luka Bracun and Dino Bezic, 2026-11-10, '
            'https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html) '
            'say Defender calls MetaVault, kept in ProgramData/Microsoft/Windows '
            'Defender/Scans. Their write-up says its pages and WAL frame bodies are encrypted '
            'with RC4 under one fixed 256-byte key restarted for every page, that bytes 16 to '
            '23 of page 1 and the WAL frame headers are in the clear, and that the WAL '
            'checksums run over the encrypted bytes. This module reads it that way with the key '
            'built into their parser (https://github.com/Protokol-7/mpenginedb_parser, MIT); '
            'the decryption and WAL replay follow their write-up and parser, and no file of '
            'theirs is vendored. It decrypts only when page 1 comes out as a SQLite header and '
            'reads as a table b-tree page and at least half of the next 16 pages start as '
            'b-tree pages, and otherwise logs why and reports nothing. The key decrypted the '
            'file on all seven corpus images found to hold it: Windows 10 1709, 1809 and 2004, '
            'Windows 11 22H2 and 24H2, and Windows Server 2019 and 2022. Where the Engine table '
            'has rows (five of the seven) its EngineVersion values, read as four 16-bit fields, '
            'run from 1.1.14104.0 to 1.1.19200.6; that reading is an inference from the values, '
            'not a sourced format. The write-up tested engine build 1.1.26100.4. The key also '
            'decrypted the file of a Windows 11 25H2 ARM64 lab VM running that build (known '
            'data, corpus keys windows11_arm_defender_mpenginedb_known_20261113 and the same '
            'name ending _baseline; README beside them), where all 480 WAL frames are readable '
            "and SQLite's integrity_check on the decrypted copy reads ok. No other build or "
            'architecture was tested, and the seven images are not known to be ARM. The WAL is '
            'replayed as SQLite reads one: frames in order up to the last commit frame, a frame '
            "counting only when its salts equal the WAL header's and the checksum chain, "
            'computed over the stored bytes, holds up to it, and the later copy of a page '
            'winning. The evidence is never written to: the decrypted copy is a temporary file '
            'opened read-only and removed with the files SQLite makes beside it. The run log '
            'gives, per database, the frames in the WAL, how many were readable and applied, '
            'and the frame and page counts the -shm records. Three of the seven images have a '
            'WAL. On lonewolf_win10 384 of 1,053 frames are readable and the -shm records 321; '
            'on szechuan_win10 896 of 1,001 are readable and the -shm records 896; on '
            'pc_mus_001_win11 4 of 679 are readable and the -shm records 612 frames and 213 '
            'pages, and 603 of the 679 frames are all zero bytes, the first of them frame 6. '
            "Rows are read from each table's own b-tree, never from an index; a table that "
            'stops reading part-way keeps the rows read and logs the error. Tables of the file '
            'that none of the six Defender MpEngineDb artifacts report: Engine and '
            'SQLiteGlobals (engine and schema version history), ScanInfo, File and '
            'RecordIdentifier (tables on the three Windows 10 images only, which the write-up '
            'does not describe), ProcessInfo (31 rows on two images), FileLowFiAsync (17 rows '
            'on four), RollingQueuesTables, ValueMapArray, SystemRegistryCache, AmsiFileCache '
            'and sqlite_stat1; every other table was empty or absent on all seven images.'
        ),
        "paths": ('*/Windows Defender/Scans/mpenginedb.db*',),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            'alihadi_threatsim_server2019': 'Windows Server 2019 Standard (build 17763.3046) | 7 rows',
            'szechuan_win10': 'Windows 10 2004 (build 19041) | 1 rows',
            'pc_mus_001_win11': 'Windows 11 22H2 (build 22621) | 15 rows',
            'hexordia_mvs2025_win11': 'Windows 11 24H2 (build 26100.2033) | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113': 'Windows 11 25H2 (build 26200), ARM64 | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113_baseline': 'Windows 11 25H2 (build 26200), ARM64 | 0 rows',
        },
    },
    "windowsDefenderMpEngineFileInstances": {
        "name": "Defender MpEngineDb File Instances",
        "description": (
            'Rows of the FileInstance table of mpenginedb.db (on the three Windows 10 images): '
            "instance time, the file's created, last accessed and last written times, file "
            'name, USN, parent file and process, the MOTW columns and signer.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": (
            'Table FileInstance, which exists on the three Windows 10 images only and is not '
            'described in the Protokol-7 write-up; column meanings below are measured or taken '
            'from the column names and are marked so. Instance Time (UTC) is InstanceTimeStamp '
            'read as a FILETIME: 2018-03-27 09:22:47 to 2018-04-06 12:27:06 on lonewolf_win10 '
            'and 2020-09-18 05:52:04 to 2020-09-19 03:37:39 on szechuan_win10. Created, Last '
            'Accessed and Last Written (UTC) are CreateTime, LastAccessTime and LastWriteTime '
            'read as FILETIMEs and shown blank when 0, which they are on 16 of 336 rows of '
            'lonewolf_win10, 1 of 119 of szechuan_win10 and the 1 row of af_case2_win10. '
            'Measured on lonewolf_win10 against the NTFS times the raw image reader reports for '
            'the same path, on the 136 rows (115 distinct paths) whose path it found: Created '
            '(UTC) equals the NTFS created time on all 136 (to 1 ms), and Last Written (UTC) '
            'equals the NTFS modified time on 115, the NTFS time being later on the other 21 '
            'and earlier on none. Last Accessed was not compared here. USN is as stored; on '
            "lonewolf_win10 and szechuan_win10, checked against this repository's USN Journal "
            "artifact, the 12 and 19 values inside the journal's range each equal the USN of a "
            'record that names the same file, and the other 308 and 94 lie below its first '
            'record (none above). Parent File Name and Parent Process ID are as stored. Storage '
            'Event, MOTW and MOTW From Parent are integers as stored: Storage Event is 2, 3 or '
            '9 on lonewolf_win10 and 2, 3, 8 or 9 on szechuan_win10; MOTW is 3 on 300 of 336 '
            'rows of lonewolf_win10 and blank on the rest and on all 119 of szechuan_win10, '
            'where MOTW From Parent is blank on all 119 rows too; what the values mean was not '
            'tested here. The one row of af_case2_win10 has no value in USN, Parent File Name, '
            'Parent Process ID, MOTW, MOTW From Parent, Signer or Issuer. Signer and Issuer are '
            'as stored (301 of 336 rows of lonewolf_win10 have a signer) and Is Valid Cert is 1 '
            "or 0 as stored. Record ID is the table's ID. How this table relates to the File, "
            'ScanInfo and RecordIdentifier tables is not established here. Not reported: the '
            'other columns. Rows: af_case2_win10 1; lonewolf_win10 336; szechuan_win10 119. The '
            'file is the SQLite database that Protokol-7 (Mato Vlajcic, Luka Bracun and Dino '
            'Bezic, 2026-11-10, '
            'https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html) '
            'say Defender calls MetaVault, kept in ProgramData/Microsoft/Windows '
            'Defender/Scans. Their write-up says its pages and WAL frame bodies are encrypted '
            'with RC4 under one fixed 256-byte key restarted for every page, that bytes 16 to '
            '23 of page 1 and the WAL frame headers are in the clear, and that the WAL '
            'checksums run over the encrypted bytes. This module reads it that way with the key '
            'built into their parser (https://github.com/Protokol-7/mpenginedb_parser, MIT); '
            'the decryption and WAL replay follow their write-up and parser, and no file of '
            'theirs is vendored. It decrypts only when page 1 comes out as a SQLite header and '
            'reads as a table b-tree page and at least half of the next 16 pages start as '
            'b-tree pages, and otherwise logs why and reports nothing. The key decrypted the '
            'file on all seven corpus images found to hold it: Windows 10 1709, 1809 and 2004, '
            'Windows 11 22H2 and 24H2, and Windows Server 2019 and 2022. Where the Engine table '
            'has rows (five of the seven) its EngineVersion values, read as four 16-bit fields, '
            'run from 1.1.14104.0 to 1.1.19200.6; that reading is an inference from the values, '
            'not a sourced format. The write-up tested engine build 1.1.26100.4. The key also '
            'decrypted the file of a Windows 11 25H2 ARM64 lab VM running that build (known '
            'data, corpus keys windows11_arm_defender_mpenginedb_known_20261113 and the same '
            'name ending _baseline; README beside them), where all 480 WAL frames are readable '
            "and SQLite's integrity_check on the decrypted copy reads ok. No other build or "
            'architecture was tested, and the seven images are not known to be ARM. The WAL is '
            'replayed as SQLite reads one: frames in order up to the last commit frame, a frame '
            "counting only when its salts equal the WAL header's and the checksum chain, "
            'computed over the stored bytes, holds up to it, and the later copy of a page '
            'winning. The evidence is never written to: the decrypted copy is a temporary file '
            'opened read-only and removed with the files SQLite makes beside it. The run log '
            'gives, per database, the frames in the WAL, how many were readable and applied, '
            'and the frame and page counts the -shm records. Three of the seven images have a '
            'WAL. On lonewolf_win10 384 of 1,053 frames are readable and the -shm records 321; '
            'on szechuan_win10 896 of 1,001 are readable and the -shm records 896; on '
            'pc_mus_001_win11 4 of 679 are readable and the -shm records 612 frames and 213 '
            'pages, and 603 of the 679 frames are all zero bytes, the first of them frame 6. '
            "Rows are read from each table's own b-tree, never from an index; a table that "
            'stops reading part-way keeps the rows read and logs the error. Tables of the file '
            'that none of the six Defender MpEngineDb artifacts report: Engine and '
            'SQLiteGlobals (engine and schema version history), ScanInfo, File and '
            'RecordIdentifier (tables on the three Windows 10 images only, which the write-up '
            'does not describe), ProcessInfo (31 rows on two images), FileLowFiAsync (17 rows '
            'on four), RollingQueuesTables, ValueMapArray, SystemRegistryCache, AmsiFileCache '
            'and sqlite_stat1; every other table was empty or absent on all seven images.'
        ),
        "paths": ('*/Windows Defender/Scans/mpenginedb.db*',),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            'af_case2_win10': 'Windows 10 1809 (build 17763) | 1 rows',
            'lonewolf_win10': 'Windows 10 Education (build 16299, version 1709) | 336 rows',
            'szechuan_win10': 'Windows 10 2004 (build 19041) | 119 rows',
            'pc_mus_001_win11': 'Windows 11 22H2 (build 22621) | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113': 'Windows 11 25H2 (build 26200), ARM64 | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113_baseline': 'Windows 11 25H2 (build 26200), ARM64 | 0 rows',
        },
    },
    "windowsDefenderMpEngineRollingQueues": {
        "name": "Defender MpEngineDb Rolling Queues",
        "description": (
            'Rows of the RollingQueuesValues table of mpenginedb.db: queue name, key and value '
            'as stored, with insert and expire times.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Windows Defender",
        "notes": (
            'Table RollingQueuesValues. Insert Time (UTC) and Expire Time (UTC) are InsertTime '
            'and ExpireTime read as FILETIMEs: on hexordia_mvs2025_win11 inserts fall on '
            '2024-11-23 05:04:58 to 05:05:50 and expiries an hour later, and on '
            'ou_ransomware_server2022 the 4 rows were inserted 2023-11-05 02:12:15 and expire '
            '2028-11-03 02:12:15; those 4 rows share one Entry Table and one Entry Value, and '
            'their Entry Key is 1, 2, 3 and 4, equal to Record ID on every row. Entry Table, '
            'Entry Key and Entry Value are as stored text (Entry Value is non-null on every '
            'row). Entry Table begins Tech-pid or Tact-pid on 10 of 37 rows of '
            'alihadi_threatsim_server2019, 68 of 105 of hexordia_mvs2025_win11 and both rows of '
            'pc_mus_001_win11, followed by a PID and a ProcessStart number; Protokol-7 describe '
            'these as per-process attack scoring queues whose keys name ATT&CK techniques or, '
            'for Tact queues, tactic or rule names. That, and the PID and ProcessStart inside '
            "the name, are not decoded or tested here, and Protokol-7's parser calls the rest "
            "global or named queues. Record ID is the table's ID. Rows: "
            'alihadi_threatsim_server2019 37; hexordia_mvs2025_win11 105; '
            'ou_ransomware_server2022 4; pc_mus_001_win11 2. The other three images do not hold '
            'the table. The file is the SQLite database that Protokol-7 (Mato Vlajcic, Luka '
            'Bracun and Dino Bezic, 2026-11-10, '
            'https://protokol-7.github.io/dfir/2026/11/10/defenders-hidden-flight-recorder-mpenginedb.html) '
            'say Defender calls MetaVault, kept in ProgramData/Microsoft/Windows '
            'Defender/Scans. Their write-up says its pages and WAL frame bodies are encrypted '
            'with RC4 under one fixed 256-byte key restarted for every page, that bytes 16 to '
            '23 of page 1 and the WAL frame headers are in the clear, and that the WAL '
            'checksums run over the encrypted bytes. This module reads it that way with the key '
            'built into their parser (https://github.com/Protokol-7/mpenginedb_parser, MIT); '
            'the decryption and WAL replay follow their write-up and parser, and no file of '
            'theirs is vendored. It decrypts only when page 1 comes out as a SQLite header and '
            'reads as a table b-tree page and at least half of the next 16 pages start as '
            'b-tree pages, and otherwise logs why and reports nothing. The key decrypted the '
            'file on all seven corpus images found to hold it: Windows 10 1709, 1809 and 2004, '
            'Windows 11 22H2 and 24H2, and Windows Server 2019 and 2022. Where the Engine table '
            'has rows (five of the seven) its EngineVersion values, read as four 16-bit fields, '
            'run from 1.1.14104.0 to 1.1.19200.6; that reading is an inference from the values, '
            'not a sourced format. The write-up tested engine build 1.1.26100.4. The key also '
            'decrypted the file of a Windows 11 25H2 ARM64 lab VM running that build (known '
            'data, corpus keys windows11_arm_defender_mpenginedb_known_20261113 and the same '
            'name ending _baseline; README beside them), where all 480 WAL frames are readable '
            "and SQLite's integrity_check on the decrypted copy reads ok. No other build or "
            'architecture was tested, and the seven images are not known to be ARM. The WAL is '
            'replayed as SQLite reads one: frames in order up to the last commit frame, a frame '
            "counting only when its salts equal the WAL header's and the checksum chain, "
            'computed over the stored bytes, holds up to it, and the later copy of a page '
            'winning. The evidence is never written to: the decrypted copy is a temporary file '
            'opened read-only and removed with the files SQLite makes beside it. The run log '
            'gives, per database, the frames in the WAL, how many were readable and applied, '
            'and the frame and page counts the -shm records. Three of the seven images have a '
            'WAL. On lonewolf_win10 384 of 1,053 frames are readable and the -shm records 321; '
            'on szechuan_win10 896 of 1,001 are readable and the -shm records 896; on '
            'pc_mus_001_win11 4 of 679 are readable and the -shm records 612 frames and 213 '
            'pages, and 603 of the 679 frames are all zero bytes, the first of them frame 6. '
            "Rows are read from each table's own b-tree, never from an index; a table that "
            'stops reading part-way keeps the rows read and logs the error. Tables of the file '
            'that none of the six Defender MpEngineDb artifacts report: Engine and '
            'SQLiteGlobals (engine and schema version history), ScanInfo, File and '
            'RecordIdentifier (tables on the three Windows 10 images only, which the write-up '
            'does not describe), ProcessInfo (31 rows on two images), FileLowFiAsync (17 rows '
            'on four), RollingQueuesTables, ValueMapArray, SystemRegistryCache, AmsiFileCache '
            'and sqlite_stat1; every other table was empty or absent on all seven images.'
        ),
        "paths": ('*/Windows Defender/Scans/mpenginedb.db*',),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            'alihadi_threatsim_server2019': 'Windows Server 2019 Standard (build 17763.3046) | 37 rows',
            'hexordia_mvs2025_win11': 'Windows 11 24H2 (build 26100.2033) | 105 rows',
            'ou_ransomware_server2022': 'Windows Server 2022 Standard (build 20348.1850) | 4 rows',
            'pc_mus_001_win11': 'Windows 11 22H2 (build 22621) | 2 rows',
            'szechuan_win10': 'Windows 10 2004 (build 19041) | 0 rows',
            'windows11_arm_defender_mpenginedb_known_20261113': 'Windows 11 25H2 (build 26200), ARM64 | 1 rows',
            'windows11_arm_defender_mpenginedb_known_20261113_baseline': 'Windows 11 25H2 (build 26200), ARM64 | 1 rows',
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.mpenginedb import Database, filetime, read_database, shm_summary

_LABEL = 'Defender MpEngineDb'

# Each spec is a table and a list of (header, column, kind). kind 'time' converts a FILETIME,
# 'hex' writes a BLOB as lower-case hex, anything else is written as stored.
_PROCESSES = ('BmProcessInfo', [
    (('Process Start (UTC)', 'datetime'), 'ProcessStartTime', 'time'),
    ('PID', 'PID', 'raw'),
    ('Image File Name', 'ImageFileName', 'raw'),
    ('Command Line', 'CommandLineArgs', 'raw'),
    ('PPIDHash', 'PPIDHash', 'raw'),
    ('Record ID', 'ID', 'raw'),
])
_FILE_TRACKING = ('BackupProcessInfo', [
    (('Instance Time (UTC)', 'datetime'), 'InstanceTimeStamp', 'time'),
    ('File Path', 'FilePath', 'raw'),
    ('Next USN', 'NextUSN', 'raw'),
    ('First Start Time (as stored)', 'FirstStartTime', 'raw'),
    ('Record ID', 'ID', 'raw'),
])
_PATH_TAGS = ('AttributePersistContext', [
    (('Insert Time (UTC)', 'datetime'), 'InsertTime', 'time'),
    (('Expire Time (UTC)', 'datetime'), 'ExpireTime', 'time'),
    ('File Path', 'FilePath', 'raw'),
    ('Context', 'Context', 'raw'),
    ('Record ID', 'ID', 'raw'),
])
_FILE_HASHES = ('FileHashes', [
    (('Instance Time (UTC)', 'datetime'), 'InstanceTimeStamp', 'time'),
    ('VSN', 'VSN', 'raw'),
    ('File ID', 'FileID', 'raw'),
    ('USN', 'USN', 'raw'),
    ('SHA-256', 'SHA256', 'hex'),
    ('MD5 (stored in column SHA1)', 'SHA1', 'hex'),
    ('SHA-1 (stored in column MD5)', 'MD5', 'hex'),
    ('Record ID', 'ID', 'raw'),
])
_FILE_INSTANCES = ('FileInstance', [
    (('Instance Time (UTC)', 'datetime'), 'InstanceTimeStamp', 'time'),
    (('Created (UTC)', 'datetime'), 'CreateTime', 'time'),
    (('Last Accessed (UTC)', 'datetime'), 'LastAccessTime', 'time'),
    (('Last Written (UTC)', 'datetime'), 'LastWriteTime', 'time'),
    ('File Name', 'FileName', 'raw'),
    ('USN', 'USN', 'raw'),
    ('Parent File Name', 'Parent_FileName', 'raw'),
    ('Parent Process ID', 'Parent_ProcessID', 'raw'),
    ('Storage Event', 'StorageEvent', 'raw'),
    ('MOTW', 'MOTW', 'raw'),
    ('MOTW From Parent', 'MOTWFromParent', 'raw'),
    ('Signer', 'Signer', 'raw'),
    ('Issuer', 'Issuer', 'raw'),
    ('Is Valid Cert', 'IsValidCert', 'raw'),
    ('Record ID', 'ID', 'raw'),
])
_ROLLING_QUEUES = ('RollingQueuesValues', [
    (('Insert Time (UTC)', 'datetime'), 'InsertTime', 'time'),
    (('Expire Time (UTC)', 'datetime'), 'ExpireTime', 'time'),
    ('Entry Table', 'EntryTable', 'raw'),
    ('Entry Key', 'EntryKey', 'raw'),
    ('Entry Value', 'EntryValue', 'raw'),
    ('Record ID', 'ID', 'raw'),
])


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _value(kind, value, bad):
    if kind == 'time':
        converted = filetime(value)
        if converted == '' and isinstance(value, int) and value != 0:
            bad[0] += 1
        return converted
    if value is None:
        return ''
    if kind == 'hex':
        return value.hex() if isinstance(value, (bytes, bytearray)) else str(value)
    return value


def _collect(context, spec):
    """(headers, rows, source) for one table of every mpenginedb.db found."""
    table, columns = spec
    headers = tuple(header for header, _column, _kind in columns)
    found = sorted(str(path) for path in context.get_files_found() if os.path.isfile(str(path)))
    databases = [path for path in found if os.path.basename(path).lower() == 'mpenginedb.db']
    data_list, sources = [], []
    for path in databases:
        relative = context.get_relative_path(path)
        wal, shm = path + '-wal', path + '-shm'
        wal_bytes = _read(wal) if os.path.isfile(wal) else None
        shm_bytes = _read(shm) if os.path.isfile(shm) else None
        sources.append(path)
        if wal_bytes is not None:
            sources.append(wal)
        if shm_bytes is not None:
            sources.append(shm)
        result = read_database(_read(path), wal_bytes)
        if result.plain is None:
            logfunc(f'{_LABEL}: {relative} was not read: {result.reason}')
            continue
        note = (f'{_LABEL}: {relative}: {result.page_size}-byte pages, {result.pages_in_file} in the '
                f'file, {result.pages_after_wal} after the WAL')
        if result.wal_present:
            note += (f'; WAL of {result.wal_frames} frames, {result.wal_valid_frames} readable in an '
                     f'unbroken checksum chain, {result.wal_applied_frames} applied')
        index = shm_summary(shm_bytes)
        if index:
            note += f'; the -shm records {index[0]} frames and a database of {index[1]} pages'
        logfunc(note)
        for extra in result.wal_notes:
            logfunc(f'{_LABEL}: {relative}: {extra}')
        with Database(result.plain) as database:
            rows, error, missing = database.rows(table, [column for _h, column, _k in columns])
            counted = database.count(table)
        if error == 'table not present':
            logfunc(f'{_LABEL}: {relative}: no {table} table')
            continue
        if missing:
            logfunc(f'{_LABEL}: {relative}: {table} has no column {", ".join(missing)}')
        if error:
            logfunc(f'{_LABEL}: {relative}: reading {table} stopped after {len(rows)} row(s): {error}')
        ids = [row['ID'] for row in rows if row.get('ID') is not None]
        if len(ids) != len(set(ids)):
            logfunc(f'{_LABEL}: {relative}: {table} read {len(rows)} row(s) with {len(set(ids))} distinct '
                    'Record IDs; a Record ID that occurs twice is reported twice')
        if counted is not None and counted != len(rows):
            logfunc(f'{_LABEL}: {relative}: {table}: {len(rows)} row(s) read from the table, '
                    f'SELECT count(*) says {counted}')
        bad = [0]
        for row in rows:
            data_list.append(tuple(_value(kind, row[column], bad) for _h, column, kind in columns))
        if bad[0]:
            logfunc(f'{_LABEL}: {relative}: {bad[0]} non-zero time value(s) in {table} are outside '
                    '1980 to 2107 and are left blank')
    return headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsDefenderMpEngineProcesses(context):
    return _collect(context, _PROCESSES)


@artifact_processor
def windowsDefenderMpEngineFileTracking(context):
    return _collect(context, _FILE_TRACKING)


@artifact_processor
def windowsDefenderMpEnginePathTags(context):
    return _collect(context, _PATH_TAGS)


@artifact_processor
def windowsDefenderMpEngineFileHashes(context):
    return _collect(context, _FILE_HASHES)


@artifact_processor
def windowsDefenderMpEngineFileInstances(context):
    return _collect(context, _FILE_INSTANCES)


@artifact_processor
def windowsDefenderMpEngineRollingQueues(context):
    return _collect(context, _ROLLING_QUEUES)
