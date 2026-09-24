"""Records from six macOS Biome streams, for DLEAPP.

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
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the App.InFocus Biome stream. Each file in the stream's local folder, and in "
                 "each folder under its remote folder, is read as a SEGB file with the vendored "
                 "ccl_segb package, one row per record the file marks as written, and each such record"
                 " is read as one protobuf message whose fields are taken by number without a schema; "
                 "a record that does not read as one is counted in the run log and not reported. "
                 "Records the file does not mark as written are counted in the run log and not "
                 "reported, and files under a tombstone folder are not read. Record Time (UTC) is the "
                 "time the SEGB file stores with each record, which ccl_segb reads from a version 2 "
                 "file as seconds since 00:00:00 UTC on 1 January 2001 (Reference: CCL Solutions "
                 "Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the "
                 "folder name under Users. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is the "
                 "record's data offset in its file. When a logical extraction holds the stream under "
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
                 "from one of 3 remote folders; the other 2 hold only records not marked as written. "
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
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the App.WebUsage Biome stream. Each file in the stream's local folder, and in "
                 "each folder under its remote folder, is read as a SEGB file with the vendored "
                 "ccl_segb package, one row per record the file marks as written, and each such record"
                 " is read as one protobuf message whose fields are taken by number without a schema; "
                 "a record that does not read as one is counted in the run log and not reported. "
                 "Records the file does not mark as written are counted in the run log and not "
                 "reported, and files under a tombstone folder are not read. Record Time (UTC) is the "
                 "time the SEGB file stores with each record, which ccl_segb reads from a version 2 "
                 "file as seconds since 00:00:00 UTC on 1 January 2001 (Reference: CCL Solutions "
                 "Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the "
                 "folder name under Users. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is the "
                 "record's data offset in its file. When a logical extraction holds the stream under "
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
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Safari.Navigations Biome stream. Each file in the stream's local folder, "
                 "and in each folder under its remote folder, is read as a SEGB file with the vendored"
                 " ccl_segb package, one row per record the file marks as written, and each such "
                 "record is read as one protobuf message whose fields are taken by number without a "
                 "schema; a record that does not read as one is counted in the run log and not "
                 "reported. Records the file does not mark as written are counted in the run log and "
                 "not reported, and files under a tombstone folder are not read. Record Time (UTC) is "
                 "the time the SEGB file stores with each record, which ccl_segb reads from a version "
                 "2 file as seconds since 00:00:00 UTC on 1 January 2001 (Reference: CCL Solutions "
                 "Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the "
                 "folder name under Users. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is the "
                 "record's data offset in its file. When a logical extraction holds the stream under "
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
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Notification.Usage Biome stream. Each file in the stream's local folder, "
                 "and in each folder under its remote folder, is read as a SEGB file with the vendored"
                 " ccl_segb package, one row per record the file marks as written, and each such "
                 "record is read as one protobuf message whose fields are taken by number without a "
                 "schema; a record that does not read as one is counted in the run log and not "
                 "reported. Records the file does not mark as written are counted in the run log and "
                 "not reported, and files under a tombstone folder are not read. Record Time (UTC) is "
                 "the time the SEGB file stores with each record, which ccl_segb reads from a version "
                 "2 file as seconds since 00:00:00 UTC on 1 January 2001 (Reference: CCL Solutions "
                 "Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the "
                 "folder name under Users. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is the "
                 "record's data offset in its file. When a logical extraction holds the stream under "
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
                 " time in field 2 of the Biome record; db2/db holds 2 records there. Field 2, read as"
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
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Media.NowPlaying Biome stream. Each file in the stream's local folder, and"
                 " in each folder under its remote folder, is read as a SEGB file with the vendored "
                 "ccl_segb package, one row per record the file marks as written, and each such record"
                 " is read as one protobuf message whose fields are taken by number without a schema; "
                 "a record that does not read as one is counted in the run log and not reported. "
                 "Records the file does not mark as written are counted in the run log and not "
                 "reported, and files under a tombstone folder are not read. Record Time (UTC) is the "
                 "time the SEGB file stores with each record, which ccl_segb reads from a version 2 "
                 "file as seconds since 00:00:00 UTC on 1 January 2001 (Reference: CCL Solutions "
                 "Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the "
                 "folder name under Users. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is the "
                 "record's data offset in its file. When a logical extraction holds the stream under "
                 "Users/ and under System/Volumes/Data/Users/, a record with the same offset, time and"
                 " bytes in both is reported once, and the run log counts the repeats. On "
                 "dleapp_macos_bigsur no Biome stream folder exists. Title, Artist and Bundle ID or "
                 "Process (as stored) are fields 8, 5 and 15, as iLEAPP's biomeNowplaying module reads"
                 " them as title, artist and bundle ID (Reference: iLEAPP, "
                 "scripts/artifacts/biomeNowplaying.py, "
                 "https://github.com/abrignoni/iLEAPP/blob/f4af0947555d8bbf894975aab1c9e19ab3a05903/scripts/artifacts/biomeNowplaying.py#L119-L127),"
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
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Device.Wireless.WiFi Biome stream. Each file in the stream's local folder,"
                 " and in each folder under its remote folder, is read as a SEGB file with the "
                 "vendored ccl_segb package, one row per record the file marks as written, and each "
                 "such record is read as one protobuf message whose fields are taken by number without"
                 " a schema; a record that does not read as one is counted in the run log and not "
                 "reported. Records the file does not mark as written are counted in the run log and "
                 "not reported, and files under a tombstone folder are not read. Record Time (UTC) is "
                 "the time the SEGB file stores with each record, which ccl_segb reads from a version "
                 "2 file as seconds since 00:00:00 UTC on 1 January 2001 (Reference: CCL Solutions "
                 "Group, ccl-segb, ccl_segb/ccl_segb2.py, "
                 "https://github.com/cclgroupltd/ccl-segb/blob/23c3f7d3d969a79627b738ba0a2486c31d675753/ccl_segb/ccl_segb2.py#L133-L142);"
                 " every file of the stream on the tested extraction is SEGB version 2. User is the "
                 "folder name under Users. Sync Origin is Local for the local folder, or Remote with "
                 "the name of the folder under remote the record came from. Record Offset is the "
                 "record's data offset in its file. When a logical extraction holds the stream under "
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
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_biome import fields, first, stream_records, text

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
