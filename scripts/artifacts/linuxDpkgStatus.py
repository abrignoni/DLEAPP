"""Packages in dpkg's status database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "dpkgPackageStatus": {
        "name": "Package Status (dpkg)",
        "description": "One row per package dpkg's status database records, installed or not: its version, "
                       "architecture and state as stored, whether apt marks it automatically installed, and when "
                       "dpkg last wrote the package's file list.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Installed Software (Linux)",
        "notes": "One row per stanza that has a Package field, in each var/lib/dpkg/status file the declared paths "
                 "match, the file in which dpkg records whether each package it knows is installed or marked for "
                 "removal (Reference: dpkg, 'dpkg.pod', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/dpkg.pod#L1547-L1554), "
                 "in the order the file stores them, with Source File naming the status file, so a chroot or "
                 "container that keeps its own database gives rows of its own. Stanzas are read the way dpkg's "
                 "parser reads them: an empty line ends a stanza, a line that begins with white space continues "
                 "the field before it, and field names are matched without regard to case (Reference: dpkg, "
                 "'parse.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/parse.c#L631-L750, "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/parse.c#L122). "
                 "A line that is neither a field nor the continuation of one, and a stanza with no Package field, "
                 "are counted in the run log and not reported. Status is the stanza's Status field as stored, "
                 "which dpkg writes as three words: the selection (unknown, install, hold, deinstall or purge), a "
                 "flag (ok, or reinstreq for a package that needs reinstalling) and the package state "
                 "(not-installed, config-files, half-installed, unpacked, half-configured, triggers-awaited, "
                 "triggers-pending or installed), which dpkg's manual describes (Reference: dpkg, 'dpkg.pod', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/dpkg.pod#L78-L168) "
                 "and dpkg writes from these names (Reference: dpkg, 'pkg-namevalue.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/pkg-namevalue.c#L52-L92). "
                 "deinstall ok config-files marks a package removed with only its configuration files, or its "
                 "postrm script and the data that script needs, left on the system, install ok unpacked one "
                 "unpacked and not configured, and hold ok installed one held at its version; the known steps of "
                 "ubuntu2604_arm64_packages produced each of them. dpkg writes a stanza only for a package whose "
                 "selection is not unknown, whose flag is not ok, whose state is not not-installed, or that still "
                 "has control information such as a version (Reference: dpkg, 'dump.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/dump.c#L540-L542; "
                 "'pkg.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/pkg.c#L194-L217). "
                 "dpkg 1.23.7 resets the selection to unknown when a purge ends, so a purged package leaves no "
                 "stanza (Reference: dpkg, 'remove.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/remove.c#L735-L741), "
                 "as the known purge showed, while dpkg 1.14.31 leaves the selection at purge (Reference: dpkg, "
                 "'remove.c', "
                 "https://github.com/guillemj/dpkg/blob/6f4708b786579fa5fdb4d992459332c5c13c9bfb/src/remove.c#L565-L605; "
                 "'database.c', "
                 "https://github.com/guillemj/dpkg/blob/6f4708b786579fa5fdb4d992459332c5c13c9bfb/lib/database.c#L96-L107), "
                 "so a database it wrote can keep a purge ok not-installed stanza after a purge: "
                 "honeynet_fc7_debian5, whose installed dpkg is 1.14.31, holds one, with no file list. File List "
                 "Written (UTC) is the modified time the extraction recorded for the package's file list in the "
                 "same var/lib/dpkg: info/<package>.list, or info/<package>:<architecture>.list for a Multi-Arch: "
                 "same package when info/format marks the multiarch layout; dpkg reads a missing format file as "
                 "the older layout (Reference: dpkg, 'db-ctrl-format.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/db-ctrl-format.c#L41-L61, "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/db-ctrl-format.c#L127-L146), "
                 "and where no format file was found the plain name is tried first and then the qualified one. "
                 "dpkg writes the list when it unpacks the package, when another package takes over files it held, "
                 "and while it removes or purges the package, and deletes it at the end of a purge (Reference: "
                 "dpkg, 'db-fsys-files.c', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/lib/dpkg/db-fsys-files.c#L321-L349, "
                 "called at "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/unpack.c#L1690, "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/unpack.c#L1223, "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/remove.c#L393, "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/remove.c#L504 "
                 "and "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/remove.c#L675; "
                 "the deletion is at "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/src/main/remove.c#L723-L727). "
                 "So the time is when dpkg last wrote the list, which is not necessarily when the package was "
                 "first installed. Measured with the known steps: dleapp-known-a's list carries the second of K6, "
                 "when dleapp-known-e took over one of its files, not K1, its install, or K5, its upgrade; "
                 "dleapp-known-b's carries K7, its removal; and each of the other four the second of its own "
                 "install or unpack. A list's time can be earlier than anything the system's journal holds: on "
                 "ubuntu2604_arm64_packages 452 of the 1,561 system lists carry a time on 2026-04-22, the date of "
                 "dpkg.log's first line and of info/format, 939 on 2026-08-12, 2 on 2026-08-31, 99 on 2026-09-12 "
                 "and 69 on 2026-09-25, while the earliest entry of the same VM's journal "
                 "(ubuntu2604_arm64_journal) is from 2026-08-12. The column is blank where no file list was found, "
                 "as for honeynet_fc7_debian5's purge ok not-installed stanza, or where the extraction recorded no "
                 "time for it. Automatically Installed (apt) is Yes where apt's extended_states file in the same "
                 "system (var/lib/apt/extended_states) holds an Auto-Installed value above 0 for the package, and "
                 "No where that file holds none; apt marks a package it installs to satisfy another package's "
                 "dependencies as automatically installed and a package installed explicitly as manual, and "
                 "apt-mark auto and apt-mark manual change the mark (Reference: apt, 'apt-mark.8.xml', "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/doc/apt-mark.8.xml#L41-L66). "
                 "apt reads a stanza without Architecture as applying to every architecture of the package "
                 "(Reference: apt, 'depcache.cc', "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/depcache.cc#L302-L325) "
                 "and files a package whose Architecture is all under the native architecture (Reference: apt, "
                 "'pkgcachegen.cc', "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/pkgcachegen.cc#L673-L674; "
                 "'depcache.cc', "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/depcache.cc#L423-L433), "
                 "so for such a package a mark under any architecture counts. The column is blank where no "
                 "extended_states file sits in the same system, and on a config-files or not-installed row, "
                 "because apt drops the mark of a package that is no longer installed when it rewrites the file "
                 "(Reference: apt, 'depcache.cc', "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/depcache.cc#L383-L398, "
                 "with the default of "
                 "https://salsa.debian.org/apt-team/apt/-/blob/6cc5779d18baf520278952aed504b9d9b168a4bd/apt-pkg/depcache.h#L512). "
                 "On ubuntu2604_arm64_packages the Yes rows of the system database are the 1,351 packages apt-mark "
                 "showauto listed on the VM right after the capture, and the No rows the 201 apt-mark showmanual "
                 "listed; on honeynet_fc7_debian5 31 rows are Yes and 214 No. Package, Version, Architecture, "
                 "Section, Priority and Maintainer are those fields as stored. Source Package is the Source field "
                 "as stored, which names the source package when its name differs from the package's and adds the "
                 "source version in parentheses when that differs (Reference: dpkg, 'deb-control.pod', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/deb-control.pod#L218-L225); "
                 "it is blank when the stanza has none. Installed Size (KiB) is Installed-Size, the approximate "
                 "total size of the package's installed files in KiB (Reference: dpkg, 'deb-control.pod', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/deb-control.pod#L120-L122), "
                 "and Description the first line of the Description field, its short summary (Reference: dpkg, "
                 "'deb-control.pod', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/deb-control.pod#L92-L101). "
                 "Only the status file, info/format, the file lists' times and extended_states are read: dpkg's "
                 "status-old, the backup copies of the status file in /var/backups (Reference: dpkg, 'dpkg.pod', "
                 "https://github.com/guillemj/dpkg/blob/ef4d59f5925661818484ac666014ee3e665aadcf/man/dpkg.pod#L1556-L1558), "
                 "the lists' contents and the other info files are not, and neither are RPM databases. On "
                 "ubuntu2604_arm64_packages there are 1,567 rows: 1,561 from the VM's own database (1,552 install "
                 "ok installed and 9 deinstall ok config-files, each with its file list) and 6 from the known "
                 "database the VM's dpkg wrote in the user's home through --root, whose Package, Version, "
                 "Architecture and Status match what dpkg-query listed for it on the VM. The VM's dpkg is Ubuntu's "
                 "1.23.7ubuntu1, whose program reports 1.23.7; the dpkg sources cited are upstream's 1.23.7 tag, "
                 "and the known steps measured Ubuntu's build. honeynet_fc7_debian5 gives 248 rows: 245 install ok "
                 "installed, 2 deinstall ok config-files and 1 purge ok not-installed. No member of the other "
                 "fifteen tested images matches the declared paths.",
        "paths": ("*/var/lib/dpkg/status", "*/var/lib/dpkg/info/*.list", "*/var/lib/dpkg/info/format", "*/var/lib/apt/extended_states"),
        "output_types": "standard",
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 248 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 1,567 rows",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_time, seeker_of

STATUS = 'var/lib/dpkg/status'
WHITESPACE = ' \t\v\f\r'  # what dpkg's c_isspace() accepts, newline aside


def stanzas(data):
    """(stanzas, counts): each stanza of a deb822 file as a dict of lower-case field name to value, continuation
    lines joined with a newline, and a count of the lines that are neither a field nor a continuation. As in dpkg's
    parser, only an empty line ends a stanza; a line that begins with white space continues the field before
    it."""
    found, counts = [], Counter()
    fields, name = {}, None
    for line in data.decode('utf-8', errors='replace').split('\n'):
        if not line:
            if fields:
                found.append(fields)
            fields, name = {}, None
            continue
        if line[0] in WHITESPACE:
            if name is None:
                counts['continuation lines with no field before them, not read'] += 1
                continue
            fields[name] += '\n' + line[1:]
            continue
        key, colon, value = line.partition(':')
        key = key.strip()
        if not colon or not key or any(c.isspace() for c in key):
            counts['lines that are not a field, not read'] += 1
            name = None
            continue
        name = key.lower()
        fields[name] = value.strip()
    if fields:
        found.append(fields)
    return found, counts


def auto_marks(data):
    """{(package, architecture or None)} for the stanzas of apt's extended_states that carry an Auto-Installed value
    above 0; None stands for a stanza with no Architecture, which apt applies to every architecture."""
    marks = set()
    for fields in stanzas(data)[0]:
        value = fields.get('auto-installed', '0')
        if fields.get('package') and value.isdigit() and int(value) > 0:
            marks.add((fields['package'], fields.get('architecture') or None))
    return marks


def is_auto(marks, package, arch):
    """Whether apt marks a package automatically installed. apt files a package whose Architecture is all under the
    native architecture, which the status file does not name, so for all any mark on the name counts."""
    if arch == 'all':
        return any(name == package for name, _arch in marks)
    return (package, arch) in marks or (package, None) in marks


def list_names(fields, multiarch_db):
    """The info file names dpkg would give a package's file list, in the order to look for them: qualified with the
    architecture for a Multi-Arch: same package in a multiarch database."""
    name = fields.get('package', '')
    plain = f'{name}.list'
    qualified = f"{name}:{fields.get('architecture', '')}.list"
    if fields.get('multi-arch') != 'same':
        return [plain]
    if multiarch_db is None:
        return [plain, qualified]
    return [qualified] if multiarch_db else [plain]


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _source(context, seeker, path):
    """Where a staged file sits in the evidence, with / separators and no leading /: the path the seeker recorded,
    which keeps a character such as : that it replaced in the staged name, or the staged path when it recorded
    none."""
    info = getattr(seeker, 'file_infos', {}).get(path)
    source = getattr(info, 'source_path', None) or context.get_relative_path(path)
    return str(source).replace('\\', '/').lstrip('/')


@artifact_processor
def dpkgPackageStatus(context):
    data_headers = (('File List Written (UTC)', 'datetime'), 'Package', 'Version', 'Architecture', 'Status',
                    'Automatically Installed (apt)', 'Section', 'Priority', 'Installed Size (KiB)', 'Source Package',
                    'Maintainer', 'Description', 'Source File')
    seeker = seeker_of(context)
    staged = {}
    for path in (str(p) for p in context.get_files_found()):
        if not os.path.isdir(path):
            staged.setdefault(_source(context, seeker, path), path)
    counts = Counter()
    data_list = []
    read = []
    for source in sorted(s for s in staged if s == STATUS or s.endswith('/' + STATUS)):
        path = staged[source]
        root = source[:-len(STATUS)]
        try:
            records, problems = stanzas(_read(path))
        except OSError:
            counts['status files that could not be read'] += 1
            continue
        counts.update(problems)
        info = root + 'var/lib/dpkg/info/'
        multiarch_db = None
        if info + 'format' in staged:
            try:
                text = _read(staged[info + 'format']).decode('ascii', errors='replace').split()
                multiarch_db = bool(text) and text[0].isdigit() and int(text[0]) >= 1
            except OSError:
                counts['info/format files that could not be read'] += 1
        states = staged.get(root + 'var/lib/apt/extended_states')
        marks = None
        if states:
            try:
                marks = auto_marks(_read(states))
            except OSError:
                counts['extended_states files that could not be read'] += 1
        relative = context.get_relative_path(path)
        rows = 0
        for fields in records:
            if not fields.get('package'):
                counts['stanzas with no Package field, not reported'] += 1
                continue
            written = ''
            for name in list_names(fields, multiarch_db):
                if info + name in staged:
                    written = recorded_time(seeker, staged[info + name], None)
                    break
            else:
                counts['packages with no file list found'] += 1
            auto = ''
            state = fields.get('status', '').split(' ')[-1]
            if marks is not None and state not in ('config-files', 'not-installed'):
                auto = 'Yes' if is_auto(marks, fields['package'], fields.get('architecture', '')) else 'No'
            description = fields.get('description', '').split('\n', 1)[0]
            size = fields.get('installed-size', '')
            data_list.append((written, fields['package'], fields.get('version', ''), fields.get('architecture', ''),
                              fields.get('status', ''), auto, fields.get('section', ''), fields.get('priority', ''),
                              int(size) if size.isdigit() else size, fields.get('source', ''),
                              fields.get('maintainer', ''), description, relative))
            rows += 1
        if rows:
            read.append(path)
            if states and marks is not None:
                read.append(states)
    if counts:
        logfunc('Package Status (dpkg): ' + ', '.join(f'{count} {what}' for what, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
