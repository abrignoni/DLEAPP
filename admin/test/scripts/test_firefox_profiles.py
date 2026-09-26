"""Firefox profile bookkeeping cases; every file is written by hand for the test."""

import fnmatch
import json
import pathlib
import sys
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import firefox_profiles as fp  # pylint: disable=wrong-import-position
from scripts.artifacts import firefoxProfiles  # pylint: disable=wrong-import-position

PROFILES_INI = '''[Install308046B0AF4A39CB]
Default=Profiles/ab12.default-release
Locked=1

[Profile1]
Name=default
IsRelative=1
Path=Profiles/cd34.default
Default=1

[Profile0]
Name=default-release
IsRelative=1
Path=Profiles/ab12.default-release
StoreID=abc123
ShowSelector=0

[General]
StartWithLastProfile=1
Version=2
'''
MS = 1704067200000


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class ProfileListTest(unittest.TestCase):

    def test_sections_keys_and_other_values(self):
        rows = {row[0]: row for row in fp.ini_rows(PROFILES_INI)}
        self.assertEqual(list(rows), ['Install308046B0AF4A39CB', 'Profile1', 'Profile0', 'General'])
        self.assertEqual(rows['Install308046B0AF4A39CB'][1:9],
                         ('', '', '', 'Profiles/ab12.default-release', '1', '', '', ''))
        self.assertEqual(rows['Profile1'][1:5], ('default', 'Profiles/cd34.default', '1', '1'))
        self.assertEqual(rows['Profile0'][6:8], ('abc123', '0'))
        self.assertEqual(rows['General'][8], 'StartWithLastProfile=1; Version=2')

    def test_both_files_are_read_and_a_broken_file_is_logged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            base = root/'Users'/'tester'/'Library'/'Application Support'/'Firefox'
            base.mkdir(parents=True)
            (base/'profiles.ini').write_text(PROFILES_INI, encoding='utf-8')
            (base/'installs.ini').write_text('[308046B0AF4A39CB]\nDefault=Profiles/ab12.default-release\n',
                                              encoding='utf-8')
            broken = root/'home'/'linux'/'.mozilla'/'firefox'
            broken.mkdir(parents=True)
            (broken/'profiles.ini').write_text('no section header\n', encoding='utf-8')
            files = [str(p) for p in root.rglob('*.ini')]
            with unittest.mock.patch.object(fp, 'logfunc') as logged:
                rows, source = fp.read_profile_list(Context(root, files), 'Firefox Profile List')
        self.assertEqual(sorted((row[9], row[0]) for row in rows)[:2],
                         [('installs.ini', '308046B0AF4A39CB'), ('profiles.ini', 'General')])
        self.assertEqual({row[10] for row in rows}, {'tester'})
        self.assertEqual(len(rows), 5)
        self.assertNotIn('.ini\'', repr([row[:9] + row[10:] for row in rows]))
        self.assertTrue(all(len(row) == 11 for row in rows))
        self.assertEqual(len(source.split('\n')), 2)
        self.assertTrue(any('.mozilla/firefox/profiles.ini was not read' in str(c) for c in logged.call_args_list))


class ProfileTimesTest(unittest.TestCase):

    def test_times_and_missing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            profiles = root/'home'/'linux'/'.mozilla'/'firefox'
            new = profiles/'ab12.default-release'
            old = profiles/'cd34.default'
            bad = profiles/'ef56.default'
            for folder in (new, old, bad):
                folder.mkdir(parents=True)
            (new/'times.json').write_text(json.dumps({'created': MS, 'firstUse': MS + 1000, 'reset': MS + 2000,
                                                       'source': 'reset'}), encoding='utf-8')
            (old/'times.json').write_text(json.dumps({'created': MS, 'firstUse': None}), encoding='utf-8')
            (bad/'times.json').write_text('[1, 2]', encoding='utf-8')
            files = [str(p) for p in root.rglob('times.json')]
            with unittest.mock.patch.object(fp, 'logfunc') as logged:
                rows, _ = fp.read_profile_times(Context(root, files), 'Firefox Profile Times')
        by_profile = {row[5]: row for row in rows}
        self.assertEqual(sorted(by_profile), ['ab12.default-release', 'cd34.default'])
        self.assertEqual(by_profile['ab12.default-release'][:5],
                         (datetime(2024, 1, 1, tzinfo=timezone.utc),
                          datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
                          datetime(2024, 1, 1, 0, 0, 2, tzinfo=timezone.utc), '', 'reset'))
        self.assertEqual(by_profile['cd34.default'][1:5], ('', '', '', ''))
        self.assertEqual(by_profile['cd34.default'][5:], ('cd34.default', 'linux'))
        self.assertTrue(any('ef56.default/times.json was not read' in str(c) for c in logged.call_args_list))


