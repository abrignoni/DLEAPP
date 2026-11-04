"""Virtual disk files (VHD, VHDX, VMDK, VDI, qcow2) in the extraction, identified from their headers, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The disks are read with the seeker's peek(), which reads a file's first bytes without staging it, so a
multi-gigabyte disk is not copied into the report. Header layouts are from the format documents cited in the notes.
"""

import os
import struct
import uuid
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.search_files import PeekUnsupported

_PATTERNS = ('*.[Vv][Hh][Dd]', '*.[Vv][Hh][Dd][Xx]', '*.[Aa][Vv][Hh][Dd]', '*.[Aa][Vv][Hh][Dd][Xx]',
             '*.[Vv][Mm][Dd][Kk]', '*.[Vv][Dd][Ii]', '*.[Qq][Cc][Oo][Ww]', '*.[Qq][Cc][Oo][Ww]2')
# The VHDX metadata region sat at 2 MiB and was 1 MiB long on the VHDX files checked; 3 MiB reaches its end.
_PEEK_SIZE = 3 << 20
_VHDX_REGION_TABLES = (0x30000, 0x40000)
_VHDX_METADATA = uuid.UUID('8b7ca206-4790-4b9a-b8fe-575f050f886e').bytes_le
_VHDX_VIRTUAL_SIZE = uuid.UUID('2fa54224-cd1b-4876-b211-5dbed83bf4b8').bytes_le
_VHDX_FILE_PARAMETERS = uuid.UUID('caa16737-fa36-4d43-b3b6-33f0aa44e76b').bytes_le
_VHD_DISK_TYPES = {2: 'Fixed', 3: 'Dynamic', 4: 'Differential'}
_VHD_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
_VDI_SIGNATURE = 0xBEDA107F

