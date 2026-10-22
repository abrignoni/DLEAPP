"""Pin the TeamViewer readers in scripts/artifacts/teamViewer.py.

The connection list lines are written in the layouts plaso's TeamViewer parser reads
(plaso/parsers/text_plugins/teamviewer.py at commit f951fc6cda): seven fields for
Connections_incoming.txt and six for Connections.txt. The log lines are written in the
layout that parser reads, with the messages shown in TeamViewer's "Log file reading -
Incoming connection" knowledge base article. Every value is invented. The expected
values are written out, never read back from the code.
"""
import fnmatch
import os
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import teamViewer as tv  # pylint: disable=wrong-import-position

INCOMING = ('123456789\tLAB-PC one\t02-03-2025 10:11:12\t02-03-2025 10:20:00\ttester\t'
            'RemoteControl\t{00000000-1111-2222-3333-444444444444}\t')
OUTGOING_PADDED = ('987654321                     03-03-2025 08:00:01'
                   '             03-03-2025 08:05:09             tester'
                   '                  FileTransfer                {aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}')
OUTGOING_TABS = '987654321\t04-03-2025 09:00:00\t04-03-2025 09:30:00\ttester\tRemoteControl\t{guid}'


def log_line(time, message, tag='S0'):
    return f'{time}  1111       2222 {tag}   {message}'


HEADER = [
    log_line('2025/03/02 10:00:00.010', ''),
    'Start:              2025/03/02 10:00:00.005 (UTC+1:00)',
    'Version:            15.99.1 (64-bit)',
    'Version short hash: 0123abc',
    'ID:                 0',
    'Loglevel:           Info',
]

LOG = [
    log_line('2025/03/02 10:00:00.001', 'Logger started.', tag='0'),
    *HEADER,
    log_line('2025/03/02 10:11:10.100',
             'CommandHandlerRouting[2]::CreatePassiveSession(): incoming session via '
             'xx-yyy-zzz-r001.router.example, protocol Tcp'),
    log_line('2025/03/02 10:11:10.200', 'CLoginServer::CheckIfConnectionIsAllowed()', tag='D1'),
    log_line('2025/03/02 10:11:10.300', 'CLoginServer::AuthenticateServer()', tag='D1'),
    log_line('2025/03/02 10:11:11.000', 'AuthenticationPublicKey_Passive::Verify: Success', tag='D1'),
    log_line('2025/03/02 10:11:11.100',
             ' LookupPublicKeyV2: Manager {~key0000} does not have EasyAccess right, '
             'reject Authentication', tag='D1'),
    log_line('2025/03/02 10:11:11.200',
             'AuthenticationPasswordLogin_Passive::RunAuthenticationMethod: authentication '
             'using dynamic password was denied', tag='D1'),
    log_line('2025/03/02 10:11:11.300',
             'AuthenticationPasswordLogin_Passive::RunAuthenticationMethod: authentication '
             'using fixed password was successful', tag='D1'),
    log_line('2025/03/02 10:11:12.000',
             'CPersistentParticipantManager::AddParticipant: [123456789,-1] type=3 name=LAB-PC'),
    log_line('2025/03/02 10:11:12.100', 'SessionStateParticipants::AddParticipant: pid: [1,2]', tag='G1'),
    'a continuation line without a date',
    log_line('2025/03/02 10:20:00.500',
             'SessionManagerDesktop::SessionTerminate: removing session with TVSessionID = -1', tag='D1'),
    log_line('2025/03/02 10:30:00.000',
             'CLoginServer::CheckIfConnectionIsAllowed: Partner 111111111 (Bob) not whitelisted', tag='D1'),
    log_line('2025/03/02 10:30:00.001', 'CLoginServer::runServer: Connection is not allowed', tag='D1'),
    log_line('2025/03/02 10:30:01.000',
             'SessionManagerDesktop::SessionTerminate: no session with ID=1, aborting logins', tag='D1'),
    log_line('2025/03/02 10:40:00.000', 'Send file C:\\x\\y.txt', tag='G1'),
]


