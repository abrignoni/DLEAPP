"""Pin the Biome stream helpers in scripts/macos_biome.py.

fields() is checked against protobuf messages written out by hand below. stream_records() is
checked with ccl_segb's reader replaced by a stub, so the test can hand it two views of one
stream file that differ: records both views hold must come back once, and records only one
view holds must be kept. The expected values are written out, never read back from the code.
"""
import datetime
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_biome  # pylint: disable=wrong-import-position
from scripts.vendor.ccl_segb.ccl_segb_common import EntryState  # pylint: disable=wrong-import-position

# field 1 varint 150, field 2 fixed64, field 3 "hi", field 4 fixed32, field 3 again
MESSAGE = (b'\x08\x96\x01' + b'\x11' + bytes(range(8)) + b'\x1a\x02hi' + b'\x25\x01\x02\x03\x04'
           + b'\x1a\x01x')


class FieldsTest(unittest.TestCase):
    def test_every_wire_type_reads(self):
        self.assertEqual(macos_biome.fields(MESSAGE), {
            1: [150], 2: [bytes(range(8))], 3: [b'hi', b'x'], 4: [b'\x01\x02\x03\x04']})
        self.assertEqual(macos_biome.first(macos_biome.fields(MESSAGE), 3), b'hi')
        self.assertEqual(macos_biome.text(b'hi'), 'hi')
        self.assertEqual(macos_biome.double(b'\x00\x00\x00\x00\x00\x00\xf0\x3f'), 1.0)

    def test_malformed_messages_raise(self):
        for data in (b'\x08', b'\x1a\x05hi', b'\x00\x01', b'\x0b'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                macos_biome.fields(data)


def _entry(offset, seconds, payload, state=EntryState.Written):
    return SimpleNamespace(state=state, data_start_offset=offset, data=payload,
                           timestamp1=datetime.datetime(2025, 12, 1) + datetime.timedelta(seconds=seconds))


class StreamRecordsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self._tmp.name)
        self.rel = {
            'users': 'Users/someone/Library/Biome/streams/restricted/App.InFocus/local/700000000000001',
            'data': 'System/Volumes/Data/Users/someone/Library/Biome/streams/restricted/App.InFocus/local/700000000000001',
            'remote': 'Users/someone/Library/Biome/streams/restricted/App.InFocus/remote/11111111-2222-3333-4444-555555555555/700000000000002',
            'tomb': 'Users/someone/Library/Biome/streams/restricted/App.InFocus/local/tombstone/700000000000003',
        }
        self.paths = {}
        for name, relative in self.rel.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
            self.paths[name] = str(path)
        self.context = SimpleNamespace(
            get_files_found=lambda: list(self.paths.values()),
            get_relative_path=lambda p: str(pathlib.Path(p).relative_to(root)))
        self.entries = {
            self.paths['users']: [_entry(32, 0, b'A'), _entry(64, 1, b'B'), _entry(96, 2, b'\x00', EntryState.Deleted)],
            self.paths['data']: [_entry(32, 0, b'A'), _entry(64, 1, b'B'), _entry(128, 3, b'C')],
            self.paths['remote']: [_entry(32, 0, b'A')],
            self.paths['tomb']: [_entry(32, 5, b'T')],
        }

    def tearDown(self):
        self._tmp.cleanup()

    def test_views_collapse_per_record_and_tombstones_are_skipped(self):
        with mock.patch.object(macos_biome, 'read_segb_file', side_effect=lambda p: self.entries[p]), \
                mock.patch.object(macos_biome, 'logfunc'):
            records, sources = macos_biome.stream_records(self.context, 'test')
        got = sorted((r.source, r.offset, r.data, r.origin, r.user) for r in records)
        self.assertEqual(got, sorted([
            (self.rel['users'], 32, b'A', 'Local', 'someone'),
            (self.rel['users'], 64, b'B', 'Local', 'someone'),
            (self.rel['data'], 128, b'C', 'Local', 'someone'),
            (self.rel['remote'], 32, b'A', 'Remote (11111111-2222-3333-4444-555555555555)', 'someone'),
        ]))
        self.assertEqual(sorted(sources), sorted([self.paths['users'], self.paths['data'], self.paths['remote']]))
        self.assertTrue(all(r.time.tzinfo is datetime.timezone.utc for r in records))


if __name__ == '__main__':
    unittest.main()
