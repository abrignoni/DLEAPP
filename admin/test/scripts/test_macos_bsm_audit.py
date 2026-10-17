"""BSM audit trails built here token by token, in the layouts OpenBSM's bsm_token.c and xnu's
audit_bsm_token.c write. Every value is made up for the test."""

import datetime
import os
import pathlib
import plistlib
import struct
import tempfile
import unittest
from collections import Counter
from unittest import mock

from scripts import bsm_audit, macos_plists
from scripts.artifacts import macosBsmAudit

UTC = datetime.timezone.utc


def counted(value):
    raw = value.encode() + b'\x00'
    return struct.pack('>H', len(raw)) + raw


def header32(event, seconds, msec, modifier=0):
    return lambda size: struct.pack('>BIBHHII', 0x14, size, 11, event, modifier, seconds, msec)


def header32_ex(event, seconds, msec, addr):
    return lambda size: (struct.pack('>BIBHHI', 0x15, size, 11, event, 0, 4) + bytes(addr)
                         + struct.pack('>II', seconds, msec))


def header64(event, seconds, msec):
    return lambda size: struct.pack('>BIBHHQQ', 0x74, size, 11, event, 0, seconds, msec)


def subject32(auid, euid, egid, ruid, rgid, pid, sid, port, addr):
    return struct.pack('>BIIIIIIII', 0x24, auid & 0xFFFFFFFF, euid, egid, ruid, rgid, pid, sid, port) + bytes(addr)


def subject32_ex6(auid, euid, pid, sid, port, addr16):
    return struct.pack('>BIIIIIIIII', 0x7a, auid, euid, 20, euid, 20, pid, sid, port, 16) + addr16


def subject64(auid, euid, pid, sid, port, addr):
    return struct.pack('>BIIIIIIIQ', 0x75, auid, euid, 20, euid, 20, pid, sid, port) + bytes(addr)


def text(value):
    return b'\x28' + counted(value)


def path(value):
    return b'\x23' + counted(value)


def arg32(number, value, desc):
    return struct.pack('>BBI', 0x2d, number, value) + counted(desc)


def arg64(number, value, desc):
    return struct.pack('>BBQ', 0x71, number, value) + counted(desc)


def return32(status, value):
    return struct.pack('>BBI', 0x27, status, value)


def return64(status, value):
    return struct.pack('>BBQ', 0x72, status, value)


def identity(signing_id, team_id, cdhash, truncated=0):
    return (struct.pack('>BI', 0xed, 1) + counted(signing_id) + bytes([truncated]) + counted(team_id) + b'\x00'
            + struct.pack('>H', len(cdhash)) + cdhash)


def exec_args(*args):
    return struct.pack('>BI', 0x3c, len(args)) + b''.join(a.encode() + b'\x00' for a in args)


def in_addr(addr):
    return b'\x2a' + bytes(addr)


def record(head, *tokens):
    body = b''.join(tokens)
    size = len(head(0)) + len(body) + 7
    return head(size) + body + struct.pack('>BHI', 0x13, 0xb105, size)


def file_token(seconds, msec, name):
    return struct.pack('>BII', 0x11, seconds, msec) + counted(name)


LOGIN = record(header32(45021, 1700000000, 250), subject32(-1, 0, 0, 0, 0, 120, 100001, 7, (0, 0, 0, 0)),
               text('made-up text one'), text('made-up\ntext two'), return32(0, 0),
               identity('org.example.login', '', bytes(range(20))))
FAIL = record(header32(45023, 1700000001, 999), subject32(501, 501, 20, 501, 20, 9, 100002, 0, (10, 0, 0, 5)),
              arg32(1, 0x30, 'flags'), arg64(2, 0x1_0000_0000, 'wide'), return32(1, 4294907291))
EXEC = record(header64(23, 1700000002, 1), subject64(501, 0, 33, 100003, 2, (127, 0, 0, 1)),
              exec_args('/bin/echo', 'two words', 'x'), path('/bin/echo'), in_addr((192, 0, 2, 1)),
              return64(0, 0))
EX6 = record(header32_ex(44901, 1700000003, 5, (198, 51, 100, 7)),
             subject32_ex6(4242, 4242, 77, 100004, 3, bytes(range(16))), return32(255, 5000))
UNKNOWN = record(header32(6153, 1700000004, 0), b'\x99' + b'opaque bytes', return32(0, 0))


