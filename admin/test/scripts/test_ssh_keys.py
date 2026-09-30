"""Pin how the SSH artifacts read authorized_keys and known_hosts files."""
import base64
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import sshKeys
# pylint: enable=wrong-import-position

# Two synthetic public keys. The fingerprints are what `ssh-keygen -lf` (OpenSSH) printed for
# them, written out here so the tests do not check the code against itself.
ED25519 = 'AAAAC3NzaC1lZDI1NTE5AAAAIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f'
ED25519_FP = 'SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA'
RSA = ('AAAAB3NzaC1yc2EAAAADAQABAAABAQDAAQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8'
       'PT4/QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+Q'
       'kZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7CxsrO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk'
       '5ebn6Onq6+zt7u/w8fLz9PX29/j5+vv8/f7/')
RSA_FP = 'SHA256:/sExSN3dej5bryMa2+9IxHq9XrCBbcbzrft6W/eg6kI'


def cert(kind='ssh-ed25519-cert-v01@openssh.com'):
    name = kind.encode()
    return base64.b64encode(struct.pack('>I', len(name)) + name + bytes(40)).decode()


AUTHORIZED = ('# keys for this account\n'
              '\n'
              f'ssh-ed25519 {ED25519} alex@laptop  two spaces kept\n'
              f'from="10.0.0.1,10.0.0.2",command="echo \\"hi there\\"",no-pty ssh-rsa {RSA} rsa key\n'
              f'  \tssh-ed25519 {ED25519}\n'
              f'ssh-ed25519-cert-v01@openssh.com {cert()} a certificate\n'
              f'ssh-rsa {ED25519} type does not match\n'
              'ssh-ed25519 not*base64 broken\n').encode()


class AuthorizedKeysTest(unittest.TestCase):
    def test_key_lines_with_and_without_options(self):
        counts = Counter()
        rows = sshKeys.authorized_key_rows(AUTHORIZED, counts)
        self.assertEqual(rows, [(ED25519_FP, 'ssh-ed25519', 'alex@laptop  two spaces kept', '', 3),
                                (RSA_FP, 'ssh-rsa', 'rsa key', 'from="10.0.0.1,10.0.0.2",command="echo \\"hi there\\"",no-pty', 4),
                                (ED25519_FP, 'ssh-ed25519', '', '', 5),
                                ('', 'ssh-ed25519-cert-v01@openssh.com', 'a certificate', '', 6)])
        self.assertEqual(counts, {'certificates, fingerprint not computed': 1,
                                  'authorized_keys lines that do not hold a key, not reported': 2})

    def test_text_that_is_not_utf8_shows_the_replacement_character(self):
        rows = sshKeys.authorized_key_rows(f'ssh-ed25519 {ED25519} caf'.encode() + b'\xe9\n', Counter())
        self.assertEqual(rows[0][2], 'caf\ufffd')

    def test_a_blob_shorter_than_its_type_length_says_is_not_a_key(self):
        short = base64.b64encode(struct.pack('>I', 100) + b'ssh-ed25519').decode()
        counts = Counter()
        self.assertEqual(sshKeys.authorized_key_rows(f'ssh-ed25519 {short}\n'.encode(), counts), [])
        self.assertEqual(counts, {'authorized_keys lines that do not hold a key, not reported': 1})

    def test_crlf_line_ends_are_not_part_of_the_comment(self):
        rows = sshKeys.authorized_key_rows(AUTHORIZED.replace(b'\n', b'\r\n'), Counter())
        self.assertEqual(rows[0][2], 'alex@laptop  two spaces kept')


KNOWN = ('# known hosts\n'
         f'|1|c2FsdHNhbHRzYWx0c2FsdA==|aGFzaGhhc2hoYXNoaGFzaGhhc2g= ssh-ed25519 {ED25519}\n'
         f'[git.example.com]:2222,192.0.2.7\tssh-rsa\t{RSA} a comment\n'
         f'@revoked *.example.org ssh-ed25519 {ED25519}\n'
         f'@cert-authority *.corp ssh-rsa {RSA}\n'
         f'@unknown host ssh-ed25519 {ED25519}\n'
         'hostonly\n').encode()


