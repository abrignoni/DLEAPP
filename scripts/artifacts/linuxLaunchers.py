"""User application launchers (.desktop files) and mimeapps.list default applications, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxUserLaunchers": {
        "name": "User Application Launchers",
        "description": "Desktop entry files in users' ~/.local/share/applications folders and in a Desktop folder, with "
                       "each file's desktop file ID and the keys that name the program it runs and the file types it "
                       "handles, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "One row per .desktop file in a user's .local/share/applications folder, its subfolders included, "
                 "and in a Desktop folder, file by file in path order; Source File is the file, and the files read "
                 "are named in the report's located-at line. $XDG_DATA_HOME defaults to ~/.local/share and is "
                 "searched before the system data folders "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/basedir/basedir-spec.xml#L136-139"
                 " and "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/basedir/basedir-spec.xml#L203-212)."
                 " A launcher's desktop file ID is its path below the applications folder with / turned into -, and "
                 "when two files share an ID only the first in that order is used; a file outside an applications "
                 "folder has none "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/desktop-entry/desktop-entry-spec.xml#L147-185),"
                 " so Desktop File ID is blank for a Location of Desktop. A user launcher can carry the ID of a "
                 "system one: GLib 2.88.0 on the lab VM resolved org.gnome.TextEditor.desktop to a file of that name"
                 " in a test $XDG_DATA_HOME ahead of the system one, and to the system file without it. The artifact"
                 " does not read the system folders and cannot say whether an ID repeats one there. Name, Type, "
                 "Exec, Try Exec, MIME Types, No Display and Hidden are the first value of each key in the [Desktop "
                 "Entry] group as stored; NoDisplay keeps a launcher out of the menus while it can still open files,"
                 " and Hidden marks it as deleted at the user's level "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/desktop-entry/desktop-entry-spec.xml#L528-540"
                 " and "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/desktop-entry/desktop-entry-spec.xml#L566-580)."
                 " Other Keys lists every other key line of that group as stored, a repeated key included, and "
                 "translated keys (a name holding [) are left out. Link Target is the target a symbolic link "
                 "records; the extraction holds the link and not the file, so that row's keys are blank. A Desktop "
                 "folder under another name is not read. On ubuntu2604_arm64_launchers, known data made on the lab "
                 "VM, whose clock was 5,157.7 to 5,158.1 s ahead of real time, the test home gives 4 rows: "
                 "dlknown-editor.desktop, installed with desktop-file-install, whose Other Keys include the "
                 "X-Desktop-File-Install-Version=0.28 line that tool added; dlknown-viewer.desktop, installed with "
                 "xdg-desktop-menu, with No Display true and no such line; a web app launcher written by hand in the"
                 " shape Chrome gives its launchers, whose Exec holds the --app-id; and a copy of the editor "
                 "launcher on the Desktop. Type holds one value, Application, on all 4 rows, and Try Exec, Hidden "
                 "and Link Target are blank on all 4.",
        "paths": ('*/.local/share/applications/*.desktop', '*/Desktop/*.desktop'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "app-window",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
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
            "ubuntu2604_arm64_launchers": "Ubuntu 26.04 LTS aarch64 | 4 rows",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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
    "linuxDefaultApplications": {
        "name": "Default Applications",
        "description": "Lines of mimeapps.list files that set the default, added and removed applications for "
                       "file and link types, with the file type and the applications as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "One row per line of the [Default Applications], [Added Associations] and [Removed Associations] "
                 "groups of each mimeapps.list and <desktop>-mimeapps.list file under .config, "
                 ".local/share/applications, etc/xdg, usr/share/applications, usr/local/share/applications and "
                 "usr/share/<folder>/applications, file by file in path order; lines of other groups are counted in "
                 "the run log and not reported. The Desktop Menu mime-apps specification lists these files in order "
                 "of precedence: the user's $XDG_CONFIG_HOME ones first, then the administrator's $XDG_CONFIG_DIRS "
                 "ones, then the deprecated $XDG_DATA_HOME/applications ones, then the distribution's "
                 "$XDG_DATA_DIRS/applications ones, a <desktop>- file coming before the plain one of its folder "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/mime-apps/mime-apps-spec.xml#L41-69)."
                 " [Added Associations] and [Removed Associations] add or remove applications for a type as if their"
                 " desktop files said so "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/mime-apps/mime-apps-spec.xml#L75-88),"
                 " and [Default Applications] names the application a file manager opens a type with, the next one "
                 "in the list tried if the first is not installed "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/mime-apps/mime-apps-spec.xml#L103-118)."
                 " MIME Type and Applications are the key and value as stored; Desktop is the <desktop> part of a "
                 "desktop-specific file's name, blank otherwise; Scope is User for a file under .config or "
                 ".local/share and System otherwise. The artifact does not work out which application is the "
                 "default. On ubuntu2604_arm64_launchers, known data made on the lab VM, whose clock was 5,157.7 to "
                 "5,158.1 s ahead of real time, the test user's mimeapps.list gives 3 rows: xdg-mime default wrote "
                 "the text/plain default with no trailing semicolon, and gio mime wrote the x-scheme-handler/dlknown"
                 " default and an added association ending in a semicolon; gio mime and xdg-mime query default, run "
                 "with the same folders, reported those two defaults. The VM's own gnome-mimeapps.list gives 499 "
                 "rows and ubuntu-mimeapps.list 73, all in [Default Applications]. Link Target is blank on all 575 "
                 "rows of that image, which holds no symbolic link there.",
        "paths": ('*/.config/mimeapps.list', '*/.config/*-mimeapps.list',
                  '*/.local/share/applications/mimeapps.list', '*/.local/share/applications/*-mimeapps.list',
                  '*/etc/xdg/*mimeapps.list', '*/usr/share/applications/*mimeapps.list',
                  '*/usr/local/share/applications/*mimeapps.list', '*/usr/share/*/applications/*mimeapps.list'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
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
            "ubuntu2604_arm64_launchers": "Ubuntu 26.04 LTS aarch64 | 575 rows",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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
import posixpath
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_link, recorded_time, seeker_of

SHOWN = ('Name', 'Type', 'Exec', 'TryExec', 'MimeType', 'NoDisplay', 'Hidden')
GROUPS = ('Default Applications', 'Added Associations', 'Removed Associations')


def key_file(data, wanted_group):
    """[(group, key, value, line number)] for the key lines of a desktop entry style file, groups given in
    wanted_group (a tuple) only; blank lines and # comments are skipped. Also returns the number of key lines in
    other groups."""
    rows, group, other = [], None, 0
    for number, raw in enumerate(data.decode('utf-8', errors='backslashreplace').split('\n'), 1):
        line = raw.strip(' \t\r')
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            group = line[1:-1]
            continue
        if '=' not in line:
            continue
        if group not in wanted_group:
            other += 1
            continue
        key, value = (part.strip(' \t') for part in line.split('=', 1))
        rows.append((group, key, value, number))
    return rows, other


def desktop_file_id(source):
    """The desktop file ID of a file under an applications folder (its path below that folder with / turned into
    -), or '' for a file outside one."""
    parts = source.strip('/').split('/')
    if 'applications' not in parts:
        return ''
    below = parts[len(parts) - 1 - parts[::-1].index('applications') + 1:]
    return '-'.join(below)


def launcher_fields(data):
    """(first value of each shown key in [Desktop Entry] as stored, the other key lines as stored); translated keys
    (a name holding [) are left out."""
    rows, _other = key_file(data, ('Desktop Entry',))
    shown, other = {}, []
    for _group, key, value, _number in rows:
        if '[' in key:
            continue
        if key in SHOWN and key not in shown:
            shown[key] = value
        else:
            other.append(f'{key}={value}')
    return shown, other


def _source(context, seeker, path):
    info = getattr(seeker, 'file_infos', {}).get(path)
    return info.source_path if info is not None else context.get_relative_path(path).replace(os.sep, '/')


def _files(context, seeker, counts):
    for path in sorted(str(p) for p in context.get_files_found()):
        link = recorded_link(seeker, path)
        if link is None and not os.path.isfile(path):
            continue
        if link is None:
            try:
                with open(path, 'rb') as handle:
                    data = handle.read()
            except OSError:
                counts['files that could not be read'] += 1
                continue
        else:
            data = None
        yield path, _source(context, seeker, path), link, data


@artifact_processor
def linuxUserLaunchers(context):
    data_headers = (('File Modified', 'datetime'), 'Location', 'Desktop File ID', 'Name', 'Type', 'Exec', 'Try Exec',
                    'MIME Types', 'No Display', 'Hidden', 'Other Keys', 'Link Target', 'Source File')
    seeker = seeker_of(context)
    data_list, read, counts = [], [], Counter()
    for path, source, link, data in _files(context, seeker, counts):
        location = 'Applications' if '/.local/share/applications/' in '/' + source.strip('/') else 'Desktop'
        shown, other = launcher_fields(data) if data is not None else ({}, [])
        if data is not None and not shown and not other:
            counts['files with no [Desktop Entry] key, reported with blank keys'] += 1
        data_list.append((recorded_time(seeker, path, link), location,
                          desktop_file_id(source) if location == 'Applications' else '',
                          *(shown.get(k, '') for k in SHOWN), '\n'.join(other), link or '', source))
        read.append(path)
    if counts:
        logfunc('User Application Launchers: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


def _desktop_prefix(name):
    return name[:-len('-mimeapps.list')] if name.endswith('-mimeapps.list') else ''


@artifact_processor
def linuxDefaultApplications(context):
    data_headers = (('File Modified', 'datetime'), 'Scope', 'Desktop', 'Group', 'MIME Type', 'Applications',
                    'Link Target', 'Line', 'Source File')
    seeker = seeker_of(context)
    data_list, read, counts = [], [], Counter()
    for path, source, link, data in _files(context, seeker, counts):
        name = posixpath.basename(source)
        scope = 'User' if ('/.config/' in '/' + source or '/.local/share/' in '/' + source) else 'System'
        when = recorded_time(seeker, path, link)
        if link is not None:
            data_list.append((when, scope, _desktop_prefix(name), '', '', '', link, '', source))
            read.append(path)
            continue
        rows, other = key_file(data, GROUPS)
        if other:
            counts['lines in other groups, not reported'] += other
        for group, key, value, number in rows:
            data_list.append((when, scope, _desktop_prefix(name), group, key, value, '', number, source))
        read.append(path)
    if counts:
        logfunc('Default Applications: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
