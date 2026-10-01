"""Pin the Event Logs Cleared rows in scripts/artifacts/windowsEventLogCleared.py.

The records are built from XML of the shape python-evtx renders for the two events (the layout measured on known
data, with made-up names); the expected rows are written out.
"""
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsEventLogCleared as cleared  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
UD = 'http://manifests.microsoft.com/win/2004/08/windows/eventlog'


def record(event_id, channel, when, record_id, user_id, fields, source='/case/data/Logs/x.evtx',
           provider='Microsoft-Windows-Eventlog', block='LogFileCleared'):
    data = ''.join(f'<{name}>{value}</{name}>' for name, value in fields)
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="{provider}" Guid="{{fc65ddd8-d6ef-4962-83d5-6e5cfe9ce148}}">'
           f'</Provider><EventID Qualifiers="">{event_id}</EventID><Version>1</Version><Level>4</Level>'
           f'<TimeCreated SystemTime="{when}"></TimeCreated><EventRecordID>{record_id}</EventRecordID>'
           f'<Execution ProcessID="2304" ThreadID="1496"></Execution><Channel>{channel}</Channel>'
           f'<Computer>LAB-PC</Computer><Security UserID="{user_id}"></Security></System>'
           f'<UserData><{block} xmlns="{UD}">{data}</{block}></UserData></Event>')
    return EventRecord(ElementTree.fromstring(xml), source)


SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
SECURITY = record('1102', 'Security', '2026-10-01 18:08:58.148073+00:00', '189203', '',
                  [('SubjectUserSid', SID), ('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB-PC'),
                   ('SubjectLogonId', '0x000000000002c927'), ('ClientProcessId', '5832'),
                   ('ClientProcessStartKey', '21673573206729015')])
NO_BACKUP = record('104', 'System', '2026-10-01 18:08:52.038153+00:00', '15363', SID,
                   [('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB-PC'), ('Channel', 'Internet Explorer'),
                    ('BackupPath', ''), ('ClientProcessId', '11476'), ('ClientProcessStartKey', '21673573206729013')])
BACKUP = record('104', 'System', '2026-10-01 18:08:55.085314+00:00', '15364', SID,
                [('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB-PC'),
                 ('Channel', 'Key Management Service'), ('BackupPath', 'C:\\Temp\\kms_backup.evtx'),
                 ('ClientProcessId', '6624'), ('ClientProcessStartKey', '21673573206729014')])


def utc(*parts):
    return datetime.datetime(*parts, tzinfo=datetime.timezone.utc)


SECURITY_ROW = (utc(2026, 10, 1, 18, 8, 58, 148073), '1102', 'Security', 'examiner', 'LAB-PC', SID,
                '0x000000000002c927', '', '5832', 'LAB-PC', '189203')
NO_BACKUP_ROW = (utc(2026, 10, 1, 18, 8, 52, 38153), '104', 'Internet Explorer', 'examiner', 'LAB-PC', SID, '', '',
                 '11476', 'LAB-PC', '15363')
BACKUP_ROW = (utc(2026, 10, 1, 18, 8, 55, 85314), '104', 'Key Management Service', 'examiner', 'LAB-PC', SID, '',
              'C:\\Temp\\kms_backup.evtx', '6624', 'LAB-PC', '15364')


