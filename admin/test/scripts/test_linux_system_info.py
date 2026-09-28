"""Pin how the Linux System Information artifact reads os-release, host name, machine ID and time zone files."""
import io
import os
import pathlib
import struct
import sys
import tarfile
import tempfile
import unittest
import zipfile
from collections import Counter
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxSystemInfo
# pylint: enable=wrong-import-position


def tzif(version, footer):
    """TZif data with one UTC time type and no transitions, in RFC 9636's layout."""
    counts = struct.pack('>6L', 0, 0, 0, 0, 1, 4)
    header = b'TZif' + version + b'\0' * 15 + counts
    block = struct.pack('>lBB', 0, 0, 0) + b'UTC\0'
    if version == b'\0':
        return header + block
    return header + block + header + block + footer


def tzif_full(footer):
    """Version 2 TZif data in which every count is above zero: 2 UT/local and 2 standard/wall indicators, 1 leap
    second, 3 transitions, 2 time types and 8 designation characters, so each block has a size of its own."""
    header = b'TZif2' + b'\0' * 15 + struct.pack('>6L', 2, 2, 1, 3, 2, 8)
    types = struct.pack('>lBB', 3600, 0, 0) + struct.pack('>lBB', 7200, 1, 4) + b'CET\0CEST'
    v1 = struct.pack('>3l', 1, 2, 3) + bytes([0, 1, 0]) + types + struct.pack('>2l', 5, 1) + b'\1\0' + b'\1\0'
    v2 = struct.pack('>3q', 1, 2, 3) + bytes([0, 1, 0]) + types + struct.pack('>ql', 5, 1) + b'\1\0' + b'\1\0'
    return header + v1 + header + v2 + footer


