"""Logs and settings a Skybell video doorbell keeps on its own flash, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "skybellDoorbellLog": {
        "name": "Skybell Doorbell Device Log",
        "description": "Lines of a Skybell doorbell's own system and debug logs, each with the Unix time it "
                       "records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Skybell (Video Doorbell)",
        "notes": "Reads the numbered files 0 to 9 of the doorbell's logs/system and logs/debug folders, which "
                 "the doorbell keeps as two separate logs; the same message can appear in both, each time "
                 "with its own time. A logs folder is read only when one of its files, reboot.txt and restart.txt "
                 "included, holds the word skybell, in any case; a raw NAND image of the doorbell holds it "
                 "on a UBI volume, which qnxprobe reads. Each line reported starts with the time as the "
                 "doorbell writes it, YYYY/MM/DD-hh:mm:ss, then a Unix time in seconds and microseconds in "
                 "brackets. Time (UTC) is that Unix time and Time as Recorded the time before it; the two "
                 "agreed as UTC, to within a second, on the lines of the private sample this was field "
                 "mapped from. A line written before the doorbell's clock is set carries whatever time the "
                 "clock held, and Skybell Doorbell Restarts lists the 'Time changed from' lines that record "
                 "a setting. Where the rest of the line is '<LEVEL>-<function>().<line>: <message>', Level, "
                 "Function and Message are split out, Function keeping its source line number; other timed "
                 "lines are reported with the whole rest in Message. Lines starting DBUG, the debug log's "
                 "developer trace, and lines with no time are counted in the run log and not reported; the "
                 "identity lines among the latter are reported in Skybell Doorbell Identity. Log is system "
                 "or debug and Rotation the file's number; the order in which the doorbell fills the "
                 "numbered files is not established, so sort by Time (UTC). Not reported: battery.txt, a "
                 "voltage reading per line; the counter files reboot-count.bin, restart-count.bin and "
                 "reboot_cycles, whose meaning is not established; tinyvenc.log; and the .enc files beside "
                 "the settings, which are OpenSSL encrypted ('Salted__') and not decrypted.",
        "sample_data": {},
        "paths": ('*/logs/system/*', '*/logs/debug/*', '*/logs/reboot.txt', '*/logs/restart.txt'),
        "output_types": "standard",
    },
    "skybellDoorbellRestarts": {
        "name": "Skybell Doorbell Restarts",
        "description": "Lines of a Skybell doorbell's reboot.txt and restart.txt logs, times as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Skybell (Video Doorbell)",
        "notes": "Reads logs/reboot.txt and logs/restart.txt, each line 'YYYY/MM/DD-hh:mm:ss <message>', and "
                 "reports every line, in file order, when the file holds the word skybell in any case. The "
                 "lines carry no Unix time, so Time as Recorded is the time as stored and is not converted; "
                 "in the doorbell's device logs, where each line also carries a Unix time, the same form of "
                 "reading agreed with UTC (see Skybell Doorbell Device Log). A time before the doorbell's "
                 "clock is set is the time the clock held then, and a 'Time changed from [<time>]' line "
                 "records the time the clock left when it was set. What each message means beyond its own "
                 "words is not established.",
        "sample_data": {},
        "paths": ('*/logs/reboot.txt', '*/logs/restart.txt'),
        "output_types": "standard",
    },
    "skybellDoorbellIdentity": {
        "name": "Skybell Doorbell Identity",
        "description": "The device ID, UUID, serial number, MAC and IP address and firmware a Skybell doorbell "
                       "wrote into its own logs, with when each combination was first and last written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Skybell (Video Doorbell)",
        "notes": "Reads the same files as Skybell Doorbell Device Log. The doorbell writes, with no time of "
                 "their own, a line \"Device-ID: '<id>', UUID: '<uuid>'\" and then a line \"Serial-No: "
                 "'<number>', MAC: '<address>' IP: '<address>'\"; each Serial-No line is paired with the latest "
                 "Device-ID line before it in the same file (two writers can interleave them), and each "
                 "pair is taken with the Unix "
                 "time of the timed line before it (none when no timed line comes before it in the "
                 "file) and with the firmware named by the latest timed line of the form 'v<version> "
                 "[<build time>] -- <rootfs>[<build>]' before it in the same file, all as stored. "
                 "One row is reported per distinct combination, with First Written (UTC) and Last Written "
                 "(UTC) the earliest and latest of those times, blank when none of its pairs has one, "
                 "Times Written the number of pairs, and Logs "
                 "the logs holding them. A time is the doorbell's clock and may predate its being set (see "
                 "Skybell Doorbell Device Log). An empty value is reported as stored, empty; the pairs were "
                 "field mapped from a private sample.",
        "sample_data": {},
        "paths": ('*/logs/system/*', '*/logs/debug/*', '*/logs/reboot.txt', '*/logs/restart.txt'),
        "output_types": "standard",
    },
    "skybellDoorbellSettings": {
        "name": "Skybell Doorbell Settings",
        "description": "Settings a Skybell doorbell keeps in settings.json, system_settings.json and "
                       "media_settings.json, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Skybell (Video Doorbell)",
        "notes": "Reads settings.json, system_settings.json and media_settings.json from a folder whose "
                 "system_settings.json names skybell, in any case, in its ota_uri or dns_server_name, and "
                 "reports one row per key of each, with the value as stored (JSON text for anything but a "
                 "string). The folder also keeps backup.json, system_backup.json and media_backup.json, and "
                 "copies of all six in a revert folder; a key whose value in one of those differs from its "
                 "value in the matching settings file, or which only that copy holds, is reported again "
                 "with that file named in File. Each JSON file sits beside a .crc file of the same name; CRC "
                 "is 'matches' when that file holds the CRC-32 of the JSON file's bytes, stored "
                 "little-endian, 'differs' when it does not, and 'no .crc file' when there is none. The CRC "
                 "form was field mapped from a private sample, where CRC read 'matches' on every row. What each "
                 "setting controls is not established beyond its name.",
        "sample_data": {},
        "paths": ('*/settings.json', '*/system_settings.json', '*/media_settings.json', '*/backup.json',
                  '*/system_backup.json', '*/media_backup.json', '*/settings.crc', '*/system_settings.crc',
                  '*/media_settings.crc', '*/backup.crc', '*/system_backup.crc', '*/media_backup.crc'),
        "output_types": "standard",
    },
}

import json
import os
import re
import struct
import zlib
from collections import Counter
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

TIMED_RE = re.compile(r'^(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})\[(\d+)\.(\d{1,6})\] ?(.*)$')
FIELDS_RE = re.compile(r'^([A-Z]+)-(\w+\(\)(?:\.\d+)?): ?(.*)$')
VERSION_RE = re.compile(r'^v\S+ \[[^\]]*\] -- \S+$')
DEVICE_RE = re.compile(r"^Device-ID: '([^']*)', UUID: '([^']*)'")
SERIAL_RE = re.compile(r"^Serial-No: '([^']*)', MAC: '([^']*)' IP: '([^']*)'")
RECORDED_RE = re.compile(r'^(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}) ?(.*)$')


def _read_text(path):
    with open(path, 'rb') as handle:
        return handle.read().decode('utf-8', 'replace')


def _mentions_skybell(path):
    try:
        return 'skybell' in _read_text(path).lower()
    except OSError:
        return False


def skybell_log_files(paths):
    """{logs folder: [(log, rotation, path)]} for the logs folders whose files name skybell."""
    folders = {}
    for path in paths:
        parent = os.path.dirname(path)
        name = os.path.basename(path)
        if name in ('reboot.txt', 'restart.txt'):
            folders.setdefault(parent, [])
        elif os.path.basename(parent) in ('system', 'debug') and re.fullmatch(r'\d', name):
            folders.setdefault(os.path.dirname(parent), []).append((os.path.basename(parent), int(name), path))
    kept = {}
    for folder, files in folders.items():
        candidates = [os.path.join(folder, n) for n in ('reboot.txt', 'restart.txt')] + [p for _l, _r, p in files]
        if any(os.path.isfile(p) and _mentions_skybell(p) for p in candidates):
            kept[folder] = sorted(files)
    return kept


def _utc(seconds, micros):
    return datetime.fromtimestamp(int(seconds), timezone.utc).replace(microsecond=int(micros.ljust(6, '0')))


def log_rows(text, counts):
    """(time, time as recorded, level, function, message, line) for each timed line that is not DBUG."""
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        match = TIMED_RE.match(line)
        if not match:
            if line.strip():
                counts['lines with no time, not reported'] += 1
            continue
        recorded, seconds, micros, rest = match.groups()
        if rest.startswith('DBUG'):
            counts['DBUG lines, not reported'] += 1
            continue
        fields = FIELDS_RE.match(rest)
        level, function, message = fields.groups() if fields else ('', '', rest)
        rows.append((_utc(seconds, micros), recorded, level, function, message, number))
    return rows


def identity_pairs(text):
    """(time, device id, uuid, serial, mac, ip, firmware) for each Device-ID and Serial-No pair."""
    out, last_time, firmware, device = [], None, '', None
    for line in text.splitlines():
        match = TIMED_RE.match(line)
        if match:
            last_time = _utc(match.group(2), match.group(3))
            if VERSION_RE.match(match.group(4)):
                firmware = match.group(4)
            continue
        found = DEVICE_RE.match(line)
        if found:
            device = found.groups()
            continue
        found = SERIAL_RE.match(line)
        if found and device is not None:
            out.append((last_time,) + device + found.groups() + (firmware,))
    return out


@artifact_processor
def skybellDoorbellLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Level', 'Function', 'Message', 'Log',
                    'Rotation', 'Line', 'Log File')
    data_list, read = [], []
    counts = Counter()
    files = sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p))
    for _folder, logs in sorted(skybell_log_files(files).items()):
        for log, rotation, path in logs:
            try:
                text = _read_text(path)
            except OSError:
                counts['files that could not be read'] += 1
                continue
            relative = context.get_relative_path(path)
            for when, recorded, level, function, message, number in log_rows(text, counts):
                data_list.append((when, recorded, level, function, message, log, rotation, number, relative))
            read.append(path)
    if counts:
        logfunc('Skybell Doorbell Device Log: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def skybellDoorbellRestarts(context):
    data_headers = ('Time as Recorded', 'Message', 'Line', 'Log File')
    data_list, read = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        if os.path.basename(path) not in ('reboot.txt', 'restart.txt'):
            continue
        try:
            text = _read_text(path)
        except OSError:
            counts['files that could not be read'] += 1
            continue
        if 'skybell' not in text.lower():
            counts['files without the word skybell, not read'] += 1
            continue
        relative = context.get_relative_path(path)
        for number, line in enumerate(text.splitlines(), 1):
            match = RECORDED_RE.match(line)
            if match:
                data_list.append((match.group(1), match.group(2), number, relative))
            elif line.strip():
                counts['lines with no time, not reported'] += 1
        read.append(path)
    if counts:
        logfunc('Skybell Doorbell Restarts: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def skybellDoorbellIdentity(context):
    data_headers = (('First Written (UTC)', 'datetime'), ('Last Written (UTC)', 'datetime'), 'Device ID', 'UUID',
                    'Serial Number', 'MAC Address', 'IP Address', 'Firmware', 'Times Written', 'Logs')
    seen = {}
    read = []
    files = sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p))
    for _folder, logs in sorted(skybell_log_files(files).items()):
        for log, _rotation, path in logs:
            try:
                pairs = identity_pairs(_read_text(path))
            except OSError:
                continue
            for when, *values in pairs:
                entry = seen.setdefault(tuple(values), [None, None, 0, set()])
                if when is not None:
                    entry[0] = when if entry[0] is None else min(entry[0], when)
                    entry[1] = when if entry[1] is None else max(entry[1], when)
                entry[2] += 1
                entry[3].add(log)
            if pairs:
                read.append(path)
    earliest = datetime.min.replace(tzinfo=timezone.utc)
    order = sorted(seen.items(), key=lambda kv: (kv[1][0] is None, kv[1][0] or earliest))
    data_list = [(first or '', last or '', *values, count, ', '.join(sorted(logs)))
                 for values, (first, last, count, logs) in order]
    return data_headers, data_list, '\n'.join(read)


SETTINGS_FILES = ('settings.json', 'system_settings.json', 'media_settings.json')
COPIES = {'settings.json': 'backup.json', 'system_settings.json': 'system_backup.json',
          'media_settings.json': 'media_backup.json'}


def crc_state(path):
    crc_path = path[:-len('.json')] + '.crc'
    if not os.path.isfile(crc_path):
        return 'no .crc file'
    with open(path, 'rb') as handle:
        data = handle.read()
    with open(crc_path, 'rb') as handle:
        stored = handle.read()
    return 'matches' if stored == struct.pack('<I', zlib.crc32(data)) else 'differs'


def _load(path):
    with open(path, 'rb') as handle:
        return json.loads(handle.read().decode('utf-8'))


def _shown(value):
    return value if isinstance(value, str) else json.dumps(value)


def is_skybell_settings_folder(folder):
    path = os.path.join(folder, 'system_settings.json')
    try:
        data = _load(path)
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and any(
        'skybell' in str(data.get(key, '')).lower() for key in ('ota_uri', 'dns_server_name'))


@artifact_processor
def skybellDoorbellSettings(context):
    data_headers = ('File', 'Setting', 'Value', 'CRC')
    data_list, read = [], []
    counts = Counter()
    files = {str(p) for p in context.get_files_found() if not os.path.isdir(p)}
    folders = sorted({os.path.dirname(p) for p in files if os.path.basename(p) == 'system_settings.json'
                      and os.path.basename(os.path.dirname(p)) != 'revert'})
    for folder in folders:
        if not is_skybell_settings_folder(folder):
            counts['folders whose system_settings.json names no skybell server, not read'] += 1
            continue
        for name in SETTINGS_FILES:
            path = os.path.join(folder, name)
            try:
                main = _load(path)
            except (OSError, ValueError):
                counts['settings files that could not be read'] += 1
                continue
            if not isinstance(main, dict):
                continue
            state = crc_state(path)
            for key, value in main.items():
                data_list.append((context.get_relative_path(path), key, _shown(value), state))
            read.append(path)
            for copy in (os.path.join(folder, COPIES[name]), os.path.join(folder, 'revert', name),
                         os.path.join(folder, 'revert', COPIES[name])):
                try:
                    other = _load(copy)
                except (OSError, ValueError):
                    continue
                if not isinstance(other, dict):
                    continue
                copy_state = crc_state(copy)
                for key, value in other.items():
                    if key not in main or main[key] != value:
                        data_list.append((context.get_relative_path(copy), key, _shown(value), copy_state))
                read.append(copy)
    if counts:
        logfunc('Skybell Doorbell Settings: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