class ReaderTest(unittest.TestCase):
    def test_tokens_of_every_kind_written_here(self):
        counts = Counter()
        records = bsm_audit.read_trail(LOGIN + FAIL + EXEC + EX6 + UNKNOWN, counts)
        self.assertEqual(len(records), 5)
        self.assertEqual(counts, {bsm_audit.UNKNOWN_TOKEN: 1})
        login = dict(records[0]['tokens'][:2])
        self.assertEqual(login[0x14], {'size': len(LOGIN), 'version': 11, 'event': 45021, 'modifier': 0,
                                       'seconds': 1700000000, 'msec': 250})
        self.assertEqual(login[0x24], {'auid': -1, 'euid': 0, 'egid': 0, 'ruid': 0, 'rgid': 0, 'pid': 120,
                                       'sid': 100001, 'port': 7, 'addr': '0.0.0.0'})
        ident = records[0]['tokens'][-2]
        self.assertEqual(ident, (0xed, {'signer_type': 1, 'signing_id': 'org.example.login',
                                        'signing_id_truncated': 0, 'team_id': '', 'team_id_truncated': 0,
                                        'cdhash': bytes(range(20)).hex()}))
        self.assertEqual(records[0]['tokens'][-1], (0x13, {'magic': 0xb105, 'count': len(LOGIN)}))
        fail = records[1]['tokens']
        self.assertEqual(fail[2], (0x2d, {'number': 1, 'value': 0x30, 'desc': 'flags'}))
        self.assertEqual(fail[3], (0x71, {'number': 2, 'value': 0x1_0000_0000, 'desc': 'wide'}))
        self.assertEqual(fail[4], (0x27, {'status': 1, 'value': 4294907291}))
        exec_ = dict(records[2]['tokens'])
        self.assertEqual(exec_[0x74]['seconds'], 1700000002)
        self.assertEqual(exec_[0x75]['port'], 2)
        self.assertEqual(exec_[0x3c], {'strings': ['/bin/echo', 'two words', 'x']})
        self.assertEqual(exec_[0x2a], {'addr': '192.0.2.1'})
        self.assertEqual(exec_[0x72], {'status': 0, 'value': 0})
        ex6 = dict(records[3]['tokens'])
        self.assertEqual(ex6[0x15]['host'], '198.51.100.7')
        self.assertEqual(ex6[0x7a]['addr'], '1:203:405:607:809:a0b:c0d:e0f')
        # as fetch_invalid_tok does, the unknown token runs to where the trailer starts, so
        # the return token after it is inside the skipped bytes
        self.assertEqual(records[4]['tokens'][1], (0x99, {'skipped_bytes': len(b'opaque bytes') + 6}))
        self.assertEqual([t for t, _ in records[4]['tokens']], [0x14, 0x99, 0x13])

    def test_reading_stops_where_a_record_cannot_be_framed(self):
        counts = Counter()
        records = bsm_audit.read_trail(LOGIN + FAIL[:-3], counts)
        self.assertEqual(len(records), 1)
        self.assertEqual(counts[bsm_audit.TRAILING], len(FAIL) - 3)
        counts = Counter()
        self.assertEqual(bsm_audit.read_trail(b'\x00' + LOGIN, counts), [])
        self.assertEqual(counts[bsm_audit.TRAILING], len(LOGIN) + 1)

    def test_a_token_that_runs_past_its_record_ends_that_record(self):
        # a text token whose count runs past the record: the tokens before it are kept
        bad = record(header32(45021, 1, 0), return32(0, 0), b'\x28\x00\xff' + b'x' * 4)
        counts = Counter()
        records = bsm_audit.read_trail(bad + LOGIN, counts)
        self.assertEqual(len(records), 2)
        self.assertEqual([t for t, _ in records[0]['tokens']], [0x14, 0x27])
        self.assertEqual(counts[bsm_audit.SHORT_TOKEN], 1)
        self.assertEqual(counts[bsm_audit.NO_TRAILER], 1)

    def test_trailer_disagreeing_with_header_is_counted(self):
        bad = bytearray(LOGIN)
        bad[-4:] = struct.pack('>I', len(LOGIN) + 1)
        counts = Counter()
        bsm_audit.read_trail(bytes(bad), counts)
        self.assertEqual(counts[bsm_audit.BAD_TRAILER], 1)

    def test_file_token_stands_alone(self):
        records = bsm_audit.read_trail(file_token(1700000000, 3, '/var/audit/made.up') + LOGIN)
        self.assertEqual(records[0]['tokens'], [(0x11, {'seconds': 1700000000, 'msec': 3,
                                                        'name': '/var/audit/made.up'})])
        self.assertEqual(len(records), 2)

    def test_event_table_reads_like_getauevnum(self):
        table = bsm_audit.parse_event_table(
            b'# 9:AUE_X:comment:no\n6168:AUE_one:first wins:ad\n6168:AUE_two:second:ad\n'
            b'43082:AUE_RTPRIO::rtprio(2):pc\n7:AUE_ONLY\n70000:AUE_WRAP:wraps:no\n')
        self.assertEqual(table[6168], 'first wins')
        self.assertEqual(table[43082], 'rtprio(2)')
        self.assertEqual(table[7], '')
        self.assertEqual(table[70000 & 0xFFFF], 'wraps')
        self.assertNotIn(9, table)

    def test_bundled_tables(self):
        self.assertEqual(bsm_audit.BUNDLED_EVENTS[45021], 'loginwindow login')
        self.assertEqual(bsm_audit.BUNDLED_EVENTS[6168], 'system shutdown')
        self.assertNotIn(44901, bsm_audit.BUNDLED_EVENTS)
        self.assertEqual(bsm_audit.EVENT_CONSTANTS[44901], 'AUE_SESSION_START')
        self.assertEqual(bsm_audit.BSM_ERRNO[1], 'EPERM')


