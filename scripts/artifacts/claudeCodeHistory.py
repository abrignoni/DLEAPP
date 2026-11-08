"""Prompts recorded in Claude Code's prompt history (history.jsonl), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "claudeCodeHistory": {
        "name": "Claude Code Prompt History",
        "description": "Prompts, slash commands and shell-mode commands submitted in Claude Code, one row per line "
                       "of history.jsonl, with the text of each paste the line names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Claude Code",
        "notes": "Reads history.jsonl in each .claude folder the paths match, the file in which the Claude Code command-line client keeps the prompts typed at its prompt for recall. Claude Code keeps it in the folder named by the CLAUDE_CONFIG_DIR environment variable, or else in .claude in the home folder; a folder set through that variable under another name is not read. Source: Claude Code 2.1.112 (https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-2.1.112.tgz, package/cli.js, line 8 for the folder; line 673 for the writer, line 674 for what a line holds), the last release whose code ships as readable JavaScript; later releases ship a compiled binary. In 2.1.112 each line is a JSON object of display (the text as shown at the prompt), pastedContents, timestamp, which the code takes from Date.now() and the artifact reads as Unix milliseconds, project and sessionId. On windows11_arm_claude_code_history_known_20261108, written by Claude Code 2.1.319 on Windows 11 ARM64, every line held those five fields and no other. Its 14 lines are 14 rows: for the 11 submitted with Enter, the Timestamp is within 0.1 s of the time that Enter was sent, 2 ms before it on one row and 2 to 83 ms after it on the others, with the two machines' clocks not compared. Recorded there: prompts, slash commands such as /model, /clear and /exit, a shell-mode command with its leading !, a prompt cancelled while it was being answered, a prompt given on the command line when the client was started, stamped when the session took it, and text typed and then cleared with Esc pressed twice, never submitted, stamped 83 ms after the second Esc (the code saves it at line 688). A prompt run with claude -p left no line. A row is therefore what was entered at the prompt, not proof that it was sent or answered. Project is the project value as stored; on the known data it was the folder the client was started in, neither folder being a git repository. Session ID is the sessionId as stored; on the known data each value was also the name of a session transcript under projects in the same .claude folder, which this artifact does not read, and /clear started a new value within one run of the client. Older releases wrote fewer fields: across the npm releases, history.jsonl first appears in 1.0.124, whose lines have no sessionId, and sessionId first in 2.1.63. The prompt history kept by releases before 1.0.124 inside .claude.json is not read. Pasted Text holds each paste a line names, as [#n] and its text, n being the number in the [Pasted text #n] placeholder of Prompt. A paste is stored in the line itself, or, in 2.1.112 for a paste over 1,024 characters, as a contentHash naming a file paste-cache/<contentHash>.txt beside history.jsonl (line 673, line 674); paste-cache first appears in 2.1.0 among the npm releases. The artifact reads that file from the paste-cache folder of the same .claude folder only, so a hash never takes its text from another profile, and Paste Files names it. On the known data one paste of 601 characters was stored in the line and one of 2,161 characters in paste-cache, and the file name was the first 16 hexadecimal digits of the SHA-256 of the file's bytes, as in the code (line 673); Paste Files says when a file does not match its name that way, and when the file is not in the extraction, in which case Pasted Text says it was not found. In 2.1.112 the cleanup run at start deletes paste-cache files last modified longer ago than the cleanupPeriodDays setting, 30 days by default (line 8577), so an old line can name a file that is gone. Strings in 2.1.319 also name a history retention prune whose rule was not read. Image pastes are not stored in history in 2.1.112 (line 674), which was not exercised. Both pastes in the known data end in 1~, left there by the rig that typed them. Rows are in file order and Line is the line of the file a row comes from. A line that is not a JSON object gives no row and is counted in the run log. Source File is the history.jsonl a row comes from and stays because no other column says which profile a row belongs to; the report's located-at line also names the paste-cache files used. Claude Code's other files in the same folder (session transcripts, .claude.json, .credentials.json, settings.json, backups, shell snapshots) are not read.",
        "paths": ("*/.claude/history.jsonl", "*/.claude/paste-cache/*.txt"),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "windows11_arm_claude_code_history_known_20261108": "Windows 11 build 26200 (ARM64), Claude Code 2.1.319 | 14 rows",
        },
    },
}

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_FIELDS = {'display', 'pastedContents', 'timestamp', 'project', 'sessionId'}


def history_time(value):
    """The UTC time of a history line's timestamp, which Claude Code writes as Date.now(): Unix milliseconds.
    Anything that is not a whole number is returned unchanged."""
    if isinstance(value, bool) or not isinstance(value, int):
        return value
    try:
        return _EPOCH + timedelta(milliseconds=value)
    except OverflowError:
        return value


def paste_cell(pasted, paste_dir, available, counts, used):
    """(pasted text, paste files) for a line's pastedContents. Text stored inline is shown as stored; a contentHash is
    looked up as <hash>.txt in the paste-cache folder beside the same history.jsonl, never in another one. The
    paste files cell names each file used, and says when the file is missing or its name is not the start of the
    SHA-256 of its bytes."""
    if not isinstance(pasted, dict) or not pasted:
        if pasted not in (None, {}):
            counts['lines whose pastedContents is not an object, shown empty'] += 1
        return '', ''
    texts, files = [], []
    for key in sorted(pasted, key=lambda k: (not str(k).isdigit(), int(k) if str(k).isdigit() else 0, str(k))):
        item = pasted[key]
        if not isinstance(item, dict):
            counts['pastes that are not an object, shown as stored'] += 1
            texts.append(f'[#{key}] {item}')
            continue
        label = f'[#{item.get("id", key)}]'
        kind = item.get('type')
        if kind not in (None, 'text'):
            label = f'{label} ({kind})'
        if 'content' in item:
            texts.append(f'{label} {item["content"]}')
            continue
        digest = item.get('contentHash')
        if not isinstance(digest, str) or not digest:
            counts['pastes with neither content nor contentHash'] += 1
            texts.append(f'{label} (no content stored)')
            continue
        name = f'{digest}.txt'
        path = available.get(os.path.normcase(os.path.join(paste_dir, name)))
        if path is None:
            counts['pastes whose paste-cache file is not in the extraction'] += 1
            texts.append(f'{label} (paste-cache file {name} not found)')
            files.append(f'{name} (not found)')
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['paste-cache files that could not be read'] += 1
            texts.append(f'{label} (paste-cache file {name} could not be read)')
            files.append(f'{name} (not read)')
            continue
        used.append(path)
        if hashlib.sha256(data).hexdigest().startswith(digest.lower()):
            files.append(name)
        else:
            counts['paste-cache files whose name does not match their SHA-256'] += 1
            files.append(f'{name} (SHA-256 does not start with its name)')
        texts.append(f'{label} {data.decode("utf-8", errors="backslashreplace")}')
    return '\n\n'.join(texts), '\n'.join(files)


def history_rows(data, paste_dir, available, counts, used):
    """(timestamp, prompt, pasted text, paste files, project, session id, line number) for each line of a
    history.jsonl, in file order. A line that is not a JSON object is counted and gives no row."""
    rows = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            counts['lines that are not JSON, not reported'] += 1
            continue
        if not isinstance(entry, dict):
            counts['lines that are not a JSON object, not reported'] += 1
            continue
        if set(entry) - _FIELDS:
            counts['lines with fields beyond display, pastedContents, timestamp, project and sessionId'] += 1
        pasted, files = paste_cell(entry.get('pastedContents'), paste_dir, available, counts, used)
        rows.append((history_time(entry.get('timestamp')), entry.get('display', ''), pasted, files,
                     entry.get('project', ''), entry.get('sessionId', ''), number))
    return rows


@artifact_processor
def claudeCodeHistory(context):
    data_headers = (('Timestamp', 'datetime'), 'Prompt', 'Pasted Text', 'Paste Files', 'Project', ('Session ID', 'hash'),
                    'Line', 'Source File')
    data_list = []
    read = []
    counts = Counter()
    found = sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p))
    available = {os.path.normcase(os.path.normpath(p)): p for p in found}
    for path in found:
        if os.path.basename(path) != 'history.jsonl':
            continue
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['history files that could not be read'] += 1
            continue
        paste_dir = os.path.normcase(os.path.normpath(os.path.join(os.path.dirname(path), 'paste-cache')))
        used = []
        rows = history_rows(data, paste_dir, available, counts, used)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
            read.extend(p for p in dict.fromkeys(used) if p not in read)
    if counts:
        logfunc('Claude Code Prompt History: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
