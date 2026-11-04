"""Pin the AnyDesk readers in scripts/artifacts/anyDesk.py.

The lines are written in the layouts measured on the AnyDesk known data (AnyDesk 9.8.3
on Windows 11, 8.1.0 on Ubuntu 26.04): connection_trace.txt space aligned, the
file_transfer_trace.txt tab separated, UTF-16LE without a byte order mark on Windows and
UTF-8 on Linux, and trace lines with three thread fields on Windows and four on the
Linux service. Every value is invented. The expected values are written out, never
read back from the code.
"""
import fnmatch
import pathlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import anyDesk as ad  # pylint: disable=wrong-import-position

CONNECTION = 'Incoming    2025-02-03, 04:05    User                             123456789    123456789'
TRANSFER = "File Manager\t2025-02-03, 04:06\tfinish\tdownload\t'notes v2.txt' (~1.00 KiB out of 1.00 KiB)"
TRACE_WINDOWS = ('   info 2025-02-03 04:05:06.789       gsvc   1960  10904   48'
                 '                anynet.any_socket - Accepting from 123456789.')
TRACE_LINUX = ('warning 2025-02-03 04:05:07.001       gsvc   main  85268  85268   44'
               '                      app.session - Passphrase not accepted.')


class DecodeText(unittest.TestCase):
    def test_utf16le_without_bom(self):
        text, replaced = ad.decode_text(CONNECTION.encode('utf-16-le'))
        self.assertEqual(text, CONNECTION)
        self.assertEqual(replaced, 0)

    def test_utf8(self):
        self.assertEqual(ad.decode_text(CONNECTION.encode('utf-8'))[0], CONNECTION)

    def test_utf16_with_bom(self):
        self.assertEqual(ad.decode_text(b'\xff\xfe' + CONNECTION.encode('utf-16-le'))[0], CONNECTION)


class ConnectionLine(unittest.TestCase):
    def test_fields(self):
        self.assertEqual(ad.parse_connection_line(CONNECTION),
                         {'direction': 'Incoming', 'time': '2025-02-03, 04:05', 'status': 'User',
                          'id': '123456789', 'second_id': '123456789'})

    def test_not_five_fields(self):
        self.assertIsNone(ad.parse_connection_line('Incoming    2025-02-03, 04:05    User'))
        self.assertIsNone(ad.parse_connection_line('Incoming    yesterday    User    1    2'))


class TransferLine(unittest.TestCase):
    def test_fields(self):
        self.assertEqual(ad.parse_transfer_line(TRANSFER),
                         {'mode': 'File Manager', 'time': '2025-02-03, 04:06', 'event': 'finish',
                          'direction': 'download', 'name': 'notes v2.txt',
                          'size': '~1.00 KiB out of 1.00 KiB'})

    def test_padded_fields_and_empty_tabs(self):
        line = "Clipboard\t\t2025-02-03, 04:07\tstart \tupload  \t'a.bin' (~0 B out of 2.00 MiB)"
        record = ad.parse_transfer_line(line)
        self.assertEqual((record['mode'], record['event'], record['direction'], record['name']),
                         ('Clipboard', 'start', 'upload', 'a.bin'))

    def test_unquoted_item_kept_whole(self):
        record = ad.parse_transfer_line('File Manager\t2025-02-03, 04:06\tstart\tupload\tsomething else')
        self.assertEqual((record['name'], record['size']), ('something else', ''))


class Times(unittest.TestCase):
    def test_text_time(self):
        self.assertEqual(ad.text_time('2025-02-03, 04:05'), datetime(2025, 2, 3, 4, 5, tzinfo=timezone.utc))
        self.assertIsNone(ad.text_time('2025-02-30, 04:05'))
        self.assertIsNone(ad.text_time('2025-02-03 04:05'))

    def test_windows_folders_only(self):
        self.assertTrue(ad.in_windows_folder('ProgramData/AnyDesk/connection_trace.txt'))
        self.assertTrue(ad.in_windows_folder('lba0/Users/u/AppData/Roaming/AnyDesk/connection_trace.txt'))
        self.assertTrue(ad.in_windows_folder('C:\\ProgramData\\AnyDesk\\ad_x\\connection_trace.txt'))
        self.assertFalse(ad.in_windows_folder('etc/anydesk/connection_trace.txt'))
        self.assertFalse(ad.in_windows_folder('home/u/.anydesk/connection_trace.txt'))
        self.assertFalse(ad.in_windows_folder('MyProgramData/AnyDesk/connection_trace.txt'))


class TraceLine(unittest.TestCase):
    def test_windows_layout(self):
        self.assertEqual(ad.parse_trace_line(TRACE_WINDOWS),
                         ('info', datetime(2025, 2, 3, 4, 5, 6, 789000, tzinfo=timezone.utc),
                          '2025-02-03 04:05:06.789', 'anynet.any_socket', 'Accepting from 123456789.'))

    def test_linux_service_layout(self):
        level, stamp, _, component, message = ad.parse_trace_line(TRACE_LINUX)
        self.assertEqual((level, stamp.microsecond, component, message),
                         ('warning', 1000, 'app.session', 'Passphrase not accepted.'))

    def test_banner_is_not_a_line(self):
        self.assertIsNone(ad.parse_trace_line(' * * * * * * * * * * * * * * * * * *'))

    def test_rules(self):
        self.assertEqual(ad.match_trace_rule('anynet.any_socket', 'Accepting from 123456789.'),
                         ('Accepting from', '123456789'))
        self.assertEqual(ad.match_trace_rule('anynet.connection_mgr', '[192.0.2.4:5000] Incoming connection.'),
                         ('Peer address (incoming connection)', '192.0.2.4:5000'))
        self.assertEqual(ad.match_trace_rule('app.session', '3: Authenticated by local user.'),
                         ('Authenticated', 'Authenticated by local user'))
        self.assertEqual(ad.match_trace_rule('app.session', 'Session closed locally: desk_rt_rejected.'),
                         ('Session closed', 'desk_rt_rejected'))
        self.assertEqual(ad.match_trace_rule('app.session', 'Passphrase not accepted.'),
                         ('Password not accepted', ''))

    def test_rule_needs_its_component(self):
        # the punch connector writes the same text for the same connection; only one is kept
        self.assertIsNone(ad.match_trace_rule('anynet.punch_connector', '[192.0.2.4:5000] Incoming connection.'))


class Paths(unittest.TestCase):
    """Each declared pattern matches the files it was written for, with the root/ prefix
    the seekers add, and not the hidden 0-byte .anydesk.trace beside anydesk.trace."""

    def matches(self, artifact, path):
        return any(fnmatch.fnmatchcase('root/' + path, p) for p in ad.__artifacts_v2__[artifact]['paths'])

    def test_connections(self):
        for path in ('ProgramData/AnyDesk/connection_trace.txt',
                     'Users/u/AppData/Roaming/AnyDesk/ad_custom/connection_trace.txt',
                     'etc/anydesk/connection_trace.txt', 'home/u/.anydesk/connection_trace.txt'):
            self.assertTrue(self.matches('anyDeskConnections', path), path)

    def test_traces(self):
        for path in ('ProgramData/AnyDesk/ad_svc.trace', 'Users/u/AppData/Roaming/AnyDesk/ad.trace',
                     'var/log/anydesk.trace', 'home/u/.anydesk/anydesk.trace'):
            self.assertTrue(self.matches('anyDeskTraceEvents', path), path)
        self.assertFalse(self.matches('anyDeskTraceEvents', 'home/u/.anydesk/.anydesk.trace'))


if __name__ == '__main__':
    unittest.main()
