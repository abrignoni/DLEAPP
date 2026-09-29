"""USB devices the Linux kernel announced, from its messages in syslog files and in the systemd journal, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxUsbDevicesSyslog": {
        "name": "USB Devices (syslog)",
        "description": "USB device connections the Linux kernel logged in syslog, kern.log and messages: when "
                       "rsyslog recorded each connection and, when the kernel logged one, its disconnection, and "
                       "the vendor and product IDs, strings, port and speed the kernel logged for the device.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "USB Devices (Linux)",
        "notes": "One row per USB device connection the Linux kernel logged in the syslog files /var/log/syslog, "
                 "kern.log and messages and their rotations (numbered and gzip ones, and dated ones of messages), "
                 "read folder by folder and each file oldest rotation first. The kernel logs a line as it sets up "
                 "a device connected to a port, \"new <speed> USB device number <N> using <driver>\" (Reference: "
                 "Linux, 'drivers/usb/core/hub.c', v7.0, "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/core/hub.c#L4995-L4999, "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/core/hub.c#L5086-L5100), "
                 "worded \"number <N>\" from Linux 2.6.39 "
                 "(https://github.com/torvalds/linux/blob/61c4f2c81c61f73549928dfd9f3e8f26aa36a8cf/drivers/usb/core/hub.c#L2803-L2807) "
                 "and \"using <driver> and address <N>\" before it "
                 "(https://github.com/torvalds/linux/blob/521cb40b0c44418a4fd36dc633f575813d59a43d/drivers/usb/core/hub.c#L2740-L2744, "
                 "https://github.com/torvalds/linux/blob/521cb40b0c44418a4fd36dc633f575813d59a43d/drivers/usb/core/hub.c#L2857-L2862); "
                 "a \"New USB device found\" line with the vendor and product IDs, which adds bcdDevice from Linux "
                 "4.17 "
                 "(https://github.com/torvalds/linux/blob/0adb32858b0bddf4ada5f364a84ed60b196dbcda/drivers/usb/core/hub.c#L2195-L2197, "
                 "https://github.com/torvalds/linux/blob/29dcea88779c856c7dc92040a0c01233263101d4/drivers/usb/core/hub.c#L2202-L2206); "
                 "and a line for each product, manufacturer and serial number string the device has, all only in a "
                 "kernel built with CONFIG_USB_ANNOUNCE_NEW_DEVICES "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/core/hub.c#L2396-L2424). "
                 "It logs \"USB disconnect, device number <N>\", before 2.6.39 \"address <N>\", when the device is "
                 "disconnected "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/core/hub.c#L2327-L2328, "
                 "https://github.com/torvalds/linux/blob/521cb40b0c44418a4fd36dc633f575813d59a43d/drivers/usb/core/hub.c#L1603). "
                 "A row starts at a connection line, and the ID, string and disconnect lines of the same port fill "
                 "it, so a row whose ID and string lines never came keeps those columns blank; a disconnect fills "
                 "it only when its device number is the row's. A connection line that begins with reset is a reset "
                 "of a device already connected and starts no row. A Linux version line, which start_kernel() logs "
                 "as the kernel starts (Reference: Linux, 'init/main.c', v7.0, "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/init/main.c#L1008-L1029, "
                 "and 'init/version-timestamp.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/init/version-timestamp.c#L24-L25), "
                 "ends every connection still open, whose Disconnected columns stay blank. An ID line on a port "
                 "with no open connection starts a row of its own, with Device Number, Speed and Host Controller "
                 "Driver blank. Lines about root hubs (usbN), disconnect lines with no connection earlier in the "
                 "same boot, string lines with no connection on their port and other lines about a device are "
                 "counted in the run log and not reported. Lines of the storage drivers (usb-storage, scsi, sd) "
                 "are not read, so the rows do not name the disk a device became, and /var/log/dmesg, whose lines "
                 "on honeynet_fc7_debian5 carry only the time since boot, is not read. One kernel line can be in "
                 "several of these files: on the tested VM rsyslog's rules (/etc/rsyslog.d/50-default.conf) send "
                 "kernel lines to both syslog and kern.log. A connection several of these files hold is reported "
                 "once, and Source File lists every file that holds its lines; a disconnect only a later file "
                 "holds is added to it. A line is read in either of rsyslog's two file formats, an RFC 3339 time "
                 "with a UTC offset (rsyslog 8.2512.0, tools/smfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smfile.c#L5) "
                 "or a month, day and time with no year and no zone (tools/smtradfile.c, "
                 "https://github.com/rsyslog/rsyslog/blob/cba4c502c21e5c722cea449d1bc1ffcdfb6a2196/tools/smtradfile.c#L5). "
                 "Connected as Recorded and Disconnected as Recorded are the times as the lines store them, and "
                 "Connected (UTC) and Disconnected (UTC) those times converted with each line's own offset, blank "
                 "for a time with no year and no zone. The time is the one rsyslog gave the line, which need not "
                 "be when the kernel logged it: on ubuntu2604_arm64_usb, compared with the journal in the same "
                 "capture, the 24 connections of devices present at boot are 4.0 to 8.6 s later in syslog, the 27 "
                 "later connections within 3.5 ms and the 28 disconnects within 21.2 ms. Speed, Device Number and "
                 "Host Controller Driver are as the connection line gives them; Vendor ID, Product ID and Device "
                 "Release (bcdDevice, blank before Linux 4.17) as the ID line gives them; Manufacturer, Product "
                 "and Serial Number as the string lines give them, the first of each. Hostname is the host name "
                 "the lines store. On ubuntu2604_arm64_usb there are 51 rows, 28 with a disconnect, all for the "
                 "virtual mouse, keyboard and camera Parallels Desktop presents to the VM: Vendor ID 203a and "
                 "Manufacturer Parallels on every row. syslog and kern.log hold the same 385 lines about these "
                 "devices, and every row's Source File names a file of each. The journal in the same capture holds "
                 "the same 51 connections, with the same port, device number, IDs, strings, speed and driver, and "
                 "one more, a camera connection it logged 4.2 s after systemd began stopping rsyslog during a "
                 "shutdown. Speed is SuperSpeed and Host Controller Driver xhci_hcd on all 51 rows, and Hostname "
                 "held one value on every row. On ubuntu2604_arm64_cron, whose capture holds syslog alone, there "
                 "are 48 rows. On honeynet_fc7_debian5 (Linux 2.6.26), kern.log, messages and syslog hold only "
                 "lines about its two root hubs at each boot, the same 96 lines in each file, so the forms before "
                 "Linux 2.6.39 and a time with no year and no zone were tested only with constructed lines. No "
                 "member of the other sixteen tested images matches the declared paths.",
        "paths": ("*/var/log/syslog", "*/var/log/syslog.*", "*/var/log/kern.log", "*/var/log/kern.log.*", "*/var/log/messages", "*/var/log/messages.*", "*/var/log/messages-*"),
        "output_types": "standard",
        "artifact_icon": "usb",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (only lines about root hubs)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 48 rows",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 51 rows",
        },
    },
    "linuxUsbDevicesJournal": {
        "name": "USB Devices (journal)",
        "description": "USB device connections the Linux kernel logged in the systemd journal: when journald "
                       "received each connection and, when the kernel logged one, its disconnection, and the "
                       "vendor and product IDs, strings, port and speed the kernel logged for the device, with the "
                       "boot's ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "USB Devices (Linux)",
        "notes": "One row per USB device connection the Linux kernel logged in the systemd journal files under "
                 "var/log/journal and run/log/journal, read with the same reader as systemd Journal "
                 "(scripts/systemd_journal.py); only entries with _TRANSPORT kernel are read. The kernel's lines "
                 "and the way a row is built from them are those described for USB Devices (syslog), with the same "
                 "references to the kernel's code, read boot by boot: the lines of one boot ID, in the order of "
                 "the times since boot at which journald received them, give that boot's connections, and a "
                 "connection still open when they end keeps its Disconnected column blank. An entry that more than "
                 "one file holds is read once, and Source File lists the files that hold the lines of a "
                 "connection. Connected (UTC) and Disconnected (UTC) are the times journald received the lines "
                 "(Reference: systemd, 'systemd.journal-fields', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L642-L651). "
                 "On ubuntu2604_arm64_usb the kernel's own time for each of the 24 connection lines logged at "
                 "boot, which journald stores as _SOURCE_BOOTTIME_TIMESTAMP (Reference: systemd, "
                 "'journald-kmsg.c', "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-kmsg.c#L160-L168, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/journal/journald-kmsg.c#L259-L261), "
                 "is within 1.1 ms of the time since boot at which journald received it (Reference: "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.journal-fields.xml#L655-L666). "
                 "Boot ID is the entry's boot ID and Hostname its _HOSTNAME field. On ubuntu2604_arm64_usb and on "
                 "ubuntu2604_arm64_journal there are 52 rows over 8 boots, 28 with a disconnect, all for the "
                 "virtual mouse, keyboard and camera Parallels Desktop presents to the VM: Vendor ID 203a and "
                 "Manufacturer Parallels on every row. Speed is SuperSpeed and Host Controller Driver xhci_hcd on "
                 "all 52 rows, and Hostname held one value on every row. The rows include one connection the "
                 "syslog files lack, which journald logged 4.2 s after systemd began stopping rsyslog during a "
                 "shutdown. No member of the other seventeen tested images matches the declared paths.",
        "paths": ("*/var/log/journal/*.journal", "*/var/log/journal/*.journal~", "*/run/log/journal/*.journal", "*/run/log/journal/*.journal~"),
        "output_types": "standard",
        "artifact_icon": "usb",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 52 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 52 rows",
        },
    },
}

import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts import systemd_journal
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_syslog import read_file, reported_time, syslog_lines

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# The kernel names a USB device on a port bus-port[.port...] (1-1, 2-1.4) and a root hub usbN, and prefixes the
# messages about it with the driver name "usb" and that name.
DEVICE = re.compile(r'usb (\d+-\d+(?:\.\d+)*): (.*)', re.DOTALL)
ROOT_HUB = re.compile(r'usb usb\d+: .*', re.DOTALL)
# rsyslog 3 kept the kernel's own time since boot in front of the message.
KERNEL_TIME = re.compile(r'\[ *\d+\.\d+\] ')
# hub_port_init() from Linux 2.6.39 on, and before it.
NEW = re.compile(r'(new|reset) (.+?) USB device number (\d+) using (\S+)', re.DOTALL)
NEW_BEFORE_2_6_39 = re.compile(r'(new|reset) (.+?) USB device using (\S+) and address (\d+)', re.DOTALL)
# announce_device(); bcdDevice from Linux 4.17 on.
FOUND = re.compile(r'New USB device found, idVendor=([0-9a-f]{4}), idProduct=([0-9a-f]{4})'
                   r'(?:, bcdDevice= ?([0-9a-f]{1,2}\.[0-9a-f]{2}))?')
STRING = re.compile(r'(Product|Manufacturer|SerialNumber): (.*)', re.DOTALL)
# usb_disconnect(), from Linux 2.6.39 on and before it.
GONE = re.compile(r'USB disconnect, (?:device number|address) (\d+)')
STRING_COLUMNS = {'Product': 'product', 'Manufacturer': 'manufacturer', 'SerialNumber': 'serial'}

RESETS = 'reset lines for a device already connected, not reported'
ROOT_HUBS = 'lines about root hubs (usbN), not reported'
ORPHAN_GONE = 'disconnect lines with no connection earlier in the same boot, not reported'
ORPHAN_STRING = 'string lines with no connection on their port, not reported'
OTHER = 'other lines about a device, not reported'


def new_line(body):
    """(new or reset, speed, device number, host controller driver) for a connection line in either form, or None."""
    match = NEW.fullmatch(body)
    if match:
        return match.groups()
    match = NEW_BEFORE_2_6_39.fullmatch(body)
    if match:
        kind, speed, driver, number = match.groups()
        return kind, speed, number, driver
    return None


class Connection:
    """One device connection as the kernel's messages describe it."""

    __slots__ = ('connected', 'connected_recorded', 'disconnected', 'disconnected_recorded', 'vendor', 'product_id',
                 'release', 'manufacturer', 'product', 'serial', 'port', 'number', 'speed', 'driver', 'host', 'boot',
                 'sources')

    def __init__(self, when, recorded, port, number, speed, driver, host, boot, source):
        self.connected, self.connected_recorded = when, recorded
        self.disconnected, self.disconnected_recorded = '', ''
        self.vendor = self.product_id = self.release = self.manufacturer = self.product = self.serial = ''
        self.port, self.number, self.speed, self.driver = port, number, speed, driver
        self.host, self.boot = host, boot
        self.sources = [source]

    def key(self):
        """What identifies one connection in any file that holds its lines."""
        return (self.host, self.boot, self.port, self.number, self.connected_recorded, self.vendor, self.product_id,
                self.serial)


