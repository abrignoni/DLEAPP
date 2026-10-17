"""Pin how the phoneLink* artifacts read Phone Link's per-device databases.

Author: @AlexisBrignoni, Claude.

Every database here is synthetic, built with the column layout of the tables Phone Link
1.24101.61.0 writes (the CREATE TABLE text of those files, trimmed to the columns read).
The expected values are written out, never read back from the code under test.
"""
import datetime
import fnmatch
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsPhoneLink as link  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
PACKAGE = 'C/Users/{user}/AppData/Local/Packages/Microsoft.YourPhone_8wekyb3d8bbwe'
DATABASE = PACKAGE + '/LocalCache/Indexed/{device}/System/Database'
# 2024-11-04 15:33:34.623 UTC as a FILETIME and as Unix milliseconds.
FILETIME = 133752080146230000
UNIX_MS = 1730734414623
WHEN = datetime.datetime(2024, 11, 4, 15, 33, 34, 623000, tzinfo=UTC)
JPEG = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00' + b'\x00' * 64
PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64

PHONE_SCHEMA = '''
CREATE TABLE conversation(thread_id INTEGER PRIMARY KEY, recipient_list TEXT NOT NULL,
    timestamp INTEGER NOT NULL DEFAULT 0, msg_count INTEGER, unread_count INTEGER);
CREATE TABLE message(message_id INTEGER PRIMARY KEY, thread_id INTEGER NOT NULL,
    status INTEGER NOT NULL, from_address TEXT, type INTEGER, subject TEXT, body TEXT NOT NULL,
    timestamp INTEGER NOT NULL, pc_status INTEGER, subscription_id INTEGER NOT NULL DEFAULT -1,
    checksum INTEGER NOT NULL DEFAULT 0, group_id INTEGER);
CREATE TABLE message_to_address(message_id INTEGER NOT NULL, address TEXT NOT NULL,
    PRIMARY KEY (message_id, address));
CREATE TABLE mms(message_id INTEGER PRIMARY KEY, thread_id INTEGER NOT NULL,
    status INTEGER NOT NULL, type INTEGER, subscription_id INTEGER NOT NULL DEFAULT -1,
    subject TEXT, charset INTEGER, timestamp INTEGER NOT NULL, pc_status INTEGER,
    from_address TEXT, checksum INTEGER NOT NULL DEFAULT 0);
CREATE TABLE mms_address(message_id INTEGER NOT NULL, contact_id INTEGER NOT NULL,
    address TEXT, type INTEGER, charset INTEGER, PRIMARY KEY (message_id, address));
CREATE TABLE mms_part(part_id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL,
    sequence_num INTEGER, content_id TEXT, content_type TEXT, text TEXT, name TEXT,
    charset INTEGER, blob BLOB, size INTEGER NOT NULL DEFAULT 0);
CREATE TABLE participant(id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id INTEGER NOT NULL,
    send_address TEXT NOT NULL, normalized_address TEXT NOT NULL);
CREATE TABLE subscription(subscription_id INTEGER PRIMARY KEY, sim_slot_index INTEGER NOT NULL,
    country_iso TEXT NOT NULL, name TEXT, is_roaming INTEGER NOT NULL, number TEXT NOT NULL);
'''


class PhoneLinkTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _db(self, user, device, name, script, rows=()):
        folder = self.root / DATABASE.format(user=user, device=device)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        with sqlite3.connect(path) as db:
            db.executescript(script)
            for statement, values in rows:
                db.execute(statement, values)
        db.close()
        self.files.append(str(path))
        return path

    def _run(self, function):
        context = SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())
        checked = []

        def check_in(_source, data, name, **kwargs):
            checked.append((name, kwargs.get('force_type'), len(data)))
            return f'ref:{name}'
        with mock.patch.object(link, 'logfunc') as log, \
                mock.patch.object(link, 'check_in_embedded_media', side_effect=check_in):
            result = getattr(link, function).__wrapped__(context)
        return result, checked, [call.args[0] for call in log.call_args_list]

    def _phone(self, user='jdoe', device='dev-1'):
        return self._db(user, device, 'phone.db', PHONE_SCHEMA, [
            ('INSERT INTO conversation VALUES (?,?,?,?,?)', (4, '5550100', FILETIME, 2, 0)),
            ('INSERT INTO conversation VALUES (?,?,?,?,?)', (7, '5550199', FILETIME, 1, 1)),
            ('INSERT INTO participant VALUES (?,?,?,?)', (1, 4, '555-0100', '+15550100')),
            ('INSERT INTO message VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
             (1, 4, 1, '5550100', 1, '', 'hello', FILETIME, 1, 1, 0, -1)),
            ('INSERT INTO message VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
             (2, 4, 2, '', 2, '', 'reply', FILETIME + 10_000_000, 2, 1, 1, -1)),
            ('INSERT INTO message VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
             (3, 4, 2, '', 3, '', 'draft', FILETIME + 20_000_000, 2, 1, 1, -1)),
            ('INSERT INTO message_to_address VALUES (?,?)', (2, '5550100')),
            ('INSERT INTO mms VALUES (?,?,?,?,?,?,?,?,?,?,?)',
             (2, 7, 2, 1, 1, 'pic', 0, FILETIME - 10_000_000, 1, '5550199', 1)),
            ('INSERT INTO mms_address VALUES (?,?,?,?,?)', (2, 0, '5550199', 137, 106)),
            ('INSERT INTO mms_part VALUES (?,?,?,?,?,?,?,?,?,?)',
             (10, 2, 1, '<1>', 'image/jpeg', None, 'IMG.jpg', 0, JPEG, len(JPEG))),
            ('INSERT INTO mms_part VALUES (?,?,?,?,?,?,?,?,?,?)',
             (9, 2, 0, '<0>', 'text/plain', 'look', '', 106, None, 0)),
            ('INSERT INTO mms_part VALUES (?,?,?,?,?,?,?,?,?,?)',
             (8, 2, -1, '<smil>', 'application/smil', '<smil><body/></smil>', '', 106, None, 0)),
            ('INSERT INTO subscription VALUES (?,?,?,?,?,?)', (1, 0, 'us', 'SIM one', 1, '15550123')),
        ])

    def test_sms_and_mms_rows_with_direction_type_and_mms_media(self):
        self._phone()
        (headers, rows, source), checked, _log = self._run('phoneLinkMessages')
        self.assertEqual(len(headers), len(rows[0]))
        tail = ('dev-1', 'jdoe', DATABASE.format(user='jdoe', device='dev-1') + '/phone.db')
        self.assertEqual(rows, [
            (WHEN - datetime.timedelta(seconds=1), 'Incoming', '5550199', '5550199', 'look',
             ['ref:IMG.jpg'], 'image/jpeg', 'pic', 'MMS', 'MESSAGE_BOX_INBOX (1)', 2, 1,
             '5550199', 1, 7, 2) + tail,
            (WHEN, 'Incoming', '5550100', '555-0100', 'hello', [], '', '', 'SMS',
             'MESSAGE_TYPE_INBOX (1)', 1, 1, '', 1, 4, 1) + tail,
            (WHEN + datetime.timedelta(seconds=1), 'Outgoing', '', '555-0100', 'reply', [], '', '',
             'SMS', 'MESSAGE_TYPE_SENT (2)', 2, 2, '5550100', 1, 4, 2) + tail,
            (WHEN + datetime.timedelta(seconds=2), '', '', '555-0100', 'draft', [], '', '', 'SMS',
             'MESSAGE_TYPE_DRAFT (3)', 2, 2, '', 1, 4, 3) + tail,
        ])
        self.assertEqual(checked, [('IMG.jpg', 'image/jpeg', len(JPEG))])
        self.assertEqual(source.split('\n'), [str(self.root / tail[2])])

    def test_two_users_and_two_devices_keep_their_own_rows(self):
        self._phone('alice', 'dev-1')
        self._phone('alice', 'dev-2')
        self._phone('bob', 'dev-1')
        (_headers, rows, source), _checked, _log = self._run('phoneLinkMessages')
        self.assertEqual(sorted({(row[-3], row[-2]) for row in rows}),
                         [('dev-1', 'alice'), ('dev-1', 'bob'), ('dev-2', 'alice')])
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(source.split('\n')), 3)

    def test_a_phone_db_outside_a_device_database_folder_is_not_read(self):
        folder = self.root / PACKAGE.format(user='jdoe') / 'LocalCache'
        folder.mkdir(parents=True)
        path = folder / 'phone.db'
        with sqlite3.connect(path) as db:
            db.executescript(PHONE_SCHEMA)
        db.close()
        self.files.append(str(path))
        (_headers, rows, source), _checked, _log = self._run('phoneLinkMessages')
        self.assertEqual((rows, source), ([], ''))

    def test_a_file_that_is_not_sqlite_is_logged_and_left_out(self):
        folder = self.root / DATABASE.format(user='jdoe', device='dev-1')
        folder.mkdir(parents=True)
        (folder / 'phone.db').write_bytes(b'not a database' * 100)
        self.files.append(str(folder / 'phone.db'))
        (_headers, rows, source), _checked, log = self._run('phoneLinkMessages')
        self.assertEqual((rows, source), ([], ''))
        self.assertTrue(any(line.startswith('Phone Link Messages: could not') for line in log))

    def test_subscriptions(self):
        self._phone()
        (headers, rows, _source), _checked, _log = self._run('phoneLinkSubscriptions')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][:5], (1, 0, '15550123', 'SIM one', 'us'))

    def test_photos_prefer_the_full_image_and_fall_back_to_the_thumbnail(self):
        schema = '''CREATE TABLE media(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            last_updated_time INTEGER NOT NULL, taken_time INTEGER NOT NULL, orientation TEXT,
            last_seen_time INTEGER, mime_type TEXT NOT NULL, height INTEGER NOT NULL,
            width INTEGER NOT NULL, size INTEGER NOT NULL, uri TEXT NOT NULL, thumbnail BLOB,
            media BLOB, checksum INTEGER NOT NULL DEFAULT 0);'''
        self._db('jdoe', 'dev-1', 'photos.db', schema, [
            ('INSERT INTO media VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
             (5, 'a.jpg', 133752080140000000, FILETIME, '0', FILETIME, 'image/jpeg', 40, 30, 900,
              'content://media/external/images/media/5', JPEG, None, 0)),
            ('INSERT INTO media VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
             (6, 'b.png', FILETIME, FILETIME, None, None, 'image/png', 40, 30, 900,
              'content://media/external/images/media/6', JPEG, PNG, 0)),
        ])
        (headers, rows, _source), checked, _log = self._run('phoneLinkPhotos')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][:13], (
            WHEN, datetime.datetime(2024, 11, 4, 15, 33, 34, tzinfo=UTC), WHEN, 'ref:thumbnail_a.jpg',
            'thumbnail', 'a.jpg', 'image/jpeg', 30, 40, 900, '0',
            'content://media/external/images/media/5', 5))
        self.assertEqual(rows[1][2:5], ('', 'ref:b.png', 'media and thumbnail'))
        self.assertEqual(checked, [('thumbnail_a.jpg', 'image/jpeg', len(JPEG)),
                                   ('b.png', 'image/png', len(PNG))])

    def test_phone_apps_read_unix_milliseconds_and_render_the_icon(self):
        schema = '''CREATE TABLE phone_apps(app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL, package_name TEXT NOT NULL UNIQUE, version TEXT NOT NULL,
            etag INTEGER NOT NULL, favorite_rank INTEGER, blob BLOB, last_updated_time INTEGER,
            checksum INTEGER NOT NULL DEFAULT 0, phoneapp_web_url TEXT);'''
        self._db('jdoe', 'dev-1', 'phoneapps.db', schema, [
            ('INSERT INTO phone_apps VALUES (?,?,?,?,?,?,?,?,?,?)',
             (99, 'Maps', 'com.example.maps', '1.2', 0, -1, PNG, UNIX_MS, UNIX_MS, '')),
            ('INSERT INTO phone_apps VALUES (?,?,?,?,?,?,?,?,?,?)',
             (98, 'Clock', 'com.example.clock', '3', 0, -1, b'\x00\x01not an image', None, 0, '')),
        ])
        (headers, rows, _source), checked, log = self._run('phoneLinkPhoneApps')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual([row[:5] for row in rows], [
            ('', 'Clock', 'com.example.clock', '3', ''),
            (WHEN, 'Maps', 'com.example.maps', '1.2', 'ref:com.example.maps_icon')])
        self.assertEqual(checked, [('com.example.maps_icon', 'image/png', len(PNG))])
        self.assertTrue(any('has no recognised type' in line for line in log))

    def test_contacts_group_their_details(self):
        schema = '''
        CREATE TABLE contact(contact_id INTEGER PRIMARY KEY, display_name TEXT, nickname TEXT,
            last_updated_time INTEGER, thumbnail BLOB, company TEXT, job_title TEXT, notes TEXT,
            name_prefix TEXT, name_suffix TEXT, given_name TEXT, middle_name TEXT,
            family_name TEXT, checksum INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE phonenumber(phone_number_id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL, phone_number TEXT NOT NULL, display_phone_number TEXT,
            phone_number_type INTEGER NOT NULL DEFAULT 0, label TEXT,
            checksum INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE emailaddress(email_address_id INTEGER PRIMARY KEY, contact_id INTEGER NOT NULL,
            type INTEGER NOT NULL DEFAULT 0, label TEXT, address TEXT NOT NULL,
            checksum INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE postaladdress(postal_address_id INTEGER PRIMARY KEY,
            contact_id INTEGER NOT NULL, type INTEGER NOT NULL DEFAULT 0, label TEXT,
            display_address TEXT, checksum INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE contactdate(contact_date_id INTEGER PRIMARY KEY, contact_id INTEGER NOT NULL,
            date_type INTEGER NOT NULL DEFAULT 0, label TEXT, display_date TEXT NOT NULL,
            checksum INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE contacturl(contact_url_id INTEGER PRIMARY KEY, contact_id INTEGER NOT NULL,
            type INTEGER NOT NULL DEFAULT 0, label TEXT, url_address TEXT NOT NULL,
            checksum INTEGER NOT NULL DEFAULT 0);'''
        self._db('jdoe', 'dev-1', 'contacts.db', schema, [
            ('INSERT INTO contact (contact_id, display_name, last_updated_time, given_name, '
             'family_name, company) VALUES (?,?,?,?,?,?)', (3, 'Pat Doe', FILETIME, 'Pat', 'Doe', 'Acme')),
            ('INSERT INTO phonenumber (contact_id, phone_number, phone_number_type) VALUES (?,?,?)',
             (3, '5550100', 2)),
            ('INSERT INTO phonenumber (contact_id, phone_number, phone_number_type, label) '
             'VALUES (?,?,?,?)', (3, '5550101', 8, 'Boat')),
            ('INSERT INTO emailaddress (contact_id, type, address) VALUES (?,?,?)',
             (3, 1, 'pat@example.com')),
        ])
        (headers, rows, _source), _checked, _log = self._run('phoneLinkContacts')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][:16], (
            WHEN, 'Pat Doe', 'Pat', '', 'Doe', '', 'Acme', '', '', '5550100 [2]\n5550101 (Boat) [8]',
            'pat@example.com [1]', '', '', '', '', 3))

    def test_calls_keep_the_stored_start_time(self):
        schema = '''CREATE TABLE call_history(call_id INTEGER NOT NULL PRIMARY KEY,
            phone_number TEXT NOT NULL, duration INTEGER, call_type INTEGER NOT NULL,
            start_time INTEGER NOT NULL, is_read INTEGER, phone_account_id TEXT,
            last_updated_time INTEGER);'''
        self._db('jdoe', 'dev-1', 'calling.db', schema, [
            ('INSERT INTO call_history VALUES (?,?,?,?,?,?,?,?)',
             (8, '5550100', 61, 1, FILETIME, 1, 'acct', FILETIME)),
        ])
        (headers, rows, _source), _checked, _log = self._run('phoneLinkCalls')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][:9], (WHEN, WHEN, FILETIME, '5550100', 61, 1, 1, 'acct', 8))

    def test_the_paths_match_the_device_databases_and_not_a_lookalike(self):
        block = link.__artifacts_v2__
        patterns = block['phoneLinkMessages']['paths']
        def hits(relative):
            return [p for p in patterns if fnmatch.fnmatchcase('root/' + relative, p)]
        folder = DATABASE.format(user='u', device='abcd1234')
        self.assertEqual(len(hits(folder + '/phone.db')), 1)
        self.assertEqual(len(hits(folder + '/phone.db-wal')), 1)
        self.assertEqual(hits(folder + '/photos.db'), [])
        self.assertEqual(hits('C/Users/u/AppData/Local/Packages/Contoso.Phone_abc/LocalCache/'
                              'Indexed/d/System/Database/phone.db'), [])


if __name__ == '__main__':
    unittest.main()
