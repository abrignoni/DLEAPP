"""Pin the QSettings reader and the rows in scripts/artifacts/vlcDesktop.py.

Every settings text below is made up for the test (invented users, paths and URLs). The escapes and quoting are
the forms Qt 5.6.3's QSettings writes: a list item holding ',' ';' or '=' is quoted, '"' and '\\' are
backslash-escaped, a character from 0x7F up is written as \\x and the UTF-16 code unit, and a hex digit right after
such an escape is escaped too so that the reader's greedy \\x stops in the right place.
"""
import datetime
import os
import pathlib
import struct
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import vlcDesktop as vlc  # pylint: disable=wrong-import-position


def qurl_variant(url):
    """The @Variant text QSettings writes for a QUrl, with the escapes iniEscapedString applies."""
    raw = struct.pack('>I', 17) + struct.pack('>I', len(url)) + url.encode('latin-1')
    out, after_escape = [], False
    for byte in raw:
        char = chr(byte)
        if after_escape and char in '0123456789abcdefABCDEF':
            out.append(f'\\x{byte:x}')
            continue
        after_escape = False
        if byte == 0:
            out.append('\\0')
            after_escape = True
        elif byte <= 0x1f or byte >= 0x7f:
            out.append(f'\\x{byte:x}')
            after_escape = True
        else:
            out.append(char)
    return '@Variant(' + ''.join(out) + ')'


INI = ('[General]\r\n'
       'filedialog-path=' + qurl_variant('file:///C:/Users/tester/Videos/trip%20one.mkv') + '\r\n'
       '\r\n'
       '[RecentsMRL]\r\n'
       'list=file:///C:/Users/tester/Videos/trip%20one.mkv, "file:///C:/Users/tester/Videos/a,b;c=d.mkv", '
       'https://media.example.test/live?x=1, "file:///C:/Users/tester/Videos/q\\"uote.mkv"\r\n'
       'times=95500, 0, -1, 1500\r\n'
       '\r\n'
       '[OpenDialog]\r\n'
       'netMRL=rtsp://camera.example.test/stream, "https://media.example.test/a,b"\r\n').encode('latin-1')

CONF = ('; a comment line\n'
        '[General]\n'
        'filedialog-path=' + qurl_variant('file:///home/tester/Films') + '\n'
        '[RecentsMRL]\n'
        'list=@Invalid()\n'
        'times=@Invalid()\n'
        '[OpenDialog]\n'
        'netMRL=http://192.0.2.10:8080/clip.mp4\n').encode('latin-1')

VLCRC = (b'\xef\xbb\xbf###\n###  vlc 3.0.24\n###\n[qt] # Qt interface\n\n'
         b'# Save the recently played items in the menu (boolean)\nqt-recentplay=0\n\n'
         b'# List of words separated by | to filter (string)\n#qt-recentplay-filter=\n')