class FakeContext:
    def __init__(self, root, files):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, value):
        return pathlib.Path(value).relative_to(self.root).as_posix()


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        target = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'wb') as handle:
            handle.write(data)
        return target

    def _run(self, function, files):
        with mock.patch.object(macosBsmAudit, 'logfunc', self.logs.append), \
                mock.patch.object(macos_plists, 'logfunc', self.logs.append):
            return function.__wrapped__(FakeContext(self.root, files))

    def _user(self, relative, name, uid):
        return self._write(relative, plistlib.dumps({'name': [name], 'uid': [str(uid)]}))

    def test_rows_from_bundled_tables_and_named_users(self):
        trail = self._write('private/var/audit/20231114221320.not_terminated', LOGIN + FAIL + EXEC + EX6 + UNKNOWN)
        user = self._user('private/var/db/dslocal/nodes/Default/users/someone.plist', 'someone', 501)
        unused = self._user('private/var/db/dslocal/nodes/Default/users/nobody.plist', 'nobody', 777)
        headers, rows, source = self._run(macosBsmAudit.macosBsmAudit, [trail, user, unused, os.path.dirname(trail)])
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 5)
        col = {name if isinstance(name, str) else name[0]: i for i, name in enumerate(headers)}
        login, fail, exec_, ex6, unknown = rows
        self.assertEqual(login[col['Time (UTC)']], datetime.datetime(2023, 11, 14, 22, 13, 20, 250000, tzinfo=UTC))
        self.assertEqual((login[col['Event']], login[col['Event ID']], login[col['Event Name From']]),
                         ('loginwindow login', 45021, macosBsmAudit.FROM_TABLE))
        self.assertEqual((login[col['Result']], login[col['Error (BSM)']], login[col['Audit UID']],
                          login[col['Audit User']]), ('success', '', -1, ''))
        self.assertEqual(login[col['Text']], 'made-up text one\nmade-up\ntext two')
        self.assertEqual((login[col['Signing ID']], login[col['CDHash']]),
                         ('org.example.login', bytes(range(20)).hex()))
        self.assertEqual((fail[col['Result']], fail[col['Error (BSM)']], fail[col['Return Value']]),
                         ('failure', '1 (EPERM)', 4294907291))
        self.assertEqual((fail[col['Audit User']], fail[col['Effective User']], fail[col['Real User']]),
                         ('someone', 'someone', 'someone'))
        self.assertEqual((fail[col['Terminal Port']], fail[col['Terminal Address']]), (0, '10.0.0.5'))
        self.assertEqual(fail[col['Arguments']], '1 flags=0x30\n2 wide=0x100000000')
        self.assertEqual(exec_[col['Exec Args']], '/bin/echo\ntwo words\nx')
        self.assertEqual(exec_[col['Paths']], '/bin/echo')
        self.assertEqual(exec_[col['Other Tokens']], 'ip addr: addr=192.0.2.1')
        self.assertEqual((ex6[col['Event']], ex6[col['Event Name From']]),
                         ('AUE_SESSION_START', macosBsmAudit.FROM_CONSTANT))
        self.assertEqual(ex6[col['Error (BSM)']], '255')
        self.assertEqual(ex6[col['Other Tokens']], 'header: host=198.51.100.7')
        self.assertEqual((unknown[col['Other Tokens']], unknown[col['Result']]), ('token 0x99: skipped_bytes=18', ''))
        self.assertEqual(login[col['Source File']], 'private/var/audit/20231114221320.not_terminated')
        self.assertEqual(source.split('\n'), [trail, user])

    def test_the_extractions_event_table_comes_first(self):
        trail = self._write('private/var/audit/a.crash_recovery', LOGIN + EX6)
        live = self._write('private/etc/security/audit_event', b'45021:AUE_lw_login:made-up name:lo\n')
        template = self._write('System/Library/Templates/Data/private/etc/security/audit_event',
                               b'45021:AUE_lw_login:template name:lo\n44901:AUE_SESSION_START:x:aa\n')
        _headers, rows, source = self._run(macosBsmAudit.macosBsmAudit, [template, trail, live])
        self.assertEqual((rows[0][1], rows[0][3]), ('made-up name', macosBsmAudit.FROM_IMAGE))
        # a number the extraction's table lacks falls back to the bundled names, labelled
        self.assertEqual((rows[1][1], rows[1][3]), ('AUE_SESSION_START', macosBsmAudit.FROM_CONSTANT))
        self.assertEqual(source.split('\n'), [trail, live])

    def test_views_of_one_trail_are_read_once(self):
        first = self._write('private/var/audit/a.crash_recovery', LOGIN + FAIL)
        same = self._write('System/Volumes/Data/private/var/audit/a.crash_recovery', LOGIN + FAIL)
        longer = self._write('System/Volumes/Update/mnt1/private/var/audit/a.crash_recovery', LOGIN + FAIL + EXEC)
        _headers, rows, _source = self._run(macosBsmAudit.macosBsmAudit, [first, same, longer])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][-1].split('\n'), ['private/var/audit/a.crash_recovery',
                                                   'System/Volumes/Update/mnt1/private/var/audit/a.crash_recovery'])
        self.assertEqual(rows[2][-1], 'System/Volumes/Update/mnt1/private/var/audit/a.crash_recovery')
        other = self._write('private/var/audit/b.crash_recovery', LOGIN + FAIL)
        _headers, rows, _source = self._run(macosBsmAudit.macosBsmAudit, [first, other])
        self.assertEqual(len(rows), 4)

    def test_a_copy_of_the_current_link_adds_only_what_the_named_trail_lacks(self):
        named = self._write('private/var/audit/e.not_terminated', LOGIN + FAIL)
        current = self._write('private/var/audit/current', LOGIN + FAIL + EXEC)
        _headers, rows, source = self._run(macosBsmAudit.macosBsmAudit, [current, named])
        self.assertEqual([row[2] for row in rows], [45021, 45023, 23])
        self.assertEqual([row[-1] for row in rows], ['private/var/audit/e.not_terminated'] * 2
                         + ['private/var/audit/current'])
        self.assertEqual(source.split('\n'), [named, current])
        same = self._write('private/var/audit/current', LOGIN + FAIL)
        _headers, rows, source = self._run(macosBsmAudit.macosBsmAudit, [same, named])
        self.assertEqual((len(rows), source), (2, named))

    def test_files_that_are_not_trails_and_file_tokens(self):
        trail = self._write('private/var/audit/c', file_token(1700000000, 0, '/var/audit/prev') + LOGIN)
        junk = self._write('private/var/audit/notes.txt', b'not a trail')
        empty = self._write('private/var/audit/empty', b'')
        _headers, rows, source = self._run(macosBsmAudit.macosBsmAudit, [trail, junk, empty])
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0][1], rows[0][23]), (macosBsmAudit.FILE_TOKEN, '/var/audit/prev'))
        self.assertEqual(source, trail)
        self.assertTrue(any('2 files under var/audit that do not start' in line for line in self.logs))

    def test_accounts_artifact_keeps_the_listed_events(self):
        trail = self._write('private/var/audit/d', LOGIN + FAIL + EXEC + EX6 + UNKNOWN)
        _headers, rows, _source = self._run(macosBsmAudit.macosBsmAuditAccounts, [trail])
        self.assertEqual([row[2] for row in rows], [45021, 45023, 6153])

    def test_no_trail_gives_no_rows_and_no_source(self):
        table = self._write('private/etc/security/audit_event', b'1:AUE_EXIT:exit(2):pc\n')
        _headers, rows, source = self._run(macosBsmAudit.macosBsmAudit, [table])
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
