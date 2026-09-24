"""Pin three Wire values against their sources rather than against the code.

The conversation Type labels follow the CONVERSATION_TYPE enum in Wire's web client
(REGULAR 0, SELF 1, ONE_TO_ONE 2, CONNECT 3, GLOBAL_TEAM 4). A recovered asset takes its
time from the confirmed version of its asset-add event, the version Wire Attachments
reports, not from whichever version LevelDB happened to return last. The service-worker
cache reports the Content-Type header stored with the cached response, never a value
from the request's Accept header. Every input is built by hand and every expected value
is written out.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import wireIndexedDb, wireServiceWorkerCache  # pylint: disable=wrong-import-position
from scripts.ccl import wire_assets  # pylint: disable=wrong-import-position

OWNER = '11111111-1111-4111-8111-111111111111'
DB = f'wire@production@{OWNER}@permanent'


def _rec(value):
    return {'db_name': DB, 'db_number': 1, 'origin': 'test', 'key': None, 'value': value}


def _header(tag, name, value):
    entry = b'\x0a' + bytes([len(name)]) + name + b'\x12' + bytes([len(value)]) + value
    return tag + bytes([len(entry)]) + entry


class WireConversationTypeTest(unittest.TestCase):
    def test_type_codes_carry_the_wire_enum_names(self):
        stores = {'users': [_rec({'id': OWNER, 'handle': 'owner'})],
                  'conversations': [_rec({'id': f'c{code}', 'type': code, 'name': f'n{code}'})
                                    for code in (0, 1, 2, 3, 4, 7)]}
        context = SimpleNamespace(get_files_found=lambda: [], get_relative_path=str)
        with mock.patch.object(wireIndexedDb, '_load', return_value=(stores, [])):
            headers, rows, _ = wireIndexedDb.wireConversations.__wrapped__(context)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        by_name = {row[names.index('Name')]: row[names.index('Type')] for row in rows}
        self.assertEqual(by_name, {'n0': 'Regular', 'n1': 'Self', 'n2': 'One-to-one',
                                   'n3': 'Connect', 'n4': 'Global team', 'n7': 'Type 7'})


class WireAssetEventVersionTest(unittest.TestCase):
    SENDING = {'id': 'e1', 'type': 'conversation.asset-add', 'from': OWNER, 'conversation': 'c',
               'time': '2026-07-23T13:42:36.441Z', 'status': 1,
               'data': {'otr_key': b'k' * 32, 'sha256': b'\x01' * 32, 'key': '3-1-a'}}
    SENT = dict(SENDING, time='2026-07-23T13:42:37.374Z', status=2, primary_key='p1')

    def test_the_confirmed_version_gives_the_time_in_either_order(self):
        for versions in ((self.SENDING, self.SENT), (self.SENT, self.SENDING)):
            index = wire_assets.build_asset_index({'events': [_rec(v) for v in versions]})
            self.assertEqual([d['time'] for d in index.values()], ['2026-07-23T13:42:37.374Z'])


class WireServiceWorkerContentTypeTest(unittest.TestCase):
    REQUEST = _header(b'\x12', b'Accept', b'application/json, text/plain, */*')
    RESPONSE = _header(b'\x22', b'Content-Type', b'application/octet-stream')

    def test_the_response_header_is_read_and_the_request_accept_header_is_not(self):
        read = wireServiceWorkerCache._response_content_type  # pylint: disable=protected-access
        self.assertEqual(read(self.REQUEST + self.RESPONSE), 'application/octet-stream')
        self.assertEqual(read(self.REQUEST), '')

    def test_the_artifact_reports_the_response_header(self):
        url = b'https://prod-nginz-https.wire.com/assets/v4/wire.com/3-5-01234567-89ab-4cde-8f01-23456789abcd'
        with tempfile.TemporaryDirectory() as folder:
            entry = os.path.join(folder, '0123456789abcdef_0')
            with open(entry, 'wb') as handle:
                handle.write(b'\x00' * 8 + url + b'\x00' + self.REQUEST + self.RESPONSE + b'\x00' * 8)
            context = SimpleNamespace(get_files_found=lambda: [entry], get_relative_path=str)
            headers, rows, _ = wireServiceWorkerCache.wireServiceWorkerCache.__wrapped__(context)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertEqual([row[names.index('Response Content Type')] for row in rows],
                         ['application/octet-stream'])


if __name__ == '__main__':
    unittest.main()
