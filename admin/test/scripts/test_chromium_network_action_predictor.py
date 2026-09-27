"""Pin the rows scripts/artifacts/chromiumNetworkActionPredictor.py reads.

The databases are built here with the table Chromium creates
(autocomplete_action_predictor_table.cc), and the expected rows are written out.
"""
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import chromiumNetworkActionPredictor as nap  # pylint: disable=wrong-import-position

_CHROME = 'Users/someone/AppData/Local/Google/Chrome/User Data'
_CREATE = ('CREATE TABLE network_action_predictor ( id TEXT PRIMARY KEY, user_text TEXT, url TEXT, '
           'number_of_hits INTEGER, number_of_misses INTEGER)')


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _database(self, relative, rows, create=_CREATE):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path)
        with db:
            if create:
                db.execute(create)
                db.executemany('INSERT INTO network_action_predictor VALUES (?, ?, ?, ?, ?)', rows)
        db.close()
        self.files.append(str(path))

    def _run(self):
        logs = []
        with mock.patch.object(nap, 'logfunc', logs.append), \
                mock.patch.object(macos_plists, 'logfunc', logs.append):
            result = nap.chromiumNetworkActionPredictor.__wrapped__(FakeContext(self.root, self.files))
        return result + (logs,)

    def test_rows_are_read_per_profile_in_text_and_url_order(self):
        self._database(f'{_CHROME}/Default/Network Action Predictor', [
            ('b', 'fa', 'https://www.facebook.com/', 2, 1),
            ('a', 'f', 'https://www.facebook.com/', 0, 3),
            ('c', 'f', 'https://example.com/', 1, 0),
        ])
        self._database(f'{_CHROME}/Guest Profile/Network Action Predictor', [])
        self._database('Users/someone/AppData/Local/Packages/App/LocalState/EBWebView/Default/'
                       'Network Action Predictor', [('d', 'x', 'https://x.example/', 1, 0)])
        headers, rows, source, logs = self._run()
        self.assertEqual(headers, ('Typed Text', 'URL', 'Hits', 'Misses', 'Browser', 'Profile', 'User'))
        self.assertEqual(rows, [
            ('f', 'https://example.com/', 1, 0, 'Google Chrome', 'Default', 'someone'),
            ('f', 'https://www.facebook.com/', 0, 3, 'Google Chrome', 'Default', 'someone'),
            ('fa', 'https://www.facebook.com/', 2, 1, 'Google Chrome', 'Default', 'someone'),
        ])
        self.assertEqual([line.split('User Data/')[-1] for line in source.splitlines()],
                         ['Default/Network Action Predictor', 'Guest Profile/Network Action Predictor'])
        self.assertEqual(logs, [])

    def test_a_database_without_the_table_is_skipped(self):
        self._database(f'{_CHROME}/Default/Network Action Predictor', [], create=None)
        _headers, rows, source, logs = self._run()
        self.assertEqual((rows, source, logs), ([], '', []))

    def test_opera_keeps_its_database_in_the_user_data_folder(self):
        self._database('Users/someone/AppData/Roaming/Opera Software/Opera Stable/'
                       'Network Action Predictor', [('e', 'o', 'https://opera.example/', 1, 0)])
        _headers, rows, _source, _logs = self._run()
        self.assertEqual(rows, [('o', 'https://opera.example/', 1, 0, 'Opera', 'Opera Stable',
                                 'someone')])


if __name__ == '__main__':
    unittest.main()
