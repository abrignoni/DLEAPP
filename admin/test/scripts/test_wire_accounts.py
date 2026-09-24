"""Pin how the Wire IndexedDB artifacts treat a profile holding two accounts' databases.

Two accounts that know each other each hold the other as a user, their shared conversation
and a copy of the same message. Every account's copy must be reported, "me" and Outgoing
must follow the account the row was read from, and key-material counts must be per account,
with a key LevelDB holds twice counted once among the distinct keys.
The stores are built by hand below and the expected values are written out, never read back
from the code.
"""
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import wireIndexedDb  # pylint: disable=wrong-import-position

ALICE = '11111111-1111-4111-8111-111111111111'
BOB = '22222222-2222-4222-8222-222222222222'
CONV = '33333333-3333-4333-8333-333333333333'
EVENT = '44444444-4444-4444-8444-444444444444'
A_DB = f'wire@production@{ALICE}@permanent'
B_DB = f'wire@production@{BOB}@permanent'


def _rec(db, value, key=None):
    return {'db_name': db, 'db_number': 1, 'origin': 'test', 'key': key, 'value': value}


def _stores():
    alice = {'id': ALICE, 'name': 'Alice', 'handle': 'alice'}
    bob = {'id': BOB, 'name': 'Bob', 'handle': 'bob'}
    message = {'id': EVENT, 'type': 'conversation.message-add', 'from': ALICE, 'conversation': CONV,
               'time': '2026-01-02T03:04:05.000Z', 'data': {'content': 'hello'}, 'status': 2}
    return {
        'users': [_rec(A_DB, alice), _rec(A_DB, bob), _rec(B_DB, bob), _rec(B_DB, alice)],
        'conversations': [_rec(A_DB, {'id': CONV, 'type': 2, 'others': [BOB]}),
                          _rec(B_DB, {'id': CONV, 'type': 2, 'others': [ALICE]})],
        'events': [_rec(A_DB, dict(message)), _rec(B_DB, dict(message))],
        'secrets': [_rec(f'secrets-{A_DB}', {'k': 1}, 'a'),
                    _rec(f'secrets-{B_DB}', {'k': 2}, 'b'), _rec(f'secrets-{B_DB}', {'k': 3}, 'c'),
                    _rec(f'secrets-{B_DB}', {'k': 4}, 'c')],
    }


class WireAccountsTest(unittest.TestCase):
    def setUp(self):
        self.context = SimpleNamespace(get_files_found=lambda: [], get_relative_path=str)
        patches = [mock.patch.object(wireIndexedDb, '_load', return_value=(_stores(), [])),
                   mock.patch.object(wireIndexedDb, '_recovered_media', return_value=lambda d: '')]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _run(self, artifact, *columns):
        headers, rows, _source = getattr(wireIndexedDb, artifact).__wrapped__(self.context)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        return sorted(tuple(str(row[names.index(c)]) for c in columns) for row in rows)

    def test_each_account_keeps_its_own_users(self):
        self.assertEqual(self._run('wireUsers', 'Account', 'Is Account Owner', 'User ID'), [
            ('@alice', '', BOB), ('@alice', 'Yes', ALICE), ('@bob', '', ALICE), ('@bob', 'Yes', BOB)])

    def test_me_and_outgoing_follow_the_account_the_row_was_read_from(self):
        self.assertEqual(
            self._run('wireMessages', 'Account', 'Outgoing', 'Sender', 'Conversation', 'Message'), [
                ('@alice', '1', 'Alice (me)', 'Bob', 'hello'),
                ('@bob', '0', 'Alice', 'Alice', 'hello')])

    def test_both_accounts_copies_of_one_conversation_are_reported(self):
        self.assertEqual(self._run('wireConversations', 'Account', 'Participants'), [
            ('@alice', 'Bob'), ('@bob', 'Alice')])

    def test_key_material_is_counted_per_account(self):
        self.assertEqual(self._run('wireKeyMaterialInventory', 'Account', 'Key-Material Store',
                                   'Record Count', 'Distinct Keys'), [
            ('@alice', 'secrets', '1', '1'), ('@bob', 'secrets', '3', '2')])


if __name__ == '__main__':
    unittest.main()
