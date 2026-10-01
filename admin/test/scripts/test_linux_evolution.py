"""Pin the Evolution Data Server artifacts (scripts/artifacts/linuxEvolution.py).

CARDS, CALENDAR and TASKS are the vCards in contacts.db and the calendar.ics and tasks.ics text of
ubuntu2604_arm64_eds, byte for byte as evolution-data-server 3.56.2 stored them after the known steps (synthetic
names, dleapp.example addresses and 555 numbers). PHOTO stands in for the 1,001-byte JPEG of the capture.
"""
import base64
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxEvolution as ev
# pylint: enable=wrong-import-position

CARDS = {
    'dleapp-known-list': (
        'BEGIN:VCARD\r\n'
        'VERSION:3.0\r\n'
        'UID:dleapp-known-list\r\n'
        'FN:Known List\r\n'
        'X-EVOLUTION-LIST:TRUE\r\n'
        'X-EVOLUTION-LIST-SHOW-ADDRESSES:TRUE\r\n'
        'EMAIL;X-EVOLUTION-DEST-EMAIL="alpha.home@dleapp.example";X-EVOLUTION-DEST-N\r\n'
        ' AME="Known Alpha":Known Alpha <alpha.home@dleapp.example>\r\n'
        'EMAIL;X-EVOLUTION-DEST-EMAIL="bravo@dleapp.example";X-EVOLUTION-DEST-NAME="\r\n'
        ' Known Bravo":Known Bravo <bravo@dleapp.example>\r\n'
        'REV:2026-10-01T02:22:50Z\r\n'
        'END:VCARD'
    ),
    'dleapp-known-alpha': (
        'BEGIN:VCARD\r\n'
        'VERSION:3.0\r\n'
        'UID:dleapp-known-alpha\r\n'
        'FN:Known Alpha\r\n'
        'N:Alpha;Known;;;\r\n'
        'NICKNAME:Alfie\r\n'
        'ORG:DLEAPP Known Data;Lab\r\n'
        'TITLE:Examiner\r\n'
        'EMAIL;TYPE=HOME:alpha.home@dleapp.example\r\n'
        'EMAIL;TYPE=WORK:alpha.work@dleapp.example\r\n'
        'TEL;X-EVOLUTION-E164=5550101,"+1";TYPE=CELL:+1-555-0101\r\n'
        'TEL;X-EVOLUTION-E164=5550102,"+1";TYPE=WORK,VOICE:+1-555-0102\r\n'
        'ADR;TYPE=HOME:;;1 Known Street;Testville;PR;00901;USA\r\n'
        'BDAY:1990-03-14\r\n'
        'URL:https://dleapp.example/alpha\r\n'
        'NOTE:Known note for Alpha\\, with a comma.\r\n'
        'CATEGORIES:Known\r\n'
        'REV:2026-10-01T02:22:50Z\r\n'
        'END:VCARD'
    ),
    'dleapp-known-bravo': (
        'BEGIN:VCARD\r\n'
        'VERSION:3.0\r\n'
        'UID:dleapp-known-bravo\r\n'
        'FN:Known Bravo\r\n'
        'N:Bravo;Known;;;\r\n'
        'EMAIL:bravo.new@dleapp.example\r\n'
        'TEL;X-EVOLUTION-E164=5550104,"+1";TYPE=HOME:+1-555-0104\r\n'
        'REV:2026-10-01T02:23:02Z\r\n'
        'END:VCARD'
    ),
    'dleapp-known-delta': (
        'BEGIN:VCARD\r\n'
        'VERSION:3.0\r\n'
        'UID:dleapp-known-delta\r\n'
        'FN:Known Delta\r\n'
        'N:Delta;Known;;;\r\n'
        'EMAIL:delta@dleapp.example\r\n'
        'PHOTO;VALUE=uri:file:///home/parallels/.local/share/evolution/addressbook/s\r\n'
        ' ystem/photos/dleapp_known_delta_photo-file0.image-2FJPEG\r\n'
        'REV:2026-10-01T02:26:04Z\r\n'
        'END:VCARD'
    ),
}

