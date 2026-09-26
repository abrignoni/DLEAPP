"""Biome sync peers and Biome Sets stores on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""
__artifacts_v2__ = {
    "macosBiomeDeviceSync": {
        "name": 'Biome Device Sync',
        "description": 'Devices listed in the Biome sync store: last sync time, the device and IDS device identifiers, name, and the model, platform and me values as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the DevicePeer table of the Biome sync store, one row per row of that table. Last Sync (UTC) is last_sync_date read as seconds since 1 January 1970 UTC, and the other columns are device_identifier, ids_device_identifier, name, model, platform and me, as iLEAPP's biomeSync module reads them (Reference: iLEAPP, scripts/artifacts/biomeSync.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSync.py#L52-L80). That module names the platform numbers as device types and shows model as an OS build without a cited source, so here Platform (as stored), Model (as stored) and Me (as stored) are reported as stored. The table declares model as STRING, a declared type SQLite gives numeric affinity, so a value that reads as a number, such as a build string holding the letter E between digits, is stored as a real number and is shown here in that form (Reference: SQLite, 'Datatypes In SQLite', sections 3.1 and 3.1.1, https://www.sqlite.org/datatype3.html). On the public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the table holds one row: Me (as stored) is 1, Platform (as stored) is 4, Name and IDS Device ID are blank, Last Sync (UTC) is blank because last_sync_date is null, and Model (as stored) is 2.4e+249, which is 24E248 read as a number; 24E248 is the ProductBuildVersion in that extraction's System/Library/CoreServices/SystemVersion.plist. The protocol_version column is not reported. When a logical extraction holds a store under Users/ and under System/Volumes/Data/Users/, a row both copies hold is reported once. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur no Biome folder exists.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/sync/sync.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'devices',
    },
    "macosBiomeSetsInstalledApps": {
        "name": 'Biome Sets Installed Apps',
        "description": 'Items of the App.InstalledApp Biome set: record time, bundle ID and app name, with any other fields as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the App.InstalledApp Biome set. Bundle ID is field 1 and App Name is field 3, as iLEAPP's biomeSetsInstalledApps reads them (Reference: https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L224-L236). On the public MacBook Pro logical extraction the store gives 327 rows from one user's folder; Bundle ID and App Name were filled on every row and Other Fields (as stored) on 4. Each Set.db is a SQLite store whose content table holds one protobuf message per item, read by field number without a schema. Two store layouts are read, as iLEAPP's biomeSetsStores module reads them (Reference: iLEAPP, scripts/artifacts/biomeSetsStores.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L139-L188): where the store has an instance table, each content row is joined through the provenance table to its instance row and Record Time (UTC) is instance.modified; otherwise each content row is joined to its metacontent_provenance row and Record Time (UTC) is metacontent_provenance.written_date. Both are read as microseconds since 1 January 1970 UTC. The public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) has the instance layout. Record Time (UTC) is when the store recorded the item; it is not established as the time the item itself was created, installed or changed. Provenance rows that carry no content, including those metacontent_provenance marks with a deleted date, are not reported, and the run log counts the deleted ones. Other Fields (as stored) lists every field of the message the named columns do not show, as field number and value, with a submessage's fields numbered under it (so 8.1 is field 1 of field 8); what those fields record is not established. When a logical extraction holds a store under Users/ and under System/Volumes/Data/Users/, a row both copies hold is reported once. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur no Biome folder exists.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/sets/Default/App.InstalledApp/Database/Set.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'package',
    },
    "macosBiomeSetsContacts": {
        "name": 'Biome Sets Contacts',
        "description": 'Items of the Contacts.Contact Biome set: record time, given name and family name, with any other fields as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Contacts.Contact Biome set. Given Name is field 1 and Family Name is field 3, as iLEAPP's biomeSetsContacts reads them (Reference: https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L240-L252). On the public MacBook Pro logical extraction the store gives 2 rows from one user's folder; Given Name and Family Name were filled on both and Other Fields (as stored) on 1. Each Set.db is a SQLite store whose content table holds one protobuf message per item, read by field number without a schema. Two store layouts are read, as iLEAPP's biomeSetsStores module reads them (Reference: iLEAPP, scripts/artifacts/biomeSetsStores.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L139-L188): where the store has an instance table, each content row is joined through the provenance table to its instance row and Record Time (UTC) is instance.modified; otherwise each content row is joined to its metacontent_provenance row and Record Time (UTC) is metacontent_provenance.written_date. Both are read as microseconds since 1 January 1970 UTC. The public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) has the instance layout. Record Time (UTC) is when the store recorded the item; it is not established as the time the item itself was created, installed or changed. Provenance rows that carry no content, including those metacontent_provenance marks with a deleted date, are not reported, and the run log counts the deleted ones. Other Fields (as stored) lists every field of the message the named columns do not show, as field number and value, with a submessage's fields numbered under it (so 8.1 is field 1 of field 8); what those fields record is not established. When a logical extraction holds a store under Users/ and under System/Volumes/Data/Users/, a row both copies hold is reported once. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur no Biome folder exists.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/sets/Default/Contacts.Contact/Database/Set.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'address-book',
    },
    "macosBiomeSetsFindMyDevices": {
        "name": 'Biome Sets FindMy Devices',
        "description": 'Items of the FindMy.Device Biome set: record time, device name and owner given and family names, with any other fields as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the FindMy.Device Biome set. Device Name is field 1, and Owner Given Name and Owner Family Name are fields 1 and 2 of field 2, as iLEAPP's biomeSetsFindMyDevices reads them (Reference: https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L256-L270). The public MacBook Pro logical extraction holds no FindMy.Device set. Each Set.db is a SQLite store whose content table holds one protobuf message per item, read by field number without a schema. Two store layouts are read, as iLEAPP's biomeSetsStores module reads them (Reference: iLEAPP, scripts/artifacts/biomeSetsStores.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L139-L188): where the store has an instance table, each content row is joined through the provenance table to its instance row and Record Time (UTC) is instance.modified; otherwise each content row is joined to its metacontent_provenance row and Record Time (UTC) is metacontent_provenance.written_date. Both are read as microseconds since 1 January 1970 UTC. The public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) has the instance layout. Record Time (UTC) is when the store recorded the item; it is not established as the time the item itself was created, installed or changed. Provenance rows that carry no content, including those metacontent_provenance marks with a deleted date, are not reported, and the run log counts the deleted ones. Other Fields (as stored) lists every field of the message the named columns do not show, as field number and value, with a submessage's fields numbered under it (so 8.1 is field 1 of field 8); what those fields record is not established. When a logical extraction holds a store under Users/ and under System/Volumes/Data/Users/, a row both copies hold is reported once. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur no Biome folder exists.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/sets/Default/FindMy.Device/Database/Set.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'device-mobile',
    },
    "macosBiomeSetsShortcutPhrases": {
        "name": 'Biome Sets App Shortcut Phrases',
        "description": 'Items of the App.Shortcut.Phrase Biome sets: record time, the source app named in the store path, phrase, phrase template, field 3 and intent URL as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Set.db in each sourceIdentifier= folder of the App.Shortcut.Phrase Biome set; Source App is that folder's sourceIdentifier= value. Phrase is field 1, Phrase Template is field 2 and Intent URL is field 4, as iLEAPP's biomeSetsShortcutPhrases reads them (Reference: https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L291-L305). That module does not read field 3; it is reported here as Field 3 (as stored). The public MacBook Pro logical extraction holds no App.Shortcut.Phrase set. Each Set.db is a SQLite store whose content table holds one protobuf message per item, read by field number without a schema. Two store layouts are read, as iLEAPP's biomeSetsStores module reads them (Reference: iLEAPP, scripts/artifacts/biomeSetsStores.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L139-L188): where the store has an instance table, each content row is joined through the provenance table to its instance row and Record Time (UTC) is instance.modified; otherwise each content row is joined to its metacontent_provenance row and Record Time (UTC) is metacontent_provenance.written_date. Both are read as microseconds since 1 January 1970 UTC. The public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) has the instance layout. Record Time (UTC) is when the store recorded the item; it is not established as the time the item itself was created, installed or changed. Provenance rows that carry no content, including those metacontent_provenance marks with a deleted date, are not reported, and the run log counts the deleted ones. Other Fields (as stored) lists every field of the message the named columns do not show, as field number and value, with a submessage's fields numbered under it (so 8.1 is field 1 of field 8); what those fields record is not established. When a logical extraction holds a store under Users/ and under System/Volumes/Data/Users/, a row both copies hold is reported once. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur no Biome folder exists.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/sets/Default/App.Shortcut.Phrase/*/Database/Set.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'message-circle',
    },
    "macosBiomeSetsShortcutEntities": {
        "name": 'Biome Sets App Shortcut Entities',
        "description": 'Items of the App.Shortcut.Entity Biome sets: record time, the source app named in the store path, entity name, identifier, type and query provider as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Biome (macOS)",
        "notes": "Reads the Set.db in each sourceIdentifier= folder of the App.Shortcut.Entity Biome set; Source App is that folder's sourceIdentifier= value. Entity Name, Entity Identifier, Entity Type and Query Provider are fields 1 to 4, as iLEAPP's biomeSetsShortcutEntities reads them (Reference: https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L309-L324). The public MacBook Pro logical extraction holds no App.Shortcut.Entity set. Each Set.db is a SQLite store whose content table holds one protobuf message per item, read by field number without a schema. Two store layouts are read, as iLEAPP's biomeSetsStores module reads them (Reference: iLEAPP, scripts/artifacts/biomeSetsStores.py, https://github.com/abrignoni/iLEAPP/blob/ea591113284c3e2e48bff4bee934fe45827a5c22/scripts/artifacts/biomeSetsStores.py#L139-L188): where the store has an instance table, each content row is joined through the provenance table to its instance row and Record Time (UTC) is instance.modified; otherwise each content row is joined to its metacontent_provenance row and Record Time (UTC) is metacontent_provenance.written_date. Both are read as microseconds since 1 January 1970 UTC. The public MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) has the instance layout. Record Time (UTC) is when the store recorded the item; it is not established as the time the item itself was created, installed or changed. Provenance rows that carry no content, including those metacontent_provenance marks with a deleted date, are not reported, and the run log counts the deleted ones. Other Fields (as stored) lists every field of the message the named columns do not show, as field number and value, with a submessage's fields numbered under it (so 8.1 is field 1 of field 8); what those fields record is not established. When a logical extraction holds a store under Users/ and under System/Volumes/Data/Users/, a row both copies hold is reported once. User is the folder after Users in the source path, or root under private/var/root, and is blank when the input is one user's home folder whose path names no user. On dleapp_macos_bigsur no Biome folder exists.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no member matches the declared paths)",
                 },
        "paths": ('*/Biome/sets/Default/App.Shortcut.Entity/*/Database/Set.db*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": 'database',
    },
}

import os
import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_biome import fields, first, text
from scripts.macos_plists import canonical_relative, unique_sources, user_from_path

_SOURCE_APP = re.compile(r'sourceIdentifier=([^/\\]+)')


def _stores(context, db_name, label):
    """The store files named db_name, less byte-identical copies under a second view."""
    paths = [p for p in context.get_files_found() if os.path.basename(str(p)) == db_name]
    kept, _skipped = unique_sources(context, paths, sidecars=('-wal', '-shm'), label=label)
    return kept


def _query(path, sql):
    db = open_sqlite_db_readonly(path)
    if db is None:
        return None
    try:
        return db.execute(sql).fetchall()
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f'Could not query {os.path.basename(path)}: {ex}')
        return None
    finally:
        db.close()


def _micro_utc(value):
    """Microseconds since 1970-01-01 UTC as an aware datetime, or ''."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ''
    try:
        return datetime.fromtimestamp(value / 1_000_000, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _seconds_utc(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ''
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _as_stored(value):
    return '' if value is None else str(value)


def _submessage(value):
    """The fields of a length-delimited value that is a message rather than text, or None."""
    if not isinstance(value, (bytes, bytearray)):
        return None
    raw = bytes(value)
    if raw.decode('utf-8', errors='replace').isprintable():
        return None
    try:
        found = fields(raw)
    except ValueError:
        return None
    return found or None


def _flatten(found, prefix=''):
    """(field path, value) pairs for every field, with submessage fields numbered under it."""
    for number in sorted(found):
        for value in found[number]:
            label = f'{prefix}{number}'
            inner = _submessage(value)
            if inner is not None:
                yield from _flatten(inner, f'{label}.')
            else:
                yield label, text(value)


def _other(found, shown):
    """Every field the named columns do not show, as 'number: value' pairs."""
    rest = {number: values for number, values in found.items() if number not in shown}
    return '; '.join(f'{label}: {value}' for label, value in _flatten(rest))


def _set_items(path, label):
    """(record time, message fields) for each item of a Set.db store."""
    tables = {row[0] for row in (_query(path, "SELECT name FROM sqlite_master WHERE type='table'") or [])}
    if 'content' not in tables:
        logfunc(f'{label}: {os.path.basename(path)} has no content table and is not read')
        return
    if 'instance' in tables:
        sql = ('SELECT i.source_item_id_hash, i.modified, c.content FROM content c '
               'JOIN provenance p ON p.content_hash = c.content_hash '
               'JOIN instance i ON i.provenance_row_id = p.provenance_row_id')
    elif 'metacontent_provenance' in tables:
        sql = ('SELECT mp.source_item_id_hash, mp.written_date, c.content FROM content c '
               'JOIN metacontent_provenance mp ON mp.content_hash = c.content_hash')
        deleted = _query(path, 'SELECT count(*) FROM metacontent_provenance WHERE deleted_date IS NOT NULL')
        if deleted and deleted[0][0]:
            logfunc(f'{label}: {deleted[0][0]} item(s) marked deleted carry no content and are not reported')
    else:
        logfunc(f'{label}: {os.path.basename(path)} has neither layout this artifact reads')
        return
    for item, recorded, blob in _query(path, sql) or []:
        try:
            found = fields(blob)
        except (ValueError, TypeError):
            logfunc(f'{label}: an item of {os.path.basename(path)} did not read as a protobuf message')
            continue
        yield item, _micro_utc(recorded), bytes(blob), found


def _set_artifact(context, label, row_for, per_app=False):
    rows, read, seen = [], [], set()
    for path in _stores(context, 'Set.db', label):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        app_match = _SOURCE_APP.search(str(relative).replace('\\', '/'))
        read.append(path)
        for item, recorded, blob, found in _set_items(path, label):
            key = (canonical_relative(relative), item, recorded, blob)
            if key in seen:
                continue
            seen.add(key)
            row = (recorded,)
            if per_app:
                row += (app_match.group(1) if app_match else '',)
            row += row_for(found) + (user,)
            if per_app:
                row += (relative,)
            rows.append(row)
    rows.sort(key=lambda r: (r[0] or datetime.min.replace(tzinfo=timezone.utc)))
    return rows, '\n'.join(read)


@artifact_processor
def macosBiomeDeviceSync(context):
    data_headers = (('Last Sync (UTC)', 'datetime'), 'Device ID', 'IDS Device ID', 'Name',
                    'Model (as stored)', 'Platform (as stored)', 'Me (as stored)', 'User')
    rows, read, seen = [], [], set()
    for path in _stores(context, 'sync.db', 'Biome Device Sync'):
        relative = context.get_relative_path(path)
        records = _query(path, 'SELECT rowid, last_sync_date, device_identifier, ids_device_identifier, '
                               'name, model, platform, me FROM DevicePeer')
        if records is None:
            continue
        read.append(path)
        for record in records:
            key = (canonical_relative(relative),) + tuple(record)
            if key in seen:
                continue
            seen.add(key)
            _rowid, last, device, ids, name, model, platform, me = record
            rows.append((_seconds_utc(last), _as_stored(device), _as_stored(ids), _as_stored(name),
                         _as_stored(model), _as_stored(platform), _as_stored(me),
                         user_from_path(relative)))
    return data_headers, rows, '\n'.join(read)


@artifact_processor
def macosBiomeSetsInstalledApps(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Bundle ID', 'App Name', 'Other Fields (as stored)', 'User')
    rows, source = _set_artifact(context, 'Biome Sets Installed Apps', lambda f: (
        text(first(f, 1)), text(first(f, 3)), _other(f, {1, 3})))
    return data_headers, rows, source


@artifact_processor
def macosBiomeSetsContacts(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Given Name', 'Family Name', 'Other Fields (as stored)', 'User')
    rows, source = _set_artifact(context, 'Biome Sets Contacts', lambda f: (
        text(first(f, 1)), text(first(f, 3)), _other(f, {1, 3})))
    return data_headers, rows, source


def _owner(found):
    inner = _submessage(first(found, 2))
    inner = inner if inner is not None else {}
    return text(first(inner, 1)), text(first(inner, 2))


@artifact_processor
def macosBiomeSetsFindMyDevices(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Device Name', 'Owner Given Name', 'Owner Family Name',
                    'Other Fields (as stored)', 'User')
    rows, source = _set_artifact(context, 'Biome Sets FindMy Devices', lambda f: (
        (text(first(f, 1)),) + _owner(f) + (_other(f, {1, 2}),)))
    return data_headers, rows, source


@artifact_processor
def macosBiomeSetsShortcutPhrases(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Source App', 'Phrase', 'Phrase Template',
                    'Field 3 (as stored)', 'Intent URL', 'Other Fields (as stored)', 'User', 'Source File')
    rows, source = _set_artifact(context, 'Biome Sets App Shortcut Phrases', lambda f: (
        text(first(f, 1)), text(first(f, 2)), text(first(f, 3)), text(first(f, 4)), _other(f, {1, 2, 3, 4})),
        per_app=True)
    return data_headers, rows, source


@artifact_processor
def macosBiomeSetsShortcutEntities(context):
    data_headers = (('Record Time (UTC)', 'datetime'), 'Source App', 'Entity Name', 'Entity Identifier',
                    'Entity Type', 'Query Provider', 'Other Fields (as stored)', 'User', 'Source File')
    rows, source = _set_artifact(context, 'Biome Sets App Shortcut Entities', lambda f: (
        text(first(f, 1)), text(first(f, 2)), text(first(f, 3)), text(first(f, 4)), _other(f, {1, 2, 3, 4})),
        per_app=True)
    return data_headers, rows, source
