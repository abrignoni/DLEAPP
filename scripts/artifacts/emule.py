"""eMule known files, unfinished downloads, download list, search history, stored searches and settings, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Formats are read by scripts/emule.py, which follows the eMule 0.72a source pinned there.
"""

import os
from datetime import datetime, timezone

from scripts.emule import (SEARCH_TYPES, EmuleFormatError, ini_values, parse_file_link, read_download_overview,
                           read_known_met, read_part_met, read_preferences_dat, read_stored_searches,
                           read_utf16_lines)
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
        "platforms": ("Windows",),
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
        "platforms": ("Windows",),
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
        "platforms": ("Windows",),
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
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "eMule",
        "platforms": ("Windows",),
        "notes": "Files are read as eMule 0.72a reads them. The known data (windows11_arm_emule_known_20261108) is eMule 0.72a on Windows 11 ARM64, never connected to eD2K or Kad. Nothing in these files names the program that wrote them; other eD2K clients may use the same file names, and only eMule 0.72a was tested. Matched in eMule's config folder under any folder named eMule (eMule keeps it under AppData\\\\Local\\\\eMule, ProgramData\\\\eMule or its own install folder, https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/Preferences.cpp#L2947-L2958); a config folder under another name is not matched. User is the account folder name taken from the file path; User held one value on all rows of the known data, which has one profile. One row per line of AC_SearchStrings.dat, the list eMule saves for its search box suggestions (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/CustomAutoComplete.cpp#L310-L319). eMule adds the text when Start is clicked, before the search runs (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/SearchParamsWnd.cpp#L657-L659): on the known data the search was refused because eMule was not connected, and the text was saved anyway, so a row does not show that a search ran or returned anything. Position is the line number. eMule inserts new text at the top and moves reused text there (https://github.com/irwir/eMule/blob/ac3d52eafd88e9f6d9e0c2204c6dbead18db750b/srchybrid/CustomAutoComplete.cpp#L112-L131), so Position 1 is the most recently used; the known data held one entry, so the order is source-verified only. The file holds no times. StoredSearches.met, which keeps search results, held no search on the known data. It is reported by eMule Stored Searches and eMule Stored Search Results.",
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
        "platforms": ("Windows",),
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
    "emuleStoredSearches": {
        "name": "eMule Stored Searches",
        "description": "Searches eMule stored in StoredSearches.met to restore on its next start, with the search "
                       "text, type, file type and the number of results stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "eMule",
        "platforms": ("Windows",),
        "notes": "One row per search in config/StoredSearches.met. eMule writes the file on shutdown from its "
                 "open search tabs when its option to store searches is on (SearchList.cpp, StoreSearches, and "
                 "EmuleDlg.cpp, in the eMule 0.72a source pinned in scripts/emule.py). With the option off the "
                 "file is not rewritten (EmuleDlg.cpp), so it can be older than the last shutdown. This "
                 "follows the source and was not tested. Tested on constructed data: eMule refuses to search "
                 "while disconnected, so a file with two searches and three results was built with test "
                 "values, eMule 0.72a loaded it with a firewall blocking it and saved it again on exit "
                 "(windows11_arm_emule_search_known_20261121). Every reported field read back the same. A "
                 "search made on a real network was not tested, and other versions were not tested. Search "
                 "Type comes from the ESearchType list in SearchParams.h. It is the type stored for the tab. "
                 "eMule replaces Automatic with the method it chose (SearchResultsWnd.cpp, StartNewSearch). A "
                 "client shared files tab keeps the default, eD2K Server (SearchParams.h), which does not "
                 "describe it. Both follow the source and were not tested. No time is stored for a search, so "
                 "a row does not say when it was made. eMule renumbers searches when it loads them, so the "
                 "stored search ID is not reported. Search Order is the position in the file. Search Text is "
                 "the stored search expression, read as UTF-8, or as Windows-1252 when the bytes are not valid "
                 "UTF-8. eMule also stores expressions it builds itself, as for a related-files search "
                 "(SearchResultsWnd.cpp), so it is not always text a person typed. File Type is the file type "
                 "text stored for the search, read the same way. Stored Results is the count stored for the "
                 "search, blank when the file ends before it. Results Read is how many results were read. The "
                 "two differ when reading stopped before every stored result was read, as when the file is cut "
                 "short or a result holds a tag type the reader does not know. The run log names the file and "
                 "where reading stopped. Equal counts do not show the file is whole. A file cut between two "
                 "searches, or inside the next search's header, leaves both counts equal and only the run log "
                 "shows it. Stored Results and Results Read held the same value as each other on each row of "
                 "the known data. Title is the special title stored for the tab. Client Shared Files is Yes "
                 "when the tab holds a client's shared files and not a search. Search Text then holds that "
                 "client's user name (SearchList.cpp, ProcessSearchAnswer). This was not in the known data. "
                 "Title had no value and Client Shared Files held No on all rows of the known data. User is "
                 "the folder name after Users in the file's path, blank when there is none, and held one value "
                 "on all rows of the known data. Source File is the file the row was read from. Source File "
                 "tells apart two files that share a User value or have none, as when eMule keeps its config "
                 "under ProgramData or its install folder. Search Order and Source File together link a result "
                 "to its search.",
        "paths": ('*/eMule/config/StoredSearches.met',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "windows11_arm_emule_search_known_20261121": "Windows 11 build 26200 (ARM64), eMule 0.72a | 2 rows (constructed)",
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 0 rows (no stored search)",
        },
    },
    "emuleStoredSearchResults": {
        "name": "eMule Stored Search Results",
        "description": "Results stored with eMule's open searches, with the file name, size, eD2K hash, the client "
                       "address and the source counts.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "eMule",
        "platforms": ("Windows",),
        "notes": "One row per result read from config/StoredSearches.met (SearchList.cpp and SearchFile.cpp in "
                 "the eMule 0.72a source pinned in scripts/emule.py). When reading stops early, as on a file "
                 "cut short, the result being read and every later result and search are not listed. eMule "
                 "Stored Searches shows Stored Results against Results Read, and the run log names the file. "
                 "Tested on constructed data: three results with test values were built into the file, eMule "
                 "0.72a loaded it with a firewall blocking it and saved it again on exit "
                 "(windows11_arm_emule_search_known_20261121). Every field the known data held read back the "
                 "same: file name, size, hash, client address and port, both source counts, file type, and the "
                 "artist, title and bitrate tags. Folder, AICH hash, rating, comment, album, length, codec, "
                 "format, last seen complete, a tag with any other name, a repeated tag name, a low ID, a "
                 "client ID or port of 0 and a size of 4 GiB or more were not in the known data. They were not "
                 "tested. Some differences between the reader and eMule are said below. The list is not "
                 "complete. Results from a real server or Kad were not tested. The result record has no time "
                 "field. eMule reads a last seen complete time from a result's tags (FT_LASTSEENCOMPLETE, "
                 "GetLastSeenComplete in SearchFile.cpp). When that tag is stored it shows in Other Values as "
                 "the stored number. The known data had none. A row records a result eMule kept for an open "
                 "search. It does not show that the file was downloaded or that the client really held it. "
                 "Client Address is the stored client ID read as an IPv4 address, and Client Port its port. A "
                 "client ID below 16777216 is a low ID (IsLowID, OtherFunctions.h), not an address: the "
                 "address is then blank and the ID is in Low ID. A client ID of 0 shows no address and no ID, "
                 "and a port of 0 shows blank. eMule sets both to 0 when it rejects the client address of a "
                 "result it reads (SearchFile.cpp, IsValidSearchResultClientIPPort), and it writes 0 for both "
                 "on results of a Kademlia search (SearchList.cpp, KademliaSearchKeyword). A blank address "
                 "does not say which. Sources and Complete Sources are the counts stored for the result. "
                 "Search Order is the position in the file of the search the result was stored under, the same "
                 "value as in eMule Stored Searches. Folder, AICH Hash and Rating (as stored) come from their "
                 "stored tags. AICH Hash is the last stored text value of 32 base32 characters. eMule's own "
                 "check also accepts 31 characters (OtherFunctions.cpp, DecodeBase32). Such a value stays in "
                 "Other Values. Folder, AICH Hash and Rating (as stored) had no value on any row of the known "
                 "data. Other Values holds the remaining stored tags as name=value: format, artist, album, "
                 "title, length, bitrate, codec, comment, last_seen_complete, and any other tag under its name "
                 "or number. A tag whose value does not fit its dedicated column, one stored with empty text, "
                 "and the other copies of a repeated tag stay in Other Values. A folder tag repeating the "
                 "value shown in Folder is not listed again, because eMule writes the folder again each time "
                 "it saves a result it loaded (SearchFile.cpp, StoreToFile). Entries are separated by '; '. A "
                 "backslash or semicolon in a name or value, or an equals sign in a name, is shown with a "
                 "backslash before it. Every entry shows its stored identifier in brackets, [tag 0xNN] for a "
                 "numbered tag and [name <hex>] for a named tag, so a numbered tag and a named tag with the "
                 "same text cannot read alike. An entry does not show the tag's type or its place in the file. "
                 "Entries are sorted by name, then value, so two tags with one identifier can read alike. When "
                 "a column's tag repeats, File Name and File Type use the last text value (AbstractFile.cpp, "
                 "GetStrTagValue), and Sources, Complete Sources and Rating use the last number of 32 bits or "
                 "less (SearchFile.cpp), as eMule does. Size uses the last size tag of any type, as eMule "
                 "does. It is blank when that tag is not a whole number of 8, 16, 32 or 64 bits. eMule then "
                 "uses 0. The first folder value that is not empty is shown, for any search type. eMule keeps "
                 "that one only for a search that is not Kademlia (SearchFile.cpp). Rating as stored is "
                 "eMule's rating times 51 (SearchFile.cpp, StoreToFile). eMule writes the folder it keeps for "
                 "a result in the computer's ANSI code page (SearchFile.cpp, StoreToFile), which the file does "
                 "not record. A folder tag kept from an earlier load is written as UTF-8. A folder name that "
                 "is not valid UTF-8 is read as Windows-1252 and can come out wrong. User is the folder name "
                 "after Users in the file's path, blank when there is none, and held one value on all rows of "
                 "the known data. Source File is the file the row was read from. Source File tells apart two "
                 "files that share a User value or have none, as when eMule keeps its config under ProgramData "
                 "or its install folder. Search Order and Source File together link a result to its search. "
                 "File Type is the text of the file type tag stored for the result. It is not mapped to "
                 "eMule's display names. Search Text is the search's text from eMule Stored Searches. For a "
                 "client shared files tab it is a user name.",
        "paths": ('*/eMule/config/StoredSearches.met',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "list",
        "sample_data": {
            "windows11_arm_emule_search_known_20261121": "Windows 11 build 26200 (ARM64), eMule 0.72a | 3 rows (constructed)",
            "windows11_arm_emule_known_20261108": "Windows 11 build 26200 (ARM64), eMule 0.72a | 0 rows (no stored search)",
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


def _escaped(value):
    """A stored name or value with the Other Values separator marked, so it cannot read as a second tag."""
    return str(value).replace('\\', '\\\\').replace(';', '\\;')


def _stored_paths(context):
    return sorted(str(f) for f in context.get_files_found()
                  if os.path.isfile(str(f)) and os.path.basename(str(f)).lower() == 'storedsearches.met')


def _stored(context, name):
    for path in _stored_paths(context):
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{name}: could not read {relative} ({type(exc).__name__})')
            continue
        try:
            result = read_stored_searches(data)
            if not result['complete']:
                logfunc(f'{name}: {relative} has bytes after the last search')
        except EmuleFormatError as exc:
            result = exc.partial or {'searches': []}
            logfunc(f'{name}: {relative} stopped ({exc}); keeping the {len(result["searches"])} searches read before it')
        yield path, result


@artifact_processor
def emuleStoredSearches(context):
    data_headers = ('Search Text', 'Search Type', 'File Type', 'Stored Results', 'Results Read', 'Title',
                    'Client Shared Files', 'Search Order', 'User', 'Source File')
    data_list = []
    for path, result in _stored(context, 'eMule Stored Searches'):
        for order, search in enumerate(result['searches'], 1):
            declared = search['declared_results']
            data_list.append((search['expression'], SEARCH_TYPES.get(search['type'], search['type']),
                              search['file_type'], '' if declared is None else declared, len(search['results']),
                              search['title'], 'Yes' if search['client_shared'] else 'No', order,
                              user_from_path(context.get_relative_path(path)), context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(_stored_paths(context))


@artifact_processor
def emuleStoredSearchResults(context):
    data_headers = ('File Name', 'Size (bytes)', 'eD2K Hash', 'Search Text', 'Search Order', 'Client Address',
                    'Client Port', 'Low ID', 'Sources', 'Complete Sources', 'File Type', 'Folder', 'AICH Hash',
                    'Rating (as stored)', 'Other Values', 'User', 'Source File')
    data_list = []
    for path, result in _stored(context, 'eMule Stored Search Results'):
        for order, search in enumerate(result['searches'], 1):
            for item in search['results']:
                address, low_id = '', ''
                if item['client_id'] >= 16777216:
                    address = '.'.join(str(octet) for octet in item['client_id'].to_bytes(4, 'little'))
                elif item['client_id']:
                    low_id = item['client_id']
                other = [f"{_escaped(key).replace('=', chr(92) + '=')}={_escaped(value)}"
                         for key, value in sorted(item['other'], key=lambda pair: (pair[0], str(pair[1])))]
                data_list.append((item['name'] or '', item['size'] if item['size'] is not None else '',
                                  item['hash'].hex().upper(), search['expression'], order, address,
                                  item['client_port'] or '', low_id,
                                  item['sources'] if item['sources'] is not None else '',
                                  item['complete_sources'] if item['complete_sources'] is not None else '',
                                  item['file_type'] or '', item['folder'] or '',
                                  '' if item['aich'] in (None, '') else item['aich'],
                                  '' if item['rating'] is None else item['rating'], '; '.join(other),
                                  user_from_path(context.get_relative_path(path)), context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(_stored_paths(context))
