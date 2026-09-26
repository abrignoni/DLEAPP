"""Pin the field mappings of the added Biome stream processors in macosBiome.py.

Each processor is driven with synthetic protobuf records (stream_records is stubbed),
so the test checks the field numbers and the two timestamp conversions without needing a
real Biome stream. Every value here is authored for the test.
"""
import datetime
import pathlib
import plistlib
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


def _interaction_archive(direction, status, start):
    """A binary NSKeyedArchiver plist holding one INInteraction, authored for the test."""
    seconds = (start - datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)).total_seconds()
    uid = plistlib.UID
    objects = [
        '$null',
        {'$class': uid(6), 'dateInterval': uid(2), 'direction': direction,
         'intentHandlingStatus': status, 'groupIdentifier': uid(4), 'identifier': uid(5),
         'intent': uid(0)},
        {'$class': uid(7), 'NS.startDate': uid(3), 'NS.endDate': uid(3), 'NS.duration': 0.0},
        {'$class': uid(8), 'NS.time': seconds},
        'group-1',
        'interaction-1',
        {'$classname': 'INInteraction', '$classes': ['INInteraction', 'NSObject']},
        {'$classname': 'NSDateInterval', '$classes': ['NSDateInterval', 'NSObject']},
        {'$classname': 'NSDate', '$classes': ['NSDate', 'NSObject']},
    ]
    archive = {'$version': 100000, '$archiver': 'NSKeyedArchiver', '$top': {'root': uid(1)},
               '$objects': objects}
    return plistlib.dumps(archive, fmt=plistlib.PlistFormat.FMT_BINARY)


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

    def test_bluetooth_use_case_fields(self):
        """Device.Wireless.BluetoothUseCase: field 1 and field 2 reported as stored."""
        data = _vi(1, 1) + _vi(2, 131090)
        row = _run(macosBiome.macosBiomeBluetoothUseCase, data)
        self.assertEqual(row['Field 1 (as stored)'], '1')
        self.assertEqual(row['Field 2 (as stored)'], '131090')
        self.assertEqual(row['Record Time (UTC)'],
                         datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))

    def test_app_intent_fields_and_interaction(self):
        """App.Intent: fields 2, 4 and 5, and the INInteraction archived in field 8."""
        data = (_ld(2, b'com.apple.MobileSMS') + _ld(4, b'INSendMessageIntent')
                + _ld(5, b'SendMessage') + _ld(8, _interaction_archive(2, 3, MAC_2025)))
        row = _run(macosBiome.macosBiomeAppIntent, data)
        self.assertEqual(row['Interval Start (UTC)'], MAC_2025)
        self.assertEqual(row['Bundle ID'], 'com.apple.MobileSMS')
        self.assertEqual(row['Intent Class (as stored)'], 'INSendMessageIntent')
        self.assertEqual(row['Action (as stored)'], 'SendMessage')
        self.assertEqual(row['Direction'], 'Incoming (2)')
        self.assertEqual(row['Handling Status'], 'Success (3)')
        self.assertEqual(row['Group ID (as stored)'], 'group-1')
        self.assertEqual(row['Interaction ID (as stored)'], 'interaction-1')

    def test_app_intent_number_outside_the_enum_is_shown_alone(self):
        """A stored number INInteraction.h does not name is reported as the number."""
        data = _ld(2, b'com.apple.news') + _ld(8, _interaction_archive(9, 42, MAC_2025))
        row = _run(macosBiome.macosBiomeAppIntent, data)
        self.assertEqual(row['Direction'], '9')
        self.assertEqual(row['Handling Status'], '42')

    def test_app_intent_without_field_8_keeps_the_row(self):
        """No keyed archive: the row is kept and the interaction columns are blank."""
        data = _ld(2, b'com.apple.news') + _ld(4, b'TodayIntent')
        row = _run(macosBiome.macosBiomeAppIntent, data)
        self.assertEqual(row['Bundle ID'], 'com.apple.news')
        self.assertEqual(row['Intent Class (as stored)'], 'TodayIntent')
        self.assertEqual(row['Interval Start (UTC)'], '')
        self.assertEqual(row['Direction'], '')
        self.assertEqual(row['Interaction ID (as stored)'], '')

    def test_unreadable_timestamp_is_blank(self):
        # field 8 present but not eight bytes: no crash, blank time.
        meta = _ld(1, _vi(8, 5) + _ld(4, b'com.apple.news'))
        row = _run(macosBiome.macosBiomeSiriInteractionHistory, meta)
        self.assertEqual(row['Interaction Time (UTC)'], '')
        self.assertEqual(row['Bundle ID'], 'com.apple.news')


if __name__ == '__main__':
    unittest.main()
