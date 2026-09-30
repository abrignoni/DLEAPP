"""XDG autostart entries in a user's ~/.config/autostart and in the system autostart folders, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxXdgAutostart": {
        "name": "XDG Autostart Entries",
        "description": "Files in a user's ~/.config/autostart folder and in system autostart folders that systemd and "
                       "GNOME Session read, with the keys that decide whether each entry is started.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Persistence (Linux)",
        "notes": "Reads every file in a user's .config/autostart folder, in /etc/xdg/autostart and "
                 "/etc/xdg/<folder>/autostart, and in the gnome/autostart folder under /usr/share, /usr/local/share,"
                 " /usr/share/<folder> and /var/lib/snapd/desktop, one row per file in path order; Source File is "
                 "the file, and the files read are named in the report's located-at line. Files in folders below "
                 "those are counted in the run log and not reported. The Desktop Application Autostart Specification"
                 " puts autostart entries in $XDG_CONFIG_HOME/autostart, ~/.config/autostart by default, and in each"
                 " $XDG_CONFIG_DIRS folder's autostart folder, /etc/xdg/autostart by default "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/autostart/autostart-spec.xml#L91-121),"
                 " and when files of the same name sit in several of them only the one in the most important folder,"
                 " the user's first, is used "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/autostart/autostart-spec.xml#L99-100);"
                 " Hidden=true in that file stops every file of that name "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/autostart/autostart-spec.xml#L135-143"
                 " and "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/autostart/autostart-spec.xml#L181-185)."
                 " Two of the programs that read these folders follow different rules. "
                 "systemd-xdg-autostart-generator (systemd 259.5) turns entries into user units attached to "
                 "xdg-desktop-autostart.target "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L691-L693),"
                 " so a session that starts that target starts them. GNOME Session (gnome-session 50.1; the Ubuntu "
                 "50.1-0ubuntu0.1 patches do not change the functions cited here) reads the user folder, then the "
                 "gnome/autostart folder of each $XDG_DATA_DIRS folder, then the autostart folder of each "
                 "$XDG_CONFIG_DIRS folder "
                 "(https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-session-fill.c#L30-54),"
                 " and starts the entries itself; Scope is System (GNOME) for a gnome/autostart folder, which "
                 "systemd does not read. On the tested Ubuntu 26.04 GNOME session xdg-desktop-autostart.target was "
                 "inactive, the three generated units checked had never started, and the running autostart programs "
                 "checked (prlcc, gsd-disk-utility-notify and evolution-alarm-notify) were in app-gnome scope units."
                 " The generator reads the user folder first and then each $XDG_CONFIG_DIRS folder, /etc/xdg when "
                 "that is unset "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-generator.c#L29-L33"
                 " and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-generator.c#L52-L71),"
                 " reads every regular file whatever its extension and follows symbolic links "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-generator.c#L86-L94),"
                 " keeps the first file of each name with any .desktop ending removed "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L55"
                 " and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-generator.c#L96-L103),"
                 " and walks the folders with a loop that skips hidden and backup file names "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/dirent-util.h#L25-L29;"
                 " "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/path-util.c#L1277-L1324)."
                 " Name Skipped by systemd is yes for such a name: one beginning with a dot or ending in ~, "
                 "lost+found, aquota.user, aquota.group, or one ending in .ignore, .rpmnew, .rpmsave, .rpmorig, "
                 ".dpkg-old, .dpkg-new, .dpkg-tmp, .dpkg-dist, .dpkg-bak, .dpkg-backup, .dpkg-remove, .ucf-new, "
                 ".ucf-old, .ucf-dist, .swp, .bak, .old or .new. The generator makes no unit for an entry whose "
                 "Hidden or X-systemd-skip is true, whose Type is not Application, that has no Exec, or whose "
                 "TryExec or Exec program it cannot find "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L526-L577);"
                 " an entry with any X-GNOME-Autostart-Phase gets NotShowIn=GNOME, and no unit at all if its "
                 "OnlyShowIn named only GNOME "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L581-L603);"
                 " OnlyShowIn and NotShowIn become a check against XDG_CURRENT_DESKTOP when the unit starts "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L654-L671)."
                 " X-GNOME-Autostart-enabled is not a key the generator reads: its key table has no entry for it "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L318-L347)."
                 " GNOME Session reads only names ending in .desktop "
                 "(https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-manager.c#L2433),"
                 " so Name Skipped by GNOME Session is yes for any other name; it keeps the first entry of each id "
                 "across its folders "
                 "(https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-manager.c#L2368-2387),"
                 " and GLib 2.88.0 on the lab VM gave every file it loaded its file name as that id; it refuses one "
                 "whose X-GNOME-Autostart-Phase is anything but Application "
                 "(https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-app.c#L203-219),"
                 " and does not start one whose X-GNOME-Autostart-enabled is false, whose Hidden is true, whose "
                 "OnlyShowIn or NotShowIn leaves out the current desktop, or whose X-GNOME-HiddenUnderSystemd or "
                 "X-systemd-skip is true "
                 "(https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-app.c#L151-190"
                 " and "
                 "https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-manager.c#L302-316)."
                 " It loads each file through GLib "
                 "(https://gitlab.gnome.org/GNOME/gnome-session/-/blob/cd403186acf6f0ca866d014fd76f6456b4f46884/gnome-session/gsm-app.c#L222-238),"
                 " and GLib 2.88.0 on the lab VM did not load a file with a line holding no =, a Type other than "
                 "Application, a TryExec program that does not exist, or no [Desktop Entry] group, and did load one "
                 "with no Exec. Name, Exec, Type, Hidden, GNOME Autostart Enabled (X-GNOME-Autostart-enabled), Only "
                 "Show In, Not Show In, Try Exec, systemd Skip (X-systemd-skip), GNOME Hidden Under systemd "
                 "(X-GNOME-HiddenUnderSystemd) and GNOME Autostart Phase (X-GNOME-Autostart-Phase) are the first "
                 "value of each key in the file's [Desktop Entry] group as stored, escape sequences not decoded. The"
                 " generator keeps the first value of a text or list key "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L166-L170"
                 " and "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L236-L240)"
                 " and the last value of Hidden and X-systemd-skip "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L85-L89);"
                 " GLib 2.88.0 on the lab VM used the last value of a repeated Exec and of a repeated Hidden. Other "
                 "Keys lists every other key line of that group as stored, a repeated key included; keys holding [, "
                 "which are translations and which the generator ignores "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/xdg-autostart-generator/xdg-autostart-service.c#L295-L301),"
                 " and lines of other groups are left out. Same-Name Entry names every file of another scope with "
                 "the same name, .desktop ending removed; which of them a reader uses follows its folder order and "
                 "its name rules. Link Target is the target a symbolic link records; the extraction holds the link "
                 "and not the file it points to, so that row's keys are blank. File Modified is the modified time "
                 "the extraction recorded for the file or link. The artifact does not decide whether an entry runs: "
                 "TryExec, Exec and the desktop name are checked on the system at login. It does not read an "
                 "autostart folder under an XDG_CONFIG_HOME other than ~/.config, or an XDG_CONFIG_DIRS or "
                 "XDG_DATA_DIRS folder outside those named above. ubuntu2604_arm64_autostart holds known data made "
                 "on the lab VM, whose clock was 5,157.9 s ahead of real time, as the README beside that capture "
                 "lists: 25 rows, 16 System, 6 User and 3 System (GNOME). Its GNOME session has "
                 "XDG_CONFIG_DIRS=/etc/xdg/xdg-ubuntu:/etc/xdg, with no autostart folder in /etc/xdg/xdg-ubuntu, and"
                 " "
                 "XDG_DATA_DIRS=/usr/share/ubuntu:/usr/share/gnome:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop,"
                 " of whose gnome/autostart folders only /usr/share/gnome/autostart exists. The generator, run on "
                 "the VM after the last known step, made 12 units, one for each User and System row except the 6 "
                 "System rows with systemd Skip true, the System and User org.gnome.Evolution-alarm-notify.desktop "
                 "rows (the User copy adds Hidden=true) and the 2 rows with Name Skipped by systemd yes. GLib's own "
                 "calls on the VM, made the way GNOME Session reads the folders, left 8 rows to start, 7 disabled, 5"
                 " refused for their phase, 3 not read because an earlier folder held the same file name and 2 not "
                 "read for their name. The two readers disagree on 3 known-data files: .dlknown-hidden.desktop is "
                 "left to start by GNOME Session and skipped by systemd, dlknown-noext has a unit and is not read by"
                 " GNOME Session, and dlknown-autostart-off.desktop, whose GNOME Autostart Enabled is false, has a "
                 "unit and is not started by GNOME Session. Whether each is started at a login was not tested. For "
                 "the login before the known steps, the user journal names an app-gnome scope for 4 of the 6 System "
                 "and System (GNOME) entries left to start, for the System Evolution entry, whose User copy was "
                 "added after that login, and for none of the System and System (GNOME) entries refused or disabled;"
                 " ptiagent and im-launch left no scope name, and why is not established. No member of the other 32 "
                 "tested images matches the declared paths.",
        "paths": ('*/.config/autostart/*', '*/etc/xdg/autostart/*', '*/etc/xdg/*/autostart/*',
                  '*/usr/share/gnome/autostart/*', '*/usr/local/share/gnome/autostart/*',
                  '*/usr/share/*/gnome/autostart/*', '*/var/lib/snapd/desktop/gnome/autostart/*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
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
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS aarch64 | 25 rows",
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
from scripts.linux_links import in_folder, recorded_link, recorded_time, seeker_of

SHOWN = ('Name', 'Exec', 'Type', 'Hidden', 'X-GNOME-Autostart-enabled', 'OnlyShowIn', 'NotShowIn', 'TryExec',
         'X-systemd-skip', 'X-GNOME-HiddenUnderSystemd', 'X-GNOME-Autostart-Phase')
# systemd's hidden_or_backup_file(): names its directory walk skips.
_SKIPPED_NAMES = ('lost+found', 'aquota.user', 'aquota.group')
_SKIPPED_SUFFIXES = ('ignore', 'rpmnew', 'rpmsave', 'rpmorig', 'dpkg-old', 'dpkg-new', 'dpkg-tmp', 'dpkg-dist',
                     'dpkg-bak', 'dpkg-backup', 'dpkg-remove', 'ucf-new', 'ucf-old', 'ucf-dist', 'swp', 'bak', 'old',
                     'new')


def skipped_name(name):
    """Whether systemd's directory walk skips a file of this name (hidden or backup)."""
    if name.startswith('.') or name in _SKIPPED_NAMES or name.endswith('~'):
        return True
    dot = name.rfind('.')
    return dot != -1 and name[dot + 1:] in _SKIPPED_SUFFIXES


