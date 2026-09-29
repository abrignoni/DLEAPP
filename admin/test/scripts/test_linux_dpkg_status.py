"""Pin the Package Status (dpkg) artifact (scripts/artifacts/linuxDpkgStatus.py).

KNOWN_STATUS is the status file dpkg 1.23.7 wrote on the lab VM for the known steps of ubuntu2604_arm64_packages
(dpkg run as the user with --root and --force-not-root): a held package upgraded to 2.0 whose file list another
package took over part of, a removed package keeping its conffile, a Multi-Arch: same package, a package unpacked and
not configured, and one with a UTF-8 description. KNOWN_LISTS holds the modification times the capture recorded for
their file lists, and KNOWN_QUERY what dpkg-query printed for that database on the VM.
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
from scripts.artifacts import linuxDpkgStatus as ds
# pylint: enable=wrong-import-position

KNOWN_STATUS = (
    'Package: dleapp-known-a\nStatus: hold ok installed\nPriority: optional\nSection: misc\nInstalled-Size: 13\n'
    'Maintainer: DLEAPP Known Data <known@example.invalid>\nArchitecture: all\nSource: dleapp-known-src (1.9)\n'
    'Version: 2.0\nDescription: DLEAPP known package a\n Second line of the description.\n .\n After an empty line.\n'
    '\n'
    'Package: dleapp-known-b\nStatus: deinstall ok config-files\nPriority: optional\nSection: admin\n'
    'Maintainer: DLEAPP Known Data <known@example.invalid>\nArchitecture: all\nVersion: 1.0\nConfig-Version: 1.0\n'
    'Conffiles:\n /etc/dleapp-known/b.conf 6bc5aa55a24a9d663f97616fed018e1a\n'
    'Description: DLEAPP known package dleapp-known-b\n'
    '\n'
    'Package: dleapp-known-d\nStatus: install ok installed\nSection: libs\n'
    'Maintainer: DLEAPP Known Data <known@example.invalid>\nArchitecture: arm64\nMulti-Arch: same\nVersion: 1.0\n'
    'Description: DLEAPP known package dleapp-known-d\n'
    '\n'
    'Package: dleapp-known-e\nStatus: install ok installed\nMaintainer: DLEAPP Known Data <known@example.invalid>\n'
    'Architecture: all\nVersion: 1.0\nReplaces: dleapp-known-a\nDescription: DLEAPP known package dleapp-known-e\n'
    '\n'
    'Package: dleapp-known-f\nStatus: install ok unpacked\nMaintainer: DLEAPP Known Data <known@example.invalid>\n'
    'Architecture: all\nVersion: 1.0\nDescription: DLEAPP known package f, unpacked and not configured\n'
    '\n'
    'Package: dleapp-known-g\nStatus: install ok installed\nMaintainer: DLEAPP Known Data <known@example.invalid>\n'
    'Architecture: all\nVersion: 1.0\nDescription: Paquete de datos conocidos: café\n\n')
KNOWN_LISTS = {'dleapp-known-a.list': 1790649577, 'dleapp-known-b.list': 1790649579,
               'dleapp-known-d:arm64.list': 1790649573, 'dleapp-known-e.list': 1790649577,
               'dleapp-known-f.list': 1790649585, 'dleapp-known-g.list': 1790649587}
KNOWN_QUERY = [('dleapp-known-a', '2.0', 'all', 'hold ok installed'),
               ('dleapp-known-b', '1.0', 'all', 'deinstall ok config-files'),
               ('dleapp-known-d', '1.0', 'arm64', 'install ok installed'),
               ('dleapp-known-e', '1.0', 'all', 'install ok installed'),
               ('dleapp-known-f', '1.0', 'all', 'install ok unpacked'),
               ('dleapp-known-g', '1.0', 'all', 'install ok installed')]


class FileInfo:
    def __init__(self, source_path, modification_date):
        self.source_path, self.modification_date = source_path, modification_date


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


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


class StanzaTest(unittest.TestCase):
    def test_fields_continuations_and_case(self):
        found, counts = ds.stanzas(b'package: x\nDescription: one\n two\n .\n\nPackage: y\n\n\n')
        self.assertEqual(found, [{'package': 'x', 'description': 'one\ntwo\n.'}, {'package': 'y'}])
        self.assertEqual(counts, {})

    def test_only_an_empty_line_ends_a_stanza(self):
        found, _counts = ds.stanzas(b'Package: x\nDescription: one\n \n more\nVersion: 1\n')
        self.assertEqual(found, [{'package': 'x', 'description': 'one\n\nmore', 'version': '1'}])

    def test_every_dpkg_space_starts_a_continuation(self):
        for space in ' \t\v\f\r':
            with self.subTest(space=repr(space)):
                found, _counts = ds.stanzas(f'Package: x\nDescription: a\n{space}b\n'.encode())
                self.assertEqual(found[0]['description'], 'a\nb')

    def test_value_spacing_and_crlf(self):
        found, _counts = ds.stanzas(b'Package :  x  \r\nVersion:1\r\n')
        self.assertEqual(found, [{'package': 'x', 'version': '1'}])

    def test_lines_that_are_not_fields_are_counted(self):
        found, counts = ds.stanzas(b' orphan\nno colon here\nPack age: x\n continued\nPackage: y\n:empty name\n')
        self.assertEqual(found, [{'package': 'y'}])
        self.assertEqual(counts, {'continuation lines with no field before them, not read': 2,
                                  'lines that are not a field, not read': 3})

    def test_file_without_final_newline(self):
        self.assertEqual(ds.stanzas(b'Package: x\nVersion: 1')[0], [{'package': 'x', 'version': '1'}])

    def test_bytes_that_are_not_utf8(self):
        self.assertEqual(ds.stanzas(b'Package: x\nMaintainer: \xff\n')[0], [{'package': 'x', 'maintainer': '�'}])


class MarkTest(unittest.TestCase):
    def test_marks(self):
        marks = ds.auto_marks(b'Package: a\nArchitecture: arm64\nAuto-Installed: 1\n\n'
                              b'Package: b\nArchitecture: arm64\nAuto-Installed: 0\n\n'
                              b'Package: c\nAuto-Installed: 1\n\n'
                              b'Package: d\nArchitecture: arm64\nAuto-Installed: 2\n\n'
                              b'Package: e\nArchitecture: arm64\n\n'
                              b'Architecture: arm64\nAuto-Installed: 1\n\n')
        self.assertEqual(marks, {('a', 'arm64'), ('c', None), ('d', 'arm64')})

    def test_architecture_matching(self):
        marks = {('a', 'arm64'), ('c', None)}
        self.assertTrue(ds.is_auto(marks, 'a', 'arm64'))
        self.assertFalse(ds.is_auto(marks, 'a', 'i386'))
        self.assertTrue(ds.is_auto(marks, 'a', 'all'))
        self.assertTrue(ds.is_auto(marks, 'c', 'i386'))
        self.assertFalse(ds.is_auto(marks, 'b', 'all'))


class ListNameTest(unittest.TestCase):
    def test_names(self):
        same = {'package': 'libx', 'architecture': 'arm64', 'multi-arch': 'same'}
        foreign = {'package': 'tool', 'architecture': 'arm64', 'multi-arch': 'foreign'}
        self.assertEqual(ds.list_names(same, True), ['libx:arm64.list'])
        self.assertEqual(ds.list_names(same, False), ['libx.list'])
        self.assertEqual(ds.list_names(same, None), ['libx.list', 'libx:arm64.list'])
        self.assertEqual(ds.list_names(foreign, True), ['tool.list'])


class ArtifactTest(unittest.TestCase):
    """Two databases: the known one dpkg wrote, staged the way the tar seeker stages it (a : in a name becomes _
    and the recorded source path keeps it), and a hand-written one in a legacy-format database with apt marks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.seeker = Seeker()
        self.logged = []
        patcher = mock.patch.object(ds, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = []
        self.add('known/var/lib/dpkg/status', KNOWN_STATUS.encode())
        self.add('known/var/lib/dpkg/info/format', b'1\n')
        self.paths.append(os.path.join(self.root, 'known', 'var', 'lib', 'dpkg', 'info'))
        os.makedirs(self.paths[-1], exist_ok=True)
        for name, when in KNOWN_LISTS.items():
            self.add(f'known/var/lib/dpkg/info/{name}', b'/.\n', when)
        self.add('old/var/lib/dpkg/status',
                 b'Package: libold\nStatus: install ok installed\nArchitecture: i386\nMulti-Arch: same\nVersion: 1\n'
                 b'Installed-Size: 3x\nDescription: legacy\n\n'
                 b'Package: tool\nStatus: install ok installed\nArchitecture: all\nVersion: 2\nInstalled-Size: 40\n\n'
                 b'Package: gone\nStatus: purge ok not-installed\nArchitecture: i386\n\n'
                 b'Package: kept\nStatus: deinstall ok config-files\nArchitecture: i386\nVersion: 3\n\n'
                 b'Status: install ok installed\nVersion: 9\n\n')
        self.add('old/var/lib/dpkg/info/libold.list', b'/.\n', 1295338628)
        self.add('old/var/lib/dpkg/info/tool.list', b'/.\n')
        self.add('old/var/lib/dpkg/info/kept.list', b'/.\n', 1295338000)
        self.add('old/var/lib/apt/extended_states',
                 b'Package: tool\nArchitecture: i386\nAuto-Installed: 1\n\nPackage: kept\nAuto-Installed: 1\n\n')

    def add(self, source, data, when=None):
        staged = os.path.join(self.root, *source.replace(':', '_').split('/'))
        os.makedirs(os.path.dirname(staged), exist_ok=True)
        with open(staged, 'wb') as handle:
            handle.write(data)
        self.paths.append(staged)
        if when is not None:
            self.seeker.file_infos[staged] = FileInfo(source, when)
        return staged

    def tearDown(self):
        self.tmp.cleanup()

    def run_artifact(self, paths=None):
        return ds.dpkgPackageStatus.__wrapped__(FakeContext(paths or self.paths, self.root, self.seeker))

    def test_known_database(self):
        _headers, rows, _source = self.run_artifact()
        known = [row for row in rows if row[-1] == 'known/var/lib/dpkg/status']
        self.assertEqual([row[1:5] for row in known], KNOWN_QUERY)
        times = {row[1]: row[0] for row in known}
        self.assertEqual(times, {'dleapp-known-a': utc(1790649577), 'dleapp-known-b': utc(1790649579),
                                 'dleapp-known-d': utc(1790649573), 'dleapp-known-e': utc(1790649577),
                                 'dleapp-known-f': utc(1790649585), 'dleapp-known-g': utc(1790649587)})
        a = known[0]
        self.assertEqual(a[6:12], ('misc', 'optional', 13, 'dleapp-known-src (1.9)',
                                   'DLEAPP Known Data <known@example.invalid>', 'DLEAPP known package a'))
        self.assertEqual({row[5] for row in known}, {''})
        self.assertEqual(known[-1][11], 'Paquete de datos conocidos: café')

    def test_legacy_database_and_apt_marks(self):
        _headers, rows, _source = self.run_artifact()
        old = {row[1]: row for row in rows if row[-1] == 'old/var/lib/dpkg/status'}
        self.assertEqual(list(old), ['libold', 'tool', 'gone', 'kept'])
        self.assertEqual(old['libold'][0], utc(1295338628))
        self.assertEqual(old['libold'][8], '3x')
        self.assertEqual(old['tool'][8], 40)
        self.assertEqual(old['tool'][0], '')
        self.assertEqual({name: row[5] for name, row in old.items()},
                         {'libold': 'No', 'tool': 'Yes', 'gone': '', 'kept': ''})
        self.assertEqual(old['kept'][0], utc(1295338000))

    def test_headers_and_sources(self):
        headers, rows, source = self.run_artifact()
        self.assertEqual(headers[0], ('File List Written (UTC)', 'datetime'))
        self.assertEqual(headers[1:], ('Package', 'Version', 'Architecture', 'Status', 'Automatically Installed (apt)',
                                       'Section', 'Priority', 'Installed Size (KiB)', 'Source Package', 'Maintainer',
                                       'Description', 'Source File'))
        self.assertEqual([row[-1] for row in rows], ['known/var/lib/dpkg/status'] * 6 + ['old/var/lib/dpkg/status'] * 4)
        self.assertEqual(source.split('\n'), [os.path.join(self.root, 'known', 'var', 'lib', 'dpkg', 'status'),
                                              os.path.join(self.root, 'old', 'var', 'lib', 'dpkg', 'status'),
                                              os.path.join(self.root, 'old', 'var', 'lib', 'apt', 'extended_states')])

    def test_counts_in_the_run_log(self):
        self.run_artifact()
        self.assertEqual(self.logged, ['Package Status (dpkg): 1 packages with no file list found, '
                                       '1 stanzas with no Package field, not reported'])

    def test_a_status_file_only_by_its_path(self):
        stray = self.add('notes/status', b'Package: x\nStatus: install ok installed\n\n')
        _headers, rows, _source = self.run_artifact(self.paths + [stray])
        self.assertNotIn('x', [row[1] for row in rows])

    def test_rows_follow_the_status_file_paths_in_order(self):
        _headers, rows, _source = self.run_artifact(list(reversed(self.paths)))
        self.assertEqual([row[-1] for row in rows], ['known/var/lib/dpkg/status'] * 6 + ['old/var/lib/dpkg/status'] * 4)

    def test_a_folder_named_status_is_passed_over(self):
        folder = os.path.join(self.root, 'dir', 'var', 'lib', 'dpkg', 'status')
        os.makedirs(folder)
        _headers, rows, _source = self.run_artifact(self.paths + [folder])
        self.assertEqual(len(rows), 10)
        self.assertNotIn('could not be read', ''.join(self.logged))

    def test_multiarch_database_does_not_fall_back_to_the_plain_name(self):
        self.add('known/var/lib/dpkg/info/dleapp-known-d.list', b'/.\n', 1)
        _headers, rows, _source = self.run_artifact()
        d = [row for row in rows if row[1] == 'dleapp-known-d']
        self.assertEqual(d[0][0], utc(1790649573))


if __name__ == '__main__':
    unittest.main()
