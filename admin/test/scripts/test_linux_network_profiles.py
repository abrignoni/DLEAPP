"""Pin the NetworkManager and netplan artifacts (scripts/artifacts/linuxNetworkProfiles.py).

The files have the layout NetworkManager 1.54.3 and netplan 1.2 wrote on ubuntu2604_arm64_nm_a. The values are made up.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxNetworkProfiles as net
# pylint: enable=wrong-import-position

U1, U2, U3 = ('11111111-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222',
              '33333333-3333-4333-8333-333333333333')
WIFI = f'''[connection]
id=home net
uuid={U1}
type=wifi
#Netplan: passthrough setting
autoconnect=false
timestamp=1700000000
interface-name=wlan0

[ipv4]
method=auto

[ipv6]
method=ignore

[wifi]
ssid=known\\sssid\\\\one
hidden=true

[wifi-security]
key-mgmt=wpa-psk
psk=first
psk = made up key

[proxy]
stray line
'''.encode()
LEGACY = f'[connection]\r\nid=old\r\nuuid={U2}\r\ntype=802-11-wireless\r\n\r\n[802-11-wireless]\r\nssid=legacy\r\n' \
         '[802-11-wireless-security]\r\nkey-mgmt=none\r\n[vpn]\r\n'.encode()
NETPLAN = f'''network:
  version: 2
  renderer: networkd
  ethernets:
    renderer: NetworkManager
    lan0:
      match:
        macaddress: 10:11:22:33:44:55
        driver: e1000
      set-name: lan0
      dhcp4: yes
      dhcp6: false
      addresses: [192.0.2.5/24, "2001:db8::5/64"]
      optional: true
      auth:
        key-management: eap
    lan1:
      renderer: networkd
  wifis:
    NM-{U3}:
      renderer: NetworkManager
      dhcp4: true
      access-points:
        "cafe net":
          hidden: true
          band: 5GHz
          auth:
            key-management: "psk"
            password: "in auth"
            identity: someone
          password: "outside auth"
          networkmanager:
            uuid: "{U3}"
            name: "cafe"
            passthrough:
              connection.autoconnect: "false"
        No: {{}}
        short form:
          password: 01234567
      networkmanager:
        uuid: "device-level"
        name: "device name"
        device: wlan0
    wlan9: {{}}
  nonsense:
    x: {{}}
'''.encode()


def utc(*parts):
    return datetime(*parts, tzinfo=timezone.utc)


class Utc(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(net.utc(' 1700000000\n'), utc(2023, 11, 14, 22, 13, 20))

    def test_not_a_time(self):
        for text in ('', '0', '00', 'x', '-5', '1.5', '١', '9' * 30):
            self.assertEqual(net.utc(text), '', text)


class KeyFile(unittest.TestCase):
    def test_groups_values_and_skipped_lines(self):
        groups, skipped = net.key_file(b'before=group\n' + WIFI + b'=novalue\n[connection]\nid = renamed\n\xff=1\n')
        self.assertEqual(skipped, 3)
        self.assertEqual(groups['connection']['id'], 'renamed')
        self.assertEqual(groups['connection']['uuid'], U1)
        self.assertEqual(groups['wifi'], {'ssid': 'known ssid\\one', 'hidden': 'true'})
        self.assertEqual(groups['wifi-security'], {'key-mgmt': 'wpa-psk', 'psk': 'made up key'})
        self.assertEqual(groups['proxy'], {})
        self.assertEqual(groups['connection']['\\xff'], '1')

    def test_escapes(self):
        groups, _ = net.key_file(b'[g]\na=one\\ntwo\\tthree\\rfour\\\\s\\x\\\nb=  kept  \n[half=1\n')
        self.assertEqual(groups, {'g': {'a': 'one\ntwo\tthree\rfour\\s\\x\\', 'b': 'kept  ', '[half': '1'}})


class ProfileRow(unittest.TestCase):
    def test_wifi(self):
        self.assertEqual(net.profile_row(net.key_file(WIFI)[0]),
                         (utc(2023, 11, 14, 22, 13, 20), 'home net', U1, 'wifi', 'wlan0', 'known ssid\\one', 'true',
                          'wpa-psk', 'made up key', 'false', 'auto', 'ignore', 'proxy'))

    def test_older_group_names_and_absent_values(self):
        self.assertEqual(net.profile_row(net.key_file(LEGACY)[0]),
                         ('', 'old', U2, '802-11-wireless', '', 'legacy', '', 'none', '', '', '', '', 'vpn'))

    def test_no_connection_group(self):
        self.assertIsNone(net.profile_row({'wifi': {'ssid': 'x'}}))


class NetplanRows(unittest.TestCase):
    def test_scalars_stay_as_written(self):
        self.assertEqual(net.load_netplan(b'a: 01234567\nb: No\nc:\nd: 10:11:22:33:44:55\n0x10: true\n'),
                         {'a': '01234567', 'b': 'No', 'c': '', 'd': '10:11:22:33:44:55', '0x10': 'true'})

    def test_devices_and_access_points(self):
        shared = 'networkmanager device'
        self.assertEqual(net.netplan_rows(net.load_netplan(NETPLAN)), [
            ('ethernets', 'lan0', 'NetworkManager', '', '', '', '', '', '', '10:11:22:33:44:55', 'lan0', 'yes',
             'false', '192.0.2.5/24 | 2001:db8::5/64', 'match driver, optional, auth'),
            ('ethernets', 'lan1', 'networkd') + ('',) * 12,
            ('wifis', 'NM-' + U3, 'NetworkManager', 'cafe', U3, 'cafe net', 'true', 'psk', 'in auth', '', '', 'true',
             '', '', shared + ', access point band, access point auth identity, access point networkmanager '
                              'passthrough'),
            ('wifis', 'NM-' + U3, 'NetworkManager', 'device name', 'device-level', 'No', '', '', '', '', '', 'true',
             '', '', shared),
            ('wifis', 'NM-' + U3, 'NetworkManager', 'device name', 'device-level', 'short form', '', '', '01234567',
             '', '', 'true', '', '', shared),
            ('wifis', 'wlan9', 'networkd') + ('',) * 12])

    def test_documents_that_are_not_a_network_mapping(self):
        for document in (None, [], 'text', {'network': None}, {'network': {'wifis': ['x']}}, {'other': {}}):
            self.assertEqual(net.netplan_rows(document), [])
        self.assertEqual(net.netplan_rows({'network': {'ethernets': {7: None}}}),
                         [('ethernets', '7') + ('',) * 13])

    def test_a_device_named_renderer_is_a_device(self):
        self.assertEqual(net.netplan_rows({'network': {'ethernets': {'renderer': {'dhcp4': 'true'}, 'e1': {}}}}),
                         [('ethernets', 'renderer') + ('',) * 9 + ('true', '', '', ''),
                          ('ethernets', 'e1') + ('',) * 13])

    def test_values_that_are_mappings_or_lists(self):
        rows = net.netplan_rows({'network': {'ethernets': {'e1': {'addresses': [{'192.0.2.9/24': {'label': 'x'}},
                                                                                 '192.0.2.8/24'], 'dhcp4': None}}}})
        self.assertEqual(rows, [('ethernets', 'e1') + ('',) * 11 + ('192.0.2.9/24 | 192.0.2.8/24', '')])


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write(self, relative, data):
        path = os.path.join(self.folder.name, *relative.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def run_artifact(self, function, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(net, 'logfunc') as log:
            result = function.__wrapped__(context)
        return result, [call.args[0] for call in log.call_args_list]

    def test_profiles(self):
        wifi = self.write('etc/NetworkManager/system-connections/home.nmconnection', WIFI)
        legacy = self.write('run/NetworkManager/system-connections/old', LEGACY)
        empty = self.write('etc/NetworkManager/system-connections/empty', b'[wifi]\nssid=x\n')
        other = self.write('etc/netplan/a.yaml', WIFI)
        folder = os.path.join(os.path.dirname(wifi), 'subfolder')
        os.makedirs(folder)
        (headers, rows, located), logged = self.run_artifact(net.networkManagerProfiles,
                                                             [legacy, other, folder, empty, wifi])
        self.assertEqual(len(headers), 14)
        self.assertEqual(headers[0], ('Timestamp (UTC)', 'datetime'))
        self.assertEqual([(row[1], row[5], row[13]) for row in rows],
                         [('home net', 'known ssid\\one',
                           os.path.join('etc', 'NetworkManager', 'system-connections', 'home.nmconnection')),
                          ('old', 'legacy', os.path.join('run', 'NetworkManager', 'system-connections', 'old'))])
        self.assertTrue(all(len(row) == 14 for row in rows))
        self.assertEqual(located, wifi + '\n' + legacy)
        self.assertEqual(logged, ['NetworkManager Connection Profiles: 1 files with no connection group, not reported, '
                                  '1 lines that are no group and no key, skipped'])

    def test_netplan(self):
        good = self.write('etc/netplan/50-a.yaml', NETPLAN)
        bad = self.write('etc/netplan/60-bad.yaml', b'network: [unclosed\n')
        bare = self.write('run/netplan/empty.yaml', b'')
        profile = self.write('etc/NetworkManager/system-connections/x.yaml', NETPLAN)
        extra = self.write('lib/netplan/00-x.yaml', b'network:\n  ethernets:\n    e9: {}\n')
        (headers, rows, located), logged = self.run_artifact(net.netplanNetworks, [extra, profile, bare, bad, good])
        self.assertEqual(len(headers), 16)
        self.assertEqual([(row[1], row[5], row[15]) for row in rows],
                         [('lan0', '', os.path.join('etc', 'netplan', '50-a.yaml')),
                          ('lan1', '', os.path.join('etc', 'netplan', '50-a.yaml')),
                          ('NM-' + U3, 'cafe net', os.path.join('etc', 'netplan', '50-a.yaml')),
                          ('NM-' + U3, 'No', os.path.join('etc', 'netplan', '50-a.yaml')),
                          ('NM-' + U3, 'short form', os.path.join('etc', 'netplan', '50-a.yaml')),
                          ('wlan9', '', os.path.join('etc', 'netplan', '50-a.yaml')),
                          ('e9', '', os.path.join('lib', 'netplan', '00-x.yaml'))])
        self.assertTrue(all(len(row) == 16 for row in rows))
        self.assertEqual(located, good + '\n' + extra)
        self.assertEqual(logged, ['Netplan Network Definitions: 1 files that are not YAML, not reported'])

    def test_timestamps(self):
        stamps = self.write('var/lib/NetworkManager/timestamps',
                            f'[timestamps]\n{U1}=1700000000\n{U3}=0\n{U2}=soon\n[other]\nzz=1\n'.encode())
        seen = self.write('var/lib/NetworkManager/seen-bssids',
                          f'[seen-bssids]\n{U1}=AA:BB:CC:00:00:01;AA:BB:CC:00:00:02;\nlone=AA:BB:CC:00:00:03;\n'.encode())
        second = self.write('mnt/var/lib/NetworkManager/timestamps', f'[timestamps]\n{U1}=1700000060\n'.encode())
        hollow = self.write('opt/var/lib/NetworkManager/timestamps', b'[timestamps]\n')
        wifi = self.write('etc/NetworkManager/system-connections/home.nmconnection', WIFI)
        again = self.write('run/NetworkManager/system-connections/z.nmconnection',
                           WIFI.replace(b'id=home net', b'id=later copy'))
        plan = self.write('etc/netplan/50-a.yaml', NETPLAN)
        broken = self.write('etc/netplan/60-bad.yaml', b'network: [unclosed\n')
        (headers, rows, located), logged = self.run_artifact(
            net.networkManagerTimestamps, [plan, broken, again, wifi, hollow, second, seen, stamps])
        state = os.path.join('var', 'lib', 'NetworkManager')
        self.assertEqual(headers, (('Last Activated (UTC)', 'datetime'), 'UUID', 'Profile Name', 'Seen BSSIDs',
                                   'Source File'))
        self.assertEqual(rows, [
            (utc(2023, 11, 14, 22, 14, 20), U1, 'home net', '', os.path.join('mnt', state, 'timestamps')),
            (utc(2023, 11, 14, 22, 13, 20), U1, 'home net', 'AA:BB:CC:00:00:01 | AA:BB:CC:00:00:02',
             os.path.join(state, 'timestamps') + ' | ' + os.path.join(state, 'seen-bssids')),
            ('', U2, '', '', os.path.join(state, 'timestamps')),
            ('', U3, 'cafe', '', os.path.join(state, 'timestamps')),
            ('', 'lone', '', 'AA:BB:CC:00:00:03', os.path.join(state, 'seen-bssids'))])
        self.assertEqual(located, second + '\n' + stamps + '\n' + seen)
        self.assertEqual(logged, ['NetworkManager Last Activation Times: 1 times that are not a count of seconds, '
                                  'Last Activated (UTC) left blank'])

    def test_nothing_found(self):
        for function in (net.networkManagerProfiles, net.netplanNetworks, net.networkManagerTimestamps):
            (_, rows, located), logged = self.run_artifact(function, [])
            self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
