"""macOS System Information from SystemVersion.plist and the system-wide preferences."""

import os
import pathlib
import plistlib
import tempfile
import unittest
from unittest import mock

from scripts.artifacts import macosSystemInfo

DATA = 'Macintosh HD - Data'
PREBOOT = 'Preboot/0A81F3B1-51D9-3335-B3E3-169C3640360D'


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


def _write(root, relative, payload):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        plistlib.dump(payload, handle, fmt=plistlib.PlistFormat.FMT_BINARY)
    return path


class SystemInfoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, files):
        with mock.patch.object(macosSystemInfo, 'logfunc', lambda *_args: None):
            return macosSystemInfo.macosSystemInfo.__wrapped__(FakeContext(self.root, files))

    def test_system_files_give_their_values_and_other_copies_are_left_out(self):
        files = [
            _write(self.root, 'Macintosh HD/System/Library/CoreServices/SystemVersion.plist',
                   {'ProductName': 'macOS', 'ProductVersion': '11.2.1', 'ProductBuildVersion': '20D74'}),
            _write(self.root, f'{DATA}/Library/Preferences/SystemConfiguration/preferences.plist',
                   {'System': {'System': {'ComputerName': 'Lab Mac', 'HostName': 'lab.example'},
                               'Network': {'HostNames': {'LocalHostName': 'Lab-Mac'}}}}),
            _write(self.root, f'{DATA}/Library/Preferences/.GlobalPreferences.plist',
                   {'AppleLocale': 'en_US', 'AppleLanguages': ['en-US', 'es-US'], 'Country': 'US',
                    'com.apple.TimeZonePref.Last_Selected_City': ['35.7813', '-78.64167', '0',
                                                                  'America/New_York', 'US']}),
            _write(self.root, f'{DATA}/Library/User Template/es.lproj/Library/Preferences/.GlobalPreferences.plist',
                   {'AppleLanguages': ['es']}),
            _write(self.root, f'{DATA}/Users/alice/Library/Preferences/.GlobalPreferences.plist',
                   {'AppleLocale': 'fr_FR'}),
            _write(self.root, f'{DATA}/Library/Preferences/com.apple.loginwindow.plist',
                   {'lastUserName': 'alice', 'GuestEnabled': False, 'autoLoginUser': 'alice'}),
            _write(self.root, f'{DATA}/private/var/root/Library/Preferences/com.apple.loginwindow.plist',
                   {'lastUserName': 'root'}),
            _write(self.root, f'{PREBOOT}/Library/Preferences/com.apple.loginwindow.plist',
                   {'lastUserName': 'bob', 'GuestEnabled': True}),
            _write(self.root, f'{DATA}/Library/Developer/CommandLineTools/SDKs/MacOSX15.5.sdk/'
                              'System/Library/CoreServices/SystemVersion.plist',
                   {'ProductName': 'macOS', 'ProductVersion': '15.5', 'ProductBuildVersion': '24F74'}),
            _write(self.root, 'Macintosh HD/System/Library/AssetsV2/com_apple_MobileAsset_PKITrustStore/'
                              'purpose_auto/x.asset/.AssetData/System/Library/CoreServices/SystemVersion.plist',
                   {'ProductBuildVersion': '11M6270'}),
            _write(self.root, f'{DATA}/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/'
                              'Developer/SDKs/MacOSX.sdk/System/Library/CoreServices/SystemVersion.plist',
                   {'ProductName': 'macOS', 'ProductVersion': '26.0'}),
        ]
        headers, rows, source = self._run(files)
        self.assertEqual(headers, ('Property', 'Value', 'Plist Key', 'Source File'))
        got = sorted((prop, value, key, where.split('/')[0]) for prop, value, key, where in rows)
        self.assertEqual(got, sorted([
            ('Product Name', 'macOS', 'ProductName', 'Macintosh HD'),
            ('Product Version', '11.2.1', 'ProductVersion', 'Macintosh HD'),
            ('Product Build Version', '20D74', 'ProductBuildVersion', 'Macintosh HD'),
            ('Computer Name', 'Lab Mac', 'System/System/ComputerName', DATA),
            ('Host Name', 'lab.example', 'System/System/HostName', DATA),
            ('Local Host Name', 'Lab-Mac', 'System/Network/HostNames/LocalHostName', DATA),
            ('Locale', 'en_US', 'AppleLocale', DATA),
            ('Languages', 'en-US, es-US', 'AppleLanguages', DATA),
            ('Country', 'US', 'Country', DATA),
            ('Last Selected City (as stored)', '35.7813, -78.64167, 0, America/New_York, US',
             'com.apple.TimeZonePref.Last_Selected_City', DATA),
            ('Last User Name', 'alice', 'lastUserName', DATA),
            ('Automatic Login User', 'alice', 'autoLoginUser', DATA),
            ('Guest Enabled', 'false', 'GuestEnabled', DATA),
            ('Last User Name', 'bob', 'lastUserName', 'Preboot'),
            ('Guest Enabled', 'true', 'GuestEnabled', 'Preboot'),
        ]))
        cited = sorted(os.path.relpath(path, self.root) for path in source.split('\n'))
        self.assertEqual(cited, sorted([
            'Macintosh HD/System/Library/CoreServices/SystemVersion.plist',
            f'{DATA}/Library/Preferences/SystemConfiguration/preferences.plist',
            f'{DATA}/Library/Preferences/.GlobalPreferences.plist',
            f'{DATA}/Library/Preferences/com.apple.loginwindow.plist',
            f'{PREBOOT}/Library/Preferences/com.apple.loginwindow.plist']))

    def test_a_firmlinked_copy_is_read_once(self):
        payload = {'System': {'System': {'ComputerName': 'Lab Mac'}}}
        files = [_write(self.root, 'Library/Preferences/SystemConfiguration/preferences.plist', payload),
                 _write(self.root, 'System/Volumes/Data/Library/Preferences/SystemConfiguration/preferences.plist',
                        payload)]
        _headers, rows, _source = self._run(files)
        self.assertEqual([row[:2] for row in rows], [('Computer Name', 'Lab Mac')])

    def test_two_captures_of_one_file_give_each_value_once(self):
        first = _write(self.root, 'Library/Preferences/com.apple.loginwindow.plist',
                       {'lastUserName': 'alice', 'GuestEnabled': False})
        second = _write(self.root, 'System/Volumes/Data/Library/Preferences/com.apple.loginwindow.plist',
                        {'GuestEnabled': False, 'lastUserName': 'bob', 'autoLoginUser': 'bob',
                         'OptimizerPreviousBuild': 'differs'})
        _headers, rows, source = self._run([second, first])
        self.assertEqual(rows, [
            ('Last User Name', 'alice', 'lastUserName', 'Library/Preferences/com.apple.loginwindow.plist'),
            ('Guest Enabled', 'false', 'GuestEnabled', 'Library/Preferences/com.apple.loginwindow.plist'),
            ('Last User Name', 'bob', 'lastUserName',
             'System/Volumes/Data/Library/Preferences/com.apple.loginwindow.plist'),
            ('Automatic Login User', 'bob', 'autoLoginUser',
             'System/Volumes/Data/Library/Preferences/com.apple.loginwindow.plist')])
        self.assertEqual(source.split('\n'), [first, second])

    def test_a_copy_left_out_is_not_opened(self):
        path = os.path.join(self.root, 'Users/alice/Library/Preferences/com.apple.loginwindow.plist')
        os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as handle:
            handle.write(b'not a plist')
        logs = []
        with mock.patch.object(macosSystemInfo, 'logfunc', logs.append):
            _headers, rows, source = macosSystemInfo.macosSystemInfo.__wrapped__(FakeContext(self.root, [path]))
        self.assertEqual((rows, source), ([], ''))
        self.assertFalse([line for line in logs if 'could not read' in line])

    def test_an_unreadable_file_gives_no_rows(self):
        path = os.path.join(self.root, 'Library/Preferences/com.apple.loginwindow.plist')
        os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as handle:
            handle.write(b'not a plist')
        _headers, rows, source = self._run([path])
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
