"""Pin the rows scripts/artifacts/chromiumSessions.py makes from Chromium session files.

The SNSS files are built byte by byte here, from the layouts in Chromium's
components/sessions/core sources, so the test does not share the reader's idea of the
format. Expected values are written out as literals.
"""
import datetime
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists  # pylint: disable=wrong-import-position
from scripts.artifacts import chromiumSessions as cs  # pylint: disable=wrong-import-position
from scripts.chromium import browser_profiles  # pylint: disable=wrong-import-position

_UTC = datetime.timezone.utc
# 2023-01-05 12:00:00 UTC as microseconds since 1601-01-01 UTC.
_T0 = 13317393600000000
_PROFILE = 'Users/someone/AppData/Local/Google/Chrome/User Data/Default'


def _at(seconds):
    return datetime.datetime(2023, 1, 5, 12, 0, 0, tzinfo=_UTC) + datetime.timedelta(seconds=seconds)


def _aligned(data):
    return data + b'\x00' * ((4 - len(data) % 4) % 4)


def _string(text):
    raw = text.encode('utf-8')
    return struct.pack('<i', len(raw)) + _aligned(raw)


def _string16(text):
    raw = text.encode('utf-16-le')
    return struct.pack('<i', len(raw) // 2) + _aligned(raw)


def _pickle(body):
    return struct.pack('<I', len(body)) + body


def _navigation(tab_id, index, url, title, when, transition=0, referrer='', original=''):
    body = (struct.pack('<ii', tab_id, index) + _string(url) + _string16(title) + _string('')
            + struct.pack('<ii', transition, 0) + _string(referrer) + struct.pack('<i', 0)
            + _string(original or url) + struct.pack('<i', 0) + struct.pack('<q', when)
            + _string16('') + struct.pack('<iii', 200, 0, 0) + struct.pack('<qqq', 0, 0, 0)
            + struct.pack('<i', 0))
    return _pickle(body)


def _snss(records, version=3):
    data = b'SNSS' + struct.pack('<i', version)
    for command, payload in records:
        data += struct.pack('<H', 1 + len(payload)) + bytes([command]) + payload
    return data


def _commands(data):
    """Split a file built by _snss back into (command, payload) pairs."""
    out, offset = [], 8
    while offset < len(data):
        size = struct.unpack_from('<H', data, offset)[0]
        out.append((data[offset + 2], data[offset + 3:offset + 2 + size]))
        offset += 2 + size
    return out


def _session_file():
    return _snss([
        (0, struct.pack('<ii', 7, 1)),                                   # tab 1 in window 7
        (6, _navigation(1, 0, 'https://a.example/0', 'A0', _T0)),
        (6, _navigation(1, 1, 'https://a.example/1', 'A1', _T0 + 10_000_000, transition=1)),
        (6, _navigation(1, 0, 'https://a.example/0', 'A0', _T0)),      # identical rewrite
        (6, _navigation(1, 1, 'https://a.example/new', 'A1b', _T0 + 20_000_000)),
        (7, struct.pack('<ii', 1, 1)),                                   # tab 1 selects index 1
        (21, struct.pack('<i4xq', 1, _T0 + 30_000_000)),                # tab 1 last active
        (0, struct.pack('<ii', 8, 2)),                                   # tab 2 in window 8
        (6, _navigation(2, 0, 'https://b.example/', 'B', _T0 + 40_000_000,
                        referrer='https://ref.example/')),
        (7, struct.pack('<ii', 2, 0)),
        (21, struct.pack('<i4xq', 2, 45568489013)),                     # a tick value, not a date
        (16, struct.pack('<i4xq', 2, _T0 + 50_000_000)),                # tab 2 closed
        (17, struct.pack('<i4xq', 8, _T0 + 60_000_000)),                # window 8 closed
        (6, _navigation(3, 0, 'https://c.example/', 'C', _T0)),         # no selected index
        (6, b'\x04\x00\x00\x00\x01\x00'),                               # a pickle that is cut short
    ])


def _window(window_id, num_tabs, when):
    body = struct.pack('<iiiq', window_id, 0, num_tabs, when) + struct.pack('<iiiii', 0, 0, 0, 0, 1)
    return _pickle(body + _string(''))


def _tabs_file():
    return _snss([
        (1, _navigation(90, 0, 'https://orphan.example/', 'O', _T0)),   # before any tab record
        (9, _window(20, 2, _T0 + 5_000_000)),
        (4, struct.pack('<iiq', 21, 1, _T0 + 5_000_000)),
        (1, _navigation(21, 4, 'https://w.example/4', 'W4', _T0)),
        (1, _navigation(21, 5, 'https://w.example/5', 'W5', _T0 + 1_000_000)),
        (4, struct.pack('<iiq', 22, 0, _T0 + 5_000_000)),
        (1, _navigation(22, 0, 'https://x.example/', 'X', _T0 + 2_000_000)),
        (4, struct.pack('<iiq', 30, 0, _T0 + 9_000_000)),                # a lone tab after the window
        (1, _navigation(30, 2, 'https://lone.example/', 'L', _T0 + 3_000_000)),
        (4, struct.pack('<iiq', 31, 0, 0)),                              # a tab with no close time
        (1, _navigation(31, 0, 'https://zero.example/', 'Z', _T0 + 4_000_000)),
        (2, struct.pack('<i', 30)),                                      # restored entry: tab 30
        (2, struct.pack('<i', 20)),                                      # restored entry: window 20
    ])


class SessionRowsTest(unittest.TestCase):
    def test_rows_facts_and_duplicates(self):
        rows, undecoded = cs.session_rows(_commands(_session_file()))
        self.assertEqual(undecoded, 1)
        by_url = {row[4]: row for row in rows}
        # The identical rewrite of index 0 is one row; the rewrite of index 1 is kept as a second row.
        self.assertEqual([row[4] for row in rows],
                         ['https://a.example/0', 'https://a.example/1', 'https://a.example/new',
                          'https://b.example/', 'https://c.example/'])
        a0, a1, new, b, c = (by_url[u] for u in ('https://a.example/0', 'https://a.example/1',
                                                 'https://a.example/new', 'https://b.example/',
                                                 'https://c.example/'))
        self.assertEqual(a0[:4], (_at(0), _at(30), '', ''))
        self.assertEqual(a0[10:16], (1, 0, 'No', 'Yes', 7, _T0 + 30_000_000))
        self.assertEqual(a1[10:15], (1, 1, 'No', 'No', 7))
        self.assertEqual((a1[6], a1[7]), ('TYPED (1)', ''))
        self.assertEqual(new[10:15], (1, 1, 'Yes', 'Yes', 7))
        self.assertEqual(new[0], _at(20))
        self.assertEqual(b[:4], (_at(40), '', _at(50), _at(60)))
        self.assertEqual(b[8], 'https://ref.example/')
        self.assertEqual(b[10:16], (2, 0, 'Yes', 'Yes', 8, 45568489013))
        self.assertEqual(c[10:16], (3, 0, '', 'Yes', '', ''))


class ClosedTabRowsTest(unittest.TestCase):
    def test_tabs_windows_and_restored_entries(self):
        rows, unreported = cs.closed_tab_rows(_commands(_tabs_file()))
        self.assertEqual(unreported, 1)
        self.assertEqual([(row[2], row[8], row[9], row[10], row[11], row[12]) for row in rows], [
            ('https://w.example/4', 21, 4, 'No', 20, 'Yes'),
            ('https://w.example/5', 21, 5, 'Yes', 20, 'Yes'),
            ('https://x.example/', 22, 0, 'Yes', 20, 'Yes'),
            ('https://lone.example/', 30, 2, 'Yes', '', 'Yes'),
            ('https://zero.example/', 31, 0, 'Yes', '', 'No'),
        ])
        self.assertEqual([row[1] for row in rows], [_at(5), _at(5), _at(5), _at(9), ''])
        self.assertEqual(rows[1][0], _at(1))

    def test_only_a_restored_entry_record_ends_the_current_tab(self):
        data = _snss([
            (4, struct.pack('<iiq', 50, 0, _T0)),
            (1, _navigation(50, 0, 'https://one.example/', 'One', _T0)),
            (13, b'\x00' * 8),                                            # a group record
            (1, _navigation(50, 1, 'https://two.example/', 'Two', _T0)),
            (2, struct.pack('<i', 99)),                                     # a restored entry record
            (1, _navigation(50, 2, 'https://three.example/', 'Three', _T0)),
        ])
        rows, unreported = cs.closed_tab_rows(_commands(data))
        self.assertEqual([(row[2], row[8]) for row in rows],
                         [('https://one.example/', 50), ('https://two.example/', 50)])
        self.assertEqual(unreported, 1)

    def test_a_restored_entry_before_the_tab_does_not_count(self):
        data = _snss([
            (2, struct.pack('<i', 40)),
            (4, struct.pack('<iiq', 40, 0, _T0)),
            (1, _navigation(40, 0, 'https://again.example/', 'G', _T0)),
        ])
        rows, _unreported = cs.closed_tab_rows(_commands(data))
        self.assertEqual([row[12] for row in rows], ['No'])


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.files = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files.append(str(path))

    def _run(self, processor):
        logs = []
        with mock.patch.object(cs, 'logfunc', logs.append), \
                mock.patch.object(macos_plists, 'logfunc', logs.append):
            headers, rows, source = processor.__wrapped__(FakeContext(self.root, self.files))
        return headers, rows, source, logs

    def test_session_files_old_and_new_names(self):
        self._write(f'{_PROFILE}/Sessions/Session_13317393600000000', _session_file())
        self._write(f'{_PROFILE}/Current Session', _session_file())
        self._write(f'{_PROFILE}/Sessions/Session_notanumber', _session_file())
        self._write(f'{_PROFILE}/Sessions/Tabs_13317393600000000', _tabs_file())
        headers, rows, source, logs = self._run(cs.chromiumSessionTabs)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 10)
        self.assertEqual(sorted({row[-1].rsplit('/', 1)[-1] for row in rows}),
                         ['Current Session', 'Session_13317393600000000'])
        self.assertEqual(rows[0][-4:-1], ('Google Chrome', 'Default', 'someone'))
        self.assertEqual(len(source.splitlines()), 2)
        self.assertEqual(sum('could not be decoded' in line for line in logs), 2)

    def test_tab_restore_files(self):
        self._write(f'{_PROFILE}/Sessions/Tabs_13317393600000000', _tabs_file())
        self._write(f'{_PROFILE}/Last Tabs', _tabs_file())
        headers, rows, _source, logs = self._run(cs.chromiumClosedTabs)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(len(rows), 10)
        self.assertEqual(sum('were not reported' in line for line in logs), 2)

    def test_an_encrypted_version_5_file_is_logged_and_not_read(self):
        self._write(f'{_PROFILE}/Sessions_Encrypted/Session_13317393600000000',
                    b'SNSS' + struct.pack('<i', 5) + b'\x00' * 32)
        _headers, rows, source, logs = self._run(cs.chromiumSessionTabs)
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(logs, ['Chromium Session Tabs: '
                                f'{_PROFILE}/Sessions_Encrypted/Session_13317393600000000 is SNSS '
                                'version 5, which the browser encrypts; not read'])

    def test_opera_keeps_its_sessions_in_the_user_data_folder(self):
        opera = 'Users/someone/AppData/Roaming/Opera Software/Opera Stable'
        self._write(f'{opera}/Sessions/Session_13317393600000000', _session_file())
        _headers, rows, _source, _logs = self._run(cs.chromiumSessionTabs)
        self.assertEqual({row[-4:-1] for row in rows}, {('Opera', 'Opera Stable', 'someone')})


class HelperTest(unittest.TestCase):
    def test_locate_reads_a_sessions_folder_in_a_user_data_folder_as_a_store(self):
        self.assertEqual(
            browser_profiles.locate('Users/u/AppData/Roaming/Opera Software/Opera Stable/'
                                    'Sessions/Session_1'),
            ('Opera', 'Opera Stable', 'u', 'Users/u/AppData/Roaming/Opera Software/Opera Stable',
             'Sessions/Session_1'))
        self.assertEqual(
            browser_profiles.locate(f'{_PROFILE}/Sessions/Tabs_1')[1:],
            ('Default', 'someone', _PROFILE, 'Sessions/Tabs_1'))

    def test_page_transition(self):
        self.assertEqual(browser_profiles.page_transition(0x30000001),
                         ('TYPED (1)', 'CHAIN_START, CHAIN_END'))
        self.assertEqual(browser_profiles.page_transition(0x00100000),
                         ('LINK (0)', 'other bits 0x00100000'))
        self.assertEqual(browser_profiles.page_transition(None), ('', ''))


if __name__ == '__main__':
    unittest.main()
