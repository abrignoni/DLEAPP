"""Searches, shell commands and saved marks in the history file of the less pager (.lesshst or lesshst), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "lessHistory": {
        "name": "less History",
        "description": "Searches and shell or pipe commands saved in the history file of the less pager, in the "
                       "order the file holds them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Command Line (less)",
        "notes": "Reads the history file of the less pager at the places less 668 looks by default: lesshst in "
                 ".local/state in the home folder, lesshst in the folder $XDG_DATA_HOME names, and .lesshst in the "
                 "home folder. less uses the first of these that exists, and makes a new file in .local/state when "
                 "that folder exists and otherwise in the home folder (Reference: less 668, 'cmdbuf.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1363-L1388 "
                 "and "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1390-L1416; "
                 "'configure.ac', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/configure.ac#L588). "
                 "The artifact reads those names, taking .local/share, the usual value of $XDG_DATA_HOME, for the "
                 "second. less tries $XDG_STATE_HOME first when it is set, and $LESSHISTFILE names any other file; "
                 "a file kept that way, and the _lesshst a native Windows build of less writes ('defines.ds', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/defines.ds#L132), is "
                 "not read. The .local/state location is new from the v598 tag of less "
                 "(https://github.com/gwsw/less/blob/fee1cc0394b0231c071d3cab51e26b0ce39f24c3/cmdbuf.c#L1411-L1419); "
                 "before it, less tried $XDG_DATA_HOME and then the home folder "
                 "(https://github.com/gwsw/less/blob/88c9136d3e89238e0e56a3acb8b05d6ba2bc859d/cmdbuf.c#L1426-L1444). "
                 "less writes the file with the first line .less-history-file:, then section headers and their "
                 "lines "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L61-L64), "
                 "and reads back a line starting with a double quote as an entry of the .search or .shell header "
                 "above it and a line starting with m as a mark "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1423-L1488). "
                 "The artifact reads the file the same way: a file whose first line is not .less-history-file: is "
                 "not read, an entry before any header or under .mark is passed over, and an empty entry, which "
                 "less keeps in the file but does not load into its history "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L732-L770), "
                 "is not reported; all three are counted in the run log. The file stores no time. less rewrites "
                 "the file when it quits if a search, a command or a mark changed during the session "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/main.c#L571-L602, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1630-L1643, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1647-L1700): "
                 "it copies the entries already there, adds the session's new ones at the end of their section, or "
                 "under a second header when that section was the last in the file "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1569-L1600), "
                 "and keeps the newest 100 of each section unless $LESSHISTSIZE sets another number "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1669-L1675), "
                 "which was read in the source and not exercised. The artifact's reading was compared with less's "
                 "own on the Mac: 300 generated history files, 2,538 lines holding 243 entries and 595 marks the "
                 "artifact reads, were each opened with /usr/bin/less 668 --save-marks with one search and one "
                 "mark added, so that less wrote back what it had read, and on every file the search entries, the "
                 "shell entries and each mark's letter, byte position and file were the ones the artifact reads. "
                 "Rows are in the order the file holds them, and Line is the line of the file an entry is on. Kind "
                 "is Search for the .search section, the patterns typed after / or ? ('command.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/command.c#L200-L204), "
                 "and Shell or pipe command for the .shell section, the commands typed after !, after # and after "
                 "| and a mark "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/command.c#L1892, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/command.c#L2074, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/command.c#L2137); # "
                 "was not exercised. A session does not add a line equal to the last one in its list "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L732-L770), "
                 "so the same text can appear more than once, as the first search does on ubuntu2604_arm64_lesshst "
                 "after a later session typed it again. An entry is the text typed at the prompt: the file does "
                 "not record which file was open, when, or what a command printed. Source File is the file a row "
                 "comes from, and the report's located-at line names the files that held a row; a file that cannot "
                 "be read is counted in the run log and not reported. On ubuntu2604_arm64_lesshst, captured from a "
                 "VM running less 668, the 5 rows are the searches and commands of three known sessions in the "
                 "order the file holds them: the two searches of the first two sessions and the third session's "
                 "repeat of the first, the shell command of the first session, and the third session's pipe "
                 "command, which less wrote under a second .shell header. On less_history_known_macos, made with "
                 "/usr/bin/less 668 on macOS in a home folder with no .local/state, the file is .lesshst and the 2 "
                 "rows are its search and its shell command. No member of the other twenty-two tested images "
                 "matches the declared paths.",
        "paths": ("*/.lesshst", "*/.local/state/lesshst", "*/.local/share/lesshst"),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434, less 668 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64, less 668 | 5 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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
    "lessMarks": {
        "name": "less Marks",
        "description": "Marks saved in the history file of the less pager, each with the file it names and a byte "
                       "position in that file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Command Line (less)",
        "notes": "Reads the history file of the less pager at the places less 668 looks by default: lesshst in "
                 ".local/state in the home folder, lesshst in the folder $XDG_DATA_HOME names, and .lesshst in the "
                 "home folder. less uses the first of these that exists, and makes a new file in .local/state when "
                 "that folder exists and otherwise in the home folder (Reference: less 668, 'cmdbuf.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1363-L1388 "
                 "and "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1390-L1416; "
                 "'configure.ac', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/configure.ac#L588). "
                 "The artifact reads those names, taking .local/share, the usual value of $XDG_DATA_HOME, for the "
                 "second. less tries $XDG_STATE_HOME first when it is set, and $LESSHISTFILE names any other file; "
                 "a file kept that way, and the _lesshst a native Windows build of less writes ('defines.ds', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/defines.ds#L132), is "
                 "not read. The .local/state location is new from the v598 tag of less "
                 "(https://github.com/gwsw/less/blob/fee1cc0394b0231c071d3cab51e26b0ce39f24c3/cmdbuf.c#L1411-L1419); "
                 "before it, less tried $XDG_DATA_HOME and then the home folder "
                 "(https://github.com/gwsw/less/blob/88c9136d3e89238e0e56a3acb8b05d6ba2bc859d/cmdbuf.c#L1426-L1444). "
                 "less writes the file with the first line .less-history-file:, then section headers and their "
                 "lines "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L61-L64), "
                 "and reads back a line starting with a double quote as an entry of the .search or .shell header "
                 "above it and a line starting with m as a mark "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L1423-L1488). "
                 "The artifact reads the file the same way: a file whose first line is not .less-history-file: is "
                 "not read, an entry before any header or under .mark is passed over, and an empty entry, which "
                 "less keeps in the file but does not load into its history "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/cmdbuf.c#L732-L770), "
                 "is not reported; all three are counted in the run log. The file stores no time. less writes its "
                 "marks only in a session run with the --save-marks option ('opttbl.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/opttbl.c#L156; "
                 "'mark.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/mark.c#L369-L392): "
                 "one line per mark, m then the letter, the screen line, the byte position and the file's path. A "
                 "later session run without that option that changes the history rewrites the file with no marks "
                 "at all, which on ubuntu2604_arm64_lesshst removed marks a and b. Marks first appear in the "
                 "history file at the v546 tag of less "
                 "(https://github.com/gwsw/less/blob/128c1dfe9d01ca7c9007fcc1cc212ee9dc210e9c/cmdbuf.c#L56). Mark "
                 "is the letter: a to z and A to Z are marks set with m "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/mark.c#L107-L121, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/command.c#L2093, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/mark.c#L196-L212), # "
                 "is the mouse mark, which was not exercised, and ' is the position before the last jump, which "
                 "less also sets when it closes the file on quitting "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/mark.c#L236-L247, "
                 "'jump.c', https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/jump.c#L49, "
                 "'edit.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/edit.c#L351-L368, "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/main.c#L571-L602). "
                 "Byte Position is the byte offset in the file of the line at the top of the screen when the mark "
                 "was set, and Screen Line the row that line was on, as stored. When less reads a mark back it "
                 "limits the screen line to the screen's height "
                 "(https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/mark.c#L397-L425), "
                 "and since it reads marks before it knows that height, it rewrote every mark it had read back "
                 "with screen line 0 in the comparison described below, 453 marks in all. File is the path less "
                 "had for the file, as stored; a mark on standard input is not written. A mark shows that the file "
                 "was open in less with --save-marks; the file does not record when. The artifact reads a mark "
                 "line as less does: a letter other than those, or a number too large for less, is not read back "
                 "and is counted in the run log, and a number with no digits reads as 0 ('output.c', "
                 "https://github.com/gwsw/less/blob/e77e1176c80cca989694818866ae6cd7e7707161/output.c#L543-L567). "
                 "Rows are in the order the file holds them, and Line is the line of the file a mark is on. Source "
                 "File is the file a row comes from, and the report's located-at line names the files that held a "
                 "row. The artifact's reading was compared with less's own on the Mac: 300 generated history "
                 "files, 2,538 lines holding 243 entries and 595 marks the artifact reads, were each opened with "
                 "/usr/bin/less 668 --save-marks with one search and one mark added, so that less wrote back what "
                 "it had read, and on every file the search entries, the shell entries and each mark's letter, "
                 "byte position and file were the ones the artifact reads. On ubuntu2604_arm64_lesshst, captured "
                 "from a VM running less 668 after three known sessions, the 1 row is the ' mark of the third "
                 "session, at byte 784, the start of line 50 of the viewed file, where the view stood when less "
                 "closed it; the first session's marks a, b and ' were at bytes 1594 and 2862, the starts of lines "
                 "100 and 178, and the second session, run without --save-marks, removed them. On "
                 "less_history_known_macos the 2 rows are mark c and ', both at byte 1513, the start of line 90 of "
                 "the viewed file, whose path is the scratch folder's absolute path on the Mac. No member of the "
                 "other twenty-two tested images matches the declared paths.",
        "paths": ("*/.lesshst", "*/.local/state/lesshst", "*/.local/share/lesshst"),
        "output_types": "standard",
        "artifact_icon": "bookmark",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 build 26A434, less 668 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 build 26A434 | 0 rows (no member matches the declared "
                                          "paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64, less 668 | 1 rows",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
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

FIRST_LINE = '.less-history-file:'
SECTIONS = {'.search': 'Search', '.shell': 'Shell or pipe command', '.mark': None}
MARK_LETTERS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\'#')
INT_MAX, POSITION_MAX = 2 ** 31 - 1, 2 ** 63 - 1


def _number(text, at, limit):
    """(value, index after it) for the decimal digits at text[at:], as less reads them: no digits read as 0, and
    None when the value passes limit."""
    end = at
    while end < len(text) and text[end] in '0123456789':
        end += 1
    value = int(text[at:end]) if end > at else 0
    return (None if value > limit else value), end


def parse_mark(text):
    """(letter, screen line, byte position, file) for a mark line as less reads it back, or None when less would
    not restore it: an unknown letter, or a number that does not fit."""
    at = 1
    while at < len(text) and text[at] == ' ':
        at += 1
    if at >= len(text) or text[at] not in MARK_LETTERS:
        return None
    letter = text[at]
    at += 1
    while at < len(text) and text[at] == ' ':
        at += 1
    screen_line, at = _number(text, at, INT_MAX)
    while at < len(text) and text[at] == ' ':
        at += 1
    position, at = _number(text, at, POSITION_MAX)
    while at < len(text) and text[at] == ' ':
        at += 1
    if screen_line is None or position is None:
        return None
    return letter, screen_line, position, text[at:]


def history_lines(data, counts):
    """The lines of a less history file after its first line, each (line number, text), cut at the first line end
    or carriage return as less cuts them; None when the file does not begin with less's first line."""
    lines = data.split(b'\n')
    if not lines[0].decode('utf-8', errors='replace').startswith(FIRST_LINE):
        counts['files that do not begin with .less-history-file:, not read'] += 1
        return None
    out = []
    for number, raw in enumerate(lines[1:], 2):
        text = raw.decode('utf-8', errors='backslashreplace').split('\r', 1)[0]
        out.append((number, text))
    return out


