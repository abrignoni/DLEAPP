"""Pin the row building of scripts/artifacts/macosAppUrlCache.py."""
import pathlib
import plistlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosAppUrlCache as cache  # pylint: disable=wrong-import-position

_EPOCH_2001 = datetime(2001, 1, 1, tzinfo=timezone.utc)
_STAMP = datetime(2021, 1, 17, 20, 18, 17, tzinfo=timezone.utc)
_RESPONSE_TIME = datetime(2021, 1, 17, 20, 18, 17, 797350, tzinfo=timezone.utc)

HEADERS = ('Time Stamp', 'Response Time', 'User', 'Cache Path', 'URL', 'Partition',
           'Data Stored In', 'Data Size', 'Response Object', 'Request Object', 'Entry ID')


def response_blob():
    return plistlib.dumps({'Version': 1, 'Array': [
        {'_CFURLString': 'https://example.test/a', '_CFURLStringType': 15},
        (_RESPONSE_TIME - _EPOCH_2001).total_seconds(), 0, 200, {'Content-Type': 'text/xml'}]})


def record(**changes):
    row = {'entry_ID': 7, 'request_key': 'https://example.test/a',
           'time_stamp': '2021-01-17 20:18:17', 'partition': None,
           'response_object': response_blob(), 'request_object': None, 'isDataOnFS': 0,
           'receiver_data': b'<xml/>'}
    row.update(changes)
    return row


class HelperTest(unittest.TestCase):
    def test_decoded(self):
        value, text = cache.decoded(plistlib.dumps({'b': b'\x01', 'a': 1}, fmt=plistlib.PlistFormat.FMT_BINARY))
        self.assertEqual(value, {'a': 1, 'b': b'\x01'})
        self.assertEqual(text, '{"a": 1, "b": "01"}')
        self.assertEqual(cache.decoded(None), (None, ''))
        self.assertEqual(cache.decoded(b'\x00\x01'), (None, '0001'))

    def test_times_and_locations(self):
        self.assertEqual(cache.utc_text('2021-01-17 20:18:17'), _STAMP)
        self.assertEqual(cache.utc_text('17/01/2021'), '')
        self.assertEqual(cache.response_time({'Array': [None, 0.0]}), _EPOCH_2001)
        self.assertEqual(cache.response_time({'Array': [None]}), '')
        self.assertEqual(cache.data_location(1, b'0D1E-UUID'), ('fsCachedData/0D1E-UUID', ''))
        self.assertEqual(cache.data_location(0, b'abcd'), ('Cache.db', 4))
        self.assertEqual(cache.data_location(0, None), ('Cache.db', ''))


class CacheRowsTest(unittest.TestCase):
    def test_a_cached_response(self):
        rows, unparsed = cache.cache_rows([record()], 'user1', 'Users/user1/Library/Caches/app')
        row = dict(zip(HEADERS, rows[0]))
        self.assertEqual(unparsed, 0)
        self.assertEqual((row['Time Stamp'], row['Response Time']), (_STAMP, _RESPONSE_TIME))
        self.assertEqual((row['User'], row['Cache Path'], row['URL'], row['Partition']),
                         ('user1', 'Users/user1/Library/Caches/app', 'https://example.test/a', ''))
        self.assertEqual((row['Data Stored In'], row['Data Size'], row['Entry ID']), ('Cache.db', 6, 7))
        self.assertIn('"Content-Type": "text/xml"', row['Response Object'])
        self.assertEqual(row['Request Object'], '')

    def test_an_unparsed_time_stamp_is_counted(self):
        rows, unparsed = cache.cache_rows([record(time_stamp='bad', isDataOnFS=1,
                                                  receiver_data='A-B')], '', 'Library/Caches/x')
        self.assertEqual(unparsed, 1)
        self.assertEqual((rows[0][0], rows[0][6]), ('', 'fsCachedData/A-B'))


if __name__ == '__main__':
    unittest.main()
