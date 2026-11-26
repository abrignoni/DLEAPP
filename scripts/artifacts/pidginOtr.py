"""Pidgin Off-the-Record fingerprints and account keys, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The pidgin-otr plugin writes three files in the .purple folder: otr.fingerprints, otr.private_key and otr.instance_tags.
It also reads an optional otr.max_message_size, which this module does not parse. Their layouts come from libotr 4.1.1 (src/privkey.c and src/instag.c). Private key values are never reported.
"""

import hashlib
import os
import re
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import user_from_path


__artifacts_v2__ = {
    "pidginOtrFingerprints": {
        "name": "Pidgin OTR Fingerprints",
        "description": "Off-the-Record key fingerprints stored for the contacts of a Pidgin account, from "
                       "otr.fingerprints, with the trust value stored for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "Messaging",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per line of otr.fingerprints that has at least four tab-separated fields and 40 "
                 "hexadecimal digits in the fourth. Other lines are skipped and logged. Source citations are to libotr 4.1.1 "
                 "(https://otr.cypherpunks.ca/libotr-4.1.1.tar.gz) and pidgin-otr 4.0.2. Which libotr build the "
                 "Windows plugin contains was not established. The line layout (contact, account, protocol, 40 "
                 "hexadecimal digits, trust, separated by tabs) is what libotr writes in src/privkey.c lines 803 to "
                 "808. Fingerprint is shown in libotr's groups of eight upper-case digits. Trust (as stored) is the "
                 "fifth field. libotr treats a fingerprint as trusted when this field is not empty (src/context.c "
                 "lines 346 to 348). pidgin-otr 4.0.2 writes verified or an empty value when the user sets it by hand "
                 "(gtk-dialog.c line 1327), and libotr writes smp or an empty value after the Socialist Millionaires' "
                 "Protocol (src/message.c line 725). On the known data (windows11_arm_pidgin_otr_known_20261122) two Pidgin profiles ran the OTR key "
                 "exchange over a loopback XMPP server, and each profile's row equals the fingerprint computed from "
                 "the other profile's key. Trust (as stored) was empty on both rows because neither user verified "
                 "the other and no SMP ran, so a non-empty value is unexercised. libotr adds a fingerprint when a key "
                 "exchange with that contact address completes (src/message.c lines 537 to 551). A row shows that "
                 "this fingerprint is stored for the contact address under the account. It does not show who held "
                 "the key. The file holds no time, and no message content. User is the folder name after Users or "
                 "home in the file's path, and is empty when the path has neither.",
        "paths": ('*/.purple/otr.fingerprints',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "windows11_arm_pidgin_otr_known_20261122": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 and pidgin-otr 4.0.2 | 2 rows",
        },
    },
    "pidginOtrAccounts": {
        "name": "Pidgin OTR Accounts",
        "description": "Pidgin accounts listed in otr.private_key or otr.instance_tags: the account, protocol, "
                       "public key fingerprint and instance tag. Private key values are not reported.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "Messaging",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per account in otr.private_key or otr.instance_tags in a .purple folder. Source citations "
                 "are to libotr 4.1.1 (https://otr.cypherpunks.ca/libotr-4.1.1.tar.gz). Which libotr build the Windows "
                 "plugin contains was not established. Account and Protocol are the name and protocol tokens libotr "
                 "reads from each account entry of otr.private_key (src/privkey.c lines 264 to 266). For an account "
                 "found only in otr.instance_tags they are the first two fields of its line (src/instag.c line 271). "
                 "Key Fingerprint is computed here the way libotr computes it: SHA-1 over the public values p, q, g "
                 "and y, each as a 4-byte length and its unsigned bytes (src/privkey.c lines 88 and 165 to 168). The "
                 "private value x is not read into any column. On the known data (windows11_arm_pidgin_otr_known_20261122) each account's Key Fingerprint "
                 "equalled the fingerprint the other profile stored for it. Instance Tag is the third field of "
                 "otr.instance_tags (src/instag.c line 271), as stored. The files hold no time. User is the folder "
                 "name after Users or home in the file's path, and is empty when the path has neither.",
        "paths": ('*/.purple/otr.private_key', '*/.purple/otr.instance_tags'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "windows11_arm_pidgin_otr_known_20261122": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 and pidgin-otr 4.0.2 | 2 rows",
        },
    },
}


_FINGERPRINT = re.compile(r'[0-9a-fA-F]{40}')
_INSTANCE_TAG = re.compile(r'[0-9a-fA-F]{8}')


def _profile_user(relative):
    user = user_from_path(relative)
    if user:
        return user
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() == 'home':
            return parts[index + 1]
    return ''


def _human(hex_digits):
    upper = hex_digits.upper()
    return ' '.join(upper[i:i + 8] for i in range(0, len(upper), 8))


def _display(value):
    """Text for the report. Identifiers keep their original bytes as surrogate escapes until here, so joins are exact."""
    return value.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')


def _read_lines(path):
    with open(path, 'rb') as handle:
        records = handle.read().split(b'\n')
    return [record.rstrip(b'\r').decode('utf-8', 'surrogateescape') for record in records]


def _tokens(text):
    index, size = 0, len(text)
    while index < size:
        char = text[index]
        if char.isspace():
            index += 1
        elif char in '()':
            yield char
            index += 1
        elif char == '"':
            end = index + 1
            value = []
            while end < size and text[end] != '"':
                if text[end] == '\\' and end + 1 < size:
                    end += 1
                value.append(text[end])
                end += 1
            if end >= size:
                raise ValueError('unterminated string')
            yield ('text', ''.join(value))
            index = end + 1
        elif char == '#':
            end = text.find('#', index + 1)
            if end < 0:
                raise ValueError('unterminated hex value')
            yield ('hex', ''.join(text[index + 1:end].split()))
            index = end + 1
        else:
            end = index
            while end < size and not text[end].isspace() and text[end] not in '()"#':
                end += 1
            yield ('text', text[index:end])
            index = end


