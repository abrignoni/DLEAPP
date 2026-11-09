"""Pin the Claude Code session artifacts (scripts/artifacts/claudeCodeSessions.py).

Every record here is constructed in the shapes Claude Code 2.1.319 and 1.0.123 wrote on
windows11_arm_claude_code_sessions_known_20261109; none is copied from that capture.
"""
import base64
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import claudeCodeSessions as cs
# pylint: enable=wrong-import-position

SID = '11111111-2222-3333-4444-555555555555'
PNG = base64.b64encode(b'\x89PNG\r\n\x1a\n not really a picture').decode()


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def write(root, relative, data):
    path = os.path.join(root, *relative.split('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode())
    return path


def jsonl(*records):
    return '\n'.join(json.dumps(r) for r in records) + '\n'


def user(text_or_blocks, ts='2026-11-09T00:57:51.801Z', **extra):
    record = {'type': 'user', 'sessionId': SID, 'timestamp': ts, 'uuid': 'u', 'cwd': 'C:\\p',
              'message': {'role': 'user', 'content': text_or_blocks}}
    record.update(extra)
    return record


def assistant(blocks, ts='2026-11-09T00:57:52.000Z', **extra):
    record = {'type': 'assistant', 'sessionId': SID, 'timestamp': ts, 'uuid': 'a', 'cwd': 'C:\\p',
              'message': {'role': 'assistant', 'model': 'm-test', 'content': blocks}}
    record.update(extra)
    return record


class TreeTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.paths = []

    def add(self, relative, data):
        self.paths.append(write(self.root, relative, data))

    def run_artifact(self, func):
        return func.__wrapped__(FakeContext(self.paths, self.root))


class MessagesTest(TreeTest):
    def test_rows_tools_media_and_skips(self):
        self.add(f'u/.claude/projects/C--p/{SID}.jsonl', jsonl(
            {'type': 'mode', 'sessionId': SID, 'mode': 'x'},
            user('first prompt'),
            assistant([{'type': 'thinking', 'thinking': '', 'signature': 's'}]),
            assistant([{'type': 'tool_use', 'id': 't', 'name': 'Read', 'input': {'file_path': 'C:\\p\\i.png'}}]),
            user([{'type': 'tool_result', 'tool_use_id': 't', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': PNG}}]}]),
            assistant([{'type': 'text', 'text': 'Red.'}]),
            user('<local-command-caveat>x</local-command-caveat>', isMeta=True),
        ) + 'not json\n')
        with mock.patch.object(cs, 'check_in_embedded_media', return_value='media/x.png') as media, \
                mock.patch.object(cs, 'logfunc') as log:
            _headers, rows, source = self.run_artifact(cs.claudeCodeMessages)
        self.assertEqual([(r[1], r[3], r[4], r[5], r[6], r[9]) for r in rows], [
            ('user', 'first prompt', '', '', '', ''),
            ('assistant', '', '', 'Read: {"file_path": "C:\\\\p\\\\i.png"}', '', ''),
            ('user', '', 'media/x.png', '', '[image]', ''),
            ('assistant', 'Red.', '', '', '', ''),
            ('user', '<local-command-caveat>x</local-command-caveat>', '', '', '', 'Yes'),
        ])
        self.assertEqual(media.call_args[0][1], base64.b64decode(PNG))
        self.assertIn('1 assistant records holding only a thinking block with no text, not reported',
                      log.call_args[0][0])
        self.assertIn('1 transcript lines that are not JSON, skipped', log.call_args[0][0])
        self.assertEqual(rows[0][0].isoformat(), '2026-11-09T00:57:51.801000+00:00')
        self.assertEqual(source, self.paths[0])

    def test_old_client_api_error_shape(self):
        self.add(f'u/.claude/projects/C--p/{SID}.jsonl', jsonl(
            user('old prompt'),
            assistant([{'type': 'text', 'text': 'API Error: 404'}], isApiErrorMessage=True),
        ))
        with mock.patch.object(cs, 'logfunc'):
            _headers, rows, _source = self.run_artifact(cs.claudeCodeMessages)
        self.assertEqual([(r[1], r[3], r[8]) for r in rows], [('user', 'old prompt', ''),
                                                               ('assistant', 'API Error: 404', 'Yes')])


class SessionsTest(TreeTest):
    def test_session_row_and_subagent(self):
        self.add(f'u/.claude/projects/C--p/{SID}.jsonl', jsonl(
            {'type': 'session-owner', 'sessionId': SID, 'accountUuid': 'acc', 'organizationUuid': 'org'},
            {'type': 'ai-title', 'sessionId': SID, 'aiTitle': 'Title one'},
            user('p1', version='2.1.319', gitBranch='HEAD'),
            assistant([{'type': 'tool_use', 'name': 'Agent', 'input': {}}], ts='2026-11-09T00:59:00.000Z'),
            user('<x>', isMeta=True, timestamp='not a time'),
        ))
        self.add(f'u/.claude/projects/C--p/{SID}/subagents/agent-abc.jsonl', jsonl(
            user('count', agentId='abc', isSidechain=True),
            assistant([{'type': 'text', 'text': '2'}], agentId='abc', isSidechain=True)))
        self.add(f'u/.claude/projects/C--p/{SID}/subagents/agent-abc.meta.json', '{"agentType": "Explore"}')
        with mock.patch.object(cs, 'logfunc'):
            _headers, rows, source = self.run_artifact(cs.claudeCodeSessions)
        main, sub = sorted(rows, key=lambda r: r[3])
        self.assertEqual(main[2:16], (SID, '', '', 'Title one', 'C:\\p', 'HEAD', '2.1.319', 'm-test', 1, 1, 0,
                                      'Agent (1)', 'acc', 'org'))
        self.assertEqual((main[0].isoformat(), main[1].isoformat()),
                         ('2026-11-09T00:57:51.801000+00:00', '2026-11-09T00:59:00+00:00'))
        self.assertEqual(sub[2:5], (SID, 'abc', 'Explore'))
        self.assertEqual(len(source.split('\n')), 3)


class FileHistoryTest(TreeTest):
    def test_versions_resolved_in_own_session_folder(self):
        other = '99999999-2222-3333-4444-555555555555'
        snapshot = {'type': 'file-history-snapshot', 'messageId': 'm', 'snapshot': {'trackedFileBackups': {
            'note.txt': {'backupFileName': 'abcd@v2', 'version': 2, 'backupTime': '2026-11-09T00:58:54.811Z',
                         'realParentDir': 'C:\\p'}}}}
        delta = {'type': 'file-history-delta', 'trackingPath': 'note.txt',
                 'backup': {'backupFileName': None, 'version': 1, 'backupTime': '2026-11-09T00:57:55.981Z',
                            'realParentDir': 'C:\\p'}}
        self.add(f'u/.claude/projects/C--p/{SID}.jsonl', jsonl(user('p'), delta, snapshot, snapshot))
        self.add(f'u/.claude/file-history/{SID}/abcd@v2', 'kept copy\n')
        self.add(f'u/.claude/file-history/{other}/abcd@v2', 'another session')
        with mock.patch.object(cs, 'logfunc'):
            _headers, rows, _source = self.run_artifact(cs.claudeCodeFileHistory)
        self.assertEqual([(r[2], r[4], r[5], r[6]) for r in rows], [
            ('note.txt', 1, '', '(no copy: the file did not exist when this version was recorded)'),
            ('note.txt', 2, 'abcd@v2', 'kept copy\n')])

    def test_missing_backup(self):
        snapshot = {'type': 'file-history-snapshot', 'snapshot': {'trackedFileBackups': {
            'gone.txt': {'backupFileName': 'ffff@v1', 'version': 1, 'backupTime': '2026-11-09T01:00:00Z'}}}}
        self.add(f'u/.claude/projects/C--p/{SID}.jsonl', jsonl(user('p'), snapshot))
        with mock.patch.object(cs, 'logfunc') as log:
            _headers, rows, _source = self.run_artifact(cs.claudeCodeFileHistory)
        self.assertEqual(rows[0][5:7], ('ffff@v1 (not found)', '(backup file ffff@v1 not found)'))
        self.assertIn('backups whose file is not in the extraction', log.call_args[0][0])


class ConfigHistoryTest(unittest.TestCase):
    def test_rows(self):
        config = {'oauthAccount': {'emailAddress': 'x'}, 'projects': {
            'C:\\a': {'history': [
                {'display': '/exit ', 'pastedContents': {}},
                {'display': 'long [Pasted text #1 +39 lines]', 'pastedContents': {
                    '1': {'id': 1, 'type': 'text', 'content': 'pasted body'}}},
                {'display': 'older [Pasted text +3 lines]', 'pastedText': 'legacy body'},
                'bare string entry', 42], 'lastSessionId': 's1'},
            'C:\\b': {'allowedTools': []}}}
        counts = Counter()
        rows = cs.config_history_rows(config, counts)
        self.assertEqual(rows, [('C:\\a', 1, '/exit ', '', 's1'),
                                ('C:\\a', 2, 'long [Pasted text #1 +39 lines]', '[#1] pasted body', 's1'),
                                ('C:\\a', 3, 'older [Pasted text +3 lines]', 'legacy body', 's1'),
                                ('C:\\a', 4, 'bare string entry', '', 's1')])
        self.assertEqual(counts['history entries that are neither text nor an object, skipped'], 1)

    def test_artifact_reads_only_dot_claude_json(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        paths = [write(root, 'u/.claude.json', json.dumps({'projects': {'C:\\a': {'history': [{'display': 'x'}]}}})),
                 write(root, 'u/.claude.json.backup', json.dumps({'projects': {'C:\\a': {'history': [{'display': 'y'}]}}}))]
        with mock.patch.object(cs, 'logfunc'):
            _headers, rows, source = cs.claudeCodeConfigHistory.__wrapped__(FakeContext(paths, root))
        self.assertEqual(rows, [('C:\\a', 1, 'x', '', '', 'u/.claude.json')])
        self.assertEqual(source, paths[0])


if __name__ == '__main__':
    unittest.main()
