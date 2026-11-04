"""Pin the location parameter reader of the WebCache module (scripts/artifacts/windowsWebcache.py).

The URLs are shaped like the cached assets.msn.com requests on the tested images; hosts, paths and values are made up.
"""
import datetime
import pathlib
import sys
import unittest
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsWebcache as webcache
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc
CLIENT = ('https://example.invalid/service/news/feed/windows?locale=en-us&clientLocation=12.3456789%7C-45.6789012'
          '&clientLocationAccuracy=31.5&clientLocationProvider=WiFi&clientLocationTimestamp=2026-01-02T03%3A04%3A05Z'
          '&timeOut=1000')


class LocationParametersTest(unittest.TestCase):
    def test_a_client_location_url_gives_every_field(self):
        problems = Counter()
        self.assertEqual(webcache.location_parameters(CLIENT, problems), {
            'time': datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC), 'latitude': 12.3456789,
            'longitude': -45.6789012, 'parameter': 'clientLocation', 'stored': '12.3456789|-45.6789012',
            'accuracy': '31.5', 'provider': 'WiFi'})
        self.assertEqual(problems, Counter())

    def test_a_location_url_gives_the_point_and_nothing_else(self):
        found = webcache.location_parameters('https://example.invalid/a/b?location=1.234%7C-5.678&timeOut=10',
                                             Counter())
        self.assertEqual((found['time'], found['latitude'], found['longitude'], found['parameter'],
                          found['accuracy'], found['provider']), ('', 1.234, -5.678, 'location', '', ''))

    def test_other_shapes_give_no_row_and_are_counted(self):
        problems = Counter()
        for url in ('https://example.invalid/?location=Somewhere', 'https://example.invalid/?location=91%7C0',
                    'https://example.invalid/?clientLocation=1%7C2%7C3', 'https://example.invalid/?clientLocation=nan%7C1'):
            self.assertIsNone(webcache.location_parameters(url, problems))
        self.assertEqual(sum(problems.values()), 4)
        for url in ('https://example.invalid/?ll=12', 'https://example.invalid/?lat=1&lon=2', 'not a url %%'):
            self.assertIsNone(webcache.location_parameters(url, problems))
        self.assertEqual(sum(problems.values()), 4)

    def test_a_timestamp_of_another_form_is_left_blank_and_counted(self):
        problems = Counter()
        found = webcache.location_parameters(CLIENT.replace('2026-01-02T03%3A04%3A05Z', '1767322800'), problems)
        self.assertEqual((found['time'], found['latitude']), ('', 12.3456789))
        self.assertEqual(problems, {'clientLocationTimestamp values not in the form YYYY-MM-DDTHH:MM:SSZ, left blank': 1})


if __name__ == '__main__':
    unittest.main()
