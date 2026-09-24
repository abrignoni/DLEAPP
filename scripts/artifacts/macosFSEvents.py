"""File system event records from the macOS fseventsd disk log stream, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The page and record reader follows iLEAPP's fileSystemEvents module, whose layout and
flag table come from the sources cited in the notes.
"""

__artifacts_v2__ = {
    "macosFSEvents": {
        "name": "FSEvents",
        "description": "Path-level file system event records from the fseventsd disk log stream "
                       "(.fseventsd at a volume's root): event ID, path, the event flags decoded, "
                       "node ID and format version.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "File System (macOS)",
        "notes": "Reads the fseventsd disk log files in each .fseventsd folder at a volume's root, one"
                 " row per record. Each file is read as one or more gzip members holding pages that "
                 "begin with a 12-byte header whose signature is 1SLD, 2SLD or 3SLD. A record is a "
                 "NUL-terminated path, an 8-byte event ID and 4-byte flags, followed in 2SLD and 3SLD "
                 "pages by an 8-byte node ID, and in 3SLD pages by one more 4-byte value, read as "
                 "unsigned and reported as Record Extra (as stored); what that value records is not "
                 "established. The records hold no time of their own. The 1SLD and 2SLD layouts and "
                 "the flag values follow the dtformats documentation of the format (Reference: libyal,"
                 " 'MacOS File System Events Disk Log Stream format', "
                 "https://github.com/libyal/dtformats/blob/a28171cf92eeacb4c53a2d214129c511b313a0a1/documentation/MacOS%20File%20System%20Events%20Disk%20Log%20Stream%20format.asciidoc#L74-L167),"
                 " and the 3SLD layout follows mac_apt's fsevents plugin (Reference: mac_apt, "
                 "plugins/fsevents.py, "
                 "https://github.com/ydkhatri/mac_apt/blob/41ca6a91789b3ba7af8141e724b69328c372054d/plugins/fsevents.py#L180)."
                 " Event Flags names each set bit after the identifier or description that "
                 "documentation gives for its value, and names a bit it does not list as Unknown flag "
                 "bits with the hex value; no row of either tested image carried one. Item Type names "
                 "the file, directory, symbolic link and hard link bits among them. Path is the stored"
                 " path, with no leading slash on any row of the tested images. On dleapp_macos_bigsur"
                 " the Data volume's .fseventsd holds 25 1SLD files of 2 records each, a "
                 ".fseventsd/sl-compat directory record and an End of transaction record with no path,"
                 " and 209 2SLD files, 528,473 rows in all; Record Extra (as stored) has no value on "
                 "any row there. The public MacBook Pro logical extraction (macOS 15.4, not a "
                 "registered corpus key) holds 17 such 1SLD files and 652 3SLD files in "
                 "System/Volumes/Data/.fseventsd, 1,759,879 rows, and 6 files of 38 bytes that hold "
                 "only a 12-byte 3SLD header and no record, which the run log names; Record Extra "
                 "there took 55 values between 0 and 56. Node ID is blank on 1SLD rows. Path has no "
                 "value on 40 rows of dleapp_macos_bigsur, 25 of them End of transaction records and "
                 "14 carrying the Mount flag, and on 19 rows of the MacBook Pro, 17 End of transaction"
                 " and 2 Mount.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 528,473 rows",
                 },
        "paths": ('*/.fseventsd/*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-search",
    }
}

import os
import struct
import zlib