class Assembler:
    """Turns the kernel's USB messages of one log, in the order the log holds them, into connections."""

    def __init__(self):
        self.open = {}
        self.connections = []
        self.gone = []          # (key of the disconnect line, matched)
        self.skipped = {}       # what was not reported: {kind: {line key}}

    def skip(self, kind, host, boot, recorded, message):
        self.skipped.setdefault(kind, set()).add((host, boot, recorded, message))

    def new_boot(self):
        """A new boot: a connection still open ended without a disconnect in the log."""
        self.open = {}

    def line(self, message, when, recorded, host, boot, source):
        """Apply one kernel message; when is the UTC time ('' when the log gives none), recorded the time as the log
        holds it."""
        message = KERNEL_TIME.sub('', message, count=1) if message.startswith('[') else message
        if ROOT_HUB.fullmatch(message):
            self.skip(ROOT_HUBS, host, boot, recorded, message)
            return
        match = DEVICE.fullmatch(message)
        if not match:
            return
        port, body = match.groups()
        started = new_line(body)
        if started:
            kind, speed, number, driver = started
            if kind == 'reset':
                self.skip(RESETS, host, boot, recorded, message)
                return
            connection = Connection(when, recorded, port, number, speed, driver, host, boot, source)
            self.connections.append(connection)
            self.open[port] = connection
            return
        found = FOUND.fullmatch(body)
        if found:
            connection = self.open.get(port)
            if connection is None or connection.vendor:
                # announced with no connection line before it on this port
                connection = Connection(when, recorded, port, '', '', '', host, boot, source)
                self.connections.append(connection)
                self.open[port] = connection
            connection.vendor, connection.product_id, connection.release = found.group(1), found.group(2), \
                found.group(3) or ''
            if source not in connection.sources:
                connection.sources.append(source)
            return
        string = STRING.fullmatch(body)
        if string:
            connection = self.open.get(port)
            if connection is None:
                self.skip(ORPHAN_STRING, host, boot, recorded, message)
                return
            name = STRING_COLUMNS[string.group(1)]
            if not getattr(connection, name):
                setattr(connection, name, string.group(2))
            if source not in connection.sources:
                connection.sources.append(source)
            return
        gone = GONE.fullmatch(body)
        if gone:
            connection = self.open.get(port)
            key = (host, boot, port, gone.group(1), recorded)
            if connection is not None and connection.number in (gone.group(1), ''):
                connection.disconnected, connection.disconnected_recorded = when, recorded
                if source not in connection.sources:
                    connection.sources.append(source)
                del self.open[port]
                self.gone.append((key, True))
            else:
                self.gone.append((key, False))
            return
        if not body.startswith('New USB device strings: '):
            self.skip(OTHER, host, boot, recorded, message)