class ConnectionListTest(unittest.TestCase):
    def test_incoming_tab_layout(self):
        records, unread = tv.parse_connection_list('\r\n' + INCOMING + '\r\n')
        self.assertEqual(unread, 0)
        self.assertEqual(records, [{
            'id': '123456789', 'name': 'LAB-PC one', 'start': '02-03-2025 10:11:12',
            'end': '02-03-2025 10:20:00', 'user': 'tester', 'type': 'RemoteControl',
            'guid': '{00000000-1111-2222-3333-444444444444}', 'line': 2}])

    def test_six_field_layouts_padded_and_tabs(self):
        records, unread = tv.parse_connection_list('\n'.join(['', OUTGOING_PADDED, OUTGOING_TABS]))
        self.assertEqual(unread, 0)
        self.assertEqual([(r['id'], r['name'], r['start'], r['end'], r['user'], r['type'],
                           r['guid'], r['line']) for r in records],
                         [('987654321', '', '03-03-2025 08:00:01', '03-03-2025 08:05:09',
                           'tester', 'FileTransfer', '{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}', 2),
                          ('987654321', '', '04-03-2025 09:00:00', '04-03-2025 09:30:00',
                           'tester', 'RemoteControl', '{guid}', 3)])

    def test_empty_display_name_kept_in_tab_layout(self):
        line = '123456789\t\t02-03-2025 10:11:12\t02-03-2025 10:20:00\ttester\tRemoteControl\t{g}'
        records, _ = tv.parse_connection_list(line)
        self.assertEqual((records[0]['name'], records[0]['user']), ('', 'tester'))

    def test_other_lines_counted_not_reported(self):
        text = '\n'.join(['some notes', 'abc\t02-03-2025 10:11:12\t02-03-2025 10:20:00\tu\tT\t{g}',
                          '123\t2025-03-02 10:11:12\t2025-03-02 10:20:00\tu\tT\t{g}', '   ', INCOMING])
        records, unread = tv.parse_connection_list(text)
        self.assertEqual((len(records), unread, records[0]['line']), (1, 3, 5))


class LogTest(unittest.TestCase):
    def test_reported_types_offsets_and_counts(self):
        events, counts = tv.parse_log('\r\n'.join(LOG) + '\r\n')
        self.assertEqual([(e['time'], e['type'], e['line']) for e in events], [
            ('2025/03/02 10:00:00.005', 'Log header Start', 3),
            ('2025/03/02 10:11:10.100', 'Connection attempt', 8),
            ('2025/03/02 10:11:11.000', 'Easy Access check', 11),
            ('2025/03/02 10:11:11.100', 'Easy Access check', 12),
            ('2025/03/02 10:11:11.200', 'Password check', 13),
            ('2025/03/02 10:11:11.300', 'Password check', 14),
            ('2025/03/02 10:11:12.000', 'Participant added', 15),
            ('2025/03/02 10:20:00.500', 'Session terminate', 18),
            ('2025/03/02 10:30:00.000', 'Allowlist check refused', 19),
            ('2025/03/02 10:30:00.001', 'Allowlist check refused', 20),
            ('2025/03/02 10:30:01.000', 'Session terminate', 21),
        ])
        self.assertEqual({(e['offset'], e['version']) for e in events},
                         {('UTC+1:00', '15.99.1 (64-bit)')})
        self.assertEqual(events[1]['message'],
                         'CommandHandlerRouting[2]::CreatePassiveSession(): incoming session via '
                         'xx-yyy-zzz-r001.router.example, protocol Tcp')
        self.assertEqual(events[3]['message'],
                         'LookupPublicKeyV2: Manager {~key0000} does not have EasyAccess right, '
                         'reject Authentication')
        self.assertEqual((counts['lines'], counts['dated'], counts['undated'], counts['headers']),
                         (22, 16, 6, 1))

    def test_lines_before_any_header_have_no_offset(self):
        text = '\n'.join([LOG[0], LOG[7], *HEADER, LOG[17]])
        events, _ = tv.parse_log(text)
        self.assertEqual([(e['type'], e['offset'], e['version']) for e in events], [
            ('Connection attempt', '', ''),
            ('Log header Start', 'UTC+1:00', '15.99.1 (64-bit)'),
            ('Session terminate', 'UTC+1:00', '15.99.1 (64-bit)')])

    def test_later_header_replaces_offset(self):
        second = [line.replace('UTC+1:00', 'UTC+2:00').replace('15.99.1', '15.99.2') for line in HEADER]
        text = '\n'.join([*HEADER, LOG[17], *second, LOG[17]])
        events, _ = tv.parse_log(text)
        self.assertEqual([(e['type'], e['offset'], e['version']) for e in events], [
            ('Log header Start', 'UTC+1:00', '15.99.1 (64-bit)'),
            ('Session terminate', 'UTC+1:00', '15.99.1 (64-bit)'),
            ('Log header Start', 'UTC+2:00', '15.99.2 (64-bit)'),
            ('Session terminate', 'UTC+2:00', '15.99.2 (64-bit)')])

    def test_version_line_outside_a_header_is_ignored(self):
        events, _ = tv.parse_log('\n'.join([HEADER[1], LOG[17], 'Version:            1.0', LOG[17]]))
        self.assertEqual([e['version'] for e in events], ['', '', ''])


