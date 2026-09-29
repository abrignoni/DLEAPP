"""Pin how the Eufy Floodlight artifacts read the camera's recordings and log files.

Every value here is made up for the test.
"""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import eufyFloodlight
# pylint: enable=wrong-import-position

UTC = timezone.utc
T0 = 1759000000000                              # 2025-09-27 19:06:40 UTC, in milliseconds


def record(kind, ms, payload_extra=40):
    """One XZYH record: magic, type, a byte, a 4-byte length, 6 bytes, then the payload."""
    at = {0x14: 30, 0x15: 24}[kind] - 16
    payload = bytearray(at + 8 + payload_extra)
    struct.pack_into('<Q', payload, at, ms)
    return b'XZYH' + bytes([kind, 5]) + struct.pack('<I', len(payload)) + bytes(6) + bytes(payload)


def recording(start_ms, frames=3):
    out = b''
    for i in range(frames):
        out += record(0x14, start_ms + i * 66) + record(0x15, start_ms + i * 66 + 3)
    return out


class RecordingTest(unittest.TestCase):
    def test_whole_records_give_counts_and_the_frame_times(self):
        video, audio, times = eufyFloodlight.read_recording(recording(T0))
        self.assertEqual((video, audio), (3, 3))
        self.assertEqual((min(times), max(times)), (T0, T0 + 135))

    def test_a_cut_or_foreign_record_is_not_read(self):
        data = recording(T0)
        self.assertIsNone(eufyFloodlight.read_recording(data[:-5]))
        self.assertIsNone(eufyFloodlight.read_recording(data + b'XZYH' + bytes([0x16, 5]) + bytes(10)))
        self.assertIsNone(eufyFloodlight.read_recording(data + b'junk'))

    def test_the_row_carries_utc_frame_times_and_the_name_time_as_stored(self):
        row = eufyFloodlight.recording_row('20250927130640.dat', recording(T0))
        self.assertEqual(row, (datetime(2025, 9, 27, 19, 6, 40, tzinfo=UTC),
                               datetime(2025, 9, 27, 19, 6, 40, 135000, tzinfo=UTC), 0.135,
                               '2025-09-27 13:06:40', 3, 3, '', len(recording(T0)), '20250927130640.dat'))

    def test_frames_stamped_before_2000_leave_the_times_blank(self):
        row = eufyFloodlight.recording_row('20250927130640.dat', recording(9979368))
        self.assertEqual(row[:3], ('', '', 0.135))
        self.assertEqual(row[6], 'stamped before 2000, first frame 1970-01-01 02:46:19.368')

    def test_a_file_without_the_magic_is_not_a_recording(self):
        self.assertIsNone(eufyFloodlight.recording_row('base_param.dat', b'\x00' * 64))

    def test_a_file_with_the_magic_but_broken_records_keeps_its_size(self):
        row = eufyFloodlight.recording_row('20250927130640.dat', recording(T0)[:-5])
        self.assertEqual(row[6:8], ('records not read', len(recording(T0)) - 5))


LOG = '\n'.join((
    '2025-09-27 13:00:00.100 [INFO][security_main.c:main:889] - =====floodlight system bootup=====',
    '2025-09-27 13:00:01.000 [WARN][sys_interface.c:System_SetTime:2477] - not system time,need calibration time.',
    '2025-09-27 13:00:02.000 [INFO][floodlight_interface.c:zx_hisi_wifi_connect_network:1] - connect wifi, '
    'bssid = , ssid = TestNet',
    '2025-09-27 13:00:03.000 [INFO][floodlight_interface.c:zx_hisi_wifi_connect_network:1] - connect wifi, '
    'bssid = 02:00:00:00:00:01, ssid = TestNet',
    '2025-09-27 13:00:04.000 [INFO][floodlight_interface.c:zx_hisi_wifi_connect_network:1] - connect wifi, '
    'bssid = , ssid = TestNet',
    '2025-09-27 13:00:05.000 [INFO][floodlight_interface.c:zx_fd_network_detection:1] - internet ip:192.0.2.7',
    '2025-09-27 13:00:06.000 [INFO][floodlight_interface.c:zx_fd_network_detection:1] - internet ip:',
    '2025-09-27 13:00:07.000 [INFO][floodlight_interface.c:zx_fd_network_detection:1] - internet ip:192.0.2.7',
    '2025-09-27 13:00:08.000 [INFO][floodlight_interface.c:zx_hisi_wifi_connect_network:1] - hisi wifi current mode '
    'status i2025-09-27 13:00:09.000 [INFO][sys_interface.c:System_SetTime:2459] - set system time:1759000000',
    '2025-09-27 13:06:40.001 [INFO][local_storage_interface.c:pir_triger_handle_by_channel:1578] - camera: 0, '
    'record trigger, mode:1, pir action: 0x9',
    '2025-09-27 13:06:40.002 [INFO][local_storage_interface.c:open_local_file_by_channel:1929] - have_bind_app = 1 '
    ',creat local file: /mnt/data/Camera00/20250927130640.dat',
    '2025-09-27 13:06:40.003 [INFO][push_interface.c:zx_push_message:879] - [131076] Floodlight Motion is detected ...',
    '',
    '64 bytes from 192.0.2.1: seq=0 ttl=64 time=1.0 ms',
    '2025-09-27 13:06:50.000 [INFO][local_storage_interface.c:close_local_fp_by_channel:1993] - close file: '
    '/mnt/data/Camera00/20250927130640.dat',
    '2025-09-27 13:06:51.000 [INFO][as_interface.c:zx_upload_hub_history_record:3289] - code=0 '
    'file:/mnt/data/Camera00/20250927130640.dat',
    '2025-09-27 13:06:52.000 [INFO][ppcs_interface.c:zx_p2p_listen:8971] - ppcs listen ...',
    '2025-09-27 13:07:00.000 [INFO][floodlight_interface.c:zx_hisi_wifi_connect_network:1] - connect wifi, '
    'bssid = 02:00:00:00:00:02, ssid = TestNet',
))


