"""HomeKit entities from a macOS datastore.sqlite (HomeKit backing store), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosHomeKit": {
        "name": "HomeKit Entities",
        "description": "HomeKit entities in each user's Library/HomeKit/datastore.sqlite, one row per record of its "
                       "record table: the model type, its decoded name and fields, the record's own identifier and "
                       "parent, and the created and modified times the backing store kept.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "HomeKit (macOS)",
        "notes": "Reads datastore.sqlite in a Library/HomeKit folder and reports one row per row of its record "
                 "table. Record Modified (UTC) and Record Created (UTC) are the RecordMtime and RecordCtime dates "
                 "inside the row's record blob, an NSKeyedArchiver property list the backing store keeps for the "
                 "CloudKit record; both decoded on every row of dleapp_macos_bigsur. Type is the record.type column, "
                 "the model type name (for example HMDHomeModel, HMDRoomModel, HMDUserModel, HMDDeviceModel, "
                 "HMDActionSetModel). UUID and Parent UUID are the record.uuid and record.parent_uuid columns, which "
                 "build the entity tree; a top-level record has no parent. Name and Details come from the row's data "
                 "blob, an NSKeyedArchiver property list whose root is a dictionary of the model's fields: Name is "
                 "that dictionary's name field when it is text (blank when the model has none, such as the "
                 "setting-constraint records), and Details is the dictionary's fields as JSON, name included, with "
                 "the internal _t, _u, _P and _V keys dropped (they repeat the Type, UUID and Parent UUID columns), "
                 "nested property lists shown as a marker rather than decoded, and any remaining bytes shown as a "
                 "length. Details is where the examiner-relevant values sit: the home owner's user ID (ownerUserID, "
                 "an email-shaped value on dleapp_macos_bigsur), a device or accessory name, an accessory "
                 "manufacturer, model, serial number and firmware version, a user's privilege, and an action set's "
                 "type. The data blob is read only when its encoding is 1 (an NSKeyedArchiver archive); no row of "
                 "dleapp_macos_bigsur used another encoding. The record and data blobs are not reported whole. Only "
                 "datastore.sqlite is read. The companion datastore3.sqlite (record_v2 table) stores its models in a "
                 "different encoding that is not an NSKeyedArchiver archive and is not read here; on "
                 "dleapp_macos_bigsur it held 108 record_v2 rows (setting, setting-constraint, user-data, "
                 "access-control and cloud-state model types) that this artifact does not report, and on the images "
                 "where datastore.sqlite is empty it held only HMBCloudDatabaseStateModel and HMBCloudZoneStateModel "
                 "records (5 rows and 15 rows), no home entities. Validated on dleapp_macos_bigsur (macOS 11), where "
                 "the record table has 232 rows from one home: 1 HMDHomeModel, 1 HMDRoomModel, 1 HMDUserModel, 2 "
                 "HMDDeviceModel, 1 HMDAppleMediaAccessoryModel, 4 HMDActionSetModel, and settings, constraints, "
                 "device capabilities, application data, account and cloud bookkeeping records making up the rest, "
                 "25 distinct type values in all. Name was filled on 52 rows and blank on the 155 setting-constraint "
                 "rows and other nameless models; Record Modified and Record Created carried a value on all 232 "
                 "rows; all 232 rows come from one user, so User holds one value there. magnet2021_macos_bigsur and "
                 "mvs2026_macbookpro_macos15 hold a datastore.sqlite whose record table is empty, and "
                 "evidencelocker_macos14 has no HomeKit datastore, so all three report no rows. When a logical "
                 "extraction holds the same database at its own path and again under System/Volumes/Data or "
                 "System/Volumes/Update/mnt1 with identical bytes it is read once, and when the copies differ a row "
                 "both hold is reported once with both files in Source File.",
        "paths": ("*/Library/HomeKit/datastore.sqlite*",),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "home",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 232 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 (Magnet 2021 CTF) | 0 rows (record table empty)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no HomeKit datastore)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (record table empty)",
        },
    },
}

import json
import os
import plistlib

from scripts.ilapfuncs import artifact_processor, does_table_exist_in_db, get_sqlite_db_records, logfunc
from scripts.macos_plists import fold_view_rows, resolve_keyed_archive, unique_sources, user_from_path

_LABEL = 'HomeKit Entities'
_QUERY = 'SELECT type, uuid, parent_uuid, encoding, record, data FROM record ORDER BY rowid'
_INTERNAL = {'_t', '_u', '_P', '_V'}


def _archive(blob):
    """The NSKeyedArchiver plist dict for a blob, or None."""
    if not isinstance(blob, (bytes, bytearray)) or not bytes(blob).startswith(b'bplist00'):
        return None
    try:
        archive = plistlib.loads(bytes(blob))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError, RecursionError):
        return None
    return archive if isinstance(archive, dict) and '$objects' in archive else None


def _date(archive, root):
    """A datetime resolved from one key of the record blob's keyed archive, or '' ."""
    from datetime import datetime
    if archive is None:
        return ''
    value = resolve_keyed_archive(archive, root=root)
    return value if isinstance(value, datetime) else ''


def _sanitize(value):
    """value made JSON-safe: bytes to a marker, datetimes to ISO text, UIDs to int."""
    import datetime as _dt
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return value
    if isinstance(value, (bytes, bytearray)):
        return '<bplist>' if bytes(value).startswith(b'bplist00') else f'<{len(value)} bytes>'
    if isinstance(value, _dt.datetime):
        return value.isoformat()
    if isinstance(value, plistlib.UID):
        return int(value.data)
    if isinstance(value, dict):
        return {str(k): _sanitize(v) for k, v in value.items() if str(k) not in _INTERNAL}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return str(value)


def _name_and_details(data_blob, encoding):
    """(name, details JSON) from the model object in the data blob; ('', '') when it is not read."""
    if encoding != 1:
        return '', ''
    archive = _archive(data_blob)
    if archive is None:
        return '', ''
    model = resolve_keyed_archive(archive)
    if not isinstance(model, dict):
        return '', ''
    name = model.get('name')
    name = name if isinstance(name, str) else ''
    details = {str(k): _sanitize(v) for k, v in model.items() if str(k) not in _INTERNAL}
    return name, json.dumps(details, ensure_ascii=False, sort_keys=True)


def _rows(path):
    for row_type, uuid, parent_uuid, encoding, record, data in (get_sqlite_db_records(path, _QUERY) or []):
        archive = _archive(record)
        name, details = _name_and_details(data, encoding)
        yield (_date(archive, 'RecordMtime'), _date(archive, 'RecordCtime'),
               '' if row_type is None else str(row_type), name,
               '' if uuid is None else str(uuid), '' if parent_uuid is None else str(parent_uuid), details)


@artifact_processor
def macosHomeKit(context):
    data_headers = (('Record Modified (UTC)', 'datetime'), ('Record Created (UTC)', 'datetime'), 'Type', 'Name',
                    'UUID', 'Parent UUID', 'Details (JSON)', 'User', 'Source File')
    data_list = []
    read = []
    databases = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'datastore.sqlite']
    paths, _skipped = unique_sources(context, databases, sidecars=('-wal', '-shm'), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'record'):
            logfunc(f'{_LABEL}: no record table read from {relative}')
            continue
        read.append(path)
        data_list.extend(row + (user_from_path(relative), relative) for row in _rows(path))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