CALENDAR = (
    'BEGIN:VCALENDAR\r\n'
    'CALSCALE:GREGORIAN\r\n'
    'PRODID:-//Ximian//NONSGML Evolution Calendar//EN\r\n'
    'VERSION:2.0\r\n'
    'X-EVOLUTION-DATA-REVISION:2026-10-01T02:23:08.796161Z(4)\r\n'
    'BEGIN:VEVENT\r\n'
    'UID:dleapp-known-event-allday\r\n'
    'DTSTART;VALUE=DATE:20261010\r\n'
    'DTEND;VALUE=DATE:20261011\r\n'
    'SUMMARY:Known all-day event\r\n'
    'DTSTAMP:20261001T022256Z\r\n'
    'CREATED:20261001T022256Z\r\n'
    'LAST-MODIFIED:20261001T022256Z\r\n'
    'END:VEVENT\r\n'
    'BEGIN:VEVENT\r\n'
    'UID:dleapp-known-event-weekly\r\n'
    'DTSTART;TZID=/freeassociation.sourceforge.net/America/New_York:\r\n'
    ' 20261006T090000\r\n'
    'DTEND;TZID=/freeassociation.sourceforge.net/America/New_York:\r\n'
    ' 20261006T093000\r\n'
    'RRULE;X-EVOLUTION-ENDDATE=20261020T130000Z:FREQ=WEEKLY;COUNT=3\r\n'
    'SUMMARY:Known weekly event New York\r\n'
    'DTSTAMP:20261001T022256Z\r\n'
    'CREATED:20261001T022256Z\r\n'
    'LAST-MODIFIED:20261001T022256Z\r\n'
    'END:VEVENT\r\n'
    'BEGIN:VEVENT\r\n'
    'UID:dleapp-known-event-utc\r\n'
    'DTSTART:20261005T143000Z\r\n'
    'DTEND:20261005T153000Z\r\n'
    'SUMMARY:Known meeting UTC moved\r\n'
    'LOCATION:Known Room 2\r\n'
    'DESCRIPTION:Known event in UTC\r\n'
    'DTSTAMP:20261001T022302Z\r\n'
    'LAST-MODIFIED:20261001T022302Z\r\n'
    'END:VEVENT\r\n'
    'END:VCALENDAR\r\n'
)

TASKS = (
    'BEGIN:VCALENDAR\r\n'
    'CALSCALE:GREGORIAN\r\n'
    'PRODID:-//Ximian//NONSGML Evolution Calendar//EN\r\n'
    'VERSION:2.0\r\n'
    'X-EVOLUTION-DATA-REVISION:2026-10-01T02:22:56.724177Z(0)\r\n'
    'BEGIN:VTODO\r\n'
    'UID:dleapp-known-task-open\r\n'
    'SUMMARY:Known open task\r\n'
    'DUE;VALUE=DATE:20261015\r\n'
    'STATUS:NEEDS-ACTION\r\n'
    'PRIORITY:1\r\n'
    'DTSTAMP:20261001T022256Z\r\n'
    'CREATED:20261001T022256Z\r\n'
    'LAST-MODIFIED:20261001T022256Z\r\n'
    'END:VTODO\r\n'
    'BEGIN:VTODO\r\n'
    'UID:dleapp-known-task-done\r\n'
    'SUMMARY:Known completed task\r\n'
    'STATUS:COMPLETED\r\n'
    'PERCENT-COMPLETE:100\r\n'
    'COMPLETED:20260930T120000Z\r\n'
    'DTSTAMP:20261001T022256Z\r\n'
    'CREATED:20261001T022256Z\r\n'
    'LAST-MODIFIED:20261001T022256Z\r\n'
    'END:VTODO\r\n'
    'END:VCALENDAR\r\n'
)

