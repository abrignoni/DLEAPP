"""Pin how scripts/chromium/sync_data.py and the chromiumSyncData artifacts read a Sync Data store.

Author: @AlexisBrignoni, Claude.

Every store here is synthetic: a LevelDB log file written by the helpers below,
whose values are protocol buffers encoded by hand with the field numbers of
Chromium's components/sync/protocol messages. The expected values are written
out, never read back from the code under test.
"""
import datetime
import pathlib
import struct
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.chromium import sync_data  # pylint: disable=wrong-import-position
from scripts.artifacts import chromiumSyncData  # pylint: disable=wrong-import-position

UTC = datetime.timezone.utc
PROFILE = 'Users/someone/AppData/Local/Google/Chrome/User Data/Profile 2'
SECOND_PROFILE = 'Users/someone/AppData/Local/Microsoft/Edge/User Data/Default'
OTHER_USER = 'Users/another/AppData/Local/Google/Chrome/User Data/Default'
MAC_PROFILE = 'Users/someone/Library/Application Support/Google/Chrome/Default'
MAC_DATA_VIEW = 'System/Volumes/Data/' + MAC_PROFILE
OPERA_ROOT = 'Users/someone/AppData/Roaming/Opera Software/Opera Stable'


def varint(value):
    value &= (1 << 64) - 1
    out = bytearray()
    while value > 127:
        out.append((value & 127) | 128)
        value >>= 7
    return bytes(out + bytes([value]))


def field(number, value):
    """One encoded field: an int is a varint, bytes or str length-delimited."""
    if isinstance(value, bool):
        return varint(number << 3) + varint(int(value))
    if isinstance(value, int):
        return varint(number << 3) + varint(value)
    if isinstance(value, str):
        value = value.encode('utf-8')
    return varint((number << 3) | 2) + varint(len(value)) + value


def message(*fields):
    return b''.join(fields)


def log_file(records):
    """A LevelDB log holding one write batch per (sequence, key, value) record; value None deletes."""
    out = b''
    for sequence, key, value in records:
        payload = struct.pack('<QI', sequence, 1)
        if value is None:
            payload += b'\x00' + varint(len(key)) + key
        else:
            payload += b'\x01' + varint(len(key)) + key + varint(len(value)) + value
        block = struct.pack('<IHB', 0, len(payload), 1) + payload
        out += block
    return out


def device(guid, name, updated_ms, os_type=None, version=None, old_version=None):
    parts = [field(1, guid), field(2, name), field(3, 1), field(4, 'Chrome WIN 1.0'),
             field(7, 'signin-' + guid), field(8, updated_ms), field(11, 'Model ' + name),
             field(12, 'Maker')]
    if old_version:
        parts.append(field(5, old_version))
    if version:
        parts.append(field(17, message(field(1, version))))
    if os_type is not None:
        parts.append(field(19, os_type))
    return message(*parts)


def header(tag, name, windows, start_ms=None):
    parts = [field(3, name), field(4, 6), field(5, 2)]
    for window_id, tabs in windows:
        parts.append(field(2, message(field(1, window_id), field(3, 1),
                                      *[field(4, tab) for tab in tabs])))
    if start_ms:
        parts.append(field(6, start_ms))
    return message(field(1, tag), field(2, message(*parts)))


def navigation(url, title, when_ms, transition=1, status=200, address_bar=True):
    return message(field(2, url), field(3, ''), field(4, title), field(6, transition),
                   field(9, when_ms), field(11, address_bar), field(20, status))


def tab(tag, node, tab_id, window_id, navigations, current, last_active_ms=None):
    parts = [field(1, tab_id), field(2, window_id), field(4, current), field(5, False)]
    parts += [field(7, nav) for nav in navigations]
    if last_active_ms:
        parts.append(field(14, last_active_ms))
    return message(field(1, tag), field(3, message(*parts)), field(4, node))


