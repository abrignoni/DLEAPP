"""Pin the launchd overrides reading in scripts/artifacts/macosLaunchdOverrides.py.

Every property list below is written by the test; no label or value comes from a real device.
"""
import fnmatch
import os
import pathlib
import plistlib
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosLaunchdOverrides as artifact  # pylint: disable=wrong-import-position
from scripts.search_files import FileInfo  # pylint: disable=wrong-import-position

UTC = timezone.utc
FOLDER = 'private/var/db/com.apple.xpc.launchd'
DATA = 'System/Volumes/Data/'


class FileSeekerZip:  # the name the artifact reads to trust recorded times
    def __init__(self):
        self.file_infos = {}


class FileSeekerDir:
    def __init__(self):
        self.file_infos = {}


class Context:
    def __init__(self, root, files, seeker=None):
        self.root = root
        self.files = files
        self.seeker = seeker

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        return self.seeker


class LaunchdOverridesTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        patcher = patch.object(artifact, 'logfunc')
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, relative, value=None, raw=None):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(raw if raw is not None else plistlib.dumps(value))
        return path

    def run_artifact(self, paths, seeker=None):
        return artifact.macosLaunchdDisabledOverrides.__wrapped__(
            Context(self.root, list(paths), seeker))

    def test_one_row_per_entry_with_value_and_domain(self):
        system = self.write(f'{FOLDER}/disabled.plist',
                            {'com.example.b': True, 'com.example.a': False})
        user = self.write(f'{FOLDER}/disabled.502.plist', {'com.example.c': True})
        headers, rows, source = self.run_artifact([system, user])
        self.assertEqual(headers[0], ('File Modified (UTC)', 'datetime'))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            ('', 'com.example.a', 'false', 'system', '', '', f'{FOLDER}/disabled.plist'),
            ('', 'com.example.b', 'true', 'system', '', '', f'{FOLDER}/disabled.plist'),
            ('', 'com.example.c', 'true', 'user/502', '502', '', f'{FOLDER}/disabled.502.plist'),
        ])
        self.assertEqual(source.split('\n'), sorted([system, user], key=lambda p: (len(p), p)))

    def test_a_value_that_is_not_a_boolean_is_kept_as_stored(self):
        path = self.write(f'{FOLDER}/disabled.plist', {'com.example.a': 1,
                                                        'com.example.b': {'k': 'v'}})
        _headers, rows, _source = self.run_artifact([path])
        self.assertEqual([row[2] for row in rows], ['1', '{"k": "v"}'])

    def test_other_names_get_no_domain_and_a_non_plist_is_logged(self):
        other = self.write(f'{FOLDER}/disabled.other.plist', {'com.example.a': True})
        empty = self.write(f'{FOLDER}/disabled.migrated', raw=b'')
        _headers, rows, source = self.run_artifact([other, empty])
        self.assertEqual([(row[3], row[4]) for row in rows], [('', '')])
        self.assertEqual(source, other)
        self.assertTrue(any('disabled.migrated (0 bytes)' in str(call)
                            for call in self.log.call_args_list))

    def test_launch_plists_are_joined_by_their_recorded_label_only(self):
        overrides = self.write(f'{FOLDER}/disabled.plist',
                               {'com.example.agent': True, 'com.example.none': True})
        agent = self.write('Library/LaunchAgents/com.example.agent.plist',
                           {'Label': 'com.example.agent'})
        shipped = self.write('System/Library/LaunchDaemons/x.plist', {'Label': 'com.example.agent'})
        # Named for the label but recording another one: not joined.
        decoy = self.write('Library/LaunchAgents/com.example.none.plist',
                           {'Label': 'com.example.other'})
        _headers, rows, source = self.run_artifact([overrides, agent, shipped, decoy])
        joined = {row[1]: row[5] for row in rows}
        self.assertEqual(joined, {
            'com.example.agent': 'Library/LaunchAgents/com.example.agent.plist\n'
                                 'System/Library/LaunchDaemons/x.plist',
            'com.example.none': '',
        })
        self.assertEqual(source, overrides)

    def test_launch_plists_alone_produce_no_rows(self):
        agent = self.write('Library/LaunchAgents/a.plist', {'Label': 'a'})
        self.assertEqual(self.run_artifact([agent])[1:], ([], ''))

    def test_identical_data_view_copy_is_read_once(self):
        root = self.write(f'{FOLDER}/disabled.plist', {'com.example.a': True})
        view = self.write(f'{DATA}{FOLDER}/disabled.plist', {'com.example.a': True})
        _headers, rows, source = self.run_artifact([root, view])
        self.assertEqual(len(rows), 1)
        self.assertEqual(source, root)

    def test_differing_data_view_copy_lists_both_files_for_a_shared_entry(self):
        root = self.write(f'{FOLDER}/disabled.plist', {'com.example.a': True})
        view = self.write(f'{DATA}{FOLDER}/disabled.plist',
                          {'com.example.a': True, 'com.example.b': False})
        _headers, rows, _source = self.run_artifact([root, view])
        self.assertEqual([(row[1], row[-1]) for row in rows], [
            ('com.example.a', f'{FOLDER}/disabled.plist\n{DATA}{FOLDER}/disabled.plist'),
            ('com.example.b', f'{DATA}{FOLDER}/disabled.plist'),
        ])

    def test_templates_copy_is_not_read(self):
        template = self.write(f'System/Library/Templates/Data/{FOLDER}/disabled.plist',
                              {'com.example.a': True})
        self.assertEqual(self.run_artifact([template])[1:], ([], ''))

    def test_modified_time_is_reported_only_from_an_evidence_seeker(self):
        path = self.write(f'{FOLDER}/disabled.plist', {'com.example.a': True})
        for seeker, expected in ((FileSeekerZip(), datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)),
                                 (FileSeekerDir(), '')):
            seeker.file_infos[path] = FileInfo(f'{FOLDER}/disabled.plist', 0, 1735787045)
            with self.subTest(seeker=type(seeker).__name__):
                self.assertEqual(self.run_artifact([path], seeker)[1][0][0], expected)
        zip_seeker = FileSeekerZip()
        zip_seeker.file_infos[path] = FileInfo(f'{FOLDER}/disabled.plist', None, None)
        self.assertEqual(self.run_artifact([path], zip_seeker)[1][0][0], '')

    def test_patterns(self):
        patterns = artifact.__artifacts_v2__['macosLaunchdDisabledOverrides']['paths']
        def hits(member):
            return [p for p in patterns if fnmatch.fnmatchcase('root/' + member, p)]
        for member in (f'{FOLDER}/disabled.plist', f'{FOLDER}/disabled.501.plist',
                       f'{DATA}{FOLDER}/disabled.plist', 'Users/u/Library/LaunchAgents/a.plist',
                       'System/Library/LaunchDaemons/a.plist'):
            with self.subTest(member=member):
                self.assertEqual(len(hits(member)), 1)
        self.assertEqual(hits(f'{FOLDER}/config/x.plist'), [])


if __name__ == '__main__':
    unittest.main()