class ContainersTest(unittest.TestCase):

    def test_built_in_user_created_internal_and_policy_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            old = root/'Users'/'tester'/'Library'/'Application Support'/'Firefox'/'Profiles'/'ab12.default-release'
            new = root/'Users'/'tester'/'Library'/'Application Support'/'Firefox'/'Profiles'/'cd34.default'
            for folder in (old, new):
                folder.mkdir(parents=True)
            (old/'containers.json').write_text(json.dumps({'version': 5, 'identities': [
                {'userContextId': 1, 'public': True, 'icon': 'fingerprint', 'color': 'blue',
                 'l10nId': 'user-context-personal'},
                {'userContextId': 5, 'public': False, 'icon': '', 'color': '',
                 'name': 'userContextIdInternal.thumbnail', 'accessKey': ''},
                'not an identity']}), encoding='utf-8')
            (new/'containers.json').write_text(json.dumps({'version': 8, 'identities': [
                {'userContextId': 1, 'public': True, 'icon': 'fingerprint', 'color': 'blue'},
                {'userContextId': 6, 'public': True, 'icon': 'cart', 'color': 'red', 'name': 'Travel'},
                {'userContextId': 7, 'public': False, 'name': 'corp', 'policy': True, 'policyId': 'corp'}]}),
                encoding='utf-8')
            files = [str(p) for p in root.rglob('containers.json')]
            rows, source = fp.read_containers(Context(root, files), 'Firefox Containers')
        by_key = {(row[8], row[0]): row for row in rows}
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(len(row) == 10 for row in rows))
        self.assertEqual(by_key[('ab12.default-release', '1')][:8],
                         ('1', '', 'user-context-personal', 'True', 'fingerprint', 'blue', '', '5'))
        self.assertEqual(by_key[('ab12.default-release', '5')][1:4], ('userContextIdInternal.thumbnail', '', 'False'))
        self.assertEqual(by_key[('cd34.default', '1')][1:3], ('', ''))
        self.assertEqual(by_key[('cd34.default', '6')][1:6], ('Travel', '', 'True', 'cart', 'red'))
        self.assertEqual(by_key[('cd34.default', '7')][6:], ('corp', '8', 'cd34.default', 'tester'))
        self.assertNotIn('containers.json', repr(rows))
        self.assertEqual(len(source.split('\n')), 2)


class PatternTest(unittest.TestCase):

    def test_each_file_matches_one_pattern(self):
        info = firefoxProfiles.__artifacts_v2__
        cases = {'firefoxProfileList': ['/c/Users/a/Library/Application Support/Firefox/{}',
                                        '/c/Users/a/AppData/Roaming/Mozilla/Firefox/{}',
                                        '/c/home/a/.mozilla/firefox/{}'],
                 'firefoxProfileTimes': ['/c/Users/a/Library/Application Support/Firefox/Profiles/p/{}',
                                         '/c/Users/a/AppData/Roaming/Mozilla/Firefox/Profiles/p/{}',
                                         '/c/home/a/.mozilla/firefox/p/{}',
                                         '/c/Users/a/Desktop/Old Firefox Data/p/{}']}
        cases['firefoxContainers'] = cases['firefoxProfileTimes']
        names = {'firefoxProfileList': ('profiles.ini', 'installs.ini'), 'firefoxProfileTimes': ('times.json',),
                 'firefoxContainers': ('containers.json',)}
        for key, templates in cases.items():
            for template in templates:
                for name in names[key]:
                    path = template.format(name)
                    with self.subTest(artifact=key, path=path):
                        self.assertEqual(sum(fnmatch.fnmatchcase(path, p) for p in info[key]['paths']), 1)
        self.assertFalse(any(fnmatch.fnmatchcase('/c/Users/a/Desktop/Backups/p/times.json', p)
                             for p in info['firefoxProfileTimes']['paths']))


if __name__ == '__main__':
    unittest.main()
