"""The Mattermost Desktop artifacts on hand-built trees; every value is made up.

Cached API responses are simple-cache entries written by the test, in the layout of
the cache folder of the desktop app. IndexedDB is stood in for by a small fake that has the
methods the drafts artifact calls; the real IndexedDB reading is exercised on the corpus sample.
"""

import gzip
import json
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import mattermostDesktop as artifact  # pylint: disable=wrong-import-position
from scripts.chromium import mattermost_api, simple_cache  # pylint: disable=wrong-import-position

UTC = timezone.utc
RESPONSE = 13_400_000_000_000_000
REQUEST = RESPONSE - 250_000
SERVER = 'https://chat.fixture.test'
APP = 'Users/tester/AppData/Roaming/Mattermost'
CACHE = APP + '/Cache/Cache_Data'
T0 = 1_900_000_000_000            # an invented time in unix milliseconds
ID = {name: (name * 26)[:26] for name in 'abcdefghij'}


def entry(url, body, content_type='application/json', status=b'HTTP/1.1 200 OK', encoding=None):
    key = b'1/0/' + url.encode()
    headers = [status, b'content-type: ' + content_type.encode()]
    if encoding:
        headers.append(b'content-encoding: ' + encoding.encode())
    raw = b'\x00'.join(headers) + b'\x00\x00'
    stream0 = struct.pack('<Iiqq', 0, 3, REQUEST, RESPONSE) + struct.pack('<I', len(raw)) + raw
    stream0 = struct.pack('<I', len(stream0) - 4) + stream0[4:]
    out = struct.pack('<QIII', simple_cache.SIMPLE_HEADER_MAGIC, 5, len(key), 0) + b'\x00' * 4
    out += key + body
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, 1, 0, 0) + b'\x00' * 4
    out += stream0
    out += struct.pack('<QIII', simple_cache.SIMPLE_EOF_MAGIC, 1, 0, len(stream0)) + b'\x00' * 4
    return out


def post(name, **extra):
    base = {'id': ID[name], 'create_at': T0 + 1000, 'update_at': T0 + 1000, 'edit_at': 0, 'delete_at': 0,
            'is_pinned': False, 'user_id': ID['u'] if 'u' in ID else '', 'channel_id': ID['c'], 'root_id': '',
            'original_id': '', 'message': 'hello', 'type': '', 'props': {}, 'hashtags': '', 'file_ids': [],
            'pending_post_id': ''}
    base.update(extra)
    return base


ID['u'] = 'u' * 26
ID['v'] = 'v' * 26
USER = {'id': ID['u'], 'create_at': T0, 'update_at': T0 + 5, 'delete_at': 0, 'username': 'testuser', 'email': 't@fixture.test',
        'nickname': 'tt', 'first_name': 'Test', 'last_name': 'User', 'position': '', 'roles': 'system_user'}
USER2 = dict(USER, id=ID['v'], username='other', email='o@fixture.test')
CHANNEL = {'id': ID['c'], 'create_at': T0, 'update_at': T0 + 9, 'delete_at': 0, 'team_id': ID['t'] if 't' in ID else 't' * 26,
           'type': 'O', 'display_name': 'Town Square', 'name': 'town-square', 'header': 'h', 'purpose': 'p',
           'last_post_at': T0 + 2000, 'total_msg_count': 3, 'creator_id': ''}
