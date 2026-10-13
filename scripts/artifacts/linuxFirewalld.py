"""firewalld configuration on a Linux system: its global settings and its zone files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxFirewalldConfig": {
        "name": "Firewalld Global Configuration",
        "description": "firewalld's global settings read from firewalld.conf, one row per setting: the default "
                       "zone, the firewall backend, whether denied packets are logged, and the other keys the "
                       "file holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "Networks (Linux)",
        "notes": "Reads firewalld's main configuration file, etc/firewalld/firewalld.conf, and reports one row per "
                 "setting. The file holds Key=Value lines with lines beginning with # as comments (Reference: "
                 "firewalld v2.4.4, 'config/firewalld.conf', "
                 "https://github.com/firewalld/firewalld/blob/295901d8467a2c9a3700677f9e06225d850bade6/config/firewalld.conf); "
                 "Setting and Value are the key and the value with surrounding whitespace removed. DefaultZone is the "
                 "zone firewalld uses for a connection or interface that has no zone selected or specified "
                 "(firewalld.conf(5)); FirewallBackend is the packet-filter the daemon drives (nftables or iptables); "
                 "LogDenied adds logging rules before firewalld's reject and drop rules, its values all, unicast, "
                 "broadcast, multicast and off. A setting the file does not list is not shown, and firewalld applies "
                 "its built-in default for it; the Fedora presets list most settings explicitly, including ones at "
                 "their default. On Fedora firewalld.conf is a symbolic link to the preset for the installed variant "
                 "(firewalld-server.conf on Server) that the package creates when no firewalld.conf exists at install "
                 "(Fedora firewalld.spec, %posttrans), so the artifact also matches the firewalld-*.conf presets, "
                 "reads the target the link the extraction recorded names (looked up by file name in the same folder) "
                 "rather than following the link on this machine, and shows that redirection in Source File as the "
                 "link's path, an arrow and the preset's path; a firewalld.conf that is a plain file is read directly "
                 "and the preset files it does not point to are not reported on their own. Validated on "
                 "fedora44_arm64_firewalld_known (Fedora Linux 44 Server, firewalld 2.4.4 per the corpus registration, "
                 "backend nftables), where firewalld.conf links to firewalld-server.conf, which holds 14 settings "
                 "including DefaultZone=FedoraServer, FirewallBackend=nftables and LogDenied=off. Not exercised on "
                 "real data: a firewalld.conf that is a plain file (tested with constructed input). The zone "
                 "DefaultZone names appears in the Firewalld Zones artifact only when its file is under a "
                 "firewalld/zones folder in the extraction. A row shows a setting as configured, not that the "
                 "firewall was running. Reading the file needs no extra package.",
        "paths": ("*/etc/firewalld/firewalld.conf", "*/etc/firewalld/firewalld-*.conf"),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            "fedora44_arm64_firewalld_known": "Fedora Linux 44 Server (aarch64), firewalld 2.4.4 backend nftables | 14 rows (firewalld.conf is a symlink to firewalld-server.conf)",
        },
    },
    "linuxFirewalldZones": {
        "name": "Firewalld Zones",
        "description": "The firewalld zones configured on the system, read from the zone files under "
                       "etc/firewalld/zones, one row per file: the zone's target, the interfaces and sources bound "
                       "to it, and the services, ports, protocols, forward ports, source ports, ICMP blocks and "
                       "rich rules it holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "Networks (Linux)",
        "notes": "Reads the zone files under etc/firewalld/zones and reports one row per file. firewalld keeps a "
                 "zone as an XML file whose name has to be the zone name followed by .xml; a name attribute on the "
                 "zone element is deprecated and ignored by firewalld (Reference: firewalld v2.4.4, "
                 "'doc/xml/firewalld.zone.xml', "
                 "https://github.com/firewalld/firewalld/blob/295901d8467a2c9a3700677f9e06225d850bade6/doc/xml/firewalld.zone.xml). "
                 "firewalld writes new and changed zones to etc/firewalld/zones and reads its built-in zones from "
                 "usr/lib/firewalld/zones, so a built-in zone with no file under etc has no persistent override at "
                 "the time of capture. Zone is the file name without its extension. Target is the zone element's "
                 "target attribute (default, ACCEPT, DROP or %%REJECT%%), shown as default when the attribute is "
                 "absent, and sets what happens to a packet no rule in the zone matched. Interfaces and Source "
                 "Addresses are the name of each interface element and the address, ipset or mac of each source "
                 "element, the traffic bound to the zone; an ipset or mac value is shown with its kind in front. "
                 "Services, Ports, Protocols, Forward Ports and Source Ports are the service names, port/protocol "
                 "pairs, protocol values, forward-port elements and source-port elements the zone enables; a forward "
                 "port is shown as port/protocol, then 'to' and the destination address and port when set. Masquerade "
                 "and Forward are yes when the zone has a masquerade or forward element and blank otherwise. ICMP "
                 "Blocks is the name of each icmp-block element and ICMP Block Inversion is yes when the "
                 "icmp-block-inversion element is present. Rich Rules is each rule element re-serialised as XML with "
                 "its whitespace collapsed, which carries firewalld's rich language: source and destination matching, "
                 "logging and audit, accept, reject, drop and mark actions, and rate limits. Short is the zone's "
                 "short title. Each list column joins its items with ' | ' and is blank when the zone has none. A "
                 "file that does not parse as XML, or whose root element is not zone, is counted in the run log and "
                 "not reported. A .old file is the copy firewalld makes of the existing zone file each time it writes "
                 "that zone (firewalld v2.4.4 'src/firewall/core/io/zone.py', zone_writer); only the latest copy is "
                 "kept, and it is reported as its own row with the .old file in Source File. Validated on "
                 "fedora44_arm64_firewalld_known (Fedora Linux 44 Server, firewalld 2.4.4 per the corpus "
                 "registration), where etc holds two zones, FedoraServer (the default zone, target default, services "
                 "cockpit, dhcpv6-client, https and ssh, port 8443/tcp) and a constructed zone dleappzone (target "
                 "default, service ssh, port 9000/tcp, source 192.168.99.0/24), each with a .old backup of its "
                 "previous version, for 4 rows. The https service and port 8443/tcp on FedoraServer, and the whole of "
                 "dleappzone, were added for this known data to exercise a modified built-in zone and a custom zone; "
                 "the .old files hold the state before the last change. On these 4 rows Target holds default on every "
                 "row, and the Interfaces, Protocols, Forward Ports, Source Ports, Masquerade, ICMP Blocks, ICMP "
                 "Block Inversion and Rich Rules columns are empty on every row: the two zones bind no interface; "
                 "FedoraServer uses services, a port, the forward flag and a short title, and dleappzone uses a "
                 "service, a port and, in its current file, a source. Not exercised on real data: rich rules, "
                 "forward-port, source-port, protocol, masquerade, icmp-block, icmp-block-inversion, ipset or mac "
                 "sources, a non-default target and an interface binding, none of which the known-data zones use; "
                 "each was tested with constructed input. A row shows a zone as configured, not that the firewall "
                 "was running or that any traffic matched it.",
        "paths": ("*/etc/firewalld/zones/*.xml", "*/etc/firewalld/zones/*.xml.old"),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            "fedora44_arm64_firewalld_known": "Fedora Linux 44 Server (aarch64), firewalld 2.4.4 | 4 rows (two zones, each with a .old backup)",
        },
    },
}

import os
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_link, seeker_of


def _files(context, needle):
    """Found files, sorted, that are not folders and whose evidence path holds the text."""
    picked = []
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        relative = context.get_relative_path(path).replace('\\', '/')
        if needle in '/' + relative:
            picked.append(path)
    return picked


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def parse_conf(data):
    """firewalld.conf as a list of (key, value): Key=Value lines, '#' comments and blank lines dropped, order kept."""
    out = []
    for raw in data.decode('utf-8', 'replace').split('\n'):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if separator and key.strip():
            out.append((key.strip(), value.strip()))
    return out


@artifact_processor
def linuxFirewalldConfig(context):
    data_headers = ('Setting', 'Value', 'Source File')
    seeker = seeker_of(context)
    found = _files(context, '/firewalld/')
    # index every staged firewalld conf file by folder then base name, so a firewalld.conf that is a symbolic link
    # (Fedora Server points it at firewalld-server.conf) can be resolved to the sibling file it names
    by_folder = {}
    for path in found:
        relative = context.get_relative_path(path).replace('\\', '/')
        folder, _, base = relative.rpartition('/')
        by_folder.setdefault(folder, {})[base] = (path, relative)
    data_list, read = [], []
    for path in found:
        relative = context.get_relative_path(path).replace('\\', '/')
        folder, _, base = relative.rpartition('/')
        if base != 'firewalld.conf':  # the firewalld-*.conf variants are staged only to resolve the link
            continue
        target_path, source = path, relative
        link = recorded_link(seeker, path) if seeker is not None else None
        if link:
            resolved = by_folder.get(folder, {}).get(link.rsplit('/', 1)[-1])
            if resolved is None:
                logfunc(f'Firewalld Global Configuration: {relative} is a link to {link}, which was not found')
                continue
            target_path = resolved[0]
            source = f'{relative} -> {resolved[1]}'
        try:
            settings = parse_conf(_read(target_path))
        except OSError:
            logfunc(f'Firewalld Global Configuration: could not read {source}')
            continue
        data_list.extend((key, value, source) for key, value in settings)
        if settings:
            read.append(target_path)
    return data_headers, data_list, '\n'.join(read)


def _names(zone, tag, attribute):
    return [element.get(attribute, '') for element in zone.findall(tag)]


def _ports(zone, tag):
    out = []
    for element in zone.findall(tag):
        port, protocol = element.get('port', ''), element.get('protocol', '')
        out.append(f'{port}/{protocol}' if port and protocol else (port or protocol))
    return out


def _sources(zone):
    out = []
    for element in zone.findall('source'):
        for attribute in ('address', 'ipset', 'mac'):
            value = element.get(attribute)
            if value:
                out.append(value if attribute == 'address' else f'{attribute} {value}')
    return out


def _forward_ports(zone):
    out = []
    for element in zone.findall('forward-port'):
        port, protocol = element.get('port', ''), element.get('protocol', '')
        target = element.get('to-port', '')
        address = element.get('to-addr', '')
        tail = ' to ' + ':'.join(part for part in (address, target) if part) if (address or target) else ''
        out.append(f'{port}/{protocol}{tail}')
    return out


def _rich_rules(zone):
    out = []
    for element in zone.findall('rule'):
        out.append(' '.join(ElementTree.tostring(element, encoding='unicode').split()))
    return out


def zone_row(name, zone):
    """(zone, target, interfaces, sources, services, ports, protocols, forward ports, source ports, masquerade,
    forward, icmp blocks, icmp block inversion, rich rules, short) for a parsed zone element."""
    join = ' | '.join
    return (name, zone.get('target', 'default'),
            join(_names(zone, 'interface', 'name')), join(_sources(zone)),
            join(_names(zone, 'service', 'name')), join(_ports(zone, 'port')),
            join(_names(zone, 'protocol', 'value')), join(_forward_ports(zone)),
            join(_ports(zone, 'source-port')),
            'yes' if zone.find('masquerade') is not None else '',
            'yes' if zone.find('forward') is not None else '',
            join(_names(zone, 'icmp-block', 'name')),
            'yes' if zone.find('icmp-block-inversion') is not None else '',
            join(_rich_rules(zone)), (zone.findtext('short') or '').strip())


@artifact_processor
def linuxFirewalldZones(context):
    data_headers = ('Zone', 'Target', 'Interfaces', 'Source Addresses', 'Services', 'Ports', 'Protocols',
                    'Forward Ports', 'Source Ports', 'Masquerade', 'Forward', 'ICMP Blocks', 'ICMP Block Inversion',
                    'Rich Rules', 'Short', 'Source File')
    data_list, read, bad = [], [], 0
    for path in _files(context, '/firewalld/zones/'):
        base = os.path.basename(path)
        try:
            zone = ElementTree.fromstring(_read(path))
        except OSError:
            continue
        except ElementTree.ParseError:
            bad += 1
            continue
        if zone.tag != 'zone':
            bad += 1
            continue
        stem = base[:-4] if base.endswith('.old') else base  # a *.xml.old backup names the same zone
        name = stem[:-4] if stem.endswith('.xml') else stem
        data_list.append(zone_row(name, zone) + (context.get_relative_path(path),))
        read.append(path)
    if bad:
        logfunc(f'Firewalld Zones: {bad} file(s) that are not a firewalld zone, not reported')
    return data_headers, data_list, '\n'.join(read)
