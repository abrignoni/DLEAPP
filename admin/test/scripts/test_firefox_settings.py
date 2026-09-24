"""Independently authored synthetic records only; no private corpus fixtures."""

import fnmatch
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox_settings  # pylint: disable=wrong-import-position
from scripts.artifacts import firefoxSettings  # pylint: disable=wrong-import-position


class FirefoxSettingsTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)

    def test_modern_permissions_and_partitioned_origins(self):
        self.db.executescript('''CREATE TABLE moz_perms(id INTEGER,origin TEXT,type TEXT,
            permission INTEGER,expireType INTEGER,expireTime INTEGER,modificationTime INTEGER);
            INSERT INTO moz_perms VALUES(1,'https://example.test^userContextId=7','camera',
                999,1,1704153600456,1704067200123);''')
        row = list(firefox_settings.permissions(self.db))[0]
        self.assertEqual(row[:2], (datetime(2024, 1, 1, microsecond=123000, tzinfo=timezone.utc),
                                  datetime(2024, 1, 2, microsecond=456000, tzinfo=timezone.utc)))
        self.assertEqual(row[3:], ('https://example.test^userContextId=7', 'camera',999,1,'moz_perms'))

    def test_empty_modern_table_does_not_resurrect_legacy_rows(self):
        self.db.executescript('''CREATE TABLE moz_perms(id INTEGER,origin TEXT);
            CREATE TABLE moz_hosts(id INTEGER,host TEXT);
            INSERT INTO moz_hosts VALUES(2,'obsolete.test');''')
        self.assertEqual(list(firefox_settings.permissions(self.db)), [])

    def test_legacy_schema_without_dates(self):
        self.db.executescript('''CREATE TABLE moz_hosts(id INTEGER,host TEXT,type TEXT,permission INTEGER);
            INSERT INTO moz_hosts VALUES(2,'legacy.test','popup',2);''')
        self.assertEqual(list(firefox_settings.permissions(self.db))[0],
                         ('','',2,'legacy.test','popup',2,None,'moz_hosts'))

    def test_missing_permission_tables(self):
        self.assertEqual(list(firefox_settings.permissions(self.db)), [])

    def test_extensions_preserve_dates_and_permission_scopes(self):
        document = {'addons': [{'id': 'synthetic@example.test', 'type': 'extension',
            'defaultLocale': {'name': '<Synthetic extension>'}, 'version': '1.2',
            'installDate': 1704067200123, 'updateDate': 1704153600456,
            'active': False, 'userDisabled': True, 'appDisabled': False,
            'location': 'app-profile', 'userPermissions': {'permissions': ['tabs']},
            'optionalPermissions': {'origins': ['https://optional.test/*']}}]}
        row = list(firefox_settings.extensions(document))[0]
        self.assertEqual(row[0], datetime(2024,1,1,microsecond=123000,tzinfo=timezone.utc))
        self.assertEqual(row[1], datetime(2024,1,2,microsecond=456000,tzinfo=timezone.utc))
        self.assertEqual(row[6:9], (False, True, False))
        self.assertEqual(json.loads(row[11]), {'permissions':['tabs']})
        self.assertEqual(json.loads(row[12]), {'origins':['https://optional.test/*']})

    def test_non_extensions_skipped_and_missing_update_not_fabricated(self):
        document = {'addons':[None, {'type':'theme','id':'theme@example.test'},
            {'type':'extension','id':'addon@example.test','installDate':1704067200000,
             'defaultLocale':None}]}
        rows = list(firefox_settings.extensions(document))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], '')
        self.assertIsNone(rows[0][3])

    def test_invalid_extension_document_rejected(self):
        for value in (None, [], {}, {'addons':{}}):
            with self.assertRaises(ValueError):
                list(firefox_settings.extensions(value))

    def test_distinct_profiles_and_corrupt_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            paths = []
            for name in ('one','two','bad'):
                path=root/'home'/'evidence'/'.mozilla/firefox'/name/'extensions.json'
                path.parent.mkdir(parents=True)
                path.write_text('{broken' if name=='bad' else json.dumps(
                    {'addons':[{'id':'synthetic@example.test','type':'extension'}]}))
                paths.append(path)

            class Context:
                @staticmethod
                def get_files_found():
                    return paths+[paths[0]]

                @staticmethod
                def get_relative_path(path):
                    return str(pathlib.Path(path).relative_to(root))

            with patch('scripts.firefox_settings.logfunc') as log:
                rows, sources = firefox_settings.read_extensions(Context)
            self.assertEqual(len(rows), 2)
            self.assertEqual({row[-3] for row in rows}, {'one','two'})
            self.assertEqual({row[-2] for row in rows}, {'evidence'})
            self.assertEqual(len(sources.splitlines()), 2)
            self.assertEqual(log.call_count, 1)

    def test_platform_patterns(self):
        for artifact in firefoxSettings.__artifacts_v2__.values():
            filename=artifact['paths'][0].rsplit('/',1)[1].rstrip('*')
            for prefix in ('root/Library/Application Support/Firefox/Profiles/a/',
                           'root/Users/A/AppData/Roaming/Mozilla/Firefox/Profiles/a/',
                           'root/home/a/.mozilla/firefox/a/'):
                self.assertEqual(sum(fnmatch.fnmatchcase(prefix+filename,p)
                                     for p in artifact['paths']),1)


if __name__ == '__main__':
    unittest.main()
