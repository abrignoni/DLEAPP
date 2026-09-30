"""Pin how the SSH configuration artifacts split directives. Every file here is constructed for the test."""
import fnmatch
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
from scripts.artifacts import sshConfig
# pylint: enable=wrong-import-position

CLIENT = (b'# comment\n'
          b'ServerAliveInterval 60  \n'
          b'\n'
          b'Host jump alias\n'
          b'    User=jumpuser\n'
          b'\tPort = 2222\n'
          b'    IdentityFile "~/.ssh/id with space"\n'
          b'   # indented comment\n'
          b'Match user nobody\n'
          b'    ForwardAgent yes\r\n'
          b'User\n'
          b'"quoted keyword\n'
          b'=\n')


class DirectiveTest(unittest.TestCase):
    def test_directive(self):
        self.assertEqual(sshConfig.directive('Port 22'), ('Port', '22'))
        self.assertEqual(sshConfig.directive('  Port=22'), ('Port', '22'))
        self.assertEqual(sshConfig.directive('Port = 22 # not a comment to OpenSSH\f'), ('Port', '22 # not a comment to OpenSSH'))
        self.assertEqual(sshConfig.directive('Port==22'), ('Port', '=22'))
        self.assertEqual(sshConfig.directive('SendEnv\tLANG LC_*'), ('SendEnv', 'LANG LC_*'))
        self.assertEqual(sshConfig.directive('User'), ('User', ''))
        # OpenSSH's WHITESPACE is space, tab, CR and LF; a vertical tab is part of the value, a leading one of the keyword.
        self.assertEqual(sshConfig.directive('Port 22\x0b'), ('Port', '22\x0b'))
        self.assertEqual(sshConfig.directive('\x0bPort 22'), ('\x0bPort', '22'))
        for line in ('', '   ', '# c', '  #c', '"User x', '=x'):
            self.assertIsNone(sshConfig.directive(line), line)

    def test_sections_and_counts(self):
        counts = Counter()
        rows = sshConfig.config_rows(CLIENT, ('host', 'match'), counts)
        self.assertEqual(rows, [('', 'ServerAliveInterval', '60', 2), ('Host jump alias', 'Host', 'jump alias', 4),
                                ('Host jump alias', 'User', 'jumpuser', 5), ('Host jump alias', 'Port', '2222', 6),
                                ('Host jump alias', 'IdentityFile', '"~/.ssh/id with space"', 7),
                                ('Match user nobody', 'Match', 'user nobody', 9),
                                ('Match user nobody', 'ForwardAgent', 'yes', 10), ('Match user nobody', 'User', '', 11)])
        self.assertEqual(counts, Counter({'lines whose first token is not a keyword, not reported': 2,
                                          'directives with no argument, which OpenSSH rejects': 1}))
        server = sshConfig.config_rows(b'Port 22\nHost x\nMatch User a\nPermitRootLogin no\n', ('match',), Counter())
        self.assertEqual([r[0] for r in server], ['', '', 'Match User a', 'Match User a'])

    def test_paths(self):
        client = sshConfig.__artifacts_v2__['sshClientConfig']['paths']
        server = sshConfig.__artifacts_v2__['sshServerConfig']['paths']
        for member in ('home/a/.ssh/config', 'root/.ssh/config', 'etc/ssh/ssh_config', 'etc/ssh/ssh_config.d/20-x.conf'):
            self.assertEqual(sum(fnmatch.fnmatch('x/' + member, p) for p in client), 1, member)
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in server), member)
        for member in ('etc/ssh/sshd_config', 'etc/ssh/sshd_config.d/50-cloud-init.conf'):
            self.assertEqual(sum(fnmatch.fnmatch('x/' + member, p) for p in server), 1, member)
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in client), member)
        for member in ('home/a/.ssh/config.bak', 'etc/ssh/ssh_config.bak', 'home/a/.ssh/known_hosts'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in client + server), member)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        raise ValueError('no seeker')


class ArtifactTest(unittest.TestCase):
    def test_rows_scope_and_sources(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            user = write('home/a/.ssh/config', CLIENT)
            system = write('etc/ssh/ssh_config', b'Include /etc/ssh/ssh_config.d/*.conf\nHost *\n    HashKnownHosts yes\n')
            folder = os.path.join(root, 'etc', 'ssh', 'ssh_config.d')
            os.makedirs(folder)
            with mock.patch.object(sshConfig, 'logfunc') as log:
                headers, rows, source = sshConfig.sshClientConfig.__wrapped__(FakeContext([user, folder, system], root))
            with mock.patch.object(sshConfig, 'logfunc'):
                sheaders, srows, _ = sshConfig.sshServerConfig.__wrapped__(FakeContext(
                    [write('etc/ssh/sshd_config', b'PermitRootLogin no\nHost x\nMatch User b\n  X11Forwarding no\n')], root))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(names, ['File Modified', 'Scope', 'Section', 'Keyword', 'Value', 'Link Target', 'Line', 'Source File'])
        self.assertEqual([(r[1], r[7]) for r in rows[:3]], [('System', 'etc/ssh/ssh_config')] * 3)
        self.assertEqual([r[1] for r in rows[3:]], ['User'] * 8)
        self.assertEqual(rows[2][2:7], ('Host *', 'HashKnownHosts', 'yes', '', 3))
        self.assertEqual(source.split('\n'), [system, user])
        log.assert_called_once_with('SSH Client Config: 1 directives with no argument, which OpenSSH rejects, 2 lines '
                                    'whose first token is not a keyword, not reported')
        snames = [h[0] if isinstance(h, tuple) else h for h in sheaders]
        self.assertEqual(snames, ['File Modified', 'Section', 'Keyword', 'Value', 'Link Target', 'Line', 'Source File'])
        self.assertEqual([r[1:4] for r in srows], [('', 'PermitRootLogin', 'no'), ('', 'Host', 'x'), ('Match User b', 'Match', 'User b'),
                                                    ('Match User b', 'X11Forwarding', 'no')])


if __name__ == '__main__':
    unittest.main()
