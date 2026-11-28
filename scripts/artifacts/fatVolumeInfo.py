"""FAT12, FAT16, FAT32 and exFAT volume information from the boot sector, for DLEAPP.

Author: @AlexisBrignoni, Claude.

These file systems keep no file holding the boot sector, so the module reads it through the volumes the raw image
seeker already lists, and reads nothing for inputs that are not disk images.
"""

import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import qnxprobe

_LABEL = 'FAT and exFAT Volume Information'
_FAT_KINDS = {'fat12': 'FAT12', 'fat16': 'FAT16', 'fat32': 'FAT32'}
_KINDS = {**_FAT_KINDS, 'exfat': 'exFAT'}
_ENTRY_SIZE = 32
_ATTR_VOLUME = 0x08
_ATTR_LONG_NAME = 0x0F
_DELETED = 0xE5
_EXFAT_LABEL_ENTRY = 0x83
_EXTENDED_BOOT_SIGNATURE = 0x29

__artifacts_v2__ = {
    "fatVolumeInfo": {
        "name": "FAT and exFAT Volume Information",
        "description": "FAT12, FAT16, FAT32 and exFAT volumes read from a raw image: serial number, labels, sector "
                       "and cluster sizes, size and where each starts.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-28",
        "requirements": "none",
        "category": "Multi-platform - File System",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per FAT12, FAT16, FAT32 or exFAT volume the raw image reader lists and can read. A volume it "
                 "lists without a reader, or whose boot sector is shorter than 120 bytes, gives a log line and no row. "
                 "Neither case occurred in the runs. Other inputs give no row. "
                 "FAT fields follow the Linux boot sector structure (https://github.com/torvalds/linux/blob/"
                 "adc218676eef25575469234709c2d87185ca223a/include/uapi/linux/msdos_fs.h#L108-L159). exFAT fields follow "
                 "Microsoft's specification (https://github.com/MicrosoftDocs/win32/blob/"
                 "8ea4fb742b61a0fcc85672f30cf433ba087bb1a0/desktop-src/FileIO/exfat-specification.md#L324-L407, and "
                 "#L2599-L2680 for the label). Serial Number is the stored 32-bit value in hex, the form the Shell Links "
                 "artifacts use for Drive Serial. On FAT it is read, with the boot sector label, only when the extended "
                 "boot signature is 0x29 (https://github.com/dosfstools/dosfstools/blob/"
                 "697f7692c951173c1b732901e13f72bd3182d575/src/mkfs.fat.c#L144), and is blank otherwise. All 9 FAT "
                 "volumes run carried 0x29. Volume Label (Root Directory) is the first in-use root directory entry with "
                 "the volume label attribute (0x08, msdos_fs.h#L40 at the same commit) that is not a long-name entry. On "
                 "exFAT it is the first Volume Label entry (type 0x83). Deleted label entries are not read. Volume Label "
                 "(Root Directory) has no value on the 3 Windows corpus volumes: no in-use label entry was found in their "
                 "root directories. Volume Label (Boot Sector) is a separate field in the boot sector. The two differed on "
                 "4 of the 9 FAT volumes run. The exFAT boot sector has no label field. Its 8 bytes at offset 3 are the "
                 "FileSystemName field, which this artifact does not report. Volume Label (Boot Sector) and OEM Name are "
                 "blank for exFAT. OEM Name is the 8 bytes at boot sector offset 3. OEM Name and the FAT labels are read "
                 "as code page 437 text, cut at the first null byte, with trailing spaces removed. No label or OEM Name "
                 "with non-ASCII bytes was run. Volume Offset is the byte offset the raw image reader gives for the start "
                 "of the volume. On the 10 volumes run it was the offset from the start of the disk the image holds: the "
                 "partition's starting sector times 512 on 5 volumes, and 0 on the 5 that fill the image. A volume inside "
                 "a RAID array, an LVM group or an encrypted container was not run. On the 6 corpus volumes and 4 test "
                 "images (admin/test/data/raw_images), Serial Number, Bytes per Sector and Cluster Size matched The Sleuth "
                 "Kit 4.15.0 fsstat in value (fsstat prints the serial in lower case), as did the boot sector label and "
                 "OEM Name on the 9 FAT volumes. The root directory label equalled fsstat on 5 volumes: 3 with no in-use "
                 "label entry (both blank), 1 FAT32 entry with attribute 0x08 and the exFAT test image. On the other 5, "
                 "fsstat printed it blank and the label entry had attribute 0x28 (volume label plus archive), which this "
                 "artifact reads as a label. FAT12, FAT16 and exFAT were each run on one test image. The 6 corpus volumes "
                 "are FAT32. Dirty flags, free space and backup boot sectors are not read.",
        "paths": None,
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 1 row",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the image is a single NTFS volume)",
        },
    },
}


