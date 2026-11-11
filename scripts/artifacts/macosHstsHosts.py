__artifacts_v2__ = {
    "macosHstsHosts": {
        "name": "macOS HSTS Hosts",
        "description": "Hosts recorded in the HSTS.plist files of Safari and other macOS apps.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": (
            "Reads HSTS.plist in a Library/Cookies folder and in the folders under Library/Caches, including "
            "those inside app containers: the host names recorded under each storage session key, with the "
            "entry's Create Time, Expiry, Include Subdomains and HSTS Host values. Create Time, Expiry, Include "
            "Subdomains and HSTS Host are the plist's own key names. Host is the entry's dictionary key and "
            "Storage Session is the top-level key. Create Time and Expiry are stored as numbers and are read as "
            "seconds since 2001-01-01 UTC; read that way the Create Time values on the five tested images are "
            "dates between 2020-12 and 2026-02. That reading comes from the values, not from Apple documentation, "
            "and what event sets Create Time is not established. A row shows that the host is recorded in that "
            "HSTS.plist; it does not show a page visit by itself. An Expiry stored as infinity cannot be shown as "
            "a date, so Expiry is blank and Expiry Stored As Infinity is true: 706 of the 708 hosts in "
            "Library/Cookies/HSTS.plist on magnet2021_macos_bigsur were stored that way and their Create Time "
            "values all fall within one second, and the Expiry Stored As Infinity column was empty on the other "
            "four images. HSTS Host held true on every row but one, where the key was absent. Storage Session "
            "held com.apple.CFNetwork.defaultStorageSession on every row. The folder in Source File (a container "
            "folder, a folder under Caches, or Cookies) is the only record of which app's file a row came from. "
            "Top-level keys that are not dictionaries (a schema version, a content version and a preload entries "
            "signature on the macOS 11.2.1 images) are not reported. User is the folder after Users in the path, "
            "root under private/var/root, otherwise blank. User held one value on every row of each tested image; "
            "every file read sat under one user's folder. When a logical extraction holds the same file under "
            "Users/ and under System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical "
            "copy is not read again and the run log counts it, and a row that copies with different bytes both "
            "hold is reported once with every file that held it in Source File. "
        ),
        "paths": ('*/Library/Cookies/HSTS.plist', '*/Library/Caches/*/HSTS.plist'),
        "output_types": "standard",
        "artifact_icon": "lock",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 714 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 15 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 6 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 43 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 127 rows",
        },
    }
}

import math
import os

from scripts.ilapfuncs import artifact_processor
from scripts.macos_plists import fold_view_rows, load_plist, mac_absolute_utc, unique_sources, user_from_path


def _moment(value):
    """A finite number read as seconds since 2001-01-01 UTC, or ''."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return ''
    return mac_absolute_utc(value)


def _flag(entry, key):
    value = entry.get(key)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return '' if value is None else str(value)


@artifact_processor
def macosHstsHosts(context):
    data_headers = (('Create Time', 'datetime'), ('Expiry', 'datetime'), 'Host', 'Include Subdomains',
                    'HSTS Host', 'Expiry Stored As Infinity', 'Storage Session', 'User', 'Source File')
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'HSTS.plist']
    paths, _skipped = unique_sources(context, found, label='macOS HSTS Hosts')
    rows, read = [], []
    for path in paths:
        plist = load_plist(path)
        if not isinstance(plist, dict):
            continue
        relative = context.get_relative_path(path)
        read.append(path)
        user = user_from_path(relative)
        for session in sorted(plist):
            hosts = plist[session]
            if not isinstance(hosts, dict):
                continue
            for host in sorted(hosts):
                entry = hosts[host]
                if not isinstance(entry, dict):
                    continue
                expiry = entry.get('Expiry')
                infinite = 'true' if isinstance(expiry, float) and math.isinf(expiry) else ''
                rows.append((_moment(entry.get('Create Time')), _moment(expiry), host,
                             _flag(entry, 'Include Subdomains'), _flag(entry, 'HSTS Host'), infinite, session,
                             user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
