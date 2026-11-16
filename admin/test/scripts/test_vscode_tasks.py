"""Pin the VS Code Tasks and Trusted Folders artifacts (scripts/artifacts/vscodeTasks.py).

The tasks.json text and the state.vscdb rows are made up, in the layouts of the VS Code source
(workspaceTrust.ts at daa23473) and of one state.vscdb from a Mac.
"""
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import vscodeTasks as vt
# pylint: enable=wrong-import-position

TASKS = '''{
    // a comment with "quotes" and a trailing comma below
    "version": "2.0.0",
    "tasks": [
        {
            "label": "build /* not a comment */",
            "type": "shell",
            "command": "echo http://example.invalid/a",
            "args": ["-x", "y"],
            "runOptions": { "runOn": "folderOpen", },
            "windows": { "command": "cmd /c echo win" },
        },
        { "type": "npm", "script": "start" }, /* block */
    ],
}
'''


class Strip(unittest.TestCase):
    def test_strip_keeps_strings(self):
        data = json.loads(vt.strip_jsonc('{"a": "x // y /* z */", /* c */ "b": [1, 2,],}'))
        self.assertEqual(data, {'a': 'x // y /* z */', 'b': [1, 2]})

    def test_escaped_quote_in_string(self):
        self.assertEqual(json.loads(vt.strip_jsonc('{"a": "q\\" // still string",}')), {'a': 'q" // still string'})


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def path(self, rel):
        path = os.path.join(self.folder.name, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def run_artifact(self, func, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(vt, 'logfunc') as log, mock.patch('scripts.macos_plists.logfunc'):
            result = func.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_tasks(self):
        path = self.path('Users/a/proj/.vscode/tasks.json')
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(TASKS)
        (headers, rows, located), _ = self.run_artifact(vt.vscodeTasks, [path])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(len(headers), 10)
        self.assertEqual(rows, [
            ('build /* not a comment */', 'shell', 'echo http://example.invalid/a', '["-x","y"]', '', 'folderOpen', '',
             '{"windows":{"command":"cmd /c echo win"}}', 'a', rel),
            ('', 'npm', '', '', '', '', '', '', 'a', rel)])
        self.assertEqual(located, path)

    def test_broken_file_is_logged(self):
        path = self.path('p/.vscode/tasks.json')
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write('{"tasks": [')
        (_, rows, located), log = self.run_artifact(vt.vscodeTasks, [path])
        self.assertEqual((rows, located), ([], ''))
        self.assertTrue(any('could not be read' in m for m in log))

    def trust_db(self, rel, value, table=True):
        path = self.path(rel)
        db = sqlite3.connect(path)
        if table:
            db.execute('CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)')
            db.execute('INSERT INTO ItemTable VALUES (?, ?)', ('content.trust.model.key', value))
            db.execute('INSERT INTO ItemTable VALUES (?, ?)', ('other.key', '{"uriTrustInfo": [{"uri": {"path": "/no"}}]}'))
        else:
            db.execute('CREATE TABLE other (x)')
        db.commit()
        db.close()
        return path

    def test_trusted_folders(self):
        value = json.dumps({'uriTrustInfo': [
            {'uri': {'$mid': 1, 'path': '/made/up/one', 'scheme': 'file'}, 'trusted': True},
            {'uri': {'$mid': 1, 'fsPath': 'c:\\made\\two', 'path': '/c:/made/two', 'scheme': 'file'}, 'trusted': True},
            {'uri': 'bad'}]})
        path = self.trust_db('Users/a/Library/Application Support/Code/User/globalStorage/state.vscdb', value)
        (_, rows, _), _ = self.run_artifact(vt.vscodeTrustedFolders, [path, path + '-wal'])
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(rows, [('/made/up/one', 'file', 'true', 'a', rel), ('c:\\made\\two', 'file', 'true', 'a', rel)])

    def test_no_table_or_bad_value(self):
        path = self.trust_db('Users/a/User/globalStorage/state.vscdb', 'x', table=False)
        (_, rows, located), log = self.run_artifact(vt.vscodeTrustedFolders, [path])
        self.assertEqual((rows, located), ([], ''))
        self.assertTrue(any('no ItemTable' in m for m in log))
        path = self.trust_db('Users/b/User/globalStorage/state.vscdb', 'not json')
        (_, rows, _), log = self.run_artifact(vt.vscodeTrustedFolders, [path])
        self.assertEqual(rows, [])
        self.assertTrue(any('not JSON' in m for m in log))

    def test_paths(self):
        import fnmatch  # pylint: disable=import-outside-toplevel
        spec = vt.__artifacts_v2__
        tasks = spec['vscodeTasks']['paths']
        for good in ('root/p/.vscode/tasks.json', 'root/x/Code/User/tasks.json', 'root/x/Code/User/profiles/ab1/tasks.json'):
            self.assertTrue(any(fnmatch.fnmatchcase(good, p) for p in tasks), good)
        self.assertFalse(any(fnmatch.fnmatchcase('root/p/tasks.json', p) for p in tasks))
        self.assertTrue(any(fnmatch.fnmatchcase('root/x/Code/User/globalStorage/state.vscdb-wal', p)
                            for p in spec['vscodeTrustedFolders']['paths']))
        self.assertFalse(any(fnmatch.fnmatchcase('root/x/Code/User/globalStorage/state.vscdb.backup', p)
                             for p in spec['vscodeTrustedFolders']['paths']))


if __name__ == '__main__':
    unittest.main()
