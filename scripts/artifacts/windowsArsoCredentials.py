"""Windows ARSO (Trusted Boot Auto-Logon / TBAL) credentials, recovered offline, for DLEAPP.

Automatic Restart Sign-On stashes the signed-in account's credentials in the LSA secret
M$_MSV1_0_TBAL_PRIMARY_<GUID> so Windows can log the account back on after an update
reboot. The secret is decrypted with the boot key alone (no user password), and its
payload carries the account's user name, NT hash and SHA-1 password hash. The SHA-1 hash
opens that account's DPAPI master keys without the password, which this module confirms
against any user master keys in the extraction. Decryption and parsing use the vendored
dpapiprobe library; see the notes.
"""

__artifacts_v2__ = {
    "windowsArsoCredentials": {
        "name": "Windows ARSO Credentials",
        "description": "Account credentials recovered from the Automatic Restart Sign-On (TBAL) LSA secret "
                       "with the boot key alone: the user name, NT hash and SHA-1 password hash, and whether "
                       "the SHA-1 hash opens that account's user DPAPI master keys (by SID and count).",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Windows Registry",
        "notes": "Recovers the account credentials Automatic Restart Sign-On (ARSO), also called Trusted Boot Auto-Logon, stores in the LSA secret M$_MSV1_0_TBAL_PRIMARY_<GUID>. The secret is decrypted with the boot key from the SYSTEM hive and the SECURITY hive (the Vista-and-later LSA scheme) via the vendored dpapiprobe library (scripts/vendor/dpapiprobe, PyCryptodome and python-registry); no user password is needed. Its payload carries the account's user name, NT hash and SHA-1 password hash. Written is the CupdTime of the secret's Policy\\Secrets key (the current-value update time, FILETIME, UTC). Username is the account name decoded from the payload. NT Hash and SHA-1 Hash are the account's password hashes as hex; a hash stored as all zeros (absent) is left blank. Opens User DPAPI reports whether the SHA-1 hash, salted with an account SID, opens any user DPAPI master keys found under Users\\<u>\\AppData\\Roaming\\Microsoft\\Protect in the extraction, naming the SID and the count; this confirms the recovered hash and ties it to an account, and where it opens, that account's DPAPI master keys are recovered, which is the key its DPAPI-protected data is encrypted under. This module does not itself decrypt that data. The TBAL payload layout was read from a real secret: the NT-hash field is the 16-byte NT hash, the SHA-1-hash field is the one that opens the account's master keys, and the trailing printable field is the user name. It is validated on one image, so treat the layout as that single observation. The hives and master key files are opened read only; the hives are read per Windows install and user master keys are matched to the recovered hash by account SID. Automatic Restart Sign-On stores this secret only on systems configured for it, so it is present on some images and not others: in the tested corpus it was found on one image (af_case2_win10, one local account, the SHA-1 hash opening both of that account's user master keys) and absent on the other nine (cfreds_leakage_win7, lonewolf_win10, szechuan_win10, hexordia_mvs2025_win11, ou_ransomware_server2022, alihadi_threatsim_server2019, szechuan_dc01_server2012r2, alihadi_challenge3_win81, pc_mus_001_win11). Not covered: the NTLM-only and cloud-account (cloudAP) ARSO variants, and the meaning of the payload's other fields. NT Hash, SHA-1 Hash and Username are the recovered credential's own values.",
        "paths": (
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Users/*/AppData/Roaming/Microsoft/Protect/*/*',
        ),
        "output_types": "standard",
        "artifact_icon": "key",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row (one local account; SHA-1 hash opens both of that account's user master keys)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no ARSO/TBAL secret)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no ARSO/TBAL secret)",
        },
    },
}

import struct
from datetime import datetime, timedelta, timezone

from Registry import Registry

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows ARSO Credentials'
_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _is_config_hive(path):
    return '/config/' in path.replace('\\', '/').lower()


def _hive_root(path):
    """The part of a hive path before \\Windows\\System32 (one Windows install).

    Anchored on the Windows system-folder marker only. User master keys are grouped by
    account SID, not by a path root, so the examiner's own folders (which may contain a
    'Users' segment) never enter the grouping.
    """
    lowered = path.replace('\\', '/').lower()
    cut = lowered.find('/windows/system32/')
    return path[:cut] if cut != -1 else path


