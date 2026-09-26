"""Pin the ASL reader in scripts/artifacts/macosASL.py.

The files below are written from the record layout in the comment of Apple's asl_file.h
(syslog-406): an 80-byte header, STR records (type 1, length, text and NUL) and MSG
records (type 0, length, then Next, ID, Time, Nano, Level, Flags, PID, UID, GID, RUID,
RGID, RefPID, KV count, six string references, the key/value references and Previous).
A string reference with its top bit set holds up to seven bytes inline. Expected values
are written out, never read back from the reader.
"""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosASL as asl  # pylint: disable=wrong-import-position

HEADER_LEN = 80


def inline(text):
    raw = text.encode('utf-8')
    return int.from_bytes(bytes([0x80 | len(raw)]) + raw.ljust(7, b'\0'), 'big')


def str_record(text):
    raw = text.encode('utf-8') + b'\0'
    return struct.pack('>HI', 1, len(raw)) + raw


def msg_record(fields, strings, pairs, nxt, prev=0):
    """fields: mid, time, nano, level, pid, uid, gid, ruid, rgid, refpid."""
    mid, time, nano, level, pid, uid, gid, ruid, rgid, refpid = fields
    body = struct.pack('>QQQIHHIIIIIII', nxt, mid, time, nano, level, 0, pid, uid, gid, ruid, rgid,
                       refpid, len(pairs) * 2)
    body += b''.join(struct.pack('>Q', ref) for ref in strings)
    body += b''.join(struct.pack('>QQ', key, value) for key, value in pairs)
    body += struct.pack('>Q', prev)
    return struct.pack('>HI', 0, len(body)) + body


def header(first, version=2):
    head = b'ASL DB'.ljust(12, b'\0') + struct.pack('>IQQIBQ', version, first, 0, 0, 0, 0)
    return head.ljust(HEADER_LEN, b'\0')


def two_message_file():
    """A STR record then two chained messages; returns the bytes and the message offsets."""
    text = str_record('USER_PROCESS: 139 console')
    user = str_record('thisisdfir')
    str_at, user_at = HEADER_LEN, HEADER_LEN + len(text)
    first_at = user_at + len(user)
    strings = [inline('Mac'), inline('login'), inline('auth'), str_at, 0, 0]
    placeholder = msg_record((1, 1613404746, 430159000, 5, 139, 0xFFFFFFFF, 20, 0xFFFFFFFF, 80, 0),
                             strings, [(inline('ut_user'), user_at), (inline('ut_type'), inline('7'))], 0)
    second_at = first_at + len(placeholder)
    first = msg_record((1, 1613404746, 430159000, 5, 139, 0xFFFFFFFF, 20, 0xFFFFFFFF, 80, 0),
                       strings, [(inline('ut_user'), user_at), (inline('ut_type'), inline('7'))],
                       second_at)
    second = msg_record((2, 1613431506, 0, 3, 4477, 0, 0, 0xFFFFFFFF, 80, 7),
                        [inline('Mac'), inline('shut'), inline('daemon'), inline('bye'), 0, 0],
                        [(inline('k'), 0)], 0, prev=first_at)
    return header(first_at) + text + user + first + second, first_at, second_at


class ReadTest(unittest.TestCase):
    def test_chain_fields_strings_and_pairs(self):
        data, first_at, second_at = two_message_file()
        records, problem = asl.read_asl(data)
        self.assertIsNone(problem)
        self.assertEqual([r['offset'] for r in records], [first_at, second_at])
        one, two = records
        self.assertEqual((one['mid'], one['time'], one['nano'], one['level'], one['pid']),
                         (1, 1613404746, 430159000, 5, 139))
        self.assertEqual((one['host'], one['sender'], one['facility'], one['message']),
                         ('Mac', 'login', 'auth', 'USER_PROCESS: 139 console'))
        self.assertIsNone(one['refproc'])
        self.assertEqual(one['pairs'], [('ut_user', 'thisisdfir'), ('ut_type', '7')])
        self.assertEqual(two['pairs'], [('k', None)])
        self.assertEqual((two['refpid'], two['level'], two['message']), (7, 3, 'bye'))

    def test_next_offset_going_back_stops(self):
        data, first_at, second_at = two_message_file()
        start = second_at + 6
        looped = data[:start] + struct.pack('>Q', first_at) + data[start + 8:]
        records, problem = asl.read_asl(looped)
        self.assertEqual(len(records), 2)
        self.assertEqual(problem, f'stopped at offset {second_at}: the next offset goes back')

    def test_other_versions_and_files_are_not_read(self):
        data, first_at, _ = two_message_file()
        self.assertEqual(asl.read_asl(header(first_at, version=1) + data[HEADER_LEN:]),
                         ([], 'ASL version 1, not read'))
        self.assertEqual(asl.read_asl(b'bplist00' + bytes(100)), ([], 'not an ASL file'))

    def test_bad_strings_stop_the_file(self):
        with self.assertRaises(asl.AslError):
            asl.fetch_string(b'', int.from_bytes(bytes([0x88]) + bytes(7), 'big'))
        unterminated = bytes(HEADER_LEN) + struct.pack('>HI', 1, 3) + b'abc'
        with self.assertRaises(asl.AslError):
            asl.fetch_string(unterminated, HEADER_LEN)


