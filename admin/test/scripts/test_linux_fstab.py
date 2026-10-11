"""Pin the Filesystem Table (fstab) artifact (scripts/artifacts/linuxFstab.py). The values are made up."""
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxFstab as fstab
# pylint: enable=wrong-import-position

TABLE = (b'# /etc/fstab: static file system information.\n'
         b'#\n'
         b'# <file system> <mount point>   <type>  <options>       <dump>  <pass>\n'
         b'## / was on /dev/sda2 during installation  \n'
         b'UUID=aaaa-bbbb / ext4 defaults,errors=remount-ro 0 1\r\n'
         b'/swap.img\tnone\tswap\tsw\t0\t0\n'
         b'# a comment with a blank line after it\n'
         b'\n'
         b'  \t# an indented comment \xff\n'
         b' //server/share\\040one /mnt/my\\040share\\011x cifs user=me\\054pw,ro\\134 +1 -2 extra\n'
         b'tmpfs /tmp tmpfs\n'
         b'LABEL=lone /mnt/lone\n'
         b'\xffdev /mnt/\\0409 ext\\0604 opt\\08 x 3')


def rows_and_counts(data):
    counts = Counter()
    return fstab.fstab_rows(data, counts), dict(counts)


class Unmangle(unittest.TestCase):
    def test_octal_escapes_only(self):
        self.assertEqual(fstab.unmangle(b'a\\040b\\011c\\134d\\04f\\x20g\\0400h\\089'), 'a b\tc\\d\\04f\\x20g 0h\\089')

    def test_escaped_bytes_form_characters_and_stray_ones_are_shown_as_hex(self):
        self.assertEqual(fstab.unmangle(b'caf\\303\\251 \\777 \xc3\xa9'), 'caf\u00e9 \\xff \u00e9')

    def test_a_zero_byte_ends_the_field(self):
        self.assertEqual(fstab.unmangle(b'seen\\000hidden'), 'seen')
        self.assertEqual(fstab.unmangle(b'seen\\400hidden'), 'seen')


class Rows(unittest.TestCase):
    def test_entries_comments_and_short_lines(self):
        rows, counts = rows_and_counts(TABLE)
        self.assertEqual(rows, [
            ('UUID=aaaa-bbbb', '/', 'ext4', 'defaults,errors=remount-ro', '0', '1',
             '/ was on /dev/sda2 during installation', 5),
            ('/swap.img', 'none', 'swap', 'sw', '0', '0', '', 6),
            ('//server/share one', '/mnt/my share\tx', 'cifs', 'user=me,pw,ro\\', '+1', '-2',
             'an indented comment \\xff', 10),
            ('tmpfs', '/tmp', 'tmpfs', '', '', '', '', 11),
            ('LABEL=lone', '/mnt/lone', '', '', '', '', '', 12),
            ('\\xffdev', '/mnt/ 9', 'ext04', 'opt\\08', 'x', '3', '', 13)])
        self.assertEqual(counts, {fstab.SHORT: 1, fstab.NOT_NUMBER: 1})

    def test_nothing_but_comments(self):
        self.assertEqual(rows_and_counts(b'# one\n\n   \n#two\n\r\n \t\r\n'), ([], {}))
        self.assertEqual(rows_and_counts(b''), ([], {}))

    def test_a_blank_line_drops_the_comment_and_only_four_fields_are_unescaped(self):
        self.assertEqual(rows_and_counts(b'# c\n\na\\040 /b c d \\0601 \\0602\n'),
                         ([('a ', '/b', 'c', 'd', '\\0601', '\\0602', '', 3)], {fstab.NOT_NUMBER: 1}))

    def test_only_spaces_and_tabs_separate_fields(self):
        text = '/dev/x /mnt/a\u3000b\u00a0c\x0cd\x0be\rf ext4 rw 0 0\r\r\n'.encode()
        self.assertEqual(rows_and_counts(text),
                         ([('/dev/x', '/mnt/a\u3000b\u00a0c\x0cd\x0be\rf', 'ext4', 'rw', '0', '0\r', '', 1)],
                          {fstab.NOT_NUMBER: 1}))

    def test_one_field(self):
        self.assertEqual(rows_and_counts(b'#c\nalone'), ([('alone', '', '', '', '', '', 'c', 2)], {fstab.SHORT: 1}))

    def test_numbers(self):
        self.assertEqual(rows_and_counts(b'a b c d 1\na b c d\na b c d 1x 2\na b c d 1 2.0\n')[1], {fstab.NOT_NUMBER: 2})


class Artifact(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write(self, relative, data):
        path = os.path.join(self.folder.name, *relative.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def run_artifact(self, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(fstab, 'logfunc') as log:
            result = fstab.linuxFstab.__wrapped__(context)
        return result, [call.args[0] for call in log.call_args_list]

    def test_files(self):
        first = self.write('a/etc/fstab', TABLE)
        second = self.write('b/etc/fstab', b'/dev/sdb1 /data xfs noauto\nshort /x\n')
        empty = self.write('c/etc/fstab', b'# nothing\n')
        folder = os.path.join(self.folder.name, 'd', 'etc', 'fstab')
        os.makedirs(folder)
        gone = os.path.join(self.folder.name, 'e', 'etc', 'fstab')
        (headers, rows, located), logged = self.run_artifact([second, folder, gone, empty, first])
        self.assertEqual(headers, ('Device', 'Mount Point', 'Type', 'Options', 'Dump', 'Pass', 'Comment Above', 'Line',
                                   'Source File'))
        self.assertEqual([(row[0], row[7], row[8]) for row in rows],
                         [('UUID=aaaa-bbbb', 5, os.path.join('a', 'etc', 'fstab')),
                          ('/swap.img', 6, os.path.join('a', 'etc', 'fstab')),
                          ('//server/share one', 10, os.path.join('a', 'etc', 'fstab')),
                          ('tmpfs', 11, os.path.join('a', 'etc', 'fstab')),
                          ('LABEL=lone', 12, os.path.join('a', 'etc', 'fstab')),
                          ('\\xffdev', 13, os.path.join('a', 'etc', 'fstab')),
                          ('/dev/sdb1', 1, os.path.join('b', 'etc', 'fstab')),
                          ('short', 2, os.path.join('b', 'etc', 'fstab'))])
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(located, first + '\n' + second)
        self.assertEqual(logged, ['Filesystem Table (fstab): 1 ' + fstab.NOT_NUMBER + ', 2 ' + fstab.SHORT
                                  + ', 1 files that could not be read'])

    def test_nothing_found(self):
        (_, rows, located), logged = self.run_artifact([])
        self.assertEqual((rows, located, logged), ([], '', []))


if __name__ == '__main__':
    unittest.main()
