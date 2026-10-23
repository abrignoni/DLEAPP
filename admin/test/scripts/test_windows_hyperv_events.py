"""Pin the rows in scripts/artifacts/windowsHyperVEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up names and GUIDs); the
expected rows are written out. In the tested logs the Worker and SynthNic events are UserData holding a VmlEventLog
or VmNicNoAvailableMac element, the Compute events are UserData holding a VmlEventLog element, and the VmSwitch
events are EventData with named Data elements; each shape is built here.
"""
import datetime
import pathlib
import re
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsHyperVEvents as hyperv  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOGS = '/case/data/vol1/Windows/System32/winevt/Logs/'
WORKER = LOGS + 'Microsoft-Windows-Hyper-V-Worker-Admin.evtx'
COMPUTE = LOGS + 'Microsoft-Windows-Hyper-V-Compute-Operational.evtx'
SWITCH = LOGS + 'Microsoft-Windows-Hyper-V-VmSwitch-Operational.evtx'

VM_ID = '11111111-2222-3333-4444-555555555555'
WHEN = '2026-10-23 05:24:32.108000+00:00'
TIME = datetime.datetime(2026, 10, 23, 5, 24, 32, 108000, tzinfo=datetime.timezone.utc)


def record(record_id, event_id, body, provider='Microsoft-Windows-Hyper-V-Worker',
           channel='Microsoft-Windows-Hyper-V-Worker-Admin', version='0', source=WORKER):
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" '
           f'Guid="{{51ddfa29-d5c8-4803-be4b-2ecb715570fe}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>{version}</Version><Level>4</Level><TimeCreated SystemTime="{WHEN}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="2000"></Execution>'
           f'<Channel>{channel}</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="S-1-5-83-0"></Security></System>{body}</Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


def user_data(element, fields):
    data = ''.join(f'<{name}>{value}</{name}>' for name, value in fields)
    return f'<UserData><{element} xmlns="http://www.microsoft.com/Windows/Virtualization/Events">{data}</{element}></UserData>'


def event_data(fields):
    return '<EventData>' + ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields) + '</EventData>'


def compute(record_id, event_id, fields, channel='Microsoft-Windows-Hyper-V-Compute-Operational'):
    return record(record_id, event_id, user_data('VmlEventLog', fields), provider='Microsoft-Windows-Hyper-V-Compute',
                  channel=channel, source=COMPUTE)


def switch(record_id, event_id, fields):
    return record(record_id, event_id, event_data(fields), provider='Microsoft-Windows-Hyper-V-VmSwitch',
                  channel='Microsoft-Windows-Hyper-V-VmSwitch-Operational', source=SWITCH)


class _Context:
    @staticmethod
    def get_files_found():
        return [WORKER, COMPUTE, SWITCH]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class TableTest(unittest.TestCase):
    def test_every_insertion_has_a_field_name(self):
        for table in (hyperv._WORKER, hyperv._NIC, hyperv._COMPUTE, hyperv._SWITCH):  # pylint: disable=protected-access
            for key, (message, names) in table.items():
                positions = [int(n) for n in re.findall(r'%(\d+)', message)]
                self.assertEqual(len(names), max(positions, default=0), key)
                self.assertTrue(all(names), key)

    def test_the_providers_do_not_share_a_table(self):
        self.assertEqual(set(hyperv._WORKER_TABLES),  # pylint: disable=protected-access
                         {'Microsoft-Windows-Hyper-V-Worker', 'Microsoft-Windows-Hyper-V-SynthNic'})


