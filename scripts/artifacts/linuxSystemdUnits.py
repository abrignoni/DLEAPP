"""Unit files, drop-ins and the links that enable, alias, link or mask units in the folders where an administrator or a
user configures systemd, and the settings those files hold, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxSystemdUnitEntries": {
        "name": "systemd Unit Files and Links",
        "description": "Entries of the folders where an administrator or a user configures systemd units "
                       "(/etc/systemd/system, /etc/systemd/user and ~/.config/systemd/user): unit files, drop-ins "
                       "and the links that alias, link or mask a unit or make one unit want, require or uphold "
                       "another.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Persistence (Linux)",
        "notes": "Reads each file and link under a folder named etc/systemd/system, etc/systemd/user or "
                 ".config/systemd/user, wherever it sits in the extraction, and reports one row per entry in the "
                 "order of Source File, the path the evidence records for it. Scope is System for "
                 "etc/systemd/system, which systemd.unit(5) lists as system units created by the administrator, All "
                 "users for etc/systemd/user, user units created by the administrator, and User for a user's "
                 ".config/systemd/user, that user's configuration (systemd v259.5, man/systemd.unit.xml, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L402-L403, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L472-L473, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L464-L465); "
                 "the other folders systemd loads units from, such as /usr/lib/systemd/system, /run/systemd/system "
                 "and ~/.local/share/systemd/user, are not read. Kind is Unit file for a file directly in the folder "
                 "whose name is a unit name "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L121-L128, "
                 "src/basic/unit-name.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/unit-name.c#L37-L83), "
                 "Empty unit file (masked) for such a file of size 0 and Masked (link to /dev/null) for such a link "
                 "to /dev/null, both of which systemd shows as masked and does not load "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L273-L278). "
                 "Any other link with a unit name directly in the folder is an Alias link when its target lies in a "
                 "folder of the unit load path and a Linked unit file when it lies outside "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L537-L552); "
                 "the load path is the one systemd-analyze unit-paths printed on the VM the capture below comes "
                 "from, with a user's own folders matched by the name of the home folder the link is in and runtime "
                 "folders under /run/user taken for any user, and a target under /lib counts as under /usr/lib, as "
                 "on a system where /lib is a link to usr/lib, since systemd resolves the folders in a target before "
                 "comparing (src/shared/unit-file.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/shared/unit-file.c#L318-L333): "
                 "on that VM, where /lib is such a link, systemctl list-unit-files called display-manager.service, a "
                 "link to /lib/systemd/system/gdm3.service, an alias. systemd also requires an alias's name to agree "
                 "with its target's "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L157-L170), "
                 "which is not checked here. Wants link, Requires link and Upholds link are links in a folder named "
                 "for a unit, a template, a prefix of unit names or a unit type followed by .wants, .requires or "
                 ".upholds, which make that unit want, require or uphold the unit the link names "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L184-L201, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L2196-L2199, "
                 "src/shared/dropin.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/shared/dropin.c#L143-L295); "
                 "Dependency Of names that unit, and a Masked dependency (link to /dev/null) is such a link to "
                 "/dev/null, which adds no dependency (src/core/load-dropin.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/core/load-dropin.c#L43-L48). "
                 "Drop-in and Drop-in link are a file and a link whose name ends in .conf in a folder named like "
                 "those but followed by .d, which systemd reads after the unit file "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L203-L221, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L241-L250); "
                 "Unit is then the folder's name without .d, so it can name a template, a prefix of unit names "
                 "ending in a dash or a whole unit type. Kind is Other for any other entry, such as a name that is "
                 "not a unit name, a file that is not a link in a .wants, .requires or .upholds folder, and a name "
                 "in one of those folders or a .d folder that begins with a dot, all of which systemd skips "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/shared/unit-file.c#L463-L465, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/core/load-dropin.c#L51-L72, "
                 "src/basic/path-util.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/path-util.c#L1277-L1325). "
                 "These readings were checked by loading constructed files into the user manager of a VM running "
                 "systemd 259.5 and reading what systemctl reported, for Wants links and for folders named for a "
                 "unit; Requires links were seen only in the capture below and Upholds links not at all, and that "
                 "manager also loaded a unit file whose name begins with a dot, which systemctl list-unit-files did "
                 "not list. Unit is the unit's name as stored, with any escape systemd writes into a name made from "
                 "a path, such as \\x2d for a dash "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L299-L303); "
                 "Link Target is a link's target as recorded and blank for a file. Modified (UTC) is the modified "
                 "time the seeker recorded for the entry, for a link the link's own, and is blank where none was "
                 "recorded. A tar or a zip records a link as a link, and in an input folder the link is read from "
                 "the folder itself, where DLEAPP's folder reader stages nothing for a link that resolves outside "
                 "the input: ubuntu2604_arm64_units extracted to a folder gave the same 196 rows as the tar, all 179 "
                 "links included (the zip case is exercised by the unit tests' constructed inputs, not by a "
                 "registered image). DLEAPP's raw image reader lists no symbolic links (scripts/raw_image.py), so on "
                 "a raw image only files give rows: the same capture written into an ext4 image with mke2fs -d gave "
                 "the tar's 17 file rows and none of its 179 links. On ubuntu2604_arm64_units, captured from a VM "
                 "running systemd 259.5 after a script run as an unprivileged user wrote, enabled, overrode, "
                 "aliased, linked and masked known user units, the 196 rows are 154 System, 33 All users and 9 User. "
                 "There, in the states systemctl list-unit-files reported on the VM, each Alias link names an alias, "
                 "each masked entry a masked unit, the Linked unit file a linked one, each Wants or Requires link an "
                 "enabled unit and each Unit file a unit that is neither an alias nor masked; the System and All "
                 "users entries and link targets equal a listing of /etc/systemd taken on the VM afterwards; and "
                 "each User entry's time falls in the second, as the tar records it, of the script step that wrote "
                 "it.",
        "paths": ('*/etc/systemd/system/*', '*/etc/systemd/user/*', '*/.config/systemd/user/*'),
        "output_types": ["html", "tsv", "lava"],
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 196 rows",
        },
        "artifact_icon": "rocket",
    },
    "linuxSystemdUnitSettings": {
        "name": "systemd Unit Settings",
        "description": "Settings from the unit files and drop-ins in the folders where an administrator or a user "
                       "configures systemd units, as written, with the section and line each is on.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Persistence (Linux)",
        "notes": "Reads each Unit file and Drop-in that systemd Unit Files and Links reports, in its order, and "
                 "reports one row per assignment: Section is the section it is in, Key and Value are the text before "
                 "and after its first =, each with the spaces and tabs around it removed, and Line is the line the "
                 "assignment begins on; Scope, Unit and Source File are as in that artifact and Modified (UTC) is "
                 "the file's recorded modified time. Values are reported as written, with nothing unquoted, "
                 "unescaped or expanded, and so is a setting systemd ignores, under a key it does not know or in a "
                 "section it does not know or whose name begins with X- "
                 "(https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/man/systemd.unit.xml#L137-L141); "
                 "on the VM the manager ignored an assignment in a [Foo] and in an [X-Custom] section. Links are not "
                 "read, since a link's target can lie outside the evidence. A file is read as systemd's "
                 "config_parse() reads one (src/shared/conf-parser.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/shared/conf-parser.c#L331-L445, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/shared/conf-parser.c#L172-L275): "
                 "a \\n, a \\r or a \\0 ends a line (src/basic/fileio.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/fileio.c#L1466-L1482); "
                 "a line whose first character after any spaces or tabs is # or ; is a comment, even inside a "
                 "continued line; a byte order mark is removed from the first line that begins with one; a line "
                 "ending in a backslash that is not itself escaped continues on the next line, the backslash "
                 "replaced by a space; and a line before the first section header, or with no = or nothing before "
                 "it, is skipped and counted in the run log. systemd does not load a unit file that has a line that "
                 "is not valid UTF-8, a section header that does not end in ] or whose name holds a quote, a "
                 "backslash, DEL or another control character (src/basic/string-util.c, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/string-util.c#L1089-L1104), "
                 "a line of 1,048,576 characters or more, or a continued line that grows past 1,048,576 "
                 "(src/basic/fileio.h, "
                 "https://github.com/systemd/systemd/blob/b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a/src/basic/fileio.h#L6), "
                 "and it applies a drop-in only up to such a line; such a unit file gives no row, a drop-in gives "
                 "the assignments before that line, and either is named in the run log with the line. Each of these "
                 "rules was checked on the VM, where 32 constructed unit files and 3 drop-ins were loaded into the "
                 "user manager of systemd 259.5: for every one whether the unit loaded, and for all but the 4 built "
                 "to test the character limits the Description systemctl show printed, agree with this artifact's "
                 "reading. On ubuntu2604_arm64_units the 144 rows come from 16 files, none of them holding a "
                 "continued line, a carriage return or a byte order mark; for the 13 System and All users unit files "
                 "and for dleapp-known.service the Description equals what systemctl show printed on the VM, the 3 "
                 "user files hold exactly what the known-data script wrote, and the capture extracted to a folder "
                 "and written into an ext4 image gave the same 144 rows.",
        "paths": ('*/etc/systemd/system/*', '*/etc/systemd/user/*', '*/.config/systemd/user/*'),
        "output_types": ["html", "tsv", "lava"],
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 144 rows",
        },
        "artifact_icon": "settings",
    },
}

import os
import posixpath
import re
import string
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import in_folder, recorded_link, recorded_time, seeker_of

# (folder, scope) where systemd reads the configuration an administrator or a user writes.
FOLDERS = (('etc/systemd/system/', 'System'), ('etc/systemd/user/', 'All users'), ('.config/systemd/user/', 'User'))
# The unit load paths systemd-analyze unit-paths printed for the system and the user manager on a VM running
# systemd 259.5. A user's own folders are matched by the name of the home folder a link is in, and runtime folders
# under /run/user are taken for any user.
SYSTEM_LOAD_PATH = ('/etc/systemd/system.control', '/run/systemd/system.control', '/run/systemd/transient',
                    '/run/systemd/generator.early', '/etc/systemd/system', '/etc/systemd/system.attached',
                    '/run/systemd/system', '/run/systemd/system.attached', '/run/systemd/generator',
                    '/usr/local/lib/systemd/system', '/usr/lib/systemd/system', '/run/systemd/generator.late')
USER_LOAD_PATH = ('/etc/systemd/user', '/run/systemd/user', '/usr/local/share/systemd/user',
                  '/usr/share/systemd/user', '/usr/local/lib/systemd/user', '/usr/lib/systemd/user')
USER_HOME_LOAD_PATH = ('/.config/systemd/user.control', '/.config/systemd/user', '/.local/share/systemd/user')
USER_RUNTIME = re.compile(r'/run/user/\d+/systemd/(?:user\.control|transient|generator\.early|user|generator|'
                          r'generator\.late)')
# Unit types and the characters of a unit name (unit-def.c unit_type_table, unit-name.c VALID_CHARS_WITH_AT).
UNIT_TYPES = ('service', 'socket', 'target', 'device', 'mount', 'automount', 'swap', 'timer', 'path', 'slice',
              'scope')
NAME_CHARACTERS = frozenset(string.ascii_letters + string.digits + ':-_.\\@')
LINK_FOLDERS = (('.wants', 'Wants link'), ('.requires', 'Requires link'), ('.upholds', 'Upholds link'))
LONG_LINE_MAX = 1024 * 1024  # fileio.h; read_line refuses a line of this many characters or more
TOO_LONG = 'a line longer than systemd reads'
NOT_UTF8 = 'a line that is not UTF-8'
BAD_HEADER = 'a section header systemd rejects'


def source_of(seeker, path, relative):
    """Where a file the seeker returned sits in the evidence, / separated: its path in the input folder, or the
    member name a tar, zip or raw image recorded. The staged path can differ: the raw image seeker, and any seeker
    on Windows, stages a name holding a backslash in folders split at it, and a unit name holds a backslash where
    systemd escapes a character (systemd.unit(5))."""
    if getattr(seeker, 'directory', None):
        return os.path.relpath(in_folder(seeker, path), seeker.directory).replace(os.sep, '/')
    info = getattr(seeker, 'file_infos', {}).get(path)
    return info.source_path if info is not None else relative.replace(os.sep, '/')


def place(source):
    """(scope, the folder's path, path inside the folder) for a / separated path in the evidence under one of
    FOLDERS, or None. The folder's path is the one the system knows, except that a user's folder keeps the
    evidence path of the home folder it is in."""
    rel = '/' + source
    for folder, scope in FOLDERS:
        at = rel.find('/' + folder)
        if at >= 0:
            inside = rel[at + 1 + len(folder):]
            if inside:
                return scope, (rel[:at] if scope == 'User' else '') + '/' + folder.rstrip('/'), inside
    return None


def in_load_path(scope, base, target):
    """Whether a link's target lies in a folder of the unit load path of its scope. A relative target is read
    against the folder the link is in, and /lib as /usr/lib, as on a system whose /usr is merged."""
    where = posixpath.dirname(posixpath.normpath(posixpath.join(base, target)))
    if where == '/lib' or where.startswith('/lib/'):
        where = '/usr' + where
    if scope == 'System':
        return where in SYSTEM_LOAD_PATH
    if where in USER_LOAD_PATH:
        return True
    if scope != 'User':
        return False
    home = base[:-len('/.config/systemd/user')]
    name = posixpath.basename(posixpath.normpath(home)) if home else ''
    return (USER_RUNTIME.fullmatch(where) is not None
            or any(where.endswith(('/' + name if name else '') + folder) for folder in USER_HOME_LOAD_PATH))


def unit_name(name):
    """Whether systemd takes a name as a unit name: letters, digits and :-_.\\@, not starting with @, then a dot and
    a unit type, under 256 characters (unit_name_is_valid in src/basic/unit-name.c)."""
    stem, dot, kind = name.rpartition('.')
    return (bool(dot and stem) and kind in UNIT_TYPES and not stem.startswith('@')
            and set(stem) <= NAME_CHARACTERS and len(name) < 256)


def names_units(holder):
    """Whether a .wants, .requires, .upholds or .d folder of this name is one systemd reads: named for a unit, a
    template or a name prefix, or for a unit type."""
    return unit_name(holder) or holder in UNIT_TYPES


def entry_kind(scope, base, inside, link, size):
    """(unit, kind, dependency of) for one entry of a unit folder."""
    parts = inside.split('/')
    name = parts[-1]
    if len(parts) == 1 and unit_name(name):
        if link is None:
            return name, 'Empty unit file (masked)' if size == 0 else 'Unit file', ''
        if link == '/dev/null':
            return name, 'Masked (link to /dev/null)', ''
        return name, 'Alias link' if in_load_path(scope, base, link) else 'Linked unit file', ''
    # In the folders below systemd skips a name that begins with a dot (hidden_or_backup_file in
    # src/basic/path-util.c; none of its backup suffixes can end a unit name or a .conf name).
    if len(parts) == 2 and not name.startswith('.'):
        holder = parts[0]
        for suffix, kind in LINK_FOLDERS:
            owner = holder[:-len(suffix)]
            if holder.endswith(suffix) and names_units(owner) and link is not None and unit_name(name):
                return name, 'Masked dependency (link to /dev/null)' if link == '/dev/null' else kind, owner
        if holder.endswith('.d') and names_units(holder[:-2]) and name.endswith('.conf'):
            return holder[:-2], 'Drop-in' if link is None else 'Drop-in link', ''
    return name, 'Other', ''


def lines_of(data):
    """The lines of a file as systemd's read_line_full splits them: \\n, \\r and \\0 each end a line, and one of each,
    in any order with \\0 last, end it together."""
    lines, current, seen = [], bytearray(), 0
    for byte in data:
        eol = {0: 1, 10: 2, 13: 4}.get(byte, 0)
        if seen & 1 or (not eol and seen) or (eol and seen & eol):
            lines.append(bytes(current))
            current, seen = bytearray(), 0
        if eol:
            seen |= eol
        else:
            current.append(byte)
    if current or seen:
        lines.append(bytes(current))
    return lines


def unit_settings(data):
    """Read a unit file or drop-in as systemd's config_parse() reads one. Returns (settings, stop, skipped):
    settings is (line, section, key, value) for each assignment before any line systemd stops at, stop is
    (line, why) for that line or None, and skipped counts the lines systemd ignores."""
    settings, section, continuation, start, bom_seen = [], None, None, 0, False
    skipped = Counter()
    for number, raw in enumerate(lines_of(data) + [None], 1):
        if raw is None:
            if continuation is None:
                break
            text = continuation
        else:
            if len(raw) >= LONG_LINE_MAX:
                return settings, (number, TOO_LONG), skipped
            if raw.lstrip(b' \t\n\r')[:1] in (b'#', b';'):
                continue
            if not bom_seen and raw.startswith(b'\xef\xbb\xbf'):
                raw, bom_seen = raw[3:], True
            if continuation is None:
                start = number
            elif len(continuation) + len(raw) > LONG_LINE_MAX:
                return settings, (number, TOO_LONG), skipped
            text = raw if continuation is None else continuation + raw
            escaped = False
            for byte in text:
                escaped = not escaped and byte == 92
            if escaped:
                continuation = text[:-1] + b' '
                continue
        continuation = None
        line = text.strip(b' \t\n\r')
        if not line:
            continue
        try:
            line = line.decode('utf-8')
        except UnicodeDecodeError:
            return settings, (number, NOT_UTF8), skipped
        if line.startswith('['):
            name = line[1:-1]
            if not line.endswith(']') or any(ord(c) < 32 or c in '"\'\\\x7f' for c in name):
                return settings, (number, BAD_HEADER), skipped
            section = name
            continue
        if section is None:
            skipped['lines outside a section'] += 1
            continue
        key, sep, value = line.partition('=')
        if not sep or not key:
            skipped['lines that are not assignments'] += 1
            continue
        settings.append((start, section, key.strip(' \t\n\r'), value.strip(' \t\n\r')))
    return settings, None, skipped


def _entries(context):
    """(source, path, scope, folder's path, inside, link, time) for every entry of the unit folders, sorted."""
    seeker = seeker_of(context)
    found = []
    for path in map(str, context.get_files_found()):
        link = recorded_link(seeker, path)
        if link is None and not os.path.isfile(path):
            continue  # a folder, or a path the seeker returned without staging a file there
        source = source_of(seeker, path, context.get_relative_path(path))
        where = place(source)
        if where is not None:
            found.append((source, path, *where, link, recorded_time(seeker, path, link)))
    return sorted(found)


@artifact_processor
def linuxSystemdUnitEntries(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Scope', 'Unit', 'Kind', 'Dependency Of', 'Link Target',
                    'Source File')
    data_list = []
    read = []
    for source, path, scope, base, inside, link, when in _entries(context):
        size = os.path.getsize(path) if link is None else None
        unit, kind, owner = entry_kind(scope, base, inside, link, size)
        data_list.append((when, scope, unit, kind, owner, link or '', source))
        read.append(path)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def linuxSystemdUnitSettings(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Scope', 'Unit', 'Section', 'Key', 'Value', 'Line',
                    'Source File')
    data_list = []
    read = []
    counts = Counter()
    for source, path, scope, base, inside, link, when in _entries(context):
        if link is not None:
            continue
        unit, kind, _owner = entry_kind(scope, base, inside, link, os.path.getsize(path))
        if kind not in ('Unit file', 'Drop-in'):
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        settings, stop, skipped = unit_settings(data)
        counts.update(skipped)
        if stop is not None:
            number, why = stop
            if kind == 'Unit file':
                logfunc(f'systemd Unit Settings: {source} not reported: systemd does not load a unit file with '
                        f'{why} (line {number})')
                continue
            logfunc(f'systemd Unit Settings: {source} read up to line {number}, where systemd stops reading a '
                    f'drop-in with {why}')
        if not settings:
            continue
        data_list.extend((when, scope, unit, section, key, value, number, source)
                         for number, section, key, value in settings)
        read.append(path)
    if counts:
        logfunc('systemd Unit Settings: ' + ', '.join(f'{count} {what}' for what, count in sorted(counts.items()))
                + ', not reported')
    return data_headers, data_list, '\n'.join(read)
