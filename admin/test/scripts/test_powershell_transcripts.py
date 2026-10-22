"""Pin the PowerShell transcript reader in scripts/artifacts/windowsPowerShellTranscripts.py.

The input text is written from PowerShell's own strings and code at commit 7962a6ae10:
TranscriptPrologue, MinimalTranscriptPrologue, TranscriptEpilogue and CommandStartTime in
src/System.Management.Automation/resources/InternalHostUserInterfaceStrings.resx (and its
French and Traditional Chinese translations), the header built in LogTranscriptHeader, and
the command lines added in TranscribeCommand, in MshHostUserInterface.cs. Every value is
invented. The expected values are written out, never read back from the code.
"""
import os
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsPowerShellTranscripts as pst  # pylint: disable=wrong-import-position

STARS = '*' * 22

PS7_HEADER = [
    STARS,
    'PowerShell transcript start',
    'Start time: 20250102030405',
    'Username: LAB\\tester',
    'RunAs User: LAB\\tester',
    'Configuration Name: ',
    'Machine: LABPC (Microsoft Windows NT 10.0.22631.0)',
    'Host Application: C:\\Program Files\\PowerShell\\7\\pwsh.dll -NoLogo',
    'Process ID: 4242',
    'PSVersion: 7.4.6',
    'PSEdition: Core',
    'GitCommitId: 7.4.6',
    'OS: Microsoft Windows 10.0.22631',
    'Platform: Win32NT',
    'PSCompatibleVersions: 1.0, 2.0, 3.0, 4.0, 5.0, 5.1, 6.0, 7.0',
    'PSRemotingProtocolVersion: 2.3',
    'SerializationVersion: 1.1.0.1',
    'WSManStackVersion: 3.0',
    STARS,
]
FOOTER = [STARS, 'PowerShell transcript end', 'End time: 20250102031000', STARS]


def command(time, line, *output):
    return [STARS, f'Command start time: {time}', STARS, line, *output]


def text_of(lines):
    return '\r\n'.join(lines) + '\r\n'


class FullSessionTest(unittest.TestCase):
    def test_ps7_header_footer_and_commands(self):
        lines = (PS7_HEADER + ['Transcript started, output file is C:\\t\\x.txt']
                 + command('20250102030500', 'PS C:\\Users\\tester> Get-Date', '',
                           'Thursday, January 2, 2025 3:05:00 AM', '', '')
                 + command('20250102030600', 'PS C:\\Users\\tester> Stop-Transcript')
                 + FOOTER)
        sessions, commands = pst.parse_transcript(text_of(lines))
        self.assertEqual(len(sessions), 1)
        s = sessions[0]
        self.assertEqual((s['start'], s['end']), ('2025-01-02 03:04:05', '2025-01-02 03:10:00'))
        self.assertEqual((s['username'], s['runas'], s['configuration']),
                         ('LAB\\tester', 'LAB\\tester', ''))
        self.assertEqual((s['machine'], s['os_version']),
                         ('LABPC', 'Microsoft Windows NT 10.0.22631.0'))
        self.assertEqual(s['host_application'],
                         'C:\\Program Files\\PowerShell\\7\\pwsh.dll -NoLogo')
        self.assertEqual((s['process_id'], s['ps_version'], s['ps_edition']),
                         ('4242', '7.4.6', 'Core'))
        self.assertEqual((s['header'], s['commands'], s['line']), ('full', 2, 1))
        self.assertEqual([(c['time'], c['command'], c['output'], c['output_lines'], c['line'])
                          for c in commands],
                         [('2025-01-02 03:05:00', 'PS C:\\Users\\tester> Get-Date',
                           '\nThursday, January 2, 2025 3:05:00 AM', 2, 24),
                          ('2025-01-02 03:06:00', 'PS C:\\Users\\tester> Stop-Transcript',
                           '', 0, 32)])
        self.assertEqual({c['session'] for c in commands}, {0})

    def test_header_without_configuration_name(self):
        # The prologue before PowerShell commit 3f274aad9 has no Configuration Name line.
        header = [line for line in PS7_HEADER if not line.startswith('Configuration Name')]
        header[1] = 'Windows PowerShell transcript start'
        sessions, _ = pst.parse_transcript(text_of(header))
        s = sessions[0]
        self.assertEqual((s['username'], s['configuration'], s['machine'], s['process_id']),
                         ('LAB\\tester', '', 'LABPC', '4242'))

    def test_remoting_configuration_name(self):
        header = list(PS7_HEADER)
        header[3] = 'Username: LAB\\remote'
        header[5] = 'Configuration Name: Microsoft.PowerShell'
        s = pst.parse_transcript(text_of(header))[0][0]
        self.assertEqual((s['username'], s['runas'], s['configuration']),
                         ('LAB\\remote', 'LAB\\tester', 'Microsoft.PowerShell'))

    def test_session_without_footer_and_without_invocation_headers(self):
        lines = PS7_HEADER + ['PS C:\\> whoami', 'lab\\tester']
        sessions, commands = pst.parse_transcript(text_of(lines))
        self.assertEqual((sessions[0]['end'], sessions[0]['commands']), ('', 0))
        self.assertEqual(commands, [])


