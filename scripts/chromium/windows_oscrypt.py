"""Recover Windows Chromium os_crypt keys for the decryption artifacts.

Shared by the windowsChromium* artifacts. Collects the Windows hives, the user DPAPI
master keys and each installation's Local State from the files the seeker staged, builds a
master-key pool unlocked by the account's ARSO (TBAL) secret or by a cleartext password
supplied with --windows-user-password, and unwraps the per-installation os_crypt AES key.
The hives and master key files are opened read only. Decryption uses the vendored
dpapiprobe library.
"""

from scripts.chromium.browser_profiles import BROWSER_ROOTS
from scripts.context import Context
from scripts.ilapfuncs import logfunc
from scripts.vendor import dpapiprobe


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


def user_data_dir(relative):
    """The user data folder a Chromium file sits in, evidence-relative, or ''.

    Matches the same roots the profile locator uses, so a Local State and the Login Data
    or Cookies of its profiles share this key.
    """
    parts = [part for part in _norm(relative).split('/') if part]
    for _browser, root in BROWSER_ROOTS:
        width = len(root)
        for start in range(len(parts) - width + 1):
            if tuple(parts[start:start + width]) == root:
                return '/'.join(parts[:start + width])
    return ''


def _tbal_hashes(system_hive, security_hive, label):
    try:
        bootkey = dpapiprobe.get_bootkey(system_hive)
        secrets = dpapiprobe.get_lsa_secrets(security_hive, bootkey)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f'{label}: could not read LSA secrets from {security_hive}: {type(ex).__name__}')
        return []
    hashes = []
    for name, value in secrets.items():
        if name.startswith('M$_MSV1_0_TBAL'):
            parsed = dpapiprobe.parse_tbal(value)
            if parsed and parsed['sha1_hash']:
                hashes.append(parsed['sha1_hash'])
    return hashes


def _collect(context):
    """(installs, user_mks, local_states) from the staged files."""
    installs = {}          # hive root -> {'SYSTEM', 'SECURITY'}
    user_mks = {}          # SID -> [master-key file paths]
    local_states = {}      # user data folder -> Local State path
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
        elif name == 'Local State':
            udd = user_data_dir(context.get_relative_path(path))
            if udd:
                local_states[udd] = path
    return installs, user_mks, local_states


def _unlocked_pool(user_mks, sha1_hashes, password):
    pool = dpapiprobe.MasterKeyPool()
    candidates = []
    for sid, paths in user_mks.items():
        for sha1 in sha1_hashes:
            candidates.extend(dpapiprobe.user_master_key_candidates(sid, sha1_hash=sha1))
        if password:
            candidates.extend(dpapiprobe.user_master_key_candidates(sid, password=password))
        for path in paths:
            pool.add_file(path)
    if candidates:
        pool.decrypt_all(candidates)
    return pool


def recover_os_keys(context, label):
    """Return (pool, {user data folder: os_crypt AES key or None}).

    The pool is the user master keys unlocked by the account's TBAL secret or by the
    supplied password; it is also returned so an artifact can decrypt legacy per-value
    DPAPI blobs. os_crypt keys are unwrapped per installation from its Local State.
    """
    installs, user_mks, local_states = _collect(context)
    sha1_hashes = []
    for hives in installs.values():
        if hives.get('SYSTEM') and hives.get('SECURITY'):
            sha1_hashes.extend(_tbal_hashes(hives['SYSTEM'], hives['SECURITY'], label))
    password = Context.get_app_secret('windows_user_password')
    pool = _unlocked_pool(user_mks, sha1_hashes, password)
    os_keys = {}
    for udd, ls_path in local_states.items():
        try:
            key, _info = dpapiprobe.os_crypt_key(ls_path, pool)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read Local State {ls_path}: {type(ex).__name__}')
            key = None
        os_keys[udd] = key
    return pool, os_keys