def merge(assemblers, counts):
    """The connections of several logs of one system, each once: rsyslog writes a kernel message to every file whose
    rule selects it, so one connection can be in syslog, kern.log and messages. A later log's copy adds its files and
    a disconnect the earlier copy lacks."""
    merged = {}
    order = []
    for assembler in assemblers:
        for connection in assembler.connections:
            key = connection.key()
            kept = merged.get(key)
            if kept is None:
                merged[key] = connection
                order.append(connection)
                continue
            for source in connection.sources:
                if source not in kept.sources:
                    kept.sources.append(source)
            if not kept.disconnected_recorded and connection.disconnected_recorded:
                kept.disconnected, kept.disconnected_recorded = connection.disconnected, \
                    connection.disconnected_recorded
    matched = {key for assembler in assemblers for key, ok in assembler.gone if ok}
    orphans = {key for assembler in assemblers for key, ok in assembler.gone if not ok} - matched
    if orphans:
        counts[ORPHAN_GONE] += len(orphans)
    # a line several logs hold is counted once
    for kind in sorted({kind for assembler in assemblers for kind in assembler.skipped}):
        counts[kind] += len(set().union(*(assembler.skipped.get(kind, set()) for assembler in assemblers)))
    return order


# ---------------------------------------------------------------------------------------------- syslog

