"""Pin the webOS DB8 reader (scripts/webos_db8.py) and the LG webOS DB8 artifacts
(scripts/artifacts/lgWebosDb8.py).

Every store here is synthetic. The byte vectors in ByteVectorTest are written out by hand from the
db8 source (webosose/db8 7b551709f5bbd932e7119752e4929014f4bf8837: MojObjectSerialization.h
lines 32 to 54, MojObjectSerialization.cpp and MojDataSerialization.cpp), not produced by the
encoder below, so the reader is not only checked against a writer from the same hand. The encoder
mirrors MojObjectWriter and is used to build stores, and to repeat db8's own round-trip test
(test/core/MojObjectSerializationTest.cpp) through this reader. Stores are written as real LevelDB
log files, with masked CRC32C and block fragmentation as LevelDB writes them.
"""
import json
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import webos_db8 as db8
from scripts.artifacts import lgWebosDb8 as art
# pylint: enable=wrong-import-position


def _crc32c_table():
    table = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ 0x82F63B78 if c & 1 else c >> 1
        table.append(c)
    return table


_CRC_TABLE = _crc32c_table()


def masked_crc32c(data):
    crc = 0xFFFFFFFF
    for b in data:
        crc = _CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    crc ^= 0xFFFFFFFF
    return ((((crc >> 15) | (crc << 17)) & 0xFFFFFFFF) + 0xA282EAD8) & 0xFFFFFFFF


def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def write_log(path, batches, block=32768):
    """A LevelDB log file: each batch is (sequence, [(key, value or None for a deletion)])."""
    out = bytearray()
    for seq, entries in batches:
        payload = bytearray(struct.pack('<QI', seq, len(entries)))
        for key, value in entries:
            if value is None:
                payload += b'\x00' + varint(len(key)) + key
            else:
                payload += b'\x01' + varint(len(key)) + key + varint(len(value)) + value
        first = True
        remaining = bytes(payload)
        while True:
            left = block - len(out) % block
            if left < 7:
                out += b'\x00' * left
                left = block
            room = left - 7
            piece, remaining = remaining[:room], remaining[room:]
            if first and not remaining:
                kind = 1
            elif first:
                kind = 2
            elif remaining:
                kind = 3
            else:
                kind = 4
            out += struct.pack('<IHB', masked_crc32c(bytes([kind]) + piece), len(piece), kind) + piece
            first = False
            if not remaining:
                break
    with open(path, 'wb') as handle:
        handle.write(bytes(out))


def enc(value, tokens=None):
    """MojObjectWriter's encoding of a value. tokens maps a property name to its token byte."""
    tokens = tokens or {}
    if value is None:
        return b'\x01'
    if value is True:
        return b'\x06'
    if value is False:
        return b'\x05'
    if isinstance(value, Decimal):
        rep = int(value * 1000000)
        return (b'\x07' if rep < 0 else b'\x08') + struct.pack('>q', rep)
    if isinstance(value, int):
        if value < 0:
            return b'\x09' + struct.pack('>q', value)
        if value == 0:
            return b'\x0a'
        if value <= 0xFF:
            return b'\x0b' + bytes([value])
        if value <= 0xFFFF:
            return b'\x0c' + struct.pack('>H', value)
        if value <= 0xFFFFFFFF:
            return b'\x0d' + struct.pack('>I', value)
        return b'\x0e' + struct.pack('>q', value)
    if isinstance(value, str):
        return b'\x04' + value.encode('utf-8') + b'\x00'
    if isinstance(value, list):
        return b'\x03' + b''.join(enc(v, tokens) for v in value) + b'\x00'
    if isinstance(value, dict):
        out = b'\x02'
        for name, item in value.items():
            out += bytes([tokens[name]]) if name in tokens else enc(name)
            out += enc(item, tokens)
        return out + b'\x00'
    raise TypeError(value)


def header(kind_token, rev, deleted=False):
    return b'\x01' + enc(kind_token) + enc(rev) + (b'\x06' if deleted else b'') + b'\x10'


