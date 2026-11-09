__artifacts_v2__ = {
    "chromiumMediaPlaybacks": {
        "name": "Chromium Media Playbacks",
        "description": "Rows of the playback table of the Media History database that Chromium-based "
                       "browsers kept from about version 86 to 91: the page that played media, the "
                       "seconds watched and whether the media had video and audio.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Media History is a SQLite database in each browser profile, named in media_history_store.cc "
                 "(https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/chrome/browser/media/history/media_history_store.cc#L35), "
                 "written while the UseMediaHistoryStore feature was on. It is on by default at the "
                 "88.0.4324.0 and 91.0.4472.0 snapshots "
                 "(https://github.com/chromium/chromium/blob/c73b5a651d37a6c4d0b8e3262cc4015a5579c6c8/media/base/media_switches.cc#L419-L420, "
                 "https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/media/base/media_switches.cc#L454-L455) "
                 "and off by default at the 92.0.4515.159 tag "
                 "(https://github.com/chromium/chromium/blob/01f0145da37acadacd53b1f0c3afd5f1e0a48f3d/media/base/media_switches.cc#L463-L464); "
                 "the release tags checked put the default on from 86 to 91. Chromium removed the "
                 "database in d5bb0ed111869bfff34b440cf0e15aee97fabf48 (2023-11-21). Whether a later "
                 "release deletes an existing file was not established. Tested on the known data "
                 "windows11_arm_chromium_legacy_history_known_20261108: official Chromium snapshots "
                 "88.0.4324.0 (schema version 4) and 91.0.4472.0 (version 6) on Windows 11 ARM64, each "
                 "playing a local WebM video page and the 91 build also an audio-only page, with the "
                 "network off; their profiles were placed at a standard Chromium path for the capture. "
                 "Google Chrome and Microsoft Edge of that era were not run, and the Microsoft Edge "
                 "copy on ou_ransomware_server2022 held no rows, so no Edge or Chrome row was seen. "
                 "Not read: mediaFeed and mediaFeedItem (0 rows on the known data; dropped in schema "
                 "version 6) and kaleidoscopeData (0 rows). "
                 "The user data folders read are those the Chromium Web Visits artifact reads, plus 360 "
                 "Safe Browser's on Windows; only the Windows Chromium folder was exercised, by the "
                 "known data, and the Microsoft Edge folder by one image. "
                 "One row per playback row. Chromium inserts one for each watch-time report of a media "
                 "player, so a page played twice gives two rows "
                 "(https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/chrome/browser/media/history/media_history_playback_table.cc#L62-L90); "
                 "on the known data the video page opened twice gave two rows, with 15 and 10 seconds "
                 "watched of the 20 and 15 seconds each tab was open. Watch Time (seconds) is "
                 "watch_time_s, the player's cumulative watch time in whole seconds (line 80). Has Video "
                 "and Has Audio are has_video and has_audio (lines 81 and 82); the audio-only page gave "
                 "No and Yes. Last Updated is last_updated_time_s, the time the row was written, stored "
                 "as whole seconds since 1601-01-01 UTC (line 84, base::Time::Now()."
                 "ToDeltaSinceWindowsEpoch().InSeconds()), not the microseconds the other Chromium "
                 "History databases use; on the known data it matched the logged time each tab was "
                 "closed to the second. Origin is the url of the origin row the playback names. "
                 "The origin table's own columns (an aggregate watch time and media engagement values) "
                 "are not shown: the engagement columns held NULL on the known data, and "
                 "aggregate_watchtime_audio_video_s is the sum of watch_time_s over the origin's playback "
                 "rows with both video and audio (media_history_origin_table.cc lines 139 to 144 at "
                 "the same commit). "
                 "Source File names the file each row came from, since Browser, Profile and User do not separate two copies of one profile, which a logical extraction can hold under Users/ and System/Volumes/Data/Users/. On the known data Browser held Chromium and User one value on all 4 rows (one user data folder), Origin held one value on all 4 rows (one local test origin) and Has Audio held Yes on all 4 rows (every test page had audio).",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Media History*',
            '*/Library/Application Support/Google/Chrome/*/Media History*',
            '*/.config/google-chrome/*/Media History*',
            '*/AppData/Local/Chromium/User Data/*/Media History*',
            '*/Library/Application Support/Chromium/*/Media History*',
            '*/.config/chromium/*/Media History*',
            '*/snap/chromium/common/chromium/*/Media History*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Media History*',
            '*/webbrowser/chrome/*/Media History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Media History*',
            '*/Library/Application Support/Microsoft Edge/*/Media History*',
            '*/.config/microsoft-edge/*/Media History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Media History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Media History*',
            '*/.config/BraveSoftware/Brave-Browser/*/Media History*',
            '*/AppData/Local/Vivaldi/User Data/*/Media History*',
            '*/Library/Application Support/Vivaldi/*/Media History*',
            '*/.config/vivaldi/*/Media History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Media History*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Media History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Media History*',
            '*/.config/opera/*/Media History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Media History*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Media History*',
            '*/AppData/Roaming/360se6/User Data/*/Media History*',
            '*/AppData/Roaming/360se6/User Data/Media History*',
            '*/Library/Application Support/com.operasoftware.Opera/Media History*',
            '*/.config/opera/Media History*',
        ),
        "output_types": "standard",
        "artifact_icon": "play-circle",
        "sample_data": {
            "windows11_arm_chromium_legacy_history_known_20261108": "Windows 11 build 26200 (ARM64), Chromium snapshots 88.0.4324.0 and 91.0.4472.0 | 4 rows",
            "ou_ransomware_server2022": "Windows Server 2022, Microsoft Edge | 0 rows (the one Media History copy holds no playback rows)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumMediaSessions": {
        "name": "Chromium Media Sessions",
        "description": "Rows of the playbackSession table of the Media History database that "
                       "Chromium-based browsers kept from about version 86 to 91: the page, the title, "
                       "artist and album the page declared for its media, the length and the position "
                       "reached, and the artwork URLs.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Media History is a SQLite database in each browser profile, named in media_history_store.cc "
                 "(https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/chrome/browser/media/history/media_history_store.cc#L35), "
                 "written while the UseMediaHistoryStore feature was on. It is on by default at the "
                 "88.0.4324.0 and 91.0.4472.0 snapshots "
                 "(https://github.com/chromium/chromium/blob/c73b5a651d37a6c4d0b8e3262cc4015a5579c6c8/media/base/media_switches.cc#L419-L420, "
                 "https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/media/base/media_switches.cc#L454-L455) "
                 "and off by default at the 92.0.4515.159 tag "
                 "(https://github.com/chromium/chromium/blob/01f0145da37acadacd53b1f0c3afd5f1e0a48f3d/media/base/media_switches.cc#L463-L464); "
                 "the release tags checked put the default on from 86 to 91. Chromium removed the "
                 "database in d5bb0ed111869bfff34b440cf0e15aee97fabf48 (2023-11-21). Whether a later "
                 "release deletes an existing file was not established. Tested on the known data "
                 "windows11_arm_chromium_legacy_history_known_20261108: official Chromium snapshots "
                 "88.0.4324.0 (schema version 4) and 91.0.4472.0 (version 6) on Windows 11 ARM64, each "
                 "playing a local WebM video page and the 91 build also an audio-only page, with the "
                 "network off; their profiles were placed at a standard Chromium path for the capture. "
                 "Google Chrome and Microsoft Edge of that era were not run, and the Microsoft Edge "
                 "copy on ou_ransomware_server2022 held no rows, so no Edge or Chrome row was seen. "
                 "Not read: mediaFeed and mediaFeedItem (0 rows on the known data; dropped in schema "
                 "version 6) and kaleidoscopeData (0 rows). "
                 "The user data folders read are those the Chromium Web Visits artifact reads, plus 360 "
                 "Safe Browser's on Windows; only the Windows Chromium folder was exercised, by the "
                 "known data, and the Microsoft Edge folder by one image. "
                 "One row per playbackSession row. Chromium writes a session when the tab navigates or "
                 "closes, and only when the media session had been active, had metadata the page set, "
                 "and had both audio and video "
                 "(https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/chrome/browser/media/history/media_history_contents_observer.cc#L111-L121); "
                 "the audio-only page of the known data set metadata and gave no row. url is UNIQUE and "
                 "the write is REPLACE INTO "
                 "(https://github.com/chromium/chromium/blob/afa7a1c77c10c66e16e0e097dfb62a8b01915f52/chrome/browser/media/history/media_history_session_table.cc#L70-L115), "
                 "so a page keeps one row, from its last session: the video page opened twice kept one "
                 "row with the second tab's position and close time. Title, Artist and Album are the "
                 "values the page gave (lines 105 to 107); Source Title is source_title as stored (line "
                 "108), which held the page's host and port on the known data, where the page did not "
                 "set one. Duration (seconds) and Position (seconds) are duration_ms and position_ms "
                 "divided by 1000 (lines 93 to 100; both are 0 when the player reported no position). "
                 "Last Updated is last_updated_time_s, whole seconds since 1601-01-01 UTC (line 104). "
                 "Artwork URLs lists the url and size of each mediaImage row linked to the session "
                 "through sessionImage, one per line. Origin is the url of the origin row the session "
                 "names. "
                 "Source File names the file each row came from, since Browser, Profile and User do not separate two copies of one profile, which a logical extraction can hold under Users/ and System/Volumes/Data/Users/. On the known data Browser held Chromium, User one value, Origin one value and Title, Artist and Album one value each on both rows (the same test page in two profiles).",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Media History*',
            '*/Library/Application Support/Google/Chrome/*/Media History*',
            '*/.config/google-chrome/*/Media History*',
            '*/AppData/Local/Chromium/User Data/*/Media History*',
            '*/Library/Application Support/Chromium/*/Media History*',
            '*/.config/chromium/*/Media History*',
            '*/snap/chromium/common/chromium/*/Media History*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Media History*',
            '*/webbrowser/chrome/*/Media History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Media History*',
            '*/Library/Application Support/Microsoft Edge/*/Media History*',
            '*/.config/microsoft-edge/*/Media History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Media History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Media History*',
            '*/.config/BraveSoftware/Brave-Browser/*/Media History*',
            '*/AppData/Local/Vivaldi/User Data/*/Media History*',
            '*/Library/Application Support/Vivaldi/*/Media History*',
            '*/.config/vivaldi/*/Media History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Media History*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Media History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Media History*',
            '*/.config/opera/*/Media History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Media History*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Media History*',
            '*/AppData/Roaming/360se6/User Data/*/Media History*',
            '*/AppData/Roaming/360se6/User Data/Media History*',
            '*/Library/Application Support/com.operasoftware.Opera/Media History*',
            '*/.config/opera/Media History*',
        ),
        "output_types": "standard",
        "artifact_icon": "film",
        "sample_data": {
            "windows11_arm_chromium_legacy_history_known_20261108": "Windows 11 build 26200 (ARM64), Chromium snapshots 88.0.4324.0 and 91.0.4472.0 | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022, Microsoft Edge | 0 rows (the one Media History copy holds no session rows)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumArchivedVisits": {
        "name": "Chromium Archived Visits",
        "description": "Rows of the visits table of the Archived History database that Chrome kept "
                       "up to version 36, where history older than 90 days was moved, with the URL "
                       "and title of each visit's urls row.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Archived History and History Index are SQLite databases that old Chrome kept beside "
                 "History in each profile. Tested on the known data "
                 "windows11_arm_chromium_legacy_history_known_20261108: the official Chromium snapshot "
                 "208281 (29.0.1547.0, x86) on Windows 11 ARM64 with the network off, two profiles, "
                 "placed at a standard Chromium path for the capture. In the second profile the "
                 "known-data rig moved four visits back by 100 days while the browser was closed, then "
                 "reopened it, and Chromium's own expirer moved those visits to Archived History; "
                 "their History Index text stayed under the original times, because the rig changed "
                 "the visit times the deletion matches on. Google Chrome and Microsoft Edge builds "
                 "were not run; Microsoft Edge on Chromium came after both stores were dropped, so "
                 "the Edge paths are read only for completeness and no image exercised them. The user "
                 "data folders read are those the Chromium Web Visits artifact reads, plus 360 Safe "
                 "Browser's on Windows; only the Windows Chromium folder was exercised. "
                 "One row per visits row of an Archived History database, joined to its urls row. "
                 "Chromium moved a visit there once it was older than 90 days "
                 "(https://github.com/chromium/chromium/blob/9dae4a37862398cd103d2d0b3d25ce1d540eac0b/chrome/browser/history/history_backend.cc#L104 "
                 "and #L756) when its transition was TYPED, AUTO_BOOKMARK or AUTO_TOPLEVEL, or LINK, "
                 "FORM_SUBMIT, KEYWORD or GENERATED at the end of a redirect chain; other visits, "
                 "subframes among them, were deleted "
                 "(https://github.com/chromium/chromium/blob/9dae4a37862398cd103d2d0b3d25ce1d540eac0b/chrome/browser/history/expire_history_backend.cc#L102-L123). "
                 "The archived visit keeps its visit_time and transition but not its referring visit, "
                 "which is set to 0 (same file, line 619). Visit Time is visits.visit_time, "
                 "microseconds since 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/9dae4a37862398cd103d2d0b3d25ce1d540eac0b/base/time.h#L6). "
                 "Transition and Transition Qualifiers name the core type and the qualifier bits as "
                 "the Chromium Web Visits artifact does. Visit Source is read from visit_source as "
                 "there; a visit with no row is shown as BROWSED (no visit_source row). URL Last "
                 "Visit Time is the archived urls row's last_visit_time: when a URL is archived again "
                 "Chromium copies the main History's last visit onto it (expire_history_backend.cc "
                 "lines 482 to 501), and on the known data the URL that also had a later visit in History "
                 "carried that later time, so it can be later than every archived visit of the URL. Visit Count and Typed Count are the urls row's counts as stored. "
                 "keyword_search_terms exists in Archived History "
                 "(https://github.com/chromium/chromium/blob/9dae4a37862398cd103d2d0b3d25ce1d540eac0b/chrome/browser/history/archived_database.cc#L64-L65) "
                 "but the expirer does not copy search terms into it (TODO at expire_history_backend.cc "
                 "line 490); it held 0 rows on the known data and is not read. "
                 "Source File names the file each row came from, since Browser, Profile and User do not separate two copies of one profile, which a logical extraction can hold under Users/ and System/Volumes/Data/Users/. On the known data Browser held Chromium, User one value and Profile one value (Profile 3, the only profile with archived visits) on all 4 rows; Transition Qualifiers held CHAIN_START, CHAIN_END and Visit Source held BROWSED (no visit_source row) on all 4 rows.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Archived History*',
            '*/Library/Application Support/Google/Chrome/*/Archived History*',
            '*/.config/google-chrome/*/Archived History*',
            '*/AppData/Local/Chromium/User Data/*/Archived History*',
            '*/Library/Application Support/Chromium/*/Archived History*',
            '*/.config/chromium/*/Archived History*',
            '*/snap/chromium/common/chromium/*/Archived History*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Archived History*',
            '*/webbrowser/chrome/*/Archived History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Archived History*',
            '*/Library/Application Support/Microsoft Edge/*/Archived History*',
            '*/.config/microsoft-edge/*/Archived History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Archived History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Archived History*',
            '*/.config/BraveSoftware/Brave-Browser/*/Archived History*',
            '*/AppData/Local/Vivaldi/User Data/*/Archived History*',
            '*/Library/Application Support/Vivaldi/*/Archived History*',
            '*/.config/vivaldi/*/Archived History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Archived History*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Archived History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Archived History*',
            '*/.config/opera/*/Archived History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Archived History*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Archived History*',
            '*/AppData/Roaming/360se6/User Data/*/Archived History*',
            '*/AppData/Roaming/360se6/User Data/Archived History*',
            '*/Library/Application Support/com.operasoftware.Opera/Archived History*',
            '*/.config/opera/Archived History*',
        ),
        "output_types": "standard",
        "artifact_icon": "archive",
        "sample_data": {
            "windows11_arm_chromium_legacy_history_known_20261108": "Windows 11 build 26200 (ARM64), Chromium snapshot 29.0.1547.0 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
    "chromiumHistoryIndex": {
        "name": "Chromium History Index",
        "description": "Pages in the monthly History Index full-text databases that Chrome kept up to "
                       "version 29: URL, title and the page's text, with the visit time it was "
                       "indexed under.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Archived History and History Index are SQLite databases that old Chrome kept beside "
                 "History in each profile. Tested on the known data "
                 "windows11_arm_chromium_legacy_history_known_20261108: the official Chromium snapshot "
                 "208281 (29.0.1547.0, x86) on Windows 11 ARM64 with the network off, two profiles, "
                 "placed at a standard Chromium path for the capture. In the second profile the "
                 "known-data rig moved four visits back by 100 days while the browser was closed, then "
                 "reopened it, and Chromium's own expirer moved those visits to Archived History; "
                 "their History Index text stayed under the original times, because the rig changed "
                 "the visit times the deletion matches on. Google Chrome and Microsoft Edge builds "
                 "were not run; Microsoft Edge on Chromium came after both stores were dropped, so "
                 "the Edge paths are read only for completeness and no image exercised them. The user "
                 "data folders read are those the Chromium Web Visits artifact reads, plus 360 Safe "
                 "Browser's on Windows; only the Windows Chromium folder was exercised. "
                 "One row per page in a History Index YYYY-MM database, Chrome's full-text index of "
                 "page text, one file per database identifier, which the source describes as a year and "
                 "month (https://github.com/chromium/chromium/blob/9dae4a37862398cd103d2d0b3d25ce1d540eac0b/chrome/browser/history/text_database.cc#L58 "
                 "and #L85-L95); the known data's file is History Index 2026-11. "
                 "The pages table is an FTS3 table with the ICU tokenizer (line 185), which a SQLite "
                 "built without ICU cannot query, so the text is read from its content table, "
                 "pages_content (c0url, c1title, c2body), the table FTS3 keeps each row's columns in, "
                 "joined on rowid to the info table. Visit Time is info.time, the time of the visit "
                 "the page was indexed for, written with base::Time::ToInternalValue (line 232), "
                 "microseconds since 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/9dae4a37862398cd103d2d0b3d25ce1d540eac0b/base/time.h#L6); "
                 "in the known-data profile whose visits the rig left unchanged, each matched the "
                 "visit_time of the History visit of the same page exactly. The page text of a frame "
                 "was indexed with its parent page: the known-data page holding an iframe has the "
                 "frame's text in its Body Text. Body Text is the page text Chrome indexed, as stored. Chrome deletes a "
                 "page's text when the visit it belongs to is deleted or archived, matched on that "
                 "visit time (expire_history_backend.cc lines 439 and 440), and deletes index "
                 "files older than three months (line 147), so pages here can outlive their visits "
                 "only when that deletion did not run. text_database.cc is gone from the 30.0.1599.101 "
                 "tag, and the 36.0.1985.143 release deletes every History Index file when it opens "
                 "the history databases "
                 "(https://github.com/chromium/chromium/blob/03a1bdf59379255b3ae984612958ae796163819f/chrome/browser/history/history_backend.cc#L562-L563 "
                 "and #L1632-L1647), so these files survive only where no later Chrome ran on the "
                 "profile. "
                 "Source File names the file each row came from, since Browser, Profile and User do not separate two copies of one profile, which a logical extraction can hold under Users/ and System/Volumes/Data/Users/. On the known data Browser held Chromium and User one value on all 9 rows (one user data folder).",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/History Index *',
            '*/Library/Application Support/Google/Chrome/*/History Index *',
            '*/.config/google-chrome/*/History Index *',
            '*/AppData/Local/Chromium/User Data/*/History Index *',
            '*/Library/Application Support/Chromium/*/History Index *',
            '*/.config/chromium/*/History Index *',
            '*/snap/chromium/common/chromium/*/History Index *',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/History Index *',
            '*/webbrowser/chrome/*/History Index *',
            '*/AppData/Local/Microsoft/Edge/User Data/*/History Index *',
            '*/Library/Application Support/Microsoft Edge/*/History Index *',
            '*/.config/microsoft-edge/*/History Index *',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/History Index *',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/History Index *',
            '*/.config/BraveSoftware/Brave-Browser/*/History Index *',
            '*/AppData/Local/Vivaldi/User Data/*/History Index *',
            '*/Library/Application Support/Vivaldi/*/History Index *',
            '*/.config/vivaldi/*/History Index *',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/History Index *',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/History Index *',
            '*/Library/Application Support/com.operasoftware.Opera/*/History Index *',
            '*/.config/opera/*/History Index *',
            '*/AppData/Roaming/Opera Software/Opera Stable/History Index *',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/History Index *',
            '*/AppData/Roaming/360se6/User Data/*/History Index *',
            '*/AppData/Roaming/360se6/User Data/History Index *',
            '*/Library/Application Support/com.operasoftware.Opera/History Index *',
            '*/.config/opera/History Index *',
        ),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "windows11_arm_chromium_legacy_history_known_20261108": "Windows 11 build 26200 (ARM64), Chromium snapshot 29.0.1547.0 | 9 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
        },
    },
}

import datetime
import re
import sqlite3

from scripts.chromium.browser_profiles import (enum_label, open_store, page_transition,
                                               profile_stores, row_tail, table_columns,
                                               webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc

# components/history/core/browser/history_types.h, lines 50 to 59, chromium
# 33f34ef179f55596f6c2fc8a55878b7ccf6276e4 (the names the Chromium Web Visits artifact uses).
_VISIT_SOURCES = {
    0: 'SYNCED', 1: 'BROWSED', 2: 'EXTENSION', 3: 'FIREFOX_IMPORTED', 4: 'IE_IMPORTED',
    5: 'SAFARI_IMPORTED', 6: 'ACTOR', 7: 'OS_MIGRATION_IMPORTED',
}

_WINDOWS_EPOCH = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)


def windows_seconds(value):
    """Whole seconds since 1601-01-01 UTC as a datetime; '' for missing, zero, negative or out of range."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return ''
    if seconds <= 0:
        return ''
    try:
        return _WINDOWS_EPOCH + datetime.timedelta(seconds=seconds)
    except OverflowError:
        return ''


def _yes_no(value):
    if value is None or value == '':
        return ''
    return 'Yes' if int(value) else 'No'


def _ms_to_seconds(value):
    if value is None or value == '':
        return ''
    return int(value) / 1000


def read_playbacks(db):
    """(last updated, url, watch seconds, has video, has audio, origin, id) per playback row, or None."""
    if not table_columns(db, 'playback'):
        return None
    origin_join = ('LEFT JOIN origin ON origin.id = playback.origin_id'
                   if table_columns(db, 'origin') else '')
    origin_column = 'origin.origin' if origin_join else 'NULL'
    rows = db.execute(f'''
        SELECT playback.last_updated_time_s, playback.url, playback.watch_time_s,
               playback.has_video, playback.has_audio, {origin_column}, playback.id
        FROM playback {origin_join}
        ORDER BY playback.last_updated_time_s, playback.id''').fetchall()
    return [(windows_seconds(updated), url or '', watch, _yes_no(video), _yes_no(audio),
             origin or '', row_id)
            for updated, url, watch, video, audio, origin, row_id in rows]


def read_sessions(db):
    """One tuple per playbackSession row, with its artwork URLs, or None when the table is absent."""
    if not table_columns(db, 'playbackSession'):
        return None
    artwork = {}
    if table_columns(db, 'sessionImage') and table_columns(db, 'mediaImage'):
        for session_id, url, width, height in db.execute('''
                SELECT sessionImage.session_id, mediaImage.url, sessionImage.width,
                       sessionImage.height
                FROM sessionImage JOIN mediaImage ON mediaImage.id = sessionImage.image_id
                ORDER BY sessionImage.session_id, mediaImage.id, sessionImage.width,
                         sessionImage.height'''):
            size = f' ({width}x{height})' if width or height else ''
            artwork.setdefault(session_id, []).append(f'{url}{size}')
    origin_join = ('LEFT JOIN origin ON origin.id = playbackSession.origin_id'
                   if table_columns(db, 'origin') else '')
    origin_column = 'origin.origin' if origin_join else 'NULL'
    rows = db.execute(f'''
        SELECT playbackSession.id, playbackSession.last_updated_time_s, playbackSession.url,
               playbackSession.title, playbackSession.artist, playbackSession.album,
               playbackSession.source_title, playbackSession.duration_ms,
               playbackSession.position_ms, {origin_column}
        FROM playbackSession {origin_join}
        ORDER BY playbackSession.last_updated_time_s, playbackSession.id''').fetchall()
    return [(windows_seconds(updated), url or '', title or '', artist or '', album or '',
             source_title or '', _ms_to_seconds(duration), _ms_to_seconds(position),
             '\n'.join(artwork.get(session_id, [])), origin or '', session_id)
            for (session_id, updated, url, title, artist, album, source_title, duration,
                 position, origin) in rows]


def read_archived_visits(db):
    """One tuple per visits row of an Archived History database, or None when it has no visits table."""
    if not table_columns(db, 'visits'):
        return None
    has_source = bool(table_columns(db, 'visit_source'))
    source_columns = 'visit_source.id, visit_source.source' if has_source else 'NULL, NULL'
    source_join = 'LEFT JOIN visit_source ON visit_source.id = visits.id' if has_source else ''
    rows = db.execute(f'''
        SELECT visits.id, visits.visit_time, urls.url, urls.title, visits.transition,
               {source_columns}, visits.visit_duration, urls.last_visit_time,
               urls.visit_count, urls.typed_count
        FROM visits
        LEFT JOIN urls ON urls.id = visits.url
        {source_join}
        ORDER BY visits.visit_time, visits.id''').fetchall()
    out = []
    for (visit_id, visit_time, url, title, transition, source_row, source, duration,
         last_visit, visit_count, typed_count) in rows:
        core, qualifiers = page_transition(transition)
        if not has_source:
            visit_source = ''
        elif source_row is None:
            visit_source = 'BROWSED (no visit_source row)'
        else:
            visit_source = enum_label(_VISIT_SOURCES, source)
        seconds = '' if duration is None else int(duration) / 1_000_000
        out.append((webkit_time(visit_time), url or '', title or '', core, qualifiers,
                    visit_source, seconds, webkit_time(last_visit), visit_count, typed_count,
                    visit_id))
    return out


def read_history_index(db):
    """(visit time, url, title, body, page id) per indexed page, or None when the content table is absent."""
    present = table_columns(db, 'pages_content')
    if not {'c0url', 'c1title', 'c2body'} <= present:
        return None
    info_join = 'LEFT JOIN info ON info.rowid = pages_content.docid' if table_columns(db, 'info') else ''
    time_column = 'info.time' if info_join else 'NULL'
    rows = db.execute(f'''
        SELECT {time_column}, pages_content.c0url, pages_content.c1title, pages_content.c2body,
               pages_content.docid
        FROM pages_content {info_join}
        ORDER BY {time_column}, pages_content.docid''').fetchall()
    return [(webkit_time(when), url or '', title or '', body or '', doc_id)
            for when, url, title, body, doc_id in rows]


class _IndexNames:
    """Matches the monthly History Index YYYY-MM file names, which profile_stores tests with `in`."""

    _NAME = re.compile(r'History Index \d{4}-\d{2}')

    def __contains__(self, name):
        return bool(self._NAME.fullmatch(name))


def _rows(context, names, label, reader):
    data_list, sources = [], []
    for store in profile_stores(context, names, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            rows = reader(db)
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        if rows is None:
            logfunc(f'{label}: {store.relative} has no table this artifact reads')
            continue
        sources.append(store.path)
        data_list.extend(row + row_tail(store) for row in rows)
    return data_list, '\n'.join(sources)


@artifact_processor
def chromiumMediaPlaybacks(context):
    data_list, sources = _rows(context, {'Media History'}, 'Chromium Media Playbacks',
                               read_playbacks)
    data_headers = (('Last Updated', 'datetime'), 'URL', 'Watch Time (seconds)', 'Has Video',
                    'Has Audio', 'Origin', 'Playback ID', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, sources


@artifact_processor
def chromiumMediaSessions(context):
    data_list, sources = _rows(context, {'Media History'}, 'Chromium Media Sessions',
                               read_sessions)
    data_headers = (('Last Updated', 'datetime'), 'URL', 'Title', 'Artist', 'Album',
                    'Source Title', 'Duration (seconds)', 'Position (seconds)', 'Artwork URLs',
                    'Origin', 'Session ID', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, sources


@artifact_processor
def chromiumArchivedVisits(context):
    data_list, sources = _rows(context, {'Archived History'}, 'Chromium Archived Visits',
                               read_archived_visits)
    data_headers = (('Visit Time', 'datetime'), 'URL', 'Title', 'Transition',
                    'Transition Qualifiers', 'Visit Source', 'Visit Duration (seconds)',
                    ('URL Last Visit Time', 'datetime'), 'Visit Count', 'Typed Count', 'Visit ID',
                    'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, sources


@artifact_processor
def chromiumHistoryIndex(context):
    data_list, sources = _rows(context, _IndexNames(), 'Chromium History Index',
                               read_history_index)
    data_headers = (('Visit Time', 'datetime'), 'URL', 'Title', 'Body Text', 'Page ID',
                    'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, sources
