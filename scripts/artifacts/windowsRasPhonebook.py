"""Windows remote access phonebook (rasphone.pbk) entries: VPN, dial-up and broadband connections, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsRasPhonebook": {
        "name": "Remote Access Phonebook (rasphone.pbk)",
        "description": "Connection entries in rasphone.pbk files under Microsoft\\Network\\Connections\\Pbk in a user "
                 "profile or in ProgramData: one row per entry, with its name, type, the configured address or "
                 "number, the device, the VPN strategy value and the time stored in LowDateTime and HighDateTime.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Windows Network",
        "platforms": ("Windows",),
        "notes": "Reads rasphone.pbk in a Microsoft\\Network\\Connections\\Pbk folder. On the lab VM the user entry "
                 "was written under the user's AppData\\Roaming and the all-users entry under ProgramData. Other "
                 ".pbk files (router.pbk of a routing server, or a phonebook an application keeps elsewhere) are "
                 "not read. The file is text: each entry starts with its name in brackets, followed by key=value "
                 "lines, and the MEDIA=, DEVICE= and PhoneNumber= lines start subsections in that order. The "
                 "layout and the keys are from the Microsoft open specification MS-RRASM, section 2.2.2 (File "
                 "Format for Phonebook) and 2.2.2.2 (Phonebook entry settings), "
                 "https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rrasm/4c69805f-b6ff-4e4a-9507-e3862f515d2c "
                 "(page metadata git_commit_id 69a493376fd5f940d8a1d406b5c00c4f70c01f68), read on 15 November "
                 "2026. That specification is written for the phonebook of a routing server's demand-dial "
                 "connections; its footnote 201 names rasphone.pbk as the client's phonebook. The rasphone.pbk "
                 "files read here used the same layout and the keys this artifact reads; they also held 49 keys "
                 "the specification does not list. Type is the Type key with the specification's label (1 Dial-up "
                 "connection, 2 VPN connection, 5 Broadband connection); another value is shown as stored. Phone "
                 "Number or Server lists every PhoneNumber line after the entry's first MEDIA line, one per line; "
                 "the specification says it holds a DNS name, IPv4 or IPv6 address for a VPN device, a telephone "
                 "number for a modem or ISDN device and a service name for a PPPoE device. Device Type is the "
                 "first DEVICE line, Device the first Device line and Port the first Port line of the first MEDIA "
                 "subsection (PreferredDevice held the same name as Device on both test entries and is not "
                 "reported). VPN Strategy is the VpnStrategy key as stored. The specification names the values a "
                 "routing server uses, and its footnote 206 says the client uses a different set, so the artifact "
                 "does not name them; on the two test entries the values 1 and 7 went with the PPTP and IKEv2 "
                 "devices named in the same entries. Entry Time (UTC) is LowDateTime and HighDateTime read as the "
                 "low and high halves of a FILETIME. The specification says only that RRAS ignores both keys, so "
                 "their meaning is not established; on the test entries the time fell within the same second as "
                 "the last-written time of each file read on the VM with Get-ChildItem (03:53:44 UTC). Custom Dial "
                 "DLLs lists the CustomDialDll and CustomRasDialDll values that are not empty, as stored; the "
                 "specification says RRAS ignores CustomDialDll. Both were empty on the test entries. Entry GUID "
                 "is the Guid key as stored. Scope is User when the path has a Users folder and All users when it "
                 "is under ProgramData, blank otherwise; User is the folder name after Users. A row shows a "
                 "configured entry, not that it was used to connect. This artifact does not report PreSharedKey, "
                 "ApnInfoUsername, ApnInfoPassword or CustomAuthData; PreSharedKey, ApnInfoUsername and "
                 "ApnInfoPassword were empty in both test files. Other keys (dial and redial settings, IP "
                 "settings, authentication data) are not reported. Evidence tier: data-proven on the two "
                 "rasphone.pbk files of a Windows 11 ARM64 lab VM, written by Add-VpnConnection for this artifact "
                 "(one IKEv2 entry for the user, one PPTP entry for all users) and removed afterwards: 2 rows. The "
                 "Dial-up and Broadband labels, a second MEDIA subsection and UTF-16 files ran only in unit tests. "
                 "None of the 12 Windows known-data zips in the corpus includes a Pbk folder, so no corpus file "
                 "was available, and no dial-up or broadband entry was read.",
        "paths": ('*/Microsoft/Network/Connections/[Pp]bk/rasphone.pbk',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "phone",
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import filetime_utc, user_from_path

_TYPES = {'1': 'Dial-up connection', '2': 'VPN connection', '5': 'Broadband connection'}


def _decode(raw):
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16', 'replace')
    return raw.decode('utf-8-sig', 'replace')


def parse_phonebook(text):
    """[(name, {key: first value}, media, phone_numbers)] for each entry.

    media holds Port, Device and DEVICE of the first MEDIA subsection; phone_numbers every PhoneNumber value.
    """
    entries = []
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        if line.startswith('[') and line.endswith(']'):
            current = (line[1:-1], {}, {}, [], {'media': 0})
            entries.append(current)
            continue
        if current is None or '=' not in line:
            continue
        key, value = line.split('=', 1)
        _name, keys, media, numbers, state = current
        if key == 'MEDIA':
            state['media'] += 1
            if state['media'] == 1:
                media['MEDIA'] = value
            continue
        if state['media']:
            if key == 'PhoneNumber':
                numbers.append(value)
            elif state['media'] == 1 and key in ('Port', 'Device', 'DEVICE') and key not in media:
                media[key] = value
            continue
        keys.setdefault(key, value)
    return [(name, keys, media, numbers) for name, keys, media, numbers, _state in entries]


def _labelled(value, labels):
    if value is None:
        return ''
    return f'{value} ({labels[value]})' if value in labels else value


def _entry_time(keys):
    try:
        low, high = int(keys['LowDateTime']), int(keys['HighDateTime'])
    except (KeyError, ValueError):
        return ''
    return filetime_utc(((high & 0xFFFFFFFF) << 32) | (low & 0xFFFFFFFF))


@artifact_processor
def windowsRasPhonebook(context):
    data_headers = (('Entry Time (UTC)', 'datetime'), 'Entry Name', 'Type', 'Phone Number or Server', 'Device Type',
                    'Device', 'Port', 'VPN Strategy', 'Custom Dial DLLs', 'Entry GUID', 'Scope',
                    'User', 'Source File')
    data_list, sources = [], []
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.basename(path).lower() != 'rasphone.pbk' or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                text = _decode(handle.read())
        except OSError as error:
            logfunc(f'Remote Access Phonebook: could not read {relative}: {error}')
            continue
        sources.append(path)
        user = user_from_path(relative)
        in_programdata = 'programdata' in relative.replace('\\', '/').lower().split('/')
        scope = 'User' if user else ('All users' if in_programdata else '')
        for name, keys, media, numbers in parse_phonebook(text):
            dlls = '\n'.join(keys[k] for k in ('CustomDialDll', 'CustomRasDialDll') if keys.get(k))
            data_list.append((_entry_time(keys), name, _labelled(keys.get('Type'), _TYPES), '\n'.join(numbers),
                              media.get('DEVICE', ''), media.get('Device', ''), media.get('Port', ''),
                              keys.get('VpnStrategy', ''),
                              dlls, keys.get('Guid', ''), scope, user, relative))
    return data_headers, data_list, '\n'.join(sources)