__artifacts_v2__ = {
    "virtualDisks": {
        "name": "Virtual Disk Files",
        "description": "VHD, VHDX, VMDK, VDI and qcow2 files in the extraction: the format their header holds, the "
                       "disk size and disk type where the header gives them, and the file's times, read without "
                       "copying the disks.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per file whose name ends in .vhd, .vhdx, .avhd, .avhdx, .vmdk, .vdi, .qcow or .qcow2, in any case and in any folder. The files are read with the seeker's peek(), which reads the first 3 MiB of each file and stages nothing, so a disk is not copied into the report and is not in its data folder; each file read is named in the run log, and the located-at list gives the files' paths in the evidence. On pc_mus_001_win11 the 13 disks, up to 2.5 GB each, were read this way with nothing written to the data folder. A single-file input cannot be read this way, and the artifact says so in the run log. Format, Virtual Size, Disk Type, Has Parent, Creator and VHD Footer Time come from the bytes read; Creator is the creator text the format holds, with surrounding spaces and nulls removed. VHDX: the file type identifier \"vhdxfile\" and its creator string (https://github.com/libyal/libvhdi/blob/f7b4f4d8ab9a60f17486b9dc33a01a1aee63f242/documentation/Virtual%20Hard%20Disk%20version%202%20(VHDX)%20image%20format.asciidoc?plain=1#L89-L100); the region table, which Microsoft's specification places in the 1 MB header section after the file type identifier and two headers, each item 64 KB (https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-vhdx/f0efbb98-f555-4efc-8374-4e77945ad422), so at 192 KB and its copy at 256 KB, where every tested VHDX held it; and in the metadata region it names, the virtual disk size item and the has parent flag of the file parameters item (#L129-L275, #L370-L378). Disk Type is left blank for a VHDX. VHD: a dynamic or differential VHD starts with a copy of its 512-byte footer (https://github.com/libyal/libvhdi/blob/f7b4f4d8ab9a60f17486b9dc33a01a1aee63f242/documentation/Virtual%20Hard%20Disk%20(VHD)%20image%20format.asciidoc?plain=1#L89-L112), read for the \"conectix\" signature, the creator application at offset 28, shown with its trailing nulls and spaces removed and not mapped to a product name, the time at offset 24 in seconds since 2000-01-01 UTC, which libyal names the modification time (shown as VHD Footer Time), the disk size at offset 40 and the disk type at 60, named as libyal names them (#L130-L230); Has Parent is Yes for a differential disk. A fixed VHD has no copy at its start, only the footer in its last 512 bytes, which is not read: its row has no format and a note saying the bytes read hold no signature, and when its first sector ends in 55 AA, as a boot sector does, the note says that too. VMDK: the sparse extent header \"KDMV\" and its capacity in 512-byte sectors (no VMDK was in the tested images; https://github.com/libyal/libvmdk/blob/175d3fc0a0b961f362f16e7560a6169d7213e16b/documentation/VMWare%20Virtual%20Disk%20Format%20(VMDK).asciidoc?plain=1#L478-L500, sector size at #L88), or a text descriptor file starting # Disk DescriptorFile, whose createType is shown without its quotes and not interpreted (#L136-L183). qcow: the magic QFI\\xfb, the version and the size at bytes 24 to 31, big-endian (https://github.com/qemu/qemu/blob/f29ccc287a6cfdd51d3a4fd17fbe9af3310a0ac5/docs/interop/qcow2.rst?plain=1#L12-L50). VDI: the signature 0xBEDA107F after the 64-byte file information text, which is shown as Creator (https://github.com/VirtualBox/virtualbox/blob/b6bea72111fcff48f31c57c9f66365b1d3301bb9/src/VBox/Storage/VDICore.h#L56-L97); the VDI disk size is not read, because where it sits depends on the header version. Measured against libyal's own reader (pyvhdi 20260901) on copies of three pc_mus_001_win11 disks, the VHDX and VHD virtual sizes and the VHD disk type agreed; the qcow and VDI fields were not checked against another reader. Created (UTC) and Modified (UTC) are the file's times as the tool's image reader reports them, and blank for a folder, zip or tar input: only the image reader's times are shown. File Size is the file's size in the evidence; a dynamic disk can be much smaller than its virtual size. Folder is the file's folder in the evidence and User the profile folder after Users or Documents and Settings in its path. On pc_mus_001_win11: 7 VHDX, 1 VHD, 1 VDI and 4 qcow2 files; on hexordia_mvs2025_win11 1 VHDX and 1 .vhd with no signature in the bytes read; on af_case2_win10 2 .vhd files with no signature whose first sector ends in 55 AA. Files with other names, and disks kept inside other files, are not found. A row records that a disk file is there, not that a virtual machine ran from it.",
        "paths": None,
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 13 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no files with these names)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no files with these names)",
        },
    },
}


def _utf16(raw):
    return raw.decode('utf-16-le', 'replace').split('\x00')[0].strip()


def vhdx_fields(head):
    """(virtual size, has parent, creator, note) from a VHDX file's first bytes."""
    creator = _utf16(head[8:520])
    for table in _VHDX_REGION_TABLES:
        if head[table:table + 4] != b'regi' or len(head) < table + 16:
            continue
        count = struct.unpack_from('<I', head, table + 8)[0]
        for index in range(min(count, 2047)):
            entry = table + 16 + index * 32
            if entry + 32 > len(head):
                break
            if head[entry:entry + 16] != _VHDX_METADATA:
                continue
            region = struct.unpack_from('<Q', head, entry + 16)[0]
            if region + 32 > len(head) or head[region:region + 8] != b'metadata':
                return '', '', creator, 'the metadata region is past the bytes read'
            size = parent = ''
            items = struct.unpack_from('<H', head, region + 10)[0]
            for item in range(items):
                at = region + 32 + item * 32
                if at + 24 > len(head):
                    break
                ident = head[at:at + 16]
                offset = struct.unpack_from('<I', head, at + 16)[0]
                if ident == _VHDX_VIRTUAL_SIZE and region + offset + 8 <= len(head):
                    size = struct.unpack_from('<Q', head, region + offset)[0]
                elif ident == _VHDX_FILE_PARAMETERS and region + offset + 8 <= len(head):
                    flags = struct.unpack_from('<I', head, region + offset + 4)[0]
                    parent = 'Yes' if flags & 2 else 'No'
            return size, parent, creator, ''
        return '', '', creator, 'no metadata region in the region table'
    return '', '', creator, 'no region table at 192 or 256 KiB'


