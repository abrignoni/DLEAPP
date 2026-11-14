"""DHCP client leases that systemd-networkd and NetworkManager write on Linux, for DLEAPP."""

import os

from scripts.ilapfuncs import artifact_processor, logfunc

# (stored key, column header) in the order the columns are reported; data_headers below is the
# literal tuple of the same headers plus Source File, so the output checkers can read it.
_FIELDS = [
    ('ADDRESS', 'Address'),
    ('NETMASK', 'Netmask'),
    ('ROUTER', 'Router'),
    ('DNS', 'DNS'),
    ('DOMAINNAME', 'Domain Name'),
    ('SERVER_ADDRESS', 'Server Address'),
    ('NEXT_SERVER', 'Next Server'),
    ('T1', 'T1'),
    ('T2', 'T2'),
    ('LIFETIME', 'Lifetime'),
    ('CLIENTID', 'Client ID'),
    ('HOSTNAME', 'Hostname'),
]

__artifacts_v2__ = {
    "linuxDhcpLeases": {
        "name": "DHCP Client Leases (Linux)",
        "description": "DHCP client lease files on Linux, one row per file: the leases "
                       "systemd-networkd keeps under run/systemd/netif/leases and the internal "
                       "lease NetworkManager keeps under var/lib/NetworkManager. The columns are "
                       "the address, netmask, router, DNS, domain, DHCP server, next server, lease "
                       "timers, client id and hostname each file carries, reported as text with no "
                       "interpretation.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-13",
        "last_update_date": "2026-11-13",
        "requirements": "none",
        "category": "Networks (Linux)",
        "notes": "One row per lease file. systemd-networkd writes one lease file per link under "
                 "run/systemd/netif/leases; the file name is the kernel interface index, a number, "
                 "and the file does not record the interface name. NetworkManager writes "
                 "internal-<connection uuid>-<iface>.lease under var/lib/NetworkManager; a copy "
                 "under run/NetworkManager and IPv6 internal6- files are not read. Both are a list "
                 "of KEY=value lines after a first comment line that reads 'This is private data. "
                 "Do not parse.', so the values are reported as text with no interpretation "
                 "(surrounding whitespace trimmed); the writers mark the file as private and the "
                 "format has changed between systemd releases. run/ is a memory filesystem, so the "
                 "systemd-networkd lease is present only in a live or triage collection. Address, "
                 "Netmask, Router, DNS, Domain Name, Server Address, Next Server, Client ID and "
                 "Hostname are the ADDRESS, NETMASK, ROUTER, DNS, DOMAINNAME, SERVER_ADDRESS, "
                 "NEXT_SERVER, CLIENTID and HOSTNAME values; a key the file does not carry is "
                 "blank, and other keys a lease can carry (for example BROADCAST, MTU, NTP, "
                 "DOMAIN_SEARCH_LIST, TIMEZONE) are not reported. systemd writes HOSTNAME and "
                 "DOMAINNAME in DNS escaped form: a character other than a letter, digit, "
                 "underscore or hyphen is written as a backslash and its three-digit decimal code, "
                 "so a space is \\032, and the value is shown with that escaping. Hostname is the "
                 "host name the DHCP server sent in the lease, which can differ from the machine's "
                 "configured hostname. T1, T2 and Lifetime are the DHCP renew, rebind and lease "
                 "timers; on the tested image they are time-span text (a number with a unit, for "
                 "example 15min, 26min 15s, 30min), older systemd releases wrote a plain number of "
                 "seconds, and the value is shown as written; they are durations, not absolute "
                 "times, and the file records no acquisition time. ISC dhclient leases "
                 "(var/lib/dhcp/*.leases, a different block format) are not read and have not been "
                 "tested. A file under the declared paths that carries no ADDRESS is counted in "
                 "the run log and not reported. Source File names the file each row came from and "
                 "is the column that separates the two writers and carries the interface index, "
                 "connection uuid and interface name. On ubuntu2604_arm64_dhcpleases_known_20261113 "
                 "(captured from the running Parallels Ubuntu 26.04 lab VM) the systemd-networkd "
                 "lease gave a value in all 12 value columns and the NetworkManager internal lease "
                 "gave only Address, 2 rows; the values are a lab VM's own network settings.",
        "paths": ('*/run/systemd/netif/leases/*', '*/var/lib/NetworkManager/internal-*.lease'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "wifi",
        "sample_data": {
            "ubuntu2604_arm64_dhcpleases_known_20261113": "Ubuntu 26.04 LTS aarch64 | 2 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    }
}


@artifact_processor
def linuxDhcpLeases(context):
    data_headers = ('Address', 'Netmask', 'Router', 'DNS', 'Domain Name', 'Server Address',
                    'Next Server', 'T1', 'T2', 'Lifetime', 'Client ID', 'Hostname', 'Source File')
    data_list = []
    sources = []
    skipped = 0
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            skipped += 1
            continue
        values = {}
        for line in data.decode('utf-8', errors='replace').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            values[key.strip()] = value.strip()
        if 'ADDRESS' not in values:
            skipped += 1
            continue
        row = tuple(values.get(key, '') for key, _ in _FIELDS)
        data_list.append(row + (context.get_relative_path(path),))
        sources.append(path)
    if skipped:
        logfunc(f'DHCP Client Leases (Linux): {skipped} file(s) under the declared paths carried '
                'no ADDRESS or could not be read, not reported')
    return data_headers, data_list, '\n'.join(sources)