_ROTATED = re.compile(r'(syslog|kern\.log|messages)(?:\.(\d+)|-(\d{8}))?(\.gz)?')


def log_family(name):
    """(family, order) for a syslog file name: the file's family and a key that puts older rotations first, or None
    for a name that is not one of these logs."""
    match = _ROTATED.fullmatch(name)
    if not match:
        return None
    family, number, date, _gz = match.groups()
    if number is not None:
        return family, (0, -int(number), '')
    if date is not None:
        return family, (1, 0, date)
    return family, (2, 0, '')


def syslog_connections(files, counts):
    """The connections the kernel messages in these syslog files describe, each once. files: (relative path, bytes)
    of the files of one folder."""
    families = {}
    for relative, data in files:
        family = log_family(os.path.basename(relative.replace('\\', '/')))
        if family is None:
            counts['files named like no syslog file, not read'] += 1
            continue
        families.setdefault(family[0], []).append((family[1], relative, data))
    assemblers = []
    for family in ('syslog', 'kern.log', 'messages'):
        if family not in families:
            continue
        assembler = Assembler()
        for _order, relative, data in sorted(families[family], key=lambda item: (item[0], item[1])):
            for _number, stamp, host, program, _pid, message in syslog_lines(data, Counter()):
                if program != 'kernel':
                    continue
                if message.startswith('Linux version ') or KERNEL_TIME.sub('', message, count=1).startswith(
                        'Linux version '):
                    assembler.new_boot()
                    continue
                if 'usb' not in message:
                    continue
                assembler.line(message, None, stamp, host, '', relative)
        assemblers.append(assembler)
    connections = merge(assemblers, counts)
    for connection in connections:
        connection.connected = reported_time(connection.connected_recorded, counts)
        if connection.disconnected_recorded:
            connection.disconnected = reported_time(connection.disconnected_recorded, counts)
    return connections


