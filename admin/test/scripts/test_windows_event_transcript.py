"""Pin the rows scripts/artifacts/windowsEventTranscript.py reads.

The database is built here with the tables EventTranscript.db carries. Every value is
made up for the test; times are written as FILETIME values computed from the expected
datetimes, and each payload carries the top-level keys the real payloads have.
"""
import datetime
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsEventTranscript as et  # pylint: disable=wrong-import-position

_UTC = datetime.timezone.utc
_FOLDER = 'ProgramData/Microsoft/Diagnosis/EventTranscript'
_RELATIVE = f'{_FOLDER}/EventTranscript.db'
_SCHEMA = (
    'CREATE TABLE events_persisted (sid TEXT, timestamp INTEGER, payload TEXT, full_event_name TEXT, '
    'full_event_name_hash INTEGER, event_keywords INTEGER, is_core INTEGER, provider_group_id INTEGER, '
    'logging_binary_name TEXT, friendly_logging_binary_name TEXT, compressed_payload_size INTEGER, '
    'producer_id INTEGER, extra1 TEXT, extra2 TEXT, extra3 TEXT)',
    'CREATE TABLE provider_groups (group_id INTEGER PRIMARY KEY AUTOINCREMENT, group_guid TEXT)',
    'CREATE TABLE event_tags (full_event_name_hash INTEGER, tag_id INTEGER)',
    'CREATE TABLE tag_descriptions (tag_id INTEGER, locale_name TEXT, tag_name TEXT, description TEXT)',
    'CREATE TABLE producers (producer_id INTEGER PRIMARY KEY AUTOINCREMENT, producer_id_text TEXT)',
    'CREATE TABLE event_categories (full_event_name_hash INTEGER, category_id INTEGER)',
    'CREATE TABLE categories (category_id INTEGER PRIMARY KEY AUTOINCREMENT, category_id_text TEXT, '
    'producer_id INTEGER)',
)
_SID = 'S-1-5-21-1-2-3-1001'
_GROUP = '11111111-2222-3333-4444-555555555555'
_EDGE = 'Aria.0123.Microsoft.WebBrowser.HistoryJournal.'
_SUMMARY = 'Win32kTraceLogging.AppInteractivitySummary'
_APP_ADD = 'Microsoft.Windows.Inventory.Core.InventoryApplicationAdd'
_APP_REMOVE = 'Microsoft.Windows.Inventory.Core.InventoryApplicationRemove'
_PNP_ADD = 'Microsoft.Windows.Inventory.Core.InventoryDevicePnpAdd'
_PNP_REMOVE = 'Microsoft.Windows.Inventory.Core.InventoryDevicePnpRemove'


def _when(day, hour, minute, second=0, micro=0):
    return datetime.datetime(2024, 3, day, hour, minute, second, micro, tzinfo=_UTC)