DM = dict(CHANNEL, id=ID['d'], type='D', display_name='', name=ID['u'] + '__' + ID['v'])


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class MattermostCacheTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        mattermost_api._scans.clear()  # pylint: disable=protected-access
        patcher = mock.patch.object(artifact, 'logfunc')
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def cache(self, entries, folder=CACHE):
        path = os.path.join(self.root, *folder.split('/'))
        os.makedirs(path, exist_ok=True)
        files = []
        for number, data in enumerate(entries):
            target = os.path.join(path, f'{number:016x}_0')
            with open(target, 'wb') as handle:
                handle.write(data)
            files.append(target)
        return files

    def run_artifact(self, function, files):
        return function.__wrapped__(Context(self.root, files))

    def test_posts_resolve_names_keep_versions_and_read_gzip_and_ndjson(self):
        listing = {'order': [ID['a']], 'posts': {ID['a']: post('a')}}
        edited = post('a', update_at=T0 + 4000, edit_at=T0 + 4000, message='hello again')
        files = self.cache([
            entry(SERVER + '/api/v4/channels/x/posts', json.dumps(listing).encode()),
            entry(SERVER + '/api/v4/posts/x/thread', gzip.compress(json.dumps({'posts': {ID['a']: edited}, 'order': [ID['a']]}).encode()), encoding='gzip'),
            entry(SERVER + '/api/v4/users/ids', json.dumps([USER, USER2]).encode()),
            entry(SERVER + '/api/v4/users/x/channel_members', (json.dumps(CHANNEL) + '\n' + json.dumps(DM) + '\n').encode(), content_type='application/x-ndjson'),
            entry(SERVER + '/api/v4/channels/y/posts', b'{}', status=b'HTTP/1.1 404 Not Found'),
            entry(SERVER + '/api/v4/users/x/image', b'\x89PNG', content_type='image/png'),
            entry('https://other.fixture.test/not/api', b'{}'),
        ])
        headers, rows, source = self.run_artifact(artifact.mattermostPosts, files)
        self.assertEqual(headers[0], ('Created (UTC)', 'datetime'))
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 2)                                  # two versions of one post
        first, second = rows
        self.assertEqual(first[0], datetime.fromtimestamp((T0 + 1000) / 1000, UTC))
        self.assertEqual((first[2], first[3]), ('', ''))               # not edited, not deleted
        self.assertEqual(second[2], datetime.fromtimestamp((T0 + 4000) / 1000, UTC))
        self.assertEqual((second[10], second[6], second[8]), ('hello again', 'Town Square', 'testuser'))
        self.assertEqual(first[5], SERVER)
        self.assertEqual(second[4], simple_cache.base_time_to_datetime(RESPONSE))
        self.assertTrue(source)

    def test_users_channels_and_a_direct_channel_name_from_its_two_user_ids(self):
        posts = {'order': [ID['b']], 'posts': {ID['b']: post('b', channel_id=ID['d'], user_id=ID['v'])}}
        files = self.cache([
            entry(SERVER + '/api/v4/users/autocomplete', json.dumps({'users': [USER], 'out_of_channel': [USER2]}).encode()),
            entry(SERVER + '/api/v4/users/me/channels', json.dumps([CHANNEL, DM]).encode()),
            entry(SERVER + '/api/v4/channels/z/posts', json.dumps(posts).encode()),
        ])
        _h, users, _s = self.run_artifact(artifact.mattermostUsers, files)
        self.assertEqual(sorted(row[5] for row in users), ['other', 'testuser'])
        _h, chans, _s = self.run_artifact(artifact.mattermostChannels, files)
        self.assertEqual(sorted((row[6], row[7]) for row in chans), [('direct (D)', ''), ('open (O)', 'Town Square')])
        _h, rows, _s = self.run_artifact(artifact.mattermostPosts, files)
        self.assertEqual((rows[0][6], rows[0][8]), ('testuser and other', 'other'))   # resolved through the cached users

    def test_a_user_object_with_an_empty_username_is_left_out(self):
        files = self.cache([entry(SERVER + '/api/v4/users/x/participants', json.dumps([USER, {'id': ID['w'] if 'w' in ID else 'w' * 26, 'username': '', 'first_name': '', 'email': ''}]).encode())])
        rows = self.run_artifact(artifact.mattermostUsers, files)[1]
        self.assertEqual([row[5] for row in rows], ['testuser'])

    def test_a_cache_without_mattermost_responses_gives_nothing(self):
        files = self.cache([entry('https://elsewhere.test/page', b'<html>', content_type='text/html')])
        self.assertEqual(self.run_artifact(artifact.mattermostPosts, files)[1:], ([], ''))

    def test_objects_are_recognised_by_their_field_names_wherever_they_sit(self):
        nested = {'results': [{'wrapper': {'post': post('c', message='nested')}}], 'noise': {'id': 'x', 'message': 'no'}}
        files = self.cache([entry(SERVER + '/api/v4/teams/x/posts/search', json.dumps(nested).encode())])
        rows = self.run_artifact(artifact.mattermostPosts, files)[1]
        self.assertEqual([row[10] for row in rows], ['nested'])

    def test_system_and_deleted_posts_keep_their_stored_fields(self):
        gone = post('d', delete_at=T0 + 9000, type='system_join_channel', message='joined', file_ids=[ID['e'], ID['f']], is_pinned=True)
        files = self.cache([entry(SERVER + '/api/v4/channels/x/posts', json.dumps({'order': [], 'posts': {ID['d']: gone}}).encode())])
        row = self.run_artifact(artifact.mattermostPosts, files)[1][0]
        self.assertEqual((row[3], row[11], row[13], row[14]), (datetime.fromtimestamp((T0 + 9000) / 1000, UTC), 'system_join_channel',
                                                               ID['e'] + '\n' + ID['f'], 'yes'))

    def test_ms_to_datetime_refuses_what_is_not_a_time(self):
        for value in (0, -5, None, '1', True, 10 ** 30):
            self.assertEqual(mattermost_api.ms_to_datetime(value), '')


