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
                         'sample_data': {}}}

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