PHOTO = b'\xff\xd8\xff\xe0' + bytes(range(256)) + b'\xff\xd9'


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class VcardParsing(unittest.TestCase):
    def test_alpha(self):
        f = ev.contact_fields(CARDS['dleapp-known-alpha'])
        self.assertEqual(f['name'], 'Known Alpha')
        self.assertEqual(f['nickname'], 'Alfie')
        self.assertEqual(f['org'], 'DLEAPP Known Data, Lab')
        self.assertEqual(f['title'], 'Examiner')
        self.assertEqual(f['emails'], ['alpha.home@dleapp.example (home)', 'alpha.work@dleapp.example (work)'])
        self.assertEqual(f['phones'], ['+1-555-0101 (cell)', '+1-555-0102 (work, voice)'])
        self.assertEqual(f['addresses'], ['1 Known Street, Testville, PR, 00901, USA (home)'])
        self.assertEqual(f['birthday'], '1990-03-14')
        self.assertEqual(f['urls'], ['https://dleapp.example/alpha'])
        self.assertEqual(f['note'], 'Known note for Alpha, with a comma.')
        self.assertEqual(f['categories'], 'Known')
        self.assertEqual(f['rev'], '2026-10-01T02:22:50Z')
        self.assertFalse(f['list'])

    def test_list_keeps_the_quoted_parameters_apart(self):
        f = ev.contact_fields(CARDS['dleapp-known-list'])
        self.assertTrue(f['list'])
        self.assertEqual(f['emails'], ['Known Alpha <alpha.home@dleapp.example>', 'Known Bravo <bravo@dleapp.example>'])

    def test_folded_photo_uri(self):
        f = ev.contact_fields(CARDS['dleapp-known-delta'])
        self.assertEqual(f['photo_uri'], 'file:///home/parallels/.local/share/evolution/addressbook/system/photos/'
                                         'dleapp_known_delta_photo-file0.image-2FJPEG')
        self.assertIsNone(f['photo_data'])

    def test_inline_photo_and_lf_line_ends(self):
        card = ('BEGIN:VCARD\nVERSION:3.0\nUID:x\nFN:X\nPHOTO;ENCODING=b;TYPE=JPEG:' + base64.b64encode(PHOTO).decode()
                + '\nEND:VCARD')
        f = ev.contact_fields(card)
        self.assertEqual(f['photo_data'], PHOTO)
        self.assertEqual(f['photo_uri'], '')

    def test_escapes_and_structured_values(self):
        self.assertEqual(ev.unescape(r'a\,b\;c\nd\\e'), 'a,b;c\nd\\e')
        self.assertEqual(ev.split_unescaped(r'a\;b;c', ';'), ['a;b', 'c'])
        self.assertEqual(ev.parse_line('TEL;X-E164=5550101,"+1";TYPE=CELL:+1-555-0101'),
                         ('TEL', {'X-E164': ['5550101', '+1'], 'TYPE': ['CELL']}, '+1-555-0101'))
        self.assertEqual(ev.parse_line('item1.EMAIL;TYPE=INTERNET:a@b.example')[0], 'EMAIL')
        self.assertEqual(ev.parse_line('EMAIL;X-N="a:b":c@d.example')[2], 'c@d.example')
        self.assertIsNone(ev.parse_line('no colon here'))
        self.assertEqual(ev.parse_line('EMAIL;X-N="a;b";TYPE=WORK:x@y.example'),
                         ('EMAIL', {'X-N': ['a;b'], 'TYPE': ['WORK']}, 'x@y.example'))

    def test_list_flag_false(self):
        self.assertFalse(ev.contact_fields('BEGIN:VCARD\r\nX-EVOLUTION-LIST:FALSE\r\nEND:VCARD')['list'])


class Times(unittest.TestCase):
    def test_utc_stamp(self):
        self.assertEqual(ev.utc_stamp('2026-10-01T02:22:50Z'), utc(2026, 10, 1, 2, 22, 50))
        self.assertEqual(ev.utc_stamp('20261001T022256Z'), utc(2026, 10, 1, 2, 22, 56))
        self.assertIsNone(ev.utc_stamp('20261001T022256'))
        self.assertIsNone(ev.utc_stamp('2026-10-01'))

    def test_ical_time_forms(self):
        self.assertEqual(ev.ical_time('20261010', {'VALUE': ['DATE']}), ('2026-10-10', ''))
        self.assertEqual(ev.ical_time('20261005T143000Z', {}), ('2026-10-05 14:30:00 UTC', ''))
        self.assertEqual(ev.ical_time('20261006T090000', {'TZID': ['Europe/Paris']}),
                         ('2026-10-06 09:00:00', 'Europe/Paris'))
        self.assertEqual(ev.ical_time('20261006T090000', {}), ('2026-10-06 09:00:00', ''))
        self.assertEqual(ev.ical_time('garbage', {'TZID': ['Z1']}), ('garbage', 'Z1'))


