"""Pin how the Trash (freedesktop) artifact reads .trashinfo files."""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxTrash
# pylint: enable=wrong-import-position


class InfoTest(unittest.TestCase):
    def test_the_first_path_and_date_are_taken(self):
        data = (b'[Trash Info]\nPath=/home/alex/caf%C3%A9%20%C3%A9.txt\nDeletionDate=2026-09-28T07:10:57\n'
                b'Path=/second\nDeletionDate=1999-01-01T00:00:00\nOther=1\n')
        self.assertEqual(linuxTrash.trash_info(data), ('/home/alex/caf%C3%A9%20%C3%A9.txt', '2026-09-28T07:10:57'))

    def test_crlf_and_missing_keys(self):
        self.assertEqual(linuxTrash.trash_info(b'[Trash Info]\r\nPath=a%25b\r\n'), ('a%25b', ''))
        self.assertEqual(linuxTrash.trash_info(b'[Trash Info]\n'), ('', ''))

    def test_a_file_that_does_not_open_with_the_header_is_none(self):
        self.assertIsNone(linuxTrash.trash_info(b'Path=/x\n[Trash Info]\n'))
        self.assertIsNone(linuxTrash.trash_info(b''))

    def test_space_around_the_header_and_bytes_that_are_not_utf8(self):
        self.assertEqual(linuxTrash.trash_info(b'[Trash Info] \nPath=/a\n'), ('/a', ''))
        self.assertEqual(linuxTrash.trash_info(b'[Trash Info]\nPath=/a\xff\n'), ('/a\ufffd', ''))

    def test_the_folder_a_relative_path_starts_from(self):
        self.assertEqual(linuxTrash.relative_base('home/alex/.local/share/Trash'), 'home/alex/.local/share')
        self.assertEqual(linuxTrash.relative_base('media/usb/.Trash-1000'), 'media/usb')
        self.assertEqual(linuxTrash.relative_base('media/usb/.Trash/1000'), 'media/usb')

    def test_a_folder_not_shaped_as_a_trash_folder_has_no_base(self):
        for folder in ('media/usb/.Trash/1000/files/saved', 'home/alex/Trash', 'home/alex/.local/Trash',
                       'home/alex/share/Trash', 'home/alex/.local/other/Trash', 'home/alex/.local/share/Other',
                       'media/usb/.Trash'):
            self.assertIsNone(linuxTrash.relative_base(folder), folder)

    def test_the_trash_folder_and_the_name_in_it(self):
        self.assertEqual(linuxTrash.trash_parts('home/alex/.local/share/Trash/info/plain.2.txt.trashinfo'),
                         ('home/alex/.local/share/Trash', 'plain.2.txt'))
        self.assertEqual(linuxTrash.trash_parts('media/usb/.Trash/1000/info/a.b.trashinfo'),
                         ('media/usb/.Trash/1000', 'a.b'))

    def test_a_file_outside_a_trash_folders_info_folder_has_no_parts(self):
        self.assertIsNone(linuxTrash.trash_parts('media/usb/.Trash-1000/info/sub/x.trashinfo'))
        self.assertIsNone(linuxTrash.trash_parts('media/usb/.Trash/1000/files/saved/info/x.trashinfo'))
        self.assertIsNone(linuxTrash.trash_parts('media/usb/.Trash-1000/files/x.trashinfo'))


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def test_rows_from_home_and_volume_trashes(self):
        with tempfile.TemporaryDirectory() as root:
            files = []
            for folder, name, data in (
                    ('home/alex/.local/share/Trash', 'plain.2.txt',
                     b'[Trash Info]\nPath=/home/alex/sub/plain.txt\nDeletionDate=2026-09-28T07:10:54\n'),
                    ('home/alex/.local/share/Trash', '100%.txt',
                     b'[Trash Info]\nPath=/home/alex/100%25.txt\nDeletionDate=2026-09-28T07:10:58\n'),
                    ('media/usb/.Trash-1000', 'photo.jpg',
                     b'[Trash Info]\nPath=DCIM/photo%20one.jpg\nDeletionDate=2026-09-28T07:11:00\n'),
                    ('media/usb/.Trash/1000', 'bad',
                     b'Path=/nowhere\n'),
                    ('media/usb/.Trash/1000/files/saved', 'copy',
                     b'[Trash Info]\nPath=copy\nDeletionDate=2026-09-28T07:12:00\n'),
                    ('media/usb/.Trash-1000', 'nopath', b'[Trash Info]\nDeletionDate=2026-09-28T07:13:00\n')):
                info = os.path.join(root, folder, 'info')
                os.makedirs(info, exist_ok=True)
                path = os.path.join(info, name + '.trashinfo')
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            files.append(os.path.join(root, 'home/alex/.local/share/Trash/info'))
            files.append(os.path.join(root, 'home/alex/.local/share/Trash/files/plain.2.txt'))
            os.makedirs(os.path.join(root, 'home/alex/.local/share/Trash/info/dir.trashinfo'))
            files.append(os.path.join(root, 'home/alex/.local/share/Trash/info/dir.trashinfo'))
            files.append(os.path.join(root, 'home/alex/.local/share/Trash/info/gone.trashinfo'))
            with mock.patch.object(linuxTrash, 'logfunc') as log:
                headers, rows, source = linuxTrash.linuxTrash.__wrapped__(FakeContext(files, root))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            ('2026-09-28T07:10:58', '/home/alex/100%.txt', '', '/home/alex/100%25.txt', '100%.txt',
             os.path.join('home', 'alex', '.local', 'share', 'Trash')),
            ('2026-09-28T07:10:54', '/home/alex/sub/plain.txt', '', '/home/alex/sub/plain.txt', 'plain.2.txt',
             os.path.join('home', 'alex', '.local', 'share', 'Trash')),
            ('2026-09-28T07:13:00', '', '', '', 'nopath', os.path.join('media', 'usb', '.Trash-1000')),
            ('2026-09-28T07:11:00', 'DCIM/photo one.jpg', os.path.join('media', 'usb'), 'DCIM/photo%20one.jpg', 'photo.jpg',
             os.path.join('media', 'usb', '.Trash-1000'))])
        self.assertEqual(len(source.split('\n')), 4)
        self.assertEqual(log.call_args.args[0], 'Trash (freedesktop): 1 .trashinfo files not in the info folder of '
                                                'a Trash folder, not reported, 1 .trashinfo files whose first line '
                                                'is not [Trash Info], not reported, 1 files that could not be read')

    def test_a_path_that_is_not_utf8_is_shown_with_the_replacement_character(self):
        with tempfile.TemporaryDirectory() as root:
            info = os.path.join(root, 'home', 'alex', '.local', 'share', 'Trash', 'info')
            os.makedirs(info)
            path = os.path.join(info, 'x.trashinfo')
            with open(path, 'wb') as handle:
                handle.write(b'[Trash Info]\nPath=/home/alex/%FF.txt\nDeletionDate=2026-09-28T07:12:00\n')
            _headers, rows, _source = linuxTrash.linuxTrash.__wrapped__(FakeContext([path], root))
        self.assertEqual(rows[0][1], '/home/alex/�.txt')
        self.assertEqual(rows[0][3], '/home/alex/%FF.txt')


if __name__ == '__main__':
    unittest.main()
