"""VirtualBox and VMware virtual machine configuration files on the host computer, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The settings tell an examiner which guest systems a computer held, and which disks, installer images, host folders and
network addresses each was given. The disks themselves are listed by the Virtual Disk Files artifact.
"""

__artifacts_v2__ = {
    "virtualBoxMachines": {
        "name": "VirtualBox Machines",
        "description": "VirtualBox virtual machines from their .vbox settings files: name, guest type, memory, "
                       "processors, adapter MAC addresses, attached disks and optical images, host folders shared "
                       "with the guest, snapshots, and whether a VirtualBox.xml found in the extraction lists the "
                       "machine.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Virtual Machines",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per .vbox file, read as XML. .vbox-prev files are not read. Last State Change is the "
                 "Machine element's lastStateChange, shown as UTC. A value in any other form is left blank. Run on"
                 " files VirtualBox 7.2.22 wrote on Windows 11 ARM for three test machines, none of which was "
                 "started. On those rows the time is within one second of the machine's creation. On one row "
                 "settings changed afterwards and the time did not move. What sets this value is not sourced here,"
                 " and a machine that has run was not tested. Architecture holds one value, ARM, on all 3 rows, "
                 "because each test machine was created with the ARM platform architecture. Memory (MB) is "
                 "RAMSize, which VBoxManage 7.2.22 documents as a size in MB. Disks and Optical Images are the "
                 "current attachments, so after a snapshot the disk shown is the differencing image and not the "
                 "base image. Each image identifier is resolved through the media registry in the same file or in "
                 "VirtualBox.xml. The VirtualBox.xml lookup was not exercised. A location is shown as stored and "
                 "can be relative to the machine's folder. An identifier no registry resolves is shown in place of"
                 " the location, lower-cased and without braces. That case was not exercised. Snapshots gives each"
                 " snapshot's name and stored time. Shared Folders gives the share name and host path. MAC "
                 "Addresses lists enabled adapters only, and no test adapter was disabled. Registered is Yes when "
                 "a VirtualBox.xml in the extraction lists the machine's identifier, No when one exists and does "
                 "not, and blank when no readable VirtualBox.xml was found in the folders searched. Blank was not "
                 "exercised. No means no VirtualBox.xml that was found lists the machine now. It does not say "
                 "whether it was ever listed, or when or why it left. A setting records what the machine was "
                 "configured with, not that it was used, and an attached image or shared folder need not still "
                 "exist.",
        "paths": ('*.vbox', '*/.VirtualBox/VirtualBox.xml', '*/.config/VirtualBox/VirtualBox.xml',
                  '*/Library/VirtualBox/VirtualBox.xml'),
        "output_types": "standard",
        "artifact_icon": "monitor",
        "sample_data": {
            "windows11_arm_virtualbox_known_20261121": "Windows 11 ARM, VirtualBox 7.2.22 | 3 rows",
        },
    },
    "virtualBoxRegistry": {
        "name": "VirtualBox Machine Registry",
        "description": "The machines VirtualBox's global VirtualBox.xml lists for a user, with the path of each "
                       "machine's settings file and whether that file is in the extraction.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Virtual Machines",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per MachineEntry in VirtualBox.xml, in the per-user folders the VirtualBox manual names:"
                 " .VirtualBox on Windows, .config/VirtualBox on Linux and Library/VirtualBox on macOS. The manual"
                 " says that folder can be moved, and a registry kept in another folder is not found. Only the "
                 "Windows folder was exercised. VirtualBox.xml-prev is not read. Settings File in Extraction is "
                 "Yes when a .vbox file in the extraction holds the same machine identifier. No can mean the file "
                 "was deleted, sits on a drive the extraction does not include, or could not be read. No was not "
                 "exercised in the test data. Run on one VirtualBox.xml written by VirtualBox 7.2.22 on Windows 11"
                 " ARM, listing two machines. In that known data the file was written under the lab account's "
                 "profile and was placed under the test profile, with the account name in its default machine "
                 "folder setting replaced.",
        "paths": ('*.vbox', '*/.VirtualBox/VirtualBox.xml', '*/.config/VirtualBox/VirtualBox.xml',
                  '*/Library/VirtualBox/VirtualBox.xml'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "list",
        "sample_data": {
            "windows11_arm_virtualbox_known_20261121": "Windows 11 ARM, VirtualBox 7.2.22 | 2 rows",
        },
    },
    "vmwareVmxConfigurations": {
        "name": "VMware VM Configurations",
        "description": "VMware virtual machines from their .vmx configuration files: name, guest type, memory, "
                       "processors, identifiers, adapter MAC addresses, attached disks and optical images, host folders "
                       "shared with the guest, and any annotation.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Virtual Machines",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per .vmx file holding a displayName, guestOS or virtualHW.version key. Keys are matched "
                 "without regard to case. The file is decoded with the character set its .encoding key names, or "
                 "as UTF-8 when the key is absent or the name is not recognised. Bytes that do not decode are "
                 "shown as replacement characters. Only UTF-8 and files with no .encoding key were in the test "
                 "data. Key meanings follow libvirt's VMX reader, src/vmx/vmx.c at "
                 "aceb5e0b4b78936055d794902b136d308fe221a6, including the hex escapes it removes from the name and"
                 " annotation. libvirt does not read uuid.location, so that value is shown as stored and its "
                 "meaning is not sourced here. vc.uuid is also shown as stored. Compared on 24 public .vmx files "
                 "from libvirt's test data at that commit against libvirt's expected output for each file. Name, "
                 "memory, processors, annotation, MAC addresses and disk and optical file names agreed on all 24. "
                 "Their file names begin esx (17), gsx (4), ws (2) and fusion (1). No VMware product ran on the "
                 "lab for this artifact. Shared Folders has no value on all 24 rows, because none of those files "
                 "had a shared folder, so that column is unexercised. A device or adapter is listed only when its "
                 "present key is true, and a shared folder only when its present and enabled keys are both true, "
                 "as in libvirt. Optical Images holds devices whose deviceType contains cdrom, files ending .iso "
                 "and SCSI passthrough devices under a cdrom folder. Disks holds the other file names. Both are "
                 "shown as stored and can be relative to the VM's folder. The placeholders auto detect and "
                 "emptyBackingString are left out, as is a device marked clientDevice, which libvirt's reader also"
                 " skips. MAC Addresses uses the static address when addressType is static and otherwise the "
                 "generated one. When that one is empty the other is shown. That fallback is not in libvirt and "
                 "was not exercised. This artifact reads no time from the file, so it adds nothing to the "
                 "timeline. 8 of the 24 test files hold a vm.createDate key, which is not read because its meaning"
                 " is not sourced here. A setting records what the machine was configured with, not that it was "
                 "used.",
        "paths": ('*.[Vv][Mm][Xx]',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "monitor",
        "sample_data": {
            "vmx_public_fixtures_libvirt_20261121": "libvirt test data, esx, gsx, ws and fusion .vmx files | 24 rows",
        },
    },
}

import codecs
import os
import re
from datetime import datetime, timezone
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc

_NS = '{http://www.virtualbox.org/}'
_VMX_LINE = re.compile(r'^\s*([^#=\s][^=]*?)\s*=\s*(.*?)\s*$')
_VMX_DEVICE = re.compile(r'^((?:scsi|ide|sata|nvme)\d+:\d+)\.filename$')
_VMX_NUMBERED = re.compile(r'^(ethernet|sharedfolder)(\d+)\.present$')


def _regular_files(context):
    return sorted({str(f) for f in context.get_files_found() if not os.path.isdir(str(f))})


def _is_registry(path):
    return os.path.basename(path).lower() == 'virtualbox.xml'


def _xml_root(path, label):
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        logfunc(f'{label}: {os.path.basename(path)} could not be read as XML ({type(exc).__name__})')
        return None
    if root.tag != f'{_NS}VirtualBox':
        logfunc(f'{label}: {os.path.basename(path)} is not a VirtualBox settings file, not read')
        return None
    return root


def _uuid(value):
    return (value or '').strip('{}').lower()


def _utc(value):
    try:
        return datetime.strptime(value or '', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def _media(root):
    """Image identifier to stored location, for every image in a media registry under root."""
    found = {}
    for registry in root.iter(f'{_NS}MediaRegistry'):
        for element in registry.iter():
            if element.tag in (f'{_NS}HardDisk', f'{_NS}Image') and element.get('location'):
                found[_uuid(element.get('uuid'))] = element.get('location')
    return found


def _read_registries(files):
    """(machine identifiers per registry file, global media) for the VirtualBox.xml files."""
    registries, media = {}, {}
    for path in files:
        root = _xml_root(path, 'VirtualBox')
        if root is None:
            continue
        registries[path] = [(_uuid(entry.get('uuid')), entry.get('uuid', ''), entry.get('src', ''))
                            for entry in root.iter(f'{_NS}MachineEntry')]
        media.update(_media(root))
    return registries, media


def _attached(hardware, media):
    """(disks, optical images) currently attached in a Hardware element."""
    disks, optical = [], []
    if hardware is None:
        return disks, optical
    for device in hardware.iter(f'{_NS}AttachedDevice'):
        image = device.find(f'{_NS}Image')
        if image is None:
            continue
        identifier = _uuid(image.get('uuid'))
        location = media.get(identifier, identifier)
        kind = (device.get('type') or '').lower()
        if kind == 'harddisk':
            disks.append(location)
        elif kind == 'dvd':
            optical.append(location)
    return disks, optical


def _machine_row(root, global_media):
    machine = root.find(f'{_NS}Machine')
    if machine is None:
        return None
    media = dict(global_media)
    media.update(_media(machine))
    hardware = machine.find(f'{_NS}Hardware')
    platform = machine.find(f'{_NS}Platform')
    memory = hardware.find(f'{_NS}Memory') if hardware is not None else None
    cpu = None
    for parent in (platform, hardware):  # settings before 7.1 keep CPU under Hardware
        if parent is not None and cpu is None:
            cpu = parent.find(f'{_NS}CPU')
    macs, shares = [], []
    if hardware is not None:
        for adapter in hardware.iterfind(f'{_NS}Network/{_NS}Adapter'):
            if adapter.get('enabled', 'false').lower() == 'true' and adapter.get('MACAddress'):
                macs.append(adapter.get('MACAddress'))
        for share in hardware.iterfind(f'{_NS}SharedFolders/{_NS}SharedFolder'):
            shares.append(f"{share.get('name', '')}: {share.get('hostPath', '')}")
    disks, optical = _attached(hardware, media)
    snapshots = [f"{snap.get('name', '')} ({snap.get('timeStamp', '')})" for snap in machine.iter(f'{_NS}Snapshot')]
    description = machine.find(f'{_NS}Description')
    architecture = platform.get('architecture', '') if platform is not None else ''
    return {
        'id': _uuid(machine.get('uuid')),
        'row': (_utc(machine.get('lastStateChange')), machine.get('name', ''), machine.get('OSType', ''), architecture,
                _number(memory.get('RAMSize')) if memory is not None else '',
                _number(cpu.get('count', '1')) if cpu is not None else '',
                '; '.join(macs), '; '.join(disks), '; '.join(optical), '; '.join(shares), '; '.join(snapshots),
                (description.text or '') if description is not None else '', _uuid(machine.get('uuid'))),
    }


def _number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return ''


def _machines(context):
    """(rows with their .vbox path, registries) for the VirtualBox artifacts."""
    files = _regular_files(context)
    registries, global_media = _read_registries([f for f in files if _is_registry(f)])
    rows = []
    for path in files:
        if not path.lower().endswith('.vbox'):
            continue
        root = _xml_root(path, 'VirtualBox Machines')
        if root is None:
            continue
        parsed = _machine_row(root, global_media)
        if parsed is None:
            logfunc(f'VirtualBox Machines: {os.path.basename(path)} holds no Machine element, not read')
            continue
        rows.append((path, parsed))
    return rows, registries


@artifact_processor
def virtualBoxMachines(context):
    rows, registries = _machines(context)
    listed = {entry[0] for entries in registries.values() for entry in entries}
    data_list = []
    for path, parsed in rows:
        registered = ('Yes' if parsed['id'] in listed else 'No') if registries else ''
        data_list.append(parsed['row'] + (registered, context.get_relative_path(path)))
    data_headers = (('Last State Change', 'datetime'), 'Name', 'Guest Type', 'Architecture', ('Memory (MB)', 'number'),
                    ('Processors', 'number'), 'MAC Addresses', 'Disks', 'Optical Images', 'Shared Folders', 'Snapshots',
                    'Description', 'Machine ID', 'Registered', 'Settings File')
    return data_headers, data_list, '\n'.join([path for path, _ in rows] + sorted(registries))


@artifact_processor
def virtualBoxRegistry(context):
    rows, registries = _machines(context)
    present = {parsed['id'] for _, parsed in rows}
    data_list = []
    for registry, entries in sorted(registries.items()):
        for identifier, _stored, source in entries:
            data_list.append((identifier, source, 'Yes' if identifier in present else 'No',
                              context.get_relative_path(registry)))
    data_headers = ('Machine ID', 'Settings File Path', 'Settings File in Extraction', 'Registry File')
    return data_headers, data_list, '\n'.join(sorted(registries))


def _unescape(text, escape):
    """Remove the escape-plus-two-hex-digits form libvirt's virVMXUnescapeHex removes."""
    pattern = re.escape(escape).encode() + rb'([0-9A-Fa-f]{2})'
    raw = re.sub(pattern, lambda m: bytes([int(m.group(1), 16)]), text.encode('utf-8', 'surrogateescape'))
    return raw.decode('utf-8', 'replace')


def _vmx_settings(data):
    """Lower-cased key to value from the bytes of a .vmx file."""
    encoding = 'utf-8'
    declared = re.search(rb'(?im)^\s*\.encoding\s*=\s*"?([A-Za-z0-9_.:-]+)"?', data)
    if declared:
        try:
            encoding = codecs.lookup(declared.group(1).decode('ascii')).name
        except LookupError:
            pass
    settings = {}
    for line in data.decode(encoding, 'replace').splitlines():
        match = _VMX_LINE.match(line)
        if match:
            value = match.group(2)
            if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            settings[match.group(1).lower()] = value
    return settings


def _true(settings, key):
    return settings.get(key, '').strip().lower() in ('true', 'yes', '1')


def _vmx_row(settings):
    disks, optical = [], []
    for key in sorted(settings):
        match = _VMX_DEVICE.match(key)
        if not match or not _true(settings, f'{match.group(1)}.present'):
            continue
        name = settings[key]
        if not name or name.lower() == 'auto detect' or name == 'emptyBackingString':
            continue
        if _true(settings, f'{match.group(1)}.clientdevice'):
            continue  # libvirt's reader skips these too
        kind = settings.get(f'{match.group(1)}.devicetype', '').lower()
        is_optical = ('cdrom' in kind or name.lower().endswith('.iso')
                      or (kind == 'scsi-passthru' and '/cdrom/' in name.lower()))
        (optical if is_optical else disks).append(name)
    macs, shares = [], []
    numbered = sorted((match.group(1), int(match.group(2))) for match in map(_VMX_NUMBERED.match, settings) if match)
    for family, number in numbered:
        prefix = f'{family}{number}'
        if not _true(settings, f'{prefix}.present'):
            continue
        if family == 'ethernet':
            static = settings.get(f'{prefix}.addresstype', '').lower() == 'static'
            order = ('address', 'generatedaddress') if static else ('generatedaddress', 'address')
            mac = next((settings[f'{prefix}.{name}'] for name in order if settings.get(f'{prefix}.{name}')), '')
            if mac:
                macs.append(mac)
        elif _true(settings, f'{prefix}.enabled') and settings.get(f'{prefix}.hostpath'):
            shares.append(f"{settings.get(f'{prefix}.guestname', '')}: {settings[f'{prefix}.hostpath']}")
    name = _unescape(_unescape(settings.get('displayname', ''), '%'), '|')
    return (name, settings.get('guestos', ''), _number(settings.get('memsize')), _number(settings.get('numvcpus', '1')),
            settings.get('virtualhw.version', ''), '; '.join(macs), '; '.join(disks), '; '.join(optical),
            '; '.join(shares), _unescape(settings.get('annotation', ''), '|'), settings.get('uuid.bios', ''),
            settings.get('uuid.location', ''), settings.get('vc.uuid', ''))


@artifact_processor
def vmwareVmxConfigurations(context):
    data_list, sources = [], []
    for path in _regular_files(context):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'VMware VM Configurations: {os.path.basename(path)} could not be read ({type(exc).__name__})')
            continue
        settings = _vmx_settings(data)
        if not {'displayname', 'guestos', 'virtualhw.version'} & set(settings):
            logfunc(f'VMware VM Configurations: {os.path.basename(path)} holds none of the expected keys, not read')
            continue
        data_list.append(_vmx_row(settings) + (context.get_relative_path(path),))
        sources.append(path)
    data_headers = ('Name', 'Guest Type', ('Memory (MB)', 'number'), ('Processors', 'number'), 'Hardware Version',
                    'MAC Addresses', 'Disks', 'Optical Images', 'Shared Folders', 'Annotation', 'BIOS UUID',
                    'uuid.location', 'vc.uuid', 'Configuration File')
    return data_headers, data_list, '\n'.join(sources)