def service_name(name):
    """The name the generator keeps an entry under: the file name without a .desktop ending."""
    return name[:-len('.desktop')] if name.endswith('.desktop') else name


def gnome_skipped_name(name):
    """Whether GNOME Session's folder walk skips a file of this name (one not ending in .desktop)."""
    return not name.endswith('.desktop')


def scope_of(source):
    """'User', 'System' or 'System (GNOME)' for an autostart file, from its path; None for a file in a folder
    below one."""
    folder, _name = posixpath.split('/' + source.strip('/'))
    if folder.endswith('/.config/autostart'):
        return 'User'
    if folder.endswith('/gnome/autostart'):
        return 'System (GNOME)'
    if folder.endswith('/etc/xdg/autostart') or (folder.endswith('/autostart')
                                                 and posixpath.dirname(posixpath.dirname(folder)).endswith('/etc/xdg')):
        return 'System'
    return None


def desktop_entry(data):
    """(first value of each key in the [Desktop Entry] group, the other key=value lines as stored) for a file's
    bytes. Translated keys (a name holding [) are left out; lines outside that group are not read."""
    shown, other = {}, []
    group = None
    for raw in data.decode('utf-8', 'backslashreplace').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            group = line[1:-1]
            continue
        if group != 'Desktop Entry' or '=' not in line:
            continue
        key, value = (part.strip() for part in line.split('=', 1))
        if '[' in key:
            continue
        if key in SHOWN and key not in shown:
            shown[key] = value
        else:
            other.append(f'{key}={value}')
    return shown, other