class OtherShapesTest(unittest.TestCase):
    def test_minimal_header(self):
        lines = ([STARS, 'PowerShell transcript start', 'Start time: 20250102030405', STARS]
                 + command('20250102030500', 'PS>dir') + FOOTER)
        sessions, commands = pst.parse_transcript(text_of(lines))
        self.assertEqual(len(sessions), 1)
        s = sessions[0]
        self.assertEqual((s['header'], s['start'], s['end'], s['username'], s['commands']),
                         ('minimal', '2025-01-02 03:04:05', '2025-01-02 03:10:00', '', 1))
        self.assertEqual(commands[0]['command'], 'PS>dir')

    def test_minimal_header_after_a_session_without_footer(self):
        # Only the title tells a minimal header from a footer once a session is open.
        minimal = [STARS, 'PowerShell transcript start', 'Start time: 20250103000000', STARS]
        sessions, _ = pst.parse_transcript(text_of(PS7_HEADER + minimal + FOOTER))
        self.assertEqual([(s['header'], s['start'], s['end']) for s in sessions],
                         [('full', '2025-01-02 03:04:05', ''),
                          ('minimal', '2025-01-03 00:00:00', '2025-01-02 03:10:00')])

    def test_appended_sessions(self):
        lines = PS7_HEADER + FOOTER + PS7_HEADER[:2] + ['Start time: 20250103000000'] \
            + PS7_HEADER[3:] + FOOTER
        sessions, _ = pst.parse_transcript(text_of(lines))
        self.assertEqual([(s['start'], s['end'], s['line']) for s in sessions],
                         [('2025-01-02 03:04:05', '2025-01-02 03:10:00', 1),
                          ('2025-01-03 00:00:00', '2025-01-02 03:10:00', 24)])

    def test_french_labels_with_no_break_space(self):
        lines = [STARS, 'Début de la transcription PowerShell',
                 'Heure de début\u00a0: 20250102030405',
                 'Nom d\u2019utilisateur\u00a0: LAB\\testeur',
                 'Utilisateur RunAs\u00a0: LAB\\testeur', 'Nom de la configuration\u00a0: ',
                 'Ordinateur\u00a0: LABPC (Microsoft Windows NT 10.0.22631.0)',
                 'Application hôte\u00a0: pwsh', 'ID de processus\u00a0: 77',
                 'PSVersion: 7.4.6', STARS]
        lines += command('20250102030500', 'PS>Get-Date')
        lines += [STARS, 'Fin de la transcription PowerShell', 'Heure de fin\u00a0: 20250102031000',
                  STARS]
        sessions, commands = pst.parse_transcript(text_of(lines))
        s = sessions[0]
        self.assertEqual((s['username'], s['machine'], s['host_application'], s['process_id'],
                          s['end']),
                         ('LAB\\testeur', 'LABPC', 'pwsh', '77', '2025-01-02 03:10:00'))
        self.assertEqual(commands[0]['time'], '2025-01-02 03:05:00')

    def test_traditional_chinese_machine_without_space(self):
        lines = [STARS, 'PowerShell 文字記錄開始', '開始時間: 20250102030405',
                 '使用者名稱: LAB\\t', 'RunAs 使用者: LAB\\t', '設定名稱: ',
                 '機器: LABPC(Microsoft Windows NT 10.0.22631.0)', '主應用程式: pwsh',
                 '處理序識別碼: 5', 'PSVersion: 7.4.6', STARS]
        s = pst.parse_transcript(text_of(lines))[0][0]
        self.assertEqual((s['machine'], s['os_version']),
                         ('LABPC', 'Microsoft Windows NT 10.0.22631.0'))

    def test_unknown_title_read_by_shape(self):
        minimal = [STARS, 'Unlisted start title', 'Start: 20250102030405', STARS]
        footer = [STARS, 'Unlisted end title', 'End: 20250102031000', STARS]
        sessions, _ = pst.parse_transcript(text_of(minimal + footer))
        self.assertEqual([(s['header'], s['start'], s['end']) for s in sessions],
                         [('minimal', '2025-01-02 03:04:05', '2025-01-02 03:10:00')])
        header = list(PS7_HEADER)
        header[1] = 'Unlisted start title'
        sessions, _ = pst.parse_transcript(text_of(PS7_HEADER + header))
        self.assertEqual(len(sessions), 2)

    def test_output_keeps_continuation_lines_and_stray_asterisks(self):
        lines = PS7_HEADER + command('20250102030500', 'PS C:\\> a; b', 'one',
                                     '>> b', STARS, 'not a block') + FOOTER
        _, commands = pst.parse_transcript(text_of(lines))
        self.assertEqual(commands[0]['output'], 'one\n>> b\n' + STARS + '\nnot a block')

    def test_output_is_cut_at_the_limit(self):
        long_line = 'x' * (pst.OUTPUT_LIMIT + 50)
        lines = PS7_HEADER + command('20250102030500', 'PS>x', long_line, 'y') + FOOTER
        c = pst.parse_transcript(text_of(lines))[1][0]
        self.assertEqual((len(c['output']), c['output_lines'], c['cut']),
                         (pst.OUTPUT_LIMIT, 2, True))

    def test_command_before_any_header(self):
        _, commands = pst.parse_transcript(text_of(command('20250102030500', 'PS>x')))
        self.assertEqual((commands[0]['session'], commands[0]['line']), (None, 4))

    def test_invalid_time_kept_as_digits(self):
        self.assertEqual(pst.show_time('20251399999999'), '20251399999999')
        self.assertEqual(pst.show_time('20250102030405'), '2025-01-02 03:04:05')


