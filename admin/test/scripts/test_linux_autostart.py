"""Pin how the XDG Autostart Entries artifact reads autostart files. Every file here is constructed for the test."""
import fnmatch
import io
import os
import pathlib
import sys
import tarfile
import tempfile
import types
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxAutostart as la
# pylint: enable=wrong-import-position

ENTRY = (b'# comment\n[Desktop Entry]\nType=Application\nName = First\nName[fr]=Premier\nName=Second\n'
         b'Exec=/usr/bin/true a\\sb\nX-GNOME-Autostart-enabled=false\nOnlyShowIn=GNOME;\nComment=c\n'
         b'Hidden=true\nX-GNOME-Autostart-Phase=Initialization\nX-GNOME-HiddenUnderSystemd=true\n'
         b'[Desktop Action x]\nExec=/bin/false\nIcon=i\n')


class HelpersTest(unittest.TestCase):
    def test_desktop_entry(self):
        shown, other = la.desktop_entry(ENTRY)
        self.assertEqual(shown, {'Type': 'Application', 'Name': 'First', 'Exec': '/usr/bin/true a\\sb',
                                 'X-GNOME-Autostart-enabled': 'false', 'OnlyShowIn': 'GNOME;', 'Hidden': 'true',
                                 'X-GNOME-Autostart-Phase': 'Initialization', 'X-GNOME-HiddenUnderSystemd': 'true'})
        self.assertEqual(other, ['Name=Second', 'Comment=c'])
        self.assertEqual(la.desktop_entry(b'Exec=x\n'), ({}, []))
        self.assertEqual(la.desktop_entry(b'[Desktop Entry]\nExec=\xff\n')[0]['Exec'], '\\xff')

    def test_skipped_names(self):
        for name in ('.a.desktop', 'a.desktop~', 'lost+found', 'aquota.user', 'aquota.group', 'a.dpkg-old',
                     'a.rpmnew', 'a.bak', 'a.swp', 'a.new', 'a.old', 'a.ignore', 'a.ucf-dist', 'a.dpkg-remove'):
            self.assertTrue(la.skipped_name(name), name)
        for name in ('a.desktop', 'a', 'a.desktop.x', 'new', 'a.dpkg'):
            self.assertFalse(la.skipped_name(name), name)
        self.assertEqual((la.service_name('a.desktop'), la.service_name('a')), ('a', 'a'))
        for name in ('a', 'a.desktop~', 'a.desktop.bak', 'desktop'):
            self.assertTrue(la.gnome_skipped_name(name), name)
        for name in ('a.desktop', '.a.desktop', 'a.bak.desktop'):
            self.assertFalse(la.gnome_skipped_name(name), name)

    def test_scope(self):
        self.assertEqual(la.scope_of('home/u/.config/autostart/a.desktop'), 'User')
        self.assertEqual(la.scope_of('etc/xdg/autostart/a.desktop'), 'System')
        self.assertEqual(la.scope_of('/etc/xdg/xdg-ubuntu/autostart/a.desktop'), 'System')
        self.assertIsNone(la.scope_of('home/u/.config/autostart/sub/a.desktop'))
        self.assertIsNone(la.scope_of('etc/xdg/autostart/sub/a.desktop'))
        self.assertIsNone(la.scope_of('opt/x/autostart/a.desktop'))
        for folder in ('usr/share/gnome/autostart', 'usr/local/share/gnome/autostart', 'usr/share/ubuntu/gnome/autostart',
                       'var/lib/snapd/desktop/gnome/autostart'):
            self.assertEqual(la.scope_of(folder + '/a.desktop'), 'System (GNOME)', folder)
        self.assertIsNone(la.scope_of('usr/share/gnome/autostart/sub/a.desktop'))

    def test_paths(self):
        patterns = la.__artifacts_v2__['linuxXdgAutostart']['paths']
        for member in ('home/u/.config/autostart/a.desktop', 'root/.config/autostart/noext', 'etc/xdg/autostart/a',
                       'etc/xdg/xdg-ubuntu/autostart/a.desktop', 'usr/share/gnome/autostart/a.desktop',
                       'usr/local/share/gnome/autostart/a', 'usr/share/ubuntu/gnome/autostart/a.desktop',
                       'var/lib/snapd/desktop/gnome/autostart/a.desktop'):
            self.assertEqual(sum(fnmatch.fnmatch('x/' + member, p) for p in patterns), 1, member)


class FakeContext:
    def __init__(self, paths, root, seeker=None):
        self.paths, self.root, self.seeker = paths, root, seeker

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        if self.seeker is None:
            raise ValueError('no seeker')
        return self.seeker


