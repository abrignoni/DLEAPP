"""Launch agents and daemons outside the folders macOS itself ships, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosLaunchItems": {
        "name": "Launch Agents and Daemons",
        "description": "Property lists in the Library/LaunchAgents and Library/LaunchDaemons folders "
                       "outside /System/Library and /Library/Apple, with the label, program, arguments "
                       "and "
                       "launch keys each one sets.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "notes": "Reads the property lists in every Library/LaunchAgents and "
                 "Library/LaunchDaemons folder the paths match, among them "
                 "/Library/LaunchAgents, /Library/LaunchDaemons and each user's "
                 "~/Library/LaunchAgents, one row per file; Location is User Agent or User "
                 "Daemon when the path names a folder under Users or /private/var/root, and "
                 "System Agent or System Daemon otherwise. Files under /System/Library or "
                 "/Library/Apple are counted in the run log and not reported; the run log "
                 "counted 72 on dleapp_macos_bigsur, where 617 more files in those folders could "
                 "not be staged from the image because they are compressed with a method the "
                 "image reader does not read, and the run log names each one. Label, Program, "
                 "Program Arguments, Run At Load, Keep Alive, "
                 "Disabled, Start Interval and User Name are the file's Label, Program, "
                 "ProgramArguments, RunAtLoad, KeepAlive, Disabled, StartInterval and UserName keys, "
                 "with lists and dictionaries written as JSON. A file here is a definition; whether it"
                 " was loaded is not established from the file. On dleapp_macos_bigsur the two "
                 "reported files, one system agent and one system daemon, both use ProgramArguments "
                 "and set none of Program, Disabled, StartInterval or UserName, so Program, Disabled, "
                 "Start Interval, User Name and User are empty there. On the public MacBook Pro "
                 "logical extraction (macOS 15.4, not a registered corpus key) 868 files under "
                 "/System/Library or /Library/Apple were not reported, 7 byte-identical copies "
                 "under System/Volumes/Data were not read again, and 7 were reported. Five of "
                 "those 7, the com.google.keystone plists of 181 bytes "
                 "each, parse to an empty dictionary, so their rows carry only Location, Source "
                 "File and, on the two in a user's ~/Library/LaunchAgents, User, and none of the "
                 "7 sets Program, RunAtLoad, KeepAlive, Disabled or UserName, so"
                 " Program, Run At Load, Keep Alive, Disabled and User Name are empty there. When a "
                 "logical extraction holds the same file at its own path and again under "
                 "System/Volumes/Data/, a second copy byte-identical to the first is not read "
                 "again, and is counted in the run log.",
        "paths": ('*/Library/LaunchAgents/*.plist', '*/Library/LaunchDaemons/*.plist'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "rocket",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 2 rows",
        },
    },
}

import json

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import load_plist, unique_sources, user_from_path

_SHIPPED = ('/System/Library/', '/Library/Apple/')


def _text(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str)
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    return str(value)


def _location(relative):
    user = user_from_path(relative)
    kind = 'Agent' if '/LaunchAgents/' in relative else 'Daemon'
    return (f'User {kind}', user) if user else (f'System {kind}', '')


@artifact_processor
def macosLaunchItems(context):
    data_headers = ('Label', 'Program', 'Program Arguments', 'Run At Load', 'Keep Alive',
                    'Disabled', 'Start Interval', 'User Name', 'Location', 'User', 'Source File')
    data_list = []
    read = []
    candidates = []
    shipped = 0
    for found in context.get_files_found():
        relative = '/' + context.get_relative_path(str(found)).replace('\\', '/').lstrip('/')
        if any(folder in relative for folder in _SHIPPED):
            shipped += 1
            continue
        candidates.append(found)
    if shipped:
        logfunc(f'Launch Agents and Daemons: {shipped} file(s) under /System/Library or '
                f'/Library/Apple not reported')
    paths, _skipped = unique_sources(context, candidates, label='Launch Agents and Daemons')
    for path in paths:
        relative = context.get_relative_path(path)
        item = load_plist(path)
        if not isinstance(item, dict):
            logfunc(f'Launch Agents and Daemons: could not read {relative}')
            continue
        read.append(path)
        location, user = _location('/' + relative.replace('\\', '/'))
        data_list.append((_text(item.get('Label')), _text(item.get('Program')),
                          _text(item.get('ProgramArguments')), _text(item.get('RunAtLoad')),
                          _text(item.get('KeepAlive')), _text(item.get('Disabled')),
                          _text(item.get('StartInterval')), _text(item.get('UserName')),
                          location, user, relative))
    return data_headers, data_list, '\n'.join(read)
