"""Entries in the history file of Python's interactive interpreter (.python_history), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "pythonReplHistory": {
        "name": "Python REPL History",
        "description": "Entries in the history file of Python's interactive interpreter (.python_history), in the "
                       "order the file holds them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Command Line (Python)",
        "notes": "Reads each .python_history file the paths match, the file Python's interactive interpreter keeps "
                 "in the home folder unless the PYTHON_HISTORY environment variable names another (Reference: "
                 "CPython 3.14.4, 'Lib/site.py', "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/site.py#L474-L484); "
                 "a history file kept under another name is not read. The file stores no time for any entry. Rows "
                 "are in the order the file holds them. First Line and Last Line are the lines of the file an "
                 "entry occupies, the same line for an entry on one line, which on python_history_known_macos is "
                 "every row, since the interpreter that wrote it stored each line typed as its own entry. Python "
                 "3.13 and later start the new interpreter unless PYTHON_BASIC_REPL is set or it cannot run, and "
                 "otherwise the basic one, which uses the readline module; either reads the file when it starts "
                 "and writes its history back to it at exit, replacing what it held (3.14.4, "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/site.py#L520-L521 "
                 "and "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/site.py#L565-L592; "
                 "3.13.0, "
                 "https://github.com/python/cpython/blob/60403a5409ff2c3f3b07dd2ca91a7a3e096839c7/Lib/site.py#L528-L545). "
                 "From 3.14.0b1 the new interpreter also appends each statement to the file after running it "
                 "('Lib/_pyrepl/simple_interact.py', "
                 "https://github.com/python/cpython/blob/b092705907c758d4f9742028652c9802f9f03dd3/Lib/_pyrepl/simple_interact.py#L146-L149; "
                 "3.14.4, "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/simple_interact.py#L151-L155); "
                 "the 3.13 releases checked, 3.13.0 to 3.13.13, do not. The new interpreter leaves bare commands "
                 "such as exit and quit out of its history "
                 "(https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/simple_interact.py#L72-L79, "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/simple_interact.py#L124), "
                 "which was read in the source and not exercised. The new interpreter writes a statement that "
                 "spans several lines with a carriage return at the end of each line but the last "
                 "('Lib/_pyrepl/readline.py', 3.13.0, "
                 "https://github.com/python/cpython/blob/60403a5409ff2c3f3b07dd2ca91a7a3e096839c7/Lib/_pyrepl/readline.py#L455; "
                 "3.14.4, "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/readline.py#L464 "
                 "and "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/readline.py#L476) "
                 "and joins those lines back into one entry when it reads the file "
                 "(https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/readline.py#L428-L455); "
                 "the artifact joins them the same way, and on ubuntu2604_arm64_pyhistory its entries equal, one "
                 "for one, the ones that reader returns for the file. GNU Readline, which the basic interpreter "
                 "uses on Linux, drops a carriage return before a line end when it reads a history file (GNU "
                 "Readline 8.3, histfile.c lines 420 to 424, "
                 "https://ftp.gnu.org/gnu/readline/readline-8.3.tar.gz), so a session of the basic interpreter "
                 "writes such a statement back as one entry per line. An empty line is no entry, nor is a "
                 "statement whose lines are all empty, and both are counted in the run log; a file that ends "
                 "inside a statement, its last line ending in a carriage return, gives that statement a row and is "
                 "counted there, which was tested with constructed input only. A file whose first line is "
                 "_HiStOrY_V2_, the line libedit writes first "
                 "(https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L54, "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L846), "
                 "is read as libedit writes it, every line after that one included, and File Format is libedit for "
                 "it and plain for any other, one value on every row from a file. libedit encodes each entry with "
                 "strvis "
                 "(https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L874), "
                 "and decodes it with strunvis when it reads "
                 "(https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libedit/history.c#L813); "
                 "the artifact decodes each line as strunvis does, with no flags ('lib/libc/gen/unvis.c', "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libc/gen/unvis.c#L549-L552, "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libc/gen/unvis.c#L210-L221, "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libc/gen/unvis.c#L247-L396), "
                 "and reads the rest as UTF-8. On 9,000 generated lines using each escape form that decoder "
                 "accepts, all of them decoding to ASCII text, the artifact and libedit's reader on the Mac "
                 "returned the same text for every line except the 1,601 that end in an octal escape of 1 or 2 "
                 "digits or a hex escape of 1 digit, which that reader dropped while the artifact keeps it, as "
                 "NetBSD's decoder does; strvis with libedit's flag writes an octal escape as three digits and no "
                 "hex escape ('lib/libc/gen/vis.c', "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libc/gen/vis.c#L268-L272, "
                 "https://github.com/NetBSD/src/blob/c84b9c2ea07d89d66f769e02700ef985e99cf271/lib/libc/gen/vis.c#L340-L347). "
                 "A line holding a sequence the decoder rejects is reported undecoded and counted in the run log, "
                 "which was tested with constructed input only. On python_history_known_macos, written by the "
                 "Command Line Tools' Python 3.9.6, whose readline module links libedit, spaces were stored as "
                 "\\040, backslashes as \\134 and é as its two UTF-8 bytes, and the artifact's 6 entries equal, one "
                 "for one, the ones that Python's readline module returned when it read the file on the Mac. The "
                 "new interpreter of Python 3.13 and later reads a libedit file with the unicode-escape codec "
                 "(3.13.0, "
                 "https://github.com/python/cpython/blob/60403a5409ff2c3f3b07dd2ca91a7a3e096839c7/Lib/_pyrepl/readline.py#L430-L432; "
                 "3.14.4, "
                 "https://github.com/python/cpython/blob/23116f998f6789d8c2fbe5ed5b8146854c8c2a4f/Lib/_pyrepl/readline.py#L436-L438), "
                 "and Python 3.14's reader returned the é in that file as two other characters; the artifact does "
                 "not follow that reading. Bytes that are not UTF-8 are shown as backslash escapes such as \\xe9, "
                 "tested with constructed input only. A row holding only spaces is as stored; in the known data "
                 "those rows are the empty line typed to close an indented block, on which the new interpreter had "
                 "put 4 spaces of indentation. An entry is the text entered at the prompt as the interpreter "
                 "stored it: the file does not record whether it ran without error, what it printed, or who typed "
                 "it. Source File is the file a row comes from, and the report's located-at line names the files "
                 "that held a row; a file that cannot be read is counted in the run log and not reported. On "
                 "ubuntu2604_arm64_pyhistory, captured from a VM running Python 3.14.4 and GNU Readline 8.3, the "
                 "file's 16 lines are the 16 lines typed in five sessions, in 14 rows: after each session of the "
                 "new interpreter every statement typed so far was in the file, a block as one entry; one session "
                 "of the basic interpreter rewrote the two blocks typed before it as one entry per line, and the "
                 "class block typed after it is one row; and the two statements of the last session were in the "
                 "file while its interpreter still ran, and killing it with SIGKILL left the file unchanged. On "
                 "python_history_known_macos the 6 rows are the 6 lines typed that were not empty, each its own "
                 "entry, a tab typed in one of them having gone to completion rather than into the line; the empty "
                 "line that closed the block was not kept. No member of the other twenty tested images matches the "
                 "declared paths.",
        "paths": ("*/.python_history",),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434, Python 3.9.6 | 6 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64, Python 3.14.4 | 14 rows",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared "
                                           "paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

LIBEDIT_COOKIE = b'_HiStOrY_V2_'
_SIMPLE = {ord('n'): 10, ord('r'): 13, ord('b'): 8, ord('a'): 7, ord('v'): 11, ord('t'): 9, ord('f'): 12,
           ord('s'): 32, ord('E'): 27}
_OCTAL = b'01234567'
_HEX = b'0123456789abcdefABCDEF'


def unvis(line):
    """A libedit history line decoded as its reader decodes it, with strunvis: unvis() with no flags, applied byte by
    byte (NetBSD lib/libc/gen/unvis.c). None when the line holds a sequence that decoder rejects."""
    out = bytearray()
    state, cur, i = 'ground', 0, 0
    while i < len(line):
        c = line[i]
        i += 1
        if state == 'ground':
            if c == 0x5C:
                state, cur = 'start', 0
            else:
                out.append(c)
        elif state == 'start':
            state = 'ground'
            if c == 0x5C:
                out.append(c)
            elif c in _OCTAL:
                cur, state = c - 0x30, 'octal2'
            elif c == ord('M'):
                cur, state = 0o200, 'meta'
            elif c == ord('^'):
                state = 'ctrl'
            elif c in _SIMPLE:
                out.append(_SIMPLE[c])
            elif c == ord('x'):
                state = 'hex'
            elif c in (0x0A, ord('$')):
                pass
            elif 0x21 <= c <= 0x7E:
                out.append(c)
            else:
                return None
        elif state == 'meta':
            if c == ord('-'):
                state = 'meta1'
            elif c == ord('^'):
                state = 'ctrl'
            else:
                return None
        elif state == 'meta1':
            out.append(cur | c)
            state = 'ground'
        elif state == 'ctrl':
            out.append((cur | 0o177) if c == ord('?') else (cur | (c & 0o37)) & 0xFF)
            state = 'ground'
        elif state in ('octal2', 'octal3'):
            if c in _OCTAL:
                cur = ((cur << 3) + c - 0x30) & 0xFF
                if state == 'octal3':
                    out.append(cur)
                    state = 'ground'
                else:
                    state = 'octal3'
            else:
                out.append(cur)
                state = 'ground'
                i -= 1
        elif state == 'hex':
            if c not in _HEX:
                return None
            cur, state = int(chr(c), 16), 'hex2'
        elif state == 'hex2':
            state = 'ground'
            if c in _HEX:
                out.append((cur << 4) | int(chr(c), 16))
            else:
                out.append(cur)
                i -= 1
    if state in ('octal2', 'octal3', 'hex2'):
        out.append(cur)
    return bytes(out)


def history_entries(data, counts):
    """(file format, entries) for the bytes of a .python_history file, each entry (text, first line, last line) in
    file order. The format is 'libedit' for a file whose first line is libedit's _HiStOrY_V2_ cookie, whose lines are
    decoded from its escapes, and 'plain' for any other. A line ending in a carriage return continues into the next
    line, as Python's own reader joins it; an empty line is no entry."""
    lines = data.split(b'\n')
    form = 'plain'
    first = 1
    if lines and lines[0].startswith(LIBEDIT_COOKIE):
        form, first = 'libedit', 2
        lines = lines[1:]
    entries, pending = [], []
    last = len(lines) - 1
    for index, raw in enumerate(lines):
        number = index + first
        if form == 'libedit':
            decoded = unvis(raw)
            if decoded is None:
                counts['libedit lines holding an escape its decoder rejects, reported undecoded'] += 1
            else:
                raw = decoded
        text = raw.decode('utf-8', errors='backslashreplace')
        if text.endswith('\r'):
            pending.append((number, text[:-1]))
            continue
        if pending:
            joined = ('\n'.join(t for _n, t in pending) + '\n' + text).rstrip('\n')
            end = pending[-1][0] if index == last and text == '' else number
            if joined:
                entries.append((joined, pending[0][0], end))
            else:
                counts['continued entries with no text, which are no entry'] += 1
            pending = []
            continue
        if text == '':
            if index != last:
                counts['empty lines, which are no entry'] += 1
            continue
        entries.append((text, number, number))
    if pending:
        joined = '\n'.join(t for _n, t in pending).rstrip('\n')
        counts['entries whose last line ends in a carriage return at the end of the file'] += 1
        if joined:
            entries.append((joined, pending[0][0], pending[-1][0]))
        else:
            counts['continued entries with no text, which are no entry'] += 1
    return form, entries


@artifact_processor
def pythonReplHistory(context):
    data_headers = ('Entry', 'First Line', 'Last Line', 'File Format', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        form, entries = history_entries(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend((text, first, last, form, relative) for text, first, last in entries)
        if entries:
            read.append(path)
    if problems:
        logfunc('Python REPL History: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
