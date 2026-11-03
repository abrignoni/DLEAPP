"""Windows user Vault web credentials, decrypted offline, for DLEAPP.

The Windows Vault keeps saved web logins per user under
Users\\<u>\\AppData\\Local\\Microsoft\\Vault\\<GUID>\\, as a Policy.vpol (the vault's AES
keys, wrapped in a DPAPI blob) and one or more *.vcrd credential records. Opening them
needs the user's DPAPI master key. Where the account has an Automatic Restart Sign-On
(TBAL) secret, this module recovers the account's SHA-1 password hash from it with the
boot key alone and opens the master key without a password, then decrypts the vpol keys
and the vcrd records. Decryption and parsing use the vendored dpapiprobe library.
"""

__artifacts_v2__ = {
    "windowsUserVaultCredentials": {
        "name": "Windows User Vault Web Credentials",
        "description": "Saved web logins from a user's Windows Vault (the Internet Explorer / Web "
                       "Credentials schema), decrypted with the user DPAPI key recovered from the "
                       "account's ARSO (TBAL) secret: the resource (URL), user name and password.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Windows Registry",
        "notes": "Decrypts the saved web logins in a user's Windows Vault (Users\\<u>\\AppData\\Local\\Microsoft\\Vault\\<GUID>\\, a Policy.vpol holding the vault's AES keys wrapped in a DPAPI blob and one or more *.vcrd credential records). Opening a record needs the user's DPAPI master key: this module recovers it with the boot key alone from the account's Automatic Restart Sign-On (TBAL) secret (the TBAL SHA-1 password hash, salted with the account SID, opens the user master keys), then decrypts the vpol AES keys and, with them, the vcrd attributes; the vendored dpapiprobe library (scripts/vendor/dpapiprobe, PyCryptodome and python-registry) runs the chain. Last Written is the record's own FILETIME (UTC). Resource is the saved resource, typically the login URL; Username and Password are the stored credential, decoded as UTF-16LE. Vault Schema is the record's schema friendly name (Internet Explorer for web logins). Account is the Windows user folder the vault belongs to. Status is 'recovered' when the record decrypted, 'locked (user key not recovered)' when no vault policy key decrypted the record (this release recovers that key only from a TBAL/ARSO secret, so a missing ARSO secret or the account's master keys being absent from the extraction are two reasons it can happen), and 'decrypted, no web credential in this schema' for a record whose schema this module does not map to fields. The hives and master key files are opened read only. The vcrd attribute layout and the Internet Explorer / Web Credentials schema were read from a real record and follow impacket's documented structures; they are validated on one record on one image (af_case2_win10, user IEUser: a web login with a URL, user name and password recovered through that account's TBAL key), with no independent reference implementation to cross-check against and only that one record available. Key source: this release recovers the user key only from a TBAL/ARSO secret, so it decrypts a vault only where the account has one; recovering a vault from a supplied or cracked account password is a planned addition. Not covered: vault schemas other than Internet Explorer / Web Credentials, the user Credential Manager files, and vaults whose account key cannot be recovered here. Resource, Username and Password are the decrypted credential's own values.",
        "paths": (
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Users/*/AppData/Roaming/Microsoft/Protect/*/*',
            '*/Users/*/AppData/Local/Microsoft/Vault/*/Policy.vpol',
            '*/Users/*/AppData/Local/Microsoft/Vault/*/*.vcrd',
        ),
        "output_types": "standard",
        "artifact_icon": "key",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row (IEUser web login, recovered via the account's TBAL key)",
        },
    },
}

from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows User Vault Web Credentials'
_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _norm(path):
    return path.replace('\\', '/')


def _is_config_hive(path):
    return '/config/' in _norm(path).lower()


def _hive_root(path):
    lowered = _norm(path).lower()
    cut = lowered.find('/windows/system32/')
    return path[:cut] if cut != -1 else path


def _looks_like_guid(name):
    return len(name) == 36 and name.count('-') == 4


def _account_from_path(path):
    """The account folder in a ``Users\\<account>\\AppData`` path (evidence-relative)."""
    parts = _norm(path).split('/')
    for i in range(len(parts) - 2):
        if parts[i].lower() == 'users' and parts[i + 2].lower() == 'appdata':
            return parts[i + 1]
    return ''


