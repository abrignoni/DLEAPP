"""Pin the Windows Error Reporting readers in scripts/artifacts/windowsErrorReporting.py.

REPORT is shaped like the Report.wer files on the registered images: UTF-16 with a
byte-order mark, one Key=Value pair per line, indexed Sig[n] and LoadedModule[n] fields.
The expected values are written out, never read back from the code.
"""
import pathlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsErrorReporting as wer  # pylint: disable=wrong-import-position

REPORT = ('Version=1\r\nEventType=APPCRASH\r\nEventTime=131666691375272319\r\n'
          'UploadTime=131666691385165802\r\n'
          'Sig[1].Name=Application Version\r\nSig[1].Value=45.4.92.0\r\n'
          'Sig[0].Name=Application Name\r\nSig[0].Value=Dropbox.exe\r\n'
          'LoadedModule[1]=C:\\Windows\\SYSTEM32\\ntdll.dll\r\n'
          'LoadedModule[0]=C:\\Program Files (x86)\\Dropbox\\Client\\Dropbox.exe\r\n'
          'TargetAppId=W:0006a1b2!0000e9317913576d3e0787fd2338f956aa9392f04dac!Dropbox.exe\r\n'
          'AppName=Dropbox\r\nEventType=SECOND\r\n').encode('utf-16')


class _Record:  # pylint: disable=too-few-public-methods
    def __init__(self, provider, event_id, fields=None, values=None):
        self.provider = provider
        self.event_id = event_id
        self.fields = fields or {}
        self.values = values or []


class ReportTest(unittest.TestCase):
    def test_fields_first_occurrence_kept(self):
        fields = wer.read_report(REPORT)
        self.assertEqual(fields['EventType'], 'APPCRASH')
        self.assertEqual(fields['AppName'], 'Dropbox')

    def test_problem_signature_in_index_order(self):
        self.assertEqual(wer.problem_signature(wer.read_report(REPORT)),
                         'Application Name: Dropbox.exe\nApplication Version: 45.4.92.0')

    def test_loaded_modules_in_index_order(self):
        self.assertEqual(wer.loaded_modules(wer.read_report(REPORT)),
                         ['C:\\Program Files (x86)\\Dropbox\\Client\\Dropbox.exe',
                          'C:\\Windows\\SYSTEM32\\ntdll.dll'])

    def test_utf8_report(self):
        self.assertEqual(wer.read_report(b'\xef\xbb\xbfAppName=x\n')['AppName'], 'x')


class TimeTest(unittest.TestCase):
    def test_decimal_filetime(self):
        # EventTime of a lonewolf_win10 report; 2018-03-28 00:05:37.527231 UTC by
        # Unix-epoch arithmetic (value / 10**7 - 11644473600).
        self.assertEqual(wer.filetime('131666691375272319'),
                         datetime(2018, 3, 28, 0, 5, 37, 527231, tzinfo=timezone.utc))
        self.assertEqual(wer.filetime('0'), '')
        self.assertEqual(wer.filetime('0x01d3c5ae0590aea7'), '')

    def test_hex_filetime_with_and_without_prefix(self):
        expected = datetime(2018, 3, 27, 9, 28, 53, 222570, tzinfo=timezone.utc)
        self.assertEqual(wer.hex_filetime('01d3c5ae0590aea7'), expected)
        self.assertEqual(wer.hex_filetime('0x01d3c5ae0590aea7'), expected)
        self.assertEqual(wer.hex_filetime('4294967295'), '')
        self.assertEqual(wer.hex_filetime(''), '')


class ValueTest(unittest.TestCase):
    def test_target_sha1(self):
        self.assertEqual(wer.target_sha1('W:0006a1b2!0000E9317913576D3E0787FD2338F956AA9392F04DAC!x'),
                         'e9317913576d3e0787fd2338f956aa9392f04dac')
        self.assertEqual(wer.target_sha1('W:0006!0000e9317913576d3e0787fd2338f956aa9392f04dac'),
                         'e9317913576d3e0787fd2338f956aa9392f04dac')
        self.assertEqual(wer.target_sha1('U:Microsoft.Windows.x!App'), '')
        self.assertEqual(wer.target_sha1('W:0006!00001234!x'), '')

    def test_process_id(self):
        self.assertEqual(wer.process_id('0x000019a0', False), '6560 (0x19A0)')
        self.assertEqual(wer.process_id('1008', True), '4104 (0x1008)')
        self.assertEqual(wer.process_id('1008', False), '1008')
        self.assertEqual(wer.process_id('zz', True), 'zz')

    def test_hex_code(self):
        self.assertEqual(wer.hex_code('c0000005'), '0xC0000005')
        self.assertEqual(wer.hex_code('0xc0000005'), '0xc0000005')
        self.assertEqual(wer.hex_code(''), '')


class EventFieldsTest(unittest.TestCase):
    def test_named_fields_are_used_as_stored(self):
        record = _Record('Application Error', '1000', {'AppName': ' a.exe ', 'ProcessId': '0x10'})
        self.assertEqual(wer.event_fields(record), ({'AppName': 'a.exe', 'ProcessId': '0x10'}, False))

    def test_classic_strings_are_labelled_by_position(self):
        pieces = ['svchost.exe', '10.0.16299.15', '9c786b9a', 'ucrtbase.dll', '10.0.16299.125',
                  '70f70cc4', 'c0000409', '000000000006b70e', '1008', '01d3c5ae0590aea7',
                  'C:\\Windows\\System32\\svchost.exe', 'C:\\Windows\\System32\\ucrtbase.dll',
                  '808d5242-23ca-4f4b-920e-a8513fb70cf0', '', '']
        record = _Record('Application Error', '1000',
                         values=[''.join(f'<string>{p}</string>' for p in pieces)])
        fields, classic = wer.event_fields(record)
        self.assertTrue(classic)
        self.assertEqual(fields['ProcessId'], '1008')
        self.assertEqual(fields['ProcessCreationTime'], '01d3c5ae0590aea7')
        self.assertEqual(fields['IntegratorReportId'], '808d5242-23ca-4f4b-920e-a8513fb70cf0')
        self.assertEqual(fields['PackageRelativeAppId'], '')

    def test_short_classic_record_leaves_the_rest_blank(self):
        record = _Record('Windows Error Reporting', '1001',
                         values=['<string>0</string><string></string><string>BEX64</string>'])
        fields, _ = wer.event_fields(record)
        self.assertEqual(fields['EventName'], 'BEX64')
        self.assertEqual(fields['CabGuid'], '')


if __name__ == '__main__':
    unittest.main()
