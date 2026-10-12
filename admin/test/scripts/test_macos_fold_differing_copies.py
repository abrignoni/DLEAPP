"""A record held by two volume views of one file is reported once.

A logical extraction of a Mac can hold a file at its own path and again under System/Volumes/Data, and the two copies
can differ in bytes. These tests build such a pair for the local items keychain, the iMessage chat list, an app URL
cache and the Signal settings files and pin that a record both copies hold is one row. The values are made up.
"""
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import Keychains as keychains
from scripts.artifacts import iMessageMessages as imessage
from scripts.artifacts import macosAppUrlCache as cache
from scripts.artifacts import signalAccount as signal
# pylint: enable=wrong-import-position


def keychain_db(path, accounts):
    database = sqlite3.connect(path)
    for table, third in (('genp', 'svce'), ('inet', 'srvr')):
        database.execute(f'CREATE TABLE {table} (cdat REAL, mdat REAL, labl, acct, {third}, agrp TEXT, pdmn TEXT, data BLOB)')
    database.execute('CREATE TABLE cert (cdat REAL, mdat REAL, labl, agrp TEXT, pdmn TEXT, data BLOB)')
    database.execute('CREATE TABLE keys (cdat REAL, mdat REAL, labl, agrp TEXT, pdmn TEXT, data BLOB)')
    for account in accounts:
        database.execute("INSERT INTO genp VALUES (700000000.0, 700000060.0, 'label', ?, 'service', 'group.example', 'ak', x'0102')",
                         (account,))
    database.commit()
    database.close()


def chat_db(path, chats):
    database = sqlite3.connect(path)
    database.execute('CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, guid TEXT, chat_identifier TEXT, display_name TEXT, '
                     'service_name TEXT, style INTEGER, is_archived INTEGER)')
    database.execute('CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)')
    database.execute('CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER)')
    database.execute("INSERT INTO handle VALUES (1, '+15555550100')")
    for number, identifier in enumerate(chats, 1):
        database.execute("INSERT INTO chat VALUES (?, ?, ?, '', 'iMessage', 45, 0)", (number, 'guid-' + identifier, identifier))
        database.execute('INSERT INTO chat_handle_join VALUES (?, 1)', (number,))
    database.commit()
    database.close()


def cache_db(path, urls):
    database = sqlite3.connect(path)
    database.execute('CREATE TABLE cfurl_cache_response (entry_ID INTEGER PRIMARY KEY, request_key TEXT, time_stamp TEXT, '
                     'partition TEXT)')
    database.execute('CREATE TABLE cfurl_cache_blob_data (entry_ID INTEGER, response_object BLOB, request_object BLOB)')
    database.execute('CREATE TABLE cfurl_cache_receiver_data (entry_ID INTEGER, isDataOnFS INTEGER, receiver_data BLOB)')
    for number, url in enumerate(urls, 1):
        database.execute("INSERT INTO cfurl_cache_response VALUES (?, ?, '2021-01-17 20:18:17', NULL)", (number, url))
        database.execute("INSERT INTO cfurl_cache_receiver_data VALUES (?, 0, x'3c2f3e')", (number,))
    database.commit()
    database.close()


class FoldTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def pair(self, relative, builder, own, data_view):
        """The file at its own path and a differing copy under System/Volumes/Data."""
        paths = []
        for top, content in (((), own), (('System', 'Volumes', 'Data'), data_view)):
            path = os.path.join(self.folder.name, *top, *relative.split('/'))
            os.makedirs(os.path.dirname(path))
            builder(path, content)
            paths.append(path)
        return paths[0], paths[1]

    def run_artifact(self, module, function, found):
        context = mock.Mock()
        context.get_files_found.return_value = found
        context.get_relative_path.side_effect = lambda p: os.path.relpath(p, self.folder.name)
        with mock.patch.object(module, 'logfunc'), mock.patch('scripts.macos_plists.logfunc'):
            return function.__wrapped__(context)

    def relative(self, path):
        return os.path.relpath(path, self.folder.name)

    def test_local_items_keychain(self):
        own, view = self.pair('Users/a/Library/Keychains/UUID/keychain-2.db', keychain_db, ['one', 'two'], ['one', 'three'])
        other = os.path.join(self.folder.name, 'Users', 'b', 'Library', 'Keychains', 'UUID', 'keychain-2.db')
        os.makedirs(os.path.dirname(other))
        keychain_db(other, ['one'])
        _, rows, _ = self.run_artifact(keychains, keychains.keychainLocalItems, [own, view, other])
        self.assertEqual(sorted((row[4], row[-1]) for row in rows),
                         sorted([('one', self.relative(own) + '\n' + self.relative(view)), ('two', self.relative(own)),
                                 ('three', self.relative(view)), ('one', self.relative(other))]))

    def test_chat_threads(self):
        own, view = self.pair('Users/a/Library/Messages/chat.db', chat_db, ['chat-one', 'chat-two'], ['chat-one'])
        _, rows, _ = self.run_artifact(imessage, imessage.imessageChats, [own, view])
        self.assertEqual(sorted((row[0], row[-1]) for row in rows),
                         sorted([('chat-one', self.relative(own) + '\n' + self.relative(view)), ('chat-two', self.relative(own))]))

    def test_app_url_cache(self):
        own, view = self.pair('Users/a/Library/Caches/com.example.app/Cache.db', cache_db,
                              ['https://example.test/a', 'https://example.test/b'], ['https://example.test/a'])
        headers, rows, located = self.run_artifact(cache, cache.macosAppUrlCache, [own, view])
        self.assertEqual(sorted(row[4] for row in rows), ['https://example.test/a', 'https://example.test/b'])
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(sorted(located.split('\n')), sorted([own, view]))

    def test_signal_settings(self):
        def settings(path, content):
            with open(path, 'w', encoding='utf-8') as handle:
                json.dump(content, handle)
        own, view = self.pair('Users/a/Library/Application Support/Signal/ephemeral.json', settings,
                              {'theme-setting': 'dark', 'spell-check': True}, {'theme-setting': 'dark', 'spell-check': False})
        _, rows, _ = self.run_artifact(signal, signal.signalAccount, [own, view])
        both = self.relative(own) + '\n' + self.relative(view)
        self.assertEqual(sorted(row for row in rows if row[0].startswith('Setting')), sorted([
            ('Setting: theme-setting', 'dark', both), ('Setting: spell-check', 'True', self.relative(own)),
            ('Setting: spell-check', 'False', self.relative(view))]))
        self.assertEqual([row[0] for row in rows if not row[0].startswith('Setting')], ['Database'])


if __name__ == '__main__':
    unittest.main()
