"""Windows mapped network drive parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads two keys of each user's NTUSER.DAT. Network holds one subkey per
remembered drive, named for the drive letter, with the share it points at.
Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Map Network Drive MRU
holds the share paths entered in Explorer's Map Network Drive dialog, with
their order.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive,
                                      open_key, user_from_path)

_DRIVES_LABEL = 'Mapped Network Drives'
_MRU_LABEL = 'Map Network Drive MRU'
_NETWORK = 'Network'
_MRU = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Map Network Drive MRU'
_DRIVE_VALUES = ('RemotePath', 'UserName', 'ProviderName', 'ProviderType', 'ConnectionType',
                 'DeferFlags', 'ConnectFlags')

__artifacts_v2__ = {
    "mappedNetworkDrives": {
        "name": "Mapped Network Drives",
        "description": "Subkeys of the Network key of each user's NTUSER.DAT, each with its name, the share its "
                       "RemotePath value gives and its other values as stored, the user and two last written times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from each user's NTUSER.DAT, named in the report's located-at line. Each subkey of the "
                 "Network key at the root of the hive is one row. Drive is the subkey's name. Remote Path, User "
                 "Name, Provider Name, Provider Type, Connection Type, Defer Flags and Connect Flags are the "
                 "subkey's RemotePath, UserName, ProviderName, ProviderType, ConnectionType, DeferFlags and "
                 "ConnectFlags values, as stored; a column is blank when the subkey has no such value or its data is "
                 "neither text nor a number. User is the folder after Users in the hive's path. Key Last Written "
                 "(UTC) is the subkey's last-written time and Network Key Last Written (UTC) is that of the Network "
                 "key above it, the same on the rows of one hive. RECmd's DFIR batch file reads the RemotePath, "
                 "UserName and ProviderName values below this key as 'Network Shares': the UNC path, the user "
                 "account and the provider of a mounted network share (Andrew Rathbun, 'DFIR RECmd Batch File', "
                 "https://github.com/EricZimmerman/RECmd/blob/bcd0ac33ed98de61ea6de551eef96052bddbbd49/BatchExamples/DFIRBatch.reb#L1640-L1688). "
                 "plaso's network_drives plugin reads the same subkeys as a drive letter with the server and share "
                 "of RemotePath (log2timeline, 'network_drives.py', "
                 "https://github.com/log2timeline/plaso/blob/31ce90b720f0260e2f5a9045fcb814f31e9aa285/plaso/parsers/winreg_plugins/network_drives.py#L38-L71). "
                 "Microsoft documents that a connection made with the CONNECT_UPDATE_PROFILE flag is remembered, "
                 "that the operating system then tries to restore it when the user logs on, and that only successful "
                 "connections that redirect a local device are remembered (Microsoft, 'WNetAddConnection2W "
                 "function', "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/winnetwk/nf-winnetwk-wnetaddconnection2w.md#L188-L202); "
                 "no Microsoft source naming this key as the place they are kept was found. The 12 NTUSER.DAT files "
                 "of the five tested inputs, the Default profile's among them, include 10 with a Network key, and "
                 "one of those, on szechuan_win10, has a subkey: 1 row. The other four inputs give no rows. On that "
                 "row Drive is one letter, Remote Path is a UNC path of a server and a share, Provider Name is "
                 "Microsoft Windows Network, User Name is the number 0, stored as a DWORD, and Provider Type, "
                 "Connection Type, Defer Flags and Connect Flags are 131072, 1, 4 and 0. No source for what those "
                 "numbers mean was found, so they are reported as stored. The subkey also holds a binary UseOptions "
                 "value, 124 bytes beginning DefC, which is not reported. The two times of that row differ. Network "
                 "Key Last Written (UTC) is 0.012 second before the last-written time of the same hive's Map Network "
                 "Drive MRU key and 0.074 second before that of the MountPoints2 key named for the same share (see "
                 "Map Network Drive MRU and MountPoints2), inside a session of the user that began 75 seconds "
                 "earlier and ended 29 seconds later (Winlogon events 7001 and 7002, see Winlogon Logon and Logoff "
                 "Notifications; the user's SID is from User Profile List). Key Last Written (UTC) is 443 seconds "
                 "after it: 0.10 second after the user's next interactive logon (Security event 4624, logon type 2, "
                 "see Windows Security Logons) and 0.09 second after that logon's Winlogon 7001. The user's later "
                 "logon, 6.3 hours on and of type 11 (CachedInteractive), is after Key Last Written (UTC), and the "
                 "hive as read holds a MountPoints2 key written 44 seconds after that logon, so the hive shows no "
                 "write to the subkey at that logon. On the one tested drive, then, the subkey's time is that of a "
                 "later logon, and the Network key's time is the one that matches the share's other keys. What the "
                 "logon wrote in the subkey was not established, and one drive cannot show whether other hives "
                 "behave the same. Not established either: what unmapping a drive leaves in the key. A row records "
                 "that the user's hive holds a subkey for the share under Network; it does not show that the share "
                 "was reachable or that a file on it was opened. Reading the hive needs the python-registry package. "
                 "A dirty hive, one whose base block's two sequence numbers differ, is read after the entries in its "
                 ".LOG1 and .LOG2 transaction logs that continue its sequence are applied, following Maxim Suhanov's "
                 "'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
    "mapNetworkDriveMru": {
        "name": "Map Network Drive MRU",
        "description": "Text values of the Map Network Drive MRU key of each user's NTUSER.DAT, in the order its "
                       "MRUList value gives, with the user and the key's last written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from each user's NTUSER.DAT, named in the report's located-at line. Each text value of "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Map Network Drive MRU other than MRUList is one "
                 "row: Value is its name and Share its data, as stored. Order is the position of the value's name in "
                 "the MRUList value, 1 for the first. libyal's Windows Registry knowledge base lists this key among "
                 "those with a MRUList value and describes MRUList as the value names in order of use, the most "
                 "recently used first (libyal, 'Most recently used (MRU)', "
                 "https://github.com/libyal/winreg-kb/blob/d572cf86269bd3aa393f5eb73932aec181283838/docs/sources/explorer-keys/Most-recently-used.md#L11-L18, "
                 "https://github.com/libyal/winreg-kb/blob/d572cf86269bd3aa393f5eb73932aec181283838/docs/sources/explorer-keys/Most-recently-used.md#L34). "
                 "A value MRUList does not name has a blank Order and follows the named ones; a name in MRUList that "
                 "the key holds no value for gives no row and is counted in the run log, and a name MRUList repeats "
                 "is used once. User is the folder after Users in the hive's path. Key Last Written (UTC) is the "
                 "key's last-written time, the same on the rows of one hive, so no row has a time of its own. "
                 "RECmd's DFIR batch file reads the key as 'Network Drive MRU', with the comment 'Displays drives "
                 "that were mapped by the user' (Andrew Rathbun, 'DFIR RECmd Batch File', "
                 "https://github.com/EricZimmerman/RECmd/blob/bcd0ac33ed98de61ea6de551eef96052bddbbd49/BatchExamples/DFIRBatch.reb#L1693-L1698). "
                 "What adds a value to the key was not tested here: no known data was made for it. Of the 12 "
                 "NTUSER.DAT files of the five tested inputs, the Default profile's among them, one, on "
                 "szechuan_win10, holds the key: 1 row, with Order 1. The other four inputs give no rows. On that "
                 "hive Share equals the Remote Path of the user's one row in Mapped Network Drives and the share "
                 "path of the user's network share row in MountPoints2, and Key Last Written (UTC) is 0.012 second "
                 "after the last-written time of the hive's Network key and 0.062 second before that of the "
                 "MountPoints2 key (see Mapped Network Drives and MountPoints2). The order of several values, a "
                 "blank Order, a name with no value and a repeated name were exercised only by constructed keys in "
                 "the unit tests. A row records that the hive lists the share in this key; it does not show that a "
                 "connection was made or that a file on the share was opened. Reading the hive needs the "
                 "python-registry package. A dirty hive, one whose base block's two sequence numbers differ, is read "
                 "after the entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are applied, "
                 "following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def _stored(key):
    """The data of a drive key's reported values, by value name without case; bytes are left out."""
    wanted = {name.lower(): name for name in _DRIVE_VALUES}
    found = {}
    for value in key.values():
        name = wanted.get(value.name().lower())
        if name is None:
            continue
        data = value.value()
        if isinstance(data, (str, int)):
            found[name] = data
    return found


