"""Pin how scripts/windows_evtx.py's EventRecord reads each shape of UserData.

The records are XML of the shape python-evtx renders (made-up names and values). The first test is the one
that fails without the reading of an element that holds its value as its own text; the others pin the shapes
that read the same as before it.
"""
import pathlib
import sys
import unittest
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsUpdateOperationalEvents as wuop  # noqa: E402  pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # noqa: E402  pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
UD = 'http://manifests.microsoft.com/win/2004/08/windows/eventlog'


def record(body, provider='P', event_id='25'):
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>2</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>5</EventRecordID><Channel>C</Channel><Computer>PC</Computer>'
           f'<Security UserID="S-1-5-18"></Security></System>{body}</Event>')
    return EventRecord(ElementTree.fromstring(xml))


def read(record_):
    return record_.user_data_name, record_.fields, record_.values


class LeafElementTest(unittest.TestCase):
    def test_an_element_holding_its_value_as_its_text_is_a_field_of_its_own_name(self):
        r = record(f'<UserData><errorCode xmlns="{UD}">0x00000001</errorCode></UserData>')
        self.assertEqual(read(r), ('errorCode', {'errorCode': '0x00000001'}, ['0x00000001']))
        self.assertEqual(r.get('errorCode'), '0x00000001')

    def test_the_text_is_kept_as_stored_and_get_strips_it(self):
        r = record(f'<UserData><errorCode xmlns="{UD}"> 7 </errorCode></UserData>')
        self.assertEqual((r.fields, r.get('errorCode')), ({'errorCode': ' 7 '}, '7'))

    def test_an_attribute_on_the_element_does_not_change_its_value(self):
        r = record(f'<UserData><Value xmlns="{UD}" Kind="k">v</Value></UserData>')
        self.assertEqual(read(r), ('Value', {'Value': 'v'}, ['v']))

    def test_an_empty_element_is_no_field_as_before(self):
        self.assertEqual(read(record(f'<UserData><Marker xmlns="{UD}"></Marker></UserData>')), ('Marker', {}, []))
        self.assertEqual(read(record(f'<UserData><Marker xmlns="{UD}"/></UserData>')), ('Marker', {}, []))

    def test_the_error_code_column_of_windows_update_operational_events(self):
        r = record(f'<UserData><errorCode xmlns="{UD}">0x00000001</errorCode></UserData>',
                   provider='Microsoft-Windows-WindowsUpdateClient')
        self.assertEqual(wuop.update_row(r)[3:10], ('', '', '', '', '', '0x00000001', ''))


class ShapesReadAsBeforeTest(unittest.TestCase):
    def test_elements_inside_the_element_are_the_fields(self):
        r = record(f'<UserData><EventXML xmlns="{UD}"><A>1</A><B>2</B><C></C></EventXML></UserData>')
        self.assertEqual(read(r), ('EventXML', {'A': '1', 'B': '2', 'C': ''}, ['1', '2', '']))

    def test_an_element_holding_elements_reads_as_its_own_text_only(self):
        r = record(f'<UserData><EventXML xmlns="{UD}"><A><X>1</X><Y>2</Y></A><B>3</B></EventXML></UserData>')
        self.assertEqual(read(r), ('EventXML', {'A': '', 'B': '3'}, ['', '3']))

    def test_a_repeated_name_keeps_the_last_value_and_every_value_in_order(self):
        r = record(f'<UserData><EventXML xmlns="{UD}"><A>1</A><A>2</A></EventXML></UserData>')
        self.assertEqual(read(r), ('EventXML', {'A': '2'}, ['1', '2']))

    def test_attributes_are_not_read(self):
        r = record(f'<UserData><EventXML xmlns="{UD}" Top="t"><A Kind="k">1</A></EventXML></UserData>')
        self.assertEqual(read(r), ('EventXML', {'A': '1'}, ['1']))

    def test_only_the_first_element_of_user_data_is_read(self):
        r = record(f'<UserData><First xmlns="{UD}"><A>1</A></First><Second xmlns="{UD}">2</Second></UserData>')
        self.assertEqual(read(r), ('First', {'A': '1'}, ['1']))

    def test_empty_user_data_has_no_fields(self):
        self.assertEqual(read(record('<UserData></UserData>')), ('', {}, []))

    def test_event_data_is_read_as_before(self):
        r = record('<EventData><Data Name="A">1</Data><Data>2</Data><Binary>00</Binary></EventData>')
        self.assertEqual(read(r), ('', {'A': '1'}, ['1', '2']))


if __name__ == '__main__':
    unittest.main()
