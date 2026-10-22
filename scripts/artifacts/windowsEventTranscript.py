"""Windows Diagnostic Data Viewer database (EventTranscript.db) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

When the Diagnostic Data Viewer setting is on, Windows keeps a local copy of its
diagnostic events in ProgramData/Microsoft/Diagnosis/EventTranscript/EventTranscript.db.
Each row of events_persisted is one event: a FILETIME timestamp, the full event
name, the logging binary, a user SID and the event's JSON payload. The tag tables
put each event name in one or more of the categories the viewer shows.

One artifact lists every event with its payload as stored. Four more read the
payload of event families whose field names are documented or have been
described in published research: Microsoft Edge HistoryJournal events, app
interactivity summaries, and application and PnP device inventory changes.
Citations are in the notes.
"""

__artifacts_v2__ = {
    "eventTranscriptEvents": {
        "name": 'Diagnostic Data Events',
        "description": 'The events in the Windows Diagnostic Data Viewer database (EventTranscript.db), one row each, '
                       'with the time, event name, categories, producer, logging binary, user SID and JSON payload as '
                       'stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Read from ProgramData\\Microsoft\\Diagnosis\\EventTranscript\\EventTranscript.db with its '
                 'write-ahead log when one is beside it; Source File names the database each row came from, since '
                 'the declared path can match one copy per volume. Windows keeps this database while the Turn on '
                 'the Diagnostic Data Viewer option (Settings, Privacy & security, Diagnostics & feedback) is on; '
                 'Microsoft says turning it off clears the stored data, that by default up to 1 GB or 30 days is '
                 'kept with the oldest dropped first, and that an event shown may still be queued and not yet '
                 "uploaded (Microsoft, 'Diagnostic Data Viewer', ms.date 2026-02-12, "
                 'https://learn.microsoft.com/en-us/windows/privacy/diagnostic-data-viewer-overview), so a row '
                 "does not show that the event reached Microsoft. The location follows Andrew Rathbun's "
                 'EventTranscript.db research '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L17), '
                 'which Abhiram Kumar credits to Andrew Rathbun and Josh Mitchell '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/README.md#L93), '
                 'and the tag names come from its Tag Descriptions table '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L21-L32); '
                 'the other tables are read by name from the database schema. Timestamp (UTC) is '
                 "events_persisted.timestamp read as a FILETIME value, as Andrew Rathbun's SQLECmd map "
                 '(https://github.com/EricZimmerman/SQLECmd/blob/5839a5dbbc24285f8a0dfe769470d73a70a64d4b/SQLMap/Maps/Windows_EventTranscriptDB_NoDataSampling.smap#L215) '
                 'and plaso '
                 '(https://github.com/log2timeline/plaso/blob/f663c00cbc33ff930dd4f1e6297e4840192b5d39/plaso/parsers/sqlite_plugins/windows_eventtranscript.py#L172-L174) '
                 "read it; on plaso_testdata_f951fc6 it equalled the payload's own time field to the 100 "
                 'nanoseconds on all 2,526 rows. Validated on one database only, plaso_testdata_f951fc6 from '
                 "plaso's test data, whose origin the source does not state; every payload's ext.os.ver begins "
                 '10.0.19041.1165, and the database is in WAL mode with no -wal, so it was read alone. None of '
                 'the other registered Windows corpus images checked holds the database; the EventTranscript '
                 'folder is present and empty on seven of them. One row per events_persisted row. Diagnostic Data '
                 'Categories joins event_tags to tag_descriptions on full_event_name_hash, as the SQLECmd map '
                 'does '
                 '(https://github.com/EricZimmerman/SQLECmd/blob/5839a5dbbc24285f8a0dfe769470d73a70a64d4b/SQLMap/Maps/Windows_EventTranscriptDB_NoDataSampling.smap#L235-L236), '
                 'and lists each tag ID once, in tag ID order, by its stored tag name (names from more than one '
                 "locale joined with ' / '); a tag ID with no stored description is shown as 'tag <n> (no "
                 "description stored)', a case the sample does not have. On plaso_testdata_f951fc6 "
                 'tag_descriptions held 6 names and 9 of the 2,526 rows had no tag. Producer is '
                 'producers.producer_id_text and Provider Group GUID is provider_groups.group_guid. Trailing NUL '
                 'characters are removed from Friendly Logging Binary Name and nothing else is changed; on the '
                 'sample 1,397 rows ended in exactly one NUL and none held a NUL elsewhere. User SID is as stored '
                 'and was empty on 570 rows. Is Core, Event Keywords and Compressed Payload Size are the stored '
                 'integers; the sources cited here do not document their meaning (the SQLECmd map shows is_core 0 '
                 'and 1 as No and Yes). Payload is the stored JSON text; Rathbun and Mitchell list its top-level '
                 'keys as ver, name, time, iKey, ext and data '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L52-L60), '
                 'the keys every sample payload held. The other Diagnostic Data artifacts read named fields from '
                 'it. Event families they do not read stay only here, among them WlanMSM.WirelessScanResults, '
                 'Microsoft.OneCore.NetworkingTriage.GetConnected.WiFiConnectedEvent, '
                 "Microsoft.Windows.SRUM.Telemetry.AppTimelines and Census.Userdefault, which Abhiram Kumar's "
                 'EventTranscriptParser reads '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/EventTranscriptParser.py#L104-L230); '
                 'the sample holds none of the first three and one Census.Userdefault event. Not reported: '
                 'full_event_name_hash (the join key), extra1 to extra3 (empty on every sample row), and the '
                 'categories and event_categories tables, which were empty on the sample, so how they are filled '
                 'is not established.',
        "paths": ('*/ProgramData/Microsoft/Diagnosis/EventTranscript/EventTranscript.db*',),
        "output_types": "standard",
        "artifact_icon": "activity",
        "sample_data": {
            "af_case2_win10": 'Windows 10 1809 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "alihadi_threatsim_server2019": 'Windows Server 2019 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "hexordia_mvs2025_win11": 'Windows 11 24H2 build 26100 | 0 rows (the EventTranscript folder holds no database)',
            "lonewolf_win10": 'Windows 10 Education build 16299 | 0 rows (the EventTranscript folder holds no database)',
            "ou_ransomware_server2022": 'Windows Server 2022 build 20348 | 0 rows (the EventTranscript folder holds no database)',
            "pc_mus_001_win11": 'Windows 11 22H2 build 22621 | 0 rows (the EventTranscript folder holds no database)',
            "plaso_testdata_f951fc6": 'payload ext.os.ver 10.0.19041.1165 | 2,526 rows (the database placed at its ProgramData path in a derived zip)',
            "szechuan_win10": 'Windows 10 2004 build 19041 | 0 rows (the EventTranscript folder holds no database)',
        },
    },
    "eventTranscriptEdgeHistory": {
        "name": 'Diagnostic Data Edge HistoryJournal Events',
        "description": 'Microsoft Edge HistoryJournal events in the Windows Diagnostic Data Viewer database that carry '
                       'a navigation URL, a referrer URL or a page title, with the tab ID as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Read from ProgramData\\Microsoft\\Diagnosis\\EventTranscript\\EventTranscript.db with its '
                 'write-ahead log when one is beside it; Source File names the database each row came from, since '
                 'the declared path can match one copy per volume. Windows keeps this database while the Turn on '
                 'the Diagnostic Data Viewer option (Settings, Privacy & security, Diagnostics & feedback) is on; '
                 'Microsoft says turning it off clears the stored data, that by default up to 1 GB or 30 days is '
                 'kept with the oldest dropped first, and that an event shown may still be queued and not yet '
                 "uploaded (Microsoft, 'Diagnostic Data Viewer', ms.date 2026-02-12, "
                 'https://learn.microsoft.com/en-us/windows/privacy/diagnostic-data-viewer-overview), so a row '
                 "does not show that the event reached Microsoft. The location follows Andrew Rathbun's "
                 'EventTranscript.db research '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L17), '
                 'which Abhiram Kumar credits to Andrew Rathbun and Josh Mitchell '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/README.md#L93), '
                 'and the tag names come from its Tag Descriptions table '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L21-L32); '
                 'the other tables are read by name from the database schema. Timestamp (UTC) is '
                 "events_persisted.timestamp read as a FILETIME value, as Andrew Rathbun's SQLECmd map "
                 '(https://github.com/EricZimmerman/SQLECmd/blob/5839a5dbbc24285f8a0dfe769470d73a70a64d4b/SQLMap/Maps/Windows_EventTranscriptDB_NoDataSampling.smap#L215) '
                 'and plaso '
                 '(https://github.com/log2timeline/plaso/blob/f663c00cbc33ff930dd4f1e6297e4840192b5d39/plaso/parsers/sqlite_plugins/windows_eventtranscript.py#L172-L174) '
                 "read it; on plaso_testdata_f951fc6 it equalled the payload's own time field to the 100 "
                 'nanoseconds on all 2,526 rows. Validated on one database only, plaso_testdata_f951fc6 from '
                 "plaso's test data, whose origin the source does not state; every payload's ext.os.ver begins "
                 '10.0.19041.1165, and the database is in WAL mode with no -wal, so it was read alone. None of '
                 'the other registered Windows corpus images checked holds the database; the EventTranscript '
                 'folder is present and empty on seven of them. Rows are events whose name contains '
                 "'.Microsoft.WebBrowser.HistoryJournal.' and whose payload data holds a non-empty navigationUrl, "
                 'referUrl or PageTitle; Event is the part of the name after HistoryJournal. Navigation URL '
                 '(navigationUrl), Referrer URL (referUrl), Page Title (PageTitle), Tab ID (TabId), HTTP Status '
                 'Code (HttpStatusCode), Correlation GUID (CorrelationGuid) and data.Timestamp are those payload '
                 'keys as stored, with data.Timestamp read as an ISO 8601 UTC time. Microsoft says optional '
                 "diagnostic data includes browsing history in Microsoft browsers (Microsoft, 'Configure Windows "
                 "diagnostic data in your organization', ms.date 2025-09-11, "
                 'https://learn.microsoft.com/en-us/windows/privacy/configure-windows-diagnostic-data-in-your-organization), '
                 "and Abhiram Kumar's EventTranscriptParser builds its browsing history output from navigationUrl "
                 'as the URL, data.Timestamp as the time and referUrl as the referring URL '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/EventTranscriptParser.py#L22-L33); '
                 'this artifact names the keys and does not attach those meanings. On plaso_testdata_f951fc6, 392 '
                 'of 679 HistoryJournal rows qualified (HJ_BeforeNavigateExtended 128, '
                 'HJ_NavigateCompleteExtended 128, HJ_HistoryAddUrlEx 54, HJ_HistoryAddUrl 53, HJ_PageContentInfo '
                 '29) and data.Timestamp was 0.0004 to 182.4 seconds earlier than Timestamp (UTC). '
                 'HJ_HistoryAddUrlEx rows held a Page Title and no URL, HJ_HistoryAddUrl rows a URL and an empty '
                 'title, and 52 of the 54 HJ_HistoryAddUrlEx rows shared a Correlation GUID with an '
                 'HJ_HistoryAddUrl row; that grouping is observed on this sample only. User SID held one value on '
                 'all 392 rows, the only S-1-5-21 SID in the database. All 679 HistoryJournal rows had logging '
                 'binary msedge.exe and producer Microsoft Edge; those columns are in Diagnostic Data Events, as '
                 'are the 287 HistoryJournal rows with none of these values: 120 navigation events whose '
                 'navigationUrl is empty, 6 HJ_HistoryAddUrl rows with an empty URL, and the W3cNavTiming, '
                 'element click, tab, preference and browser information events. Not read: the older '
                 'Microsoft.Windows.App.Browser.HJ_* events, which Rathbun and Mitchell show with the URL '
                 'hex-encoded in navigationUrlBytes '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L222-L245); '
                 'the sample holds none.',
        "paths": ('*/ProgramData/Microsoft/Diagnosis/EventTranscript/EventTranscript.db*',),
        "output_types": "standard",
        "artifact_icon": "globe",
        "sample_data": {
            "af_case2_win10": 'Windows 10 1809 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "alihadi_threatsim_server2019": 'Windows Server 2019 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "hexordia_mvs2025_win11": 'Windows 11 24H2 build 26100 | 0 rows (the EventTranscript folder holds no database)',
            "lonewolf_win10": 'Windows 10 Education build 16299 | 0 rows (the EventTranscript folder holds no database)',
            "ou_ransomware_server2022": 'Windows Server 2022 build 20348 | 0 rows (the EventTranscript folder holds no database)',
            "pc_mus_001_win11": 'Windows 11 22H2 build 22621 | 0 rows (the EventTranscript folder holds no database)',
            "plaso_testdata_f951fc6": 'payload ext.os.ver 10.0.19041.1165 | 392 rows (the database placed at its ProgramData path in a derived zip)',
            "szechuan_win10": 'Windows 10 2004 build 19041 | 0 rows (the EventTranscript folder holds no database)',
        },
    },
    "eventTranscriptAppInteractivity": {
        "name": 'Diagnostic Data App Interactivity',
        "description": 'Win32kTraceLogging app interactivity events in the Windows Diagnostic Data Viewer database: the '
                       'app, the aggregation period and the focus, activity and input counters the event stores.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Read from ProgramData\\Microsoft\\Diagnosis\\EventTranscript\\EventTranscript.db with its '
                 'write-ahead log when one is beside it; Source File names the database each row came from, since '
                 'the declared path can match one copy per volume. Windows keeps this database while the Turn on '
                 'the Diagnostic Data Viewer option (Settings, Privacy & security, Diagnostics & feedback) is on; '
                 'Microsoft says turning it off clears the stored data, that by default up to 1 GB or 30 days is '
                 'kept with the oldest dropped first, and that an event shown may still be queued and not yet '
                 "uploaded (Microsoft, 'Diagnostic Data Viewer', ms.date 2026-02-12, "
                 'https://learn.microsoft.com/en-us/windows/privacy/diagnostic-data-viewer-overview), so a row '
                 "does not show that the event reached Microsoft. The location follows Andrew Rathbun's "
                 'EventTranscript.db research '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L17), '
                 'which Abhiram Kumar credits to Andrew Rathbun and Josh Mitchell '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/README.md#L93), '
                 'and the tag names come from its Tag Descriptions table '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L21-L32); '
                 'the other tables are read by name from the database schema. Timestamp (UTC) is '
                 "events_persisted.timestamp read as a FILETIME value, as Andrew Rathbun's SQLECmd map "
                 '(https://github.com/EricZimmerman/SQLECmd/blob/5839a5dbbc24285f8a0dfe769470d73a70a64d4b/SQLMap/Maps/Windows_EventTranscriptDB_NoDataSampling.smap#L215) '
                 'and plaso '
                 '(https://github.com/log2timeline/plaso/blob/f663c00cbc33ff930dd4f1e6297e4840192b5d39/plaso/parsers/sqlite_plugins/windows_eventtranscript.py#L172-L174) '
                 "read it; on plaso_testdata_f951fc6 it equalled the payload's own time field to the 100 "
                 'nanoseconds on all 2,526 rows. Validated on one database only, plaso_testdata_f951fc6 from '
                 "plaso's test data, whose origin the source does not state; every payload's ext.os.ver begins "
                 '10.0.19041.1165, and the database is in WAL mode with no -wal, so it was read alone. None of '
                 'the other registered Windows corpus images checked holds the database; the EventTranscript '
                 'folder is present and empty on seven of them. Rows are '
                 'Win32kTraceLogging.AppInteractivitySummary and Win32kTraceLogging.AppInteractivity events, the '
                 "two Costas Katsavounidis's AppInteractivity.sql reads "
                 '(https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/AppInteractivity.sql#L1-L3). '
                 'The sample holds only AppInteractivitySummary events, so Event Name held one value on all 152 '
                 "rows and the AppInteractivity name is read but unexercised. Field meanings are that query's "
                 "comments, which cite Microsoft's enhanced diagnostic data events page "
                 '(https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/AppInteractivity.sql#L7), '
                 'a page that on 2026-10-22 redirected to a Microsoft Tech Community post on the retirement of '
                 'Desktop Analytics: AggregationStartTime the start date and time of the aggregation, '
                 'AggregationDurationMS the actual duration of the aggregation period in milliseconds, '
                 'FocusLostCount the number of times the app lost focus during the period, MouseInputSec the '
                 'seconds with mouse input, InFocusDurationMS the time the application had focus, '
                 'UserActiveDurationMS the time the user was active including all input methods and '
                 'UserOrDisplayActiveDurationMS the time the user was using the display '
                 '(https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/AppInteractivity.sql#L23-L24, '
                 'https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/AppInteractivity.sql#L40, '
                 'https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/AppInteractivity.sql#L67-L71). '
                 'They were not checked against a Microsoft page. Keyboard Input (KeyboardInputSec), App ID '
                 '(AppId), App Version (AppVersion) and App Session ID (AppSessionId) are reported as stored, by '
                 'key name. Aggregation Start Time is read as an ISO 8601 UTC time and a value that is not one is '
                 'shown as stored; on plaso_testdata_f951fc6 all 152 were read, and Timestamp (UTC) was within '
                 "2.4 seconds of Aggregation Start Time plus Aggregation Duration on every row. App ID held 'W:', "
                 "two hexadecimal identifiers and an executable name on 127 rows and 'U:' with a package and app "
                 "name on 25; the query reads the 'W:' identifiers as Amcache's ProgramId and FileId "
                 '(https://github.com/kacos2000/Queries/blob/e2698f6583ea2f8bc415f2e55dc0786ab7d58b9c/AppInteractivity.sql#L76-L84), '
                 'which is not checked here because the sample has no Amcache. A row records a period over which '
                 'the counters were aggregated for the app; on its own it does not give the time the program '
                 "started. The event's other counters (touch, pen, audio, window and monitor sizes and more) are "
                 'in its payload in Diagnostic Data Events.',
        "paths": ('*/ProgramData/Microsoft/Diagnosis/EventTranscript/EventTranscript.db*',),
        "output_types": "standard",
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": 'Windows 10 1809 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "alihadi_threatsim_server2019": 'Windows Server 2019 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "hexordia_mvs2025_win11": 'Windows 11 24H2 build 26100 | 0 rows (the EventTranscript folder holds no database)',
            "lonewolf_win10": 'Windows 10 Education build 16299 | 0 rows (the EventTranscript folder holds no database)',
            "ou_ransomware_server2022": 'Windows Server 2022 build 20348 | 0 rows (the EventTranscript folder holds no database)',
            "pc_mus_001_win11": 'Windows 11 22H2 build 22621 | 0 rows (the EventTranscript folder holds no database)',
            "plaso_testdata_f951fc6": 'payload ext.os.ver 10.0.19041.1165 | 152 rows (the database placed at its ProgramData path in a derived zip)',
            "szechuan_win10": 'Windows 10 2004 build 19041 | 0 rows (the EventTranscript folder holds no database)',
        },
    },
    "eventTranscriptAppInventory": {
        "name": 'Diagnostic Data Application Inventory Changes',
        "description": 'InventoryApplicationAdd and InventoryApplicationRemove events in the Windows Diagnostic Data '
                       'Viewer database, with the application name, version, publisher, folder and install date the Add '
                       'event stores.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Read from ProgramData\\Microsoft\\Diagnosis\\EventTranscript\\EventTranscript.db with its '
                 'write-ahead log when one is beside it; Source File names the database each row came from, since '
                 'the declared path can match one copy per volume. Windows keeps this database while the Turn on '
                 'the Diagnostic Data Viewer option (Settings, Privacy & security, Diagnostics & feedback) is on; '
                 'Microsoft says turning it off clears the stored data, that by default up to 1 GB or 30 days is '
                 'kept with the oldest dropped first, and that an event shown may still be queued and not yet '
                 "uploaded (Microsoft, 'Diagnostic Data Viewer', ms.date 2026-02-12, "
                 'https://learn.microsoft.com/en-us/windows/privacy/diagnostic-data-viewer-overview), so a row '
                 "does not show that the event reached Microsoft. The location follows Andrew Rathbun's "
                 'EventTranscript.db research '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L17), '
                 'which Abhiram Kumar credits to Andrew Rathbun and Josh Mitchell '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/README.md#L93), '
                 'and the tag names come from its Tag Descriptions table '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L21-L32); '
                 'the other tables are read by name from the database schema. Timestamp (UTC) is '
                 "events_persisted.timestamp read as a FILETIME value, as Andrew Rathbun's SQLECmd map "
                 '(https://github.com/EricZimmerman/SQLECmd/blob/5839a5dbbc24285f8a0dfe769470d73a70a64d4b/SQLMap/Maps/Windows_EventTranscriptDB_NoDataSampling.smap#L215) '
                 'and plaso '
                 '(https://github.com/log2timeline/plaso/blob/f663c00cbc33ff930dd4f1e6297e4840192b5d39/plaso/parsers/sqlite_plugins/windows_eventtranscript.py#L172-L174) '
                 "read it; on plaso_testdata_f951fc6 it equalled the payload's own time field to the 100 "
                 'nanoseconds on all 2,526 rows. Validated on one database only, plaso_testdata_f951fc6 from '
                 "plaso's test data, whose origin the source does not state; every payload's ext.os.ver begins "
                 '10.0.19041.1165, and the database is in WAL mode with no -wal, so it was read alone. None of '
                 'the other registered Windows corpus images checked holds the database; the EventTranscript '
                 'folder is present and empty on seven of them. Rows are '
                 'Microsoft.Windows.Inventory.Core.InventoryApplicationAdd and InventoryApplicationRemove events. '
                 'Name, Version, Publisher, Root Directory Path (RootDirPath), Install Date (InstallDate), '
                 'Source, Type, Package Full Name (PackageFullName) and Program Instance ID (ProgramInstanceId) '
                 "are the Add event's fields, which Microsoft describes as the application's name, version and "
                 'publisher, the root directory where it was installed, the install date (a best guess based on '
                 'folder creation date heuristics), how it was installed, its type, the Store package full name '
                 "and a hash of the file IDs in the app (Microsoft, 'Windows 11, version 24H2 required Windows "
                 "diagnostic events and fields', ms.date 2026-04-05, "
                 'https://learn.microsoft.com/en-us/windows/privacy/required-diagnostic-events-fields-windows-11-24H2). '
                 'Object Instance ID is baseData.objectInstanceId, which the same page, under '
                 'Ms.Device.DeviceInventoryChange, describes as an object identity unique within the device '
                 "scope. That page's text for InventoryApplicationRemove describes a different event, so the "
                 "Remove event's meaning is taken from its name only. Remove events store only InventoryVersion, "
                 'baseType and baseData, so their rows carry an Object Instance ID and no name. On '
                 'plaso_testdata_f951fc6 there were 17 Add and 11 Remove rows, Install Date held a value on 6 of '
                 'the 17 Add rows, and 1 of the 11 Remove rows has an Object Instance ID that an Add row in the '
                 'same database also carries. Not reported: InstallDateMsi, InstallDateFromLinkFile and '
                 'InstallDateArpLastModified (empty lists on all 17 Add rows), and the other inventory events '
                 '(drivers, frameworks, device containers), which are in Diagnostic Data Events.',
        "paths": ('*/ProgramData/Microsoft/Diagnosis/EventTranscript/EventTranscript.db*',),
        "output_types": "standard",
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": 'Windows 10 1809 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "alihadi_threatsim_server2019": 'Windows Server 2019 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "hexordia_mvs2025_win11": 'Windows 11 24H2 build 26100 | 0 rows (the EventTranscript folder holds no database)',
            "lonewolf_win10": 'Windows 10 Education build 16299 | 0 rows (the EventTranscript folder holds no database)',
            "ou_ransomware_server2022": 'Windows Server 2022 build 20348 | 0 rows (the EventTranscript folder holds no database)',
            "pc_mus_001_win11": 'Windows 11 22H2 build 22621 | 0 rows (the EventTranscript folder holds no database)',
            "plaso_testdata_f951fc6": 'payload ext.os.ver 10.0.19041.1165 | 28 rows (the database placed at its ProgramData path in a derived zip)',
            "szechuan_win10": 'Windows 10 2004 build 19041 | 0 rows (the EventTranscript folder holds no database)',
        },
    },
    "eventTranscriptDeviceInventory": {
        "name": 'Diagnostic Data PnP Device Inventory Changes',
        "description": 'InventoryDevicePnpAdd and InventoryDevicePnpRemove events in the Windows Diagnostic Data Viewer '
                       'database, with the device and driver values the Add event stores.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Read from ProgramData\\Microsoft\\Diagnosis\\EventTranscript\\EventTranscript.db with its '
                 'write-ahead log when one is beside it; Source File names the database each row came from, since '
                 'the declared path can match one copy per volume. Windows keeps this database while the Turn on '
                 'the Diagnostic Data Viewer option (Settings, Privacy & security, Diagnostics & feedback) is on; '
                 'Microsoft says turning it off clears the stored data, that by default up to 1 GB or 30 days is '
                 'kept with the oldest dropped first, and that an event shown may still be queued and not yet '
                 "uploaded (Microsoft, 'Diagnostic Data Viewer', ms.date 2026-02-12, "
                 'https://learn.microsoft.com/en-us/windows/privacy/diagnostic-data-viewer-overview), so a row '
                 "does not show that the event reached Microsoft. The location follows Andrew Rathbun's "
                 'EventTranscript.db research '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L17), '
                 'which Abhiram Kumar credits to Andrew Rathbun and Josh Mitchell '
                 '(https://github.com/stuxnet999/EventTranscriptParser/blob/902eb3c773d5c0a63b0997ea0f1612e860f05c1c/README.md#L93), '
                 'and the tag names come from its Tag Descriptions table '
                 '(https://github.com/rathbuna/EventTranscript.db-Research/blob/a07e42a8a4fc9bfbe1fbf1c500fa79d0d4de92ed/README.md#L21-L32); '
                 'the other tables are read by name from the database schema. Timestamp (UTC) is '
                 "events_persisted.timestamp read as a FILETIME value, as Andrew Rathbun's SQLECmd map "
                 '(https://github.com/EricZimmerman/SQLECmd/blob/5839a5dbbc24285f8a0dfe769470d73a70a64d4b/SQLMap/Maps/Windows_EventTranscriptDB_NoDataSampling.smap#L215) '
                 'and plaso '
                 '(https://github.com/log2timeline/plaso/blob/f663c00cbc33ff930dd4f1e6297e4840192b5d39/plaso/parsers/sqlite_plugins/windows_eventtranscript.py#L172-L174) '
                 "read it; on plaso_testdata_f951fc6 it equalled the payload's own time field to the 100 "
                 'nanoseconds on all 2,526 rows. Validated on one database only, plaso_testdata_f951fc6 from '
                 "plaso's test data, whose origin the source does not state; every payload's ext.os.ver begins "
                 '10.0.19041.1165, and the database is in WAL mode with no -wal, so it was read alone. None of '
                 'the other registered Windows corpus images checked holds the database; the EventTranscript '
                 'folder is present and empty on seven of them. Rows are '
                 'Microsoft.Windows.Inventory.Core.InventoryDevicePnpAdd and InventoryDevicePnpRemove events. '
                 'Headers are the stored key names and values are as stored, because the field table for '
                 "InventoryDevicePnpAdd on Microsoft's 'Windows 11, version 24H2 required Windows diagnostic "
                 "events and fields' page (ms.date 2026-04-05, "
                 'https://learn.microsoft.com/en-us/windows/privacy/required-diagnostic-events-fields-windows-11-24H2) '
                 "pairs several keys with another key's description (Description is described as a container "
                 'GUID, HWID as a driver version and Inf as the enumerating bus), so no meaning is taken from it. '
                 'HWID, a list, is written as compact JSON. Object Instance ID is baseData.objectInstanceId, '
                 'which the same page, under Ms.Device.DeviceInventoryChange, describes as an object identity '
                 'unique within the device scope. Remove events store only InventoryVersion, baseType and '
                 'baseData. On plaso_testdata_f951fc6 there were 12 Add and 5 Remove rows; InstallDate (as '
                 'stored) and FirstInstallDate (as stored) were identical on all 17 rows, blank on the Remove '
                 'rows; and none of the 5 Remove rows has an Object Instance ID that an Add row in the same '
                 'database carries. The other keys (COMPID, STACKID, ClassGuid, MatchingID, DriverId, the filter '
                 'lists, DeviceState, InstallState, ProblemCode and more) are in the payload in Diagnostic Data '
                 'Events.',
        "paths": ('*/ProgramData/Microsoft/Diagnosis/EventTranscript/EventTranscript.db*',),
        "output_types": "standard",
        "artifact_icon": "cpu",
        "sample_data": {
            "af_case2_win10": 'Windows 10 1809 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "alihadi_threatsim_server2019": 'Windows Server 2019 build 17763 | 0 rows (the EventTranscript folder holds no database)',
            "hexordia_mvs2025_win11": 'Windows 11 24H2 build 26100 | 0 rows (the EventTranscript folder holds no database)',
            "lonewolf_win10": 'Windows 10 Education build 16299 | 0 rows (the EventTranscript folder holds no database)',
            "ou_ransomware_server2022": 'Windows Server 2022 build 20348 | 0 rows (the EventTranscript folder holds no database)',
            "pc_mus_001_win11": 'Windows 11 22H2 build 22621 | 0 rows (the EventTranscript folder holds no database)',
            "plaso_testdata_f951fc6": 'payload ext.os.ver 10.0.19041.1165 | 17 rows (the database placed at its ProgramData path in a derived zip)',
            "szechuan_win10": 'Windows 10 2004 build 19041 | 0 rows (the EventTranscript folder holds no database)',
        },
    },
}