class ShellWordTest(unittest.TestCase):
    def test_values_as_a_posix_shell_reads_them(self):
        # Each expected value is what /bin/sh printed for `eval "X=<raw>"; printf '[%s]' "$X"`.
        cases = {
            'ubuntu': 'ubuntu',
            '"Ubuntu 26.04 LTS"': 'Ubuntu 26.04 LTS',
            "'single quoted'": 'single quoted',
            '"a\\$b\\`c\\"d\\\\e\\nf"': 'a$b`c"d\\e\\nf',
            '""': '',
            '': '',
            'a"b c"d': 'ab cd',
            'x # comment': 'x',
            'a\\ b': 'a b',
            "'it'\\''s'": "it's",
            '"tab\tin"': 'tab\tin',
            'caf\\é': 'café',
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(linuxSystemInfo.shell_word(raw), expected)

    def test_values_a_shell_would_expand_or_split(self):
        for raw in ('$HOME', '"$HOME"', '`id`', '"`id`"', 'foo bar', 'a;b', 'a|b', 'a&b', 'a<b', 'a>b', '(a)',
                    '"unterminated', "'unterminated", 'trailing\\'):
            with self.subTest(raw=raw):
                self.assertIsNone(linuxSystemInfo.shell_word(raw))


class ReadersTest(unittest.TestCase):
    def test_assignments_in_file_order_with_counts(self):
        counts = Counter()
        text = ('# comment\n\nNAME="Ubuntu"\n  ID=ubuntu  \nexport X=1\nnot an assignment\nPRETTY=$NAME\n'
                'NAME=again\n')
        self.assertEqual(linuxSystemInfo.assignments(text, counts),
                         [('NAME', 'Ubuntu'), ('ID', 'ubuntu'), ('PRETTY', '$NAME'), ('NAME', 'again')])
        self.assertEqual(counts, {'lines that are not variable assignments, not reported': 2,
                                  linuxSystemInfo.NOT_ONE_WORD: 1})
        self.assertEqual(linuxSystemInfo.assignments('name=lower\n_X1=y\n', Counter()),
                         [('name', 'lower'), ('_X1', 'y')])

    def test_first_line(self):
        self.assertEqual(linuxSystemInfo.first_line('# set by the installer\n\n  box-1  \nsecond\n'), 'box-1')
        self.assertIsNone(linuxSystemInfo.first_line('\n# only a comment\n   \n'))
        self.assertIsNone(linuxSystemInfo.first_line(''))

    def test_tzif_rule(self):
        self.assertEqual(linuxSystemInfo.tzif_rule(tzif(b'2', b'\nCET-1CEST,M3.5.0,M10.5.0/3\n')),
                         'CET-1CEST,M3.5.0,M10.5.0/3')
        self.assertEqual(linuxSystemInfo.tzif_rule(tzif(b'3', b'\n\n')), '')
        self.assertEqual(linuxSystemInfo.tzif_rule(tzif(b'\0', b'')), '')
        self.assertIsNone(linuxSystemInfo.tzif_rule(tzif(b'2', b'no footer')))
        self.assertIsNone(linuxSystemInfo.tzif_rule(tzif(b'5', b'\nUTC0\n')))
        self.assertIsNone(linuxSystemInfo.tzif_rule(tzif(b'2', b'\nUTC0')))
        self.assertIsNone(linuxSystemInfo.tzif_rule(tzif(b'2', b'\nUTC0\n')[:60]))
        self.assertIsNone(linuxSystemInfo.tzif_rule(b'/usr/share/zoneinfo/America/New_York'))
        self.assertIsNone(linuxSystemInfo.tzif_rule(b''))
        self.assertEqual(linuxSystemInfo.tzif_rule(tzif_full(b'\nCET-1CEST,M3.5.0,M10.5.0/3\n')),
                         'CET-1CEST,M3.5.0,M10.5.0/3')
        self.assertIsNone(linuxSystemInfo.tzif_rule(b'TZiX' + tzif(b'2', b'\nUTC0\n')[4:]))
        second = tzif(b'2', b'\nUTC0\n')
        self.assertIsNone(linuxSystemInfo.tzif_rule(second[:54] + b'TZiX' + second[58:]))
        self.assertIsNone(linuxSystemInfo.tzif_rule(tzif(b'2', b'XUTC0\n')))

    def test_which_file_a_path_is(self):
        self.assertEqual(linuxSystemInfo.file_kind('etc/hostname')[1:], ('Host name', 'line'))
        self.assertEqual(linuxSystemInfo.file_kind('lba0/etc/hostname')[1:], ('Host name', 'line'))
        self.assertEqual(linuxSystemInfo.file_kind('lba0\\etc\\localtime')[1:], ('Time zone', 'localtime'))
        self.assertIsNone(linuxSystemInfo.file_kind('lba0/notetc/hostname'))
        self.assertIsNone(linuxSystemInfo.file_kind('etc/hostname.bak'))


class FakeContext:
    def __init__(self, files, root, seeker):
        self.files = files
        self.root = root
        self.seeker = seeker

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)

    def get_seeker(self):
        return self.seeker


