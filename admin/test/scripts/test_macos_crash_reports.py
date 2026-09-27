"""Crash reports from the .ips and .crash files in Library/Logs/DiagnosticReports."""

import datetime
import fnmatch
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import macos_plists
from scripts.artifacts import macosCrashReports

UTC = datetime.timezone.utc
REPORTS = 'Library/Logs/DiagnosticReports'
HEADER = {'app_name': 'Google Drive', 'timestamp': '2025-12-24 17:05:50.00 -0500', 'bug_type': '309',
          'os_version': 'macOS 15.4 (24E248)', 'incident_id': '612D4E1C-DD52-4ACF-B786-E15F46BDD1C9',
          'name': 'Google Drive'}
BODY = {'captureTime': '2025-12-24 17:05:33.6811 -0500', 'procLaunch': '2025-12-24 17:05:32.3915 -0500',
        'procName': 'Google Drive', 'pid': 74977,
        'procPath': '/Applications/Google Drive.app/Contents/MacOS/Google Drive',
        'bundleInfo': {'CFBundleShortVersionString': '118.0', 'CFBundleVersion': '118.0.1',
                       'CFBundleIdentifier': 'com.google.drivefs'},
        'parentProc': 'Google Drive', 'parentPid': 514, 'userID': 501,
        'exception': {'type': 'EXC_BAD_ACCESS', 'signal': 'SIGKILL (Code Signature Invalid)'},
        'termination': {'flags': 0, 'code': 2, 'namespace': 'CODESIGNING', 'indicator': 'Invalid Page',
                        'byProc': 'launchd', 'byPid': 1},
        'crashReporterKey': 'F3A3FD12-329A-9D81-90B8-FCEAF69ABEC0'}