def source_of(seeker, path, relative):
    """Where a file the seeker returned sits in the evidence, / separated."""
    if getattr(seeker, 'directory', None):
        return os.path.relpath(in_folder(seeker, path), seeker.directory).replace(os.sep, '/')
    info = getattr(seeker, 'file_infos', {}).get(path)
    return info.source_path if info is not None else relative.replace(os.sep, '/')


@artifact_processor
def linuxXdgAutostart(context):
    data_headers = (('File Modified', 'datetime'), 'Scope', 'File Name', 'Name', 'Exec', 'Type', 'Hidden',
                    'GNOME Autostart Enabled', 'Only Show In', 'Not Show In', 'Try Exec', 'systemd Skip',
                    'GNOME Hidden Under systemd', 'GNOME Autostart Phase', 'Other Keys', 'Same-Name Entry',
                    'Name Skipped by systemd', 'Name Skipped by GNOME Session', 'Link Target', 'Source File')
    seeker = seeker_of(context)
    counts = Counter()
    found = []
    for path in sorted(map(str, context.get_files_found())):
        link = recorded_link(seeker, path)
        if link is None and not os.path.isfile(path):
            continue
        source = source_of(seeker, path, context.get_relative_path(path))
        scope = scope_of(source)
        if scope is None:
            counts['files in folders below an autostart folder, which are not read'] += 1
            continue
        found.append((source, path, scope, link))
    names = {}
    for source, _path, scope, _link in found:
        names.setdefault(service_name(posixpath.basename(source)), []).append((scope, source))
    data_list, read = [], []
    for source, path, scope, link in found:
        name = posixpath.basename(source)
        shown, other = {}, []
        if link is None:
            try:
                with open(path, 'rb') as handle:
                    shown, other = desktop_entry(handle.read())
            except OSError:
                counts['files that could not be read'] += 1
                continue
        same = [s for sc, s in names[service_name(name)] if sc != scope]
        data_list.append((recorded_time(seeker, path, link), scope, name, *(shown.get(k, '') for k in SHOWN),
                          '\n'.join(other), '\n'.join(same), 'yes' if skipped_name(name) else '',
                          'yes' if gnome_skipped_name(name) else '', link or '', source))
        read.append(path)
    if counts:
        logfunc('XDG Autostart Entries: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