import json
import os
import sqlite3
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.windows_registry import filetime_utc

_DATABASE = 'EventTranscript.db'

# The events_persisted columns every query reads.
_REQUIRED_COLUMNS = frozenset(('timestamp', 'payload', 'full_event_name', 'full_event_name_hash', 'sid'))

_HISTORY_JOURNAL = '.Microsoft.WebBrowser.HistoryJournal.'
_APP_INTERACTIVITY = ('Win32kTraceLogging.AppInteractivitySummary', 'Win32kTraceLogging.AppInteractivity')
_APP_INVENTORY = ('Microsoft.Windows.Inventory.Core.InventoryApplicationAdd',
                  'Microsoft.Windows.Inventory.Core.InventoryApplicationRemove')
_DEVICE_INVENTORY = ('Microsoft.Windows.Inventory.Core.InventoryDevicePnpAdd',
                     'Microsoft.Windows.Inventory.Core.InventoryDevicePnpRemove')


def _databases(context):
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.basename(path) == _DATABASE and os.path.isfile(path):
            yield path, context.get_relative_path(path)


def _tables(db):
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def _columns(db, table):
    return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}


def _column(present, name, alias='e'):
    """The column when the table has it, NULL otherwise, so a missing column costs no rows."""
    return f'{alias}.{name}' if name in present else 'NULL'