CRASH = (
    'Process:               searchpartyuseragent [557]\n'
    'Path:                  /usr/libexec/searchpartyuseragent\n'
    'Identifier:            searchpartyuseragent\n'
    'Version:               1.0 (1.0)\n'
    'Parent Process:        ??? [1]\n'
    'User ID:               501\n'
    '\n'
    'Date/Time:             2021-02-15 07:27:52.927 -0800\n'
    'Launch Time:           2021-02-15 07:25:52.000 -0800\n'
    'OS Version:            macOS 11.1 (20C69)\n'
    '\n'
    'Exception Type:        EXC_BAD_ACCESS (SIGBUS)\n'
    'Termination Reason:    Namespace SIGNAL, Code 0xa\n'
    '\n'
    'Thread 0 Crashed:\n'
    'Process:               not a field this time\n')


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class CrashReportsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, text):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        return path

    def _ips(self, relative, header=None, body=None):
        return self._write(relative, json.dumps(header or HEADER) + '\n' + json.dumps(body or BODY, indent=2))

    def _run(self, files):
        with mock.patch.object(macosCrashReports, 'logfunc', self.logs.append), \
                mock.patch.object(macos_plists, 'logfunc', self.logs.append):
            return macosCrashReports.macosCrashReports.__wrapped__(FakeContext(self.root, files))

    def test_a_json_crash_report(self):
        path = self._ips(f'{REPORTS}/Google Drive-2025-12-24-170550.ips')
        headers, rows, source = self._run([path])
        self.assertEqual(headers[:2], (('Crash Time (UTC)', 'datetime'), ('Launch Time (UTC)', 'datetime')))
        self.assertEqual(rows, [(
            datetime.datetime(2025, 12, 24, 22, 5, 33, 681100, tzinfo=UTC),
            datetime.datetime(2025, 12, 24, 22, 5, 32, 391500, tzinfo=UTC),
            'Google Drive', '74977', '/Applications/Google Drive.app/Contents/MacOS/Google Drive',
            'com.google.drivefs', '118.0 (118.0.1)', 'Google Drive [514]', '501',
            'EXC_BAD_ACCESS (SIGKILL (Code Signature Invalid))',
            'Namespace CODESIGNING, Code 2, Invalid Page, by launchd [1]', 'macOS 15.4 (24E248)',
            '612D4E1C-DD52-4ACF-B786-E15F46BDD1C9', 'F3A3FD12-329A-9D81-90B8-FCEAF69ABEC0',
            f'{REPORTS}/Google Drive-2025-12-24-170550.ips')])
        self.assertEqual(source, path)

    def test_a_text_crash_report(self):
        path = self._write(f'Users/alice/{REPORTS}/searchpartyuseragent_2021-02-15-072802_Mac.crash', CRASH)
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows, [(
            datetime.datetime(2021, 2, 15, 15, 27, 52, 927000, tzinfo=UTC),
            datetime.datetime(2021, 2, 15, 15, 25, 52, tzinfo=UTC),
            'searchpartyuseragent', '557', '/usr/libexec/searchpartyuseragent', 'searchpartyuseragent',
            '1.0 (1.0)', '??? [1]', '501', 'EXC_BAD_ACCESS (SIGBUS)', 'Namespace SIGNAL, Code 0xa',
            'macOS 11.1 (20C69)', '', '',
            f'Users/alice/{REPORTS}/searchpartyuseragent_2021-02-15-072802_Mac.crash')])

    def test_a_crash_metadata_line_over_a_text_report(self):
        path = self._write(f'{REPORTS}/old.ips', json.dumps(HEADER) + '\n' + CRASH)
        _headers, rows, _source = self._run([path])
        self.assertEqual((rows[0][2], rows[0][11], rows[0][12]),
                         ('searchpartyuseragent', 'macOS 11.1 (20C69)', '612D4E1C-DD52-4ACF-B786-E15F46BDD1C9'))

    def test_other_report_types_and_unreadable_files_are_counted_not_read(self):
        jetsam = self._ips(f'{REPORTS}/JetsamEvent-2025-12-20.ips', dict(HEADER, bug_type='298'), {'processes': []})
        broken = self._write(f'{REPORTS}/broken.ips', 'not json\n{}')
        empty = self._write(f'{REPORTS}/notes.crash', 'nothing here\n')
        array = self._write(f'{REPORTS}/array.ips', json.dumps(HEADER) + '\n[1, 2]')
        stackshot = self._ips(f'{REPORTS}/stacks-2025-12-20.ips', dict(HEADER, bug_type='288'), BODY)
        _headers, rows, source = self._run([jetsam, broken, empty, array, stackshot])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn('Crash Reports: files not read as crash reports: 1 of bug_type 288, 1 of bug_type 298, '
                      '1 of bug_type 309 whose report is not a JSON object, 1 without a JSON metadata line, 1 '
                      'without crash report fields', self.logs)

    def test_one_report_reached_twice_is_reported_once(self):
        first = self._ips(f'{REPORTS}/Google Drive-2025-12-24-170550.ips')
        retired = self._ips(f'{REPORTS}/Retired/Google Drive-2025-12-24-170550.ips')
        mirror = self._ips(f'System/Volumes/Data/{REPORTS}/Google Drive-2025-12-24-170550.ips')
        other = self._ips(f'{REPORTS}/Retired/Google Drive-2025-12-24-170551.ips',
                          dict(HEADER, incident_id='BE5D247C-33A5-4E96-8D89-51D0DA3594CE'))
        _headers, rows, source = self._run([mirror, retired, other, first])
        self.assertEqual([row[-1] for row in rows], [f'{REPORTS}/Google Drive-2025-12-24-170550.ips',
                                                     f'{REPORTS}/Retired/Google Drive-2025-12-24-170551.ips'])
        self.assertEqual(source.split('\n'), [first, other])
        self.assertIn('Crash Reports: 1 report(s) with an incident ID already read not reported again', self.logs)

    def test_a_text_report_captured_twice_is_reported_once(self):
        first = self._write(f'{REPORTS}/a.crash', CRASH)
        mirror = self._write(f'System/Volumes/Data/{REPORTS}/a.crash', CRASH)
        _headers, rows, _source = self._run([mirror, first])
        self.assertEqual([row[-1] for row in rows], [f'{REPORTS}/a.crash'])

    def test_the_metadata_line_fills_what_a_text_report_leaves_out(self):
        body = CRASH.replace('OS Version:            macOS 11.1 (20C69)\n', '')
        path = self._write(f'{REPORTS}/old.ips', json.dumps(HEADER) + '\n' + body)
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows[0][11], 'macOS 15.4 (24E248)')

    def test_times_without_an_offset_are_left_blank(self):
        body = dict(BODY, captureTime='2025-12-24 17:05:33', procLaunch='Wed Dec 24 17:05:32 2025')
        path = self._ips(f'{REPORTS}/x.ips', body=body)
        _headers, rows, _source = self._run([path])
        self.assertEqual(rows[0][:2], ('', ''))

    def test_paths_reach_the_report_folders_and_nothing_else(self):
        patterns = macosCrashReports.__artifacts_v2__['macosCrashReports']['paths']
        def matched(path):
            return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        self.assertTrue(matched('/case/Macintosh HD - Data/Library/Logs/DiagnosticReports/a.ips'))
        self.assertTrue(matched('/case/Users/alice/Library/Logs/DiagnosticReports/Retired/b.crash'))
        self.assertFalse(matched('/case/Users/alice/Downloads/b.crash'))


if __name__ == '__main__':
    unittest.main()
