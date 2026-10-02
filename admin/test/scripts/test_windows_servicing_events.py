"""Pin the rows in scripts/artifacts/windowsServicingEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up package names); the expected
rows are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsServicingEvents as servicing  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
CBS = 'http://manifests.microsoft.com/win/2004/08/windows/setup_provider'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Setup.evtx'


def record(when, record_id, event_id, element, fields, user='S-1-5-18'):
    data = ''.join(f'<{name}>{value}</{name}>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Servicing" '
           f'Guid="{{bd12f3b8-fc40-4a61-a307-b7a013a069c1}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>0</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1000" ThreadID="2000"></Execution>'
           f'<Channel>Setup</Channel><Computer>LAB-PC</Computer><Security UserID="{user}"></Security></System>'
           f'<UserData><{element} xmlns="{CBS}">{data}</{element}></UserData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
INITIATE = [('PackageIdentifier', 'KB0000001'), ('InitialPackageState', '5000'), ('InitialPackageStateTextized', 'Absent'),
            ('IntendedPackageState', '5112'), ('IntendedPackageStateTextized', 'Installed'), ('Client', 'WindowsUpdateAgent')]
CHANGED = [('PackageIdentifier', 'KB0000001'), ('IntendedPackageState', '5112'), ('IntendedPackageStateTextized', 'Installed'),
           ('ErrorCode', '0x0'), ('Client', 'WindowsUpdateAgent')]
UPDATE = [('UpdateName', 'Example-Feature'), ('PackageIdentifier', 'Example-Feature-Package'), ('ErrorCode', '0x0'),
          ('Client', 'Windows Optional Component Manager')]


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_initiating_changes_carries_the_package_both_states_as_text_and_the_client(self):
        self.assertEqual(servicing.servicing_row(record(WHEN, '11', '1', 'CbsPackageInitiateChanges', INITIATE)),
                         (TIME, '1', 'Initiating changes for package', 'KB0000001', '', 'Absent', 'Installed', '',
                          'WindowsUpdateAgent', '11', 'LAB-PC'))

    def test_a_package_state_record_carries_the_intended_state_and_the_error_code(self):
        self.assertEqual(servicing.servicing_row(record(WHEN, '12', '2', 'CbsPackageChangeState', CHANGED)),
                         (TIME, '2', 'Package was successfully changed to the state', 'KB0000001', '', '', 'Installed', '0x0',
                          'WindowsUpdateAgent', '12', 'LAB-PC'))
        failed = [(n, '0x800f081f' if n == 'ErrorCode' else v) for n, v in CHANGED]
        self.assertEqual(servicing.servicing_row(record(WHEN, '13', '3', 'CbsPackageChangeState', failed))[2:9],
                         ('Package failed to be changed to the state', 'KB0000001', '', '', 'Installed', '0x800f081f',
                          'WindowsUpdateAgent'))
        self.assertEqual(servicing.servicing_row(record(WHEN, '14', '4', 'CbsPackageChangeState', CHANGED))[2],
                         'A reboot is necessary before package can be changed to the state')

    def test_an_update_record_carries_the_update_name_beside_the_package(self):
        self.assertEqual(servicing.servicing_row(record(WHEN, '15', '9', 'CbsUpdateChangeState', UPDATE)),
                         (TIME, '9', 'Selectable update of package was successfully turned on', 'Example-Feature-Package',
                          'Example-Feature', '', '', '0x0', 'Windows Optional Component Manager', '15', 'LAB-PC'))
        started = [(n, '' if n == 'ErrorCode' else v) for n, v in UPDATE]
        self.assertEqual(servicing.servicing_row(record(WHEN, '16', '7', 'CbsUpdateChangeState', started))[2:9],
                         ('Initiating changes to turn on update of package', 'Example-Feature-Package', 'Example-Feature', '',
                          '', '', 'Windows Optional Component Manager'))

    def test_every_event_id_from_1_to_16_has_its_own_label(self):
        labels = [servicing.servicing_row(record(WHEN, '17', str(n), 'CbsUpdateChangeState', []))[2] for n in range(1, 17)]
        self.assertEqual(len(set(labels)), 16)
        self.assertEqual(labels[4], 'The servicing request received for package cannot be satisfied since the package is not '
                                    'applicable')
        self.assertEqual(labels[5], 'Package failed to be changed to the state and is now partially installed')
        self.assertEqual(labels[7], 'Initiating changes to turn off update of package')
        self.assertEqual(labels[9:16], ['Selectable update of package was successfully turned off',
                                        'Update of package failed to be turned on', 'Update of package failed to be turned off',
                                        'A reboot is necessary before the selectable update of package can be turned on',
                                        'A reboot is necessary before the selectable update of package can be turned off',
                                        'Selectable update of package was successfully turned off with its payload removed',
                                        'Update of package failed to be turned off. Payload removal was requested'])

    def test_the_state_numbers_are_not_shown_and_white_space_at_either_end_is_removed(self):
        fields = [('PackageIdentifier', ' KB0000001 '), ('InitialPackageState', '5080'), ('InitialPackageStateTextized', ' Superseded '),
                  ('IntendedPackageState', '5000'), ('IntendedPackageStateTextized', 'Absent'), ('Client', ' CbsTask ')]
        row = servicing.servicing_row(record(WHEN, '18', '1', 'CbsPackageInitiateChanges', fields))
        self.assertEqual(row[3:9], ('KB0000001', '', 'Superseded', 'Absent', '', 'CbsTask'))
        self.assertNotIn('5080', row)
        self.assertNotIn('5000', row)

    def test_a_record_with_no_user_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(servicing.servicing_row(record(WHEN, '19', '2', 'CbsPackageChangeState', [])),
                         (TIME, '2', 'Package was successfully changed to the state', '', '', '', '', '', '', '19', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_events_1_to_16_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '1', 'CbsPackageInitiateChanges', INITIATE), record(WHEN, '21', '2', 'CbsPackageChangeState', CHANGED),
                  record(WHEN, '23', '16', 'CbsUpdateChangeState', UPDATE)], [LOG])
        with mock.patch.object(servicing, 'read_event_records', return_value=found) as reader:
            headers, rows, source = servicing.windowsServicingEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'setup.evtx', 'Windows Servicing Events',
                                       event_ids={str(n) for n in range(1, 17)}, provider='Microsoft-Windows-Servicing')
        self.assertEqual([(row[9], row[1]) for row in rows], [('22', '1'), ('21', '2'), ('23', '16')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Package', 'Update', 'Initial State',
                                   'Intended State', 'Error Code (as stored)', 'Client', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        with mock.patch.object(servicing, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(servicing.windowsServicingEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(servicing, 'read_event_records', return_value=([], [])):
            self.assertEqual(servicing.windowsServicingEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