def _looks_like_guid(name):
    return len(name) == 36 and name.count('-') == 4


def _tbal_written_times(security_hive):
    """{secret name: CupdTime datetime} for the TBAL secrets, from Policy\\Secrets."""
    times = {}
    with open(security_hive, 'rb') as handle:
        reg = Registry.Registry(handle)
        try:
            root = reg.open('Policy\\Secrets')
        except Registry.RegistryKeyNotFoundException:
            return times
        for sub in root.subkeys():
            if not sub.name().startswith('M$_MSV1_0_TBAL'):
                continue
            for child in sub.subkeys():
                if child.name() == 'CupdTime':
                    raw = child.value('').value()
                    ticks = struct.unpack('<Q', raw[:8])[0] if raw and len(raw) >= 8 else 0
                    times[sub.name()] = (_FILETIME_ZERO + timedelta(microseconds=ticks // 10)
                                         if ticks else '')
    return times


def _opens_which_sid(sha1_hash, user_mks):
    """A description of which account SID's master keys ``sha1_hash`` opens."""
    if sha1_hash is None:
        return ''
    if not user_mks:
        return 'no user master keys in extraction'
    for sid, raw_keys in user_mks.items():
        candidates = dpapiprobe.user_master_key_candidates(sid, sha1_hash=sha1_hash)
        opened = sum(1 for raw in raw_keys
                     if dpapiprobe.decrypt_master_key(raw, candidates) is not None)
        if opened:
            return 'yes: %s (%d master key%s)' % (sid, opened, '' if opened == 1 else 's')
    return 'no match among the user master keys present'


def _rows_for_install(context, hives, user_mks, data_list):
    system_hive, security_hive = hives.get('SYSTEM'), hives.get('SECURITY')
    if not (system_hive and security_hive):
        return []
    try:
        bootkey = dpapiprobe.get_bootkey(system_hive)
        secrets = dpapiprobe.get_lsa_secrets(security_hive, bootkey)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f'{_LABEL}: could not read LSA secrets from {security_hive}: '
                f'{type(ex).__name__}: {ex}')
        return []
    tbal_names = [name for name in secrets if name.startswith('M$_MSV1_0_TBAL')]
    if not tbal_names:
        return []
    written = _tbal_written_times(security_hive)
    relative = context.get_relative_path(security_hive)
    for name in sorted(tbal_names):
        parsed = dpapiprobe.parse_tbal(secrets[name])
        if parsed is None:
            data_list.append(('', '', '', '', 'TBAL secret did not parse', name, relative))
            continue
        nt = parsed['nt_hash'].hex() if parsed['nt_hash'] else ''
        sha1 = parsed['sha1_hash'].hex() if parsed['sha1_hash'] else ''
        data_list.append((written.get(name, ''), parsed['username'], nt, sha1,
                          _opens_which_sid(parsed['sha1_hash'], user_mks), name, relative))
    return [system_hive, security_hive]


@artifact_processor
def windowsArsoCredentials(context):
    data_headers = (('Written', 'datetime'), 'Username', 'NT Hash', 'SHA-1 Hash',
                    'Opens User DPAPI', 'Secret Name', 'Source File')
    data_list = []

    installs = {}       # hive root -> {'SYSTEM': path, 'SECURITY': path}
    user_mks = {}       # account SID -> [master-key file bytes]
    for found in context.get_files_found():
        path = str(found)
        lowered = path.replace('\\', '/').lower()
        name = path.replace('\\', '/').rsplit('/', 1)[-1]
        if name in ('SYSTEM', 'SECURITY') and _is_config_hive(path):
            installs.setdefault(_hive_root(path), {}).setdefault(name, path)
        elif '/protect/' in lowered and _looks_like_guid(name):
            sid = path.replace('\\', '/').rsplit('/', 2)[-2]
            if sid.upper().startswith('S-1-'):
                with open(path, 'rb') as handle:
                    user_mks.setdefault(sid, []).append(handle.read())

    sources = []
    for root in sorted(installs):
        sources.extend(_rows_for_install(context, installs[root], user_mks, data_list))

    return data_headers, data_list, '\n'.join(sources)
