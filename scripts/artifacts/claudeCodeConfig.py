"""Claude Code settings, MCP servers and project trust entries, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "claudeCodeSettings": {
        "name": "Claude Code Settings",
        "description": "Entries of the settings.json and settings.local.json files in .claude folders that name a "
                 "command to run, a variable to set, a permission rule or a plugin: hooks, status line, env, API "
                 "key helper, permission rules, MCP approval lists and plugin lists, one row per entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Claude Code",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "Reads settings.json and settings.local.json in every .claude folder the paths match, the user "
                 "folder and any project folder alike; Source File says which, because a row alone does not (the "
                 "Claude Code documentation names ~/.claude/settings.json as the user file, .claude/settings.json "
                 "in a project as the shared project file and .claude/settings.local.json as the project-local "
                 "file, https://code.claude.com/docs/en/settings, read on 15 November 2026). A settings file can "
                 "sit anywhere in the extraction, so every .claude folder is read. A config folder set through "
                 "CLAUDE_CONFIG_DIR under another name is not, and managed settings (managed-settings.json) are "
                 "not read. Rows come from these keys only: hooks (one row per hook: Item is the event, Matcher "
                 "the matcher of its group, Type the hook type and Value its command, or its url or prompt when it "
                 "has no command; a hook with none of the three shows its other fields as JSON, and other fields "
                 "of a hook, such as timeout, are not shown); statusLine; env (Item is the variable name; Value is "
                 "the stored string, a value that is not a string is shown as compact JSON and null is shown "
                 "blank); apiKeyHelper; permissions (Item is allow, ask, deny, defaultMode or "
                 "additionalDirectories, one row per rule; other sub-keys of permissions are not reported); "
                 "enableAllProjectMcpServers, enabledMcpjsonServers and disabledMcpjsonServers; enabledPlugins and "
                 "extraKnownMarketplaces. Every other key (theme, model and the rest) is not reported. String "
                 "values are shown as stored and nothing is redacted, secrets in env or in a command included. A "
                 "row shows what a file holds, not that a hook ran or that the file was loaded: the documentation "
                 "says some project keys wait until the user trusts the folder, and Claude Code Project Trust "
                 "shows the hasTrustDialogAccepted value stored for a project path. Evidence tier: the key names "
                 "are source-verified from https://code.claude.com/docs/en/settings-reference and the hooks layout "
                 "(event, then groups with a matcher and a hooks list holding type and command) from "
                 "https://code.claude.com/docs/en/hooks, both read on 15 November 2026. The hooks layout, "
                 "enabledPlugins and permissions allow and defaultMode were also seen in the settings.json of a "
                 "macOS 27.2.1 Mac. The artifact has not been run against a corpus image that holds hooks, env or "
                 "permission entries: the settings.json of windows11_arm_claude_code_sessions_known_20261109 holds "
                 "only theme and model, so it gives no rows. All 14 rows of the validation run came from a "
                 "settings.json written by hand for the test; hook prompt values, permissions ask and "
                 "additionalDirectories, disabledMcpjsonServers, extraKnownMarketplaces and settings.local.json "
                 "were not in that run.",
        "paths": ("*/.claude/settings.json", "*/.claude/settings.local.json"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
    },
    "claudeCodeMcpServers": {
        "name": "Claude Code MCP Servers",
        "description": "MCP server entries read from the mcpServers of any .mcp.json file and of .claude.json, at its "
                 "top level and under each project path, one row per server.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Claude Code",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "Scope is where the server was read: Project file for a .mcp.json (Project is its folder), User "
                 "for mcpServers at the top level of .claude.json, Local for mcpServers under a project path of "
                 ".claude.json (Project is that path). The Claude Code documentation describes these three places "
                 "(https://code.claude.com/docs/en/mcp, read on 15 November 2026); a server in a Project file is, "
                 "per that page, prompted for approval before use in interactive sessions. The approval keys in "
                 "settings files are shown by Claude Code Settings, and the same key names in a .claude.json "
                 "project entry by Claude Code Project Trust; in Claude Code 2.1.112 the approval prompt writes "
                 "them to the local settings file "
                 "(https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-2.1.112.tgz, package/cli.js, "
                 "line 8664) and a migration moves them out of the project entry (line 18088). Type is the type of "
                 "the entry as stored, blank when it has none. Command or URL is the command of the entry, or its "
                 "url when it has no command. Arguments, Environment and Headers are the args, env and headers of "
                 "the entry as compact JSON, blank when absent; they can hold tokens and are not redacted, and "
                 "other keys of an entry, such as headersHelper and oauth, are not reported. A row shows a "
                 "configured server, not that it was started, approved or connected. Servers declared inline in a "
                 "plugin's plugin.json, in managed settings or managed-mcp.json, or in settings files are not "
                 "read; a .mcp.json at a plugin root matches the path and is reported as Project file with the "
                 "plugin folder as Project. A .claude.json under a config folder set through CLAUDE_CONFIG_DIR is "
                 "read when its file name is .claude.json. Source File stays because it is the only column that "
                 "says which user's .claude.json a row came from. Evidence tier: data-proven on a .claude.json and "
                 "a .mcp.json made with claude mcp add in Claude Code 2.1.325 (the .claude.json records that "
                 "version; the host was an Ubuntu VM), one server of each scope, 3 rows; the files were made for "
                 "this artifact and have no corpus key. The .claude.json files of "
                 "windows11_arm_claude_code_sessions_known_20261109 hold no MCP server and that image holds no "
                 ".mcp.json, so no corpus image was used for these rows.",
        "paths": ("*/.mcp.json", "*/.claude.json"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "server",
    },
    "claudeCodeProjectTrust": {
        "name": "Claude Code Project Trust",
        "description": "The per-project entries of .claude.json: the stored hasTrustDialogAccepted value, the "
                 "enabledMcpjsonServers and disabledMcpjsonServers lists, allowedTools and the names of the MCP "
                 "servers stored for the project, one row per project path.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Claude Code",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per key of projects in each .claude.json. Project is the key as stored. On the Windows "
                 "known data, 1.0.123 wrote backslashes and 2.1.319 wrote forward slashes; Claude Code 2.1.112 "
                 "replaces backslashes with forward slashes in the key "
                 "(https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-2.1.112.tgz, package/cli.js, "
                 "line 136). Two spellings of one folder are two rows. Trust Dialog Accepted is "
                 "hasTrustDialogAccepted as stored. In Claude Code 2.1.112 (cli.js sha256 "
                 "bc3358282800e3e99daa8e71ac5b7b1566bd0d7ca7eb94f714a7859365d3163, lines counted at newline) a new "
                 "project entry starts with it false (line 513, anchor hasTrustDialogAccepted:!1), and the "
                 "function that tests it walks from the working folder up through its parent folders and treats "
                 "the folder as trusted when any of them holds true (line 500), so a true on a parent applies to "
                 "its subfolders. The same function returns trusted without reading an entry when the "
                 "CLAUDE_CODE_SANDBOXED environment variable is set, when trust was accepted for the session only, "
                 "and for a background session. Two places set it true: a function on line 500 and the accept "
                 "handler of the folder trust dialog on line 8664. That handler writes true unless the working "
                 "folder is the home folder, where the acceptance is kept for the session only and no entry is "
                 "written. A false or missing value therefore does not show the prompt was declined. No key of an "
                 "entry was identified as the time the prompt was answered, so a row does not say when; the "
                 "2.1.319 entries hold lastStartTime, which is not reported and whose meaning was not traced. "
                 "Enabled and Disabled .mcp.json Servers are enabledMcpjsonServers and disabledMcpjsonServers, "
                 "Allowed Tools is allowedTools and Local MCP Servers lists the names under mcpServers, all as "
                 "stored and joined with commas; the contents of those servers are in Claude Code MCP Servers. In "
                 "Claude Code 2.1.112 the two .mcp.json lists are moved from the entry to the local settings file "
                 "(line 18088), so an empty list here does not show that no server was approved or rejected. Other "
                 "keys of the entry (usage figures, session ids, history) are not reported here; the prompt "
                 "history is read by Claude Code Prompt History (.claude.json). Backup copies of .claude.json "
                 "under other file names are not read. Source File stays because it is the only column that says "
                 "which user's .claude.json a row came from. Evidence tier: data-proven on the .claude.json files "
                 "of windows11_arm_claude_code_sessions_known_20261109 (Claude Code 2.1.319 in one file; 1.0.123 "
                 "per the corpus registry, the file itself holds no version key): 4 entries, three with "
                 "hasTrustDialogAccepted true and one false, and a .claude.json made with claude mcp add in Claude "
                 "Code 2.1.325 (not a corpus image; made for this artifact): 1 entry, false. In a run over these "
                 "files, 5 rows, 3 true and 2 false, Enabled .mcp.json Servers, Disabled .mcp.json Servers and "
                 "Allowed Tools were empty on all 5 rows and CLAUDE.md External Includes Approved held false on "
                 "all 5 rows; its writers were not traced. The known data holds no approval or allowed tool, so "
                 "those columns are untested against a populated entry. Code statements hold for 2.1.112 only.",
        "paths": ("*/.claude.json",),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "shield",
    },
}

import json
import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import fold_view_rows, unique_sources

_SIMPLE_KEYS = ('apiKeyHelper', 'enableAllProjectMcpServers', 'enabledMcpjsonServers', 'disabledMcpjsonServers',
                'enabledPlugins', 'extraKnownMarketplaces')
_PERMISSION_LISTS = ('allow', 'ask', 'deny', 'additionalDirectories')


def _json_text(value):
    """A settings value as the text it holds: strings as they are, anything else as compact JSON."""
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def _load(path, label):
    """The JSON object in path, or None (logged) when it cannot be read as one."""
    try:
        with open(path, 'rb') as handle:
            data = json.loads(handle.read().decode('utf-8-sig'))
    except (OSError, ValueError) as error:
        logfunc(f'{label}: {path} could not be read as JSON ({type(error).__name__})')
        return None
    if not isinstance(data, dict):
        logfunc(f'{label}: {path} holds JSON that is not an object')
        return None
    return data


def _names(value):
    return ', '.join(str(v) for v in value) if isinstance(value, list) else _json_text(value)


def _hook_rows(hooks):
    """(event, matcher, type, value) per hook of a settings hooks object."""
    if not isinstance(hooks, dict):
        return [('hooks', '', '', '', _json_text(hooks))]
    rows = []
    for event, groups in hooks.items():
        for group in groups if isinstance(groups, list) else [groups]:
            if not isinstance(group, dict):
                rows.append(('hooks', event, '', '', _json_text(group)))
                continue
            matcher = _json_text(group.get('matcher'))
            members = group.get('hooks')
            for hook in members if isinstance(members, list) else []:
                if not isinstance(hook, dict):
                    rows.append(('hooks', event, matcher, '', _json_text(hook)))
                    continue
                value = next((hook[k] for k in ('command', 'url', 'prompt') if hook.get(k) is not None),
                             {k: v for k, v in hook.items() if k != 'type'})
                rows.append(('hooks', event, matcher, _json_text(hook.get('type')), _json_text(value)))
    return rows


def _settings_rows(data):
    rows = []
    if 'hooks' in data:
        rows.extend(_hook_rows(data['hooks']))
    if 'statusLine' in data:
        status = data['statusLine']
        if isinstance(status, dict):
            rows.append(('statusLine', '', '', _json_text(status.get('type')),
                         _json_text(status.get('command', {k: v for k, v in status.items() if k != 'type'}))))
        else:
            rows.append(('statusLine', '', '', '', _json_text(status)))
    if 'env' in data:
        env = data['env']
        if isinstance(env, dict):
            rows.extend(('env', name, '', '', _json_text(value)) for name, value in env.items())
        else:
            rows.append(('env', '', '', '', _json_text(env)))
    if 'permissions' in data:
        permissions = data['permissions']
        if isinstance(permissions, dict):
            for item in _PERMISSION_LISTS:
                values = permissions.get(item)
                for rule in values if isinstance(values, list) else ([] if values is None else [values]):
                    rows.append(('permissions', item, '', '', _json_text(rule)))
            if 'defaultMode' in permissions:
                rows.append(('permissions', 'defaultMode', '', '', _json_text(permissions['defaultMode'])))
        else:
            rows.append(('permissions', '', '', '', _json_text(permissions)))
    for key in _SIMPLE_KEYS:
        if key in data:
            rows.append((key, '', '', '', _json_text(data[key])))
    return rows


def _server_row(scope, project, name, server):
    if not isinstance(server, dict):
        return (scope, project, name, '', _json_text(server), '', '', '')
    return (scope, project, name, _json_text(server.get('type')),
            _json_text(server.get('command') if server.get('command') is not None else server.get('url')),
            _json_text(server.get('args')), _json_text(server.get('env')), _json_text(server.get('headers')))


def _server_rows(path, data):
    rows = []
    if os.path.basename(path) == '.mcp.json':
        servers = data.get('mcpServers')
        folder = os.path.dirname(path)
        for name, server in (servers.items() if isinstance(servers, dict) else []):
            rows.append(_server_row('Project file', folder, name, server))
        return rows
    servers = data.get('mcpServers')
    for name, server in (servers.items() if isinstance(servers, dict) else []):
        rows.append(_server_row('User', '', name, server))
    projects = data.get('projects')
    for project, entry in (projects.items() if isinstance(projects, dict) else []):
        servers = entry.get('mcpServers') if isinstance(entry, dict) else None
        for name, server in (servers.items() if isinstance(servers, dict) else []):
            rows.append(_server_row('Local', project, name, server))
    return rows


def _trust_rows(data):
    rows = []
    projects = data.get('projects')
    for project, entry in (projects.items() if isinstance(projects, dict) else []):
        if not isinstance(entry, dict):
            continue
        servers = entry.get('mcpServers')
        rows.append((project, _json_text(entry.get('hasTrustDialogAccepted')),
                     _names(entry.get('enabledMcpjsonServers')), _names(entry.get('disabledMcpjsonServers')),
                     _names(entry.get('allowedTools')), ', '.join(servers) if isinstance(servers, dict) else '',
                     _json_text(entry.get('hasClaudeMdExternalIncludesApproved'))))
    return rows


def _run(context, names, label, extract):
    """(rows, read paths): extract(path, data) rows plus the relative source, folded across volume views."""
    wanted = [p for p in context.get_files_found() if os.path.basename(str(p)) in names]
    paths, _skipped = unique_sources(context, wanted, label=label)
    data_list, read = [], []
    for path in paths:
        data = _load(path, label)
        if data is None:
            continue
        read.append(path)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in extract(path, data))
    return fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def claudeCodeSettings(context):
    data_headers = ('Setting', 'Item', 'Matcher', 'Type', 'Value', 'Source File')
    rows, located = _run(context, ('settings.json', 'settings.local.json'), 'Claude Code Settings',
                         lambda _path, data: _settings_rows(data))
    # settings.json outside a .claude folder is not this artifact's: the paths already require one.
    return data_headers, rows, located


@artifact_processor
def claudeCodeMcpServers(context):
    data_headers = ('Scope', 'Project', 'Server', 'Type', 'Command or URL', 'Arguments', 'Environment',
                    'Headers', 'Source File')
    rows, located = _run(context, ('.mcp.json', '.claude.json'), 'Claude Code MCP Servers',
                         lambda path, data: [row[:1] + (context.get_relative_path(row[1]) if row[0] == 'Project file'
                                                        else row[1],) + row[2:] for row in _server_rows(path, data)])
    return data_headers, rows, located


@artifact_processor
def claudeCodeProjectTrust(context):
    data_headers = ('Project', 'Trust Dialog Accepted (as stored)', 'Enabled .mcp.json Servers',
                    'Disabled .mcp.json Servers', 'Allowed Tools', 'Local MCP Servers',
                    'CLAUDE.md External Includes Approved (as stored)', 'Source File')
    rows, located = _run(context, ('.claude.json',), 'Claude Code Project Trust',
                         lambda _path, data: _trust_rows(data))
    return data_headers, rows, located
