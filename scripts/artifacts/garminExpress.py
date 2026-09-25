"""Garmin Express devices and uploads on macOS, for DLEAPP.

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
        "last_update_date": "2026-09-25",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "One row per folder in ~/Library/Application Support/Garmin/Express/"
                 "RegisteredDevices, read from its GarminDevice.xml and AdditionalInfo.plist. "
                 "Model, Part Number and Software Version are the Description, PartNumber and "
                 "SoftwareVersion of the XML's Model element, and Unit ID is its Id, or the "
                 "folder name when the XML has none; the XML follows Garmin's published "
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
                 " columns blank and is logged. The Logs folder is not read. Only the macOS "
                 "location is covered. User is the folder after Users in the source path, and is "
                 "blank when the input is one user's home folder whose path names no user. Public "
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
        "last_update_date": "2026-09-25",
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
                 "ID and Serial Number tie each row to its row in Garmin Express Devices. User is "
                 "the folder after Users in the source path, and is blank when the input is one "
                 "user's home folder whose path names no user. Public regression cases are "
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
}

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources, user_from_path

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
