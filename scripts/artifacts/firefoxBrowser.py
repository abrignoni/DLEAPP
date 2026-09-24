"""Firefox browser artifacts. Author: @AlexisBrignoni, Codex."""

__artifacts_v2__ = {'firefoxVisits': {'name': 'Firefox Visits',
                   'description': 'Visit records from Firefox places.sqlite, including URL, title, '
                                  'referring visit, transition, profile, and source file.',
                   'author': '@AlexisBrignoni, Codex',
                   'creation_date': '2026-09-24',
                   'last_update_date': '2026-09-24',
                   'requirements': 'none',
                   'category': 'Firefox',
                   'notes': 'One row per moz_historyvisits record, including redirects and '
                            'downloads. Visit types follow Mozilla constants; Source Code is the '
                            'stored integer, not an assertion about synchronization or the person '
                            'who initiated a visit. Visit timestamps are Unix microseconds. A URL '
                            'title is current stored metadata, not necessarily its title at the '
                            'visit time. References: '
                            'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L595-L596; '
                            'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L918-L977. '
                            'Tested against Firefox 156.0 on the '
                            'brunofischer_macos27_fuji_20260924 corpus. Reads allocated SQLite '
                            'rows with accompanying WAL files. Deleted-row recovery, session '
                            'restore, saved logins, IndexedDB, local storage, caches, and '
                            'extension data are not covered. Profile and source paths distinguish '
                            'stores; User is blank for a user-folder-only extraction whose path '
                            'does not name the account. Windows and Linux paths are covered by '
                            'synthetic tests, not real images. Byte-identical macOS firmlink '
                            'copies are deduplicated only when the database and WAL match. See '
                            'admin/docs/firefox-corpus-20260924.md for surveyed exclusions and '
                            'validation.  Profile holds one value on all rows in this sample '
                            'because one populated profile was acquired; it distinguishes profiles '
                            'in larger extractions. ',
                   'paths': ('*/Library/Application Support/Firefox/Profiles/*/places.sqlite*',
                             '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                             '*/.mozilla/firefox/*/places.sqlite*'),
                   'output_types': 'standard',
                   'artifact_icon': 'browser',
                   'sample_data': {'brunofischer_macos27_fuji_20260924': 'Firefox 156.0; 267 rows '
                                                                         'from one macOS 27 '
                                                                         'user-folder '
                                                                         'acquisition.'}},
 'firefoxDownloads': {'name': 'Firefox Downloads',
                      'description': 'Firefox download annotations with source URL, destination '
                                     'URI, stored end time, state, and file size.',
                      'author': '@AlexisBrignoni, Codex',
                      'creation_date': '2026-09-24',
                      'last_update_date': '2026-09-24',
                      'requirements': 'none',
                      'category': 'Firefox',
                      'notes': 'One row per place with downloads/destinationFileURI or '
                               'downloads/metaData annotations; repeated downloads of the same URL '
                               'can overwrite this metadata. The metadata is not joined to every '
                               'visit and annotation creation is not labeled download start. End '
                               'Time uses metadata.endTime (Unix milliseconds); Annotation Added '
                               'and Modified use Unix microseconds. State names follow Mozilla '
                               'constants; Deleted Flag is stored metadata, not a check of the '
                               'target file. Invalid JSON retains the destination and raw metadata '
                               'with a parse status. All eight tested records have FINISHED state '
                               'and false Deleted Flag; other states and malformed metadata are '
                               'tested synthetically. References: '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadHistory.sys.mjs#L27-L36; '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadHistory.sys.mjs#L125-L151. '
                               'Tested against Firefox 156.0 on the '
                               'brunofischer_macos27_fuji_20260924 corpus. Reads allocated SQLite '
                               'rows with accompanying WAL files. Deleted-row recovery, session '
                               'restore, saved logins, IndexedDB, local storage, caches, and '
                               'extension data are not covered. Profile and source paths '
                               'distinguish stores; User is blank for a user-folder-only '
                               'extraction whose path does not name the account. Windows and Linux '
                               'paths are covered by synthetic tests, not real images. '
                               'Byte-identical macOS firmlink copies are deduplicated only when '
                               'the database and WAL match. See '
                               'admin/docs/firefox-corpus-20260924.md for surveyed exclusions and '
                               'validation.  Profile holds one value on all rows in this sample '
                               'because one populated profile was acquired; it distinguishes '
                               'profiles in larger extractions. In this sample State Code is 1 on '
                               'all rows, Deleted Flag is false on all rows, and Metadata Status '
                               'is Parsed on all rows. Annotation Added and Annotation Modified '
                               'are identical on all eight rows. These fields retain the '
                               'distinction when metadata changes or a download is unsuccessful. ',
                      'paths': ('*/Library/Application Support/Firefox/Profiles/*/places.sqlite*',
                                '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                                '*/.mozilla/firefox/*/places.sqlite*'),
                      'output_types': 'standard',
                      'artifact_icon': 'browser',
                      'sample_data': {'brunofischer_macos27_fuji_20260924': 'Firefox 156.0; 8 rows '
                                                                            'from one macOS 27 '
                                                                            'user-folder '
                                                                            'acquisition.'}},
 'firefoxBookmarks': {'name': 'Firefox Bookmarks',
                      'description': 'Firefox URL bookmark records with stored titles, folder '
                                     'hierarchy, identifiers, and added and modified times.',
                      'author': '@AlexisBrignoni, Codex',
                      'creation_date': '2026-09-24',
                      'last_update_date': '2026-09-24',
                      'requirements': 'none',
                      'category': 'Firefox',
                      'notes': 'Only moz_bookmarks type 1 rows are emitted. Folder rows supply '
                               'hierarchy; separators are omitted. Timestamps are Unix '
                               'microseconds. Default and synchronized bookmarks may be present; a '
                               'bookmark row does not establish a local manual save or a visit. '
                               'Cyclic or missing parents are marked instead of dropping the '
                               'bookmark. Reference: '
                               'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L140-L157. '
                               'Tested against Firefox 156.0 on the '
                               'brunofischer_macos27_fuji_20260924 corpus. Reads allocated SQLite '
                               'rows with accompanying WAL files. Deleted-row recovery, session '
                               'restore, saved logins, IndexedDB, local storage, caches, and '
                               'extension data are not covered. Profile and source paths '
                               'distinguish stores; User is blank for a user-folder-only '
                               'extraction whose path does not name the account. Windows and Linux '
                               'paths are covered by synthetic tests, not real images. '
                               'Byte-identical macOS firmlink copies are deduplicated only when '
                               'the database and WAL match. See '
                               'admin/docs/firefox-corpus-20260924.md for surveyed exclusions and '
                               'validation.  Profile holds one value on all rows in this sample '
                               'because one populated profile was acquired; it distinguishes '
                               'profiles in larger extractions. In this sample Added Time and '
                               'Modified Time each hold one value on all rows, and Folder Path is '
                               'uniformly root________ / menu / Mozilla Firefox. The four URLs are '
                               'Mozilla product/support bookmarks and are not evidence of a manual '
                               'user save; user-created bookmarks are exercised synthetically. The '
                               'dates and hierarchy remain useful to distinguish bookmarks in '
                               'other profiles. ',
                      'paths': ('*/Library/Application Support/Firefox/Profiles/*/places.sqlite*',
                                '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                                '*/.mozilla/firefox/*/places.sqlite*'),
                      'output_types': 'standard',
                      'artifact_icon': 'browser',
                      'sample_data': {'brunofischer_macos27_fuji_20260924': 'Firefox 156.0; 4 rows '
                                                                            'from one macOS 27 '
                                                                            'user-folder '
                                                                            'acquisition.'}},
 'firefoxCookies': {'name': 'Firefox Cookies',
                    'description': 'Firefox cookie records with host, name, value, path, origin '
                                   'attributes, and stored access, creation, update, and expiry '
                                   'times.',
                    'author': '@AlexisBrignoni, Codex',
                    'creation_date': '2026-09-24',
                    'last_update_date': '2026-09-24',
                    'requirements': 'none',
                    'category': 'Firefox',
                    'notes': 'Last Accessed, Created and Updated are Unix microseconds. Cookie '
                             'expiry is seconds for schemas before 16 and milliseconds for schema '
                             '16 and later. Updated may reflect migration: Mozilla initializes '
                             'existing rows to the migration time when upgrading schema 16 to 17, '
                             'so it is not necessarily a server replacement time. Zero or invalid '
                             'dates are blank. Cookie presence or access does not establish a '
                             'top-level page visit; third-party and partitioned cookies are '
                             'included. Origin Attributes and flag values are retained as stored. '
                             'Only schema 17 is real-corpus validated; the older expiry format is '
                             'tested synthetically. References: '
                             'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/netwerk/cookie/CookiePersistentStorage.cpp#L1593-L1614; '
                             'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/netwerk/cookie/nsICookie.idl#L118-L138. '
                             'Tested against Firefox 156.0 on the '
                             'brunofischer_macos27_fuji_20260924 corpus. Reads allocated SQLite '
                             'rows with accompanying WAL files. Deleted-row recovery, session '
                             'restore, saved logins, IndexedDB, local storage, caches, and '
                             'extension data are not covered. Profile and source paths distinguish '
                             'stores; User is blank for a user-folder-only extraction whose path '
                             'does not name the account. Windows and Linux paths are covered by '
                             'synthetic tests, not real images. Byte-identical macOS firmlink '
                             'copies are deduplicated only when the database and WAL match. See '
                             'admin/docs/firefox-corpus-20260924.md for surveyed exclusions and '
                             'validation.  Profile holds one value on all rows in this sample '
                             'because one populated profile was acquired; it distinguishes '
                             'profiles in larger extractions. ',
                    'paths': ('*/Library/Application Support/Firefox/Profiles/*/cookies.sqlite*',
                              '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite*',
                              '*/.mozilla/firefox/*/cookies.sqlite*'),
                    'output_types': 'standard',
                    'artifact_icon': 'browser',
                    'sample_data': {'brunofischer_macos27_fuji_20260924': 'Firefox 156.0; 317 rows '
                                                                          'from one macOS 27 '
                                                                          'user-folder '
                                                                          'acquisition.'}},
 'firefoxFormHistory': {'name': 'Firefox Form History',
                        'description': 'Firefox saved form-history entries with field names, '
                                       'values, usage counters, linked sources, and first and last '
                                       'used times.',
                        'author': '@AlexisBrignoni, Codex',
                        'creation_date': '2026-09-24',
                        'last_update_date': '2026-09-24',
                        'requirements': 'none',
                        'category': 'Firefox',
                        'notes': 'One row per moz_formhistory record, with all linked moz_sources '
                                 'values as a JSON list. Counters and values are stored browser '
                                 'data, not a reconstruction of individual submissions. First Used '
                                 'and Last Used are Unix microseconds. The tested '
                                 'moz_deleted_formhistory table is empty; deletion tombstones are '
                                 'not reported. Six of seven entries have a source relationship in '
                                 'the tested image. Reference: '
                                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/satchel/FormHistory.sys.mjs#L390-L430. '
                                 'Tested against Firefox 156.0 on the '
                                 'brunofischer_macos27_fuji_20260924 corpus. Reads allocated '
                                 'SQLite rows with accompanying WAL files. Deleted-row recovery, '
                                 'session restore, saved logins, IndexedDB, local storage, caches, '
                                 'and extension data are not covered. Profile and source paths '
                                 'distinguish stores; User is blank for a user-folder-only '
                                 'extraction whose path does not name the account. Windows and '
                                 'Linux paths are covered by synthetic tests, not real images. '
                                 'Byte-identical macOS firmlink copies are deduplicated only when '
                                 'the database and WAL match. See '
                                 'admin/docs/firefox-corpus-20260924.md for surveyed exclusions '
                                 'and validation.  Profile holds one value on all rows in this '
                                 'sample because one populated profile was acquired; it '
                                 'distinguishes profiles in larger extractions. In this sample '
                                 'Times Used is 1 on all rows and Last Used and First Used are '
                                 'identical on all seven rows. These fields describe the stored '
                                 'entry lifetime and count rather than separate submission '
                                 'events. ',
                        'paths': ('*/Library/Application '
                                  'Support/Firefox/Profiles/*/formhistory.sqlite*',
                                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/formhistory.sqlite*',
                                  '*/.mozilla/firefox/*/formhistory.sqlite*'),
                        'output_types': 'standard',
                        'artifact_icon': 'browser',
                        'sample_data': {'brunofischer_macos27_fuji_20260924': 'Firefox 156.0; 7 '
                                                                              'rows from one macOS '
                                                                              '27 user-folder '
                                                                              'acquisition.'}},
 'firefoxInteractions': {'name': 'Firefox Page Interactions',
                         'description': 'Firefox page-interaction records with URLs, stored view '
                                        'and typing durations, keypress counters, and scrolling '
                                        'measurements.',
                         'author': '@AlexisBrignoni, Codex',
                         'creation_date': '2026-09-24',
                         'last_update_date': '2026-09-24',
                         'requirements': 'none',
                         'category': 'Firefox',
                         'notes': 'One row per moz_places_metadata record. Created and Updated are '
                                  'Unix milliseconds. Durations are stored milliseconds and '
                                  'scrolling distance is stored pixels, following Mozilla field '
                                  'definitions. These are browser measurements, not proof of '
                                  'attention, typed text, or a complete browsing session. Document '
                                  'Type is retained as an integer. The tested '
                                  'moz_places_metadata_search_queries table is empty and '
                                  'search-query joins are not implemented. Reference: '
                                  'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/browser/components/places/Interactions.sys.mjs#L88-L113. '
                                  'Tested against Firefox 156.0 on the '
                                  'brunofischer_macos27_fuji_20260924 corpus. Reads allocated '
                                  'SQLite rows with accompanying WAL files. Deleted-row recovery, '
                                  'session restore, saved logins, IndexedDB, local storage, '
                                  'caches, and extension data are not covered. Profile and source '
                                  'paths distinguish stores; User is blank for a user-folder-only '
                                  'extraction whose path does not name the account. Windows and '
                                  'Linux paths are covered by synthetic tests, not real images. '
                                  'Byte-identical macOS firmlink copies are deduplicated only when '
                                  'the database and WAL match. See '
                                  'admin/docs/firefox-corpus-20260924.md for surveyed exclusions '
                                  'and validation.  Profile holds one value on all rows in this '
                                  'sample because one populated profile was acquired; it '
                                  'distinguishes profiles in larger extractions. In this sample '
                                  'Document Type is 0 on all rows; it is retained to distinguish '
                                  'other stored document types without guessing a label. ',
                         'paths': ('*/Library/Application '
                                   'Support/Firefox/Profiles/*/places.sqlite*',
                                   '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite*',
                                   '*/.mozilla/firefox/*/places.sqlite*'),
                         'output_types': 'standard',
                         'artifact_icon': 'browser',
                         'sample_data': {'brunofischer_macos27_fuji_20260924': 'Firefox 156.0; 50 '
                                                                               'rows from one '
                                                                               'macOS 27 '
                                                                               'user-folder '
                                                                               'acquisition.'}}}

from scripts import firefox
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
