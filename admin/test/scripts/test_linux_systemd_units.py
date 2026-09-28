"""Pin how the systemd unit artifacts sort the entries of unit folders and read unit files and drop-ins. The
expected readings were checked against systemd 259.5 itself: each file in SystemdReadingTest was loaded into a user
manager on a VM and systemctl show printed the Description and load state asserted here."""
import io
import os
import pathlib
import sys
import tarfile
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxSystemdUnits as units
# pylint: enable=wrong-import-position

SVC = b'[Service]\nType=oneshot\nExecStart=/usr/bin/true\n'
LIMIT = units.LONG_LINE_MAX


class NamesTest(unittest.TestCase):
    def test_unit_names(self):
        for name in ('ssh.service', 'getty@.service', 'getty@tty1.service', 'snap-gnome\\x2d46\\x2d2404-154.mount',
                     '.hidden.service', 'a:b_c.d-e.socket', 'x@y@z.timer', 'a' * 247 + '.service'):
            with self.subTest(name=name):
                self.assertTrue(units.unit_name(name))
        for name in ('@x.service', 'x.service.bak', 'README', 'x.foo', '.service', 'a b.service', 'é.service',
                     'a' * 248 + '.service', 'x.service~', ''):
            with self.subTest(name=name):
                self.assertFalse(units.unit_name(name))

    def test_folder_names(self):
        for holder, expected in (('service', True), ('foo-.service', True), ('multi-user.target', True),
                                 ('getty@.service', True), ('bogus', False), ('x.conf', False)):
            with self.subTest(holder=holder):
                self.assertEqual(units.names_units(holder), expected)


class LoadPathTest(unittest.TestCase):
    def test_targets_in_and_out_of_the_load_path(self):
        system, everyone, alice = '/etc/systemd/system', '/etc/systemd/user', '/home/alice/.config/systemd/user'
        cases = [
            ('System', system, '/usr/lib/systemd/system/ssh.service', True),
            ('System', system, '/lib/systemd/system/gdm3.service', True),
            ('System', system, 'ssh.service', True),
            ('System', system, '/etc/systemd/system/../system/ssh.service', True),
            ('System', system, '../ssh.service', False),
            ('System', system, '/opt/ssh.service', False),
            ('System', system, '/usr/lib/systemd/user/ssh.service', False),
            ('System', system, '/libx/systemd/system/a.service', False),
            ('All users', everyone, '/usr/lib/systemd/user/obex.service', True),
            ('All users', everyone, 'obex.service', True),
            ('All users', everyone, '/lib/systemd/user/obex.service', True),
            ('All users', everyone, '/home/alice/.config/systemd/user/x.service', False),
            ('User', alice, '/home/alice/.config/systemd/user/x.service', True),
            ('User', alice, 'x.service', True),
            ('User', alice, '/home/alice/.local/share/systemd/user/x.service', True),
            ('User', alice, '/home/alice/.config/systemd/user.control/x.service', True),
            ('User', alice, '/run/user/1000/systemd/transient/x.service', True),
            ('User', alice, '/usr/lib/systemd/user/x.service', True),
            ('User', alice, '/home/bob/.config/systemd/user/x.service', False),
            ('User', alice, '/tmp/x.service', False),
            ('User', '/fs/home/alice/.config/systemd/user', '/home/alice/.config/systemd/user/x.service', True),
            ('User', '/.config/systemd/user', '/home/zed/.config/systemd/user/x.service', True),
        ]
        for scope, base, target, expected in cases:
            with self.subTest(scope=scope, target=target):
                self.assertEqual(units.in_load_path(scope, base, target), expected)