class Components(unittest.TestCase):
    def test_events_and_nested_alarm(self):
        events = ev.components(CALENDAR, 'VEVENT')
        self.assertEqual([ev.prop_text(p, 'UID') for p in events],
                         ['dleapp-known-event-allday', 'dleapp-known-event-weekly', 'dleapp-known-event-utc'])
        nested = ('BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:a\r\nSUMMARY:outer\r\nBEGIN:VALARM\r\nSUMMARY:inner\r\n'
                  'END:VALARM\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n')
        got = ev.components(nested, 'VEVENT')
        self.assertEqual(len(got), 1)
        self.assertEqual(ev.prop_text(got[0], 'SUMMARY'), 'outer')
        self.assertEqual([p[0] for p in got[0]], ['UID', 'SUMMARY'])

    def test_only_top_level_components(self):
        text = ('BEGIN:VCALENDAR\r\nBEGIN:X-WRAP\r\nBEGIN:VEVENT\r\nUID:deep\r\nEND:VEVENT\r\nEND:X-WRAP\r\n'
                'BEGIN:VEVENT\r\nUID:top\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n')
        self.assertEqual([ev.prop_text(p, 'UID') for p in ev.components(text, 'VEVENT')], ['top'])
        nested = ('BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:outer\r\nSUMMARY:kept\r\nBEGIN:VEVENT\r\nUID:inner\r\n'
                  'END:VEVENT\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n')
        got = ev.components(nested, 'VEVENT')
        self.assertEqual([[p[2] for p in c] for c in got], [['outer', 'kept']])

    def test_tasks(self):
        self.assertEqual([ev.prop_text(p, 'STATUS') for p in ev.components(TASKS, 'VTODO')], ['NEEDS-ACTION', 'COMPLETED'])
        self.assertEqual(ev.components(TASKS, 'VEVENT'), [])


class FakeContext:
    def __init__(self, files, root):
        self.files, self.root = files, root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


def build_tree(root):
    book = os.path.join(root, 'home', 'u', '.local', 'share', 'evolution', 'addressbook', 'system')
    os.makedirs(os.path.join(book, 'photos'))
    db = sqlite3.connect(os.path.join(book, 'contacts.db'))
    db.execute('CREATE TABLE folder_id (uid TEXT PRIMARY KEY, Rev TEXT, vcard TEXT, bdata TEXT)')
    for uid, card in CARDS.items():
        db.execute('INSERT INTO folder_id (uid, vcard) VALUES (?, ?)', (uid, card))
    db.execute('INSERT INTO folder_id (uid, vcard) VALUES (?, ?)', ('empty', None))
    db.commit()
    db.close()
    with open(os.path.join(book, 'photos', 'dleapp_known_delta_photo-file0.image-2FJPEG'), 'wb') as handle:
        handle.write(PHOTO)
    cal = os.path.join(root, 'home', 'u', '.local', 'share', 'evolution', 'calendar', 'system')
    tasks = os.path.join(root, 'home', 'u', '.local', 'share', 'evolution', 'tasks', 'system')
    os.makedirs(cal)
    os.makedirs(tasks)
    with open(os.path.join(cal, 'calendar.ics'), 'w', newline='', encoding='utf-8') as handle:
        handle.write(CALENDAR)
    with open(os.path.join(tasks, 'tasks.ics'), 'w', newline='', encoding='utf-8') as handle:
        handle.write(TASKS)
    files = []
    for folder, _, names in os.walk(root):
        files.extend(os.path.join(folder, n) for n in names)
    return files


