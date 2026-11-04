"""Tests for scripts/etl.py and the Wifi.etl artifacts, on the synthetic file etl_fixture.py writes.

The expected times and values are what Get-WinEvent (Windows 11 build 26200) returned for that same file.
"""

import os
import struct
import sys
import unittest
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import etl_fixture  # noqa: E402  pylint: disable=wrong-import-position
from scripts import etl  # noqa: E402  pylint: disable=wrong-import-position
from scripts.artifacts import windowsWifiEtl as wifi  # noqa: E402  pylint: disable=wrong-import-position

# Get-WinEvent on the fixture: time (UTC), provider, event ID, properties joined with ';'
WINDOWS = [
    ('2022-06-18T04:26:40.3804899Z', 'Microsoft-Windows-WLAN-AutoConfig', 20025, 'fixture-net-a;2;7;4;4294967216'),
    ('2022-06-18T04:26:40.3804953Z', 'Microsoft-Windows-WLAN-AutoConfig', 20025, ';5;6;4;4294967238'),
    ('2022-06-20T09:17:24.4217597Z', 'Microsoft-Windows-NWiFi', 10040,
     '18446603336526616184;11111111-2222-3333-4444-555555555555;2 0 94 16 32 48'),
    ('2022-06-20T09:17:24.4253557Z', 'Microsoft-Windows-NWiFi', 10041,
     '18446603336526616184;11111111-2222-3333-4444-555555555555;2 0 94 16 32 48;0'),
    ('2022-06-18T04:26:41.1953410Z', 'Microsoft-Windows-WLAN-AutoConfig', 8001,
     '11111111-2222-3333-4444-555555555555;Fixture Wireless Adapter;Automatic connection with a profile;'
     'fixture-net-a;fixture-net-a;Infrastructure;802.11ac;WPA2-Personal;AES;0;42;False'),
]
_EPOCH = datetime(1601, 1, 1)


def _text(filetime):
    us, rest = divmod(filetime, 10)
    moment = _EPOCH + timedelta(microseconds=us)
    return moment.strftime('%Y-%m-%dT%H:%M:%S.') + f'{moment.microsecond:06d}{rest}Z'


def _render(value):
    if isinstance(value, bytes):
        return ' '.join(str(byte) for byte in value)
    return str(value)


def _decoded(data):
    out = []
    for event in etl.EtlFile(data).events():
        template = wifi._TEMPLATES[(event.provider, event.event_id, event.version)]  # pylint: disable=protected-access
        values, left = etl.decode(event.data, template, event.pointer_size)
        out.append((_text(event.filetime), event.event_id, ';'.join(_render(v) for v in values.values()), left))
    return sorted(out)


class EtlReaderTest(unittest.TestCase):

    def setUp(self):
        self.data = etl_fixture.build()

    def test_matches_windows(self):
        self.assertEqual(_decoded(self.data), sorted((t, i, p, 0) for t, _, i, p in WINDOWS))

    def test_session_header_and_kinds(self):
        trace = etl.EtlFile(self.data)
        list(trace.events())
        self.assertEqual(trace.header['perf_freq'], etl_fixture.PERF_FREQ)
        self.assertEqual(trace.header['start_time'], etl_fixture.START_TIME)
        self.assertEqual(trace.header['clock_type'], etl.CLOCK_PERFORMANCE_COUNTER)
        self.assertEqual(trace.header['build'], 26200)
        self.assertEqual(trace.kinds, Counter({'event64': 5, 'system64': 1, 'wpp': 1}))
        self.assertEqual(trace.problems, Counter())

    def test_integer_scaling_would_disagree_with_windows(self):
        """Windows' times come from a truncated floating-point scale. Integer division gives other times on this
        fixture, so the time comparison can fail."""
        stamps = [etl_fixture.T0 + offset for offset, _ in etl_fixture.EVENTS_1 + etl_fixture.EVENTS_2
                  if offset != 2_500_001]              # the WPP record is not an event
        floor = {_text(etl_fixture.START_TIME + (s - etl_fixture.T0) * 10_000_000 // etl_fixture.PERF_FREQ)
                 for s in stamps}
        windows = {t for t, *_ in WINDOWS}
        self.assertEqual({_text(etl.EtlFile(self.data).filetime(s)) for s in stamps}, windows)
        self.assertNotEqual(floor, windows)

    def test_a_changed_byte_is_seen(self):
        data = bytearray(self.data)
        position = bytes(data).index('fixture-net-a'.encode('utf-16-le'))
        data[position] ^= 0x01
        self.assertNotEqual(_decoded(bytes(data)), sorted((t, i, p, 0) for t, _, i, p in WINDOWS))

    def test_not_an_etl_file(self):
        with self.assertRaises(etl.EtlError):
            etl.EtlFile(b'\x00' * 8192)

    def test_cut_short_and_unknown_records_are_counted(self):
        cut = etl.EtlFile(self.data[:6000])
        self.assertEqual(len(list(cut.events())), 3)
        self.assertEqual(cut.problems, Counter({'a last buffer cut short by the end of the file, not read': 1}))
        data = bytearray(self.data)
        second = etl_fixture.BUFFER + 0x48
        struct.pack_into('<I', data, second, 0xc0770000 | 0x40)
        odd = etl.EtlFile(bytes(data))
        self.assertEqual(len(list(odd.events())), 3)
        self.assertEqual(odd.problems, Counter({'records of header type 0x77, which ended their buffer': 1}))

    def test_decode_refuses_short_data(self):
        with self.assertRaises(ValueError):
            etl.decode(b'\x01\x00', (('Count', 'win:UInt32'),), 8)
        with self.assertRaises(ValueError):
            etl.decode('ab'.encode('utf-16-le'), (('Name', 'win:UnicodeString'),), 8)
        values, left = etl.decode(b'\x01\x00\x00\x00\xff', (('Flag', 'win:Boolean'),), 8)
        self.assertEqual((values, left), ({'Flag': True}, 1))


class WifiArtifactTest(unittest.TestCase):

    def test_events_for_each_artifact(self):
        problems = Counter()
        data = etl_fixture.build()
        visible = wifi.wifi_events(data, {(wifi._AUTOCONFIG, 20025)}, 'test', problems)  # pylint: disable=protected-access
        connections = wifi.wifi_events(data, set(wifi._CONNECTION_EVENTS), 'test', problems)  # pylint: disable=protected-access
        self.assertEqual(problems, Counter())
        self.assertEqual([v['Ssid'] for _, v in visible], ['fixture-net-a', ''])
        self.assertEqual(sorted(e.event_id for e, _ in connections), [8001, 10040, 10041])
        self.assertEqual(wifi._utc(visible[0][0].filetime),  # pylint: disable=protected-access
                         datetime(2022, 6, 18, 4, 26, 40, 380489, tzinfo=timezone.utc))
        self.assertEqual(wifi._mac(b'\x02\x00\x5e\x10\x20\x30'), '02:00:5E:10:20:30')  # pylint: disable=protected-access

    def test_a_version_without_a_template_is_counted(self):
        data = bytearray(etl_fixture.build())
        position = 0x48 + len(etl_fixture.logfile_header_record()) + 0x2a
        data[position] = 1                                  # the first 20025's EVENT_DESCRIPTOR Version
        problems = Counter()
        visible = wifi.wifi_events(bytes(data), {(wifi._AUTOCONFIG, 20025)}, 'test', problems)  # pylint: disable=protected-access
        self.assertEqual(len(visible), 1)
        self.assertEqual(problems, Counter({'test: events 20025 of version 1, which has no template here': 1}))


if __name__ == '__main__':
    unittest.main()