class ArtifactTest(unittest.TestCase):
    def test_rows_links_overrides_and_counts(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            sysfile = write('etc/xdg/autostart/foo.desktop', b'[Desktop Entry]\nType=Application\nExec=/bin/foo\n')
            gnomefile = write('usr/share/gnome/autostart/foo.desktop',
                              b'[Desktop Entry]\nExec=/bin/g\nX-GNOME-Autostart-Phase=Initialization\n')
            userfile = write('home/u/.config/autostart/foo.desktop', b'[Desktop Entry]\nHidden=true\n')
            hidden = write('home/u/.config/autostart/.foo.desktop', b'[Desktop Entry]\nExec=/bin/h\n')
            noext = write('home/u/.config/autostart/foo', b'[Desktop Entry]\nExec=/bin/n\n')
            nested = write('etc/xdg/autostart/sub/x.desktop', b'[Desktop Entry]\n')
            link = write('etc/xdg/autostart/tool.desktop', b'[Desktop Entry]\nExec=/bin/from-staged-bytes\n')
            sysbak = write('etc/xdg/autostart/a.desktop.bak.desktop', b'[Desktop Entry]\nExec=/bin/a\n')
            userbak = write('home/u/.config/autostart/a.desktop.bak', b'[Desktop Entry]\nExec=/bin/b\n')
            regular = (sysfile, gnomefile, userfile, hidden, noext, nested, sysbak, userbak)
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode='w') as tar:
                for member in regular:
                    tar.add(member, arcname=os.path.relpath(member, root).replace(os.sep, '/'))
                info = tarfile.TarInfo('etc/xdg/autostart/tool.desktop')
                info.type, info.linkname = tarfile.SYMTYPE, '/usr/lib/tool/tool.desktop'
                tar.addfile(info)
            buf.seek(0)
            infos = {p: types.SimpleNamespace(source_path=os.path.relpath(p, root).replace(os.sep, '/'),
                                              modification_date=1790808467)
                     for p in regular + (link,)}
            seeker = types.SimpleNamespace(file_infos=infos, tar_file=tarfile.open(fileobj=buf))
            paths = [userfile, noext, sysfile, gnomefile, hidden, link, nested, sysbak, userbak,
                     os.path.join(root, 'etc', 'xdg', 'autostart')]
            with mock.patch.object(la, 'logfunc') as log:
                headers, rows, source = la.linuxXdgAutostart.__wrapped__(FakeContext(paths, root, seeker))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(len(names), 20)
        col = {n: names.index(n) for n in names}
        by = {r[col['Source File']]: {n: r[i] for n, i in col.items()} for r in rows}
        self.assertEqual(sorted(by), ['etc/xdg/autostart/a.desktop.bak.desktop', 'etc/xdg/autostart/foo.desktop',
                                      'etc/xdg/autostart/tool.desktop', 'home/u/.config/autostart/.foo.desktop',
                                      'home/u/.config/autostart/a.desktop.bak', 'home/u/.config/autostart/foo',
                                      'home/u/.config/autostart/foo.desktop', 'usr/share/gnome/autostart/foo.desktop'])
        self.assertEqual([r[col['Source File']] for r in rows], sorted(by))
        skip = {k: (v['Name Skipped by systemd'], v['Name Skipped by GNOME Session']) for k, v in by.items()}
        self.assertEqual(skip, {'etc/xdg/autostart/a.desktop.bak.desktop': ('', ''),
                                'etc/xdg/autostart/foo.desktop': ('', ''), 'etc/xdg/autostart/tool.desktop': ('', ''),
                                'home/u/.config/autostart/.foo.desktop': ('yes', ''),
                                'home/u/.config/autostart/a.desktop.bak': ('yes', 'yes'),
                                'home/u/.config/autostart/foo': ('', 'yes'),
                                'home/u/.config/autostart/foo.desktop': ('', ''),
                                'usr/share/gnome/autostart/foo.desktop': ('', '')})
        same = {k: v['Same-Name Entry'] for k, v in by.items()}
        self.assertEqual(same['etc/xdg/autostart/foo.desktop'], 'home/u/.config/autostart/foo\n'
                         'home/u/.config/autostart/foo.desktop\nusr/share/gnome/autostart/foo.desktop')
        self.assertEqual(same['home/u/.config/autostart/foo.desktop'],
                         'etc/xdg/autostart/foo.desktop\nusr/share/gnome/autostart/foo.desktop')
        self.assertEqual(same['usr/share/gnome/autostart/foo.desktop'], 'etc/xdg/autostart/foo.desktop\n'
                         'home/u/.config/autostart/foo\nhome/u/.config/autostart/foo.desktop')
        self.assertEqual(same['etc/xdg/autostart/a.desktop.bak.desktop'], 'home/u/.config/autostart/a.desktop.bak')
        self.assertEqual(same['home/u/.config/autostart/a.desktop.bak'], 'etc/xdg/autostart/a.desktop.bak.desktop')
        self.assertEqual(same['home/u/.config/autostart/.foo.desktop'], '')
        gnome = by['usr/share/gnome/autostart/foo.desktop']
        self.assertEqual((gnome['Scope'], gnome['GNOME Autostart Phase'], gnome['Exec']),
                         ('System (GNOME)', 'Initialization', '/bin/g'))
        self.assertEqual(by['home/u/.config/autostart/foo.desktop']['Hidden'], 'true')
        tool = by['etc/xdg/autostart/tool.desktop']
        self.assertEqual((tool['Link Target'], tool['Exec'], tool['Scope']), ('/usr/lib/tool/tool.desktop', '', 'System'))
        self.assertEqual(tool['File Modified'], datetime.fromtimestamp(1790808467, timezone.utc))
        self.assertEqual(by['home/u/.config/autostart/foo']['Exec'], '/bin/n')
        self.assertNotIn(nested, source.split('\n'))
        self.assertEqual(len(source.split('\n')), 8)
        log.assert_called_once_with('XDG Autostart Entries: 1 files in folders below an autostart folder, which are '
                                    'not read')

if __name__ == '__main__':
    unittest.main()
