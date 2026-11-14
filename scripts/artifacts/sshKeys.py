"""Public keys in OpenSSH authorized_keys files and host keys in known_hosts files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sshAuthorizedKeys": {
        "name": "SSH Authorized Keys",
        "description": "Public keys in OpenSSH authorized_keys files, which sshd reads by default for public key "
                       "authentication to the account, and in the administrators_authorized_keys file of Windows "
                       "OpenSSH, with each key's SHA256 fingerprint, type, comment and options.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-10-23",
        "requirements": "none",
        "category": "SSH",
        "notes": "Reads each authorized_keys and authorized_keys2 file in a .ssh folder, "
                 "one row per key line in file order. OpenSSH 10.2p1's sshd reads those "
                 "two files by default for public key authentication, each line holding an "
                 "optional options field, the key type, the base64-encoded key and a "
                 "comment, separated by spaces, with empty lines and lines beginning with "
                 "# ignored "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd.8#L440-L455). "
                 "Options is the options field as stored, which ends at the first space or "
                 "tab outside double quotes, and Key Type and Comment are those fields as "
                 "stored. Fingerprint (SHA256) is the SHA-256 of the key's stored bytes in "
                 "base64 with its padding removed, the way OpenSSH prints the fingerprint "
                 "of a key it has encoded "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshkey.c#L965-L1025); "
                 "on the keys tested, which include synthetic keys built for the unit "
                 "tests, it equals what ssh-keygen prints, while an RSA key whose stored "
                 "modulus carries redundant leading zero bytes, not the way OpenSSH "
                 "encodes one, prints differently in ssh-keygen. A certificate's "
                 "fingerprint, which OpenSSH takes over the certified key alone, is left "
                 "blank and counted in the run log. A line that does not hold a key whose "
                 "stored bytes begin with its own type is counted in the run log and not "
                 "reported. Source File names the file each row came from, since the paths "
                 "can match more than one account's .ssh folder. On "
                 "ubuntu2604_arm64_triage the file held 1 key, ssh-ed25519, whose "
                 "fingerprint equals what ssh-keygen prints for that file and the "
                 "fingerprint sshd logged for all 416 logins with a public key in auth.log "
                 "and its three rotations. The key carried no options, so Options is blank "
                 "on that image."
                 " On ubuntu2604_arm64_sshkeys, known data written with ssh-keygen 10.2p1, authorized_keys and "
                 "authorized_keys2 give 5 rows: Options keeps a quoted option field holding escaped quotes as "
                 "stored, the key made with no comment has Comment blank and the certificate's fingerprint is "
                 "blank. A line whose key is not base64 and one whose options open a quote they never close are"
                 " counted in the run log and not reported, as sshd skips them "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/auth2-pubkeyfile.c#L284-L299"
                 " and "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/authfile.c#L469-L484)."
                 " Every other fingerprint equals what ssh-keygen -lf prints for those files."
                 " ProgramData/ssh/administrators_authorized_keys is read the same way: Microsoft's OpenSSH Server "
                 "Configuration for Windows says that when the user belongs to the administrator group, "
                 "%programdata%/ssh/administrators_authorized_keys is used instead of the account's .ssh/authorized_keys "
                 "(https://github.com/MicrosoftDocs/windowsserverdocs/blob/5abff92b2dc270ef58ef88a7b471219541d7feb1/"
                 "WindowsServerDocs/administration/OpenSSH/openssh-server-configuration.md#L118-L122), and the default "
                 "sshd_config of Win32-OpenSSH names it in a Match Group administrators section "
                 "(https://github.com/PowerShell/openssh-portable/blob/274893f8d1fe86c4d128b514c3af4bc10cdc0c99/"
                 "contrib/win32/openssh/sshd_config#L85-L86), so the file applies only where the configuration in "
                 "effect says so. No tested image holds that file, so it was tested with constructed input only.",
        "paths": ('*/.ssh/authorized_keys', '*/.ssh/authorized_keys2', '*/ProgramData/ssh/administrators_authorized_keys'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 5 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1 row",
        },
    },
    "sshKnownHosts": {
        "name": "SSH Known Hosts",
        "description": "Host keys recorded in OpenSSH known_hosts files, with the host names as stored, whether "
                       "they are hashed, and each key's type and SHA256 fingerprint.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-10-23",
        "requirements": "none",
        "category": "SSH",
        "notes": "Reads each known_hosts, known_hosts2 and known_hosts.old file in a .ssh folder and each "
                 "ssh_known_hosts and ssh_known_hosts2 file in an etc/ssh or ProgramData/ssh folder, one row "
                 "per key line in file order; ssh_config(5) of OpenSSH 10.2p1 names these "
                 "as the default user and global host key files "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L2191-L2193, "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L972-L974). "
                 "Its sshd(8) documents each line as an optional marker, the host names, "
                 "the key type, the base64-encoded key and a comment, separated by spaces, "
                 "with @cert-authority and @revoked the only markers, host names a "
                 "comma-separated list of patterns, a hashed host name starting with | and "
                 "hiding the host names and addresses, and empty lines and lines beginning "
                 "with # ignored "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd.8#L713-L787). "
                 "Hosts, Marker, Key Type and Comment are those fields as stored, and "
                 "Hashed is yes where the host names start with |. Fingerprint (SHA256) is "
                 "worked out as in SSH Authorized Keys. A line with another marker, or one "
                 "that does not hold host names and a key, is counted in the run log and "
                 "not reported. On ubuntu2604_arm64_triage the file held 1 hashed "
                 "ssh-ed25519 entry, which ssh-keygen finds when asked for localhost and "
                 "not when asked for the VM's own address, left by the known ssh "
                 "connection to localhost at 2026-09-28 06:45:33 UTC; its fingerprint "
                 "equals that of the VM's ssh_host_ed25519_key.pub. On pc_mus_001_win11 a "
                 "known_hosts file in a Windows user profile folder held 1 ssh-ed25519 "
                 "entry whose host is an IPv4 address in plain text, and its fingerprint "
                 "equals what ssh-keygen prints for that file. Marker and Comment were "
                 "blank on the entries of both images, and Hashed was blank on the "
                 "plain-text entry of pc_mus_001_win11."
                 " ssh-keygen -H and -R keep the file they replace as known_hosts.old, and when it has hashed host "
                 "names that were in plain text "
                 "ssh-keygen warns that the .old file contains unhashed entries "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh-keygen.c#L1324-L1349)."
                 " ssh-keygen -H writes each comma-separated host name as its own hashed line and leaves a line"
                 " alone when its host names are already hashed, hold a wildcard or follow a marker "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh-keygen.c#L1144-L1170)."
                 " On ubuntu2604_arm64_sshkeys, known data written with ssh-keygen 10.2p1, known_hosts holds 6 "
                 "entries: the two names of one line hashed onto 2 lines, a hashed [host]:port line, a @revoked"
                 " line and a @cert-authority line whose host names ssh-keygen -H left in plain text, and one "
                 "plain line added afterwards; its known_hosts.old holds the 4 lines as they were before "
                 "hashing, every host name in plain text; etc/ssh/ssh_known_hosts holds 1. Each fingerprint "
                 "ssh-keygen -lf prints for those files, which list no marker line, equals the one reported."
                 " The Windows port of OpenSSH in PowerShell/openssh-portable defines the global host key files as SSHDIR "
                 "/ssh_known_hosts and /ssh_known_hosts2 "
                 "(https://github.com/PowerShell/openssh-portable/blob/274893f8d1fe86c4d128b514c3af4bc10cdc0c99/"
                 "pathnames.h#L29-L31) with SSHDIR set to __PROGRAMDATA__\\ssh "
                 "(https://github.com/PowerShell/openssh-portable/blob/274893f8d1fe86c4d128b514c3af4bc10cdc0c99/"
                 "contrib/win32/openssh/config.h.vs#L1728); Microsoft says the server's host keys, which the default "
                 "sshd_config lists under __PROGRAMDATA__/ssh, are stored under C:\\ProgramData\\ssh "
                 "(https://github.com/MicrosoftDocs/windowsserverdocs/blob/5abff92b2dc270ef58ef88a7b471219541d7feb1/"
                 "WindowsServerDocs/administration/OpenSSH/OpenSSH_KeyManagement.md#L53 and "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/5abff92b2dc270ef58ef88a7b471219541d7feb1/"
                 "WindowsServerDocs/administration/OpenSSH/openssh-server-configuration.md#L165-L173). No tested image holds "
                 "either file there, so those paths were tested with constructed input only.",
        "paths": ('*/.ssh/known_hosts', '*/.ssh/known_hosts2', '*/.ssh/known_hosts.old',
                  '*/etc/ssh/ssh_known_hosts', '*/etc/ssh/ssh_known_hosts2', '*/ProgramData/ssh/ssh_known_hosts',
                  '*/ProgramData/ssh/ssh_known_hosts2'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "server",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (root's known_hosts is empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 11 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1 row",
        },
    },
    "sshKeyFiles": {
        "name": "SSH Key Files",
        "description": "Private and public SSH key files (a user's .ssh/id_* and .pub files and the "
                       "host keys in etc/ssh and ProgramData/ssh), with each key's kind and type, "
                       "its SHA256 fingerprint where one is computed, whether an OpenSSH-format "
                       "private key is encrypted, and the comment of a public key file. The "
                       "private part of a key is not parsed, decrypted or reported: the type and "
                       "fingerprint of an OpenSSH private key come from the public key stored "
                       "unencrypted inside it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "SSH",
        "notes": "One row per private key file, and one row per key line of a public key file. A "
                 "public key file (a .pub, or a host key's .pub) is read as lines holding a type, "
                 "a base64 key and an optional comment; Fingerprint (SHA256) is the SHA-256 of the "
                 "key's stored bytes in base64 with its padding removed, the way OpenSSH prints a "
                 "key's fingerprint, computed with the same read_key used by SSH Authorized Keys "
                 "and SSH Known Hosts. A certificate's fingerprint is left blank and counted in "
                 "the run log. A private key file in the OpenSSH format (-----BEGIN OPENSSH PRIVATE "
                 "KEY-----) carries its first public key unencrypted even when the private key is "
                 "passphrase-encrypted (https://github.com/openssh/openssh-portable/blob/"
                 "d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/PROTOCOL.key#L5-L19); the Key Type and "
                 "Fingerprint (SHA256) are read from that public key, and Encrypted is yes when the "
                 "file's cipher name is not none and no when it is none "
                 "(https://github.com/openssh/openssh-portable/blob/"
                 "d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/PROTOCOL.key#L59-L69). A private key "
                 "file with any other -----BEGIN ... PRIVATE KEY----- header (RSA, EC, DSA, PRIVATE "
                 "KEY, ENCRYPTED PRIVATE KEY) has its Key Type set to the label in the header (RSA, "
                 "EC or DSA), blank for a PKCS#8 header which names no algorithm; Encrypted is yes "
                 "when the header says ENCRYPTED or the file has a DEK-Info line, and blank "
                 "otherwise, where blank does not mean the key is unencrypted; this artifact does "
                 "not compute a fingerprint for these files, so Fingerprint is blank. No tested "
                 "image holds such a legacy PEM key and no unit test covers it, so that branch is "
                 "implemented from the code only. Comment is blank for a private key; the OpenSSH "
                 "format keeps the comment in the private key list "
                 "(https://github.com/openssh/openssh-portable/blob/"
                 "d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/PROTOCOL.key#L30-L44), which this "
                 "artifact does not read, and a .pub beside it can carry a comment. On "
                 "ubuntu2604_arm64_sshkeyfiles_known_20261113 (known data made with ssh-keygen "
                 "10.2p1) the four private keys, their four .pub files and three host .pub files "
                 "give 11 rows; every fingerprint equals what ssh-keygen -lf prints for that file, "
                 "including id_ed25519_enc, whose private key is encrypted (aes256-ctr) while its "
                 "fingerprint reads from the plaintext public key. No tested image holds a host "
                 "private key, a ProgramData/ssh key or a certificate, and a private key saved "
                 "under a name that does not start with id_ or ssh_host_ is not read. "
                 "authorized_keys and known_hosts in the same folder are not read here; they are "
                 "covered by SSH Authorized Keys and SSH Known Hosts. A line of a public key file "
                 "that does not hold a key, and an OpenSSH-format private key that could not be "
                 "parsed, are counted in the run log and not reported; an empty file gives no row "
                 "and no count. Source File names the file each row came from.",
        "paths": ('*/.ssh/id_*', '*/.ssh/*.pub', '*/etc/ssh/ssh_host_*', '*/ProgramData/ssh/ssh_host_*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "ubuntu2604_arm64_sshkeyfiles_known_20261113": "Ubuntu 26.04 LTS aarch64 | 11 rows",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import base64
import binascii
import hashlib
import os
import re
import struct
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

_KEY = re.compile(r'(\S+)\s+(\S+)(?:\s+(.*))?')
_MARKERS = ('@cert-authority', '@revoked')


def _lines(data):
    return [line.rstrip('\r') for line in data.decode('utf-8', errors='replace').split('\n')]


def _field(text):
    """(first field, separator, the rest after the spaces or tabs that follow it)."""
    match = re.match(r'(\S+)([ \t]+)(.*)', text)
    return (match.group(1), match.group(2), match.group(3)) if match else (text, '', '')


def _blob_type(blob):
    """The key type name a public key blob begins with, or None when it does not begin with one."""
    if len(blob) < 4:
        return None
    (length,) = struct.unpack('>I', blob[:4])
    if len(blob) < 4 + length:
        return None
    return blob[4:4 + length].decode('ascii', errors='replace')


def read_key(key_type, encoded, counts):
    """(fingerprint, is a key): the SHA256 fingerprint OpenSSH prints for the key, blank for a
    certificate or a key whose stored bytes do not name its type."""
    try:
        blob = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return '', False
    if _blob_type(blob) != key_type:
        return '', False
    if key_type.endswith('-cert-v01@openssh.com'):
        counts['certificates, fingerprint not computed'] += 1
        return '', True
    return 'SHA256:' + base64.b64encode(hashlib.sha256(blob).digest()).decode('ascii').rstrip('='), True


def _options_end(line):
    """Where the options field of an authorized_keys line ends: at the first space or tab outside
    double quotes, a backslash-escaped quote not ending a quoted run."""
    quoted, i = False, 0
    while i < len(line):
        char = line[i]
        if char == '\\' and quoted and line[i + 1:i + 2] == '"':
            i += 2
            continue
        if char == '"':
            quoted = not quoted
        elif char in ' \t' and not quoted:
            return i
        i += 1
    return len(line)


def authorized_key_rows(data, counts):
    """(fingerprint, type, comment, options, line number) for each key line of an authorized_keys file."""
    rows = []
    for number, line in enumerate(_lines(data), 1):
        text = line.lstrip(' \t')
        if not text or text.startswith('#'):
            continue
        options = ''
        match = _KEY.fullmatch(text)
        fingerprint, is_key = read_key(match.group(1), match.group(2), counts) if match else ('', False)
        if not is_key:
            end = _options_end(text)
            options, rest = text[:end], text[end:].lstrip(' \t')
            match = _KEY.fullmatch(rest)
            fingerprint, is_key = read_key(match.group(1), match.group(2), counts) if match else ('', False)
        if not is_key:
            counts['authorized_keys lines that do not hold a key, not reported'] += 1
            continue
        rows.append((fingerprint, match.group(1), match.group(3) or '', options, number))
    return rows


def known_host_rows(data, counts):
    """(hosts, hashed, marker, type, fingerprint, comment, line number) for each key line of a known_hosts file."""
    rows = []
    for number, line in enumerate(_lines(data), 1):
        text = line.lstrip(' \t')
        if not text or text.startswith('#'):
            continue
        marker = ''
        if text.startswith('@'):
            marker, _, text = _field(text)
            if marker not in _MARKERS:
                counts['known_hosts lines with a marker OpenSSH does not define, not reported'] += 1
                continue
        hosts, _, rest = _field(text)
        match = _KEY.fullmatch(rest)
        fingerprint, is_key = read_key(match.group(1), match.group(2), counts) if match else ('', False)
        if not hosts or not is_key:
            counts['known_hosts lines that do not hold a host and a key, not reported'] += 1
            continue
        rows.append((hosts, 'yes' if hosts.startswith('|') else '', marker, match.group(1), fingerprint,
                     match.group(3) or '', number))
    return rows


def _process(context, reader, name):
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = reader(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc(f'{name}: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_list, '\n'.join(read)


@artifact_processor
def sshAuthorizedKeys(context):
    data_headers = ('Fingerprint (SHA256)', 'Key Type', 'Comment', 'Options', 'Line', 'Source File')
    data_list, source = _process(context, authorized_key_rows, 'SSH Authorized Keys')
    return data_headers, data_list, source


@artifact_processor
def sshKnownHosts(context):
    data_headers = ('Hosts', 'Hashed', 'Marker', 'Key Type', 'Fingerprint (SHA256)', 'Comment', 'Line', 'Source File')
    data_list, source = _process(context, known_host_rows, 'SSH Known Hosts')
    return data_headers, data_list, source


def _openssh_private_key(data):
    """(type, SHA256 fingerprint, 'yes'/'no' encrypted) of an OpenSSH private key, from the
    public key stored unencrypted in it, or None when it cannot be parsed."""
    try:
        body = ''.join(line for line in data.decode('ascii', errors='replace').splitlines()
                       if '-----' not in line)
        raw = base64.b64decode(body, validate=False)
    except (binascii.Error, ValueError):
        return None
    if raw[:15] != b'openssh-key-v1\x00':
        return None

    def read(offset):
        if offset + 4 > len(raw):
            raise ValueError('truncated')
        (length,) = struct.unpack('>I', raw[offset:offset + 4])
        start = offset + 4
        if start + length > len(raw):
            raise ValueError('truncated')
        return raw[start:start + length], start + length

    try:
        cipher, offset = read(15)
        _kdf, offset = read(offset)
        _kdfopts, offset = read(offset)
        offset += 4  # number of keys
        public, _ = read(offset)
    except (ValueError, struct.error):
        return None
    key_type = _blob_type(public)
    if not key_type:
        return None
    fingerprint = 'SHA256:' + base64.b64encode(hashlib.sha256(public).digest()).decode('ascii').rstrip('=')
    encrypted = 'no' if cipher.decode('ascii', errors='replace') == 'none' else 'yes'
    return key_type, fingerprint, encrypted


def key_file_rows(data, counts):
    """(kind, type, fingerprint, encrypted, comment) for a private or public SSH key file."""
    head = data[:40].decode('ascii', errors='replace')
    if head.startswith('-----BEGIN ') and 'PRIVATE KEY-----' in data[:80].decode('ascii', 'replace'):
        header = data.decode('ascii', 'replace').splitlines()[0]
        if 'OPENSSH PRIVATE KEY' in header:
            parsed = _openssh_private_key(data)
            if parsed is None:
                counts['OpenSSH private key files that could not be parsed, not reported'] += 1
                return []
            key_type, fingerprint, encrypted = parsed
            return [('Private', key_type, fingerprint, encrypted, '')]
        label = header.replace('-----BEGIN ', '').replace(' PRIVATE KEY-----', '').strip()
        key_type = label if label in ('RSA', 'EC', 'DSA') else ''
        text = data.decode('ascii', errors='replace')
        encrypted = 'yes' if (label == 'ENCRYPTED' or 'DEK-Info:' in text) else ''
        return [('Private', key_type, '', encrypted, '')]
    rows = []
    for line in _lines(data):
        text = line.strip()
        if not text or text.startswith('#'):
            continue
        match = _KEY.fullmatch(text)
        fingerprint, is_key = read_key(match.group(1), match.group(2), counts) if match else ('', False)
        if not is_key:
            counts['public key lines that do not hold a key, not reported'] += 1
            continue
        rows.append(('Public', match.group(1), fingerprint, '', match.group(3) or ''))
    return rows


@artifact_processor
def sshKeyFiles(context):
    data_headers = ('Key Kind', 'Key Type', 'Fingerprint (SHA256)', 'Encrypted', 'Comment',
                    'Source File')
    data_list, source = _process(context, key_file_rows, 'SSH Key Files')
    return data_headers, data_list, source
