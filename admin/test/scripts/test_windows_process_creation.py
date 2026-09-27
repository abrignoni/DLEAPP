"""Pin the rows of the Windows Process Creation artifact."""
import datetime
import fnmatch
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree
from xml.sax.saxutils import escape

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsProcessCreation as pc
from scripts.windows_evtx import EventRecord
# pylint: enable=wrong-import-position

_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
_UTC = datetime.timezone.utc


def volume_files(volume):
    return (f'/case/data/{volume}/Windows/System32/winevt/Logs/Security.evtx',
            f'/case/data/{volume}/Windows/System32/en-US/msobjs.dll.mui')


_LOG, _MUI = volume_files('p3')


def event_4688(version='2', source=_LOG, **overrides):
    """A 4688 record like python-evtx renders one; version 0 and 1 carry fewer fields."""
    fields = {'SubjectUserSid': 'S-1-5-21-1-2-3-1001', 'SubjectUserName': 'examiner',
              'SubjectDomainName': 'HOST', 'SubjectLogonId': '0x3e7', 'NewProcessId': '0x1f4',
              'NewProcessName': 'C:\\Windows\\System32\\cmd.exe', 'TokenElevationType': '%%1937',
              'ProcessId': '0x10', 'CommandLine': 'cmd /c whoami', 'TargetUserSid': 'S-1-0-0',
              'TargetUserName': '-', 'TargetDomainName': '-', 'TargetLogonId': '0x0',
              'ParentProcessName': 'C:\\Windows\\explorer.exe', 'MandatoryLabel': 'S-1-16-12288'}
    if version == '0':
        fields = {name: fields[name] for name in ('SubjectUserSid', 'SubjectUserName', 'SubjectDomainName',
                                                  'SubjectLogonId', 'NewProcessId', 'NewProcessName',
                                                  'TokenElevationType', 'ProcessId')}
    fields.update(overrides)
    items = ''.join(f'<Data Name="{name}">{escape(value)}</Data>' for name, value in fields.items())
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="{pc._SECURITY}"/>'  # pylint: disable=protected-access
           f'<EventID>4688</EventID><Version>{version}</Version>'
           '<TimeCreated SystemTime="2022-11-23 03:57:03.413883+00:00"/>'
           '<EventRecordID>41</EventRecordID><Execution ProcessID="4" ThreadID="2"/>'
           f'<Computer>HOST</Computer></System><EventData>{items}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


class FakeContext:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1]


class ProcessRowTest(unittest.TestCase):
    def test_a_version_2_event_gives_every_field_with_the_ids_in_decimal(self):
        row = pc.process_row(event_4688(), 'Elevation text')
        self.assertEqual(row, (datetime.datetime(2022, 11, 23, 3, 57, 3, 413883, tzinfo=_UTC),
                               'C:\\Windows\\System32\\cmd.exe', '500', 'cmd /c whoami',
                               'C:\\Windows\\explorer.exe', '16', 'examiner', 'HOST',
                               'S-1-5-21-1-2-3-1001', '0x3e7', '-', '-', 'S-1-0-0', '0x0',
                               'Elevation text', 'S-1-16-12288', 'HOST'))

    def test_a_version_0_event_leaves_the_later_fields_blank(self):
        row = pc.process_row(event_4688(version='0'), '%%1937')
        self.assertEqual(row[3:6], ('', '', '16'))
        self.assertEqual(row[10:], ('', '', '', '', '%%1937', '', 'HOST'))

    def test_an_id_that_is_not_hexadecimal_is_kept_as_stored(self):
        self.assertEqual(pc._decimal('1234'), '1234')  # pylint: disable=protected-access
        self.assertEqual(pc._decimal('0xZZ'), '0xZZ')  # pylint: disable=protected-access


