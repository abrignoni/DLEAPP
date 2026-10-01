__artifacts_v2__ = {
    "safariHistory": {
        "name": "Safari History",
        "description": "Each row in History.db's history_visits table, "
                       "joined back to history_items for the URL, domain "
                       "and lifetime visit count.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every History.db found is parsed, so a Mac with more than one user account reports "
                 "each account, tagged by Source File. A Safari profile's History.db under "
                 "Library/Safari/Profiles/<UUID>/ is read as its own store, and its Source File names "
                 "that folder. Profile is the title of the row in the bookmarks table of SafariTabs.db, "
                 "in the same Safari folder, whose server_id or external_uuid equals that folder's "
                 "name. Profile is blank for a History.db outside Profiles/, when no row names the "
                 "folder, and when that Safari folder has no SafariTabs.db. Source File is kept beside "
                 "Profile because Profile does not distinguish two accounts, two copies of one store, "
                 "or the History.db outside Profiles/. On "
                 "safari_tags_known_data_macos27 (macOS 27.0.1, Safari 27.0.1) two profiles made for "
                 "the test kept their folders in Safari's container, under "
                 "Library/Containers/com.apple.Safari/Data/Library/Safari/Profiles/. The name of each "
                 "History.db folder equalled the server_id of the row titled with that profile's name, "
                 "and Profile reads TagTest on 11 visits and TagTest2 on 3. 10 of the 14 visits show a "
                 "tag, and Item Visit Count (lifetime) held one value, 1, on all 14 rows. That sample's "
                 "SafariTabs.db was built for the sample: it holds the bookmarks CREATE statement and "
                 "the three profile rows of the SafariTabs.db on the Mac the sample was made on, with "
                 "their sync and attribute columns left empty, and nothing else. The row for the default profile had an empty title and the text "
                 "DefaultProfile in both columns, while Safari's settings listed that profile as "
                 "Personal (Default). Profile was blank on every row of dleapp_safari_bigsur, which "
                 "has no profile folder. visit_time is read as Mac Absolute Time "
                 "(seconds since 2001-01-01): read that way, the 27 visits on dleapp_safari_bigsur "
                 "fall between 2020-12-12 and 2021-02-17, and the 2 LastVisitTime numbers in that "
                 "image's LastSession.plist each equal the visit_time of a visit of the same URL. Tags "
                 "and Tag Identifiers list the title and identifier of each history_tags row that a "
                 "history_items_to_tags row links to the visit's history item, ordered by the link's "
                 "timestamp and separated by a semicolon and a space. The link is to the history item, "
                 "so each visit of that item shows the same tags. Tags and Tag Identifiers are blank "
                 "when the item has no link or the database lacks either table; they were blank on "
                 "every row of dleapp_safari_bigsur, whose two tag tables are empty. Safari History "
                 "Tags reports the tags themselves. A logical extraction can hold one user's "
                 "History.db under Users/ and again under System/Volumes/Data/Users/. The two are read "
                 "as one store: a visit both copies hold with the same values and tags is reported "
                 "once, with the Source File of the copy under Users/, and a visit only one copy "
                 "holds, or that differs between them, is reported from the copy that holds it. On the "
                 "public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) "
                 "History.db was byte-identical under the two paths, its -wal differed, and each copy "
                 "held the same 139 visits, which are reported once; 11 of them show a tag. The "
                 "differing-copies case was exercised with constructed databases only. On "
                 "dleapp_safari_bigsur Load Successful held one value, Yes, on all 27 rows, HTTP "
                 "Non-GET and Synthesized had no value on any of the 27 rows, and Origin (raw) held "
                 "one value, 0, on all 27. On the MacBook Pro extraction Synthesized had no value on "
                 "any of the 139 rows. What the origin values mean is not established.",
        "paths": (
            "*/Library/Safari/History.db*",
            "*/Library/Safari/Profiles/*/History.db*",
            "*/Library/Safari/SafariTabs.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), History.db | 22 history items, 27 visits",
            "safari_tags_known_data_macos27": "macOS 27.0.1 build 26A434, Safari 27.0.1 | 14 rows",
        },
    },
    "safariHistoryTags": {
        "name": "Safari History Tags",
        "description": "Tags stored in Safari's History.db and the history "
                       "items each tag is linked to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per history_items_to_tags row, which links a "
                 "history_tags row to a history_items row, and one row for "
                 "each history_tags row that no link names. Tag Modified is "
                 "history_tags.modification_timestamp and Item Tagged is "
                 "history_items_to_tags.timestamp, both read as Mac Absolute "
                 "Time (seconds since 2001-01-01) and shown in UTC. Tag is "
                 "the title "
                 "column, Identifier the identifier column and URL the linked "
                 "item's url. Item Count is history_tags.item_count as "
                 "stored, Linked Items is the number of links that name the "
                 "tag in the same database, counted by this artifact, and "
                 "Type and Level are the stored integers. On the row of a tag "
                 "with no link, Item Tagged and URL are blank and Linked "
                 "Items is 0. A link that names a tag id history_tags lacks "
                 "would not be reported, and a link that names a missing "
                 "history item would show a blank URL. No tested database "
                 "held either. "
                 "The CREATE statements stored in the database allow one link "
                 "per item and tag (UNIQUE(history_item, tag_id) ON CONFLICT "
                 "REPLACE) and define two triggers that add 1 to item_count "
                 "after a link is inserted and subtract 1 before a link is "
                 "deleted. "
                 "Measured on the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key), which holds 4 "
                 "tags and 5 links: every tag had a link, Item Count was "
                 "higher than Linked Items on 1 of the 4 tags and lower on "
                 "none, Tag Modified equalled the tag's latest Item Tagged "
                 "value on all 4, and Item Tagged was within 60 seconds of a "
                 "visit to the linked item on 4 of the 5 links. What event "
                 "either time records is not established. Type held one "
                 "value, 1, and Level held one value, 200, on all 4 tags, "
                 "and what they mean is not established. Each Identifier was the letter Q followed by "
                 "digits, the form of a Wikidata item identifier. How Safari "
                 "chooses a tag for a page is not established. "
                 "dleapp_safari_bigsur (macOS 11.2.1) holds both tables with "
                 "no rows. A History.db without the two tables was exercised "
                 "with a constructed database only. "
                 "safari_tags_known_data_macos27 is one Safari profile's "
                 "History.db from a known-data session on macOS 27.0.1 with "
                 "Safari 27.0.1, in which a script opened 13 public pages in a "
                 "profile made for the test. 9 of the 13 pages were linked to "
                 "a tag, each link's time 5.4 to 8.8 seconds after the visit. "
                 "Two history items were then deleted in Safari's History "
                 "window. Deleting the only item linked to a tag removed the "
                 "link and left the tag, with Item Count going from 1 to 0. "
                 "Deleting one of the two items linked to another tag removed "
                 "that link and Item Count went from 2 to 1. Tag Modified did "
                 "not change on either tag. Quitting Safari and opening it "
                 "again changed nothing in the two tables. The sample holds that "
                 "database as copied while Safari was quit: 7 tags and 7 links, reported as 8 "
                 "rows, 1 of them a tag with no link, Item Count 0 and Linked "
                 "Items 0. Item Count equalled Linked Items on all 7 tags, and "
                 "Type held 1 and Level held 200 on all 7. Tag Modified is "
                 "later than every Item Tagged value on the tag that lost one "
                 "of its two links. After the sample was copied, Clear "
                 "History for the last hour, which covered every visit, "
                 "removed every row of both tables, the tag with no link "
                 "included. History that expires by age and a Clear History "
                 "range that leaves some of a tag's items were not tested. "
                 "The sample also holds the History.db of a second test "
                 "profile, with 3 tags and 3 links reported as 3 rows. One of "
                 "its tags has the Tag and Identifier of a tag in the first "
                 "profile's database; each database is read on its own. "
                 "A Safari profile's History.db under "
                 "Library/Safari/Profiles/<UUID>/ is read as its own store. "
                 "Profile is the title SafariTabs.db stores for that folder, "
                 "resolved as the Safari History notes describe, and is blank "
                 "when no row names the folder. On the sample Profile reads "
                 "TagTest on 8 rows and TagTest2 on 3. Source File is kept "
                 "beside Profile because Profile does not distinguish two "
                 "accounts, two copies of one store, or the History.db "
                 "outside Profiles/. "
                 "A logical extraction can hold one user's History.db under "
                 "Users/ and again under System/Volumes/Data/Users/. The two "
                 "are read as one store: a row both copies hold with the same "
                 "values is reported once, with the Source File of the copy "
                 "under Users/, and a row only one copy holds, or that "
                 "differs between them, is reported from the copy that holds "
                 "it. The MacBook Pro's 5 rows were held by both copies and "
                 "are reported once. "
                 "The two tables and the Wikidata form of the identifier are "
                 "described in the reference. Reference: Yogesh Khatri, 'Tags "
                 "in Safari History db', "
                 "https://www.swiftforensics.com/2026/10/tags-in-safari-history-db.html",
        "paths": (
            "*/Library/Safari/History.db*",
            "*/Library/Safari/Profiles/*/History.db*",
            "*/Library/Safari/SafariTabs.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "tag",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (both "
                "tag tables are empty)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (both "
                "tag tables are empty)",
            "safari_tags_known_data_macos27": "macOS 27.0.1 build 26A434, Safari 27.0.1 | 11 rows",
        },
    },
    "safariBookmarks": {
        "name": "Safari Bookmarks",
        "description": "Bookmarks in Safari's Bookmarks.plist, one row per WebBookmarkTypeLeaf node, with "
                       "the folders above it, its title, URL and UUID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per node whose WebBookmarkType is WebBookmarkTypeLeaf. Folder Path joins, "
                 "with a slash, the Title of each node above the leaf, leaving out an empty Title; "
                 "Title is URIDictionary.title, URL is URLString and Bookmark UUID is WebBookmarkUUID. "
                 "A node of any other type is not reported: each tested file held one "
                 "WebBookmarkTypeProxy node, titled History. Measured on dleapp_safari_bigsur (macOS "
                 "11.2.1, 7 rows) and on the public MacBook Pro logical extraction (macOS 15.4, not a "
                 "registered corpus key; 4 rows): none of the 11 leaves had a Title key of its own and "
                 "all 11 had URIDictionary.title; Folder Path held one value, BookmarksBar, on every "
                 "row of both files, and the BookmarksMenu and com.apple.ReadingList lists held no "
                 "entry on either. A leaf under com.apple.ReadingList and a folder inside a folder "
                 "were exercised with constructed plists only. A logical extraction can hold one "
                 "user's Bookmarks.plist under Users/ and again under System/Volumes/Data/Users/. A "
                 "copy under System/Volumes/Data/ whose bytes equal the other copy's is not read again "
                 "and the run log counts it; copies that differ are both read, and each row shows the "
                 "Source File it came from. On the MacBook Pro extraction the two copies were "
                 "byte-identical and the 4 bookmarks are reported once, from the copy under Users/. "
                 "Copies that differ were exercised with constructed plists only.",
        "paths": (
            "*/Library/Safari/Bookmarks.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "bookmark",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 7 rows",
        },
    },
    "safariTopSites": {
        "name": "Safari Top Sites",
        "description": "Entries of the TopSites list in Safari's TopSites.plist, with each entry's title, "
                       "URL and TopSiteIsBuiltIn value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per entry of the plist's TopSites list. Title is TopSiteTitle and URL is "
                 "TopSiteURLString. Built-in Default shows Yes or No for a stored TopSiteIsBuiltIn of "
                 "true or false and is blank when the entry has no such key. What TopSiteIsBuiltIn "
                 "marks is not established. On dleapp_safari_bigsur (macOS 11.2.1) the list held 12 "
                 "entries: Built-in Default held one value, Yes, on all 12 rows, and Title was blank "
                 "on 1 row, whose entry had no TopSiteTitle key. An entry with a false "
                 "TopSiteIsBuiltIn, and one without the key, were exercised with a constructed plist "
                 "only. On the public MacBook Pro logical extraction (macOS 15.4, not a registered "
                 "corpus key) the TopSites list held no entry, so no row is reported from it. The "
                 "plist's BannedURLStrings and DemoSites lists are not reported; both were empty on "
                 "both files. A logical extraction can hold one user's TopSites.plist under Users/ and "
                 "again under System/Volumes/Data/Users/. A copy under System/Volumes/Data/ whose "
                 "bytes equal the other copy's is not read again and the run log counts it; copies "
                 "that differ are both read, and each row shows the Source File it came from. On the "
                 "MacBook Pro extraction the two copies were byte-identical. Copies that differ were "
                 "exercised with constructed plists only. A Safari profile's TopSites.plist under "
                 "Library/Safari/Profiles/<UUID>/ is also read. Profile is the title of the row in the "
                 "bookmarks table of SafariTabs.db, in the same Safari folder, whose server_id or "
                 "external_uuid equals that folder's name, and is blank for a TopSites.plist outside "
                 "Profiles/ or when no row names the folder. On safari_tags_known_data_macos27 (macOS "
                 "27.0.1, Safari 27.0.1) each of two test profiles had a TopSites.plist in a folder "
                 "named with the external_uuid of its row, a different folder from the one holding "
                 "its History.db. Both files held no entry and the same bytes, both are read, and no "
                 "row is reported from them, so a row with a Profile value was exercised with a "
                 "constructed plist only. That sample's SafariTabs.db was built for the sample from "
                 "the three profile rows of the Mac's database. Profile was blank on all 12 rows of "
                 "dleapp_safari_bigsur.",
        "paths": (
            "*/Library/Safari/TopSites.plist",
            "*/Library/Safari/Profiles/*/TopSites.plist",
            "*/Library/Safari/SafariTabs.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "star",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 12 rows",
            "safari_tags_known_data_macos27": "macOS 27.0.1 build 26A434, Safari 27.0.1 | 0 rows "
                "(two TopSites.plist files, no entries)",
        },
    },
    "safariRecentlyClosedTabs": {
        "name": "Safari Recently Closed Tabs",
        "description": "Tabs listed in Safari's RecentlyClosedTabs.plist, one row per tab of each "
                       "ClosedTabOrWindowPersistentStates entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Each entry of ClosedTabOrWindowPersistentStates holds a PersistentState. An entry "
                 "whose PersistentState holds TabStates is read as a window and gives one row per tab. "
                 "An entry that holds no TabStates and holds TabUUID or TabURL is read as one tab. An "
                 "entry that holds neither is not reported and the run log counts it. Tab Title is "
                 "TabTitle, URL is TabURL, Tab UUID is TabUUID and Tab Index is TabIndex. Closed is "
                 "the tab's DateClosed, or the window's DateClosed when the tab has none. Last Visit "
                 "Time is LastVisitTime: a date value is shown as stored, in UTC, and a number is read "
                 "as Mac Absolute Time (seconds since 2001-01-01). Window UUID is the window's "
                 "WindowUUID, or the entry's own WindowUUID on a one-tab entry. Private Window shows "
                 "Yes or No for the window's IsPrivateWindow and is blank when that key is absent, as "
                 "it is on a one-tab entry. Session State Size (bytes) is the length of the tab's "
                 "SessionState value, which is not decoded. PersistentStateType is not read; the two "
                 "entry shapes are told apart by their keys. Measured on dleapp_safari_bigsur (macOS "
                 "11.2.1): 2 entries, each a window with 1 tab, 2 rows; Last Visit Time and Session "
                 "State Size (bytes) had no value on either row, because neither tab had a "
                 "LastVisitTime or a SessionState key. Measured on the public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key): 11 entries, 7 of them windows "
                 "holding 13 tabs and 4 of them one-tab entries, 17 rows. PersistentStateType was 1 on "
                 "the 7 windows and on both macOS 11.2.1 entries, and 0 on the 4 one-tab entries. "
                 "Private Window was No on the 13 window rows and blank on the 4 one-tab rows. "
                 "LastVisitTime was a date value on all 17 rows; Last Visit Time was later than Closed "
                 "on 5 rows and earlier on 12, and within one second of a History.db visit of the same "
                 "URL on 2. Session State Size (bytes) had no value on any of the 17 rows, because no "
                 "tab had a SessionState key. What Closed and Last Visit Time each mark is not "
                 "established. A Private Window of Yes, a number LastVisitTime, a SessionState and an "
                 "entry that is neither a window nor a tab were exercised with constructed plists "
                 "only. A logical extraction can hold one user's RecentlyClosedTabs.plist under Users/ "
                 "and again under System/Volumes/Data/Users/. A copy under System/Volumes/Data/ whose "
                 "bytes equal the other copy's is not read again and the run log counts it; copies "
                 "that differ are both read, and each row shows the Source File it came from. On the "
                 "MacBook Pro extraction the two copies were byte-identical and the 17 tabs are "
                 "reported once, from the copy under Users/. Copies that differ were exercised with "
                 "constructed plists only.",
        "paths": (
            "*/Library/Safari/RecentlyClosedTabs.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "x-circle",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
        },
    },
    "safariCloudTabs": {
        "name": "Safari iCloud Tabs (CloudTabs.db)",
        "description": "Rows of the cloud_tabs table in Safari's CloudTabs.db, each with the name of the "
                       "cloud_tab_devices row its device_uuid names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per cloud_tabs row, joined to cloud_tab_devices on device_uuid. Tab Title, "
                 "URL and Tab UUID are the title, url and tab_uuid columns. Last Viewed is "
                 "last_viewed_time read as Mac Absolute Time (seconds since 2001-01-01) and shown in "
                 "UTC; it is blank when the stored value is 0, the column's declared default, or when "
                 "the table has no such column. What last_viewed_time marks is not established. Device "
                 "Name, Device Type, Device UUID and Device Last Modified come from the device row: "
                 "Device Type is device_type_identifier, blank when the table has no such column, and "
                 "Device Last Modified is last_modified read as Mac Absolute Time and shown in UTC. "
                 "Ephemeral Device, Pinned and Showing Reader show Yes for a stored true value and are "
                 "blank otherwise. Reader Scroll Page is reader_scroll_position_page_index as stored. "
                 "A cloud_tab_devices row that no tab names gives no row here; Safari iCloud Tab "
                 "Devices lists every device. cloud_tab_close_requests is not read. system_fields and "
                 "position are not decoded; on both tested databases every system_fields value began "
                 "with bplist00 and every position value with the bytes 78 DA. A row is not by itself "
                 "evidence that a tab was open on another device: on dleapp_safari_bigsur (macOS "
                 "11.2.1, 2 tabs, 1 device, 2 rows) the 2 rows carry the same 2 URLs as the 2 tabs in "
                 "that image's LastSession.plist, and Device Last Modified is less than 0.04 seconds "
                 "before the DateClosed of those tabs. On that database Last Viewed and Device Type "
                 "had no value on either row, because it has neither column; Ephemeral Device, Pinned "
                 "and Showing Reader had no value on either row, each stored value being 0; and Reader "
                 "Scroll Page held 0 on both. On the public MacBook Pro logical extraction (macOS "
                 "15.4, not a registered corpus key) the database holds 1 tab and 2 devices: 1 row is "
                 "reported, with Last Viewed and Device Type filled and Device Type naming an iPhone "
                 "model, and Ephemeral Device, Pinned and Showing Reader had no value on it. "
                 "cloud_tab_close_requests held no row on either database. No tested database held a "
                 "true value for Ephemeral Device, Pinned or Showing Reader. A true value in each of "
                 "the three, a stored last_viewed_time of 0, a tab whose device_uuid no device row has "
                 "(its device columns are blank) and a database that lacks cloud_tabs or "
                 "cloud_tab_devices (named in the run log and not read) were exercised with "
                 "constructed databases only. The database was at Library/Safari/CloudTabs.db on the "
                 "macOS 11.2.1 image and at "
                 "Library/Containers/com.apple.Safari/Data/Library/Safari/CloudTabs.db on the macOS "
                 "15.4 extraction; the declared path matches both. A logical extraction can hold one "
                 "CloudTabs.db under Users/ and again under System/Volumes/Data/Users/. The two are "
                 "read as one store: a tab both copies hold with the same values is reported once, "
                 "with the Source File of the copy under Users/, and a tab only one copy holds, or "
                 "that differs between them, is reported from the copy that holds it. On the MacBook "
                 "Pro extraction CloudTabs.db was byte-identical under the two paths, with an empty "
                 "-wal beside each, and its 1 tab is reported once. The differing-copies case was "
                 "exercised with constructed databases only.",
        "paths": (
            "*/Library/Safari/CloudTabs.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "cloud",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
        },
    },
    "safariCloudTabDevices": {
        "name": "Safari iCloud Tab Devices",
        "description": "Rows of the cloud_tab_devices table in Safari's CloudTabs.db, with the number "
                       "of cloud_tabs rows that name each device.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per cloud_tab_devices row. Last Modified is last_modified read as Mac "
                 "Absolute Time (seconds since 2001-01-01) and shown in UTC; what it marks is not "
                 "established. Device Name is device_name, Device UUID is device_uuid and Device Type "
                 "is device_type_identifier, blank when the table has no such column. Tabs is the "
                 "number of cloud_tabs rows in the same database whose device_uuid is the device's, "
                 "counted by this artifact. Ephemeral Device and Duplicate Device Name show Yes or No "
                 "for a stored is_ephemeral_device and has_duplicate_device_name of true or false, and "
                 "are blank when no value is stored. system_fields is not decoded. A row is not by "
                 "itself evidence of a device other than the Mac the database came from: on "
                 "dleapp_safari_bigsur (macOS 11.2.1, 1 device, 1 row) the device's 2 tabs carry the "
                 "same 2 URLs as the 2 tabs in that image's LastSession.plist. On that database Device "
                 "Type had no value on the 1 row, because cloud_tab_devices has no "
                 "device_type_identifier column there, and Ephemeral Device and Duplicate Device Name "
                 "were No. On the public MacBook Pro logical extraction (macOS 15.4, not a registered "
                 "corpus key) the database holds 2 devices, 2 rows: one with Tabs of 1, whose Device "
                 "Type names an iPhone model, and one with Tabs of 0, whose Device Type names a "
                 "MacBook Pro model. Ephemeral Device held one value, No, and Duplicate Device Name "
                 "held one value, No, on both rows. A Yes in either column, a blank in either and a "
                 "database that lacks cloud_tabs or cloud_tab_devices (named in the run log and not "
                 "read) were exercised with constructed databases only. A logical extraction can hold "
                 "one CloudTabs.db under Users/ and again under System/Volumes/Data/Users/. The two "
                 "are read as one store: a device both copies hold with the same values and tab count "
                 "is reported once, with the Source File of the copy under Users/, and a device only "
                 "one copy holds, or that differs between them, is reported from the copy that holds "
                 "it. On the MacBook Pro extraction CloudTabs.db was byte-identical under the two "
                 "paths and its 2 devices are reported once. The differing-copies case was exercised "
                 "with constructed databases only.",
        "paths": (
            "*/Library/Safari/CloudTabs.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "smartphone",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
        },
    },
    "safariLastSession": {
        "name": "Safari Last Session (Open Tabs)",
        "description": "Tabs of the windows listed in Safari's LastSession.plist, with each tab's title, "
                       "URL, stored times and whether its window is marked private.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per tab of each SessionWindows window's TabStates. Tab Title is TabTitle, "
                 "URL is TabURL, Tab UUID is TabUUID, Tab Index is TabIndex and Window UUID is the "
                 "window's WindowUUID. Window Closed is the tab's DateClosed, or the window's "
                 "DateClosed when the tab has none. Last Visit Time is LastVisitTime: a number is read "
                 "as Mac Absolute Time (seconds since 2001-01-01) and a date value is shown as stored, "
                 "in UTC. Private Window shows Yes or No for the window's IsPrivateWindow and is blank "
                 "when that key is absent. Session State Size (bytes) is the length of the tab's "
                 "SessionState value, which is not decoded. What event writes the file, and what "
                 "DateClosed marks in it, are not established. Measured on dleapp_safari_bigsur (macOS "
                 "11.2.1): 1 window with 2 tabs, 2 rows. Each tab's LastVisitTime was a number that, "
                 "read as Mac Absolute Time, equals the visit_time of a History.db visit of the same "
                 "URL (2 of 2). Each tab had its own DateClosed, so Window Closed shows the tab's "
                 "value on both rows; the window's own DateClosed was less than 0.01 seconds earlier. "
                 "Private Window was No on both rows. Session State Size (bytes) was 1,516,728 and "
                 "244,757; each SessionState began with the bytes 00 00 00 02 followed by bplist, and "
                 "each tab's SessionStateIsEncrypted was false. The public MacBook Pro logical "
                 "extraction (macOS 15.4, not a registered corpus key) holds no LastSession.plist "
                 "under either path. A date LastVisitTime, a window without IsPrivateWindow, a Private "
                 "Window of Yes and a tab without its own DateClosed were exercised with constructed "
                 "plists only. A logical extraction can hold one user's LastSession.plist under Users/ "
                 "and again under System/Volumes/Data/Users/. A copy under System/Volumes/Data/ whose "
                 "bytes equal the other copy's is not read again and the run log counts it; copies "
                 "that differ are both read, and each row shows the Source File it came from. Both "
                 "cases were exercised with constructed plists only.",
        "paths": (
            "*/Library/Safari/LastSession.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "layout",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
        },
    },
}

