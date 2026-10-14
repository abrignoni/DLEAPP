"""Pin the User Access Logging - System Identity artifact (scripts/artifacts/windowsUserAccessLogging.py).

No ESE writer is available here, so the record conversion is tested on dicts shaped like the rows
scripts/ese_rows.TableRows gives for SYSTEM_IDENTITY, and the processor with the database read replaced. The
strings are made up. The numbers and timestamps are those of the first and third szechuan_dc01_server2012r2
records.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsUserAccessLogging as ual
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
PAD = '\0' * 12


def record(**changes):
    row = {
        'CreationTime': 132448316944240000,
        'PhysicalProcessorCount': 1, 'CoresPerPhysicalProcessor': 2, 'LogicalProcessorsPerPhysicalProcessor': 4,
        'MaximumMemory': 2147483648,
        'OSMajor': 6, 'OSMinor': 3, 'OSBuildNumber': 9600, 'OSPlatformId': 2,
        'ServicePackMajor': 0, 'ServicePackMinor': 0, 'OSSuiteMask': 272, 'OSProductType': 3,
        'OSCurrentTimeZone': 65116, 'OSDaylightInEffect': 255,
        'SystemManufacturer': 'Maker' + PAD, 'SystemProductName': 'Model' + PAD,
        'SystemSMBIOSUUID': '00000000-1111-2222-3333-444444444444\0', 'SystemSerialNumber': 'SN-1' + PAD,
        'SystemDNSHostName': 'HOST-A' + PAD, 'SystemDomainName': 'example.test' + PAD,
        'OSSerialNumber': '00000-00000-00000-AA000' + PAD, 'OSCountryCode': '1' + PAD,
        'OSLastBootUpTime': '20200917100320.485021-420' + PAD,
    }
    row.update(changes)
    return row


class Values(unittest.TestCase):
    def test_text(self):
        self.assertEqual(ual.text('abc\0\0\0'), 'abc')
        self.assertEqual(ual.text('abc\0junk'), 'abc')
        self.assertEqual(ual.text(b'abc\0'), 'abc')
        self.assertEqual(ual.text(None), '')
        self.assertEqual(ual.text(''), '')

    def test_cim_datetime(self):
        self.assertEqual(ual.cim_datetime_utc('20200917100320.485021-420'),
                         datetime.datetime(2020, 9, 17, 17, 3, 20, 485021, tzinfo=UTC))
        self.assertEqual(ual.cim_datetime_utc('20200917100320.485021+060'),
                         datetime.datetime(2020, 9, 17, 9, 3, 20, 485021, tzinfo=UTC))
        self.assertEqual(ual.cim_datetime_utc('20200917100320.000000+000'),
                         datetime.datetime(2020, 9, 17, 10, 3, 20, tzinfo=UTC))
        self.assertEqual(ual.cim_datetime_utc('20200101003000.000000+060'),
                         datetime.datetime(2019, 12, 31, 23, 30, tzinfo=UTC))

    def test_cim_datetime_not_converted(self):
        for value in ('', '20200917100320.485021-***', '20200917100320.485021', '20201317100320.000000+000',
                      '2020091710032.485021-420', 'x20200917100320.485021-420', '20200917100320.485021-4200'):
            self.assertEqual(ual.cim_datetime_utc(value), '', value)

    def test_signed_minutes(self):
        self.assertEqual(ual.signed_minutes(65116), -420)
        self.assertEqual(ual.signed_minutes(0x8000), -0x8000)
        self.assertEqual(ual.signed_minutes(0x7fff), 0x7fff)
        self.assertEqual(ual.signed_minutes(60), 60)
        self.assertEqual(ual.signed_minutes(0), 0)
        self.assertEqual(ual.signed_minutes(None), '')

    def test_product_type(self):
        self.assertEqual(ual.product_type(1), '1 (Work Station)')
        self.assertEqual(ual.product_type(2), '2 (Domain Controller)')
        self.assertEqual(ual.product_type(3), '3 (Server)')
        self.assertEqual(ual.product_type(7), '7')
        self.assertEqual(ual.product_type(0), '0')
        self.assertEqual(ual.product_type(None), '')


class IdentityRow(unittest.TestCase):
    def test_row(self):
        self.assertEqual(ual.identity_row(record()), (
            datetime.datetime(2020, 9, 17, 15, 54, 54, 424000, tzinfo=UTC),
            datetime.datetime(2020, 9, 17, 17, 3, 20, 485021, tzinfo=UTC),
            '20200917100320.485021-420', -420, 'HOST-A', 'example.test', '3 (Server)', '6.3.9600', '0.0',
            '00000-00000-00000-AA000', 'Maker', 'Model', '00000000-1111-2222-3333-444444444444', 'SN-1',
            1, 2, 4, 2147483648, '1'))

    def test_missing_values(self):
        row = ual.identity_row({})
        self.assertEqual(row, ('',) * 19)
        self.assertEqual(ual.identity_row(record(OSBuildNumber=None))[7], '')
        self.assertEqual(ual.identity_row(record(ServicePackMinor=None))[8], '')
        self.assertEqual(ual.identity_row(record(ServicePackMajor=None))[8], '')
        self.assertEqual(ual.identity_row(record(OSMajor=None))[7], '')

    def test_zero_values_kept(self):
        row = ual.identity_row(record(OSMinor=0, ServicePackMajor=2, ServicePackMinor=1,
                                      PhysicalProcessorCount=0, OSCurrentTimeZone=0))
        self.assertEqual(row[7], '6.0.9600')
        self.assertEqual(row[8], '2.1')
        self.assertEqual(row[3], 0)
        self.assertEqual(row[14], 0)

    def test_creation_time_not_an_integer(self):
        self.assertEqual(ual.identity_row(record(CreationTime=b'\x00' * 8))[0], '')
        self.assertEqual(ual.identity_row(record(CreationTime=0))[0], '')

    def test_boot_time_unconverted_kept_as_stored(self):
        row = ual.identity_row(record(OSLastBootUpTime='20200917100320.485021-***\0'))
        self.assertEqual(row[1:3], ('', '20200917100320.485021-***'))

    def test_named(self):
        self.assertEqual(ual._named({b'OSMajor': 6, 'OSMinor': 3}), {'OSMajor': 6, 'OSMinor': 3})  # pylint: disable=protected-access


class Processor(unittest.TestCase):
    def run_artifact(self, names, read):
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for name in names:
                path = os.path.join(folder, *name.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(b'x')
                paths.append(path)
            context = mock.Mock()
            context.get_files_found.return_value = paths
            context.get_relative_path.side_effect = lambda p: os.path.relpath(p, folder)
            logged = []
            with mock.patch.object(ual, '_read', side_effect=read), \
                    mock.patch.object(ual, 'logfunc', side_effect=logged.append):
                result = ual.windowsUserAccessLoggingSystemIdentity.__wrapped__(context)
            return result, [os.path.relpath(p, folder) for p in result[2].split('\n') if p], logged

    def test_rows_sorted_and_only_the_database_read(self):
        late = ual.identity_row(record(CreationTime=132449418114420000))
        early = ual.identity_row(record())
        seen = []

        def read(_path, relative):
            seen.append(relative)
            return [late, early]

        (headers, rows, _), sources, logged = self.run_artifact(
            ['Sum/SystemIdentity.mdb', 'Sum/Current.mdb'], read)
        self.assertEqual(len(headers), 19)
        self.assertEqual(rows, [early, late])
        self.assertEqual(seen, [os.path.join('Sum', 'SystemIdentity.mdb')])
        self.assertEqual(sources, [os.path.join('Sum', 'SystemIdentity.mdb')])
        self.assertEqual(logged, [])

    def test_unreadable_database_logged_and_skipped(self):
        def read(_path, relative):
            if relative.startswith('b'):
                raise ValueError('bad page')
            return [ual.identity_row(record())]

        (_, rows, _), sources, logged = self.run_artifact(
            ['a/SystemIdentity.mdb', 'b/SystemIdentity.mdb'], read)
        self.assertEqual(len(rows), 1)
        self.assertEqual(sources, [os.path.join('a', 'SystemIdentity.mdb')])
        self.assertEqual(len(logged), 1)
        self.assertIn('could not read', logged[0])
        self.assertIn('ValueError: bad page', logged[0])

    def test_empty_table_still_names_the_file(self):
        (_, rows, _), sources, _ = self.run_artifact(['Sum/SystemIdentity.mdb'], lambda path, relative: [])
        self.assertEqual(rows, [])
        self.assertEqual(sources, [os.path.join('Sum', 'SystemIdentity.mdb')])

    def test_reader_missing(self):
        with mock.patch.object(ual, 'ese_rows', None):
            (_, rows, source), _, logged = self.run_artifact(['Sum/SystemIdentity.mdb'], lambda *a: [])
        self.assertEqual((rows, source), ([], ''))
        self.assertIn('not available', logged[0])


if __name__ == '__main__':
    unittest.main()
