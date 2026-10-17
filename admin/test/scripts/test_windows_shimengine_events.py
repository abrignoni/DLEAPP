"""Pin the rows of the Kernel-ShimEngine device flags (4) and driver shims (3) artifacts."""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree
from xml.sax.saxutils import escape

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsShimEngineEvents as shim
from scripts.windows_evtx import EventRecord
# pylint: enable=wrong-import-position

_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
_PROVIDER = 'Microsoft-Windows-Kernel-ShimEngine'


def event(event_id, fields, provider=_PROVIDER, record_id='7'):
    """An EventRecord like python-evtx renders one, with synthetic values."""
    items = ''.join(f'<Data Name="{name}">{escape(value)}</Data>' for name, value in fields.items())
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="{provider}"/>'
           f'<EventID>{event_id}</EventID><Version>1</Version>'
           '<TimeCreated SystemTime="2024-01-02 03:04:05.123456+00:00"/>'
           f'<EventRecordID>{record_id}</EventRecordID><Computer>HOST</Computer>'
           f'<Security UserID="S-1-5-18"/></System><EventData>{items}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), '/case/data/vol/log.evtx')


DEVICE = {'DeviceName': 'USBSTOR:USB\\VID_1234&PID_ABCD', 'DeviceClass': 'USBSTOR',
          'FlagSource': '1', 'Flags': '2048'}
DRIVER = {'DriverName': 'example.sys', 'ShimSource': '0', 'ShimCount': '1',
          'AppliedGuids': '{00000000-1111-2222-3333-444444444444}'}
WHEN = datetime.datetime(2024, 1, 2, 3, 4, 5, 123456, tzinfo=datetime.timezone.utc)


class Context:
    """The two calls the artifacts make on the run context."""

    @staticmethod
    def get_files_found():
        return []

    @staticmethod
    def get_relative_path(path):
        return path


class RowTest(unittest.TestCase):
    def test_device_flags_row_follows_the_manifest_field_names(self):
        self.assertEqual(shim.device_flags_row(event('4', DEVICE)),
                         (WHEN, 'USBSTOR:USB\\VID_1234&PID_ABCD', 'USBSTOR', '2048', '1', '7', 'HOST'))

    def test_driver_shim_row_follows_the_manifest_field_names(self):
        self.assertEqual(shim.driver_shim_row(event('3', DRIVER)),
                         (WHEN, 'example.sys', '1', '{00000000-1111-2222-3333-444444444444}', '0', '7',
                          'HOST'))

    def test_a_missing_field_is_blank_not_shifted(self):
        partial = dict(DEVICE)
        del partial['DeviceClass']
        row = shim.device_flags_row(event('4', partial))
        self.assertEqual(len(row), 7)
        self.assertEqual(row[2], '')
        self.assertEqual(row[3], '2048')


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, function, wanted):
        """Call the artifact with read_event_records filtering a mixed set the way it does."""
        mixed = [event('4', DEVICE, record_id='1'), event('3', DRIVER, record_id='2'),
                 event('4', DEVICE, provider='Other-Provider', record_id='3')]

        def fake_read(_context, file_name, _label, event_ids=None, provider=None):
            self.assertEqual(file_name, 'Microsoft-Windows-Kernel-ShimEngine%4Operational.evtx')
            kept = [r for r in mixed if r.event_id in event_ids and r.provider == provider]
            return kept, ['/case/data/vol/log.evtx']

        with mock.patch.object(shim, 'read_event_records', fake_read):
            headers, rows, source = function.__wrapped__(Context)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(source, '/case/data/vol/log.evtx')
        self.assertEqual([row[5] for row in rows], wanted)

    def test_device_flags_reads_only_event_4_of_the_provider(self):
        self.run_artifact(shim.shimEngineDeviceFlags, ['1'])

    def test_driver_shims_reads_only_event_3_of_the_provider(self):
        self.run_artifact(shim.shimEngineDriverShims, ['2'])


if __name__ == '__main__':
    unittest.main()
