"""Pin how the Skybell Doorbell artifacts read the doorbell's logs and settings.

Every value here is made up for the test.
"""
import json
import os
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import skybellDoorbell
# pylint: enable=wrong-import-position

UTC = timezone.utc

SYSTEM = '\n'.join((
    'cut short at the rotation',
    "Device-ID: 'aaaa', UUID: '00000000-0000-4000-8000-000000000001'",
    "Serial-No: '123', MAC: '02:00:00:00:00:01' IP: '192.0.2.5'",
    '2025/09/27-19:06:40[1759000000.5] v1.0.0 [Sep 27 2025/19:00:00] -- rootfs-A[version.1]',
    "Device-ID: 'aaaa', UUID: '00000000-0000-4000-8000-000000000001'",
    "Serial-No: '123', MAC: '02:00:00:00:00:01' IP: '192.0.2.5'",
    '2025/09/27-19:06:41[1759000001.000123] ALERT-wifi_get_info().646: wifi is not up',
    '2025/09/27-19:06:42[1759000002.9] DBUG0: [pir[2]=80]',
    '2025/09/27-19:06:43[1759000003.25] log_restart(system): session 0x1',
    "Device-ID: 'aaaa', UUID: '00000000-0000-4000-8000-000000000001'",
    "Serial-No: '123', MAC: '02:00:00:00:00:01' IP: '192.0.2.6'",
    "Serial-No: '123', MAC: '02:00:00:00:00:01' IP: '192.0.2.6'",
))


class LogTest(unittest.TestCase):
    def test_timed_lines_are_split_and_dbug_and_untimed_lines_counted(self):
        counts = Counter()
        rows = skybellDoorbell.log_rows(SYSTEM, counts)
        self.assertEqual(rows, [
            (datetime(2025, 9, 27, 19, 6, 40, 500000, tzinfo=UTC), '2025/09/27-19:06:40', '', '',
             'v1.0.0 [Sep 27 2025/19:00:00] -- rootfs-A[version.1]', 4),
            (datetime(2025, 9, 27, 19, 6, 41, 123, tzinfo=UTC), '2025/09/27-19:06:41', 'ALERT',
             'wifi_get_info().646', 'wifi is not up', 7),
            (datetime(2025, 9, 27, 19, 6, 43, 250000, tzinfo=UTC), '2025/09/27-19:06:43', '', '',
             'log_restart(system): session 0x1', 9)])
        self.assertEqual(counts, {'DBUG lines, not reported': 1, 'lines with no time, not reported': 8})

    def test_identity_pairs_take_the_time_and_firmware_before_them(self):
        pairs = skybellDoorbell.identity_pairs(SYSTEM)
        self.assertEqual([p[0] for p in pairs], [None, datetime(2025, 9, 27, 19, 6, 40, 500000, tzinfo=UTC),
                                                 datetime(2025, 9, 27, 19, 6, 43, 250000, tzinfo=UTC),
                                                 datetime(2025, 9, 27, 19, 6, 43, 250000, tzinfo=UTC)])
        self.assertEqual(pairs[1][1:], ('aaaa', '00000000-0000-4000-8000-000000000001', '123',
                                        '02:00:00:00:00:01', '192.0.2.5',
                                        'v1.0.0 [Sep 27 2025/19:00:00] -- rootfs-A[version.1]'))
        self.assertEqual(pairs[0][-1], '')


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))
    return path


