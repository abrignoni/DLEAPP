"""Items in a freedesktop.org Trash folder (the .trashinfo files), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxTrash": {
        "name": "Trash (freedesktop)",
        "description": "Items the .trashinfo files of a freedesktop.org Trash folder describe, with the original path "
                       "and the deletion date each file records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads each .trashinfo file in the info folder of a Trash folder laid out by the freedesktop.org "
                 "Trash specification: the home Trash, $XDG_DATA_HOME/Trash "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L138-142), "
                 "read at .local/share/Trash, where it is when $XDG_DATA_HOME is not set or is empty (Base "
                 "Directory specification, "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/basedir/basedir-spec.xml#L136-139), "
                 "so a home Trash under a $XDG_DATA_HOME that does not end in .local/share is not read, and a "
                 "volume's $topdir/.Trash/$uid and $topdir/.Trash-$uid "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L203-213). "
                 "It gives one row per file, in path order, and names the files it read in the report's located-at "
                 "line. The specification gives each item an info file named as the item is named in the Trash's "
                 "files folder plus .trashinfo "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L294-297), "
                 "whose first line is [Trash Info], with a Path key holding the original location, absolute or "
                 "relative, escaped as in URLs, and a DeletionDate key in the form YYYY-MM-DDThh:mm:ss in the "
                 "user's or the file system's local time "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L302-327), "
                 "the first Path and DeletionDate lines being the ones that count "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L337-340). "
                 "A matched .trashinfo file that is not directly in the info folder of a folder of one of those "
                 "three shapes, one whose first line is not [Trash Info] and one that cannot be read are counted "
                 "in the run log and not reported. Deletion Date (local) is DeletionDate as stored: it records no "
                 "zone, so it is not converted. GLib writes it from the local time as %Y-%m-%dT%H:%M:%S, or as "
                 "9999-12-31T23:59:59 when it cannot get the local time (gio/glocalfile.c at 2.88.0, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L2454-L2461), "
                 "and escapes the path with g_uri_escape_string allowing '/' "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L2449), "
                 "which, through g_string_append_uri_escaped (glib/guri.c, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/guri.c#L2709-L2723; "
                 "glib/gstring.c, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gstring.c#L600-L609), "
                 "writes every byte other than ASCII letters and digits, '-', '.', '_', '~' and '/' as % and two "
                 "upper-case hexadecimal digits "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/guri.c#L265-L271, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/guri.c#L399-L450). "
                 "Path as Stored is Path as stored, read as UTF-8, and Original Path is it with the escapes "
                 "decoded as UTF-8; in both, a byte sequence that is not UTF-8 is shown as the replacement "
                 "character. Relative To is blank for an absolute path; for a relative one it is the folder the "
                 "path starts from. The specification has a relative path start from the folder the Trash folder "
                 "is in, $XDG_DATA_HOME for the home Trash "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L307-313). "
                 "GLib writes an absolute path in the home Trash and, in a volume's Trash, one relative to the "
                 "volume's top folder "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L2444-L2448), "
                 "the folder holding .Trash for .Trash/$uid "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L2228-L2234) "
                 "and holding .Trash-$uid "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L2261-L2263), "
                 "or the absolute path when it cannot make one relative "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L1820-L1844). "
                 "Relative To is the .local/share folder for the home Trash and the folder holding .Trash-$uid, as "
                 "the specification gives, and for .Trash/$uid the folder holding .Trash, as GLib writes it, where "
                 "the specification's wording would give .Trash. Name in Trash is the info file's name without "
                 ".trashinfo, the item's name in the files folder, which the specification says must never be used "
                 "to recover the original name "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/trash/index.rst#L283-292): "
                 "GLib numbers a repeated name before its first dot "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L1782-L1796) "
                 "and drops characters from the start of a name too long for the file system "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/gio/glocalfile.c#L2375-L2409). "
                 "Trash Folder is the Trash folder the info file is in. The trashed item itself, in the files "
                 "folder, is not read. On ubuntu2604_arm64_trash, captured from a VM running GLib 2.88.0, the 7 "
                 "rows are the one from ubuntu2604_arm64_triage and 6 items moved to the Trash with gio trash for "
                 "that capture. For those 6, Original Path equals the path each had, Deletion Date (local) is the "
                 "UTC second logged just before gio ran on it, converted to America/New_York, the second of two "
                 "items named plain.txt is plain.2.txt in the Trash, and Path as Stored holds %20 for a space, %25 "
                 "for a percent sign and %C3%A9 for é. America/New_York is the zone /etc/localtime names in "
                 "ubuntu2604_arm64_triage, a capture of the same VM, whose /etc/timezone names "
                 "America/Los_Angeles: those 6 deletion dates followed /etc/localtime. Relative To was blank and "
                 "Trash Folder held the same value, the home Trash, on every row of both images.",
        "paths": ('*/.local/share/Trash/info/*.trashinfo', '*/.Trash/*/info/*.trashinfo',
                  '*/.Trash-*/info/*.trashinfo'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 7 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 1 row",
        },
    },
}

import os
from collections import Counter
from urllib.parse import unquote

from scripts.ilapfuncs import artifact_processor, logfunc

_HEADER = '[Trash Info]'
_SUFFIX = '.trashinfo'


def trash_info(data):
    """(path as stored, deletion date) from the text of a .trashinfo file, the first of each key, or None when the
    first line is not [Trash Info]."""
    lines = data.decode('utf-8', errors='replace').replace('\r\n', '\n').split('\n')
    if not lines or lines[0].strip() != _HEADER:
        return None
    found = {}
    for line in lines[1:]:
        key, sep, value = line.partition('=')
        if sep and key in ('Path', 'DeletionDate') and key not in found:
            found[key] = value
    return found.get('Path', ''), found.get('DeletionDate', '')


def relative_base(folder):
    """The folder a relative Path in this Trash folder starts from, or None when the folder is not shaped as a
    Trash folder: the .local/share folder for <folder>/.local/share/Trash, the folder holding .Trash-<uid>, and the
    folder holding .Trash for .Trash/<uid>."""
    name = os.path.basename(folder)
    parent = os.path.dirname(folder)
    if name == 'Trash' and os.path.basename(parent) == 'share' \
            and os.path.basename(os.path.dirname(parent)) == '.local':
        return parent
    if name.startswith('.Trash-'):
        return parent
    if os.path.basename(parent) == '.Trash':
        return os.path.dirname(parent)
    return None


def trash_parts(relative):
    """(Trash folder, name in the Trash) for the evidence-relative path of a .trashinfo file, or None when the file
    is not directly in the info folder of a Trash-shaped folder."""
    info_dir, info_name = os.path.split(relative)
    folder = os.path.dirname(info_dir)
    if os.path.basename(info_dir) != 'info' or relative_base(folder) is None:
        return None
    return folder, info_name[:-len(_SUFFIX)]


@artifact_processor
def linuxTrash(context):
    data_headers = ('Deletion Date (local)', 'Original Path', 'Relative To', 'Path as Stored', 'Name in Trash',
                    'Trash Folder')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        if not path.endswith(_SUFFIX):
            continue
        parts = trash_parts(context.get_relative_path(path))
        if parts is None:
            problems['.trashinfo files not in the info folder of a Trash folder, not reported'] += 1
            continue
        folder, name = parts
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        info = trash_info(data)
        if info is None:
            problems['.trashinfo files whose first line is not [Trash Info], not reported'] += 1
            continue
        stored_path, deleted = info
        original = unquote(stored_path, errors='replace')
        relative_to = '' if original.startswith('/') or not original else relative_base(folder)
        data_list.append((deleted, original, relative_to, stored_path, name, folder))
        read.append(path)
    if problems:
        logfunc('Trash (freedesktop): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
