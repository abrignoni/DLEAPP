"""Operating system release, host name, machine ID and time zone of a Linux system, as its files record them,
for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxSystemInfo": {
        "name": "Linux System Information",
        "description": "Operating system release, host name, machine ID and time zone as a Linux system's own files "
                       "record them (os-release, lsb-release, debian_version, hostname, machine-id, timezone and "
                       "localtime), one row per value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "System (Linux)",
        "notes": "Reads /etc/os-release, /usr/lib/os-release, /etc/lsb-release, /etc/debian_version, /etc/hostname, "
                 "/etc/machine-id, /var/lib/dbus/machine-id, /etc/timezone and /etc/localtime wherever they sit in "
                 "the extraction and reports one row per value, file by file in that order: Property names what the "
                 "row holds, Key is the variable name in an os-release or lsb-release file and blank on other rows, "
                 "Source File is the file, and the files that gave a row are named in the report's located-at line. "
                 "Modified (UTC) is the modified time the seeker recorded for the file, for a link in an input "
                 "folder the link's own, and is blank where none was recorded; on the tar captures it is each "
                 "member's own time. Other release files, such as /etc/redhat-release, and network settings are not "
                 "read. An os-release or lsb-release file is read in the os-release format, one variable assignment "
                 "per line with lines beginning # and blank lines ignored (systemd v259.5, man/os-release.xml, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/os-release.xml#L40-L50), "
                 "and each value as a POSIX shell reads it: text inside single quotes as written, inside double "
                 'quotes with a backslash before $, `, ", a backslash or a newline removed, and outside quotes with '
                 "each backslash removed; a value the shell would not read as one plain word, because it would "
                 "expand something in it, split it or reject it, is reported as written, and it and any line that is "
                 "not an assignment are counted in the run log. /etc/os-release takes precedence over "
                 "/usr/lib/os-release, which applications use only when the former is missing, and it should be a "
                 "relative link to /usr/lib/os-release "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/os-release.xml#L52-L57, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/os-release.xml#L60-L65); "
                 "both are reported when both are present, and a key repeated in one file, which the format forbids, "
                 "is reported each time, the later one being the one readers keep "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/os-release.xml#L80-L82). "
                 "A file recorded as a symbolic link in a tar or a zip, or present as one in an input folder, gives "
                 "a row whose Property ends in link and whose Value is the link's target as recorded, and the file "
                 "it points to is not read: ubuntu2604_arm64_sysinfo extracted to a folder gave the same 25 rows as "
                 "the tar, including a link whose target is missing on the examiner's machine (the zip case is "
                 "exercised by the unit tests' constructed inputs, not by a registered image); DLEAPP's raw image "
                 "reader lists no symbolic links (scripts/raw_image.py), so on a raw image a file that is a link "
                 "gives no row. /etc/hostname holds the static host name, which systemd sets at boot unless the "
                 "kernel command line gives another with systemd.hostname= (hostname(5), man/hostname.xml, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/hostname.xml#L32-L37, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/hostname.xml#L68-L76); "
                 "Host name is its first line that is not blank or a comment "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/hostname.xml#L39-L40), "
                 "as stored, and a ? in it is replaced by a character derived from the machine ID when the name is "
                 "applied "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/hostname.xml#L48-L53). "
                 "/etc/machine-id holds the machine ID, 32 lowercase hexadecimal characters on one line "
                 "(machine-id(5), man/machine-id.xml, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/machine-id.xml#L29-L33); "
                 "a systemd.machine_id= kernel parameter takes precedence over it "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/machine-id.xml#L40-L44), "
                 "and systemd writes uninitialized to it on a first boot until the real ID is saved "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/machine-id.xml#L133-L140); "
                 "/var/lib/dbus/machine-id is D-Bus's older file, which may be a link to /etc/machine-id "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/machine-id.xml#L183-L187). "
                 "Machine ID is the file's first line, as stored. A file with no line of text other than comments, "
                 "and one that cannot be read, gives no row and is counted in the run log. /etc/localtime sets the "
                 "system-wide time zone and should be a link to /usr/share/zoneinfo/ followed by the zone's name, "
                 "from which the name is taken (localtime(5), man/localtime.xml, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/localtime.xml#L29-L38, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/localtime.xml#L40-L42); "
                 "systemd takes the name as the link's target after /usr/share/zoneinfo/ or ../usr/share/zoneinfo/ "
                 "(src/basic/time-util.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/time-util.c#L1671-L1684), "
                 "and Time zone the link names is the target after either prefix; systemd also checks the name "
                 "against the zone files, and this artifact does not. A copied zone file, as honeynet_fc7_debian5 "
                 "has it, is read as TZif data (RFC 9636, sections 3.1 to 3.3, "
                 "https://www.rfc-editor.org/rfc/rfc9636#section-3.1) and Time zone rule is the TZ string in its "
                 "footer, the rule for local time after the last transition the file lists "
                 "(https://www.rfc-editor.org/rfc/rfc9636#section-3.3), which names no zone; a version 1 file, which "
                 "has no footer, a footer whose string is empty, and a file that is neither a recorded link nor TZif "
                 "data are counted in the run log. Time zone name is the first line of /etc/timezone, a separate "
                 "file that can disagree with /etc/localtime. On ubuntu2604_arm64_sysinfo, captured from a VM "
                 "running systemd 259.5 and base-files 14ubuntu6.1, the 25 rows are 13 OS release and 1 OS release "
                 "link, 4 LSB release, and one each of Debian version, Host name, Machine ID, Machine ID link, Time "
                 "zone name, Time zone link and Time zone the link names; each OS release and LSB release value "
                 "equals the value /bin/sh read from the same file on the VM, and Host name equals what hostnamectl "
                 "reported, at capture. There /etc/timezone, recorded as modified 2026-08-12 12:02:56 UTC, names "
                 "America/Los_Angeles, while the /etc/localtime link, recorded 2026-08-31 14:34:16 UTC, points to "
                 "America/New_York, which timedatectl reported at capture; auth.log in ubuntu2604_arm64_triage, from "
                 "the same VM, carries +00:00 until 2026-08-12 12:17:01 UTC, -07:00, the offset America/Los_Angeles "
                 "had that day, from 12:20:36 to 12:30:47, +04:00 from 2026-08-31 14:34:15 to 20:12:49 and -04:00, "
                 "America/New_York's offset, from 2026-09-02 18:50:43 UTC, so its lines have not been written in "
                 "America/Los_Angeles's offset since 2026-08-12. ubuntu2604_arm64_triage gives 19 rows, the same "
                 "files without lsb-release, debian_version and the D-Bus link, and ubuntu2604_arm64_logins 15, its "
                 "os-release link, os-release and host name. On honeynet_fc7_debian5, which has no os-release, "
                 "lsb-release or machine-id, the 4 rows are Debian version 5.0.7, Host name, Time zone name "
                 "Europe/Paris and Time zone rule CET-1CEST,M3.5.0,M10.5.0/3 from its TZif copy of /etc/localtime.",
        "paths": ('*/etc/os-release', '*/usr/lib/os-release', '*/etc/lsb-release', '*/etc/debian_version',
                  '*/etc/hostname', '*/etc/machine-id', '*/var/lib/dbus/machine-id', '*/etc/timezone',
                  '*/etc/localtime'),
        "output_types": ["html", "tsv", "lava"],
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 4 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 15 rows",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 25 rows",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 19 rows",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
        "artifact_icon": "monitor",
    }
}

import re
import struct
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_link, recorded_time, seeker_of

# (path the file ends with, the property its rows carry, how it is read), in the order rows are reported.
FILES = (
    ('etc/os-release', 'OS release', 'assignments'),
    ('usr/lib/os-release', 'OS release', 'assignments'),
    ('etc/lsb-release', 'LSB release', 'assignments'),
    ('etc/debian_version', 'Debian version', 'line'),
    ('etc/hostname', 'Host name', 'line'),
    ('etc/machine-id', 'Machine ID', 'line'),
    ('var/lib/dbus/machine-id', 'Machine ID', 'line'),
    ('etc/timezone', 'Time zone name', 'line'),
    ('etc/localtime', 'Time zone', 'localtime'),
)
_ASSIGNMENT = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)=(.*)')
_ZONEINFO = ('/usr/share/zoneinfo/', '../usr/share/zoneinfo/')
NOT_ONE_WORD = 'values that are not one plain shell word, reported as written'


def shell_word(raw):
    """The value of an assignment's right-hand side as a POSIX shell reads it, or None when it is not one word
    the shell reads without expanding anything: unquoted text, single quotes, and double quotes in which a
    backslash escapes $, `, ", backslash or a newline and nothing else."""
    out = []
    i = 0
    while i < len(raw):
        char = raw[i]
        if char == "'":
            end = raw.find("'", i + 1)
            if end < 0:
                return None
            out.append(raw[i + 1:end])
            i = end + 1
        elif char == '"':
            i += 1
            while i < len(raw) and raw[i] != '"':
                if raw[i] in '$`':
                    return None
                if raw[i] == '\\' and i + 1 < len(raw) and raw[i + 1] in '$`"\\\n':
                    out.append(raw[i + 1])
                    i += 2
                else:
                    out.append(raw[i])
                    i += 1
            if i >= len(raw):
                return None
            i += 1
        elif char == '\\':
            if i + 1 >= len(raw):
                return None
            out.append(raw[i + 1])
            i += 2
        elif char in ' \t':
            rest = raw[i:].strip()
            if rest and not rest.startswith('#'):
                return None
            break
        elif char in '$`;&|<>()':
            return None
        else:
            out.append(char)
            i += 1
    return ''.join(out)