def _filetime(moment):
    delta = moment - datetime.datetime(1601, 1, 1, tzinfo=_UTC)
    return (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10


def _payload(name, data):
    return json.dumps({'ver': '4.0', 'name': name, 'time': '2024-03-01T00:00:00.0000000Z', 'iKey': 'o:test',
                       'ext': {}, 'data': data}, separators=(',', ':'))


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.path = self.root / _FOLDER / 'EventTranscript.db'
        self.path.parent.mkdir(parents=True)
        self.writer = None
        self.hashes = {}

    def tearDown(self):
        if self.writer is not None:
            self.writer.close()
        self._tmp.cleanup()

    def _hash(self, name):
        return self.hashes.setdefault(name, 1000 + len(self.hashes))

    def _event(self, db, moment, name, data, *, sid=_SID, friendly='Example Binary\x00', producer=1,
               payload=None):
        db.execute('INSERT INTO events_persisted VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (sid, _filetime(moment), payload if payload is not None else _payload(name, data), name,
                    self._hash(name), 140737488355328, 0, 1, 'example.exe', friendly, 42, producer, '', '', ''))

    def _build(self, skip=(), wal_rows=False):
        db = sqlite3.connect(self.path)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA wal_autocheckpoint=0')
        for statement in _SCHEMA:
            if not any(f'TABLE {name} (' in statement for name in skip):
                db.execute(statement)
        with db:
            if 'provider_groups' not in skip:
                db.execute('INSERT INTO provider_groups VALUES (1, ?)', (_GROUP,))
            if 'producers' not in skip:
                db.executemany('INSERT INTO producers VALUES (?, ?)', [(1, 'Windows'), (2, 'Microsoft Edge')])
            if 'tag_descriptions' not in skip:
                db.executemany('INSERT INTO tag_descriptions VALUES (?, ?, ?, ?)', [
                    (1, 'en-US', 'Browsing History', 'text'), (24, 'en-US', 'Product and Service Performance',
                                                               'text')])
            # Inserted out of time order, so the rows must come back sorted by timestamp.
            self._event(db, _when(2, 10, 0), 'Example.Second', {'value': 2})
            self._event(db, _when(1, 9, 30, 15, 123456), 'Example.First', {'value': 1}, sid='',
                        friendly='Plain Name')
            self._event(db, _when(3, 8, 0), _EDGE + 'HJ_NavigateCompleteExtended', {
                'navigationUrl': 'https://example.test/a', 'referUrl': 'https://example.test/',
                'TabId': 7, 'HttpStatusCode': 200, 'CorrelationGuid': 'c1',
                'Timestamp': '2024-03-03T07:59:59.500Z'}, producer=2)
            self._event(db, _when(3, 8, 1), _EDGE + 'HJ_HistoryAddUrlEx', {
                'PageTitle': 'Example Title', 'TabId': 7, 'CorrelationGuid': 'c1',
                'Timestamp': '2024-03-03T08:00:59.000Z'}, producer=2)
            self._event(db, _when(3, 8, 2), _EDGE + 'HJ_TabClosed', {'TabId': 7,
                                                                       'Timestamp': '2024-03-03T08:02:00.000Z'},
                        producer=2)
            self._event(db, _when(3, 8, 3), _EDGE + 'HJ_BeforeNavigateExtended', {}, payload='not json',
                        producer=2)
            self._event(db, _when(4, 12, 0), _SUMMARY, {
                'AppId': 'W:0000aaaa!0000bbbb!example.exe', 'AppVersion': '2024/01/01:00:00:00!1!example.exe',
                'AggregationStartTime': '2024-03-04T11:58:00.1234567Z', 'AggregationDurationMS': 120000,
                'InFocusDurationMS': 60000, 'UserActiveDurationMS': 50000,
                'UserOrDisplayActiveDurationMS': 55000, 'FocusLostCount': 2, 'KeyboardInputSec': 10,
                'MouseInputSec': 20, 'AppSessionId': 'S1'})
            self._event(db, _when(4, 12, 5), _SUMMARY, {'AppId': 'U:Example.App!App',
                                                         'AggregationStartTime': 'not a time'})
            base = {'action': 1, 'objectType': 'InventoryApplication', 'objectInstanceId': '0000abc'}
            self._event(db, _when(5, 1, 0), _APP_ADD, {
                'Name': 'Example App', 'Version': '1.2', 'Publisher': 'Example Publisher',
                'RootDirPath': 'C:\\Program Files\\Example', 'InstallDate': '03/01/2024 10:00:00',
                'Source': 'AddRemoveProgram', 'Type': 'Application', 'PackageFullName': '',
                'ProgramInstanceId': '0000def', 'baseType': 'Ms.Device.DeviceInventoryChange', 'baseData': base})
            self._event(db, _when(5, 2, 0), _APP_REMOVE, {
                'InventoryVersion': '1', 'baseData': dict(base, action=2)})
            self._event(db, _when(5, 3, 0), _PNP_ADD, {
                'Description': 'Example Device', 'Manufacturer': 'Example Maker', 'Model': 'Model 1',
                'Class': 'USB', 'Enumerator': 'USB', 'InstallDate': '03-01-2024',
                'FirstInstallDate': '02-29-2024', 'HWID': [{'Value': 'usb\\vid_0000', 'Order': 0}],
                'baseData': {'objectInstanceId': 'usb\\vid_0000\\1'}})
            self._event(db, _when(5, 4, 0), _PNP_REMOVE, {'baseData': {'objectInstanceId': 'usb\\vid_0000\\1'}})
            if 'event_tags' not in skip:
                db.executemany('INSERT INTO event_tags VALUES (?, ?)', [
                    (self._hash('Example.Second'), 24), (self._hash('Example.Second'), 1),
                    (self._hash('Example.Second'), 9), (self._hash('Example.Second'), 24),
                    (self._hash(_EDGE + 'HJ_NavigateCompleteExtended'), 1), (987654, 1)])
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        if wal_rows:
            # Written after the checkpoint and kept open, so this row exists only in the WAL.
            with db:
                self._event(db, _when(6, 6, 6), 'Example.InWal', {'value': 3})
            self.writer = db
        else:
            db.close()

    def _files(self):
        return [str(p) for p in sorted(self.path.parent.iterdir())]

    def _run(self, processor):
        logs = []
        with mock.patch.object(et, 'logfunc', logs.append):
            result = processor.__wrapped__(FakeContext(self.root, self._files()))
        return result + (logs,)

    def test_every_event_is_listed_in_time_order_with_its_lookups(self):
        self._build(wal_rows=True)
        self.assertTrue(any(p.endswith('-wal') for p in self._files()))
        headers, rows, source, logs = self._run(et.eventTranscriptEvents)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 13)
        self.assertEqual([row[0] for row in rows], sorted(row[0] for row in rows))
        first, second = rows[0], rows[1]
        self.assertEqual(first[:11], (_when(1, 9, 30, 15, 123456), 'Example.First', '', 'Windows',
                                      'example.exe', 'Plain Name', '', 0, 140737488355328, _GROUP, 42))
        self.assertEqual(first[12:], (2, _RELATIVE))
        self.assertEqual(json.loads(first[11])['data'], {'value': 1})
        # Tags in tag ID order, each once; an ID with no description is named as such.
        self.assertEqual(second[1:7], ('Example.Second',
                                       'Browsing History; tag 9 (no description stored); '
                                       'Product and Service Performance',
                                       'Windows', 'example.exe', 'Example Binary', _SID))
        self.assertEqual(rows[-1][1], 'Example.InWal')
        self.assertEqual(rows[2][3], 'Microsoft Edge')
        self.assertEqual(source.splitlines(), [str(self.path)])
        self.assertEqual(logs, [])

    def test_lookup_tables_missing_cost_no_rows(self):
        self._build(skip=('producers', 'provider_groups', 'event_tags', 'tag_descriptions'))
        _headers, rows, _source, logs = self._run(et.eventTranscriptEvents)
        self.assertEqual(len(rows), 12)
        self.assertEqual({(row[2], row[3], row[9]) for row in rows}, {('', '', '')})
        self.assertEqual(logs, [f'Diagnostic Data Events: {_RELATIVE} has no event_tags table; '
                                'categories left blank'])

    def test_edge_rows_need_a_url_or_title_and_bad_payloads_are_logged(self):
        self._build()
        headers, rows, _source, logs = self._run(et.eventTranscriptEdgeHistory)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (_when(3, 8, 0), datetime.datetime(2024, 3, 3, 7, 59, 59, 500000, tzinfo=_UTC),
             'HJ_NavigateCompleteExtended', 'https://example.test/a', 'https://example.test/', '', 7, 200,
             'c1', _SID, _EDGE + 'HJ_NavigateCompleteExtended', 3, _RELATIVE),
            (_when(3, 8, 1), datetime.datetime(2024, 3, 3, 8, 0, 59, tzinfo=_UTC), 'HJ_HistoryAddUrlEx', '',
             '', 'Example Title', 7, '', 'c1', _SID, _EDGE + 'HJ_HistoryAddUrlEx', 4, _RELATIVE),
        ])
        self.assertEqual(len(logs), 1)
        self.assertIn('1 payloads without a JSON data object were skipped (row IDs 6)', logs[0])

    def test_app_interactivity_fields_and_a_start_time_that_is_not_iso(self):
        self._build()
        headers, rows, _source, logs = self._run(et.eventTranscriptAppInteractivity)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0], (
            datetime.datetime(2024, 3, 4, 11, 58, 0, 123456, tzinfo=_UTC), _when(4, 12, 0),
            'W:0000aaaa!0000bbbb!example.exe', '2024/01/01:00:00:00!1!example.exe', 120000, 60000, 50000,
            55000, 2, 10, 20, 'S1', _SUMMARY, _SID, 7, _RELATIVE))
        self.assertEqual(rows[1][:3], ('not a time', _when(4, 12, 5), 'U:Example.App!App'))
        self.assertEqual(rows[1][4:12], ('',) * 8)
        self.assertEqual(logs, [])

    def test_application_inventory_add_and_remove(self):
        self._build()
        headers, rows, _source, logs = self._run(et.eventTranscriptAppInventory)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (_when(5, 1, 0), 'InventoryApplicationAdd', 'Example App', '1.2', 'Example Publisher',
             'C:\\Program Files\\Example', '03/01/2024 10:00:00', 'AddRemoveProgram', 'Application', '',
             '0000def', '0000abc', 9, _RELATIVE),
            (_when(5, 2, 0), 'InventoryApplicationRemove') + ('',) * 9 + ('0000abc', 10, _RELATIVE),
        ])
        self.assertEqual(logs, [])

    def test_device_inventory_lists_are_compact_json(self):
        self._build()
        headers, rows, _source, logs = self._run(et.eventTranscriptDeviceInventory)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows[0][:11], (_when(5, 3, 0), 'InventoryDevicePnpAdd', 'Example Device', '',
                                        'Example Maker', 'Model 1', 'USB', 'USB', '03-01-2024', '02-29-2024',
                                        '[{"Value":"usb\\\\vid_0000","Order":0}]'))
        self.assertEqual(rows[1][1], 'InventoryDevicePnpRemove')
        self.assertEqual(rows[1][-3:], ('usb\\vid_0000\\1', 12, _RELATIVE))
        self.assertEqual(logs, [])

    def test_a_database_without_the_events_table_reports_its_path_and_no_rows(self):
        db = sqlite3.connect(self.path)
        db.execute('CREATE TABLE other (x)')
        db.close()
        _headers, rows, source, logs = self._run(et.eventTranscriptEvents)
        self.assertEqual((rows, source.splitlines()), ([], [str(self.path)]))
        self.assertEqual(logs, [f'Diagnostic Data Events: {_RELATIVE} has no events_persisted table'])

    def test_a_sidecar_alone_or_another_file_name_is_not_read(self):
        (self.path.parent / 'EventTranscript.db-wal').write_bytes(b'\x00' * 32)
        (self.path.parent / 'Other.db').write_bytes(b'')
        _headers, rows, source, logs = self._run(et.eventTranscriptEvents)
        self.assertEqual((rows, source, logs), ([], '', []))


class IsoTest(unittest.TestCase):
    def test_iso_values(self):
        self.assertEqual(et._iso_utc('2024-03-04T11:58:00Z'),  # pylint: disable=protected-access
                         datetime.datetime(2024, 3, 4, 11, 58, tzinfo=_UTC))
        for raw in ('2024-03-04T11:58:00', '2024-03-04T11:58:00.12a4Z', 'x'):
            self.assertEqual(et._iso_utc(raw), raw)  # pylint: disable=protected-access
        self.assertEqual(et._iso_utc(None), '')  # pylint: disable=protected-access
        self.assertEqual(et._iso_utc(5), 5)  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
