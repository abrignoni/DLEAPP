"""Parallels Desktop virtual machines on the macOS host: the VM registry and each VM bundle."""

__artifacts_v2__ = {
    "parallelsVmRegistry": {
        "name": "Parallels VM Registry",
        "description": "Virtual machines registered with Parallels Desktop on the Mac, from its VM "
                       "directory list: each VM's name, folder, who registered it and when, and the "
                       "time stored for its last state change.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-17",
        "last_update_date": "2026-11-17",
        "requirements": "none",
        "category": "macOS - Virtual Machines",
        "platforms": ("macOS",),
        "notes": "Reads /Library/Preferences/Parallels/vmdirectorylist.desktop.xml, the VM directory list of Parallels Desktop, one row per VirtualMachine element of each VmDirectory, those under OtherVirtualMachines included. Most element names also appear in the VmDirectories.xsd schema of OpenVZ libprlxmlmodel (https://github.com/OpenVZ/libprlxmlmodel/blob/90ed1b5df2167816ce5924d5980764a81544e383/Schema/VmDirectories.xsd, commit dated 2024-03-12), a Virtuozzo library whose root element is VirtuozzoVmDirectories; StateChangeDateTime and OtherVirtualMachines are not in that schema. The behaviour described here was measured on known data recorded on one Mac running Parallels Desktop 27.1.0 with four VMs (Windows 11, Ubuntu 26.04, Fedora 44, macOS 27); power actions were recorded on two of them. None of the public macOS images tested (dleapp_macos_bigsur, evidencelocker_macos14, mvs2026_macbookpro_macos15, magnet2021_macos_bigsur) holds a .pvm or .macvm bundle, so there is no public test image. State Changed (UTC) is StateChangeDateTime. In the known data it changed at 1 start, 4 suspends, 4 resumes and 1 stop, and on one VM it also moved by 1 second after a resume with no state change logged. Over those 10 changes it fell 1 to 20 seconds before the UTC time of the step-log entry that first recorded the new state (a watcher polled every 5 seconds and logged again 20 seconds after each change), while the Mac's offset was -0500, so it is read as UTC and as the time stored for the last state change, not of the last run. Registered (UTC) is RegistrationDateTime, stored without a zone and read as UTC. On the macOS VM it equalled the VM's creation time in its config.pvs, which matched the bundle folder's creation time in UTC to the second; on the Windows VM it was 1 hour 59 minutes 59 seconds before that creation time, which is not explained here; on the two Linux VMs it was 19 and 62 days after the creation time and equalled VmUptimeStartDateTime. The zone is established on the macOS VM only. Last Running State is LastRunningState as stored; the schema types it as a boolean. In the known data it was 1 after each start or resume and 0 after each suspend and the stop, and at the start of the recording one stopped VM held 1, so neither value shows whether a VM was running, suspended or stopped. A non-zero Suspend Memory File Size in Parallels VM Bundles was seen only on suspended VMs. VM Type is VmType as stored. The SDK header names 0 a virtual machine and 1 a container (https://github.com/OpenVZ/libprlsdk/blob/eb2dc030a827e431641d5771e964ef3b6c401d9b/Sources/SDK/Include/PrlEnums.h); the macOS VM, a .macvm bundle, held 2, which the header does not name. VM Config Path is VmHome as stored; in the known data it was the host path of the VM's config.pvs. Registered By is RegisteredBy and VM Directory Name the directory's UserFriendlyName, as stored. Registered By and VM Directory Name held one value on all 3 rows; the file held two VmDirectory elements and only one held VMs. Registry Section is the element the row came from, VirtualMachine or OtherVirtualMachines; on the tested Mac the macOS VM was the one under OtherVirtualMachines, and what decides the section is not established. In the known data, removing a VM with File > Remove > Move to Trash deleted its element from this file entirely, so that VM has no row here; its bundle went to the Trash with the same files and is a row of Parallels VM Bundles. A copy of the file under System/Volumes/Data is read once. Not reported: ChangeDateTime, which did not change on any power action in the known data and whose meaning is not established, the VM UUIDs, the password hash fields and the network settings. Other Parallels stores are not read: com.parallels.Parallels Desktop.plist, which held window and console state in keys named by VM UUID, the parallels.log files, whose lines carry a month and day with no year, and the files beside this one in /Library/Preferences/Parallels.",
        "paths": ('*/Library/Preferences/Parallels/vmdirectorylist.desktop.xml',),
        "output_types": "standard",
        "artifact_icon": "monitor",
    },
    "parallelsVmBundles": {
        "name": "Parallels VM Bundles",
        "description": "Parallels Desktop virtual machine bundles (.pvm and .macvm folders) found "
                       "anywhere in the extraction: each VM's stored creation time, its guest operating "
                       "system, its serial number, its counted run time and the size of its suspend "
                       "memory file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-17",
        "last_update_date": "2026-11-17",
        "requirements": "none",
        "category": "macOS - Virtual Machines",
        "platforms": ("macOS",),
        "notes": "One row per config.pvs directly inside a folder whose name ends .pvm or .macvm, anywhere in the extraction (the Parallels folder in a user's home folder, a Trash folder, any other volume), with the VmInfo.pvi in the same folder. A config.pvs deeper inside a bundle, such as in its Snapshots folder, is not read, and a copy of a bundle under System/Volumes/Data is reported once. The behaviour described here was measured on known data recorded on one Mac running Parallels Desktop 27.1.0 with four VMs (Windows 11, Ubuntu 26.04, Fedora 44, macOS 27); power actions were recorded on two of them. None of the public macOS images tested (dleapp_macos_bigsur, evidencelocker_macos14, mvs2026_macbookpro_macos15, magnet2021_macos_bigsur) holds a .pvm or .macvm bundle, so there is no public test image. Created (UTC) is VmCreationDate in config.pvs, stored without a zone: on the Windows and macOS VMs it matched the bundle folder's creation time in UTC to the second; on the Ubuntu VM it was 26 hours and on the Fedora VM about 1 hour 38 minutes before the folder's creation time, which is not explained here. Uptime (seconds) is VmUptimeInSeconds and Uptime Counted From (UTC) VmUptimeStartDateTime, as stored. The zone of Uptime Counted From is not established on its own: on two VMs it equalled the creation time and on two the registration time in the VM directory list. On the Fedora VM the uptime grew at each of 3 suspends and 1 stop by the length of the run that ended (110, 130, 11 and 81 seconds against 111, 131, 12 and 82 seconds between the stored state-change times of the start or resume and the suspend or stop); on the Ubuntu VM it grew 333,810 seconds over a 342,909 second interval, a difference not explained here. Uptime Counted From did not change. Configured Guest OS is the guest OS version code OsNumber in config.pvs named as the SDK header's lookup function PVS_GUEST_TO_STRING names it (https://github.com/OpenVZ/libprlsdk/blob/eb2dc030a827e431641d5771e964ef3b6c401d9b/Sources/SDK/Include/PrlOses.h), or else the family code OsType named by the same function, or else both codes as stored. Windows 11 (0x813), Ubuntu (0x90A) and Fedora (0x907) matched their guests; the macOS VM held 0x703, which the function names only Mac OS X. Guest OS Reported, Guest OS Version Reported, Guest Device Name and VM Serial Number are RealOsType, RealOsVersion, DeviceName and SerialNumber of VmInfo.pvi, as stored. The content of VmInfo.pvi changed within 25 seconds of the Ubuntu VM's resume; on the Fedora VM only the file's modification time moved at each start and resume. Guest Device Name held a value only for the Windows VM; the two Linux VMs left it empty, and the macOS VM had no VmInfo.pvi. VM UUID is VmUuid without its braces. Suspend Memory File Size (bytes) is the size of the .mem file directly in the bundle (the largest, if there are several), listed with the seeker's peek(), so the file is not copied into the report; a single-file input cannot be listed this way and the run log says so. In the known data the file held 231,903,296 to 232,230,976 bytes over three suspends of the Fedora VM and 940,281,920 bytes over one suspend of the Ubuntu VM, 0 bytes after each resume, and was gone after the stop from the app; at the start of the recording the stopped Fedora VM also held a 0-byte file, so 0 does not show the VM was running; the .macvm bundle had none. A blank means no .mem file was listed: none was found, or the input could not be listed. VM Type is VmType as stored (see Parallels VM Registry). Bundle Path is the bundle folder inside the extraction, with any System/Volumes/Data prefix removed; in the known data a VM removed with File > Remove > Move to Trash left its bundle in the user's Trash with the same files. Not read: config.pvs.backup, the virtual disk (.hdd) and NVRAM files, the .mem file's contents and the .mem.sh file beside it, statistic.log and parallels.log.",
        "paths": ('*.pvm/config.pvs', '*.macvm/config.pvs', '*.pvm/VmInfo.pvi', '*.macvm/VmInfo.pvi'),
        "output_types": "standard",
        "artifact_icon": "monitor",
    },
}

