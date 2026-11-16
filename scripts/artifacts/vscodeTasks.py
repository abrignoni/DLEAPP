"""Visual Studio Code tasks.json tasks and the trusted folders list, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "vscodeTasks": {
        "name": "VS Code Tasks",
        "description": "Tasks defined in tasks.json files: .vscode/tasks.json in any folder, and tasks.json in a folder "
                 "named User or under User/profiles, where VS Code keeps user and profile tasks, one row per task. "
                 "Strings are shown as stored and lists and objects as compact JSON.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Visual Studio Code",
        "notes": "Reads .vscode/tasks.json (a workspace or folder file, which can sit in any project folder in the "
                 "extraction, so every one found is read; a file that does not parse is logged and skipped) and "
                 "tasks.json in a folder named User or under User/profiles. The VS Code documentation names the "
                 "tasks.json file in the .vscode folder for workspace tasks "
                 "(https://code.visualstudio.com/docs/debugtest/tasks, read on 15 November 2026), and the source "
                 "gives the user and profile tasks.json as the file tasks.json in the profile's folder "
                 "(src/vs/platform/userDataProfile/common/userDataProfile.ts, line 199, microsoft/vscode at "
                 "daa23473dac649d89eea75cf123acc96615fde14; lines 273 and 353 for the folders). Files are read as "
                 "JSON with comments and trailing commas allowed. Only the tasks list is read: a top-level "
                 "command, the inputs section and the other properties of a task are not reported, and a tasks "
                 "element that is not an object is shown whole in Command. Command, Arguments, Options and Depends "
                 "On are the command, args, options and dependsOn of the task; strings are shown as stored and "
                 "lists and objects as compact JSON. Run On is runOptions.runOn as stored; the documentation says "
                 "a value of folderOpen means the task runs when the containing folder is opened, that automatic "
                 "tasks are controlled by the task.allowAutomaticTasks setting (default off, with one prompt per "
                 "workspace) and that they never run in an untrusted workspace. A row shows what a file defines, "
                 "not that the task ran: VS Code Trusted Folders lists the entries stored in the trust list. "
                 "Platform Overrides holds the windows, osx and linux objects of the task as compact JSON, which "
                 "can carry a different command. Label is blank for a task without one. A task defined by an "
                 "extension type is reported with its Type and whichever of these columns it has; its other "
                 "properties, such as an npm script name, are not reported. Evidence tier: source-verified. The "
                 "artifact has been exercised only on a tasks.json written for the test, none from a corpus image, "
                 "so no tasks.json written by VS Code has been read. In the run over the test file, 2 rows, "
                 "Options and Depends On were empty on both.",
        "paths": ("*/.vscode/tasks.json", "*/User/tasks.json", "*/User/profiles/*/tasks.json"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
    },
    "vscodeTrustedFolders": {
        "name": "VS Code Trusted Folders",
        "description": "The workspace trust list where it is held in User/globalStorage/state.vscdb: one row per entry "
                 "(a folder or a saved workspace file), with its path and scheme as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Visual Studio Code",
        "notes": "Reads the ItemTable row with the key content.trust.model.key in state.vscdb under "
                 "User/globalStorage, a JSON object whose uriTrustInfo list holds one entry per trusted folder or "
                 "workspace file: a uri and a trusted flag. The key and the layout are from the VS Code source "
                 "(src/vs/workbench/services/workspaces/common/workspaceTrust.ts, line 42 for the key, "
                 "microsoft/vscode at daa23473dac649d89eea75cf123acc96615fde14). At that commit the list is "
                 "written to application-shared storage (line 364), which is a separate state.vscdb in a "
                 "sharedStorage folder under the user's home "
                 "(src/vs/platform/storage/electron-main/storageMainService.ts, line 203), and the key is moved "
                 "there from User/globalStorage/state.vscdb on first read. This artifact does not read that file, "
                 "so an empty result does not show that no folder was trusted; which VS Code releases use the "
                 "shared file, and the name of its folder in Microsoft's build, were not established. The sample "
                 "read here held the key in User/globalStorage. The Workspace Trust documentation page "
                 "(https://code.visualstudio.com/docs/editing/workspaces/workspace-trust, read on 15 November "
                 "2026) names no file for the list. In the source, an entry that equals or contains a path gives "
                 "it that entry's flag (line 492), other rules in the same function can also make a folder "
                 "trusted, and VS Code drops entries whose trusted flag is not set when it loads the list (line "
                 "358). This artifact reports every entry. Path is the fsPath of the uri when it has one, "
                 "otherwise its path; the uri authority is not reported. Scheme is the uri scheme; Trusted is the "
                 "flag as stored. An entry has no time. A missing entry does not show a folder was never trusted: "
                 "entries are removed when trust is withdrawn (line 525), the setting "
                 "security.workspace.trust.enabled turns the feature off, and newer builds keep the list in "
                 "another file. Only this one key is read from the file; workspace storage and the shared storage "
                 "file are not read. Evidence tier: data-proven on one state.vscdb from VS Code on the author's "
                 "Mac (file modified 17 November 2025; the VS Code and OS versions that wrote it are not "
                 "established), which holds 2 entries, both trusted, one with an fsPath and one with a path only; "
                 "no corpus image was run.",
        "paths": ("*/User/globalStorage/state.vscdb", "*/User/globalStorage/state.vscdb-wal"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "shield",
    },
}

import json
import os

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db, get_sqlite_db_records, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path

_TRUST_KEY = 'content.trust.model.key'
_PLATFORMS = ('windows', 'osx', 'linux')


def strip_jsonc(text):
    """text with // and /* */ comments and trailing commas removed, string contents untouched."""
    out = []
    i, size = 0, len(text)
    while i < size:
        char = text[i]
        if char == '"':
            j = i + 1
            while j < size and text[j] != '"':
                j += 2 if text[j] == '\\' else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith('//', i):
            while i < size and text[i] not in '\r\n':
                i += 1
        elif text.startswith('/*', i):
            end = text.find('*/', i + 2)
            i = size if end < 0 else end + 2
        else:
            out.append(char)
            i += 1
    cleaned, result = ''.join(out), []
    i, size = 0, len(cleaned)
    while i < size:
        char = cleaned[i]
        if char == '"':
            j = i + 1
            while j < size and cleaned[j] != '"':
                j += 2 if cleaned[j] == '\\' else 1
            result.append(cleaned[i:j + 1])
            i = j + 1
            continue
        if char == ',':
            j = i + 1
            while j < size and cleaned[j] in ' \t\r\n':
                j += 1
            if j < size and cleaned[j] in '}]':
                i += 1
                continue
        result.append(char)
        i += 1
    return ''.join(result)