class EntryKindTest(unittest.TestCase):
    def test_kinds(self):
        system = '/etc/systemd/system'
        cases = [
            ('ssh.service', None, 9, ('ssh.service', 'Unit file', '')),
            ('.hidden.service', None, 9, ('.hidden.service', 'Unit file', '')),
            ('ssh.service', None, 0, ('ssh.service', 'Empty unit file (masked)', '')),
            ('ssh.service', '/dev/null', None, ('ssh.service', 'Masked (link to /dev/null)', '')),
            ('sshd.service', '/usr/lib/systemd/system/ssh.service', None, ('sshd.service', 'Alias link', '')),
            ('x.service', '/opt/x.service', None, ('x.service', 'Linked unit file', '')),
            ('README', None, 9, ('README', 'Other', '')),
            ('x.service.bak', None, 9, ('x.service.bak', 'Other', '')),
            ('x.service.wants', '/srv/wants', None, ('x.service.wants', 'Other', '')),
            ('multi-user.target.wants/ssh.service', '/usr/lib/systemd/system/ssh.service', None,
             ('ssh.service', 'Wants link', 'multi-user.target')),
            ('a.target.requires/b.service', 'b.service', None, ('b.service', 'Requires link', 'a.target')),
            ('a.target.upholds/b.service', 'b.service', None, ('b.service', 'Upholds link', 'a.target')),
            ('service.wants/b.service', 'b.service', None, ('b.service', 'Wants link', 'service')),
            ('a.target.wants/b.service', '/dev/null', None,
             ('b.service', 'Masked dependency (link to /dev/null)', 'a.target')),
            ('a.target.wants/b.service', None, 9, ('b.service', 'Other', '')),
            ('a.target.wants/.b.service', 'b.service', None, ('.b.service', 'Other', '')),
            ('a.target.wants/b.service.bak', 'b.service', None, ('b.service.bak', 'Other', '')),
            ('bogus.wants/b.service', 'b.service', None, ('b.service', 'Other', '')),
            ('ssh.service.d/override.conf', None, 9, ('ssh.service', 'Drop-in', '')),
            ('ssh.service.d/override.conf', None, 0, ('ssh.service', 'Drop-in', '')),
            ('ssh.service.d/extra.conf', '/srv/extra.conf', None, ('ssh.service', 'Drop-in link', '')),
            ('foo-.service.d/x.conf', None, 9, ('foo-.service', 'Drop-in', '')),
            ('service.d/x.conf', None, 9, ('service', 'Drop-in', '')),
            ('ssh.service.d/.x.conf', None, 9, ('.x.conf', 'Other', '')),
            ('ssh.service.d/notes.txt', None, 9, ('notes.txt', 'Other', '')),
            ('README.d/x.conf', None, 9, ('x.conf', 'Other', '')),
            ('ssh.service.d/sub/x.conf', None, 9, ('x.conf', 'Other', '')),
        ]
        for inside, link, size, expected in cases:
            with self.subTest(inside=inside, link=link):
                self.assertEqual(units.entry_kind('System', system, inside, link, size), expected)

    def test_place(self):
        self.assertEqual(units.place('etc/systemd/system/a.service'),
                         ('System', '/etc/systemd/system', 'a.service'))
        self.assertEqual(units.place('./etc/systemd/user/a.target.wants/b.service'),
                         ('All users', '/etc/systemd/user', 'a.target.wants/b.service'))
        self.assertEqual(units.place('home/alice/.config/systemd/user/a.service'),
                         ('User', '/home/alice/.config/systemd/user', 'a.service'))
        self.assertEqual(units.place('.config/systemd/user/a.service'), ('User', '/.config/systemd/user', 'a.service'))
        self.assertIsNone(units.place('etc/systemd/system/'))
        self.assertIsNone(units.place('etc/systemd/system.conf'))


class LinesTest(unittest.TestCase):
    def test_line_ends_as_read_line_full_splits_them(self):
        cases = {
            b'': [], b'a': [b'a'], b'\n': [b''], b'a\nb': [b'a', b'b'], b'a\r\nb': [b'a', b'b'],
            b'a\n\rb': [b'a', b'b'], b'a\n\nb': [b'a', b'', b'b'], b'a\r\rb': [b'a', b'', b'b'],
            b'a\0b': [b'a', b'b'], b'a\n\0b': [b'a', b'b'], b'a\r\n\0b': [b'a', b'b'], b'a\0\nb': [b'a', b'', b'b'],
            b'a\n': [b'a'], b'a\n\n': [b'a', b''],
        }
        for data, expected in cases.items():
            with self.subTest(data=data):
                self.assertEqual(units.lines_of(data), expected)


