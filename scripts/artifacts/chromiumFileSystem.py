"""Sites, saved entries and bucket storage of the File System APIs in Chromium-based browser
profiles, for DLEAPP.

Ported from ALEAPP's chromiumFileSystem.py, with browser, profile and user taken from
scripts/chromium/browser_profiles and the folders grouped by scripts/chromium/web_storage.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "chromiumFileSystemSites": {
        "name": "Chromium File System API - Sites",
        "description": "Sites listed in the Origins database of a Chromium-based browser profile's File System "
                       "folder, the store Chromium keeps for its File System APIs (webkitRequestFileSystem and the "
                       "Origin Private File System).",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the File System/Origins database of each Chromium-based browser profile that scripts/chromium/browser_profiles locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and webOS webbrowser) on Windows, macOS and Linux. Format and meanings come from Chromium at commit 3a50e012e4c9b8a410a4e2b12bf577e69ee8f755 (tag 130.0.6723.58). The cited source is one release; the tested profiles were written by others (Folder Last Changed falls in 2018 and 2025 on the corpus images, and the known data is Chrome 157), and their records decoded with this layout. Each LevelDB folder is read with the vendored ccl_leveldb, and only the newest version of each key is used: LevelDB orders the versions of a key by sequence number (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Browser, Profile and User come from the path, as in the other Chromium artifacts. On a Mac logical extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a folder whose copy under the second path holds the same files with the same bytes is read once, as it was on mvs2026_macbookpro_macos15, and two copies that differ are each read on their own. A folder that cannot be read is skipped and named in the run log. Ported from ALEAPP's Chromium File System API - Sites; the Android known data in its notes was not repeated here. It is the store Chromium keeps for webkitRequestFileSystem and for the Origin Private File System, which Chromium opens as the temporary sandboxed type (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/content/browser/file_system_access/file_system_access_manager_impl.cc#L401-L406). Each row is one ORIGIN key of that database, which keys each site as ORIGIN:<identifier> and stores the name of the numbered folder that holds its files (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_origin_database.cc#L32-L33, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_origin_database.cc#L253-L258); its LAST_PATH key is not reported. Site Key (as stored) is the identifier; Site is the origin it encodes, scheme_host_port with port 0 for the scheme's default port (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/common/database/database_identifier.cc#L101-L104, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/common/database/database_identifier.cc#L203-L204), split at the first and last underscore as Chromium does (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/common/database/database_identifier.cc#L126-L137). State is Deleted when the newest version of the key is a deletion. Chromium deletes the key when it deletes the site's last type folder (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_origin_database.cc#L276-L277, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L1016-L1021), and when a repair of the database finds the site's folder missing (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_origin_database.cc#L164-L171); a deleted key still names the site, and Folder and Saved Entries are blank on it and Folder Present is No. LevelDB compaction can drop a deletion (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/doc/impl.md#L104), so the absence of a Deleted row is not evidence that no site was removed. Folder is the stored folder name, Folder Present says whether the extraction gave at least one file under that folder, and Saved Entries counts the folders and files its Paths databases list, the root folder not counted (see Chromium File System API - Files); a Paths folder that could not be read is not counted. Only a site's first-party default storage is kept in this folder (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L926-L942); other storage is under WebStorage/<bucket>/FileSystem and is reported in Chromium File System API - Bucket Storage. Source File names the Origins folder each row came from. A row records that Chromium was asked for that site's file system folder with creation allowed, which opening the file system does (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L1369-L1375, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_file_system_backend_delegate.cc#L97-L104); it need not have saved a file, and the database stores no time, so a row does not say when that happened or who was using the browser. Known data (windows11_arm_chrome_fs_notifications_known_20261114, Chrome 157.0.8103.51 on Windows 11 ARM64, a fresh profile and one local test page at http://localhost:8765, minted 2026-11-14 07:52:26 to 07:53:12 UTC; README beside the image): the page wrote three files and a folder through the Origin Private File System and one file through webkitRequestFileSystem. Its one row named the test site with Folder 000, Folder Present Yes and Saved Entries 5, the four files and the folder written. On the corpus images: 22 rows on 5 of 7 images (hexordia_mvs2025_win11 3, lonewolf_win10 15, mvs2026_macbookpro_macos15 1, ou_ransomware_server2022 1, pc_mus_001_win11 2), from Google Chrome and Microsoft Edge. State held Live and Folder Present held Yes on all 22 rows; no tested image held a Deleted row. Saved Entries was above 0 on 3 of the 22 rows (2 on lonewolf_win10, 1 on mvs2026_macbookpro_macos15) and held 0 on all 3 rows of hexordia_mvs2025_win11; on lonewolf_win10 and mvs2026_macbookpro_macos15 its sum equalled the number of non-root rows in Chromium File System API - Files (544 and 376), which comes from the same reading. Browser, Profile and User held one value on all 15 rows of lonewolf_win10 and all 3 rows of hexordia_mvs2025_win11. ubuntu2604_arm64_chromium and windows11_arm_operagx_360se_known_20261107 held no file under a File System folder. Not exercised by the tested images: a Deleted row, Folder Present No, any Linux profile, browsers other than Google Chrome and Microsoft Edge, and a profile at the user data folder root.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/File System/*',
            '*/Library/Application Support/Google/Chrome/*/File System/*',
            '*/.config/google-chrome/*/File System/*',
            '*/AppData/Local/Chromium/User Data/*/File System/*',
            '*/Library/Application Support/Chromium/*/File System/*',
            '*/.config/chromium/*/File System/*',
            '*/snap/chromium/common/chromium/*/File System/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/File System/*',
            '*/webbrowser/chrome/*/File System/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/File System/*',
            '*/Library/Application Support/Microsoft Edge/*/File System/*',
            '*/.config/microsoft-edge/*/File System/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/File System/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/File System/*',
            '*/.config/BraveSoftware/Brave-Browser/*/File System/*',
            '*/AppData/Local/Vivaldi/User Data/*/File System/*',
            '*/Library/Application Support/Vivaldi/*/File System/*',
            '*/.config/vivaldi/*/File System/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/File System/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/File System/*',
            '*/AppData/Roaming/360se6/User Data/*/File System/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/File System/*',
            '*/.config/opera/*/File System/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/File System/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/File System/*',
            '*/AppData/Roaming/360se6/User Data/File System/*',
            '*/Library/Application Support/com.operasoftware.Opera/File System/*',
            '*/.config/opera/File System/*',
        ),
        "output_types": "standard",
        "artifact_icon": "folder",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 3 rows",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 15 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no file under a File System folder)",
            "windows11_arm_chrome_fs_notifications_known_20261114": "Windows 11 build 26200 ARM64 | 1 rows (known data)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows (no file under a File System folder)",
        },
    },
    "chromiumFileSystemEntries": {
        "name": "Chromium File System API - Files",
        "description": "Folders and files websites saved through a Chromium-based browser's File System APIs, "
                       "rebuilt from the Paths database of each site folder, with the saved file shown as media.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Paths databases in the File System folder and in the bucket WebStorage folders of each Chromium-based browser profile that scripts/chromium/browser_profiles locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and webOS webbrowser) on Windows, macOS and Linux. Format and meanings come from Chromium at commit 3a50e012e4c9b8a410a4e2b12bf577e69ee8f755 (tag 130.0.6723.58). The cited source is one release; the tested profiles were written by others (Folder Last Changed falls in 2018 and 2025 on the corpus images, and the known data is Chrome 157), and their records decoded with this layout. Each LevelDB folder is read with the vendored ccl_leveldb, and only the newest version of each key is used: LevelDB orders the versions of a key by sequence number (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Browser, Profile and User come from the path, as in the other Chromium artifacts. On a Mac logical extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a folder whose copy under the second path holds the same files with the same bytes is read once, as it was on mvs2026_macbookpro_macos15, and two copies that differ are each read on their own. A folder that cannot be read is skipped and named in the run log. Ported from ALEAPP's Chromium File System API - Files; the Android known data in its notes was not repeated here. Each row is one entry of a Paths database: in each type folder of a site folder (File System/<folder>/t, p or s) and of each bucket FileSystem folder (WebStorage/<bucket id>/FileSystem/t, p or s), the temporary, persistent and syncable types (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_file_system_backend_delegate.cc#L52-L54). Each entry is stored under its numeric id (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L112-L114) as a record of parent id, data path, name and time (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L46-L49), and its name under CHILD_OF:<parent id>:<name> (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L70-L73, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L90-L96). An entry whose record does not decode is skipped and named in the run log. Path is rebuilt from the parent ids, / being the root folder, and a parent id with no record shows as <unresolved> (none on the tested images); an entry with an empty data path is a folder (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.h#L50). File is the saved file at Data Path in the type folder (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L1284-L1290), shown as media with its type sniffed from its content, and Size its size in bytes; both are blank when the extraction did not give that file. Data Path (as stored) is the platform's own path string (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L43-L47, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/common/file_system/file_system_util.cc#L294-L301): it held \\ on all 538 file rows of lonewolf_win10 and the 4 of the known data, and / on all 374 of mvs2026_macbookpro_macos15. Both separators are read. A row with State Deleted comes from a CHILD_OF key whose newest version is a deletion: it gives the name and parent folder of a name that was removed from that folder, because the entry was deleted, renamed or moved, and nothing else (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L892-L909, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L552-L556, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L566-L590, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L620-L635); Entry Type, File, Size and Data Path are blank on it. Folder Last Changed is the stored time of a folder entry, rounded down to the second (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L38-L49), microseconds since 1601-01-01 UTC (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/base/time/time.h#L511). Chromium sets it to the current time when the folder is made (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L450; the root folder at https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.cc#L825-L829) and when an entry inside it is created, copied, moved or removed (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L103-L106). A touch of the folder stores the time its caller passes (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L539-L541), so the value is not always the time of a change. Chromium reports the stored time only for folders and takes a file's time from its data file (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L1144-L1156, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_directory_database.h#L55-L57), so the column is blank on file rows; it leads the table as the only stored time, although only folder rows fill it. Site is the live Origins key whose folder this is, blank when none names it; for a bucket FileSystem folder Site is the origin of the bucket's storage key and Top-Level Site the top-level site the key names (see Chromium File System API - Bucket Storage). Top-Level Site and Bucket ID are blank on rows from the File System folder. Storage Type names the type folder. Source File names the Paths folder each row came from; on lonewolf_win10 Site and Storage Type separate its two folders, and Source File is kept because, as in the other Chromium artifacts, Browser, Profile and User do not separate two copies of one profile. A row shows that the browser stored the entry for that site through the API. It does not show that a person chose to save the file, opened it or saw it. Known data (windows11_arm_chrome_fs_notifications_known_20261114, Chrome 157.0.8103.51 on Windows 11 ARM64, a fresh profile and one local test page at http://localhost:8765, minted 2026-11-14 07:52:26 to 07:53:12 UTC; README beside the image): the page wrote three files and a folder through the Origin Private File System and one file through webkitRequestFileSystem. Its 9 rows were the root folder, the kd-folder folder, the four files, each with its saved file byte-identical to what was written, and 3 Deleted rows naming each Origin Private File System file with .crswap appended, the swap file Chrome creates and removes while writing one (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/content/browser/file_system_access/file_system_access_file_handle_impl.cc#L615-L616). Both APIs' files were in one site folder under Storage Type Temporary, and both folders' Folder Last Changed fell inside the mint, to the second. On the corpus images: 923 rows on 2 of 7 images, all from the File System folder and from Google Chrome: lonewolf_win10 546 (538 files and 8 folders, 2 sites) and mvs2026_macbookpro_macos15 377 (374 files and 3 folders, 1 site). Every file row had its saved file in the extraction. By the sniffed type, lonewolf_win10 held 529 web fonts (application/font-woff), 8 PNG images and 1 empty file (0 bytes), which has no type, and mvs2026_macbookpro_macos15 373 web fonts and 1 empty file (0 bytes); what the sites stored them for is not established. State held Live on all 923 rows, and Top-Level Site and Bucket ID held no value on any of the 923 rows. Site and Storage Type held one value on all 377 rows of mvs2026_macbookpro_macos15. Browser, Profile and User held one value on all 546 rows of lonewolf_win10 and all 377 rows of mvs2026_macbookpro_macos15. Folder Last Changed fell in 2018 on lonewolf_win10 and in 2025 on mvs2026_macbookpro_macos15. The Paths databases of hexordia_mvs2025_win11, ou_ransomware_server2022 and pc_mus_001_win11 held no entry. Not exercised by the tested images: bucket rows, a missing saved file, any Linux profile, browsers other than Google Chrome, the syncable type and an entry kept in a table file (.ldb).",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/File System/*',
            '*/Library/Application Support/Google/Chrome/*/File System/*',
            '*/.config/google-chrome/*/File System/*',
            '*/AppData/Local/Chromium/User Data/*/File System/*',
            '*/Library/Application Support/Chromium/*/File System/*',
            '*/.config/chromium/*/File System/*',
            '*/snap/chromium/common/chromium/*/File System/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/File System/*',
            '*/webbrowser/chrome/*/File System/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/File System/*',
            '*/Library/Application Support/Microsoft Edge/*/File System/*',
            '*/.config/microsoft-edge/*/File System/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/File System/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/File System/*',
            '*/.config/BraveSoftware/Brave-Browser/*/File System/*',
            '*/AppData/Local/Vivaldi/User Data/*/File System/*',
            '*/Library/Application Support/Vivaldi/*/File System/*',
            '*/.config/vivaldi/*/File System/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/File System/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/File System/*',
            '*/AppData/Roaming/360se6/User Data/*/File System/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/File System/*',
            '*/.config/opera/*/File System/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/File System/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/File System/*',
            '*/AppData/Roaming/360se6/User Data/File System/*',
            '*/Library/Application Support/com.operasoftware.Opera/File System/*',
            '*/.config/opera/File System/*',
            '*/AppData/Local/Google/Chrome/User Data/*/WebStorage/*',
            '*/Library/Application Support/Google/Chrome/*/WebStorage/*',
            '*/.config/google-chrome/*/WebStorage/*',
            '*/AppData/Local/Chromium/User Data/*/WebStorage/*',
            '*/Library/Application Support/Chromium/*/WebStorage/*',
            '*/.config/chromium/*/WebStorage/*',
            '*/snap/chromium/common/chromium/*/WebStorage/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/WebStorage/*',
            '*/webbrowser/chrome/*/WebStorage/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/WebStorage/*',
            '*/Library/Application Support/Microsoft Edge/*/WebStorage/*',
            '*/.config/microsoft-edge/*/WebStorage/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/WebStorage/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/WebStorage/*',
            '*/.config/BraveSoftware/Brave-Browser/*/WebStorage/*',
            '*/AppData/Local/Vivaldi/User Data/*/WebStorage/*',
            '*/Library/Application Support/Vivaldi/*/WebStorage/*',
            '*/.config/vivaldi/*/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/WebStorage/*',
            '*/AppData/Roaming/360se6/User Data/*/WebStorage/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/WebStorage/*',
            '*/.config/opera/*/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/WebStorage/*',
            '*/AppData/Roaming/360se6/User Data/WebStorage/*',
            '*/Library/Application Support/com.operasoftware.Opera/WebStorage/*',
            '*/.config/opera/WebStorage/*',
        ),
        "output_types": "standard",
        "artifact_icon": "file",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (its Paths databases held no entry)",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 546 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 377 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (its Paths databases held no entry)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (its Paths databases held no entry)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no file under a File System folder)",
            "windows11_arm_chrome_fs_notifications_known_20261114": "Windows 11 build 26200 ARM64 | 9 rows (known data)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows (no file under a File System folder)",
        },
    },
    "chromiumFileSystemBuckets": {
        "name": "Chromium File System API - Bucket Storage",
        "description": "File System API storage a Chromium-based browser keeps per storage bucket under WebStorage, "
                       "such as the storage of a site embedded in another site, with the bucket's storage key and "
                       "times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the bucket FileSystem folders under WebStorage of each Chromium-based browser profile that scripts/chromium/browser_profiles locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and webOS webbrowser) on Windows, macOS and Linux. Format and meanings come from Chromium at commit 3a50e012e4c9b8a410a4e2b12bf577e69ee8f755 (tag 130.0.6723.58). The cited source is one release; the tested profiles were written by others (Folder Last Changed falls in 2018 and 2025 on the corpus images, and the known data is Chrome 157), and their records decoded with this layout. Each LevelDB folder is read with the vendored ccl_leveldb, and only the newest version of each key is used: LevelDB orders the versions of a key by sequence number (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). Browser, Profile and User come from the path, as in the other Chromium artifacts. On a Mac logical extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a folder or QuotaManager file whose copy under the second path has the same bytes is read once. On mvs2026_macbookpro_macos15 that applied to QuotaManager only, as no bucket folder existed. A folder that cannot be read is skipped and named in the run log. Ported from ALEAPP's Chromium File System API - Bucket Storage; the Android known data in its notes was not repeated here. Chromium keeps File System API storage per storage bucket in <profile>/WebStorage/<bucket id>/FileSystem (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/quota/storage_directory_util.cc#L11-L25, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/components/services/storage/public/cpp/constants.cc#L11-L12, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/components/services/storage/public/cpp/constants.cc#L36-L38), for every bucket that is not a site's first-party default bucket (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/obfuscated_file_util.cc#L926-L942), such as the storage of a site embedded in another site. One row per bucket that has at least one Paths database under its FileSystem folder; its Paths databases have the same format as a first-party site's and their entries are listed in Chromium File System API - Files. The bucket is looked up by its id in the buckets table of WebStorage/QuotaManager (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/quota/quota_database.cc#L164-L176), opened read-only. Storage Key (as stored) is the bucket's serialized StorageKey (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/quota/quota_database.cc#L88-L97); Site is its origin and Top-Level Site the site after ^0 (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/third_party/blink/common/storage_key/storage_key.cc#L29, https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/third_party/blink/common/storage_key/storage_key.cc#L93), blank for other shapes. Bucket Name (as stored) is the bucket's name. Bucket Last Accessed and Bucket Last Modified are the bucket's last_accessed and last_modified, microseconds since 1601-01-01 UTC (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/sql/statement.cc#L43-L45). They are the bucket's, not its File System storage's: Chromium updates them when a storage client reports an access to or a change in the bucket (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/quota/quota_manager_impl.cc#L1985-L2046), and File System storage reports an access when it is opened (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_file_system_backend_delegate.cc#L240-L244). Saved Entries counts the folders and files the bucket's Paths databases list, the root folder not counted; a row with no saved entries shows the bucket has a Paths database, in a folder Chromium makes when the file system is opened with creation allowed (https://github.com/chromium/chromium/blob/3a50e012e4c9b8a410a4e2b12bf577e69ee8f755/storage/browser/file_system/sandbox_file_system_backend_delegate.cc#L97-L104). When QuotaManager is missing or does not list the id, Site, Top-Level Site, Storage Key, Bucket Name and both times are blank. Source File names one Paths folder of the bucket. On the tested images no file sat under a bucket FileSystem folder: the WebStorage folders of hexordia_mvs2025_win11, mvs2026_macbookpro_macos15, ou_ransomware_server2022, pc_mus_001_win11, ubuntu2604_arm64_chromium, windows11_arm_operagx_360se_known_20261107 and windows11_arm_chrome_fs_notifications_known_20261114 held none, and lonewolf_win10 held no file under a WebStorage folder, so this artifact wrote no row and everything above is from the cited source only.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/WebStorage/*',
            '*/Library/Application Support/Google/Chrome/*/WebStorage/*',
            '*/.config/google-chrome/*/WebStorage/*',
            '*/AppData/Local/Chromium/User Data/*/WebStorage/*',
            '*/Library/Application Support/Chromium/*/WebStorage/*',
            '*/.config/chromium/*/WebStorage/*',
            '*/snap/chromium/common/chromium/*/WebStorage/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/WebStorage/*',
            '*/webbrowser/chrome/*/WebStorage/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/WebStorage/*',
            '*/Library/Application Support/Microsoft Edge/*/WebStorage/*',
            '*/.config/microsoft-edge/*/WebStorage/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/WebStorage/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/WebStorage/*',
            '*/.config/BraveSoftware/Brave-Browser/*/WebStorage/*',
            '*/AppData/Local/Vivaldi/User Data/*/WebStorage/*',
            '*/Library/Application Support/Vivaldi/*/WebStorage/*',
            '*/.config/vivaldi/*/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/WebStorage/*',
            '*/AppData/Roaming/360se6/User Data/*/WebStorage/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/WebStorage/*',
            '*/.config/opera/*/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/WebStorage/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/WebStorage/*',
            '*/AppData/Roaming/360se6/User Data/WebStorage/*',
            '*/Library/Application Support/com.operasoftware.Opera/WebStorage/*',
            '*/.config/opera/WebStorage/*',
        ),
        "output_types": "standard",
        "artifact_icon": "archive",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no file under a bucket FileSystem folder)",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 0 rows (no file under a WebStorage folder)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no file under a bucket FileSystem folder)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no file under a bucket FileSystem folder)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no file under a bucket FileSystem folder)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no file under a bucket FileSystem folder)",
            "windows11_arm_chrome_fs_notifications_known_20261114": "Windows 11 build 26200 ARM64 | 0 rows (no file under a bucket FileSystem folder)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows (no file under a bucket FileSystem folder)",
        },
    },
}

import os
import re
import sqlite3
import struct

from scripts.chromium.browser_profiles import open_store, profile_stores, row_tail, webkit_time
from scripts.chromium.web_storage import is_deleted, newest_versions, profile_folders, split_storage_key
from scripts.ilapfuncs import artifact_processor, check_in_media, logfunc

_ORIGINS = 'File System/Origins'
_ORIGIN_PREFIX = 'ORIGIN:'
_CHILD_PREFIX = 'CHILD_OF:'
# SandboxFileSystemBackendDelegate type folders (see the notes).
_TYPES = {'t': 'Temporary', 'p': 'Persistent', 's': 'Syncable'}
_SITE_PATHS = re.compile(r'File System/([^/]+)/([tps])/Paths')
_BUCKET_PATHS = re.compile(r'WebStorage/(\d+)/FileSystem/([tps])/Paths')
_QUOTA = 'WebStorage/QuotaManager'
_READ_ERRORS = (OSError, ValueError, KeyError, IndexError, EOFError, struct.error)


def _site_paths(name):
    return bool(_SITE_PATHS.fullmatch(name))


def _bucket_paths(name):
    return bool(_BUCKET_PATHS.fullmatch(name))


_site_paths.folder_label = 'File System Paths'
_bucket_paths.folder_label = 'bucket FileSystem Paths'


def _newest(store, label):
    """{key text: (deleted, value)} for the newest version of every key of a LevelDB folder, or None."""
    try:
        newest, _puts, _records = newest_versions(store.path)
    except _READ_ERRORS as ex:
        logfunc(f'{label}: could not read {store.relative}: {ex}')
        return None
    return {key.decode('utf-8', 'replace'): (is_deleted(state), value)
            for key, (_seq, state, value) in newest.items()}


def _site(identifier):
    """The origin a DatabaseIdentifier string names: scheme_host_port, port 0 the default."""
    if identifier == 'file__0':
        return 'file:///'
    first, last = identifier.find('_'), identifier.rfind('_')
    if first <= 0 or last == first or last == len(identifier) - 1:
        return ''
    scheme, host, port = identifier[:first], identifier[first + 1:last], identifier[last + 1:]
    return f'{scheme}://{host}' if port == '0' else f'{scheme}://{host}:{port}'


def _file_info(value):
    """(parent id, data path, name, time) from a Paths record's pickled FileInfo."""
    size, = struct.unpack_from('<I', value, 0)
    if size + 4 > len(value):
        raise ValueError('pickle shorter than its header')
    offset = 4
    parent, = struct.unpack_from('<q', value, offset)
    offset += 8
    strings = []
    for _ in range(2):
        length, = struct.unpack_from('<i', value, offset)
        offset += 4
        if length < 0 or offset + length > len(value):
            raise ValueError('string runs past the pickle')
        strings.append(value[offset:offset + length].decode('utf-8', 'replace'))
        offset += (length + 3) // 4 * 4
    internal, = struct.unpack_from('<q', value, offset)
    return parent, strings[0], strings[1], internal


