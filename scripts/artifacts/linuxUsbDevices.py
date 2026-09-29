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
    "linuxUsbStorageSyslog": {
        "name": "USB Storage Devices (syslog)",
        "description": "USB storage devices the Linux kernel logged in syslog, kern.log and messages, and the disk "
                       "it made of each: its name, the vendor, model and revision the device reported, its "
                       "capacity, removable and write protect flags, and the USB connection's times, IDs and "
                       "strings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "USB Devices (Linux)",
        "notes": "One row per disk the usb-storage driver made of a USB device, from the kernel's lines in the "
                 "syslog files /var/log/syslog, kern.log and messages and their rotations, read as USB Devices "
                 "(syslog) reads them: folder by folder, each file oldest rotation first, a Linux version line "
                 "ending every connection still open, and a connection several of these files hold reported once, "
                 "with Source File listing every file that holds its lines. The usb-storage driver logs \"USB Mass "
                 "Storage device detected\" for the interface of a device it claims, named "
                 "<port>:<configuration>.<interface> (Reference: Linux, 'drivers/usb/storage/usb.c', v7.0, "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/usb.c#L1028), "
                 "and names the SCSI host it registers for it \"usb-storage <interface>\" "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/usb.c#L1153-L1154), "
                 "which the SCSI layer logs as \"scsi host<N>: usb-storage <interface>\" ('drivers/scsi/hosts.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/hosts.c#L225-L226, "
                 "with the name from the driver's info function, 'drivers/usb/storage/scsiglue.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/scsiglue.c#L61-L65 "
                 "and "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/scsiglue.c#L621). "
                 "For each device it finds on that host the SCSI layer logs \"scsi <host>:<channel>:<target>:<lun>: "
                 "<device type> <vendor> <model> <revision> PQ: <n> ANSI: <n>\" ('drivers/scsi/scsi_scan.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/scsi_scan.c#L981-L984), "
                 "and the sd driver prefixes its lines about a disk with that address and the disk's name in "
                 "brackets ('drivers/scsi/sd.h', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.h#L167-L171, "
                 "'drivers/scsi/scsi_logging.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/scsi_logging.c#L70-L78) "
                 "as it logs the capacity ('drivers/scsi/sd.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.c#L2963-L2966), "
                 "whether the disk is write protected "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.c#L3043-L3044) "
                 "and \"Attached SCSI disk\", with \"removable \" before disk for a removable one "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.c#L4072-L4073). "
                 "The artifact attaches the usb-storage line to the USB connection open on its port, the host line "
                 "to that connection, and each SCSI and sd line to the connection whose host number begins the "
                 "line's address, while that connection is open; a later device can be given a host number an "
                 "earlier one had, so a line goes to the connection that registered the host last. SCSI and sd "
                 "lines about a device on no USB storage host (a built-in disk, for instance) and storage lines "
                 "with no open connection to attach them to are counted in the run log and not reported. A "
                 "connection the usb-storage driver claimed whose SCSI lines never came gives one row with the "
                 "disk columns blank, also counted. Disk is the name in brackets on the sd lines (sdb, for "
                 "instance), the first when they give more than one. SCSI Vendor, SCSI Model and SCSI Revision are "
                 "the identification line's text split at the 8, 16 and 4 characters the kernel prints them in; "
                 "from Linux 4.6 the kernel pads them with spaces to those widths ('drivers/scsi/scsi_scan.c', "
                 "v4.6, "
                 "https://github.com/torvalds/linux/blob/2dcd0af568b0cf583645c8a317dd12e344b1c72a/drivers/scsi/scsi_scan.c#L633-L635, "
                 "absent from v4.5, "
                 "https://github.com/torvalds/linux/blob/b562e44f507e863c6792946e4e1b1449fbbac85d/drivers/scsi/scsi_scan.c), "
                 "and before it a NUL in a string ends it early, so when the spaces between them are not where "
                 "those widths put them the whole text is reported in SCSI Model with Device Type, SCSI Vendor and "
                 "SCSI Revision blank, and the row is counted. Device Type is the type the line names "
                 "(Direct-Access, for instance). Capacity is the size as the capacity line gives it (in decimal "
                 "and binary units from Linux 2.6.28), and Blocks and Block Size the number and size of its "
                 "blocks; the artifact also reads the line's forms \"hardware sectors: (...)\" from Linux 2.6.28 to "
                 "2.6.30 "
                 "(https://github.com/torvalds/linux/blob/4a6908a3a050aacc9c3a2f36b276b46c0629ad91/drivers/scsi/sd.c#L1442) "
                 "and \"hardware sectors (<n> MB)\" before 2.6.28 "
                 "(https://github.com/torvalds/linux/blob/3fa8749e584b55f1180411ab1b51117190bac1e5/drivers/scsi/sd.c#L1450); "
                 "\"logical blocks\" is the wording from 2.6.31 "
                 "(https://github.com/torvalds/linux/blob/74fca6a42863ffacaf7ba6f1936a9f228950f657/drivers/scsi/sd.c#L1538). "
                 "The older forms and a split that fails were tested with constructed lines only. Removable is Yes "
                 "or No from the attach line, blank when no attach line came; Write Protect is on or off as the "
                 "line gives it. SCSI Address is <host>:<channel>:<target>:<lun>, and a device with several (a "
                 "card reader with a slot for each card, for instance) gives a row for each, which was tested with "
                 "constructed lines only. Interface is the usb-storage driver's interface name. Vendor ID, Product "
                 "ID, Manufacturer, Product, Serial Number, Port and Hostname are those of the USB connection, "
                 "read as the USB Devices artifacts read them. Lines about partitions, the SCSI generic (sg) name "
                 "and every other sd message are not read, and nothing here records whether or where a disk was "
                 "mounted. Connected (UTC) and Disconnected (UTC) are the times rsyslog gave the USB connection "
                 "and disconnect lines, converted with each line's own offset, and Connected as Recorded and "
                 "Disconnected as Recorded those times as the lines store them. On ubuntu2604_arm64_usbstorage, "
                 "made with one USB flash drive passed through to the lab VM, there are 2 rows, both Disk sdb, "
                 "Device Type Direct-Access, Removable Yes and Write Protect off: one for the drive's connection "
                 "on port 3-1, disconnected when udisksctl power-off removed it, and one for its connection on "
                 "port 3-2 about 18 minutes later, disconnected when the drive was pulled out without being "
                 "ejected. Both connections registered SCSI host 6. The two disconnects read alike, so a row does "
                 "not say whether the drive was ejected before it was removed. The columns the syslog rows share "
                 "with the journal's in the same capture agree, apart from the times and Source File; the times in "
                 "syslog are 6 and 18 microseconds later for the connections and 0.93 and 0.28 ms later for the "
                 "disconnects; syslog and kern.log each hold both rows' lines. On ubuntu2604_arm64_usb and "
                 "ubuntu2604_arm64_cron the syslog files hold no USB storage device, and their SCSI and sd lines, "
                 "about the VM's built-in disk and DVD drive, are counted, as are the 48 SCSI and sd lines on "
                 "honeynet_fc7_debian5 (Linux 2.6.26), none of them about a USB storage device. No member of the "
                 "other twenty-three tested images matches the declared paths.",
        "paths": ("*/var/log/syslog", "*/var/log/syslog.*", "*/var/log/kern.log", "*/var/log/kern.log.*", "*/var/log/messages", "*/var/log/messages.*", "*/var/log/messages-*"),
        "output_types": "standard",
        "artifact_icon": "hard-drive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (syslog files with no USB storage device)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (syslog files with no USB storage device)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                            "paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (syslog files with no USB storage device)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64, Linux 7.0.0-34-generic | 2 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxUsbStorageJournal": {
        "name": "USB Storage Devices (journal)",
        "description": "USB storage devices the Linux kernel logged in the systemd journal, and the disk it made "
                       "of each: its name, the vendor, model and revision the device reported, its capacity, "
                       "removable and write protect flags, and the USB connection's times, IDs and strings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "USB Devices (Linux)",
        "notes": "One row per disk the usb-storage driver made of a USB device, from the kernel's entries in the "
                 "systemd journal files, read as USB Devices (journal) reads them: entries of each boot in the "
                 "order the kernel logged them, an entry that two journal files hold read once, and boots kept "
                 "apart. The usb-storage driver logs \"USB Mass Storage device detected\" for the interface of a "
                 "device it claims, named <port>:<configuration>.<interface> (Reference: Linux, "
                 "'drivers/usb/storage/usb.c', v7.0, "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/usb.c#L1028), "
                 "and names the SCSI host it registers for it \"usb-storage <interface>\" "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/usb.c#L1153-L1154), "
                 "which the SCSI layer logs as \"scsi host<N>: usb-storage <interface>\" ('drivers/scsi/hosts.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/hosts.c#L225-L226, "
                 "with the name from the driver's info function, 'drivers/usb/storage/scsiglue.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/scsiglue.c#L61-L65 "
                 "and "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/usb/storage/scsiglue.c#L621). "
                 "For each device it finds on that host the SCSI layer logs \"scsi <host>:<channel>:<target>:<lun>: "
                 "<device type> <vendor> <model> <revision> PQ: <n> ANSI: <n>\" ('drivers/scsi/scsi_scan.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/scsi_scan.c#L981-L984), "
                 "and the sd driver prefixes its lines about a disk with that address and the disk's name in "
                 "brackets ('drivers/scsi/sd.h', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.h#L167-L171, "
                 "'drivers/scsi/scsi_logging.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/scsi_logging.c#L70-L78) "
                 "as it logs the capacity ('drivers/scsi/sd.c', "
                 "https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.c#L2963-L2966), "
                 "whether the disk is write protected "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.c#L3043-L3044) "
                 "and \"Attached SCSI disk\", with \"removable \" before disk for a removable one "
                 "(https://github.com/torvalds/linux/blob/028ef9c96e96197026887c0f092424679298aae8/drivers/scsi/sd.c#L4072-L4073). "
                 "The artifact attaches the usb-storage line to the USB connection open on its port, the host line "
                 "to that connection, and each SCSI and sd line to the connection whose host number begins the "
                 "line's address, while that connection is open; a later device can be given a host number an "
                 "earlier one had, so a line goes to the connection that registered the host last. SCSI and sd "
                 "lines about a device on no USB storage host (a built-in disk, for instance) and storage lines "
                 "with no open connection to attach them to are counted in the run log and not reported. A "
                 "connection the usb-storage driver claimed whose SCSI lines never came gives one row with the "
                 "disk columns blank, also counted. Disk is the name in brackets on the sd lines (sdb, for "
                 "instance), the first when they give more than one. SCSI Vendor, SCSI Model and SCSI Revision are "
                 "the identification line's text split at the 8, 16 and 4 characters the kernel prints them in; "
                 "from Linux 4.6 the kernel pads them with spaces to those widths ('drivers/scsi/scsi_scan.c', "
                 "v4.6, "
                 "https://github.com/torvalds/linux/blob/2dcd0af568b0cf583645c8a317dd12e344b1c72a/drivers/scsi/scsi_scan.c#L633-L635, "
                 "absent from v4.5, "
                 "https://github.com/torvalds/linux/blob/b562e44f507e863c6792946e4e1b1449fbbac85d/drivers/scsi/scsi_scan.c), "
                 "and before it a NUL in a string ends it early, so when the spaces between them are not where "
                 "those widths put them the whole text is reported in SCSI Model with Device Type, SCSI Vendor and "
                 "SCSI Revision blank, and the row is counted. Device Type is the type the line names "
                 "(Direct-Access, for instance). Capacity is the size as the capacity line gives it (in decimal "
                 "and binary units from Linux 2.6.28), and Blocks and Block Size the number and size of its "
                 "blocks; the artifact also reads the line's forms \"hardware sectors: (...)\" from Linux 2.6.28 to "
                 "2.6.30 "
                 "(https://github.com/torvalds/linux/blob/4a6908a3a050aacc9c3a2f36b276b46c0629ad91/drivers/scsi/sd.c#L1442) "
                 "and \"hardware sectors (<n> MB)\" before 2.6.28 "
                 "(https://github.com/torvalds/linux/blob/3fa8749e584b55f1180411ab1b51117190bac1e5/drivers/scsi/sd.c#L1450); "
                 "\"logical blocks\" is the wording from 2.6.31 "
                 "(https://github.com/torvalds/linux/blob/74fca6a42863ffacaf7ba6f1936a9f228950f657/drivers/scsi/sd.c#L1538). "
                 "The older forms and a split that fails were tested with constructed lines only. Removable is Yes "
                 "or No from the attach line, blank when no attach line came; Write Protect is on or off as the "
                 "line gives it. SCSI Address is <host>:<channel>:<target>:<lun>, and a device with several (a "
                 "card reader with a slot for each card, for instance) gives a row for each, which was tested with "
                 "constructed lines only. Interface is the usb-storage driver's interface name. Vendor ID, Product "
                 "ID, Manufacturer, Product, Serial Number, Port and Hostname are those of the USB connection, "
                 "read as the USB Devices artifacts read them. Lines about partitions, the SCSI generic (sg) name "
                 "and every other sd message are not read, and nothing here records whether or where a disk was "
                 "mounted. Connected (UTC) and Disconnected (UTC) are the journal's times for the USB connection "
                 "and disconnect entries, and Boot ID the boot the entries belong to. On "
                 "ubuntu2604_arm64_usbstorage, made with one USB flash drive passed through to the lab VM, there "
                 "are 2 rows, both Disk sdb, Device Type Direct-Access, Removable Yes and Write Protect off: one "
                 "for the drive's connection on port 3-1, disconnected when udisksctl power-off removed it, and "
                 "one for its connection on port 3-2 about 18 minutes later, disconnected when the drive was "
                 "pulled out without being ejected. Both connections registered SCSI host 6. The two disconnects "
                 "read alike, so a row does not say whether the drive was ejected before it was removed. The "
                 "columns the journal rows share with the syslog files' in the same capture agree, apart from the "
                 "times and Source File; the times in the journal are 6 and 18 microseconds earlier for the "
                 "connections and 0.93 and 0.28 ms earlier for the disconnects. On ubuntu2604_arm64_usb and "
                 "ubuntu2604_arm64_journal the journal holds no USB storage device, and its SCSI and sd entries, "
                 "about the VM's built-in disk and DVD drive, are counted. No member of the other twenty-four "
                 "tested images matches the declared paths.",
        "paths": ("*/var/log/journal/*.journal", "*/var/log/journal/*.journal~", "*/run/log/journal/*.journal", "*/run/log/journal/*.journal~"),
        "output_types": "standard",
        "artifact_icon": "hard-drive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                            "paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (journal files with no USB storage "
                                        "device)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (journal files with no USB storage device)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64, Linux 7.0.0-34-generic | 2 rows",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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
                 'sources', 'interface', 'scsi_host', 'disks')

    def __init__(self, when, recorded, port, number, speed, driver, host, boot, source):
        self.connected, self.connected_recorded = when, recorded
        self.disconnected, self.disconnected_recorded = '', ''
        self.vendor = self.product_id = self.release = self.manufacturer = self.product = self.serial = ''
        self.port, self.number, self.speed, self.driver = port, number, speed, driver
        self.host, self.boot = host, boot
        self.sources = [source]
        # filled only by StorageAssembler, for a device the usb-storage driver claimed
        self.interface = self.scsi_host = ''
        self.disks = []

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
            if not kept.interface and connection.interface:
                kept.interface, kept.scsi_host = connection.interface, connection.scsi_host
            for disk in connection.disks:
                if disk.address not in {d.address for d in kept.disks}:
                    kept.disks.append(disk)
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


def syslog_connections(files, counts, assembler_class=None, wanted=None):
    """The connections the kernel messages in these syslog files describe, each once. files: (relative path, bytes)
    of the files of one folder. assembler_class and wanted (which kernel messages to pass it) default to the USB
    ones."""
    assembler_class = assembler_class or Assembler
    wanted = wanted or (lambda message: 'usb' in message)
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
        assembler = assembler_class()
        for _order, relative, data in sorted(families[family], key=lambda item: (item[0], item[1])):
            for _number, stamp, host, program, _pid, message in syslog_lines(data, Counter()):
                if program != 'kernel':
                    continue
                if message.startswith('Linux version ') or KERNEL_TIME.sub('', message, count=1).startswith(
                        'Linux version '):
                    assembler.new_boot()
                    continue
                if not wanted(message):
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


def journal_connections(journals, counts, assembler_class=None, wanted=None):
    """The connections the kernel messages in these journal files describe. journals: (relative path, JournalFile).
    assembler_class and wanted (which raw kernel messages to pass it) default to the USB ones."""
    assembler_class = assembler_class or Assembler
    wanted = wanted or (lambda raw: b'usb' in raw)
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
            if raw is None or not wanted(raw):
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
        assembler = assembler_class()
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


# ---------------------------------------------------------------------------------------------- USB storage

_PORT = r'\d+-\d+(?:\.\d+)*'
# usb_stor_probe1() and the host name it gives the SCSI host, which scsi_add_host() prints.
STORAGE = re.compile(r'usb-storage (' + _PORT + r'):(\d+\.\d+): USB Mass Storage device detected')
SCSI_HOST = re.compile(r'scsi host(\d+): usb-storage (' + _PORT + r'):(\d+\.\d+)')
# scsi_add_lun(): the device type, then the INQUIRY vendor, model and revision, 8, 16 and 4 characters.
SCSI_DEVICE = re.compile(r'scsi (\d+:\d+:\d+:\d+): (.*) PQ: \d+ ANSI: \d+(?: CCS)?', re.DOTALL)
# sd_printk(): "sd <address>: [<disk>] <message>".
SD = re.compile(r'sd (\d+:\d+:\d+:\d+): \[([^\]\s]+)\] (.*)', re.DOTALL)
# sd_print_capacity() from Linux 2.6.31 on, from 2.6.28 to 2.6.30, and before 2.6.28.
CAPACITY = re.compile(r'(\d+) (\d+)-byte (?:logical blocks|hardware sectors): \((.+)\)')
CAPACITY_MB = re.compile(r'(\d+) (\d+)-byte hardware sectors \((\d+ MB)\)')
WRITE_PROTECT = re.compile(r'Write Protect is (on|off)')
ATTACHED = re.compile(r'Attached SCSI (removable )?disk')

USB_ONLY = {RESETS, ROOT_HUBS, ORPHAN_GONE, ORPHAN_STRING, OTHER}
STORAGE_ORPHAN = 'SCSI and disk lines about a device on no USB storage host (a built-in disk, for instance), not reported'
IDENT_UNSPLIT = 'device identification lines not split into vendor, model and revision (reported in SCSI Model)'


class Disk:
    """One SCSI device on a USB storage host, as the SCSI and sd drivers describe it."""

    __slots__ = ('address', 'name', 'kind', 'vendor', 'model', 'revision', 'capacity', 'blocks', 'block_size',
                 'removable', 'write_protect', 'unsplit')

    def __init__(self, address):
        self.address = address
        self.name = self.kind = self.vendor = self.model = self.revision = ''
        self.capacity = self.blocks = self.block_size = self.removable = self.write_protect = ''
        self.unsplit = False


def split_identification(text):
    """(device type, vendor, model, revision) from the text between the address and 'PQ:'. The kernel prints the
    INQUIRY strings at 8, 16 and 4 characters, space padded from Linux 4.6 on; when the spaces between them are not
    where those widths put them (a string a NUL cut short before 4.6), the whole text is the model, and the fifth
    value is True."""
    if len(text) >= 32 and text[-5] == ' ' and text[-22] == ' ' and text[-31] == ' ':
        return text[:-31].strip(), text[-30:-22].strip(), text[-21:-5].strip(), text[-4:].strip(), False
    return '', '', text.strip(), '', True


class StorageAssembler(Assembler):
    """The USB connections of one log, with the SCSI devices the usb-storage driver made of them: the driver names
    the interface it claimed on the device's port, the SCSI host it registered names that interface, and the SCSI
    and sd drivers name the host in every device address (host:channel:target:lun)."""

    def __init__(self):
        super().__init__()
        self.hosts = {}

    def new_boot(self):
        super().new_boot()
        self.hosts = {}

    def _disk(self, address, host, boot, recorded, message):
        connection = self.hosts.get(address.split(':', 1)[0])
        if connection is None or connection.disconnected_recorded:
            self.skip(STORAGE_ORPHAN, host, boot, recorded, message)
            return None
        for disk in connection.disks:
            if disk.address == address:
                return disk
        disk = Disk(address)
        connection.disks.append(disk)
        return disk

    def line(self, message, when, recorded, host, boot, source):
        message = KERNEL_TIME.sub('', message, count=1) if message.startswith('[') else message
        match = STORAGE.fullmatch(message)
        if match:
            connection = self.open.get(match.group(1))
            if connection is None:
                self.skip(STORAGE_ORPHAN, host, boot, recorded, message)
            else:
                connection.interface = f'{match.group(1)}:{match.group(2)}'
                if source not in connection.sources:
                    connection.sources.append(source)
            return
        match = SCSI_HOST.fullmatch(message)
        if match:
            connection = self.open.get(match.group(2))
            if connection is None:
                self.skip(STORAGE_ORPHAN, host, boot, recorded, message)
            else:
                self.hosts[match.group(1)] = connection
                connection.scsi_host = match.group(1)
            return
        match = SCSI_DEVICE.fullmatch(message)
        if match:
            disk = self._disk(match.group(1), host, boot, recorded, message)
            if disk is not None:
                disk.kind, disk.vendor, disk.model, disk.revision, disk.unsplit = split_identification(match.group(2))
            return
        match = SD.fullmatch(message)
        if match:
            disk = self._disk(match.group(1), host, boot, recorded, message)
            if disk is None:
                return
            disk.name = disk.name or match.group(2)
            body = match.group(3)
            capacity = CAPACITY.fullmatch(body) or CAPACITY_MB.fullmatch(body)
            if capacity:
                disk.blocks, disk.block_size, disk.capacity = capacity.groups()
            elif WRITE_PROTECT.fullmatch(body):
                disk.write_protect = WRITE_PROTECT.fullmatch(body).group(1)
            elif ATTACHED.fullmatch(body):
                disk.removable = 'Yes' if ATTACHED.fullmatch(body).group(1) else 'No'
            return
        super().line(message, when, recorded, host, boot, source)


def _storage_message(message):
    body = KERNEL_TIME.sub('', message, count=1) if message.startswith('[') else message
    return 'usb' in body or body.startswith(('scsi ', 'sd '))


def _storage_raw(raw):
    return b'usb' in raw or raw.startswith((b'scsi ', b'sd '))


def storage_rows(connections, counts):
    """(connection, disk or None) for each disk of each connection the usb-storage driver claimed, and one row with
    no disk for such a connection whose SCSI device lines never came."""
    rows = []
    for connection in connections:
        if not connection.interface:
            continue
        if not connection.disks:
            counts['USB storage devices with no SCSI device lines, reported without a disk'] += 1
            rows.append((connection, None))
        for disk in connection.disks:
            if disk.unsplit:
                counts[IDENT_UNSPLIT] += 1
            rows.append((connection, disk))
    return rows


def _disk_columns(disk):
    if disk is None:
        return ('',) * 11
    return (disk.name, disk.vendor, disk.model, disk.revision, disk.kind, disk.capacity, disk.blocks,
            disk.block_size, disk.removable, disk.write_protect, disk.address)


@artifact_processor
def linuxUsbStorageSyslog(context):
    data_headers = (('Connected (UTC)', 'datetime'), ('Disconnected (UTC)', 'datetime'), 'Connected as Recorded',
                    'Disconnected as Recorded', 'Disk', 'SCSI Vendor', 'SCSI Model', 'SCSI Revision', 'Device Type',
                    'Capacity', 'Blocks', 'Block Size', 'Removable', 'Write Protect', 'SCSI Address', 'Vendor ID',
                    'Product ID', 'Manufacturer', 'Product', 'Serial Number', 'Port', 'Interface', 'Hostname',
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
        split = Counter()
        connections = syslog_connections(files, split, StorageAssembler, _storage_message)
        for kind, count in split.items():
            if kind not in USB_ONLY:
                counts[kind] += count
        for connection, disk in storage_rows(connections, counts):
            data_list.append((connection.connected, connection.disconnected, connection.connected_recorded,
                              connection.disconnected_recorded, *_disk_columns(disk), connection.vendor,
                              connection.product_id, connection.manufacturer, connection.product, connection.serial,
                              connection.port, connection.interface, connection.host,
                              '\n'.join(connection.sources)))
            for source in connection.sources:
                if source not in read:
                    read.append(source)
    if counts:
        logfunc('USB Storage Devices (syslog): ' + ', '.join(f'{count} {what}'
                                                              for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def linuxUsbStorageJournal(context):
    data_headers = (('Connected (UTC)', 'datetime'), ('Disconnected (UTC)', 'datetime'), 'Disk', 'SCSI Vendor',
                    'SCSI Model', 'SCSI Revision', 'Device Type', 'Capacity', 'Blocks', 'Block Size', 'Removable',
                    'Write Protect', 'SCSI Address', 'Vendor ID', 'Product ID', 'Manufacturer', 'Product',
                    'Serial Number', 'Port', 'Interface', 'Hostname', 'Boot ID', 'Source File')
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
    split = Counter()
    connections = journal_connections(journals, split, StorageAssembler, _storage_raw)
    for kind, count in split.items():
        if kind not in USB_ONLY:
            counts[kind] += count
    data_list = []
    read = []
    for connection, disk in storage_rows(connections, counts):
        data_list.append((connection.connected, connection.disconnected, *_disk_columns(disk), connection.vendor,
                          connection.product_id, connection.manufacturer, connection.product, connection.serial,
                          connection.port, connection.interface, connection.host, connection.boot,
                          '\n'.join(connection.sources)))
        for source in connection.sources:
            if source not in read:
                read.append(source)
    if counts:
        logfunc('USB Storage Devices (journal): ' + ', '.join(f'{count} {what}'
                                                               for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