def drive_rows(network, user):
    """One row per subkey of a Network key.

    Each row holds the subkey's last written time, the Network key's own, the user, the subkey's
    name and its values as stored.
    """
    network_written = key_written_utc(network)
    rows = []
    for drive in network.subkeys():
        stored = _stored(drive)
        rows.append((key_written_utc(drive), network_written, user, drive.name())
                    + tuple(stored.get(name, '') for name in _DRIVE_VALUES))
    return rows


def mru_rows(key, user):
    """One row per share value of a Map Network Drive MRU key, in the order MRUList gives.

    Returns (rows, value names MRUList lists that the key does not hold). A value MRUList does
    not list has a blank Order and follows the listed ones; a name MRUList repeats is used once.
    """
    written = key_written_utc(key)
    order, shares = '', {}
    for value in key.values():
        data = value.value()
        if value.name().lower() == 'mrulist':
            order = data if isinstance(data, str) else ''
        elif isinstance(data, str):
            shares[value.name()] = data
    rows, missing, listed = [], [], set()
    for position, name in enumerate(order, 1):
        if name in shares:
            rows.append((written, user, position, name, shares.pop(name)))
        elif name not in listed:
            missing.append(name)
        listed.add(name)
    rows.extend((written, user, '', name, share) for name, share in shares.items())
    return rows, missing


def _read(context, label, key_path, build):
    """Rows from one key of every found NTUSER.DAT; build(key, user, relative path) gives a hive's rows."""
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{label}: the python-registry package is not installed')
        return data_list, ''
    for source in found_hives(context, 'NTUSER.DAT'):
        relative_source = context.get_relative_path(source)
        try:
            key = open_key(open_hive(source, context), key_path)
            rows = [] if key is None else build(key, user_from_path(relative_source), relative_source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        data_list.extend(rows)
    return data_list, '\n'.join(sources)


@artifact_processor
def mappedNetworkDrives(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), ('Network Key Last Written (UTC)', 'datetime'), 'User',
                    'Drive', 'Remote Path', 'User Name', 'Provider Name', 'Provider Type', 'Connection Type',
                    'Defer Flags', 'Connect Flags')
    data_list, sources = _read(context, _DRIVES_LABEL, _NETWORK, lambda key, user, _relative: drive_rows(key, user))
    return data_headers, data_list, sources


@artifact_processor
def mapNetworkDriveMru(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'Order', 'Value', 'Share')

    def build(key, user, relative):
        rows, missing = mru_rows(key, user)
        if missing:
            logfunc(f'{_MRU_LABEL}: MRUList of {relative} lists {len(missing)} value name(s) the key does not hold')
        return rows

    data_list, sources = _read(context, _MRU_LABEL, _MRU, build)
    return data_headers, data_list, sources
