"""Firefox browser artifacts. Author: @AlexisBrignoni, Codex."""

__artifacts_v2__ = {'firefoxVisits': {'name': 'Firefox Visits',
                   'description': 'Visit records from Firefox places.sqlite, including URL, title, '
                                  'referring visit, transition, profile, and source file.',
                   'author': '@AlexisBrignoni, Codex',
                   'creation_date': '2026-09-24',
                   'last_update_date': '2026-09-24',
                   'requirements': 'none',
                   'category': 'Firefox',
                   'notes': 'One row per moz_historyvisits record, including redirects and downloads. Times are Unix microseconds. Transition labels follow Mozilla constants. Source Code is stored without inferring synchronization or who initiated a visit. Titles are current URL metadata, not necessarily their value at visit time. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic.'
                            " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                            ' profile folder, under its own name, made unique if taken, inside a Desktop folder named from the '
                            "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                            'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                            'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                            'the home folder because no Desktop is available is not matched. Refresh sources: '
                            'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                            ' '
                            'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                            ' '
                            'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                            ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L595-L596; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L918-L977',
                   'paths': ('*/Library/Application Support/Firefox/Profiles/*/places.sqlite*',
                             '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                             '*/.mozilla/firefox/*/places.sqlite*',
                             '*/Desktop/*Firefox*/*/places.sqlite*'),
                   'output_types': 'standard',
                   'artifact_icon': 'browser',
                   'sample_data': {}},
 'firefoxDownloads': {'name': 'Firefox Downloads',
                      'description': 'Firefox download annotations with source URL, destination '
                                     'URI, stored end time, state, and file size.',
                      'author': '@AlexisBrignoni, Codex',
                      'creation_date': '2026-09-24',
                      'last_update_date': '2026-09-24',
                      'requirements': 'none',
                      'category': 'Firefox',
                      'notes': 'One row per place carrying download annotations. Metadata may be replaced by later downloads of the same URL and is not multiplied by visit rows. End Time is Unix milliseconds; annotation dates are Unix microseconds, not a download start time. State labels follow Mozilla constants. Deleted Flag is stored metadata, not a filesystem check. Invalid JSON is retained with a parse status. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic.'
                               " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                               ' profile folder, under its own name, made unique if taken, inside a Desktop folder named from the '
                               "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                               'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                               'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                               'the home folder because no Desktop is available is not matched. Refresh sources: '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                               ' '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                               ' '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                               ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadHistory.sys.mjs#L27-L36; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadHistory.sys.mjs#L125-L151',
                      'paths': ('*/Library/Application Support/Firefox/Profiles/*/places.sqlite*',
                                '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                                '*/.mozilla/firefox/*/places.sqlite*',
                                '*/Desktop/*Firefox*/*/places.sqlite*'),
                      'output_types': 'standard',
                      'artifact_icon': 'browser',
                      'sample_data': {}},
 'firefoxBookmarks': {'name': 'Firefox Bookmarks',
                      'description': 'Firefox URL bookmark records with stored titles, folder '
                                     'hierarchy, identifiers, and added and modified times.',
                      'author': '@AlexisBrignoni, Codex',
                      'creation_date': '2026-09-24',
                      'last_update_date': '2026-09-24',
                      'requirements': 'none',
                      'category': 'Firefox',
                      'notes': 'Only type 1 URL bookmarks are reported. Folders supply hierarchy and separators are omitted. Times are Unix microseconds. Default and synchronized bookmarks may be present; a bookmark does not establish a local manual save or visit. Broken and cyclic hierarchy references are marked. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic.'
                               " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                               ' profile folder, under its own name, made unique if taken, inside a Desktop folder named from the '
                               "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                               'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                               'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                               'the home folder because no Desktop is available is not matched. Refresh sources: '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                               ' '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                               ' '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                               ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L140-L157',
                      'paths': ('*/Library/Application Support/Firefox/Profiles/*/places.sqlite*',
                                '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                                '*/.mozilla/firefox/*/places.sqlite*',
                                '*/Desktop/*Firefox*/*/places.sqlite*'),
                      'output_types': 'standard',
                      'artifact_icon': 'browser',
                      'sample_data': {}},
 'firefoxCookies': {'name': 'Firefox Cookies',
                    'description': 'Firefox cookie records with host, name, value, path, origin '
                                   'attributes, and stored access, creation, update, and expiry '
                                   'times.',
                    'author': '@AlexisBrignoni, Codex',
                    'creation_date': '2026-09-24',
                    'last_update_date': '2026-09-24',
                    'requirements': 'none',
                    'category': 'Firefox',
                    'notes': 'Access, creation and update times are Unix microseconds. Expiry is seconds before schema 16 and milliseconds from schema 16. The schema 17 migration initializes updateTime for existing rows, so it is not necessarily a server replacement time. Zero or invalid dates remain blank. Cookie access does not establish a top-level page visit. Origin attributes and flags are stored values. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic.'
                             " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                             ' profile folder, under its own name, made unique if taken, inside a Desktop folder named from the '
                             "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                             'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                             'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                             'the home folder because no Desktop is available is not matched. Refresh sources: '
                             'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                             ' '
                             'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                             ' '
                             'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                             ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/netwerk/cookie/CookiePersistentStorage.cpp#L1593-L1614; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/netwerk/cookie/nsICookie.idl#L118-L138',
                    'paths': ('*/Library/Application Support/Firefox/Profiles/*/cookies.sqlite*',
                              '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite*',
                              '*/.mozilla/firefox/*/cookies.sqlite*',
                              '*/Desktop/*Firefox*/*/cookies.sqlite*'),
                    'output_types': 'standard',
                    'artifact_icon': 'browser',
                    'sample_data': {}},
 'firefoxFormHistory': {'name': 'Firefox Form History',
                        'description': 'Firefox saved form-history entries with field names, '
                                       'values, usage counters, linked sources, and first and last '
                                       'used times.',
                        'author': '@AlexisBrignoni, Codex',
                        'creation_date': '2026-09-24',
                        'last_update_date': '2026-09-24',
                        'requirements': 'none',
                        'category': 'Firefox',
                        'notes': 'One row per form-history entry with linked sources in a JSON list. First and last used dates are Unix microseconds. Stored counters do not reconstruct individual submissions. Deletion tombstones are outside this artifact. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic.'
                                 " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                                 ' profile folder, under its own name, made unique if taken, inside a Desktop folder named from the '
                                 "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                                 'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                                 'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                                 'the home folder because no Desktop is available is not matched. Refresh sources: '
                                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                                 ' '
                                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                                 ' '
                                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                                 ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/satchel/FormHistory.sys.mjs#L390-L430',
                        'paths': ('*/Library/Application '
                                  'Support/Firefox/Profiles/*/formhistory.sqlite*',
                                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/formhistory.sqlite*',
                                  '*/.mozilla/firefox/*/formhistory.sqlite*',
                                  '*/Desktop/*Firefox*/*/formhistory.sqlite*'),
                        'output_types': 'standard',
                        'artifact_icon': 'browser',
                        'sample_data': {}},
 'firefoxInteractions': {'name': 'Firefox Page Interactions',
                         'description': 'Firefox page-interaction records with URLs, stored view '
                                        'and typing durations, keypress counters, and scrolling '
                                        'measurements.',
                         'author': '@AlexisBrignoni, Codex',
                         'creation_date': '2026-09-24',
                         'last_update_date': '2026-09-24',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': 'One row per moz_places_metadata record. Dates and durations use milliseconds; scrolling distance uses pixels. Browser measurements do not establish attention, typed text or a complete session. Document Type is a stored integer. Search-query joins are outside this artifact. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic.'
                                  " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                                  ' profile folder, under its own name, made unique if taken, inside a Desktop folder named from the '
                                  "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                                  'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                                  'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                                  'the home folder because no Desktop is available is not matched. Refresh sources: '
                                  'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                                  ' '
                                  'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                                  ' '
                                  'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                                  ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/browser/components/places/Interactions.sys.mjs#L88-L113',
                         'paths': ('*/Library/Application '
                                   'Support/Firefox/Profiles/*/places.sqlite*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                                   '*/.mozilla/firefox/*/places.sqlite*',
                                   '*/Desktop/*Firefox*/*/places.sqlite*'),
                         'output_types': 'standard',
                         'artifact_icon': 'browser',
                         'sample_data': {}},
                  'firefoxFavicons': {'name': 'Firefox Favicons',
                         'description': 'Page and icon records from Firefox favicons.sqlite: page URL, icon URL, icon and link expiry, width, root and flags as stored, icon size, profile, and source file.',
                         'author': '@AlexisBrignoni, Claude',
                         'creation_date': '2026-09-26',
                         'last_update_date': '2026-09-26',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': "One row per link in moz_icons_to_pages between a page in moz_pages_w_icons and an icon in moz_icons, then one row for each icon in moz_icons that no link names, with Page URL and Link Expires blank. Firefox does not link root icons to pages: an icon whose host is the page's host and whose path is /favicon.ico is treated as valid for the whole origin, and no page URL or link is written for it (References: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/nsFaviconService.cpp#L421-L427; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L778-L783). Icon Expires is moz_icons.expire_ms and Link Expires is moz_icons_to_pages.expire_ms, read as milliseconds since 1970 UTC: Firefox writes both as its microsecond time divided by 1000 (icons: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L246 and https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L269; links: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L828 and https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L1061-L1077) and reads the icon value back multiplied by 1000 (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L338-L341). A stored 0, the column default, is left blank. Width is the stored width; Firefox treats icons as square, keeps one size, and stores 65535 for an SVG icon (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/nsPlacesTables.h#L232-L236). Root (as stored) is moz_icons.root. Flags (as stored) is moz_icons.flags, a bitset whose bit 0 Firefox names ICONDATA_FLAGS_RICH (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/nsIFaviconService.idl#L18-L19); what makes an icon rich is not stated there. Icon Size (bytes) is the length of the stored icon data; the image is not rendered. Icon ID is moz_icons.id. A row records that Firefox stored an icon for a page or an origin; it is not established as a visit, and Firefox's own comment says history removal also expires orphan icons (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/FaviconHelpers.cpp#L790-L792). Table definitions: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/places/nsPlacesTables.h#L224-L263. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Source File shows which copy a row came from. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
                         'paths': ('*/Library/Application Support/Firefox/Profiles/*/favicons.sqlite*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/favicons.sqlite*',
                                   '*/.mozilla/firefox/*/favicons.sqlite*',
                                   '*/Desktop/*Firefox*/*/favicons.sqlite*'),
                         'output_types': 'standard',
                         'artifact_icon': 'photo',
                         'sample_data': {}},
                  'firefoxLocalStorage': {'name': 'Firefox Local Storage',
                         'description': 'Keys and values from each origin LocalStorage database in a Firefox profile, decoded from their stored compression and encoding, with origin, stored lengths and types, profile, and source file.',
                         'author': '@AlexisBrignoni, Claude',
                         'creation_date': '2026-09-26',
                         'last_update_date': '2026-09-26',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': "One row per key in the data table of each origin's LocalStorage database, storage/default/<origin>/ls/data.sqlite in a Firefox profile (table definitions: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/ActorsParent.cpp#L367-L374 and https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/ActorsParent.cpp#L383-L389). Origin is the origin column of that database's database table. Value is the stored value decoded as Firefox's LSValue decodes it (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/LSValue.h#L38-L48; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/LSValue.cpp#L80-L90): a Compression Type of 1 is raw Snappy, which Firefox reads with snappy::RawUncompress (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/SnappyUtils.cpp#L51-L75); it is decompressed here by a decoder written from Google's format description (https://github.com/google/snappy/blob/9c28114a38866f6deeaa826db918293bc28ae410/format_description.txt), which rejects a stream whose output is not exactly the length the stream declares. A Conversion Type of 1 means the value was stored as UTF-8; 0 means Firefox copied the UTF-16 code units' bytes unchanged, which it does only for a value that is not valid UTF-16 (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/LSValue.cpp#L19-L31; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/LSValue.cpp#L104-L118), and such a value is decoded here as little-endian UTF-16 with anything that is not valid UTF-16 replaced. A value that cannot be decoded is left blank, and the run log counts those values and any decoded value whose UTF-16 length differs from the utf16_length Firefox stored. UTF-16 Length (as stored), Conversion Type (as stored) and Compression Type (as stored) are the stored columns, and Stored Size (bytes) is the length of the stored value. The last_access_time column is not reported: in Firefox's LocalStorage source it appears where the table is created and where rows are copied from an older schema (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/localstorage/ActorsParent.cpp#L448-L464), and no code that updates it was found. Keys and values are written by each site's own scripts, and what they record is not established. Profile is the folder that holds storage/default in the store's path. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Source File shows which copy a row came from. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
                         'paths': ('*/Library/Application Support/Firefox/Profiles/*/storage/default/*/ls/data.sqlite*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/storage/default/*/ls/data.sqlite*',
                                   '*/.mozilla/firefox/*/storage/default/*/ls/data.sqlite*',
                                   '*/Desktop/*Firefox*/*/storage/default/*/ls/data.sqlite*'),
                         'output_types': 'standard',
                         'artifact_icon': 'database',
                         'sample_data': {}},
                  'firefoxIndexedDB': {'name': 'Firefox IndexedDB',
                         'description': 'Records from the IndexedDB databases in a Firefox profile\'s origin storage, with origin, database, object store, key and value (decoded to JSON where the format allows), decode status, file references, profile, and source file.',
                         'author': '@AlexisBrignoni, Claude',
                         'creation_date': '2026-09-26',
                         'last_update_date': '2026-09-26',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': 'One row per record in the object_data table of each IndexedDB database, storage/default/<origin>/idb/<name>.sqlite in a Firefox profile. Origin and Database are the origin and name columns of that file\'s database table, and Object Store is the name of the record\'s object store (table definitions: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/DBSchema.cpp#L91-L129). Key is the record\'s key decoded as Firefox\'s Key.cpp decodes it (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/Key.cpp#L467-L545; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/Key.cpp#L755-L848; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/Key.cpp#L872-L891; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/Key.cpp#L959-L982), written as JSON. Value is the record\'s value, which Firefox stores as a SpiderMonkey structured-clone buffer compressed with raw Snappy (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/ActorsParent.cpp#L19366-L19392); it is decompressed by a decoder written from Google\'s format description (https://github.com/google/snappy/blob/9c28114a38866f6deeaa826db918293bc28ae410/format_description.txt) and read by a reader that follows SpiderMonkey\'s own read loop (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/js/src/vm/StructuredClone.cpp#L4081-L4227; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/js/src/vm/StructuredClone.cpp#L3137-L3451), then written as JSON. A Date is written as {"$date": ...} in UTC, an ArrayBuffer as {"$arraybuffer": ...} in hex, a Map as {"$map": [[key, value], ...]}, a Set as {"$set": [...]}, undefined as {"$undefined": true}, a regular expression as {"$regexp": ..., "flags": ...}, a number that is not finite as {"$number": ...}, and a reference to an object already read as {"$backref": n}, n being its position in read order; a Boolean, String or Number object is written as its value. Decode Status says whether the value was decoded. A value that uses a part of the format not read here is left blank and Decode Status names what stopped it, for example a Firefox DOM object tag such as SCTAG_DOM_BLOB, a typed array, a DataView, a BigInt, an error or saved frame object, or a transfer map (tag lists: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/js/src/vm/StructuredClone.cpp#L101-L175; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/base/StructuredCloneTags.h#L17-L80). A value Firefox wrote to a separate file because it was over its size threshold is stored as an integer instead of a blob, holding flags in its upper 32 bits and a position in the record\'s file_ids in its lower 32 bits (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/indexedDB/ActorsParent.cpp#L19348-L19362); it is not read here and Decode Status says so. The run log counts each kind of value not decoded. File IDs (as stored) is the file_ids column. What the keys and values record is not established; they are reported as stored. Profile is the folder that holds storage/default in the store\'s path. SQLite WAL files are included. Profiles remain separate; User is blank when source paths do not identify an account. Byte-identical macOS firmlink database/WAL copies are deduplicated. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox\'s Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, \'Old %S Data\' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Source File shows which copy a row came from. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.',
                         'paths': ('*/Library/Application Support/Firefox/Profiles/*/storage/default/*/idb/*.sqlite*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/storage/default/*/idb/*.sqlite*',
                                   '*/.mozilla/firefox/*/storage/default/*/idb/*.sqlite*',
                                   '*/Desktop/*Firefox*/*/storage/default/*/idb/*.sqlite*'),
                         'output_types': 'standard',
                         'artifact_icon': 'database',
                         'sample_data': {}},
                  'firefoxSessionStore': {'name': 'Firefox Session Store',
                         'description': "Tabs recorded in a Firefox profile's session store files (open tabs, recently closed tabs and windows, and tab groups), one row per tab history entry, with last accessed and closed times, URL, title, container, session file, profile and source file.",
                         'author': '@AlexisBrignoni, Claude',
                         'creation_date': '2026-09-26',
                         'last_update_date': '2026-09-26',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': "One row per session history entry of each tab in each session file of a Firefox profile: sessionstore.jsonlz4 in the profile folder, and previous.jsonlz4, recovery.jsonlz4, recovery.baklz4 and upgrade.jsonlz4-<platform build ID> in its sessionstore-backups folder (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionFile.sys.mjs#L73-L121; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionFile.sys.mjs#L129-L142). Older Firefox versions wrote the same files uncompressed with .js and .bak names (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionFile.sys.mjs#L187-L189; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionFile.sys.mjs#L211-L220), and those are read too. Each file is a separate copy of the session state, so one tab can appear in several files; Session File names the file a row came from. A compressed file holds the bytes mozLz40, the uncompressed size and one LZ4 block (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/xpcom/ioutils/IOUtils.h#L748-L766; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/xpcom/ioutils/IOUtils.cpp#L2661-L2710), decompressed by a decoder written from the LZ4 block format description (https://github.com/lz4/lz4/blob/0774d05537f9762f838f7ab541b7765f1a729cb5/doc/lz4_Block_format.md#L25-L136). Scope says where the tab sits in the state: Open tab is a window's tabs, Closed tab a window's _closedTabs, Tab in closed window and Closed tab in closed window the same two lists in _closedWindows, and Tab in closed group and Tab in saved group the tabs of closed and saved tab groups. The prefix Last session: marks tabs in lastSessionState, the previous session Firefox keeps in the file while its restore is deferred (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionStore.sys.mjs#L5733-L5736). Structure definitions: https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionStore.sys.mjs#L10-L86; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/TabState.sys.mjs#L7-L101; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/TabGroupState.sys.mjs#L10-L73. Last Accessed is the tab's lastAccessed, which the definition describes as when the tab was last selected, and Closed At the closedAt of the closed tab, of the window for a tab in a closed window, or of the group for a group tab that has none of its own; the definitions give both as Date.now() values, milliseconds since 1970. Session Updated is session.lastUpdate, the Date.now() value taken when the state was collected (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/sessionstore/SessionStore.sys.mjs#L5711-L5724). Window and Position are 1-based positions in the lists the file holds, and Window is blank for a saved group; the definition gives a window's closed tabs most recently closed first. Entry is the 1-based position in the tab's entries, which the definition gives oldest first, and Current Entry is Yes for the entry the tab's 1-based index names. URL, Title and Original URI are the entry's url, title and originalURI (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/sessionstore/SessionHistory.sys.mjs#L153-L174). User Interaction (as stored) is the entry's hasUserInteraction, copied from session history (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/sessionstore/SessionHistory.sys.mjs#L248); what it records is not established here. Subframe entries, held in an entry's children (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/sessionstore/SessionHistory.sys.mjs#L275-L286), are not reported. Container ID is the tab's userContextId, 0 for the default container. Pinned and Hidden are the tab's pinned and hidden values as stored, blank when the file omits them. Tab Group is the name of the tab's group, blank for a tab that belongs to none. Form data, scroll positions, session storage and cookies the file holds are not reported. Profile is the folder that holds the file, or the folder above sessionstore-backups for a backup. Profiles remain separate; User is blank when source paths do not identify an account. A byte-identical copy of a file under the macOS firmlink path System/Volumes/Data is read once. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Source File shows which copy a row came from. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
                         'paths': ('*/Library/Application Support/Firefox/Profiles/*/sessionstore.js*',
                                   '*/Library/Application Support/Firefox/Profiles/*/sessionstore-backups/*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/sessionstore.js*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/sessionstore-backups/*',
                                   '*/.mozilla/firefox/*/sessionstore.js*',
                                   '*/.mozilla/firefox/*/sessionstore-backups/*',
                                   '*/Desktop/*Firefox*/*/sessionstore.js*',
                                   '*/Desktop/*Firefox*/*/sessionstore-backups/*'),
                         'output_types': 'standard',
                         'artifact_icon': 'browser',
                         'sample_data': {}},
                  'firefoxSavedLogins': {'name': 'Firefox Saved Logins',
                         'description': "Saved logins in a Firefox profile's logins.json, logins-backup.json and logins.db, with creation, last use and change times, use count, site and form fields; the encrypted username and password are not reported.",
                         'author': '@AlexisBrignoni, Claude',
                         'creation_date': '2026-09-26',
                         'last_update_date': '2026-09-26',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': "One row per saved login in each Firefox profile's logins.json, its backup copy logins-backup.json, and the local table loginsL and mirror table loginsM of logins.db; Store names which one the row came from (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/storage-json.sys.mjs#L105-L118; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/LoginStore.sys.mjs#L117-L119; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/storage-rust.sys.mjs#L458-L459). Firefox opens both logins.json and logins.db at startup and a migrator picks the store it uses (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/storage-desktop.sys.mjs#L22-L39); this artifact reads both, and GUID is the value Firefox uses to identify a login (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/nsILoginMetaInfo.idl#L20-L28). The logins.json fields hostname and formSubmitURL are reported as Origin and Form Action Origin, the names Firefox gives those values when it writes them (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/storage-json.sys.mjs#L288-L308). Time Created, Time Last Used, Time Password Changed and Breach Alert Dismissed are timeCreated, timeLastUsed, timePasswordChanged and timeLastBreachAlertDismissed, which Firefox defines in Unix epoch milliseconds as the login's first creation, the last time it was submitted in a form or used to begin an HTTP auth session, the last time it was modified, which counts a change of username as well as of password, and the last time the user dismissed its breach alert, blank if it was never dismissed (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/nsILoginMetaInfo.idl#L30-L59). Times Used is timesUsed, the number of times the login was submitted in a form or used to begin an HTTP auth session. The logins.db schema also stores its times in milliseconds (https://github.com/mozilla/application-services/blob/7f0fd9266205f4d88c657fa2e65a94c020f87963/components/logins/src/schema.rs#L99-L113). HTTP Realm is blank for a login obtained from an HTML form, and Form Action Origin for one obtained from HTTP or FTP authentication (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/passwordmgr/nsILoginInfo.idl#L36-L65). Local Modified is loginsL.local_modified, when the record was changed locally, blank if it never was; Server Modified is loginsM.server_modified, the most recent server modification time seen for the record; Deleted (as stored) is loginsL.is_deleted, set on a tombstone; Sync Status is loginsL.sync_status with its name, 0 Synced, 1 Changed and 2 New; and Mirror Overridden (as stored) is loginsM.is_overridden, set when the mirror copy is to be ignored in favour of loginsL (https://github.com/mozilla/application-services/blob/7f0fd9266205f4d88c657fa2e65a94c020f87963/components/logins/src/schema.rs#L28-L73). Local Modified, Server Modified, Deleted (as stored), Sync Status and Mirror Overridden (as stored) are blank on rows from logins.json, which has no such fields, and each is blank on rows from the logins.db table that lacks it. The encrypted username and password are not reported and not decrypted. Profile is the folder that holds the file. Profiles remain separate; User is blank when source paths do not identify an account. A byte-identical copy of a file, with its WAL, under the macOS firmlink path System/Volumes/Data is read once. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Source File shows which copy a row came from. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
                         'paths': ('*/Library/Application Support/Firefox/Profiles/*/logins.db*',
                                   '*/Library/Application Support/Firefox/Profiles/*/logins*.json',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/logins.db*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/logins*.json',
                                   '*/.mozilla/firefox/*/logins.db*',
                                   '*/.mozilla/firefox/*/logins*.json',
                                   '*/Desktop/*Firefox*/*/logins.db*',
                                   '*/Desktop/*Firefox*/*/logins*.json'),
                         'output_types': 'standard',
                         'artifact_icon': 'key',
                         'sample_data': {}}}

from scripts import firefox
from scripts import firefox_indexeddb
from scripts import firefox_logins
from scripts import firefox_session
from scripts.ilapfuncs import artifact_processor


@artifact_processor
def firefoxVisits(context):
    data_headers = (('Visit Time', 'datetime'),
     'Visit ID',
     'Place ID',
     'URL',
     'Title',
     'Transition Code',
     'Transition',
     'Source Code (as stored)',
     'Referring Visit ID',
     'Referring URL',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'places.sqlite', firefox.visits, 'Firefox Visits')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxDownloads(context):
    data_headers = (('End Time', 'datetime'),
     ('Annotation Added', 'datetime'),
     ('Annotation Modified', 'datetime'),
     'Place ID',
     'URL',
     'Destination URI',
     'State Code',
     'State',
     'File Size (bytes)',
     'Deleted Flag (as stored)',
     'Metadata Status',
     'Metadata JSON',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'places.sqlite', firefox.downloads, 'Firefox Downloads')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxBookmarks(context):
    data_headers = (('Added Time', 'datetime'),
     ('Modified Time', 'datetime'),
     'Bookmark ID',
     'GUID',
     'Title',
     'URL',
     'Folder Path',
     'Position',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'places.sqlite', firefox.bookmarks, 'Firefox Bookmarks')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxCookies(context):
    data_headers = (('Last Accessed', 'datetime'),
     ('Created', 'datetime'),
     ('Updated', 'datetime'),
     ('Expires', 'datetime'),
     'Cookie ID',
     'Host',
     'Path',
     'Name',
     'Value',
     'Origin Attributes',
     'Secure Flag (as stored)',
     'HTTP Only Flag (as stored)',
     'SameSite Code (as stored)',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'cookies.sqlite', firefox.cookies, 'Firefox Cookies')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxFormHistory(context):
    data_headers = (('Last Used', 'datetime'),
     ('First Used', 'datetime'),
     'Entry ID',
     'GUID',
     'Field Name',
     'Value',
     'Times Used',
     'Sources (JSON)',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'formhistory.sqlite', firefox.form_history, 'Firefox Form History')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxInteractions(context):
    data_headers = (('Created', 'datetime'),
     ('Updated', 'datetime'),
     'Interaction ID',
     'Place ID',
     'URL',
     'Title',
     'Referring URL',
     'View Time (ms)',
     'Typing Time (ms)',
     'Keypress Count',
     'Scrolling Time (ms)',
     'Scrolling Distance (pixels)',
     'Document Type (as stored)',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'places.sqlite', firefox.interactions, 'Firefox Page Interactions')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxFavicons(context):
    data_headers = (('Icon Expires', 'datetime'),
     ('Link Expires', 'datetime'),
     'Page URL',
     'Icon URL',
     'Width',
     'Root (as stored)',
     'Flags (as stored)',
     'Icon Size (bytes)',
     'Icon ID',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'favicons.sqlite', firefox.favicons, 'Firefox Favicons')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxLocalStorage(context):
    data_headers = ('Origin',
     'Key',
     'Value',
     'UTF-16 Length (as stored)',
     'Conversion Type (as stored)',
     'Compression Type (as stored)',
     'Stored Size (bytes)',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox.read_local_storage(context, 'Firefox Local Storage')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxIndexedDB(context):
    data_headers = ('Origin',
     'Database',
     'Object Store',
     'Key',
     'Value',
     'Decode Status',
     'File IDs (as stored)',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox_indexeddb.read_indexeddb(context, 'Firefox IndexedDB')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxSessionStore(context):
    data_headers = (('Last Accessed', 'datetime'),
     ('Closed At', 'datetime'),
     ('Session Updated', 'datetime'),
     'Scope',
     'Window',
     'Position',
     'Entry',
     'Current Entry',
     'URL',
     'Title',
     'Original URI',
     'User Interaction (as stored)',
     'Container ID',
     'Pinned',
     'Hidden',
     'Tab Group',
     'Session File',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox_session.read_session_store(context, 'Firefox Session Store')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxSavedLogins(context):
    data_headers = (('Time Created', 'datetime'),
     ('Time Last Used', 'datetime'),
     ('Time Password Changed', 'datetime'),
     ('Breach Alert Dismissed', 'datetime'),
     ('Local Modified', 'datetime'),
     ('Server Modified', 'datetime'),
     'Times Used',
     'Origin',
     'Form Action Origin',
     'HTTP Realm',
     'Username Field',
     'Password Field',
     'GUID',
     'Store',
     'Deleted (as stored)',
     'Sync Status',
     'Mirror Overridden (as stored)',
     'Profile',
     'User',
     'Source File')
    data_list, source_path = firefox_logins.read_saved_logins(context, 'Firefox Saved Logins')
    return data_headers, data_list, source_path