class LogTest(unittest.TestCase):
    def test_selected_lines_become_events_and_the_rest_are_counted(self):
        counts = Counter()
        rows = eufyFloodlight.log_rows(LOG, counts)
        self.assertEqual([(r[0], r[1]) for r in rows], [
            ('2025-09-27 13:00:00.100', 'System Boot'),
            ('2025-09-27 13:00:01.000', 'Clock Not Set'),
            ('2025-09-27 13:00:02.000', 'Wi-Fi Network'),
            ('2025-09-27 13:00:03.000', 'Wi-Fi Network'),
            ('2025-09-27 13:00:05.000', 'Internet IP'),
            ('2025-09-27 13:00:09.000', 'Clock Set'),
            ('2025-09-27 13:06:40.001', 'Record Trigger'),
            ('2025-09-27 13:06:40.002', 'Recording Created'),
            ('2025-09-27 13:06:40.003', 'Motion Push'),
            ('2025-09-27 13:06:50.000', 'Recording Closed'),
            ('2025-09-27 13:06:51.000', 'Recording Uploaded'),
            ('2025-09-27 13:07:00.000', 'Wi-Fi Network')])
        self.assertEqual(counts, {'lines in no known form, not reported': 1})

    def test_the_line_split_off_a_merged_line_keeps_its_line_number_and_its_unix_time(self):
        clock = [r for r in eufyFloodlight.log_rows(LOG, Counter()) if r[1] == 'Clock Set'][0]
        self.assertEqual(clock[4], datetime(2025, 9, 27, 19, 6, 40, tzinfo=UTC))
        self.assertEqual((clock[5], clock[6], clock[7]), ('INFO', 'sys_interface.c:System_SetTime:2459', 9))

    def test_a_recording_named_in_a_message_is_given_by_name(self):
        rows = eufyFloodlight.log_rows(LOG, Counter())
        self.assertEqual([r[3] for r in rows if r[3]], ['20250927130640.dat'] * 3)

    def test_a_log_with_no_line_from_the_camera_program_is_not_its_own(self):
        self.assertTrue(eufyFloodlight.is_own_log(LOG))
        self.assertFalse(eufyFloodlight.is_own_log(
            '2025-09-27 13:00:00.100 [INFO][other.c:main:1] - hello\n'))


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_recordings_are_read_in_name_order_and_other_files_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            cam = os.path.join(root, 'vol', 'Camera00')
            os.makedirs(cam)
            files = []
            for name, data in (('20250927130700.dat', recording(T0 + 20000)), ('20250927130640.dat', recording(T0)),
                               ('notes.dat', b'\x00' * 32)):
                path = os.path.join(cam, name)
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            other = os.path.join(root, 'vol', 'data', 'base_param.dat')
            os.makedirs(os.path.dirname(other))
            with open(other, 'wb') as handle:
                handle.write(recording(T0))
            files += [other, cam]
            with mock.patch.object(eufyFloodlight, 'logfunc') as log:
                headers, rows, source = eufyFloodlight.eufyFloodlightRecordings.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([r[-1] for r in rows], [os.path.join('vol', 'Camera00', '20250927130640.dat'),
                                                 os.path.join('vol', 'Camera00', '20250927130700.dat')])
        self.assertEqual(len(source.split('\n')), 2)
        self.assertEqual(log.call_args.args[0],
                         'Eufy Floodlight Recordings: 1 files without the XZYH magic, not reported')

    def test_log_files_are_read_only_under_their_own_name_and_program(self):
        with tempfile.TemporaryDirectory() as root:
            logs = os.path.join(root, 'vol', 'log')
            os.makedirs(logs)
            files = []
            for name, text in (('sec.2025-09-27.log', LOG), ('sec.2025-09-28.log', '2025-09-28 00:00:00.000 '
                                                             '[INFO][other.c:main:1] - hello\n'),
                               ('messages.log', LOG)):
                path = os.path.join(logs, name)
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write(text)
                files.append(path)
            with mock.patch.object(eufyFloodlight, 'logfunc') as log:
                headers, rows, source = eufyFloodlight.eufyFloodlightLog.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 12)
        self.assertEqual({r[-1] for r in rows}, {os.path.join('vol', 'log', 'sec.2025-09-27.log')})
        self.assertEqual(source, os.path.join(logs, 'sec.2025-09-27.log'))
        self.assertEqual(log.call_args.args[0], 'Eufy Floodlight Log Events: 1 files with no line from the camera '
                                                'program, not read, 1 lines in no known form, not reported')


if __name__ == '__main__':
    unittest.main()
