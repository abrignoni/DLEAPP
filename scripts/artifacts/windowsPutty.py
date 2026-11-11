"""PuTTY registry parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

PuTTY for Windows keeps its saved sessions, its cache of SSH host keys and its list of recently loaded
saved sessions under Software\\SimonTatham\\PuTTY in the hive of the account that ran it. This reads the
three keys from each user's NTUSER.DAT. The layout is PuTTY's own storage code, cited in the notes.
"""

import base64
import hashlib
import os
import struct

from scripts.windows_registry import Registry

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import key_written_utc, open_hive

_PUTTY = 'Software\\SimonTatham\\PuTTY'
# Session values reported, in column order after Session.
_SESSION_VALUES = ('HostName', 'PortNumber', 'Protocol', 'UserName', 'ProxyMethod', 'ProxyHost', 'ProxyPort',
                   'PublicKeyFile', 'RemoteCommand', 'PortForwardings', 'LogType', 'LogFileName')
# Coordinate size in bytes of the curves RFC 5656 (10.1) requires.
_ECDSA_CURVES = {'nistp256': 32, 'nistp384': 48, 'nistp521': 66}

__artifacts_v2__ = {
    "windowsPuttySessions": {
        "name": "PuTTY Saved Sessions",
        "description": "Saved session entries under PuTTY's Sessions key in each account's registry hive: the session name, host, "
                       "port, protocol and other connection settings, as stored, with the session key's last "
                       "written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none (vendored regfprobe)",
        "category": "PuTTY",
        "notes": ('Read from Software\\SimonTatham\\PuTTY in each NTUSER.DAT under Users and under '
                  'Windows/ServiceProfiles; the PuTTY manual gives that key as where PuTTY for Windows stores saved '
                  'sessions and host keys (https://the.earth.li/~sgtatham/putty/0.85/htmldoc/AppendixA.html, A.5.2). '
                  'Source citations are to PuTTY 0.85 (commit a3cce3a) in a mirror whose cited files are byte for byte '
                  'those of the PuTTY repository at that commit. One row per subkey of Sessions '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/windows/storage.c#L23). '
                  "Session is the subkey's name with each %XX read back as the byte it stands for, the reverse of how "
                  'PuTTY names the key '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/windows/utils/escape_registry_key.c#L12-L47); '
                  'the bytes are then read as UTF-8, or as Latin-1 when they are not UTF-8, and names outside ASCII are '
                  'unexercised: on the known data the keys kd%20putty%20lab and kd.second%2Asession were the sessions '
                  "saved as 'kd putty lab' and 'kd.second*session'. Host Name, Port, Protocol, User Name, Proxy Method "
                  '(as stored), Proxy Host, Proxy Port, Public Key File, Remote Command, Port Forwardings, Log Type (as '
                  "stored) and Log File Name are the session's HostName, PortNumber, Protocol, UserName, ProxyMethod, "
                  'ProxyHost, ProxyPort, PublicKeyFile, RemoteCommand, PortForwardings, LogType and LogFileName values '
                  'as stored, blank when the value is absent, is an empty string or could not be read (named in the run '
                  'log); Proxy Method and Log Type are numbers and are not given names here. Each known-data session '
                  'held 242 values, and the others are not reported. The four known-data sessions were saved with only '
                  "a host, a port and a session name entered, and PuTTY wrote Proxy Host 'proxy', Proxy Port 80, Proxy "
                  "Method 0, Log File Name 'putty.log' and Log Type 0 for each, so those two names are present without "
                  'a proxy or a log file having been set; On those four rows Protocol (ssh), Proxy Method (as stored), '
                  'Proxy Host, Proxy Port, Log Type (as stored), Log File Name and Profile each held one value, and '
                  'User Name, Public Key File, Remote Command and Port Forwardings each held no value on any row (an '
                  'empty string in the hive). On the known data a host entered as user@host was stored whole in '
                  "HostName and UserName was empty. Session Key Last Written (UTC) is the subkey's last written time: "
                  'for the two sessions PuTTY alone wrote it was within 25 milliseconds of the logged press of Save, '
                  'and for the two whose values were then changed with reg add it was 55 and 57 seconds after the '
                  "logged Save; the time of the reg add itself was not logged. Microsoft describes a key's last write "
                  'time as the last time the key or any of its values was modified '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/winreg/nf-winreg-regqueryinfokeyw.md#L140-L141). '
                  'A row shows the settings now stored under the session key. It does not show that the session was '
                  'used, or that PuTTY wrote every value. PuTTY Recent Sessions and PuTTY SSH Host Keys read what PuTTY '
                  'stores when a saved session is loaded and when a host key is cached. Measured on one input only, the '
                  'Windows 11 build 26200 known data made with PuTTY 0.85 in one user profile. None of the 41 '
                  'NTUSER.DAT files read from the eight other inputs below held the PuTTY key (14 of them service '
                  'profile hives). Other PuTTY versions, and a service profile hive that holds the key, are '
                  'unexercised. A hive that cannot be opened is named in the run log and skipped. Profile is the folder '
                  'that holds the NTUSER.DAT.'),
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Windows/ServiceProfiles/*/NTUSER.DAT',
                  '*/Windows/ServiceProfiles/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "windows11_arm_putty_known_20261111": "Windows 11 build 26200 (ARM64), PuTTY 0.85 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
        },
    },
    "windowsPuttyHostKeys": {
        "name": "PuTTY SSH Host Keys",
        "description": "SSH host keys PuTTY cached in each account's registry hive: the host, port and key type "
                       "each was stored for, the stored key, and a SHA-256 fingerprint computed from it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none (vendored regfprobe)",
        "category": "PuTTY",
        "notes": ('Read from Software\\SimonTatham\\PuTTY in each NTUSER.DAT under Users and under '
                  'Windows/ServiceProfiles; the PuTTY manual gives that key as where PuTTY for Windows stores saved '
                  'sessions and host keys (https://the.earth.li/~sgtatham/putty/0.85/htmldoc/AppendixA.html, A.5.2). '
                  'Source citations are to PuTTY 0.85 (commit a3cce3a) in a mirror whose cited files are byte for byte '
                  'those of the PuTTY repository at that commit. One row per value of SshHostKeys. PuTTY names each '
                  'value keytype@port:host, the host escaped as a session name is '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/windows/storage.c#L267-L271), '
                  'and stores the key as text: an RSA key as its exponent and modulus, each 0x and hex '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/crypto/rsa.c#L293-L301), '
                  "and an elliptic curve key as its point's x and y, with the curve name first for ECDSA "
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/crypto/ecc-ssh.c#L677-L687). '
                  'Key Type, Port and Host are the three parts of the value name, and Stored Key is the value as '
                  'stored; a name of any other form is shown whole in Host with Key Type and Port blank. Key '
                  'Fingerprint (SHA-256, computed) is not stored: it is the SHA-256 of the SSH public key built from '
                  'the stored numbers, in the SHA256: base-64 form OpenSSH prints, for rsa2 (RFC 4253, 6.6), '
                  'ssh-ed25519 (RFC 8709, 4) and ecdsa-sha2-nistp256, nistp384 and nistp521 (RFC 5656, 3.1), and blank '
                  'for any other key type or a stored value not in that form. On the known data the three rows, an '
                  'ssh-ed25519, an rsa2 (3,072 bits) and an ecdsa-sha2-nistp256 key, each gave the fingerprint '
                  "ssh-keygen -lf printed for the server's public key of that type, and the Ed25519 one was also the "
                  "fingerprint PuTTY's own prompt showed; nistp384 and nistp521 follow the same construction and were "
                  "not exercised. On the known data each value appeared after Accept was pressed in PuTTY's host key "
                  'prompt. In the source Connect Once does not store the key '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/windows/dialog.c#L1206-L1211); '
                  "that was not tested. The command-line tools' prompt and the storing of another key type for a host "
                  'already cached also write here and were not exercised. Host is the name PuTTY stored the key under, '
                  "the host connected to, or the session's logical host name when one is set (unexercised): the known "
                  "data's three rows are one server reached under three names. No time is stored per key. SshHostKeys "
                  "Key Last Written (UTC) is the key's last written time, the same on every row of a hive: on the known "
                  'data it was 5.3 milliseconds after the logged press of Accept for the last key added, and Microsoft '
                  'describes it as the last time the key or any of its values was modified '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/winreg/nf-winreg-regqueryinfokeyw.md#L140-L141), '
                  'so it dates the latest change to the cache and no other row. SshHostKeys Key Last Written (UTC), '
                  'Port and Profile each held one value on all 3 rows. Measured on one input only, the Windows 11 build '
                  '26200 known data made with PuTTY 0.85 in one user profile. None of the 41 NTUSER.DAT files read from '
                  'the eight other inputs below held the PuTTY key (14 of them service profile hives). Other PuTTY '
                  'versions, and a service profile hive that holds the key, are unexercised. A hive that cannot be '
                  'opened is named in the run log and skipped. Profile is the folder that holds the NTUSER.DAT.'),
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Windows/ServiceProfiles/*/NTUSER.DAT',
                  '*/Windows/ServiceProfiles/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "windows11_arm_putty_known_20261111": "Windows 11 build 26200 (ARM64), PuTTY 0.85 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
        },
    },
    "windowsPuttyRecentSessions": {
        "name": "PuTTY Recent Sessions",
        "description": "The list of recently loaded saved sessions PuTTY keeps for its jump list in each "
                       "account's registry hive, in stored order.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none (vendored regfprobe)",
        "category": "PuTTY",
        "notes": ('Read from Software\\SimonTatham\\PuTTY in each NTUSER.DAT under Users and under '
                  'Windows/ServiceProfiles; the PuTTY manual gives that key as where PuTTY for Windows stores saved '
                  'sessions and host keys (https://the.earth.li/~sgtatham/putty/0.85/htmldoc/AppendixA.html, A.5.2). '
                  'Source citations are to PuTTY 0.85 (commit a3cce3a) in a mirror whose cited files are byte for byte '
                  'those of the PuTTY repository at that commit. One row per name in the Recent sessions value '
                  '(REG_MULTI_SZ) of the Jumplist key '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/windows/storage.c#L21-L22), '
                  'in stored order: Position 1 is the first name stored. When PuTTY loads a saved session that has a '
                  'host, at launch or with Load in its configuration dialog '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/settings.c#L693-L706), '
                  'it writes the name at the beginning of the list and drops its earlier entry, and drops names that no '
                  'longer have a saved session '
                  '(https://github.com/larryli/PuTTY/blob/a3cce3a48d4ab12e0fccb32998b9042d4f7c3ff1/windows/storage.c#L718-L745). '
                  'A name in the list does not by itself show a connection, and Load without a launch was not tested. '
                  'On the known data three saved sessions were launched and the stored order was the reverse of the '
                  'order of their last launches; the one saved session never launched was not in the list. Session is '
                  "the name as stored, which is the session's own name and not its escaped key name. No time is stored "
                  "per name. Jumplist Key Last Written (UTC) is the key's last written time, the same on every row of a "
                  'hive: on the known data it was 34 milliseconds after the logged start of the last launch, so it '
                  'dates the latest write to the list. Jumplist Key Last Written (UTC) and Profile each held one value '
                  'on all 3 rows. Measured on one input only, the Windows 11 build 26200 known data made with PuTTY '
                  '0.85 in one user profile. None of the 41 NTUSER.DAT files read from the eight other inputs below '
                  'held the PuTTY key (14 of them service profile hives). Other PuTTY versions, and a service profile '
                  'hive that holds the key, are unexercised. A hive that cannot be opened is named in the run log and '
                  'skipped. Profile is the folder that holds the NTUSER.DAT.'),
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Windows/ServiceProfiles/*/NTUSER.DAT',
                  '*/Windows/ServiceProfiles/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "windows11_arm_putty_known_20261111": "Windows 11 build 26200 (ARM64), PuTTY 0.85 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no NTUSER.DAT holds a Software\\SimonTatham\\PuTTY key)",
        },
    },
}