def history_rows(data, counts):
    """(entries, marks) for the bytes of a less history file, in file order. An entry is (kind, text, line number)
    for a line starting with a double quote inside a .search or .shell section; a mark is (letter, file, byte
    position, screen line, line number) for a line starting with m that less can read back."""
    lines = history_lines(data, counts)
    if lines is None:
        return None
    entries, marks = [], []
    kind, in_section = None, False
    for number, text in lines:
        if text in SECTIONS:
            kind, in_section = SECTIONS[text], text != '.mark'
            continue
        if text.startswith('"'):
            if in_section and text == '"':
                counts['empty entries, which less does not load, not reported'] += 1
            elif in_section:
                entries.append((kind, text[1:], number))
            else:
                counts['entries outside a .search or .shell section, not reported'] += 1
        elif text.startswith('m'):
            mark = parse_mark(text)
            if mark:
                letter, screen_line, position, filename = mark
                marks.append((letter, filename, position, screen_line, number))
            else:
                counts['mark lines less cannot read back, not reported'] += 1
        elif text:
            counts['other lines, passed over'] += 1
    return entries, marks


def _read(context, problems):
    """[(path, entries, marks)] for each history file found, in path order."""
    out = []
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = history_rows(data, problems)
        if rows is not None:
            out.append((path, rows[0], rows[1]))
    return out


def _log(name, problems):
    if problems:
        logfunc(f'{name}: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))


@artifact_processor
def lessHistory(context):
    data_headers = ('Entry', 'Kind', 'Line', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path, entries, _marks in _read(context, problems):
        relative = context.get_relative_path(path)
        data_list.extend((text, kind, number, relative) for kind, text, number in entries)
        if entries:
            read.append(path)
    _log('less History', problems)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def lessMarks(context):
    data_headers = ('Mark', 'File', 'Byte Position', 'Screen Line', 'Line', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path, _entries, marks in _read(context, problems):
        relative = context.get_relative_path(path)
        data_list.extend((letter, filename, position, screen, number, relative)
                         for letter, filename, position, screen, number in marks)
        if marks:
            read.append(path)
    _log('less Marks', problems)
    return data_headers, data_list, '\n'.join(read)