class ParameterTextTest(unittest.TestCase):
    def text(self, value, files, table):
        context = FakeContext(files)
        with mock.patch.object(pc.windows_messages, 'read_message_table', return_value=table), \
                mock.patch('os.path.isdir', return_value=False):
            parameters = pc._ParameterText(context)  # pylint: disable=protected-access
            return parameters, parameters.text(event_4688(), value)

    def test_a_reference_is_given_its_text_from_the_mui_on_the_logs_volume(self):
        parameters, text = self.text('%%1937', [_LOG, _MUI], {1937: 'TokenElevationTypeFull (2)\r\n'})
        self.assertEqual(text, 'TokenElevationTypeFull (2) (%%1937)')
        self.assertEqual(parameters.files_used(), [_MUI])

    def test_a_mui_on_another_volume_is_not_used(self):
        _log, mui = volume_files('p4')
        parameters, text = self.text('%%1937', [_LOG, mui], {1937: 'TokenElevationTypeFull (2)'})
        self.assertEqual((text, parameters.kept, parameters.files_used()), ('%%1937', 1, []))

    def test_a_reference_the_table_lacks_is_kept_as_stored(self):
        parameters, text = self.text('%%1938', [_LOG, _MUI], {1937: 'TokenElevationTypeFull (2)'})
        self.assertEqual((text, parameters.kept, parameters.files_used()), ('%%1938', 1, []))

    def test_a_mui_for_another_language_is_not_used(self):
        german = _MUI.replace('/en-US/', '/de-DE/')
        parameters, text = self.text('%%1937', [_LOG, german], {1937: 'TokenElevationTypeFull (2)'})
        self.assertEqual((text, parameters.kept, parameters.files_used()), ('%%1937', 1, []))

    def test_a_value_that_is_not_a_reference_is_shown_as_stored(self):
        parameters, text = self.text('Full', [_LOG, _MUI], {1937: 'TokenElevationTypeFull (2)'})
        self.assertEqual((text, parameters.kept, parameters.files_used()), ('Full', 0, []))


class ProcessorTest(unittest.TestCase):
    """The processor asks for its own log, provider and event, and cites what it read."""

    def run_processor(self, records, files):
        calls = []

        def fake_read(_context, file_name, _label, event_ids=None, provider=None):
            calls.append((file_name, frozenset(event_ids), provider))
            return records, sorted({record.source for record in records})

        with mock.patch.object(pc, 'read_event_records', side_effect=fake_read), \
                mock.patch.object(pc, 'logfunc'), \
                mock.patch.object(pc.windows_messages, 'read_message_table',
                                  return_value={1937: 'TokenElevationTypeFull (2)'}), \
                mock.patch('os.path.isdir', return_value=False):
            _headers, rows, source = pc.processCreation.__wrapped__(FakeContext(list(files)))
        return calls, rows, source

    def test_it_reads_4688_of_security_auditing_and_cites_the_log_and_the_mui(self):
        calls, rows, source = self.run_processor([event_4688()], (_LOG, _MUI))
        self.assertEqual(calls, [('security.evtx', frozenset({'4688'}), pc._SECURITY)])  # pylint: disable=protected-access
        self.assertEqual([row[14] for row in rows], ['TokenElevationTypeFull (2) (%%1937)'])
        self.assertEqual(source, '\n'.join([_LOG, _MUI]))

    def test_a_log_is_cited_once_however_many_rows_it_gave(self):
        _calls, rows, source = self.run_processor([event_4688(), event_4688()], (_LOG, _MUI))
        self.assertEqual((len(rows), source), (2, '\n'.join([_LOG, _MUI])))

    def test_each_log_takes_the_mui_on_its_own_volume(self):
        log4, mui4 = volume_files('p4')
        records = [event_4688(), event_4688(source=log4)]
        _calls, rows, source = self.run_processor(records, (_LOG, log4, mui4))
        self.assertEqual([row[14] for row in rows], ['%%1937', 'TokenElevationTypeFull (2) (%%1937)'])
        self.assertEqual(source, '\n'.join([_LOG, log4, mui4]))


class DeclaredPathsTest(unittest.TestCase):
    def matches(self, path):
        return any(fnmatch.fnmatch(path, pattern) for pattern in pc.__artifacts_v2__['processCreation']['paths'])

    def test_it_reads_the_security_log_and_the_english_msobjs_mui(self):
        self.assertTrue(self.matches('p3/Windows/System32/winevt/Logs/Security.evtx'))
        self.assertTrue(self.matches('p3/Windows/System32/en-US/msobjs.dll.mui'))
        self.assertFalse(self.matches('p3/Windows/System32/winevt/Logs/System.evtx'))
        self.assertFalse(self.matches('p3/Windows/System32/de-DE/msobjs.dll.mui'))


if __name__ == '__main__':
    unittest.main()