class ReaderTest(unittest.TestCase):
    def test_a_quoted_item_keeps_its_comma_semicolon_and_equals(self):
        settings = vlc.read_qsettings(INI)
        self.assertEqual(vlc.string_list(settings['RecentsMRL/list'][1]),
                         ['file:///C:/Users/tester/Videos/trip%20one.mkv',
                          'file:///C:/Users/tester/Videos/a,b;c=d.mkv',
                          'https://media.example.test/live?x=1',
                          'file:///C:/Users/tester/Videos/q"uote.mkv'])
        self.assertEqual(vlc.string_list(settings['RecentsMRL/times'][1]), ['95500', '0', '-1', '1500'])

    def test_a_general_key_has_no_section_and_its_qurl_decodes(self):
        settings = vlc.read_qsettings(INI)
        self.assertEqual(vlc.qurl_text(settings['filedialog-path'][1]),
                         'file:///C:/Users/tester/Videos/trip%20one.mkv')

    def test_a_hex_digit_after_an_escape_is_read_as_its_own_escape(self):
        # The length 0x41 is 'A', a hex digit right after \0, and 'f' follows it, so Qt writes \x41\x66ile.
        url = 'file:///home/tester/' + 'v' * 45
        text = qurl_variant(url)
        self.assertIn('\\x41\\x66ile', text)
        settings = vlc.read_qsettings(f'[General]\nfiledialog-path={text}\n'.encode('latin-1'))
        self.assertEqual(vlc.qurl_text(settings['filedialog-path'][1]), url)

    def test_a_non_latin_character_comes_from_its_utf16_escape(self):
        # \xe9 is U+00E9; \xd83c\xdfac is a surrogate pair for U+1F3AC.
        data = b'[A]\nname=caf\\xe9 \\xd83c\\xdfac, two\n'
        self.assertEqual(vlc.string_list(vlc.read_qsettings(data)['A/name'][1]), ['caf\u00e9 \U0001F3AC', 'two'])

    def test_invalid_is_an_empty_list_and_a_single_value_is_a_list_of_one(self):
        settings = vlc.read_qsettings(CONF)
        self.assertEqual(vlc.string_list(settings['RecentsMRL/list'][1]), [])
        self.assertEqual(settings['RecentsMRL/list'][0], '@Invalid()')
        self.assertEqual(vlc.string_list(settings['OpenDialog/netMRL'][1]), ['http://192.0.2.10:8080/clip.mp4'])

    def test_section_and_key_escapes_comments_and_a_repeated_key(self):
        data = (b'\xef\xbb\xbf[%General]\nkey=1\n[My%20Section]\nsub\\name = spaced value  \n'
                b'semi=before;after\nsemi=last\n')
        settings = vlc.read_qsettings(data)
        self.assertEqual(settings['General/key'][1], '1')
        self.assertEqual(settings['My Section/sub/name'][1], 'spaced value')
        self.assertEqual(settings['My Section/semi'][1], 'last')

    def test_double_at_loses_one_at(self):
        self.assertEqual(vlc.read_qsettings(b'[A]\nk=@@literal\n')['A/k'][1], '@literal')


class ValueTest(unittest.TestCase):
    def test_resume_positions(self):
        self.assertEqual(vlc.resume_position('128000')[0], '0:02:08')
        self.assertEqual(vlc.resume_position('1500')[0], '0:00:01.500')
        self.assertEqual(vlc.resume_position('3723000')[0], '1:02:03')
        self.assertTrue(vlc.resume_position('0')[1].startswith('no position saved'))
        self.assertTrue(vlc.resume_position('-1')[1].startswith('no time stored yet'))
        self.assertTrue(vlc.resume_position(None)[1].startswith('no value at this position'))
        self.assertEqual(vlc.resume_position('abc'), ('', 'not a whole number; reported as stored'))

    def test_media_is_decoded_as_the_recent_menu_labels_it(self):
        self.assertEqual(vlc.media_text('file:///C:/Videos/caf%C3%A9%20one.mkv', True), 'C:/Videos/caf\u00e9 one.mkv')
        self.assertEqual(vlc.media_text('file:///home/tester/a%2Cb.mkv', False), '/home/tester/a,b.mkv')
        self.assertEqual(vlc.media_text('http://example.test/a%20b', False), 'http://example.test/a b')
        self.assertEqual(vlc.media_text('file:///home/tester/100%.mkv', False), '/home/tester/100%.mkv')

    def test_vlcrc_options(self):
        found = vlc._vlcrc_options(VLCRC)  # pylint: disable=protected-access
        self.assertEqual(found['qt-recentplay'], ('0', 'qt-recentplay=0', False))
        self.assertEqual(found['qt-recentplay-filter'], ('', '#qt-recentplay-filter=', True))
        later = vlc._vlcrc_options(b'qt-recentplay=0\n#qt-recentplay=1\nqt-recentplay-filter=a\n'  # pylint: disable=protected-access
                                   b'qt-recentplay-filter=b\r\n')
        self.assertEqual(later['qt-recentplay'][0], '0')
        self.assertEqual(later['qt-recentplay-filter'][0], 'b')


