"""Pin the setting rows of scripts/artifacts/macosApplicationFirewall.py.

Every value below is authored for the test; none comes from a real device.
"""
import pathlib
import plistlib
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import macosApplicationFirewall as alf  # pylint: disable=wrong-import-position

_PREFS = pathlib.Path('Library', 'Preferences', 'com.apple.alf.plist')


class Context:
    """The two calls the artifact makes, over a temporary tree."""

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class StoredTextTest(unittest.TestCase):
    def test_values(self):
        self.assertEqual(alf.stored_text(True), 'Yes')
        self.assertEqual(alf.stored_text(False), 'No')
        self.assertEqual(alf.stored_text(b'\x01\xab'), '01ab')
        self.assertEqual(alf.stored_text(bytearray(b'\x02')), '02')
        self.assertEqual(alf.stored_text(datetime(2021, 2, 20, 1, 2, 3)), '2021-02-20 01:02:03+00:00')
        self.assertEqual(alf.stored_text(None), '')
        self.assertEqual(alf.stored_text(0), '0')
        self.assertEqual(alf.stored_text('1.6'), '1.6')


class FlattenTest(unittest.TestCase):
    def test_paths_follow_keys_and_positions(self):
        settings = {
            'globalstate': 0,
            'version': '1.6',
            'exceptions': [{'path': '/usr/libexec/example', 'state': 3},
                           {'path': '/opt/example', 'bundleid': 'com.example.tool', 'state': 3}],
            'firewall': {'Example Service': {'proc': 'exampled', 'state': 0}},
            'nested': [[5]],
            'applications': [],
            'empty': {},
        }
        self.assertEqual(list(alf.flatten(settings)), [
            ('globalstate', '0'),
            ('version', '1.6'),
            ('exceptions[1]/path', '/usr/libexec/example'),
            ('exceptions[1]/state', '3'),
            ('exceptions[2]/path', '/opt/example'),
            ('exceptions[2]/bundleid', 'com.example.tool'),
            ('exceptions[2]/state', '3'),
            ('firewall/Example Service/proc', 'exampled'),
            ('firewall/Example Service/state', '0'),
            ('nested[1][1]', '5'),
            ('applications', ''),
            ('empty', ''),
        ])

    def test_an_empty_dictionary_is_one_blank_row(self):
        self.assertEqual(list(alf.flatten({})), [('', '')])


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        for target in (alf, macos_plists):
            patcher = patch.object(target, 'logfunc', self.logged.append)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, relative, data):
        path = self.root/relative
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        return path

    def test_each_file_is_named_and_copies_under_two_views_are_read_once(self):
        live = plistlib.dumps({'globalstate': 0, 'applications': []}, fmt=plistlib.PlistFormat.FMT_BINARY,
                             sort_keys=False)
        files = [
            self.write(_PREFS, live),
            self.write(pathlib.Path('System', 'Volumes', 'Data')/_PREFS, live),
            self.write(pathlib.Path('Volumes', 'Other')/_PREFS, b'not a plist'),
            self.write(pathlib.Path('Volumes', 'Array')/_PREFS, plistlib.dumps([1])),
            self.write(pathlib.Path('Backups.backupdb', 'Mac', 'Latest')/_PREFS,
                       plistlib.dumps({'globalstate': 1})),
        ]
        headers, rows, source = alf.macosApplicationFirewall.__wrapped__(
            Context(self.root, files + [self.root/'Library']))
        backup = str(pathlib.Path('Backups.backupdb', 'Mac', 'Latest')/_PREFS)
        self.assertEqual(headers, ('Setting', 'Value', 'Settings File'))
        self.assertEqual(rows, [
            ('globalstate', '0', str(_PREFS)),
            ('applications', '', str(_PREFS)),
            ('globalstate', '1', backup),
        ])
        self.assertEqual(source.split('\n'), [str(files[0]), str(files[4])])
        self.assertEqual(sorted(self.logged), sorted([
            'Application Firewall: 1 byte-identical copy(ies) under System/Volumes/Data not read again',
            f'Application Firewall: {pathlib.Path("Volumes", "Other")/_PREFS} is not a plist dictionary',
            f'Application Firewall: {pathlib.Path("Volumes", "Array")/_PREFS} is not a plist dictionary',
        ]))


if __name__ == '__main__':
    unittest.main()
