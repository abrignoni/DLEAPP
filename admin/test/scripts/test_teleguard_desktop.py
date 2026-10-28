"""Pins the TeleGuard Windows reader in scripts/artifacts/teleguardDesktop.py.

Every store below is written by this file: the ids, names, texts and times are
authored for the test and no part of them comes from a real client. The
framework's media check-in is replaced by a marker function, because the media
context it reads belongs to the decorator, not to the parser.
"""

from contextlib import closing
import hashlib
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import teleguardDesktop  # pylint: disable=wrong-import-position
import scripts.teleguard_desktop as tg_helper  # pylint: disable=wrong-import-position

STORE = tg_helper.DB_NAME

# The columns the tested store declares. A store written without the optional
# ones stands for an older client.
MESSAGE_COLUMNS = ('id', 'chatId', 'sender', 'parentId', 'receiver', 'content',
                   'createDate', 'type', 'userTime', 'status', 'isEdited',
                   'metadata')
CONTACT_COLUMNS = ('serverId', 'alias', 'type', 'color', 'avatar',
                   'lastActivityTime', 'options', 'info', 'lastVisitTime',
                   'personalId')

# 2025-06-02 07:00 UTC, the time every message of the basic store carries; the
# expected value in the tests is this instant named in words.
BASE_TIME = 1748847600000
BASE_STAMP = '2025-06-02 07:00:00'

from admin.test.scripts.make_teleguard_desktop_fixture import (  # pylint: disable=wrong-import-position
    JPEG, JPEG_SECOND, PNG, build_external)


def write_store(directory, messages, contacts, account=None,
                message_columns=MESSAGE_COLUMNS,
                contact_columns=CONTACT_COLUMNS):
    """Write a synthetic store of the tested layout into `directory`."""
    path = os.path.join(directory, STORE)
    connection = sqlite3.connect(path)
    try:
        def declare(names):
            numeric = ('createDate', 'userTime', 'lastActivityTime',
                       'lastVisitTime', 'isEdited')
            return ', '.join(f'{name} INTEGER' if name in numeric
                             else f'{name} TEXT' for name in names)
        connection.execute(f'CREATE TABLE messages({declare(message_columns)})')
        connection.execute('CREATE TABLE service(id TEXT, data TEXT)')
        connection.execute(f'CREATE TABLE contacts({declare(contact_columns)})')
        for row in messages:
            connection.execute('INSERT INTO messages ('
                               + ', '.join(message_columns) + ') VALUES ('
                               + ', '.join('?' * len(message_columns)) + ')',
                               row)
        for row in contacts:
            connection.execute('INSERT INTO contacts ('
                               + ', '.join(contact_columns) + ') VALUES ('
                               + ', '.join('?' * len(contact_columns)) + ')',
                               row)
        if account:
            connection.execute('INSERT INTO service(id, data) VALUES (?, ?)',
                               ('user', json.dumps(account)))
    finally:
        # close() alone drops the buffered writes, so the store is committed
        # first: the parser reads the file back through a second connection.
        connection.commit()
        connection.close()
    return path


def media_marker(path, name=None, **_kwargs):
    """The stand-in for the framework's media check-in of a staged file."""
    return f'media:{name or os.path.basename(str(path))}'


def embedded_marker(_source, _data, **_kwargs):
    """The stand-in for the framework's check-in of bytes held in the store."""
    return 'media:embedded'


def note_collector(notes):
    """A logfunc stand-in that keeps what a parser reported."""
    return notes.append


class Context:
    """The part of the framework context a parser reads."""

    def __init__(self, files, root):
        self.files = files
        self.root = root

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return str(pathlib.Path(str(path)).relative_to(self.root))


