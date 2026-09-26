"""Firefox profile bookkeeping artifacts. Author: @AlexisBrignoni, Claude."""

__artifacts_v2__ = {
    'firefoxProfileList': {
        'name': 'Firefox Profile List',
        'description': "Sections of Firefox's profiles.ini and installs.ini: each profile's name and path, the default profile, and each installation's default profile.",
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-09-26',
        'last_update_date': '2026-09-26',
        'requirements': 'none',
        'category': 'Firefox',
        'notes': "One row per section of the profiles.ini and installs.ini files Firefox keeps in its application data folder (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L1018-L1024); File names which file a row came from. A profile section records the profile's Name, Path and IsRelative, and StoreID and ShowSelector for a profile that has a store ID, so Store ID and Show Selector (as stored) are blank for a profile without one (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L305-L322). Default is 1 on the section of the profile Firefox records as its normal default, which is separate from an installation's default below (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L1353-L1367). On a section whose name begins with Install, Default is the path of that installation's default profile, empty when the installation has been used without one (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L1370-L1386), and Locked is set to 1 under conditions that include Firefox being the default application (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L740-L748). The General section carries StartWithLastProfile and Version, which appear in Other Values (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L1087-L1094). installs.ini is a copy Firefox writes of the Install sections, with Install removed from the start of each section name, and it is read back only when profiles.ini carries no Version (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L2825-L2850; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/profile/nsToolkitProfileService.cpp#L1057-L1082). Other Values lists every key of a section that has no column of its own, as key=value pairs. Is Relative (as stored), Locked (as stored) and Show Selector (as stored) are the values as written. User is blank when source paths do not identify an account. A byte-identical copy of a file under the macOS firmlink path System/Volumes/Data is read once. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. ",
        'paths': ('*/Library/Application Support/Firefox/profiles.ini',
                  '*/Library/Application Support/Firefox/installs.ini',
                  '*/AppData/Roaming/Mozilla/Firefox/profiles.ini',
                  '*/AppData/Roaming/Mozilla/Firefox/installs.ini',
                  '*/.mozilla/firefox/profiles.ini',
                  '*/.mozilla/firefox/installs.ini'),
        'output_types': 'standard',
        'artifact_icon': 'users',
        'sample_data': {},
    },
    'firefoxProfileTimes': {
        'name': 'Firefox Profile Times',
        'description': "Times recorded in each Firefox profile's times.json: the computed creation time, first use, most recent reset and recovery from backup.",
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-09-26',
        'last_update_date': '2026-09-26',
        'requirements': 'none',
        'category': 'Firefox',
        'notes': "One row per times.json, the file in which Firefox records a profile's age (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L7; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L118-L133). Created is created, which Firefox computes the first time it needs it, as the oldest creation time among the entries directly inside the profile folder, or their modification time where the file system gives no creation time; it is not a time Firefox records when the profile is made (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L9-L46; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L85-L98; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L140-L145). First Use is firstUse, the Date.now() time Firefox writes when it finds no readable times.json (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L54-L64; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L205-L217). Reset is reset, the time of the most recent profile reset, Recovered From Backup is recoveredFromBackup, the time of a recovery from a backup, and Source (as stored) is source, which Firefox sets to reset, copy or backup when it records a reset, a copy of the profile from another, or a recovery (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L147-L199). Firefox writes source from commit 204a96d56b40 of 2026-05-15 (https://github.com/mozilla-firefox/firefox/commit/204a96d56b40285148fea160628bbad54ff98f3c), so Source (as stored) is blank on a times.json last written by an earlier version. When Firefox's Refresh builds a new profile it copies the old profile's times.json into it before recording the reset (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/migration/FirefoxProfileMigrator.sys.mjs#L404-L424), so a refreshed profile and the profile it replaced can hold the same value in Created and First Use. Created, First Use, Reset and Recovered From Backup are milliseconds since 1970, and each is blank when the file does not hold it (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/chrome-webidl/IOUtils.webidl#L717-L735). Profile is the folder that holds the file. Profiles remain separate; User is blank when source paths do not identify an account. A byte-identical copy of a file under the macOS firmlink path System/Volumes/Data is read once. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Source File shows which copy a row came from. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
        'paths': ('*/Library/Application Support/Firefox/Profiles/*/times.json',
                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/times.json',
                  '*/.mozilla/firefox/*/times.json',
                  '*/Desktop/*Firefox*/*/times.json'),
        'output_types': 'standard',
        'artifact_icon': 'clock',
        'sample_data': {},
    },
}

from scripts import firefox_profiles
from scripts.ilapfuncs import artifact_processor


@artifact_processor
def firefoxProfileList(context):
    data_headers = ('Section', 'Name', 'Path', 'Is Relative (as stored)', 'Default', 'Locked (as stored)',
                    'Store ID', 'Show Selector (as stored)', 'Other Values', 'File', 'User', 'Source File')
    data_list, source_path = firefox_profiles.read_profile_list(context, 'Firefox Profile List')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxProfileTimes(context):
    data_headers = (('Created', 'datetime'), ('First Use', 'datetime'), ('Reset', 'datetime'),
                    ('Recovered From Backup', 'datetime'), 'Source (as stored)', 'Profile', 'User', 'Source File')
    data_list, source_path = firefox_profiles.read_profile_times(context, 'Firefox Profile Times')
    return data_headers, data_list, source_path