class SystemdReadingTest(unittest.TestCase):
    """What systemd 259.5 made of each file: the last Description in [Unit], or None where it was not loaded."""

    def test_unit_files_as_systemd_read_them(self):
        cases = [
            (b'[Unit]\nDescription=alpha \\\n  beta\n' + SVC, 'alpha    beta'),
            (b'[Unit]\nDescription=alpha \\\n# note\nbeta\n' + SVC, 'alpha  beta'),
            (b'[Unit]\n  #Description=hidden \\\nDescription=kept\n' + SVC, 'kept'),
            (b'\xef\xbb\xbf[Unit]\nDescription=bom\n' + SVC, 'bom'),
            (b'[Unit]\rDescription=cr\r[Service]\rType=oneshot\rExecStart=/usr/bin/true\r', 'cr'),
            (b'[Unit]\x00Description=nul\x00[Service]\x00Type=oneshot\x00ExecStart=/usr/bin/true\x00', 'nul'),
            (b'[Unit]\nDescription=crlf\r\n' + SVC.replace(b'\n', b'\r\n'), 'crlf'),
            (b'[Unit]\nDescription=bad\xff\n' + SVC, None),
            (b'[Unit\nDescription=x\n' + SVC, None),
            (b'[Un"it]\nDescription=x\n[Unit]\nDescription=y\n' + SVC, None),
            (b'Description=outside\n' + SVC, ''),
            (b'[Unit]\nDescription=first\nDescription\n' + SVC, 'first'),
            (b'[Unit]\n  Description =   spaced   \n' + SVC, 'spaced'),
            (b'[Unit]\n=value\nDescription=ok\n' + SVC, 'ok'),
            (b'[Unit]\nDescription=first\nDescription=second\n' + SVC, 'second'),
            (b'[Unit]   \nDescription=trail\n' + SVC, 'trail'),
            (SVC + b'[Unit]\nDescription=eof \\', 'eof'),
            (b'\xef\xbb\xbf# comment first\n\xef\xbb\xbf[Unit]\nDescription=bom2\n' + SVC, ''),
            (b'[Unit]\nDescription=one \\\n\\\ntwo\n' + SVC, 'one   two'),
            (b'[Unit]\nDescription=tab\t\t\n\tDescription2=x\n' + SVC, 'tab'),
            (b'[Unit]\nDescription=long\nX-Long=' + b'a' * LIMIT + b'\n' + SVC, None),
            (b'[Unit]\nDescription=before\n[Foo]\nDescription=inside\n' + SVC, 'before'),
            (b'[Unit]\nDescription=before\n[X-Custom]\nDescription=inside\n' + SVC, 'before'),
            (b'[Unit]\nDescription=a\\\\\nDocumentation=man:b(1)\n' + SVC, 'a\\\\'),
            (b'[Unit]\nDescription=x\n[Un\tit]\n' + SVC, None),
            (b'[Unit]\nDescription=x\n[Un\x7fit]\n' + SVC, None),
            (b'[Unit]\nDescription=x\n[Un\xc3\xa9it]\nDescription=y\n' + SVC, 'x'),
        ]
        for data, expected in cases:
            with self.subTest(data=data[:60]):
                settings, stop, _skipped = units.unit_settings(data)
                described = [v for _n, section, key, v in settings if section == 'Unit' and key == 'Description']
                self.assertEqual(None if stop else (described[-1] if described else ''), expected)

    def test_an_escaped_backslash_ends_the_line(self):
        # systemd applied the Documentation line after it, so it was not taken as a continuation.
        settings = units.unit_settings(b'[Unit]\nDescription=a\\\\\nDocumentation=man:b(1)\n')[0]
        self.assertEqual(settings, [(2, 'Unit', 'Description', 'a\\\\'), (3, 'Unit', 'Documentation', 'man:b(1)')])

    def test_line_length_limits(self):
        first = b'X-B=' + b'b' * 996 + b'\\'
        cases = [
            (b'[Unit]\n' + b'X-A=' + b'a' * (LIMIT - 5) + b'\n', None),
            (b'[Unit]\n' + b'X-A=' + b'a' * (LIMIT - 4) + b'\n', (2, units.TOO_LONG)),
            (b'[Unit]\n' + first + b'\n' + b'c' * (LIMIT - len(first)) + b'\n', None),
            (b'[Unit]\n' + first + b'\n' + b'c' * (LIMIT - len(first) + 1) + b'\n', (3, units.TOO_LONG)),
            (b'[Unit]\n# ' + b'c' * LIMIT + b'\n', (2, units.TOO_LONG)),
        ]
        for data, stop in cases:
            with self.subTest(size=len(data)):
                self.assertEqual(units.unit_settings(data)[1], stop)

    def test_drop_ins_stop_at_the_line_systemd_stops_at(self):
        # systemd applied Description=kept (or ok1, ok3) and nothing after, and still loaded the unit.
        cases = [
            (b'[Unit]\nDescription=kept\n[Unit\nDocumentation=man:after(1)\n', (3, units.BAD_HEADER)),
            (b'[Unit]\nDescription=kept\nDocumentation=man:x\xff(1)\nDescription=after\n', (3, units.NOT_UTF8)),
            (b'[Unit]\nDescription=kept\nX-Long=' + b'a' * LIMIT + b'\nDescription=after\n', (3, units.TOO_LONG)),
        ]
        for data, stop in cases:
            with self.subTest(stop=stop):
                settings, got, _skipped = units.unit_settings(data)
                self.assertEqual((settings, got), ([(2, 'Unit', 'Description', 'kept')], stop))

    def test_rows_line_numbers_sections_and_skipped_lines(self):
        data = (b'X=outside\n# c\n[Unit]\nDescription=a \\\n b\n\n[Service]\n  ExecStart = /usr/bin/true x  \n'
                b'no equals\n=v\n[X-Custom]\nKey=v\n[]\nK=\n')
        settings, stop, skipped = units.unit_settings(data)
        self.assertIsNone(stop)
        self.assertEqual(settings, [(4, 'Unit', 'Description', 'a   b'), (8, 'Service', 'ExecStart', '/usr/bin/true x'),
                                    (12, 'X-Custom', 'Key', 'v'), (14, '', 'K', '')])
        self.assertEqual(skipped, {'lines outside a section': 1, 'lines that are not assignments': 2})


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