import datetime
import posixpath
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative
from scripts.search_files import PeekUnsupported

_BUNDLE_SUFFIXES = ('.pvm', '.macvm')

# Guest OS family (PVS_GUEST_TYPE_*) and version (PVS_GUEST_VER_*) codes with the names the header's own
# lookup function PVS_GUEST_TO_STRING returns for them: OpenVZ/libprlsdk
# Sources/SDK/Include/PrlOses.h at eb2dc030a827e431641d5771e964ef3b6c401d9b. A code it does not name is shown as stored.
_GUEST_NAMES = {
    0x7: 'Mac OS X', 0x8: 'Windows', 0x9: 'Linux', 0xA: 'FreeBSD', 0xB: 'OS/2', 0xC: 'MS-DOS',
    0xD: 'NetWare', 0xE: 'Solaris', 0xF: 'Chrome OS', 0x10: 'Android', 0xFF: 'Other',
    0x701: 'Mac OS X', 0x702: 'Mac OS X', 0x703: 'Mac OS X', 0x801: 'Windows 3.11',
    0x802: 'Windows 95', 0x803: 'Windows 98', 0x804: 'Windows ME', 0x805: 'Windows NT',
    0x806: 'Windows 2000', 0x807: 'Windows XP', 0x808: 'Windows Server 2003',
    0x809: 'Windows Vista', 0x80A: 'Windows Server 2008', 0x80B: 'Windows 7', 0x80C: 'Windows 8',
    0x80D: 'Windows Server 2012', 0x80E: 'Windows 8.1', 0x810: 'Windows Server 2016',
    0x811: 'Windows Server 2019', 0x812: 'Windows Server 2022', 0x813: 'Windows 11',
    0x8FF: 'Other Windows', 0x901: 'Red Hat Enterprise Linux 6 and older',
    0x902: 'SUSE Linux Enterprise', 0x903: 'Mandriva Linux', 0x904: 'Other Linux kernel 2.4',
    0x905: 'Other Linux kernel 2.6', 0x906: 'Debian GNU/Linux', 0x907: 'Fedora Linux',
    0x908: 'Fedora Core 5 Linux', 0x909: 'Xandros Linux', 0x90A: 'Ubuntu Linux',
    0x90B: 'SUSE Linux Enterprise Server 9', 0x90C: 'Red Hat Enterprise Server 3',
    0x90D: 'CentOS Linux 6 and older', 0x90E: 'Red Hat Linux', 0x90F: 'OpenSUSE Linux',
    0x910: 'Virtuozzo Cloud Server', 0x911: 'Mageia Linux', 0x912: 'Mint Linux',
    0x913: 'Red Hat Enterprise Linux', 0x914: 'CentOS Linux', 0x915: 'Virtuozzo Linux 6',
    0x916: 'Virtuozzo Linux', 0x919: 'CloudLinux 6 and older', 0x91A: 'Red Hat Enterprise Linux',
    0x91B: 'CentOS Linux', 0x91C: 'Virtuozzo Linux', 0x91D: 'CloudLinux', 0x91E: 'CloudLinux',
    0x91F: 'Red Hat Enterprise Linux', 0x920: 'AlmaLinux', 0x9FF: 'Other Linux',
    0xA01: 'FreeBSD 4.x', 0xA02: 'FreeBSD 5.x', 0xA03: 'FreeBSD 6.x', 0xA04: 'FreeBSD 7.x',
    0xA05: 'FreeBSD 8.x', 0xAFF: 'Other FreeBSD', 0xB01: 'OS/2 Warp 3', 0xB02: 'OS/2 Warp 4',
    0xB03: 'OS/2 Warp 4.5', 0xB04: 'eComStation 1.1', 0xB05: 'eComStation 1.2', 0xBFF: 'Other OS/2',
    0xC01: 'MS-DOS 6.22', 0xCFF: 'Other DOS', 0xD01: 'NetWare 4.x', 0xD02: 'NetWare 5.x',
    0xD03: 'NetWare 6.x', 0xDFF: 'Other NetWare', 0xE01: 'Solaris 9', 0xE02: 'Solaris 10',
    0xE03: 'Solaris 11', 0xEFF: 'Other Solaris', 0xF01: 'Chrome OS', 0xFFF: 'Other Chrome OS',
    0xFF01: 'QNX', 0xFF02: 'OpenStep', 0xFFFF: 'Other',
}