class MessageTest(unittest.TestCase):
    def test_fields_are_read_by_name_not_by_position(self):
        rec = record('1', '18500', user_data('VmlEventLog', [('VmId', VM_ID), ('VmName', 'Lab VM')]))
        self.assertEqual(hyperv.event_message(hyperv._WORKER, rec),  # pylint: disable=protected-access
                         f"'Lab VM' started successfully. (Virtual machine ID {VM_ID})")

    def test_the_version_picks_the_message(self):
        fields = [('VmName', 'Lab VM'), ('VmId', VM_ID), ('ProcessorFeatures', '0x1'),
                  ('ProcessorXsaveFeatures', '0x2'), ('PartitionCreationFlags', '0x3'),
                  ('NonArchitecturalCoreSharing', '0'), ('ProcessorCLFlushSize', '64'),
                  ('ImplementedAddressBits', '48')]
        old = record('2', '18609', user_data('VmlEventLog', fields))
        new = record('3', '18609', user_data('VmlEventLog', fields), version='1')
        table = hyperv._WORKER  # pylint: disable=protected-access
        self.assertEqual(hyperv.event_message(table, old),
                         f"'Lab VM' properties were successfully initialized. (Virtual machine ID {VM_ID})")
        self.assertEqual(hyperv.event_message(table, new),
                         f"'Lab VM' properties were successfully initialized. (Virtual machine ID {VM_ID})  "
                         "Guest processor features: 0x1 Guest xsave features: 0x2 Partition creation flags: 0x3 "
                         "Non architectural core sharing: 0 Cache line flush size: 64 Address bit width: 48 "
                         "Physical address width:")

    def test_an_unknown_event_or_version_has_no_message(self):
        table = hyperv._WORKER  # pylint: disable=protected-access
        self.assertEqual(hyperv.event_message(table, record('4', '3086', '')), '')
        self.assertEqual(hyperv.event_message(table, record('5', '18500', '', version='7')), '')
        self.assertEqual(hyperv.event_message(table, record('6', '', '')), '')

    def test_a_percent_escape(self):
        rec = record('7', '1', '')
        self.assertEqual(hyperv.event_message({(1, 0): ('100%% of %1%n', ('Name',))}, rec), '100% of')


class RowTest(unittest.TestCase):
    def test_a_virtual_pci_device_offered(self):
        fields = [('VmName', 'Lab VM'), ('VmId', VM_ID), ('ErrorCode', '0'), ('HResult', '0'),
                  ('Parameter0', 'Bus {AAAA} Slot 0'), ('Parameter1', 'PCI\\VEN_1414'), ('Parameter2', '1')]
        row = hyperv.worker_row(record('8', '33103', user_data('VmlEventLog', fields)))
        self.assertEqual(row, (TIME, '33103', f"'Lab VM': A virtual PCI device was successfully offered to the "
                               f"virtual machine: 'Bus {{AAAA}} Slot 0'. PnpID = 'PCI\\VEN_1414', FunctionType = 1. "
                               f"(Virtual machine ID {VM_ID})", 'Lab VM', VM_ID, 'Microsoft-Windows-Hyper-V-Worker',
                               'Microsoft-Windows-Hyper-V-Worker-Admin', '0', '8', 'LAB-PC'))

    def test_a_synthetic_nic(self):
        fields = [('VmName', 'Lab VM'), ('VmId', VM_ID), ('NicGuid', VM_ID + '--{BBBB}'), ('NicName', 'Lab NIC')]
        row = hyperv.worker_row(record('9', '12597', user_data('VmNicNoAvailableMac', fields),
                                       provider='Microsoft-Windows-Hyper-V-SynthNic'))
        self.assertEqual(row[2:6], (f"'Lab VM' Lab NIC ({VM_ID}--{{BBBB}}) Connected to virtual network. "
                                    f"(Virtual Machine ID {VM_ID})", 'Lab VM', VM_ID,
                                    'Microsoft-Windows-Hyper-V-SynthNic'))

    def test_a_compute_system(self):
        row = hyperv.compute_row(compute('10', '2001', [('SystemId', VM_ID), ('Result', '0x00000000')]))
        self.assertEqual(row, (TIME, '2001', f'[{VM_ID}] Start compute system, result 0x00000000', VM_ID,
                               '0x00000000', 'Microsoft-Windows-Hyper-V-Compute-Operational', '0', '10', 'LAB-PC'))
        row = hyperv.compute_row(compute('11', '1001', [], channel='Microsoft-Windows-Hyper-V-Compute-Admin'))
        self.assertEqual(row[1:6], ('1001', 'The Host Compute Service started successfully.', '', '',
                                    'Microsoft-Windows-Hyper-V-Compute-Admin'))

    def test_a_switch_port(self):
        fields = [('PortNameLen', '36'), ('PortName', 'PORT-GUID'), ('PortFNameLen', '8'), ('PortFName', 'Lab Port'),
                  ('SwitchNameLen', '36'), ('SwitchName', 'SWITCH-GUID'), ('SwitchFNameLen', '10'),
                  ('SwitchFName', 'Lab Switch'), ('Flags', '0'), ('OwnerService', '0')]
        row = hyperv.switch_row(switch('12', '67', fields))
        self.assertEqual(row, (TIME, '67', 'Port PORT-GUID (Friendly Name: Lab Port) successfully created on switch '
                               'SWITCH-GUID (Friendly Name: Lab Switch).', 'Lab Switch', 'SWITCH-GUID', 'Lab Port',
                               'PORT-GUID', '', '', 'Microsoft-Windows-Hyper-V-VmSwitch-Operational', '0', '12',
                               'LAB-PC'))

    def test_a_nic(self):
        row = hyperv.switch_row(switch('13', '125', [('NicNameLen', '8'), ('NicName', 'NIC-GUID'),
                                                     ('NicFNameLen', '7'), ('NicFName', 'Lab NIC')]))
        self.assertEqual(row[2:9], ('Media connected on NIC NIC-GUID (Friendly Name: Lab NIC).', '', '', '', '',
                                    'Lab NIC', 'NIC-GUID'))


