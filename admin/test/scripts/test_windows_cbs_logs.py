"""Pin the CBS and DISM log readers (scripts/artifacts/windowsCbsLogs.py).

The log lines are shaped like those of the tested CBS.log and dism.log files; the times, IDs, clients and command
lines are made up. The cabinets are written here, one MSZIP block per 32 KiB as the tested CbsPersist cabs hold them.
"""
import datetime
import pathlib
import struct
import sys
import unittest
import zlib
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsCbsLogs as cbs
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc


def _cab(payload, name='CbsPersist_20240101000000.log', compression=1, block=32768, recorded=None):
    """A one-folder, one-file cabinet holding payload, MSZIP blocks carrying the previous 32 KiB as history."""
    blocks, done = [], 0
    while done < len(payload):
        chunk = payload[done:done + block]
        history = payload[max(0, done - 32768):done]
        packer = zlib.compressobj(9, zlib.DEFLATED, -15, zdict=history) if history else \
            zlib.compressobj(9, zlib.DEFLATED, -15)
        blocks.append((b'CK' + packer.compress(chunk) + packer.flush(), len(chunk)))
        done += len(chunk)
    file_entry = struct.pack('<IIHHHH', len(payload) if recorded is None else recorded, 0, 0, 0, 0, 0x20) + \
        name.encode() + b'\0'
    folder_at, files_at = 36, 36 + 8
    data_at = files_at + len(file_entry)
    data = b''.join(struct.pack('<IHH', 0, len(packed), size) + packed for packed, size in blocks)
    total = data_at + len(data)
    header = b'MSCF' + struct.pack('<IIIIIBBHHHHH', 0, total, 0, files_at, 0, 3, 1, 1, 1, 0, 0, 0)
    folder = struct.pack('<IHH', data_at, len(blocks), compression)
    assert len(header) == folder_at
    return header + folder + file_entry + data


class MszipCabTest(unittest.TestCase):
    def test_a_cab_of_several_blocks_gives_its_file_back(self):
        payload = ''.join(f'2024-01-01 00:00:{n % 60:02d}, Info                  CBS    line {n}\r\n'
                          for n in range(6000)).encode('utf-8')
        name, data = cbs.mszip_cab_member(_cab(payload))
        self.assertEqual((name, data), ('CbsPersist_20240101000000.log', payload))
        self.assertGreater(len(payload), 3 * 32768)

    def test_a_recorded_size_that_does_not_match_raises(self):
        with self.assertRaises(cbs.CabError):
            cbs.mszip_cab_member(_cab(b'x' * 1000, recorded=999))

    def test_a_cab_that_is_not_mszip_raises(self):
        with self.assertRaises(cbs.CabError):
            cbs.mszip_cab_member(_cab(b'x' * 1000, compression=3))
        with self.assertRaises(cbs.CabError):
            cbs.mszip_cab_member(b'PK\x03\x04' + b'\0' * 60)


def _cbs(*lines):
    return '\ufeff' + ''.join(f'{local}, Info                  {component}    {message}\r\n'
                              for local, component, message in lines)


TI = 'TI: --- Initializing Trusted Installer ---'


class CbsEventsTest(unittest.TestCase):
    def test_each_run_takes_the_offset_of_its_own_utc_line(self):
        text = _cbs(('2024-03-09 10:00:00', 'CBS', 'Session: 1_1 initialized by client Before'),
                    ('2024-03-09 10:00:01', 'CBS', TI),
                    ('2024-03-09 10:00:01', 'CBS', 'TI: Last boot time: 2024-03-09 09:58:00.500'),
                    ('2024-03-09 10:00:02', 'CBS', 'Session: 2_2 initialized by client WinMgmt'),
                    ('2024-03-09 10:00:03', 'CBS', 'Universal Time is: 2024-03-09 18:00:03.120'),
                    ('2024-03-09 10:00:03', 'CBS', 'Loaded Servicing Stack v10.0.1.1 with Core: x'),
                    ('2024-03-09 10:00:04', 'CBS', 'Session: 3_3 initialized by client DISM Package Manager '
                                                   'Provider, external staging directory: (null), external '
                                                   'registry directory: (null'),
                    ('2024-03-09 10:00:05', 'CSI', 'Session: 9_9 initialized by client NotCbs'),
                    ('2024-03-12 10:00:00', 'CBS', TI),
                    ('2024-03-12 10:00:01', 'CBS', 'Universal Time is: 2024-03-12 17:00:01.000'),
                    ('2024-03-12 10:00:02', 'CBS', 'Session: 4_4 initialized by client WindowsUpdateAgent.'),
                    ('2024-03-12 11:00:00', 'CBS', TI),
                    ('2024-03-12 11:00:00', 'CBS', 'Session: 5_5 initialized by client NoUtcInRun'))
        problems = Counter()
        starts, sessions = cbs.cbs_events(text, problems)
        self.assertEqual([(s['local'], s['offset'], s['boot'], s['stack']) for s in starts], [
            ('2024-03-09 10:00:01', -480, '2024-03-09 09:58:00.500', 'v10.0.1.1'),
            ('2024-03-12 10:00:00', -420, '', ''),
            ('2024-03-12 11:00:00', None, '', ''),
        ])
        self.assertEqual(sessions, [
            ('2024-03-09 10:00:00', None, '1_1', 'Before'),
            ('2024-03-09 10:00:02', -480, '2_2', 'WinMgmt'),
            ('2024-03-09 10:00:04', -480, '3_3', 'DISM Package Manager Provider'),
            ('2024-03-12 10:00:02', -420, '4_4', 'WindowsUpdateAgent'),
            ('2024-03-12 11:00:00', None, '5_5', 'NoUtcInRun'),
        ])
        self.assertEqual(problems, {'TrustedInstaller starts with no UTC line in their run, UTC left blank': 1})
        self.assertEqual(cbs._utc('2024-03-09 10:00:02', -480),  # pylint: disable=protected-access
                         datetime.datetime(2024, 3, 9, 18, 0, 2, tzinfo=UTC))
        self.assertEqual(cbs._utc('2024-03-09 09:58:00.500', -480),  # pylint: disable=protected-access
                         datetime.datetime(2024, 3, 9, 17, 58, 0, 500000, tzinfo=UTC))
        self.assertEqual(cbs._utc('not a time', -480), '')  # pylint: disable=protected-access
        self.assertEqual(cbs._offset_text(-480), 'UTC-08:00')  # pylint: disable=protected-access
        self.assertEqual(cbs._offset_text(330), 'UTC+05:30')  # pylint: disable=protected-access

    def test_a_log_with_no_utc_line_leaves_utc_blank(self):
        text = _cbs(('2015-03-25 03:33:15', 'CBS', 'Session: 6_6 initialized by client WindowsUpdateAgent'))
        starts, sessions = cbs.cbs_events(text, Counter())
        self.assertEqual((starts, sessions), ([], [('2015-03-25 03:33:15', None, '6_6', 'WindowsUpdateAgent')]))
        self.assertEqual(cbs._utc('2015-03-25 03:33:15', None), '')  # pylint: disable=protected-access

    def test_a_run_whose_utc_lines_disagree_is_counted_and_rows_follow_the_line_before_them(self):
        text = _cbs(('2024-11-03 01:00:00', 'CBS', TI),
                    ('2024-11-03 01:00:01', 'CBS', 'Universal Time is: 2024-11-03 05:00:01.000'),
                    ('2024-11-03 01:30:00', 'CBS', 'Session: 7_7 initialized by client A'),
                    ('2024-11-03 01:10:00', 'CBS', 'Universal Time is: 2024-11-03 06:10:00.000'),
                    ('2024-11-03 01:20:00', 'CBS', 'Session: 8_8 initialized by client B'))
        problems = Counter()
        starts, sessions = cbs.cbs_events(text, problems)
        self.assertEqual(starts[0]['offset'], -240)
        self.assertEqual([s[1] for s in sessions], [-240, -300])
        self.assertEqual(problems, {'TrustedInstaller runs whose UTC lines give more than one offset': 1})