class FakeStore:
    def __init__(self, records):
        self.object_store_names = ['keyvaluepairs']
        self.records = records

    def __getitem__(self, name):
        return SimpleNamespace(iterate_records=lambda **_kw: iter(self.records))


class FakeWrapped:
    def __init__(self, records):
        self.database_ids = [SimpleNamespace(name='localforage', dbid_no=1)]
        self.store = FakeStore(records)

    def __getitem__(self, _number):
        return self.store


def state(drafts):
    return json.dumps({'_persist': json.dumps({'version': -1, 'rehydrated': True}),
                       **{key: json.dumps({'timestamp': stamp, 'value': {'message': text, 'fileInfos': files, 'uploadsInProgress': [], 'metadata': {}}})
                          for key, (stamp, text, files) in drafts.items()}})


class MattermostDraftsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        mattermost_api._scans.clear()  # pylint: disable=protected-access
        patcher = mock.patch.object(artifact, 'logfunc')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_every_version_of_a_draft_is_kept_and_only_the_last_is_latest(self):
        folder = os.path.join(self.root, *(APP + '/IndexedDB/https_chat.fixture.test_0.indexeddb.leveldb').split('/'))
        os.makedirs(folder)
        log = os.path.join(folder, '000003.log')
        open(log, 'wb').close()
        key = 'draft_' + ID['c']
        records = [SimpleNamespace(key=SimpleNamespace(value='persist:storage'), ldb_seq_no=n, value=state({key: (stamp, text, files)}))
                   for n, (stamp, text, files) in enumerate([('2031-01-02T03:04:05.100Z', 'he', []), ('2031-01-02T03:04:07.200Z', 'hello', []),
                                                             ('2031-01-02T03:04:09.300Z', 'hello there', [{'name': 'a.txt'}])], start=1)]
        records.insert(1, SimpleNamespace(key=SimpleNamespace(value='other'), ldb_seq_no=9, value='{}'))
        with mock.patch.object(artifact.indexeddb, 'WrappedIndexDB', return_value=FakeWrapped(records)):
            headers, rows, source = artifact.mattermostDrafts.__wrapped__(Context(self.root, [log]))
        self.assertEqual(headers[0], ('Draft Time (UTC)', 'datetime'))
        self.assertEqual([(row[0], row[4], row[7]) for row in rows], [
            (datetime(2031, 1, 2, 3, 4, 5, 100000, tzinfo=UTC), 'he', ''),
            (datetime(2031, 1, 2, 3, 4, 7, 200000, tzinfo=UTC), 'hello', ''),
            (datetime(2031, 1, 2, 3, 4, 9, 300000, tzinfo=UTC), 'hello there', 'yes')])
        self.assertEqual(rows[0][1], 'https://chat.fixture.test')   # port 0 is the default port
        self.assertEqual((rows[0][2], rows[2][5], rows[0][6]), ('channel draft', 'a.txt', ID['c']))
        self.assertEqual(source, log)

    def test_draft_kinds_follow_the_key_prefix_and_other_keys_are_ignored(self):
        folder = os.path.join(self.root, *(APP + '/IndexedDB/http_host_8065.indexeddb.leveldb').split('/'))
        os.makedirs(folder)
        log = os.path.join(folder, '000003.log')
        open(log, 'wb').close()
        drafts = {'comment_draft_' + ID['a']: ('2031-02-01T00:00:00.000Z', 'reply', []), 'edit_draft_' + ID['b']: ('2031-02-01T00:00:01.000Z', 'edit', []),
                  'draft_short': ('2031-02-01T00:00:02.000Z', 'ignored', [])}
        records = [SimpleNamespace(key=SimpleNamespace(value='persist:storage'), ldb_seq_no=1, value=state(drafts))]
        with mock.patch.object(artifact.indexeddb, 'WrappedIndexDB', return_value=FakeWrapped(records)):
            rows = artifact.mattermostDrafts.__wrapped__(Context(self.root, [log]))[1]
        self.assertEqual(sorted(row[2] for row in rows), ['edit draft', 'reply draft'])
        self.assertEqual({row[1] for row in rows}, {'http://host:8065'})

    def test_origin_and_time_parsing(self):
        self.assertEqual(artifact._origin('https_a.b.test_8443.indexeddb.leveldb'), 'https://a.b.test:8443')  # pylint: disable=protected-access
        self.assertEqual(artifact._origin('http_a.b.test_0.indexeddb.leveldb'), 'http://a.b.test')  # pylint: disable=protected-access
        self.assertEqual(artifact._iso_to_datetime('nonsense'), '')  # pylint: disable=protected-access
        self.assertEqual(artifact._iso_to_datetime(5), '')  # pylint: disable=protected-access


class MattermostLaterFixesTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        mattermost_api._scans.clear()  # pylint: disable=protected-access
        patcher = mock.patch.object(artifact, 'logfunc')
        patcher.start()
        self.addCleanup(patcher.stop)

    def cache(self, entries):
        path = os.path.join(self.root, *CACHE.split('/'))
        os.makedirs(path, exist_ok=True)
        files = []
        for number, data in enumerate(entries):
            target = os.path.join(path, f'{number:016x}_0')
            with open(target, 'wb') as handle:
                handle.write(data)
            files.append(target)
        return files

    def test_a_scheduled_post_is_not_reported_as_a_post(self):
        scheduled = {'id': ID['a'], 'channel_id': ID['c'], 'user_id': ID['u'], 'create_at': T0, 'message': 'later', 'scheduled_at': T0 + 99}
        files = self.cache([entry(SERVER + '/api/v4/posts/scheduled/team/x', json.dumps([scheduled]).encode())])
        self.assertEqual(artifact.mattermostPosts.__wrapped__(Context(self.root, files))[1], [])

    def test_the_object_of_the_newest_response_is_kept(self):
        older = dict(CHANNEL, total_msg_count=20, last_post_at=T0 + 100)
        newer = dict(CHANNEL, total_msg_count=32, last_post_at=T0 + 900)
        files = self.cache([entry(SERVER + '/api/v4/channels/a', json.dumps(older).encode()),
                            entry(SERVER + '/api/v4/channels/b', json.dumps(newer).encode())])
        # Make the second entry the newer response by rewriting its response time.
        newer_entry = open(files[1], 'rb').read()
        patched = newer_entry.replace(struct.pack('<q', RESPONSE), struct.pack('<q', RESPONSE + 5_000_000))
        self.assertNotEqual(patched, newer_entry)
        with open(files[1], 'wb') as handle:
            handle.write(patched)
        rows = artifact.mattermostChannels.__wrapped__(Context(self.root, files))[1]
        self.assertEqual([row[13] for row in rows], [32])

    def test_last_active_is_the_rank_by_order_not_the_position_in_the_file(self):
        folder = os.path.join(self.root, *APP.split('/'))
        os.makedirs(folder)
        config = os.path.join(folder, 'config.json')
        with open(config, 'w', encoding='utf-8') as handle:
            json.dump({'lastActiveServer': 0, 'servers': [{'name': 'late', 'url': 'https://b.test', 'order': 5}, {'name': 'first', 'url': 'https://a.test', 'order': 1}]}, handle)
        rows = artifact.mattermostServers.__wrapped__(Context(self.root, [config]))[1]
        self.assertEqual({row[0]: row[4] for row in rows}, {'late': '', 'first': 'yes'})

    def test_latest_is_only_on_what_the_newest_record_holds_and_bad_records_are_counted(self):
        folder = os.path.join(self.root, *(APP + '/IndexedDB/https_chat.fixture.test_0.indexeddb.leveldb').split('/'))
        os.makedirs(folder)
        log = os.path.join(folder, '000003.log')
        open(log, 'wb').close()
        k1, k2 = 'draft_' + ID['a'], 'draft_' + ID['b']
        records = [SimpleNamespace(key=SimpleNamespace(value='persist:storage'), ldb_seq_no=1, value=state({k1: ('2031-01-01T00:00:00.000Z', 'one', []), k2: ('2031-01-01T00:00:01.000Z', 'two', [])})),
                   SimpleNamespace(key=SimpleNamespace(value='persist:storage'), ldb_seq_no=2, value=state({k1: ('2031-01-01T00:00:02.000Z', 'one more', [])}))]
        with mock.patch.object(artifact.indexeddb, 'WrappedIndexDB', return_value=FakeWrapped(records)):
            rows = artifact.mattermostDrafts.__wrapped__(Context(self.root, [log]))[1]
        latest = {(row[4], row[7]) for row in rows}
        self.assertEqual(latest, {('one', ''), ('two', ''), ('one more', 'yes')})   # k2 is gone from the newest record


class MattermostServersTest(unittest.TestCase):
    def test_servers_with_the_active_one_and_the_app_version(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        folder = os.path.join(root, *APP.split('/'))
        os.makedirs(folder)
        config = os.path.join(folder, 'config.json')
        with open(config, 'w', encoding='utf-8') as handle:
            json.dump({'version': 4, 'lastActiveServer': 1, 'servers': [{'name': 'A', 'url': 'https://a.test', 'order': 0},
                                                                         {'name': 'B', 'url': 'https://b.test', 'order': 1, 'isPredefined': True}]}, handle)
        state_file = os.path.join(folder, 'app-state.json')
        with open(state_file, 'w', encoding='utf-8') as handle:
            json.dump({'lastAppVersion': '9.9.9'}, handle)
        with mock.patch.object(artifact, 'logfunc'):
            _h, rows, source = artifact.mattermostServers.__wrapped__(Context(root, [config, state_file]))
        self.assertEqual(rows, [('A', 'https://a.test', 0, '', '', '9.9.9'), ('B', 'https://b.test', 1, 'yes', 'yes', '9.9.9')])
        self.assertEqual(source.split('\n'), [config, state_file])


if __name__ == '__main__':
    unittest.main()
