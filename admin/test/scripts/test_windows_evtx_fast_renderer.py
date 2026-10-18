"""Pin that FastRenderer and python-evtx's Record.xml() render the committed fixtures alike.

Every reader in scripts/windows_evtx.py and the artifacts that open a log themselves render
records with FastRenderer. These tests compare it with Record.xml() on every record of every
fixture in admin/test/data/evtx (README.md there), and check that read_event_records keeps the
same records, fields and run log lines as it does with Record.xml().
"""
import gzip
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import windows_evtx
# pylint: enable=wrong-import-position

DATA = REPO_ROOT / 'admin' / 'test' / 'data' / 'evtx'
FIXTURES = sorted(DATA.glob('*.evtx.gz'))


class Unpacked:
    """Every fixture unpacked to its own folder of a temporary staging tree."""

    def __init__(self):
        self.folder = None
        self.paths = []

    def __enter__(self):
        self.folder = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        for fixture in FIXTURES:
            logs = pathlib.Path(self.folder.name, 'data', fixture.name[:-len('.evtx.gz')])
            logs.mkdir(parents=True)
            path = logs / 'Fixture.evtx'
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


def _rendering(render, record):
    try:
        return render(record)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return f'raised {type(exc).__name__}'


def _record_view(record):
    return (record.provider, record.event_id, record.version, record.level, record.time, record.record_id,
            record.computer, record.user_sid, record.process_id, record.channel, record.activity_id,
            record.related_activity_id, record.fields, record.values, record.user_data_name,
            record.processing_error, record.source)


@unittest.skipUnless(windows_evtx.evtx is not None, 'python-evtx is not installed')
class FastRendererMatchesRecordXmlTest(unittest.TestCase):
    def test_the_fixtures_are_there(self):
        self.assertEqual(len(FIXTURES), 4)

    def test_every_record_of_every_fixture_renders_alike(self):
        with Unpacked() as unpacked:
            for path in unpacked.paths:
                renderer = windows_evtx.FastRenderer()
                with windows_evtx.evtx.Evtx(path) as log:
                    pairs = [(_rendering(renderer.xml, record), _rendering(lambda r: r.xml(), record))
                             for record in windows_evtx.log_records(log)]
                with self.subTest(fixture=path.split('/data/', 1)[1]):
                    self.assertTrue(pairs)
                    for fast, reference in pairs:
                        self.assertFalse(reference.startswith('raised '))
                        self.assertEqual(fast, reference)

    def test_read_event_records_keeps_what_record_xml_gives(self):
        with Unpacked() as unpacked:
            context = FakeContext(unpacked.paths)
            with mock.patch.object(windows_evtx, 'logfunc') as fast_log:
                fast, fast_sources = windows_evtx.read_event_records(context, 'fixture.evtx', 'Test')
            with mock.patch.object(windows_evtx.FastRenderer, 'xml', lambda _self, record: record.xml()), \
                    mock.patch.object(windows_evtx, 'logfunc') as reference_log:
                reference, reference_sources = windows_evtx.read_event_records(context, 'fixture.evtx', 'Test')
        self.assertEqual(len(fast), 27)
        self.assertEqual([_record_view(r) for r in fast], [_record_view(r) for r in reference])
        self.assertEqual(fast_sources, reference_sources)
        self.assertEqual(fast_log.call_args_list, reference_log.call_args_list)

    def test_read_event_records_renders_with_fast_renderer(self):
        with Unpacked() as unpacked:
            context = FakeContext(unpacked.paths)
            with mock.patch.object(windows_evtx.FastRenderer, 'xml', autospec=True,
                                   side_effect=lambda _self, record: record.xml()) as fast_xml, \
                    mock.patch.object(windows_evtx, 'logfunc'):
                records, _sources = windows_evtx.read_event_records(context, 'fixture.evtx', 'Test')
        self.assertEqual(fast_xml.call_count, len(records))


if __name__ == '__main__':
    unittest.main()
