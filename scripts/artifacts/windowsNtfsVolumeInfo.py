"""NTFS volume information from $Boot and the $Volume record, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each NTFS volume a raw image holds lists $Boot, the volume's boot sector, and $MFT. The boot sector gives the
volume serial number, the sector and cluster sizes, the volume's size and where the MFT is; MFT record 3, $Volume,
holds the volume's name and NTFS version. Offsets are from the Linux-NTFS documentation cited in the notes.
"""

import os
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import _apply_fixup, decode_flags, mft_record_size  # pylint: disable=protected-access

_LABEL = 'NTFS Volume Information'
_VOLUME_RECORD = 3
_ATTR_VOLUME_NAME = 0x60
_ATTR_VOLUME_INFORMATION = 0x70
_ATTR_END = 0xFFFFFFFF
# attributes/volume_information.html, the Flags table.
_VOLUME_FLAGS = ((0x0001, 'Dirty'), (0x0002, 'Resize LogFile'), (0x0004, 'Upgrade on Mount'),
                 (0x0008, 'Mounted on NT4'), (0x0010, 'Delete USN underway'), (0x0020, 'Repair Object Ids'),
                 (0x8000, 'Modified by chkdsk'))

__artifacts_v2__ = {
    "ntfsVolumeInfo": {
        "name": "NTFS Volume Information",
        "description": "Each NTFS volume in a raw image: its serial number, name, NTFS version and state flags, "
                       "sector and cluster sizes, size, and where its MFT and MFT mirror start, from $Boot and the "
                       "$Volume record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per $Boot in the extraction that starts with an NTFS boot sector, which a raw image lists "
                 "once for each NTFS volume it holds. The fields follow the Linux-NTFS documentation of the boot sector "
                 "(https://github.com/flatcap/ntfs-docs/blob/641edd36dc5f6b62c2aae6658c5a60a4d6d3fe29/files/boot.html#L79-L171): Bytes per Sector and Sectors per Cluster at 0x0B and 0x0D, "
                 "Total Sectors at 0x28, MFT Cluster and MFT Mirror Cluster (the clusters where $MFT and $MFTMirr "
                 "start) at 0x30 and 0x38, the clusters per MFT record at 0x40 (a negative value giving a record of 2 "
                 "to that power in bytes, #L182-L186) and Serial Number, the 8-byte volume serial number, at 0x48. "
                 "Cluster Size is bytes per sector times sectors per cluster, Volume Size is total sectors times bytes "
                 "per sector, and MFT Record Size is worked out from the 0x40 value as the documentation gives. Serial "
                 "Number (low 32 bits) is the serial's last 8 hex digits: on the tested images 103 Drive Serial values "
                 "in Recent Shell Links (LNK), on 9 images, each equalled this value for a volume of the same image, "
                 "and the other Drive Serial values named volumes the images do not hold. Volume Name, NTFS Version "
                 "and Volume Flags come from MFT record 3, $Volume, of the $MFT in the same folder: its resident "
                 "$VOLUME_NAME attribute (https://github.com/flatcap/ntfs-docs/blob/641edd36dc5f6b62c2aae6658c5a60a4d6d3fe29/attributes/volume_name.html) and the major and minor version and "
                 "flags of its $VOLUME_INFORMATION attribute (https://github.com/flatcap/ntfs-docs/blob/641edd36dc5f6b62c2aae6658c5a60a4d6d3fe29/attributes/volume_information.html#L56-L115), "
                 "the flags named from that page's table and any other bit given in hex; a 0x00000080 bit, which the "
                 "table does not name, was set on 6 of the 17 tested volumes. Volume Name is blank where the volume "
                 "has none, and all three are blank, with a run log line, where no $MFT is beside the $Boot. Volume is "
                 "the folder the extraction gives the volume. On every one of the 17 NTFS volumes of the ten tested raw "
                 "Windows images, Serial Number, Volume Name, Bytes per Sector, Cluster Size, MFT Cluster and Total "
                 "Sectors equalled what The Sleuth Kit 4.15.0 fsstat reports for the same volume. A logical "
                 "extraction such as an AD1 lists no $Boot and gives no row (hexordia_mvs2025_win11). Only NTFS is "
                 "read; FAT, exFAT and ReFS volumes give no row.",
        "paths": ('*/$Boot', '*/$MFT'),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 2 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 1 row",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 1 row",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 3 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 2 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 1 row",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (a logical AD1 lists no $Boot)",
        },
    },
}


