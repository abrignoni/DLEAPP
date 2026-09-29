"""Belkin WeMo settings from its libnvram store, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "belkinWemoNvram": {
        "name": "Belkin WeMo NVRAM Settings",
        "description": "Name and value strings from a Belkin libnvram store (NVRM header), the store format "
                       "of Belkin's libnvram library for WeMo devices.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Belkin WeMo",
        "notes": "Reads nvram.bin, the one-file volume qnxprobe 1.54 and later gives a libnvram store found "
                 "in a raw flash dump. The layout is env_image_gemtek in Belkin's own libnvram.c (its header "
                 "carries Belkin's copyright), as found in a public copy of the WeMo firmware tree (https://github.com/svenschwermer/wemo/blob/46d0ccd248806e8e07210f9b34166b127e9d3d52/"
                 "package/belkin_nvram_bd/src/libnvram.c#L97-L108): 'NVRM', a CRC-32, an entry count and the "
                 "offset of the end of the data, then NUL-separated strings. A file is read only when it opens "
                 "with 'NVRM' and the CRC-32 of the bytes after the 16-byte header equals the stored one, as "
                 "libnvram checks it (lines 853 to 874); a file that fails gives no row and is counted in the "
                 "run log. One row per string, up to the first empty one, in stored order (Position, from 1). "
                 "Name is the text before the first '=' and Value the rest, as stored, including any secret or "
                 "key; a string with no '=' is its own Name with Value blank. Bytes after the empty string are "
                 "not read. The header's entry count and end of data are not reported or checked, as the CRC-32 does not "
                 "cover them; a store whose count differs from the strings read is counted in the run log. Folder names the volume the "
                 "store came from, and holds one value on every row from one store. What each name means, and when a value was set, are not established; field "
                 "mapped from a private sample. The store records no time, and none is reported. Validated only against a "
                 "private sample; sample_data is left empty for that reason.",
        "paths": ("*/nvram.bin",),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {},
    },
}

import binascii
import os
import struct
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

MAGIC = b'NVRM'
HEADER = 16


def nvram_strings(data):
    """The NUL-separated strings after the header, up to the first empty one."""
    out = []
    pos = HEADER
    while pos < len(data):
        end = data.find(b'\x00', pos)
        if end < 0:
            end = len(data)
        if end == pos:
            break
        out.append(data[pos:end])
        pos = end + 1
    return out


def nvram_header(data):
    """(count, end of data) as the header stores them, for a store whose CRC-32 holds, else None."""
    if len(data) < HEADER or data[:4] != MAGIC:
        return None
    stored, count, eod = struct.unpack_from('<III', data, 4)
    if binascii.crc32(data[HEADER:]) != stored:
        return None
    return count, eod


@artifact_processor
def belkinWemoNvram(context):
    data_headers = ('Name', 'Value', 'Position', 'Folder')
    rows = []
    read = []
    counts = Counter()
    found = []
    for path in (str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path) != 'nvram.bin':
            continue
        found.append((context.get_relative_path(path), path))
    for relative, path in sorted(found):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        header = nvram_header(data)
        if header is None:
            counts['files without an NVRM header whose CRC-32 holds, not read'] += 1
            continue
        strings = nvram_strings(data)
        if header[0] != len(strings):
            counts['stores whose header count differs from the strings read'] += 1
        for position, item in enumerate(strings, 1):
            name, _sep, value = item.partition(b'=')
            rows.append((name.decode('utf-8', 'backslashreplace'), value.decode('utf-8', 'backslashreplace'),
                         position, os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Belkin WeMo NVRAM Settings: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)
