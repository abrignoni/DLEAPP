"""Package installs, upgrades and removals Linux records in apt's history.log and dpkg's dpkg.log, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "aptHistory": {
        "name": "Package History (apt)",
        "description": "Package installs, reinstalls, upgrades, downgrades and removals recorded in apt's "
                       "history.log and its rotations, with each transaction's start and end times as recorded, "
                       "its command line and requesting user, and each package's versions.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Installed Software (Linux)",
        "notes": "Reads /var/log/apt/history.log and its numbered rotations, gzip ones "
                 "included, one row per package entry of each transaction in file order. "
                 "apt 3.2.0, the version on the VM the tested image was taken from, writes "
                 "a transaction as tag lines that begin with Start-Date, "
                 "then Commandline, Requested-By and Comment, one package list each for "
                 "Install, Reinstall, Upgrade, Downgrade, Remove and Purge "
                 "(https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/deb/dpkgpm.cc#L1052-1097), "
                 "and at the end a Disappeared list when packages disappeared, Error when "
                 "dpkg failed, and End-Date "
                 "(https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/deb/dpkgpm.cc#L1124-1141). "
                 "Command Line, Requested By, Comment and Error are those tags as stored. "
                 "apt writes Requested-By, as a user name and user ID, only when the "
                 "SUDO_UID, PKEXEC_UID or PACKAGEKIT_CALLER_UID environment variable names "
                 "a user ID above 0 "
                 "(https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/deb/dpkgpm.cc#L68-95), "
                 "so a blank Requested By does not say who ran the command. Package is "
                 "each entry's name as apt wrote it, and its versions in parentheses read "
                 "as follows: for an install or a reinstall, the version installed, shown "
                 "as To Version, with Automatic yes where apt added automatic after it; "
                 "for an upgrade or a downgrade, the current and the new version, shown as "
                 "From Version and To Version; for a removal, a purge or a disappeared "
                 "package, the current version, shown as From Version. A package list that "
                 "does not read as whole entries, a line that is not a tag and a value, "
                 "and a transaction with no package entry are counted in the run log and "
                 "not reported. Start Time (local) and End Time (local) are Start-Date and "
                 "End-Date as stored: apt writes both from the local time of the machine "
                 "and records no time zone "
                 "(https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/deb/dpkgpm.cc#L1014-1018, "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/deb/dpkgpm.cc#L1107-1111), "
                 "so they are not converted. On ubuntu2604_arm64_triage the last End-Date, "
                 "2026-09-25 11:13:11, equals history.log's modification time in New York "
                 "time, the zone its /etc/localtime names, while its /etc/timezone names "
                 "America/Los_Angeles, so on that image /etc/timezone would give the wrong "
                 "zone. history.log and history.log.1.gz held 189 transactions, "
                 "the first starting 2026-04-22 08:33:09 and the last ending 2026-09-25 "
                 "11:13:11, and 2,339 package entries: 1,549 Install, 1,191 of them with "
                 "Automatic yes, 389 Reinstall, 317 Upgrade, 47 Remove and 37 Purge. "
                 "Requested By was filled on 1,003 rows, from 33 transactions, and Comment "
                 "and Error were blank on every row. Each of the 2,339 entries has a "
                 "dpkg.log action line for the same package and versions between its "
                 "transaction's start and end times, once apt's :arm64 is read as dpkg's "
                 ":all for the 601 entries dpkg names with :all (see Package Actions "
                 "(dpkg.log)).",
        "paths": ('*/var/log/apt/history.log', '*/var/log/apt/history.log.[0-9]*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 2339 rows",
        },
    },
    "dpkgLog": {
        "name": "Package Actions (dpkg.log)",
        "description": "Package installs, upgrades, removals and purges recorded in dpkg.log and its rotations, "
                       "with the time recorded and the installed and available versions as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Installed Software (Linux)",
        "notes": "Reads /var/log/dpkg.log and its numbered rotations, gzip ones included, "
                 "one row per install, upgrade, remove, purge or disappear line in file "
                 "order. dpkg 1.23.7, the upstream release of the dpkg 1.23.7ubuntu1 on the "
                 "VM ubuntu2604_arm64_triage was taken from, documents its log lines as a "
                 "date and "
                 "time followed "
                 "by startup, by status, by one of the actions install, upgrade, "
                 "configure, trigproc, disappear, remove or purge with a package and its "
                 "installed and available versions, or by conffile "
                 "(https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/dpkg.pod#L1228-L1256); "
                 "the dpkg(1) page installed on that VM gives the same list. Package, "
                 "Installed Version and Available Version "
                 "are those fields as stored, <none> included. Startup, status, configure, "
                 "trigproc and conffile lines, and any line that does not read as a date, "
                 "a time and a package action with two versions, are counted in the run "
                 "log and not reported. Time (local) is the date and time as stored: dpkg "
                 "writes it from the local time of the machine and records no time zone "
                 "(https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/log.c#L64-L70), "
                 "so it is not converted. dpkg 1.14.31, which wrote honeynet_fc7_debian5's "
                 "dpkg.log, stamps a line the same way (lib/log.c, "
                 "https://github.com/guillemj/dpkg/blob/6f4708b786579fa5fdb4d992459332c5c13c9bfb/lib/log.c#L71-L74). "
                 "On ubuntu2604_arm64_triage the last line's time, "
                 "2026-09-25 11:13:11, equals dpkg.log's modification time in New York "
                 "time, the zone its /etc/localtime names. dpkg.log and dpkg.log.1 held "
                 "2,453 action lines, the first at 2026-04-22 08:32:52 and the last at "
                 "2026-09-25 11:13:11: 1,635 install, 713 upgrade, 84 remove and 21 purge; "
                 "14,477 status, 2,348 configure, 686 startup, 279 trigproc and 1 conffile "
                 "lines were counted and not reported. For 601 of apt's 2,339 package "
                 "entries on that image, dpkg.log names the package with :all where "
                 "history.log uses :arm64. On honeynet_fc7_debian5, whose "
                 "/var/lib/dpkg/status records dpkg 1.14.31, the last line's time, "
                 "2011-02-06 12:51:49, is the file's modification time as The Sleuth Kit's "
                 "istat reports it, 2011-02-06 11:51:49 UTC, in Europe/Paris time, the zone "
                 "its /etc/timezone names. dpkg.log held 275 action lines, the first at "
                 "2011-01-18 08:16:55 and the last at 2011-02-06 12:51:48: 251 install, 16 "
                 "upgrade, 7 remove and 1 purge; 2,185 status, 265 configure, 70 startup and "
                 "29 trigproc lines were counted and not reported.",
        "paths": ('*/var/log/dpkg.log', '*/var/log/dpkg.log.[0-9]*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 275 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 2453 rows",
        },
    },
}

import gzip
import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

# The tags apt writes a package list under, in the order it writes them, and how each entry's
# parenthesised versions read: apt's dpkgpm.cc writes the candidate version for an install or a
# reinstall (an install may add ", automatic"), the current and the candidate version for an
# upgrade or a downgrade, and the current version for a removal, a purge or a package that
# disappeared, which may also carry no version at all.
_PACKAGE_TAGS = {'Install': 'to', 'Reinstall': 'to', 'Upgrade': 'both', 'Downgrade': 'both',
                 'Remove': 'from', 'Purge': 'from', 'Disappeared': 'from'}
_TEXT_TAGS = ('Commandline', 'Requested-By', 'Comment', 'Error')
_TAG_LINE = re.compile(r'([A-Za-z-]+): (.*)')
_ENTRY = re.compile(r'([^\s,()]+)(?: \(([^()]*)\))?(?:, |$)')
# dpkg's own log lines: date, time, then what happened.
_DPKG_LINE = re.compile(r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\S+) (.*)')
_DPKG_ACTIONS = ('install', 'upgrade', 'remove', 'purge', 'disappear')


def _read(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rb') as handle:
        return handle.read()


def _lines(data):
    return [line.rstrip('\r') for line in data.decode('utf-8', errors='replace').split('\n')]


def package_entries(value):
    """[(package, versions)] for one of apt's package lists, or None when the list does not read
    as whole entries."""
    entries, end = [], 0
    for match in _ENTRY.finditer(value):
        if match.start() != end:
            return None
        entries.append((match.group(1), match.group(2)))
        end = match.end()
        if end == len(value):
            return entries
    return entries if end == len(value) else None


def history_transactions(data):
    """([transaction], counts): each transaction a dict of the tags apt wrote for it, in file order."""
    transactions, counts, current = [], Counter(), None
    for line in _lines(data):
        if not line:
            continue
        match = _TAG_LINE.fullmatch(line)
        if not match:
            counts['history lines that are not a tag and a value, not reported'] += 1
            continue
        tag, value = match.groups()
        if tag == 'Start-Date':
            current = {'Start-Date': value}
            transactions.append(current)
        elif current is None:
            counts['history lines before the first Start-Date, not reported'] += 1
        elif tag in current:
            counts['history tags repeated within one transaction, the first kept'] += 1
        else:
            current[tag] = value
    return transactions, counts


def history_rows(transaction, counts):
    """The rows for one transaction: one per package entry in its package lists."""
    rows = []
    for tag, reads in _PACKAGE_TAGS.items():
        if tag not in transaction:
            continue
        entries = package_entries(transaction[tag])
        if entries is None:
            counts[f'{tag} lists that do not read as whole package entries, not reported'] += 1
            continue
        for package, versions in entries:
            parts = versions.split(', ') if versions else []
            automatic = 'yes' if parts[-1:] == ['automatic'] else ''
            if automatic:
                parts = parts[:-1]
            if reads == 'both' and len(parts) == 2:
                before, after = parts
            elif reads == 'to':
                before, after = '', ', '.join(parts)
            else:
                before, after = ', '.join(parts), ''
            rows.append((tag, package, before, after, automatic))
    return rows


@artifact_processor
def aptHistory(context):
    data_headers = ('Start Time (local)', 'End Time (local)', 'Action', 'Package', 'From Version', 'To Version',
                    'Automatic', 'Requested By', 'Command Line', 'Comment', 'Error', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = _read(path)
        except (OSError, EOFError):
            problems['history files that could not be read'] += 1
            continue
        transactions, counts = history_transactions(data)
        problems.update(counts)
        relative = context.get_relative_path(path)
        before = len(data_list)
        for transaction in transactions:
            rows = history_rows(transaction, problems)
            if not rows:
                problems['transactions with no package entry, not reported'] += 1
            text = tuple(transaction.get(tag, '') for tag in _TEXT_TAGS)
            for action, package, version_from, version_to, automatic in rows:
                data_list.append((transaction['Start-Date'], transaction.get('End-Date', ''), action, package,
                                  version_from, version_to, automatic, text[1], text[0], text[2], text[3],
                                  relative))
        if len(data_list) > before:
            read.append(path)
    if problems:
        logfunc('Package History (apt): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


def dpkg_rows(data, counts):
    """(time, action, package, installed version, available version) for each action line of a
    dpkg.log; every other line is counted by its kind."""
    rows = []
    for line in _lines(data):
        if not line:
            continue
        match = _DPKG_LINE.fullmatch(line)
        if not match:
            counts['dpkg.log lines that do not begin with a date and time, not reported'] += 1
            continue
        when, kind, rest = match.groups()
        fields = rest.split(' ')
        if kind in _DPKG_ACTIONS and len(fields) == 3:
            rows.append((when, kind) + tuple(fields))
        elif kind in _DPKG_ACTIONS:
            counts[f'{kind} lines that are not a package and two versions, not reported'] += 1
        else:
            counts[f'{kind} lines, not reported'] += 1
    return rows


@artifact_processor
def dpkgLog(context):
    data_headers = ('Time (local)', 'Action', 'Package', 'Installed Version', 'Available Version', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            data = _read(path)
        except (OSError, EOFError):
            problems['dpkg.log files that could not be read'] += 1
            continue
        rows = dpkg_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Package Actions (dpkg.log): ' + ', '.join(
            f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
