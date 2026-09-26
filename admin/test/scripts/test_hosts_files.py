"""Pin the hosts file reading in scripts/artifacts/hostsFiles.py."""
import pathlib
import sys
import unittest

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


if __name__ == '__main__':
    unittest.main()
