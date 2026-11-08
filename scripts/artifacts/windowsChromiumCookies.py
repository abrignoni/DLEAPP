"""Windows Chromium cookies, decrypted offline, for DLEAPP.

Chromium-based browsers on Windows encrypt each cookie's value in the Cookies database
with the same per-installation AES-256 key kept in Local State (the v10 AES-GCM scheme).
This module unwraps that key with the user DPAPI key recovered from the account's ARSO
(TBAL) secret or from a cleartext password supplied with --windows-user-password, then
decrypts the cookie values. At Cookies-database schema version 24 and later the decrypted
value carries a 32-byte SHA-256 of the cookie's host, which is removed. Decryption uses
the vendored dpapiprobe library.
"""

__artifacts_v2__ = {
    "windowsChromiumCookies": {
        "name": "Windows Chromium Cookies (decrypted)",
        "description": "Cookie values from the Cookies databases of Windows Chromium browsers "
                       "(Chrome, Edge, Brave, Vivaldi, Opera, Chromium), decrypted with the "
                       "installation's Local State key, which is unwrapped with the user DPAPI key "
                       "recovered either from the account's ARSO (TBAL) secret with the boot key "
                       "alone or from a cleartext account password supplied with "
                       "--windows-user-password: host, name, path and the decrypted value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Decrypts the encrypted_value column of the cookies table of each Windows "
                 "Chromium Cookies database (<profile>/Cookies on older releases, "
                 "<profile>/Network/Cookies on newer ones). Chromium stores a random AES-256 key "
                 "in the installation's Local State under os_crypt.encrypted_key, as base64 of the "
                 "literal 'DPAPI' followed by a user DPAPI blob of the key "
                 "(Reference: Chromium, 'os_crypt_win.cc', "
                 "https://github.com/chromium/chromium/blob/bcf73217bfaf1adb3b51ba42dbfc9c396e8dc1c7/components/os_crypt/sync/os_crypt_win.cc), "
                 "and encrypts each cookie value with it as 'v10' + 12-byte nonce + ciphertext + "
                 "16-byte tag, AES-256-GCM. Opening the Local State key needs the user DPAPI "
                 "master key, recovered here with the boot key alone from the account's Automatic "
                 "Restart Sign-On (TBAL) secret (by the library's reading, the SHA-1 hash a TBAL "
                 "secret carries, salted with the account SID, opens the user master keys), or "
                 "from a cleartext account password supplied with --windows-user-password; the SAM "
                 "NT hash alone did not open the user master key on the Windows 11 image tested "
                 "(the SHA-1 candidate did), and the library documents the same for Windows 10 and "
                 "later. The vendored dpapiprobe library (scripts/vendor/dpapiprobe, with PyCryptodome; it reads the hives with the vendored regfprobe) runs the chain. Value is the decrypted cookie value, "
                 "decoded as UTF-8 with undecodable bytes replaced. At Cookies-database schema "
                 "version 24 and later (read from the database's meta table) the decrypted "
                 "plaintext begins with a 32-byte SHA-256 of the cookie's host_key, which is "
                 "removed before Value is reported (Reference: Chromium, "
                 "'sqlite_persistent_cookie_store.cc', "
                 "https://github.com/chromium/chromium/blob/bcf73217bfaf1adb3b51ba42dbfc9c396e8dc1c7/net/extras/sqlite/sqlite_persistent_cookie_store.cc); "
                 "earlier schema versions have no such prefix. Scheme is the stored value's "
                 "format: 'v10' for the AES-GCM scheme above, 'dpapi' for a per-value DPAPI blob, "
                 "the format Chromium wrote before the v10 scheme (os_crypt_win.cc still decrypts "
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
                 "available; 'unknown' for anything else. Status is 'recovered' when the value decrypted, "
                 "'locked (not decrypted)' when the value is v10 or dpapi and no recovered key "
                 "decrypted it: no key was recovered (no TBAL secret and no password supplied, or "
                 "the account's master keys or Local State absent), or the recovered key did not "
                 "verify the value; 'app-bound (v20) not decrypted' for a v20 value, and "
                 "'unrecognized value format' otherwise. Last Access Time, Created and Expires are "
                 "last_access_utc, creation_utc and expires_utc, microseconds since 1601-01-01 UTC "
                 "(a zero or missing value, such as a session cookie's expiry, is shown empty); "
                 "Host, Name and Path are host_key, name and path, decoded as UTF-8 with "
                 "undecodable bytes replaced. Secure and HttpOnly are is_secure and is_httponly "
                 "(named secure and httponly before schema version 10). Browser, Profile and User "
                 "come from the path, as in the Chromium Cookies artifact. The databases, hives "
                 "and master key files are opened read only. Only the Windows user data folders "
                 "(under AppData) are read; the macOS and Linux Chromium key stores are not DPAPI "
                 "and are out of scope here. Validated on one known-data profile: a Chrome v10 "
                 "cookie minted under a known account on a Windows 11 VM at Cookies schema version "
                 "24 (so the host-hash prefix path is exercised), encrypted under the account's "
                 "genuine os_crypt key and decrypted through the account password; the v10 chain "
                 "is also covered by the library's forged round-trip tests. The 'dpapi' (legacy "
                 "per-value) and 'v20' branches are source-verified and unit-tested but were not "
                 "exercised against real data here, nor was the schema-version-23-and-earlier "
                 "no-prefix path. Not covered: App-Bound (v20) values, and profiles whose account "
                 "key cannot be recovered; the ARSO/TBAL recovery path and the Edge, Brave, "
                 "Vivaldi, Opera and Chromium folders were not exercised against real data here "
                 "(only Google Chrome was). The dpapiprobe TBAL layout was read from one Windows "
                 "image upstream and is covered by the library's forged tests."
                 " Opera GX and 360 Safe Browser are read from their Windows user data folders, AppData/Roaming/Opera Software/Opera GX Stable and AppData/Roaming/360se6/User Data; on the known data windows11_arm_operagx_360se_known_20261107 (Opera GX 139.0.6053.42 and 360 Safe Browser 16.1.2000.64 on Windows 11, each started on three local test pages) this artifact gave 2 rows for Opera GX and 17 for 360 Safe Browser. On the known data one cookie per browser was set by a test page; the other rows came from pages the browsers loaded on their own. The known data holds no DPAPI master key, so none of its values were decrypted.",
        "paths": (
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Users/*/AppData/Roaming/Microsoft/Protect/*/*',
            '*/AppData/Local/Google/Chrome/User Data/Local State',
            '*/AppData/Local/Google/Chrome/User Data/*/Cookies',
            '*/AppData/Local/Chromium/User Data/Local State',
            '*/AppData/Local/Chromium/User Data/*/Cookies',
            '*/AppData/Local/Microsoft/Edge/User Data/Local State',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Cookies',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/Local State',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Cookies',
            '*/AppData/Local/Vivaldi/User Data/Local State',
            '*/AppData/Local/Vivaldi/User Data/*/Cookies',
            '*/AppData/Roaming/Opera Software/Opera Stable/Local State',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Local State',
            '*/AppData/Roaming/360se6/User Data/Local State',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Cookies',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Cookies',
            '*/AppData/Roaming/360se6/User Data/*/Cookies',
            '*/AppData/Roaming/Opera Software/Opera Stable/Cookies',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Cookies',
            '*/AppData/Roaming/360se6/User Data/Cookies',
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "windows11_chromium_oscrypt_known_20261102": "Windows 11 build 26200, Chrome v10, Cookies schema 24 | 1 row (minted known account, recovered via the account password)",
            "windows11_arm_operagx_360se_known_20261107": "Windows 11 build 26200 (ARM64), Opera GX 139.0.6053.42 and 360 Safe Browser 16.1.2000.64 | 19 rows",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (locate, open_store, table_columns,
                                               webkit_time)
from scripts.chromium.windows_oscrypt import recover_os_keys, user_data_dir
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows Chromium Cookies'


def _flag(value):
    if value is None or value == '':
        return ''
    return 'Yes' if int(value) else 'No'


def _result(clear, scheme):
    """(value text, status) for one cookie value's decrypt attempt."""
    if clear is not None:
        return clear.decode('utf-8', 'replace'), 'recovered'
    if scheme == 'v20':
        return '', 'app-bound (v20) not decrypted'
    if scheme in ('v10', 'dpapi'):
        return '', 'locked (not decrypted)'
    return '', 'unrecognized value format'


def _db_version(db):
    try:
        row = db.execute("SELECT value FROM meta WHERE key='version'").fetchone()
        return int(row[0]) if row and row[0] is not None else None
    except (sqlite3.Error, TypeError, ValueError):
        return None


@artifact_processor
def windowsChromiumCookies(context):
    data_headers = (('Last Access Time', 'datetime'), ('Created', 'datetime'),
                    ('Expires', 'datetime'), 'Host', 'Name', 'Path', 'Value', 'Scheme',
                    'Status', 'Secure', 'HttpOnly', 'Browser', 'Profile', 'User', 'Source File')
    data_list = []

    cookie_stores = []     # (store path, relative, browser, profile, user)
    for found in context.get_files_found():
        path = str(found)
        relative = context.get_relative_path(path)
        located = locate(relative.replace('\\', '/'))
        if located is None or located[4] not in ('Cookies', 'Network/Cookies'):
            continue
        browser, profile, user, _container, _name = located
        cookie_stores.append((path, relative, browser, profile, user))

    if not cookie_stores:
        return data_headers, data_list, ''

    pool, os_keys = recover_os_keys(context, _LABEL)

    sources = []
    for store_path, relative, browser, profile, user in sorted(cookie_stores,
                                                               key=lambda item: item[1]):
        db = open_store(_Store(store_path, relative), _LABEL)
        if db is None:
            continue
        try:
            present = table_columns(db, 'cookies')
            if not present:
                continue
            secure = 'is_secure' if 'is_secure' in present else 'secure'
            httponly = 'is_httponly' if 'is_httponly' in present else 'httponly'
            version = _db_version(db)
            rows = db.execute(f'''
                SELECT last_access_utc, creation_utc, expires_utc, host_key, name, path,
                       {secure}, {httponly}, encrypted_value
                FROM cookies ORDER BY host_key, name, path''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{_LABEL}: could not read {relative}: {ex}')
            continue
        finally:
            db.close()
        key = os_keys.get(user_data_dir(relative))
        for (last_access, created, expires, host, name, cookie_path, is_secure, is_httponly,
             enc) in rows:
            if not enc:
                continue
            clear, scheme = dpapiprobe.decrypt_value(bytes(enc), key=key, mk_pool=pool)
            if clear is not None and scheme in ('v10', 'v20'):
                clear = dpapiprobe.strip_cookie_host_hash(clear, version)
            value_text, status = _result(clear, scheme)
            data_list.append((webkit_time(last_access), webkit_time(created),
                              webkit_time(expires), host, name, cookie_path, value_text, scheme,
                              status, _flag(is_secure), _flag(is_httponly), browser, profile,
                              user, relative))
        sources.append(store_path)

    return data_headers, data_list, '\n'.join(sources)


class _Store:
    """The minimal fields open_store reads: the staged path and its evidence-relative path."""

    __slots__ = ('path', 'relative')

    def __init__(self, path, relative):
        self.path = path
        self.relative = relative
