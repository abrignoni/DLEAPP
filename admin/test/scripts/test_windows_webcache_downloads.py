"""Pin the iedownload record reader of the WebCache module (scripts/artifacts/windowsWebcache.py).

The records are built in the shape of the tested entries: a first 32-bit value, fixed fields with the size at
byte 72, then NUL-terminated UTF-16LE strings. Every string value is made up.
"""
import pathlib
import struct
import sys
import unittest
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsWebcache as webcache
# pylint: enable=wrong-import-position


def record(first, strings, size=1234, second=None):
    start = {137: 336, 140: 344}.get(first, 344)
    head = bytearray(start)
    struct.pack_into('<II', head, 0, first, 11)
    struct.pack_into('<QQ', head, 72, size, size if second is None else second)
    return bytes(head) + b''.join(text.encode('utf-16-le') + b'\x00\x00' for text in strings)


EDGE = ['https://example.invalid/page', 'application/octet-stream',
        'C:\\Users\\u\\AppData\\Local\\Packages\\pkg\\AC\\#!001\\MicrosoftEdge\\Cache\\ABC\\file[1].bin',
        'https://example.invalid/file.bin', 'C:\\Users\\u\\Downloads\\file.bin']
IE = ['Publisher Name', 'https://example.invalid/page', 'application/x-msdownload',
      'C:\\Users\\u\\AppData\\Local\\Microsoft\\Windows\\INetCache\\IE\\XYZ\\setup[1].exe',
      'https://example.invalid/setup.exe', '\\\\server\\share\\setup.exe']


class DownloadRecordTest(unittest.TestCase):
    def test_a_five_string_record_gives_every_field(self):
        problems = Counter()
        self.assertEqual(webcache.download_record(record(140, EDGE, size=661), problems), {
            'url': EDGE[3], 'saved_to': EDGE[4], 'size': 661, 'other': ' | '.join(EDGE[:3])})
        self.assertEqual(problems, Counter())

    def test_the_strings_are_read_from_the_end_whatever_their_number(self):
        found = webcache.download_record(record(137, IE, size=99, second=7), Counter())
        self.assertEqual((found['url'], found['saved_to'], found['size']), (IE[4], IE[5], 99))
        self.assertEqual(found['other'], ' | '.join(IE[:4]))

    def test_a_string_that_is_not_text_is_shown_as_a_byte_count(self):
        blob = record(140, EDGE[:2]) + b'\x01\xd8\x02\x03\x00\x00' + record(140, EDGE[3:])[344:]
        found = webcache.download_record(blob, Counter())
        self.assertEqual(found['other'], ' | '.join(EDGE[:2] + ['(4 bytes that are not text, not shown)']))
        self.assertEqual(found['saved_to'], EDGE[4])

    def test_a_last_string_that_is_not_a_path_leaves_url_and_path_blank(self):
        problems = Counter()
        found = webcache.download_record(record(140, EDGE[:4] + ['not a path']), problems)
        self.assertEqual((found['url'], found['saved_to'], found['size']), ('', '', 1234))
        self.assertEqual(found['other'], ' | '.join(EDGE[:4] + ['not a path']))
        self.assertEqual(sum(problems.values()), 1)

    def test_an_unknown_first_value_or_a_short_record_is_not_decoded(self):
        problems = Counter()
        self.assertIsNone(webcache.download_record(record(150, EDGE), problems))
        self.assertIsNone(webcache.download_record(record(140, EDGE)[:200], problems))
        self.assertIsNone(webcache.download_record(b'', problems))
        self.assertEqual(sum(problems.values()), 3)

    def test_impacket_hex_text_is_turned_back_into_bytes(self):
        blob = record(140, EDGE)
        self.assertEqual(webcache._raw(blob.hex().encode()), blob)  # pylint: disable=protected-access
        self.assertEqual(webcache._raw(None), b'')  # pylint: disable=protected-access


if __name__ == '__main__':
    unittest.main()
