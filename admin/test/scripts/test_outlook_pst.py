"""Pin the routing, file handling and binary decoders of the Outlook PST and OST artifacts
(scripts/outlook_pst.py, scripts/artifacts/outlookPst.py, scripts/artifacts/outlookAutocomplete.py).

Item classes are routed by prefix, case-insensitively, as [MS-OXCMSG] 2.2.1.3 says
matching on PidTagMessageClass is done. Every expected value is written out here, never
read back from the code.
"""
import fnmatch
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import outlook_pst as O  # pylint: disable=wrong-import-position
from scripts.artifacts import outlookPst  # pylint: disable=wrong-import-position


class Routing(unittest.TestCase):
    def test_each_kind(self):
        cases = {
            'IPM.Note': 'email', 'IPM.Note.SMIME': 'email', 'IPM.Schedule.Meeting.Request': 'email',
            'IPM.TaskRequest': 'email', 'REPORT.IPM.Note.NDR': 'email', 'IPM.Post': 'email',
            'IPM.Contact': 'contact', 'IPM.DistList': 'contact', 'IPM.Appointment': 'appointment',
            'IPM.Task': 'task', 'IPM.StickyNote': 'note', 'IPM.Activity': 'journal',
        }
        for message_class, kind in cases.items():
            with self.subTest(message_class=message_class):
                self.assertEqual(O.kind_of(message_class), kind)

    def test_case_insensitive(self):
        self.assertEqual(O.kind_of('ipm.contact'), 'contact')
        self.assertEqual(O.kind_of('IPM.APPOINTMENT.Custom'), 'appointment')

    def test_prefix_ends_at_a_period(self):
        # IPM.TaskRequest continues "IPM.Task" without a period, so it is not a task
        self.assertEqual(O.kind_of('IPM.TaskRequest.Accept'), 'email')
        self.assertEqual(O.kind_of('IPM.Contacts'), 'email')

    def test_excluded_classes(self):
        for message_class in ('IPM.Microsoft.ScheduleData.FreeBusy', 'IPM.AbchPerson', 'IPM.Network'):
            with self.subTest(message_class=message_class):
                self.assertIsNone(O.kind_of(message_class))

    def test_missing_class_is_reported_under_emails(self):
        self.assertEqual(O.kind_of(None), 'email')
        self.assertEqual(O.kind_of(''), 'email')


class Paths(unittest.TestCase):
    def test_patterns_match_either_case(self):
        patterns = outlookPst.__artifacts_v2__['outlookPstEmails']['paths']
        for name in ('root/Users/a/Documents/Outlook Files/x.pst', 'root/Users/a/x.PST',
                     'root/Users/a/AppData/Local/Microsoft/Outlook/a@b.ost', 'root/a/B.Ost'):
            with self.subTest(name=name):
                self.assertTrue(any(fnmatch.fnmatchcase(name, p) for p in patterns))
        for name in ('root/a/x.pst.tmp', 'root/a/x.nst', 'root/a/xpst'):
            with self.subTest(name=name):
                self.assertFalse(any(fnmatch.fnmatchcase(name, p) for p in patterns))

    def test_every_artifact_reads_the_same_files(self):
        paths = {info['paths'] for info in outlookPst.__artifacts_v2__.values()}
        self.assertEqual(paths, {('*.[pP][sS][tT]', '*.[oO][sS][tT]')})


