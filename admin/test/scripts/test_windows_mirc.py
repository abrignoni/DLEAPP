"""Pin parse_log in scripts/artifacts/windowsMirc.py on a log built here in mIRC 7.86's layout (made-up names)."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsMirc as mirc  # pylint: disable=wrong-import-position

LOG = ('\r\nSession Start: Wed Nov 04 03:25:17 2026\r\nSession Ident: #room\r\n'
       '\x0303[03:25] * Now talking in #room\r\n'
       '[03:25] <peer> hello \x02there\x02\r\n'
       '\x0306[03:25] * peer waves\r\n'
       '\x0301[03:26] <me> reply\r\n'
       '-\r\n'
       'Session Close: Wed Nov 04 03:25:49 2026\r\n'
       '\r\nSession Start: Bad date\r\nSession Ident: #room\r\n[03:27] <peer> again\r\n')


class ParseLogTest(unittest.TestCase):
    def test_sessions_and_lines(self):
        sessions, lines = mirc.parse_log(LOG)
        self.assertEqual(sessions, [
            {'start': '2026-11-04 03:25:17', 'close': '2026-11-04 03:25:49', 'window': '#room', 'lines': 4},
            {'start': 'Bad date', 'close': '', 'window': '#room', 'lines': 1}])
        self.assertEqual(lines, [
            ('2026-11-04 03:25:17', '03:25', '#room', '', '* Now talking in #room', 4),
            ('2026-11-04 03:25:17', '03:25', '#room', 'peer', 'hello there', 5),
            ('2026-11-04 03:25:17', '03:25', '#room', '', '* peer waves', 6),
            ('2026-11-04 03:25:17', '03:26', '#room', 'me', 'reply', 7),
            ('Bad date', '03:27', '#room', 'peer', 'again', 13)])

    def test_a_line_before_any_session_has_no_session(self):
        _sessions, lines = mirc.parse_log('[10:00] <a> b\n')
        self.assertEqual(lines, [('', '10:00', '', 'a', 'b', 1)])


if __name__ == '__main__':
    unittest.main()
