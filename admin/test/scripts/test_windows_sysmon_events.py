"""Pin the Sysmon artifacts and the streaming event log reader they use.

The two fixtures are public CC0 Sysmon logs (admin/test/data/evtx/README.md). The expected Event IDs and
record header numbers are evtx 0.13.1's reading of them (the Rust evtx crate's Python binding).
"""
import gzip
import pathlib
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import windows_evtx
from scripts.artifacts import windowsSysmonEvents as sysmon
# pylint: enable=wrong-import-position

DATA = REPO_ROOT / 'admin' / 'test' / 'data' / 'evtx'
PSEXEC = DATA / 'sysmon-psexec-11-13-17-18.evtx.gz'
LOADS = DATA / 'sysmon-3-7-10.evtx.gz'
UTC = timezone.utc
# evtx 0.13.1: record header number and Event ID of every record, in file order.
PSEXEC_EVENTS = [(1, '1'), (2, '13'), (3, '11'), (4, '13'), (5, '13'), (6, '17'), (7, '18'), (8, '17'),
                 (9, '17'), (10, '17'), (11, '18'), (12, '18'), (13, '18'), (14, '1'), (15, '22')]
LOADS_EVENTS = [(1, '7'), (2, '7'), (3, '3'), (4, '10'), (5, '3')]
_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'


class Unpacked:
    """A fixture unpacked to a temporary folder as a volume's Sysmon log."""

    def __init__(self, *fixtures):
        self.fixtures = fixtures
        self.folder = None
        self.paths = []

    def __enter__(self):
        self.folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        for index, fixture in enumerate(self.fixtures):
            logs = pathlib.Path(self.folder.name, 'data', f'v{index}', 'Windows', 'System32', 'winevt', 'Logs')
            logs.mkdir(parents=True)
            path = logs / 'Microsoft-Windows-Sysmon%4Operational.evtx'
            with gzip.open(fixture, 'rb') as packed, open(path, 'wb') as out:
                shutil.copyfileobj(packed, out)
            self.paths.append(str(path))
        return self

    def __exit__(self, *_exc):
        self.folder.cleanup()
        return False


class FakeContext:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1]


class Result:
    """Stands in for the ArtifactResult the artifacts stream their rows into."""

    def __init__(self, headers):
        self.headers = headers
        self.rows = []
        self.source = None

    def add_row(self, row):
        self.rows.append(row)

    def set_source_path(self, value):
        self.source = value


class ResultContext(FakeContext):
    @staticmethod
    def create_artifact_result(headers=None):
        return Result(headers)


def rendered(path):
    """(record number, Record.xml() or the exception type, FastRenderer.xml(), event_fields) per record."""
    renderer = windows_evtx.FastRenderer()
    out = []
    with windows_evtx.evtx.Evtx(path) as log:
        for record in windows_evtx.log_records(log):
            try:
                reference = record.xml()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                reference = type(exc).__name__
            out.append((record.record_num(), reference, renderer.xml(record), renderer.event_fields(record)))
    return out


@unittest.skipUnless(windows_evtx.evtx is not None, 'python-evtx is not installed')
class FastRendererTest(unittest.TestCase):
    def test_every_record_renders_as_python_evtx_renders_it(self):
        for fixture, expected in ((PSEXEC, PSEXEC_EVENTS), (LOADS, LOADS_EVENTS)):
            with Unpacked(fixture) as unpacked:
                records = rendered(unpacked.paths[0])
            self.assertEqual(len(records), len(expected))
            for (number, reference, fast, (event_id, provider)), (want_number, want_id) in zip(records, expected):
                self.assertEqual(fast, reference)
                parsed = windows_evtx.EventRecord(ET.fromstring(reference))
                self.assertEqual((number, parsed.event_id, event_id), (want_number, want_id, want_id))
                self.assertEqual((parsed.provider, provider), ('Microsoft-Windows-Sysmon',) * 2)

    def test_the_event_data_comes_from_a_substitution_holding_binary_xml(self):
        # Sysmon's records hold their EventData as a nested binary XML substitution, rendered once per chunk.
        with Unpacked(PSEXEC) as unpacked, windows_evtx.evtx.Evtx(unpacked.paths[0]) as log:
            record = next(iter(windows_evtx.log_records(log)))
            values = record.root().substitutions()
        self.assertTrue(any(isinstance(value, windows_evtx.evtx_nodes.BXmlTypeNode) for value in values))

    def test_a_record_the_fast_path_cannot_render_falls_back_to_python_evtx(self):
        class Record:
            @staticmethod
            def root():
                raise ValueError('no root')

            @staticmethod
            def xml():
                return '<Event/>'
        self.assertEqual(windows_evtx.FastRenderer().xml(Record()), '<Event/>')
        self.assertEqual(windows_evtx.FastRenderer().event_fields(Record()), (None, None))