def _dism(*lines):
    return '\ufeff' + ''.join(f'{local}, {level:<22}DISM   {message}\r\n' for local, level, message in lines)


class DismSessionsTest(unittest.TestCase):
    def test_exe_and_api_sessions_with_interleaved_processes(self):
        text = _dism(
            ('2024-08-30 15:53:16', 'Info', 'DISM.EXE: <----- Starting Dism.exe session ----->'),
            ('2024-08-30 15:53:16', 'Info', 'DISM.EXE: Host machine information: OS Version=10.0.26100, Running '
                                            'architecture=amd64, Number of processors=8'),
            ('2024-08-30 15:53:16', 'Info', 'DISM.EXE: Executing command line: dism.exe /online /get-features'),
            ('2024-08-30 15:53:16', 'Info', 'DISM Manager: PID=7624 TID=7616 Image session successfully loaded - '
                                            'CDISMManager::CreateImageSession'),
            ('2024-08-30 15:53:17', 'Info', 'API: PID=100 TID=1 DismApi.dll: <----- Starting DismApi.dll session '
                                            '-----> - DismInitializeInternal'),
            ('2024-08-30 15:53:17', 'Info', 'API: PID=100 TID=1 DismApi.dll: Host machine information: OS '
                                            'Version=10.0.26100, Running architecture=x86 - DismInitializeInternal'),
            ('2024-08-30 15:53:17', 'Info', 'API: PID=100 TID=1 DismApi.dll: Parent process command line: '
                                            'C:\\Windows\\system32\\made-up.exe /x - DismInitializeInternal'),
            ('2024-08-30 15:53:18', 'Info', 'API: PID=200 TID=2 DismApi.dll: <----- Starting DismApi.dll session '
                                            '-----> - DismInitializeInternal'),
            ('2024-08-30 15:53:18', 'Info', 'API: PID=100 TID=1 DismApi.dll: <----- Ending DismApi.dll session '
                                            '-----> - DismShutdownInternal'),
            ('2024-08-30 15:53:19', 'Info', 'DISM.EXE: Image session has been closed. Reboot required=no.'),
            ('2024-08-30 15:53:19', 'Info', 'DISM.EXE: <----- Ending Dism.exe session ----->'))
        problems = Counter()
        sessions = cbs.dism_sessions(text, problems)
        self.assertEqual([(s['start'], s['end'], s['kind'], s['command'], s['parent'], s['pid'], s['reboot'])
                          for s in sessions], [
            ('2024-08-30 15:53:16', '2024-08-30 15:53:19', 'Dism.exe', 'dism.exe /online /get-features', '', '7624',
             'no'),
            ('2024-08-30 15:53:17', '2024-08-30 15:53:18', 'DismApi.dll', '', 'C:\\Windows\\system32\\made-up.exe /x',
             '100', ''),
            ('2024-08-30 15:53:18', '', 'DismApi.dll', '', '', '200', ''),
        ])
        self.assertEqual(problems, {'sessions with no ending line, reported with a blank end time': 1})

    def test_a_log_with_no_session_gives_no_rows(self):
        self.assertEqual(cbs.dism_sessions(_dism(('2024-08-30 15:53:16', 'Info', 'DISM.EXE: nothing')), Counter()),
                         [])


if __name__ == '__main__':
    unittest.main()
