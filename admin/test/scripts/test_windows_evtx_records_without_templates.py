"""Pin how scripts/windows_evtx.py reads records whose binary XML holds no template instance.

The fixture is a public CC0 log (admin/test/data/evtx/README.md). The expected values are evtx 0.13.1's reading of it,
with times cut to whole microseconds.
"""
import gzip
import pathlib
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import Evtx.Evtx as evtx  # noqa: E402  pylint: disable=wrong-import-position
import Evtx.Nodes as evtx_nodes  # noqa: E402  pylint: disable=wrong-import-position

from scripts import windows_evtx  # noqa: E402  pylint: disable=wrong-import-position

DATA = REPO_ROOT / 'admin' / 'test' / 'data' / 'evtx'
FIXTURE = DATA / 'defender-1116-1117-no-templates.evtx.gz'
UTC = timezone.utc
EXPECTED = [
    ('171', '1116', datetime(2020, 12, 11, 12, 28, 1, 299004, tzinfo=UTC)),
    ('172', '1116', datetime(2020, 12, 11, 12, 28, 1, 566292, tzinfo=UTC)),
    ('173', '1116', datetime(2020, 12, 11, 12, 28, 1, 651126, tzinfo=UTC)),
    ('175', '1116', datetime(2020, 12, 11, 12, 28, 43, 10296, tzinfo=UTC)),
    ('176', '1117', datetime(2020, 12, 11, 12, 28, 44, 271182, tzinfo=UTC)),
    ('177', '1116', datetime(2020, 12, 11, 12, 28, 44, 317875, tzinfo=UTC)),
]


def read_fixture(fixture=FIXTURE):
    with tempfile.TemporaryDirectory() as folder:
        path = pathlib.Path(folder, 'log.evtx')
        with gzip.open(fixture, 'rb') as packed, open(path, 'wb') as out:
            shutil.copyfileobj(packed, out)
        with evtx.Evtx(str(path)) as log:
            return [(record.record_num(), windows_evtx.EventRecord(ET.fromstring(record.xml())))
                    for record in windows_evtx.log_records(log)]


class RecordsWithoutTemplatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = read_fixture()
        cls.numbers = [number for number, _ in read]
        cls.records = [record for _, record in read]

    def test_every_record_is_read(self):
        # The record headers number them 1 to 6; the EventRecordID each stores runs 171 to 177 without 174.
        self.assertEqual(self.numbers, [1, 2, 3, 4, 5, 6])
        self.assertEqual([(r.record_id, r.event_id, r.time) for r in self.records], EXPECTED)
        self.assertEqual({r.provider for r in self.records}, {'Microsoft-Windows-Windows Defender'})

    def test_event_data(self):
        first = self.records[0]
        self.assertEqual(len(first.values), 42)
        self.assertEqual(first.get('Product Version'), '4.18.2011.6')
        self.assertEqual(first.get('Detection ID'), '{82C6A580-0C4C-48BD-A0AC-6D3DE58FDABB}')
        self.assertEqual(first.get('Threat Name'), 'HackTool:Win64/Mikatz!dha')
        self.assertEqual(first.get('Severity Name'), 'High')

    def test_entity_references_give_their_character_once(self):
        self.assertEqual(self.records[0].get('FWLink'),
                         'https://go.microsoft.com/fwlink/?linkid=37020&name=HackTool:Win64/Mikatz!dha'
                         '&threatid=2147705511&enterprise=0')


class TemplatedRecordTest(unittest.TestCase):
    def test_a_record_read_through_a_template_is_unchanged(self):
        ((number, rec),) = read_fixture(DATA / 'security-4688-template.evtx.gz')
        self.assertEqual((number, rec.record_id, rec.event_id, rec.version, rec.provider),
                         (1, '2774613', '4688', '2', 'Microsoft-Windows-Security-Auditing'))
        self.assertEqual(rec.time, datetime(2020, 7, 11, 21, 9, 3, 249240, tzinfo=UTC))
        self.assertEqual(len(rec.values), 15)
        self.assertEqual((rec.get('NewProcessName'), rec.get('ParentProcessName'), rec.get('MandatoryLabel')),
                         ('C:\\Windows\\System32\\schtasks.exe', 'C:\\Windows\\System32\\cmd.exe', 'S-1-16-8192'))
        self.assertEqual(rec.fields['CommandLine'], 'schtasks  /create /s fs02 /tn tasks_test_hacker2 /tr myapp.exe /sc daily /mo 10')


class EntityReferenceTest(unittest.TestCase):
    @staticmethod
    def reference(name):
        node = SimpleNamespace(string_offset=lambda: 0,
                               _chunk=SimpleNamespace(strings=lambda: {0: SimpleNamespace(string=lambda: name)}))
        return evtx_nodes.EntityReferenceNode.entity_reference(node)

    def test_named_and_numeric_references(self):
        self.assertEqual([self.reference(n) for n in ('amp', 'lt', 'gt', 'quot', 'apos', '#65', '#x42', '#X43')],
                         ['&', '<', '>', '"', "'", 'A', 'B', 'C'])

    def test_unknown_and_malformed_references_stay_as_written(self):
        self.assertEqual([self.reference(n) for n in ('nbsp', '#xZZ', '#', '#x110000', '#' + '9' * 30)],
                         ['&nbsp;', '&#xZZ;', '&#;', '&#x110000;', '&#' + '9' * 30 + ';'])


if __name__ == '__main__':
    unittest.main()