def _text(raw, encoding='cp437'):
    return raw.split(b'\x00')[0].decode(encoding, 'replace').rstrip(' ')


def boot_fields(sector, kind):
    """The fields of a FAT or exFAT boot sector, or None when the sector is too short to hold them."""
    if len(sector) < 120:
        return None
    if kind == 'exfat':
        bytes_per_sector = 1 << sector[108]
        sectors_per_cluster = 1 << sector[109]
        total_sectors = struct.unpack_from('<Q', sector, 72)[0]
        serial = f"{struct.unpack_from('<I', sector, 100)[0]:08X}"
        oem = label = ''
    else:
        bytes_per_sector = struct.unpack_from('<H', sector, 11)[0]
        sectors_per_cluster = sector[13]
        total_sectors = struct.unpack_from('<H', sector, 19)[0] or struct.unpack_from('<I', sector, 32)[0]
        extended = 64 if kind == 'fat32' else 36
        oem = _text(sector[3:11])
        serial = label = ''
        if sector[extended + 2] == _EXTENDED_BOOT_SIGNATURE:
            serial = f"{struct.unpack_from('<I', sector, extended + 3)[0]:08X}"
            label = _text(sector[extended + 7:extended + 18])
    return {'serial': serial, 'boot_label': label, 'oem': oem, 'bytes_per_sector': bytes_per_sector,
            'sectors_per_cluster': sectors_per_cluster, 'cluster': bytes_per_sector * sectors_per_cluster,
            'total_sectors': total_sectors, 'size': total_sectors * bytes_per_sector}


def root_label(raw, kind):
    """The volume label a root directory holds, or '' when it holds none."""
    for offset in range(0, len(raw) - _ENTRY_SIZE + 1, _ENTRY_SIZE):
        entry = raw[offset:offset + _ENTRY_SIZE]
        if entry[0] == 0x00:
            break
        if kind == 'exfat':
            if entry[0] == _EXFAT_LABEL_ENTRY:
                return entry[2:2 + min(entry[1], 11) * 2].decode('utf-16-le', 'replace')
        elif entry[0] != _DELETED and entry[11] & 0x3F != _ATTR_LONG_NAME and entry[11] & _ATTR_VOLUME:
            return _text(entry[:11])
    return ''


def _root_directory(walker, kind):
    """The root directory's bytes, read without the walker's own folder reader, which records
    damage and cluster claims for the walk the seeker has already made."""
    # pylint: disable=protected-access
    if kind == 'exfat':
        return walker._read(walker.root_clus, 0, False)
    if walker.root_clus == 0 and walker.FAT_BITS != 32:
        # FAT12 and FAT16 keep the root directory in a fixed run before the data area
        return qnxprobe.read_at(walker.fh, walker.root_dir_start, walker.root_dir_bytes)
    return b''.join(qnxprobe.read_at(walker.fh, walker._cluster_off(clus), walker.cluster_bytes)
                    for clus in walker._chain(walker.root_clus))


def volume_rows(volumes):
    """One row for each FAT and exFAT volume among the seeker's volumes."""
    rows = []
    for volume in volumes or ():
        kind = volume.get('kind')
        walker = volume.get('walker')
        if kind not in _KINDS:
            continue
        name = volume.get('name') or volume.get('label') or ''
        if walker is None:
            logfunc(f'{_LABEL}: {name} has no reader, so it gave no row')
            continue
        fields = boot_fields(qnxprobe.read_at(walker.fh, walker.base, 512), kind)
        if fields is None:
            logfunc(f'{_LABEL}: the boot sector of {name} could not be read')
            continue
        try:
            label = root_label(_root_directory(walker, kind), kind)
        except (OSError, ValueError, IndexError, struct.error) as exc:
            logfunc(f'{_LABEL}: could not read the root directory of {name}: {type(exc).__name__}')
            label = ''
        rows.append((name, _KINDS[kind], fields['serial'], label, fields['boot_label'], fields['oem'],
                     fields['bytes_per_sector'], fields['sectors_per_cluster'], fields['cluster'],
                     fields['total_sectors'], fields['size'], volume.get('base')))
    return rows


@artifact_processor
def fatVolumeInfo(context):
    data_headers = ('Volume', 'File System', 'Serial Number', 'Volume Label (Root Directory)',
                    'Volume Label (Boot Sector)', 'OEM Name', ('Bytes per Sector', 'number'),
                    ('Sectors per Cluster', 'number'), ('Cluster Size (bytes)', 'number'),
                    ('Total Sectors', 'number'), ('Volume Size (bytes)', 'number'),
                    ('Volume Offset (bytes)', 'number'))
    seeker = context.get_seeker()
    rows = volume_rows(getattr(seeker, 'volumes', None))
    source = '\n'.join(getattr(seeker, 'image_paths', None) or ()) if rows else ''
    return data_headers, rows, source