def assignments(text, counts):
    """(key, value) for each variable assignment in an os-release style file, in file order."""
    pairs = []
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = _ASSIGNMENT.fullmatch(line)
        if not match:
            counts['lines that are not variable assignments, not reported'] += 1
            continue
        key, raw = match.groups()
        value = shell_word(raw)
        if value is None:
            counts[NOT_ONE_WORD] += 1
            value = raw
        pairs.append((key, value))
    return pairs


def first_line(text):
    """The first line that is not blank and not a # comment, without surrounding white space, or None."""
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            return line
    return None


def tzif_rule(data):
    """The TZ string in the footer of TZif data of version 2, 3 or 4, '' for version 1 data, which has no footer,
    or None for data that is not TZif as RFC 9636 lays it out."""
    if len(data) < 44 or data[:4] != b'TZif':
        return None
    if data[4:5] == b'\0':
        return ''
    if data[4:5] not in (b'2', b'3', b'4'):
        return None
    try:
        isut, isstd, leap, times, types, chars = struct.unpack('>6L', data[20:44])
        second = 44 + times * 5 + types * 6 + chars + leap * 8 + isstd + isut
        if data[second:second + 4] != b'TZif':
            return None
        isut, isstd, leap, times, types, chars = struct.unpack('>6L', data[second + 20:second + 44])
    except struct.error:
        return None
    footer = data[second + 44 + times * 9 + types * 6 + chars + leap * 12 + isstd + isut:]
    end = footer.find(b'\n', 1)
    if footer[:1] != b'\n' or end < 0:
        return None
    return footer[1:end].decode('ascii', errors='replace')