def _event_query(db, where):
    """The events_persisted query with the lookup tables joined where they exist."""
    tables = _tables(db)
    present = _columns(db, 'events_persisted')
    producer, group, joins = 'NULL', 'NULL', ''
    if 'producer_id' in present and 'producers' in tables:
        producer = 'p.producer_id_text'
        joins += '\n    LEFT JOIN producers p ON p.producer_id = e.producer_id'
    if 'provider_group_id' in present and 'provider_groups' in tables:
        group = 'g.group_guid'
        joins += '\n    LEFT JOIN provider_groups g ON g.group_id = e.provider_group_id'
    return f'''
    SELECT e.rowid, e.timestamp, e.full_event_name, e.full_event_name_hash, e.sid,
           {_column(present, 'logging_binary_name')}, {_column(present, 'friendly_logging_binary_name')},
           {_column(present, 'is_core')}, {_column(present, 'event_keywords')},
           {_column(present, 'compressed_payload_size')}, {producer}, {group}, e.payload
    FROM events_persisted e{joins}
    {where}
    ORDER BY e.timestamp, e.rowid'''


def _categories(db, label, relative):
    """{full_event_name_hash: 'name; name'} from event_tags and tag_descriptions."""
    tables = _tables(db)
    if 'event_tags' not in tables:
        logfunc(f'{label}: {relative} has no event_tags table; categories left blank')
        return {}
    names = {}
    if 'tag_descriptions' in tables:
        for tag_id, tag_name in db.execute(
                'SELECT tag_id, tag_name FROM tag_descriptions ORDER BY tag_id, locale_name'):
            names.setdefault(tag_id, [])
            if tag_name and tag_name not in names[tag_id]:
                names[tag_id].append(tag_name)
    tags = {}
    for name_hash, tag_id in db.execute(
            'SELECT DISTINCT full_event_name_hash, tag_id FROM event_tags '
            'WHERE full_event_name_hash IN (SELECT full_event_name_hash FROM events_persisted) '
            'ORDER BY full_event_name_hash, tag_id'):
        tags.setdefault(name_hash, []).append(
            ' / '.join(names[tag_id]) if names.get(tag_id) else f'tag {tag_id} (no description stored)')
    return {name_hash: '; '.join(values) for name_hash, values in tags.items()}


