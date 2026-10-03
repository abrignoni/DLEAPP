"""Location Services clients from locationd's clients.plist on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosLocationServicesClients": {
        "name": "Location Services Clients",
        "description": "Entries in locationd's clients.plist, the apps and other software listed "
                       "for Location Services, with each entry's Authorized value and any "
                       "LocationTimeStarted and LocationTimeStopped times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Location Services (macOS)",
        "notes": "Reads private/var/db/locationd/clients.plist, one row per top-level entry whose "
                 "value is a dictionary; a top-level value that is not one, such as the number "
                 "under MigrationVersionNumber on the MacBook Pro extraction below, is not "
                 "reported, and a file that is not a plist dictionary is logged and skipped. "
                 "Howard Oakley describes the file as a dictionary of all the apps and other "
                 "software that could access Location Services data, and says those currently "
                 "granted access carry the key Authorized set to true (The Eclectic Light Company, "
                 "'Managing access to location information', 2025-03-07, "
                 "https://eclecticlight.co/2025/03/07/managing-access-to-location-information/). "
                 "Client is the entry's key as stored. Bundle ID, Bundle Path, Executable, "
                 "Authorized, Registered, Whitelisted, System Service and Requirement are the keys "
                 "BundleId, BundlePath, Executable, Authorized, Registered, Whitelisted, "
                 "isSystemService and Requirement as stored, blank when absent, with a boolean "
                 "shown as Yes or No. Every other key is kept in Other Keys as 'key: value', "
                 "joined with ' | ', with data in hex and a dictionary or array as JSON. Location "
                 "Time Started (UTC) and Location Time Stopped (UTC) are LocationTimeStarted and "
                 "LocationTimeStopped read as seconds since 2001-01-01 UTC, the reading Kolide's "
                 "post 'How to Deal With Dates and Times in Osquery' gives LocationTimeStopped in "
                 "this file "
                 "(https://www.kolide.com/blog/how-to-deal-with-dates-and-times-in-osquery). What "
                 "event each time records beyond its name is not established here. The layout "
                 "differs between the tested versions. On dleapp_macos_bigsur (macOS 11.2.1) the "
                 "12 entries are keyed by a bundle ID (4), by com.apple.locationd.bundle- and a "
                 "path (7), or by com.apple.locationd.executable- (1). Authorized was Yes on 3, No "
                 "on 2 and absent on 7, and 6 entries each carry one of the two times, between "
                 "2020-12-02 15:17:15 and 2021-02-19 19:42:07 UTC. On the public MacBook Pro "
                 "logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15) the 23 entries are "
                 "keyed by root (14) or a UUID (9), a colon, p and a path or i and a bundle ID, "
                 "and a colon, with a further p and a path on 4 of them. The UUID equals the "
                 "GeneratedUID in the dslocal record of the account with uid 501 on that "
                 "extraction. There Authorized was Yes on 1, No on 1 and absent on 21, and no "
                 "entry carries either time. When a logical extraction holds the file under "
                 "private/var and again under System/Volumes/Data/private/var, a copy "
                 "byte-identical to another is read once and counted in the run log, as the "
                 "MacBook Pro extraction's two copies were.",
        "paths": ('*/private/var/db/locationd/clients.plist',),
        "output_types": ["standard"],
        "artifact_icon": "map-pin",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 12 rows",
        },
    },
}

import json

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import load_plist, mac_absolute_utc, unique_sources

# Report column -> the entry key it is read from; every other key goes to Other Keys.
_COLUMNS = (
    ('Bundle ID', 'BundleId'),
    ('Bundle Path', 'BundlePath'),
    ('Executable', 'Executable'),
    ('Authorized', 'Authorized'),
    ('Registered', 'Registered'),
    ('Whitelisted', 'Whitelisted'),
    ('System Service', 'isSystemService'),
    ('Requirement', 'Requirement'),
)
_TIMES = ('LocationTimeStarted', 'LocationTimeStopped')
_READ = {key for _column, key in _COLUMNS} | set(_TIMES)


def _json_default(value):
    return value.hex() if isinstance(value, (bytes, bytearray)) else str(value)


def stored_text(value):
    """A plist value as report text: Yes or No for a boolean, hex for data, JSON for a
    dictionary or array, and anything else as stored."""
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=_json_default, ensure_ascii=False, sort_keys=True)
    return '' if value is None else str(value)


def client_row(key, entry):
    """The report row for one clients.plist entry."""
    cells = [stored_text(entry.get(field)) for _column, field in _COLUMNS]
    other = [f'{name}: {stored_text(value)}' for name, value in entry.items() if name not in _READ]
    return (mac_absolute_utc(entry.get('LocationTimeStarted')),
            mac_absolute_utc(entry.get('LocationTimeStopped')), key, *cells, ' | '.join(other))


@artifact_processor
def macosLocationServicesClients(context):
    data_headers = (('Location Time Started (UTC)', 'datetime'),
                    ('Location Time Stopped (UTC)', 'datetime'), 'Client') + tuple(
                        column for column, _key in _COLUMNS) + ('Other Keys',)
    data_list, sources = [], []
    files = [str(f) for f in context.get_files_found() if str(f).endswith('clients.plist')]
    kept, _skipped = unique_sources(context, files, label='Location Services Clients')
    for path in kept:
        clients = load_plist(path)
        if not isinstance(clients, dict):
            logfunc('Location Services Clients: '
                    f'{context.get_relative_path(path)} is not a plist dictionary')
            continue
        for key, entry in clients.items():
            if isinstance(entry, dict):
                data_list.append(client_row(str(key), entry))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
