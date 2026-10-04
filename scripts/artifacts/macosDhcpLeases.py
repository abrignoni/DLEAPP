"""DHCP leases the macOS DHCP client stores, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The client keeps one plist per interface in /private/var/db/dhcpclient/leases. Its keys
and the way it writes them are in Apple's bootp source (DHCPLease.c); PacketData holds a
DHCP message, read here by RFC 2131 and RFC 2132.
"""

__artifacts_v2__ = {
    "macosDhcpLeases": {
        "name": "DHCP Leases",
        "description": "DHCP leases the macOS DHCP client stores in its lease file for each "
                       "interface, with the address, lease start and length, router, Wi-Fi "
                       "network, and the DHCP server, DNS servers and domain name from the stored "
                       "DHCP message.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": "Reads each plist in private/var/db/dhcpclient/leases, one row per file; a file "
                 "that is not a plist dictionary is logged and skipped. Apple's DHCP client names "
                 "each file after its interface and writes to it only the last lease in its list "
                 "for that interface (bootp-534.120.2, DHCPLease.c, "
                 "https://github.com/apple-oss-distributions/bootp/blob/25029796948a368f40ded4f5a47a7945c13c4621/IPConfiguration.bproj/DHCPLease.c#L427-L433 "
                 "and "
                 "https://github.com/apple-oss-distributions/bootp/blob/25029796948a368f40ded4f5a47a7945c13c4621/IPConfiguration.bproj/DHCPLease.c#L536-L542), "
                 "with the keys defined at "
                 "https://github.com/apple-oss-distributions/bootp/blob/25029796948a368f40ded4f5a47a7945c13c4621/IPConfiguration.bproj/DHCPLease.c#L49-L62, "
                 "where SSID and NetworkID are marked Wi-Fi only. Interface is the file name "
                 "without .plist. Lease Start (UTC), IP Address, Lease Length (seconds), Router IP "
                 "Address, SSID and Network ID are LeaseStartDate, IPAddress, LeaseLength, "
                 "RouterIPAddress, SSID and NetworkID as stored, Router Hardware Address is "
                 "RouterHardwareAddress in colon-separated hex, and Client Identifier (hex) is "
                 "ClientIdentifier in hex. Lease End (UTC) is Lease Start plus Lease Length, the "
                 "point from which the client's own check treats the lease as expired "
                 "(https://github.com/apple-oss-distributions/bootp/blob/25029796948a368f40ded4f5a47a7945c13c4621/IPConfiguration.bproj/DHCPLease.c#L469-L472). "
                 "It is blank for a length of 0xFFFFFFFF, which RFC 2131 reserves for infinity "
                 "(section 3.3, https://www.rfc-editor.org/rfc/rfc2131#section-3.3). PacketData is "
                 "a DHCP message: 236 bytes of fixed fields, then the options field, which begins "
                 "with the magic cookie 99, 130, 83, 99 followed by tagged options (RFC 2131 "
                 "sections 2 and 3, https://www.rfc-editor.org/rfc/rfc2131#section-2, "
                 "https://www.rfc-editor.org/rfc/rfc2131#section-3). DHCP Server, Subnet Mask, DNS "
                 "Servers, Domain Name and Message Type are options 54, 1, 6, 15 and 53 (RFC 2132 "
                 "sections 9.7, 3.3, 3.8, 3.17 and 9.6, https://www.rfc-editor.org/rfc/rfc2132), "
                 "with the message type named as section 9.6 names it. Repeated instances of one "
                 "option are joined, as RFC 3396 has a decoder do "
                 "(https://www.rfc-editor.org/rfc/rfc3396). Options carried in the message's file "
                 "or sname fields are not read, and other options are not reported. On all 3 "
                 "tested leases the message was a DHCPACK, and its option 51 lease time equalled "
                 "LeaseLength. When a logical extraction holds the leases folder under private/var "
                 "and again under System/Volumes/Data/private/var, a copy byte-identical to "
                 "another is read once and counted in the run log, and copies that differ each "
                 "give a row. The located-at line names every file read. dleapp_macos_bigsur held "
                 "one lease, for en0 with no SSID. On the public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15) the two copies of en0.plist differed "
                 "and gave 2 rows, with lease starts about 11 and a half hours apart, the later "
                 "one in the copy under System/Volumes/Data.",
        "paths": ('*/private/var/db/dhcpclient/leases/*.plist',),
        "output_types": ["standard"],
        "artifact_icon": "network",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
        },
    },
}

