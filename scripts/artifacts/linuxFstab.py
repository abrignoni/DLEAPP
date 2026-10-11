"""Filesystems a Linux system is configured to mount, from /etc/fstab, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxFstab": {
        "name": "Filesystem Table (fstab)",
        "description": "The entries of /etc/fstab, the table of filesystems a Linux system can mount and swap areas "
                       "it can enable, one row per entry: the device or remote share, the mount point, the "
                       "filesystem type and the mount options.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "System (Linux)",
        "notes": "Reads /etc/fstab, which the manual describes as the filesystems the system can mount. Each "
                 "filesystem is on its own line with fields separated by tabs or spaces, a line starting with # is a "
                 "comment and blank lines are ignored (Reference: util-linux 2.41, commit "
                 "caa26876bc75041833c9644491cc2670d623f750, https://github.com/util-linux/util-linux, "
                 "'sys-utils/fstab.5.adoc' lines 53 to 59). The file is read the way libmount reads it: a line ends "
                 "at a line feed, one carriage return before it is dropped, and only spaces and tabs separate fields "
                 "('libmount/src/tab_parse.c' lines 85 to 97 and 598 to 603). One row is reported per line that is "
                 "neither. Device, Mount Point, Type, Options, Dump and Pass are the six fields in order, which the "
                 "manual names fs_spec, the device, remote filesystem or image to mount, fs_file, the mount point, "
                 "fs_vfstype, the filesystem type, fs_mntops, the mount options, fs_freq, used by dump, and "
                 "fs_passno, the order of filesystem checks at boot (lines 67 to 124). In the first four fields a "
                 "backslash and three octal digits are replaced by the byte of that value, the escape mount reads, "
                 "so a space written as \\040 is shown as a space ('libmount/src/tab_parse.c' lines 109 to 139 and "
                 "'lib/mangle.c' lines 60 to 64); a zero byte ends the field, and a byte that is not valid UTF-8 is "
                 "shown as \\x and two hexadecimal digits. A field the line does not have gives an empty cell; mount "
                 "reads an absent Dump or Pass as 0 (line 107 of that file), and rejects a line whose Dump or Pass "
                 "is not a number (lines 51 to 66 and 153 to 169); such a value is shown as written and counted in "
                 "the run log. A line is a comment when # is its first character after any blanks (lines 602 to "
                 "603). Comment Above is the comment line directly above the entry, with no blank line between, "
                 "without its leading # marks; only that one line is kept. Line is the entry's line number. An entry "
                 "with fewer than the three fields mount requires (lines 109 to 134) is still reported, and counted "
                 "in the run log. Fields after the sixth are not shown. The file is matched by its path, so the "
                 "table of another program that keeps an etc/fstab is read too. On ubuntu2604_arm64_nm_a, a capture "
                 "of an Ubuntu 26.04 virtual machine, the 3 rows are the root filesystem and the EFI partition, each "
                 "named by a /dev/disk path and each with a comment above it that says which device node it was on "
                 "during installation, and a swap file; Comment Above is empty on the swap row. On "
                 "honeynet_fc7_debian5, a Debian 5 image, the 4 rows are proc, the root filesystem on a partition "
                 "named by device node, a swap partition and an entry at an optical disc mount point with two types "
                 "and the options user and noauto; Dump is 0 on all 4 rows, and Comment Above is filled on the first "
                 "row only, with the file's column heading comment. On pc_mus_001_win11, a Windows 11 image, the 2 "
                 "rows are not a Linux system's table: they come from the etc/fstab in the Git for Windows folder "
                 "under Program Files, with the types cygdrive and usertemp; Device, Dump and Pass each held one "
                 "value on both rows, none, 0 and 0. Not exercised on real data: a network share, an entry named by "
                 "UUID= or LABEL=, an escaped space, a line with fewer than six fields, a Dump or Pass that is not a "
                 "number, and a byte that is not UTF-8; all of these but the first two were tested with constructed "
                 "input. A row shows what the table lists, not that the filesystem was mounted or that the device "
                 "was present.",
        "paths": ("*/etc/fstab",),
        "output_types": "standard",
        "artifact_icon": "hard-drive",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Git for Windows | 2 rows",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_a": "Ubuntu 26.04 LTS aarch64 | 3 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

_OCTAL = re.compile(rb'\\([0-7]{3})')
_BLANKS = b' \t'
_SEPARATOR = re.compile(rb'[ \t]+')
_NUMBER = re.compile(rb'[+-]?[0-9]+')
SHORT = 'entries with fewer than three fields, still reported'
NOT_NUMBER = 'entries whose Dump or Pass is not a number, shown as written'


def _text(data):
    return data.decode('utf-8', 'backslashreplace')


def unmangle(field):
    """A field's bytes as text, each backslash and three octal digits first replaced by the byte of that value, the
    way mount reads a space written as \\040, and the field ended at a zero byte as a C string is."""
    return _text(_OCTAL.sub(lambda match: bytes([int(match.group(1), 8) & 0xff]), field).split(b'\x00')[0])


def fstab_rows(data, counts):
    """(device, mount point, type, options, dump, pass, comment above, line) for each entry of an fstab. Lines end
    at a line feed, with one carriage return before it dropped; fields are separated by spaces and tabs only; a
    line whose first byte after those blanks is # is a comment, and the comment directly above an entry, with no
    blank line between, is kept with it."""
    rows, comment = [], ''
    for number, raw in enumerate(data.split(b'\n'), 1):
        line = (raw[:-1] if raw.endswith(b'\r') else raw).strip(_BLANKS)
        if not line:
            comment = ''
            continue
        if line.startswith(b'#'):
            comment = _text(line.lstrip(b'#')).strip()
            continue
        fields = _SEPARATOR.split(line)
        if len(fields) < 3:
            counts[SHORT] += 1
        if any(not _NUMBER.fullmatch(field) for field in fields[4:6]):
            counts[NOT_NUMBER] += 1
        named = [unmangle(field) for field in fields[:4]] + [_text(field) for field in fields[4:6]]
        rows.append(tuple(named + [''] * (6 - len(named))) + (comment, number))
        comment = ''
    return rows


@artifact_processor
def linuxFstab(context):
    data_headers = ('Device', 'Mount Point', 'Type', 'Options', 'Dump', 'Pass', 'Comment Above', 'Line',
                    'Source File')
    data_list, read, counts = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                rows = fstab_rows(handle.read(), counts)
        except OSError:
            counts['files that could not be read'] += 1
            continue
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc('Filesystem Table (fstab): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
