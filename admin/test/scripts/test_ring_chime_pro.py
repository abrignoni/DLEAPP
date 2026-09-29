"""Pin the Ring Chime Pro artifacts (scripts/artifacts/ringChimePro.py).

Every file here is made up. The DHCP lease file is built from busybox 1.24.1's layout
(networking/udhcp/dhcpd.h struct dyn_lease and files.c write_leases at 5c23f256): an 8-byte
big-endian write time, then 36-byte records of seconds remaining, IP, MAC, host name and padding.
"""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import ringChimePro as rc
# pylint: enable=wrong-import-position


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


class FileInfo:
    def __init__(self, modified):
        self.modification_date = modified


class Seeker:
    def __init__(self):
        self.file_infos = {}


class FakeContext:
    def __init__(self, paths, root, seeker):
        self.paths, self.root, self.seeker = paths, root, seeker

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        return self.seeker


def lease(remaining, ip, mac, hostname=b''):
    return struct.pack('>I4s6s20s2x', remaining, bytes(ip), bytes(mac), hostname)


class RingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.seeker = Seeker()
        self.logged = []
        patcher = mock.patch.object(rc, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = []
        a = 'lba100/rootfs/var/ring/properties/'
        b = 'lba200/rootfs/var/ring/properties/'
        self.add(a + 'system.version', b'0 0 9.9.9', 1700000000)
        self.add(a + 'system.last_reboot_ts', b'0 0 1600000000', 1700000100)
        self.add(a + 'reboot.count', b'3 250 7', 1700000200)
        self.add(a + 'system.oobe_done', b'0 0 ', 1700000300)
        self.add(a + 'network.config', b'0 0 {"S":"Example Net","T":"wpa-personal","P":"secret","IP_TYPE":"dhcp",'
                                       b'"IP_ADDR":"","K":"abc","X":1}', 1700000400)
        self.add(b + 'system.version', b'0 0 9.9.8', 1690000000)
        self.add(b + 'system.bad_ts', b'0 0 later', 1690000000)
        self.add(b + 'blob', b'\xff\xfe\x00', 1690000000)
        self.add(b + 'network.config_backup', b'0 0 {\n  "country": "ZZ",\n  "domain": "",\n  "net": {"S": "Other",'
                                              b' "T": "open", "IP_TYPE": "static", "IP_ADDR": "10.0.0.2"}\n}',
                 1690000100)
        self.add(b + 'network.config', b'0 0 not json', 1690000200)
        s = 'lba300/ubifs_system/'
        self.add(s + 'last_boot_reason', b'test\n', 1680000000)
        self.add(s + 'reboot_tmp_prop/network.up_time', b'42', 1680000000)
        self.add(s + 'ring.conf', b'alpha 1\n\nbeta two words\nlonely\n', 1680000500)
        self.add(s + 'audio.wav', b'RIFF', 1680000000)
        self.add(s + 'properties/nested/deeper', b'0 0 x', 1680000000)
        self.add('lba200/rootfs/var/lib/misc/udhcpd.leases',
                 struct.pack('>q', 1650000000) + lease(3600, [192, 168, 1, 10], [0, 1, 2, 3, 4, 5], b'phone') +
                 lease(0, [192, 168, 1, 11], [10, 11, 12, 13, 14, 15]) + b'\x01\x02\x03', 1650000000)
        self.add('lba200/rootfs/webSvr/logs/error.log',
                 b'2021-01-02 03:04:05: (src/example.c.10) listener up \nplain line\n\n', 1650000000)
        # A Linux volume with the same generic files and no var/ring/properties.
        self.add('lba900/root/var/lib/misc/udhcpd.leases', struct.pack('>q', 1) + lease(5, [1, 2, 3, 4], [9] * 6))
        self.add('lba900/root/webSvr/logs/error.log', b'2021-01-02 03:04:05: (x.c.1) other\n')
        folder = os.path.join(self.root, 'lba100', 'rootfs', 'var', 'ring', 'properties', 'dir')
        os.makedirs(folder)
        self.paths.append(folder)

    def add(self, relative, data, modified=None):
        path = os.path.join(self.root, *relative.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        self.paths.append(path)
        if modified is not None:
            self.seeker.file_infos[path] = FileInfo(modified)
        return path

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self, func):
        headers, rows, source = getattr(rc, func).__wrapped__(FakeContext(self.paths, self.root, self.seeker))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertTrue(all(len(r) == len(names) for r in rows))
        self.source = source  # pylint: disable=attribute-defined-outside-init
        return [dict(zip(names, r)) for r in rows]

    def test_properties(self):
        rows = {(r['Folder'], r['Property']): r for r in self.rows('ringChimeProProperties')}
        a = 'lba100/rootfs/var/ring/properties'
        self.assertEqual(sorted(rows), sorted([
            (a, 'system.version'), (a, 'system.last_reboot_ts'), (a, 'reboot.count'), (a, 'system.oobe_done'),
            ('lba200/rootfs/var/ring/properties', 'system.version'),
            ('lba200/rootfs/var/ring/properties', 'system.bad_ts'),
            ('lba200/rootfs/var/ring/properties', 'blob'),
            ('lba300/ubifs_system', 'last_boot_reason'),
            ('lba300/ubifs_system/reboot_tmp_prop', 'network.up_time')]))
        version = rows[(a, 'system.version')]
        self.assertEqual((version['Value'], version['Header (as stored)'], version['Modified (UTC)']),
                         ('9.9.9', '0 0', utc(1700000000)))
        self.assertEqual(rows[(a, 'system.last_reboot_ts')]['Value as Time (UTC)'], utc(1600000000))
        self.assertEqual((rows[(a, 'reboot.count')]['Header (as stored)'], rows[(a, 'reboot.count')]['Value']),
                         ('3 250', '7'))
        self.assertEqual(rows[(a, 'system.oobe_done')]['Value'], '')
        self.assertEqual(rows[('lba200/rootfs/var/ring/properties', 'system.bad_ts')]['Value as Time (UTC)'], '')
        self.assertEqual(rows[('lba200/rootfs/var/ring/properties', 'blob')]['Value'], 'fffe00')
        boot = rows[('lba300/ubifs_system', 'last_boot_reason')]
        self.assertEqual((boot['Value'], boot['Header (as stored)']), ('test', ''))
        self.assertEqual(rows[('lba300/ubifs_system/reboot_tmp_prop', 'network.up_time')]['Value'], '42')
        self.assertEqual(rows[(a, 'system.version')]['Value as Time (UTC)'], '')
        self.assertEqual(rows[(a, 'reboot.count')]['Value as Time (UTC)'], '')
        self.assertEqual(rows[('lba300/ubifs_system/reboot_tmp_prop', 'network.up_time')]['Value as Time (UTC)'], '')
        self.assertNotIn('network.config', self.source)
        self.assertFalse(any('could not be read' in line for line in self.logged))

    def test_wifi(self):
        rows = {(r['Folder'], r['Property']): r for r in self.rows('ringChimeProWifi')}
        self.assertEqual(len(rows), 3)
        a = rows[('lba100/rootfs/var/ring/properties', 'network.config')]
        self.assertEqual((a['SSID'], a['Security Type'], a['Passphrase'], a['IP Type'], a['K (as stored)'],
                          a['Other Fields'], a['Modified (UTC)']),
                         ('Example Net', 'wpa-personal', 'secret', 'dhcp', 'abc', '{"X": 1}', utc(1700000400)))
        backup = rows[('lba200/rootfs/var/ring/properties', 'network.config_backup')]
        self.assertEqual((backup['SSID'], backup['IP Address'], backup['Country'], backup['Domain'],
                          backup['Other Fields']), ('Other', '10.0.0.2', 'ZZ', '', ''))
        bad = rows[('lba200/rootfs/var/ring/properties', 'network.config')]
        self.assertEqual((bad['SSID'], bad['Other Fields']), ('', 'not json'))
        self.assertTrue(any('1 files whose JSON could not be read' in line for line in self.logged))

    def test_conf(self):
        rows = self.rows('ringChimeProConf')
        self.assertEqual([(r['Key'], r['Value'], r['Line Number']) for r in rows],
                         [('alpha', '1', 1), ('beta', 'two words', 3), ('lonely', '', 4)])
        self.assertEqual(rows[0]['Modified (UTC)'], utc(1680000500))

    def test_dhcp_leases(self):
        rows = self.rows('ringChimeProDhcpLeases')
        self.assertEqual([(r['IP Address'], r['MAC Address'], r['Hostname'], r['Seconds Remaining When Written'])
                          for r in rows],
                         [('192.168.1.10', '00:01:02:03:04:05', 'phone', 3600),
                          ('192.168.1.11', '0a:0b:0c:0d:0e:0f', '', 0)])
        self.assertEqual((rows[0]['Written (UTC)'], rows[0]['Lease Expires (UTC)']), (utc(1650000000), utc(1650003600)))
        self.assertEqual(rows[1]['Lease Expires (UTC)'], '')
        self.assertEqual({r['Folder'] for r in rows}, {'lba200/rootfs/var/lib/misc'})
        self.assertTrue(any('3 bytes after the last whole lease record' in line for line in self.logged))
        self.assertTrue(any('1 lease files in a volume without var/ring/properties' in line for line in self.logged))
        self.assertNotIn('lba900', self.source)

    def test_web_log(self):
        rows = self.rows('ringChimeProWebLog')
        self.assertEqual([(r['Time (as stored, local)'], r['Source (as stored)'], r['Message'], r['Line Number'])
                          for r in rows],
                         [('2021-01-02 03:04:05', '(src/example.c.10)', 'listener up', 1), ('', '', 'plain line', 2)])
        self.assertTrue(any('1 error.log files in a volume without' in line for line in self.logged))

    def test_no_ring_volume_reads_no_generic_files(self):
        self.paths = [p for p in self.paths if '/var/ring/' not in p.replace(os.sep, '/')]
        self.assertEqual(self.rows('ringChimeProDhcpLeases'), [])
        self.assertEqual(self.rows('ringChimeProWebLog'), [])


if __name__ == '__main__':
    unittest.main()