def _read(context, label, where='', params=(), with_categories=False):
    """Yield (relative path, row, categories) per event, and the list of databases read."""
    sources = []
    results = []
    for path, relative in _databases(context):
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            if 'events_persisted' not in _tables(db):
                logfunc(f'{label}: {relative} has no events_persisted table')
                sources.append(path)
                continue
            missing = _REQUIRED_COLUMNS - _columns(db, 'events_persisted')
            if missing:
                logfunc(f'{label}: {relative} events_persisted lacks {", ".join(sorted(missing))}')
                sources.append(path)
                continue
            categories = _categories(db, label, relative) if with_categories else {}
            rows = db.execute(_event_query(db, where), params).fetchall()
        except sqlite3.Error as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            sources.append(path)
            continue
        finally:
            db.close()
        sources.append(path)
        results.append((relative, rows, categories))
    return results, sources


def _text(value):
    """A stored value as report text: scalars as they are, lists and objects as compact JSON."""
    if value is None:
        return ''
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return value


def _strip_nul(value):
    """The value without the NUL characters some rows end with."""
    return value.rstrip('\x00') if isinstance(value, str) else ('' if value is None else value)


def _payload_data(payload, row_id, skipped):
    """The payload's data object, or None (counted) when the payload is not JSON with one."""
    try:
        data = json.loads(payload).get('data')
    except (TypeError, ValueError, AttributeError):
        data = None
    if not isinstance(data, dict):
        skipped.append(row_id)
        return None
    return data


