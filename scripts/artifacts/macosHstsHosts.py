__artifacts_v2__ = {
    "macosHstsHosts": {
        "name": "HSTS Hosts",
        "description": "Hosts recorded in the HSTS.plist files of Safari and other macOS apps.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Network",
        "notes": (
            "Reads every HSTS.plist under a user's Library/Cookies and Library/Caches folders, including app "
            "containers: the host names recorded under each storage session key, with the entry's Create Time, "
            "Expiry, Include Subdomains and HSTS Host values. The column names are the plist's own key names. "
            "Create Time and Expiry are stored as numbers and are read as seconds since 2001-01-01 UTC; read that way the Create Time values on the five tested images are dates between 2020-12 and 2026-02. That reading comes from the values, not from Apple documentation, and what event sets Create Time is not "
            "established. A row shows that the app's network storage recorded an HSTS policy for the host; it "
            "does not show a page visit by itself. An Expiry stored as infinity cannot be shown as a date, so "
            "Expiry is blank and Expiry Stored As Infinity is true: 706 of the 708 hosts in "
            "Library/Cookies/HSTS.plist on magnet2021_macos_bigsur were stored that way, all created within the "
            "same second, and the Expiry Stored As Infinity column was empty on the other four images. HSTS Host "
            "held true on every row but one, where the key was absent. Storage Session held "
            "com.apple.CFNetwork.defaultStorageSession on every row. App Folder is the container folder, or the "
            "folder under Caches, or Cookies. Top-level keys that are not dictionaries (schema and content "
            "versions) are not reported. User is the folder after Users in the path, root under private/var/root, "
            "otherwise blank; it held one value on every row of each tested image, which each hold one user's "
            "Safari data. When a logical extraction holds the same file under Users/ and under "
            "System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical copy is not read "
            "again and the run log counts it, and a row that copies with different bytes both hold is reported "
            "once with every file that held it in Source File. "
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


def _store_folder(relative):
    """The folders between Library and HSTS.plist, which name the app that owns the file."""
    parts = str(relative).replace('\\', '/').split('/')
    owner = ''
    for index, part in enumerate(parts[:-1]):
        if part == 'Containers' and index + 1 < len(parts) - 1:
            return parts[index + 1]
        if part == 'Caches' and index + 1 < len(parts) - 1:
            owner = parts[index + 1]
        if part == 'Cookies':
            owner = 'Cookies'
    return owner


@artifact_processor
def macosHstsHosts(context):
    data_headers = (('Create Time', 'datetime'), ('Expiry', 'datetime'), 'Host', 'Include Subdomains',
                    'HSTS Host', 'Expiry Stored As Infinity', 'Storage Session', 'App Folder', 'User', 'Source File')
    found = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'HSTS.plist']
    paths, _skipped = unique_sources(context, found, label='HSTS Hosts')
    rows, read = [], []
    for path in paths:
        plist = load_plist(path)
        if not isinstance(plist, dict):
            continue
        relative = context.get_relative_path(path)
        read.append(path)
        user = user_from_path(relative)
        folder = _store_folder(relative)
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
                             folder, user, relative))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
