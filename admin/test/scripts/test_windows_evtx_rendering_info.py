"""Pin how scripts/windows_evtx.py keeps RenderingInfo and the order of EventData, and the Forwarded Events row.

The XML is written here, with placeholder values, in the shape the Windows Event Collector stores a forwarded
record (RenderingInfoType, https://learn.microsoft.com/en-us/windows/win32/wes/eventschema-renderingtype-complextype).
"""
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_evtx  # noqa: E402  pylint: disable=wrong-import-position
from scripts.artifacts import windowsForwardedEvents  # noqa: E402  pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
FORWARDED = f'''<Event xmlns="{NS}">
  <System>
    <Provider Name="Example-Provider"/>
    <EventID>4624</EventID>
    <Level>0</Level>
    <TimeCreated SystemTime="2020-01-02 03:04:05.678901+00:00"/>
    <EventRecordID>42</EventRecordID>
    <Execution ProcessID="600" ThreadID="700"/>
    <Channel>Security</Channel>
    <Computer>host.example.test</Computer>
    <Security/>
  </System>
  <EventData>
    <Data Name="First">one</Data>
    <Data>unnamed</Data>
    <Data Name="Second">two</Data>
  </EventData>
  <RenderingInfo Culture="en-US">
    <Message>Line one
Line two &amp; more</Message>
    <Level>Information</Level>
    <Opcode>Info</Opcode>
    <Task>Logon</Task>
    <Channel>Security</Channel>
    <Provider>Example provider</Provider>
    <Keywords><Keyword>Audit Success</Keyword><Keyword>Second Keyword</Keyword></Keywords>
  </RenderingInfo>
</Event>'''

PLAIN = f'''<Event xmlns="{NS}">
  <System>
    <Provider Name="Example-Provider"/>
    <EventID>1</EventID>
    <TimeCreated SystemTime="2020-01-02 03:04:05+00:00"/>
    <Computer>host.example.test</Computer>
  </System>
  <EventData><Data Name="Only">value</Data></EventData>
</Event>'''

SPARSE = f'''<Event xmlns="{NS}">
  <System><Provider Name="Example-Provider"/><EventID>2</EventID><Computer>c</Computer></System>
  <RenderingInfo Culture="en-US"><Message>m</Message><Channel/></RenderingInfo>
</Event>'''


def record(xml_text, source='/x/Archive-ForwardedEvents-test.evtx'):
    return windows_evtx.EventRecord(ET.fromstring(xml_text), source)


class RenderingInfoTest(unittest.TestCase):
    def test_rendering_fields(self):
        rendering = record(FORWARDED).rendering
        self.assertEqual(rendering, {
            'Culture': 'en-US', 'Message': 'Line one\nLine two & more', 'Level': 'Information',
            'Opcode': 'Info', 'Task': 'Logon', 'Channel': 'Security', 'Provider': 'Example provider',
            'Keywords': 'Audit Success, Second Keyword'})

    def test_no_rendering_info_is_empty(self):
        self.assertEqual(record(PLAIN).rendering, {})

    def test_absent_and_empty_elements_are_blank(self):
        rendering = record(SPARSE).rendering
        self.assertEqual(rendering['Message'], 'm')
        self.assertEqual(rendering['Channel'], '')
        self.assertEqual(rendering['Task'], '')
        self.assertEqual(rendering['Keywords'], '')

    def test_data_pairs_keep_order_and_unnamed_values(self):
        parsed = record(FORWARDED)
        self.assertEqual(parsed.data_pairs, [('First', 'one'), ('', 'unnamed'), ('Second', 'two')])
        self.assertEqual(parsed.values, ['one', 'unnamed', 'two'])
        self.assertEqual(parsed.fields, {'First': 'one', 'Second': 'two'})


class ForwardedRowTest(unittest.TestCase):
    def test_row(self):
        row = windowsForwardedEvents.forwarded_row(record(FORWARDED))
        self.assertEqual(row[1:], (
            'host.example.test', 'Security', 'Example-Provider', '4624', 'Line one\nLine two & more',
            'Information', 'Logon', 'Info', 'Audit Success, Second Keyword', 'en-US',
            'First: one\nunnamed\nSecond: two', '', '600', '42', 'Archive-ForwardedEvents-test.evtx'))
        self.assertEqual(str(row[0]), '2020-01-02 03:04:05.678901+00:00')

    def test_row_without_rendering_info(self):
        row = windowsForwardedEvents.forwarded_row(record(PLAIN))
        self.assertEqual(row[5:11], ('', '', '', '', '', ''))
        self.assertEqual(row[11], 'Only: value')

    def test_time_order_puts_undated_last(self):
        dated, undated = record(FORWARDED), record(SPARSE)
        self.assertEqual(windowsForwardedEvents._in_time_order([undated, dated]),  # pylint: disable=protected-access
                         [dated, undated])


if __name__ == '__main__':
    unittest.main()