def _log_skipped(label, relative, skipped):
    if skipped:
        logfunc(f'{label}: {relative}: {len(skipped)} payloads without a JSON data object were '
                f'skipped (row IDs {", ".join(str(r) for r in skipped[:20])}'
                f'{", ..." if len(skipped) > 20 else ""})')


def _iso_utc(value):
    """An ISO 8601 UTC string ending in Z as an aware datetime; the value itself when it is not one."""
    if not isinstance(value, str) or not value.endswith('Z'):
        return _text(value)
    text = value[:-1]
    fraction = ''
    if '.' in text:
        text, fraction = text.split('.', 1)
    try:
        moment = datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return value
    if fraction and not fraction.isdigit():
        return value
    micro = int((fraction + '000000')[:6]) if fraction else 0
    return moment.replace(microsecond=micro, tzinfo=timezone.utc)


@artifact_processor
def eventTranscriptEvents(context):
    label = 'Diagnostic Data Events'
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Event Name', 'Diagnostic Data Categories', 'Producer',
                    'Logging Binary', 'Friendly Logging Binary Name', 'User SID', 'Is Core (as stored)',
                    'Event Keywords (as stored)', 'Provider Group GUID',
                    'Compressed Payload Size (as stored)', 'Payload (as stored)', 'Row ID', 'Source File')
    data_list = []
    results, sources = _read(context, label, with_categories=True)
    for relative, rows, categories in results:
        for (row_id, stamp, name, name_hash, sid, binary, friendly, is_core, keywords, size, producer,
             group, payload) in rows:
            data_list.append((filetime_utc(stamp), name or '', categories.get(name_hash, ''),
                              producer or '', binary or '', _strip_nul(friendly), sid or '',
                              _text(is_core), _text(keywords), group or '', _text(size),
                              payload or '', row_id, relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def eventTranscriptEdgeHistory(context):
    label = 'Diagnostic Data Edge HistoryJournal Events'
    data_headers = (('Timestamp (UTC)', 'datetime'), ('data.Timestamp (UTC)', 'datetime'), 'Event',
                    'Navigation URL', 'Referrer URL (referUrl)', 'Page Title', 'Tab ID', 'HTTP Status Code',
                    'Correlation GUID', 'User SID', 'Event Name', 'Row ID', 'Source File')
    data_list = []
    results, sources = _read(context, label, where="WHERE e.full_event_name LIKE ?",
                             params=(f'%{_HISTORY_JOURNAL}%',))
    for relative, rows, _ in results:
        skipped = []
        for row_id, stamp, name, _hash, sid, *_rest, payload in rows:
            data = _payload_data(payload, row_id, skipped)
            if data is None:
                continue
            url, refer, title = data.get('navigationUrl'), data.get('referUrl'), data.get('PageTitle')
            if not (url or refer or title):
                continue
            data_list.append((filetime_utc(stamp), _iso_utc(data.get('Timestamp')),
                              name.split(_HISTORY_JOURNAL, 1)[-1], _text(url), _text(refer), _text(title),
                              _text(data.get('TabId')), _text(data.get('HttpStatusCode')),
                              _text(data.get('CorrelationGuid')), sid or '', name, row_id, relative))
        _log_skipped(label, relative, skipped)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def eventTranscriptAppInteractivity(context):
    label = 'Diagnostic Data App Interactivity'
    data_headers = (('Aggregation Start Time (UTC)', 'datetime'), ('Timestamp (UTC)', 'datetime'), 'App ID',
                    'App Version', 'Aggregation Duration (ms)', 'In Focus Duration (ms)',
                    'User Active Duration (ms)', 'User or Display Active Duration (ms)',
                    'Focus Lost Count', 'Keyboard Input (s)', 'Mouse Input (s)', 'App Session ID',
                    'Event Name', 'User SID', 'Row ID', 'Source File')
    data_list = []
    marks = ', '.join('?' for _ in _APP_INTERACTIVITY)
    results, sources = _read(context, label, where=f'WHERE e.full_event_name IN ({marks})',
                             params=_APP_INTERACTIVITY)
    for relative, rows, _ in results:
        skipped = []
        for row_id, stamp, name, _hash, sid, *_rest, payload in rows:
            data = _payload_data(payload, row_id, skipped)
            if data is None:
                continue
            data_list.append((_iso_utc(data.get('AggregationStartTime')), filetime_utc(stamp),
                              _text(data.get('AppId')), _text(data.get('AppVersion')),
                              _text(data.get('AggregationDurationMS')), _text(data.get('InFocusDurationMS')),
                              _text(data.get('UserActiveDurationMS')),
                              _text(data.get('UserOrDisplayActiveDurationMS')),
                              _text(data.get('FocusLostCount')), _text(data.get('KeyboardInputSec')),
                              _text(data.get('MouseInputSec')), _text(data.get('AppSessionId')),
                              name, sid or '', row_id, relative))
        _log_skipped(label, relative, skipped)
    return data_headers, data_list, '\n'.join(sources)


def _inventory_rows(context, label, names, fields):
    """Rows of (time, event, field values..., object instance ID, row ID, source) for names."""
    data_list = []
    marks = ', '.join('?' for _ in names)
    results, sources = _read(context, label, where=f'WHERE e.full_event_name IN ({marks})', params=names)
    for relative, rows, _ in results:
        skipped = []
        for row_id, stamp, name, *_rest, payload in rows:
            data = _payload_data(payload, row_id, skipped)
            if data is None:
                continue
            base = data.get('baseData') if isinstance(data.get('baseData'), dict) else {}
            data_list.append((filetime_utc(stamp), name.rsplit('.', 1)[-1])
                             + tuple(_text(data.get(field)) for field in fields)
                             + (_text(base.get('objectInstanceId')), row_id, relative))
        _log_skipped(label, relative, skipped)
    return data_list, sources


_APP_FIELDS = ('Name', 'Version', 'Publisher', 'RootDirPath', 'InstallDate', 'Source', 'Type',
               'PackageFullName', 'ProgramInstanceId')


@artifact_processor
def eventTranscriptAppInventory(context):
    label = 'Diagnostic Data Application Inventory Changes'
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Event', 'Name', 'Version', 'Publisher',
                    'Root Directory Path', 'Install Date (as stored)', 'Source', 'Type',
                    'Package Full Name', 'Program Instance ID', 'Object Instance ID', 'Row ID',
                    'Source File')
    data_list, sources = _inventory_rows(context, label, _APP_INVENTORY, _APP_FIELDS)
    return data_headers, data_list, '\n'.join(sources)


_DEVICE_FIELDS = ('Description', 'BusReportedDescription', 'Manufacturer', 'Model', 'Class', 'Enumerator',
                  'InstallDate', 'FirstInstallDate', 'HWID', 'ParentId', 'ContainerId', 'Service',
                  'DriverName', 'DriverVerVersion', 'Inf', 'Provider')


@artifact_processor
def eventTranscriptDeviceInventory(context):
    label = 'Diagnostic Data PnP Device Inventory Changes'
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Event', 'Description', 'BusReportedDescription',
                    'Manufacturer', 'Model', 'Class', 'Enumerator', 'InstallDate (as stored)',
                    'FirstInstallDate (as stored)', 'HWID', 'ParentId', 'ContainerId', 'Service',
                    'DriverName', 'DriverVerVersion', 'Inf', 'Provider', 'Object Instance ID', 'Row ID',
                    'Source File')
    data_list, sources = _inventory_rows(context, label, _DEVICE_INVENTORY, _DEVICE_FIELDS)
    return data_headers, data_list, '\n'.join(sources)
