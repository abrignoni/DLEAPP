"""Pin how log_records reads the chunks a dirty event log's header does not count."""
import inspect
import pathlib
import re
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import windows_evtx
# pylint: enable=wrong-import-position


class FakeRecord:
    def __init__(self, number):
        self.number = number

    def record_num(self):
        return self.number

    def xml(self):
        return ('<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event"><System>'
                f'<Provider Name="P"/><EventID>7</EventID><EventRecordID>{self.number}</EventRecordID>'
                '</System></Event>')


class FakeChunk:
    """A chunk holding records with the given numbers."""

    def __init__(self, numbers, magic=True, header_ok=True, data_ok=True, fail_at=None):
        self.numbers = numbers
        self.magic = magic
        self.header_ok = header_ok
        self.data_ok = data_ok
        self.fail_at = fail_at

    def check_magic(self):
        return self.magic

    def header_checksum(self):
        return 11

    def calculate_header_checksum(self):
        return 11 if self.header_ok else 12

    def data_checksum(self):
        return 21

    def calculate_data_checksum(self):
        return 21 if self.data_ok else 22

    def records(self):
        for index, number in enumerate(self.numbers):
            if index == self.fail_at:
                raise ValueError('record does not parse')
            yield FakeRecord(number)


class FakeHeader:
    def __init__(self, chunks, counted, dirty):
        self._chunks = chunks
        self.counted = counted
        self.dirty = dirty

    def chunk_count(self):
        return self.counted

    def is_dirty(self):
        return self.dirty

    def chunks(self, include_inactive=False):
        return iter(self._chunks if include_inactive else self._chunks[:self.counted])


class FakeLog:
    def __init__(self, chunks, counted, dirty):
        self.header = FakeHeader(chunks, counted, dirty)

    def get_file_header(self):
        return self.header


def read(chunks, counted, dirty):
    """The record numbers log_records yields, and the run log lines it writes."""
    lines = []
    with mock.patch.object(windows_evtx, 'logfunc', lines.append):
        numbers = [record.record_num() for record in
                   windows_evtx.log_records(FakeLog(chunks, counted, dirty), 'Label', 'vol/System.evtx')]
    return numbers, lines


class LogRecordsTest(unittest.TestCase):
    def test_a_dirty_log_is_read_past_the_counted_chunks(self):
        numbers, lines = read([FakeChunk([1, 2]), FakeChunk([3, 4]), FakeChunk([5, 6])], 2, True)
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6])
        self.assertEqual(lines, ['Label: vol/System.evtx is marked dirty; 2 record(s) were read '
                                 'from 1 chunk(s) after the 2 its header counts'])

    def test_a_log_not_marked_dirty_is_read_as_python_evtx_reads_it(self):
        numbers, lines = read([FakeChunk([1, 2]), FakeChunk([3, 4]), FakeChunk([5, 6])], 2, False)
        self.assertEqual(numbers, [1, 2, 3, 4])
        self.assertEqual(lines, [])

    def test_the_counted_chunks_are_read_without_the_checks_later_chunks_get(self):
        numbers, _lines = read([FakeChunk([1], magic=False, header_ok=False), FakeChunk([2])], 2, True)
        self.assertEqual(numbers, [1, 2])

    def test_a_later_chunk_without_the_signature_or_a_matching_checksum_is_not_read(self):
        chunks = [FakeChunk([1]), FakeChunk([2], magic=False), FakeChunk([3], header_ok=False),
                  FakeChunk([4], data_ok=False), FakeChunk([5])]
        numbers, lines = read(chunks, 1, True)
        self.assertEqual(numbers, [1, 5])
        self.assertEqual(lines, ['Label: vol/System.evtx is marked dirty; 1 record(s) were read '
                                 'from 1 chunk(s) after the 1 its header counts, and 2 chunk(s) '
                                 'after them failed their checksums and were not read'])

    def test_a_record_number_already_read_is_not_read_again(self):
        numbers, lines = read([FakeChunk([1, 2]), FakeChunk([2, 3]), FakeChunk([3, 4])], 1, True)
        self.assertEqual(numbers, [1, 2, 3, 4])
        self.assertIn('2 record(s) were read from 2 chunk(s)', lines[0])

    def test_a_later_chunk_that_stops_parsing_keeps_what_it_read_and_the_next_chunk_is_read(self):
        numbers, lines = read([FakeChunk([1]), FakeChunk([2, 3, 4], fail_at=2), FakeChunk([5])], 1, True)
        self.assertEqual(numbers, [1, 2, 3, 5])
        self.assertTrue(lines[0].endswith('; 1 of those chunk(s) stopped parsing part way through'))

    def test_a_dirty_log_with_nothing_after_the_counted_chunks_writes_no_line(self):
        numbers, lines = read([FakeChunk([1]), FakeChunk([], magic=False)], 1, True)
        self.assertEqual(numbers, [1])
        self.assertEqual(lines, [])