@artifact_processor
def linuxUsbDevicesSyslog(context):
    data_headers = (('Connected (UTC)', 'datetime'), ('Disconnected (UTC)', 'datetime'), 'Connected as Recorded',
                    'Disconnected as Recorded', 'Vendor ID', 'Product ID', 'Manufacturer', 'Product', 'Serial Number',
                    'Device Release', 'Port', 'Device Number', 'Speed', 'Host Controller Driver', 'Hostname',
                    'Source File')
    counts = Counter()
    folders = {}
    for path in sorted(set(map(str, context.get_files_found()))):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        folders.setdefault(os.path.dirname(relative.replace('\\', '/')), []).append((relative, path))
    data_list = []
    read = []
    for folder in sorted(folders):
        files = []
        for relative, path in folders[folder]:
            try:
                files.append((relative, read_file(path)))
            except (OSError, EOFError):
                counts['files that could not be read'] += 1
        for connection in syslog_connections(files, counts):
            data_list.append((connection.connected, connection.disconnected, connection.connected_recorded,
                              connection.disconnected_recorded, connection.vendor, connection.product_id,
                              connection.manufacturer, connection.product, connection.serial, connection.release,
                              connection.port, connection.number, connection.speed, connection.driver,
                              connection.host, '\n'.join(connection.sources)))
            for source in connection.sources:
                if source not in read:
                    read.append(source)
    if counts:
        logfunc('USB Devices (syslog): ' + ', '.join(f'{count} {what}' for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


# ---------------------------------------------------------------------------------------------- journal

def _time(microseconds):
    """A journal time as a datetime, or '' for 0 or a value past 9999."""
    if not microseconds or microseconds >= 253402300800000000:
        return ''
    return EPOCH + timedelta(microseconds=microseconds)


def journal_connections(journals, counts):
    """The connections the kernel messages in these journal files describe. journals: (relative path, JournalFile)."""
    boots = {}
    seen = set()
    for relative, journal in journals:
        for entry in journal.entries():
            fields = {}
            for name, value in entry.fields:
                fields.setdefault(name, value)
            if fields.get('_TRANSPORT') != b'kernel':
                continue
            raw = fields.get('MESSAGE')
            if raw is None or b'usb' not in raw:
                continue
            message = raw.decode('utf-8', errors='backslashreplace')
            key = (entry.boot_id, entry.monotonic, entry.realtime, message)
            if key in seen:
                counts['entries also in another journal file, reported once'] += 1
                continue
            seen.add(key)
            host = (fields.get('_HOSTNAME') or b'').decode('utf-8', errors='backslashreplace')
            boots.setdefault(entry.boot_id, []).append((entry.monotonic, entry.seqnum, relative, entry.realtime,
                                                        message, host))
    assemblers = []
    for boot in sorted(boots, key=lambda b: min(item[3] for item in boots[b])):
        assembler = Assembler()
        for _mono, _seq, relative, realtime, message, host in sorted(boots[boot], key=lambda item: item[:3]):
            assembler.line(message, _time(realtime), str(realtime), host, boot, relative)
        assemblers.append(assembler)
    return merge(assemblers, counts)


@artifact_processor
def linuxUsbDevicesJournal(context):
    data_headers = (('Connected (UTC)', 'datetime'), ('Disconnected (UTC)', 'datetime'), 'Vendor ID', 'Product ID',
                    'Manufacturer', 'Product', 'Serial Number', 'Device Release', 'Port', 'Device Number', 'Speed',
                    'Host Controller Driver', 'Hostname', 'Boot ID', 'Source File')
    counts = Counter()
    journals = []
    for path in sorted(set(map(str, context.get_files_found()))):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            journals.append((relative, systemd_journal.read_journal(path)))
        except (OSError, systemd_journal.JournalError) as exc:
            counts[f'journal files not read ({type(exc).__name__})'] += 1
    data_list = []
    read = []
    for connection in journal_connections(journals, counts):
        data_list.append((connection.connected, connection.disconnected, connection.vendor, connection.product_id,
                          connection.manufacturer, connection.product, connection.serial, connection.release,
                          connection.port, connection.number, connection.speed, connection.driver, connection.host,
                          connection.boot, '\n'.join(connection.sources)))
        for source in connection.sources:
            if source not in read:
                read.append(source)
    if counts:
        logfunc('USB Devices (journal): ' + ', '.join(f'{count} {what}' for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
