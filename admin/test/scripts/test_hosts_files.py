"""Pin the hosts file reading in scripts/artifacts/hostsFiles.py."""
import fnmatch
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import hostsFiles as hosts  # pylint: disable=wrong-import-position


class HostsEntriesTest(unittest.TestCase):
    def test_entries_comments_and_blank_lines(self):
        text = ('# a comment line\n'
                '\n'
                '127.0.0.1\tlocalhost\n'
                '  10.0.0.5   a.example b.example   # lab box\n'
                '::1\n'
                '#\t127.0.0.2 commented.example\n')
        self.assertEqual(list(hosts.hosts_entries(text)), [
            (3, '127.0.0.1', 'localhost', ''),
            (4, '10.0.0.5', 'a.example b.example', 'lab box'),
            (5, '::1', '', ''),
        ])

    def test_decoding(self):
        self.assertEqual(hosts.decode_text('1.2.3.4 a\r\n'.encode('utf-16')), '1.2.3.4 a\r\n')
        self.assertEqual(hosts.decode_text(b'\xef\xbb\xbf1.2.3.4 a'), '1.2.3.4 a')
        self.assertEqual(hosts.decode_text(b'1.2.3.4 \xff'), '1.2.3.4 �')

    def test_template_copy(self):
        self.assertTrue(hosts.is_template('vol/System/Library/Templates/Data/private/etc/hosts'))
        self.assertTrue(hosts.is_template('System\\Library\\Templates\\Data\\private\\etc\\hosts'))
        self.assertFalse(hosts.is_template('vol/private/etc/hosts'))
        self.assertFalse(hosts.is_template('System/Volumes/Data/private/etc/hosts'))


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class LinuxHostsTest(unittest.TestCase):
    def test_other_platform(self):
        self.assertTrue(hosts.is_other_platform('vol/private/etc/hosts'))
        self.assertTrue(hosts.is_other_platform('System/Library/Templates/Data/private/etc/hosts'))
        self.assertTrue(hosts.is_other_platform('Windows/System32/drivers/etc/hosts'))
        self.assertTrue(hosts.is_other_platform('WINDOWS\\system32\\Drivers\\etc\\hosts'))
        self.assertFalse(hosts.is_other_platform('etc/hosts'))
        self.assertFalse(hosts.is_other_platform('var/lib/docker/overlay2/x/diff/etc/hosts'))
        self.assertFalse(hosts.is_other_platform('home/a/myprivate/etc/hosts'))

    def test_paths(self):
        pattern = hosts.__artifacts_v2__['linuxHostsFile']['paths']
        for member in ('etc/hosts', 'var/lib/docker/overlay2/x/diff/etc/hosts'):
            self.assertTrue(any(fnmatch.fnmatch('x/' + member, p) for p in pattern), member)
        for member in ('etc/hosts.allow', 'etc/hosts.deny', 'etc/cloud/templates/hosts.debian.tmpl'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in pattern), member)

    def test_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            main = write('etc/hosts', b'127.0.0.1 localhost\n# 10.0.0.1 off\n::1 ip6-localhost ip6-loopback # v6\n')
            chroot = write('srv/jail/etc/hosts', b'10.1.2.3\tbox\n')
            mac = write('private/etc/hosts', b'127.0.0.1 localhost\n')
            win = write('Windows/System32/drivers/etc/hosts', b'127.0.0.1 localhost\n')
            folder = os.path.join(root, 'var', 'etc', 'hosts')
            os.makedirs(folder)
            with mock.patch.object(hosts, 'logfunc') as log:
                headers, rows, source = hosts.linuxHostsFile.__wrapped__(
                    FakeContext([win, main, folder, mac, chroot, main], root))
        self.assertEqual(headers, ('Line', 'Address', 'Host Names', 'Comment', 'Source File'))
        self.assertEqual(rows, [(1, '127.0.0.1', 'localhost', '', 'etc/hosts'),
                                (3, '::1', 'ip6-localhost ip6-loopback', 'v6', 'etc/hosts'),
                                (1, '10.1.2.3', 'box', '', 'srv/jail/etc/hosts')])
        self.assertEqual(source.split('\n'), [main, chroot])
        log.assert_called_once_with('Linux Hosts File: 2 macOS or Windows hosts files skipped, reported by '
                                    'their own artifacts')


if __name__ == '__main__':
    unittest.main()