import hashlib
import os
import plistlib
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

# Seconds between the Unix epoch (1970-01-01) and the Mac/Cocoa epoch
# (2001-01-01). History.db visit_time and LastSession/RecentlyClosedTabs
# LastVisitTime are both Mac Absolute Time in seconds, confirmed against the
# validation image.
_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _mac_abs_s_to_utc(value):
    """Mac/Cocoa Absolute Time in SECONDS since 2001-01-01."""
    if not value:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    try:
        return _MAC_EPOCH + timedelta(seconds=value)
    except (OverflowError, OSError, ValueError):
        return None


def _plist_time(value):
    """A time from a plist as UTC: a date value is kept (plistlib reads one as
    UTC with no zone attached), a number is read as Mac Absolute Time in
    seconds."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return _mac_abs_s_to_utc(value)


def _files_named(files_found, basename):
    """Every file whose basename matches."""
    return [p for p in files_found if os.path.basename(p) == basename]


def _load_plist(path):
    try:
        with open(path, "rb") as handle:
            return plistlib.load(handle)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Safari: could not parse plist '{path}': {ex}")
        return None


# A logical extraction can hold the Data volume at its root and again under
# System/Volumes/Data/. Removing that prefix gives both copies of a store one key.
_DATA_VOLUME = re.compile(r"(^|/)System/Volumes/Data/")


def _stores(context, basename):
    """(staged path, evidence path, store key) per file named `basename`, with
    a copy under System/Volumes/Data/ after the copy at the root."""
    stores = []
    for source in _files_named([str(f) for f in context.get_files_found()],
                               basename):
        relative_source = context.get_relative_path(source)
        normal = relative_source.replace("\\", "/")
        store = _DATA_VOLUME.sub(r"\1", normal, count=1)
        stores.append((store, store != normal, source, relative_source))
    stores.sort()
    return [(source, relative_source, store)
            for store, _second, source, relative_source in stores]


def _plist_sources(context, basename, label):
    """(staged path, evidence path, store key) per plist named `basename`. A copy under
    System/Volumes/Data/ whose bytes equal the copy at the root is left out
    and counted in the run log under `label`; copies that differ are both
    returned."""
    kept = []
    seen = set()
    skipped = 0
    for source, relative_source, store in _stores(context, basename):
        try:
            with open(source, "rb") as handle:
                digest = hashlib.sha256(handle.read()).digest()
        except OSError:
            digest = None
        if digest is not None and (store, digest) in seen:
            skipped += 1
            continue
        seen.add((store, digest))
        kept.append((source, relative_source, store))
    if skipped:
        logfunc(f"{label}: {skipped} byte-identical copy(ies) under "
                f"System/Volumes/Data not read again")
    return kept


# <Safari folder>/Profiles/<folder name>/<file>: a file a Safari profile keeps.
_PROFILE_FILE = re.compile(r"^(.*/Library/Safari)/Profiles/([^/]+)/[^/]+$")


def _profile_names(context):
    """{(Safari folder, profile folder name): title} from the bookmarks table of
    each SafariTabs.db: a row's server_id and its external_uuid each name a
    folder under that Safari folder's Profiles/."""
    names = {}
    for source, _relative_source, store in _stores(context, "SafariTabs.db"):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        safari_folder = store.rsplit("/", 1)[0]
        try:
            rows = database.execute(
                "SELECT title, server_id, external_uuid FROM bookmarks").fetchall()
        except sqlite3.Error as ex:
            logfunc(f"Safari: profile names not read from '{store}': {ex}")
            rows = []
        database.close()
        for title, server_id, external_uuid in rows:
            for folder_name in (server_id, external_uuid):
                if folder_name:
                    names.setdefault((safari_folder, folder_name), title or "")
    return names


