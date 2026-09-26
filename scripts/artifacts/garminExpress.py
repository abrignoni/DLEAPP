"""Garmin Express devices, uploads and logs on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "garminExpressDevices": {
        "name": "Garmin Express Devices",
        "description": "Garmin devices registered in Garmin Express, with the model, unit ID, "
                       "serial number, software version, device name, registration account and "
                       "last sync time as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "One row per folder in ~/Library/Application Support/Garmin/Express/"
                 "RegisteredDevices, read from its GarminDevice.xml and AdditionalInfo.plist. "
                 "Model, Part Number and Software Version are the Description, PartNumber and "
                 "SoftwareVersion of the XML's Model element, and Unit ID is its Id, or the "
                 "folder name when the XML has none; the XML declares Garmin's published "
                 "GarminDevice v2 schema. Serial Number, Friendly Name, Registration Email, "
                 "Registration User Name, Market Segment and Auto Backup are the "
                 "device_serial_number, friendly_name, registration_email, "
                 "registration_user_name, market_segment and auto_backup values of "
                 "AdditionalInfo.plist, as stored. Last Connect Sync is its last_connect_sync "
                 "number read as seconds since 1970 UTC; that reading was checked locally against "
                 "the plist dates in the same file, and what event the value records is not "
                 "established. Last Firmware Check and Last Map Check are the "
                 "last_update_check_firmware and last_update_check_map plist dates, read as UTC. "
                 "Account Keys lists the keys of AccountDictionaryDatastore.plist whose value "
                 "names this unit, as stored; what the key identifies is not established. Uploads "
                 "Recorded counts the file names in the device's CompletedUploadsV2 plists, which "
                 "the Garmin Express Uploads artifact lists. A missing or unreadable file leaves its"
                 " columns blank and is logged. The Logs folder is read by the Garmin Express Log artifact. Only the macOS "
                 "location is covered. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Public "
                 "regression cases are independently authored synthetic data; local private "
                 "validation details are not published. Reference: Garmin, GarminDevice v2 "
                 "schema, http://www.garmin.com/xmlschemas/GarminDevicev2.xsd.",
        "paths": ('*/Library/Application Support/Garmin/Express/RegisteredDevices/*/GarminDevice.xml',
                  '*/Library/Application Support/Garmin/Express/RegisteredDevices/*/AdditionalInfo.plist',
                  '*/Library/Application Support/Garmin/Express/RegisteredDevices/*/CompletedUploadsV2_*.plist',
                  '*/Library/Application Support/Garmin/Express/AccountDictionaryDatastore.plist'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "device-watch",
        "sample_data": {},
    },
    "garminExpressUploads": {
        "name": "Garmin Express Uploads",
        "description": "File names Garmin Express lists as uploaded from each registered Garmin "
                       "device, with the FIT file type named in the list's file name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "One row per string in each CompletedUploadsV2_<name>.plist of a folder in "
                 "~/Library/Application Support/Garmin/Express/RegisteredDevices, in the order "
                 "stored. List is the part of the plist's file name after CompletedUploadsV2_. "
                 "For a list named FIT_TYPE_<n>, FIT Type is n and FIT SDK Name is the name "
                 "Garmin's FIT SDK gives file type n (for example 4 is activity and 32 is "
                 "monitoring_b); that Garmin Express names these lists by FIT file type is read "
                 "from the list names and not from a Garmin source. The file names are reported "
                 "as stored and no date is decoded from them. The list records a name, not the "
                 "file: an upload listed here need not be anywhere in the extraction. Model, Unit "
                 "ID and Serial Number tie each row to its row in Garmin Express Devices. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Public regression cases are "
                 "independently authored synthetic data; local private validation details are "
                 "not published. Reference: Garmin, fit-python-sdk profile.py, "
                 "https://github.com/garmin/fit-python-sdk/blob/6db34d7958dce3cef89194e82d6bdc9437c810de/garmin_fit_sdk/profile.py#L26744-L26765.",
        "paths": ('*/Library/Application Support/Garmin/Express/RegisteredDevices/*/GarminDevice.xml',
                  '*/Library/Application Support/Garmin/Express/RegisteredDevices/*/AdditionalInfo.plist',
                  '*/Library/Application Support/Garmin/Express/RegisteredDevices/*/CompletedUploadsV2_*.plist'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "upload",
        "sample_data": {},
    },
    "garminExpressLog": {
        "name": "Garmin Express Log",
        "description": "Lines of the text logs in the Garmin Express Logs folder: the time each line records, converted to UTC with the offset the same line records, the local time and offset as recorded, the ID and level as stored, and the message.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "One row per record line of each .txt file under ~/Library/Application Support/Garmin/Express/Logs whose name does not begin with a dot. The line layout was read from the files themselves; no Garmin documentation of it was found. A record line begins with a date, a time written with dots between hours, minutes and seconds, and a bracketed zone label and UTC offset, followed by two more fields and the message, separated by ' | '. A line that does not begin that way is part of a message that spans several lines and is appended, after a line break, to the message of the record above it; non-blank lines before a file's first record line are reported on their own row with the time columns blank. Files are read as UTF-8, and any bytes that are not UTF-8 are replaced. Local Time (as recorded) and Offset (as recorded) are the time and the bracketed zone label and offset exactly as the line writes them. Time (UTC) is that local time minus the offset the same line records, so no time zone is assumed; it is blank when the date and time are not a valid calendar time. ID (as stored) and Level (as stored) are the second and third fields as written; what the ID identifies and what each level value means are not established. Message is the rest of the line as written. Line is the line number in the file where the record begins. When a logical extraction holds a log under Users/ and under System/Volumes/Data/Users/, a copy whose bytes begin with the other copy's bytes is treated as the same file written further, and only the longer copy is read; copies where neither begins with the other are both read and the run log names them. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. Only the macOS location is covered. Public regression cases are independently authored synthetic data; local private validation details are not published.",
        "paths": ('*/Library/Application Support/Garmin/Express/Logs/*.txt',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {},
    },
}

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, canonical_relative, load_plist, unique_sources, user_from_path

_UPLOADS = 'CompletedUploadsV2_'
_NS = '{http://www.garmin.com/xmlschemas/GarminDevice/v2}'

# FIT SDK 'file' type names, from the profile.py lines cited in the notes.
_FIT_FILE_TYPES = {1: 'device', 2: 'settings', 3: 'sport', 4: 'activity', 5: 'workout',
                   6: 'course', 7: 'schedules', 9: 'weight', 10: 'totals', 11: 'goals',
                   14: 'blood_pressure', 15: 'monitoring_a', 20: 'activity_summary',
                   28: 'monitoring_daily', 32: 'monitoring_b', 34: 'segment',
                   35: 'segment_list', 40: 'exd_configuration'}


def _text(value):
    return '' if value is None else str(value)


def _flag(value):
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return _text(value)


def _unix(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ''
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _device_folders(context, label):
    """{device folder: {file name: path}} for files directly inside RegisteredDevices/<unit>."""
    folders = {}
    paths, _skipped = unique_sources(context, context.get_files_found(), label=label)
    for path in paths:
        parts = context.get_relative_path(path).replace('\\', '/').split('/')
        if len(parts) >= 3 and parts[-3] == 'RegisteredDevices':
            folders.setdefault(os.path.dirname(path), {})[os.path.basename(path)] = path
    return folders


def _model(path, label):
    if not path:
        return {}
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        logfunc(f'{label}: could not read {os.path.basename(path)} in '
                f'{os.path.basename(os.path.dirname(path))}')
        return {}

    def find(tag):
        found = root.find('/'.join(_NS + part for part in tag.split('/')))
        return (found.text or '').strip() if found is not None else ''
    return {'Model': find('Model/Description'), 'Part Number': find('Model/PartNumber'),
            'Software Version': find('Model/SoftwareVersion'), 'Unit ID': find('Id')}


def _uploads(files):
    for name in sorted(files):
        if name.startswith(_UPLOADS) and name.endswith('.plist'):
            yield name[len(_UPLOADS):-len('.plist')], files[name]


def _fit_type(list_name):
    if list_name.startswith('FIT_TYPE_') and list_name[len('FIT_TYPE_'):].isdigit():
        number = int(list_name[len('FIT_TYPE_'):])
        return str(number), _FIT_FILE_TYPES.get(number, '')
    return '', ''


@artifact_processor
def garminExpressDevices(context):
    data_headers = (('Last Connect Sync (UTC)', 'datetime'),
                    ('Last Firmware Check (UTC)', 'datetime'),
                    ('Last Map Check (UTC)', 'datetime'), 'Model', 'Part Number',
                    'Software Version', 'Unit ID', 'Serial Number', 'Friendly Name',
                    'Registration Email', 'Registration User Name', 'Market Segment',
                    'Auto Backup', 'Account Keys', 'Uploads Recorded', 'User')
    data_list = []
    read = []
    accounts = {}
    for path in context.get_files_found():
        if os.path.basename(str(path)) == 'AccountDictionaryDatastore.plist':
            store = load_plist(path)
            if isinstance(store, dict):
                read.append(str(path))
                for key, units in store.items():
                    for unit in units if isinstance(units, list) else [units]:
                        accounts.setdefault(str(unit), []).append(str(key))
    for folder, files in sorted(_device_folders(context, 'Garmin Express Devices').items()):
        relative = context.get_relative_path(folder)
        model = _model(files.get('GarminDevice.xml'), 'Garmin Express Devices')
        info = {}
        if 'AdditionalInfo.plist' in files:
            loaded = load_plist(files['AdditionalInfo.plist'])
            if isinstance(loaded, dict):
                info = loaded
            else:
                logfunc(f'Garmin Express Devices: could not read AdditionalInfo.plist in {relative}')
        uploads = 0
        for _name, path in _uploads(files):
            listed = load_plist(path)
            if isinstance(listed, list):
                uploads += len(listed)
                read.append(path)
        read.extend(p for n, p in files.items() if not n.startswith(_UPLOADS))
        unit = model.get('Unit ID') or os.path.basename(folder)
        data_list.append((
            _unix(info.get('last_connect_sync')), as_utc(info.get('last_update_check_firmware')),
            as_utc(info.get('last_update_check_map')), model.get('Model', ''),
            model.get('Part Number', ''), model.get('Software Version', ''), unit,
            _text(info.get('device_serial_number')), _text(info.get('friendly_name')),
            _text(info.get('registration_email')), _text(info.get('registration_user_name')),
            _text(info.get('market_segment')), _flag(info.get('auto_backup')),
            ', '.join(accounts.get(unit, [])), uploads, user_from_path(relative)))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def garminExpressUploads(context):
    data_headers = ('File Name', 'List', 'FIT Type', 'FIT SDK Name', 'Model', 'Unit ID',
                    'Serial Number', 'User')
    data_list = []
    read = []
    for folder, files in sorted(_device_folders(context, 'Garmin Express Uploads').items()):
        relative = context.get_relative_path(folder)
        model = _model(files.get('GarminDevice.xml'), 'Garmin Express Uploads')
        info = load_plist(files['AdditionalInfo.plist']) if 'AdditionalInfo.plist' in files else None
        info = info if isinstance(info, dict) else {}
        unit = model.get('Unit ID') or os.path.basename(folder)
        for list_name, path in _uploads(files):
            listed = load_plist(path)
            if not isinstance(listed, list):
                logfunc(f'Garmin Express Uploads: could not read {os.path.basename(path)} in {relative}')
                continue
            read.append(path)
            number, sdk_name = _fit_type(list_name)
            for name in listed:
                data_list.append((_text(name), list_name, number, sdk_name,
                                  model.get('Model', ''), unit,
                                  _text(info.get('device_serial_number')),
                                  user_from_path(relative)))
    return data_headers, data_list, '\n'.join(read)


_LOG_LINE = re.compile(r'^(\d{4}-\d{2}-\d{2}) (\d{2})\.(\d{2})\.(\d{2}) '
                       r'\(([A-Za-z]*)([+-])(\d{2}):(\d{2})\) \| ([^|]*?) \| ([^|]*?) \| ?(.*)$')


def _log_utc(match):
    """The line's local time minus the UTC offset the same line records."""
    date, hours, minutes, seconds = match.group(1), match.group(2), match.group(3), match.group(4)
    sign, off_h, off_m = match.group(6), int(match.group(7)), int(match.group(8))
    try:
        local = datetime.strptime(f'{date} {hours}:{minutes}:{seconds}', '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return ''
    offset = timedelta(hours=off_h, minutes=off_m) * (1 if sign == '+' else -1)
    return (local - offset).replace(tzinfo=timezone.utc)


def _log_copies(context, label):
    """The log files to read: one per file, the longer copy where one extends the other."""
    groups = {}
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.isfile(path) and not os.path.basename(path).startswith('.'):
            groups.setdefault(canonical_relative(context.get_relative_path(path)), []).append(path)
    chosen = []
    for key, paths in sorted(groups.items()):
        copies = []
        for path in paths:
            with open(path, 'rb') as handle:
                copies.append((path, handle.read()))
        copies.sort(key=lambda item: len(item[1]), reverse=True)
        longest = copies[0][1]
        if all(longest.startswith(data) for _path, data in copies[1:]):
            chosen.append(copies[0])
            continue
        logfunc(f'{label}: copies of {key} differ and neither extends the other; each copy no other copy extends is read')
        kept = []
        for path, data in copies:
            if not any(other.startswith(data) for _p, other in kept):
                kept.append((path, data))
        chosen.extend(kept)
    return chosen


@artifact_processor
def garminExpressLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Local Time (as recorded)', 'Offset (as recorded)',
                    'ID (as stored)', 'Level (as stored)', 'Message', 'Source File', 'Line', 'User')
    data_list = []
    read = []
    for path, data in _log_copies(context, 'Garmin Express Log'):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        read.append(path)
        row = None
        for number, line in enumerate(data.decode('utf-8', errors='replace').splitlines(), start=1):
            match = _LOG_LINE.match(line.lstrip('\ufeff') if number == 1 else line)
            if match:
                if row is not None:
                    data_list.append(tuple(row))
                local = f'{match.group(1)} {match.group(2)}.{match.group(3)}.{match.group(4)}'
                zone = f'{match.group(5)}{match.group(6)}{match.group(7)}:{match.group(8)}'
                row = [_log_utc(match), local, zone, match.group(9).strip(), match.group(10).strip(),
                       match.group(11), relative, number, user]
            elif row is not None:
                row[5] = f'{row[5]}\n{line}'
            elif line.strip():
                data_list.append(('', '', '', '', '', line, relative, number, user))
        if row is not None:
            data_list.append(tuple(row))
    return data_headers, data_list, '\n'.join(read)