class StoreBuilder:
    """A synthetic DB8 sandwich store: meta part, kinds.db, indexIds.db and objects.db."""

    COOKIES = {b'seq.ldb': 1, b'indexes.ldb': 2, b'objects.db': 3, b'kinds.db': 4, b'indexIds.db': 5}

    def __init__(self):
        self.seq = 1
        self.batches = []
        self.kind_tokens = {}
        self.prop_tokens = {}
        for name, cookie in self.COOKIES.items():
            self.put(b'\x00\x00' + name, struct.pack('<H', cookie))
        self.put(b'\x00\x00', struct.pack('<H', 6))

    def put(self, key, value):
        self.batches.append((self.seq, [(key, value)]))
        self.seq += 1

    def delete(self, key):
        self.batches.append((self.seq, [(key, None)]))
        self.seq += 1

    def part_key(self, part, obj_id):
        return struct.pack('<H', self.COOKIES[part]) + enc(obj_id)

    def kind(self, kind_id, token, props=(), owner=None):
        """Register a kind, with its property names as tokens 32 upward, and its Kind:1 record."""
        self.kind_tokens[kind_id] = token
        self.prop_tokens[kind_id] = {name: 32 + i for i, name in enumerate(props)}
        self.put(self.part_key(b'indexIds.db', kind_id),
                 enc({'kindTokens': {kind_id: token}, 'indexIds': {'_id': token + 100}}))
        if props:
            self.put(self.part_key(b'kinds.db', kind_id), enc({'tokens': dict(self.prop_tokens[kind_id])}))
        if owner is not None:
            self.obj('Kind:1', 'kind-' + kind_id, 1, {'id': kind_id, 'owner': owner})

    def obj(self, kind_id, obj_id, rev, body, deleted=False):
        value = header(self.kind_tokens[kind_id], rev, deleted) + enc(body, self.prop_tokens.get(kind_id))
        self.put(self.part_key(b'objects.db', obj_id), value)
        return value

    def remove(self, obj_id):
        self.delete(self.part_key(b'objects.db', obj_id))

    def write(self, folder, log_name='000003.log', version=True):
        os.makedirs(folder, exist_ok=True)
        write_log(os.path.join(folder, log_name), self.batches)
        with open(os.path.join(folder, 'CURRENT'), 'w', encoding='ascii') as handle:
            handle.write('MANIFEST-000002\n')
        if version:
            with open(os.path.join(folder, '_version'), 'w', encoding='ascii') as handle:
                handle.write('8')
        return folder