def _profile_name(names, store):
    """The title SafariTabs.db stores for the profile folder a file is in, or
    an empty string for a file outside Profiles/ or a folder no row names."""
    match = _PROFILE_FILE.match(store)
    if match is None:
        return ""
    return names.get((match.group(1), match.group(2)), "")


def _has_tag_tables(database):
    names = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    return {"history_tags", "history_items_to_tags"} <= names


def _item_tags(database):
    """history_items.id -> (tag titles, tag identifiers), ordered by link
    timestamp."""
    if not _has_tag_tables(database):
        return {}
    tags = {}
    for item, title, identifier in database.execute("""
            SELECT l.history_item, t.title, t.identifier
            FROM history_items_to_tags l
            JOIN history_tags t ON t.id = l.tag_id
            ORDER BY l.history_item, l.timestamp, t.id"""):
        titles, identifiers = tags.setdefault(item, ([], []))
        titles.append(title)
        identifiers.append(identifier)
    return {item: ("; ".join(titles), "; ".join(identifiers))
            for item, (titles, identifiers) in tags.items()}


_HISTORY_QUERY = """
    SELECT
        hv.visit_time, hi.url, hi.domain_expansion, hv.title,
        hi.visit_count, hv.load_successful, hv.http_non_get,
        hv.synthesized, hv.origin, hv.id, hi.id
    FROM history_visits hv
    JOIN history_items hi ON hi.id = hv.history_item
    ORDER BY hv.visit_time DESC
"""