def global_metadata(guid):
    return message(field(5, guid))


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _store(self, profile, records, name='000003.log'):
        folder = self.root / profile / 'Sync Data' / 'LevelDB'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(log_file(records))
        (folder / 'CURRENT').write_bytes(b'MANIFEST-000001\n')
        self.files += [str(folder / name), str(folder / 'CURRENT')]
        return folder

    def _context(self):
        return SimpleNamespace(
            get_files_found=lambda: list(self.files),
            get_relative_path=lambda p: pathlib.Path(p).relative_to(self.root).as_posix())

    def _run(self, function):
        with mock.patch.object(chromiumSyncData, 'logfunc'), \
                mock.patch('scripts.ilapfuncs.logfunc'):
            return getattr(chromiumSyncData, function).__wrapped__(self._context())

    def _standard_store(self, profile=PROFILE):
        return self._store(profile, [
            (1, b'device_info-GlobalMetadata', global_metadata('LOCAL')),
            (2, b'sessions-GlobalMetadata', global_metadata('LOCAL')),
            (3, b'device_info-dt-LOCAL', device('LOCAL', 'Old Name', 1_600_000_000_000)),
            (9, b'device_info-dt-LOCAL', device('LOCAL', 'Desk', 1_700_000_000_000, os_type=1,
                                                 version='120.0.1', old_version='119')),
            (4, b'device_info-dt-PHONE', device('PHONE', 'Phone', 1_690_000_000_000)),
            (5, b'device_info-dt-GONE', device('GONE', 'Gone', 1_650_000_000_000)),
            (6, b'device_info-dt-GONE', None),
            (7, b'sessions-dt-PHONE-h', header('PHONE', 'Phone', [(10, [20])], 1_680_000_000_000)),
            (8, b'sessions-dt-PHONE-t', tab('PHONE', 0, 20, 10, [
                navigation('https://example.com/a', 'A', 1_690_000_100_000),
                navigation('https://example.com/b', 'B', 1_690_000_200_000, transition=0,
                           status=404, address_bar=False)], current=1,
                last_active_ms=1_690_000_300_000)),
            (10, b'sessions-dt-NOHEADER-t', tab('PHONE', 1, 21, 10, [], current=0)),
            (11, b'sessions-dt-BAD', b'\x0a\x05ab'),
            (12, b'preferences-dt-x', b'\x0a\x01x'),
        ])

    def test_only_the_newest_version_of_each_key_is_kept(self):
        folder = self._standard_store()
        store = sync_data.SyncStore(str(folder))
        self.assertEqual(store.records, 12)
        self.assertEqual(store.superseded, 2)
        self.assertEqual(store.deleted, 1)
        guids = [key for _account, key, _value in store.records_of('device_info')]
        self.assertEqual(guids, ['LOCAL', 'PHONE'])
        self.assertEqual(store.local_cache_guid('device_info'), 'LOCAL')
        self.assertEqual(store.local_cache_guid('send_tab_to_self'), '')

    def test_decode_follows_the_published_field_numbers(self):
        decoded = sync_data.decode(device('G', 'Name', 1_700_000_000_000, os_type=2,
                                          version='1.2'), 'DeviceInfoSpecifics')
        self.assertEqual(decoded, {
            'cache_guid': 'G', 'client_name': 'Name', 'device_type': 1,
            'sync_user_agent': 'Chrome WIN 1.0', 'signin_scoped_device_id': 'signin-G',
            'last_updated_timestamp': 1_700_000_000_000, 'model': 'Model Name',
            'manufacturer': 'Maker', 'chrome_version_info': {'version_number': '1.2'},
            'os_type': 2})

    def test_a_negative_int32_reads_as_negative(self):
        self.assertEqual(sync_data.decode(field(2, -1), 'SessionWindow'),
                         {'selected_tab_index': -1})

    def test_a_wire_type_that_disagrees_with_the_schema_raises(self):
        with self.assertRaises(sync_data.ProtoError):
            sync_data.decode(field(1, 5), 'SessionSpecifics')
        with self.assertRaises(sync_data.ProtoError):
            sync_data.decode(b'\x0a\x05ab', 'SessionSpecifics')

    def test_devices(self):
        self._standard_store()
        headers, rows, source = self._run('chromiumSyncDevices')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (datetime.datetime(2023, 11, 14, 22, 13, 20, tzinfo=UTC), 'Desk', 'Yes', 'Maker',
             'Model Desk', 'OS_TYPE_WINDOWS (1)', '', 'TYPE_WIN (1)', '120.0.1',
             'Chrome WIN 1.0', 'LOCAL', 'signin-LOCAL', 'Google Chrome', 'Profile 2',
             'someone', f'{PROFILE}/Sync Data/LevelDB'),
            (datetime.datetime(2023, 7, 22, 4, 26, 40, tzinfo=UTC), 'Phone', 'No', 'Maker',
             'Model Phone', '', '', 'TYPE_WIN (1)', '', 'Chrome WIN 1.0', 'PHONE',
             'signin-PHONE', 'Google Chrome', 'Profile 2', 'someone',
             f'{PROFILE}/Sync Data/LevelDB'),
        ])
        self.assertEqual(source, str(self.root / PROFILE / 'Sync Data' / 'LevelDB'))

    def test_synced_tabs_take_the_device_name_from_the_header(self):
        self._standard_store()
        headers, rows, _source = self._run('chromiumSyncedTabs')
        self.assertEqual(len(headers), len(rows[0]))
        tail = ('PHONE', 'Google Chrome', 'Profile 2', 'someone', f'{PROFILE}/Sync Data/LevelDB')
        self.assertEqual(rows, [
            (datetime.datetime(2023, 7, 22, 4, 28, 20, tzinfo=UTC),
             datetime.datetime(2023, 7, 22, 4, 31, 40, tzinfo=UTC), 'Phone', 'No',
             'https://example.com/a', 'A', '', 200, 'TYPED (1)', 'Yes', 0, 'No',
             'No', 20, 10) + tail,
            (datetime.datetime(2023, 7, 22, 4, 30, tzinfo=UTC),
             datetime.datetime(2023, 7, 22, 4, 31, 40, tzinfo=UTC), 'Phone', 'No',
             'https://example.com/b', 'B', '', 404, 'LINK (0)', 'No', 1, 'Yes',
             'No', 20, 10) + tail,
        ])

    def test_synced_sessions(self):
        self._standard_store()
        headers, rows, _source = self._run('chromiumSyncedSessions')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            ('Phone', 'No', 'DEVICE_FORM_FACTOR_PHONE (2)', 'TYPE_PHONE (6)', 1, 1,
             'TYPE_TABBED (1)', datetime.datetime(2023, 3, 28, 10, 40, tzinfo=UTC), 'PHONE',
             'Google Chrome', 'Profile 2', 'someone', f'{PROFILE}/Sync Data/LevelDB'),
        ])

    def test_send_tab_to_self(self):
        shared = message(field(1, 'Title'), field(2, 'https://example.com/s'),
                         field(3, 13_340_000_000_000_000), field(4, 'Desk'), field(5, 'E1'),
                         field(7, 'PHONE'), field(8, True), field(9, False),
                         field(13, 13_340_000_001_000_000))
        self._store(PROFILE, [
            (1, b'device_info-dt-PHONE', device('PHONE', 'Phone', 1_690_000_000_000)),
            (2, b'send_tab_to_self-dt-E1', message(field(1, shared))),
        ])
        headers, rows, _source = self._run('chromiumSendTabToSelf')
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (datetime.datetime(2023, 9, 24, 3, 33, 20, tzinfo=UTC),
             datetime.datetime(2023, 9, 24, 3, 33, 21, tzinfo=UTC), '', '', 'Title',
             'https://example.com/s', 'Desk', 'Phone', 'PHONE', 'Yes', 'No', 'E1',
             'Google Chrome', 'Profile 2', 'someone', f'{PROFILE}/Sync Data/LevelDB'),
        ])

    def test_two_profiles_and_two_users_each_add_their_own_rows(self):
        self._standard_store(PROFILE)
        self._standard_store(SECOND_PROFILE)
        self._standard_store(OTHER_USER)
        _headers, rows, source = self._run('chromiumSyncDevices')
        self.assertEqual([(row[-4], row[-3], row[-2], row[1]) for row in rows], [
            ('Google Chrome', 'Default', 'another', 'Desk'),
            ('Google Chrome', 'Default', 'another', 'Phone'),
            ('Google Chrome', 'Profile 2', 'someone', 'Desk'),
            ('Google Chrome', 'Profile 2', 'someone', 'Phone'),
            ('Microsoft Edge', 'Default', 'someone', 'Desk'),
            ('Microsoft Edge', 'Default', 'someone', 'Phone'),
        ])
        self.assertEqual(len(source.split('\n')), 3)

    def test_identical_mac_views_are_read_once_and_differing_ones_twice(self):
        self._standard_store(MAC_PROFILE)
        self._standard_store(MAC_DATA_VIEW)
        _headers, rows, _source = self._run('chromiumSyncDevices')
        self.assertEqual(len(rows), 2)
        self._store(MAC_DATA_VIEW, [(20, b'device_info-dt-NEW', device('NEW', 'New', 1))],
                    name='000004.log')
        _headers, rows, _source = self._run('chromiumSyncDevices')
        self.assertEqual(len(rows), 5)

    def test_a_store_directly_in_the_user_data_folder_names_that_folder_as_profile(self):
        self._store(OPERA_ROOT, [(1, b'device_info-dt-G', device('G', 'Opera Box', 1))])
        _headers, rows, _source = self._run('chromiumSyncDevices')
        self.assertEqual([(row[-4], row[-3], row[-2]) for row in rows],
                         [('Opera', 'Opera Stable', 'someone')])

    def test_a_folder_outside_a_browser_profile_is_not_read(self):
        self._store('Users/someone/AppData/Local/SomeApp/EBWebView/Default',
                    [(1, b'device_info-dt-G', device('G', 'Embedded', 1))])
        _headers, rows, source = self._run('chromiumSyncDevices')
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
