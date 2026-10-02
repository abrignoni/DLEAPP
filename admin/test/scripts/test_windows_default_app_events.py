"""Pin the rows in scripts/artifacts/windowsDefaultAppEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up values); the expected rows
are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsDefaultAppEvents as defaults  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-Shell-Core%4AppDefaults.evtx'
SID = 'S-1-5-21-1-2-3-1001'
PLAIN = 'SetDefault: Association=.pdf, ProgId=AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723'
DETAIL = 'SetDefault-Info: Association=.pdf, ProgId=AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723, U=' + SID + \
         ', T=2023:01:02:03:17:29, H=QUJDREVGR0g='


def record(record_id, event_id, fields, user=SID):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Shell-Core" '
           f'Guid="{{30336ed4-e327-447c-9de0-51b652c86108}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="700" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-Shell-Core/AppDefaults</Channel><Computer>LAB-PC</Computer>{security}</System>'
           f'<EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


def info(record_id, text, user=SID):
    return record(record_id, '62443', [('Info', text)], user)


TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class SetDefaultTest(unittest.TestCase):
    def test_a_set_default_text_gives_its_association_and_program_id(self):
        self.assertEqual(defaults.set_default(PLAIN), ('.pdf', 'AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723'))

    def test_a_set_default_info_text_stops_the_program_id_at_the_account(self):
        self.assertEqual(defaults.set_default(DETAIL), ('.pdf', 'AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723'))

    def test_the_program_id_of_an_info_text_runs_to_the_last_account_marker(self):
        text = 'SetDefault-Info: Association=http, ProgId=A, U=x, B, U=' + SID + ', T=1, H=2'
        self.assertEqual(defaults.set_default(text), ('http', 'A, U=x, B'))

    def test_the_program_id_of_a_plain_text_is_everything_after_its_marker(self):
        self.assertEqual(defaults.set_default('SetDefault: Association=http, ProgId=A, U=x, B'), ('http', 'A, U=x, B'))

    def test_the_association_stops_at_the_first_program_marker(self):
        self.assertEqual(defaults.set_default('SetDefault: Association=.a, ProgId=one, ProgId=two'), ('.a', 'one, ProgId=two'))

    def test_an_info_text_with_no_account_marker_keeps_the_whole_program_id(self):
        self.assertEqual(defaults.set_default('SetDefault-Info: Association=.a, ProgId=one two'), ('.a', 'one two'))

    def test_only_the_first_colon_ends_the_head_and_the_values_are_kept_as_written(self):
        self.assertEqual(defaults.set_default('SetDefault: Association=.PDF, ProgId=x: y,'), ('.PDF', 'x: y,'))
        self.assertEqual(defaults.set_default('SetDefault-Info: Association=HTTP, ProgId=,a,, U=u'), ('HTTP', ',a,'))

    def test_an_empty_program_id_and_an_empty_association(self):
        self.assertEqual(defaults.set_default('SetDefault: Association=, ProgId='), ('', ''))
        self.assertEqual(defaults.set_default('SetDefault-Info: Association=.a, ProgId=, U=' + SID), ('.a', ''))

    def test_other_texts_give_nothing(self):
        for text in ('', 'AppDefaults-Logon-UserProfileLoaded', 'SetDefault-Error(1): 0X80070005',
                     'AppDefaults-Logon-UpgradeDefault: current=a, new=b', 'SetDefault: ProgId=a',
                     'SetDefault: Association=.a', 'SetDefault:Association=.a, ProgId=b',
                     'Other: Association=.a, ProgId=b', 'SetDefault: x Association=.a, ProgId=b',
                     'setdefault: Association=.a, ProgId=b', 'SetDefaultX: Association=.a, ProgId=b',
                     'SetDefault-Error(1): Association=.a, ProgId=b', 'SetDefault-Info2: Association=.a, ProgId=b'):
            self.assertEqual(defaults.set_default(text), ('', ''), text)


class RowTest(unittest.TestCase):
    def test_a_set_default_record_has_its_association_and_program_id_and_the_whole_text(self):
        self.assertEqual(defaults.default_app_row(info('7', PLAIN)),
                         (TIME, '62443', 'AppDefault Info: %1', '.pdf', 'AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723', PLAIN, '',
                          SID, '7', 'LAB-PC'))

    def test_a_set_default_info_record_keeps_the_account_time_and_hash_in_info(self):
        row = defaults.default_app_row(info('8', DETAIL))
        self.assertEqual(row[3:7], ('.pdf', 'AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723', DETAIL, ''))

    def test_another_info_text_has_no_association_or_program_id(self):
        row = defaults.default_app_row(info('9', 'AppDefaults-Logon-UserProfileLoaded', user='S-1-5-18'))
        self.assertEqual(row[1:8], ('62443', 'AppDefault Info: %1', '', '', 'AppDefaults-Logon-UserProfileLoaded', '', 'S-1-5-18'))

    def test_a_reset_record_takes_the_two_fields_and_lists_the_others(self):
        fields = [('ProgId', ' AppXabc '), ('ExtOrUriScheme', '.HTM'), ('ShouldToast', 'True\n'), ('Blank', '   '),
                  ('Empty', ''), ('CurrentDefaultProgId', 'html  file')]
        row = defaults.default_app_row(record('10', '62441', fields))
        self.assertEqual(row[1:7], ('62441', 'User choice has been reset to prog id %1 for %2.', '.HTM', 'AppXabc', '',
                                    'ShouldToast: True | CurrentDefaultProgId: html  file'))

    def test_the_fields_win_over_a_set_default_text_in_the_same_record(self):
        row = defaults.default_app_row(record('11', '62444', [('ProgId', 'P'), ('Info', PLAIN)]))
        self.assertEqual(row[2:7], ('Missing Hash -- ProgId: %1 FileExtOrUriScheme: %2', '', 'P', PLAIN, ''))
        row = defaults.default_app_row(record('12', '62440', [('ExtOrUriScheme', 'http'), ('Info', PLAIN), ('UserSid', SID)]))
        self.assertEqual(row[2:7], ('Hash mismatch detected for: %1.', 'http', '', PLAIN, 'UserSid: ' + SID))

    def test_the_fields_decide_whatever_the_event_id(self):
        row = defaults.default_app_row(record('17', '62443', [('ExtOrUriScheme', 'mailto'), ('Info', PLAIN)]))
        self.assertEqual(row[3:6], ('mailto', '', PLAIN))
        text = 'SetDefault: Association=.Txt, ProgId=two  spaces'
        row = defaults.default_app_row(record('18', '62445', [('Info', text)]))
        self.assertEqual(row[2:6], ('Migration Info: %1', '.Txt', 'two  spaces', text))

    def test_an_empty_field_still_wins_over_the_text(self):
        row = defaults.default_app_row(record('13', '62441', [('ProgId', ''), ('ExtOrUriScheme', ''), ('Info', PLAIN)]))
        self.assertEqual(row[3:6], ('', '', PLAIN))

    def test_white_space_at_either_end_of_info_is_removed_before_it_is_read(self):
        row = defaults.default_app_row(info('14', f'\n {PLAIN} ', user=''))
        self.assertEqual(row[3:8], ('.pdf', 'AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723', PLAIN, '', ''))

    def test_an_event_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(defaults.default_app_row(record('15', '62442', []))[2:7],
                         ('Upgraded to prog id %1 from prog id %2 for %3', '', '', '', ''))
        row = defaults.default_app_row(record('16', '9999', [('Extra', 'kept'), ('Info', 'x')]))
        self.assertEqual((row[1], row[2], row[5], row[6]), ('9999', '', 'x', 'Extra: kept'))

    def test_the_table_holds_the_six_events_of_the_app_defaults_channel(self):
        events = defaults._EVENTS  # pylint: disable=protected-access
        self.assertEqual(sorted(events), ['62440', '62441', '62442', '62443', '62444', '62445'])
        self.assertEqual(events['62445'], 'Migration Info: %1')


class ArtifactTest(unittest.TestCase):
    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [info('23', PLAIN), info('21', DETAIL), record('22', '62441', [('ProgId', 'P'), ('ExtOrUriScheme', '.x')]),
                   record('24', '9999', [])]
        with mock.patch.object(defaults, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = defaults.defaultAppEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-Shell-Core%4AppDefaults.evtx', 'Default App Events',
                                       provider='Microsoft-Windows-Shell-Core')
        self.assertEqual([(row[8], row[1]) for row in rows], [('23', '62443'), ('21', '62443'), ('22', '62441'), ('24', '9999')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Association', 'Program ID', 'Info',
                                   'Other Fields', 'User SID', 'Record ID', 'Computer'))
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(defaults, 'read_event_records', return_value=([info('1', PLAIN)], [LOG, LOG + '.copy'])):
            self.assertEqual(defaults.defaultAppEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(defaults, 'read_event_records', return_value=([], [])):
            self.assertEqual(defaults.defaultAppEvents.__wrapped__(_Context())[1:], ([], ''))


if __name__ == '__main__':
    unittest.main()