# One row per link between a tag and a history item, and one row for a tag no
# link names.
_TAGS_QUERY = """
    SELECT
        t.modification_timestamp, l.timestamp, t.title, t.identifier, hi.url,
        t.item_count,
        (SELECT COUNT(*) FROM history_items_to_tags c WHERE c.tag_id = t.id),
        t.type, t.level, t.id, l.history_item
    FROM history_tags t
    LEFT JOIN history_items_to_tags l ON l.tag_id = t.id
    LEFT JOIN history_items hi ON hi.id = l.history_item
    ORDER BY t.modification_timestamp DESC, t.id, l.timestamp DESC
"""


@artifact_processor
def safariHistory(context):
    data_headers = (
        ("Visit Time", "datetime"), "URL", "Domain", "Visit Title",
        "Item Visit Count (lifetime)", "Load Successful", "HTTP Non-GET",
        "Synthesized", "Origin (raw)", "Tags", "Tag Identifiers",
        "Profile", "Source File",
    )
    data_list = []
    read_sources = []
    seen = set()
    repeated = 0
    names = _profile_names(context)
    for source, relative_source, store in _stores(context, "History.db"):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        read_sources.append(relative_source)
        profile = _profile_name(names, store)
        item_tags = _item_tags(database)
        for row in database.execute(_HISTORY_QUERY):
            (visit_time, url, domain, title, visit_count, load_successful,
             http_non_get, synthesized, origin, _visit_id, item_id) = row
            tags, tag_identifiers = item_tags.get(item_id, ("", ""))
            record = (store, tuple(row), tags, tag_identifiers)
            if record in seen:
                repeated += 1
                continue
            seen.add(record)
            data_list.append((
                _mac_abs_s_to_utc(visit_time), url or "", domain or "",
                title or "", visit_count if visit_count is not None else "",
                "Yes" if load_successful else "No",
                "Yes" if http_non_get else "",
                "Yes" if synthesized else "",
                origin if origin is not None else "", tags, tag_identifiers,
                profile, relative_source,
            ))
        database.close()

    logfunc(f"Safari History: {len(data_list)} visit(s) across "
            f"{len(read_sources)} History.db file(s); {repeated} visit(s) "
            f"held by a second copy of a store were not reported again.")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariHistoryTags(context):
    data_headers = (
        ("Tag Modified", "datetime"), ("Item Tagged", "datetime"), "Tag",
        "Identifier", "URL", "Item Count", "Linked Items", "Type", "Level",
        "Profile", "Source File",
    )
    data_list = []
    read_sources = []
    seen = set()
    repeated = 0
    names = _profile_names(context)
    for source, relative_source, store in _stores(context, "History.db"):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        read_sources.append(relative_source)
        profile = _profile_name(names, store)
        if not _has_tag_tables(database):
            database.close()
            continue
        for row in database.execute(_TAGS_QUERY):
            (modified, tagged, title, identifier, url, item_count, linked,
             tag_type, level, _tag_id, _item_id) = row
            record = (store, tuple(row))
            if record in seen:
                repeated += 1
                continue
            seen.add(record)
            data_list.append((
                _mac_abs_s_to_utc(modified), _mac_abs_s_to_utc(tagged),
                title, identifier, url or "", item_count, linked, tag_type,
                level, profile, relative_source,
            ))
        database.close()

    logfunc(f"Safari History Tags: {len(data_list)} row(s) across "
            f"{len(read_sources)} History.db file(s); {repeated} row(s) held "
            f"by a second copy of a store were not reported again.")
    return data_headers, data_list, "\n".join(read_sources)