def file_rows(kind, prop, data, link, counts):
    """(property, value, key) for one file: its link, or what its content holds."""
    if link is not None:
        rows = [(prop + ' link', link, '')]
        if kind == 'localtime':
            for prefix in _ZONEINFO:
                if link.startswith(prefix) and link[len(prefix):]:
                    rows.append(('Time zone the link names', link[len(prefix):], ''))
                    break
        return rows
    if kind == 'localtime':
        rule = tzif_rule(data)
        if rule is None:
            counts['localtime files that are neither a recorded link nor TZif data, not reported'] += 1
            return []
        if rule == '':
            counts['TZif files with no TZ string in a footer, not reported'] += 1
            return []
        return [('Time zone rule', rule, '')]
    text = data.decode('utf-8', errors='replace')
    if first_line(text) is None:
        counts['files with no line of text, not reported'] += 1
        return []
    if kind == 'assignments':
        return [(prop, value, key) for key, value in assignments(text, counts)]
    return [(prop, first_line(text), '')]


def file_kind(relative):
    relative = relative.replace('\\', '/')
    for order, (suffix, prop, kind) in enumerate(FILES):
        if relative == suffix or relative.endswith('/' + suffix):
            return order, prop, kind
    return None


@artifact_processor
def linuxSystemInfo(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Property', 'Value', 'Key', 'Source File')
    seeker = seeker_of(context)
    found = []
    counts = Counter()
    for path in map(str, context.get_files_found()):
        relative = context.get_relative_path(path)
        kind = file_kind(relative)
        if kind is None:
            continue
        found.append((kind[0], relative, path, kind[1], kind[2]))
    data_list = []
    read = []
    for _order, relative, path, prop, kind in sorted(found):
        link = recorded_link(seeker, path)
        data = b''
        if link is None:
            try:
                with open(path, 'rb') as handle:
                    data = handle.read()
            except OSError:
                counts['files that could not be read'] += 1
                continue
        rows = file_rows(kind, prop, data, link, counts)
        when = recorded_time(seeker, path, link)
        data_list.extend((when, *row, relative) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc('Linux System Information: ' + ', '.join(f'{count} {what}' for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
