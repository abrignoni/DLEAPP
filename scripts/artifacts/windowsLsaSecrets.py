"""Windows LSA secrets, decrypted offline, for DLEAPP.

The LSA keeps a set of secrets under Policy\\Secrets in the SECURITY hive, each
encrypted under the machine boot key (syskey) held in the SYSTEM hive. This module
lists every secret and decrypts its current value with the vendored dpapiprobe
library (the Vista-and-later AES scheme). The meanings of the named secrets are taken
from published references, not Microsoft documentation except where noted; see the
notes field for the sources and what is and is not covered.
"""

__artifacts_v2__ = {
    "windowsLsaSecrets": {
        "name": "Windows LSA Secrets",
        "description": "LSA secrets from the SECURITY hive, decrypted with the boot key from the SYSTEM "
                       "hive: the secret name, a description of the named secret, its decrypted value and "
                       "the times its current and previous values were set.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Windows Registry",
        "notes": "Lists every secret under Policy\\Secrets in the SECURITY hive and decrypts its current value with the boot key from the SYSTEM hive, using the vendored dpapiprobe library (scripts/vendor/dpapiprobe, with PyCryptodome; it reads the hives with the vendored regfprobe); this is the Windows Vista and later AES scheme (PolEKList). Every secret is listed whether or not it decrypted, so one that could not be decrypted is reported with Status 'decrypt failed' rather than dropped. Both hives are opened read only, and an image with more than one Windows install is read install by install, each SECURITY hive paired with the SYSTEM hive of the same config folder. Current Value Set and Previous Value Set are the CupdTime and OupdTime values stored under the secret's Policy\\Secrets key (FILETIME, UTC), the update times the LSA records for the current and previous values. Value is the decrypted current value, shown as UTF-16LE text when it is printable (Value Encoding 'utf-16 text', used for the autologon and service-account passwords) and as hex otherwise (Value Encoding 'hex', for binary key material); Value Length is the decrypted value's size in bytes. A secret present with an empty current value is Status 'present, no current value' with an empty Value, which is not evidence a value was never set; when the SYSTEM hive or boot key is not available the secrets are still listed with names and timestamps and Status 'boot key unavailable', and a SECURITY hive that uses the pre-Vista scheme is listed with Status 'pre-Vista LSA scheme (not decrypted)', in both cases with no value shown. Secret Type is a short description of the named secret taken from published references rather than Microsoft documentation except where noted, and is a pointer to the secret's meaning, not a decoding of the stored bytes: DefaultPassword and CachedDefaultPassword are the Winlogon automatic-logon password (AutoAdminLogon); $MACHINE.ACC is the computer account credential the system holds for the domain secure channel; NL$KM is the key that decrypts the cached domain logon credentials under SECURITY\\Cache (MSCACHE/DCC2); DPAPI_SYSTEM is the machine DPAPI key (a machine half at offset 4 and a user half at offset 24) that protects the SYSTEM-context DPAPI master keys; M$_MSV1_0_TBAL_PRIMARY_<GUID> is the Automatic Restart Sign-On (ARSO), or Trusted Boot Auto-Logon, credential the MSV1_0 package saves to log a local account back on after an update reboot, reported from third-party research (vztekoverflow 2018, Passcape) and not from Microsoft; a name beginning _SC_ is a service account password and one beginning L$ is a local LSA secret; any other name is labelled '(undocumented)' with its value shown as text when printable, otherwise hex. Tested on ten Windows Vista-and-later images: af_case2_win10 (5 secrets, with a DefaultPassword value and a TBAL entry), szechuan_dc01_server2012r2 (4), alihadi_threatsim_server2019, ou_ransomware_server2022 and szechuan_win10 (3 each, carrying $MACHINE.ACC on the three domain machines), lonewolf_win10 (2), alihadi_challenge3_win81 and cfreds_leakage_win7 (2 each, DefaultPassword present with no current value), and hexordia_mvs2025_win11 and pc_mus_001_win11 (1 each, DPAPI_SYSTEM only). Not covered: this module decrypts the LSA secrets only; it does not read the cached domain logon credentials that NL$KM protects or the DPAPI-protected data that DPAPI_SYSTEM protects. Windows XP and Server 2003 use a pre-Vista LSA scheme (PolSecretEncryptionKey, not the PolEKList this module reads); such a hive is listed with Status 'pre-Vista LSA scheme (not decrypted)' and no value, confirmed on the SECURITY hive of cfreds_hacking_case_winxp (19 secrets listed, none decrypted). Value holds the decrypted secrets themselves.",
        "paths": (
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
        ),
        "output_types": "standard",
        "artifact_icon": "key",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 | 4 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 | 3 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 3 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "alihadi_challenge3_win81": "Windows 8.1 | 2 rows (DefaultPassword present, no current value)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows (DefaultPassword present, no current value)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row (DPAPI_SYSTEM only)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row (DPAPI_SYSTEM only)",
        },
    },
}

import struct
from datetime import datetime, timedelta, timezone

from scripts.windows_registry import Registry

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows LSA Secrets'
_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)

# Short descriptions of the named secrets, and how to render the value ('text' tries a
# UTF-16LE decode and falls back to hex; 'hex' is always hex). Sourced in the notes.
_TYPES = {
    'DefaultPassword': ('Winlogon automatic-logon password (AutoAdminLogon)', 'text'),
    'CachedDefaultPassword': ('Cached Winlogon automatic-logon password', 'text'),
    '$MACHINE.ACC': ('Computer account credential for the domain secure channel', 'hex'),
    'NL$KM': ('Key that decrypts the cached domain logon credentials (MSCACHE)', 'hex'),
    'DPAPI_SYSTEM': ('Machine DPAPI key protecting the SYSTEM DPAPI master keys', 'hex'),
}


