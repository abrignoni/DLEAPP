"""Tests for the Explorer startup log artifacts, on synthetic files built with etl_fixture.py's record writers.

Every value is made up. The Windows 7 case reproduces the first-buffer header the ten Windows 7 files read had:
SavedOffset 0 and an Offset that ends at the last record.
"""

import os
import struct
import sys
import tempfile
import unittest
import uuid
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import etl_fixture  # noqa: E402  pylint: disable=wrong-import-position
from scripts import etl  # noqa: E402  pylint: disable=wrong-import-position
from scripts.artifacts import windowsExplorerStartupLog as startup  # noqa: E402  pylint: disable=wrong-import-position

SHELL_CORE = uuid.UUID('30336ed4-e327-447c-9de0-51b652c86108')
OTHER = uuid.UUID('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
KEY = 'Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
COMMAND = 'fixture.exe /startup '                       # the trailing space is trimmed in the report
T0 = etl_fixture.T0


def _u(text):
    return text.encode('utf-16-le') + b'\x00\x00'


def _records():
    return [
        etl_fixture.event_record(SHELL_CORE, 19501, T0 + 10, _u('C:\\fixture')),
        etl_fixture.event_record(SHELL_CORE, 9705, T0 + 2_628_198, _u(KEY)),
        etl_fixture.event_record(SHELL_CORE, 9707, T0 + 2_628_198 * 2, _u(COMMAND)),
        etl_fixture.event_record(SHELL_CORE, 9708, T0 + 2_628_198 * 3, struct.pack('<I', 4321) + _u(COMMAND)),
        etl_fixture.event_record(SHELL_CORE, 9706, T0 + 2_628_198 * 4, _u(KEY)),
        etl_fixture.event_record(OTHER, 9707, T0 + 2_628_198 * 5, _u('not shell core')),
    ]


def build(windows7=False):
    first = bytearray(etl_fixture.buffer([etl_fixture.logfile_header_record()], 0, 0, first=True))
    if windows7:
        struct.pack_into('<I', first, 4, 0)                 # SavedOffset; Offset at 0x30 keeps the bytes in use
    second = etl_fixture.buffer(_records(), 1, T0 + 2_628_198 * 5)
    return bytes(first) + second


class _Context:

    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return path


class StartupLogTest(unittest.TestCase):

    def test_command_events(self):
        problems = Counter()
        trace, found, total = startup.startup_log(build(), 'test', problems)
        self.assertEqual(problems, Counter())
        self.assertEqual(total, 5)                          # the event of the other provider is not counted
        self.assertEqual([(e.event_id, message) for e, message, _ in found], [
            (9705, 'Started enumeration of commands for registry key'),
            (9707, 'Started execution of command'),
            (9708, 'Finished execution of command'),
            (9706, 'Finished enumeration of commands for registry key')])
        self.assertEqual([values for _, _, values in found],
                         [{'KeyName': KEY}, {'Command': COMMAND}, {'PID': 4321, 'Command': COMMAND}, {'KeyName': KEY}])
        self.assertEqual(trace.header['start_time'], etl_fixture.START_TIME)

    def test_windows7_first_buffer(self):
        """SavedOffset 0 in the first buffer: the Offset member gives the bytes in use and nothing is skipped."""
        data = build(windows7=True)
        self.assertEqual(struct.unpack_from('<I', data, 4)[0], 0)
        trace = etl.EtlFile(data)
        self.assertEqual(len(list(trace.events())), 6)
        self.assertEqual(trace.kinds, Counter({'event64': 6, 'system64': 1}))
        self.assertEqual(trace.problems, Counter())
        both = bytearray(data)
        struct.pack_into('<I', both, 0x30, 0)               # neither member set: the buffer is counted, not read
        trace = etl.EtlFile(bytes(both))
        self.assertEqual(len(list(trace.events())), 6)
        self.assertEqual(trace.problems,
                         Counter({'buffers whose bytes in use lie outside the buffer, not read': 1}))

    def test_other_version_and_bad_data_are_counted(self):
        records = _records()
        records[1] = etl_fixture.event_record(SHELL_CORE, 9705, T0 + 2_628_198, _u(KEY), version=1)
        records[3] = etl_fixture.event_record(SHELL_CORE, 9708, T0 + 2_628_198 * 3, b'\x01\x00')
        records.append(etl_fixture.event_record(SHELL_CORE, 9707, T0 + 2_628_198 * 6, _u(COMMAND) + b'\x00' * 8))
        first = etl_fixture.buffer([etl_fixture.logfile_header_record()], 0, 0, first=True)
        data = first + etl_fixture.buffer(records, 1, T0 + 2_628_198 * 6)
        problems = Counter()
        _trace, found, _total = startup.startup_log(data, 'test', problems)
        self.assertEqual([e.event_id for e, _, _ in found], [9707, 9706])
        self.assertEqual(problems, Counter({
            'test: events 9705 of version 1, which has no template here': 1,
            'test: events 9708 whose data ends before their template': 1,
            'test: events 9707 with data left after their template': 1}))

    def test_profile_folder(self):
        tail = 'AppData/Local/Microsoft/Windows/Explorer/ExplorerStartupLog.etl'
        self.assertEqual(startup._profile(f'/case/data/p3/Users/fixture user/{tail}'), 'fixture user')  # pylint: disable=protected-access
        self.assertEqual(startup._profile('C:\\case\\data\\Users\\other\\' + tail.replace('/', '\\')), 'other')  # pylint: disable=protected-access
        self.assertEqual(startup._profile('/case/data/Users/x/APPDATA/LOCAL/MICROSOFT/WINDOWS/EXPLORER/a.etl'), 'x')  # pylint: disable=protected-access
        self.assertEqual(startup._profile('/case/Users/fixture/ExplorerStartupLog.etl'), '')  # pylint: disable=protected-access

    def test_artifact_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for user, windows7 in (('fixture one', False), ('fixture two', True)):
                where = os.path.join(folder, 'Users', user, 'AppData', 'Local', 'Microsoft', 'Windows', 'Explorer')
                os.makedirs(where)
                name = 'ExplorerStartupLog_RunOnce.etl' if windows7 else 'ExplorerStartupLog.etl'
                paths.append(os.path.join(where, name))
                with open(paths[-1], 'wb') as handle:
                    handle.write(build(windows7))
            bad = os.path.join(os.path.dirname(paths[0]), 'ExplorerStartupLog_bad.etl')
            with open(bad, 'wb') as handle:
                handle.write(b'\x00' * 8192)
            context = _Context(paths + [bad, paths[0]])
            headers, rows, sources = startup.windowsExplorerStartupLogCommands.__wrapped__(context)
            self.assertEqual(sources.split('\n'), sorted(paths))
            self.assertEqual(len(rows), 8)
            self.assertEqual(len(headers), len(rows[0]))
            self.assertEqual(rows[2], (datetime(2022, 6, 18, 4, 26, 43, tzinfo=timezone.utc), 9708,
                                       'Finished execution of command', '', 'fixture.exe /startup', 4321, 200,
                                       'fixture one', 'ExplorerStartupLog.etl'))
            self.assertEqual(rows[0][3:6], (KEY, '', ''))
            self.assertEqual({row[7:] for row in rows}, {('fixture one', 'ExplorerStartupLog.etl'),
                                                         ('fixture two', 'ExplorerStartupLog_RunOnce.etl')})
            headers, rows, sources = startup.windowsExplorerStartupLogSessions.__wrapped__(context)
            self.assertEqual(sources.split('\n'), sorted(paths))
            self.assertEqual(len(headers), len(rows[0]))
            start = datetime(2022, 6, 18, 4, 26, 40, tzinfo=timezone.utc)
            self.assertEqual(rows[0][:2], (start, ''))      # the fixture's EndTime is 0
            self.assertEqual([row[4:] for row in rows], [('fixture one', 'ExplorerStartupLog.etl', 5, 4, 0, 0),
                                                         ('fixture two', 'ExplorerStartupLog_RunOnce.etl', 5, 4, 0, 0)])


if __name__ == '__main__':
    unittest.main()
