"""Pin the lease and DHCP message reading in scripts/artifacts/macosDhcpLeases.py."""
import pathlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosDhcpLeases as dhcp  # pylint: disable=wrong-import-position

HEADERS = ('Lease Start', 'Lease End', 'Interface', 'IP Address', 'Lease Length',
           'Router IP Address', 'Router Hardware Address', 'SSID', 'Network ID', 'DHCP Server',
           'Subnet Mask', 'DNS Servers', 'Domain Name', 'Message Type', 'Client Identifier')


def message(*options):
    """A BOOTREPLY with the magic cookie and the given (code, value) options, then end."""
    fixed = bytearray(236)
    fixed[0] = 2
    body = b''.join(bytes((code, len(value))) + value for code, value in options)
    return bytes(fixed) + bytes((99, 130, 83, 99)) + body + b'\xff'


class OptionsTest(unittest.TestCase):
    def test_options_after_the_cookie_with_pads_and_repeats(self):
        packet = message((53, b'\x05'), (54, bytes((10, 0, 0, 1))), (6, bytes((10, 0, 0, 2))),
                         (6, bytes((10, 0, 0, 3))))
        packet = packet[:240] + b'\x00' + packet[240:]
        options = dhcp.dhcp_options(packet)
        self.assertEqual(sorted(options), [6, 53, 54])
        self.assertEqual(options[53], b'\x05')
        self.assertEqual(dhcp.ipv4_list(options[6]), '10.0.0.2, 10.0.0.3')
        self.assertEqual(dhcp.ipv4_list(options[54]), '10.0.0.1')

    def test_no_cookie_or_a_truncated_option_stops_reading(self):
        self.assertEqual(dhcp.dhcp_options(bytes(300)), {})
        wrong_cookie = bytearray(message((53, b'\x05')))
        wrong_cookie[239] = 0
        self.assertEqual(dhcp.dhcp_options(bytes(wrong_cookie)), {})
        self.assertEqual(dhcp.dhcp_options(None), {})
        cut = message((53, b'\x05'), (15, b'example'))[:-4]
        self.assertEqual(dhcp.dhcp_options(cut), {53: b'\x05'})

    def test_values(self):
        self.assertEqual(dhcp.message_type(b'\x05'), 'DHCPACK (5)')
        self.assertEqual(dhcp.message_type(b'\x09'), '9')
        self.assertEqual(dhcp.message_type(b''), '')
        self.assertEqual(dhcp.ipv4_list(b'\x01\x02\x03'), '')
        self.assertEqual(dhcp.hardware_address(b'\x16\xc2\x13\xce\x8c\x64'), '16:c2:13:ce:8c:64')


class LeaseRowTest(unittest.TestCase):
    def test_a_lease_row(self):
        lease = {
            'ClientIdentifier': b'\x01\x00\x0c\x29\x4a\x6b\xa6', 'IPAddress': '10.0.0.9',
            'LeaseLength': 3600, 'LeaseStartDate': datetime(2021, 2, 19, 19, 20, 49),
            'RouterIPAddress': '10.0.0.1', 'RouterHardwareAddress': b'\x16\xc2\x13\xce\x8c\x64',
            'SSID': 'net', 'NetworkID': 'N-1',
            'PacketData': message((53, b'\x05'), (54, bytes((10, 0, 0, 1))),
                                  (1, bytes((255, 255, 255, 0))), (15, b'lan\x00')),
        }
        row = dict(zip(HEADERS, dhcp.lease_row(lease, 'en0')))
        self.assertEqual(row['Lease Start'], datetime(2021, 2, 19, 19, 20, 49, tzinfo=timezone.utc))
        self.assertEqual(row['Lease End'], datetime(2021, 2, 19, 20, 20, 49, tzinfo=timezone.utc))
        self.assertEqual((row['Interface'], row['Lease Length'], row['SSID'], row['Network ID']),
                         ('en0', 3600, 'net', 'N-1'))
        self.assertEqual((row['DHCP Server'], row['Subnet Mask'], row['Domain Name'],
                          row['Message Type']), ('10.0.0.1', '255.255.255.0', 'lan', 'DHCPACK (5)'))
        self.assertEqual(row['Client Identifier'], '01000c294a6ba6')

    def test_an_infinite_lease_has_no_end_and_a_missing_packet_leaves_blanks(self):
        row = dict(zip(HEADERS, dhcp.lease_row(
            {'LeaseLength': 0xFFFFFFFF, 'LeaseStartDate': datetime(2021, 2, 19)}, 'en1')))
        self.assertEqual((row['Lease End'], row['DHCP Server'], row['Message Type']), ('', '', ''))
        self.assertEqual(row['Lease Length'], 0xFFFFFFFF)


if __name__ == '__main__':
    unittest.main()