class FakeEvtxModule:
    """Stands in for python-evtx's Evtx module: Evtx(path) opens the given fake log."""

    def __init__(self, log):
        self.log = log

    def Evtx(self, _path):  # pylint: disable=invalid-name
        log = self.log

        class _Open:
            def __enter__(self):
                return log

            def __exit__(self, *_exc):
                return False
        return _Open()


class FakeContext:
    @staticmethod
    def get_files_found():
        return ['/case/data/vol/Windows/System32/winevt/Logs/System.evtx']

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1]


class ReadEventRecordsTest(unittest.TestCase):
    def test_the_shared_reader_returns_the_records_a_dirty_header_does_not_count(self):
        log = FakeLog([FakeChunk([1, 2]), FakeChunk([3])], 1, True)
        lines = []
        with mock.patch.object(windows_evtx, 'evtx', FakeEvtxModule(log)), \
                mock.patch.object(windows_evtx, 'logfunc', lines.append):
            records, sources = windows_evtx.read_event_records(FakeContext(), 'system.evtx', 'Label')
        self.assertEqual([r.record_id for r in records], ['1', '2', '3'])
        self.assertEqual(len(sources), 1)
        self.assertIn('1 record(s) were read from 1 chunk(s) after the 1 its header counts', lines[0])


class NoDirectReadsTest(unittest.TestCase):
    def test_no_module_reads_a_log_with_python_evtx_records(self):
        offenders = []
        for path in sorted((REPO_ROOT / 'scripts').rglob('*.py')):
            if path.name == 'windows_evtx.py':
                continue
            text = path.read_text(encoding='utf-8', errors='replace')
            if 'Evtx' in text and re.search(r'\blog\.records\(\)|\.Evtx\([^)]*\)\.records\(\)', text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(offenders, [])


@unittest.skipUnless(windows_evtx.evtx is not None, 'python-evtx is not installed')
class PythonEvtxInterfaceTest(unittest.TestCase):
    def test_python_evtx_can_list_the_chunks_its_header_does_not_count(self):
        # chunk_count, header_checksum, data_checksum and record_num are fields python-evtx
        # declares on each instance, so they are checked on instances built over zeroed bytes.
        header = windows_evtx.evtx.FileHeader(bytearray(0x1000), 0)
        self.assertIn('include_inactive', inspect.signature(header.chunks).parameters)
        for name in ('chunk_count', 'is_dirty'):
            self.assertTrue(callable(getattr(header, name)))
        chunk = windows_evtx.evtx.ChunkHeader(bytearray(0x10000), 0)
        for name in ('check_magic', 'header_checksum', 'calculate_header_checksum', 'data_checksum',
                     'calculate_data_checksum', 'records'):
            self.assertTrue(callable(getattr(chunk, name)))
        self.assertTrue(callable(windows_evtx.evtx.Record(bytearray(0x100), 0, chunk).record_num))


if __name__ == '__main__':
    unittest.main()