def unescape(name):
    """A session or host name from the registry name PuTTY stored it under: %XX is the byte XX.

    Follows unescape_registry_key in PuTTY's windows/utils/escape_registry_key.c, except that a % not
    followed by two hex digits is kept as it is. The bytes are read as UTF-8, and as Latin-1 when they are
    not UTF-8."""
    raw = bytearray()
    at = 0
    while at < len(name):
        if name[at] == '%' and at + 2 < len(name):
            try:
                raw.append(int(name[at + 1:at + 3], 16))
                at += 3
                continue
            except ValueError:
                pass
        raw.extend(name[at].encode('utf-8'))
        at += 1
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def host_key_name(name):
    """(key type, port, host) from a SshHostKeys value name of the form keytype@port:host.

    A name of any other form is returned as ('', '', the name unescaped)."""
    head, at, rest = name.partition('@')
    port, colon, host = rest.partition(':')
    if not at or not colon or not port.isdigit():
        return '', '', unescape(name)
    return head, int(port), unescape(host)


def _string(raw):
    return struct.pack('>I', len(raw)) + raw


def _mpint(number):
    raw = number.to_bytes((number.bit_length() + 8) // 8, 'big') if number else b''
    return _string(raw)


def _numbers(parts):
    return [int(part, 16) for part in parts if part.lower().startswith('0x')]


def public_key_blob(key_type, stored):
    """The SSH public key blob for a stored host key, or None for a type or form not handled.

    PuTTY stores an RSA key as 0x<exponent>,0x<modulus>, an Ed25519 key as 0x<x>,0x<y> and an ECDSA key as
    <curve>,0x<x>,0x<y>. The blobs are ssh-rsa (RFC 4253, 6.6), ssh-ed25519 (RFC 8709, 4: the 32-byte
    encoding of the point, y little-endian with the low bit of x in the top bit, RFC 8032, 5.1.2) and
    ecdsa-sha2-<curve> (RFC 5656, 3.1: the uncompressed point 04 || x || y)."""
    parts = [part.strip() for part in str(stored).split(',')]
    try:
        if key_type == 'rsa2' and len(parts) == 2:
            exponent, modulus = _numbers(parts)
            return _string(b'ssh-rsa') + _mpint(exponent) + _mpint(modulus)
        if key_type == 'ssh-ed25519' and len(parts) == 2:
            x, y = _numbers(parts)
            point = bytearray(y.to_bytes(32, 'little'))
            point[31] |= (x & 1) << 7
            return _string(b'ssh-ed25519') + _string(bytes(point))
        if key_type.startswith('ecdsa-sha2-') and len(parts) == 3 and parts[0] in _ECDSA_CURVES:
            if key_type != 'ecdsa-sha2-' + parts[0]:
                return None
            size = _ECDSA_CURVES[parts[0]]
            x, y = _numbers(parts[1:])
            point = b'\x04' + x.to_bytes(size, 'big') + y.to_bytes(size, 'big')
            return _string(key_type.encode('ascii')) + _string(parts[0].encode('ascii')) + _string(point)
    except (ValueError, OverflowError):
        return None
    return None


def fingerprint(key_type, stored):
    """SHA256:<base-64 without padding> of the public key blob, the form OpenSSH prints, or ''."""
    blob = public_key_blob(key_type, stored)
    if blob is None:
        return ''
    return 'SHA256:' + base64.b64encode(hashlib.sha256(blob).digest()).decode('ascii').rstrip('=')


def _stored(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, list):
        return '; '.join(str(item) for item in value)
    return value


def profile_of(relative):
    """The folder that holds the NTUSER.DAT."""
    parts = relative.replace('\\', '/').rstrip('/').split('/')
    return parts[-2] if len(parts) >= 2 else ''


def _putty_keys(context, label):
    """[(staged hive path, profile, PuTTY key)] for each NTUSER.DAT that holds the PuTTY key."""
    found = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if not os.path.isfile(source) or os.path.basename(source).upper() != 'NTUSER.DAT':
            continue
        relative = context.get_relative_path(source)
        try:
            key = open_hive(source, context).open(_PUTTY)
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        found.append((source, profile_of(relative), key))
    return found


def _subkey(key, name):
    try:
        return key.subkey(name)
    except Registry.RegistryKeyNotFoundException:
        return None


@artifact_processor
def windowsPuttySessions(context):
    data_headers = (('Session Key Last Written (UTC)', 'datetime'), 'Session', 'Host Name', 'Port', 'Protocol',
                    'User Name', 'Proxy Method (as stored)', 'Proxy Host', 'Proxy Port', 'Public Key File',
                    'Remote Command', 'Port Forwardings', 'Log Type (as stored)', 'Log File Name', 'Profile')
    data_list, sources = [], []
    for source, profile, putty in _putty_keys(context, 'PuTTY Saved Sessions'):
        sessions = _subkey(putty, 'Sessions')
        if sessions is None:
            continue
        sources.append(source)
        for session in sessions.subkeys():
            values = {value.name(): value for value in session.values()}
            row = [key_written_utc(session), unescape(session.name())]
            for name in _SESSION_VALUES:
                try:
                    row.append(_stored(values[name].value()) if name in values else '')
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logfunc(f'PuTTY Saved Sessions: could not read {name} under {session.name()}: {exc}')
                    row.append('')
            row.append(profile)
            data_list.append(tuple(row))
    data_list.sort(key=lambda row: (row[-1], row[0] == '', str(row[0]), row[1]))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsPuttyHostKeys(context):
    data_headers = (('SshHostKeys Key Last Written (UTC)', 'datetime'), 'Host', 'Port', 'Key Type',
                    'Key Fingerprint (SHA-256, computed)', 'Stored Key', 'Profile')
    data_list, sources = [], []
    for source, profile, putty in _putty_keys(context, 'PuTTY SSH Host Keys'):
        cache = _subkey(putty, 'SshHostKeys')
        if cache is None:
            continue
        sources.append(source)
        written = key_written_utc(cache)
        for value in cache.values():
            key_type, port, host = host_key_name(value.name())
            try:
                stored = _stored(value.value())
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logfunc(f'PuTTY SSH Host Keys: could not read {value.name()}: {exc}')
                stored = ''
            data_list.append((written, host, port, key_type, fingerprint(key_type, stored), stored, profile))
    data_list.sort(key=lambda row: (row[-1], row[1], str(row[2]), row[3]))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsPuttyRecentSessions(context):
    data_headers = (('Jumplist Key Last Written (UTC)', 'datetime'), 'Position', 'Session', 'Profile')
    data_list, sources = [], []
    for source, profile, putty in _putty_keys(context, 'PuTTY Recent Sessions'):
        jumplist = _subkey(putty, 'Jumplist')
        if jumplist is None:
            continue
        try:
            stored = jumplist.value('Recent sessions').value()
        except Registry.RegistryValueNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'PuTTY Recent Sessions: could not read the Recent sessions value: {exc}')
            continue
        sources.append(source)
        names = stored if isinstance(stored, list) else [stored]
        written = key_written_utc(jumplist)
        position = 0
        for name in names:
            if not name:
                continue
            position += 1
            data_list.append((written, position, str(name), profile))
    data_list.sort(key=lambda row: (row[-1], row[1]))
    return data_headers, data_list, '\n'.join(sources)