class DecodeTest(unittest.TestCase):
    def test_utf8_with_and_without_mark(self):
        self.assertEqual(pst.decode_transcript('\ufeff' .encode('utf-8') + 'café'.encode('utf-8')),
                         ('café', 0))
        self.assertEqual(pst.decode_transcript('café'.encode('utf-8')), ('café', 0))

    def test_utf16_by_mark(self):
        self.assertEqual(pst.decode_transcript('ñandú\r\n'.encode('utf-16')), ('ñandú\r\n', 0))

    def test_non_utf8_bytes_counted(self):
        text, replaced = pst.decode_transcript(b'caf\xe9 \xef\xbf\xbd')
        self.assertEqual((text, replaced), ('caf\ufffd \ufffd', 1))


class _Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return os.path.basename(path)


class ReadFilesTest(unittest.TestCase):
    def test_non_transcript_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            good = os.path.join(folder, 'PowerShell_transcript.LABPC.abc.20250102030405.txt')
            bad = os.path.join(folder, 'PowerShell_transcript.notes.txt')
            with open(good, 'wb') as handle:
                handle.write(b'\xef\xbb\xbf' + text_of(PS7_HEADER + FOOTER).encode('utf-8'))
            with open(bad, 'wb') as handle:
                handle.write(b'just some notes\r\n')
            results, sources = pst._read_transcripts(  # pylint: disable=protected-access
                _Context([bad, good, good]), 'test')
        self.assertEqual(sources, [good])
        self.assertEqual([(r[0], len(r[1])) for r in results],
                         [('PowerShell_transcript.LABPC.abc.20250102030405.txt', 1)])


if __name__ == '__main__':
    unittest.main()
