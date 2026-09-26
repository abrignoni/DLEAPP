"""Pin the rows, time handling and file handling of scripts/artifacts/windowsStartupInfo.py."""
import datetime
import pathlib
import sys
import tempfile
import unittest
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsStartupInfo as si  # pylint: disable=wrong-import-position

_UTC = datetime.timezone.utc
_SID = 'S-1-5-21-1-2-3-1001'

_DOC = '''<?xml version="1.0" encoding="UTF-16"?>
<StartupData IntervalStartMs="8391" IntervalEndMs="98391">
\t<Process Name="C:\\Program Files\\App\\app.exe" PID="10020" StartedInTraceSec="28.398">
\t\t<StartTime>2023/01/05:01:24:03.6392207</StartTime>
\t\t<CommandLine>"C:\\Program Files\\App\\app.exe" --type=gpu</CommandLine>
\t\t<DiskUsage Units="bytes">27667456</DiskUsage>
\t\t<CpuUsage Units="us">4486251</CpuUsage>
\t\t<ParentPID>10084</ParentPID>
\t\t<ParentStartTime>2023/01/05:01:24:02.1053013</ParentStartTime>
\t\t<ParentName>app.exe</ParentName>
\t</Process>
\t<Process Name="C:\\Devic" PID="7" StartedInTraceSec="30">
\t\t<StartTime>2023/01/05:01:24:05</StartTime>
\t\t<CommandLine>C:\\Windows\\a.exe</CommandLine>
\t\t<DiskUsage Units="KB">5</DiskUsage>
\t\t<CpuUsage Units="us">0</CpuUsage>
\t\t<ParentPID>4</ParentPID>
\t\t<ParentStartTime>not a time</ParentStartTime>
\t\t<ParentName>explorer.exe</ParentName>
\t</Process>
\t<ReadAheadAnalysisTime>0</ReadAheadAnalysisTime>
\t<RurLegacyResourceAttribution>15</RurLegacyResourceAttribution>
</StartupData>
'''


class TimeTest(unittest.TestCase):
    def test_times_are_utc_and_truncated_to_microseconds(self):
        self.assertEqual(si.utc_time('2023/01/05:01:24:03.6392207'),
                         datetime.datetime(2023, 1, 5, 1, 24, 3, 639220, tzinfo=_UTC))
        self.assertEqual(si.utc_time('2023/01/05:01:24:03'),
                         datetime.datetime(2023, 1, 5, 1, 24, 3, tzinfo=_UTC))
        self.assertEqual(si.utc_time('2023/01/05:01:24:03.5'),
                         datetime.datetime(2023, 1, 5, 1, 24, 3, 500000, tzinfo=_UTC))

    def test_a_time_that_does_not_parse_is_blank(self):
        for text in ('', None, 'not a time', '2023-01-05 01:24:03', '2023/13/05:01:24:03',
                     '2023/01/05:01:24:03.12345678'):
            self.assertEqual(si.utc_time(text), '', text)

    def test_interval_start_is_start_time_less_trace_seconds_plus_the_interval(self):
        started = si.utc_time('2023/01/05:01:24:03.6392207')
        self.assertEqual(si.interval_start(started, '28.398', '8391'),
                         datetime.datetime(2023, 1, 5, 1, 23, 43, 632220, tzinfo=_UTC))
        self.assertEqual(si.interval_start(started, '', '8391'), '')
        self.assertEqual(si.interval_start(started, '28.398', ''), '')


class RowTest(unittest.TestCase):
    def test_rows(self):
        root = ElementTree.fromstring(_DOC.split('\n', 1)[1])
        rows = si.process_rows(root, _SID, 'StartupInfo3.xml')
        self.assertEqual(len(rows), 2)
        first, second = rows[0], rows[1]
        self.assertEqual(first[0], datetime.datetime(2023, 1, 5, 1, 24, 3, 639220, tzinfo=_UTC))
        self.assertEqual(first[1:6], ('C:\\Program Files\\App\\app.exe', '10020',
                                      '"C:\\Program Files\\App\\app.exe" --type=gpu', 'app.exe',
                                      '10084'))
        self.assertEqual(first[6], datetime.datetime(2023, 1, 5, 1, 24, 2, 105301, tzinfo=_UTC))
        self.assertEqual(first[7:10], ('27667456', '4486251', '28.398'))
        self.assertEqual(first[10], datetime.datetime(2023, 1, 5, 1, 23, 43, 632220, tzinfo=_UTC))
        self.assertEqual(first[11:], ('8391', '98391', _SID, 'StartupInfo3.xml'))
        self.assertEqual(second[1], 'C:\\Devic')
        self.assertEqual(second[6], '')
        self.assertEqual((second[7], second[8]), ('5 KB', '0'))


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))


class ProcessorTest(unittest.TestCase):
    def test_reads_utf16_files_named_for_a_sid_and_skips_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'Windows', 'System32', 'WDI', 'LogFiles', 'StartupInfo')
            folder.mkdir(parents=True)
            good = folder / f'{_SID}_StartupInfo3.xml'
            good.write_bytes(_DOC.encode('utf-16'))
            empty = folder / f'{_SID}_StartupInfo1.xml'
            empty.write_bytes('<?xml version="1.0" encoding="UTF-16"?>\r\n<StartupData '
                              'IntervalStartMs="1" IntervalEndMs="90001"/>'.encode('utf-16'))
            broken = folder / f'{_SID}_StartupInfo2.xml'
            broken.write_bytes('<StartupData><Process'.encode('utf-16'))
            other_root = folder / f'{_SID}_StartupInfo4.xml'
            other_root.write_bytes('<Other/>'.encode('utf-16'))
            unnamed = folder / 'StartupInfo5.xml'
            unnamed.write_bytes(_DOC.encode('utf-16'))
            files = [str(p) for p in (good, empty, broken, other_root, unnamed, folder)]
            headers, rows, source = si.startupInfo.__wrapped__(FakeContext(tmp, files))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 2)
        self.assertEqual({row[13:] for row in rows}, {(_SID, 'StartupInfo3.xml')})
        self.assertEqual(source.split('\n'), [str(empty), str(good)])


if __name__ == '__main__':
    unittest.main()
