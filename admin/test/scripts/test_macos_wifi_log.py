"""macOS Wi-Fi log lines from private/var/log/wifi.log, its rotated copies and wifi-<time>.log files."""
# pylint: disable=protected-access

import bz2
import fnmatch
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts.artifacts import macosWifiLog

LOG = 'private/var/log'
DATA = 'System/Volumes/Data/private/var/log'

# Synthetic lines in the two header forms seen on real images, with made-up values.
BRACKET = 'Wed Jan  7 10:00:00.100 [airport]/321 @[5000.250000] (airportProcessCommand.m:{}) {}'
ANGLE = 'Thu Jan  8 11:00:00.{:03d} {}<airport[654]> {}'


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class WifiLogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, lines, compress=False):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = ('\n'.join(lines) + '\n').encode('utf-8')
        with open(path, 'wb') as handle:
            handle.write(bz2.compress(data) if compress else data)
        return path

    def _run(self, function, files):
        with mock.patch.object(macosWifiLog, 'logfunc', self.logs.append):
            return getattr(macosWifiLog, function).__wrapped__(FakeContext(self.root, files))

    def _both(self, files):
        return self._run('macosWifiLogEvents', files), self._run('macosWifiLogEntries', files)

    def test_bracket_form_events_and_other_entries(self):
        path = self._write(f'{LOG}/wifi.log', [
            'Jan  7 00:30:00 ExampleMac newsyslog[100]: logfile turned over',
            BRACKET.format(1715, 'Processed events, count[  1], @[1.0], took 0.000034'),
            BRACKET.format(4687, "caps = , connection[0x1] token[0x2] capabilties[0x0], "
                                 "description:'DarkWake:cpu disk net ', lastSleepType[0x5]/'Standby'"),
            BRACKET.format(3826, 'Acknowledging sleep event, connection[0x1] token[0x2]'),
            BRACKET.format(1377, 'driver unavailable (reason=0x1, subreason=0x0, flags=0x0), node:x=1'),
            BRACKET.format(1377, 'driver available (reason=0x1, subreason=0x0, flags=0x0), node:x=1'),
            BRACKET.format(501, 'IPV4 State change for en0'),
            BRACKET.format(513, 'IP Address: 192.0.2.10'),
            BRACKET.format(562, 'Router MAC Address: 02:00:00:00:00:01'),
            BRACKET.format(596, 'ARP offload settings ({'),
            'Wed Jan  7 10:00:00.106     "ROUTER_IP_ADDR" = {length = 4, bytes = 0x00000000};',
            'Wed Jan  7 10:00:00.100 })',
            'Tue Jan  6 09:00:00.200 Usb Host Notification hostNotificationUSBDeviceRemoved Example Drive '
            'seqNum 3 Total 1',
        ])
        (headers, events, source), (other_headers, other, _) = self._both([path])
        self.assertEqual(headers, ('Time (as written)', 'Event (as written)', 'Interface', 'SSID', 'BSSID',
                                   'Network ID (as stored)', 'Detail', 'Message', 'Process', 'PID',
                                   'Category (as written)', 'File and Line (as written)',
                                   '@[ ] Value (as stored)', 'Source File', 'Line'))
        where = f'{LOG}/wifi.log'
        self.assertEqual([row[:7] for row in events], [
            ('Wed Jan  7 10:00:00.100', 'caps', '', '', '', '', 'DarkWake:cpu disk net'),
            ('Wed Jan  7 10:00:00.100', 'Acknowledging sleep event', '', '', '', '', ''),
            ('Wed Jan  7 10:00:00.100', 'driver unavailable', '', '', '', '',
             'reason=0x1, subreason=0x0, flags=0x0'),
            ('Wed Jan  7 10:00:00.100', 'driver available', '', '', '', '',
             'reason=0x1, subreason=0x0, flags=0x0'),
            ('Wed Jan  7 10:00:00.100', 'IPV4 State change', 'en0', '', '', '', ''),
            ('Wed Jan  7 10:00:00.100', 'IP Address', '', '', '', '', '192.0.2.10'),
            ('Wed Jan  7 10:00:00.100', 'Router MAC Address', '', '', '', '', '02:00:00:00:00:01'),
            ('Tue Jan  6 09:00:00.200', 'hostNotificationUSBDeviceRemoved', '', '', '', '', 'Example Drive'),
        ])
        self.assertEqual(events[0][8:], ('airport', '321', '', 'airportProcessCommand.m:4687',
                                         '5000.250000', where, 3))
        self.assertEqual(source, path)
        self.assertEqual(other_headers, ('Time (as written)', 'Process', 'PID', 'Category (as written)',
                                         'File and Line (as written)', '@[ ] Value (as stored)', 'Host',
                                         'Message', 'Source File', 'Line'))
        self.assertEqual(other[0], ('Jan  7 00:30:00', 'newsyslog', '100', '', '', '', 'ExampleMac',
                                    'logfile turned over', where, 1))
        self.assertEqual(other[1][7], 'Processed events, count[  1], @[1.0], took 0.000034')
        # A continuation keeps only its text when its time is the entry's, the whole line when not.
        self.assertEqual(other[2][7], 'ARP offload settings ({\n'
                                      'Wed Jan  7 10:00:00.106     "ROUTER_IP_ADDR" = {length = 4, '
                                      'bytes = 0x00000000};\n})')
        self.assertEqual(len(events) + len(other), 11)

    def test_angle_form_events(self):
        path = self._write(f'{LOG}/wifi.log', [
            ANGLE.format(1, 'Info: ', 'psCallback: powerSource = AC Power'),
            ANGLE.format(2, '', 'airportdProcessDLILEvent: en1 attached (up)'),
            ANGLE.format(3, 'AutoJoin: ', 'AUTO-JOIN STARTED for interface en1 (Power On)'),
            ANGLE.format(4, 'AutoJoin: ', "Adding network ['ExampleNet' (wifi.ssid.4578616d706c654e6574) - "
                                          "WPA2/WPA3 Personal]"),
            ANGLE.format(5, 'AutoJoin: ', "__filteredScanResultsForAutoJoin: ['(null)' - 2:0:0:a:b:c] is not "
                                          "Passpoint and SSID==nil, remove from join candidates"),
            ANGLE.format(6, 'AutoJoin: ', "AUTO-JOIN COMPLETED for interface en1, took 5.7 seconds, "
                                          "returned result 'failure', error [NO ERROR]"),
            ANGLE.format(7, 'Driver Event: ', '_bsd_80211_event_callback: SCAN_CACHE_UPDATED (en1)'),
            ANGLE.format(8, 'Driver Event: ', '_bsd_80211_event_callback: POWER_CHANGED (en1)'),
            ANGLE.format(9, 'Info: ', 'REMEMBER WIFI NETWORK (id=wifi.ssid.4578616d706c654e6574 event=3) '
                                      'request received from pid 42 (WiFiAgent)'),
            ANGLE.format(10, 'AutoJoin: ', 'user: exampleuser'),
            ANGLE.format(11, 'Assoc: ', '<en1> REACHABILITY [reachable=yes, ipv4Primary=no]'),
            'Thu Jan  8 11:00:00.012 Info: <WiFiAge[655]> WIFICLOUDSYNC SomeFunction: CLOUD --> LOCAL: '
            '<ExampleNet> more recently added on cloud KVS, update local KVS',
            ANGLE.format(13, 'AutoJoin: ', 'MULTI-SSID AUTO-JOIN on interface en1, optimized channel list {('),
            'Thu Jan  8 11:00:00.013     Channel: 149',
            'Thu Jan  8 11:00:00.014 Weight: 1.0000',
            'Thu Jan  8 11:00:00.014 )}',
        ])
        (_h, events, _s), (_oh, other, _os) = self._both([path])
        self.assertEqual([row[1:7] for row in events], [
            ('powerSource', '', '', '', '', 'AC Power'),
            ('airportdProcessDLILEvent', 'en1', '', '', '', 'attached (up)'),
            ('AUTO-JOIN STARTED', 'en1', '', '', '', '(Power On)'),
            ('Adding network', '', 'ExampleNet', '', 'wifi.ssid.4578616d706c654e6574', 'WPA2/WPA3 Personal'),
            ('__filteredScanResultsForAutoJoin', '', '(null)', '2:0:0:a:b:c', '',
             'is not Passpoint and SSID==nil, remove from join candidates'),
            ('AUTO-JOIN COMPLETED', 'en1', '', '', '', "took 5.7 seconds, returned result 'failure', error [NO ERROR]"),
            ('POWER_CHANGED', 'en1', '', '', '', ''),
            ('REMEMBER WIFI NETWORK', '', 'ExampleNet', '', 'wifi.ssid.4578616d706c654e6574',
             'event=3; request received from pid 42 (WiFiAgent)'),
            ('user', '', '', '', '', 'exampleuser'),
            ('REACHABILITY', 'en1', '', '', '', 'reachable=yes, ipv4Primary=no'),
            ('CLOUD --> LOCAL', '', 'ExampleNet', '', '', 'more recently added on cloud KVS, update local KVS'),
        ])
        self.assertEqual(events[0][8:11], ('airport', '654', 'Info'))
        self.assertEqual(events[-1][8:10], ('WiFiAge', '655'))
        self.assertEqual([row[7] for row in other], [
            '_bsd_80211_event_callback: SCAN_CACHE_UPDATED (en1)',
            'MULTI-SSID AUTO-JOIN on interface en1, optimized channel list {(\n'
            '    Channel: 149\nThu Jan  8 11:00:00.014 Weight: 1.0000\n'
            'Thu Jan  8 11:00:00.014 )}',
        ])

    def test_doubled_time_untimed_unmatched_and_blank_lines_are_kept_and_counted(self):
        path = self._write(f'{LOG}/wifi.log', [
            'Tue Jan  6 09:00:00.200 Tue Jan  6 09:00:00.200 [airport]/321 @[4000.500000] '
            '(configdIODriverInterface.m:1377) driver unavailable (reason=0x1, subreason=0x0, flags=0x0)',
            '[airport]/321 @[4000.400000] (airportdMain.m:1730) Health check alive, count[1]',
            '',
            'something of no known form',
        ])
        (_h, events, _s), (_oh, other, _os) = self._both([path])
        self.assertEqual([(row[0], row[1], row[14]) for row in events],
                         [('Tue Jan  6 09:00:00.200', 'driver unavailable', 1)])
        self.assertEqual([(row[0], row[1], row[7], row[9]) for row in other], [
            ('Tue Jan  6 09:00:00.200', '', '', 1),
            ('', 'airport', 'Health check alive, count[1]', 2),
            ('', '', 'something of no known form', 4),
        ])
        self.assertIn('Wi-Fi Log Other Entries: 1 file(s) read (0 could not be read), 4 lines: 1 blank, 0 joined '
                      'to the entry above, 1 holding two times, 1 with no time, 1 of no known line form '
                      '(reported with only a message)', self.logs)

    def test_rotated_copies_are_read_oldest_first_and_bunzipped(self):
        live = self._write(f'{LOG}/wifi.log', [ANGLE.format(3, '', 'no user logged in')])
        newest = self._write(f'{LOG}/wifi.log.0.bz2', [ANGLE.format(2, '', 'no user logged in')], compress=True)
        oldest = self._write(f'{LOG}/wifi.log.10.bz2', [ANGLE.format(0, '', 'no user logged in')],
                             compress=True)
        middle = self._write(f'{LOG}/wifi.log.2.bz2', [ANGLE.format(1, '', 'no user logged in')], compress=True)
        dump = self._write(f'{LOG}/wifi-01-08-2026__10_00_00.500.log',
                           [ANGLE.format(4, 'AutoJoin: ', 'user: exampleuser')])
        ignored = self._write(f'{LOG}/wifi.log.notes', [ANGLE.format(5, '', 'no user logged in')])
        (_h, events, source), _other = self._both([live, newest, oldest, middle, dump, ignored])
        self.assertEqual([row[0][-3:] for row in events], ['000', '001', '002', '004', '003'])
        self.assertEqual(source.split('\n'), [oldest, middle, newest, dump, live])

    def test_two_volume_views_of_a_rotated_log_are_read_as_one_log(self):
        # The Data view was captured after a rotation: its wifi.log.1 is the root view's wifi.log.0
        # and its wifi.log.0 holds the root view's wifi.log and more.
        day1 = [ANGLE.format(1, '', 'no user logged in')]
        day2 = [ANGLE.format(2, '', 'no user logged in')]
        day3 = [ANGLE.format(3, '', 'no user logged in')]
        files = [
            self._write(f'{LOG}/wifi.log.1.bz2', ['Thu Jan  8 11:00:00.000 old line'], compress=True),
            self._write(f'{LOG}/wifi.log.0.bz2', day1, compress=True),
            self._write(f'{LOG}/wifi.log', day2),
            self._write(f'{DATA}/wifi.log.1.bz2', day1, compress=True),
            self._write(f'{DATA}/wifi.log.0.bz2', day2 + day3, compress=True),
            self._write(f'{DATA}/wifi.log', [ANGLE.format(4, '', 'no user logged in')]),
        ]
        (_h, events, _s), (_oh, other, _os) = self._both(files)
        self.assertEqual([row[0][-3:] for row in events], ['001', '002', '003', '004'])
        # The Data view holds more entries, so its copies are the ones reported.
        self.assertEqual([row[13] for row in events], [f'{DATA}/wifi.log.1.bz2', f'{DATA}/wifi.log.0.bz2',
                                                       f'{DATA}/wifi.log.0.bz2', f'{DATA}/wifi.log'])
        self.assertEqual([row[7] for row in other], ['old line'])
        self.assertIn('Wi-Fi Log Events: 2 entries held by more than one volume view of one log folder '
                      'reported once', self.logs)

    def test_a_record_one_file_holds_twice_stays_twice(self):
        line = ANGLE.format(1, '', 'no user logged in')
        files = [self._write(f'{LOG}/wifi.log', [line, line]), self._write(f'{DATA}/wifi.log', [line, line])]
        (_h, events, _s), _other = self._both(files)
        self.assertEqual([row[14] for row in events], [1, 2])

    def test_unreadable_bzip2_is_logged_and_skipped(self):
        bad = os.path.join(self.root, LOG, 'wifi.log.0.bz2')
        os.makedirs(os.path.dirname(bad), exist_ok=True)
        with open(bad, 'wb') as handle:
            handle.write(b'BZh9 not really bzip2')
        (_h, events, source), _other = self._both([bad])
        self.assertEqual((events, source), ([], ''))
        self.assertIn(f'Wi-Fi Log Events: could not read {LOG}/wifi.log.0.bz2', self.logs)

    def test_paths_match_the_names_read(self):
        paths = macosWifiLog.__artifacts_v2__['macosWifiLogEvents']['paths']
        self.assertEqual(paths, macosWifiLog.__artifacts_v2__['macosWifiLogEntries']['paths'])
        for name in ('wifi.log', 'wifi.log.0.bz2', 'wifi.log.10.bz2', 'wifi-01-08-2026__10_00_00.500.log'):
            relative = f'root/{LOG}/{name}'
            self.assertEqual(sum(fnmatch.fnmatchcase(relative, pattern) for pattern in paths), 1, name)
            self.assertTrue(macosWifiLog._NAME.fullmatch(name), name)
        self.assertFalse(macosWifiLog._NAME.fullmatch('wifi.log.notes'))


if __name__ == '__main__':
    unittest.main()