class KnownHostsTest(unittest.TestCase):
    def test_host_lines(self):
        counts = Counter()
        rows = sshKeys.known_host_rows(KNOWN, counts)
        self.assertEqual(rows, [('|1|c2FsdHNhbHRzYWx0c2FsdA==|aGFzaGhhc2hoYXNoaGFzaGhhc2g=', 'yes', '', 'ssh-ed25519',
                                 ED25519_FP, '', 2),
                                ('[git.example.com]:2222,192.0.2.7', '', '', 'ssh-rsa', RSA_FP, 'a comment', 3),
                                ('*.example.org', '', '@revoked', 'ssh-ed25519', ED25519_FP, '', 4),
                                ('*.corp', '', '@cert-authority', 'ssh-rsa', RSA_FP, '', 5)])
        self.assertEqual(counts, {'known_hosts lines with a marker OpenSSH does not define, not reported': 1,
                                  'known_hosts lines that do not hold a host and a key, not reported': 1})


class FakeContext:
    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, function, members):
        with tempfile.TemporaryDirectory() as root:
            files = []
            for relative, data in members:
                path = os.path.join(root, relative)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                files.append(path)
            with mock.patch.object(sshKeys, 'logfunc') as log:
                _headers, rows, source = function.__wrapped__(FakeContext(files, root))
            source = [os.path.relpath(path, root) for path in source.split('\n')] if source else []
        return rows, source, log

    def test_each_account_file_is_read_and_named(self):
        root_keys = os.path.join('root', '.ssh', 'authorized_keys')
        user_keys = os.path.join('home', 'a', '.ssh', 'authorized_keys')
        rows, source, log = self.run_artifact(sshKeys.sshAuthorizedKeys, [(root_keys, f'ssh-rsa {RSA}\n'.encode()),
                                                                          (user_keys, AUTHORIZED)])
        self.assertEqual([(row[0], row[-1]) for row in rows][-1], (RSA_FP, root_keys))
        self.assertEqual(rows[0][-1], user_keys)
        self.assertEqual(len(rows), 5)
        self.assertEqual(source, [user_keys, root_keys])
        self.assertIn('2 authorized_keys lines that do not hold a key', log.call_args.args[0])

    def test_known_hosts_rows_carry_their_file(self):
        system = os.path.join('etc', 'ssh', 'ssh_known_hosts')
        rows, source, _log = self.run_artifact(sshKeys.sshKnownHosts, [(system, KNOWN)])
        self.assertEqual(len(rows), 4)
        self.assertEqual({row[-1] for row in rows}, {system})
        self.assertEqual(source, [system])

    def test_declared_paths_include_the_copy_ssh_keygen_keeps(self):
        import fnmatch  # pylint: disable=import-outside-toplevel
        patterns = sshKeys.__artifacts_v2__['sshKnownHosts']['paths']
        for member in ('home/a/.ssh/known_hosts', 'home/a/.ssh/known_hosts2', 'home/a/.ssh/known_hosts.old',
                       'root/.ssh/known_hosts.old', 'etc/ssh/ssh_known_hosts', 'etc/ssh/ssh_known_hosts2'):
            self.assertEqual(sum(fnmatch.fnmatch('x/' + member, p) for p in patterns), 1, member)
        for member in ('home/a/.ssh/known_hosts.old.1', 'home/a/.ssh/known_hosts.bak', 'home/a/.ssh/known_hosts.XXXXXXXXXX'):
            self.assertFalse(any(fnmatch.fnmatch('x/' + member, p) for p in patterns), member)


if __name__ == '__main__':
    unittest.main()