def _walk_bookmarks(node, folder_path, rows):
    if not isinstance(node, dict):
        return
    node_type = node.get("WebBookmarkType")

    if node_type == "WebBookmarkTypeLeaf":
        title = (node.get("URIDictionary") or {}).get("title", "")
        rows.append((
            folder_path, title, node.get("URLString", ""),
            node.get("WebBookmarkUUID", ""),
        ))
        return

    # Folder/list node (WebBookmarkTypeList) or the unlabeled root dict: both
    # use 'Children'; proxy nodes (e.g. the History shortcut) have no useful
    # children and simply fall through with nothing appended.
    name = node.get("Title", "")
    child_path = f"{folder_path}/{name}" if folder_path and name else (name or folder_path)
    for child in node.get("Children", []) or []:
        _walk_bookmarks(child, child_path, rows)


@artifact_processor
def safariBookmarks(context):
    data_headers = ("Folder Path", "Title", "URL", "Bookmark UUID", "Source File")
    data_list = []
    read_sources = []
    for source, relative_source, _store in _plist_sources(context, "Bookmarks.plist",
                                                  "Safari Bookmarks"):
        plist = _load_plist(source)
        if plist is None:
            continue
        read_sources.append(relative_source)
        rows = []
        _walk_bookmarks(plist, "", rows)
        for row in rows:
            data_list.append(row + (relative_source,))

    logfunc(f"Safari Bookmarks: {len(data_list)} bookmark(s) across "
            f"{len(read_sources)} Bookmarks.plist file(s).")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariTopSites(context):
    data_headers = ("Title", "URL", "Built-in Default", "Profile", "Source File")
    data_list = []
    read_sources = []
    names = _profile_names(context)
    for source, relative_source, store in _plist_sources(context, "TopSites.plist",
                                                         "Safari Top Sites"):
        plist = _load_plist(source)
        if plist is None:
            continue
        read_sources.append(relative_source)
        profile = _profile_name(names, store)
        for site in plist.get("TopSites", []) or []:
            if "TopSiteIsBuiltIn" in site:
                built_in = "Yes" if site["TopSiteIsBuiltIn"] else "No"
            else:
                built_in = ""
            data_list.append((
                site.get("TopSiteTitle", ""), site.get("TopSiteURLString", ""),
                built_in, profile, relative_source,
            ))

    logfunc(f"Safari Top Sites: {len(data_list)} entr(ies) across "
            f"{len(read_sources)} TopSites.plist file(s).")
    return data_headers, data_list, "\n".join(read_sources)


