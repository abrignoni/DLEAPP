"""Pin how the launcher and mimeapps.list artifacts read their files. Every file here is constructed for the test."""
import fnmatch
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxLaunchers as ll
# pylint: enable=wrong-import-position

LAUNCHER = (b'#!/usr/bin/env xdg-open\n[Desktop Entry]\n# Exec=/bin/commented\nType=Application\nName=First\nName[de]=Erste\nName=Second\n'
            b'Exec=/usr/bin/true %f\nMimeType=text/plain;\nNoDisplay=true\nIcon=x\n[Desktop Action a]\nExec=/bin/false\n')
MIMEAPPS = (b'# user defaults\n[Default Applications]\n# text/html=commented.desktop\ntext/plain=a.desktop\nimage/png=b.desktop;c.desktop;\n\n'
            b'[Added Associations]\nx-scheme-handler/dl=d.desktop;\n[Removed Associations]\ntext/html=e.desktop;\n'
            b'[MIME Cache]\ntext/plain=f.desktop;\n')


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        raise ValueError('no seeker')


class HelperTest(unittest.TestCase):
    def test_desktop_file_id(self):
        self.assertEqual(ll.desktop_file_id('home/a/.local/share/applications/x.desktop'), 'x.desktop')
        self.assertEqual(ll.desktop_file_id('home/a/.local/share/applications/foo/bar.desktop'), 'foo-bar.desktop')
        self.assertEqual(ll.desktop_file_id('home/applications/.local/share/applications/foo/bar.desktop'),
                         'foo-bar.desktop')
        self.assertEqual(ll.desktop_file_id('home/a/Desktop/x.desktop'), '')

    def test_launcher_fields(self):
        shown, other = ll.launcher_fields(LAUNCHER)
        self.assertEqual(shown, {'Type': 'Application', 'Name': 'First', 'Exec': '/usr/bin/true %f',
                                 'MimeType': 'text/plain;', 'NoDisplay': 'true'})
        self.assertEqual(other, ['Name=Second', 'Icon=x'])

    def test_paths(self):
        la = ll.__artifacts_v2__['linuxUserLaunchers']['paths']
        ma = ll.__artifacts_v2__['linuxDefaultApplications']['paths']
        for member in ('home/a/.local/share/applications/x.desktop', 'home/a/.local/share/applications/sub/y.desktop',
                       'home/a/Desktop/z.desktop'):
            self.assertTrue(any(fnmatch.fnmatch('x/' + member, p) for p in la), member)
        for member in ('usr/share/applications/x.desktop', 'home/a/.local/share/applications/mimeinfo.cache',
                       'home/a/.local/share/applications/mimeapps.list'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in la), member)
        for member in ('home/a/.config/mimeapps.list', 'home/a/.config/gnome-mimeapps.list',
                       'home/a/.local/share/applications/mimeapps.list', 'etc/xdg/mimeapps.list',
                       'etc/xdg/xdg-ubuntu/mimeapps.list', 'usr/share/applications/gnome-mimeapps.list',
                       'usr/local/share/applications/mimeapps.list', 'usr/share/ubuntu/applications/mimeapps.list'):
            self.assertTrue(any(fnmatch.fnmatch('x/' + member, p) for p in ma), member)
        for member in ('home/a/.config/mimeapps.list.bak', 'usr/share/applications/defaults.list',
                       'home/a/.local/share/applications/mimeinfo.cache'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in ma), member)


class ArtifactTest(unittest.TestCase):
    def test_launchers_and_mimeapps(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            app = write('home/a/.local/share/applications/sub/x.desktop', LAUNCHER)
            desk = write('home/a/Desktop/y.desktop', LAUNCHER)
            empty = write('home/a/.local/share/applications/empty.desktop', b'# nothing\n')
            user = write('home/a/.config/mimeapps.list', MIMEAPPS)
            system = write('usr/share/applications/gnome-mimeapps.list', b'[Default Applications]\ntext/plain=g.desktop\n')
            folder = os.path.join(root, 'home', 'a', '.local', 'share', 'applications')
            with mock.patch.object(ll, 'logfunc') as log:
                headers, rows, source = ll.linuxUserLaunchers.__wrapped__(FakeContext([desk, folder, app, empty], root))
            with mock.patch.object(ll, 'logfunc') as mlog:
                mheaders, mrows, msource = ll.linuxDefaultApplications.__wrapped__(FakeContext([user, system], root))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(names, ['File Modified', 'Location', 'Desktop File ID', 'Name', 'Type', 'Exec', 'Try Exec',
                                 'MIME Types', 'No Display', 'Hidden', 'Other Keys', 'Link Target', 'Source File'])
        self.assertEqual([(r[1], r[2], r[-1]) for r in rows],
                         [('Applications', 'empty.desktop', 'home/a/.local/share/applications/empty.desktop'),
                          ('Applications', 'sub-x.desktop', 'home/a/.local/share/applications/sub/x.desktop'),
                          ('Desktop', '', 'home/a/Desktop/y.desktop')])
        self.assertEqual(rows[1][3:11], ('First', 'Application', '/usr/bin/true %f', '', 'text/plain;', 'true', '',
                                         'Name=Second\nIcon=x'))
        self.assertEqual(source.split('\n'), [empty, app, desk])
        log.assert_called_once_with('User Application Launchers: 1 files with no [Desktop Entry] key, reported with '
                                    'blank keys')
        mnames = [h[0] if isinstance(h, tuple) else h for h in mheaders]
        self.assertEqual(mnames, ['File Modified', 'Scope', 'Desktop', 'Group', 'MIME Type', 'Applications',
                                  'Link Target', 'Line', 'Source File'])
        self.assertEqual([r[1:6] + (r[7],) for r in mrows],
                         [('User', '', 'Default Applications', 'text/plain', 'a.desktop', 4),
                          ('User', '', 'Default Applications', 'image/png', 'b.desktop;c.desktop;', 5),
                          ('User', '', 'Added Associations', 'x-scheme-handler/dl', 'd.desktop;', 8),
                          ('User', '', 'Removed Associations', 'text/html', 'e.desktop;', 10),
                          ('System', 'gnome', 'Default Applications', 'text/plain', 'g.desktop', 2)])
        self.assertEqual(msource.split('\n'), [user, system])
        mlog.assert_called_once_with('Default Applications: 1 lines in other groups, not reported')


if __name__ == '__main__':
    unittest.main()
