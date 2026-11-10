"""Pin the routing and file handling of the Outlook PST and OST artifacts
(scripts/outlook_pst.py, scripts/artifacts/outlookPst.py).

Item classes are routed by prefix, case-insensitively, as [MS-OXCMSG] 2.2.1.3 says
matching on PidTagMessageClass is done. Every expected value is written out here, never
read back from the code.
"""
import fnmatch
import os
import pathlib
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


if __name__ == '__main__':
    unittest.main()
