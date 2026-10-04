"""Entries in the Windows, macOS and Linux hosts files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsHostsFile": {
        "name": "Windows Hosts File",
        "description": "Address entries in the Windows hosts file, one row per line that maps an "
                       "address to host names, with any comment on the line.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows\\System32\\drivers\\etc\\hosts, one row per line that holds an "
                 "address. The comment block of the default file describes the format: each entry "
                 "on its own line, the IP address in the first column followed by the host name, "
                 "separated by at least one space, and comments after a '#' symbol, on their own "
                 "lines or following the machine name (lines 5 to 12 of the file on the tested "
                 "images). Line is the line number, Address the first field, Host Names the other "
                 "fields joined with a space, and Comment the text after a '#' on the same line. A "
                 "line with nothing before any '#' gives no row. The file is decoded as UTF-16 "
                 "when it begins with a UTF-16 byte order mark, and otherwise as UTF-8 with any "
                 "byte order mark removed and undecodable bytes replaced. af_case2_win10 held one "
                 "entry, on line 23 after the default comment block. lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10 held byte-identical 824-byte files whose "
                 "example and localhost lines are "
                 "all commented out, so they give no rows.",
        "paths": ('*/Windows/System32/drivers/etc/hosts',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "address-book",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (every address line in the file is commented out)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (every address line in the file is commented out)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (every address line in the file is commented out)",
        },
    },
    "macosHostsFile": {
        "name": "Hosts File",
        "description": "Address entries in the macOS hosts file, one row per line that maps an "
                       "address to host names, with any comment on the line.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Networks (macOS)",
        "notes": "Reads private/etc/hosts, one row per line that holds an address, and skips the "
                 "copy under System/Library/Templates. Apple's hosts(5) describes the format: one "
                 "line per host with the Internet address, the official host name and any aliases, "
                 "items separated by blanks or tabs, and a '#' beginning a comment that runs to "
                 "the end of the line. It also says mDNSResponder reads the file to supply results "
                 "for calls such as getaddrinfo, in addition to DNS results (files-974.120.2, "
                 "https://github.com/apple-oss-distributions/files/blob/5fc07dd6ecbaa178fff2431dc99e4dffd611ea2d/usr/share/man/man5/hosts.5#L44-L76). "
                 "Line is the line number, Address the first field, Host Names the other fields "
                 "joined with a space, and Comment the text after a '#' on the same line. A line "
                 "with nothing before any '#' gives no row. The file is decoded as UTF-16 when it "
                 "begins with a UTF-16 byte order mark, and otherwise as UTF-8 with any byte order "
                 "mark removed and undecodable bytes replaced. When a logical extraction holds the "
                 "file under private/etc and again under System/Volumes/Data/private/etc, a copy "
                 "byte-identical to another is read once and counted in the run log. "
                 "dleapp_macos_bigsur held 3 entries, 127.0.0.1 and ::1 for localhost and "
                 "255.255.255.255 for broadcasthost, byte-identical to its template copy, and so "
                 "did the public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15"
                 ").",
        "paths": ('*/private/etc/hosts',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "address-book",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
        },
    },
    "linuxHostsFile": {
        "name": "Linux Hosts File",
        "description": "Address entries in Linux hosts files, one row per line that maps an "
                       "address to host names, with any comment on the line.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Networks (Linux)",
        "notes": "Reads etc/hosts wherever the extraction holds one, one row per line that holds "
                 "an address. It skips the macOS private/etc/hosts, including its template copy, "
                 "and the Windows drivers/etc/hosts, which the Hosts File and Windows Hosts File "
                 "artifacts report, and the run log counts the files skipped. The hosts(5) manual "
                 "page describes the format: one line per IP address with the address, the "
                 "canonical host name and any aliases, fields separated by blanks or tabs, and "
                 "text from a '#' to the end of the line a comment "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/hosts.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n17). "
                 "It also says changes to the file normally take effect immediately, except where "
                 "an application caches it "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/hosts.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n73). "
                 "Line is the line number, Address the first field, Host Names the other fields "
                 "joined with a space, Comment the text after a '#' on the same line, and Source "
                 "File the file the row came from, since the path also matches an etc/hosts inside "
                 "a container or chroot folder. A line with nothing before any '#' gives no row. "
                 "Fields are split on any whitespace, a wider set than the blanks and tabs the "
                 "page names. The file is decoded as UTF-16 when it begins with a UTF-16 byte "
                 "order mark, and otherwise as UTF-8 with any byte order mark removed and "
                 "undecodable bytes replaced. ubuntu2604_arm64_triage (Ubuntu 26.04) held 7 "
                 "entries in etc/hosts: 127.0.0.1 for localhost, a 127.0.1.1 line carrying the "
                 "name in etc/hostname, ::1 with two names, and four more IPv6 lines (fe00::0, "
                 "ff00::0, ff02::1, ff02::2). honeynet_fc7_debian5 (Debian 5) held 8 in "
                 "lba0/etc/hosts, the same addresses plus ff02::3, with ::1 carrying three names "
                 "and 127.0.1.1 again the name in etc/hostname. The Sleuth Kit's icat read that "
                 "file with the same SHA-256 as the copy the run staged. Comment held no value on "
                 "any of the 15 rows from the two images, since neither file has a comment after "
                 "an address. On the Windows and macOS images the path matched only the files the "
                 "other two artifacts report, and no other registered image holds an etc/hosts.",
        "paths": ('*/etc/hosts',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "address-book",
        "sample_data": {
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 8 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 7 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (only the Windows hosts file matches, skipped)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (only the macOS hosts file and its template match, skipped)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import unique_sources

_TEMPLATE = '/System/Library/Templates/'


def decode_text(data):
    """A hosts file's bytes as text: UTF-16 when it opens with a UTF-16 byte order mark,
    otherwise UTF-8 without any BOM, undecodable bytes replaced."""
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return data.decode('utf-16', 'replace')
    return data.decode('utf-8-sig', 'replace')


def hosts_entries(text):
    """(line number, address, host names, comment) for each line that holds an address.

    A '#' begins a comment that runs to the end of its line; the rest of a line is fields
    separated by blanks or tabs, the first the address and the others host names.
    """
    for number, line in enumerate(text.splitlines(), 1):
        body, hash_mark, comment = line.partition('#')
        fields = body.split()
        if fields:
            yield number, fields[0], ' '.join(fields[1:]), comment.strip() if hash_mark else ''


def is_template(relative):
    """Whether a path is the copy under System/Library/Templates rather than the live file."""
    return _TEMPLATE in '/' + str(relative).replace('\\', '/')


def _read(context, paths, label):
    data_list, sources = [], []
    for path in paths:
        try:
            with open(path, 'rb') as handle:
                text = decode_text(handle.read())
        except OSError as exc:
            logfunc(f'{label}: could not read {context.get_relative_path(path)}: {exc}')
            continue
        data_list.extend(hosts_entries(text))
        sources.append(path)
    return data_list, sources


_HEADERS = ('Line', 'Address', 'Host Names', 'Comment')


@artifact_processor
def windowsHostsFile(context):
    paths = sorted({str(f) for f in context.get_files_found() if os.path.isfile(str(f))})
    data_list, sources = _read(context, paths, 'Windows Hosts File')
    return _HEADERS, data_list, '\n'.join(sources)


@artifact_processor
def macosHostsFile(context):
    live = [str(f) for f in context.get_files_found()
            if not is_template(context.get_relative_path(str(f)))]
    paths, _skipped = unique_sources(context, live, label='Hosts File')
    data_list, sources = _read(context, paths, 'Hosts File')
    return _HEADERS, data_list, '\n'.join(sources)


def is_other_platform(relative):
    """Whether a path is the macOS (private/etc) or Windows (drivers/etc) hosts file, which
    have their own artifacts."""
    path = '/' + str(relative).replace('\\', '/').lower()
    return path.endswith(('/private/etc/hosts', '/drivers/etc/hosts'))


@artifact_processor
def linuxHostsFile(context):
    paths, skipped = [], 0
    for found in sorted({str(f) for f in context.get_files_found()}):
        if not os.path.isfile(found):
            continue
        if is_other_platform(context.get_relative_path(found)):
            skipped += 1
            continue
        paths.append(found)
    if skipped:
        logfunc(f'Linux Hosts File: {skipped} macOS or Windows hosts files skipped, reported by their own '
                'artifacts')
    data_list, sources = [], []
    for path in paths:
        rows, read = _read(context, [path], 'Linux Hosts File')
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        sources.extend(read)
    data_headers = ('Line', 'Address', 'Host Names', 'Comment', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
