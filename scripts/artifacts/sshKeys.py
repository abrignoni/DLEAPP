"""Public keys in OpenSSH authorized_keys files and host keys in known_hosts files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sshAuthorizedKeys": {
        "name": "SSH Authorized Keys",
        "description": "Public keys in OpenSSH authorized_keys files, which sshd reads by default for public key "
                       "authentication to the account, with each key's SHA256 fingerprint, type, comment and options.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
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
                 "on that image.",
        "paths": ('*/.ssh/authorized_keys', '*/.ssh/authorized_keys2'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1 row",
        },
    },
    "sshKnownHosts": {
        "name": "SSH Known Hosts",
        "description": "Host keys recorded in OpenSSH known_hosts files, with the host names as stored, whether "
                       "they are hashed, and each key's type and SHA256 fingerprint.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "SSH",
        "notes": "Reads each known_hosts and known_hosts2 file in a .ssh folder and each "
                 "ssh_known_hosts and ssh_known_hosts2 file in an etc/ssh folder, one row "
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
                 "plain-text entry of pc_mus_001_win11.",
        "paths": ('*/.ssh/known_hosts', '*/.ssh/known_hosts2', '*/etc/ssh/ssh_known_hosts',
                  '*/etc/ssh/ssh_known_hosts2'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "server",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1 row",
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