class ClearedRowTest(unittest.TestCase):
    def test_a_security_log_clear_takes_its_own_channel_and_the_sid_field(self):
        self.assertEqual(cleared.cleared_row(SECURITY), SECURITY_ROW)

    def test_another_log_cleared_takes_the_channel_field_and_the_header_user(self):
        self.assertEqual(cleared.cleared_row(NO_BACKUP), NO_BACKUP_ROW)
        self.assertEqual(cleared.cleared_row(BACKUP), BACKUP_ROW)

    def test_a_record_with_only_the_documented_fields(self):
        old = record('1102', 'Security', '2015-10-16 00:39:58.656871+00:00', '1087729', '',
                     [('SubjectUserSid', SID), ('SubjectUserName', 'dadmin'), ('SubjectDomainName', 'CONTOSO'),
                      ('SubjectLogonId', '0x55cd1d')])
        self.assertEqual(cleared.cleared_row(old),
                         (utc(2015, 10, 16, 0, 39, 58, 656871), '1102', 'Security', 'dadmin', 'CONTOSO', SID, '0x55cd1d',
                          '', '', 'LAB-PC', '1087729'))

    def test_the_sid_field_wins_over_the_header_user(self):
        both = record('1102', 'Security', '2026-10-01 18:08:58.148073+00:00', '7', 'S-1-5-18',
                      [('SubjectUserSid', SID), ('SubjectUserName', 'examiner')])
        self.assertEqual(cleared.cleared_row(both)[5], SID)


class ArtifactTest(unittest.TestCase):
    def run_artifact(self, by_file):
        calls = []

        def reader(_context, file_name, label, event_ids=None, provider=None):
            calls.append((file_name, label, event_ids, provider))
            return list(by_file.get(file_name, [])), []
        with mock.patch.object(cleared, 'read_event_records', side_effect=reader):
            return cleared.eventLogsCleared.__wrapped__(object()), calls

    def test_rows_are_in_time_order_across_the_two_logs_and_name_the_logs_read(self):
        other = record('104', 'System', '2026-10-01 18:08:55.085314+00:00', '15364', SID,
                       [('Channel', 'Key Management Service'), ('BackupPath', 'C:\\Temp\\kms_backup.evtx'),
                        ('SubjectUserName', 'examiner'), ('SubjectDomainName', 'LAB-PC'), ('ClientProcessId', '6624')],
                       source='/case/data/Logs/System.evtx')
        first = record('104', 'System', '2026-10-01 18:08:52.038153+00:00', '15363', SID,
                       [('Channel', 'Internet Explorer'), ('BackupPath', ''), ('SubjectUserName', 'examiner'),
                        ('SubjectDomainName', 'LAB-PC'), ('ClientProcessId', '11476')],
                       source='/case/data/Logs/System.evtx')
        security = record('1102', 'Security', '2026-10-01 18:08:53.5+00:00', '9', '',
                          [('SubjectUserSid', SID), ('SubjectUserName', 'examiner')],
                          source='/case/data/Logs/Security.evtx')
        (headers, rows, source), calls = self.run_artifact({'security.evtx': [security], 'system.evtx': [other, first]})
        self.assertEqual([r[2] for r in rows], ['Internet Explorer', 'Security', 'Key Management Service'])
        self.assertEqual(rows[0], NO_BACKUP_ROW)
        self.assertEqual(rows[2], BACKUP_ROW)
        self.assertEqual(source, '/case/data/Logs/System.evtx\n/case/data/Logs/Security.evtx')
        self.assertEqual(headers, (('Event Time (UTC)', 'datetime'), 'Event ID', 'Log Cleared', 'Account Name',
                                   'Account Domain', 'Account SID', 'Logon ID', 'Backup Path', 'Client Process ID',
                                   'Computer', 'Event Record ID'))
        self.assertEqual(calls, [('security.evtx', 'Event Logs Cleared', {'1102'}, 'Microsoft-Windows-Eventlog'),
                                 ('system.evtx', 'Event Logs Cleared', {'104'}, 'Microsoft-Windows-Eventlog')])

    def test_a_record_without_a_time_is_listed_last(self):
        undated = record('104', 'System', '', '3', SID, [('Channel', 'Application')])
        (_headers, rows, _source), _calls = self.run_artifact({'system.evtx': [undated, BACKUP, NO_BACKUP]})
        self.assertEqual([r[10] for r in rows], ['15363', '15364', '3'])
        self.assertEqual(rows[2][0], '')

    def test_no_records_no_rows_and_no_source(self):
        (_headers, rows, source), _calls = self.run_artifact({})
        self.assertEqual((rows, source), ([], ''))


if __name__ == '__main__':
    unittest.main()