import ipaddress
import os
from datetime import timedelta

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, load_plist, unique_sources

_MAGIC_COOKIE = bytes((99, 130, 83, 99))
_OPTIONS_AT = 240          # 236 bytes of fixed fields, then the magic cookie
_INFINITE_LEASE = 0xFFFFFFFF
_MESSAGE_TYPES = {1: 'DHCPDISCOVER', 2: 'DHCPOFFER', 3: 'DHCPREQUEST', 4: 'DHCPDECLINE',
                  5: 'DHCPACK', 6: 'DHCPNAK', 7: 'DHCPRELEASE', 8: 'DHCPINFORM'}


def dhcp_options(packet):
    """{option code: value} from a DHCP message's options field, or {} when it has none.

    Repeated instances of one option are joined in order, as RFC 3396 has a decoder do.
    Reading stops at the end option, 255, or where an option runs past the message.
    """
    if not isinstance(packet, (bytes, bytearray)) or packet[236:240] != _MAGIC_COOKIE:
        return {}
    options, index = {}, _OPTIONS_AT
    while index < len(packet):
        code = packet[index]
        if code == 255:
            break
        if code == 0:
            index += 1
            continue
        if index + 1 >= len(packet):
            break
        length = packet[index + 1]
        value = bytes(packet[index + 2:index + 2 + length])
        if len(value) < length:
            break
        options[code] = options.get(code, b'') + value
        index += 2 + length
    return options


def ipv4_list(value):
    """Four-byte IPv4 addresses, ', '-joined, or '' when the length is not a multiple of 4."""
    if not value or len(value) % 4:
        return ''
    return ', '.join(str(ipaddress.IPv4Address(value[i:i + 4])) for i in range(0, len(value), 4))


def message_type(value):
    """An option 53 value as 'name (number)', the number alone for one RFC 2132 does not name."""
    if len(value or b'') != 1:
        return ''
    name = _MESSAGE_TYPES.get(value[0])
    return f'{name} ({value[0]})' if name else str(value[0])


def hardware_address(value):
    if isinstance(value, (bytes, bytearray)):
        return ':'.join(f'{byte:02x}' for byte in value)
    return '' if value is None else str(value)


def lease_row(lease, interface):
    """The report row for one lease plist."""
    options = dhcp_options(lease.get('PacketData'))
    start = as_utc(lease.get('LeaseStartDate'))
    length = lease.get('LeaseLength')
    end = ''
    if start and isinstance(length, int) and not isinstance(length, bool) \
            and 0 <= length < _INFINITE_LEASE:
        end = start + timedelta(seconds=length)
    client = lease.get('ClientIdentifier')
    domain = options.get(15, b'').rstrip(b'\x00').decode('ascii', 'replace')
    return (start, end, interface, lease.get('IPAddress', ''),
            length if isinstance(length, int) else '', lease.get('RouterIPAddress', ''),
            hardware_address(lease.get('RouterHardwareAddress')), lease.get('SSID', ''),
            lease.get('NetworkID', ''), ipv4_list(options.get(54)), ipv4_list(options.get(1)),
            ipv4_list(options.get(6)), domain, message_type(options.get(53)),
            client.hex() if isinstance(client, (bytes, bytearray)) else '')


@artifact_processor
def macosDhcpLeases(context):
    data_headers = (('Lease Start (UTC)', 'datetime'), ('Lease End (UTC)', 'datetime'),
                    'Interface', 'IP Address', 'Lease Length (seconds)', 'Router IP Address',
                    'Router Hardware Address', 'SSID', 'Network ID', 'DHCP Server',
                    'Subnet Mask', 'DNS Servers', 'Domain Name', 'Message Type',
                    'Client Identifier (hex)')
    data_list, sources = [], []
    files = [str(f) for f in context.get_files_found() if str(f).endswith('.plist')]
    kept, _skipped = unique_sources(context, files, label='DHCP Leases')
    for path in kept:
        lease = load_plist(path)
        if not isinstance(lease, dict):
            logfunc(f'DHCP Leases: {context.get_relative_path(path)} is not a plist dictionary')
            continue
        data_list.append(lease_row(lease, os.path.basename(path)[:-len('.plist')]))
        sources.append(path)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0])))
    return data_headers, data_list, '\n'.join(sources)
