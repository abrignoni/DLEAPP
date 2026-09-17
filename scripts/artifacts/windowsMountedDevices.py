"""Windows MountedDevices parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange and RegRipper mountdev artifacts that read
the same SYSTEM\\MountedDevices key; the implementation reads the hive directly
and is not ported from those artifacts.
"""

import struct
import uuid

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The SYSTEM hive keeps a top-level MountedDevices key (the Mount Manager's
# persistent name database): one value per mount point, named either
# \DosDevices\<letter>: (a drive letter) or \??\Volume{GUID} (a mounted volume).
# The value's binary data is the device the mount point maps to, in one of three
# shapes: a UTF-16LE device symbolic-link target, a 12-byte MBR fixed-disk record
# (4-byte disk signature and 8-byte partition offset), or a 24-byte GPT record
# (the ASCII marker DMIO:ID: and the 16-byte GPT partition GUID).
# Format reference: libyal winreg-kb, docs/sources/system-keys/Mounted-devices.md
# (pinned commit d149aff1); the same key is read by RegRipper's mountdev plugin.

__artifacts_v2__ = {
    "mountedDevices": {
        "name": "Mounted Devices",
        "description": "Drive letters and mounted volumes recorded in the "
                       "Windows MountedDevices key of the SYSTEM hive, with the "
                       "device each one maps to: a USB storage device path with "
                       "its serial, an optical or floppy device path, an MBR "
                       "disk signature and partition offset, or a GPT partition "
                       "GUID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per value in the SYSTEM hive's top-level "
                 "MountedDevices key (the Mount Manager's persistent name "
                 "database), named in the report's located-at line. Mount Point "
                 "is the value name. Kind is read from that name: a name "
                 "beginning "
                 "\\DosDevices\\ is a Drive Letter and a name beginning "
                 "\\??\\Volume is a Volume GUID; any other name (for example a "
                 "#{GUID} entry) is left blank. Device is decoded from the "
                 "value's binary data, which takes one of three shapes "
                 "documented by libyal winreg-kb and read by RegRipper's "
                 "mountdev plugin. A value stored as UTF-16LE text beginning "
                 "\\??\\ or _??_ is a device symbolic-link target and is shown "
                 "as stored: a _??_USBSTOR#... target carries the device serial "
                 "(the segment between the second and third # signs), which "
                 "matches the Serial column of the USB Storage Devices artifact, "
                 "so a drive letter or volume can be tied to a USB device row "
                 "there; other \\??\\ targets name non-USB devices, for example "
                 "\\??\\SCSI or \\??\\IDE for an optical drive and \\??\\FDC for "
                 "a floppy, with the device given in the path text. A 12-byte "
                 "value is an MBR fixed disk: a 4-byte disk signature (shown "
                 "byte-reversed from storage so it reads as the disk identifier "
                 "Windows Disk Management shows, matching RegRipper's mountdev) "
                 "followed by the 8-byte partition offset in bytes (1048576 and "
                 "65536 on the tested images). A 24-byte value is a GPT fixed "
                 "disk: the 8-byte ASCII signature DMIO:ID: followed by the "
                 "16-byte GPT partition GUID (a little-endian GUID that "
                 "winreg-kb documents as the identifier mapping the mount point "
                 "to its GPT partition-table entry). Any other shape is shown as "
                 "hex as stored. MountedDevices maps mount points to devices and "
                 "carries no timestamps, so a row records that a mount point was "
                 "mapped to a device, not when the mapping was made or by whom, "
                 "and the key can retain entries for devices that are not "
                 "presently mounted (Windows removes those with mountvol /r). "
                 "Reading the hive requires python-registry. Format reference: "
                 "libyal "
                 "winreg-kb Mounted-devices at commit d149aff1, "
                 "https://github.com/libyal/winreg-kb/blob/"
                 "d149aff1b8ff97e1cc8d7416fc583b964bad4ccd/docs/sources/"
                 "system-keys/Mounted-devices.md",
        "paths": ('*/Windows/System32/config/SYSTEM',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows "
                                "(2 GPT partitions, 1 USB volume)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 6 rows "
                              "(2 MBR disks, optical and floppy)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows "
                              "(GPT partition, USB, optical)",
        },
    },
}


def _kind(name):
    if name.startswith('\\DosDevices\\'):
        return 'Drive Letter'
    if name.startswith('\\??\\Volume'):
        return 'Volume GUID'
    return ''


def _value_bytes(value):
    """Read a MountedDevices value as raw bytes. These are REG_BINARY, so value()
    returns the bytes; fall back to raw_data() if a value ever stores a type that
    value() cannot decode."""
    try:
        data = value.value()
    except Exception:  # pylint: disable=broad-exception-caught
        data = None
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    try:
        raw = value.raw_data()
    except Exception:  # pylint: disable=broad-exception-caught
        return b''
    return bytes(raw) if isinstance(raw, (bytes, bytearray)) else b''


def _decode_device(data):
    """Decode the binary value into a human-readable device reference, following
    the three shapes libyal winreg-kb documents for MountedDevices values."""
    if not data:
        return ''
    # A device symbolic-link target is stored as UTF-16LE text beginning \??\
    # (optical, ATAPI, floppy, volume) or _??_ (USB storage).
    text = data.decode('utf-16-le', 'replace').rstrip('\x00')
    if text.startswith('\\??\\') or text.startswith('_??_'):
        return text
    # A 12-byte value is an MBR fixed disk: 4-byte disk signature (shown
    # byte-reversed from storage to read as the disk identifier) plus an 8-byte
    # partition offset in bytes.
    if len(data) == 12:
        signature = data[3::-1].hex()
        offset = struct.unpack('<Q', data[4:12])[0]
        return f"disk signature {signature} offset {offset}"
    # A 24-byte value is a GPT fixed disk: the 8-byte ASCII signature DMIO:ID:
    # and the 16-byte GPT partition GUID (little-endian GUID).
    if len(data) == 24:
        marker = data[:8].decode('ascii', 'replace')
        guid = uuid.UUID(bytes_le=data[8:24])
        if marker.isprintable():
            return f"{marker} {guid}"
        return f"{data[:8].hex()} {guid}"
    # Anything else is reported as stored.
    return data.hex()


@artifact_processor
def mountedDevices(context):
    data_headers = ('Mount Point', 'Kind', 'Device')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Mounted Devices: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()]:
        relative_source = context.get_relative_path(source)
        try:
            reg = Registry.Registry(source)
            key = reg.open('MountedDevices')
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Mounted Devices: could not read {relative_source}: {exc}')
            continue
        rows_here = 0
        for value in key.values():
            name = value.name()
            data_list.append((
                name, _kind(name), _decode_device(_value_bytes(value))))
            rows_here += 1
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
