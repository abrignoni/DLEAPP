"""Lines in the history file of the sqlite3 command line shell (.sqlite_history), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "sqliteShellHistory": {
        "name": "SQLite Shell History",
        "description": "Lines typed into the sqlite3 command line shell, from its history file (.sqlite_history), "
                       "in the order the file holds them, with each line's number in the file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Command Line (SQLite)",
        "notes": "One row per entry in a .sqlite_history file, the history the sqlite3 command line shell keeps. "
                 "When it reads commands from its standard input interactively, which it does when it classes that "
                 "input as a console (Reference: SQLite 3.46.1, 'src/shell.c.in', "
                 "https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L12243-L12244) "
                 "and which the -interactive option turns on "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L12644-L12648) "
                 "and -batch off "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L12367-L12373), "
                 "the shell reads the file named by SQLITE_HISTORY or, when that is not set, .sqlite_history in "
                 "the home folder as it starts "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L12770 "
                 "and "
                 "https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L12788-L12797), "
                 "adds every non-empty line typed to its history "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L853), "
                 "and when the session ends keeps the last 2000 and writes them all back to the file "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L12805-L12807). "
                 "The artifact reads only files named .sqlite_history, so a history kept under another name "
                 "through SQLITE_HISTORY is not read. How the file is written depends on the line editing library "
                 "the shell was built with: GNU readline and libedit are used through the same calls "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L146-L150), "
                 "and a build with linenoise "
                 "(https://github.com/sqlite/sqlite/blob/f3d536d37825302e31ed0eddd811c689f38f85a3/src/shell.c.in#L152-L159) "
                 "was not tested. Measured on ubuntu2604_arm64_sqlitehist, from sqlite3 3.46.1 linked with GNU "
                 "readline 8.3 on the lab VM: each line of a statement typed over two lines was its own entry and "
                 "an empty line was not kept; a session killed with SIGKILL wrote nothing; when two sessions "
                 "overlapped, the one that ended last wrote the file from what it had read at its start plus its "
                 "own lines, so the other session's lines were gone; a session of 2010 statements left the last "
                 "2000 lines; and a session run with SQLITE_HISTORY set wrote to that file and left "
                 ".sqlite_history unchanged. File Format is plain for any other file, the form GNU readline "
                 "writes, one entry per line, read as readline 8.3 reads a history file (GNU Readline 8.3, "
                 "'histfile.c', from the release tarball https://ftp.gnu.org/gnu/readline/readline-8.3.tar.gz, "
                 "sha256 fe5383204467828cd495ee8d1d3c037a7eba1389c22bc6a041f627976f9061cc): a line ends at a "
                 "newline (lines 417 to 418), a carriage return before it is dropped (lines 420 to 424), an empty "
                 "line is no entry (line 426), and when the file begins with # and a digit, every line that does "
                 "is a timestamp rather than an entry (lines 373 to 381 and line 140); the artifact counts those "
                 "lines in the run log and does not report them. Readline does not load a last line with no "
                 "newline after it; the artifact reports it and counts it in the run log. File Format is libedit "
                 "for a file whose first line is exactly _HiStOrY_V2_, the line libedit writes first and checks "
                 "when it reads ('lib/libedit/history.c', "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L846 "
                 "and "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L794); "
                 "libedit encodes each entry with strvis "
                 "(https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L874) "
                 "and decodes each later line with strunvis when it reads "
                 "(https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L800-L817), "
                 "and the artifact decodes each line as strunvis does, with no flags, as the Python REPL History "
                 "artifact does ('lib/libc/gen/unvis.c', "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libc/gen/unvis.c#L549-L552); "
                 "libedit's reader on the Mac drops a trailing octal escape of 1 or 2 digits or hex escape of 1 "
                 "digit, which the artifact keeps, as that artifact's notes record, and strvis does not write "
                 "those. libedit loads an empty line as an empty entry; the artifact counts it in the run log and "
                 "does not report it. Entry is the text as UTF-8, with any byte that is not valid UTF-8 written as "
                 "a \\x escape, and Line is its line number in the file, the _HiStOrY_V2_ line being line 1. File "
                 "Format is decided once per file, so it holds one value on every row from a file, and on each "
                 "tested image it held one value on every row. The file records no times. Readers compared on "
                 "generated files: GNU readline 8.3's own reader, through the readline module of the lab VM's "
                 "Python, read 300 plain files with carriage returns, empty lines, # lines with and without a "
                 "timestamp start, invalid UTF-8 and missing final newlines, and returned the same 1,362 entries "
                 "as the artifact, apart from the 113 unterminated last lines readline does not load; libedit's "
                 "reader on the Mac (/usr/lib/libedit.3.dylib, which Apple's /usr/bin/sqlite3 links), through "
                 "Apple's Python 3.9.6, read 300 files that libedit's own writer wrote, with empty lines, carriage "
                 "returns and missing final newlines added, and returned the same 1,149 entries as the artifact "
                 "apart from 68 empty ones, and refused 16 files that held only the _HiStOrY_V2_ line, for which "
                 "the artifact reports no row. On ubuntu2604_arm64_sqlitehist there are 2000 rows, all plain, the "
                 "lines the file held after its sixth step. On sqlite_history_known_macos there are 8 rows, all "
                 "libedit, from two sessions of Apple's sqlite3 3.54.0: its file stored a space as \\040, a "
                 "backslash as \\134 and é and ü as their UTF-8 bytes, and did not keep the empty line typed. No "
                 "member of the other twenty-seven tested images matches the declared paths.",
        "paths": ("*/.sqlite_history",),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 build 26A434, sqlite3 3.54.0 | 8 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                            "paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64, sqlite3 3.46.1 | 2000 rows",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.libedit_history import LIBEDIT_COOKIE, unvis

UNDECODED = 'libedit lines holding an escape its decoder rejects, reported undecoded'
EMPTY = 'empty lines, which are no entry'
UNTERMINATED = 'last lines with no newline after them, which GNU readline does not load, reported'
TIMESTAMPS = 'timestamp lines (#<digits>), which GNU readline reads as times and not entries, not reported'


def history_lines(data, counts):
    """(file format, lines) for the bytes of a .sqlite_history file, each line (text, line number) in file order.

    The format is 'libedit' when the first line is exactly libedit's _HiStOrY_V2_ cookie: every later line is an
    entry, decoded as libedit decodes it. Otherwise it is 'plain', read as GNU readline reads a history file: lines
    end at a newline, a carriage return before it is dropped, and when the file begins with # and a digit, a line
    that does is a timestamp rather than an entry. An empty line is no entry in either format."""
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
        unterminated = False
    else:
        unterminated = bool(lines)
    if lines and lines[0] == LIBEDIT_COOKIE:
        out = []
        for index, raw in enumerate(lines[1:], 2):
            decoded = unvis(raw)
            if decoded is None:
                counts[UNDECODED] += 1
            else:
                raw = decoded
            if raw == b'':
                counts[EMPTY] += 1
                continue
            out.append((raw.decode('utf-8', errors='backslashreplace'), index))
        return 'libedit', out
    timestamped = len(data) > 1 and data[:1] == b'#' and data[1:2].isdigit()
    out = []
    for index, raw in enumerate(lines, 1):
        if raw.endswith(b'\r') and not (unterminated and index == len(lines)):
            raw = raw[:-1]
        if raw == b'':
            counts[EMPTY] += 1
            continue
        if timestamped and raw[:1] == b'#' and raw[1:2].isdigit():
            counts[TIMESTAMPS] += 1
            continue
        if unterminated and index == len(lines):
            counts[UNTERMINATED] += 1
        out.append((raw.decode('utf-8', errors='backslashreplace'), index))
    return 'plain', out


@artifact_processor
def sqliteShellHistory(context):
    data_headers = ('Entry', 'Line', 'File Format', 'Source File')
    data_list = []
    read = []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        form, lines = history_lines(data, counts)
        relative = context.get_relative_path(path)
        data_list.extend((text, number, form, relative) for text, number in lines)
        if lines:
            read.append(path)
    if counts:
        logfunc('SQLite Shell History: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