class StoreTest(unittest.TestCase):
    """Runs the parser over stores written by this file."""

    def setUp(self):
        """Keeps the last temporary store alive for the length of a test."""
        self.temporary = None

    def tearDown(self):
        if self.temporary is not None:
            self.temporary.close()

    def parse(self, artifact, files, root):
        """The (headers, rows) a parser returns, plus what it logged."""
        notes = []
        with patch.multiple(
                teleguardDesktop,
                check_in_media=media_marker,
                check_in_embedded_media=embedded_marker,
                logfunc=note_collector(notes)), \
                patch.multiple(tg_helper,
                               logfunc=note_collector(notes)):
            headers, rows, _source = getattr(
                teleguardDesktop, artifact).__wrapped__(Context(files, root))
        names = [head[0] if isinstance(head, tuple) else head
                 for head in headers]
        return names, rows, notes

    def basic(self):
        """A store with two conversations, a media reference and a quote."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'AppData' / 'teleguard_desktop'
            app.mkdir(parents=True)
            (app / 'example_photo.jpeg').write_bytes(JPEG)
            write_store(app, (
                ('m1', 'c1', 'u1', None, 'u2', 'Hello there', BASE_TIME,
                 'TEXT', BASE_TIME + 400, 'READ', 0,
                 '{"client-version":"9.9.1","ttl":30}'),
                ('m2', 'c1', 'u2', None, 'u1', 'Hallo', BASE_TIME + 60000,
                 'TEXT', BASE_TIME + 60001, 'READ', 1,
                 '{"client-version":"9.9.1"}'),
                ('m3', 'c2', 'u1', None, 'u3', 'Foto?', BASE_TIME + 120000,
                 'MEDIA', BASE_TIME + 120001, 'READ', 0,
                 '{"mediaFiles":[{"id":"media-1","name":"example_photo.jpeg",'
                 '"mediaType":"IMAGE","order":0,"duration":null,'
                 '"aspectRatio":1.33,"blurHash":"Q0","cacheName":'
                 '"example_photo.jpeg","thumbnailCacheName":"example_photo.jpeg"}],'
                 '"mediaType":"IMAGE"}'),
                ('m4', 'c2', 'u3', None, 'u1',
                 json.dumps({'de': 'Viola', 'en': 'Violet'}), BASE_TIME + 180000,
                 'QUOTE', BASE_TIME + 180001, 'READ', 0,
                 '{"isLocalized":1,"quote":"Hallo","messageId":"m2",'
                 '"author":"u2","quotedMessageType":"TEXT"}'),
                ('m5', 'c2', None, None, 'u1', 'system line', BASE_TIME + 240000,
                 'SERVICE', None, 'STATIC', 0, '{}'),
                ('m6', 'c1', 'u9', None, 'u1', 'unknown kind', BASE_TIME + 300000,
                 'WIDGET', BASE_TIME + 300001, 'READ', 0,
                 '{"client-version":"9.9.1"}'),
            ), (
                ('u1', 'Alice', 'PERSON', None, JPEG, BASE_TIME, '{"key":1}',
                 '{"avatarId":"a1"}', BASE_TIME, 'p1'),
                ('u2', 'Bob', 'PERSON', None, None, None, None, None, None, None),
                ('u3', 'Carolin', 'PERSON', None, PNG, None, None, None, None, None),
                ('c2', 'Example Group', 'GROUP', None, None, None, None, None,
                 None, None),
            ), account={'serverId': 'u1', 'alias': 'Alice',
                        'privateKey': 'secret-key'})
            yield [str(app / STORE), str(app / 'example_photo.jpeg')], root

    def keep(self, generator):
        """The first value of a temporary-store generator, kept alive.

        A generator suspended at its yield still holds its TemporaryDirectory
        open, so the paths it yields can be read until the test ends. The
        generator itself is kept on the test object for as long as those paths
        are used."""
        self.temporary = generator
        return next(generator)

    def by_id(self, headers, rows, column):
        """The rows keyed by one column, so a test can name the row it reads."""
        return {row[headers.index(column)]: row for row in rows}

    def test_rows_are_reported_for_every_message(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        self.assertEqual(len(rows), 6)
        first = self.by_id(headers, rows, 'Message ID')['m1']
        self.assertEqual(first[headers.index('Timestamp')].strftime(
            '%Y-%m-%d %H:%M:%S'), BASE_STAMP)
        self.assertEqual(first[headers.index('Client Time')].strftime(
            '%Y-%m-%d %H:%M:%S'), BASE_STAMP)
        self.assertEqual(first[headers.index('Direction')], 'Outgoing')
        self.assertEqual(first[headers.index('Sender')], 'Alice')
        self.assertEqual(first[headers.index('Sender ID')], 'u1')
        self.assertEqual(first[headers.index('Recipient ID')], 'u2')
        self.assertEqual(first[headers.index('Chat ID')], 'c1')
        self.assertEqual(first[headers.index('Conversation')], 'c1')
        self.assertEqual(first[headers.index('Recipient')], 'Bob')
        self.assertEqual(first[headers.index('Client Version')], '9.9.1')
        self.assertEqual(first[headers.index('Status (as stored)')], 'READ')
        self.assertEqual(first[headers.index('Edited (as stored)')], 0)
        self.assertEqual(first[headers.index('Metadata (as stored)')],
                         '{"client-version":"9.9.1","ttl":30}')

    def test_a_foreign_author_is_incoming(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m2']
        self.assertEqual(row[headers.index('Direction')], 'Incoming')
        self.assertEqual(row[headers.index('Sender')], 'Bob')
        self.assertEqual(row[headers.index('Edited (as stored)')], 1)

    def test_an_empty_author_leaves_the_direction_blank(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m5']
        self.assertEqual(row[headers.index('Direction')], '')
        self.assertEqual(row[headers.index('Sender')], '')
        self.assertEqual(row[headers.index('Message')], 'system line')
        self.assertEqual(row[headers.index('Client Time')], '')

    def test_an_unknown_type_is_passed_through(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m6']
        self.assertEqual(row[headers.index('Message Type')], 'WIDGET')

    def test_an_unresolved_reference_keeps_its_id(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m6']
        self.assertEqual(row[headers.index('Sender')], 'u9')
        self.assertEqual(row[headers.index('Conversation')], 'c1')

    def test_a_language_map_resolves_to_one_value(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m4']
        self.assertEqual(row[headers.index('Message')], 'Viola')
        self.assertEqual(row[headers.index('Quoted Text')], 'Hallo')
        self.assertEqual(row[headers.index('Quoted Message ID')], 'm2')
        self.assertEqual(row[headers.index('Quote Author')], 'Bob')
        self.assertEqual(row[headers.index('Quoted Message Type')], 'TEXT')

    def test_media_is_shown_when_the_file_is_staged(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m3']
        self.assertEqual(row[headers.index('Media')],
                         ['media:example_photo.jpeg'])
        self.assertEqual(row[headers.index('Media File Names')],
                         'example_photo.jpeg')
        self.assertEqual(row[headers.index('Media Type')], 'IMAGE')
        self.assertEqual(row[headers.index('Media Durations')], None)
        self.assertEqual(self.by_id(headers, rows, 'Message ID')['m1']
                         [headers.index('Media')], None)

    def test_two_stores_holding_the_same_ids_stay_apart(self):
        """Two profiles with the same stored ids keep their rows apart."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            staged = []
            for profile in ('first', 'second'):
                app = root / profile / 'teleguard_desktop'
                app.mkdir(parents=True)
                write_store(app, (
                    ('m1', 'c1', 'u1', None, 'u1', 'same id', BASE_TIME,
                     'TEXT', BASE_TIME, 'READ', 0, '{}'),),
                    (('u1', 'Alice', 'PERSON', None, None, None, None, None,
                      None, None),),
                    account={'serverId': 'u1', 'alias': 'Alice'})
                staged.append(str(app / STORE))
            headers, rows, _notes = self.parse('teleguardMessages', staged, root)
            self.assertEqual(len(rows), 2)
            keys = sorted(row[headers.index('Conversation ID')]
                          for row in rows)
            self.assertEqual(len(keys), 2)
            self.assertEqual([key.split(' :: ')[1] for key in keys],
                             ['c1', 'c1'])
            self.assertIn('first', keys[0])
            self.assertIn('second', keys[1])

    def test_the_same_store_staged_twice_is_read_once(self):
        """Two `paths` patterns matching one file do not double the rows."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'teleguard_desktop'
            app.mkdir(parents=True)
            write_store(app, (
                ('m1', 'c1', 'u1', None, 'u1', 'one', BASE_TIME, 'TEXT',
                 BASE_TIME, 'READ', 0, '{}'),
                ('m2', 'c1', 'u2', None, 'u1', 'two', BASE_TIME + 1, 'TEXT',
                 BASE_TIME + 1, 'READ', 0, '{}'),),
                (('u1', 'Alice', 'PERSON', None, None, None, None, None, None,
                  None),),
                account={'serverId': 'u1', 'alias': 'Alice'})
            once = [str(app / STORE)]
            _headers, single, _notes = self.parse('teleguardMessages', once, root)
            _headers, again, _notes = self.parse(
                'teleguardMessages', once + once, root)
            self.assertEqual(len(single), 2)
            self.assertEqual(len(again), len(single))

    def test_a_store_without_the_optional_columns_still_yields_rows(self):
        """An older store lacking `userTime` and `parentId` keeps its rows."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'teleguard_desktop'
            app.mkdir(parents=True)
            write_store(app, (
                ('m1', 'c1', 'u1', 'u1', 'older', BASE_TIME, 'TEXT',
                 'READ', 0, '{}'),),
                (('u1', 'Alice', 'PERSON'),),
                account={'serverId': 'u1', 'alias': 'Alice'},
                message_columns=('id', 'chatId', 'sender', 'receiver',
                                 'content', 'createDate', 'type', 'status',
                                 'isEdited', 'metadata'),
                contact_columns=('serverId', 'alias', 'type'))
            staged = [str(app / STORE)]
            headers, rows, _notes = self.parse('teleguardMessages', staged, root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][headers.index('Message')], 'older')
            self.assertEqual(rows[0][headers.index('Client Time')], '')
            self.assertEqual(rows[0][headers.index('Source File')],
                             (pathlib.Path('teleguard_desktop') / STORE).as_posix())
            _headers, contacts, _notes = self.parse('teleguardContacts', staged, root)
            self.assertEqual(len(contacts), 1)
            self.assertEqual(contacts[0][_headers.index('Personal ID')], None)
            self.assertEqual(contacts[0][_headers.index('Last Activity')], '')

    def test_a_store_without_the_account_leaves_direction_blank(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'teleguard_desktop'
            app.mkdir(parents=True)
            write_store(app, (
                ('m1', 'c1', 'u1', None, 'u1', 'no account', BASE_TIME,
                 'TEXT', BASE_TIME, 'READ', 0, '{}'),),
                ())
            headers, rows, notes = self.parse(
                'teleguardMessages', [str(app / STORE)], root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][headers.index('Direction')], '')
            self.assertEqual(rows[0][headers.index('Sender')], 'u1')
            self.assertIn('no unique account row in service', ' '.join(notes))

    def test_a_foreign_database_yields_no_rows(self):
        """A SQLite file that is not the client's store is not parsed."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'teleguard_desktop'
            app.mkdir(parents=True)
            other = sqlite3.connect(str(app / STORE))
            try:
                other.execute('CREATE TABLE unrelated(kind TEXT)')
            finally:
                other.commit()
                other.close()
            _headers, rows, notes = self.parse(
                'teleguardMessages', [str(app / STORE)], root)
            self.assertEqual(rows, [])
            logged = ' '.join(notes)
            self.assertIn('declares no messages table', logged)

    def test_a_sidecar_is_not_read_as_a_store(self):
        """A `-wal` beside the store does not add rows of its own."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'teleguard_desktop'
            app.mkdir(parents=True)
            write_store(app, (
                ('m1', 'c1', 'u1', None, 'u1', 'one', BASE_TIME, 'TEXT',
                 BASE_TIME, 'READ', 0, '{}'),),
                ())
            (app / f'{STORE}-wal').write_bytes(b'')
            main = str(app / STORE)
            _headers, single, _notes = self.parse('teleguardMessages',
                                                [main], root)
            _headers, with_sidecar, _notes = self.parse(
                'teleguardMessages', [main, str(app / f'{STORE}-wal')], root)
            self.assertEqual(len(with_sidecar), len(single))

    def test_contacts_count_their_own_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            app = root / 'teleguard_desktop'
            app.mkdir(parents=True)
            write_store(app, (
                ('m1', 'c1', 'u1', None, 'u2', 'one', BASE_TIME, 'TEXT',
                 BASE_TIME, 'READ', 0, '{}'),
                ('m2', 'c1', 'u2', None, 'u1', 'two', BASE_TIME + 1, 'TEXT',
                 BASE_TIME + 1, 'READ', 0, '{}'),
                ('m3', 'u1', 'u1', None, 'u2', 'in own chat', BASE_TIME + 2,
                 'TEXT', BASE_TIME + 2, 'READ', 0, '{}'),),
                (('u1', 'Alice', 'PERSON', None, JPEG, BASE_TIME, '{"key":1}',
                  '{"avatarId":"a1"}', BASE_TIME, 'p1'),
                 ('u2', 'Bob', 'PERSON', None, None, None, None, None, None,
                  None),
                 ('u3', 'Carolin', 'PERSON', None, PNG, None, None, None, None,
                  None)),
                account={'serverId': 'u1', 'alias': 'Alice'})
            headers, rows, _notes = self.parse('teleguardContacts',
                                             [str(app / STORE)], root)
            by_contact = self.by_id(headers, rows, 'Contact ID')
            self.assertEqual(len(rows), 3)
            alice = by_contact['u1']
            self.assertEqual(alice[headers.index('Messages In This Chat')], 1)
            self.assertEqual(alice[headers.index('Messages Sent')], 2)
            self.assertEqual(alice[headers.index('Messages Received')], 1)
            self.assertEqual(alice[headers.index('Last Activity')].strftime(
                '%Y-%m-%d %H:%M:%S'), BASE_STAMP)
            self.assertEqual(alice[headers.index('Personal ID')], 'p1')
            self.assertEqual(alice[headers.index('Options (as stored)')],
                             '{"key":1}')
            self.assertEqual(alice[headers.index('Avatar')], 'media:embedded')
            self.assertEqual(by_contact['u3'][headers.index('Avatar')],
                             'media:embedded')
            self.assertEqual(by_contact['u2'][headers.index('Messages In This Chat')],
                             0)
            self.assertEqual(by_contact['u2'][headers.index('Messages Sent')], 1)
            self.assertEqual(by_contact['u2'][headers.index('Messages Received')], 2)
            self.assertEqual(by_contact['u3'][headers.index('Messages Sent')], 0)

    def test_the_chat_overview_counts_match_the_messages(self):
        files, root = self.keep(self.basic())
        _headers, message_rows, _notes = self.parse(
            'teleguardMessages', files, root)
        headers, rows, _notes = self.parse('teleguardChatOverview', files, root)
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(row[headers.index('Messages Total')]
                             for row in rows), len(message_rows))
        first = self.by_id(headers, rows, 'Chat ID')['c1']
        self.assertEqual(first[headers.index('Messages Total')], 3)
        self.assertEqual(first[headers.index('Outgoing')], 1)
        self.assertEqual(first[headers.index('Incoming')], 2)
        self.assertEqual(first[headers.index('Direction Unknown')], 0)
        self.assertEqual(first[headers.index('Participants')], 3)
        self.assertEqual(first[headers.index('Messages By Type')], 'TEXT: 2, WIDGET: 1')
        self.assertEqual(first[headers.index('Conversation')], 'c1')
        self.assertEqual(first[headers.index('Chat Type')], None)
        second = self.by_id(headers, rows, 'Chat ID')['c2']
        self.assertEqual(second[headers.index('Conversation')], 'Example Group')
        self.assertEqual(second[headers.index('Chat Type')], 'GROUP')
        self.assertEqual(second[headers.index('Direction Unknown')], 1)
        self.assertEqual(second[headers.index('First Message')].strftime(
            '%Y-%m-%d %H:%M:%S'), '2025-06-02 07:02:00')

    def test_media_references_name_every_reference(self):
        files, root = self.keep(self.basic())
        headers, rows, _notes = self.parse('teleguardMediaReferences', files, root)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[headers.index('Media File Name')],
                         'example_photo.jpeg')
        self.assertEqual(row[headers.index('Media')], 'media:example_photo.jpeg')
        self.assertEqual(row[headers.index('Media ID')], 'media-1')
        self.assertEqual(row[headers.index('Blur Hash (as stored)')], 'Q0')
        self.assertEqual(row[headers.index('Cache Name')],
                         'example_photo.jpeg')
        self.assertEqual(row[headers.index('Aspect Ratio (as stored)')], 1.33)
        self.assertEqual(row[headers.index('Order (as stored)')], 0)
        self.assertEqual(row[headers.index('Message ID')], 'm3')
        self.assertEqual(row[headers.index('Conversation ID')].split(' :: ')[1],
                         'c2')



    def temporary_root(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return pathlib.Path(temporary.name)

    @staticmethod
    def message(identifier='m1', metadata='{}', timestamp=BASE_TIME):
        return (identifier, 'c1', 'u1', None, 'u2', 'Authored text', timestamp,
                'TEXT', timestamp, 'READ', 0, metadata)

    def test_equal_media_names_resolve_inside_their_own_profiles(self):
        root = self.temporary_root()
        files, expected = [], {}
        for profile, data in (('first', JPEG), ('second', JPEG_SECOND)):
            app = root / profile / 'teleguard_desktop'
            app.mkdir(parents=True)
            path = write_store(app, [self.message(metadata=json.dumps({
                'mediaFiles': [{'name': 'photo.jpg'}]}))], [], {'serverId': 'u1'})
            media = app / 'photo.jpg'
            media.write_bytes(data)
            files.extend([path, str(media)])
            expected[pathlib.Path(path).relative_to(root).as_posix()] = str(media)
        with patch.object(teleguardDesktop, 'check_in_media',
                          side_effect=lambda path, **_kwargs: str(path)):
            headers, rows, _ = teleguardDesktop.teleguardMessages.__wrapped__(Context(files, root))
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row[names.index('Media')],
                             [expected[row[names.index('Source File')]]])

    def test_parent_expiry_value_and_presence_are_not_media_resolution_states(self):
        root = self.temporary_root()
        states = ({'isContentExpired': True}, {'isContentExpired': False},
                  {'isContentExpired': None}, {})
        messages = []
        for number, state in enumerate(states):
            metadata = dict(state, mediaFiles=[{'name': 'photo.jpg'}, {'name': 'missing.jpg'}])
            messages.append(self.message(str(number), json.dumps(metadata)))
        store = write_store(root, messages, [])
        media = root / 'photo.jpg'
        media.write_bytes(JPEG)
        headers, rows, _ = self.parse('teleguardMediaReferences', [store, str(media)], root)
        self.assertEqual(len(rows), 8)
        for row in rows:
            state = states[int(row[headers.index('Message ID')])]
            self.assertIs(row[headers.index('Content Expired (as stored)')], state.get('isContentExpired'))
            self.assertEqual(row[headers.index('Content Expired Field Present')],
                             'Yes' if 'isContentExpired' in state else 'No')
            if row[headers.index('Media File Name')] == 'photo.jpg':
                self.assertEqual(row[headers.index('Reference Status')], 'Matched')
                self.assertTrue(row[headers.index('Media')])
            else:
                self.assertEqual(row[headers.index('Reference Status')], 'Missing')
                self.assertIsNone(row[headers.index('Media')])
        headers, rows, _ = self.parse('teleguardMediaFiles', [store, str(media)], root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][headers.index('Stored Name References')], 4)

    def test_ambiguous_media_is_reported_without_a_first_hit_join(self):
        root = self.temporary_root()
        app = root / 'teleguard_desktop'
        app.mkdir()
        path = write_store(app, [self.message(metadata=json.dumps({
            'mediaFiles': [{'name': 'photo.jpg'}]}))], [])
        files = [path]
        for subdirectory, data in (('a', JPEG), ('b', JPEG_SECOND)):
            (app / subdirectory).mkdir()
            candidate = app / subdirectory / 'photo.jpg'
            candidate.write_bytes(data)
            files.append(str(candidate))
        headers, rows, _ = self.parse('teleguardMediaReferences', files, root)
        self.assertIsNone(rows[0][headers.index('Media')])
        self.assertEqual(rows[0][headers.index('Reference Status')], 'Ambiguous')
        headers, rows, _ = self.parse('teleguardMediaFiles', files, root)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[headers.index('Reference Status')] == 'Ambiguous references'
                            for row in rows))

    def test_nested_store_files_do_not_fill_a_parent_store_reference(self):
        root = self.temporary_root()
        app = root / 'teleguard_desktop'
        nested = app / 'other' / 'teleguard_desktop'
        nested.mkdir(parents=True)
        parent = write_store(app, [self.message(metadata=json.dumps({
            'mediaFiles': [{'name': 'photo.jpg'}]}))], [])
        child = write_store(nested, [], [])
        media = nested / 'photo.jpg'
        media.write_bytes(JPEG)
        headers, rows, _ = self.parse('teleguardMediaReferences',
                                     [parent, child, str(media)], root)
        self.assertIsNone(rows[0][headers.index('Media')])
        self.assertEqual(rows[0][headers.index('Reference Status')], 'Missing')

    def test_shared_media_is_unassigned_when_a_profile_has_two_main_stores(self):
        root = self.temporary_root()
        build_external(root)
        saved = root / 'Users' / 'profile-one' / 'AppData' / 'Roaming' / 'TeleGuard' / 'saved'
        saved.mkdir()
        write_store(saved, [], [])
        files = [str(path) for path in root.rglob('*') if path.is_file()]
        headers, rows, _ = self.parse('teleguardMediaReferences', files, root)
        selected = [row for row in rows if row[headers.index('Media File Name')] == 'cache.jpg']
        self.assertEqual(len(selected), 2)
        for row in selected:
            expected = 'Missing' if '/profile-one/' in row[headers.index('Source File')] else 'Matched'
            self.assertEqual(row[headers.index('Reference Status')], expected)
        headers, rows, _ = self.parse('teleguardMediaFiles', files, root)
        own = [row for row in rows if '/profile-one/' in row[headers.index('Database Source')]]
        self.assertEqual(len(own), 1)
        self.assertEqual(own[0][headers.index('File Name')], 'avatar.png')

    def test_external_media_keeps_identical_users_in_separate_extractions_apart(self):
        root = self.temporary_root()
        build_external(root / 'first')
        build_external(root / 'second')
        files = [str(path) for path in root.rglob('*') if path.is_file()]
        with patch.object(teleguardDesktop, 'check_in_media',
                          side_effect=lambda path, **_kwargs: str(path)):
            headers, rows, _ = teleguardDesktop.teleguardMediaReferences.__wrapped__(Context(files, root))
        names = [head[0] if isinstance(head, tuple) else head for head in headers]
        matched = [row for row in rows if row[names.index('Reference Status')] == 'Matched']
        self.assertEqual(len(matched), 24)
        for row in matched:
            source = row[names.index('Source File')].split('/')
            media = pathlib.Path(row[names.index('Media')]).relative_to(root).parts
            self.assertEqual(tuple(source[:3]), media[:3])

    def test_external_cache_symlink_cannot_claim_another_profiles_file(self):
        root = self.temporary_root()
        build_external(root)
        first = root / 'Users' / 'profile-one' / 'AppData' / 'Local' / 'Temp' / 'TeleGuard' / 'images'
        second = root / 'Users' / 'profile-two' / 'AppData' / 'Local' / 'Temp' / 'TeleGuard' / 'images'
        (first / 'cache.jpg').unlink()
        try:
            (first / 'cache.jpg').symlink_to(second / 'cache.jpg')
        except (NotImplementedError, OSError):
            self.skipTest('Creating symlinks is unavailable')
        files = [str(path) for path in root.rglob('*') if path.is_file()]
        headers, rows, _ = self.parse('teleguardMediaReferences', files, root)
        selected = [row for row in rows if row[headers.index('Media File Name')] == 'cache.jpg'
                    and '/profile-one/' in row[headers.index('Source File')]]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0][headers.index('Reference Status')], 'Missing')

    def test_unknown_account_is_unknown_in_both_messages_and_summary(self):
        root = self.temporary_root()
        path = write_store(root, [self.message()], [])
        for account in (None, {'alias': 'No id'}, {'serverId': 'u1'}):
            with closing(sqlite3.connect(path)) as db:
                with db:
                    db.execute('DELETE FROM service')
                    if account is not None:
                        db.execute('INSERT INTO service VALUES (?, ?)', ('user', json.dumps(account)))
                        if account.get('serverId'):
                            db.execute('INSERT INTO service VALUES (?, ?)', ('user', json.dumps(account)))
            headers, rows, _ = self.parse('teleguardMessages', [path], root)
            self.assertEqual(rows[0][headers.index('Direction')], '')
            headers, rows, _ = self.parse('teleguardChatOverview', [path], root)
            self.assertEqual(rows[0][headers.index('Incoming')], 0)
            self.assertEqual(rows[0][headers.index('Outgoing')], 0)
            self.assertEqual(rows[0][headers.index('Direction Unknown')], 1)

    def test_raw_localized_content_survives_display_selection(self):
        files, root = self.keep(self.basic())
        headers, rows, _ = self.parse('teleguardMessages', files, root)
        row = self.by_id(headers, rows, 'Message ID')['m4']
        self.assertEqual(json.loads(row[headers.index('Content (as stored)')]),
                         {'de': 'Viola', 'en': 'Violet'})
        row = self.by_id(headers, rows, 'Message ID')['m1']
        self.assertEqual(row[headers.index('Content (as stored)')], 'Hello there')

    def test_timestamp_units_precision_and_invalid_values(self):
        self.assertEqual(tg_helper.utc(BASE_TIME + 123).microsecond, 123000)
        self.assertEqual(tg_helper.utc('1748847600000.123').microsecond, 123)
        self.assertEqual(tg_helper.utc(0).isoformat(), '1970-01-01T00:00:00+00:00')
        self.assertEqual(tg_helper.utc(-1).isoformat(), '1969-12-31T23:59:59.999000+00:00')
        with patch.object(tg_helper, 'logfunc'):
            for value in (None, '', True, 'invalid', 'NaN', 'Infinity', '1e100', '-1e100'):
                self.assertEqual(tg_helper.utc(value), '')
        root = self.temporary_root()
        path = write_store(root, [self.message(timestamp='invalid')], [])
        headers, rows, _ = self.parse('teleguardMessages', [path], root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][headers.index('Timestamp')], '')

    def test_all_artifacts_close_their_connections(self):
        files, root = self.keep(self.basic())
        real_open = tg_helper.open_sqlite_db_readonly
        opened = []

        def capture(path):
            db = real_open(path)
            opened.append(db)
            return db

        with patch.object(tg_helper, 'open_sqlite_db_readonly', side_effect=capture):
            for artifact in teleguardDesktop.__artifacts_v2__:
                self.parse(artifact, files, root)
        self.assertEqual(len(opened), 5)
        for db in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute('SELECT 1')

    def test_read_failure_closes_connection_and_does_not_report_partial_rows(self):
        files, root = self.keep(self.basic())
        opened = []
        real_open = tg_helper.open_sqlite_db_readonly

        def capture(path):
            db = real_open(path)
            opened.append(db)
            return db

        with patch.object(tg_helper, 'open_sqlite_db_readonly', side_effect=capture), \
                patch.object(tg_helper, 'message_rows', side_effect=sqlite3.OperationalError('test')):
            _, rows, notes = self.parse('teleguardMessages', files, root)
        self.assertEqual(rows, [])
        self.assertIn('test', ' '.join(notes))
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute('SELECT 1')

    def test_committed_wal_only_record_is_read_without_changing_db_or_wal(self):
        root = self.temporary_root()
        live = root / 'live'
        staged = root / 'teleguard_desktop'
        live.mkdir()
        staged.mkdir()
        path = write_store(live, [], [])
        writer = sqlite3.connect(path)
        self.addCleanup(writer.close)
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('PRAGMA wal_autocheckpoint=0')
        writer.execute('INSERT INTO messages VALUES (' + ','.join('?' * 12) + ')',
                       self.message(identifier='wal-only'))
        writer.commit()
        files = []
        for suffix in ('', '-wal'):
            destination = staged / (STORE + suffix)
            destination.write_bytes(pathlib.Path(path + suffix).read_bytes())
            files.append(str(destination))
        before = {p: hashlib.sha256(pathlib.Path(p).read_bytes()).digest() for p in files}
        headers, rows, _ = self.parse('teleguardMessages', files, root)
        self.assertEqual([row[headers.index('Message ID')] for row in rows], ['wal-only'])
        self.assertEqual(before, {p: hashlib.sha256(pathlib.Path(p).read_bytes()).digest()
                                  for p in files})
        # The main file copied without its WAL does not contain the inserted row.
        bare = root / 'bare'
        bare.mkdir()
        main = bare / STORE
        main.write_bytes(pathlib.Path(files[0]).read_bytes())
        _, rows, _ = self.parse('teleguardMessages', [str(main)], root)
        self.assertEqual(rows, [])

    def test_contacts_can_be_read_without_a_messages_table(self):
        root = self.temporary_root()
        path = write_store(root, [], [('u1', 'Alice', 'PERSON')],
                           contact_columns=('serverId', 'alias', 'type'))
        with closing(sqlite3.connect(path)) as db:
            with db:
                db.execute('DROP TABLE messages')
        headers, rows, _ = self.parse('teleguardContacts', [path], root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][headers.index('Messages Sent')], 0)

    def test_mixed_reference_structures_and_invalid_order_are_preserved(self):
        root = self.temporary_root()
        metadata = {'mediaFiles': [{'name': 'photo.jpg', 'order': 'NaN'}, None,
                                  {'name': '../escape.jpg', 'order': 0}],
                    'files': {'document-id': 'document.pdf', 'duplicate': 'photo.jpg'}}
        path = write_store(root, [self.message(metadata=json.dumps(metadata))], [])
        headers, rows, _ = self.parse('teleguardMediaReferences', [path], root)
        self.assertEqual(len(rows), 3)
        by_name = self.by_id(headers, rows, 'Media File Name')
        self.assertEqual(by_name['document.pdf'][headers.index('Reference Field')], 'files')
        self.assertEqual(by_name['../escape.jpg'][headers.index('Reference Status')],
                         'Invalid reference')
        self.assertEqual(by_name['photo.jpg'][headers.index('Reference Status')], 'Missing')

    def test_unreferenced_media_is_in_inventory_and_logs_are_excluded(self):
        root = self.temporary_root()
        path = write_store(root, [], [])
        image = root / 'orphan.png'
        image.write_bytes(PNG)
        log = root / 'teleguard_app.log'
        log.write_bytes(JPEG)
        headers, rows, _ = self.parse('teleguardMediaFiles', [path, str(image), str(log)], root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][headers.index('File Name')], 'orphan.png')
        self.assertEqual(rows[0][headers.index('Reference Status')], 'Unreferenced')
        self.assertEqual(rows[0][headers.index('Source File')], 'orphan.png')

    def test_corrupt_database_and_missing_required_columns_do_not_raise(self):
        root = self.temporary_root()
        path = root / STORE
        path.write_bytes(b'not a SQLite database')
        _, rows, notes = self.parse('teleguardMessages', [str(path)], root)
        self.assertEqual(rows, [])
        self.assertTrue(notes)
        path.unlink()
        with closing(sqlite3.connect(path)) as db:
            with db:
                db.execute('CREATE TABLE messages(id TEXT)')
        _, rows, notes = self.parse('teleguardMessages', [str(path)], root)
        self.assertEqual(rows, [])
        self.assertIn('required identity/content columns', ' '.join(notes))

    def test_relative_staging_paths_stay_portable_in_case_baselines(self):
        files, root = self.keep(self.basic())
        relative_files = [os.path.relpath(path) for path in files]
        relative_root = pathlib.Path(os.path.relpath(root))
        with patch.object(tg_helper, 'open_sqlite_db_readonly',
                          wraps=tg_helper.open_sqlite_db_readonly) as opened:
            headers, rows, _ = self.parse('teleguardMessages', relative_files, relative_root)
        opened.assert_called_once_with(os.path.abspath(relative_files[0]))
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0][headers.index('Source File')],
                         'AppData/teleguard_desktop/teleguard_database.db')
        headers, rows, _ = self.parse('teleguardMediaFiles', relative_files, relative_root)
        self.assertEqual(rows[0][headers.index('Source File')],
                         'AppData/teleguard_desktop/example_photo.jpeg')

    def test_third_return_value_contains_each_absolute_database_once(self):
        files, root = self.keep(self.basic())
        with patch.object(teleguardDesktop, 'check_in_media', side_effect=media_marker):
            _, _, sources = teleguardDesktop.teleguardMessages.__wrapped__(
                Context(files + files, root))
        self.assertEqual(sources, files[0])


if __name__ == '__main__':
    unittest.main()
