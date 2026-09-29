"""Ring Chime Pro state from its flash volumes, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "ringChimeProProperties": {
        "name": "Ring Chime Pro Properties",
        "description": "Property files from a Ring Chime Pro's properties folders and state volume: each "
                       "property's name, value and the modified time the filesystem records for its file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Ring (Chime Pro)",
        "notes": "One row per file in a var/ring/properties folder, in home/root/sys/properties, or in the "
                 "properties or reboot_tmp_prop folder of the volume named ubifs_system, plus that volume's "
                 "last_boot_reason and network.wan_ifname files. When more than one copy of these folders is "
                 "present, each copy gives its own rows; Folder names the folder a row came from. network.config and network.config_backup are reported by "
                 "Ring Chime Pro Wi-Fi Network instead. Property is the file name. A file whose text starts "
                 "with two whole numbers and a space is split there: Header (as stored) keeps the two numbers "
                 "and Value the rest; any other file's whole text is the Value, without one trailing line "
                 "break. What the two numbers mean is not established. Value as Time (UTC) reads the Value as "
                 "seconds since 1970 when the property name ends in _ts and the Value is a whole number; field "
                 "mapped from a private sample. A file that is not UTF-8 text is shown as hexadecimal. "
                 "Modified (UTC) is the modified time the filesystem records for the file. With a raw image "
                 "as input, a file the image lists but the reader could not read is not staged and gives no "
                 "row, and the run log names it. Values are reported as stored, including any secret or key. "
                 "Not read: "
                 "var/ring/ConfigProtobuf, a protobuf for which no schema was found, so no field could be "
                 "named without guessing; provision_info.bin; the audio files; and the .btc files. "
                 "Validated only against a private sample; sample_data is left empty for "
                 "that reason.",
        "paths": ("*/var/ring/properties/*", "*/home/root/sys/properties/*", "*/ubifs_system/properties/*",
                  "*/ubifs_system/reboot_tmp_prop/*", "*/ubifs_system/last_boot_reason",
                  "*/ubifs_system/network.wan_ifname"),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {},
    },
    "ringChimeProWifi": {
        "name": "Ring Chime Pro Wi-Fi Network",
        "description": "The Wi-Fi network settings a Ring Chime Pro stores in its network.config and "
                       "network.config_backup property files: SSID, security type, passphrase and IP settings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Ring (Chime Pro)",
        "notes": "One row per network.config or network.config_backup file in the properties folders Ring "
                 "Chime Pro Properties reads. After the two whole numbers the file is read as a JSON object; "
                 "the settings are taken from its net field when it has one, with country and domain beside "
                 "it, and from the object itself otherwise. SSID, Security Type, Passphrase, IP Type, IP Address, Netmask, Gateway and DNS are "
                 "the S, T, P, IP_TYPE, IP_ADDR, IP_MASK, IP_GW and IP_DNS fields as stored, K (as stored) is "
                 "the K field, whose meaning is not established, and Country and Domain are the country and "
                 "domain fields; field mapped from a private sample. The passphrase is reported as stored. "
                 "Whether the device was connected to this network, and when, are not established; Modified "
                 "(UTC) is the modified time the filesystem records for the file. A file whose JSON cannot be "
                 "read gives a row with the text in Other Fields and is counted in the run log. Other Fields "
                 "lists, as JSON, any field not shown in a column. Validated only against a private sample; "
                 "sample_data is left empty for that reason.",
        "paths": ("*/var/ring/properties/network.config*", "*/home/root/sys/properties/network.config*",
                  "*/ubifs_system/properties/network.config*"),
        "output_types": "standard",
        "artifact_icon": "wifi",
        "sample_data": {},
    },
    "ringChimeProConf": {
        "name": "Ring Chime Pro ring.conf",
        "description": "Key and value lines from the ring.conf file on a Ring Chime Pro's state volume.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Ring (Chime Pro)",
        "notes": "One row per non-empty line of ring.conf in the volume named ubifs_system. Key is the text "
                 "before the first space and Value the rest, as stored; a line with no space is its own Key "
                 "with Value blank. Values are reported as stored, including any secret. What each key "
                 "means is not established; field mapped from a private sample. Modified (UTC) is the "
                 "modified time the filesystem records for the file, the same on every row from one file. "
                 "Validated only against a private sample; sample_data is left empty for that reason.",
        "paths": ("*/ubifs_system/ring.conf",),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {},
    },
    "ringChimeProDhcpLeases": {
        "name": "Ring Chime Pro DHCP Leases",
        "description": "Leases in the busybox udhcpd lease file on a Ring Chime Pro volume: each client's IP "
                       "address, MAC address and host name, with the time the file was written and the "
                       "lease expiry it implies.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Ring (Chime Pro)",
        "notes": "Reads var/lib/misc/udhcpd.leases only in a volume that also holds var/ring/properties, so a "
                 "lease file from another Linux device gives no rows; the run log counts any skipped. busybox "
                 "1.24.1 udhcpd writes the file as an 8-byte big-endian time in seconds since 1970, then one "
                 "36-byte record per lease: the seconds left until the lease expires at the time of writing, "
                 "or 0 when it had already expired, as a big-endian 32-bit number; the IP address; a 6-byte "
                 "MAC address; a 20-byte host name; and 2 bytes of padding (Reference: busybox, 'dhcpd.h', "
                 "https://github.com/mirror/busybox/blob/5c23f2566c1d26c62024cc2c78ca5aad4c99dd33/networking/udhcp/dhcpd.h#L72-L91; "
                 "'files.c', "
                 "https://github.com/mirror/busybox/blob/5c23f2566c1d26c62024cc2c78ca5aad4c99dd33/networking/udhcp/files.c#L120-L166). "
                 "Written (UTC) is that first time, Seconds Remaining When Written the stored count, and Lease "
                 "Expires (UTC) their sum, left blank when the count is 0. Hostname is the stored name up to "
                 "its first zero byte and is blank when the client sent none. A client in this file obtained "
                 "an address from the device's own DHCP server; who used that client is not established. The "
                 "times are the device's clock as stored, and a device whose clock was not yet set can store "
                 "a wrong time, so corroborate with another source. Bytes after the last whole record are "
                 "counted in the run log. The busybox version was mapped from a private sample. Validated only "
                 "against a private sample; sample_data is left empty for that reason.",
        "paths": ("*/var/lib/misc/udhcpd.leases", "*/var/ring/properties/*"),
        "output_types": "standard",
        "artifact_icon": "wifi",
        "sample_data": {},
    },
    "ringChimeProWebLog": {
        "name": "Ring Chime Pro Web Server Log",
        "description": "Lines of the lighttpd error log in a Ring Chime Pro's webSvr/logs folder, with the "
                       "local time each line stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Ring (Chime Pro)",
        "notes": "Reads webSvr/logs/error.log only in a volume that also holds var/ring/properties; the run log "
                 "counts any skipped. lighttpd 1.4.41, logging to a file, starts each line with the local "
                 "time as year-month-day hours:minutes:seconds, then ': (' and the source file and line "
                 "(Reference: lighttpd, 'log.c', "
                 "https://github.com/lighttpd/lighttpd1.4/blob/29fa805695fc59cbfffde38cc60faf4186cf04c7/src/log.c#L379-L394), "
                 "and writes 'server started' when it starts (same file, "
                 "https://github.com/lighttpd/lighttpd1.4/blob/29fa805695fc59cbfffde38cc60faf4186cf04c7/src/log.c#L216). "
                 "The time carries no zone, so Time (as stored, local) is text and is not converted; rows are "
                 "in file order. Source (as stored) is the source file and "
                 "line in parentheses and Message the rest of the line; a line without that shape is reported "
                 "whole in Message. The lighttpd version was mapped from a private sample. access.log and "
                 "cgi.log are not read. Validated only against a private sample; sample_data is left empty "
                 "for that reason.",
        "paths": ("*/webSvr/logs/error.log", "*/var/ring/properties/*"),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {},
    },
}

import ipaddress
import json
import os
import re
import struct
from collections import Counter
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_time, seeker_of

PROPERTY_FOLDERS = ('/var/ring/properties/', '/home/root/sys/properties/', '/ubifs_system/properties/',
                    '/ubifs_system/reboot_tmp_prop/')
STATE_FILES = ('/ubifs_system/last_boot_reason', '/ubifs_system/network.wan_ifname')
WIFI_FILES = ('network.config', 'network.config_backup')
RING_MARKER = '/var/ring/properties/'
HEADER = re.compile(r'(-?\d+) (-?\d+) (.*)', re.S)
WIFI_COLUMNS = (('S', 'SSID'), ('T', 'Security Type'), ('P', 'Passphrase'), ('IP_TYPE', 'IP Type'),
                ('IP_ADDR', 'IP Address'), ('IP_MASK', 'Netmask'), ('IP_GW', 'Gateway'), ('IP_DNS', 'DNS'),
                ('K', 'K (as stored)'))
LEASE = struct.Struct('>I4s6s20s2x')
LOG_LINE = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): (\([^)]*\)) ?(.*)')


def _files(context):
    """(staged path, evidence-relative path) for the files found, directories left out, in relative order."""
    out = []
    for path in (str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        out.append((path, context.get_relative_path(path)))
    return sorted(out, key=lambda pr: pr[1])


def _slash(relative):
    return '/' + relative.replace('\\', '/').lstrip('/')


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _text(data):
    """UTF-8 text, or None when the bytes are not UTF-8."""
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def _split_property(text):
    """(header, value) for a property file's text: two whole numbers and a space, then the value."""
    match = HEADER.fullmatch(text)
    if match:
        return f'{match.group(1)} {match.group(2)}', match.group(3)
    return '', text[:-1] if text.endswith('\n') else text


