__artifacts_v2__ = {
    "macosBluetoothPairedLE": {
        "name": "Bluetooth Paired LE Devices",
        "description": "Rows of the PairedDevices table of a Mac's "
                       "com.apple.MobileBluetooth.ledevices.paired.db, current and read from its "
                       "write-ahead log, with names, addresses and times as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "Reads /Library/Bluetooth/com.apple.MobileBluetooth.ledevices.paired.db, the "
                 "database iLEAPP's Bluetooth Paired LE artifact reads on iOS. On "
                 "adams_macbookpro_macos26 (macOS 26.2) /Library/Preferences/com.apple.bluetooth.plist "
                 "holds settings and no DeviceCache, so Bluetooth Devices has no rows there and this "
                 "table is where its paired devices are listed. Last Seen Time and Last Connection "
                 "Time are the LastSeenTime and LastConnectionTime integers as stored; on that image "
                 "they run from tens to tens of thousands, far below any Unix or Mac absolute time, "
                 "and their unit and starting point are not established. Name Origin is the "
                 "NameOrigin integer as stored; its meaning is not established. iCloud Identifier is "
                 "the iCloudIdentifier value as stored. GATTServiceChangeConfig and Tags held one "
                 "value on every row of that image and are not reported. Record State is Current "
                 "for a row of the database as SQLite reads it with its -wal, and Not in current "
                 "state for a device (by Uuid) that an earlier state in the write-ahead log holds and "
                 "the current state does not; such a row shows the newest earlier state holding it, "
                 "and Read From names the log states it was read in. Earlier versions of a current "
                 "row are counted in the run log and not listed. Reading the log does not establish "
                 "when or why a row left the current state.",
        "paths": ('*/Library/Bluetooth/com.apple.MobileBluetooth.ledevices.paired.db*',),
        "output_types": "standard",
        "artifact_icon": "bluetooth",
        "sample_data": {
            "adams_macbookpro_macos26": "macOS 26.2 build 25C56 | 4 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no file matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no file matches the declared paths)",
        },
    },
    "macosBluetoothOtherLE": {
        "name": "Bluetooth Other LE Devices",
        "description": "Rows of the OtherDevices table of a Mac's "
                       "com.apple.MobileBluetooth.ledevices.other.db, current and read from its "
                       "write-ahead log, with names, addresses and times as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Connected Devices (macOS)",
        "notes": "Reads /Library/Bluetooth/com.apple.MobileBluetooth.ledevices.other.db, the "
                 "database iLEAPP's Bluetooth Other LE artifact reads on iOS. A row records a "
                 "device the Bluetooth stack kept a record of; it does not by itself establish a "
                 "pairing, a connection or a timed encounter. Last Seen Time and Last Connection "
                 "Time are the LastSeenTime and LastConnectionTime integers as stored; on "
                 "adams_macbookpro_macos26 (macOS 26.2) they run from 0 to tens of thousands, far "
                 "below any Unix or Mac absolute time, and their unit and starting point are not "
                 "established. Name Origin is the NameOrigin integer as stored; its meaning is not "
                 "established. ResolvedAddress was empty, and GATTServiceChangeConfig, Tags and "
                 "iCloudIdentifier each held one value on every row of that image; Resolved Address "
                 "is reported and the other three are not. Record State and Read From are as in "
                 "Bluetooth Paired LE Devices: Current for a row SQLite reads with the -wal, Not in "
                 "current state for a device (by Uuid) only an earlier log state holds, shown as the "
                 "newest earlier state holding it. On that image the log held 147 committed "
                 "transactions and 4 devices no longer in the current state. Earlier versions of a "
                 "current row are counted in the run log and not listed. Reading the log does not "
                 "establish when or why a row left the current state.",
        "paths": ('*/Library/Bluetooth/com.apple.MobileBluetooth.ledevices.other.db*',),
        "output_types": "standard",
        "artifact_icon": "bluetooth",
        "sample_data": {
            "adams_macbookpro_macos26": "macOS 26.2 build 25C56 | 32 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no file matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no file matches the declared paths)",
        },
    },
}

import os
import sqlite3

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.sqlite_wal import (EARLIER_VERSION, KIND_COMMITTED, KIND_EARLIER, KIND_UNCOMMITTED,
                                NOT_IN_CURRENT, rows_not_in_current)

_WAL_KINDS = (KIND_COMMITTED, KIND_EARLIER, KIND_UNCOMMITTED)
STATE_CURRENT = 'Current'
STATE_NOT_IN_CURRENT = 'Not in current state'


