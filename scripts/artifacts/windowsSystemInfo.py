"""Windows system information and network interfaces from the registry, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsSystemInfo": {
        "name": "Windows System Information",
        "description": "Operating system product name and build, the InstallDate and "
                       "InstallTime values, computer and host name, time zone, last shutdown "
                       "time, last logged-on user and automatic logon values, read from the "
                       "SOFTWARE and SYSTEM hives.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the SOFTWARE hive's Microsoft\\Windows NT\\CurrentVersion and Winlogon keys and "
                 "its Microsoft\\Windows\\CurrentVersion\\Authentication\\LogonUI key, and the SYSTEM "
                 "hive's control set named by the Select key's Current value, or ControlSet001 when "
                 "there is none. A SOFTWARE and a SYSTEM hive in the same config folder are read "
                 "together, and a property with no value is left out. Key Last Written is the time the"
                 " key holding the value was last written, which is not necessarily when that value "
                 "was set. Product Name is reported as stored: pc_mus_001_win11 has CurrentBuild "
                 "22621, which Microsoft lists as Windows 11 version 22H2, and a ProductName beginning"
                 " Windows 10, so Build is the value that identifies the release. InstallDate is read "
                 "as seconds since 1970 and InstallTime as a FILETIME; on the three registered Windows"
                 " images they agreed to within a second. What event they record is not established: "
                 "on pc_mus_001_win11 the user's FeatureUsage KeyCreationTime is 51 hours earlier than"
                 " InstallDate, and on lonewolf_win10 the OneDrive ClientFirstSignInTimestamp is 2.4 "
                 "hours earlier. Default Password is the Winlogon DefaultPassword value, which "
                 "Microsoft documents as stored in the registry in plain text when automatic logon is "
                 "turned on; af_case2_win10 has AutoAdminLogon 1 and a DefaultPassword value. Time "
                 "Zone Bias and Active Time Bias are read as signed minutes. Microsoft defines a time "
                 "zone bias by UTC = local time + bias, and the registered images fit it: Bias 300 "
                 "with Eastern Standard Time on pc_mus_001_win11 and lonewolf_win10, and 480 with "
                 "Pacific Standard Time on af_case2_win10. Last Shutdown is the ShutdownTime value "
                 "under Control\\Windows read as a FILETIME. Checked against the System event log, it "
                 "lies within 0.2 seconds of the latest Kernel-General event 13 on pc_mus_001_win11 "
                 "and lonewolf_win10, and 2.0 seconds after the latest EventLog event 6006 on "
                 "af_case2_win10, whose log has no event 13 for that shutdown. Reference: Microsoft, "
                 "'Configure Windows to automate logon', "
                 "https://learn.microsoft.com/en-us/troubleshoot/windows-server/user-profiles-and-logon/turn-on-automatic-logon."
                 " Reference: Microsoft, 'TIME_ZONE_INFORMATION (timezoneapi.h)', "
                 "https://learn.microsoft.com/en-us/windows/win32/api/timezoneapi/ns-timezoneapi-time_zone_information."
                 " Reference: Microsoft, 'Windows 11 - release information', "
                 "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information.",
        "paths": (
            '*/Windows/System32/config/SOFTWARE',
            '*/Windows/System32/config/SYSTEM',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 17 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 21 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 16 rows",
        },
    },
    "windowsNetworkInterfaces": {
        "name": "Windows Network Interfaces",
        "description": "TCP/IP settings of each network interface that holds an address, "
                       "static or leased by DHCP, with the adapter's connection name, read "
                       "from the SYSTEM hive.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the Services\\Tcpip\\Parameters\\Interfaces subkeys of the SYSTEM hive's control "
                 "set named by the Select key's Current value (ControlSet001 when there is none), and "
                 "reports an interface only when it holds a DhcpIPAddress or an IPAddress value. For a"
                 " DHCP interface the address, mask, gateway and name servers come from the "
                 "Dhcp-prefixed values; Domain is DhcpDomain, or Domain when that is empty. Adapter "
                 "Name is the Connection\\Name value for the interface GUID under the network adapter "
                 "class key {4D36E972-E325-11CE-BFC1-08002BE10318}. Lease Obtained and Lease "
                 "Terminates are LeaseObtainedTime and LeaseTerminatesTime read as seconds since 1970 "
                 "UTC. On pc_mus_001_win11 the decoded Lease Obtained is 0.5 seconds before the "
                 "interface key was last written, and on all three registered Windows images "
                 "LeaseTerminatesTime minus LeaseObtainedTime equals the Lease value. On "
                 "af_case2_win10 and lonewolf_win10 LeaseObtainedTime holds 4 and 812456, which decode"
                 " to January 1970, decades before the interface key was last written; why is not "
                 "established, and those rows show 1970 lease times that are not when the lease was "
                 "obtained. For that reason this artifact is not written to the timeline. On "
                 "pc_mus_001_win11 Default Gateway, DHCP Server and DNS Servers are identical on both "
                 "rows: empty on the interface with a static address, and one address on the DHCP "
                 "interface, each read from its own registry value. af_case2_win10's DHCP interface "
                 "has no DhcpDefaultGateway value, so Default Gateway is empty there.",
        "paths": ('*/Windows/System32/config/SYSTEM',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, current_control_set, filetime_bytes_utc,
                                      filetime_utc, found_hives, key_written_utc, open_key,
                                      signed32, unix_utc, value_of)

_CURRENT_VERSION = r'Microsoft\Windows NT\CurrentVersion'
_LOGON_UI = r'Microsoft\Windows\CurrentVersion\Authentication\LogonUI'
_WINLOGON = r'Microsoft\Windows NT\CurrentVersion\Winlogon'
_NETWORK_CLASS = r'Control\Network\{4D36E972-E325-11CE-BFC1-08002BE10318}'


def _text(value):
    if value is None:
        return None
    if isinstance(value, list):
        return ', '.join(str(v) for v in value if v not in (None, ''))
    return str(value)


def _stamp(value):
    return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'strftime') else ''


def _software_rows(reg):
    """(property, value, key path, key) rows from the SOFTWARE hive."""
    rows = []
    cv = open_key(reg, _CURRENT_VERSION)
    for prop, name in (('Product Name (as stored)', 'ProductName'), ('Edition', 'EditionID'),
                       ('Display Version', 'DisplayVersion'), ('Release Id', 'ReleaseId')):
        rows.append((prop, _text(value_of(cv, name)), _CURRENT_VERSION + '\\' + name, cv))
    build, ubr = value_of(cv, 'CurrentBuild'), value_of(cv, 'UBR')
    if build is not None:
        rows.append(('Build', f'{build}.{ubr}' if ubr is not None else str(build),
                     _CURRENT_VERSION + '\\CurrentBuild, UBR', cv))
    rows.append(('Install Date (UTC)', _stamp(unix_utc(value_of(cv, 'InstallDate'))),
                 _CURRENT_VERSION + '\\InstallDate', cv))
    rows.append(('Install Time (UTC)', _stamp(filetime_utc(value_of(cv, 'InstallTime'))),
                 _CURRENT_VERSION + '\\InstallTime', cv))
    for prop, name in (('Registered Owner', 'RegisteredOwner'),
                       ('Registered Organization', 'RegisteredOrganization')):
        rows.append((prop, _text(value_of(cv, name)), _CURRENT_VERSION + '\\' + name, cv))
    logon_ui = open_key(reg, _LOGON_UI)
    for prop, name in (('Last Logged On User', 'LastLoggedOnUser'),
                       ('Last Logged On SAM User', 'LastLoggedOnSAMUser'),
                       ('Last Logged On Display Name', 'LastLoggedOnDisplayName'),
                       ('Last Logged On User SID', 'LastLoggedOnUserSID')):
        rows.append((prop, _text(value_of(logon_ui, name)), _LOGON_UI + '\\' + name, logon_ui))
    winlogon = open_key(reg, _WINLOGON)
    for prop, name in (('Automatic Logon (AutoAdminLogon)', 'AutoAdminLogon'),
                       ('Default User Name', 'DefaultUserName'),
                       ('Default Domain Name', 'DefaultDomainName'),
                       ('Default Password', 'DefaultPassword')):
        rows.append((prop, _text(value_of(winlogon, name)), _WINLOGON + '\\' + name, winlogon))
    return rows


def _system_rows(reg):
    """(property, value, key path, key) rows from the SYSTEM hive."""
    rows = []
    cs = current_control_set(reg)
    names = open_key(reg, cs + r'\Control\ComputerName\ComputerName')
    rows.append(('Computer Name', _text(value_of(names, 'ComputerName')),
                 cs + r'\Control\ComputerName\ComputerName\ComputerName', names))
    tcpip = open_key(reg, cs + r'\Services\Tcpip\Parameters')
    for prop, name in (('Host Name', 'Hostname'), ('Domain', 'Domain')):
        rows.append((prop, _text(value_of(tcpip, name)),
                     cs + r'\Services\Tcpip\Parameters' + '\\' + name, tcpip))
    tz = open_key(reg, cs + r'\Control\TimeZoneInformation')
    rows.append(('Time Zone', _text(value_of(tz, 'TimeZoneKeyName')),
                 cs + r'\Control\TimeZoneInformation\TimeZoneKeyName', tz))
    for prop, name in (('Time Zone Bias (minutes)', 'Bias'),
                       ('Active Time Bias (minutes)', 'ActiveTimeBias')):
        rows.append((prop, _text(signed32(value_of(tz, name))),
                     cs + r'\Control\TimeZoneInformation' + '\\' + name, tz))
    win = open_key(reg, cs + r'\Control\Windows')
    shutdown = value_of(win, 'ShutdownTime')
    rows.append(('Last Shutdown (UTC)', _stamp(filetime_bytes_utc(shutdown)),
                 cs + r'\Control\Windows\ShutdownTime', win))
    return rows


def _config_dirs(context):
    """{config folder: {'SOFTWARE': path, 'SYSTEM': path}} for every hive found."""
    dirs = {}
    for hive in found_hives(context, 'SOFTWARE', 'SYSTEM'):
        dirs.setdefault(os.path.dirname(hive), {})[os.path.basename(hive).upper()] = hive
    return dirs


@artifact_processor
def windowsSystemInfo(context):
    data_headers = ('Property', 'Value', ('Key Last Written (UTC)', 'datetime'),
                    'Registry Value', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Windows System Information: the python-registry package is not installed')
        return data_headers, data_list, ''
    for _folder, hives in sorted(_config_dirs(context).items()):
        for kind, reader in (('SOFTWARE', _software_rows), ('SYSTEM', _system_rows)):
            path = hives.get(kind)
            if not path:
                continue
            try:
                rows = reader(Registry.Registry(path))
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logfunc(f'Windows System Information: could not read '
                        f'{context.get_relative_path(path)}: {exc}')
                continue
            relative = context.get_relative_path(path)
            kept = [(prop, value, key_written_utc(key), where, relative)
                    for prop, value, where, key in rows if value not in (None, '')]
            data_list.extend(kept)
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


def _adapter_name(reg, cs, guid):
    return _text(value_of(open_key(reg, f'{cs}\\{_NETWORK_CLASS}\\{guid}\\Connection'), 'Name')) or ''


@artifact_processor
def windowsNetworkInterfaces(context):
    data_headers = (('Lease Obtained (UTC)', 'datetime'), ('Lease Terminates (UTC)', 'datetime'),
                    'Adapter Name', 'DHCP Enabled', 'IP Address', 'Subnet Mask',
                    'Default Gateway', 'DHCP Server', 'DNS Servers', 'Domain',
                    ('Key Last Written (UTC)', 'datetime'), 'Interface GUID')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Windows Network Interfaces: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'SYSTEM'):
        relative = context.get_relative_path(path)
        try:
            reg = Registry.Registry(path)
            cs = current_control_set(reg)
            interfaces = open_key(reg, cs + r'\Services\Tcpip\Parameters\Interfaces')
            for iface in (interfaces.subkeys() if interfaces else []):
                dhcp_ip = value_of(iface, 'DhcpIPAddress')
                static_ip = value_of(iface, 'IPAddress')
                if not (dhcp_ip or _text(static_ip)):
                    continue
                dhcp = value_of(iface, 'EnableDHCP')
                data_list.append((
                    unix_utc(value_of(iface, 'LeaseObtainedTime')) if dhcp_ip else '',
                    unix_utc(value_of(iface, 'LeaseTerminatesTime')) if dhcp_ip else '',
                    _adapter_name(reg, cs, iface.name()),
                    {1: 'Yes', 0: 'No'}.get(dhcp, _text(dhcp) or ''),
                    (_text(dhcp_ip) if dhcp_ip else _text(static_ip)) or '',
                    _text(value_of(iface, 'DhcpSubnetMask') if dhcp_ip else value_of(iface, 'SubnetMask')) or '',
                    _text(value_of(iface, 'DhcpDefaultGateway') if dhcp_ip else value_of(iface, 'DefaultGateway')) or '',
                    _text(value_of(iface, 'DhcpServer')) or '',
                    _text(value_of(iface, 'DhcpNameServer') if dhcp_ip else value_of(iface, 'NameServer')) or '',
                    _text(value_of(iface, 'DhcpDomain') or value_of(iface, 'Domain')) or '',
                    key_written_utc(iface),
                    iface.name(),
                ))
            sources.append(path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Network Interfaces: could not read {relative}: {exc}')
    return data_headers, data_list, '\n'.join(sources)
