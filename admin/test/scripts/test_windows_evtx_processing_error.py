"""Pin how scripts/windows_evtx.py's EventRecord reads ProcessingErrorData and RelatedActivityID."""
import pathlib
import sys
import unittest
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.windows_evtx import EventRecord  # noqa: E402  pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'


def record(body, correlation=''):
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="P"></Provider><EventID>219</EventID><Version>0</Version>'
           f'<Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00"></TimeCreated>'
           f'<EventRecordID>5</EventRecordID>{correlation}<Channel>C</Channel><Computer>PC</Computer>'
           f'<Security UserID="S-1-5-18"></Security></System>{body}</Event>')
    return EventRecord(ElementTree.fromstring(xml))


class ProcessingErrorDataTest(unittest.TestCase):
    def test_the_three_items_become_fields_and_not_values(self):
        r = record('<ProcessingErrorData><ErrorCode>15005</ErrorCode><DataItemName>PsmFlags</DataItemName>'
                   '<EventPayload>QUJD</EventPayload></ProcessingErrorData>')
        self.assertEqual(r.fields, {'ProcessingErrorData.ErrorCode': '15005', 'ProcessingErrorData.DataItemName': 'PsmFlags',
                                    'ProcessingErrorData.EventPayload': 'QUJD'})
        self.assertEqual(list(r.fields), ['ProcessingErrorData.ErrorCode', 'ProcessingErrorData.DataItemName',
                                          'ProcessingErrorData.EventPayload'])
        self.assertEqual(r.processing_error, {'ErrorCode': '15005', 'DataItemName': 'PsmFlags', 'EventPayload': 'QUJD'})
        self.assertEqual(r.values, [])
        self.assertEqual(r.get('ProcessingErrorData.DataItemName'), 'PsmFlags')

    def test_an_empty_payload_is_kept_as_an_empty_field(self):
        r = record('<ProcessingErrorData><ErrorCode>15005</ErrorCode><DataItemName>Parameter0</DataItemName>'
                   '<EventPayload></EventPayload></ProcessingErrorData>')
        self.assertEqual(r.fields['ProcessingErrorData.EventPayload'], '')

    def test_a_record_with_event_data_is_read_as_before(self):
        r = record('<EventData><Data Name="A">1</Data><Data Name="B">2</Data></EventData>')
        self.assertEqual((r.fields, r.values, r.processing_error), ({'A': '1', 'B': '2'}, ['1', '2'], {}))


class RelatedActivityIdTest(unittest.TestCase):
    def test_both_correlation_ids_are_read(self):
        r = record('<EventData></EventData>', '<Correlation ActivityID="{A}" RelatedActivityID="{B}"></Correlation>')
        self.assertEqual((r.activity_id, r.related_activity_id), ('{A}', '{B}'))

    def test_absent_ids_are_blank(self):
        self.assertEqual(record('<EventData></EventData>', '<Correlation ActivityID="{A}"></Correlation>').related_activity_id, '')
        self.assertEqual(record('<EventData></EventData>').related_activity_id, '')


if __name__ == '__main__':
    unittest.main()