class UniqueFiles(unittest.TestCase):
    def test_identical_copy_left_out_and_users_copy_kept(self):
        with tempfile.TemporaryDirectory() as root:
            def write(rel, data):
                path = os.path.join(root, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                return path
            firm = write('System/Volumes/Data/Users/a/x.pst', b'same bytes')
            users = write('Users/a/x.pst', b'same bytes')
            other = write('Users/b/x.pst', b'same size!')     # same size, other bytes
            counts = Counter()
            kept = O.unique_files([firm, users, other], lambda p: os.path.relpath(p, root), counts)
            self.assertEqual(kept, [users, other])
            self.assertEqual(counts['byte-identical copies of a file already read, not read again'], 1)


class Values(unittest.TestCase):
    def test_task_no_date_value_is_blank(self):
        counts = Counter()
        r = O.Reader(counts)
        self.assertEqual(r.time(datetime(4501, 1, 1, tzinfo=timezone.utc), no_date_sentinel=True), '')
        self.assertEqual(counts['task dates holding the no-date value, left blank'], 1)
        when = datetime(2026, 11, 30, tzinfo=timezone.utc)
        self.assertEqual(r.time(when, no_date_sentinel=True), when)
        self.assertEqual(r.time(datetime(4501, 1, 1, tzinfo=timezone.utc)).year, 4501)

    def test_undecoded_string_is_shown_as_hex(self):
        counts = Counter()
        self.assertEqual(O.Reader(counts).text(b'\x01\x02'), '0102')
        self.assertEqual(counts['string values shown as hexadecimal because they did not decode'], 1)

    def test_visible_text(self):
        markup = ('<html><head><title>t</title><style>p{}</style></head>'
                  '<body><p>Hello &amp; welcome</p><div>second<br>third</div></body></html>')
        self.assertEqual(O.visible_text(markup), 'Hello & welcome\nsecond\nthird')

    def test_html_body_uses_its_code_page(self):
        class _PC:
            def __init__(self, codepage):
                self.codepage = codepage

            def get(self, pid):
                return self.codepage if pid == 0x3FDE else None

        class _Message:
            def __init__(self, codepage):
                self.pc = _PC(codepage)

        data = '<p>caf\u00e9 \u20ac5</p>'.encode('cp1252')     # not valid UTF-8
        counts = Counter()
        self.assertEqual(O.decode_html(_Message(1252), data, O.Reader(counts)), '<p>caf\u00e9 \u20ac5</p>')
        utf8 = '<p>caf\u00e9</p>'.encode('utf-8')
        self.assertEqual(O.decode_html(_Message(None), utf8, O.Reader(counts)), '<p>caf\u00e9</p>')
        self.assertEqual(counts['HTML bodies with bytes their code page does not decode, replaced'], 0)

    def test_storage_attachment_is_listed_not_opened(self):
        class _Attachment:
            def __init__(self, method, embedded):
                self.method, self.is_embedded_message, self.filename = method, embedded, 'a.bin'

            def embedded_message(self):
                raise AssertionError('an afStorage attachment must not be opened as an item')

        class _Message:
            def attachments(self):
                return [_Attachment(6, True), _Attachment(1, False)]

        counts = Counter()
        found = list(O.file_attachments(_Message(), O.Reader(counts)))
        self.assertEqual([a.method for _within, a in found], [6, 1])
        self.assertEqual(counts['attachments in an application-specific format (afStorage), listed without data'], 1)
        self.assertEqual(counts['attached items that could not be read'], 0)

    def test_enum_names_and_unknown_values(self):
        self.assertEqual(outlookPst._enum(2, outlookPst._BUSY), 'Busy')  # pylint: disable=protected-access
        self.assertEqual(outlookPst._enum(9, outlookPst._TASK_STATUS), '9 (as stored)')  # pylint: disable=protected-access
        self.assertEqual(outlookPst._enum(None, outlookPst._NOTE_COLOR), '')  # pylint: disable=protected-access


def _ac_prop(tag, value):
    """One autocomplete property: tag, reserved, 8-byte union, then the value data."""
    ptype = tag & 0xFFFF
    if ptype == 0x0003:
        return struct.pack('<II', tag, 0) + struct.pack('<i', value) + b'\0' * 4
    data = value.encode('utf-16-le') + b'\0\0'
    return struct.pack('<II', tag, 0) + b'\0' * 8 + struct.pack('<I', len(data)) + data


def _ac_stream(rows, major=12, extra=b'', tail=8):
    body = struct.pack('<IIII', 0xBAADF00D, major, 0, len(rows))
    for row in rows:
        body += struct.pack('<I', len(row)) + b''.join(_ac_prop(t, v) for t, v in row)
    return body + struct.pack('<I', len(extra)) + extra + b'\0' * tail


class Autocomplete(unittest.TestCase):
    ROW = [(0x6001001F, 'nick'), (0x3001001F, 'Name'), (0x3003001F, 'a@example.com'), (0x60040003, 8192)]

    def test_rows_decode(self):
        minor, rows = O.parse_autocomplete(_ac_stream([self.ROW, self.ROW[:2]]))
        self.assertEqual(minor, 0)
        self.assertEqual(rows[0], {0x6001001F: 'nick', 0x3001001F: 'Name', 0x3003001F: 'a@example.com',
                                   0x60040003: 8192})
        self.assertEqual(rows[1], {0x6001001F: 'nick', 0x3001001F: 'Name'})

    def test_extra_information_is_skipped(self):
        self.assertEqual(len(O.parse_autocomplete(_ac_stream([self.ROW], extra=b'xyz'))[1]), 1)

    def test_layout_errors_refuse(self):
        for data in (_ac_stream([self.ROW], major=11), _ac_stream([self.ROW], tail=9),
                     _ac_stream([self.ROW], tail=7), _ac_stream([self.ROW])[:40],
                     _ac_stream([[(0x60050099, 'x')]])):
            with self.subTest(size=len(data)):
                with self.assertRaises(O.AutocompleteError):
                    O.parse_autocomplete(data)


def _one_off(name, addrtype, address, unicode_=True):
    flags = 0x0180 if unicode_ else 0x0100
    enc = (lambda t: t.encode('utf-16-le') + b'\0\0') if unicode_ else (lambda t: t.encode('cp1252') + b'\0')
    return (b'\0' * 4 + O.ONE_OFF_UID + b'\0\0' + flags.to_bytes(2, 'big')
            + enc(name) + enc(addrtype) + enc(address))


class OneOff(unittest.TestCase):
    def test_unicode_and_ansi(self):
        self.assertEqual(O.parse_one_off(_one_off('N', 'SMTP', 'n@example.com')), ('N', 'SMTP', 'n@example.com'))
        self.assertEqual(O.parse_one_off(_one_off('N', 'SMTP', 'n@example.com', False)),
                         ('N', 'SMTP', 'n@example.com'))

    def test_not_a_one_off(self):
        self.assertIsNone(O.parse_one_off(b'\0' * 4 + O.WRAPPED_UID + b'\0' * 8))
        self.assertIsNone(O.parse_one_off(_one_off('N', 'SMTP', 'n@example.com') + b'x'))

    def test_wrapped_one_off_whatever_the_type_byte(self):
        # Outlook 16 wrote Type 0xB5 (a GAL user in [MS-OXOCNTC]) around a One-Off EntryID
        wrapped = b'\0' * 4 + O.WRAPPED_UID + b'\xb5' + _one_off('N', 'SMTP', 'n@example.com')
        self.assertEqual(O._member_entry(wrapped, None, None, O.Reader(Counter())),  # pylint: disable=protected-access
                         ('N <n@example.com>', None, None))


class DistributionList(unittest.TestCase):
    class _Message:
        pst = None

        def __init__(self, members, one_offs):
            self.values = {O.LID_DL_MEMBERS: members, O.LID_DL_ONE_OFF_MEMBERS: one_offs}

    def _members(self, message, counts):
        reader = O.Reader(counts)
        reader.named = lambda m, guid, lid: m.values.get(lid)
        return O.dl_members(message, None, None, reader)

    def test_one_off_array_wins_by_position(self):
        foreign = b'\0' * 4 + O.WRAPPED_UID + b'\xc3' + b'\0' * 4 + b'\x11' * 16 + b'\x24\0\x20\0'
        counts = Counter()
        text = self._members(self._Message([foreign, _one_off('B', 'SMTP', 'b@example.com')],
                                           [_one_off('A', 'SMTP', 'a@example.com'),
                                            _one_off('B', 'SMTP', 'b@example.com')]), counts)
        self.assertEqual(text, 'A <a@example.com>\nB <b@example.com>')
        self.assertEqual(sum(counts.values()), 0)

    def test_foreign_entry_without_one_off_is_shown_and_counted(self):
        foreign = b'\0' * 4 + O.WRAPPED_UID + b'\xc3' + b'\0' * 4 + b'\x11' * 16 + b'\x24\0\x20\0'
        counts = Counter()
        self.assertEqual(self._members(self._Message([foreign], None), counts), '[entry ' + foreign.hex() + ']')
        self.assertEqual(counts['distribution list members whose entry is not of this file, shown as stored'], 1)


def _minutes(y, m, d, hh=0, mm=0):
    return int((datetime(y, m, d, hh, mm) - datetime(1601, 1, 1)).total_seconds() // 60)


def _recur(exception=True, writer2=0x3009, trailing=b'', moved_day=5, pattern=0x0000):
    """A daily series of 10 from 2026-12-01 09:00 with 12-03 deleted and 12-05 moved to 14:00
    on day moved_day."""
    deleted = [_minutes(2026, 12, 3), _minutes(2026, 12, 5)] if exception else []
    modified = [_minutes(2026, 12, moved_day)] if exception else []
    b = struct.pack('<5H', 0x3004, 0x3004, 0x200A, pattern, 0) + struct.pack('<3I', 0, 1440, 0)
    if pattern == 0x0001:
        b += struct.pack('<I', 0x3E)
    b += struct.pack('<3I', 0x2022, 10, 0)
    b += struct.pack('<I', len(deleted)) + b''.join(struct.pack('<I', d) for d in deleted)
    b += struct.pack('<I', len(modified)) + b''.join(struct.pack('<I', d) for d in modified)
    b += struct.pack('<2I', _minutes(2026, 12, 1), _minutes(2026, 12, 10))
    b += struct.pack('<4I', 0x3006, writer2, 540, 570)
    b += struct.pack('<H', len(modified))
    subject, location = 'moved', 'room'
    if exception:
        b += struct.pack('<3IH', _minutes(2026, 12, moved_day, 14), _minutes(2026, 12, moved_day, 14, 30),
                         _minutes(2026, 12, 5, 9), 0x11)
        b += struct.pack('<2H', len(subject) + 1, len(subject)) + subject.encode()
        b += struct.pack('<2H', len(location) + 1, len(location)) + location.encode()
    b += struct.pack('<I', 0)
    if exception:
        if writer2 >= 0x3009:
            b += struct.pack('<II', 4, 0)
        b += struct.pack('<I', 0) + b'\0' * 12
        b += struct.pack('<H', len(subject)) + subject.encode('utf-16-le')
        b += struct.pack('<H', len(location)) + location.encode('utf-16-le')
        b += struct.pack('<I', 0)
    return b + struct.pack('<I', 0) + trailing


class Recurrence(unittest.TestCase):
    def test_series_and_exception(self):
        r = O.parse_recurrence(_recur())
        self.assertEqual(O.describe_pattern(r), 'Daily, Day, every 1 day(s)')
        self.assertEqual(r['end_type'], 0x2022)
        self.assertEqual(r['occurrences'], 10)
        self.assertEqual(O.minutes_to_local(r['end_date']), datetime(2026, 12, 10))
        self.assertEqual(r['exceptions'][0]['subject'], 'moved')
        self.assertEqual(r['exceptions'][0]['location'], 'room')
        self.assertEqual(O.minutes_to_local(r['exceptions'][0]['start']), datetime(2026, 12, 5, 14))

    def test_writer_3008_has_no_change_highlight(self):
        self.assertEqual(O.parse_recurrence(_recur(writer2=0x3008))['exceptions'][0]['subject'], 'moved')

    def test_no_exceptions(self):
        self.assertEqual(O.parse_recurrence(_recur(exception=False))['exceptions'], [])

    def test_layout_errors_refuse(self):
        for data in (_recur(trailing=b'\0'), _recur()[:-1], b'\x05\x30' + _recur()[2:]):
            with self.subTest(size=len(data)):
                with self.assertRaises(O.RecurrenceError):
                    O.parse_recurrence(data)

    def test_moved_to_another_day_is_not_a_deleted_occurrence(self):
        class _Message:
            pass
        reader = O.Reader(Counter())
        reader.named = lambda m, guid, lid: _recur(moved_day=6)
        columns = O.recurrence_columns(_Message(), reader)
        self.assertEqual(columns[2], '2026-12-03')
        self.assertEqual(columns[3], '2026-12-05 09:00 moved to 2026-12-06 14:00 to 2026-12-06 14:30'
                                     ' | Subject: moved | Location: room')

    def test_daily_week_pattern_period_shown_as_stored(self):
        r = O.parse_recurrence(_recur(exception=False, pattern=0x0001))
        self.assertEqual(O.describe_pattern(r), 'Daily, Week, Mon,Tue,Wed,Thu,Fri, Period 1440')

    def test_columns(self):
        class _Message:
            pass
        reader = O.Reader(Counter())
        reader.named = lambda m, guid, lid: _recur()
        self.assertEqual(O.recurrence_columns(_Message(), reader),
                         ('Daily, Day, every 1 day(s); end after 10 occurrences', '2026-12-10', '2026-12-03',
                          '2026-12-05 09:00 moved to 2026-12-05 14:00 to 2026-12-05 14:30 | Subject: moved | Location: room'))


if __name__ == '__main__':
    unittest.main()
