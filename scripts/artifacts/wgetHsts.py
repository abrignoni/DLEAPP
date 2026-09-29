"""Hosts in the HSTS store GNU Wget keeps in the home folder (.wget-hsts), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "wgetHsts": {
        "name": "wget HSTS Hosts",
        "description": "Hosts in the HSTS store GNU Wget keeps in the home folder (.wget-hsts), each with the time "
                       "wget last received the host's HSTS header and how long wget applies it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Command Line (wget)",
        "notes": "Reads the HSTS store GNU Wget keeps as .wget-hsts in the home folder (Reference: GNU Wget "
                 "1.25.0, 'src/main.c' lines 173 to 186, https://ftp.gnu.org/gnu/wget/wget-1.25.0.tar.gz); a store "
                 "named with --hsts-file or the hstsfile setting is not read ('src/main.c' line 339, 'src/init.c' "
                 "line 223). HSTS is on unless --no-hsts or the hsts setting turns it off ('src/init.c' line 511). "
                 "wget then reads the store when it starts and, if the store changed during the run, writes it "
                 "back when it finishes ('src/main.c' lines 2113 to 2114, 2296 to 2297 and 213 to 231), first "
                 "reading in any change another wget made to the file meanwhile ('src/hsts.c' lines 551 to 586). A "
                 "run with --no-hsts neither reads nor writes it, which on ubuntu2604_arm64_wgethsts left the "
                 "store unchanged although the host fetched sends the header. The store holds three comment lines "
                 "and then one line per host: the host, the port, a subdomains flag, a created time and a max-age, "
                 "separated by tabs, in the order of wget's hash table ('src/hsts.c' lines 313 to 337). Created "
                 "(UTC) is the created time, seconds since 1970 by the system clock: wget sets it when it first "
                 "receives a Strict-Transport-Security header from the host over https and resets it each time it "
                 "receives one again with a max-age above 0, and a header with a max-age of 0 removes the host "
                 "('src/hsts.c' lines 216 to 227 and 438 to 498); the removal was read in the source and not "
                 "exercised. Max-Age (s) is the header's max-age as stored, and Expires (UTC) is created plus "
                 "max-age, after which wget stops applying the entry and removes it the next time it is asked for "
                 "the host over plain http ('src/hsts.c' lines 374 to 413). Port is as stored, 0 standing for the "
                 "default https port, 443 ('src/hsts.c' lines 80 to 83), and Include Subdomains is Yes when the "
                 "flag is not 0, as wget reads it, meaning wget also sends the host's subdomains to https. The "
                 "artifact reads a line as wget does, with sscanf and five fields ('src/hsts.c' lines 272 to 311): "
                 "a line starting with # after any spaces is a comment, a host longer than 255 bytes or a line "
                 "without all four numbers is not read and is counted in the run log, and a number too large for "
                 "its field, which wget reads with a value its C library decides, is counted and not reported, "
                 "tested with constructed input only. A time outside what a date can hold is left blank and "
                 "counted. When it loads the store, wget passes over a line whose host is an IP address or repeats "
                 "a host and port already read, and one whose created plus max-age is below its created time "
                 "('src/hsts.c' lines 166 to 210); the compiled wget 1.25.0 on the lab VM applied that last test "
                 "as a negative max-age and kept lines whose sum passes the 64-bit range. The lines wget passes "
                 "over stay in the file only until wget next writes it; the artifact reports them as stored. The "
                 "artifact's reading was compared with wget's own on the lab VM: 300 generated stores, 1,969 lines "
                 "of which the artifact reads 531, were each passed to wget 1.25.0 with --hsts-file for a request "
                 "to a local https server that sends the header, so that wget wrote back what it had loaded, and "
                 "on every store the 278 lines wget kept were, after those checks and in the form wget writes (the "
                 "host in lower case, port 443 as 0, the flag as 0 or 1), the ones the artifact reads. A host in "
                 "the store shows that wget received an HSTS header from it over https at the created time; the "
                 "store does not record the URL, what was downloaded, or who ran wget. Rows are in the order the "
                 "file holds them, and Line is the line of the file a host is on. Source File is the file a row "
                 "comes from, and the report's located-at line names the files that held a row; a file that cannot "
                 "be read is counted in the run log and not reported. On ubuntu2604_arm64_wgethsts, captured from "
                 "a VM running wget 1.25.0 after four known runs, the 2 rows are ubuntu.com, fetched over https, "
                 "and github.com, fetched over https and about 6 seconds later over plain http, which wget sent to "
                 "https because the host was in the store, resetting its created time to the second request's; the "
                 "run with --no-hsts added nothing. No member of the other twenty-four tested images matches the "
                 "declared path.",
        "paths": ("*/.wget-hsts",),
        "output_types": "standard",
        "artifact_icon": "globe",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64, wget 1.25.0 | 2 rows",
        },
    },
}

import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

WHITESPACE = b' \t\n\v\f\r'
INT_LIMITS = (-2 ** 31, 2 ** 31 - 1)
INT64_LIMITS = (-2 ** 63, 2 ** 63 - 1)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _skip(text, at):
    while at < len(text) and text[at] in WHITESPACE:
        at += 1
    return at


def _integer(text, at, limits):
    """(value, index after it) for a signed decimal number after optional whitespace, as sscanf's %d reads one;
    None for the value when there is none or it does not fit."""
    at = _skip(text, at)
    start = at
    if at < len(text) and text[at] in b'+-':
        at += 1
    digits = at
    while at < len(text) and text[at] in b'0123456789':
        at += 1
    if at == digits:
        return None, at
    value = int(text[start:at])
    return (value if limits[0] <= value <= limits[1] else None), at


def scan_line(text):
    """(host, port, include subdomains, created, max-age) for the bytes of a line of the store as wget reads it,
    with sscanf(p, "%255s %d %d %" SCNd64 " %" SCNd64); None for a comment or a blank line, and False for a line wget
    does not read."""
    at = _skip(text, 0)
    if at >= len(text) or text[at] == ord('#'):
        return None
    end = at
    while end < len(text) and text[end] not in WHITESPACE and end - at < 255:
        end += 1
    host = text[at:end].decode('utf-8', errors='backslashreplace')
    port, end = _integer(text, end, INT_LIMITS)
    include, end = _integer(text, end, INT_LIMITS)
    created, end = _integer(text, end, INT64_LIMITS)
    max_age, end = _integer(text, end, INT64_LIMITS)
    if None in (port, include, created, max_age):
        return False
    return host, port, include, created, max_age


def utc(seconds):
    """The UTC time of a count of seconds since 1970, or '' when it is outside what a datetime can hold."""
    try:
        return EPOCH + timedelta(seconds=seconds)
    except OverflowError:
        return ''


def store_rows(data, counts):
    """The rows for the bytes of a .wget-hsts file, in file order: (created, host, port, include subdomains,
    max-age, expires, line number)."""
    rows = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        entry = scan_line(raw)
        if entry is None:
            continue
        if entry is False:
            counts['lines wget does not read, not reported'] += 1
            continue
        host, port, include, created, max_age = entry
        when, expires = utc(created), utc(created + max_age)
        if when == '' or expires == '':
            counts['times outside the range of a date, left blank'] += 1
        rows.append((when, host, port, 'Yes' if include else 'No', max_age, expires, number))
    return rows


@artifact_processor
def wgetHsts(context):
    data_headers = (('Created (UTC)', 'datetime'), 'Host', 'Port', 'Include Subdomains', 'Max-Age (s)',
                    ('Expires (UTC)', 'datetime'), 'Line', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = store_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('wget HSTS Hosts: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
