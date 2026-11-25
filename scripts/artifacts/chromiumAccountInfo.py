"""Account information in the Preferences file of Chromium-based browser profiles, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "chromiumAccountInfo": {
        "name": "Chromium Account Info",
        "description": "Accounts listed in the Preferences file of Chromium-based browser profiles, with the email, "
                       "name, hosted domain, account identifier and the profile's sync consent.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Browsers",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per entry of the account_info list in the Preferences file of each Chromium-based "
                 "browser profile that scripts/chromium/browser_profiles locates. Secure Preferences and files "
                 "beside Preferences such as Preferences.backup are not read. Key names come from Chromium at "
                 "commit 0b04123a759abeda7e18e82d86b52960f2370d42 "
                 "(components/signin/internal/identity_manager/account_info_util.cc and account_info_util.h, "
                 "and components/signin/public/base/signin_pref_names.cc). Older and vendor builds can differ. "
                 "Hosted Domain is the hd key and Picture URL the picture_url key, each blank when it holds "
                 "Chromium's marker for no value (NO_HOSTED_DOMAIN in "
                 "components/signin/public/identity_manager/signin_constants.h, NO_PICTURE_URL in "
                 "account_info.cc). The picture marker was on no row in sample_data. Consented To Sync is "
                 "google.services.consented_to_sync for the profile, so it repeats on every account of that "
                 "profile. Chromium's comment on it says it indicates whether the user gave consent for Sync. "
                 "Matches sync.gaia_id compares the row's Gaia ID with the profile's sync.gaia_id key, and is "
                 "blank when the profile has none. That key is not in components/sync/base/pref_names.h at the "
                 "commit above. Chromium 90.0.4430.0 defines it (components/sync/base/pref_names.cc) and "
                 "writes it from SyncTransportDataPrefs::SetGaiaId, with no comment on its meaning. Which "
                 "builds wrote it on these images was not checked. Other Values holds the entry's remaining "
                 "non-empty text, number and true or false values as name=value, with true and false written "
                 "as True and False, including the keys starting with edge_ on the one Microsoft Edge row, "
                 "whose meanings are not established. On the one Microsoft Edge row the account is under the "
                 "same account_info keys, so Gaia ID on an Edge row is the gaia key as stored and is not "
                 "established to be a Google identifier. The account capabilities block, the downloaded image "
                 "URL and any other dictionary or list value are not reported. Chromium's SerializeAccountInfo "
                 "at that commit writes no time for an entry, and no entry in sample_data had one. A row shows "
                 "an entry that was in account_info in the Preferences file as read. Whether it was still "
                 "signed in, and whether an entry survives sign-out, was not tested. No known data was built "
                 "for this artifact. Rows come from profiles already on the images in sample_data: 7 rows on 3 "
                 "images, 6 from Google Chrome and 1 from Microsoft Edge. The account_id key equalled the gaia "
                 "key on all 7 rows, so it has no column and appears in Other Values only when it differs. On "
                 "pc_mus_001_win11 the User column held one value on all rows, because that image has one user "
                 "with these profiles. Consented To Sync and Matches sync.gaia_id had no value on the one row "
                 "of lonewolf_win10, whose profile has neither key.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Preferences*',
            '*/Library/Application Support/Google/Chrome/*/Preferences*',
            '*/.config/google-chrome/*/Preferences*',
            '*/AppData/Local/Chromium/User Data/*/Preferences*',
            '*/Library/Application Support/Chromium/*/Preferences*',
            '*/.config/chromium/*/Preferences*',
            '*/snap/chromium/common/chromium/*/Preferences*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Preferences*',
            '*/webbrowser/chrome/*/Preferences*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Preferences*',
            '*/Library/Application Support/Microsoft Edge/*/Preferences*',
            '*/.config/microsoft-edge/*/Preferences*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Preferences*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/.config/BraveSoftware/Brave-Browser/*/Preferences*',
            '*/AppData/Local/Vivaldi/User Data/*/Preferences*',
            '*/Library/Application Support/Vivaldi/*/Preferences*',
            '*/.config/vivaldi/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Preferences*',
            '*/AppData/Roaming/360se6/User Data/*/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Preferences*',
            '*/.config/opera/*/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Preferences*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Preferences*',
            '*/AppData/Roaming/360se6/User Data/Preferences*',
            '*/Library/Application Support/com.operasoftware.Opera/Preferences*',
            '*/.config/opera/Preferences*',
        ),
        "output_types": ["standard"],
        "artifact_icon": "user",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 5 rows",
            "lonewolf_win10": "Windows 10 Education 1709 build 16299 | 1 row",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 row",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100.2033) | 0 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 ARM64 | 0 rows",
        },
    },
}

import json

from scripts.chromium.browser_profiles import profile_stores, row_tail
from scripts.ilapfuncs import artifact_processor, logfunc

_NO_VALUE = {'hd': 'NO_HOSTED_DOMAIN', 'picture_url': 'NO_PICTURE_URL'}
_SHOWN = ('email', 'full_name', 'given_name', 'hd', 'locale', 'gaia', 'account_id', 'picture_url')
_NOT_REPORTED = ('accountcapabilities', 'last_downloaded_image_url_with_size')


def _value(entry, key):
    value = entry.get(key)
    if value is None or value == _NO_VALUE.get(key):
        return ''
    return value if isinstance(value, str) else str(value)


def _other(entry):
    parts = []
    for key in sorted(entry):
        value = entry[key]
        if key in _SHOWN or key in _NOT_REPORTED or isinstance(value, (dict, list)) or value in ('', None):
            if not (key == 'account_id' and value not in ('', None) and value != entry.get('gaia')):
                continue
        parts.append(f'{key}={value}')
    return '; '.join(parts)


def _yes_no(value):
    return {True: 'Yes', False: 'No'}.get(value, '') if isinstance(value, bool) else ''


@artifact_processor
def chromiumAccountInfo(context):
    data_headers = ('Email', 'Full Name', 'Given Name', 'Hosted Domain', 'Locale', 'Gaia ID',
                    'Consented To Sync', 'Matches sync.gaia_id', 'Picture URL', 'Other Values', 'Browser',
                    'Profile', 'User')
    data_list, sources = [], []
    for store in profile_stores(context, ('Preferences',), 'Chromium Account Info'):
        try:
            with open(store.path, encoding='utf-8', errors='replace') as handle:
                data = json.load(handle)
        except (OSError, ValueError) as exc:
            logfunc(f'Chromium Account Info: could not read Preferences: {type(exc).__name__}')
            continue
        if not isinstance(data, dict):
            continue
        accounts = data.get('account_info')
        services = (data.get('google') or {}).get('services') if isinstance(data.get('google'), dict) else None
        consent = _yes_no(services.get('consented_to_sync')) if isinstance(services, dict) else ''
        sync = data.get('sync') if isinstance(data.get('sync'), dict) else {}
        sync_gaia = sync.get('gaia_id') or ''
        rows = 0
        for entry in (accounts if isinstance(accounts, list) else ()):
            if not isinstance(entry, dict):
                continue
            gaia = _value(entry, 'gaia')
            matches = ('Yes' if gaia == sync_gaia else 'No') if sync_gaia else ''
            data_list.append((_value(entry, 'email'), _value(entry, 'full_name'), _value(entry, 'given_name'),
                              _value(entry, 'hd'), _value(entry, 'locale'), gaia, consent, matches, _value(entry, 'picture_url'), _other(entry)) + row_tail(store)[:3])
            rows += 1
        if rows:
            sources.append(store.path)
    return data_headers, data_list, '\n'.join(sources)