def _parse(text):
    stack, current = [], []
    for token in _tokens(text):
        if token == '(':
            stack.append(current)
            current = []
        elif token == ')':
            if not stack:
                raise ValueError('unbalanced list')
            done = current
            current = stack.pop()
            current.append(done)
        else:
            current.append(token)
    if stack:
        raise ValueError('unbalanced list')
    return current


def _head(node):
    return node[0][1] if isinstance(node, list) and node and isinstance(node[0], tuple) else ''


def _child(node, name):
    for item in node:
        if isinstance(item, list) and _head(item) == name:
            return item
    return None


def _value(node):
    if not node or len(node) < 2 or not isinstance(node[1], tuple):
        return ''
    kind, value = node[1]
    if kind == 'hex':
        try:
            return bytes.fromhex(value).decode('utf-8', 'surrogateescape')
        except ValueError:
            return ''
    return value


def _public_fingerprint(account):
    """SHA-1 over p, q, g and y as libotr serialises them. The private value x is never touched."""
    key = _child(account, 'private-key')
    dsa = _child(key, 'dsa') if key else None
    if not dsa:
        return ''
    blob = b''
    for name in ('p', 'q', 'g', 'y'):
        item = _child(dsa, name)
        if not item or len(item) < 2 or item[1][0] != 'hex':
            return ''
        raw = bytes.fromhex(item[1][1]).lstrip(b'\0')
        if not raw:
            raise ValueError('empty public key value')
        blob += struct.pack('>I', len(raw)) + raw
    return hashlib.sha1(blob).hexdigest()  # nosec B324


def _found(context, name):
    return sorted(str(f) for f in context.get_files_found() if os.path.basename(str(f)).lower() == name and os.path.isfile(str(f)))


@artifact_processor
def pidginOtrFingerprints(context):
    data_headers = ('Contact', 'Account', 'Protocol', 'Fingerprint', 'Trust (as stored)', 'User')
    data_list, sources = [], []
    for path in _found(context, 'otr.fingerprints'):
        relative = context.get_relative_path(path)
        sources.append(path)
        try:
            lines = _read_lines(path)
        except OSError as exc:
            logfunc(f'Pidgin OTR Fingerprints: {relative} not read ({type(exc).__name__})')
            continue
        for line in lines:
            parts = line.split('\t')
            if len(parts) < 4 or not _FINGERPRINT.fullmatch(parts[3]):
                if line.strip():
                    logfunc(f'Pidgin OTR Fingerprints: skipped a malformed line in {relative}')
                continue
            data_list.append((_display(parts[0]), _display(parts[1]), _display(parts[2]), _human(parts[3]),
                              _display(parts[4]) if len(parts) > 4 else '',
                              _profile_user(context.get_relative_path(path))))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def pidginOtrAccounts(context):
    data_headers = ('Account', 'Protocol', 'Key Fingerprint', 'Instance Tag', 'User')
    folders = {}
    for path in _found(context, 'otr.private_key'):
        relative = context.get_relative_path(path)
        entry = folders.setdefault(os.path.dirname(path), {'rows': {}, 'sources': [], 'user': _profile_user(context.get_relative_path(path))})
        entry['sources'].append(path)
        try:
            with open(path, 'r', encoding='utf-8', errors='surrogateescape', newline='') as handle:
                tree = _parse(handle.read())
        except (OSError, ValueError, IndexError) as exc:
            logfunc(f'Pidgin OTR Accounts: {relative} not read ({type(exc).__name__})')
            continue
        root = next((item for item in tree if _head(item) == 'privkeys'), [])
        for account in root:
            if _head(account) != 'account':
                continue
            try:
                fingerprint = _public_fingerprint(account)
            except (ValueError, TypeError, IndexError) as exc:
                logfunc(f'Pidgin OTR Accounts: a public key value did not decode in {relative} ({type(exc).__name__})')
                fingerprint = ''
            key = (_value(_child(account, 'name')), _value(_child(account, 'protocol')))
            if not all(key):
                logfunc(f'Pidgin OTR Accounts: skipped an account entry without a name or protocol in {relative}')
                continue
            row = entry['rows'].setdefault(key, ['', ''])
            if fingerprint:
                row[0] = _human(fingerprint)
    for path in _found(context, 'otr.instance_tags'):
        relative = context.get_relative_path(path)
        entry = folders.setdefault(os.path.dirname(path), {'rows': {}, 'sources': [], 'user': _profile_user(context.get_relative_path(path))})
        entry['sources'].append(path)
        try:
            lines = _read_lines(path)
        except OSError as exc:
            logfunc(f'Pidgin OTR Accounts: {relative} not read ({type(exc).__name__})')
            continue
        for line in lines:
            parts = line.split('\t')
            if line.startswith('#') or not line.strip():
                continue
            tag = parts[2].strip() if len(parts) > 2 else ''
            if len(parts) < 3 or not parts[0] or not parts[1] or not _INSTANCE_TAG.fullmatch(tag):
                logfunc(f'Pidgin OTR Accounts: skipped a malformed instance tag line in {relative}')
                continue
            entry['rows'].setdefault((parts[0], parts[1]), ['', ''])[1] = tag
    data_list, sources = [], []
    for _folder, entry in sorted(folders.items()):
        for (account, protocol), (fingerprint, tag) in sorted(entry['rows'].items()):
            data_list.append((_display(account), _display(protocol), fingerprint, tag, entry['user']))
        sources.extend(entry['sources'])
    return data_headers, data_list, '\n'.join(sources)