def basic_store():
    b = StoreBuilder()
    b.kind('Kind:1', 1)
    b.kind('Object:1', 2)
    b.kind(art.APP_KIND, 10, ('eventId', 'startTimeStamp', 'endTimeStamp'),
           owner='com.webos.service.usercontextmanager')
    b.kind(art.CHANNEL_KIND, 11, ('eventId', 'startTimeStamp', 'endTimeStamp'))
    b.kind(art.RECENTS_KIND, 12, ('appId', 'title', 'subtitle', 'cardSnapShotFilePath', 'fullscreen'))
    b.kind(art.IOT_KIND, 13)
    b.kind(art.MEMBERSHIP_KIND, 14, ('key', 'value', 'regtime'))
    b.kind('com.webos.service.pbs.stb.ch:1', 15)
    b.kind(art.SETTINGS_KIND, 16, ('category', 'app_id', 'value', 'volatile'))
    b.kind('com.webos.notificationhistory:1', 17)
    b.kind('com.webos.service.pbs.genre:1', 18)
    b.obj(art.APP_KIND, 'a1', 50, {'eventId': 'com.example.app', 'startTimeStamp': 1600000000,
                                  'endTimeStamp': 1600000600})
    b.obj(art.APP_KIND, 'a2', 51, {'eventId': 'com.example.other', 'startTimeStamp': 1500000000,
                                  'endTimeStamp': 1500000030})
    b.obj(art.APP_KIND, 'a3', 52, {'eventId': 'com.example.bad', 'startTimeStamp': 'x',
                                  'endTimeStamp': 1500000030})
    b.obj(art.APP_KIND, 'a4', 54, {'eventId': 'com.example.text', 'startTimeStamp': '1500000000',
                                  'endTimeStamp': Decimal('1500000030.5')})
    b.obj(art.CHANNEL_KIND, 'c1', 53, {'eventId': '1_2_3', 'startTimeStamp': 1600000100,
                                      'endTimeStamp': 1600000200})
    b.obj(art.RECENTS_KIND, 'r1', 60, {'appId': 'com.example.app', 'title': 'Old title', 'subtitle': '',
                                      'cardSnapShotFilePath': '/tmp/a.png', 'fullscreen': False})
    b.obj(art.RECENTS_KIND, 'r1', 61, {'appId': 'com.example.app', 'title': 'New title', 'subtitle': 'Sub',
                                      'cardSnapShotFilePath': '/tmp/a.png', 'fullscreen': True})
    b.obj(art.RECENTS_KIND, 'r2', 62, {'appId': 'com.example.gone', 'title': 'Gone', 'subtitle': '',
                                      'cardSnapShotFilePath': '', 'fullscreen': False})
    b.remove('r2')
    b.obj(art.RECENTS_KIND, 'r3', 63, {'appId': 'com.example.flag', 'title': 'Flagged', 'subtitle': '',
                                      'cardSnapShotFilePath': '', 'fullscreen': False}, deleted=True)
    b.obj(art.IOT_KIND, 'i1', 70, {'accountInfoList': [{'userId': 'u@example.com', 'userNo': 'N1',
                                                       'aliasName': 'Alias', 'requester': 'app'},
                                                      {'userId': 'v@example.com', 'userNo': 'N2'}],
                                  'deviceId': 'DEV1', 'isEnabled': False, 'endPointUrl': 'https://example.invalid/iot',
                                  'pubTopic': 'p', 'subTopic': 's', 'shadowTopic': 'h',
                                  'cert': '-----BEGIN CERTIFICATE-----', 'privKey': ''})
    b.obj(art.IOT_KIND, 'i2', 71, {'deviceId': 'DEV2'})
    b.obj(art.MEMBERSHIP_KIND, 'm1', 80, {'key': '/example/key', 'value': 'v', 'regtime': '1600000000123'})
    b.obj('com.webos.service.pbs.stb.ch:1', 'ch1', 90, {'channelNumber': '7', 'channelName': 'Seven',
                                                       'favoriteGroup': [], 'favoriteIdxC': 3, 'locked': False,
                                                       'skipped': False, 'channelId': 'X7'})
    b.obj('com.webos.service.pbs.stb.ch:1', 'ch2', 91, {'channelNumber': '8', 'channelName': 'Eight',
                                                       'favoriteGroup': [], 'locked': False, 'skipped': False,
                                                       'channelId': 'X8'})
    b.obj('com.webos.service.pbs.stb.ch:1', 'ch3', 92, {'channelNumber': '9', 'channelName': 'Nine',
                                                       'favoriteGroup': ['A'], 'locked': True, 'skipped': False,
                                                       'channelId': 'X9'})
    b.obj(art.SETTINGS_KIND, 's1', 100, {'category': 'general', 'app_id': '', 'value': {'exampleKey': 'A',
                                                                                   'offset': Decimal('1.5')},
                                        'volatile': False})
    b.obj(art.SETTINGS_KIND, 's2', 101, {'category': 'picture$example', 'app_id': '', 'value': {'exampleLevel': 80}})
    b.obj('com.webos.notificationhistory:1', 'n1', 110, {'title': 'Hello', 'timestamp': 1600000000000})
    b.obj('com.webos.service.pbs.genre:1', 'g1', 111, {'genreName': 'News'})
    return b


