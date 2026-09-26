"""Pin the rows and time handling of scripts/artifacts/windowsUpdateReportingEvents.py."""
import datetime
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsUpdateReportingEvents as wu  # pylint: disable=wrong-import-position

_UTC = datetime.timezone.utc
_INSTALL = ('{16D57C29-A552-4B80-80E9-A353C6D90CBE}\t2023-01-06 09:45:55:528-0500\t1\t'
            '183 [AGENT_INSTALLING_SUCCEEDED]\t101\t{A188C2E0-209F-486C-9D51-9953B1D2612E}\t200\t0\t'
            'MoUpdateOrchestrator\tSuccess\tContent Install\tInstallation Successful: Windows '
            'successfully installed the following update: Security Intelligence Update - '
            'KB2267602 (Version 1.381.1819.0)\taS8pKHUwl0i6mrKJ.1.2.3.0')
_FAILED = ('{2C3C39FA-FC0F-4F44-9049-D2AA53B27FFB}\t2017-12-12 19:46:19:636+0900\t1\t'
           '182 [AGENT_INSTALLING_FAILED]\t101\t{BFC8A103-FD5F-4458-9935-231D9F79E2C1}\t203\t'
           '80242015\tUpdateOrchestrator\tFailure\tContent Install\tInstallation Failure: '
           'Windows failed to install the following update with error 0x80242015: '
           'Cumulative Update (KB4051033)')
_DETECTED = ('{F92EBDC6-56ED-4274-B83A-28BC44DAF341}\t2019-03-19 05:59:52:781-0700\t1\t'
             '147 [AGENT_DETECTION_FINISHED]\t101\t{00000000-0000-0000-0000-000000000000}\t0\t0\t'
             'OOBE ZDP\tSuccess\tSoftware Synchronization\tWindows Update Client successfully '
             'detected 0 updates.\tEfCwogNQ1EeAbVQe.1.0.0.3.0')


class TimeTest(unittest.TestCase):
    def test_the_recorded_offset_converts_the_time_to_utc(self):
        self.assertEqual(wu.utc_time('2023-01-06 09:45:55:528-0500'),
                         datetime.datetime(2023, 1, 6, 14, 45, 55, 528000, tzinfo=_UTC))
        self.assertEqual(wu.utc_time('2017-12-12 19:46:19:636+0900'),
                         datetime.datetime(2017, 12, 12, 10, 46, 19, 636000, tzinfo=_UTC))
        self.assertEqual(wu.utc_time('2019-03-19 05:59:52:781-0730'),
                         datetime.datetime(2019, 3, 19, 13, 29, 52, 781000, tzinfo=_UTC))

    def test_a_time_that_does_not_parse_is_blank(self):
        for text in ('', '2023-01-06 09:45:55-0500', '2023-01-06 09:45:55:528', '2023-13-06 '
                     '09:45:55:528-0500', 'x'):
            self.assertEqual(wu.utc_time(text), '', text)


class RowTest(unittest.TestCase):
    def test_install_line(self):
        row = wu.line_row(_INSTALL.split('\t'))
        self.assertEqual(row[0], datetime.datetime(2023, 1, 6, 14, 45, 55, 528000, tzinfo=_UTC))
        self.assertEqual(row[1:9], ('2023-01-06 09:45:55:528-0500', '183',
                                    'AGENT_INSTALLING_SUCCEEDED', 'Success', 'Content Install',
                                    '0', 'MoUpdateOrchestrator',
                                    '{A188C2E0-209F-486C-9D51-9953B1D2612E}'))
        self.assertEqual(row[10], 'Security Intelligence Update - KB2267602 (Version 1.381.1819.0)')

    def test_a_twelve_field_line_and_a_failure_title(self):
        row = wu.line_row(_FAILED.split('\t'))
        self.assertEqual((row[2], row[3], row[4], row[6]),
                         ('182', 'AGENT_INSTALLING_FAILED', 'Failure', '80242015'))
        self.assertEqual(row[10], 'Cumulative Update (KB4051033)')

    def test_a_line_naming_no_update_has_no_title(self):
        row = wu.line_row(_DETECTED.split('\t'))
        self.assertEqual((row[2], row[3], row[10]), ('147', 'AGENT_DETECTION_FINISHED', ''))

    def test_an_event_field_without_a_bracketed_name_is_kept(self):
        fields = _DETECTED.split('\t')
        fields[3] = '147'
        self.assertEqual(wu.line_row(fields)[2:4], ('147', ''))


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class ProcessorTest(unittest.TestCase):
    def run_on(self, raw):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'Windows', 'SoftwareDistribution')
            folder.mkdir(parents=True)
            log = folder / 'ReportingEvents.log'
            log.write_bytes(raw)
            return wu.windowsUpdateReportingEvents.__wrapped__(
                FakeContext(tmp, [str(folder), str(log)]))

    def test_utf16_lines_of_12_or_13_fields_are_read_and_others_skipped(self):
        text = '\r\n'.join([_DETECTED, '', _FAILED, 'a\tb\tc', _INSTALL]) + '\r\n'
        headers, rows, source = self.run_on(text.encode('utf-16'))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([row[2] for row in rows], ['147', '182', '183'])
        self.assertTrue(source.endswith('ReportingEvents.log'))

    def test_a_file_without_a_byte_order_mark_is_read_as_utf8(self):
        _headers, rows, _source = self.run_on((_INSTALL + '\n').encode('utf-8'))
        self.assertEqual(len(rows), 1)


if __name__ == '__main__':
    unittest.main()
