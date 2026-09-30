"""OpenSSH client (ssh_config, ~/.ssh/config) and server (sshd_config) configuration files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sshClientConfig": {
        "name": "SSH Client Config",
        "description": "Directives in users' ~/.ssh/config files and in /etc/ssh/ssh_config and ssh_config.d, one row "
                       "per directive, and per symbolic link, with the Host or Match section it sits in, its keyword and "
                       "its value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "SSH",
        "notes": "One row per directive in each user's .ssh/config and in etc/ssh/ssh_config and the files of "
                 "etc/ssh/ssh_config.d, file by file in path order and within a file in line order; Line is the line"
                 " number and Source File the file, and the files read are named in the report's located-at line. "
                 "ssh takes options from the command line, then the user's ~/.ssh/config, then /etc/ssh/ssh_config, "
                 "and for each parameter uses the first value it obtains "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L44-L60)."
                 " A Host line restricts the lines that follow, up to the next Host or Match line, to host names "
                 "matching its patterns, and a Match line to the conditions it names "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L60-L67,"
                 " "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L97-L103"
                 " and "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L128-L134)."
                 " Section is the Host or Match line a directive follows, as stored, and is blank before the first. "
                 "Keyword and Value are split as OpenSSH splits a line: the keyword ends at whitespace, a double "
                 "quote or a single =, and a line whose first token begins with # is a comment "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/misc.c#L442-L481"
                 " and "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/readconf.c#L1172-L1199)."
                 " Keywords are compared without case "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L74-L95),"
                 " and both are reported as stored, quotes included. A directive with no argument, which ssh "
                 "rejects, is reported with Value blank and counted in the run log. An Include line is reported as a"
                 " directive "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/ssh_config.5#L1219-L1237);"
                 " the files it names are read here only where the declared paths reach them. A symbolic link is "
                 "reported with its Link Target and not read. Scope is System for a file under etc/ssh and User "
                 "otherwise. The artifact does not work out which value ssh uses for a host. On "
                 "ubuntu2604_arm64_sshconfig, known data made on the lab VM, whose clock was 5,157.8 to 5,158.1 s "
                 "ahead of real time, the User and Port ssh -G printed for dlknown-jump, dlknown-inner, dlknown-eq "
                 "and dlknown-other, and the HostName it printed for dlknown-jump and dlknown-inner, each equal the "
                 "first row for that keyword whose Section is blank or a Host line matching the name. That image "
                 "gives 24 rows: 18 from the test ~/.ssh/config, 5 from the VM's ssh_config, whose first directive "
                 "is an Include of ssh_config.d/*.conf, and 1 for the symbolic link in ssh_config.d, whose target "
                 "the capture does not hold. honeynet_fc7_debian5 gives 5 rows from etc/ssh/ssh_config, and "
                 "pc_mus_001_win11 6 from the ssh_config Git for Windows keeps under Program Files/Git/etc/ssh. Link"
                 " Target is blank on every row except that of the ssh_config.d link on ubuntu2604_arm64_sshconfig. "
                 "On honeynet_fc7_debian5 Section holds one value, Host *, on all 5 rows, on pc_mus_001_win11 all 6 "
                 "have Scope System, and each of those two images holds one file, so File Modified holds one value "
                 "on each.",
        "paths": ('*/.ssh/config', '*/etc/ssh/ssh_config', '*/etc/ssh/ssh_config.d/*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 5 rows",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 6 rows",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS aarch64 | 24 rows",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "sshServerConfig": {
        "name": "SSH Server Config",
        "description": "Directives in /etc/ssh/sshd_config and sshd_config.d, one row per directive, and per symbolic "
                       "link, with the Match section it sits in, its keyword and its value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "SSH",
        "notes": "One row per directive in etc/ssh/sshd_config and the files of etc/ssh/sshd_config.d, file by file "
                 "in path order and within a file in line order; Line is the line number and Source File the file, "
                 "and the files read are named in the report's located-at line. sshd reads /etc/ssh/sshd_config "
                 "unless started with -f, and for each keyword uses the first value it obtains "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd_config.5#L44-L61)."
                 " A Match line makes the keywords that follow, up to the next Match line or the end of the file, "
                 "override the global ones when its criteria are satisfied "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd_config.5#L1221-L1232)."
                 " Section is that Match line as stored, blank for the global section. Keyword and Value are split "
                 "as sshd splits a line "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/misc.c#L442-L481"
                 " and "
                 "https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/servconf.c#L1334-L1355),"
                 " keywords are compared without case "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd_config.5#L44-L61),"
                 " and both are reported as stored; a directive with no argument, which sshd rejects, is reported "
                 "with Value blank and counted in the run log. sshd reads a file in sshd_config.d only when an "
                 "Include line names it "
                 "(https://github.com/openssh/openssh-portable/blob/d01efaa1c9ed84fd9011201dbc3c7cb0a82bcee3/sshd_config.5#L912-L920);"
                 " the artifact reports every file there. On ubuntu2604_arm64_sshconfig, known data made on the lab "
                 "VM, the VM's own sshd_config gives 7 rows, the first an Include of sshd_config.d/*.conf; its "
                 "sshd_config.d file is readable only by root and is not in that capture. honeynet_fc7_debian5 gives"
                 " 27 rows from etc/ssh/sshd_config, and pc_mus_001_win11 2 from the sshd_config Git for Windows "
                 "keeps under Program Files/Git/etc/ssh. Each of the three images holds one file here and no "
                 "symbolic link, so File Modified holds one value and Link Target is blank on every row of each.",
        "paths": ('*/etc/ssh/sshd_config', '*/etc/ssh/sshd_config.d/*'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 27 rows",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS aarch64 | 7 rows",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_link, recorded_time, seeker_of

# OpenSSH's strdelim(): the keyword ends at whitespace, a double quote or '='.
_KEYWORD = re.compile(r'[^ \t"=]+')


def directive(line):
    """(keyword, value) for a configuration line as OpenSSH splits it, or None for a comment or empty line and
    for a line whose first token is not a keyword."""
    text = line.rstrip(' \t\r\n\f').lstrip(' \t')
    if not text or text.startswith('#'):
        return None
    match = _KEYWORD.match(text)
    if not match:
        return None
    keyword = match.group(0)
    rest = text[len(keyword):].lstrip(' \t')
    if rest.startswith('='):
        rest = rest[1:].lstrip(' \t')
    return keyword, rest


def config_rows(data, sections, counts):
    """(section, keyword, value, line number) for each directive of a configuration file; sections are the
    keywords, compared without case, that open a section."""
    rows, section = [], ''
    for number, line in enumerate(data.decode('utf-8', errors='replace').split('\n'), 1):
        found = directive(line)
        if found is None:
            if line.strip(' \t\r\f') and not line.strip(' \t\r\f').startswith('#'):
                counts['lines whose first token is not a keyword, not reported'] += 1
            continue
        keyword, value = found
        if not value:
            counts['directives with no argument, which OpenSSH rejects'] += 1
        if keyword.lower() in sections:
            section = f'{keyword} {value}'.rstrip()
        rows.append((section, keyword, value, number))
    return rows


def _source(context, seeker, path):
    info = getattr(seeker, 'file_infos', {}).get(path)
    return info.source_path if info is not None else context.get_relative_path(path).replace(os.sep, '/')


def _scope(source):
    return 'System' if '/etc/ssh/' in '/' + source.strip('/') else 'User'


def _config(context, label, sections, with_scope):
    seeker = seeker_of(context)
    data_list, read, counts = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found()):
        link = recorded_link(seeker, path)
        if link is None and not os.path.isfile(path):
            continue
        source = _source(context, seeker, path)
        scope = (_scope(source),) if with_scope else ()
        when = recorded_time(seeker, path, link)
        if link is not None:
            counts['symbolic links, reported with their target and not read'] += 1
            data_list.append((when,) + scope + ('', '', '', link, '', source))
            read.append(path)
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        for section, keyword, value, number in config_rows(data, sections, counts):
            data_list.append((when,) + scope + (section, keyword, value, '', number, source))
        read.append(path)
    if counts:
        logfunc(f'{label}: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_list, read


@artifact_processor
def sshClientConfig(context):
    data_headers = (('File Modified', 'datetime'), 'Scope', 'Section', 'Keyword', 'Value', 'Link Target', 'Line',
                    'Source File')
    data_list, read = _config(context, 'SSH Client Config', ('host', 'match'), True)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def sshServerConfig(context):
    data_headers = (('File Modified', 'datetime'), 'Section', 'Keyword', 'Value', 'Link Target', 'Line', 'Source File')
    data_list, read = _config(context, 'SSH Server Config', ('match',), False)
    return data_headers, data_list, '\n'.join(read)