class HelperTest(unittest.TestCase):
    def test_times(self):
        # 1613404746 is 2021-02-15 15:59:06 UTC; 430159000 ns is 430159 us.
        self.assertEqual(asl.record_time(1613404746, 430159000),
                         datetime(2021, 2, 15, 15, 59, 6, 430159, tzinfo=timezone.utc))
        self.assertEqual(asl.entry_time([('ut_tv.tv_sec', '1613404746'), ('ut_tv.tv_usec', '430159')]),
                         datetime(2021, 2, 15, 15, 59, 6, 430159, tzinfo=timezone.utc))
        self.assertEqual(asl.entry_time([]), '')

    def test_names(self):
        self.assertEqual(asl.level_name(5), 'Notice (5)')
        self.assertEqual(asl.level_name(9), '9')
        self.assertEqual(asl.event_name([('ut_type', '7')]), 'USER_PROCESS (7)')
        self.assertEqual(asl.event_name([('ut_type', '11')]), 'SHUTDOWN_TIME (11)')
        self.assertEqual(asl.event_name([('ut_type', '42')]), '42')
        self.assertEqual(asl.optional_id(0xFFFFFFFF), '')
        self.assertEqual(asl.keys_text([('a', '1'), ('b', None)], ('a',)), 'b: ')


class _Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class UnionTest(unittest.TestCase):
    def _write(self, root, relative, data):
        path = os.path.join(root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def test_two_copies_are_one_store(self):
        full, first_at, second_at = two_message_file()
        # The earlier copy ends after the first message, whose Next was still 0 then.
        start = first_at + 6
        earlier = full[:start] + struct.pack('>Q', 0) + full[start + 8:second_at]
        with tempfile.TemporaryDirectory() as root:
            later_path = self._write(root, 'System/Volumes/Data/private/var/log/asl/2021.02.15.G80.asl', full)
            earlier_path = self._write(root, 'private/var/log/asl/2021.02.15.G80.asl', earlier)
            records, sources = asl.collect(_Context(root, [later_path, earlier_path]), 'asl', 'test')
        self.assertEqual([r['mid'] for r in records], [1, 2])
        self.assertEqual(sources, [earlier_path, later_path])

    def test_differing_records_at_one_offset_are_both_kept(self):
        full, first_at, _ = two_message_file()
        at = full.index(b'USER_PROCESS')
        changed = full[:at] + b'DEAD' + full[at + 4:]
        with tempfile.TemporaryDirectory() as root:
            one = self._write(root, 'private/var/log/asl/a.asl', full)
            two = self._write(root, 'System/Volumes/Data/private/var/log/asl/a.asl', changed)
            records, _ = asl.collect(_Context(root, [one, two]), 'asl', 'test')
        self.assertEqual(sorted(r['message'] for r in records if r['offset'] == first_at),
                         ['DEAD_PROCESS: 139 console', 'USER_PROCESS: 139 console'])

    def test_only_files_directly_in_the_folder(self):
        full, _, _ = two_message_file()
        with tempfile.TemporaryDirectory() as root:
            nested = self._write(root, 'private/var/log/asl/Logs/x.asl', full)
            other = self._write(root, 'private/var/log/aslx/y.asl', full)
            records, sources = asl.collect(_Context(root, [nested, other]), 'asl', 'test')
        self.assertEqual((records, sources), ([], []))


if __name__ == '__main__':
    unittest.main()