def _tab_row(tab, window_uuid, window_closed, is_private):
    session_state = tab.get("SessionState")
    state_size = len(session_state) if isinstance(session_state, (bytes, bytearray)) else ""
    return (
        tab.get("TabTitle", ""), tab.get("TabURL", ""),
        tab.get("DateClosed") or window_closed,
        _plist_time(tab.get("LastVisitTime")),
        window_uuid, tab.get("TabUUID", ""),
        tab.get("TabIndex", ""), is_private, state_size,
    )


def _tab_rows(window):
    """One row per tab of a window's TabStates."""
    if "IsPrivateWindow" in window:
        is_private = "Yes" if window["IsPrivateWindow"] else "No"
    else:
        is_private = ""
    return [_tab_row(tab, window.get("WindowUUID", ""), window.get("DateClosed"), is_private)
            for tab in window.get("TabStates", []) or []]


def _closed_entry_rows(state):
    """Rows of one RecentlyClosedTabs entry: a window's tabs when the entry
    holds TabStates, the entry itself when it holds one tab's keys, or None
    when it holds neither."""
    if "TabStates" in state:
        return _tab_rows(state)
    if "TabUUID" in state or "TabURL" in state:
        return [_tab_row(state, state.get("WindowUUID", ""), None, "")]
    return None


