"""Pin how the Audit Log (auditd) artifact reads the records auditd writes to /var/log/audit/audit.log. Every record
here is constructed for the test."""
import fnmatch
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxAudit as la
# pylint: enable=wrong-import-position

UTC = timezone.utc
USER = (b"type=USER_START msg=audit(1790794322.080:330): pid=5132 uid=0 auid=1000 ses=11 subj=u:r:t:s0 "
        b"msg='op=PAM:session_open grantors=pam_unix acct=\"alice\" exe=\"/usr/bin/su\" hostname=? addr=? "
        b"terminal=pts/1 res=success'\x1dUID=\"root\" AUID=\"alice\"")
HEX_ACCT = (b"type=USER_LOGIN msg=audit(1790794322.001:12): pid=7 uid=0 auid=4294967295 ses=4294967295 "
            b"msg='op=login acct=616C69636520626F62 exe=2F746D702F6D7920657865 hostname=h addr=10.0.0.9 terminal=ssh "
            b"res=failed'")
CMD = (b"type=USER_CMD msg=audit(1790794322.180:337): pid=5163 uid=0 auid=1000 ses=11 msg='cwd=\"/root\" "
       b"cmd=6964202D75 exe=\"/usr/bin/sudo\" terminal=pts/1 res=success'")
SYSCALL = (b"type=SYSCALL msg=audit(1790794322.271:368): arch=c00000b7 syscall=64 success=yes exit=4 ppid=868 "
           b"pid=5190 auid=1000 uid=0 ses=12 comm=\"sshd\" exe=\"/usr/sbin/sshd\" key=(null)")
TITLE = b"type=PROCTITLE msg=audit(1790794322.271:368): proctitle=2F7573722F7362696E2F637264002D6E00"
QUOTED_TITLE = b'type=PROCTITLE msg=audit(1790794322.271:369): proctitle="(systemd)"'
NODE = b"node=web1 type=DEL_GROUP msg=audit(1790794322.220:349): pid=1 uid=0 msg='op=delete-group id=1001 res=success'"
EOE = b"type=EOE msg=audit(1790794322.220:350):"


class FieldsTest(unittest.TestCase):
    def test_outside_fields_come_before_those_in_msg(self):
        fields = la.record_fields("pid=1 res=outer msg='res=inner op=x'")
        self.assertEqual((fields['pid'], fields['res'], fields['op']), ('1', 'outer', 'x'))

    def test_quotes_and_hex(self):
        fields = la.record_fields('acct=4142 id=4142 exe="/bin/x" cmd=zz proctitle=6100620063')
        self.assertEqual(la.field_value(fields, 'acct'), 'AB')
        self.assertEqual(la.field_value(fields, 'id'), '4142')
        self.assertEqual(la.field_value(fields, 'exe'), '/bin/x')
        self.assertEqual(la.field_value(fields, 'cmd'), 'zz')
        self.assertEqual(la.field_value(fields, 'proctitle'), 'a b c')
        self.assertEqual(la.field_value(fields, 'missing'), '')
        self.assertEqual(la.field_value(la.record_fields('acct=41f2'), 'acct'), '41f2')
        self.assertEqual(la.field_value(la.record_fields('acct=41FF'), 'acct'), 'A\\xff')


class RowsTest(unittest.TestCase):
    def test_records(self):
        counts = Counter()
        data = b'\n'.join([USER, HEX_ACCT, CMD, SYSCALL, TITLE, QUOTED_TITLE, NODE, EOE, b'', b'not a record',
                           b'type=X msg=audit(99999999999999999999.000:1): a=1', b'type=Y msg=audit(1.000:2): acct=FF\r'])
        rows = la.audit_rows(data, counts)
        self.assertEqual(counts, {la.NOT_AUDIT: 1, 'times that cannot be shown, Time (UTC) left blank': 1})
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0], (datetime(2026, 9, 30, 18, 52, 2, 80000, tzinfo=UTC), '330', 'USER_START', '5132', '0',
                                   '1000', '11', 'PAM:session_open', 'alice', '', '/usr/bin/su', '', '', '?', '?',
                                   'pts/1', 'success', USER.decode().split('): ', 1)[1].split('\x1d')[0],
                                   'UID="root" AUID="alice"', '', 1))
        self.assertEqual(rows[1][8:11], ('alice bob', '', '/tmp/my exe'))
        self.assertEqual((rows[1][5], rows[1][6], rows[1][16]), ('4294967295', '4294967295', 'failed'))
        self.assertEqual(rows[2][11], 'id -u')
        self.assertEqual((rows[3][3], rows[3][10], rows[3][17]), ('5190', '/usr/sbin/sshd', SYSCALL.decode().split(': ', 1)[1]))
        self.assertEqual(rows[4][12], '/usr/sbin/crd -n')
        self.assertEqual(rows[5][12], '(systemd)')
        self.assertEqual((rows[6][2], rows[6][9], rows[6][19]), ('DEL_GROUP', '1001', 'web1'))
        self.assertEqual((rows[7][2], rows[7][17], rows[7][20]), ('EOE', '', 8))
        self.assertEqual((rows[8][0], rows[8][2], rows[8][20]), ('', 'X', 11))
        self.assertEqual((rows[9][0], rows[9][8], rows[9][20]), (datetime(1970, 1, 1, 0, 0, 1, tzinfo=UTC), '\\xff', 12))


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):
    def test_files_rotations_and_sources(self):
        with tempfile.TemporaryDirectory() as root:
            logs = os.path.join(root, 'var', 'log', 'audit')
            os.makedirs(logs)
            current = os.path.join(logs, 'audit.log')
            rotated = os.path.join(logs, 'audit.log.1.gz')
            empty = os.path.join(logs, 'audit.log.2')
            with open(current, 'wb') as handle:
                handle.write(USER + b'\n' + b'garbage\n')
            with gzip.open(rotated, 'wb') as handle:
                handle.write(CMD + b'\n')
            with open(empty, 'wb') as handle:
                handle.write(b'\n')
            paths = [rotated, empty, current, os.path.join(root, 'missing', 'audit.log'), logs]
            with mock.patch.object(la, 'logfunc') as log:
                headers, rows, source = la.linuxAuditLog.__wrapped__(FakeContext(paths, root))
        self.assertEqual(headers[0], ('Time (UTC)', 'datetime'))
        self.assertEqual(len(headers), 22)
        self.assertEqual([(r[2], r[-2], r[-1]) for r in rows],
                         [('USER_START', 1, 'var/log/audit/audit.log'), ('USER_CMD', 1, 'var/log/audit/audit.log.1.gz')])
        self.assertEqual(source.split('\n'), [current, rotated])
        log.assert_called_once_with('Audit Log (auditd): 1 files that could not be read, 1 ' + la.NOT_AUDIT)

    def test_paths(self):
        patterns = la.__artifacts_v2__['linuxAuditLog']['paths']
        for member in ('root/var/log/audit/audit.log', 'root/var/log/audit/audit.log.1', 'root/var/log/audit/audit.log.4.gz'):
            self.assertTrue(any(fnmatch.fnmatch(member, p) for p in patterns), member)
        for member in ('root/var/log/audit/audit.log.bak', 'root/var/log/audit.log'):
            self.assertFalse(any(fnmatch.fnmatch(member, p) for p in patterns), member)


if __name__ == '__main__':
    unittest.main()
