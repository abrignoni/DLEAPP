"""Claude Code session transcripts, file history and the prompt history kept in .claude.json, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "claudeCodeSessions": {
        "name": "Claude Code Sessions",
        "description": "One row per Claude Code session transcript: first and last record times, title, working "
                       "folder, versions, models, message counts, tools used and the account the session ran under.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-09",
        "last_update_date": "2026-11-09",
        "requirements": "none",
        "category": "Claude Code",
        "notes": "Claude Code writes one transcript per session as projects/<folder name>/<sessionId>.jsonl in its config folder (.claude in the home folder unless CLAUDE_CONFIG_DIR names another), and a subagent's transcript as <sessionId>/subagents/agent-<agentId>.jsonl beside it with a .meta.json (Claude Code 2.1.112, https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-2.1.112.tgz, package/cli.js, line 8143). Only transcripts under a folder named .claude are read; a config folder set through CLAUDE_CONFIG_DIR under another name is not. The record format is not documented and changes between releases: the known data, windows11_arm_claude_code_sessions_known_20261109, was written by Claude Code 2.1.319 on Windows 11 ARM64, signed in to a real account, and its account identifiers were replaced by placeholders afterwards. One row per transcript file. First Record and Last Record are the earliest and latest timestamp of its records. Session ID lists the sessionId values its records carry; resuming a session with claude --resume appended to the same file under the same sessionId on the known data, so one row can cover several runs of the client. Agent ID and Agent Type are filled for a subagent transcript, Agent Type from its .meta.json. Title is the last ai-title record, a title the client generated for the session. Working Folder, Git Branch, Claude Code Version and Models list the distinct cwd, gitBranch, version and assistant model values as stored; on the known data no folder was a git repository and gitBranch held HEAD on every record. User Messages counts user records whose content is text and that are not marked isMeta (typed prompts, but also slash commands and their output, which the client stores as user records), Assistant Messages counts assistant records, and API Error Messages those marked isApiErrorMessage. Tools Used counts the tool calls by name. Account UUID and Organization UUID come from the session-owner records; on the known data they equalled oauthAccount.accountUuid and organizationUuid in .claude.json, compared by value, and subagent transcripts held no session-owner record. session-owner first appears after 2.1.112, so older transcripts leave both empty. Transcript File is the file a row describes; the located-at line also names the .meta.json files read. Not read: the other record types (attachments, api-request and api-request-blob, cost-state, mode, permission-mode, last-prompt, tools-used, atis-latch); on the known data the account email was in a session_context attachment and in an api-request-blob, and it is not reported. On the known data the 3 session transcripts and 1 subagent transcript gave 4 rows; Git Branch held HEAD, Claude Code Version 2.1.319 and Models claude-haiku-5-5 on all 4 rows, and API Error Messages held 0 on all 4 because the 1.0.123 transcript is not read.",
        "paths": ("*/.claude/projects/*.jsonl", "*/.claude/projects/*.meta.json"),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "windows11_arm_claude_code_sessions_known_20261109": "Windows 11 build 26200 (ARM64), Claude Code 2.1.319 and 1.0.123 | 4 rows",
        },
    },
    "claudeCodeMessages": {
        "name": "Claude Code Messages",
        "description": "User and assistant messages from Claude Code session transcripts, with the tool calls the "
                       "model made, the tool results it received and any image they carried.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-09",
        "last_update_date": "2026-11-09",
        "requirements": "none",
        "category": "Claude Code",
        "notes": "Claude Code writes one transcript per session as projects/<folder name>/<sessionId>.jsonl in its config folder (.claude in the home folder unless CLAUDE_CONFIG_DIR names another), and a subagent's transcript as <sessionId>/subagents/agent-<agentId>.jsonl beside it with a .meta.json (Claude Code 2.1.112, https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-2.1.112.tgz, package/cli.js, line 8143). Only transcripts under a folder named .claude are read; a config folder set through CLAUDE_CONFIG_DIR under another name is not. The record format is not documented and changes between releases: the known data, windows11_arm_claude_code_sessions_known_20261109, was written by Claude Code 2.1.319 on Windows 11 ARM64, signed in to a real account, and its account identifiers were replaced by placeholders afterwards. One row per user or assistant record, in file order per transcript. Message is the text of the record; Tool Calls lists each tool_use block as its name and its input in JSON; Tool Results the text of each tool_result block. An image block, in a tool result or in a user message, is decoded from its base64 data and shown in Media; on the known data the Read tool's result for a PNG held the whole file, byte-identical to the file read. Only the first image of a record is shown and any other is counted in the run log. Text longer than 20,000 characters is cut and says how much was left out. Role is the record type (user or assistant). Tool results, local command output and messages from subagents and background tasks are stored as user records and appear with Role user. Meta is Yes for records marked isMeta, text the client added to the conversation rather than typed by the user. API Error is Yes for records marked isApiErrorMessage; on the known data every reply of Claude Code 1.0.123 was one (a 404 for its default model), so its prompts were not answered. Agent ID is filled for records of a subagent transcript. Assistant records whose content is only thinking blocks with no text are not reported and are counted in the run log; the known data had 7, and none of its thinking blocks held text. Model is message.model as stored (<synthetic> on the API error records of 1.0.123 in the known data). Line is the line of the transcript. On the known data the transcripts gave 48 rows, and API Error held no value on any of them because the 1.0.123 transcript is not read. The 1.0.123 transcript of the known data sits in a config folder not named .claude and is not read; its record shape is covered by a unit test only.",
        "paths": ("*/.claude/projects/*.jsonl",),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "windows11_arm_claude_code_sessions_known_20261109": "Windows 11 build 26200 (ARM64), Claude Code 2.1.319 and 1.0.123 | 48 rows",
        },
        "data_views": {"conversation": {
            "conversationDiscriminatorColumn": "Session ID", "conversationLabelColumn": "Session ID",
            "directionColumn": "Role", "directionSentValue": "user", "textColumn": "Message",
            "timeColumn": "Timestamp", "mediaColumn": "Media"}},
    },
    "claudeCodeFileHistory": {
        "name": "Claude Code File History",
        "description": "Files Claude Code tracked for rewind in a session, one row per version, with the copy of the "
                       "file it kept in file-history.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-09",
        "last_update_date": "2026-11-09",
        "requirements": "none",
        "category": "Claude Code",
        "notes": "Claude Code writes one transcript per session as projects/<folder name>/<sessionId>.jsonl in its config folder (.claude in the home folder unless CLAUDE_CONFIG_DIR names another), and a subagent's transcript as <sessionId>/subagents/agent-<agentId>.jsonl beside it with a .meta.json (Claude Code 2.1.112, https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-2.1.112.tgz, package/cli.js, line 8143). Only transcripts under a folder named .claude are read; a config folder set through CLAUDE_CONFIG_DIR under another name is not. The record format is not documented and changes between releases: the known data, windows11_arm_claude_code_sessions_known_20261109, was written by Claude Code 2.1.319 on Windows 11 ARM64, signed in to a real account, and its account identifiers were replaced by placeholders afterwards. Claude Code keeps copies of the files it edits so that a session can be rewound: before a tool first edits a file, and again at each later user message while the file has changed, it records a backup version, and stores the copy as file-history/<sessionId>/<first 16 hex digits of the SHA-256 of the file's path>@v<version> (2.1.112, line 3038). One row per tracked file and version named in a transcript's file-history-snapshot and file-history-delta records, with the earliest record naming it. Backup Time is backupTime as stored. Tracked File is the path as the record holds it and Folder the realParentDir beside it, which 2.1.319 writes. A version with no backup file is one recorded while the file did not exist (2.1.112, line 3038): on the known data version 1 of the file Claude created, recorded just before it was written. Backup Content is the copy's text, read only from the file-history folder of the same session in the same .claude folder, or says that it was not found or is not UTF-8 text. On the known data the backup name matched the SHA-256 of the full Windows path of the file, the copy held the file as Claude wrote it, and the transcripts gave 2 rows.",
        "paths": ("*/.claude/projects/*.jsonl", "*/.claude/file-history/*"),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "windows11_arm_claude_code_sessions_known_20261109": "Windows 11 build 26200 (ARM64), Claude Code 2.1.319 and 1.0.123 | 2 rows",
        },
    },
    "claudeCodeConfigHistory": {
        "name": "Claude Code Prompt History (.claude.json)",
        "description": "Prompts kept per project folder in the history lists of .claude.json, the store Claude Code "
                       "used for prompt recall before history.jsonl.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-09",
        "last_update_date": "2026-11-09",
        "requirements": "none",
        "category": "Claude Code",
        "notes": "Reads the history list of each project entry in each .claude.json the paths match. Claude Code 1.0.123 adds each prompt to the front of the list of the project it runs in, keeps at most 100 entries and skips a prompt equal to the newest one (https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-1.0.123.tgz, package/cli.js, line 889); Position 1 is therefore the newest entry it kept. The entries hold no time and no session. Last Session ID is the project entry's lastSessionId, the last session run in that folder, not the session of each prompt. Pasted Text holds each paste stored with the entry, which in 1.0.123 keeps its whole text whatever its length, and the pastedText field of an older entry shape that the same line still reads. history.jsonl replaced this list from 1.0.124, which wrote both; the .claude.json of Claude Code 2.1.319 on the known data held no history list. On windows11_arm_claude_code_sessions_known_20261109 the .claude.json written by 1.0.123 (in a config folder set with CLAUDE_CONFIG_DIR) held 4 entries for one folder, 4 rows: the three prompts typed and /exit, stored with a trailing space; a 623-character paste was stored inside the prompt text and a 2,239-character paste as a paste of the entry. Project and Last Session ID held one value on all 4 rows, the one folder of that run. Other .claude.json content (the account, settings, caches) is not read, nor are backup copies of the file. Source File is the .claude.json a row comes from.",
        "paths": ("*/.claude.json",),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "windows11_arm_claude_code_sessions_known_20261109": "Windows 11 build 26200 (ARM64), Claude Code 2.1.319 and 1.0.123 | 4 rows",
        },
    },
}

import base64
import binascii
import json
import os
from collections import Counter
from datetime import datetime

from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

_MAX_TEXT = 20000


def record_time(value):
    """A transcript timestamp (ISO 8601 with Z) as an aware datetime; anything else is returned unchanged."""
    if not isinstance(value, str) or not value:
        return value
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return value


def read_records(path, counts):
    """(line number, record) for each JSON object line of a transcript; other lines are counted and skipped."""
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
    except OSError:
        counts['transcripts that could not be read'] += 1
        return []
    records = []
    for number, raw in enumerate(data.split(b'\n'), 1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            counts['transcript lines that are not JSON, skipped'] += 1
            continue
        if isinstance(record, dict):
            records.append((number, record))
        else:
            counts['transcript lines that are not a JSON object, skipped'] += 1
    return records


def transcripts(context):
    """Sorted staged paths of the transcript files (.jsonl under a projects folder of a .claude folder)."""
    return sorted(str(p) for p in context.get_files_found()
                  if str(p).endswith('.jsonl') and not os.path.isdir(p))


def main_session(records):
    """The sessionId most records of a transcript carry ('' when none does)."""
    seen = Counter(r.get('sessionId') for _n, r in records if isinstance(r.get('sessionId'), str))
    return seen.most_common(1)[0][0] if seen else ''


def joined(values):
    return '\n'.join(dict.fromkeys(v for v in values if v))


def clip(text):
    if isinstance(text, str) and len(text) > _MAX_TEXT:
        return text[:_MAX_TEXT] + f' [... {len(text) - _MAX_TEXT} more characters]'
    return text


def image_bytes(block, counts):
    """(bytes, media type) of an image block whose source is base64 data, else (None, None)."""
    source = block.get('source') if isinstance(block, dict) else None
    if not isinstance(source, dict) or source.get('type') != 'base64' or not isinstance(source.get('data'), str):
        counts['image blocks without base64 data, not shown'] += 1
        return None, None
    try:
        return base64.b64decode(source['data'], validate=True), source.get('media_type')
    except (binascii.Error, ValueError):
        counts['image blocks whose base64 data does not decode, not shown'] += 1
        return None, None


def block_text(content):
    """The text of a message content that is a string or a list of blocks, joined; images marked [image]."""
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'text' and isinstance(block.get('text'), str):
                parts.append(block['text'])
            elif block.get('type') == 'image':
                parts.append('[image]')
    return '\n'.join(parts)


@artifact_processor
def claudeCodeSessions(context):
    data_headers = (('First Record', 'datetime'), ('Last Record', 'datetime'), ('Session ID', 'hash'), 'Agent ID',
                    'Agent Type', 'Title', 'Working Folder', 'Git Branch', 'Claude Code Version', 'Models',
                    'User Messages', 'Assistant Messages', 'API Error Messages', 'Tools Used',
                    ('Account UUID', 'hash'), ('Organization UUID', 'hash'), 'Transcript File')
    data_list, read = [], []
    counts = Counter()
    found = {os.path.normcase(os.path.normpath(str(p))): str(p) for p in context.get_files_found()}
    for path in transcripts(context):
        records = read_records(path, counts)
        if not records:
            continue
        times = [r.get('timestamp') for _n, r in records if isinstance(r.get('timestamp'), str)]
        messages = [r for _n, r in records if r.get('type') in ('user', 'assistant')]
        agent_ids = joined(r.get('agentId') for r in messages if isinstance(r.get('agentId'), str))
        agent_type = ''
        meta_path = found.get(os.path.normcase(os.path.normpath(path[:-len('.jsonl')] + '.meta.json')))
        if meta_path:
            try:
                with open(meta_path, 'rb') as handle:
                    meta = json.loads(handle.read().decode('utf-8'))
                if isinstance(meta, dict) and isinstance(meta.get('agentType'), str):
                    agent_type = meta['agentType']
            except (OSError, UnicodeDecodeError, ValueError):
                counts['subagent .meta.json files that could not be read'] += 1
        tools = []
        for r in messages:
            content = (r.get('message') or {}).get('content') if isinstance(r.get('message'), dict) else None
            if isinstance(content, list):
                tools.extend(b.get('name') for b in content if isinstance(b, dict) and b.get('type') == 'tool_use')
        titles = [r.get('aiTitle') for _n, r in records if r.get('type') == 'ai-title']
        owners = [r for _n, r in records if r.get('type') == 'session-owner']
        data_list.append((
            record_time(min(times, key=record_time)) if times else '',
            record_time(max(times, key=record_time)) if times else '',
            joined(r.get('sessionId') for _n, r in records if isinstance(r.get('sessionId'), str)), agent_ids, agent_type, titles[-1] if titles else '',
            joined(r.get('cwd') for r in messages if isinstance(r.get('cwd'), str)),
            joined(r.get('gitBranch') for r in messages if isinstance(r.get('gitBranch'), str)),
            joined(r.get('version') for r in messages if isinstance(r.get('version'), str)),
            joined((r.get('message') or {}).get('model') for r in messages
                   if r.get('type') == 'assistant' and isinstance(r.get('message'), dict)),
            sum(1 for r in messages if r.get('type') == 'user'
                and isinstance((r.get('message') or {}).get('content'), str) and not r.get('isMeta')),
            sum(1 for r in messages if r.get('type') == 'assistant'),
            sum(1 for r in messages if r.get('type') == 'assistant' and r.get('isApiErrorMessage')),
            ', '.join(f'{name} ({n})' for name, n in Counter(t for t in tools if t).most_common()),
            joined(r.get('accountUuid') for r in owners if isinstance(r.get('accountUuid'), str)),
            joined(r.get('organizationUuid') for r in owners if isinstance(r.get('organizationUuid'), str)),
            context.get_relative_path(path)))
        read.append(path)
        if meta_path:
            read.append(meta_path)
    if counts:
        logfunc('Claude Code Sessions: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def claudeCodeMessages(context):
    data_headers = (('Timestamp', 'datetime'), 'Role', ('Session ID', 'hash'), 'Message', ('Media', 'media'),
                    'Tool Calls', 'Tool Results', 'Model', 'API Error', 'Meta', 'Agent ID', 'Working Folder',
                    ('Message UUID', 'hash'), 'Line', 'Transcript File')
    data_list, read = [], []
    counts = Counter()
    for path in transcripts(context):
        records = read_records(path, counts)
        relative = context.get_relative_path(path)
        rows = 0
        for number, record in records:
            if record.get('type') not in ('user', 'assistant'):
                continue
            message = record.get('message') if isinstance(record.get('message'), dict) else {}
            content = message.get('content')
            if (isinstance(content, list) and content and
                    all(isinstance(b, dict) and b.get('type') == 'thinking' and not b.get('thinking')
                        for b in content)):
                counts['assistant records holding only a thinking block with no text, not reported'] += 1
                continue
            calls, results, media = [], [], []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    kind = block.get('type')
                    if kind == 'tool_use':
                        calls.append(f'{block.get("name", "")}: '
                                     f'{json.dumps(block.get("input"), ensure_ascii=False)}')
                    elif kind == 'tool_result':
                        inner = block.get('content')
                        results.append(block_text(inner))
                        if isinstance(inner, list):
                            media.extend(b for b in inner if isinstance(b, dict) and b.get('type') == 'image')
                    elif kind == 'image':
                        media.append(block)
            media_ref = ''
            for index, block in enumerate(media):
                data, _kind = image_bytes(block, counts)
                if data is None:
                    continue
                if media_ref:
                    counts['images beyond the first on a message, not shown'] += 1
                    continue
                media_ref = check_in_embedded_media(path, data, f'{record.get("uuid", number)}-{index}') or ''
            data_list.append((
                record_time(record.get('timestamp')), record.get('type'), record.get('sessionId', ''),
                clip(block_text(content)), media_ref, clip('\n'.join(calls)), clip('\n\n'.join(r for r in results if r)),
                message.get('model', ''), 'Yes' if record.get('isApiErrorMessage') else '',
                'Yes' if record.get('isMeta') else '', record.get('agentId', ''), record.get('cwd', ''),
                record.get('uuid', ''), number, relative))
            rows += 1
        if rows:
            read.append(path)
    if counts:
        logfunc('Claude Code Messages: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


def backup_entries(records):
    """Distinct (tracking path, version) backups named by a transcript's file-history records, each with the
    first record that names it: (backup time, tracking path, folder, version, backup file name)."""
    entries = {}
    for _n, record in records:
        kind = record.get('type')
        found = []
        if kind == 'file-history-snapshot':
            snapshot = record.get('snapshot') if isinstance(record.get('snapshot'), dict) else {}
            backups = snapshot.get('trackedFileBackups')
            if isinstance(backups, dict):
                found = [(path, backup) for path, backup in backups.items() if isinstance(backup, dict)]
        elif kind == 'file-history-delta' and isinstance(record.get('backup'), dict):
            found = [(record.get('trackingPath'), record['backup'])]
        for path, backup in found:
            key = (path, backup.get('version'))
            if key not in entries:
                entries[key] = (backup.get('backupTime', ''), path or '', backup.get('realParentDir', ''),
                                backup.get('version', ''), backup.get('backupFileName'))
    return sorted(entries.values(), key=lambda e: (str(e[0]), str(e[1]), str(e[3])))


@artifact_processor
def claudeCodeFileHistory(context):
    data_headers = (('Backup Time', 'datetime'), ('Session ID', 'hash'), 'Tracked File', 'Folder', 'Version',
                    'Backup File', 'Backup Content', 'Transcript File')
    data_list, read = [], []
    counts = Counter()
    available = {os.path.normcase(os.path.normpath(str(p))): str(p) for p in context.get_files_found()}
    for path in transcripts(context):
        records = read_records(path, counts)
        entries = backup_entries(records)
        if not entries:
            continue
        session = main_session(records)
        claude_dir = path
        while os.path.basename(claude_dir) != 'projects' and os.path.dirname(claude_dir) != claude_dir:
            claude_dir = os.path.dirname(claude_dir)
        history_dir = os.path.join(os.path.dirname(claude_dir), 'file-history', session)
        read.append(path)
        for when, tracked, folder, version, name in entries:
            if name is None:
                shown, content = '', '(no copy: the file did not exist when this version was recorded)'
            else:
                backup = available.get(os.path.normcase(os.path.normpath(os.path.join(history_dir, str(name)))))
                shown = str(name)
                if backup is None:
                    counts['backups whose file is not in the extraction'] += 1
                    content = f'(backup file {name} not found)'
                    shown = f'{name} (not found)'
                else:
                    try:
                        with open(backup, 'rb') as handle:
                            data = handle.read()
                        content = clip(data.decode('utf-8'))
                    except UnicodeDecodeError:
                        content = f'({len(data)} bytes, not UTF-8 text)'
                    except OSError:
                        counts['backup files that could not be read'] += 1
                        content = '(backup file could not be read)'
                    if backup not in read:
                        read.append(backup)
            data_list.append((record_time(when), session, tracked, folder, version, shown, content,
                              context.get_relative_path(path)))
    if counts:
        logfunc('Claude Code File History: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


def config_history_rows(config, counts):
    """(project, position, prompt, pasted text, last session id) for each entry of each project's history list in
    a parsed .claude.json; position 1 is the first entry of the list."""
    rows = []
    projects = config.get('projects') if isinstance(config, dict) else None
    if not isinstance(projects, dict):
        return rows
    for project, settings in projects.items():
        if not isinstance(settings, dict) or not isinstance(settings.get('history'), list):
            continue
        for position, entry in enumerate(settings['history'], 1):
            if isinstance(entry, str):
                rows.append((project, position, entry, '', settings.get('lastSessionId', '')))
                continue
            if not isinstance(entry, dict):
                counts['history entries that are neither text nor an object, skipped'] += 1
                continue
            pasted = []
            contents = entry.get('pastedContents')
            if isinstance(contents, dict):
                for key in sorted(contents, key=lambda k: (not str(k).isdigit(), int(k) if str(k).isdigit() else 0)):
                    item = contents[key]
                    if isinstance(item, dict):
                        pasted.append(f'[#{item.get("id", key)}] {item.get("content", "")}')
            if isinstance(entry.get('pastedText'), str):
                pasted.append(entry['pastedText'])
            rows.append((project, position, entry.get('display', ''), clip('\n\n'.join(pasted)),
                         settings.get('lastSessionId', '')))
    return rows


@artifact_processor
def claudeCodeConfigHistory(context):
    data_headers = ('Project', 'Position', 'Prompt', 'Pasted Text', ('Last Session ID', 'hash'), 'Source File')
    data_list, read = [], []
    counts = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        if os.path.basename(path) != '.claude.json':
            continue
        try:
            with open(path, 'rb') as handle:
                config = json.loads(handle.read().decode('utf-8-sig'))
        except (OSError, UnicodeDecodeError, ValueError):
            counts['.claude.json files that could not be read as JSON'] += 1
            continue
        rows = config_history_rows(config, counts)
        if rows:
            relative = context.get_relative_path(path)
            data_list.extend(row + (relative,) for row in rows)
            read.append(path)
    if counts:
        logfunc('Claude Code Prompt History (.claude.json): ' +
                ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
