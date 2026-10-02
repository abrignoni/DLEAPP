"""Pin the rows in scripts/artifacts/windowsDhcpClientEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up network names and
addresses); the expected rows are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDhcpClientEvents as dhcp  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Dhcp-Client%4Admin.evtx'
# base64 of the six bytes 02 00 5E 10 AB 0F, as python-evtx renders a binary field
CARD_TEXT = 'AgBeEKsP'
CARD = '02:00:5E:10:AB:0F'


def record(when, record_id, event_id, fields):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Dhcp-Client" '
           f'Guid="{{15a7a4f8-0072-4eab-abad-f98a4d666aed}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="{when}"></TimeCreated>'
           f'<EventRecordID>{record_id}</EventRecordID><Execution ProcessID="1000" ThreadID="2000"></Execution>'
           f'<Channel>Microsoft-Windows-Dhcp-Client/Admin</Channel><Computer>LAB-PC</Computer>'
           f'<Security UserID="S-1-5-19"></Security></System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)
SSID = [('NetworkHintString', 'Lab Net'), ('NetworkHint', 'C4162602E45647'), ('HWLength', '6'), ('HWAddress', CARD_TEXT)]
RECEIVED = 'DHCP has received a Service Set Identifier(SSID)'


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class HardwareAddressTest(unittest.TestCase):
    def test_base64_text_becomes_two_digit_upper_case_hexadecimal_joined_by_colons(self):
        self.assertEqual(dhcp.hardware_address(CARD_TEXT), CARD)
        self.assertEqual(dhcp.hardware_address('AAEC'), '00:01:02')
        self.assertEqual(dhcp.hardware_address('/w=='), 'FF')
        self.assertEqual(dhcp.hardware_address('+JTC3+gAqrs='), 'F8:94:C2:DF:E8:00:AA:BB')

    def test_no_text_is_blank_and_text_that_is_not_base64_is_kept(self):
        self.assertEqual(dhcp.hardware_address(''), '')
        self.assertEqual(dhcp.hardware_address('02-00-5E'), '02-00-5E')
        self.assertEqual(dhcp.hardware_address('AgBeEKs'), 'AgBeEKs')
        self.assertEqual(dhcp.hardware_address('AA-EC'), 'AA-EC')


class RowTest(unittest.TestCase):
    def test_the_three_ssid_events_carry_the_name_its_stored_hexadecimal_and_the_card_address(self):
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '11', '50067', SSID)),
                         (TIME, '50067', RECEIVED, 'Lab Net', 'C4162602E45647', CARD, '', '', '', '11', 'LAB-PC'))
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '12', '50065', SSID))[2:6],
                         ('DHCP has found a match in the cache for Service Set Identifier(SSID)', 'Lab Net', 'C4162602E45647',
                          CARD))
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '13', '50066', SSID))[2:6],
                         ('DHCP has plumbed an address using Service Set Identifier(SSID)', 'Lab Net', 'C4162602E45647', CARD))

    def test_1001_and_1003_carry_the_card_address_and_the_status_code_as_stored(self):
        fields = [('HWLength', '6'), ('HWAddress', CARD_TEXT), ('StatusCode', '121')]
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '14', '1003', fields)),
                         (TIME, '1003', 'Your computer was not able to renew its address from the network', '', '', CARD, '121',
                          '', '', '14', 'LAB-PC'))
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '15', '1001', fields))[2:9],
                         ('Your computer was not assigned an address from the network', '', '', CARD, '121', '', ''))

    def test_1002_carries_the_lease_and_the_server_numbers_as_stored(self):
        fields = [('Address1', '3232235777'), ('HWLength', '6'), ('HWAddress', CARD_TEXT), ('Address2', '0')]
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '16', '1002', fields)),
                         (TIME, '1002', 'The IP address lease has been denied by the DHCP server', '', '', CARD, '',
                          '3232235777', '0', '16', 'LAB-PC'))

    def test_white_space_at_either_end_of_a_value_is_removed_and_inner_space_is_kept(self):
        fields = [('NetworkHintString', ' Lab Net '), ('NetworkHint', ' C4162602E45647 '), ('HWAddress', ' ' + CARD_TEXT + ' ')]
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '17', '50067', fields))[3:6], ('Lab Net', 'C4162602E45647', CARD))

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(dhcp.dhcp_row(record(WHEN, '18', '50067', [])),
                         (TIME, '50067', RECEIVED, '', '', '', '', '', '', '18', 'LAB-PC'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_the_six_events_of_the_provider_and_rows_keep_file_order(self):
        found = ([record(WHEN, '22', '50067', SSID), record(WHEN, '21', '50065', SSID), record(WHEN, '23', '1002', [])], [LOG])
        with mock.patch.object(dhcp, 'read_event_records', return_value=found) as reader:
            headers, rows, source = dhcp.dhcpClientEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'microsoft-windows-dhcp-client%4admin.evtx', 'DHCP Client Events',
                                       event_ids={'1001', '1002', '1003', '50065', '50066', '50067'},
                                       provider='Microsoft-Windows-Dhcp-Client')
        self.assertEqual([(row[9], row[1]) for row in rows], [('22', '50067'), ('21', '50065'), ('23', '1002')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'SSID',
                                   'SSID Hexadecimal (as stored)', 'Network Card Address', 'Status Code (as stored)',
                                   'Lease Address (as stored)', 'DHCP Server (as stored)', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = LOG.replace('vol1', 'vol2')
        with mock.patch.object(dhcp, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(dhcp.dhcpClientEvents.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(dhcp, 'read_event_records', return_value=([], [])):
            self.assertEqual(dhcp.dhcpClientEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