from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'FSEvents'
# Event flag bits and their names, from the cited format documentation.
_FLAGS = (
    (0x00000001, 'Created'),
    (0x00000002, 'Removed'),
    (0x00000004, 'Inode metadata modified'),
    (0x00000008, 'Renamed'),
    (0x00000010, 'Content modified'),
    (0x00000020, 'Exchanged'),
    (0x00000040, 'Finder information modified'),
    (0x00000080, 'Directory created'),
    (0x00000100, 'Permissions changed'),
    (0x00000200, 'Extended attribute modified'),
    (0x00000400, 'Extended attribute removed'),
    (0x00000800, 'Document ID created'),
    (0x00001000, 'Document revision'),
    (0x00002000, 'Unmount pending'),
    (0x00004000, 'Item cloned'),
    (0x00010000, 'Clone notification'),
    (0x00020000, 'Path truncated'),
    (0x00040000, 'Remote directory event'),
    (0x00080000, 'Last hard link removed'),
    (0x00100000, 'Hard link'),
    (0x00400000, 'Symbolic link'),
    (0x00800000, 'File'),
    (0x01000000, 'Directory'),
    (0x02000000, 'Mount'),
    (0x04000000, 'Unmount'),
    (0x20000000, 'End of transaction'),
)
_KNOWN_FLAG_MASK = sum(value for value, _name in _FLAGS)
_ITEM_TYPES = ((0x00800000, 'File'), (0x01000000, 'Directory'), (0x00400000, 'Symbolic link'),
               (0x00100000, 'Hard link'))
# Record layout after the path, by page signature: event ID and flags, then (version 2) the
# node ID, then (version 3) a further 32-bit value.
_RECORD_STRUCTS = {
    b'1SLD': struct.Struct('<QI'),
    b'2SLD': struct.Struct('<QIQ'),
    b'3SLD': struct.Struct('<QIQI'),
}


def _decode_flags(flags):
    names = [name for value, name in _FLAGS if flags & value]
    unknown = flags & ~_KNOWN_FLAG_MASK
    if unknown:
        names.append(f'Unknown flag bits 0x{unknown:08X}')
    return ' | '.join(names) if names else 'None'


def _item_type(flags):
    return ' | '.join(label for value, label in _ITEM_TYPES if flags & value)


def _decompress_members(compressed):
    """Each gzip member of a file in turn; stops at the first that does not decompress."""
    remaining = compressed
    while remaining:
        decompressor = zlib.decompressobj(31)
        try:
            member = decompressor.decompress(remaining) + decompressor.flush()
        except zlib.error:
            return
        if member:
            yield member
        if not decompressor.unused_data:
            return
        remaining = decompressor.unused_data


def _parse_stream(stream, source):
    """Records of one decompressed stream: pages of a 12-byte header and path records."""
    offset = 0
    length = len(stream)
    while offset + 12 <= length:
        signature, _unknown, page_size = struct.unpack_from('<4sII', stream, offset)
        record_struct = _RECORD_STRUCTS.get(signature)
        if record_struct is None or page_size < 12 or offset + page_size > length:
            return
        page_end = offset + page_size
        position = offset + 12
        while position < page_end:
            terminator = stream.find(b'\x00', position, page_end)
            if terminator < 0:
                break
            path = stream[position:terminator].decode('utf-8', errors='backslashreplace')
            position = terminator + 1
            if position + record_struct.size > page_end:
                break
            values = record_struct.unpack_from(stream, position)
            position += record_struct.size
            event_id, flags = values[:2]
            yield (event_id, path, _decode_flags(flags), f'0x{flags:08X}', _item_type(flags),
                   values[2] if len(values) >= 3 else '', values[3] if len(values) == 4 else '',
                   signature[:1].decode('ascii'), source)
        offset = page_end


@artifact_processor
def macosFSEvents(context):
    data_headers = ('Event ID', 'Path', 'Event Flags', 'Event Flags (Hex)', 'Item Type', 'Node ID',
                    'Record Extra (as stored)', 'Format Version', 'Source File')
    results = context.create_artifact_result(headers=data_headers)
    sources = []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path) == 'fseventsd-uuid':
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                compressed = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}')
            continue
        count = 0
        for member in _decompress_members(compressed):
            for row in _parse_stream(member, relative):
                results.add_row(row)
                count += 1
        if count:
            sources.append(path)
        else:
            logfunc(f'{_LABEL}: no event records read from {relative}')
    results.set_source_path('\n'.join(sources))
    return results
