"""Pin how the Linux user accounts artifact reads /etc/passwd and /etc/group."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxAccounts
# pylint: enable=wrong-import-position

# Commented-out and NIS lines keep an account's shape, so only the leading character keeps them out.
PASSWD = (b'root:x:0:0:root:/root:/bin/bash\n'
          b'# a comment\n'
          b'#olduser:x:1002:1002::/home/olduser:/bin/bash\n'
          b'+nisuser::0:0:::\n'
          b'-excluded\n'
          b'daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n'
          b'short:x:5\n'
          b'wrongid:x:abc:1::/:/bin/sh\n'
          b'badgid:x:5:abc::/:/bin/sh\n'
          b'six:x:7:7::/home/six\n'
          b'eight:x:8:8::/home/eight:/bin/sh:extra\n'
          b'syslog:x:101:103::/home/syslog:/usr/sbin/nologin\n'
          b'parallels:x:1000:1000:Parallels,,,:/home/parallels:/bin/bash\n'
          b'nopass::1001:1001:caf\xe9:/home/nopass:/bin/sh\n')
GROUP = (b'root:x:0:\n'
         b'daemon:x:1:\n'
         b'other101:x:101:\n'
         b'adm:x:4:syslog,parallels\n'
         b'sudo:x:27:parallels\n'
         b'syslog:x:103:\n'
         b'#oldgroup:x:1000:parallels\n'
         b'parallels:x:1000:\n'
         b'broken:x:notanumber:parallels\n')


class ParseTest(unittest.TestCase):
    def test_account_lines_and_the_lines_left_out(self):
        records, counts = linuxAccounts.passwd_records(PASSWD)
        self.assertEqual([r[0] for r in records], ['root', 'daemon', 'syslog', 'parallels', 'nopass'])
        self.assertEqual(counts, {'passwd lines beginning with #, + or -, not reported': 4,
                                  'passwd lines that are not seven fields with a numeric UID and GID, not reported': 5})

    def test_an_empty_password_field_is_kept_as_stored(self):
        records, _counts = linuxAccounts.passwd_records(PASSWD)
        self.assertEqual(records[-1][1], '')

    def test_crlf_line_ends_are_not_part_of_the_shell(self):
        records, _counts = linuxAccounts.passwd_records(PASSWD.replace(b'\n', b'\r\n'))
        self.assertEqual([r[6] for r in records],
                         ['/bin/bash', '/usr/sbin/nologin', '/usr/sbin/nologin', '/bin/bash', '/bin/sh'])

    def test_text_that_is_not_utf8_shows_the_replacement_character(self):
        records, _counts = linuxAccounts.passwd_records(PASSWD)
        self.assertEqual(records[-1][4], 'caf\ufffd')

    def test_group_lines(self):
        self.assertEqual(linuxAccounts.group_records(GROUP),
                         [('root', 0, []), ('daemon', 1, []), ('other101', 101, []), ('adm', 4, ['syslog', 'parallels']),
                          ('sudo', 27, ['parallels']), ('syslog', 103, []), ('parallels', 1000, [])])

    def test_only_a_private_etc_folder_is_macos(self):
        self.assertTrue(linuxAccounts._in_private_etc('x/private/etc/passwd'))  # pylint: disable=protected-access
        self.assertTrue(linuxAccounts._in_private_etc(  # pylint: disable=protected-access
            'System/Library/Templates/Data/private/etc/passwd'))
        self.assertFalse(linuxAccounts._in_private_etc('x/etc/passwd'))  # pylint: disable=protected-access
        self.assertFalse(linuxAccounts._in_private_etc('private/x/etc/passwd'))  # pylint: disable=protected-access


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def write(root, relative, data):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return path


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, members):
        with tempfile.TemporaryDirectory() as root:
            files = [write(root, relative, data) for relative, data in members]
            with mock.patch.object(linuxAccounts, 'logfunc') as log_lines:
                _headers, rows, source = linuxAccounts.linuxUserAccounts.__wrapped__(FakeContext(files, root))
            source = [os.path.relpath(path, root) for path in source.split('\n')] if source else []
        return rows, source, log_lines

    def test_accounts_carry_their_group_names_and_source(self):
        rows, source, _log = self.run_artifact([('etc/passwd', PASSWD), ('etc/group', GROUP)])
        self.assertEqual(rows[3], ('parallels', 1000, 1000, 'parallels', 'adm, sudo', 'Parallels,,,',
                                   '/home/parallels', '/bin/bash', 'x', os.path.join('etc', 'passwd')))
        self.assertEqual([row[:5] for row in rows[:3]], [('root', 0, 0, 'root', ''), ('daemon', 1, 1, 'daemon', ''),
                                                         ('syslog', 101, 103, 'syslog', 'adm')])
        self.assertEqual(rows[4][3], '')
        self.assertEqual(source, [os.path.join('etc', 'passwd'), os.path.join('etc', 'group')])

    def test_each_system_in_an_image_is_read_and_named(self):
        layer = os.path.join('var', 'lib', 'docker', 'overlay2', 'abc', 'diff', 'etc')
        # Handed over out of order; the rows still come file by file in path order.
        rows, _source, _log = self.run_artifact([(os.path.join(layer, 'passwd'), b'app:x:10001:10001::/app:/bin/sh\n'),
                                                 ('etc/group', GROUP), ('etc/passwd', PASSWD)])
        self.assertEqual([(row[0], row[-1]) for row in rows if row[0] in ('app', 'root')],
                         [('root', os.path.join('etc', 'passwd')), ('app', os.path.join(layer, 'passwd'))])

    def test_a_passwd_file_in_private_etc_is_not_read(self):
        rows, source, log = self.run_artifact([('private/etc/passwd', PASSWD), ('private/etc/group', GROUP)])
        self.assertEqual((rows, source), ([], []))
        self.assertIn('1 passwd files in a private/etc folder (macOS), not read', log.call_args.args[0])

    def test_no_group_file_leaves_the_group_names_blank_and_says_so(self):
        rows, source, log = self.run_artifact([('etc/passwd', PASSWD)])
        self.assertEqual({(row[3], row[4]) for row in rows}, {('', '')})
        self.assertEqual(source, [os.path.join('etc', 'passwd')])
        self.assertIn('1 passwd files with no group file beside them', log.call_args.args[0])

    def test_groups_sharing_a_gid_are_all_named(self):
        rows, _source, _log = self.run_artifact([('etc/passwd', PASSWD),
                                                 ('etc/group', GROUP + b'alsozero:x:0:\n')])
        self.assertEqual(rows[0][3], 'root, alsozero')


if __name__ == '__main__':
    unittest.main()
