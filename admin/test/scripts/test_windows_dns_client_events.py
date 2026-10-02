"""Pin the rows in scripts/artifacts/windowsDnsClientEvents.py.

The records are built from XML of the shape python-evtx renders for the event (made-up names and addresses from the
documentation ranges); the expected rows are written out.
"""
import base64
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDnsClientEvents as dns  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/System.evtx'
# 02 00 | port 00 35 | 192.0.2.53 | zeros to 128 bytes
IPV4 = base64.b64encode(bytes.fromhex('02000035c0000235') + bytes(120)).decode()
# 17 00 | port 00 35 | flow 01 02 03 04 | 2001:db8::53 | scope 05 01 02 03 | zeros to 128 bytes
IPV6 = base64.b64encode(bytes.fromhex('17000035010203042001' + '0db8' + '00' * 10 + '0053' + '05010203') + bytes(100)).decode()


def record(when, record_id, fields, version='0', provider='Microsoft-Windows-DNS-Client', event_id='1014'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{1c95126e-7eea-49a9-a3fe-a378b03ddb4d}}">'
           f'</Provider><EventID>{event_id}</EventID><Version>{version}</Version><Level>3</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="1000" ThreadID="2000"></Execution><Channel>System</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="S-1-5-20"></Security></System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


WHEN = '2023-02-20 22:16:15.500000+00:00'
TIME = datetime.datetime(2023, 2, 20, 22, 16, 15, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class SocketAddressTest(unittest.TestCase):
    def test_an_ipv4_socket_address(self):
        self.assertEqual(dns.socket_address(IPV4), ('2', '192.0.2.53', ''))

    def test_an_ipv6_socket_address_is_read_after_the_port_and_flow_fields_and_its_scope_after_it(self):
        self.assertEqual(dns.socket_address(IPV6), ('23', '2001:db8::53', '50462981'))
        big = base64.b64encode(bytes.fromhex('1700' + '00' * 6 + 'fe80' + '00' * 13 + '01' + '0c010000') + bytes(100)).decode()
        self.assertEqual(dns.socket_address(big), ('23', 'fe80::1', '268'))

    def test_another_family_gives_its_number_and_no_address(self):
        self.assertEqual(dns.socket_address(base64.b64encode(bytes(128)).decode()), ('0', '', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(bytes.fromhex('1100') + bytes(126)).decode()), ('17', '', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(bytes.fromhex('0201') + bytes(126)).decode()), ('258', '', ''))

    def test_a_socket_address_too_short_for_its_address_gives_only_the_family(self):
        self.assertEqual(dns.socket_address(base64.b64encode(bytes.fromhex('02000035c00002')).decode()), ('2', '', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(bytes.fromhex('02000035c0000235')).decode()), ('2', '192.0.2.53', ''))
        short = bytes.fromhex('17000035010203042001' + '0db8' + '00' * 10 + '00')
        self.assertEqual(dns.socket_address(base64.b64encode(short).decode()), ('23', '', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(short + b'\x53').decode()), ('23', '2001:db8::53', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(short + b'\x53\x05\x00\x00').decode()), ('23', '2001:db8::53', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(short + b'\x53\x05\x00\x00\x00').decode()), ('23', '2001:db8::53', '5'))

    def test_text_that_is_not_base64_or_holds_under_two_bytes_gives_nothing_and_two_bytes_give_the_family(self):
        self.assertEqual(dns.socket_address('not base64!'), ('', '', ''))
        self.assertEqual(dns.socket_address(''), ('', '', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(b'\x02').decode()), ('', '', ''))
        self.assertEqual(dns.socket_address(base64.b64encode(b'\x02\x00').decode()), ('2', '', ''))
        self.assertEqual(dns.socket_address('AgAA' + '!' + 'AMCo'), ('', '', ''))


class RowTest(unittest.TestCase):
    def test_a_version_0_record_has_no_client_process_id(self):
        fields = [('QueryName', 'Files.Example.COM'), ('AddressLength', '128'), ('Address', IPV4)]
        self.assertEqual(dns.timeout_row(record(WHEN, '7', fields)),
                         (TIME, 'Files.Example.COM', '192.0.2.53', '', '2', '', '7', 'LAB-PC'))

    def test_a_version_1_record_carries_the_client_process_id(self):
        fields = [('QueryName', 'wpad'), ('AddressLength', '128'), ('Address', IPV6), ('ClientPID', '4321')]
        self.assertEqual(dns.timeout_row(record(WHEN, '8', fields, version='1')),
                         (TIME, 'wpad', '2001:db8::53', '50462981', '23', '4321', '8', 'LAB-PC'))

    def test_a_record_with_no_event_data_keeps_its_time_and_blank_fields(self):
        self.assertEqual(dns.timeout_row(record(WHEN, '9', [])), (TIME, '', '', '', '', '', '9', 'LAB-PC'))

    def test_the_address_length_field_is_not_used_to_cut_the_address(self):
        fields = [('QueryName', 'a.example'), ('AddressLength', '4'), ('Address', IPV4)]
        self.assertEqual(dns.timeout_row(record(WHEN, '10', fields))[2:5], ('192.0.2.53', '', '2'))


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_event_1014_of_the_provider_and_rows_keep_file_order(self):
        one = [('QueryName', 'b.example'), ('Address', IPV4)]
        two = [('QueryName', 'a.example'), ('Address', IPV6)]
        found = ([record(WHEN, '12', one), record(WHEN, '11', two, version='1')], [LOG])
        with mock.patch.object(dns, 'read_event_records', return_value=found) as reader:
            headers, rows, source = dns.dnsNameResolutionTimeouts.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'system.evtx', 'DNS Name Resolution Timeouts', event_ids={'1014'},
                                       provider='Microsoft-Windows-DNS-Client')
        self.assertEqual([row[1] for row in rows], ['b.example', 'a.example'])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Query Name', 'Address', 'Scope ID',
                                   'Address Family (as stored)', 'Client Process ID', 'Record ID', 'Computer'))

    def test_two_logs_are_both_named_one_to_a_line_and_no_log_gives_no_source(self):
        other = '/case/data/vol2/Windows/System32/winevt/Logs/System.evtx'
        with mock.patch.object(dns, 'read_event_records', return_value=([], [LOG, other])):
            self.assertEqual(dns.dnsNameResolutionTimeouts.__wrapped__(_Context())[1:], ([], LOG + '\n' + other))
        with mock.patch.object(dns, 'read_event_records', return_value=([], [])):
            self.assertEqual(dns.dnsNameResolutionTimeouts.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
