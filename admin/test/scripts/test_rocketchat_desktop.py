"""The Rocket.Chat Desktop artifacts on hand-built trees; every value is made up.

IndexedDB is stood in for by a small fake with the methods the rooms artifact calls; the real reading is
exercised on the corpus sample.
"""

import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import rocketChatDesktop as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
APP = 'Users/tester/AppData/Roaming/Rocket.Chat'
PART = APP + '/Partitions/https%3A/chat.fixture.test/IndexedDB/https_chat.fixture.test_0.indexeddb.leveldb'


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class FakeStore:
    object_store_names = ['keyvaluepairs']

    def __init__(self, records):
        self.records = records

    def __getitem__(self, _name):
        return SimpleNamespace(iterate_records=lambda: iter(self.records))


class FakeWrapped:
    def __init__(self, records):
        self.database_ids = [SimpleNamespace(name='https://chat.fixture.test/', dbid_no=1)]
        self.store = FakeStore(records)

    def __getitem__(self, _number):
        return self.store


def rec(key, saved, items):
    return SimpleNamespace(key=SimpleNamespace(value=key), ldb_seq_no=1,
                           value={'updatedAt': saved, 'version': 19, 'token': 'x', 'records': items})


T = datetime(2031, 5, 6, 7, 8, 9)       # naive, as the V8 deserializer returns a JavaScript Date
ROOM = {'_id': 'r1', '_updatedAt': T, 't': 'p', 'name': 'room-one', 'fname': 'Room One', 'msgs': 3, 'usersCount': 2,
        'usernames': ['alice', 'bob'], 'ts': datetime(2031, 5, 1), 'lm': datetime(2031, 5, 6, 7, 0, 0),
        'lastMessage': {'msg': 'see you', 'ts': T, 'u': {'username': 'alice'}}}
SUB = {'_id': 's1', 'rid': 'r1', '_updatedAt': T, 't': 'p', 'name': 'room-one', 'fname': 'Room One', 'unread': 2, 'alert': True,
       'open': True, 'ls': datetime(2031, 5, 6, 7, 1, 0), 'usersCount': 2,
       'lastMessage': {'msg': '', 't': 'e2e', 'ts': T, 'u': {'username': 'bob'}}}


class RocketChatRoomsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        patcher = mock.patch.object(artifact, 'logfunc')
        self.log = patcher.start()
        self.addCleanup(patcher.stop)
        folder = os.path.join(self.root, *PART.split('/'))
        os.makedirs(folder)
        self.log_file = os.path.join(folder, '000003.log')
        open(self.log_file, 'wb').close()

    def run_artifact(self, records):
        with mock.patch.object(artifact.indexeddb, 'WrappedIndexDB', return_value=FakeWrapped(records)):
            return artifact.rocketChatRooms.__wrapped__(Context(self.root, [self.log_file]))

    def test_rooms_and_subscriptions_become_rows_with_their_own_columns(self):
        headers, rows, source = self.run_artifact([rec('rooms', datetime(2031, 5, 6, 8), [ROOM]), rec('subscriptions', datetime(2031, 5, 6, 8), [SUB]),
                                                   rec('permissions', datetime(2031, 5, 6, 8), [{'_id': 'x'}])])
        self.assertEqual(headers[0], ('Record Updated (UTC)', 'datetime'))
        self.assertEqual(headers[1], ('ts (UTC)', 'datetime'))
        self.assertEqual(len(headers), len(rows[0]))
        ix = {(h[0] if isinstance(h, tuple) else h): i for i, h in enumerate(headers)}
        by_store = {row[ix['Store']]: row for row in rows}
        self.assertEqual(sorted(by_store), ['rooms', 'subscriptions'])       # permissions is not reported
        room, sub = by_store['rooms'], by_store['subscriptions']
        self.assertEqual(room[0], datetime(2031, 5, 6, 7, 8, 9, tzinfo=UTC))
        self.assertEqual((room[ix['Type']], room[ix['Name']], room[ix['Messages']], room[ix['Users']], room[ix['Usernames']]),
                         ('p', 'room-one', 3, 2, 'alice\nbob'))
        self.assertEqual((room[ix['Last Message']], room[ix['Last Message Sender']], room[ix['Last Message Type']]), ('see you', 'alice', ''))
        self.assertEqual((sub[ix['Unread']], sub[ix['Alert']], sub[ix['Open']], sub[ix['Last Message Type']], sub[ix['Room ID']]), (2, 'yes', 'yes', 'e2e', 'r1'))
        self.assertEqual(sub[ix['Last Seen (UTC)']], datetime(2031, 5, 6, 7, 1, tzinfo=UTC))
        self.assertEqual(room[ix['Store Updated At (UTC)']], datetime(2031, 5, 6, 8, tzinfo=UTC))
        self.assertEqual(room[ix['Server']], 'https://chat.fixture.test')   # the folder name's port 0 is the default port
        self.assertEqual(source, self.log_file)

    def test_a_record_saved_in_several_versions_is_one_row_with_the_latest_save_time(self):
        records = [rec('rooms', datetime(2031, 5, 6, 8), [ROOM]), rec('rooms', datetime(2031, 5, 6, 9), [ROOM]),
                   rec('rooms', datetime(2031, 5, 6, 8, 30), [dict(ROOM, _updatedAt=datetime(2031, 5, 6, 8, 20), msgs=4)])]
        _h, rows, _s = self.run_artifact(records)
        self.assertEqual(len(rows), 2)                                       # two versions of the room record
        self.assertEqual(sorted(row[11] for row in rows), [3, 4])
        self.assertEqual({row[4] for row in rows if row[11] == 3}, {datetime(2031, 5, 6, 9, tzinfo=UTC)})

    def test_a_record_saved_with_the_same_updated_at_but_other_content_is_kept_as_a_second_row(self):
        changed = dict(SUB, unread=7, alert=False)
        _h, rows, _s = self.run_artifact([rec('subscriptions', datetime(2031, 5, 6, 8), [SUB]), rec('subscriptions', datetime(2031, 5, 6, 8), [changed])])
        self.assertEqual(sorted(row[16] for row in rows), [2, 7])

    def test_an_error_while_reading_records_is_logged_and_what_was_read_is_kept(self):
        def broken():
            yield rec('rooms', datetime(2031, 5, 6, 8), [ROOM])
            raise ValueError("Can't resolve blob if blob dir is not set")
        wrapped = FakeWrapped([])

        class Store:
            object_store_names = ['keyvaluepairs']
            def __getitem__(self, _name):
                return SimpleNamespace(iterate_records=lambda **_kw: broken())
        wrapped.store = Store()
        with mock.patch.object(artifact.indexeddb, 'WrappedIndexDB', return_value=wrapped):
            rows = artifact.rocketChatRooms.__wrapped__(Context(self.root, [self.log_file]))[1]
        self.assertEqual(len(rows), 1)
        self.assertTrue(any('stopped' in str(call) for call in self.log.call_args_list))

    def test_odd_values_do_not_stop_the_read(self):
        odd = {'_id': 'o', '_updatedAt': 'not a date', 't': 5, 'usernames': 'x', 'lastMessage': 'text', 'msgs': True}
        _h, rows, _s = self.run_artifact([rec('rooms', datetime(2031, 1, 1), [odd, 'not a dict'])])
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0][0], rows[0][7], rows[0][11], rows[0][12], rows[0][13]), ('', '', '', '', ''))

    def test_no_indexeddb_folder_gives_nothing(self):
        self.assertEqual(artifact.rocketChatRooms.__wrapped__(Context(self.root, []))[1:], ([], ''))

    def test_a_folder_that_cannot_be_opened_is_logged(self):
        with mock.patch.object(artifact.indexeddb, 'WrappedIndexDB', side_effect=ValueError('bad')):
            rows = artifact.rocketChatRooms.__wrapped__(Context(self.root, [self.log_file]))[1]
        self.assertEqual(rows, [])
        self.assertTrue(any('could not be opened' in str(call) for call in self.log.call_args_list))


class RocketChatServersTest(unittest.TestCase):
    def test_servers_are_read_from_config(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        folder = os.path.join(root, *APP.split('/'))
        os.makedirs(folder)
        config = os.path.join(folder, 'config.json')
        with open(config, 'w', encoding='utf-8') as handle:
            json.dump({'servers': [{'url': 'https://a.test/', 'title': 'A', 'version': '9.9.9', 'userLoggedIn': True, 'userRoles': ['user', 'admin'],
                                    'lastPath': '/home', 'isSupportedVersion': False, 'supportedVersionsValidatedAt': '2031-01-02T03:04:05.678Z'},
                                   {'url': 'https://b.test/'}]}, handle)
        with mock.patch.object(artifact, 'logfunc'):
            _h, rows, source = artifact.rocketChatServers.__wrapped__(Context(root, [config]))
        self.assertEqual(rows[0], ('A', 'https://a.test/', '9.9.9', 'yes', 'user, admin', '/home', 'no',
                                   datetime(2031, 1, 2, 3, 4, 5, 678000, tzinfo=UTC)))
        self.assertEqual(rows[1], ('', 'https://b.test/', '', '', '', '', '', ''))
        self.assertEqual(source, config)


if __name__ == '__main__':
    unittest.main()
