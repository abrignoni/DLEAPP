"""Pin the firewalld artifacts (scripts/artifacts/linuxFirewalld.py).

The firewalld.conf text and the zone XML are built here in the shapes firewalld writes, and the symbolic link
Fedora Server uses for firewalld.conf is reproduced by mocking what the extraction recorded. The values are made up.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxFirewalld as fw
# pylint: enable=wrong-import-position

CONF = ('# firewalld config\nDefaultZone=FedoraServer\nFirewallBackend=nftables\n\nLogDenied=off\n'
        '# a comment\nCleanupOnExit=yes\n')
FEDORASERVER = ('<?xml version="1.0" encoding="utf-8"?>\n<zone>\n  <short>Public</short>\n'
                '  <service name="ssh"/>\n  <service name="https"/>\n  <port port="8443" protocol="tcp"/>\n'
                '  <forward/>\n</zone>\n')
DLEAPPZONE = ('<zone>\n  <service name="ssh"/>\n  <port port="9000" protocol="tcp"/>\n'
              '  <source address="192.168.99.0/24"/>\n</zone>\n')
# one zone that exercises every dimension the known data does not: interface, ipset and mac sources, protocol,
# masquerade, icmp-block, icmp-block-inversion, forward-port, source-port, a target and a rich rule
EVERYTHING = ('<zone target="DROP">\n  <interface name="eth0"/>\n  <source ipset="badnets"/>\n'
              '  <source mac="00:11:22:33:44:55"/>\n  <protocol value="icmp"/>\n  <masquerade/>\n'
              '  <icmp-block name="echo-request"/>\n  <icmp-block-inversion/>\n'
              '  <forward-port port="80" protocol="tcp" to-port="8080" to-addr="10.0.0.5"/>\n'
              '  <source-port port="123" protocol="udp"/>\n'
              '  <rule family="ipv4">\n    <source address="203.0.113.0/24"/>\n    <drop/>\n  </rule>\n</zone>\n')


class Zones(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.zones = os.path.join(self.folder.name, 'etc', 'firewalld', 'zones')
        os.makedirs(self.zones)

    def write(self, name, text):
        path = os.path.join(self.zones, name)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        return path

    def run_zones(self, paths):
        context = mock.Mock()
        context.get_files_found.return_value = paths
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(fw, 'logfunc') as log:
            result = fw.linuxFirewalldZones.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_basic_zone_and_backup(self):
        cur = self.write('FedoraServer.xml', FEDORASERVER)
        old = self.write('FedoraServer.xml.old', FEDORASERVER.replace('  <service name="https"/>\n', ''))
        (headers, rows, located), _ = self.run_zones([cur, old])
        self.assertEqual(len(headers), 16)
        self.assertEqual(headers[0], 'Zone')
        by_src = {r[-1]: r for r in rows}
        cur_row = by_src[os.path.relpath(cur, self.folder.name)]
        old_row = by_src[os.path.relpath(old, self.folder.name)]
        # both back the same zone name; the .old suffix is stripped before .xml
        self.assertEqual((cur_row[0], old_row[0]), ('FedoraServer', 'FedoraServer'))
        self.assertEqual(cur_row[1], 'default')          # Target absent -> default
        self.assertEqual(cur_row[4], 'ssh | https')      # Services
        self.assertEqual(cur_row[5], '8443/tcp')         # Ports
        self.assertEqual(cur_row[10], 'yes')             # Forward (element present)
        self.assertEqual(cur_row[14], 'Public')          # Short
        self.assertEqual(old_row[4], 'ssh')              # the backup is the state before https was added
        self.assertEqual(located.count('\n'), 1)

    def test_every_dimension(self):
        path = self.write('everything.xml', EVERYTHING)
        (_, rows, _), _ = self.run_zones([path])
        r = rows[0]
        self.assertEqual(r[0], 'everything')
        self.assertEqual(r[1], 'DROP')                                   # Target attribute
        self.assertEqual(r[2], 'eth0')                                   # Interfaces
        self.assertEqual(r[3], 'ipset badnets | mac 00:11:22:33:44:55')  # Source Addresses
        self.assertEqual(r[6], 'icmp')                                   # Protocols
        self.assertEqual(r[7], '80/tcp to 10.0.0.5:8080')                # Forward Ports
        self.assertEqual(r[8], '123/udp')                                # Source Ports
        self.assertEqual(r[9], 'yes')                                    # Masquerade
        self.assertEqual(r[11], 'echo-request')                          # ICMP Blocks
        self.assertEqual(r[12], 'yes')                                   # ICMP Block Inversion
        self.assertIn('<rule family="ipv4">', r[13])                     # Rich Rules (raw text)
        self.assertIn('<drop />', r[13])

    def test_not_a_zone_is_counted(self):
        good = self.write('FedoraServer.xml', FEDORASERVER)
        self.write('notes.xml', '<notzone><x/></notzone>')
        self.write('broken.xml', '<zone><port')
        (_, rows, _), logged = self.run_zones([good,
                                               os.path.join(self.zones, 'notes.xml'),
                                               os.path.join(self.zones, 'broken.xml')])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(logged), 1)
        self.assertIn('2 file(s) that are not a firewalld zone', logged[0])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_zones([])
        self.assertEqual((rows, located, logged), ([], '', []))


class Config(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.conf = os.path.join(self.folder.name, 'etc', 'firewalld')
        os.makedirs(self.conf)

    def write(self, name, text):
        path = os.path.join(self.conf, name)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        return path

    def run_config(self, paths, link=None):
        context = mock.Mock()
        context.get_files_found.return_value = paths
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(fw, 'seeker_of', return_value=(object() if link else None)), \
             mock.patch.object(fw, 'recorded_link', return_value=link), \
             mock.patch.object(fw, 'logfunc') as log:
            result = fw.linuxFirewalldConfig.__wrapped__(context)
        return result, [c.args[0] for c in log.call_args_list]

    def test_plain_file(self):
        path = self.write('firewalld.conf', CONF)
        (headers, rows, located), _ = self.run_config([path])
        self.assertEqual(headers, ('Setting', 'Value', 'Source File'))
        rel = os.path.relpath(path, self.folder.name)
        self.assertEqual(rows, [('DefaultZone', 'FedoraServer', rel), ('FirewallBackend', 'nftables', rel),
                                ('LogDenied', 'off', rel), ('CleanupOnExit', 'yes', rel)])
        self.assertEqual(located, path)

    def test_symlink_resolves_to_preset(self):
        link = self.write('firewalld.conf', '')                 # staged empty, it is a symbolic link
        target = self.write('firewalld-server.conf', CONF)       # the preset the link names
        (_, rows, located), _ = self.run_config([link, target], link='firewalld-server.conf')
        self.assertEqual([r[0] for r in rows],
                         ['DefaultZone', 'FirewallBackend', 'LogDenied', 'CleanupOnExit'])
        src = rows[0][2]
        self.assertEqual(src, 'etc/firewalld/firewalld.conf -> etc/firewalld/firewalld-server.conf')
        self.assertEqual(located, target)   # the located-at path is the real preset, not the link

    def test_preset_not_reported_on_its_own(self):
        # a firewalld-*.conf present but not pointed to by any firewalld.conf is not reported
        self.write('firewalld-workstation.conf', CONF)
        (_, rows, located), _ = self.run_config([os.path.join(self.conf, 'firewalld-workstation.conf')])
        self.assertEqual((rows, located), ([], ''))

    def test_missing_link_target_is_logged(self):
        link = self.write('firewalld.conf', '')
        (_, rows, _), logged = self.run_config([link], link='firewalld-server.conf')
        self.assertEqual(rows, [])
        self.assertEqual(len(logged), 1)
        self.assertIn('which was not found', logged[0])


if __name__ == '__main__':
    unittest.main()