def _text(element, path):
    if element is None:
        return ''
    value = element.findtext(path)
    return value.strip() if value else ''


def _utc(value):
    """A stored 'YYYY-MM-DD hh:mm:ss' as a UTC datetime, or '' when blank or another shape."""
    if not value:
        return ''
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        logfunc(f'Parallels: a time stored as {value!r} is not in the expected form and is left blank')
        return ''


def _parse(path, label):
    try:
        return ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as ex:
        logfunc(f'Parallels: {label} could not be read as XML: {ex}')
        return None


def _bundle_of(relative):
    """The VM bundle folder a path is in (the nearest folder ending .pvm or .macvm), canonical."""
    parts = canonical_relative(relative).split('/')
    for index in range(len(parts) - 1, -1, -1):
        if parts[index].endswith(_BUNDLE_SUFFIXES):
            return '/'.join(parts[:index + 1])
    return ''


def _configured_os(os_type, os_number):
    """The header's name for the stored version code, else for the family code, else both codes as stored."""
    for code in (os_number, os_type):
        try:
            name = _GUEST_NAMES.get(int(code))
        except ValueError:
            name = None
        if name:
            return name
    if not os_type and not os_number:
        return ''
    return f'OsType {os_type}, OsNumber {os_number} (as stored)'


@artifact_processor
def parallelsVmRegistry(context):
    data_headers = (('State Changed (UTC)', 'datetime'), ('Registered (UTC)', 'datetime'), 'VM Name',
                    'Last Running State', 'VM Type', 'VM Config Path', 'Registered By',
                    'VM Directory Name', 'Registry Section')
    data_list, sources, seen = [], [], set()
    for file_found in sorted(context.get_files_found()):
        relative = context.get_relative_path(file_found)
        view = canonical_relative(relative)
        if view in seen:
            logfunc(f'Parallels VM Registry: {relative} is another view of a registry already read')
            continue
        seen.add(view)
        root = _parse(file_found, relative)
        if root is None:
            sources.append(file_found)
            continue
        sources.append(file_found)
        for directory in root.findall('VmDirectory'):
            owner = _text(directory, 'UserFriendlyName')
            sections = (('VirtualMachine', directory.findall('VirtualMachine')),
                        ('OtherVirtualMachines', directory.findall('OtherVirtualMachines/VirtualMachine')))
            for section, machines in sections:
                for vm in machines:
                    data_list.append((
                        _utc(_text(vm, 'StateChangeDateTime')), _utc(_text(vm, 'RegistrationDateTime')),
                        _text(vm, 'VmName'), _text(vm, 'LastRunningState'), _text(vm, 'VmType'),
                        _text(vm, 'VmHome'), _text(vm, 'RegisteredBy'), owner, section))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def parallelsVmBundles(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Uptime Counted From (UTC)', 'datetime'),
                    'VM Name', ('VM UUID', 'hash'), 'Configured Guest OS', 'Guest OS Reported',
                    'Guest OS Version Reported', 'Guest Device Name', 'VM Serial Number',
                    ('Uptime (seconds)', 'number'), ('Suspend Memory File Size (bytes)', 'number'),
                    'VM Type', 'Bundle Path')
    configs, infos = {}, {}
    for file_found in sorted(context.get_files_found()):
        relative = context.get_relative_path(file_found)
        bundle = _bundle_of(relative)
        name = posixpath.basename(relative.replace('\\', '/'))
        if not bundle or posixpath.dirname(canonical_relative(relative)) != bundle:
            continue
        target = configs if name == 'config.pvs' else infos if name == 'VmInfo.pvi' else None
        if target is not None and bundle not in target:
            target[bundle] = (file_found, relative)

    memory = {}
    seeker = context.get_seeker()
    if configs and seeker is not None and hasattr(seeker, 'peek'):
        for pattern in ('*.pvm/*.mem', '*.macvm/*.mem'):
            try:
                peeked = seeker.peek(pattern, 0)
            except PeekUnsupported as ex:
                logfunc(f'Parallels VM Bundles: suspend memory sizes not read: {ex}')
                break
            for item in peeked:
                bundle = _bundle_of(str(item.path))
                if bundle and posixpath.dirname(canonical_relative(str(item.path))) == bundle:
                    memory[bundle] = max(memory.get(bundle, 0), item.size)

    data_list, sources = [], []
    for bundle in sorted(configs):
        file_found, relative = configs[bundle]
        root = _parse(file_found, relative)
        sources.append(file_found)
        if root is None:
            continue
        ident = root.find('Identification')
        general = root.find('Settings/General')
        info_root = None
        if bundle in infos:
            info_root = _parse(infos[bundle][0], infos[bundle][1])
            sources.append(infos[bundle][0])
        guest = info_root.find('GuestOsInformation') if info_root is not None else None
        uptime = _text(ident, 'VmUptimeInSeconds')
        data_list.append((
            _utc(_text(ident, 'VmCreationDate')), _utc(_text(ident, 'VmUptimeStartDateTime')),
            _text(ident, 'VmName'), _text(ident, 'VmUuid').strip('{}'),
            _configured_os(_text(general, 'OsType'), _text(general, 'OsNumber')),
            _text(guest, 'RealOsType'), _text(guest, 'RealOsVersion'),
            _text(guest, 'DeviceName'), _text(guest, 'SerialNumber'),
            int(uptime) if uptime.isdigit() else uptime, memory.get(bundle, ''),
            _text(ident, 'VmType'), bundle))
    return data_headers, data_list, '\n'.join(sources)
