"""Pin the SRUM WPN Notifications and Energy Usage artifacts (scripts/artifacts/windowsSrum.py).

The table rows are handed to each artifact's row builder in the shape the ESE reader returns them; reading
SRUDB.dat itself is covered by test_ese_rows.py. The values are made up.
"""
import datetime
import pathlib
import struct
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsSrum as srum
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
SOURCE = '/staged/Windows/System32/sru/SRUDB.dat'
IDMAP = {7: 'Contoso.App_1.0_x64__abc', 9: 'S-1-5-21-1-2-3-1001'}


def ole(moment):
    """A UTC time as the ESE reader returns a SRUM TimeStamp: the float64 day count as its raw integer."""
    days = (moment - datetime.datetime(1899, 12, 30, tzinfo=UTC)) / datetime.timedelta(days=1)
    return struct.unpack('<Q', struct.pack('<d', days))[0]


def filetime(moment):
    return int((moment - datetime.datetime(1601, 1, 1, tzinfo=UTC)) / datetime.timedelta(microseconds=1)) * 10


STAMP = datetime.datetime(2024, 3, 1, 12, 0, tzinfo=UTC)
EVENT = datetime.datetime(2024, 3, 1, 11, 30, 15, tzinfo=UTC)


class Providers(unittest.TestCase):
    def run_artifact(self, function, table_rows):
        """Run an artifact with its provider table replaced by table_rows; returns (result, guid asked for)."""
        asked = []

        def read_table(source, guid, row_builder, label, relative_source):  # pylint: disable=unused-argument
            asked.append(guid)
            return [row_builder(row, IDMAP) for row in table_rows]

        context = mock.Mock()
        context.get_files_found.return_value = [SOURCE, '/staged/other.txt']
        context.get_relative_path.side_effect = lambda p: p.replace('/staged/', '')
        with mock.patch.object(srum, '_read_table', read_table), \
             mock.patch.object(srum, 'impacket_ese', object()):
            result = function.__wrapped__(context)
        return result, asked

    def test_wpn_notifications(self):
        rows = [{'TimeStamp': ole(STAMP), 'AppId': 7, 'UserId': 9, 'NotificationType': 128,
                 'PayloadSize': 4261, 'NetworkType': 0},
                {'TimeStamp': ole(STAMP), 'AppId': 55, 'UserId': 56, 'NotificationType': None,
                 'PayloadSize': None, 'NetworkType': None}]
        (headers, data, located), asked = self.run_artifact(srum.srumWpnNotifications, rows)
        self.assertEqual(asked, ['{D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}'])
        self.assertEqual(headers, (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID', 'Notification Type',
                                   'Payload Size', 'Network Type', 'Source File'))
        rel = 'Windows/System32/sru/SRUDB.dat'
        self.assertEqual(data, [(STAMP, 'Contoso.App_1.0_x64__abc', 'S-1-5-21-1-2-3-1001', 128, 4261, 0, rel),
                                (STAMP, '', '', '', '', '', rel)])   # ids absent from the map, no values
        self.assertEqual(located, SOURCE)

    def test_energy_usage(self):
        big = 17640505652890480657   # larger than a signed 64-bit integer holds
        rows = [{'TimeStamp': ole(STAMP), 'AppId': 1, 'UserId': 2, 'EventTimestamp': filetime(EVENT),
                 'StateTransition': 771, 'DesignedCapacity': 62160, 'FullChargedCapacity': 52259,
                 'ChargeLevel': 50760, 'CycleCount': 3, 'ConfigurationHash': big,
                 'BatteryCount': 1, 'BatteryChargeLimited': 0},
                {'TimeStamp': ole(STAMP), 'EventTimestamp': 0, 'StateTransition': 3, 'DesignedCapacity': 1,
                 'FullChargedCapacity': 2, 'ChargeLevel': 4, 'CycleCount': 0, 'ConfigurationHash': None}]
        (headers, data, located), asked = self.run_artifact(srum.srumEnergyUsage, rows)
        self.assertEqual(asked, ['{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}'])
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), ('Timestamp (UTC)', 'datetime'),
                                   'State Transition', 'Charge Level', 'Full Charged Capacity', 'Designed Capacity',
                                   'Cycle Count', 'Battery Count', 'Battery Charge Limited', 'Configuration Hash',
                                   'Source File'))
        rel = 'Windows/System32/sru/SRUDB.dat'
        self.assertEqual(data, [
            (EVENT, STAMP, 771, 50760, 52259, 62160, 3, 1, 0, str(big), rel),
            ('', STAMP, 3, 4, 2, 1, 0, '', '', '', rel)])   # no event time, an older file with no battery columns
        self.assertIsInstance(data[0][9], str)
        self.assertEqual(located, SOURCE)

    def test_sdp_tables(self):
        big = 4649015153352099455
        cases = [
            (srum.srumSdpCpu, '{DC3D3B50-BB90-5066-FA4E-A5F90DD8B677}',
             {'ProcessorTime': 92}, ('Processor Time (as stored)',), (92,)),
            (srum.srumSdpPhysicalDisk, '{841A7317-3805-518B-C2EA-AD224CB4AF84}',
             {'SizeInBytes': 53687091200}, ('Size In Bytes (as stored)',), ('53687091200',)),
            (srum.srumSdpVolume, '{17F4D97B-F26A-5E79-3A82-90040A47D13D}',
             {'Total': 104853504, 'Used': 34467840}, ('Total (as stored)', 'Used (as stored)'),
             ('104853504', '34467840')),
            (srum.srumSdpNetwork, '{EEE2F477-0659-5C47-EF03-6D6BEFD441B3}',
             {'BytesInBound': 0, 'BytesOutBound': big, 'BytesTotal': None},
             ('Bytes In Bound (as stored)', 'Bytes Out Bound (as stored)', 'Bytes Total (as stored)'),
             ('0', str(big), '')),
        ]
        rel = 'Windows/System32/sru/SRUDB.dat'
        for function, guid, values, value_headers, expected in cases:
            with self.subTest(function.__name__):
                row = {'TimeStamp': ole(STAMP), 'AppId': 7, 'UserId': 2, **values}
                (headers, data, located), asked = self.run_artifact(function, [row])
                self.assertEqual(asked, [guid])
                self.assertEqual(headers, (('Timestamp (UTC)', 'datetime'), 'AppId Entry') + value_headers
                                 + ('Source File',))
                self.assertEqual(data, [(STAMP, 'Contoso.App_1.0_x64__abc') + expected + (rel,)])
                self.assertEqual(located, SOURCE)

    def test_the_logs_beside_srudb_are_not_read_as_databases(self):
        context = mock.Mock()
        context.get_files_found.return_value = [SOURCE, '/staged/Windows/System32/sru/SRU0102A.log',
                                                '/staged/Windows/System32/sru/SRU.log']
        self.assertEqual(srum._srudb_sources(context), [SOURCE])  # pylint: disable=protected-access

    def test_no_rows_names_no_file(self):
        (_, data, located), _ = self.run_artifact(srum.srumEnergyUsage, [])
        self.assertEqual((data, located), ([], ''))

    def test_reader_missing(self):
        context = mock.Mock()
        context.get_files_found.return_value = [SOURCE]
        with mock.patch.object(srum, 'impacket_ese', None), mock.patch.object(srum, 'logfunc') as log:
            _, data, located = srum.srumWpnNotifications.__wrapped__(context)
        self.assertEqual((data, located), ([], ''))
        self.assertEqual(log.call_count, 1)