def _filetime(ticks):
    if not ticks:
        return ''
    return _FILETIME_ZERO + timedelta(microseconds=ticks // 10)


def _tbal_hashes(system_hive, security_hive):
    """The SHA-1 password hashes from every TBAL secret in one install."""
    try:
        bootkey = dpapiprobe.get_bootkey(system_hive)
        secrets = dpapiprobe.get_lsa_secrets(security_hive, bootkey)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f'{_LABEL}: could not read LSA secrets from {security_hive}: {type(ex).__name__}')
        return []
    hashes = []
    for name, value in secrets.items():
        if name.startswith('M$_MSV1_0_TBAL'):
            parsed = dpapiprobe.parse_tbal(value)
            if parsed and parsed['sha1_hash']:
                hashes.append(parsed['sha1_hash'])
    return hashes


def _unlocked_pool(user_mks, sha1_hashes):
    """A MasterKeyPool of the user master keys that the TBAL hashes open."""
    pool = dpapiprobe.MasterKeyPool()
    candidates = []
    for sid, paths in user_mks.items():
        for sha1 in sha1_hashes:
            candidates.extend(dpapiprobe.user_master_key_candidates(sid, sha1_hash=sha1))
        for path in paths:
            pool.add_file(path)
    if candidates:
        pool.decrypt_all(candidates)
    return pool


@artifact_processor
def windowsUserVaultCredentials(context):
    data_headers = (('Last Written', 'datetime'), 'Resource', 'Username', 'Password',
                    'Vault Schema', 'Account', 'Status', 'Source File')
    data_list = []

    installs = {}            # hive root -> {'SYSTEM', 'SECURITY'}
    user_mks = {}            # SID -> [master-key bytes]
    vaults = {}              # vault directory -> {'vpol': path, 'vcrds': [paths]}
    for found in context.get_files_found():
        path = str(found)
        lowered = _norm(path).lower()
        name = _norm(path).rsplit('/', 1)[-1]
        if name in ('SYSTEM', 'SECURITY') and _is_config_hive(path):
            installs.setdefault(_hive_root(path), {}).setdefault(name, path)
        elif '/protect/' in lowered and _looks_like_guid(name):
            sid = _norm(path).rsplit('/', 2)[-2]
            if sid.upper().startswith('S-1-'):
                user_mks.setdefault(sid, []).append(path)
        elif '/microsoft/vault/' in lowered and (name.lower() == 'policy.vpol'
                                                  or lowered.endswith('.vcrd')):
            vault_dir = _norm(path).rsplit('/', 1)[0]
            slot = vaults.setdefault(vault_dir, {'vpol': None, 'vcrds': []})
            if name.lower() == 'policy.vpol':
                slot['vpol'] = path
            else:
                slot['vcrds'].append(path)

    if not vaults:
        return data_headers, data_list, ''

    sha1_hashes = []
    for hives in installs.values():
        if hives.get('SYSTEM') and hives.get('SECURITY'):
            sha1_hashes.extend(_tbal_hashes(hives['SYSTEM'], hives['SECURITY']))
    pool = _unlocked_pool(user_mks, sha1_hashes)

    sources = []
    for vault_dir in sorted(vaults):
        slot = vaults[vault_dir]
        if not slot['vcrds']:
            continue
        aes_keys = []
        if slot['vpol']:
            with open(slot['vpol'], 'rb') as handle:
                vpol = dpapiprobe.VaultPolicy(handle.read())
            vpol.decrypt_with_pool(pool)
            aes_keys = vpol.aes_key_candidates(32)
            if vpol.cleartexts:
                sources.append(slot['vpol'])
        for vcrd_path in sorted(slot['vcrds']):
            relative = context.get_relative_path(vcrd_path)
            account = _account_from_path(vcrd_path)
            with open(vcrd_path, 'rb') as handle:
                record = dpapiprobe.VaultCredential(handle.read())
            written = _filetime(record.last_written_filetime)
            schema = record.friendly_name
            sources.append(vcrd_path)
            decrypted, _key = record.decrypt(aes_keys) if aes_keys else ({}, None)
            if not decrypted:
                data_list.append((written, '', '', '', schema, account,
                                  'locked (user key not recovered)', relative))
                continue
            creds = [dpapiprobe.parse_web_credential(clear) for clear in decrypted.values()]
            creds = [cred for cred in creds if cred]
            if not creds:
                data_list.append((written, '', '', '', schema, account,
                                  'decrypted, no web credential in this schema', relative))
                continue
            for cred in creds:
                data_list.append((written, cred['resource'], cred['user'], cred['password'],
                                  schema, account, 'recovered', relative))

    return data_headers, data_list, '\n'.join(sources)