def _text(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def _task_rows(data):
    tasks = data.get('tasks')
    rows = []
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            rows.append(('', '', _text(task), '', '', '', '', ''))
            continue
        run_options = task.get('runOptions')
        overrides = {k: task[k] for k in _PLATFORMS if k in task}
        rows.append((_text(task.get('label')), _text(task.get('type')), _text(task.get('command')),
                     _text(task.get('args')), _text(task.get('options')),
                     _text(run_options.get('runOn')) if isinstance(run_options, dict) else '',
                     _text(task.get('dependsOn')), _text(overrides) if overrides else ''))
    return rows


@artifact_processor
def vscodeTasks(context):
    data_headers = ('Label', 'Type', 'Command', 'Arguments', 'Options', 'Run On', 'Depends On',
                    'Platform Overrides', 'User', 'Source File')
    label = 'VS Code Tasks'
    wanted = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'tasks.json']
    paths, _skipped = unique_sources(context, wanted, label=label)
    data_list, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = json.loads(strip_jsonc(handle.read().decode('utf-8-sig')))
        except (OSError, ValueError) as error:
            logfunc(f'{label}: {relative} could not be read as JSON ({type(error).__name__})')
            continue
        if not isinstance(data, dict):
            logfunc(f'{label}: {relative} holds JSON that is not an object')
            continue
        read.append(path)
        data_list.extend(row + (user_from_path(relative), relative) for row in _task_rows(data))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def vscodeTrustedFolders(context):
    data_headers = ('Path', 'Scheme', 'Trusted (as stored)', 'User', 'Source File')
    label = 'VS Code Trusted Folders'
    wanted = [p for p in context.get_files_found() if os.path.basename(str(p)) == 'state.vscdb']
    paths, _skipped = unique_sources(context, wanted, sidecars=('-wal', '-shm'), label=label)
    data_list, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'ItemTable'):
            logfunc(f'{label}: no ItemTable in {relative}')
            continue
        read.append(path)
        records = get_sqlite_db_records(path, f"SELECT value FROM ItemTable WHERE key = '{_TRUST_KEY}'")
        for (value,) in records or []:
            try:
                info = json.loads(value if isinstance(value, str) else bytes(value).decode('utf-8'))
            except (ValueError, TypeError):
                logfunc(f'{label}: the trust value in {relative} is not JSON')
                continue
            entries = info.get('uriTrustInfo') if isinstance(info, dict) else None
            for entry in entries if isinstance(entries, list) else []:
                uri = entry.get('uri') if isinstance(entry, dict) else None
                if not isinstance(uri, dict):
                    continue
                data_list.append((_text(uri.get('fsPath') if uri.get('fsPath') is not None else uri.get('path')),
                                  _text(uri.get('scheme')), _text(entry.get('trusted')),
                                  user_from_path(relative), relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