def identify(head, file_name):
    """A dict of what a disk file's first bytes say: format, virtual size, disk type, has parent, creator,
    footer time and note."""
    found = {'format': '', 'size': '', 'type': '', 'parent': '', 'creator': '', 'time': '', 'note': ''}
    if head is None:
        return found
    if head[:8] == b'vhdxfile':
        found['format'] = 'VHDX'
        found['size'], found['parent'], found['creator'], found['note'] = vhdx_fields(head)
    elif head[:8] == b'conectix' and len(head) >= 64:
        found['format'] = 'VHD'
        found['size'] = struct.unpack_from('>Q', head, 40)[0]
        disk_type = struct.unpack_from('>I', head, 60)[0]
        found['type'] = _VHD_DISK_TYPES.get(disk_type, f'{disk_type} (as stored)')
        found['parent'] = 'Yes' if disk_type == 4 else 'No'
        found['creator'] = head[28:32].decode('latin-1').strip('\x00 ')
        found['time'] = _VHD_EPOCH + timedelta(seconds=struct.unpack_from('>I', head, 24)[0])
    elif head[:4] == b'KDMV' and len(head) >= 20:
        found['format'] = 'VMDK (sparse extent)'
        found['size'] = struct.unpack_from('<Q', head, 12)[0] * 512
    elif head.startswith(b'# Disk DescriptorFile'):
        found['format'] = 'VMDK (descriptor)'
        for line in head.decode('latin-1').splitlines():
            if line.strip().lower().startswith('createtype'):
                found['type'] = line.split('=', 1)[-1].strip().strip('"') + ' (as stored)'
                break
    elif head[:4] == b'QFI\xfb' and len(head) >= 32:
        found['format'] = f'qcow version {struct.unpack_from(">I", head, 4)[0]}'
        found['size'] = struct.unpack_from('>Q', head, 24)[0]
    elif len(head) >= 72 and struct.unpack_from('<I', head, 64)[0] == _VDI_SIGNATURE:
        found['format'] = 'VDI'
        found['creator'] = head[:64].split(b'\n')[0].split(b'\x00')[0].decode('latin-1').strip()
    else:
        note = 'no format signature in the bytes read'
        if file_name.lower().endswith('.vhd') and head[510:512] == b'\x55\xaa':
            note += ('; the first sector ends in 55 AA, as a boot sector does, and a fixed VHD keeps its only '
                     'footer in its last 512 bytes, which are not read')
        found['note'] = note
    return found


def _instant(value):
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _profile_user(path):
    parts = path.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'documents and settings'):
            return parts[index + 1]
    return ''


@artifact_processor
def virtualDisks(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), ('VHD Footer Time (UTC)', 'datetime'),
                    'File Name', 'Folder', 'File Size (bytes)', 'Format', 'Virtual Size (bytes)', 'Disk Type',
                    'Has Parent', 'Creator', 'Note', 'User')
    data_list, sources = [], []
    seeker = context.get_seeker()
    if seeker is None or not hasattr(seeker, 'peek'):
        logfunc('Virtual Disk Files: this input gives no way to read a file without staging it')
        return data_headers, data_list, ''
    from_image = hasattr(seeker, 'stream_list')
    seen = set()
    for pattern in _PATTERNS:
        try:
            peeked = seeker.peek(pattern, _PEEK_SIZE)
        except PeekUnsupported as exc:
            logfunc(f'Virtual Disk Files: {exc}')
            return data_headers, data_list, ''
        for item in peeked:
            if item.path in seen:
                continue
            seen.add(item.path)
            name = os.path.basename(item.path.replace('\\', '/'))
            found = identify(item.head, name)
            note = '; '.join(part for part in (item.note, found['note']) if part)
            created = _instant(item.info.creation_date) if from_image else ''
            modified = _instant(item.info.modification_date) if from_image else ''
            data_list.append((created, modified, found['time'], name, os.path.dirname(item.path.replace('\\', '/')),
                              item.size, found['format'], found['size'], found['type'], found['parent'],
                              found['creator'], note, _profile_user(item.path)))
            sources.append(item.path)
    return data_headers, data_list, '\n'.join(sources)