class Replay(unittest.TestCase):
    """srum._open: replayed once per file, read as stored when the replay is refused."""

    def setUp(self):
        srum._REPLAYED.clear()  # pylint: disable=protected-access
        self.stat = mock.Mock(st_size=10, st_mtime_ns=20)

    def open_twice(self, replay_result):
        logged = []
        with mock.patch.object(srum.os, 'stat', return_value=self.stat), \
             mock.patch.object(srum.ese_recovery, 'replayed_database', return_value=replay_result) as replay, \
             mock.patch.object(srum.ese_rows, 'ESEDatabase') as database, \
             mock.patch.object(srum, 'logfunc', side_effect=logged.append):
            srum._open(SOURCE, 'SRUM A', 'sru/SRUDB.dat')  # pylint: disable=protected-access
            srum._open(SOURCE, 'SRUM B', 'sru/SRUDB.dat')  # pylint: disable=protected-access
        return replay, database, logged

    def test_a_refused_replay_reads_the_file_as_stored_and_says_why(self):
        replay, database, logged = self.open_twice((None, 'not replayed: a SetExternalHeader record'))
        self.assertEqual(replay.call_count, 1)
        self.assertEqual(database.call_args_list, [mock.call(SOURCE), mock.call(SOURCE)])
        self.assertEqual(logged, ['SRUM A: sru/SRUDB.dat, not replayed: a SetExternalHeader record; read as stored',
                                  'SRUM B: sru/SRUDB.dat, not replayed: a SetExternalHeader record; read as stored'])

    def test_a_replayed_file_is_read_from_the_replayed_bytes(self):
        replay, database, logged = self.open_twice((b'replayed', 'replayed 3 change(s) from SRU.log'))
        self.assertEqual(replay.call_count, 1)
        self.assertEqual(database.call_args_list, [mock.call(SOURCE, data=b'replayed')] * 2)
        self.assertEqual(logged[0], 'SRUM A: sru/SRUDB.dat, replayed 3 change(s) from SRU.log')

    def test_a_clean_file_is_read_as_stored_without_a_log_line(self):
        _replay, database, logged = self.open_twice((b'as stored', 'not replayed: the header records clean shutdown'))
        self.assertEqual(database.call_args_list, [mock.call(SOURCE), mock.call(SOURCE)])
        self.assertEqual(logged, [])


if __name__ == '__main__':
    unittest.main()
