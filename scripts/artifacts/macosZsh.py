"""zsh startup files and their compiled (.zwc) copies, compiled zsh files, zsh history and
Terminal session files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosZshStartupFiles": {
        "name": "zsh Startup Files",
        "description": "zsh startup files (.zshenv, .zprofile, .zshrc, .zlogin, "
                       ".zlogout and their /etc equivalents) and any compiled .zwc copy "
                       "beside each, with which copy zsh would select.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-24",
        "last_update_date": "2026-11-23",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "platforms": ("macOS",),
        "notes": (
            "Reads the zsh startup files .zshenv, .zprofile, .zshrc, .zlogin and .zlogout in any "
            "folder, their system equivalents in /etc (private/etc on macOS), and a compiled copy"
            " named with .zwc added beside any of them, one row per file name and folder. Scope "
            "is Home folder when the folder sits directly under Users or is /private/var/root, "
            "System for /etc or /private/etc, and Other folder anywhere else. zsh reads the user "
            "files from ZDOTDIR when it is set and from HOME otherwise, so a Home folder row "
            "assumes ZDOTDIR was not set, and an Other folder row is read only when ZDOTDIR named"
            " that folder; neither is established from these files (Reference: zsh, 'Files', "
            "https://zsh.sourceforge.io/Doc/Release/Files.html). The same page says a build can "
            "read its system files from a directory other than /etc; such files are reported as "
            "Other folder. Copies under /System/Library/Templates are counted in the run log and "
            "not reported. Copy zsh Selects follows try_source_file, check_dump_file and "
            "dump_find_func in the zsh 5.9 source (Reference: zsh, 'Src/parse.c', "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3796"
            " and "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3153):"
            " zsh runs the compiled copy when the plaintext is absent or its modified time, in "
            "whole seconds, is not later than the compiled copy's, and the compiled copy holds an"
            " entry whose name after its last slash equals the file's name. load_dump_header also"
            " requires the version recorded in the compiled copy to equal the running shell's "
            "(https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3250),"
            " which is why the value reads Compiled copy, if run by zsh and the recorded version."
            " Each of these rules was measured by starting /bin/zsh 5.9 as a login shell against "
            "the matching case in zsh_known_data_macos, and the 16 rows for those cases and for "
            "the case with no compiled copy agree with what zsh ran: a newer compiled copy ran "
            "for all five files, as did one with the same modified time, one whose plaintext had "
            "been deleted and one compiled in mapped mode; an older compiled copy, one compiled "
            "from another file and renamed into place, and one recording version 5.8 did not run,"
            " the last with no message. A row says which copy zsh selects when it starts with "
            "these files in place, not that zsh started. Plaintext Modified and Compiled Copy "
            "Modified are the modification times the tool reads from the input for each file as "
            "UTC times, to the whole second, such as from a tar header or a zip entry's NTFS or "
            "extended timestamp field. When the tool reads no UTC time, they are blank and "
            "Plaintext Modified (no zone, as stored) and Compiled Copy Modified (no zone, as "
            "stored) show the date and time the input holds, with no zone conversion. That is the"
            " case for a FAT directory entry, an exFAT directory entry (its stored UTC offset is "
            "not applied or shown here) and a zip entry with only its DOS date and time. A "
            "recorded time of 0 is treated as no time. For a folder or single-file input they are"
            " the times the operating system reports for those files on the examiner's machine, "
            "including any conversion it applied, and whatever copied the files there may have "
            "set them. The staged copy's own time is not reported. When both files have only a "
            "reading with no zone, Copy zsh Selects compares the two as stored, and Reason says "
            "so, because that assumes both were written at one UTC offset. When both files are "
            "present and one has a UTC time and the other does not, or either time is missing or "
            "unreadable, or two exFAT entries store different UTC offsets, it reads Not "
            "established, because the two cannot be ordered. No run here produced that value. "
            "Compiled By zsh and Compiled Entry Names are read from the compiled copy's header. "
            "Compiled By zsh is the version recorded there, which does not prove which zsh "
            "compiled the file. The entry name is the name given to zcompile, so it can hold a "
            "path. On zsh_known_data_macos all 15 are bare file names. On zsh_known_data_macos "
            "Scope is Home folder and User is dleapp on all 18 rows, because each case is one "
            "home folder. On dleapp_macos_bigsur the two rows are /private/etc/zprofile and "
            "/private/etc/zshrc, plaintext with no compiled copy, and the artifact reports no "
            "user startup file and no compiled copy there, so Compiled Copy Modified, Compiled By"
            " zsh, Compiled Entry Names, Compiled Copy Size, Compiled Copy Path and User are "
            "empty there."),
        "paths": ('*/.zshenv', '*/.zshenv.zwc', '*/.zprofile', '*/.zprofile.zwc', '*/.zshrc',
                  '*/.zshrc.zwc', '*/.zlogin', '*/.zlogin.zwc', '*/.zlogout', '*/.zlogout.zwc',
                  '*/etc/zshenv', '*/etc/zshenv.zwc', '*/etc/zprofile', '*/etc/zprofile.zwc',
                  '*/etc/zshrc', '*/etc/zshrc.zwc', '*/etc/zlogin', '*/etc/zlogin.zwc',
                  '*/etc/zlogout', '*/etc/zlogout.zwc'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "zsh_known_data_macos": "zsh 5.9 known data (synthetic) | 18 rows",
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 2 rows",
        },
    },
    "macosZshCompiledFiles": {
        "name": "zsh Compiled Files",
        "description": "Entries in compiled zsh wordcode (.zwc) files, with the zsh version "
                       "recorded in each file and the strings stored for each entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-24",
        "last_update_date": "2026-11-23",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "platforms": ("macOS",),
        "notes": (
            "Reads every file whose name ends in .zwc, one row per entry. The layout is zsh 5.9's"
            " (Reference: zsh, 'Src/parse.c', "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3061):"
            " a header recording the zsh version and whether the file is mapped or read when "
            "loaded, then the entries, all written twice, first in the byte order of the machine "
            "that compiled the file and then byte-swapped. zsh Version, Mode and Byte Order come "
            "from the first copy; Second Copy says whether the byte-swapped copy holds the same "
            "entries, compared by name, stored strings and wordcode length. Stored Strings is the"
            " entry's string table: each string of four or more characters once, in the order "
            "stored, with zsh's internal token bytes written back as the characters they stand "
            "for. Shorter strings are held inside the wordcode itself "
            "(https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L431)"
            " and are not listed, so in the known data's MacSync-style line the zsh after the "
            "pipe is absent while curl, -kfsSL and the base64 command substitution are present. "
            "The strings are what was compiled, not the script: comments and layout are not "
            "stored, and the wordcode is not decoded into commands here. A .zwc anywhere is "
            "reported, not only one beside a startup file. On zsh_known_data_macos the artifact "
            "reports 15 entries in 14 files; for 13 of those files zcompile -t in zsh 5.9 lists "
            "the same entry names, and it refuses the 14th, whose recorded version was changed to"
            " 5.8, which this reader still reads. On all 15 rows there Byte Order is "
            "little-endian, Second Copy is same entries and User is dleapp. On "
            "dleapp_macos_bigsur the artifact reports no rows. Modified is the modification time "
            "the tool reads from the input for the file as a UTC time, to the whole second, such "
            "as from a tar header or a zip entry's NTFS or extended timestamp field. When the "
            "tool reads no UTC time, Modified is blank and Modified (no zone, as stored) shows "
            "the date and time the input holds, with no zone conversion. That is the case for a "
            "FAT directory entry, an exFAT directory entry (its stored UTC offset is not applied "
            "or shown here) and a zip entry with only its DOS date and time. Both columns are "
            "blank when the input holds neither, and a recorded time of 0 is treated as no time. "
            "For a folder or single-file input Modified is the time the operating system reports "
            "for that file on the examiner's machine, including any conversion it applied, and "
            "whatever copied the file there may have set it. The staged copy's own time is not "
            "reported."),
        "paths": ('*.zwc',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-code",
        "sample_data": {
            "zsh_known_data_macos": "zsh 5.9 known data (synthetic) | 15 rows",
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows",
        },
    },
    "macosZshHistory": {
        "name": "zsh History",
        "description": "Commands saved in zsh history files (.zsh_history and "
                       "Terminal's per-session .zsh_sessions history files).",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-24",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Command Line (macOS)",
        "platforms": ("macOS",),
        "notes": (
            "Reads .zsh_history, the file the stock /etc/zshrc on macOS names as HISTFILE when "
            "ZDOTDIR is unset, and Terminal's per-session .history and .historynew files in "
            ".zsh_sessions, one row per command. Reading follows readhistline and readhistfile in "
            "the zsh 5.9 source (Reference: zsh, 'Src/hist.c', "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/hist.c#L2634 "
            "and "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/hist.c#L2724): "
            "a line ending in a backslash continues the command on the next line, a line starting "
            "with a colon, a start time, a colon, a number and a semicolon was written with the "
            "extended_history option, and the bytes zsh stores escaped (Meta, 0x83, followed by "
            "the byte XOR 32) are restored. Command Start is that start time and Elapsed Seconds "
            "the number after it, which the writer sets to 0 when it recorded no finish time "
            "(https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/hist.c#L3031), "
            "so 0 does not establish that a command took under a second. Both are empty for a "
            "file written without extended_history; the stock /etc/zshrc on macOS 26.6.2 does not "
            "set it. Line is the line where the command starts. History File is Shared history "
            "for .zsh_history and Terminal session for a file in .zsh_sessions, with Session ID "
            "from its name; Terminal appends a session's new commands to both "
            "(/etc/zshrc_Apple_Terminal on macOS 26.6.2, shell_session_save_history), so one "
            "command can appear twice, as it does on zsh_known_data_macos. A command in the file "
            "is one zsh saved to history: the known data's were added with print -s, not typed, "
            "and whether a command ran or succeeded is not recorded. On zsh_known_data_macos the "
            "artifact reports 9 rows, 5 with a start time, among them a command spanning three "
            "lines, a command holding an escaped character and a plain-format command beginning "
            "with a colon, and User is dleapp on all 9 rows. On dleapp_macos_bigsur both history "
            "files are 0 bytes, so there are no rows."),
        "paths": ('*/.zsh_history', '*/.zsh_sessions/*.history', '*/.zsh_sessions/*.historynew'),
        "output_types": ["html", "tsv", "lava", "timeline"],
        "artifact_icon": "terminal",
        "sample_data": {
            "zsh_known_data_macos": "zsh 5.9 known data (synthetic) | 9 rows",
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows",
        },
    },
    "macosZshTerminalSessions": {
        "name": "zsh Terminal Sessions",
        "description": "Terminal session state files in .zsh_sessions and the time each "
                       "records the session was saved.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-24",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Command Line (macOS)",
        "platforms": ("macOS",),
        "notes": (
            "Reads Terminal's session state files, <session id>.session in .zsh_sessions, which "
            "/etc/zshrc_Apple_Terminal writes when a zsh started by Terminal exits "
            "(shell_session_save, lines 213 to 217 of the file on macOS 26.6.2). The file holds "
            "echo Restored session: followed by /bin/date -r and a number of seconds taken from "
            "/bin/date +%s as the file was written; Saved is that number as a time. The same "
            "script runs the file and deletes it when the session is restored at the next start "
            "(line 112), and deletes files in .zsh_sessions older than two weeks when a shell "
            "exits (line 238), so a file present was written at a shell's exit and not restored "
            "since. Session ID is the file name, the TERM_SESSION_ID Terminal assigned (line "
            "103). Lines a user hook adds to the file are not reported. On dleapp_macos_bigsur "
            "the one file records 2021-01-17 20:21:01 UTC, the same second as the file's own "
            "modified time in the image, and it uses the same line format as macOS 26.6.2."),
        "paths": ('*/.zsh_sessions/*.session',),
        "output_types": ["html", "tsv", "lava", "timeline"],
        "artifact_icon": "terminal",
        "sample_data": {
            "zsh_known_data_macos": "zsh 5.9 known data (synthetic) | 1 row",
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 1 row",
        },
    },
}

import calendar
import os
import posixpath
import time

from scripts.context import Context
from scripts.ilapfuncs import artifact_processor, convert_ts_int_to_utc, logfunc
from scripts.macos_plists import canonical_relative, unique_sources, user_from_path
from scripts.macos_zsh import compiled_copy_selected, read_history, read_zwc, session_saved_time

_STARTUP = ('.zshenv', '.zprofile', '.zshrc', '.zlogin', '.zlogout')
_TEMPLATES = '/System/Library/Templates/'


def _relative(context, path):
    return '/' + context.get_relative_path(str(path)).replace('\\', '/').lstrip('/')


def _file_info(seeker, path):
    """The FileInfo the seeker recorded for a staged path, in any spelling a run uses."""
    infos = getattr(seeker, 'file_infos', None) or {}
    windows = str(path).replace('/', '\\')
    bare = windows.removeprefix('\\\\?\\')
    return next((infos[name] for name in (str(path), windows, bare, '\\\\?\\' + bare)
                 if name in infos), None)


def _file_times(seeker, path):
    """(UTC seconds, reading with no zone) the input records for a staged file.

    The staged copy's own time is not used: for a FAT, exFAT or DOS-only zip reading it is
    that reading placed in the examiner's time zone.
    """
    info = _file_info(seeker, path)
    times = getattr(info, 'times', None)
    modified = getattr(times, 'modified', None)
    if isinstance(modified, (int, float)) and modified:
        return modified, ''
    # a reading with no zone comes before the older field, which is never read as its UTC time
    reading = getattr(times, 'modified_no_zone', None)
    if reading:
        return None, reading
    modified = getattr(info, 'modification_date', None)
    if isinstance(modified, (int, float)) and modified:
        return modified, ''
    return None, ''


def _comparable(plain, compiled):
    """(plaintext, compiled copy) seconds for zsh's newer-than test, or None when they cannot be ordered.

    Two UTC times compare directly. Two readings with no zone compare as stored, on one clock,
    in whole seconds as zsh compares them. One of each, or a missing time, cannot be ordered.
    """
    if plain[0] is not None and compiled[0] is not None:
        return plain[0], compiled[0]
    if plain[0] is None and compiled[0] is None and plain[1] and compiled[1]:
        try:
            return tuple(calendar.timegm(time.strptime(reading[:19], '%Y-%m-%d %H:%M:%S'))
                         for reading in (plain[1], compiled[1]))
        except ValueError:
            return None
    return None


def _when(epoch):
    try:
        return convert_ts_int_to_utc(int(epoch // 1)) if epoch is not None else ''
    except OverflowError:
        return ''


def _modified_offset(seeker, path):
    """The UTC offset an exFAT entry stores beside its modification time, as text, or ''."""
    offsets = getattr(getattr(_file_info(seeker, path), 'times', None), 'utc_offsets', None) or ''
    for part in offsets.split(';'):
        label, _, value = part.strip().partition(' ')
        if label == 'modified':
            return value
    return ''


def _read_bytes(path):
    with open(path, 'rb') as handle:
        return handle.read()


def _startup_name(relative):
    """(scope, name zsh sources it by) for a matched path, or None when it is not a startup file.

    zsh reads the user files from ZDOTDIR, or HOME when ZDOTDIR is unset, and the system files
    from /etc (private/etc on macOS). A file of the same name anywhere else is reported with
    the scope Other folder.
    """
    base = posixpath.basename(relative)
    plain = base[:-4] if base.endswith('.zwc') else base
    parts = posixpath.dirname(canonical_relative(relative.lstrip('/'))).split('/')
    if plain in _STARTUP:
        home = (len(parts) >= 2 and parts[-2] == 'Users') or parts[-3:] == ['private', 'var', 'root']
        return ('Home folder' if home else 'Other folder'), plain
    if '.' + plain in _STARTUP and parts[-1] == 'etc':
        system = parts == ['etc'] or parts[-2:] == ['private', 'etc']
        return ('System' if system else 'Other folder'), plain
    return None


@artifact_processor
def macosZshStartupFiles(context):
    data_headers = (('Plaintext Modified', 'datetime'), 'Plaintext Modified (no zone, as stored)',
                    ('Compiled Copy Modified', 'datetime'), 'Compiled Copy Modified (no zone, as stored)',
                    'Startup File', 'Scope', 'User', 'Copy zsh Selects', 'Reason',
                    'Compiled By zsh', 'Compiled Entry Names', 'Plaintext Size',
                    'Compiled Copy Size', 'Plaintext Path', 'Compiled Copy Path')
    candidates, templates = [], 0
    for found in context.get_files_found():
        if not os.path.isfile(found):
            continue
        if _TEMPLATES in _relative(context, found):
            templates += 1
            continue
        candidates.append(found)
    if templates:
        logfunc(f'zsh Startup Files: {templates} file(s) under /System/Library/Templates not reported')
    paths, _skipped = unique_sources(context, candidates, label='zsh Startup Files')

    groups = {}
    for path in paths:
        relative = _relative(context, path)
        named = _startup_name(relative)
        if not named:
            continue
        scope, plain = named
        key = (posixpath.dirname(canonical_relative(relative.lstrip('/'))), plain)
        slot = 'compiled' if relative.endswith('.zwc') else 'plain'
        groups.setdefault(key, {'scope': scope, 'plain_name': plain})[slot] = path

    data_list, read = [], []
    for key in sorted(groups):
        group = groups[key]
        plain, compiled_path = group.get('plain'), group.get('compiled')
        seeker = Context.get_seeker()
        plain_times = _file_times(seeker, plain) if plain else (None, '')
        compiled_times = _file_times(seeker, compiled_path) if compiled_path else (None, '')
        compiled, version, names = None, '', ''
        if compiled_path:
            try:
                compiled = read_zwc(_read_bytes(compiled_path))
                version = compiled['version']
                names = '\n'.join(entry['name'] for entry in compiled['entries'])
            except (OSError, ValueError) as exc:
                logfunc(f'zsh Startup Files: could not read {_relative(context, compiled_path)}: {exc}')
        sourced_name = group['plain_name']
        if compiled_path and compiled is None:
            chosen, reason = False, 'compiled copy could not be read'
        elif plain and compiled and any(entry['tail'] == sourced_name for entry in compiled['entries']):
            order = _comparable(plain_times, compiled_times)
            as_stored = order is not None and plain_times[0] is None
            if as_stored and _modified_offset(seeker, plain) != _modified_offset(seeker, compiled_path):
                order = None
            if order is None:
                chosen, reason = None, 'plaintext and compiled copy times cannot be ordered'
            else:
                chosen, reason = compiled_copy_selected(order[0], order[1], compiled, sourced_name)
                if as_stored:
                    reason += ' (readings compared as stored, assuming one UTC offset)'
        else:
            # no compiled copy, no entry of this name, or no plaintext: no time is compared
            chosen, reason = compiled_copy_selected(plain_times[0], compiled_times[0], compiled, sourced_name)
        if chosen is None:
            selects = 'Not established'
        elif chosen:
            selects = f'Compiled copy, if run by zsh {version}'
        else:
            selects = 'Plaintext' if plain else 'Neither'
        if group['scope'] == 'Other folder':
            selects += ', if zsh reads this folder (ZDOTDIR)'
        anchor = plain or compiled_path
        for path in (plain, compiled_path):
            if path:
                read.append(path)
        data_list.append((
            _when(plain_times[0]), plain_times[1], _when(compiled_times[0]), compiled_times[1],
            sourced_name, group['scope'],
            user_from_path(context.get_relative_path(anchor)),
            selects, reason, version, names,
            os.path.getsize(plain) if plain else '',
            os.path.getsize(compiled_path) if compiled_path else '',
            _relative(context, plain) if plain else '',
            _relative(context, compiled_path) if compiled_path else ''))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosZshCompiledFiles(context):
    data_headers = (('Modified', 'datetime'), 'Modified (no zone, as stored)', 'Compiled File', 'Entry Name', 'Entry Number',
                    'zsh Version', 'Mode', 'Byte Order', 'Stored Strings', 'Second Copy',
                    'User', 'Source File')
    paths, _skipped = unique_sources(
        context, [p for p in context.get_files_found() if os.path.isfile(p)],
        label='zsh Compiled Files')
    data_list, read = [], []
    for path in paths:
        relative = _relative(context, path)
        try:
            compiled = read_zwc(_read_bytes(path))
        except (OSError, ValueError) as exc:
            logfunc(f'zsh Compiled Files: not a compiled zsh file, {relative}: {exc}')
            continue
        read.append(path)
        modified, no_zone = _file_times(Context.get_seeker(), path)
        for number, entry in enumerate(compiled['entries'], 1):
            data_list.append((
                _when(modified), no_zone, posixpath.basename(relative), entry['name'], number,
                compiled['version'], compiled['mode'], compiled['byte_order'],
                '\n'.join(entry['strings']), compiled['second_copy'],
                user_from_path(context.get_relative_path(path)), relative))
    return data_headers, data_list, '\n'.join(read)


def _history_label(relative):
    base = posixpath.basename(relative)
    if posixpath.basename(posixpath.dirname(relative)) == '.zsh_sessions':
        return 'Terminal session', base.rsplit('.', 1)[0]
    return 'Shared history', ''


@artifact_processor
def macosZshHistory(context):
    data_headers = (('Command Start', 'datetime'), 'Elapsed Seconds', 'Command', 'History File',
                    'Session ID', 'Line', 'User', 'Source File')
    paths, _skipped = unique_sources(
        context, [p for p in context.get_files_found() if os.path.isfile(p)],
        label='zsh History')
    data_list, read = [], []
    for path in paths:
        relative = _relative(context, path)
        try:
            records = read_history(_read_bytes(path))
        except OSError as exc:
            logfunc(f'zsh History: could not read {relative}: {exc}')
            continue
        read.append(path)
        kind, session = _history_label(relative)
        for record in records:
            data_list.append((
                _when(record['start']), '' if record['elapsed'] is None else record['elapsed'],
                record['command'], kind, session, record['line'], user_from_path(context.get_relative_path(path)), relative))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosZshTerminalSessions(context):
    data_headers = (('Saved', 'datetime'), 'Session ID', 'User', 'Source File')
    paths, _skipped = unique_sources(
        context, [p for p in context.get_files_found() if os.path.isfile(p)],
        label='zsh Terminal Sessions')
    data_list, read = [], []
    for path in paths:
        relative = _relative(context, path)
        try:
            saved = session_saved_time(_read_bytes(path))
        except OSError as exc:
            logfunc(f'zsh Terminal Sessions: could not read {relative}: {exc}')
            continue
        read.append(path)
        data_list.append((_when(saved), posixpath.basename(relative).rsplit('.', 1)[0],
                          user_from_path(context.get_relative_path(path)), relative))
    return data_headers, data_list, '\n'.join(read)