def _ring_roots(files):
    """The part of each relative path before var/ring/properties, for the volumes that hold it."""
    roots = set()
    for _path, relative in files:
        full = _slash(relative)
        at = full.find(RING_MARKER)
        if at >= 0:
            roots.add(full[:at])
    return roots


def _in_ring_volume(relative, marker, roots):
    full = _slash(relative)
    at = full.find(marker)
    return at >= 0 and full[:at] in roots


def _is_property_file(relative):
    full = _slash(relative)
    if full.endswith(STATE_FILES):
        return True
    return any(folder in full and '/' not in full.split(folder, 1)[1] for folder in PROPERTY_FOLDERS)


def _seconds(value):
    try:
        return datetime.fromtimestamp(int(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


@artifact_processor
def ringChimeProProperties(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Property', 'Value', ('Value as Time (UTC)', 'datetime'),
                    'Header (as stored)', 'Folder')
    seeker = seeker_of(context)
    rows = []
    read = []
    counts = Counter()
    for path, relative in _files(context):
        if not _is_property_file(relative):
            continue
        name = os.path.basename(relative)
        if name in WIFI_FILES:
            continue
        try:
            data = _read(path)
        except OSError:
            counts['files that could not be read'] += 1
            continue
        text = _text(data)
        if text is None:
            header, value = '', data.hex()
            counts['files that are not UTF-8 text, shown as hexadecimal'] += 1
        else:
            header, value = _split_property(text)
        as_time = _seconds(value) if name.endswith('_ts') and value.isdigit() else ''
        rows.append((recorded_time(seeker, path, None), name, value, as_time, header,
                     os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Ring Chime Pro Properties: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)


@artifact_processor
def ringChimeProWifi(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'SSID', 'Security Type', 'Passphrase', 'IP Type',
                    'IP Address', 'Netmask', 'Gateway', 'DNS', 'K (as stored)', 'Country', 'Domain',
                    'Other Fields', 'Property', 'Folder')
    seeker = seeker_of(context)
    rows = []
    read = []
    counts = Counter()
    for path, relative in _files(context):
        name = os.path.basename(relative)
        if name not in WIFI_FILES or not _is_property_file(relative):
            continue
        try:
            text = _text(_read(path))
        except OSError:
            counts['files that could not be read'] += 1
            continue
        _header, value = _split_property(text) if text is not None else ('', '')
        try:
            obj = json.loads(value)
        except ValueError:
            obj = None
        if not isinstance(obj, dict):
            counts['files whose JSON could not be read'] += 1
            rows.append((recorded_time(seeker, path, None),) + ('',) * 11 +
                        (value if text is not None else '', name, os.path.dirname(relative)))
            read.append(path)
            continue
        outer = dict(obj)
        net = outer.pop('net') if isinstance(outer.get('net'), dict) else outer
        if net is outer:
            outer = {}
        country = outer.pop('country', '')
        domain = outer.pop('domain', '')
        net = dict(net)
        shown = [_value(net.pop(key, '')) for key, _column in WIFI_COLUMNS]
        others = dict(outer, **net)
        rows.append((recorded_time(seeker, path, None),) + tuple(shown) +
                    (_value(country), _value(domain),
                     json.dumps(others, sort_keys=True, ensure_ascii=False) if others else '',
                     name, os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Ring Chime Pro Wi-Fi Network: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)


def _value(item):
    if item is None:
        return ''
    if isinstance(item, str):
        return item
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


@artifact_processor
def ringChimeProConf(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Key', 'Value', 'Line Number', 'Folder')
    seeker = seeker_of(context)
    rows = []
    read = []
    for path, relative in _files(context):
        if not _slash(relative).endswith('/ubifs_system/ring.conf'):
            continue
        try:
            data = _read(path)
        except OSError:
            logfunc(f'Ring Chime Pro ring.conf: {relative} could not be read')
            continue
        modified = recorded_time(seeker, path, None)
        text = data.decode('utf-8', 'backslashreplace')
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            key, _sep, value = line.partition(' ')
            rows.append((modified, key, value, number, os.path.dirname(relative)))
        read.append(path)
    return data_headers, rows, '\n'.join(read)


@artifact_processor
def ringChimeProDhcpLeases(context):
    data_headers = (('Written (UTC)', 'datetime'), ('Lease Expires (UTC)', 'datetime'),
                    'Seconds Remaining When Written', 'IP Address', 'MAC Address', 'Hostname', 'Folder')
    files = _files(context)
    roots = _ring_roots(files)
    rows = []
    read = []
    counts = Counter()
    for path, relative in files:
        if not _slash(relative).endswith('/var/lib/misc/udhcpd.leases'):
            continue
        if not _in_ring_volume(relative, '/var/lib/misc/udhcpd.leases', roots):
            counts['lease files in a volume without var/ring/properties, not read'] += 1
            continue
        try:
            data = _read(path)
        except OSError:
            counts['lease files that could not be read'] += 1
            continue
        read.append(path)
        if len(data) < 8:
            counts['lease files shorter than their 8-byte header'] += 1
            continue
        written_at = struct.unpack('>q', data[:8])[0]
        written = _seconds(written_at)
        body = data[8:]
        whole = len(body) // LEASE.size
        if len(body) % LEASE.size:
            counts['bytes after the last whole lease record'] += len(body) % LEASE.size
        for index in range(whole):
            remaining, nip, mac, hostname = LEASE.unpack_from(body, index * LEASE.size)
            expires = _seconds(written_at + remaining) if remaining else ''
            rows.append((written, expires, remaining, str(ipaddress.IPv4Address(nip)),
                         ':'.join(f'{b:02x}' for b in mac),
                         hostname.split(b'\0', 1)[0].decode('utf-8', 'backslashreplace'),
                         os.path.dirname(relative)))
    if counts:
        logfunc('Ring Chime Pro DHCP Leases: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)


@artifact_processor
def ringChimeProWebLog(context):
    data_headers = ('Time (as stored, local)', 'Source (as stored)', 'Message', 'Line Number', 'Folder')
    files = _files(context)
    roots = _ring_roots(files)
    rows = []
    read = []
    counts = Counter()
    for path, relative in files:
        if not _slash(relative).endswith('/webSvr/logs/error.log'):
            continue
        if not _in_ring_volume(relative, '/webSvr/logs/error.log', roots):
            counts['error.log files in a volume without var/ring/properties, not read'] += 1
            continue
        try:
            data = _read(path)
        except OSError:
            counts['error.log files that could not be read'] += 1
            continue
        for number, line in enumerate(data.decode('utf-8', 'backslashreplace').splitlines(), 1):
            if not line.strip():
                continue
            match = LOG_LINE.fullmatch(line.rstrip())
            if match:
                rows.append((match.group(1), match.group(2), match.group(3), number, os.path.dirname(relative)))
            else:
                rows.append(('', '', line, number, os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Ring Chime Pro Web Server Log: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)