class NoRecordContext(FakeContext):
    def get_seeker(self):
        raise ValueError('no seeker set')


def staged(root, name, data):
    path = os.path.join(root, *name.split('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return path


def run(context):
    with mock.patch.object(units, 'logfunc') as log:
        entries = units.linuxSystemdUnitEntries.__wrapped__(context)
        settings = units.linuxSystemdUnitSettings.__wrapped__(context)
    return entries, settings, [call.args[0] for call in log.call_args_list]


def when(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


T = 1788000000
TAR_MEMBERS = [
    ('etc/systemd/system/ssh.service',
     b'[Unit]\nDescription=OpenSSH\n[Service]\nExecStart=/usr/sbin/sshd -D\n[Install]\nWantedBy=multi-user.target\n',
     None, T + 1),
    ('etc/systemd/system/sshd.service', None, '/usr/lib/systemd/system/ssh.service', T + 2),
    ('etc/systemd/system/multi-user.target.wants/ssh.service', None, '/usr/lib/systemd/system/ssh.service', T + 3),
    ('etc/systemd/system/display-manager.service', None, '/lib/systemd/system/gdm3.service', T + 4),
    ('etc/systemd/system/snap-a\\x2db-1.mount', b'[Unit]\nDescription=Mount a-b\n[Mount]\nWhat=/snaps/a-b_1.snap\n',
     None, T + 5),
    ('etc/systemd/system/ssh.service.d/override.conf', b'[Service]\nExecStart=\nExecStart=/usr/sbin/sshd -p 2222\n',
     None, T + 6),
    ('etc/systemd/system/broken.service', b'[Unit]\nDescription=ok\n[Unit\n', None, T + 7),
    ('etc/systemd/system/partial.service.d/10.conf', b'[Unit]\nDescription=kept\nDocumentation=x\xff\n', None, T + 8),
    ('etc/systemd/system/README', b'notes\n', None, T + 9),
    ('etc/systemd/system/ssh.service.d/notes.conf', b'# only a comment\n', None, T + 18),
    ('etc/systemd/user/default.target.wants/pipewire.service', None, '/usr/lib/systemd/user/pipewire.service', T + 10),
    ('home/alice/.config/systemd/user/job.service', b'X=outside\n[Service]\nExecStart=/usr/bin/true\nno equals\n',
     None, T + 11),
    ('home/alice/.config/systemd/user/job-alias.service', None, 'job.service', T + 12),
    ('home/alice/.config/systemd/user/masked.service', None, '/dev/null', T + 13),
    ('home/alice/.config/systemd/user/empty.service', b'', None, T + 14),
    ('home/alice/.config/systemd/user/linked.service', None, '/opt/linked.service', T + 15),
    ('home/alice/.config/systemd/user/other.service', None, '/home/bob/.config/systemd/user/x.service', T + 16),
    ('etc/passwd', b'root:x:0:0::/root:/bin/sh\n', None, T + 17),
]


class TarTest(unittest.TestCase):
    """Both artifacts on a tar extraction, with the seeker's own record of each member."""

    def test_entries_settings_and_log(self):
        with tempfile.TemporaryDirectory() as root:
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w') as archive:
                for name, data, link, mtime in TAR_MEMBERS:
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
            data_folder = os.path.join(root, 'data')
            infos, files = {}, []
            for name, data, link, mtime in TAR_MEMBERS:
                path = staged(data_folder, name, b'' if link is not None else data)
                infos[path] = SimpleNamespace(source_path=name, modification_date=mtime)
                files.append(path)
            files.append(os.path.join(data_folder, 'etc', 'systemd', 'system', 'multi-user.target.wants'))
            with tarfile.open(fileobj=buffer, mode='r') as archive:
                seeker = SimpleNamespace(tar_file=archive, file_infos=infos)
                entries, settings, log = run(FakeContext(files, data_folder, seeker))
        headers, rows, source = entries
        self.assertEqual(len(headers), len(rows[0]))
        s, u, h = 'etc/systemd/system/', 'etc/systemd/user/', 'home/alice/.config/systemd/user/'
        self.assertEqual(rows, [
            (when(T + 9), 'System', 'README', 'Other', '', '', s + 'README'),
            (when(T + 7), 'System', 'broken.service', 'Unit file', '', '', s + 'broken.service'),
            (when(T + 4), 'System', 'display-manager.service', 'Alias link', '', '/lib/systemd/system/gdm3.service',
             s + 'display-manager.service'),
            (when(T + 3), 'System', 'ssh.service', 'Wants link', 'multi-user.target',
             '/usr/lib/systemd/system/ssh.service', s + 'multi-user.target.wants/ssh.service'),
            (when(T + 8), 'System', 'partial.service', 'Drop-in', '', '', s + 'partial.service.d/10.conf'),
            (when(T + 5), 'System', 'snap-a\\x2db-1.mount', 'Unit file', '', '', s + 'snap-a\\x2db-1.mount'),
            (when(T + 1), 'System', 'ssh.service', 'Unit file', '', '', s + 'ssh.service'),
            (when(T + 18), 'System', 'ssh.service', 'Drop-in', '', '', s + 'ssh.service.d/notes.conf'),
            (when(T + 6), 'System', 'ssh.service', 'Drop-in', '', '', s + 'ssh.service.d/override.conf'),
            (when(T + 2), 'System', 'sshd.service', 'Alias link', '', '/usr/lib/systemd/system/ssh.service',
             s + 'sshd.service'),
            (when(T + 10), 'All users', 'pipewire.service', 'Wants link', 'default.target',
             '/usr/lib/systemd/user/pipewire.service', u + 'default.target.wants/pipewire.service'),
            (when(T + 14), 'User', 'empty.service', 'Empty unit file (masked)', '', '', h + 'empty.service'),
            (when(T + 12), 'User', 'job-alias.service', 'Alias link', '', 'job.service', h + 'job-alias.service'),
            (when(T + 11), 'User', 'job.service', 'Unit file', '', '', h + 'job.service'),
            (when(T + 15), 'User', 'linked.service', 'Linked unit file', '', '/opt/linked.service',
             h + 'linked.service'),
            (when(T + 13), 'User', 'masked.service', 'Masked (link to /dev/null)', '', '/dev/null',
             h + 'masked.service'),
            (when(T + 16), 'User', 'other.service', 'Linked unit file', '', '/home/bob/.config/systemd/user/x.service',
             h + 'other.service'),
        ])
        self.assertEqual(len(source.split('\n')), 17)
        headers, rows, source = settings
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (when(T + 8), 'System', 'partial.service', 'Unit', 'Description', 'kept', 2,
             s + 'partial.service.d/10.conf'),
            (when(T + 5), 'System', 'snap-a\\x2db-1.mount', 'Unit', 'Description', 'Mount a-b', 2,
             s + 'snap-a\\x2db-1.mount'),
            (when(T + 5), 'System', 'snap-a\\x2db-1.mount', 'Mount', 'What', '/snaps/a-b_1.snap', 4,
             s + 'snap-a\\x2db-1.mount'),
            (when(T + 1), 'System', 'ssh.service', 'Unit', 'Description', 'OpenSSH', 2, s + 'ssh.service'),
            (when(T + 1), 'System', 'ssh.service', 'Service', 'ExecStart', '/usr/sbin/sshd -D', 4, s + 'ssh.service'),
            (when(T + 1), 'System', 'ssh.service', 'Install', 'WantedBy', 'multi-user.target', 6, s + 'ssh.service'),
            (when(T + 6), 'System', 'ssh.service', 'Service', 'ExecStart', '', 2, s + 'ssh.service.d/override.conf'),
            (when(T + 6), 'System', 'ssh.service', 'Service', 'ExecStart', '/usr/sbin/sshd -p 2222', 3,
             s + 'ssh.service.d/override.conf'),
            (when(T + 11), 'User', 'job.service', 'Service', 'ExecStart', '/usr/bin/true', 3, h + 'job.service'),
        ])
        self.assertEqual(len(source.split('\n')), 5)
        self.assertEqual(log, [
            f'systemd Unit Settings: {s}broken.service not reported: systemd does not load a unit file with '
            f'{units.BAD_HEADER} (line 3)',
            f'systemd Unit Settings: {s}partial.service.d/10.conf read up to line 3, where systemd stops reading a '
            f'drop-in with {units.NOT_UTF8}',
            'systemd Unit Settings: 1 lines outside a section, 1 lines that are not assignments, not reported',
        ])


class OtherSeekersTest(unittest.TestCase):
    def test_zip(self):
        with tempfile.TemporaryDirectory() as root:
            archive_path = os.path.join(root, 'x.zip')
            with zipfile.ZipFile(archive_path, 'w') as archive:
                archive.writestr('etc/systemd/system/', '')
                link = zipfile.ZipInfo('etc/systemd/system/multi-user.target.wants/a.service')
                link.external_attr = 0o120777 << 16
                archive.writestr(link, '/usr/lib/systemd/system/a.service')
                archive.writestr('etc/systemd/system/a.service', '[Unit]\nDescription=A\n')
            data_folder = os.path.join(root, 'data')
            folder = os.path.join(data_folder, 'etc', 'systemd', 'system')
            files = [staged(data_folder, 'etc/systemd/system/multi-user.target.wants/a.service',
                            b'/usr/lib/systemd/system/a.service'),
                     staged(data_folder, 'etc/systemd/system/a.service', b'[Unit]\nDescription=A\n'), folder]
            with zipfile.ZipFile(archive_path) as archive:
                seeker = SimpleNamespace(zip_file=archive, file_infos={
                    files[0]: SimpleNamespace(source_path='etc/systemd/system/multi-user.target.wants/a.service',
                                              modification_date=None),
                    files[1]: SimpleNamespace(source_path='etc/systemd/system/a.service', modification_date=0),
                    folder: SimpleNamespace(source_path='etc/systemd/system/', modification_date=0)})
                entries, settings, log = run(FakeContext(files, data_folder, seeker))
        self.assertEqual([row[1:6] for row in entries[1]], [
            ('System', 'a.service', 'Unit file', '', ''),
            ('System', 'a.service', 'Wants link', 'multi-user.target', '/usr/lib/systemd/system/a.service')])
        self.assertEqual({row[0] for row in entries[1]}, {''})
        self.assertEqual([row[1:7] for row in settings[1]], [('System', 'a.service', 'Unit', 'Description', 'A', 2)])
        self.assertEqual(log, [])

    def test_raw_image_names_keep_their_backslash(self):
        # The raw image seeker stages a name holding a backslash in folders split at it.
        with tempfile.TemporaryDirectory() as root:
            data_folder = os.path.join(root, 'data')
            path = staged(data_folder, 'lba0_v/etc/systemd/system/a/x2db.mount', b'[Mount]\nWhat=/dev/x\n')
            seeker = SimpleNamespace(file_infos={path: SimpleNamespace(
                source_path='lba0_v/etc/systemd/system/a\\x2db.mount', modification_date=T)})
            entries, settings, _log = run(FakeContext([path], data_folder, seeker))
        self.assertEqual(entries[1], [(when(T), 'System', 'a\\x2db.mount', 'Unit file', '', '',
                                       'lba0_v/etc/systemd/system/a\\x2db.mount')])
        self.assertEqual([row[2:7] for row in settings[1]], [('a\\x2db.mount', 'Mount', 'What', '/dev/x', 2)])

    def test_a_file_that_cannot_be_read_is_counted(self):
        with tempfile.TemporaryDirectory() as root:
            path = staged(root, 'etc/systemd/system/a.service', b'[Unit]\nDescription=A\n')
            with mock.patch.object(units, 'open', create=True, side_effect=OSError('denied')):
                entries, settings, log = run(NoRecordContext([path], root, None))
        self.assertEqual(len(entries[1]), 1)
        self.assertEqual(settings[1], [])
        self.assertEqual(log, ['systemd Unit Settings: 1 files that could not be read, not reported'])

    def test_no_seeker(self):
        with tempfile.TemporaryDirectory() as root:
            path = staged(root, 'etc/systemd/system/a.service', b'[Unit]\nDescription=A\n')
            entries, settings, _log = run(NoRecordContext([path], root, None))
        self.assertEqual(entries[1], [('', 'System', 'a.service', 'Unit file', '', '', 'etc/systemd/system/a.service')])
        self.assertEqual(len(settings[1]), 1)


@unittest.skipIf(os.sep == '\\', 'a file name holding a backslash cannot be made here')
class FolderTest(unittest.TestCase):
    """The folder seeker stages nothing for a link that resolves outside the input folder, returning its path and
    recording the link's own times; follows a link that stays inside, recording its target's times; returns a
    matched folder without staging it; and records a backslash in a name as /."""

    def test_folder_input(self):
        with tempfile.TemporaryDirectory() as root:
            evidence = os.path.join(root, 'evidence')
            system = os.path.join(evidence, 'etc', 'systemd', 'system')
            os.makedirs(os.path.join(system, 'multi-user.target.wants'))
            staged(evidence, 'etc/systemd/system/real.service', b'[Unit]\nDescription=real\n')
            staged(evidence, 'etc/systemd/system/snap-a\\x2db.mount', b'[Unit]\nDescription=snap\n')
            staged(evidence, 'etc/systemd/system/Up.service', b'[Unit]\nDescription=up\n')
            try:
                os.symlink('/nonexistent-dleapp/real.service',
                           os.path.join(system, 'multi-user.target.wants', 'real.service'))
                os.symlink('real.service', os.path.join(system, 'alias.service'))
            except (OSError, NotImplementedError):
                self.skipTest('this platform cannot make a symbolic link here')
            for name, seconds in (('multi-user.target.wants/real.service', 1000), ('alias.service', 2000)):
                if os.utime in os.supports_follow_symlinks:
                    os.utime(os.path.join(system, name), (seconds, seconds), follow_symlinks=False)
            data = os.path.join(root, 'data')
            real = staged(data, 'etc/systemd/system/real.service', b'[Unit]\nDescription=real\n')
            alias = staged(data, 'etc/systemd/system/alias.service', b'[Unit]\nDescription=real\n')
            snap = staged(data, 'etc/systemd/system/snap-a\\x2db.mount', b'[Unit]\nDescription=snap\n')
            renamed = staged(data, 'etc/systemd/system/up.service~case-1', b'[Unit]\nDescription=up\n')
            dangling = os.path.join(data, 'etc', 'systemd', 'system', 'multi-user.target.wants', 'real.service')
            folder = os.path.join(data, 'etc', 'systemd', 'system', 'multi-user.target.wants')
            outside = os.lstat(os.path.join(system, 'multi-user.target.wants', 'real.service')).st_mtime
            seeker = SimpleNamespace(directory=evidence, data_folder=data, file_infos={
                dangling: SimpleNamespace(source_path='etc/systemd/system/multi-user.target.wants/real.service',
                                          modification_date=outside),
                real: SimpleNamespace(source_path='etc/systemd/system/real.service', modification_date=3000.0),
                alias: SimpleNamespace(source_path='etc/systemd/system/alias.service', modification_date=3000.0),
                snap: SimpleNamespace(source_path='etc/systemd/system/snap-a/x2db.mount', modification_date=4000.0),
                renamed: SimpleNamespace(source_path='etc/systemd/system/Up.service', modification_date=5000.0)})
            entries, settings, log = run(FakeContext([real, alias, snap, renamed, dangling, folder], data, seeker))
            times = {name: when(os.lstat(os.path.join(system, name)).st_mtime)
                     for name in ('multi-user.target.wants/real.service', 'alias.service')}
        s = 'etc/systemd/system/'
        self.assertEqual(entries[1], [
            (when(5000.0), 'System', 'Up.service', 'Unit file', '', '', s + 'Up.service'),
            (times['alias.service'], 'System', 'alias.service', 'Alias link', '', 'real.service', s + 'alias.service'),
            (times['multi-user.target.wants/real.service'], 'System', 'real.service', 'Wants link',
             'multi-user.target', '/nonexistent-dleapp/real.service', s + 'multi-user.target.wants/real.service'),
            (when(3000.0), 'System', 'real.service', 'Unit file', '', '', s + 'real.service'),
            (when(4000.0), 'System', 'snap-a\\x2db.mount', 'Unit file', '', '', s + 'snap-a\\x2db.mount'),
        ])
        self.assertEqual([row[2:6] for row in settings[1]], [('Up.service', 'Unit', 'Description', 'up'),
                                                              ('real.service', 'Unit', 'Description', 'real'),
                                                              ('snap-a\\x2db.mount', 'Unit', 'Description', 'snap')])
        self.assertEqual(log, [])


if __name__ == '__main__':
    unittest.main()
