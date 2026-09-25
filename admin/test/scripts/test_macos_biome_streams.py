"""Pin the field mappings of the added Biome stream processors in macosBiome.py.

Each processor is driven with synthetic protobuf records (stream_records is stubbed),
so the test checks the field numbers and the two timestamp conversions without needing a
real Biome stream. Every value here is authored for the test.
"""
import datetime
import pathlib
import struct
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosBiome  # pylint: disable=wrong-import-position


def _varint(value):
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _ld(number, data):
    return _varint((number << 3) | 2) + _varint(len(data)) + data


def _vi(number, value):
    return _varint((number << 3) | 0) + _varint(value)


def _f64(number, value):
    return _varint((number << 3) | 1) + struct.pack('<d', value)


class _Record:
    def __init__(self, data):
        self.time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
        self.data = data
        self.origin = 'Local'
        self.source = 'Users/tester/Library/Biome/streams/restricted/X/local/1'
        self.offset = 8
        self.user = 'tester'


def _run(processor, data):
    record = _Record(data)
    with mock.patch.object(macosBiome, 'stream_records', return_value=([record], [record.source])):
        headers, rows, _source = processor.__wrapped__(object())
    names = [h[0] if isinstance(h, tuple) else h for h in headers]
    return dict(zip(names, rows[0]))


UNIX_2025 = datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone.utc)
MAC_2025 = datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone.utc)


class BiomeStreamMappingTest(unittest.TestCase):

    def test_interaction_history_fields(self):
        unix = UNIX_2025.timestamp()
        meta = _ld(1, _f64(8, unix) + _ld(4, b'com.apple.news') + _ld(2, b'INIntent')
                   + _ld(1, b'guid-1') + _ld(13, b'iguid-1'))
        row = _run(macosBiome.macosBiomeSiriInteractionHistory, meta)
        self.assertEqual(row['Interaction Time (UTC)'], UNIX_2025)
        self.assertEqual(row['Bundle ID'], 'com.apple.news')
        self.assertEqual(row['Intent Class (as stored)'], 'INIntent')
        self.assertEqual(row['GUID (as stored)'], 'guid-1')
        self.assertEqual(row['Interaction GUID (as stored)'], 'iguid-1')

    def test_message_history_fields_and_participants(self):
        unix = UNIX_2025.timestamp()
        inner = (_f64(8, unix) + _vi(6, 1) + _ld(4, b'com.apple.MobileSMS')
                 + _ld(2, b'INSendMessageIntent') + _ld(12, b'SMS;-;123') + _ld(13, b'mguid'))
        item = _ld(1, b'sender') + _ld(2, _ld(1, b'Alice'))
        row = _run(macosBiome.macosBiomeSiriMessageHistory, _ld(1, inner) + _ld(2, item))
        self.assertEqual(row['Message Time (UTC)'], UNIX_2025)
        self.assertEqual(row['Direction (as stored)'], '1')
        self.assertEqual(row['Bundle ID'], 'com.apple.MobileSMS')
        self.assertEqual(row['Chat ID (as stored)'], 'SMS;-;123')
        self.assertEqual(row['Message GUID (as stored)'], 'mguid')
        self.assertEqual(row['Participants (as stored)'], 'sender: Alice')

    def test_dk_wifi_fields_and_2001_epoch(self):
        seconds_2001 = (MAC_2025 - datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)
                        ).total_seconds()
        data = (_f64(2, seconds_2001) + _ld(1, _ld(1, b'/wifi/connection'))
                + _ld(4, _ld(3, b'router-mac')) + _ld(5, b'wifi-guid'))
        row = _run(macosBiome.macosBiomeDKWifi, data)
        self.assertEqual(row['Event Time (UTC)'], MAC_2025)
        self.assertEqual(row['Event (as stored)'], '/wifi/connection')
        self.assertEqual(row['Device (as stored)'], 'router-mac')
        self.assertEqual(row['GUID (as stored)'], 'wifi-guid')

    def test_screentime_app_usage_fields(self):
        """ScreenTime.AppUsage: Bundle ID is field 3, Event is field 1."""
        data = _vi(1, 1) + _ld(3, b'com.google.Chrome')
        row = _run(macosBiome.macosBiomeScreenTimeAppUsage, data)
        self.assertEqual(row['Bundle ID'], 'com.google.Chrome')
        self.assertEqual(row['Event (as stored)'], '1')
        self.assertEqual(row['Record Time (UTC)'],
                         datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))

    def test_unreadable_timestamp_is_blank(self):
        # field 8 present but not eight bytes: no crash, blank time.
        meta = _ld(1, _vi(8, 5) + _ld(4, b'com.apple.news'))
        row = _run(macosBiome.macosBiomeSiriInteractionHistory, meta)
        self.assertEqual(row['Interaction Time (UTC)'], '')
        self.assertEqual(row['Bundle ID'], 'com.apple.news')


if __name__ == '__main__':
    unittest.main()