def _read_from(name, item):
    """Where in the write-ahead log a row was read, in words."""
    parts = []
    if item.first_state is not None:
        first, last = item.first_state, item.last_state
        states = f'state {first}' if first == last else f'states {first} to {last}'
        parts.append(f'{name}-wal, committed {states}')
    if item.earlier_generation:
        first, last = item.earlier_generation
        commits = f'commit {first}' if first == last else f'commits {first} to {last}'
        parts.append(f'{name}-wal, previous log generation, left-over {commits}')
    if not parts:
        parts.append(f'{name}-wal, frames after the last commit')
    return '; '.join(parts)


def _rank(item):
    """Orders the states a row was read in, newest last."""
    if item.first_state is not None:
        return (2, item.last_state)
    if item.earlier_generation:
        return (1, item.earlier_generation[1])
    return (0, 0)


def device_rows(db_path, table, columns, label):
    """(current rows, rows only an earlier log state holds) of table, each a tuple of columns.

    Uuid must be the first column; a device is one Uuid. Of the earlier rows, one per Uuid
    the current state does not hold, the newest, with where it was read appended.
    """
    query = f'SELECT {", ".join(columns)} FROM {table}'
    db = open_sqlite_db_readonly(db_path)
    if db is None:
        return [], []
    try:
        current = db.execute(query).fetchall()
    except sqlite3.Error as ex:
        logfunc(f'{label}: {table} not read from {os.path.basename(db_path)}: {ex}')
        return [], []
    finally:
        db.close()
    try:
        _cols, found, wal = rows_not_in_current(db_path, query, key_columns=(0,), include=_WAL_KINDS)
    except (sqlite3.Error, OSError) as ex:
        logfunc(f'{label}: write-ahead log not read for {os.path.basename(db_path)}: {ex}')
        return current, []
    logfunc(f'{label}: {wal.summary()}')
    newest = {}
    earlier_versions = 0
    for item in found:
        if item.status == EARLIER_VERSION:
            earlier_versions += 1
            continue
        if item.status != NOT_IN_CURRENT:
            continue
        uuid = item.values[0]
        if uuid not in newest or _rank(item) > _rank(newest[uuid]):
            newest[uuid] = item
    if earlier_versions:
        logfunc(f'{label}: {earlier_versions} earlier versions of current rows in the log, not listed')
    name = os.path.basename(db_path)
    removed = [tuple(item.values) + (_read_from(name, item),) for _uuid, item in sorted(newest.items())]
    return current, removed


def _databases(context, name):
    return sorted({str(p) for p in context.get_files_found()
                   if os.path.basename(str(p)) == name and os.path.isfile(str(p))})


_PAIRED_COLUMNS = ('Uuid', 'Name', 'NameOrigin', 'Address', 'ResolvedAddress', 'LastSeenTime',
                   'LastConnectionTime', 'iCloudIdentifier')
_OTHER_COLUMNS = ('Uuid', 'Name', 'NameOrigin', 'Address', 'ResolvedAddress', 'LastSeenTime',
                  'LastConnectionTime')


def _report(context, name, table, columns, label):
    data_list = []
    read = []
    for path in _databases(context, name):
        current, removed = device_rows(path, table, columns, label)
        read.append(path)
        for values in current:
            data_list.append((STATE_CURRENT, values, ''))
        for values in removed:
            data_list.append((STATE_NOT_IN_CURRENT, values[:-1], values[-1]))
    return data_list, read


@artifact_processor
def macosBluetoothPairedLE(context):
    data_headers = ('Last Seen Time (as stored)', 'Last Connection Time (as stored)', 'UUID', 'Name',
                    'Name Origin (as stored)', 'Address', 'Resolved Address',
                    'iCloud Identifier (as stored)', 'Record State', 'Read From')
    found, read = _report(context, 'com.apple.MobileBluetooth.ledevices.paired.db', 'PairedDevices',
                          _PAIRED_COLUMNS, 'Bluetooth Paired LE Devices')
    data_list = []
    for state, (uuid, name, origin, address, resolved, seen, connected, icloud), where in found:
        data_list.append((seen, connected, uuid, name, origin, address, resolved, icloud, state, where))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosBluetoothOtherLE(context):
    data_headers = ('Last Seen Time (as stored)', 'Last Connection Time (as stored)', 'UUID', 'Name',
                    'Name Origin (as stored)', 'Address', 'Resolved Address', 'Record State',
                    'Read From')
    found, read = _report(context, 'com.apple.MobileBluetooth.ledevices.other.db', 'OtherDevices',
                          _OTHER_COLUMNS, 'Bluetooth Other LE Devices')
    data_list = []
    for state, (uuid, name, origin, address, resolved, seen, connected), where in found:
        data_list.append((seen, connected, uuid, name, origin, address, resolved, state, where))
    return data_headers, data_list, '\n'.join(read)