class ArtifactTest(unittest.TestCase):
    def logs_tree(self, root, reboot_text):
        files = [write(os.path.join(root, 'vol', 'logs', 'system', '0'), SYSTEM),
                 write(os.path.join(root, 'vol', 'logs', 'debug', '1'),
                       '2025/09/27-19:07:00[1759000020.0] ISSUE-do_system().166: done\n'),
                 write(os.path.join(root, 'vol', 'logs', 'debug', 'debug'), b'log-config-000\x00'),
                 write(os.path.join(root, 'vol', 'logs', 'reboot.txt'), reboot_text)]
        files.append(write(os.path.join(root, 'other', 'logs', 'system', '0'),
                           '2025/09/27-19:06:41[1759000001.0] ALERT-x().1: not a doorbell\n'))
        return files

    def test_device_log_reads_only_a_logs_folder_that_names_skybell(self):
        with tempfile.TemporaryDirectory() as root:
            files = self.logs_tree(root, '2025/09/27-19:06:39 STARTING skybell_init\n')
            with mock.patch.object(skybellDoorbell, 'logfunc'):
                headers, rows, source = skybellDoorbell.skybellDoorbellLog.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([(r[5], r[6], r[-1]) for r in rows],
                         [('debug', 1, os.path.join('vol', 'logs', 'debug', '1'))]
                         + [('system', 0, os.path.join('vol', 'logs', 'system', '0'))] * 3)
        self.assertEqual(len(source.split('\n')), 2)

    def test_identity_counts_every_pair_and_keeps_a_timeless_one(self):
        with tempfile.TemporaryDirectory() as root:
            files = self.logs_tree(root, '2025/09/27-19:06:39 STARTING skybell_init\n')
            headers, rows, _source = skybellDoorbell.skybellDoorbellIdentity.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([(r[0], r[1], r[6], r[7], r[8]) for r in rows], [
            (datetime(2025, 9, 27, 19, 6, 40, 500000, tzinfo=UTC), datetime(2025, 9, 27, 19, 6, 40, 500000, tzinfo=UTC),
             '192.0.2.5', 'v1.0.0 [Sep 27 2025/19:00:00] -- rootfs-A[version.1]', 1),
            (datetime(2025, 9, 27, 19, 6, 43, 250000, tzinfo=UTC), datetime(2025, 9, 27, 19, 6, 43, 250000, tzinfo=UTC),
             '192.0.2.6', 'v1.0.0 [Sep 27 2025/19:00:00] -- rootfs-A[version.1]', 2),
            ('', '', '192.0.2.5', '', 1)])

    def test_restarts_need_the_word_skybell(self):
        with tempfile.TemporaryDirectory() as root:
            good = write(os.path.join(root, 'a', 'logs', 'reboot.txt'),
                         '1970/01/01-00:00:08 STARTING skybell_init\n\n2025/09/27-19:06:39 Time changed from '
                         '[2020-02-14T14:42:00.000Z]\n')
            other = write(os.path.join(root, 'b', 'logs', 'restart.txt'), '2025/09/27-19:06:39 main()\n')
            with mock.patch.object(skybellDoorbell, 'logfunc') as log:
                headers, rows, _source = skybellDoorbell.skybellDoorbellRestarts.__wrapped__(
                    FakeContext([good, other], root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [('1970/01/01-00:00:08', 'STARTING skybell_init', 1,
                                 os.path.join('a', 'logs', 'reboot.txt')),
                                ('2025/09/27-19:06:39', 'Time changed from [2020-02-14T14:42:00.000Z]', 3,
                                 os.path.join('a', 'logs', 'reboot.txt'))])
        self.assertEqual(log.call_args.args[0], 'Skybell Doorbell Restarts: 1 files without the word skybell, not read')

    def test_settings_rows_carry_the_crc_state_and_differing_copies(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, 'vol', 'ubi')
            main = json.dumps({'do_not_disturb': False, 'motion_policy': 'call'}).encode()
            system = json.dumps({'ota_uri': 'https://ota.example.skybell.test/', 'debug_level': 2}).encode()
            files = [write(os.path.join(folder, 'settings.json'), main),
                     write(os.path.join(folder, 'settings.crc'), struct.pack('<I', zlib.crc32(main))),
                     write(os.path.join(folder, 'system_settings.json'), system),
                     write(os.path.join(folder, 'system_settings.crc'), b'\x00\x00\x00\x00'),
                     write(os.path.join(folder, 'backup.json'), json.dumps({'do_not_disturb': True,
                                                                            'motion_policy': 'call'}).encode()),
                     write(os.path.join(folder, 'revert', 'settings.json'), main),
                     write(os.path.join(folder, 'revert', 'system_settings.json'), system),
                     write(os.path.join(root, 'plain', 'system_settings.json'), b'{"ota_uri": "https://x.test/"}')]
            with mock.patch.object(skybellDoorbell, 'logfunc') as log:
                headers, rows, _source = skybellDoorbell.skybellDoorbellSettings.__wrapped__(FakeContext(files, root))
        rel = lambda *p: os.path.join('vol', 'ubi', *p)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (rel('settings.json'), 'do_not_disturb', 'false', 'matches'),
            (rel('settings.json'), 'motion_policy', 'call', 'matches'),
            (rel('backup.json'), 'do_not_disturb', 'true', 'no .crc file'),
            (rel('system_settings.json'), 'ota_uri', 'https://ota.example.skybell.test/', 'differs'),
            (rel('system_settings.json'), 'debug_level', '2', 'differs')])
        self.assertEqual(log.call_args.args[0], 'Skybell Doorbell Settings: 1 folders whose system_settings.json names '
                                                'no skybell server, not read, 1 settings files that could not be read')


if __name__ == '__main__':
    unittest.main()
