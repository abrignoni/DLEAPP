"""Pin the Claude Code Prompt History artifact (scripts/artifacts/claudeCodeHistory.py).

The lines are built in the shape Claude Code 2.1.319 wrote on windows11_arm_claude_code_history_known_20261108:
display, pastedContents, timestamp (Unix milliseconds), project and sessionId, a short paste stored in the line and
a long one stored as a contentHash naming paste-cache/<contentHash>.txt.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import claudeCodeHistory as cc
# pylint: enable=wrong-import-position

LONG = 'cached paste line\n' * 80
LONG_HASH = hashlib.sha256(LONG.encode()).hexdigest()[:16]


def line(display, pasted=None, ts=1794179732903, session='s-1', project='C:\\kd\\p', **extra):
    entry = {'display': display, 'pastedContents': pasted or {}, 'timestamp': ts, 'project': project,
             'sessionId': session}
    entry.update(extra)
    return json.dumps(entry).encode()


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


class RowsTest(unittest.TestCase):
    def rows(self, data, files=None):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        found = [write(root, name, body) for name, body in (files or {}).items()]
        paste_dir = os.path.normcase(os.path.normpath(os.path.join(root, '.claude', 'paste-cache')))
        available = {os.path.normcase(os.path.normpath(p)): p for p in found}
        counts, used = Counter(), []
        return cc.history_rows(data, paste_dir, available, counts, used), counts, used

    def test_millisecond_time_and_fields(self):
        rows, counts, _ = self.rows(line('/model haiku', ts=1794179723638) + b'\n')
        self.assertEqual(rows, [(datetime(2026, 11, 8, 23, 15, 23, 638000, tzinfo=timezone.utc), '/model haiku',
                                 '', '', 'C:\\kd\\p', 's-1', 1)])
        self.assertEqual(counts, Counter())

    def test_inline_and_cached_pastes(self):
        data = b'\n'.join([
            line('two [Pasted text #1 +11 lines]', {'1': {'id': 1, 'type': 'text', 'content': 'short\ntext'}}),
            line('three [Pasted text #2 +79 lines]', {'2': {'id': 2, 'type': 'text', 'contentHash': LONG_HASH}}),
        ]) + b'\n'
        rows, counts, used = self.rows(data, {f'.claude/paste-cache/{LONG_HASH}.txt': LONG})
        self.assertEqual(rows[0][2:4], ('[#1] short\ntext', ''))
        self.assertEqual(rows[1][2:4], (f'[#2] {LONG}', f'{LONG_HASH}.txt'))
        self.assertEqual([os.path.basename(p) for p in used], [f'{LONG_HASH}.txt'])
        self.assertEqual(counts, Counter())

    def test_missing_and_mismatched_paste_files(self):
        data = b'\n'.join([
            line('gone', {'1': {'id': 1, 'type': 'text', 'contentHash': '0123456789abcdef'}}),
            line('wrong', {'1': {'id': 1, 'type': 'text', 'contentHash': 'fedcba9876543210'}}),
        ])
        rows, counts, _ = self.rows(data, {'.claude/paste-cache/fedcba9876543210.txt': 'not this hash'})
        self.assertEqual(rows[0][2:4], ('[#1] (paste-cache file 0123456789abcdef.txt not found)',
                                        '0123456789abcdef.txt (not found)'))
        self.assertEqual(rows[1][2:4], ('[#1] not this hash',
                                        'fedcba9876543210.txt (SHA-256 does not start with its name)'))
        self.assertEqual(counts['pastes whose paste-cache file is not in the extraction'], 1)
        self.assertEqual(counts['paste-cache files whose name does not match their SHA-256'], 1)

    def test_bad_lines_are_counted_not_reported(self):
        data = line('kept') + b'\n{"display": "cut off\n[1, 2]\n\n' + line('extra', ts=5, mode='x') + b'\n'
        rows, counts, _ = self.rows(data)
        self.assertEqual([(r[1], r[6]) for r in rows], [('kept', 1), ('extra', 5)])
        self.assertEqual(counts['lines that are not JSON, not reported'], 1)
        self.assertEqual(counts['lines that are not a JSON object, not reported'], 1)
        self.assertEqual(counts['lines with fields beyond display, pastedContents, timestamp, project and sessionId'], 1)

    def test_non_integer_time_is_kept(self):
        self.assertEqual(cc.history_time('2026-11-08'), '2026-11-08')
        self.assertEqual(cc.history_time(True), True)
        self.assertIsNone(cc.history_time(None))


class ArtifactTest(unittest.TestCase):
    def test_paste_never_comes_from_another_profile(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        pasted = {'1': {'id': 1, 'type': 'text', 'contentHash': LONG_HASH}}
        paths = [
            write(root, 'Users/a/.claude/history.jsonl', line('a [Pasted text #1]', pasted) + b'\n'),
            write(root, f'Users/a/.claude/paste-cache/{LONG_HASH}.txt', LONG),
            write(root, 'Users/b/.claude/history.jsonl', line('b [Pasted text #1]', pasted, session='s-2') + b'\n'),
        ]
        _headers, rows, source = cc.claudeCodeHistory.__wrapped__(FakeContext(paths, root))
        by_user = {r[7].split('/')[1]: r for r in rows}
        self.assertEqual(by_user['a'][3], f'{LONG_HASH}.txt')
        self.assertEqual(by_user['b'][3], f'{LONG_HASH}.txt (not found)')
        self.assertEqual([os.path.relpath(p, root).replace(os.sep, '/') for p in source.split('\n')],
                         ['Users/a/.claude/history.jsonl', f'Users/a/.claude/paste-cache/{LONG_HASH}.txt',
                          'Users/b/.claude/history.jsonl'])


if __name__ == '__main__':
    unittest.main()
