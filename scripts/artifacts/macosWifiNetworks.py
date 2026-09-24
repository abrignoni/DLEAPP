"""Known Wi-Fi networks on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosKnownWifiNetworks": {
        "name": "Known Wi-Fi Networks",
        "description": "Networks in /Library/Preferences/com.apple.wifi.known-networks.plist, "
                       "with the SSID, the stored add, join, discovery and update dates, the "
                       "security types and the BSSIDs recorded for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": "Reads /Library/Preferences/com.apple.wifi.known-networks.plist, one row per "
                 "top-level entry; the entries are keyed wifi.network.ssid. followed by the "
                 "SSID, and SSID is the entry's SSID value decoded as UTF-8, or the text after "
                 "wifi.network.ssid. in the key when that value is not stored as data. The six "
                 "dates are the entry's "
                 "AddedAt, JoinedByUserAt, JoinedBySystemAt, LastDiscoveredAt, UpdatedAt and "
                 "LastDisconnectTimestamp values as stored; what event each records beyond its name is"
                 " not established. BSSIDs lists each BSSList entry's BSSID, channel and "
                 "LastAssociatedAt. com.apple.airport.preferences.plist is not read. On the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) the file "
                 "holds 5 networks: all 5 have AddedAt and JoinedByUserAt, 4 have the other four "
                 "dates, and 4 carry 10 BSSList entries between them; Hidden holds one value, No, on "
                 "all 5 rows. dleapp_macos_bigsur has no com.apple.wifi.known-networks.plist, and its "
                 "com.apple.airport.preferences.plist holds no KnownNetworks key. When a logical "
                 "extraction holds the file under Library/Preferences/ and again under "
                 "System/Volumes/Data/Library/Preferences/, a second copy byte-identical to the "
                 "first is not read again, and is counted in the run log.",
        "paths": ('*/Library/Preferences/com.apple.wifi.known-networks.plist',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "wifi",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (no com.apple.wifi.known-networks.plist)",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources


def _text(value):
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return '' if value is None else str(value)


def _ssid(key, network):
    raw = network.get('SSID')
    if isinstance(raw, bytes):
        return raw.decode('utf-8', 'replace')
    return str(key).split('wifi.network.ssid.', 1)[-1]


def _bss(network):
    entries = []
    for bss in network.get('BSSList') or []:
        if isinstance(bss, dict):
            seen = as_utc(bss.get('LastAssociatedAt'))
            when = seen.strftime('%Y-%m-%d %H:%M:%S') + ' UTC' if seen else ''
            entries.append(f"{_text(bss.get('BSSID'))} (channel {_text(bss.get('Channel'))}"
                           f"{', last associated ' + when if when else ''})")
    return '; '.join(entries)


@artifact_processor
def macosKnownWifiNetworks(context):
    data_headers = (('Added At (UTC)', 'datetime'), ('Joined By User At (UTC)', 'datetime'),
                    ('Joined By System At (UTC)', 'datetime'), ('Last Discovered At (UTC)', 'datetime'),
                    ('Updated At (UTC)', 'datetime'), ('Last Disconnect (UTC)', 'datetime'),
                    'SSID', 'Security Types', 'Hidden', 'Add Reason', 'BSSIDs',
                    'Cached Private MAC Address', 'Source File')
    data_list = []
    read = []
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Known Wi-Fi Networks')
    for path in paths:
        relative = context.get_relative_path(path)
        plist = load_plist(path)
        if not isinstance(plist, dict):
            logfunc(f'Known Wi-Fi Networks: could not read {relative}')
            continue
        read.append(path)
        for key, network in plist.items():
            if not isinstance(network, dict):
                continue
            data_list.append((as_utc(network.get('AddedAt')), as_utc(network.get('JoinedByUserAt')),
                              as_utc(network.get('JoinedBySystemAt')),
                              as_utc(network.get('LastDiscoveredAt')), as_utc(network.get('UpdatedAt')),
                              as_utc(network.get('LastDisconnectTimestamp')), _ssid(key, network),
                              _text(network.get('SupportedSecurityTypes')), _text(network.get('Hidden')),
                              _text(network.get('AddReason')), _bss(network),
                              _text(network.get('CachedPrivateMACAddress')), relative))
    return data_headers, data_list, '\n'.join(read)