def boot_fields(boot):
    """The fields of an NTFS boot sector (files/boot.html), or None when it is not one."""
    if len(boot) < 0x50 or boot[3:11] != b'NTFS    ':
        return None
    bytes_per_sector = struct.unpack_from('<H', boot, 0x0B)[0]
    sectors_per_cluster = boot[0x0D]
    total_sectors, mft_lcn, mirror_lcn = struct.unpack_from('<QQQ', boot, 0x28)
    per_record = struct.unpack_from('<b', boot, 0x40)[0]
    cluster = bytes_per_sector * sectors_per_cluster
    record_size = cluster * per_record if per_record > 0 else 2 ** (-per_record)
    serial = struct.unpack_from('<Q', boot, 0x48)[0]
    return {'serial': serial, 'bytes_per_sector': bytes_per_sector, 'sectors_per_cluster': sectors_per_cluster,
            'cluster': cluster, 'total_sectors': total_sectors, 'size': total_sectors * bytes_per_sector,
            'mft_lcn': mft_lcn, 'mirror_lcn': mirror_lcn, 'record_size': record_size, 'media': boot[0x15]}


def volume_record_fields(record):
    """(name, version, flags) from MFT record 3's resident $VOLUME_NAME and $VOLUME_INFORMATION; '' for each one
    not found."""
    name = version = flags = ''
    if record[:4] != b'FILE':
        return name, version, flags
    fixed = _apply_fixup(record)
    if fixed is None:
        return name, version, flags
    first = struct.unpack_from('<H', fixed, 0x14)[0]
    used = struct.unpack_from('<I', fixed, 0x18)[0]
    limit = min(used or len(fixed), len(fixed))
    position = first
    while position + 24 <= limit:
        kind, length = struct.unpack_from('<II', fixed, position)
        if kind == _ATTR_END or length < 24 or position + length > limit:
            break
        if fixed[position + 8] == 0:
            value_length, value_offset = struct.unpack_from('<IH', fixed, position + 0x10)
            value = fixed[position + value_offset:position + value_offset + value_length]
            if kind == _ATTR_VOLUME_NAME:
                name = value.decode('utf-16-le', 'replace')
            elif kind == _ATTR_VOLUME_INFORMATION and len(value) >= 12:
                version = f'{value[8]}.{value[9]}'
                flags = decode_flags(struct.unpack_from('<H', value, 0x0A)[0], _VOLUME_FLAGS)
        position += length
    return name, version, flags


@artifact_processor
def ntfsVolumeInfo(context):
    data_headers = ('Volume', 'Serial Number', 'Serial Number (low 32 bits)', 'Volume Name', 'NTFS Version',
                    'Volume Flags', 'Bytes per Sector', 'Sectors per Cluster', 'Cluster Size (bytes)',
                    'Total Sectors', 'Volume Size (bytes)', 'MFT Cluster', 'MFT Mirror Cluster',
                    'MFT Record Size (bytes)', 'Source File')
    data_list = []
    sources = []
    found = [str(f) for f in context.get_files_found() if os.path.isfile(str(f))]
    tables = {os.path.dirname(f): f for f in found if os.path.basename(f) == '$MFT'}
    for boot_path in sorted(f for f in found if os.path.basename(f) == '$Boot'):
        relative = context.get_relative_path(boot_path)
        try:
            with open(boot_path, 'rb') as handle:
                fields = boot_fields(handle.read(512))
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}')
            continue
        if fields is None:
            logfunc(f'{_LABEL}: {relative} does not start with an NTFS boot sector')
            continue
        name = version = flags = ''
        table = tables.get(os.path.dirname(boot_path))
        if table:
            try:
                with open(table, 'rb') as handle:
                    size = mft_record_size(handle)
                    handle.seek(_VOLUME_RECORD * size)
                    name, version, flags = volume_record_fields(handle.read(size))
            except OSError as exc:
                logfunc(f'{_LABEL}: could not read the $MFT beside {relative}: {type(exc).__name__}')
        else:
            logfunc(f'{_LABEL}: no $MFT beside {relative}, so the name, version and flags are blank')
        volume = os.path.dirname(relative.replace('\\', '/'))
        data_list.append((volume, f'{fields["serial"]:016X}', f'{fields["serial"] & 0xFFFFFFFF:08X}', name, version,
                          flags, fields['bytes_per_sector'], fields['sectors_per_cluster'], fields['cluster'],
                          fields['total_sectors'], fields['size'], fields['mft_lcn'], fields['mirror_lcn'],
                          fields['record_size'], relative))
        sources.append(boot_path)
    return data_headers, data_list, '\n'.join(sources)
