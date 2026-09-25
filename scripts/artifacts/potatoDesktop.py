"""Potato Desktop (a Telegram Desktop fork) application info, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "potatoDesktopAppInfo": {
        "name": "Potato Desktop Application Info",
        "description": "Potato Desktop version, update channel, launch time and paths read "
                       "from the app's own log.txt, one row per log file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-09-25",
        "requirements": "none",
        "category": "Potato Desktop",
        "notes": "Potato Desktop is a fork of Telegram Desktop and writes the same style of "
                 "log.txt. One row per log.txt found. Version and Numeric Version are the "
                 "'set version to' and 'Launched version:' values on the launch line; Update "
                 "Channel is the 'update channel=' value on that line. Log Time is the "
                 "timestamp the log writes on its first line, as written; the log records a "
                 "device-local wall-clock time with no timezone, so it is reported as text and "
                 "not converted. Executable Directory, Executable Name and Working Directory "
                 "are the 'Executable dir:', name and 'Working dir:' values. Previous Launch "
                 "Unfinished is Yes when the log records that the previous launch was not "
                 "finished properly, with Crash Log Size the size it reports; that line is a "
                 "statement by the app about the prior run, not the current one. Each value is "
                 "blank when its line is absent. The log does not carry message content; the "
                 "encrypted pdata store is not read here. Only the macOS location was tested; "
                 "the pattern also matches other platforms' Potato Desktop folders, untested. "
                 "Public regression cases are independently authored synthetic data; local "
                 "private validation details are not published.",
        "paths": ('*/Potato Desktop/log.txt',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "info-circle",
        "sample_data": {},
    },
}

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc


def _first(pattern, text, group=1):
    match = re.search(pattern, text)
    return match.group(group).strip() if match else ''


@artifact_processor
def potatoDesktopAppInfo(context):
    data_headers = ('Log Time', 'Version', 'Numeric Version', 'Update Channel',
                    'Executable Directory', 'Executable Name', 'Working Directory',
                    'Previous Launch Unfinished', 'Crash Log Size', 'Source File')
    data_list = []
    read = []
    for path in context.get_files_found():
        path = str(path)
        if os.path.basename(path) != 'log.txt' or os.path.isdir(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as handle:
                text = handle.read()
        except OSError as exc:
            logfunc(f'Potato Desktop Application Info: could not read '
                    f'{context.get_relative_path(path)}: {exc}')
            continue
        relative = context.get_relative_path(path)
        unfinished = 'not finished properly' in text
        data_list.append((
            _first(r'^\[([0-9. :]+)\]', text),
            _first(r'set version to ([^\s,]+)', text),
            _first(r'Launched version:\s*(\d+)', text),
            _first(r'update channel=(\w+)', text),
            _first(r'Executable dir:\s*([^,\n]+)', text),
            _first(r'Executable dir:[^,]*,\s*name:\s*([^\n]+)', text),
            _first(r'Working dir:\s*([^\n]+)', text),
            'Yes' if unfinished else 'No',
            _first(r'Crash log size:\s*(\d+)', text) if unfinished else '',
            relative))
        read.append(path)
    return data_headers, data_list, '\n'.join(read)