class ByteVectorTest(unittest.TestCase):
    """Values written out by hand from MojObjectWriter (markers, widths, big-endian)."""

    def test_scalars(self):
        cases = [
            (b'\x01', None), (b'\x05', False), (b'\x06', True), (b'\x0a', 0),
            (b'\x0b\xff', 255), (b'\x0c\x01\x00', 256), (b'\x0c\xff\xff', 65535),
            (b'\x0d\x00\x01\x00\x00', 65536), (b'\x0d\xff\xff\xff\xff', 4294967295),
            (b'\x0e\x00\x00\x00\x01\x00\x00\x00\x00', 4294967296),
            (b'\x09\xff\xff\xff\xff\xff\xff\xff\xd3', -45),
            (b'\x08\x00\x00\x00\x00\x00\x2f\xe9\xa0', Decimal('3.14')),
            (b'\x07\xff\xff\xff\xff\xff\xf8\x5e\xe0', Decimal('-0.5')),
            (b'\x04hi\x00', 'hi'), (b'\x04\x00', ''),
            (b'\x03\x0b\x01\x04x\x00\x00', [1, 'x']),
            (b'\x02\x04a\x00\x0b\x02\x04b\x00\x02\x00\x00', {'a': 2, 'b': {}}),
        ]
        for data, expected in cases:
            with self.subTest(data=data.hex()):
                self.assertEqual(db8.decode_value(data), expected)

    def test_tokens_stand_for_names_and_string_values(self):
        tokens = ['title', 'Live']
        self.assertEqual(db8.decode_value(b'\x02\x20\x21\x00', tokens), {'title': 'Live'})

    def test_extension_value_is_skipped(self):
        # MojObjectReader::next skips an extension value without visiting anything.
        self.assertEqual(db8.decode_value(b'\x03\x0f\x00\x00\x00\x02ab\x0b\x05\x00'), [5])
        self.assertEqual(db8.decode_value(b'\x02\x04a\x00\x0f\x00\x00\x00\x01z\x00'), {'a': None})

    def test_malformed(self):
        for data in (b'\x02\x04a\x00', b'\x04abc', b'\x0b', b'\x0b\x01\x00', b'\x02\x20\x0b\x01\x00',
                     b'\x10'):
            with self.subTest(data=data.hex()):
                with self.assertRaises(db8.Db8Error):
                    db8.decode_value(data)
        with self.assertRaises(db8.Db8Error):
            db8.decode_value(b'\x02\x21\x0b\x01\x00', ['only'])

    def test_header(self):
        self.assertEqual(db8.read_header(b'\x01\x0b\x0a\x0c\x01\x00\x10\x02\x00'), (10, 256, False, 7))
        self.assertEqual(db8.read_header(b'\x01\x0b\x0a\x0b\x05\x06\x10'), (10, 5, True, 7))
        self.assertEqual(db8.read_header(b'\x01\x0b\x0a\x0b\x05\x05\x04x\x00\x10'), (10, 5, False, 10))
        with self.assertRaises(db8.Db8Error):
            db8.read_header(b'\x02\x0b\x0a\x0b\x05\x10')
        with self.assertRaises(db8.Db8Error):
            db8.read_header(b'\x01\x0b\x0a\x0b\x05')


class RoundTripTest(unittest.TestCase):
    def test_db8_serialization_test_object(self):
        # The object db8's own MojObjectSerializationTest round-trips; decimals as MojDecimal.
        obj = json.loads('{"i1":-9223372036854775807, "i2":-888888, "i3":-45, "i4":0, "i5":100, '
                         '"i6":255, "i7":9999, "i8":65535, "i9":65536, "i10":4294967295, '
                         '"i11":4294967296, "i12":9223372036854775807, '
                         '"d1":3.14, "d2":0.2, "s1":"hello\\t\\"world\\"", "s2":"", '
                         '"o1":{"a1":[[[],[]],2,3,4,{},{"t":4},null,true,false,4.35], "i1":42}, '
                         '"n1":null, "b1":true, "b2":false}', parse_float=Decimal)
        self.assertEqual(db8.decode_value(enc(obj)), obj)

    def test_token_encoded_object(self):
        tokens = {'eventId': 32, 'startTimeStamp': 33}
        body = {'eventId': 'x', 'startTimeStamp': 5, 'other': 'y'}
        self.assertEqual(db8.decode_value(enc(body, tokens), ['eventId', 'startTimeStamp']), body)


class TempRoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        art._STORES.clear()  # pylint: disable=protected-access

    def tearDown(self):
        self.tmp.cleanup()
        art._STORES.clear()  # pylint: disable=protected-access

    def folder(self, relative):
        return os.path.join(self.root, *relative.split('/'))


class StoreTest(TempRoot):
    def test_parts_kinds_and_tokens(self):
        store = db8.Db8Store(basic_store().write(self.folder('var/db/main')))
        self.assertTrue(store.is_db8())
        self.assertEqual(store.parts[b'objects.db'], b'\x03\x00')
        self.assertEqual(store.kinds[10], art.APP_KIND)
        self.assertEqual(store.tokens[art.APP_KIND], ['eventId', 'startTimeStamp', 'endTimeStamp'])
        self.assertEqual(store.errors, [])

    def test_versions_and_status(self):
        store = db8.Db8Store(basic_store().write(self.folder('var/db/main')))
        recents = [(o.id, o.body['title'], o.status, o.deleted, o.rev) for o in store.object_versions()
                   if o.kind == art.RECENTS_KIND]
        self.assertEqual(recents, [('r1', 'Old title', db8.STATUS_SUPERSEDED, False, 60),
                                   ('r1', 'New title', db8.STATUS_LIVE, False, 61),
                                   ('r2', 'Gone', db8.STATUS_REMOVED, False, 62),
                                   ('r3', 'Flagged', db8.STATUS_LIVE, True, 63)])
        self.assertEqual(sorted(o.id for o in store.objects() if o.kind == art.RECENTS_KIND), ['r1', 'r3'])

    def test_identical_older_version_and_duplicate_sequence_are_not_repeated(self):
        b = StoreBuilder()
        b.kind('k:1', 10, ('a',))
        value = b.obj('k:1', 'o', 5, {'a': 1})
        b.put(b.part_key(b'objects.db', 'o'), value)
        folder = b.write(self.folder('db/main'))
        # The same records again in a second log: one record can sit in two files.
        write_log(os.path.join(folder, '000004.log'), b.batches)
        store = db8.Db8Store(folder)
        self.assertEqual([(o.id, o.status) for o in store.object_versions()], [('o', db8.STATUS_LIVE)])

    def test_undecodable_record_is_named_and_skipped(self):
        b = StoreBuilder()
        b.kind('k:1', 10, ('a',))
        b.obj('k:1', 'good', 5, {'a': 1})
        b.put(b.part_key(b'objects.db', 'bad'), header(10, 6) + b'\x02\x40\x0b\x01\x00')
        b.put(b.part_key(b'objects.db', 'nokind'), header(99, 7) + b'\x02\x00')
        store = db8.Db8Store(b.write(self.folder('db/main')))
        self.assertEqual([o.id for o in store.objects()], ['good'])
        self.assertEqual(sorted(e[2].split(' ')[0] for e in store.errors), ['kind', 'token'])

    def test_fragmented_log_record(self):
        b = StoreBuilder()
        b.kind('k:1', 10, ('a',))
        b.obj('k:1', 'big', 5, {'a': 'x' * 70000})
        store = db8.Db8Store(b.write(self.folder('db/main')))
        self.assertEqual([len(o.body['a']) for o in store.objects()], [70000])

    def test_meta_part_is_the_two_zero_byte_prefix(self):
        # A cookie of 256 is b'\x00\x01' in host (little-endian) order: its keys start with a
        # zero byte but are not the meta part, even when a value is two bytes long.
        b = StoreBuilder()
        b.put(b'\x00\x00far.db', struct.pack('<H', 256))
        b.put(b'\x00\x01' + enc('k'), b'\x0b\x05')
        store = db8.Db8Store(b.write(self.folder('db/main')))
        self.assertEqual(sorted(store.parts), [b'far.db', b'indexIds.db', b'indexes.ldb', b'kinds.db',
                                               b'objects.db', b'seq.ldb'])

    def test_plain_leveldb_is_not_db8(self):
        folder = self.folder('db/main')
        os.makedirs(folder)
        write_log(os.path.join(folder, '000003.log'), [(1, [(b'hello', b'world')])])
        self.assertFalse(db8.Db8Store(folder).is_db8())


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(TempRoot):
    def setUp(self):
        super().setUp()
        self.logged = []
        patcher = mock.patch.object(art, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = []

    def add_store(self, builder, relative, **kwargs):
        folder = builder.write(self.folder(relative), **kwargs)
        for name in sorted(os.listdir(folder)):
            self.paths.append(os.path.join(folder, name))
        return folder

    def run_artifact(self, func):
        return getattr(art, func).__wrapped__(FakeContext(self.paths, self.root))

    def rows(self, func):
        headers, rows, _source = self.run_artifact(func)
        names = [h[0] if isinstance(h, tuple) else h for h in headers]
        self.assertTrue(all(len(r) == len(names) for r in rows))
        return [dict(zip(names, r)) for r in rows]

    def test_app_usage(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8AppUsage')
        self.assertEqual([(r['App ID'], r['Duration (seconds)'], r['Revision']) for r in rows],
                         [('com.example.other', 30, 51), ('com.example.app', 600, 50), ('com.example.bad', '', 52),
                          ('com.example.text', '', 54)])
        # Text and decimals are not whole seconds, so they stay out of the time columns.
        self.assertEqual((rows[3]['Start Time (UTC)'], rows[3]['End Time (UTC)']), ('', ''))
        self.assertEqual(rows[0]['Start Time (UTC)'], datetime.fromtimestamp(1500000000, timezone.utc))
        self.assertEqual(rows[1]['End Time (UTC)'], datetime.fromtimestamp(1600000600, timezone.utc))
        self.assertEqual(rows[2]['Start Time (UTC)'], '')
        self.assertEqual((rows[0]['Record Status'], rows[0]['DB8 Deleted'], rows[0]['Store']),
                         ('Live', 'No', 'var/db/main'))
        self.assertTrue(any('not a whole number' in line for line in self.logged))

    def test_channel_usage(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8ChannelUsage')
        self.assertEqual([(r['Channel ID'], r['Duration (seconds)']) for r in rows], [('1_2_3', 100)])

    def test_recent_items(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8RecentItems')
        self.assertEqual([(r['Revision'], r['Title'], r['Record Status'], r['DB8 Deleted'], r['Fullscreen'])
                          for r in rows],
                         [(60, 'Old title', db8.STATUS_SUPERSEDED, 'No', 'false'),
                          (61, 'New title', 'Live', 'No', 'true'),
                          (62, 'Gone', db8.STATUS_REMOVED, 'No', 'false'),
                          (63, 'Flagged', 'Live', 'Yes', 'false')])

    def test_iot_client(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8IotClient')
        self.assertEqual([(r['User ID'], r['User No'], r['Alias Name'], r['Device ID']) for r in rows],
                         [('u@example.com', 'N1', 'Alias', 'DEV1'), ('v@example.com', 'N2', '', 'DEV1'),
                          ('', '', '', 'DEV2')])
        self.assertEqual((rows[0]['Certificate Stored'], rows[0]['Private Key Stored'], rows[0]['Enabled']),
                         ('Yes (27 characters)', 'No', 'false'))
        self.assertNotIn('BEGIN', json.dumps(rows, default=str))

    def test_membership(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8Membership')
        self.assertEqual(rows[0]['Reg Time (UTC)'], datetime.fromtimestamp(1600000000.123, timezone.utc))
        self.assertEqual((rows[0]['Reg Time (as stored)'], rows[0]['Key'], rows[0]['Value']),
                         ('1600000000123', '/example/key', 'v'))

    def test_channel_flags(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8ChannelFlags')
        self.assertEqual([(r['Channel Number'], r['Favorite Groups'], r['Favorite Positions'], r['Locked'])
                          for r in rows], [('7', '[]', 'favoriteIdxC=3', 'false'), ('9', '["A"]', '', 'true')])
        self.assertTrue(any('1 channel records with no favorite' in line for line in self.logged))

    def test_settings(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8Settings')
        self.assertEqual([(r['Category'], r['Key'], r['Value'], r['Volatile']) for r in rows],
                         [('general', 'exampleKey', 'A', 'false'), ('general', 'offset', '1.5', 'false')])
        self.assertTrue(any('1 picture, sound and 3d' in line for line in self.logged))

    def test_other_kinds(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = self.rows('lgWebosDb8OtherKinds')
        self.assertEqual([(r['Kind'], json.loads(r['Fields (as stored)'])) for r in rows],
                         [('com.webos.notificationhistory:1', {'timestamp': 1600000000000, 'title': 'Hello'})])

    def test_kinds(self):
        self.add_store(basic_store(), 'var/db/main')
        rows = {r['Kind']: r for r in self.rows('lgWebosDb8Kinds')}
        self.assertEqual(len(rows), 11)
        recents = rows[art.RECENTS_KIND]
        self.assertEqual((recents['Live Objects'], recents['DB8 Deleted'], recents['Older Versions'],
                          recents['Removed Records']), (2, 1, 1, 1))
        self.assertEqual(rows[art.APP_KIND]['Owner'], 'com.webos.service.usercontextmanager')
        self.assertEqual(rows['Object:1']['Live Objects'], 0)

    def test_source_paths_and_two_stores(self):
        self.add_store(basic_store(), 'var/db/main')
        media = StoreBuilder()
        media.kind(art.APP_KIND, 10, ('eventId', 'startTimeStamp', 'endTimeStamp'))
        media.obj(art.APP_KIND, 'z', 5, {'eventId': 'com.example.media', 'startTimeStamp': 1400000000,
                                         'endTimeStamp': 1400000001})
        self.add_store(media, 'media/cryptofs/data/db8/mediadb/media')
        _headers, rows, source = self.run_artifact('lgWebosDb8AppUsage')
        self.assertEqual(sorted({r[-1] for r in rows}), ['media/cryptofs/data/db8/mediadb/media', 'var/db/main'])
        self.assertEqual(len(rows), 5)
        self.assertEqual(sorted(os.path.basename(p) for p in source.split('\n')), ['000003.log', '000003.log'])

    def test_folder_without_version_file_is_not_read(self):
        self.add_store(basic_store(), 'var/db/main', version=False)
        self.assertEqual(self.rows('lgWebosDb8AppUsage'), [])
        self.assertEqual(self.rows('lgWebosDb8Kinds'), [])

    def test_leveldb_that_is_not_db8_is_not_read(self):
        folder = self.folder('home/u/db/main')
        os.makedirs(folder)
        write_log(os.path.join(folder, '000003.log'), [(1, [(b'\x00\x00objects', b'\x03\x00')])])
        for name in ('CURRENT', '_version'):
            with open(os.path.join(folder, name), 'w', encoding='ascii') as handle:
                handle.write('x')
        self.paths += [os.path.join(folder, n) for n in os.listdir(folder)]
        headers, rows, source = self.run_artifact('lgWebosDb8Kinds')
        self.assertEqual((len(headers), rows, source), (7, [], ''))

    def test_decoy_kind_names_are_not_reported(self):
        b = StoreBuilder()
        b.kind('com.example.usercontextmanager.app:1', 10, ('eventId', 'startTimeStamp', 'endTimeStamp'))
        b.obj('com.example.usercontextmanager.app:1', 'd', 5, {'eventId': 'x', 'startTimeStamp': 1,
                                                                 'endTimeStamp': 2})
        self.add_store(b, 'var/db/main')
        self.assertEqual(self.rows('lgWebosDb8AppUsage'), [])


if __name__ == '__main__':
    unittest.main()
