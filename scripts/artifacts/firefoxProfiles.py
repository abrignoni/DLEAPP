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
        'notes': "One row per times.json, the file in which Firefox records a profile's age (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L7; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L118-L133). Created is created, which Firefox computes the first time it needs it, as the oldest creation time among the entries directly inside the profile folder, or their modification time where the file system gives no creation time; it is not a time Firefox records when the profile is made (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L9-L46; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L85-L98; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L140-L145). First Use is firstUse, the Date.now() time Firefox writes when it finds no readable times.json (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L54-L64; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L205-L217). Reset is reset, the time of the most recent profile reset, Recovered From Backup is recoveredFromBackup, the time of a recovery from a backup, and Source (as stored) is source, which Firefox sets to reset, copy or backup when it records a reset, a copy of the profile from another, or a recovery (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/modules/ProfileAge.sys.mjs#L147-L199). Firefox writes source from commit 204a96d56b40 of 2026-05-15 (https://github.com/mozilla-firefox/firefox/commit/204a96d56b40285148fea160628bbad54ff98f3c), so Source (as stored) is blank on a times.json last written by an earlier version. When Firefox's Refresh builds a new profile it copies the old profile's times.json into it before recording the reset (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/browser/components/migration/FirefoxProfileMigrator.sys.mjs#L404-L424), so a refreshed profile and the profile it replaced can hold the same value in Created and First Use. Created, First Use, Reset and Recovered From Backup are milliseconds since 1970, and each is blank when the file does not hold it (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/dom/chrome-webidl/IOUtils.webidl#L717-L735). Profile is the folder that holds the file. Profiles remain separate; User is blank when source paths do not identify an account. A byte-identical copy of a file under the macOS firmlink path System/Volumes/Data is read once. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Profile names the folder a row came from; the report's located-at list gives each file's full path. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
        'paths': ('*/Library/Application Support/Firefox/Profiles/*/times.json',
                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/times.json',
                  '*/.mozilla/firefox/*/times.json',
                  '*/Desktop/*Firefox*/*/times.json'),
        'output_types': 'standard',
        'artifact_icon': 'clock',
        'sample_data': {},
    },
    'firefoxContainers': {
        'name': 'Firefox Containers',
        'description': "Containers defined in each Firefox profile's containers.json: the user context number, the name or built-in label id, icon, color and whether the container is public.",
        'author': '@AlexisBrignoni, Claude',
        'creation_date': '2026-09-26',
        'last_update_date': '2026-09-26',
        'requirements': 'none',
        'category': 'Firefox',
        'notes': "One row per identity in each Firefox profile's containers.json, the file in which Firefox keeps its containers (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L1172-L1177). User Context ID is userContextId, the number the Container ID column of other Firefox artifacts, such as the session store, carries for a tab in that container. Name (as stored) is name, which Firefox writes when a container is created or renamed and shows in place of a built-in label when it is present (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L393-L428; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L487-L517; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L873-L888). Localisation ID (as stored) is l10nId, the Fluent id of a built-in container's label; files before version 8 store it, and version 8 removes it and takes the label from the built-in list, so on a version 8 file a built-in container has neither a name nor a localisation id (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L1158-L1168). File Version is the file's version. Without an enterprise policy Firefox numbers its built-in containers 1 to 4 with the Fluent ids user-context-personal2, user-context-work2, user-context-banking2 and user-context-shopping2, and numbers its internal thumbnail and extension storage identities after them, the second at 4294967295 (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L6; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L175-L217; https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L238-L265). Public (as stored) is public, false for those internal identities and for a container made for an enterprise policy, whose policyId is Policy ID, blank for any other container (https://github.com/mozilla-firefox/firefox/blob/c32abda0190531351e22da36334f18f9e994d474/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs#L436-L455). Icon and Color are the container's icon and color names as stored, blank for the internal identities. Profile is the folder that holds the file. Profiles remain separate; User is blank when source paths do not identify an account. A byte-identical copy of a file under the macOS firmlink path System/Volumes/Data is read once. Public regression cases are independently authored synthetic data. Local private validation details are not published. Windows and Linux path coverage is synthetic. A profile copied out by Firefox's Refresh is read too: Firefox puts a copy of the old profile folder, under its own name, made unique if taken, inside a Desktop folder named from the resetBackupDirectory string, 'Old %S Data' in the en-US source with the application name for %S, so the pattern matches a folder on the Desktop whose name contains Firefox, and Profile names the folder a row came from; the report's located-at list gives each file's full path. A copy Firefox places in the home folder because no Desktop is available is not matched. Refresh sources: https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L26-L27; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/xre/ProfileReset.cpp#L59-L96; https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/locales/en-US/chrome/mozapps/profile/profileSelection.properties#L55-L56.",
        'paths': ('*/Library/Application Support/Firefox/Profiles/*/containers.json',
                  '*/AppData/Roaming/Mozilla/Firefox/Profiles/*/containers.json',
                  '*/.mozilla/firefox/*/containers.json',
                  '*/Desktop/*Firefox*/*/containers.json'),
        'output_types': 'standard',
        'artifact_icon': 'box',
        'sample_data': {},
    },
}

from scripts import firefox_profiles
from scripts.ilapfuncs import artifact_processor


@artifact_processor
def firefoxProfileList(context):
    data_headers = ('Section', 'Name', 'Path', 'Is Relative (as stored)', 'Default', 'Locked (as stored)',
                    'Store ID', 'Show Selector (as stored)', 'Other Values', 'File', 'User')
    data_list, source_path = firefox_profiles.read_profile_list(context, 'Firefox Profile List')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxProfileTimes(context):
    data_headers = (('Created', 'datetime'), ('First Use', 'datetime'), ('Reset', 'datetime'),
                    ('Recovered From Backup', 'datetime'), 'Source (as stored)', 'Profile', 'User')
    data_list, source_path = firefox_profiles.read_profile_times(context, 'Firefox Profile Times')
    return data_headers, data_list, source_path


@artifact_processor
def firefoxContainers(context):
    data_headers = ('User Context ID', 'Name (as stored)', 'Localisation ID (as stored)', 'Public (as stored)',
                    'Icon', 'Color', 'Policy ID', 'File Version', 'Profile', 'User')
    data_list, source_path = firefox_profiles.read_containers(context, 'Firefox Containers')
    return data_headers, data_list, source_path