def staged(root, name, data):
    path = os.path.join(root, *name.split('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return path


def run_tar(members):
    with tempfile.TemporaryDirectory() as root:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as archive:
            for name, data, link, mtime in members:
                info = tarfile.TarInfo(name)
                info.mtime = mtime
                if link is not None:
                    info.type = tarfile.SYMTYPE
                    info.linkname = link
                    archive.addfile(info)
                else:
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
        buffer.seek(0)
        archive = tarfile.open(fileobj=buffer, mode='r')
        data_folder = os.path.join(root, 'data')
        infos = {}
        files = []
        for name, data, link, mtime in members:
            path = staged(data_folder, name, b'' if link is not None else data)
            infos[path] = SimpleNamespace(source_path=name, modification_date=mtime)
            files.append(path)
        files.append(os.path.join(data_folder, 'etc'))
        seeker = SimpleNamespace(tar_file=archive, file_infos=infos)
        with mock.patch.object(linuxSystemInfo, 'logfunc') as log:
            headers, rows, source = linuxSystemInfo.linuxSystemInfo.__wrapped__(
                FakeContext(files, data_folder, seeker))
        archive.close()
        return headers, rows, source, log, data_folder


class ArtifactTest(unittest.TestCase):
    """The artifact on a tar extraction, with the seeker's own records of each member."""

    def test_rows_links_and_order(self):
        t = 1788000000
        members = [
            ('etc/localtime', None, '/usr/share/zoneinfo/America/New_York', t + 9),
            ('etc/timezone', b'America/Los_Angeles\n', None, t + 8),
            ('var/lib/dbus/machine-id', None, '/etc/machine-id', t + 7),
            ('etc/machine-id', b'0123456789abcdef0123456789abcdef\n', None, t + 6),
            ('etc/hostname', b'box-1\n', None, t + 5),
            ('etc/debian_version', b'forky/sid\n', None, t + 4),
            ('etc/lsb-release', b'DISTRIB_ID=Ubuntu\nDISTRIB_DESCRIPTION="Ubuntu 26.04 LTS"\n', None, t + 3),
            ('usr/lib/os-release', b'NAME="Ubuntu"\nVERSION_ID="26.04"\n', None, t + 2),
            ('etc/os-release', None, '../usr/lib/os-release', t + 1),
            ('etc/passwd', b'root:x:0:0::/root:/bin/sh\n', None, t),
        ]
        headers, rows, source, log, data_folder = run_tar(members)
        self.assertEqual(len(headers), len(rows[0]))
        when = lambda s: datetime.fromtimestamp(t + s, timezone.utc)  # noqa: E731
        self.assertEqual(rows, [
            (when(1), 'OS release link', '../usr/lib/os-release', '', os.path.join('etc', 'os-release')),
            (when(2), 'OS release', 'Ubuntu', 'NAME', os.path.join('usr', 'lib', 'os-release')),
            (when(2), 'OS release', '26.04', 'VERSION_ID', os.path.join('usr', 'lib', 'os-release')),
            (when(3), 'LSB release', 'Ubuntu', 'DISTRIB_ID', os.path.join('etc', 'lsb-release')),
            (when(3), 'LSB release', 'Ubuntu 26.04 LTS', 'DISTRIB_DESCRIPTION',
             os.path.join('etc', 'lsb-release')),
            (when(4), 'Debian version', 'forky/sid', '', os.path.join('etc', 'debian_version')),
            (when(5), 'Host name', 'box-1', '', os.path.join('etc', 'hostname')),
            (when(6), 'Machine ID', '0123456789abcdef0123456789abcdef', '', os.path.join('etc', 'machine-id')),
            (when(7), 'Machine ID link', '/etc/machine-id', '', os.path.join('var', 'lib', 'dbus', 'machine-id')),
            (when(8), 'Time zone name', 'America/Los_Angeles', '', os.path.join('etc', 'timezone')),
            (when(9), 'Time zone link', '/usr/share/zoneinfo/America/New_York', '',
             os.path.join('etc', 'localtime')),
            (when(9), 'Time zone the link names', 'America/New_York', '', os.path.join('etc', 'localtime')),
        ])
        self.assertEqual(len(source.split('\n')), 9)
        self.assertNotIn(os.path.join(data_folder, 'etc', 'passwd'), source.split('\n'))
        log.assert_not_called()

    def test_relative_zone_link_tzif_copy_and_counts(self):
        members = [
            ('lba0/etc/localtime', tzif(b'2', b'\nCET-1CEST,M3.5.0,M10.5.0/3\n'), None, 0),
            ('lba1/etc/localtime', None, '../usr/share/zoneinfo/Europe/Paris', 5),
            ('lba2/etc/localtime', None, '/var/db/timezone/zoneinfo/Europe/Paris', 5),
            ('lba3/etc/localtime', b'not tzif', None, 5),
            ('lba4/etc/localtime', tzif(b'\0', b''), None, 5),
            ('lba0/etc/machine-id', b'\n', None, 5),
            ('lba0/etc/hostname', b'# none\n', None, 5),
            ('lba0/etc/os-release', b'NAME=$X\nNot one\n', None, 5),
            ('lba0/etc/lsb-release', b'# only a comment\n\n', None, 5),
        ]
        _headers, rows, source, log, _data_folder = run_tar(members)
        when = datetime.fromtimestamp(5, timezone.utc)
        self.assertEqual(rows, [
            (when, 'OS release', '$X', 'NAME', os.path.join('lba0', 'etc', 'os-release')),
            ('', 'Time zone rule', 'CET-1CEST,M3.5.0,M10.5.0/3', '', os.path.join('lba0', 'etc', 'localtime')),
            (when, 'Time zone link', '../usr/share/zoneinfo/Europe/Paris', '',
             os.path.join('lba1', 'etc', 'localtime')),
            (when, 'Time zone the link names', 'Europe/Paris', '', os.path.join('lba1', 'etc', 'localtime')),
            (when, 'Time zone link', '/var/db/timezone/zoneinfo/Europe/Paris', '',
             os.path.join('lba2', 'etc', 'localtime')),
        ])
        self.assertEqual(len(source.split('\n')), 4)
        self.assertEqual(log.call_args.args[0], 'Linux System Information: '
                                                '1 TZif files with no TZ string in a footer, not reported, '
                                                '3 files with no line of text, not reported, '
                                                '1 lines that are not variable assignments, not reported, '
                                                '1 localtime files that are neither a recorded link nor TZif data, '
                                                'not reported, '
                                                '1 values that are not one plain shell word, reported as written')


class NoRecordContext(FakeContext):
    def get_seeker(self):
        raise ValueError('no seeker set')


class EdgesTest(unittest.TestCase):
    def test_a_bare_zoneinfo_link_names_no_zone(self):
        rows = run_tar([('etc/localtime', None, '/usr/share/zoneinfo/', 7)])[1]
        self.assertEqual([row[1:3] for row in rows], [('Time zone link', '/usr/share/zoneinfo/')])

    def test_what_the_seeker_cannot_say_is_read_as_content(self):
        with tempfile.TemporaryDirectory() as root:
            path = staged(root, 'etc/hostname', b'box-2\n')
            unreadable = os.path.join(root, 'lba1', 'etc', 'timezone')
            os.makedirs(unreadable)
            for context in (NoRecordContext([path, unreadable], root, None),
                            FakeContext([path, unreadable], root, SimpleNamespace(tar_file=object(), file_infos={}))):
                with self.subTest(context=type(context).__name__), \
                        mock.patch.object(linuxSystemInfo, 'logfunc') as log:
                    _headers, rows, source = linuxSystemInfo.linuxSystemInfo.__wrapped__(context)
                    self.assertEqual(rows, [('', 'Host name', 'box-2', '', os.path.join('etc', 'hostname'))])
                    self.assertEqual(source, path)
                    self.assertEqual(log.call_args.args[0], 'Linux System Information: 1 files that could not be read')


    def test_a_recorded_time_out_of_range_is_left_blank(self):
        with tempfile.TemporaryDirectory() as root:
            path = staged(root, 'etc/hostname', b'box-3\n')
            info = SimpleNamespace(source_path='etc/hostname', modification_date=1e20)
            seeker = SimpleNamespace(file_infos={path: info})
            _headers, rows, _source = linuxSystemInfo.linuxSystemInfo.__wrapped__(FakeContext([path], root, seeker))
        self.assertEqual(rows, [('', 'Host name', 'box-3', '', os.path.join('etc', 'hostname'))])


class OtherSeekersTest(unittest.TestCase):
    def test_a_zip_link_is_reported_as_a_link(self):
        with tempfile.TemporaryDirectory() as root:
            archive_path = os.path.join(root, 'x.zip')
            with zipfile.ZipFile(archive_path, 'w') as archive:
                link = zipfile.ZipInfo('etc/localtime')
                link.external_attr = (0o120777 << 16)
                archive.writestr(link, '/usr/share/zoneinfo/Etc/UTC')
                archive.writestr('etc/timezone', 'Etc/UTC\n')
            data_folder = os.path.join(root, 'data')
            files = [staged(data_folder, 'etc/localtime', b'/usr/share/zoneinfo/Etc/UTC'),
                     staged(data_folder, 'etc/timezone', b'Etc/UTC\n')]
            with zipfile.ZipFile(archive_path) as archive:
                seeker = SimpleNamespace(zip_file=archive, file_infos={
                    files[0]: SimpleNamespace(source_path='etc/localtime', modification_date=0),
                    files[1]: SimpleNamespace(source_path='etc/timezone', modification_date=None)})
                _headers, rows, _source = linuxSystemInfo.linuxSystemInfo.__wrapped__(
                    FakeContext(files, data_folder, seeker))
        self.assertEqual([row[1:4] for row in rows], [('Time zone name', 'Etc/UTC', ''),
                                                      ('Time zone link', '/usr/share/zoneinfo/Etc/UTC', ''),
                                                      ('Time zone the link names', 'Etc/UTC', '')])
        self.assertEqual({row[0] for row in rows}, {''})

    def test_a_folder_link_is_not_followed(self):
        with tempfile.TemporaryDirectory() as root:
            evidence = os.path.join(root, 'evidence')
            os.makedirs(os.path.join(evidence, 'etc'))
            outside = staged(root, 'outside/machine-id', b'ffffffffffffffffffffffffffffffff\n')
            try:
                os.symlink(outside, os.path.join(evidence, 'etc', 'machine-id'))
            except (OSError, NotImplementedError):
                self.skipTest('this platform cannot make a symbolic link here')
            if os.utime in os.supports_follow_symlinks:
                os.utime(os.path.join(evidence, 'etc', 'machine-id'), (1000, 1000), follow_symlinks=False)
            staged(evidence, 'etc/hostname', b'box-4\n')
            data_folder = os.path.join(root, 'data')
            copy = staged(data_folder, 'etc/machine-id', b'ffffffffffffffffffffffffffffffff\n')
            host = staged(data_folder, 'etc/hostname', b'box-4\n')
            seeker = SimpleNamespace(directory=evidence, data_folder=data_folder, file_infos={
                copy: SimpleNamespace(source_path='etc/machine-id', modification_date=2000.0),
                host: SimpleNamespace(source_path='etc/hostname', modification_date=3000.0)})
            _headers, rows, _source = linuxSystemInfo.linuxSystemInfo.__wrapped__(
                FakeContext([copy, host], data_folder, seeker))
            link_time = os.lstat(os.path.join(evidence, 'etc', 'machine-id')).st_mtime
        self.assertEqual(rows, [(datetime.fromtimestamp(3000.0, timezone.utc), 'Host name', 'box-4', '',
                                 os.path.join('etc', 'hostname')),
                                (datetime.fromtimestamp(link_time, timezone.utc), 'Machine ID link', outside, '',
                                 os.path.join('etc', 'machine-id'))])


    def test_a_folder_link_the_seeker_did_not_stage_is_reported(self):
        # The folder seeker stages nothing for a link that resolves outside the input folder; it returns the path
        # and records the link's own times.
        with tempfile.TemporaryDirectory() as root:
            evidence = os.path.join(root, 'evidence')
            os.makedirs(os.path.join(evidence, 'var', 'lib', 'dbus'))
            link = os.path.join(evidence, 'var', 'lib', 'dbus', 'machine-id')
            try:
                os.symlink('/nonexistent-dleapp/machine-id', link)
            except (OSError, NotImplementedError):
                self.skipTest('this platform cannot make a symbolic link here')
            data_folder = os.path.join(root, 'data')
            returned = os.path.join(data_folder, 'var', 'lib', 'dbus', 'machine-id')
            stat = os.lstat(link)
            seeker = SimpleNamespace(directory=evidence, data_folder=data_folder, file_infos={
                returned: SimpleNamespace(source_path='var/lib/dbus/machine-id', modification_date=stat.st_mtime)})
            with mock.patch.object(linuxSystemInfo, 'logfunc') as log:
                _headers, rows, _source = linuxSystemInfo.linuxSystemInfo.__wrapped__(
                    FakeContext([returned], data_folder, seeker))
            link_time = os.lstat(link).st_mtime
        self.assertEqual(rows, [(datetime.fromtimestamp(link_time, timezone.utc), 'Machine ID link',
                                 '/nonexistent-dleapp/machine-id', '',
                                 os.path.join('var', 'lib', 'dbus', 'machine-id'))])
        log.assert_not_called()

if __name__ == '__main__':
    unittest.main()
