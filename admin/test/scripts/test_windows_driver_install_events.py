"""Pin the rows in scripts/artifacts/windowsDriverInstallEvents.py.

The records are built from XML of the shape python-evtx renders for the four events (made-up devices and drivers);
the expected rows are written out.
"""
import datetime
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDriverInstallEvents as installs  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'
DEVICE = 'USB\\VID_0000&amp;PID_0001\\0123456789'
DEVICE_TEXT = 'USB\\VID_0000&PID_0001\\0123456789'
DRIVER_FIELDS = [('DriverName', 'example.inf_amd64_0123456789abcdef\\example.inf'), ('DriverVersion', '1.2.3.4'),
                 ('DriverProvider', 'Example Corp'), ('DeviceInstanceID', DEVICE),
                 ('SetupClass', '{36fc9e60-c465-11cf-8056-444553540000}'), ('RebootOption', 'False'),
                 ('UpgradeDevice', 'True'), ('IsDriverOEM', 'True'), ('InstallStatus', '0x00000000'),
                 ('DriverDescription', 'Example USB Device')]
SERVICE_FIELDS = [('ServiceName', 'ExampleSvc'), ('DriverFileName', '\\SystemRoot\\system32\\DRIVERS\\Example.sys'),
                  ('DeviceInstanceID', DEVICE), ('PrimaryService', 'True'), ('UpdateService', 'False'),
                  ('AddServiceStatus', '0')]


def record(event_id, when, record_id, fields, source=LOG, provider='Microsoft-Windows-UserPnp'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{96f4a050-7e31-453c-88be-9634f4e02139}}">'
           f'</Provider><EventID>{event_id}</EventID><Version>0</Version><Level>4</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="1000" ThreadID="2000"></Execution><Channel>System</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-18"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


INSTALLED = record('20001', '2023-02-20 22:16:15.500000+00:00', '400', DRIVER_FIELDS)
REMOVED = record('20002', '2023-02-21 10:00:00.250000+00:00', '410', DRIVER_FIELDS)
ADDED = record('20003', '2023-02-20 22:16:16.750000+00:00', '401', SERVICE_FIELDS)
SERVICE_REMOVED = record('20004', '2023-02-21 10:00:01.000000+00:00', '411', SERVICE_FIELDS)
DRIVER_TAIL = (DEVICE_TEXT, 'example.inf_amd64_0123456789abcdef\\example.inf', 'Example USB Device', 'Example Corp',
               '1.2.3.4', '{36fc9e60-c465-11cf-8056-444553540000}', 'True', 'True', 'False', '0x00000000')
SERVICE_TAIL = (DEVICE_TEXT, 'ExampleSvc', '\\SystemRoot\\system32\\DRIVERS\\Example.sys', 'True', 'False', '0')


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_driver_install_and_a_driver_removal(self):
        self.assertEqual(installs.driver_row(INSTALLED),
                         (utc(2023, 2, 20, 22, 16, 15, 500000), '20001', 'install driver', *DRIVER_TAIL, '400', 'LAB-PC'))
        self.assertEqual(installs.driver_row(REMOVED),
                         (utc(2023, 2, 21, 10, 0, 0, 250000), '20002', 'remove driver', *DRIVER_TAIL, '410', 'LAB-PC'))

    def test_a_service_added_and_a_service_removed(self):
        self.assertEqual(installs.service_row(ADDED),
                         (utc(2023, 2, 20, 22, 16, 16, 750000), '20003', 'add Service', *SERVICE_TAIL, '401', 'LAB-PC'))
        self.assertEqual(installs.service_row(SERVICE_REMOVED),
                         (utc(2023, 2, 21, 10, 0, 1), '20004', 'remove Service', *SERVICE_TAIL, '411', 'LAB-PC'))

    def test_each_driver_field_lands_in_its_own_column(self):
        fields = [('DriverName', 'a'), ('DriverVersion', 'b'), ('DriverProvider', 'c'), ('DeviceInstanceID', 'd'),
                  ('SetupClass', 'e'), ('RebootOption', 'f'), ('UpgradeDevice', 'g'), ('IsDriverOEM', 'h'),
                  ('InstallStatus', 'i'), ('DriverDescription', 'j')]
        row = installs.driver_row(record('20001', '2023-02-20 22:16:15.500000+00:00', '1', fields))
        self.assertEqual(row[3:], ('d', 'a', 'j', 'c', 'b', 'e', 'h', 'g', 'f', 'i', '1', 'LAB-PC'))

    def test_each_service_field_lands_in_its_own_column(self):
        fields = [('ServiceName', 'a'), ('DriverFileName', 'b'), ('DeviceInstanceID', 'c'), ('PrimaryService', 'd'),
                  ('UpdateService', 'e'), ('AddServiceStatus', 'f')]
        row = installs.service_row(record('20003', '2023-02-20 22:16:15.500000+00:00', '2', fields))
        self.assertEqual(row[3:], ('c', 'a', 'b', 'd', 'e', 'f', '2', 'LAB-PC'))

    def test_a_file_name_that_is_a_command_line_is_kept_whole(self):
        command = '&quot;C:\\Program Files\\Example\\Monitor Svc.exe&quot; /run'
        fields = [(name, command if name == 'DriverFileName' else value) for name, value in SERVICE_FIELDS]
        row = installs.service_row(record('20003', '2023-02-20 22:16:16.750000+00:00', '402', fields))
        self.assertEqual(row[5], '"C:\\Program Files\\Example\\Monitor Svc.exe" /run')

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        bare = record('20003', '2020-09-18 05:41:31.000000+00:00', '7', [])
        self.assertEqual(installs.service_row(bare),
                         (utc(2020, 9, 18, 5, 41, 31), '20003', 'add Service', '', '', '', '', '', '', '7', 'LAB-PC'))
        bare = record('20002', '2020-09-18 05:41:31.000000+00:00', '8', [])
        self.assertEqual(installs.driver_row(bare),
                         (utc(2020, 9, 18, 5, 41, 31), '20002', 'remove driver', '', '', '', '', '', '', '', '', '', '',
                          '8', 'LAB-PC'))


class InstallRecordsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(folder.cleanup)
        self.addCleanup(installs._read.clear)  # pylint: disable=protected-access
        installs._read.clear()  # pylint: disable=protected-access
        self.root = folder.name
        self.log = os.path.join(folder.name, 'data', 'vol1', 'Windows', 'System32', 'winevt', 'Logs', 'System.evtx')
        os.makedirs(os.path.dirname(self.log))
        with open(self.log, 'wb') as handle:
            handle.write(b'x' * 10)
        self.folder = os.path.join(folder.name, 'data', 'vol2', 'System.evtx')
        os.makedirs(self.folder)

    def test_the_logs_are_read_once_for_both_artifacts_and_again_when_a_log_changes(self):
        found = ([INSTALLED, ADDED, REMOVED, SERVICE_REMOVED], [self.log])
        with mock.patch.object(installs, 'read_event_records', return_value=found) as reader:
            first = installs.deviceDriverInstalls.__wrapped__(_Context([self.log]))
            second = installs.deviceServiceInstalls.__wrapped__(_Context([self.folder, self.log]))
            self.assertEqual(reader.call_count, 1)
            reader.assert_called_once_with(mock.ANY, 'system.evtx', 'Driver Install Events',
                                           event_ids={'20001', '20002', '20003', '20004'},
                                           provider='Microsoft-Windows-UserPnp')
            with open(self.log, 'ab') as handle:
                handle.write(b'more')
            installs.deviceServiceInstalls.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 2)
            times = os.stat(self.log)
            with open(self.log, 'ab') as handle:
                handle.write(b'same time, other size')
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns))
            installs.deviceServiceInstalls.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 3)
            os.utime(self.log, ns=(times.st_atime_ns, times.st_mtime_ns + 5 * 10 ** 9))
            installs.deviceServiceInstalls.__wrapped__(_Context([self.log]))
            self.assertEqual(reader.call_count, 4)
            installs.deviceServiceInstalls.__wrapped__(_Context([]))
            self.assertEqual(reader.call_count, 5)
        self.assertEqual([row[1] for row in first[1]], ['20001', '20002'])
        self.assertEqual([row[1] for row in second[1]], ['20003', '20004'])
        self.assertEqual([result[2] for result in (first, second)], [self.log] * 2)

    def test_another_log_of_the_same_size_and_time_is_read_on_its_own(self):
        twin = os.path.join(self.root, 'data', 'vol3', 'System.evtx')
        os.makedirs(os.path.dirname(twin))
        with open(twin, 'wb') as handle:
            handle.write(b'x' * 10)
        times = os.stat(self.log)
        os.utime(twin, ns=(times.st_atime_ns, times.st_mtime_ns))
        with mock.patch.object(installs, 'read_event_records', return_value=([INSTALLED], [self.log])) as reader:
            installs.deviceDriverInstalls.__wrapped__(_Context([self.log]))
            installs.deviceDriverInstalls.__wrapped__(_Context([twin]))
        self.assertEqual(reader.call_count, 2)

    def test_two_logs_are_both_named_one_to_a_line(self):
        other = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        with mock.patch.object(installs, 'read_event_records', return_value=([INSTALLED, ADDED], [LOG, other])), \
                mock.patch.object(installs, '_system_logs', return_value=[]):
            drivers = installs.deviceDriverInstalls.__wrapped__(_Context([]))
            services = installs.deviceServiceInstalls.__wrapped__(_Context([]))
        self.assertEqual(drivers[2], LOG + '\n' + other)
        self.assertEqual(services[2], drivers[2])

    def test_the_headers(self):
        with mock.patch.object(installs, 'read_event_records', return_value=([], [])):
            drivers = installs.deviceDriverInstalls.__wrapped__(_Context([]))
            services = installs.deviceServiceInstalls.__wrapped__(_Context([]))
        self.assertEqual(drivers, ((('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Instance ID',
                                    'Driver Name', 'Driver Description', 'Driver Provider', 'Driver Version',
                                    'Setup Class GUID', 'OEM Driver (as stored)', 'Upgrade Device (as stored)',
                                    'Reboot Option (as stored)', 'Install Status (as stored)', 'Record ID', 'Computer'),
                                   [], ''))
        self.assertEqual(services, ((('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Device Instance ID',
                                     'Service Name', 'Driver File Name', 'Primary Service (as stored)',
                                     'Update Service (as stored)', 'Status (as stored)', 'Record ID', 'Computer'),
                                    [], ''))


if __name__ == '__main__':
    unittest.main()
