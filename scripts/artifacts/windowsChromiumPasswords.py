"""Windows Chromium saved passwords, decrypted offline, for DLEAPP.

Chromium-based browsers on Windows (Chrome, Edge, Brave, Vivaldi, Opera, Chromium) keep a
random AES-256 key in each installation's Local State, wrapped in a user DPAPI blob, and
encrypt each saved password in the Login Data database with it (the v10 AES-GCM scheme).
Opening the key needs the user's DPAPI master key: this module recovers it either from the
account's ARSO (TBAL) secret with the boot key alone, or from a cleartext account password
supplied with --windows-user-password, then unwraps the Local State key and decrypts the
stored passwords. Decryption uses the vendored dpapiprobe library.
"""

__artifacts_v2__ = {
    "windowsChromiumPasswords": {
        "name": "Windows Chromium Saved Passwords (decrypted)",
        "description": "Saved passwords from the Login Data databases of Windows Chromium "
                       "browsers (Chrome, Edge, Brave, Vivaldi, Opera, Chromium), decrypted with "
                       "the installation's Local State key, which is unwrapped with the user DPAPI "
                       "key recovered either from the account's ARSO (TBAL) secret with the boot "
                       "key alone or from a cleartext account password supplied with "
                       "--windows-user-password: site, username and the decrypted password. Rows "
                       "with no stored password value are left to the Chromium Saved Logins "
                       "artifact.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Decrypts the password_value column of the logins table of each Windows Chromium "
                 "Login Data and Login Data For Account database. Chromium stores a random AES-256 "
                 "key in the installation's Local State under os_crypt.encrypted_key, as base64 of "
                 "the literal 'DPAPI' followed by a user DPAPI blob of the key "
                 "(Reference: Chromium, 'os_crypt_win.cc', "
                 "https://github.com/chromium/chromium/blob/bcf73217bfaf1adb3b51ba42dbfc9c396e8dc1c7/components/os_crypt/sync/os_crypt_win.cc), "
                 "and encrypts each saved password with it as 'v10' + 12-byte nonce + ciphertext "
                 "+ 16-byte tag, AES-256-GCM. Opening the Local State key needs the user DPAPI "
                 "master key, recovered here with the boot key alone from the account's Automatic "
                 "Restart Sign-On (TBAL) secret (by the library's reading, the SHA-1 hash a TBAL "
                 "secret carries, salted with the account SID, opens the user master keys), or "
                 "from a cleartext account password supplied with --windows-user-password; the SAM "
                 "NT hash alone did not open the user master key on the Windows 11 image tested "
                 "(the SHA-1 candidate did), and the library documents the same for Windows 10 and "
                 "later, so a known or cracked password is needed when there is no ARSO secret. "
                 "The vendored dpapiprobe library (scripts/vendor/dpapiprobe, with PyCryptodome; it reads the hives with the vendored regfprobe) runs the chain. Password is the decrypted value, decoded as "
                 "UTF-8 with undecodable bytes replaced. Scheme is the stored value's format: "
                 "'v10' for the AES-GCM scheme above, 'dpapi' for a per-value DPAPI blob, the "
                 "format Chromium wrote before the v10 scheme (os_crypt_win.cc still decrypts "
                 "values without the v10 prefix that way), decrypted directly with the user master "
                 "key, 'v20' for the App-Bound Encryption scheme Chrome 127 and later can write "
                 "(os_crypt.app_bound_encrypted_key, values prefixed 'v20'; Reference: Chromium, "
                 "'app_bound_encryption_provider_win.cc', "
                 "https://github.com/chromium/chromium/blob/bcf73217bfaf1adb3b51ba42dbfc9c396e8dc1c7/chrome/browser/os_crypt/app_bound_encryption_provider_win.cc, "
                 "and the Google Security blog 'Improving the security of Chrome cookies on "
                 "Windows', 30 July 2024), which this module reports but does not decrypt: the final key is held by "
                 "Chrome's elevation service (running as SYSTEM) and is version-specific (published "
                 "research reports it hardcoded in elevation_service.exe or bound to the machine, and "
                 "the scheme has changed repeatedly since Chrome 127), so there is no stable offline "
                 "recovery and a v20 value is instead recovered by live acquisition with the service "
                 "available; 'unknown' for anything else. Status is 'recovered' when the password decrypted, "
                 "'locked (not decrypted)' when the value is v10 or dpapi and no recovered key "
                 "decrypted it: no key was recovered (no TBAL secret and no password supplied, or "
                 "the account's master keys or Local State absent), or the recovered key did not "
                 "verify the value; 'app-bound (v20) not decrypted' for a v20 value, and "
                 "'unrecognized value format' otherwise. Created, Last Used and Password Modified "
                 "are date_created, date_last_used and date_password_modified, microseconds since "
                 "1601-01-01 UTC (a zero or missing value is shown empty); Origin URL, Signon "
                 "Realm and Username are origin_url, signon_realm and username_value, decoded as "
                 "UTF-8 with undecodable bytes replaced. Browser, Profile and User come from the "
                 "path, as in the Chromium Saved Logins artifact. The databases, hives and master "
                 "key files are opened read only. Only the Windows user data folders (under "
                 "AppData) are read; the macOS and Linux Chromium key stores are not DPAPI and are "
                 "out of scope here. Validated on one known-data profile: a Chrome v10 saved "
                 "password minted under a known account on a Windows 11 VM "
                 "(windows11_chromium_oscrypt_known_20261102), decrypted through the account "
                 "password; the v10 chain is also covered by the library's forged round-trip "
                 "tests. The 'dpapi' (legacy per-value) and 'v20' branches are source-verified and "
                 "unit-tested but were not exercised against real data here. Not covered: "
                 "App-Bound (v20) values, and profiles whose account key cannot be recovered; the "
                 "ARSO/TBAL recovery path and the Edge, Brave, Vivaldi, Opera and Chromium folders "
                 "were not exercised against real data here (only Google Chrome was). The "
                 "dpapiprobe TBAL layout was read from one Windows image upstream and is covered "
                 "by the library's forged tests."
                 " Opera GX and 360 Safe Browser are read from their Windows user data folders, AppData/Roaming/Opera Software/Opera GX Stable and AppData/Roaming/360se6/User Data; on the known data windows11_arm_operagx_360se_known_20261107 (Opera GX 139.0.6053.42 and 360 Safe Browser 16.1.2000.64 on Windows 11, each started on three local test pages) this artifact gave 0 rows for Opera GX and 0 for 360 Safe Browser.",
        "paths": (
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Users/*/AppData/Roaming/Microsoft/Protect/*/*',
            '*/AppData/Local/Google/Chrome/User Data/Local State',
            '*/AppData/Local/Google/Chrome/User Data/*/Login Data*',
            '*/AppData/Local/Chromium/User Data/Local State',
            '*/AppData/Local/Chromium/User Data/*/Login Data*',
            '*/AppData/Local/Microsoft/Edge/User Data/Local State',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Login Data*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/Local State',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Login Data*',
            '*/AppData/Local/Vivaldi/User Data/Local State',
            '*/AppData/Local/Vivaldi/User Data/*/Login Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Local State',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Local State',
            '*/AppData/Roaming/360se6/User Data/Local State',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Login Data*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Login Data*',
            '*/AppData/Roaming/360se6/User Data/*/Login Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Login Data*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Login Data*',
            '*/AppData/Roaming/360se6/User Data/Login Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "key",
        "sample_data": {
            "windows11_chromium_oscrypt_known_20261102": "Windows 11 build 26200, Chrome v10 | 1 row (minted known account, recovered via the account password)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 (ARM64), Opera GX 139.0.6053.42 and 360 Safe Browser 16.1.2000.64 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (locate, open_store, select_list,
                                               table_columns, webkit_time)
from scripts.chromium.windows_oscrypt import recover_os_keys, user_data_dir
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows Chromium Saved Passwords'
_COLUMNS = ('date_created', 'date_last_used', 'date_password_modified', 'origin_url',
            'signon_realm', 'username_value', 'password_value')


@artifact_processor
def windowsChromiumPasswords(context):
    data_headers = (('Created', 'datetime'), ('Last Used', 'datetime'),
                    ('Password Modified', 'datetime'), 'Origin URL', 'Signon Realm',
                    'Username', 'Password', 'Scheme', 'Status', 'Browser', 'Profile', 'User',
                    'Source File')
    data_list = []

    login_stores = []      # (store path, relative)
    for found in context.get_files_found():
        path = str(found)
        name = path.replace('\\', '/').rsplit('/', 1)[-1]
        if name in ('Login Data', 'Login Data For Account'):
            login_stores.append((path, context.get_relative_path(path)))

    if not login_stores:
        return data_headers, data_list, ''

    pool, os_keys = recover_os_keys(context, _LABEL)

    sources = []
    for store_path, relative in sorted(login_stores, key=lambda item: item[1]):
        located = locate(relative.replace('\\', '/'))
        if located is None:
            continue
        browser, profile, user, _container, _store_name = located
        db = open_store(_Store(store_path, relative), _LABEL)
        if db is None:
            continue
        try:
            present = table_columns(db, 'logins')
            if not present:
                continue
            rows = db.execute(f'SELECT {select_list(present, _COLUMNS)} FROM logins '
                              f'ORDER BY date_created, signon_realm').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{_LABEL}: could not read {relative}: {ex}')
            continue
        finally:
            db.close()
        key = os_keys.get(user_data_dir(relative))
        emitted = False
        for (created, last_used, modified, origin, realm, username, pwv) in rows:
            if not pwv:
                continue
            emitted = True
            clear, scheme = dpapiprobe.decrypt_value(bytes(pwv), key=key, mk_pool=pool)
            password_text, status = _result(clear, scheme)
            data_list.append((webkit_time(created), webkit_time(last_used),
                              webkit_time(modified), origin, realm, username, password_text,
                              scheme, status, browser, profile, user, relative))
        if emitted:
            sources.append(store_path)

    return data_headers, data_list, '\n'.join(sources)


def _result(clear, scheme):
    """(password text, status) for one value's decrypt attempt."""
    if clear is not None:
        return clear.decode('utf-8', 'replace'), 'recovered'
    if scheme == 'v20':
        return '', 'app-bound (v20) not decrypted'
    if scheme in ('v10', 'dpapi'):
        return '', 'locked (not decrypted)'
    return '', 'unrecognized value format'


class _Store:
    """The minimal fields open_store reads: the staged path and its evidence-relative path."""

    __slots__ = ('path', 'relative')

    def __init__(self, path, relative):
        self.path = path
        self.relative = relative