@artifact_processor
def safariRecentlyClosedTabs(context):
    data_headers = (
        "Tab Title", "URL", ("Closed", "datetime"), ("Last Visit Time", "datetime"),
        "Window UUID", "Tab UUID", "Tab Index", "Private Window",
        "Session State Size (bytes)", "Source File",
    )
    data_list = []
    read_sources = []
    unread = 0
    for source, relative_source, _store in _plist_sources(context, "RecentlyClosedTabs.plist",
                                                  "Safari Recently Closed Tabs"):
        plist = _load_plist(source)
        if plist is None:
            continue
        read_sources.append(relative_source)
        for entry in plist.get("ClosedTabOrWindowPersistentStates", []) or []:
            rows = _closed_entry_rows(entry.get("PersistentState", {}) or {})
            if rows is None:
                unread += 1
                continue
            for row in rows:
                data_list.append(row + (relative_source,))

    logfunc(f"Safari Recently Closed Tabs: {len(data_list)} tab(s) across "
            f"{len(read_sources)} file(s); {unread} entr(ies) held neither "
            f"TabStates nor a tab's own keys and were not reported.")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariLastSession(context):
    data_headers = (
        "Tab Title", "URL", ("Window Closed", "datetime"),
        ("Last Visit Time", "datetime"), "Window UUID", "Tab UUID",
        "Tab Index", "Private Window", "Session State Size (bytes)",
        "Source File",
    )
    data_list = []
    read_sources = []
    for source, relative_source, _store in _plist_sources(context, "LastSession.plist",
                                                  "Safari Last Session"):
        plist = _load_plist(source)
        if plist is None:
            continue
        read_sources.append(relative_source)
        for window in plist.get("SessionWindows", []) or []:
            for row in _tab_rows(window):
                data_list.append(row + (relative_source,))

    logfunc(f"Safari Last Session: {len(data_list)} tab(s) across "
            f"{len(read_sources)} file(s).")
    return data_headers, data_list, "\n".join(read_sources)