@unittest.skipUnless(windows_evtx.evtx is not None, 'python-evtx is not installed')
class EventRecordStreamTest(unittest.TestCase):
    def test_only_the_wanted_events_are_yielded_from_every_copy(self):
        lines = []
        with Unpacked(PSEXEC, LOADS) as unpacked, mock.patch.object(windows_evtx, 'logfunc', lines.append):
            stream = windows_evtx.EventRecordStream(FakeContext(unpacked.paths), sysmon._LOG, 'Label',  # pylint: disable=protected-access
                                                    event_ids=('1', '3'), provider='Microsoft-Windows-Sysmon')
            ids = [record.event_id for record in stream]
            self.assertEqual(stream.sources, unpacked.paths)
        self.assertEqual(ids, ['1', '1', '3', '3'])
        self.assertEqual(lines, [
            'Label: 15 records in v0/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx; '
            '2 rendered (the others carry an Event ID or provider this artifact does not read); 0 could not be '
            'rendered by python-evtx and 0 did not parse as XML',
            'Label: 5 records in v1/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%4Operational.evtx; '
            '2 rendered (the others carry an Event ID or provider this artifact does not read); 0 could not be '
            'rendered by python-evtx and 0 did not parse as XML'])

    def test_another_provider_is_not_yielded(self):
        with Unpacked(PSEXEC) as unpacked, mock.patch.object(windows_evtx, 'logfunc'):
            stream = windows_evtx.EventRecordStream(FakeContext(unpacked.paths), sysmon._LOG, 'Label',  # pylint: disable=protected-access
                                                    event_ids=('1',), provider='Another-Provider')
            self.assertEqual(list(stream), [])

    def test_each_artifact_takes_its_own_events(self):
        expected = {'sysmonProcessEvents': ['1', '1'], 'sysmonNetworkConnections': ['3', '3'],
                    'sysmonDnsQueries': ['22'], 'sysmonFileEvents': ['11'],
                    'sysmonRegistryEvents': ['13', '13', '13'], 'sysmonImageLoads': ['7', '7'],
                    'sysmonProcessAccess': ['10'], 'sysmonRawAccessTampering': [],
                    'sysmonPipeEvents': ['17', '18', '17', '17', '17', '18', '18', '18'],
                    'sysmonWmiEvents': [], 'sysmonClipboardChanges': [], 'sysmonServiceEvents': []}
        self.assertEqual(set(expected), set(sysmon.__artifacts_v2__))
        with Unpacked(PSEXEC, LOADS) as unpacked, mock.patch.object(windows_evtx, 'logfunc'):
            for name, ids in expected.items():
                result = getattr(sysmon, name).__wrapped__(ResultContext(unpacked.paths))
                self.assertEqual([row[result.headers.index('Event ID')] for row in result.rows], ids, name)
                self.assertEqual(result.source, '\n'.join(unpacked.paths), name)
                for row in result.rows:
                    self.assertEqual(len(row), len(result.headers), name)


def sysmon_record(event_id, fields, version='5'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields.items())
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="Microsoft-Windows-Sysmon"/>'
           f'<EventID>{event_id}</EventID><Version>{version}</Version>'
           '<TimeCreated SystemTime="2021-12-04 21:19:16.741995+00:00"/>'
           '<EventRecordID>48593</EventRecordID><Computer>HOST</Computer></System>'
           f'<EventData>{data}</EventData></Event>')
    return windows_evtx.EventRecord(ET.fromstring(xml))


class SysmonRowTest(unittest.TestCase):
    def test_a_field_no_column_shows_goes_to_other_fields(self):
        row = sysmon.sysmon_row(sysmon_record('5', {'UtcTime': '2021-12-04 21:19:16.741', 'ProcessId': '4',
                                             'Extra': 'x'}), ('ProcessId', 'Image'))
        self.assertEqual(row, (datetime(2021, 12, 4, 21, 19, 16, 741000, tzinfo=UTC),
                               datetime(2021, 12, 4, 21, 19, 16, 741995, tzinfo=UTC), '5',
                               'Process terminated', '4', '', 'Extra: x', '5', '48593', 'HOST'))

    def test_a_time_that_does_not_parse_is_kept_as_stored_in_other_fields(self):
        row = sysmon.sysmon_row(sysmon_record('1', {'UtcTime': 'not a time'}), ())
        self.assertEqual(row[0], '')
        self.assertEqual(row[4], 'UtcTime: not a time')

    def test_both_spellings_of_a_process_guid_fill_one_column(self):
        fields = ('SourceProcessGuid', 'TargetProcessGuid')
        upper = sysmon.sysmon_row(sysmon_record('10', {'SourceProcessGUID': '{a}', 'TargetProcessGUID': '{b}'}), fields)
        lower = sysmon.sysmon_row(sysmon_record('8', {'SourceProcessGuid': '{a}', 'TargetProcessGuid': '{b}'}), fields)
        self.assertEqual(upper[4:7], ('{a}', '{b}', ''))
        self.assertEqual(lower[4:7], ('{a}', '{b}', ''))

    def test_a_value_is_kept_with_its_spaces(self):
        row = sysmon.sysmon_row(sysmon_record('1', {'CommandLine': ' cmd /c dir '}), ('CommandLine',))
        self.assertEqual(row[4], ' cmd /c dir ')

    def test_an_unknown_event_id_has_no_event_name(self):
        self.assertEqual(sysmon.sysmon_row(sysmon_record('99', {}), ())[3], '')

    def test_the_headers_match_the_row_and_are_unique(self):
        for fields, times in ((sysmon._SERVICE_FIELDS, ('UtcTime',)),  # pylint: disable=protected-access
                              (sysmon._FILE_FIELDS, sysmon._FILE_TIME_FIELDS)):  # pylint: disable=protected-access
            headers = sysmon.headers_for(fields, times)
            names = [h[0] if isinstance(h, tuple) else h for h in headers]
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(len(sysmon.sysmon_row(sysmon_record('4', {}), fields, times)), len(headers))

    def test_sysmon_time(self):
        self.assertEqual(sysmon.sysmon_time('2022-02-08 11:41:18.1'),
                         datetime(2022, 2, 8, 11, 41, 18, 100000, tzinfo=UTC))
        self.assertEqual(sysmon.sysmon_time('2022-02-08 11:41:18'), datetime(2022, 2, 8, 11, 41, 18, tzinfo=UTC))
        self.assertIsNone(sysmon.sysmon_time('2022-02-30 11:41:18.100'))
        self.assertIsNone(sysmon.sysmon_time(''))


if __name__ == '__main__':
    unittest.main()
