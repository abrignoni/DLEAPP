"""Firefox saved login reader cases; every store is built by hand for the test."""

import fnmatch
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox_logins as fl  # pylint: disable=wrong-import-position

MS = 1704067200000   # 2024-01-01T00:00:00Z
JAN1 = datetime(2024, 1, 1, tzinfo=timezone.utc)

COMMON = '''id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT NOT NULL, httpRealm TEXT,
    formActionOrigin TEXT, usernameField TEXT, passwordField TEXT, timesUsed INTEGER NOT NULL DEFAULT 0,
    timeCreated INTEGER NOT NULL, timeLastUsed INTEGER, timePasswordChanged INTEGER NOT NULL,
    timeLastBreachAlertDismissed INTEGER, secFields TEXT, guid TEXT NOT NULL UNIQUE'''


def build_db(path):
    db = sqlite3.connect(path)
    db.executescript(f'''CREATE TABLE loginsL ({COMMON}, local_modified INTEGER,
            is_deleted TINYINT NOT NULL DEFAULT 0, sync_status TINYINT NOT NULL DEFAULT 0);
        CREATE TABLE loginsM ({COMMON}, server_modified INTEGER NOT NULL,
            is_overridden TINYINT NOT NULL DEFAULT 0, enc_unknown_fields TEXT);''')
    db.execute("INSERT INTO loginsL VALUES (1, 'https://a.test', NULL, 'https://a.test', 'user', 'pass', 3, ?, ?, ?,"
               " NULL, 'secret', '{g1}', ?, 0, 2)", (MS, MS + 1000, MS, MS + 2000))
    db.execute("INSERT INTO loginsL VALUES (2, 'https://b.test', 'Realm', NULL, '', '', 0, ?, NULL, ?,"
               " ?, 'secret', '{g2}', NULL, 1, 7)", (MS, MS, MS + 3000))
    db.execute("INSERT INTO loginsM VALUES (1, 'https://a.test', NULL, 'https://a.test', 'user', 'pass', 3, ?, ?, ?,"
               " NULL, 'secret', '{g1}', ?, 1, NULL)", (MS, MS, MS, MS + 4000))
    db.commit()
    db.close()


class SavedLoginsTest(unittest.TestCase):

    def test_json_and_db_stores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            profile = root/'Users'/'tester'/'Library'/'Application Support'/'Firefox'/'Profiles'/'ab12.default-release'
            profile.mkdir(parents=True)
            login = {'hostname': 'https://c.test', 'formSubmitURL': 'https://c.test/login', 'httpRealm': None,
                     'usernameField': 'email', 'passwordField': 'pw', 'guid': '{g3}', 'timeCreated': MS,
                     'timeLastUsed': MS + 5000, 'timePasswordChanged': MS, 'timesUsed': 4,
                     'timeLastBreachAlertDismissed': None, 'encryptedUsername': 'ENC', 'encryptedPassword': 'ENC'}
            (profile/'logins.json').write_text(json.dumps({'logins': [login, 'not a login']}), encoding='utf-8')
            (profile/'logins-backup.json').write_text('{broken', encoding='utf-8')
            build_db(profile/'logins.db')
            files = [str(p) for p in profile.iterdir()]

            class Context:
                def get_files_found(self):
                    return files

                def get_relative_path(self, path):
                    return str(pathlib.Path(path).relative_to(root))
            with unittest.mock.patch.object(fl, 'logfunc') as logged:
                rows, source = fl.read_saved_logins(Context(), 'Firefox Saved Logins')
        by_guid = {(row[12], row[13]): row for row in rows}
        self.assertEqual(sorted(by_guid), [('{g1}', 'logins.db local (loginsL)'), ('{g1}', 'logins.db mirror (loginsM)'),
                                           ('{g2}', 'logins.db local (loginsL)'), ('{g3}', 'logins.json')])
        local = by_guid[('{g1}', 'logins.db local (loginsL)')]
        self.assertEqual(local[:2], (JAN1, datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)))
        self.assertEqual(local[4], datetime(2024, 1, 1, 0, 0, 2, tzinfo=timezone.utc))
        self.assertEqual(local[6:12], ('3', 'https://a.test', 'https://a.test', '', 'user', 'pass'))
        self.assertEqual(local[14:17], ('0', '2 (New)', ''))
        tomb = by_guid[('{g2}', 'logins.db local (loginsL)')]
        self.assertEqual((tomb[1], tomb[3], tomb[9], tomb[14], tomb[15]),
                         ('', datetime(2024, 1, 1, 0, 0, 3, tzinfo=timezone.utc), 'Realm', '1', '7 (as stored)'))
        mirror = by_guid[('{g1}', 'logins.db mirror (loginsM)')]
        self.assertEqual((mirror[4], mirror[5], mirror[15], mirror[16]),
                         ('', datetime(2024, 1, 1, 0, 0, 4, tzinfo=timezone.utc), '', '1'))
        from_json = by_guid[('{g3}', 'logins.json')]
        self.assertEqual(from_json[6:13], ('4', 'https://c.test', 'https://c.test/login', '', 'email', 'pw', '{g3}'))
        self.assertEqual(from_json[14:], ('', '', '', 'ab12.default-release', 'tester',
                                          'Users/tester/Library/Application Support/Firefox/Profiles/'
                                          'ab12.default-release/logins.json'))
        self.assertNotIn('ENC', repr(rows))
        self.assertNotIn('secret', repr(rows))
        self.assertEqual(len(source.split('\n')), 2)
        self.assertTrue(any('logins-backup.json was not read' in str(c) for c in logged.call_args_list))

    def test_each_store_matches_one_pattern_on_every_platform(self):
        from scripts.artifacts import firefoxBrowser  # pylint: disable=import-outside-toplevel
        patterns = firefoxBrowser.__artifacts_v2__['firefoxSavedLogins']['paths']
        for profile in ('/case/Users/a/Library/Application Support/Firefox/Profiles/p/',
                        '/case/Users/a/AppData/Roaming/Mozilla/Firefox/Profiles/p/',
                        '/case/home/a/.mozilla/firefox/p/', '/case/Users/a/Desktop/Old Firefox Data/p/'):
            for name in ('logins.json', 'logins-backup.json', 'logins.db', 'logins.db-wal'):
                with self.subTest(path=profile + name):
                    self.assertEqual(sum(fnmatch.fnmatchcase(profile + name, p) for p in patterns), 1)


if __name__ == '__main__':
    unittest.main()
