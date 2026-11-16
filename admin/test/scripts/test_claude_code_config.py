"""Pin the Claude Code configuration artifacts (scripts/artifacts/claudeCodeConfig.py).

The files are written for the test in the layouts the Claude Code documentation and Claude Code 2.1.325 use;
every value is made up.
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import claudeCodeConfig as cc
# pylint: enable=wrong-import-position

SETTINGS = {
    'theme': 'dark',
    'hooks': {'PostToolUse': [{'matcher': 'Edit|Write', 'hooks': [
        {'type': 'command', 'command': 'echo made-up', 'timeout': 5},
        {'type': 'http', 'url': 'https://example.invalid/hook'}]}],
              'Stop': [{'hooks': [{'type': 'command', 'command': 'true'}]}]},
    'statusLine': {'type': 'command', 'command': 'echo status'},
    'env': {'MADE_UP_VAR': 'value-1', 'COUNT': 3},
    'apiKeyHelper': 'echo helper',
    'permissions': {'allow': ['Bash(ls:*)', 'Read(*)'], 'deny': ['Read(.env)'], 'defaultMode': 'acceptEdits'},
    'enabledMcpjsonServers': ['one'], 'enableAllProjectMcpServers': True,
    'enabledPlugins': {'p@m': True},
}
CLAUDE_JSON = {
    'mcpServers': {'user-stdio': {'type': 'stdio', 'command': '/usr/bin/env', 'args': ['echo', 'hello'], 'env': {}}},
    'projects': {
        '/work/a': {'hasTrustDialogAccepted': True, 'enabledMcpjsonServers': ['one'], 'disabledMcpjsonServers': [],
                    'allowedTools': [], 'hasClaudeMdExternalIncludesApproved': False,
                    'mcpServers': {'local-http': {'type': 'http', 'url': 'https://example.invalid/l',
                                                  'headers': {'X-Lab': '1'}}}},
        '/work/b': {'hasTrustDialogAccepted': False, 'mcpServers': {}}}}
MCP_JSON = {'mcpServers': {'proj-http': {'type': 'http', 'url': 'https://example.invalid/mcp'},
                           'proj-cmd': {'command': 'node', 'args': ['s.js'], 'env': {'K': 'v'}}}}


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write(self, rel, data):
        path = os.path.join(self.folder.name, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(data if isinstance(data, str) else json.dumps(data))
        return path

    def run_artifact(self, func, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(cc, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'):
            result = func.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_settings_rows(self):
        path = self.write('Users/a/.claude/settings.json', SETTINGS)
        (headers, rows, located), _ = self.run_artifact(cc.claudeCodeSettings, [path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 6)
        self.assertEqual(rows, [
            ('hooks', 'PostToolUse', 'Edit|Write', 'command', 'echo made-up', rel),
            ('hooks', 'PostToolUse', 'Edit|Write', 'http', 'https://example.invalid/hook', rel),
            ('hooks', 'Stop', '', 'command', 'true', rel),
            ('statusLine', '', '', 'command', 'echo status', rel),
            ('env', 'MADE_UP_VAR', '', '', 'value-1', rel),
            ('env', 'COUNT', '', '', '3', rel),
            ('permissions', 'allow', '', '', 'Bash(ls:*)', rel),
            ('permissions', 'allow', '', '', 'Read(*)', rel),
            ('permissions', 'deny', '', '', 'Read(.env)', rel),
            ('permissions', 'defaultMode', '', '', 'acceptEdits', rel),
            ('apiKeyHelper', '', '', '', 'echo helper', rel),
            ('enableAllProjectMcpServers', '', '', '', 'true', rel),
            ('enabledMcpjsonServers', '', '', '', '["one"]', rel),
            ('enabledPlugins', '', '', '', '{"p@m":true}', rel)])
        self.assertEqual(located, path)
        self.assertNotIn('theme', ' '.join(r[0] for r in rows))

    def test_settings_unusual_shapes_do_not_crash(self):
        path = self.write('p/.claude/settings.local.json',
                          {'hooks': 'x', 'env': [1], 'permissions': 'y', 'statusLine': 'z'})
        (_, rows, _), _ = self.run_artifact(cc.claudeCodeSettings, [path])
        self.assertEqual([r[0] for r in rows], ['hooks', 'statusLine', 'env', 'permissions'])

    def test_broken_json_is_logged_and_skipped(self):
        path = self.write('p/.claude/settings.json', '{"hooks": ')
        (_, rows, located), log = self.run_artifact(cc.claudeCodeSettings, [path])
        self.assertEqual((rows, located), ([], ''))
        self.assertTrue(any('could not be read as JSON' in m for m in log))

    def test_mcp_servers_by_scope(self):
        mcp = self.write('Users/a/proj/.mcp.json', MCP_JSON)
        cfg = self.write('Users/a/.claude.json', CLAUDE_JSON)
        (_, rows, _), _ = self.run_artifact(cc.claudeCodeMcpServers, [mcp, cfg])
        by_scope = {(r[0], r[2]): r for r in rows}
        self.assertEqual(len(rows), 4)
        self.assertEqual(by_scope[('Project file', 'proj-http')][1], 'Users/a/proj')
        self.assertEqual(by_scope[('Project file', 'proj-http')][4], 'https://example.invalid/mcp')
        self.assertEqual(by_scope[('Project file', 'proj-cmd')][4:7], ('node', '["s.js"]', '{"K":"v"}'))
        self.assertEqual(by_scope[('User', 'user-stdio')][1:7], ('', 'user-stdio', 'stdio', '/usr/bin/env',
                                                                '["echo","hello"]', '{}'))
        self.assertEqual(by_scope[('Local', 'local-http')][1], '/work/a')
        self.assertEqual(by_scope[('Local', 'local-http')][7], '{"X-Lab":"1"}')

    def test_project_trust(self):
        cfg = self.write('Users/a/.claude.json', CLAUDE_JSON)
        (_, rows, _), _ = self.run_artifact(cc.claudeCodeProjectTrust, [cfg])
        rel = os.path.relpath(cfg, self.folder.name)
        self.assertEqual(rows, [('/work/a', 'true', 'one', '', '', 'local-http', 'false', rel),
                                ('/work/b', 'false', '', '', '', '', '', rel)])

    def test_each_artifact_ignores_the_other_files(self):
        cfg = self.write('Users/a/.claude.json', CLAUDE_JSON)
        mcp = self.write('Users/a/proj/.mcp.json', MCP_JSON)
        (_, rows, _), _ = self.run_artifact(cc.claudeCodeProjectTrust, [cfg, mcp])
        self.assertEqual(len(rows), 2)

    def test_identical_views_read_once(self):
        own = self.write('Users/a/.claude.json', CLAUDE_JSON)
        view = self.write('System/Volumes/Data/Users/a/.claude.json', CLAUDE_JSON)
        (_, rows, located), _ = self.run_artifact(cc.claudeCodeProjectTrust, [view, own])
        self.assertEqual(len(rows), 2)
        self.assertNotIn('\n', located)

    def test_paths(self):
        import fnmatch  # pylint: disable=import-outside-toplevel
        spec = cc.__artifacts_v2__
        self.assertTrue(any(fnmatch.fnmatchcase('root/Users/a/.claude/settings.local.json', p)
                            for p in spec['claudeCodeSettings']['paths']))
        self.assertFalse(any(fnmatch.fnmatchcase('root/Users/a/.claude.json.backup', p)
                             for p in spec['claudeCodeProjectTrust']['paths']))
        self.assertTrue(any(fnmatch.fnmatchcase('root/a/b/.mcp.json', p) for p in spec['claudeCodeMcpServers']['paths']))


if __name__ == '__main__':
    unittest.main()
