"""Firefox settings artifacts. Author: @AlexisBrignoni, Codex."""

__artifacts_v2__ = {
    'firefoxSitePermissions': {
        'name': 'Firefox Site Permissions',
        'description': 'Stored Firefox origin permissions with modification and expiry times, permission types, and raw capability codes.',
        'author': '@AlexisBrignoni, Codex',
        'creation_date': '2026-09-24', 'last_update_date': '2026-09-24',
        'requirements': 'none', 'category': 'Firefox', 'artifact_icon': 'shield',
        'paths': ('*/Library/Application Support/Firefox/Profiles/*/permissions.sqlite*',
                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/permissions.sqlite*',
                  '*/.mozilla/firefox/*/permissions.sqlite*',
                  '*/Desktop/*Firefox*/*/permissions.sqlite*'),
        'output_types': 'standard', 'sample_data': {},
        'notes': 'Reads moz_perms when present, even if empty; otherwise reads legacy moz_hosts. The legacy table may remain after migration and is not combined with the modern table. Dates use Unix milliseconds; zero and absent dates remain blank. Capability and expiry codes are reported as stored because meanings can depend on permission type. A stored permission does not establish that a person accepted a prompt, visited an origin, or used the permitted feature. Origin attributes remain attached to the origin. moz_origin_interactions is excluded: its timestamps can be initialized by migration and are not permission-change times. WAL files are included. Profiles remain distinct and byte-identical macOS firmlink database/WAL copies are deduplicated. User is blank when paths do not name the account. Public tests are synthetic; private corpus details are not published.'
                 " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                 ' profile folder, under its own name, inside a Desktop folder named from the '
                 "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                 'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                 'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                 'the home folder because no Desktop is available is not matched. Refresh sources: '
                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                 ' '
                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                 ' '
                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                 ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/extensions/permissions/PermissionManager.cpp#L94; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/extensions/permissions/PermissionManager.cpp#L1575-L1595.',
    },
    'firefoxExtensions': {
        'name': 'Firefox Extensions',
        'description': 'Firefox extension inventory with stored versions, installation and update dates, location, state flags, and permission metadata.',
        'author': '@AlexisBrignoni, Codex',
        'creation_date': '2026-09-24', 'last_update_date': '2026-09-24',
        'requirements': 'none', 'category': 'Firefox', 'artifact_icon': 'puzzle',
        'paths': ('*/Library/Application Support/Firefox/Profiles/*/extensions.json',
                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/extensions.json',
                  '*/.mozilla/firefox/*/extensions.json',
                  '*/Desktop/*Firefox*/*/extensions.json'),
        'output_types': 'standard', 'sample_data': {},
        'notes': 'One row per addons entry with type extension. Includes browser-supplied extensions; Location is retained to distinguish installation locations. Dates are stored Unix milliseconds and can be derived from package modification times; they do not establish a manual installation. A missing update date is left blank rather than copied from installation time. Active and disabled flags are stored states, not execution events. User Permissions and Optional Permissions preserve the respective JSON objects; optional permissions are not described as granted. The name comes from defaultLocale, without selecting the examiner computer locale. Install Path is a stored evidence value, not a path resolved on the examiner computer. Themes and other non-extension entries, package contents, and permission-change history are excluded. Profiles remain distinct; byte-identical macOS firmlink copies are deduplicated. User is blank when source paths do not identify an account. Public tests are synthetic; private corpus details are not published.'
                 " A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old"
                 ' profile folder, under its own name, inside a Desktop folder named from the '
                 "resetBackupDirectory string, 'Old %S Data' in the en-US source with the application "
                 'name for %S, so the pattern matches a folder on the Desktop whose name contains '
                 'Firefox, and Source File shows which copy a row came from. A copy Firefox places in '
                 'the home folder because no Desktop is available is not matched. Refresh sources: '
                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27;'
                 ' '
                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96;'
                 ' '
                 'https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.'
                 ' References: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/mozapps/extensions/internal/XPIDatabase.sys.mjs#L1622-L1627; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/mozapps/extensions/internal/XPIDatabase.sys.mjs#L3350-L3361.',
    },
}

from scripts import firefox, firefox_settings
from scripts.ilapfuncs import artifact_processor


@artifact_processor
def firefoxSitePermissions(context):
    data_headers = (('Modified Time', 'datetime'), ('Expiry Time', 'datetime'),
                    'Permission ID', 'Origin or Host', 'Permission Type',
                    'Capability Code (as stored)', 'Expiry Type (as stored)',
                    'Source Table', 'Profile', 'User', 'Source File')
    data_list, source_path = firefox.read_artifact(
        context, 'permissions.sqlite', firefox_settings.permissions, 'Firefox Site Permissions')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxExtensions(context):
    data_headers = (('Installed Time', 'datetime'), ('Updated Time', 'datetime'),
                    'Extension ID', 'Name', 'Version', 'Location', 'Active (as stored)',
                    'User Disabled (as stored)', 'App Disabled (as stored)', 'Source URI',
                    'Install Path (as stored)', 'User Permissions (JSON)',
                    'Optional Permissions (JSON)', 'Profile', 'User', 'Source File')
    data_list, source_path = firefox_settings.read_extensions(context)
    return data_headers, data_list, source_path