def _classify(name):
    """A (description, value-kind) pair for a secret name."""
    if name in _TYPES:
        return _TYPES[name]
    if name.startswith('M$_MSV1_0_TBAL'):
        return ('Automatic Restart Sign-On (ARSO) auto-logon credential', 'hex')
    if name.startswith('_SC_'):
        return ('Service account password (service %s)' % name[4:], 'text')
    if name.startswith('L$'):
        return ('Local LSA secret', 'hex')
    return ('(undocumented)', 'text')


def _as_utf16_text(value):
    """The value as printable UTF-16LE text, or None if it is not clean text."""
    if len(value) % 2:
        return None
    try:
        text = value.decode('utf-16-le')
    except UnicodeDecodeError:
        return None
    text = text.rstrip('\x00')
    if text and all(char.isprintable() for char in text):
        return text
    return None


def _decode_value(value, kind):
    """(display value, encoding label) for a decrypted secret value."""
    if not value:
        return '', ''
    if kind != 'hex':
        text = _as_utf16_text(value)
        if text is not None:
            return text, 'utf-16 text'
    return value.hex(), 'hex'


def _filetime(raw):
    """A FILETIME (8 bytes LE) as an aware UTC datetime, or '' for absent/zero."""
    if not raw or len(raw) < 8:
        return ''
    ticks = struct.unpack('<Q', raw[:8])[0]
    if ticks == 0:
        return ''
    return _FILETIME_ZERO + timedelta(microseconds=ticks // 10)


def _secret_metadata(security_hive):
    """{name: (current-value-set, previous-value-set)} for every Policy\\Secrets entry."""
    meta = {}
    with open(security_hive, 'rb') as handle:
        reg = Registry.Registry(handle)
        try:
            root = reg.open('Policy\\Secrets')
        except Registry.RegistryKeyNotFoundException:
            return meta
        for sub in root.subkeys():
            cupd = oupd = ''
            for child in sub.subkeys():
                if child.name() == 'CupdTime':
                    cupd = _filetime(child.value('').value())
                elif child.name() == 'OupdTime':
                    oupd = _filetime(child.value('').value())
            meta[sub.name()] = (cupd, oupd)
    return meta


def _is_config_hive(path):
    return '/config/' in path.replace('\\', '/').lower()


def _config_dir(path):
    """The .../config directory of a hive path (the key for pairing SYSTEM with SECURITY)."""
    return path.replace('\\', '/').rsplit('/', 1)[0]


def _rows_for_install(context, security_hive, system_hive, data_list):
    """Append a row per LSA secret of one Windows install. Returns the hives actually read."""
    try:
        meta = _secret_metadata(security_hive)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f'{_LABEL}: could not read Policy\\Secrets from {security_hive}: '
                f'{type(ex).__name__}: {ex}')
        return []
    if not meta:
        return [security_hive]

    used = [security_hive]
    decrypted = {}
    blocked = None
    if not system_hive:
        blocked = 'boot key unavailable (SYSTEM hive not in extraction)'
    else:
        try:
            bootkey = dpapiprobe.get_bootkey(system_hive)
            used.append(system_hive)
            decrypted = dpapiprobe.get_lsa_secrets(security_hive, bootkey)
        except dpapiprobe.UnsupportedHive as ex:
            logfunc(f'{_LABEL}: {security_hive} uses a pre-Vista LSA scheme ({ex})')
            blocked = 'pre-Vista LSA scheme (not decrypted)'
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not decrypt the LSA secrets of {security_hive}: '
                    f'{type(ex).__name__}: {ex}')
            blocked = 'boot key unavailable'

    relative = context.get_relative_path(security_hive)
    for name in sorted(meta):
        cupd, oupd = meta[name]
        description, kind = _classify(name)
        if blocked:
            value, encoding, status, length = '', '', blocked, ''
        elif name in decrypted:
            raw = decrypted[name]
            if raw:
                value, encoding = _decode_value(raw, kind)
                status, length = 'recovered', len(raw)
            else:
                value, encoding, status, length = '', '', 'present, no current value', 0
        else:
            value, encoding, status, length = '', '', 'decrypt failed', ''
        data_list.append((cupd, oupd, name, description, value, encoding, length, status, relative))
    return used


@artifact_processor
def windowsLsaSecrets(context):
    data_headers = (('Current Value Set', 'datetime'), ('Previous Value Set', 'datetime'),
                    'Secret Name', 'Secret Type', 'Value', 'Value Encoding', 'Value Length',
                    'Status', 'Source File')
    data_list = []

    # Pair each SECURITY hive with the SYSTEM hive of the same config directory, so an
    # image with more than one Windows install is read install by install rather than
    # cross-pairing one install's SECURITY with another's boot key.
    installs = {}
    for found in context.get_files_found():
        path = str(found)
        if not _is_config_hive(path):
            continue
        name = path.replace('\\', '/').rsplit('/', 1)[-1]
        if name in ('SYSTEM', 'SECURITY'):
            installs.setdefault(_config_dir(path), {}).setdefault(name, path)

    sources = []
    for config_dir in sorted(installs):
        security_hive = installs[config_dir].get('SECURITY')
        if not security_hive:
            continue
        sources.extend(_rows_for_install(context, security_hive,
                                         installs[config_dir].get('SYSTEM'), data_list))

    return data_headers, data_list, '\n'.join(sources)
