"""Windows System (LocalSystem) Credential Manager entries, decrypted offline, for DLEAPP.

The LocalSystem profile keeps saved credentials under
config\\systemprofile\\AppData\\{Local,Roaming}\\Microsoft\\Credentials\\<hash>. Each file
wraps a DPAPI blob protected in the SYSTEM context; decrypting it yields a CREDENTIAL
structure with the credential's target, user name, type and its stored secret. This
module recovers them with the SYSTEM DPAPI chain via the vendored dpapiprobe library.
The CREDENTIAL header and string sequence follow impacket's CREDENTIAL_BLOB; impacket
leaves the sixth string undocumented, and this module reads it as the inline secret.
See the notes.
"""

__artifacts_v2__ = {
    "windowsSystemCredentials": {
        "name": "Windows System Credential Manager",
        "description": "Saved credentials of the LocalSystem profile's Credential Manager, decrypted with "
                       "the SYSTEM DPAPI chain: the credential target, user name, type, when it was last "
                       "written, and the stored secret where the credential holds one inline.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Windows Registry",
        "notes": "Decrypts the saved credentials of the LocalSystem profile's Credential Manager (config\\systemprofile\\AppData\\Local\\Microsoft\\Credentials and the Roaming path). Each file wraps a DPAPI blob protected in the SYSTEM context; the vendored dpapiprobe library (scripts/vendor/dpapiprobe, PyCryptodome and python-registry) opens it from the boot key in the SYSTEM hive, the DPAPI_SYSTEM secret in the SECURITY hive and the SYSTEM master keys under Windows\\System32\\Microsoft\\Protect\\S-1-5-18, which must all be in the same extraction; the hives and master key files are opened read only. Each Windows install in the image is read on its own, pairing its credential files with the master keys and hives under the same Windows folder. The decrypted blob is a CREDENTIAL structure read with impacket's documented CREDENTIAL_BLOB layout: a 48-byte header (Credential Type at offset 12, Persistence at 32, LastWritten FILETIME at 20) then length-prefixed UTF-16 strings for target, alias, description, an unknown field, user name and a sixth string that impacket leaves undocumented, then any credential attributes. This module reads that sixth string as the credential's inline secret. Last Written is that FILETIME (UTC). Target is the credential target, decoded as printable UTF-16LE text, which names what the credential is for (for example Domain:batch=TaskScheduler:<task> for a scheduled-task run-as credential, or WindowsLive:target=... for a machine Microsoft-account credential). Username is the account on the credential, decoded as printable UTF-16LE text. Credential Type and Persistence are the CRED_TYPE_* and CRED_PERSIST_* values from wincred.h, reported by name or, when unknown, by number. Secret is that sixth string decoded as printable UTF-16LE: on the tested data the one domain-password scheduled-task credential held a readable value here, while the generic WindowsLive credentials had it empty because their data is in attributes. A credential whose data is kept in attributes has an empty Secret and a non-empty Attributes count; this module reports the attribute count and total size and does not decode the attribute payload. A credential file whose blob does not decrypt is listed with empty fields and 'decrypt failed' in the Attributes column (not seen on any image run). Tested on seven Windows images: ou_ransomware_server2022 held two (a scheduled-task domain-password credential with a recovered value, and a WindowsLive machine credential), pc_mus_001_win11, lonewolf_win10, szechuan_win10, hexordia_mvs2025_win11 and alihadi_threatsim_server2019 held one WindowsLive machine credential each, and af_case2_win10 held none. The SYSTEM Vault beside these credentials was checked on all seven images and held a policy file, schema files and on some a Latest.dat pointer, but no credential records (no .vcrd), so it is not reported here. Not covered: the user-profile Credential Manager and Vault (a different, credential-gated context) and the attribute payloads of the token credentials.",
        "paths": (
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Windows/System32/Microsoft/Protect/S-1-5-18/*',
            '*/Windows/System32/Microsoft/Protect/S-1-5-18/User/*',
            '*/Windows/System32/config/systemprofile/AppData/Local/Microsoft/Credentials/*',
            '*/Windows/System32/config/systemprofile/AppData/Roaming/Microsoft/Credentials/*',
        ),
        "output_types": "standard",
        "artifact_icon": "key",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 2 rows (scheduled-task domain password + WindowsLive machine credential)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row (WindowsLive machine credential)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row (WindowsLive machine credential)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row (WindowsLive machine credential)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row (WindowsLive machine credential)",
            "alihadi_threatsim_server2019": "Windows Server 2019 | 1 row (WindowsLive machine credential)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no systemprofile credentials)",
        },
    },
}

import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows System Credential Manager'
_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)

# CRED_TYPE_* and CRED_PERSIST_* (wincred.h); reported as the name, else the number.
_CRED_TYPE = {1: 'generic', 2: 'domain password', 3: 'domain certificate',
              4: 'domain visible password', 5: 'generic certificate', 6: 'domain extended',
              7: 'maximum', 1007: 'maximum ex'}
_PERSIST = {1: 'session', 2: 'local machine', 3: 'enterprise'}


def _u32(buf, off):
    return struct.unpack('<L', buf[off:off + 4])[0]


def _utf16(raw):
    """``raw`` as printable UTF-16LE text, or None when it is not clean text."""
    if not raw or len(raw) % 2:
        return None
    try:
        text = raw.decode('utf-16-le')
    except UnicodeDecodeError:
        return None
    text = text.rstrip('\x00')
    if text and all(char.isprintable() for char in text):
        return text
    return None


def _filetime(buf, off):
    ticks = struct.unpack('<Q', buf[off:off + 8])[0]
    if ticks == 0:
        return ''
    return _FILETIME_ZERO + timedelta(microseconds=ticks // 10)


def _parse_credential(clear):
    """Fields of a decrypted CREDENTIAL_BLOB (impacket layout): 48-byte header then
    the length-prefixed UTF-16 strings target, alias, description, unknown, username,
    secret, then the remaining bytes as credential attributes."""
    info = {
        'last_written': _filetime(clear, 20),
        'type': _CRED_TYPE.get(_u32(clear, 12), str(_u32(clear, 12))),
        'persist': _PERSIST.get(_u32(clear, 32), str(_u32(clear, 32))),
        'attr_count': _u32(clear, 36),
    }
    offset = 48
    strings = []
    for _ in range(6):  # target, alias, description, unknown, username, secret
        length = _u32(clear, offset)
        offset += 4
        strings.append(clear[offset:offset + length])
        offset += length
    info['target'] = _utf16(strings[0]) or ''
    info['username'] = _utf16(strings[4]) or ''
    info['secret'] = _utf16(strings[5]) or ''        # a password for the password types
    info['attr_bytes'] = max(0, len(clear) - offset)
    return info


def _is_config_hive(path):
    return '/config/' in path.replace('\\', '/').lower()


def _install_root(path):
    """The part of a path before \\Windows\\System32 (one Windows install)."""
    lowered = path.replace('\\', '/').lower()
    cut = lowered.find('/windows/system32/')
    return path[:cut] if cut != -1 else path


def _looks_like_guid(name):
    return len(name) == 36 and name.count('-') == 4


def _rows_for_install(context, hives, mk_dirs, cred_files, data_list):
    """Append a row per decryptable SYSTEM credential of one install. Returns files read."""
    system_hive, security_hive = hives.get('SYSTEM'), hives.get('SECURITY')
    if not (system_hive and security_hive and mk_dirs and cred_files):
        if cred_files:
            logfunc(f'{_LABEL}: {len(cred_files)} credential file(s) but the SYSTEM/SECURITY hives '
                    f'or SYSTEM master keys were not all present; cannot decrypt')
        return []
    try:
        bootkey = dpapiprobe.get_bootkey(system_hive)
        dpapi_system = dpapiprobe.get_dpapi_system(security_hive, bootkey)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f'{_LABEL}: could not read the SYSTEM DPAPI key: {type(ex).__name__}: {ex}')
        return []
    pool = dpapiprobe.MasterKeyPool()
    for directory in mk_dirs:
        pool.load_directory(directory)
    pool.decrypt_all(dpapiprobe.system_master_key_candidates(dpapi_system))

    used = [system_hive, security_hive]
    for cred_path in sorted(cred_files):
        relative = context.get_relative_path(cred_path)
        with open(cred_path, 'rb') as handle:
            raw = handle.read()
        try:
            cred = dpapiprobe.CredentialFile(raw)
            clear = cred.decrypt(pool.get_key(cred.blob.mk_guid))
        except (ValueError, struct.error, KeyError) as ex:
            logfunc(f'{_LABEL}: {relative}: {type(ex).__name__}')
            clear = None
        if not clear:
            data_list.append(('', '', '', '', '', '', 'decrypt failed', relative))
            continue
        used.append(cred_path)
        info = _parse_credential(clear)
        attributes = ('%d (%s bytes)' % (info['attr_count'], f"{info['attr_bytes']:,}")
                      if info['attr_bytes'] else '')
        data_list.append((info['last_written'], info['target'], info['username'], info['type'],
                          info['persist'], info['secret'], attributes, relative))
    return used


@artifact_processor
def windowsSystemCredentials(context):
    data_headers = (('Last Written', 'datetime'), 'Target', 'Username', 'Credential Type',
                    'Persistence', 'Secret', 'Attributes', 'Source File')
    data_list = []

    installs = {}
    for found in context.get_files_found():
        path = str(found)
        root = _install_root(path)
        slot = installs.setdefault(root, {'hives': {}, 'mk_dirs': set(), 'creds': []})
        lowered = path.replace('\\', '/').lower()
        name = path.replace('\\', '/').rsplit('/', 1)[-1]
        if name in ('SYSTEM', 'SECURITY') and _is_config_hive(path):
            slot['hives'].setdefault(name, path)
        elif '/microsoft/protect/s-1-5-18/' in lowered and _looks_like_guid(name):
            slot['mk_dirs'].add(path.replace('\\', '/').rsplit('/', 1)[0])
        elif '/systemprofile/' in lowered and '/credentials/' in lowered:
            slot['creds'].append(path)

    sources = []
    for root in sorted(installs):
        slot = installs[root]
        if not slot['creds']:
            continue
        sources.extend(_rows_for_install(context, slot['hives'], sorted(slot['mk_dirs']),
                                         slot['creds'], data_list))

    return data_headers, data_list, '\n'.join(sources)
