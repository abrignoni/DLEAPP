"""Stores in U-Boot's environment layout, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "ubootEnvironment": {
        "name": "U-Boot Environment Variables",
        "description": "Name and value strings from stores in U-Boot's environment layout, as found on a "
                       "flash dump or kept as a uboot.env file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Bootloader (U-Boot)",
        "notes": "Reads uboot-env.bin, the one-file volume qnxprobe 1.54 and later gives a store in U-Boot's "
                 "environment layout found in a raw flash dump, and a file named uboot.env. The layout is "
                 "env_t in U-Boot's include/env_internal.h (https://github.com/u-boot/u-boot/blob/"
                 "866ca972d6c3cabeaf6dbac431e8e08bb30b3c8e/include/env_internal.h#L80-L86): a little-endian "
                 "CRC-32, a flags byte only in a build configured for a redundant copy "
                 "(CONFIG_SYS_REDUNDAND_ENVIRONMENT), then NUL-separated strings, which U-Boot reads up to the "
                 "first empty one (https://github.com/u-boot/u-boot/blob/866ca972d6c3cabeaf6dbac431e8e08bb30b3c8e/"
                 "lib/hashtable.c#L955). A file is read only when the CRC-32 of the rest of the file equals "
                 "the stored one, first after a 4-byte header and then after a 5-byte one; a file for which "
                 "neither holds gives no row and is counted in the run log. One row per string, up to the first "
                 "empty one, in stored order (Position, from 1). Name is the text before the first '=' and "
                 "Value the rest, as stored, including any secret or key; a string with no '=' is its own Name "
                 "with Value blank. Bytes after the empty string are not read. Layout gives the header size, "
                 "the store's size and, for the 5-byte header, the flags byte as stored. Folder names the volume or folder the "
                 "store came from, as a device can hold several. Folder and Layout hold one value on every row "
                 "from one store. The layout does not establish which program "
                 "wrote a store, and what each name means is not established; field mapped from a private "
                 "sample. A store records no time; the modified time a filesystem records for a uboot.env file is "
                 "not reported. The uboot.env path is tested only with made-up "
                 "files. Validated only against private samples; sample_data is left empty for that reason.",
        "paths": ("*/uboot-env.bin", "*/uboot.env"),
        "output_types": "standard",
        "artifact_icon": "cpu",
        "sample_data": {},
    },
}

import binascii
import os
import struct
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

STORE_NAMES = ('uboot-env.bin', 'uboot.env')


def env_strings(data, start):
    """The NUL-separated strings of data from start, up to the first empty one."""
    out = []
    pos = start
    while pos < len(data):
        end = data.find(b'\x00', pos)
        if end < 0:
            end = len(data)
        if end == pos:
            break
        out.append(data[pos:end])
        pos = end + 1
    return out


def env_layout(data):
    """(header size, flags byte or None) for bytes in U-Boot's environment layout, else None."""
    if len(data) < 8:
        return None
    stored = struct.unpack_from('<I', data)[0]
    for header in (4, 5):
        if binascii.crc32(data[header:]) == stored:
            return header, (data[4] if header == 5 else None)
    return None


def name_value(item):
    name, _sep, value = item.partition(b'=')
    return name.decode('utf-8', 'backslashreplace'), value.decode('utf-8', 'backslashreplace')


@artifact_processor
def ubootEnvironment(context):
    data_headers = ('Name', 'Value', 'Position', 'Layout', 'Folder')
    rows = []
    read = []
    counts = Counter()
    found = []
    for path in (str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path) not in STORE_NAMES:
            continue
        found.append((context.get_relative_path(path), path))
    for relative, path in sorted(found):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        layout = env_layout(data)
        if layout is None:
            counts['files whose CRC-32 does not hold, not read'] += 1
            continue
        header, flags = layout
        shown = (f'4-byte header, {len(data):,} bytes' if header == 4 else
                 f'5-byte header, flags byte {flags}, {len(data):,} bytes')
        for position, item in enumerate(env_strings(data, header), 1):
            name, value = name_value(item)
            rows.append((name, value, position, shown, os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('U-Boot Environment Variables: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)