def _origins(store, label):
    """[(site key, state, folder)] from an Origins store, newest version of each ORIGIN key."""
    records = _newest(store, label)
    if records is None:
        return []
    out = []
    for key, (deleted, value) in sorted(records.items()):
        if not key.startswith(_ORIGIN_PREFIX):
            continue
        out.append((key[len(_ORIGIN_PREFIX):], 'Deleted' if deleted else 'Live',
                    '' if deleted else value.decode('utf-8', 'replace')))
    return out


def _full_path(entry_id, entries):
    names, seen = [], set()
    while entry_id and entry_id in entries and entry_id not in seen:
        seen.add(entry_id)
        parent, _data, name, _time = entries[entry_id]
        names.append(name)
        entry_id = parent
    if entry_id and entry_id not in entries:
        names.append('<unresolved>')
    return '/' + '/'.join(reversed(names))


def _entries(store, label):
    """(live entries {id: info}, deleted [(parent id, name)]) from a Paths store."""
    records = _newest(store, label)
    if records is None:
        return {}, []
    live, deleted = {}, []
    for key, (is_gone, value) in records.items():
        if key.isdigit() and not is_gone:
            try:
                live[int(key)] = _file_info(value)
            except _READ_ERRORS as ex:
                logfunc(f'{label}: entry {key} in {store.relative} did not decode: {ex}')
        elif key.startswith(_CHILD_PREFIX) and is_gone:
            parent, _sep, name = key[len(_CHILD_PREFIX):].partition(':')
            if parent.isdigit():
                deleted.append((int(parent), name))
    return live, deleted


