"""User accounts Linux lists in /etc/passwd, with group names from /etc/group, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxUserAccounts": {
        "name": "User Accounts (passwd)",
        "description": "Accounts listed in Linux /etc/passwd files, with user and group IDs, group names from "
                       "/etc/group, comment, home directory, shell and password field as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Accounts (Linux)",
        "notes": "Reads each /etc/passwd the paths match, apart from the macOS copies described below, "
                 "one row per account line in file order, with group names from the /etc/group in the "
                 "same folder. Each "
                 "passwd line is read as the seven colon-separated fields passwd(5) gives, "
                 "name:password:UID:GID:GECOS:directory:shell "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/passwd.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n60, "
                 "lines 60 to 65); a line beginning with #, + or -, and a line that is not "
                 "seven fields with a numeric UID and GID, is counted in the run log and "
                 "not reported. Account, Comment, Home Directory and Shell are the name, "
                 "GECOS, directory and shell fields as stored, read as UTF-8 (a byte that "
                 "is not valid UTF-8 shows as the replacement character). Password Field "
                 "is the password field as stored: passwd(5) says that under the shadow "
                 "password suite it holds x and the encrypted passwords are kept in "
                 "/etc/shadow, readable by the superuser only "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/passwd.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n22, "
                 "lines 22 to 27), and that an empty encrypted password lets the account "
                 "log in without being asked for a password, unless an application or "
                 "pam_unix(8) is set to refuse that "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/passwd.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n29, "
                 "lines 29 to 40). Primary Group names the groups in the same folder's "
                 "/etc/group whose GID matches the account's, and Other Groups the groups "
                 "whose member list names the account, each group line read as the four "
                 "colon-separated fields group(5) gives "
                 "(https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/tree/man/man5/group.5?id=c420f73ec92dacd8c6801283e2e4c47e9a1828b7#n12, "
                 "lines 12 to 33); both are blank when no group file sits beside the "
                 "passwd file, which the run log counts. Source File names the passwd file "
                 "each row came from, because the paths can match more than one passwd "
                 "file in one image and each belongs to the system tree it sits in. A "
                 "passwd file in a private/etc folder is not read, because that is where "
                 "macOS keeps /etc and macOS's own copy says at its top that it is "
                 "consulted directly only when the system is running in single-user mode, "
                 "Open Directory providing this information at other times; the run log counts such "
                 "files. On the public MacBook Pro logical extraction its three copies, in private/etc, "
                 "System/Volumes/Data/private/etc and System/Library/Templates/Data/private/etc, were "
                 "counted and none was read. On ubuntu2604_arm64_logins and "
                 "ubuntu2604_arm64_triage, which hold the same passwd and group files, the "
                 "file held 49 accounts: Password Field held the same value, x, on all 49, and Shell was "
                 "/usr/sbin/nologin on 41, /bin/false on 5, /bin/bash on 2 and /bin/sync "
                 "on 1. Other Groups was filled on 3 accounts, and for each of them "
                 "Primary Group and Other Groups name the same groups the id command "
                 "reported for that account on the running system the same day. On honeynet_fc7_debian5 "
                 "the file held 23 accounts: Password Field held the same value, x, on all 23, Shell was "
                 "/bin/sh on 17, /bin/bash on 2, /bin/false on 2, /bin/sync on 1 and /usr/sbin/nologin on "
                 "1, and Other Groups was filled on 1 account.",
        "paths": ('*/etc/passwd', '*/etc/group'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (passwd and group only under private/etc, "
                                   "LZVN-compressed, which the image reader does not stage)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 23 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 49 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 49 rows",
        },
    },
}

import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc


def _lines(data):
    """The text lines of a file, without their line ends."""
    return [line.rstrip('\r') for line in data.decode('utf-8', errors='replace').split('\n')]


def passwd_records(data):
    """(records, counts): the seven fields of each account line of an /etc/passwd file, and a count
    of the lines left out, by reason."""
    records, counts = [], Counter()
    for line in _lines(data):
        if not line:
            continue
        if line[0] in '#+-':
            counts['passwd lines beginning with #, + or -, not reported'] += 1
            continue
        fields = line.split(':')
        if len(fields) != 7 or not fields[2].isdigit() or not fields[3].isdigit():
            counts['passwd lines that are not seven fields with a numeric UID and GID, not reported'] += 1
            continue
        records.append(fields)
    return records, counts


def group_records(data):
    """[(name, gid, members)] for the lines of an /etc/group file that are four colon-separated
    fields with a numeric GID."""
    groups = []
    for line in _lines(data):
        if not line or line[0] in '#+-':
            continue
        fields = line.split(':')
        if len(fields) != 4 or not fields[2].isdigit():
            continue
        groups.append((fields[0], int(fields[2]), [member for member in fields[3].split(',') if member]))
    return groups


def _in_private_etc(path):
    """True for a file in a private/etc folder, where macOS keeps /etc."""
    parts = path.replace('\\', '/').split('/')
    return any(first == 'private' and second == 'etc' for first, second in zip(parts, parts[1:]))


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


@artifact_processor
def linuxUserAccounts(context):
    data_headers = ('Account', 'UID', 'GID', 'Primary Group', 'Other Groups', 'Comment', 'Home Directory',
                    'Shell', 'Password Field', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    files = [str(p) for p in context.get_files_found() if not os.path.isdir(p)]
    group_files = {os.path.normpath(p): p for p in files if os.path.basename(p) == 'group'}
    for path in sorted(p for p in files if os.path.basename(p) == 'passwd'):
        if _in_private_etc(path):
            problems['passwd files in a private/etc folder (macOS), not read'] += 1
            continue
        try:
            records, counts = passwd_records(_read(path))
        except OSError:
            problems['passwd files that could not be read'] += 1
            continue
        problems.update(counts)
        beside = os.path.normpath(os.path.join(os.path.dirname(path), 'group'))
        groups = []
        if beside in group_files:
            try:
                groups = group_records(_read(group_files[beside]))
            except OSError:
                problems['group files that could not be read'] += 1
        else:
            problems['passwd files with no group file beside them, so no group names'] += 1
        relative = context.get_relative_path(path)
        for name, password, uid, gid, gecos, home, shell in records:
            primary = ', '.join(group for group, number, _members in groups if number == int(gid))
            others = ', '.join(group for group, _number, members in groups if name in members)
            data_list.append((name, int(uid), int(gid), primary, others, gecos, home, shell, password, relative))
        if records:
            read.append(path)
            if beside in group_files:
                read.append(group_files[beside])
    if problems:
        logfunc('User Accounts (passwd): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