class DecodeTest(unittest.TestCase):
    def test_utf8_mark_and_utf16(self):
        self.assertEqual(tv.decode_text(b'\xef\xbb\xbfab'), ('ab', 0))
        self.assertEqual(tv.decode_text('ab'.encode('utf-16')), ('ab', 0))
        self.assertEqual(tv.decode_text(b'a\xe9b'), ('a\ufffdb', 1))


class _Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return os.path.relpath(path, os.path.dirname(os.path.dirname(path)))


class ArtifactTest(unittest.TestCase):
    def test_rows_and_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            program = os.path.join(folder, 'TeamViewer')
            os.mkdir(program)
            incoming = os.path.join(program, 'Connections_incoming.txt')
            outgoing = os.path.join(program, 'Connections.txt')
            log = os.path.join(program, 'TeamViewer15_Logfile.log')
            other = os.path.join(program, 'notes.txt')
            for path, text in ((incoming, '\n' + INCOMING), (outgoing, '\n' + OUTGOING_PADDED),
                               (log, '\n'.join(LOG)), (other, INCOMING)):
                with open(path, 'w', encoding='utf-8', newline='') as handle:
                    handle.write(text)
            headers, rows, source = tv.teamViewerConnections.__wrapped__(
                _Context([incoming, outgoing, other, outgoing]))
            self.assertEqual(len(headers), len(rows[0]))
            self.assertEqual([(r[0], r[2], r[3], r[7], r[8]) for r in rows], [
                ('03-03-2025 08:00:01', '987654321', '', 2, os.path.join('TeamViewer', 'Connections.txt')),
                ('02-03-2025 10:11:12', '123456789', 'LAB-PC one', 2,
                 os.path.join('TeamViewer', 'Connections_incoming.txt'))])
            self.assertEqual(source.split('\n'), [outgoing, incoming])
            headers, rows, source = tv.teamViewerLogEvents.__wrapped__(_Context([log, other]))
            self.assertEqual(len(headers), len(rows[0]))
            self.assertEqual(len(rows), 11)
            self.assertEqual(rows[1][:3], ('2025/03/02 10:11:10.100', 'UTC+1:00', 'Connection attempt'))
            self.assertEqual(source, log)


class PathsTest(unittest.TestCase):
    def test_list_globs(self):
        patterns = tv.__artifacts_v2__['teamViewerConnections']['paths']
        matching = [
            'root/C/Program Files (x86)/TeamViewer/Connections_incoming.txt',
            'root/C/Program Files/TeamViewer/Connections.txt',
            'root/C/Users/tester/AppData/Roaming/TeamViewer/Connections_incoming.txt',
            'root/test_data/teamviewer/connections_incoming.txt',
        ]
        other = ['root/C/Users/tester/AppData/Roaming/OtherApp/Connections.txt',
                 'root/C/Users/tester/Documents/TeamViewerNotes/Connections_incoming.txt',
                 'root/C/Program Files/TeamViewer/Connections_incoming.txt.bak']
        self.assertEqual([sum(fnmatch.fnmatchcase(p, pat) for pat in patterns) for p in matching],
                         [1] * 4)
        self.assertEqual([any(fnmatch.fnmatchcase(p, pat) for pat in patterns) for p in other],
                         [False] * 3)

    def test_log_glob(self):
        (pattern,) = tv.__artifacts_v2__['teamViewerLogEvents']['paths']
        matching = [
            'root/C/Program Files (x86)/TeamViewer/TeamViewer15_Logfile.log',
            'root/C/Program Files/TeamViewer/TeamViewer15_Logfile_OLD.log',
            'root/C/Users/tester/AppData/Roaming/TeamViewer/TeamViewer14_Logfile.log',
            'root/Users/tester/Library/Logs/TeamViewer/TeamViewer15_Logfile.log',
        ]
        other = ['root/C/Program Files/TeamViewer/Connections.txt',
                 'root/C/Program Files/TeamViewer/TV15Install.log']
        self.assertEqual([fnmatch.fnmatchcase(p, pattern) for p in matching], [True] * 4)
        self.assertEqual([fnmatch.fnmatchcase(p, pattern) for p in other], [False] * 2)


if __name__ == '__main__':
    unittest.main()