class ArtifactRuns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.files = build_tree(self.root)
        self.logged = []
        self.media = []
        patches = [mock.patch.object(ev, 'logfunc', self.logged.append),
                   mock.patch.object(ev, 'check_in_media', lambda p, n='': self.media.append(('file', p, n)) or 'm1'),
                   mock.patch.object(ev, 'check_in_embedded_media',
                                     lambda s, d, n='': self.media.append(('embedded', s, d)) or 'm2')]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_artifact(self, func, files=None):
        return func.__wrapped__(FakeContext(files if files is not None else self.files, self.root))

    def test_contacts(self):
        headers, rows, located = self.run_artifact(ev.linuxEvolutionContacts)
        self.assertEqual(headers[0], ('Last Changed', 'datetime'))
        self.assertEqual([r[1] for r in rows], ['Known List', 'Known Alpha', 'Known Bravo', 'Known Delta'])
        self.assertEqual([r[0] for r in rows], [utc(2026, 10, 1, 2, 22, 50), utc(2026, 10, 1, 2, 22, 50),
                                                utc(2026, 10, 1, 2, 23, 2), utc(2026, 10, 1, 2, 26, 4)])
        self.assertEqual([r[12] for r in rows], ['Yes', '', '', ''])
        self.assertEqual([r[13] for r in rows], ['', '', '', 'm1'])
        self.assertEqual(self.media[0][0], 'file')
        self.assertTrue(self.media[0][1].endswith(os.path.join('system', 'photos',
                                                               'dleapp_known_delta_photo-file0.image-2FJPEG')))
        self.assertEqual({r[15] for r in rows}, {'system'})
        self.assertEqual(rows[3][14], 'dleapp-known-delta')
        self.assertEqual(rows[1][16], os.path.join('home', 'u', '.local', 'share', 'evolution', 'addressbook', 'system',
                                                   'contacts.db'))
        self.assertTrue(located.endswith('contacts.db'))
        self.assertEqual(self.logged, ['Evolution Contacts: 1 rows with no vCard, not reported'])

    def test_contacts_photo_missing_and_inline(self):
        files = [f for f in self.files if 'photos' not in f]
        _, rows, _ = self.run_artifact(ev.linuxEvolutionContacts, files)
        self.assertEqual(rows[3][13], '')
        self.assertIn('1 photo files named by a contact and not in the extraction', self.logged[0])
        db_path = [f for f in self.files if f.endswith('contacts.db')][0]
        db = sqlite3.connect(db_path)
        card = ('BEGIN:VCARD\r\nVERSION:3.0\r\nUID:inline\r\nFN:Inline\r\nREV:20261001T000000\r\n'
                'PHOTO;ENCODING=b;TYPE=JPEG:' + base64.b64encode(PHOTO).decode() + '\r\nEND:VCARD')
        db.execute('INSERT INTO folder_id (uid, vcard) VALUES (?, ?)', ('inline', card))
        db.commit()
        db.close()
        self.media.clear()
        self.logged.clear()
        _, rows, _ = self.run_artifact(ev.linuxEvolutionContacts)
        self.assertEqual(rows[-1][13], 'm2')
        self.assertEqual(rows[-1][0], '')
        self.assertEqual(self.media[-1][2], PHOTO)
        self.assertIn('1 REV values not in UTC, left blank', self.logged[0])

    def test_uid_comes_from_the_vcard_and_falls_back_to_the_row(self):
        db_path = [f for f in self.files if f.endswith('contacts.db')][0]
        db = sqlite3.connect(db_path)
        db.execute('INSERT INTO folder_id (uid, vcard) VALUES (?, ?)', ('row-a', 'BEGIN:VCARD\r\nUID:card-a\r\nFN:A\r\nEND:VCARD'))
        db.execute('INSERT INTO folder_id (uid, vcard) VALUES (?, ?)', ('row-b', 'BEGIN:VCARD\r\nFN:B\r\nEND:VCARD'))
        db.commit()
        db.close()
        _, rows, _ = self.run_artifact(ev.linuxEvolutionContacts)
        self.assertEqual([r[14] for r in rows[-2:]], ['card-a', 'row-b'])

    def test_not_a_contacts_store(self):
        bad = os.path.join(self.root, 'x', 'addressbook', 'b', 'contacts.db')
        os.makedirs(os.path.dirname(bad))
        sqlite3.connect(bad).execute('CREATE TABLE other (a)').connection.close()
        _, rows, located = self.run_artifact(ev.linuxEvolutionContacts, [bad])
        self.assertEqual((rows, located), ([], ''))
        self.assertEqual(self.logged, ['Evolution Contacts: 1 files with no folder_id table, not reported'])

    def test_events(self):
        headers, rows, located = self.run_artifact(ev.linuxEvolutionEvents)
        self.assertEqual(headers[7], ('Created', 'datetime'))
        self.assertEqual([r[0] for r in rows], ['2026-10-10', '2026-10-06 09:00:00', '2026-10-05 14:30:00 UTC'])
        self.assertEqual(rows[1][2], '/freeassociation.sourceforge.net/America/New_York')
        self.assertEqual(rows[1][6], 'FREQ=WEEKLY;COUNT=3')
        self.assertEqual(rows[2][4:6], ('Known Room 2', 'Known event in UTC'))
        self.assertEqual([r[7] for r in rows], [utc(2026, 10, 1, 2, 22, 56), utc(2026, 10, 1, 2, 22, 56), ''])
        self.assertEqual(rows[2][8], utc(2026, 10, 1, 2, 23, 2))
        self.assertEqual({r[10] for r in rows}, {'system'})
        self.assertTrue(located.endswith('calendar.ics'))
        self.assertEqual(self.logged, [])

    def test_tasks(self):
        _, rows, located = self.run_artifact(ev.linuxEvolutionTasks)
        self.assertEqual(rows[0][:7], ('2026-10-15', '', 'Known open task', '', 'NEEDS-ACTION', '1', ''))
        self.assertEqual(rows[1][4:8], ('COMPLETED', '', '100', utc(2026, 9, 30, 12, 0, 0)))
        self.assertEqual(rows[1][11], 'system')
        self.assertTrue(located.endswith('tasks.ics'))

    def test_zones_and_other_files(self):
        path = [f for f in self.files if f.endswith('calendar.ics')][0]
        extra = ('BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:z1\r\nDTSTART;TZID=Europe/Paris:20261001T100000\r\nEND:VEVENT\r\n'
                 'BEGIN:VEVENT\r\nUID:z2\r\nDTSTART;TZID=Europe/Paris:20261001T100000\r\n'
                 'DTEND;TZID=Asia/Tokyo:20261001T180000\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n')
        with open(path, 'w', newline='', encoding='utf-8') as handle:
            handle.write(extra)
        backup = path + '~'
        with open(backup, 'w', newline='', encoding='utf-8') as handle:
            handle.write(CALENDAR)
        _, rows, _ = self.run_artifact(ev.linuxEvolutionEvents, self.files + [backup])
        self.assertEqual([(r[9], r[2]) for r in rows], [('z1', 'Europe/Paris'), ('z2', 'Europe/Paris\nAsia/Tokyo')])

    def test_floating_created_is_counted(self):
        path = [f for f in self.files if f.endswith('calendar.ics')][0]
        with open(path, 'w', newline='', encoding='utf-8') as handle:
            handle.write(CALENDAR.replace('CREATED:20261001T022256Z', 'CREATED:20261001T022256', 1))
        _, rows, _ = self.run_artifact(ev.linuxEvolutionEvents)
        self.assertEqual(rows[0][7], '')
        self.assertEqual(self.logged, ['Evolution Calendar Events: 1 CREATED values not in UTC, left blank'])

    def test_empty_calendar_is_not_located(self):
        path = [f for f in self.files if f.endswith('calendar.ics')][0]
        with open(path, 'w', newline='', encoding='utf-8') as handle:
            handle.write('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n')
        _, rows, located = self.run_artifact(ev.linuxEvolutionEvents)
        self.assertEqual((rows, located), ([], ''))


if __name__ == '__main__':
    unittest.main()