class _Context:
    def __init__(self, files):
        self.files = files

    def get_files_found(self):
        return self.files

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path

    @staticmethod
    def get_seeker():
        raise ValueError


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        root = os.path.join(self.tmp.name, 'data')
        self.ini = os.path.join(root, 'C/Users/tester/AppData/Roaming/vlc/vlc-qt-interface.ini')
        self.conf = os.path.join(root, 'home/tester/.config/vlc/vlc-qt-interface.conf')
        self.rc = os.path.join(root, 'home/tester/.config/vlc/vlcrc')
        for path, data in ((self.ini, INI), (self.conf, CONF), (self.rc, VLCRC)):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as handle:
                handle.write(data)

    def tearDown(self):
        self.tmp.cleanup()

    def test_recent_media_rows(self):
        headers, rows, source = vlc.vlcRecentMedia.__wrapped__(_Context([self.ini, self.conf, self.rc]))
        self.assertEqual(headers[0], ('File Modified', 'datetime'))
        ini = 'C/Users/tester/AppData/Roaming/vlc/vlc-qt-interface.ini'
        self.assertEqual([row[1:] for row in rows], [
            (1, 'C:/Users/tester/Videos/trip one.mkv', '0:01:35.500', '95500',
             'time saved when playback of the item ended', 'file:///C:/Users/tester/Videos/trip%20one.mkv', ini),
            (2, 'C:/Users/tester/Videos/a,b;c=d.mkv', '', '0',
             vlc.resume_position('0')[1], 'file:///C:/Users/tester/Videos/a,b;c=d.mkv', ini),
            (3, 'https://media.example.test/live?x=1', '', '-1',
             vlc.resume_position('-1')[1], 'https://media.example.test/live?x=1', ini),
            (4, 'C:/Users/tester/Videos/q"uote.mkv', '0:00:01.500', '1500',
             'time saved when playback of the item ended', 'file:///C:/Users/tester/Videos/q"uote.mkv', ini)])
        self.assertEqual(source.split('\n'), sorted([self.ini, self.conf]))

    def test_settings_rows(self):
        _, rows, source = vlc.vlcSettings.__wrapped__(_Context([self.ini, self.conf, self.rc]))
        got = [(row[1], row[2], row[3], row[4]) for row in rows]
        self.assertEqual(got, [
            ('RecentsMRL/list', '', '4 items', ''),
            ('OpenDialog/netMRL', 1, 'rtsp://camera.example.test/stream', ''),
            ('OpenDialog/netMRL', 2, 'https://media.example.test/a,b', ''),
            ('filedialog-path', '', 'file:///C:/Users/tester/Videos/trip%20one.mkv',
             'C:/Users/tester/Videos/trip one.mkv'),
            ('RecentsMRL/list', '', '0 items', ''),
            ('OpenDialog/netMRL', 1, 'http://192.0.2.10:8080/clip.mp4', ''),
            ('filedialog-path', '', 'file:///home/tester/Films', '/home/tester/Films'),
            ('vlcrc qt-recentplay', '', '0', ''),
            ('vlcrc qt-recentplay-filter', '', '', '')])
        self.assertEqual(rows[4][5], '@Invalid()')
        self.assertEqual(rows[8][5], '#qt-recentplay-filter=')
        self.assertEqual(len(source.split('\n')), 3)

    def test_a_file_with_no_recents_gives_no_recent_rows(self):
        _, rows, _ = vlc.vlcRecentMedia.__wrapped__(_Context([self.conf]))
        self.assertEqual(rows, [])

    def test_file_modified_is_utc_when_the_seeker_recorded_it(self):
        when = vlc.recorded_time(type('S', (), {'file_infos': {self.ini: type('I', (), {
            'modification_date': 1760821049})()}})(), self.ini, None)
        self.assertEqual(when, datetime.datetime(2025, 10, 18, 20, 57, 29, tzinfo=datetime.timezone.utc))


if __name__ == '__main__':
    unittest.main()