def _columns(database, table):
    """The column names of `table`, empty when the database has no such table."""
    return {row[1] for row in database.execute(f'PRAGMA table_info("{table}")')}


def _cloud_columns(database):
    """(cloud_tabs columns, cloud_tab_devices columns), or None when the
    database lacks either table."""
    tabs = _columns(database, "cloud_tabs")
    devices = _columns(database, "cloud_tab_devices")
    return (tabs, devices) if tabs and devices else None


def _stored(columns, name, prefix):
    """`prefix.name` when the table has the column, NULL when it does not."""
    return f"{prefix}.{name}" if name in columns else "NULL"


def _cloud_tabs_query(tabs, devices):
    return f"""
        SELECT
            ct.tab_uuid, ct.title, ct.url, ct.is_pinned, ct.is_showing_reader,
            ct.reader_scroll_position_page_index, ctd.device_name,
            ctd.device_uuid, ctd.last_modified, ctd.is_ephemeral_device,
            {_stored(tabs, "last_viewed_time", "ct")},
            {_stored(devices, "device_type_identifier", "ctd")}
        FROM cloud_tabs ct
        LEFT JOIN cloud_tab_devices ctd ON ctd.device_uuid = ct.device_uuid
        ORDER BY ctd.last_modified DESC, ct.rowid, ctd.rowid
    """


def _cloud_devices_query(devices):
    return f"""
        SELECT
            d.last_modified, d.device_name,
            {_stored(devices, "device_type_identifier", "d")}, d.device_uuid,
            (SELECT COUNT(*) FROM cloud_tabs t WHERE t.device_uuid = d.device_uuid),
            d.is_ephemeral_device, d.has_duplicate_device_name
        FROM cloud_tab_devices d
        ORDER BY d.last_modified DESC, d.device_uuid
    """


def _yes_no(value):
    """Yes or No for a stored true or false, blank for no value."""
    if value is None:
        return ""
    return "Yes" if value else "No"


@artifact_processor
def safariCloudTabs(context):
    data_headers = (
        "Tab Title", "URL", ("Last Viewed", "datetime"), "Device Name",
        "Device Type", "Device UUID", ("Device Last Modified", "datetime"),
        "Ephemeral Device", "Pinned", "Showing Reader", "Reader Scroll Page",
        "Tab UUID", "Source File",
    )
    data_list = []
    read_sources = []
    seen = set()
    repeated = 0
    for source, relative_source, store in _stores(context, "CloudTabs.db"):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        read_sources.append(relative_source)
        columns = _cloud_columns(database)
        if columns is None:
            logfunc(f"Safari iCloud Tabs: {relative_source} lacks cloud_tabs or "
                    f"cloud_tab_devices and was not read.")
            database.close()
            continue
        for row in database.execute(_cloud_tabs_query(*columns)):
            (tab_uuid, title, url, is_pinned, is_reader, reader_page,
             device_name, device_uuid, last_modified, is_ephemeral,
             last_viewed, device_type) = row
            record = (store, tuple(row))
            if record in seen:
                repeated += 1
                continue
            seen.add(record)
            data_list.append((
                title or "", url or "", _mac_abs_s_to_utc(last_viewed),
                device_name or "", device_type or "", device_uuid or "",
                _mac_abs_s_to_utc(last_modified),
                "Yes" if is_ephemeral else "",
                "Yes" if is_pinned else "", "Yes" if is_reader else "",
                reader_page if reader_page is not None else "",
                tab_uuid or "", relative_source,
            ))
        database.close()

    logfunc(f"Safari iCloud Tabs: {len(data_list)} tab(s) across "
            f"{len(read_sources)} CloudTabs.db file(s); {repeated} tab(s) held "
            f"by a second copy of a store were not reported again.")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariCloudTabDevices(context):
    data_headers = (
        ("Last Modified", "datetime"), "Device Name", "Device Type",
        "Device UUID", "Tabs", "Ephemeral Device", "Duplicate Device Name",
        "Source File",
    )
    data_list = []
    read_sources = []
    seen = set()
    repeated = 0
    for source, relative_source, store in _stores(context, "CloudTabs.db"):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        read_sources.append(relative_source)
        columns = _cloud_columns(database)
        if columns is None:
            logfunc(f"Safari iCloud Tab Devices: {relative_source} lacks "
                    f"cloud_tabs or cloud_tab_devices and was not read.")
            database.close()
            continue
        for row in database.execute(_cloud_devices_query(columns[1])):
            (last_modified, device_name, device_type, device_uuid, tabs,
             is_ephemeral, has_duplicate_name) = row
            record = (store, tuple(row))
            if record in seen:
                repeated += 1
                continue
            seen.add(record)
            data_list.append((
                _mac_abs_s_to_utc(last_modified), device_name or "",
                device_type or "", device_uuid or "", tabs,
                _yes_no(is_ephemeral), _yes_no(has_duplicate_name),
                relative_source,
            ))
        database.close()

    logfunc(f"Safari iCloud Tab Devices: {len(data_list)} device(s) across "
            f"{len(read_sources)} CloudTabs.db file(s); {repeated} device(s) "
            f"held by a second copy of a store were not reported again.")
    return data_headers, data_list, "\n".join(read_sources)