class ArtifactTest(unittest.TestCase):
    RECORDS = {
        'microsoft-windows-hyper-v-worker-admin.evtx': (
            [record('1', '18500', ''), record('2', '3086', ''),
             record('3', '12582', '', provider='Microsoft-Windows-Hyper-V-SynthNic'),
             record('4', '18500', '', provider='Microsoft-Windows-Hyper-V-SynthNic')], [WORKER]),
        'microsoft-windows-hyper-v-compute-operational.evtx': (
            [compute('5', '2001', []), compute('6', '2008', []), compute('7', '18500', [])], [COMPUTE]),
        'microsoft-windows-hyper-v-vmswitch-operational.evtx': (
            [switch('8', '67', []), switch('9', '0', []), switch('10', '285', [])], [SWITCH]),
    }

    def _run(self, function):
        calls = []

        def fake_read(_context, file_name, label, event_ids=None, provider=None):
            calls.append((file_name, label, event_ids, provider))
            return self.RECORDS.get(file_name, ([], []))

        with mock.patch.object(hyperv, 'read_event_records', side_effect=fake_read):
            return function.__wrapped__(_Context()), calls

    def test_each_log_keeps_only_its_providers_events(self):
        for function, logs, label, kept in (
                (hyperv.hyperVWorkerEvents, ['microsoft-windows-hyper-v-worker-admin.evtx',
                                             'microsoft-windows-hyper-v-worker-operational.evtx'],
                 'Hyper-V Worker Events', ['1', '3']),
                (hyperv.hyperVComputeEvents, ['microsoft-windows-hyper-v-compute-admin.evtx',
                                              'microsoft-windows-hyper-v-compute-operational.evtx'],
                 'Hyper-V Compute Events', ['5']),
                (hyperv.hyperVVmSwitchEvents, ['microsoft-windows-hyper-v-vmswitch-operational.evtx'],
                 'Hyper-V Virtual Switch Events', ['8'])):
            (headers, rows, source), calls = self._run(function)
            self.assertEqual([call[0] for call in calls], logs)
            self.assertTrue(all(call[1] == label and call[3] is None for call in calls))
            self.assertEqual([row[-2] for row in rows], kept)
            self.assertTrue(all(len(row) == len(headers) for row in rows))
            self.assertEqual(headers[0], ('Event Time (UTC)', 'datetime'))
            self.assertTrue(source)

    def test_no_log_gives_no_rows_and_no_source(self):
        with mock.patch.object(hyperv, 'read_event_records', return_value=([], [])):
            for function in (hyperv.hyperVWorkerEvents, hyperv.hyperVComputeEvents, hyperv.hyperVVmSwitchEvents):
                self.assertEqual(function.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
