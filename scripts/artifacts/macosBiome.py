"""Records from fifteen macOS Biome streams, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each stream is a folder of SEGB files whose records hold one protobuf message. The field
numbers read are the ones iLEAPP's Biome modules read for the same streams, checked against
macOS records as each artifact's notes describe.
"""

__artifacts_v2__ = {
    "macosBiomeAppInFocus": {
        "name": "Biome App In Focus",
        "description": "Records from the App.InFocus Biome stream: record time, bundle ID, the "
                       "app's version strings, field 3 as stored and the transition reason where a "
                       "record holds one.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the App.InFocus Biome stream. Each file in the stream's local folder, "
                 "and in each folder under its remote folder, other than one whose name begins "
                 "with a dot, is read as a SEGB file with the vendored ccl_segb package, one row "
                 "per record the file marks as written whose data ccl_segb can still read, and "
                 "each such record"
                 " is read as one protobuf message whose fields are taken by number without a schema; "
                 "a record that does not read as one is counted in the run log and not reported. "
                 "Records the file does not mark as written are not reported; those ccl_segb "
                 "returns are counted in the run log, and it returns none of the entries a "
                 "version 2 file marks as empty. Files under a tombstone folder are not read. "
                 "Record Time (UTC) is the "
                 "time the SEGB file stores with each record, which ccl_segb reads from a "
                 "version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports "
                 "as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, "
                 "and ccl_segb/ccl_segb_common.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is "
                 "where the record begins in its file: in a version 2 file that is the record's "
                 "8-byte header, which starts with its stored CRC, and the record's data begins "
                 "8 bytes later. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. Bundle ID is field 6, and Field 3"
                 " (as stored) is field 3, as iLEAPP's biomeInfocus module reads them (Reference: "
                 "iLEAPP, scripts/artifacts/biomeInfocus.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeInfocus.py#L94-L97);"
                 " iLEAPP shows 1 and 0 as Foreground and Background, and its notes call those labels "
                 "an interpretation of the stream name. Transition Reason (as stored) is field 1, "
                 "which that module does not read: the description of the stream that Mattia Epifani "
                 "quotes from the System Events plist in '84 Streams Later, Part 2: Inside Apple "
                 "Biome' "
                 "(https://blog.digital-forensics.it/2026/07/84-streams-later-part-2-inside-apple.html)"
                 " says the stream includes the reason for transition. App Version (as stored) and "
                 "Bundle Version (as stored) are fields 9 and 10: on 373 of the 501 local records of "
                 "the MacBook Pro they equal the CFBundleShortVersionString and CFBundleVersion of an "
                 "Info.plist in that extraction with the same CFBundleIdentifier, on 80 more they are "
                 "lower version numbers than that Info.plist holds, and the bundle IDs of the other 48"
                 " records were not among the Info.plists compared, those of the application bundles "
                 "in the extraction whose path holds no dot before .app. Fields 2, 4, 11, 12 and 13 "
                 "are not reported: field 4, read as seconds since 1 January 2001, equaled Record Time"
                 " on all 642 records of the MacBook Pro, and what the others record is not "
                 "established. On the public MacBook Pro logical extraction (macOS 15.4, not a "
                 "registered corpus key) the stream gives 642 rows, 501 from the local folder and 141 "
                 "from one of 3 remote folders; the other 2 hold, outside their tombstone "
                 "folders, only records not marked as written. "
                 "The one DevicePeer row in the MacBook Pro's Biome sync.db, whose me column is 1, "
                 "names none of the remote folders. Transition Reason has a value on 60 of the remote "
                 "rows and on no local row, and 33 of those values begin "
                 "com.apple.SpringBoard.transitionReason. In the local rows, taken in time order, 1 "
                 "and 0 alternate for each bundle ID on 23 of 24 bundle IDs, and 226 of the 248 rows "
                 "with 0 share their Record Time with a row with 1 for another bundle ID. All rows "
                 "there come from one user, so User holds one value there.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/App.InFocus/local/*', '*/Biome/streams/*/App.InFocus/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "focus-2",
    },
    "macosBiomeAppWebUsage": {
        "name": "Biome App Web Usage",
        "description": "Records from the App.WebUsage Biome stream: record time, URL, domain and "
                       "the bundle ID of the app the stream names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the App.WebUsage Biome stream. Each file in the stream's local folder, "
                 "and in each folder under its remote folder, other than one whose name begins "
                 "with a dot, is read as a SEGB file with the vendored ccl_segb package, one row "
                 "per record the file marks as written whose data ccl_segb can still read, and "
                 "each such record"
                 " is read as one protobuf message whose fields are taken by number without a schema; "
                 "a record that does not read as one is counted in the run log and not reported. "
                 "Records the file does not mark as written are not reported; those ccl_segb "
                 "returns are counted in the run log, and it returns none of the entries a "
                 "version 2 file marks as empty. Files under a tombstone folder are not read. "
                 "Record Time (UTC) is the "
                 "time the SEGB file stores with each record, which ccl_segb reads from a "
                 "version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports "
                 "as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, "
                 "and ccl_segb/ccl_segb_common.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is "
                 "where the record begins in its file: in a version 2 file that is the record's "
                 "8-byte header, which starts with its stored CRC, and the record's data begins "
                 "8 bytes later. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. URL, Domain, Bundle ID and GUID "
                 "(as stored) are fields 4, 5, 6 and 1, and Field 3 (as stored) is field 3, as "
                 "iLEAPP's biomeAppWebUsage module reads them (Reference: iLEAPP, "
                 "scripts/artifacts/biomeAppWebUsage.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeAppWebUsage.py#L60-L65),"
                 " which leaves the meaning of field 3 open. Field 2, read as seconds since 1 January "
                 "2001, was within one millisecond of Record Time on all 121 records of the MacBook "
                 "Pro, and field 8 held one value on all of them; neither is reported. On the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream "
                 "gives 121 rows; Bundle ID held one value, com.apple.Safari, on all 121 rows, GUID "
                 "(as stored) took 47 distinct values, and Field 3 (as stored) took the values 1, 2 "
                 "and 3. The URLs of 119 of the 121 records are in the history_items table of the same"
                 " user's Safari History.db in that extraction, but only 33 of the records fall within"
                 " one second of a visit to the same URL there, so a record's time is not established "
                 "as the time of a visit. All rows there come from one user's local folder, so User "
                 "and Sync Origin each held one value there.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/App.WebUsage/local/*', '*/Biome/streams/*/App.WebUsage/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "world",
    },
    "macosBiomeSafariNavigations": {
        "name": "Biome Safari Navigations",
        "description": "Records from the Safari.Navigations Biome stream: record time, URL, host and "
                       "country code as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Safari.Navigations Biome stream. Each file in the stream's local "
                 "folder, and in each folder under its remote folder, other than one whose name "
                 "begins with a dot, is read as a SEGB file with the vendored ccl_segb package, "
                 "one row per record the file marks as written whose data ccl_segb can still "
                 "read, and each such "
                 "record is read as one protobuf message whose fields are taken by number without a "
                 "schema; a record that does not read as one is counted in the run log and not "
                 "reported. Records the file does not mark as written are not reported; those "
                 "ccl_segb returns are counted in the run log, and it returns none of the "
                 "entries a version 2 file marks as empty. Files under a tombstone folder are "
                 "not read. Record Time (UTC) is "
                 "the time the SEGB file stores with each record, which ccl_segb reads from a "
                 "version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports "
                 "as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, "
                 "and ccl_segb/ccl_segb_common.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is "
                 "where the record begins in its file: in a version 2 file that is the record's "
                 "8-byte header, which starts with its stored CRC, and the record's data begins "
                 "8 bytes later. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. URL, Host and Country Code (as "
                 "stored) are fields 8, 1 and 5, as iLEAPP's biomeSafariNavigations module reads them "
                 "(Reference: iLEAPP, scripts/artifacts/biomeSafariNavigations.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeSafariNavigations.py#L103-L106)."
                 " Field 2 is not reported: read as Unix seconds it equaled Record Time rounded up to "
                 "the next 30-minute boundary on 26 of the 26 records of the MacBook Pro, the rounding"
                 " the notes of that module describe. Fields 3, 4, 6, 7 and 9 each held one value on "
                 "all 26 records there and are not reported. On the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key) the stream gives 26 rows, and "
                 "Country Code (as stored) held one value on all 26 rows. The URLs of 24 of the 26 "
                 "records are in the history_items table of the same user's Safari History.db in that "
                 "extraction, and 22 of the records fall within one second of a visit to the same URL "
                 "there. All rows there come from one user's local folder, so User and Sync Origin "
                 "each held one value there.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Safari.Navigations/local/*',
                  '*/Biome/streams/*/Safari.Navigations/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "compass",
    },
    "macosBiomeNotificationUsage": {
        "name": "Biome Notification Usage",
        "description": "Records from the Notification.Usage Biome stream: record time, and the "
                       "bundle ID and UUID each record holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Notification.Usage Biome stream. Each file in the stream's local "
                 "folder, and in each folder under its remote folder, other than one whose name "
                 "begins with a dot, is read as a SEGB file with the vendored ccl_segb package, "
                 "one row per record the file marks as written whose data ccl_segb can still "
                 "read, and each such "
                 "record is read as one protobuf message whose fields are taken by number without a "
                 "schema; a record that does not read as one is counted in the run log and not "
                 "reported. Records the file does not mark as written are not reported; those "
                 "ccl_segb returns are counted in the run log, and it returns none of the "
                 "entries a version 2 file marks as empty. Files under a tombstone folder are "
                 "not read. Record Time (UTC) is "
                 "the time the SEGB file stores with each record, which ccl_segb reads from a "
                 "version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports "
                 "as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, "
                 "and ccl_segb/ccl_segb_common.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is "
                 "where the record begins in its file: in a version 2 file that is the record's "
                 "8-byte header, which starts with its stored CRC, and the record's data begins "
                 "8 bytes later. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. Bundle ID is field 4 and UUID (as"
                 " stored) is field 5. On the public MacBook Pro logical extraction (macOS 15.4, not a"
                 " registered corpus key) the stream gives 13 rows, whose records hold fields 2, 3, 4 "
                 "and 5 only; iLEAPP's biomeNotificationUsage module reads an application name and "
                 "notification content from fields 14, 8 and 12 (Reference: iLEAPP, "
                 "scripts/artifacts/biomeNotificationUsage.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeNotificationUsage.py#L77-L79),"
                 " and no record there holds those fields. One of the 13 UUIDs equals the uuid of a "
                 "record in the Notification Center database db2/db, whose app identifier is the same "
                 "Bundle ID in lower case, and that record's delivered_date is 0.19 seconds before the"
                 " time in field 2 of the Biome record; the Users/ copy of db2/db holds 2 "
                 "records there and the System/Volumes/Data/ copy 1, and both hold the matching "
                 "record. Field 2, read as"
                 " seconds since 1 January 2001, was between 2 and 24 milliseconds before Record Time "
                 "on all 13 records, and field 3 held one value on all of them; neither is reported. "
                 "All rows there come from one user's local folder, so User and Sync Origin each held "
                 "one value there.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Notification.Usage/local/*',
                  '*/Biome/streams/*/Notification.Usage/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "bell",
    },
    "macosBiomeNowPlaying": {
        "name": "Biome Now Playing",
        "description": "Records from the Media.NowPlaying Biome stream: record time, title, artist, "
                       "the bundle ID or process name as stored, and field 3 as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Media.NowPlaying Biome stream. Each file in the stream's local "
                 "folder, and in each folder under its remote folder, other than one whose name "
                 "begins with a dot, is read as a SEGB file with the vendored ccl_segb package, "
                 "one row per record the file marks as written whose data ccl_segb can still "
                 "read, and each such record"
                 " is read as one protobuf message whose fields are taken by number without a schema; "
                 "a record that does not read as one is counted in the run log and not reported. "
                 "Records the file does not mark as written are not reported; those ccl_segb "
                 "returns are counted in the run log, and it returns none of the entries a "
                 "version 2 file marks as empty. Files under a tombstone folder are not read. "
                 "Record Time (UTC) is the "
                 "time the SEGB file stores with each record, which ccl_segb reads from a "
                 "version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports "
                 "as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, "
                 "and ccl_segb/ccl_segb_common.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is "
                 "where the record begins in its file: in a version 2 file that is the record's "
                 "8-byte header, which starts with its stored CRC, and the record's data begins "
                 "8 bytes later. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. Title, Artist and Bundle ID or "
                 "Process (as stored) are fields 8, 5 and 15, as iLEAPP's biomeNowplaying module reads"
                 " them as title, artist and bundle ID (Reference: iLEAPP, "
                 "scripts/artifacts/biomeNowplaying.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeNowplaying.py#L119-L138),"
                 " and Field 3 (as stored) is field 3, which that module does not report. The media "
                 "type and output device that module reads from fields 10 and 14 are in no record of "
                 "the MacBook Pro and are not read. Field 2, read as seconds since 1 January 2001, was"
                 " within 9 milliseconds of Record Time on all 40 records there, and fields 4, 6, 13, "
                 "20 and 21 are not reported; what they record is not established. On the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream "
                 "gives 40 rows. Field 15 held app_mode_loader on 34 records, com.apple.WebKit.GPU on "
                 "4 and an empty string on 2, so it is not always a bundle identifier. Artist has no "
                 "value on any of the 40 rows there, and Field 3 (as stored) took the values 0, 1, 2 "
                 "and 3. All rows there come from one user's local folder, so User and Sync Origin "
                 "each held one value there.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Media.NowPlaying/local/*',
                  '*/Biome/streams/*/Media.NowPlaying/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "music",
    },
    "macosBiomeWifi": {
        "name": "Biome Wi-Fi Connections",
        "description": "Records from the Device.Wireless.WiFi Biome stream: record time, SSID and "
                       "whether the record marks a connection or a disconnection.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Device.Wireless.WiFi Biome stream. Each file in the stream's local "
                 "folder, and in each folder under its remote folder, other than one whose name "
                 "begins with a dot, is read as a SEGB file with the vendored ccl_segb package, "
                 "one row per record the file marks as written whose data ccl_segb can still "
                 "read, and each "
                 "such record is read as one protobuf message whose fields are taken by number without"
                 " a schema; a record that does not read as one is counted in the run log and not "
                 "reported. Records the file does not mark as written are not reported; those "
                 "ccl_segb returns are counted in the run log, and it returns none of the "
                 "entries a version 2 file marks as empty. Files under a tombstone folder are "
                 "not read. Record Time (UTC) is "
                 "the time the SEGB file stores with each record, which ccl_segb reads from a "
                 "version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports "
                 "as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, "
                 "and ccl_segb/ccl_segb_common.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is "
                 "where the record begins in its file: in a version 2 file that is the record's "
                 "8-byte header, which starts with its stored CRC, and the record's data begins "
                 "8 bytes later. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. SSID is field 1, and Status shows"
                 " field 2 as Connected for 1 and Disconnected for 0, as iLEAPP's biomeDevWifi module "
                 "reads them (Reference: iLEAPP, scripts/artifacts/biomeDevWifi.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeDevWifi.py#L42-L67);"
                 " any other value is shown as stored. On the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key) the stream gives 35 rows naming 4 SSIDs, "
                 "all 4 of which /Library/Preferences/com.apple.wifi.known-networks.plist lists. For 5"
                 " of the 8 JoinedBySystemAt and JoinedByUserAt times that plist records for those "
                 "networks, a row with Connected falls in the same second, and for 3 of their 4 "
                 "LastDisconnectTimestamp values a row with Disconnected falls within one second. All "
                 "rows there come from one user's local folder, so User and Sync Origin each held one "
                 "value there.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Device.Wireless.WiFi/local/*',
                  '*/Biome/streams/*/Device.Wireless.WiFi/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "wifi",
    },
    "macosBiomeSiriInteractionHistory": {
        "name": 'Biome Siri Interaction History',
        "description": 'Records from the Siri.Remembers.InteractionHistory Biome stream: record time, the interaction time, the app bundle ID, and the intent class and identifiers as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Siri.Remembers.InteractionHistory Biome stream. Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Each written record holds one field 1 submessage. Interaction Time (UTC) is that submessage's field 8, eight bytes read as a little-endian double of seconds since 1 January 1970 UTC; Bundle ID, Intent Class (as stored), GUID (as stored) and Interaction GUID (as stored) are its fields 4, 2, 1 and 13, as iLEAPP's biomeSiriRemembersInteractionHistory module reads them (Reference: iLEAPP, scripts/artifacts/biomeSiriRemembersInteractionHistory.py, https://github.com/abrignoni/iLEAPP/blob/8d6a44d946a2c79cecf196c2599e21e2d42ba2e2/scripts/artifacts/biomeSiriRemembersInteractionHistory.py#L139-L149). What each field records beyond the field name is not established, and the submessage's other fields are not reported. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 129 rows, all from one user's local folder, so User and Sync Origin each held one value there; Bundle ID held one value, com.apple.news, on all 129 rows; Interaction Time fell in 2025 on the rows checked. The Device.Wireless.Bluetooth and Siri.Remembers.CallHistory streams were also examined and held no written records on that extraction or on the extraction this artifact was built against, so no artifact is added for them here.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Siri.Remembers.InteractionHistory/local/*', '*/Biome/streams/*/Siri.Remembers.InteractionHistory/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'message-circle',
    },
    "macosBiomeSiriMessageHistory": {
        "name": 'Biome Siri Message History',
        "description": 'Records from the Siri.Remembers.MessageHistory Biome stream: record time, the message time, direction as stored, the app bundle ID, chat and message identifiers, and the participants the record pairs by name.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Siri.Remembers.MessageHistory Biome stream. Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Each written record holds one field 1 submessage and, at the top level, repeated field 2 items. Message Time (UTC) is the submessage's field 8, eight bytes read as a little-endian double of seconds since 1 January 1970 UTC; Direction (as stored), Bundle ID, Intent Class (as stored), Chat ID (as stored) and Message GUID (as stored) are its fields 6, 4, 2, 12 and 13, as iLEAPP's biomeSiriRemembersMessageHistory module reads them (Reference: iLEAPP, scripts/artifacts/biomeSiriRemembersMessageHistory.py, https://github.com/abrignoni/iLEAPP/blob/8d6a44d946a2c79cecf196c2599e21e2d42ba2e2/scripts/artifacts/biomeSiriRemembersMessageHistory.py#L148-L154). Participants (as stored) joins each top-level field 2 item as its field 1 name and the field 1 text of its field 2 entity, which that module reads as the parameter names and values (for example sender and recipients); what a value denotes is not established. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 4 rows from one user's local folder, so User and Sync Origin each held one value there, and on those 4 rows Direction (1), Bundle ID (com.apple.MobileSMS), Intent Class (INSendMessageIntent) and Chat ID each held one value; Message Time fell in 2025 on the rows checked.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Siri.Remembers.MessageHistory/local/*', '*/Biome/streams/*/Siri.Remembers.MessageHistory/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'message-2',
    },
    "macosBiomeDKWifi": {
        "name": 'Biome Wi-Fi Connection Events',
        "description": 'Records from the _DKEvent.Wifi.Connection Biome stream: record time, the event time, the event, and the device and GUID as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the _DKEvent.Wifi.Connection Biome stream. Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Event Time (UTC) is field 2, eight bytes read as a little-endian double of seconds since 1 January 2001 UTC (the same reference DLEAPP reports the record time in); Event (as stored) is field 1's field 1, Device (as stored) is field 4's field 3, and GUID (as stored) is field 5, as iLEAPP's biomeWifi module reads them (Reference: iLEAPP, scripts/artifacts/biomeWifi.py, https://github.com/abrignoni/iLEAPP/blob/8d6a44d946a2c79cecf196c2599e21e2d42ba2e2/scripts/artifacts/biomeWifi.py#L116-L124). This is a DuetKnowledge event stream, separate from the Device.Wireless.WiFi stream the Biome Wi-Fi Connections artifact reads. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 37 rows from one user's local folder, so User and Sync Origin each held one value there; Event (as stored) held /wifi/connection on the rows checked and Event Time fell in 2025.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/_DKEvent.Wifi.Connection/local/*', '*/Biome/streams/*/_DKEvent.Wifi.Connection/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'wifi',
    },
    "macosBiomeScreenTimeAppUsage": {
        "name": 'Biome ScreenTime App Usage',
        "description": 'Per-app usage events from the ScreenTime.AppUsage Biome stream: record time, the app bundle ID, and the event code as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Each written record is one protobuf message. Bundle ID is field 3 and Event (as stored) is field 1, as iLEAPP's biomeScreenTimeAppUsage module reads them (Reference: iLEAPP, scripts/artifacts/biomeStreams.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeStreams.py#L249-L259). Event (as stored) held an integer on every record measured and is reported as stored; its meaning is not documented, and iLEAPP's notes for the same stream say the same. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 370 rows from one user's local folder, so User and Sync Origin each held one value there; the rows name 18 distinct bundle IDs, Event (as stored) held 0 on 202 rows and 1 on 168, and Record Time fell in 2025 on every row.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/ScreenTime.AppUsage/local/*', '*/Biome/streams/*/ScreenTime.AppUsage/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'chart-bar',
    },
    "macosBiomeBluetoothUseCase": {
        "name": 'Biome Bluetooth Use Case',
        "description": 'Records from the Device.Wireless.BluetoothUseCase Biome stream: record time and the two integer fields each record holds, reported as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Each written record is one protobuf message holding two integer fields. Field 1 (as stored) is field 1 and Field 2 (as stored) is field 2, both reported as stored: no source documents what either records, so neither is named or interpreted. iLEAPP has no reader for this stream; its biomeBluetooth module reads the separate Device.Wireless.Bluetooth stream, which holds a device MAC and name and is not this one. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 3,707 rows from one user's local folder, so User and Sync Origin each held one value there; Field 1 (as stored) held 0 on 1,849 rows and 1 on 1,858, Field 2 (as stored) held five distinct values (131090 on 3,346 rows, then 65553 on 167, 65544 on 162, 6 on 22 and 22 on 10), and Record Time fell in 2025 on every row.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Device.Wireless.BluetoothUseCase/local/*', '*/Biome/streams/*/Device.Wireless.BluetoothUseCase/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'bluetooth',
    },
    "macosBiomeAppIntent": {
        "name": 'Biome App Intents',
        "description": 'Records from the App.Intent Biome stream: record time, the interaction start time, the app bundle ID, the intent class and action as stored, direction, handling status, and the group and interaction identifiers as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Bundle ID is field 2, Intent Class (as stored) is field 4 and Action (as stored) is field 5, and field 8 is read as an NSKeyedArchiver plist, as iLEAPP's biomeIntents module reads them (Reference: iLEAPP, scripts/artifacts/biomeIntents.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeIntents.py#L94-L127). On every record of the tested extraction the root object of that plist is an INInteraction, and the remaining columns are INInteraction properties that Apple's Intents framework declares in INInteraction.h (read from the macOS 27.0 SDK, where both enumerations below are marked available from macOS 11): Interval Start (UTC) is the start date of dateInterval, Direction is direction, Handling Status is intentHandlingStatus, Group ID (as stored) is groupIdentifier and Interaction ID (as stored) is identifier. Direction and Handling Status show the name INInteraction.h gives the stored number (INInteractionDirection: 0 Unspecified, 1 Outgoing, 2 Incoming; INIntentHandlingStatus: 0 Unspecified, 1 Ready, 2 In Progress, 3 Success, 4 Failure, 5 Deferred To Application, 6 User Confirmation Required) with the number beside it, and a number outside those lists is shown alone. When field 8 is absent or does not read as a keyed archive, those columns are blank and the run log counts the record. The intent's own payload (its backing store bytes) and the intent response are not reported: their content is written by each app, and iLEAPP's notes for the same stream say the fields inside it are not documented. Intent Class (as stored) is not always the class of the archived intent object: on 129 of the 135 records of the tested extraction the archived object is INIntent while field 4 names TodayIntent or TagIntent, and on the other 6 the two are equal. The end date of dateInterval equalled its start on all 135 records of the tested extraction and its duration was 0, so only the start is reported. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 135 rows from one user's local folder, so User and Sync Origin each held one value there. Bundle ID was com.apple.news on 129 rows, com.apple.MobileSMS on 4 and com.apple.parsecd on 2, and Action (as stored) was filled on 6 rows. On the 4 com.apple.MobileSMS rows Direction was Incoming (2), Handling Status was Success (3), Group ID (as stored) was filled, and Record Time was later than Interval Start by up to 2,345,339 seconds (about 27 days); on the other 131 rows Direction and Handling Status were Unspecified (0), Group ID (as stored) was blank and Record Time was within one second of Interval Start. Both times fell in 2025 on every row.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/App.Intent/local/*', '*/Biome/streams/*/App.Intent/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'bolt',
    },
    "macosBiomeDiscoverabilitySignals": {
        "name": 'Biome Discoverability Signals',
        "description": 'Records from the Discoverability.Signals Biome stream: record time, the signal name, its value, and field 3 as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. Signal is field 1 and Value is field 2, as iLEAPP's biomeDiscoverabilitySignals module reads them (Reference: iLEAPP, scripts/artifacts/biomeDiscoverabilitySignals.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeDiscoverabilitySignals.py#L93-L100). Field 3 (as stored) is field 3: that module reads field 3 as a submessage, but on every record of the tested extraction that holds it, field 3 is a plain string, macOS-24E248, and 24E248 is the ProductBuildVersion in that extraction's System/Library/CoreServices/SystemVersion.plist. That module also reads field 4 as a payload; no record of the tested extraction holds a field 4, so it is not reported. What each signal records beyond its name is not established. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 30 rows from one user's local folder, so User and Sync Origin each held one value there; Signal held five distinct names: two in the com.apple.Safari namespace, on 13 rows and on 8, spotlightWillAppear on 6, com.apple.notificationcenter.opened on 2 and com.apple.controlcenter.presented on 1, Value was filled on 23 rows and Field 3 (as stored) on 9, and Record Time fell in 2025 on every row.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Discoverability.Signals/local/*', '*/Biome/streams/*/Discoverability.Signals/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'radio',
    },
    "macosBiomeMediaUsage": {
        "name": 'Biome App Media Usage',
        "description": 'Records from the App.MediaUsage Biome stream: record time and the fields each record holds as stored, including an app bundle ID, URLs where present and a UUID.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. No iLEAPP module reads this stream, so the fields are reported as stored and each column is named for the form of its value, not for a meaning. Field 1 (as stored) is field 1. Bundle ID (as stored) is field 2, which held a reverse-DNS app identifier on every record. URL (as stored) is field 3 and Blob URL (as stored) is field 4, which held an https URL and a blob: URL where present. Field 5 (as stored) is field 5 and UUID (as stored) is field 8. Field 6, read as eight bytes of a little-endian double of seconds since 1 January 1970 UTC, was within 0.012 seconds of Record Time on every record of the tested extraction, so it is not reported separately. What each field records is not established. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 14 rows from one user's local folder, so User and Sync Origin each held one value there; Bundle ID (as stored) was com.apple.AppStore on 10 rows and com.apple.Safari on 4, URL (as stored) and Blob URL (as stored) were filled on the 4 com.apple.Safari rows only, Field 5 (as stored) held 1 on every row, and each of the 7 UUID (as stored) values appeared on two rows with the same Bundle ID (as stored), the earlier with Field 1 (as stored) 1 and the later with 0, between 2 and 301 seconds apart. Record Time fell in 2025 on every row.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/App.MediaUsage/local/*', '*/Biome/streams/*/App.MediaUsage/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'player-play',
    },
    "macosBiomeSafariAutoPlay": {
        "name": 'Biome Safari AutoPlay',
        "description": 'Records from the Safari.AutoPlay Biome stream: record time, a host name, and fields 3, 4 and 5 as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Each file in the stream's local folder, and in each folder under its remote folder, other than one whose name begins with a dot, is read as a SEGB file with the vendored ccl_segb package, one row per record the file marks as written whose data ccl_segb can still read, and each such record is read as one protobuf message whose fields are taken by number without a schema; a record that does not read as one is counted in the run log and not reported. Records the file does not mark as written are not reported; those ccl_segb returns are counted in the run log, and it returns none of the entries a version 2 file marks as empty. Files under a tombstone folder are not read. Record Time (UTC) is the time the SEGB file stores with each record, which ccl_segb reads from a version 2 file as seconds since 00:00:00 on 1 January 2001 and DLEAPP reports as UTC (Reference: CCL Solutions Group, ccl-segb, ccl_segb/ccl_segb2.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142, and ccl_segb/ccl_segb_common.py, https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb_common.py#L5-L21); every file of the stream on the tested extraction is SEGB version 2. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Sync Origin is Local for the local folder, or Remote with the name of the folder under remote the record came from. Record Offset is where the record begins in its file: in a version 2 file that is the record's 8-byte header, which starts with its stored CRC, and the record's data begins 8 bytes later. When a logical extraction holds the stream under Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and bytes in both is reported once, and the run log counts the repeats. On dleapp_macos_bigsur no Biome stream folder exists. No iLEAPP module reads this stream, so the fields are reported as stored and each column is named for the form of its value, not for a meaning. Host (as stored) is field 1, which held a host name on every record. Field 3 (as stored), Field 4 (as stored) and Field 5 (as stored) are fields 3, 4 and 5. Field 2, read as eight bytes of a little-endian double of seconds since 1 January 1970 UTC, was the first half-hour boundary after Record Time on every record of the tested extraction, so it is not reported separately. What each field records is not established. On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the stream gives 8 rows from one user's local folder, so User and Sync Origin each held one value there; Host (as stored) held three distinct host names, Field 3 (as stored), Field 4 (as stored) and Field 5 (as stored) held 2, US and 0 on every row, and Record Time fell in 2025 on every row.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/streams/*/Safari.AutoPlay/local/*', '*/Biome/streams/*/Safari.AutoPlay/remote/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'brand-safari',
    },
}

import plistlib
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, webkit_timestampsconv
from scripts.macos_biome import double, fields, first, stream_records, text
from scripts.macos_plists import resolve_keyed_archive

def _as_stored(value):
    return '' if value is None else str(value)


def _read(context, label, row_for):
    """(rows, source path) for one stream: one row per written record that reads as a message."""
    records, sources = stream_records(context, label)
    rows = []
    unreadable = 0
    for record in records:
        try:
            found = fields(record.data)
        except ValueError:
            unreadable += 1
            continue
        rows.append((record.time,) + row_for(found) + (record.user, record.origin, record.source,
                                                        record.offset))
    if unreadable:
        logfunc(f'{label}: {unreadable} written record(s) did not read as a protobuf message and '
                'are not reported')
    rows.sort(key=lambda row: (row[0], str(row[-2]), row[-1]))
    return rows, '\n'.join(sources)


@artifact_processor
def macosBiomeAppInFocus(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Bundle ID', 'Field 3 (as stored)',
                    'Transition Reason (as stored)', 'App Version (as stored)', 'Bundle Version (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome App In Focus', lambda f: (
        text(first(f, 6)), _as_stored(first(f, 3)), text(first(f, 1)), text(first(f, 9)),
        text(first(f, 10))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeAppWebUsage(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'URL', 'Domain', 'Bundle ID', 'GUID (as stored)',
                    'Field 3 (as stored)', 'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome App Web Usage', lambda f: (
        text(first(f, 4)), text(first(f, 5)), text(first(f, 6)), text(first(f, 1)),
        _as_stored(first(f, 3))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeSafariNavigations(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'URL', 'Host', 'Country Code (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Safari Navigations', lambda f: (
        text(first(f, 8)), text(first(f, 1)), text(first(f, 5))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeNotificationUsage(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Bundle ID', 'UUID (as stored)', 'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Notification Usage', lambda f: (
        text(first(f, 4)), text(first(f, 5))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeNowPlaying(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Title', 'Artist',
                    'Bundle ID or Process (as stored)', 'Field 3 (as stored)', 'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Now Playing', lambda f: (
        text(first(f, 8)), text(first(f, 5)), text(first(f, 15)), _as_stored(first(f, 3))))
    return data_headers, rows, source


def _wifi_status(value):
    if value == 1:
        return 'Connected'
    if value == 0:
        return 'Disconnected'
    return _as_stored(value) + ' (as stored)' if value is not None else ''


@artifact_processor
def macosBiomeWifi(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'SSID', 'Status', 'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Wi-Fi Connections', lambda f: (
        text(first(f, 1)), _wifi_status(first(f, 2))))
    return data_headers, rows, source


def _submessage(value):
    """Re-parse a length-delimited value as a nested message, or {} on failure."""
    if isinstance(value, (bytes, bytearray)):
        try:
            return fields(value)
        except ValueError:
            return {}
    return {}


def _unix_double(value):
    """An 8-byte little-endian double read as seconds since 1970 UTC, or ''."""
    seconds = double(value)
    if seconds is None:
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _mac2001_double(value):
    """An 8-byte little-endian double read as seconds since 2001 UTC, or ''."""
    seconds = double(value)
    if seconds is None:
        return ''
    try:
        return webkit_timestampsconv(seconds)
    except (OverflowError, OSError, ValueError):
        return ''


def _participants(found):
    """Join each top-level field 2 item as 'name: value' from its field 1 and field 2 entity."""
    parts = []
    for item in found.get(2, []):
        entry = _submessage(item)
        name = text(first(entry, 1))
        value = text(first(_submessage(first(entry, 2)), 1))
        if name or value:
            parts.append(f'{name}: {value}' if name else value)
    return '; '.join(parts)


@artifact_processor
def macosBiomeSiriInteractionHistory(context):
    data_headers = (('Record Time (UTC)', 'datetime'), ('Interaction Time (UTC)', 'datetime'),
                    'Bundle ID', 'Intent Class (as stored)', 'GUID (as stored)',
                    'Interaction GUID (as stored)', 'User', 'Sync Origin',
                    'Source File', 'Record Offset')

    def row_for(f):
        meta = _submessage(first(f, 1))
        return (_unix_double(first(meta, 8)), text(first(meta, 4)), text(first(meta, 2)),
                text(first(meta, 1)), text(first(meta, 13)))
    rows, source = _read(context, 'Biome Siri Interaction History', row_for)
    return data_headers, rows, source


@artifact_processor
def macosBiomeSiriMessageHistory(context):
    data_headers = (('Record Time (UTC)', 'datetime'), ('Message Time (UTC)', 'datetime'),
                    'Direction (as stored)', 'Bundle ID', 'Intent Class (as stored)',
                    'Chat ID (as stored)', 'Message GUID (as stored)', 'Participants (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')

    def row_for(f):
        meta = _submessage(first(f, 1))
        return (_unix_double(first(meta, 8)), _as_stored(first(meta, 6)), text(first(meta, 4)),
                text(first(meta, 2)), text(first(meta, 12)), text(first(meta, 13)),
                _participants(f))
    rows, source = _read(context, 'Biome Siri Message History', row_for)
    return data_headers, rows, source


@artifact_processor
def macosBiomeDKWifi(context):
    data_headers = (('Record Time (UTC)', 'datetime'), ('Event Time (UTC)', 'datetime'),
                    'Event (as stored)', 'Device (as stored)', 'GUID (as stored)', 'User',
                    'Sync Origin', 'Source File', 'Record Offset')

    def row_for(f):
        return (_mac2001_double(first(f, 2)), text(first(_submessage(first(f, 1)), 1)),
                text(first(_submessage(first(f, 4)), 3)), text(first(f, 5)))
    rows, source = _read(context, 'Biome Wi-Fi Connection Events', row_for)
    return data_headers, rows, source


@artifact_processor
def macosBiomeScreenTimeAppUsage(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Bundle ID', 'Event (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome ScreenTime App Usage', lambda f: (
        text(first(f, 3)), text(first(f, 1))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeBluetoothUseCase(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Field 1 (as stored)', 'Field 2 (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Bluetooth Use Case', lambda f: (
        _as_stored(first(f, 1)), _as_stored(first(f, 2))))
    return data_headers, rows, source


_DIRECTIONS = {0: 'Unspecified', 1: 'Outgoing', 2: 'Incoming'}
_HANDLING_STATUSES = {0: 'Unspecified', 1: 'Ready', 2: 'In Progress', 3: 'Success', 4: 'Failure',
                      5: 'Deferred To Application', 6: 'User Confirmation Required'}


def _named(value, names):
    """The INInteraction.h name for a stored number, with the number beside it."""
    if isinstance(value, bool) or not isinstance(value, int):
        return ''
    name = names.get(value)
    return f'{name} ({value})' if name else str(value)


def _interaction(found):
    """The INInteraction archived in field 8 as a plain dict, or None."""
    raw = first(found, 8)
    if not isinstance(raw, (bytes, bytearray)):
        return None
    try:
        archive = plistlib.loads(bytes(raw))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
        return None
    root = resolve_keyed_archive(archive)
    return root if isinstance(root, dict) else None


@artifact_processor
def macosBiomeAppIntent(context):
    data_headers = (('Record Time (UTC)', 'datetime'), ('Interval Start (UTC)', 'datetime'), 'Bundle ID',
                    'Intent Class (as stored)', 'Action (as stored)', 'Direction', 'Handling Status',
                    'Group ID (as stored)', 'Interaction ID (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    unread = []

    def row_for(f):
        interaction = _interaction(f)
        if interaction is None:
            unread.append(1)
            interaction = {}
        interval = interaction.get('dateInterval')
        start = interval.get('NS.startDate') if isinstance(interval, dict) else None
        group, identifier = interaction.get('groupIdentifier'), interaction.get('identifier')
        return (start if isinstance(start, datetime) else '', text(first(f, 2)), text(first(f, 4)),
                text(first(f, 5)), _named(interaction.get('direction'), _DIRECTIONS),
                _named(interaction.get('intentHandlingStatus'), _HANDLING_STATUSES),
                group if isinstance(group, str) else '', identifier if isinstance(identifier, str) else '')

    rows, source = _read(context, 'Biome App Intents', row_for)
    if unread:
        logfunc(f'Biome App Intents: field 8 of {len(unread)} record(s) did not read as a keyed '
                'archive; their interaction columns are blank')
    return data_headers, rows, source


@artifact_processor
def macosBiomeDiscoverabilitySignals(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Signal', 'Value', 'Field 3 (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Discoverability Signals', lambda f: (
        text(first(f, 1)), text(first(f, 2)), text(first(f, 3))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeMediaUsage(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Field 1 (as stored)', 'Bundle ID (as stored)',
                    'URL (as stored)', 'Blob URL (as stored)', 'Field 5 (as stored)', 'UUID (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome App Media Usage', lambda f: (
        _as_stored(first(f, 1)), text(first(f, 2)), text(first(f, 3)), text(first(f, 4)),
        _as_stored(first(f, 5)), text(first(f, 8))))
    return data_headers, rows, source


@artifact_processor
def macosBiomeSafariAutoPlay(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Host (as stored)', 'Field 3 (as stored)',
                    'Field 4 (as stored)', 'Field 5 (as stored)',
                    'User', 'Sync Origin', 'Source File', 'Record Offset')
    rows, source = _read(context, 'Biome Safari AutoPlay', lambda f: (
        text(first(f, 1)), _as_stored(first(f, 3)), text(first(f, 4)), _as_stored(first(f, 5))))
    return data_headers, rows, source
