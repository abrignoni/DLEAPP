"""Pin the rows of windowsAccountManagement and windowsRdpSessions for the events each reads.

The records are XML of the shape python-evtx renders (made-up names and SIDs); field names are those of the
Microsoft-Windows-Security-Auditing and Microsoft-Windows-TerminalServices-LocalSessionManager manifests.
"""
import datetime
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position,protected-access
from scripts.artifacts import windowsAccountManagement as accounts
from scripts.artifacts import windowsRdpSessions as sessions
# pylint: enable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
WHEN = '2023-01-05 20:15:01.100000+00:00'
UTC = datetime.datetime(2023, 1, 5, 20, 15, 1, 100000, tzinfo=datetime.timezone.utc)
SUBJECT = [('SubjectUserSid', 'S-1-5-21-1-2-3-1001'), ('SubjectUserName', 'admin'),
           ('SubjectDomainName', 'LAB'), ('SubjectLogonId', '0x12345')]


def security(event_id, fields):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    return (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-Security-Auditing"></Provider>'
            f'<EventID>{event_id}</EventID><TimeCreated SystemTime="{WHEN}"></TimeCreated>'
            f'<Computer>LAB-PC</Computer></System><EventData>{data}</EventData></Event>')


def local_session(event_id, fields):
    data = ''.join(f'<{name}>{value}</{name}>' for name, value in fields)
    return (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-TerminalServices-LocalSessionManager">'
            f'</Provider><EventID>{event_id}</EventID><TimeCreated SystemTime="{WHEN}"></TimeCreated>'
            f'<Computer>LAB-PC</Computer></System><UserData><EventXML xmlns="Event_NS">{data}</EventXML>'
            f'</UserData></Event>')


class AccountRowTest(unittest.TestCase):
    def test_a_rename_reports_the_new_name_and_the_old_one(self):
        row = accounts._account_row(security('4781', [
            ('OldTargetUserName', 'olduser'), ('NewTargetUserName', 'newuser'), ('TargetDomainName', 'LAB'),
            ('TargetSid', 'S-1-5-21-1-2-3-1002')] + SUBJECT + [('PrivilegeList', '-')]))
        self.assertEqual(row, (UTC, '4781', 'The name of an account was changed', 'newuser', 'olduser', 'LAB', '',
                               'admin', 'LAB-PC'))

    def test_group_and_computer_events_name_the_group_or_computer(self):
        cases = {'4731': 'A security-enabled local group was created',
                 '4735': 'A security-enabled local group was changed',
                 '4737': 'A security-enabled global group was changed',
                 '4742': 'A computer account was changed'}
        for event_id, title in cases.items():
            row = accounts._account_row(security(event_id, [
                ('TargetUserName', 'Target'), ('TargetDomainName', 'LAB'), ('TargetSid', 'S-1-5-21-1-2-3-1100')]
                + SUBJECT + [('PrivilegeList', '-'), ('SamAccountName', '-')]))
            self.assertEqual(row, (UTC, event_id, title, 'Target', '', 'LAB', '', 'admin', 'LAB-PC'))

    def test_a_membership_change_keeps_its_member(self):
        row = accounts._account_row(security('4732', [
            ('MemberName', '-'), ('MemberSid', 'S-1-5-21-1-2-3-1002'), ('TargetUserName', 'Administrators'),
            ('TargetDomainName', 'Builtin'), ('TargetSid', 'S-1-5-32-544')] + SUBJECT))
        self.assertEqual(row[3:7], ('Administrators', '', 'Builtin', 'S-1-5-21-1-2-3-1002'))

    def test_an_event_it_does_not_read(self):
        self.assertIsNone(accounts._account_row(security('4797', SUBJECT)))

    def test_every_title_is_one_event_id(self):
        self.assertEqual(len(set(accounts._ACCOUNT_EVENTS.values())), len(accounts._ACCOUNT_EVENTS))


class SessionRowTest(unittest.TestCase):
    def test_a_disconnect_by_another_session(self):
        row = sessions._session_row(local_session('39', [('TargetSession', '2'), ('Source', '5')]))
        self.assertEqual(row, (UTC, '39', 'Session has been disconnected by session', '', '2', '5', '', '',
                               'LAB-PC'))

    def test_a_disconnect_with_a_reason(self):
        row = sessions._session_row(local_session('40', [('Session', '2'), ('Reason', '11')]))
        self.assertEqual(row, (UTC, '40', 'Session has been disconnected, reason code', '', '2', '', '11', '',
                               'LAB-PC'))

    def test_arbitration_and_a_logon(self):
        begin = sessions._session_row(local_session('41', [('User', 'LAB\\user'), ('SessionID', '2')]))
        logon = sessions._session_row(local_session('21', [('User', 'LAB\\user'), ('SessionID', '2'),
                                                           ('Address', 'LOCAL')]))
        self.assertEqual(begin, (UTC, '41', 'Begin session arbitration', 'LAB\\user', '2', '', '', '', 'LAB-PC'))
        self.assertEqual(logon, (UTC, '21', 'Session logon succeeded', 'LAB\\user', '2', '', '', 'LOCAL',
                                 'LAB-PC'))


if __name__ == '__main__':
    unittest.main()
