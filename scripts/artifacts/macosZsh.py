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
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "notes": (
            "Reads the zsh startup files .zshenv, .zprofile, .zshrc, .zlogin and .zlogout in any "
            "folder, their system equivalents in /etc (private/etc on macOS), and a compiled copy "
            "named with .zwc added beside any of them, one row per file name and folder. Scope is "
            "Home folder when the folder sits directly under Users or is /private/var/root, "
            "System for /etc or /private/etc, and Other folder anywhere else. zsh reads the user "
            "files from ZDOTDIR when it is set and from HOME otherwise, so a Home folder row "
            "assumes ZDOTDIR was not set, and an Other folder row is read only when ZDOTDIR named "
            "that folder; neither is established from these files (Reference: zsh, 'Files', "
            "https://zsh.sourceforge.io/Doc/Release/Files.html). The same page says a build can "
            "read its system files from a directory other than /etc; such files are reported as "
            "Other folder. Copies under /System/Library/Templates are counted in the run log and "
            "not reported. Copy zsh Selects follows try_source_file and check_dump_file in the "
            "zsh 5.9 source (Reference: zsh, 'Src/parse.c', "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3796 "
            "and "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3153): "
            "zsh runs the compiled copy when the plaintext is absent or its modified time, in "
            "whole seconds, is not later than the compiled copy's, and the compiled copy holds an "
            "entry whose name after its last slash equals the file's name. load_dump_header also "
            "requires the version recorded in the compiled copy to equal the running shell's "
            "(https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3250), "
            "which is why the value reads Compiled copy, if run by zsh and the recorded version. "
            "Each of these rules was measured by starting /bin/zsh 5.9 as a login shell against "
            "the matching case in zsh_known_data_macos, and the 16 rows for those cases agree "
            "with what zsh ran: a newer compiled copy ran for all five files, as did one with the "
            "same modified time, one whose plaintext had been deleted and one compiled in mapped "
            "mode; an older compiled copy, one compiled from another file and renamed into place, "
            "and one recording version 5.8 did not run, the last with no message. A row says "
            "which copy zsh selects when it starts with these files in place, not that zsh "
            "started. Plaintext Modified and Compiled Copy Modified are the modified times the "
            "evidence records for each file. Compiled By zsh and Compiled Entry Names are read "
            "from the compiled copy's header; zcompile stores the name exactly as it was given, "
            "so an entry name can be a bare file name or a full path on the machine that compiled "
            "it. On zsh_known_data_macos Scope is Home folder and User is dleapp on all 18 rows, "
            "because each case is one home folder. On dleapp_macos_bigsur the one row is "
            "/etc/zprofile, plaintext with no compiled copy; /etc/zshrc was not staged because "
            "the image reader does not read its LZFSE compression, which the run log names, and "
            "the image holds no user startup file and no .zwc, so Compiled Copy Modified, "
            "Compiled By zsh, Compiled Entry Names, Compiled Copy Size, Compiled Copy Path and "
            "User are empty there."),
        "paths": ('*/.zshenv', '*/.zshenv.zwc', '*/.zprofile', '*/.zprofile.zwc', '*/.zshrc',
                  '*/.zshrc.zwc', '*/.zlogin', '*/.zlogin.zwc', '*/.zlogout', '*/.zlogout.zwc',
                  '*/etc/zshenv', '*/etc/zshenv.zwc', '*/etc/zprofile', '*/etc/zprofile.zwc',
                  '*/etc/zshrc', '*/etc/zshrc.zwc', '*/etc/zlogin', '*/etc/zlogin.zwc',
                  '*/etc/zlogout', '*/etc/zlogout.zwc'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "zsh_known_data_macos": "zsh 5.9 known data (synthetic) | 18 rows",
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 1 row",
        },
    },
    "macosZshCompiledFiles": {
        "name": "zsh Compiled Files",
        "description": "Entries in compiled zsh wordcode (.zwc) files, with the zsh "
                       "version that wrote each file and the strings stored for each "
                       "entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-24",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "notes": (
            "Reads every file whose name ends in .zwc, one row per entry. The layout is zsh 5.9's "
            "(Reference: zsh, 'Src/parse.c', "
            "https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L3061): "
            "a header recording the zsh version and whether the file is mapped or read when "
            "loaded, then the entries, all written twice, first in the byte order of the machine "
            "that compiled the file and then byte-swapped. zsh Version, Mode and Byte Order come "
            "from the first copy; Second Copy says whether the byte-swapped copy holds the same "
            "entries, compared by name, stored strings and wordcode length. Stored Strings is the "
            "entry's string table: each string of four or more characters once, in the order "
            "stored, with zsh's internal token bytes written back as the characters they stand "
            "for. Shorter strings are held inside the wordcode itself "
            "(https://github.com/zsh-users/zsh/blob/73d317384c9225e46d66444f93b46f0fbe7084ef/Src/parse.c#L431) "
            "and are not listed, so in the known data's MacSync-style line the zsh after the pipe "
            "is absent while curl, -kfsSL and the base64 command substitution are present. The "
            "strings are what was compiled, not the script: comments and layout are not stored, "
            "and the wordcode is not decoded into commands here. A .zwc anywhere is reported, not "
            "only one beside a startup file. On zsh_known_data_macos the artifact reports 15 "
            "entries in 14 files; for 13 of those files zcompile -t in zsh 5.9 lists the same "
            "entry names, and it refuses the 14th, whose recorded version was changed to 5.8, "
            "which this reader still reads. The files there were compiled on Apple silicon, so "
            "Byte Order is little-endian, Second Copy is same entries and User is dleapp on all "
            "15 rows. dleapp_macos_bigsur holds no .zwc."),
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

import os
import posixpath

from scripts.context import Context
from scripts.ilapfuncs import artifact_processor, convert_ts_int_to_utc, logfunc
from scripts.macos_plists import canonical_relative, unique_sources, user_from_path
from scripts.macos_zsh import compiled_copy_selected, read_history, read_zwc, session_saved_time

_STARTUP = ('.zshenv', '.zprofile', '.zshrc', '.zlogin', '.zlogout')
_TEMPLATES = '/System/Library/Templates/'


def _relative(context, path):
    return '/' + context.get_relative_path(str(path)).replace('\\', '/').lstrip('/')


def _modified(path):
    """The modified time the seeker recorded for a staged file, in epoch seconds."""
    seeker = Context.get_seeker()
    info = getattr(seeker, 'file_infos', {}).get(path) if seeker else None
    value = getattr(info, 'modification_date', None)
    if isinstance(value, (int, float)) and value:
        return value
    return os.path.getmtime(path)


def _when(epoch):
    return convert_ts_int_to_utc(int(epoch)) if epoch is not None else ''


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
    data_headers = (('Plaintext Modified', 'datetime'), ('Compiled Copy Modified', 'datetime'),
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
        plain_mtime = _modified(plain) if plain else None
        compiled_mtime = _modified(compiled_path) if compiled_path else None
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
        else:
            chosen, reason = compiled_copy_selected(plain_mtime, compiled_mtime, compiled, sourced_name)
        if chosen:
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
            _when(plain_mtime), _when(compiled_mtime), sourced_name, group['scope'],
            user_from_path(context.get_relative_path(anchor)),
            selects, reason, version, names,
            os.path.getsize(plain) if plain else '',
            os.path.getsize(compiled_path) if compiled_path else '',
            _relative(context, plain) if plain else '',
            _relative(context, compiled_path) if compiled_path else ''))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def macosZshCompiledFiles(context):
    data_headers = (('Modified', 'datetime'), 'Compiled File', 'Entry Name', 'Entry Number',
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
        modified = _modified(path)
        for number, entry in enumerate(compiled['entries'], 1):
            data_list.append((
                _when(modified), posixpath.basename(relative), entry['name'], number,
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