def _site_key(paths_store):
    """(File System folder, site folder) of a File System/<site>/<type>/Paths store, from its staged path.

    Keyed on the staged folder rather than the profile container, so two copies of one profile
    that differ (Users/ and System/Volumes/Data/Users/) never count into each other.
    """
    type_folder = os.path.dirname(paths_store.path)
    site_folder = os.path.dirname(type_folder)
    return os.path.dirname(site_folder), os.path.basename(site_folder)


def _saved(live):
    """Folders and files a Paths store lists, the root folder (id 0) not counted."""
    return sum(1 for entry_id in live if entry_id)


def _quota(context, label):
    """{profile container: {bucket id: (storage key, name, last accessed, last modified)}} from QuotaManager."""
    out = {}
    for store in profile_stores(context, {_QUOTA}, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            rows = db.execute('SELECT id, storage_key, name, last_accessed, last_modified FROM buckets').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read buckets in {store.relative}: {ex}')
            continue
        finally:
            db.close()
        out[store.container] = (store, {str(row[0]): tuple(row[1:]) for row in rows})
    return out


def _entry_rows(store, live, deleted, site, top_site, bucket_id):
    """Rows of one Paths store: its live entries, then the names its deleted CHILD_OF keys give."""
    type_folder = os.path.dirname(store.path)
    storage_type = _TYPES[os.path.basename(type_folder)]
    rows = []
    for entry_id in sorted(live):
        _parent, data_path, name, internal = live[entry_id]
        is_folder = data_path == ''
        media, size = '', ''
        if not is_folder:
            # Windows builds store the data path with \, POSIX builds with / (see the notes).
            stored = os.path.join(type_folder, *data_path.replace('\\', '/').split('/'))
            if os.path.isfile(stored):
                size = os.path.getsize(stored)
                media = check_in_media(stored, name) or ''
        rows.append((webkit_time(internal) if is_folder else '', site, top_site,
                     _full_path(entry_id, live) if entry_id else '/',
                     'Folder' if is_folder else 'File', 'Live', media, size, data_path, storage_type, bucket_id)
                    + row_tail(store))
    for parent, name in deleted:
        parent_path = _full_path(parent, live) if parent else ''
        rows.append(('', site, top_site, f'{parent_path}/{name}' if parent_path not in ('', '/') else f'/{name}',
                     '', 'Deleted', '', '', '', storage_type, bucket_id) + row_tail(store))
    return rows


@artifact_processor
def chromiumFileSystemSites(context):
    label = 'Chromium File System API - Sites'
    data_headers = ('State', 'Site', 'Site Key (as stored)', 'Folder', 'Folder Present', 'Saved Entries',
                    'Browser', 'Profile', 'User', 'Source File')
    data_list, sources = [], []
    saved = {}
    for store in profile_folders(context, _site_paths, label):
        live, _deleted = _entries(store, label)
        key = _site_key(store)
        saved[key] = saved.get(key, 0) + _saved(live)
    for store in profile_folders(context, _ORIGINS, label):
        origins = _origins(store, label)
        if not origins:
            continue
        sources.append(store.path)
        root = os.path.dirname(store.path)
        for key, state, folder in origins:
            present = os.path.isdir(os.path.join(root, folder)) if folder else False
            data_list.append((state, _site(key), key, folder, 'Yes' if present else 'No',
                              saved.get((root, folder), 0) if folder else '') + row_tail(store))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumFileSystemEntries(context):
    label = 'Chromium File System API - Files'
    data_headers = (('Folder Last Changed', 'datetime'), 'Site', 'Top-Level Site', 'Path', 'Entry Type', 'State',
                    ('File', 'media'), 'Size', 'Data Path (as stored)', 'Storage Type', 'Bucket ID', 'Browser',
                    'Profile', 'User', 'Source File')
    data_list, sources = [], []
    sites = {}
    for store in profile_folders(context, _ORIGINS, label):
        for key, state, folder in _origins(store, label):
            if state == 'Live' and folder:
                sites[(os.path.dirname(store.path), folder)] = _site(key)
    for store in profile_folders(context, _site_paths, label):
        live, deleted = _entries(store, label)
        if not live and not deleted:
            continue
        sources.append(store.path)
        site = sites.get(_site_key(store), '')
        data_list.extend(_entry_rows(store, live, deleted, site, '', ''))
    quota = _quota(context, label)
    for store in profile_folders(context, _bucket_paths, label):
        live, deleted = _entries(store, label)
        if not live and not deleted:
            continue
        sources.append(store.path)
        bucket_id = store.name.split('/')[1]
        buckets = quota.get(store.container, (None, {}))[1]
        storage_key = buckets.get(bucket_id, ('',))[0] or ''
        site, top_site, _other = split_storage_key(storage_key) if storage_key else ('', '', '')
        data_list.extend(_entry_rows(store, live, deleted, site, top_site, bucket_id))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumFileSystemBuckets(context):
    label = 'Chromium File System API - Bucket Storage'
    data_headers = (('Bucket Last Modified', 'datetime'), ('Bucket Last Accessed', 'datetime'), 'Site',
                    'Top-Level Site', 'Storage Key (as stored)', 'Bucket Name (as stored)', 'Bucket ID',
                    'Saved Entries', 'Browser', 'Profile', 'User', 'Source File')
    data_list, sources = [], []
    quota = _quota(context, label)
    buckets_seen = {}
    for store in profile_folders(context, _bucket_paths, label):
        live, _deleted = _entries(store, label)
        bucket_id = store.name.split('/')[1]
        key = (store.container, bucket_id)
        held = buckets_seen.setdefault(key, [store, 0])
        held[1] += _saved(live)
    for (container, bucket_id), (store, saved) in sorted(buckets_seen.items(), key=lambda item: item[0]):
        quota_store, buckets = quota.get(container, (None, {}))
        if quota_store is not None and quota_store.path not in sources:
            sources.append(quota_store.path)
        sources.append(store.path)
        storage_key, name, accessed, modified = buckets.get(bucket_id, ('', '', 0, 0))
        site, top_site, _other = split_storage_key(storage_key) if storage_key else ('', '', '')
        data_list.append((webkit_time(modified), webkit_time(accessed), site, top_site, storage_key or '', name or '',
                          bucket_id, saved) + row_tail(store))
    return data_headers, data_list, '\n'.join(sources)
