"""PowerShell PSReadLine command history parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

PSReadLine, the line editor PowerShell uses at an interactive prompt, saves the
commands typed there to a text file per user and per PowerShell host, by default
AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\<host name>_history.txt.
Each command is one line; a command spanning several lines is saved with a backtick
ending every line but its last, and this reader joins those lines the way PSReadLine
does when it loads the file.
"""

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc

_LINE_BREAK = re.compile(r'\r\n|\r|\n')
_HISTORY_SUFFIX = '_history.txt'
_PSREADLINE_FOLDER = '/appdata/roaming/microsoft/windows/powershell/psreadline/'

__artifacts_v2__ = {
    "psReadLineHistory": {
        "name": "PowerShell PSReadLine History",
        "description": "Commands saved to PowerShell's PSReadLine history file, one row "
                       "per command with the line of the file where it begins, the "
                       "PowerShell host and the profile folder the file belongs to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\"
                 "<host name>_history.txt, the path PSReadLine builds on Windows from the "
                 "roaming application data folder and the name of the PowerShell host, or "
                 "PSReadLine when no host name is found (PSReadLine 2.0.0, "
                 "https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/Cmdlets.cs#L159-L168, "
                 "https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/ReadLine.cs#L647-L666). "
                 "Host is that name, taken from the file name, and Profile Folder is the "
                 "part of the file's path before AppData; together they identify the file. "
                 "Host held ConsoleHost on every row of the tested images, and Profile Folder "
                 "held one value on every row of each tested image, because each held one "
                 "history file. PSReadLine "
                 "writes each command as one line and ends every line but the last of a "
                 "command spanning several lines with a backtick "
                 "(https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L342-L343), "
                 "and joins such lines when it reads the file back "
                 "(https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L412-L424). "
                 "This artifact joins them the same way, so Command can hold several lines, "
                 "and Line Number is the line of the file where the command begins. No "
                 "command on the tested images spanned more than one line. A line holding "
                 "only white space outside such a command is not reported. The file "
                 "stores the command text and nothing else, so no row carries a time. With "
                 "PSReadLine's default save style, SaveIncrementally "
                 "(https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/Cmdlets.cs#L129), "
                 "each command is appended to the file when PSReadLine adds it to its "
                 "history (https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L213-L216), which it does for a command accepted "
                 "at the prompt (https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/ReadLine.cs#L485-L487) or passed to its AddToHistory "
                 "method (https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L446-L451); the save style is a user setting and "
                 "this artifact does not read it. The file is not a complete record of what "
                 "was typed. By default PSReadLine does not add a command identical to the "
                 "one before it (https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L132-L137, https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/Cmdlets.cs#L277), it never "
                 "adds one holding only white space (https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L126-L130), and from "
                 "2.0.0 its default handler keeps out of the file any command matching "
                 "password, asplaintext, token, key or secret, compared without case "
                 "(https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L114-L115, https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L340, https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/History.cs#L435-L440). "
                 "PSReadLine 2.1.0 matches apikey in place of key "
                 "(https://github.com/PowerShell/PSReadLine/blob/3856776b1d215873a51ab0d0fe0f9a91f6ac2d67/PSReadLine/History.cs#L115), "
                 "and from 2.2.2 it parses a matching command and saves some of them, such as "
                 "one passing a variable as a parameter's value "
                 "(https://github.com/PowerShell/PSReadLine/blob/878a0743c82dde3f9d28c9045082b573c3173960/PSReadLine/History.cs#L555-L668). "
                 "PSReadLine 1.2 has no such filter "
                 "(https://github.com/PowerShell/PSReadLine/blob/38eb016b0a942dde0ab0b2f71f51944b56b05af4/PSReadLine/History.cs). "
                 "A command's absence from the file therefore does not establish that it "
                 "was never typed, and a script's own lines are not written here, because "
                 "only commands accepted at the prompt or passed to AddToHistory are added. "
                 "On af_case2_win10 the one history file held 11 commands, all distinct, "
                 "and on pc_mus_001_win11 it held 24 commands, 14 of them distinct; "
                 "lonewolf_win10 holds no PSReadLine history file. "
                 "Not read: the location PSReadLine uses on macOS and Linux, "
                 ".local/share/powershell/PSReadLine or the same folder under XDG_DATA_HOME "
                 "(https://github.com/PowerShell/PSReadLine/blob/6b5e9ff4bdfe15f67b3647e0d1ecdb6cf2e3bda6/PSReadLine/Cmdlets.cs#L170-L204), "
                 "PowerShell transcripts, and the PowerShell event logs, which the "
                 "PowerShell event artifacts read.",
        "paths": ('*/AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/*_history.txt',),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 11 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 24 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no PSReadLine history file)",
        },
    },
}


def decode_history(data):
    """Text of a history file: UTF-8 (PSReadLine's encoding), or UTF-16 by its mark."""
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16', errors='replace')
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    return data.decode('utf-8', errors='replace')


def read_history(text):
    """Commands in a history file's text, as (line number, command, lines) tuples.

    A line ending in a backtick continues on the next line, as PSReadLine reads it. A
    command whose last line still ends in a backtick at the end of the file is kept as
    it stands. A line holding only white space outside a command is dropped, as
    PSReadLine drops it.
    """
    lines = _LINE_BREAK.split(text)
    if lines and lines[-1] == '':
        lines.pop()
    commands = []
    pending = []
    start = 0
    for number, line in enumerate(lines, start=1):
        if not pending:
            start = number
        if line.endswith('`'):
            pending.append(line[:-1])
            continue
        if pending:
            pending.append(line)
            commands.append((start, '\n'.join(pending), len(pending)))
            pending = []
            continue
        if line.strip():
            commands.append((start, line, 1))
    if pending:
        # The file ended inside a command: keep its last backtick, as the file has it.
        commands.append((start, '\n'.join(pending) + '`', len(pending)))
    return commands


def host_name(file_name):
    """The PowerShell host name a history file is named after, or the file name."""
    if file_name.lower().endswith(_HISTORY_SUFFIX):
        return file_name[:-len(_HISTORY_SUFFIX)]
    return file_name


def profile_folder(relative_path):
    """The part of a history file's path before AppData, or the file's folder."""
    path = relative_path.replace('\\', '/')
    at = path.lower().find(_PSREADLINE_FOLDER)
    if at >= 0:
        return path[:at]
    return os.path.dirname(path)


@artifact_processor
def psReadLineHistory(context):
    data_headers = ('Line Number', 'Command', 'Host', 'Profile Folder')
    data_list = []
    sources = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isdir(source) or not source.lower().endswith(_HISTORY_SUFFIX):
            continue
        relative_source = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                text = decode_history(handle.read())
        except OSError as exc:
            logfunc(f'PowerShell PSReadLine History: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        host = host_name(os.path.basename(source))
        profile = profile_folder(relative_source)
        commands = read_history(text)
        for line_number, command, _ in commands:
            data_list.append((line_number, command, host, profile))
        joined = sum(1 for _, _, count in commands if count > 1)
        logfunc(f'PowerShell PSReadLine History: {len(commands)} commands read from '
                f'{relative_source} ({joined} spanning more than one line)')
    return data_headers, data_list, '\n'.join(sources)
