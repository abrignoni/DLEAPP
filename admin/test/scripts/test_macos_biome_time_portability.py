"""macosBiome reads 8-byte doubles as Unix or Cocoa seconds the same way on every platform.

_unix_double and _mac2001_double turn any conversion error into ''. They used
datetime.fromtimestamp, directly or through webkit_timestampsconv, which on Windows fails
outside 1970-01-01 to 3000-12-31. NSDate.distantFuture (4001-01-01) therefore converted on
macOS and came out blank on Windows. WindowsGmtime reproduces that range here, so the tests
show the difference on any platform. All values here are constructed. In a macOS run on
adams_macbookpro_macos26 the changed converters fill two populated columns, Siri Message History
times (199 rows, _unix_double) and Wi-Fi Connection Events times (126, _mac2001_double); none is
before 1970 or after 3000, and they are identical before and after this change. Their other users,
Siri Interaction History and App Intents Transcript, have no rows there.
"""
from datetime import datetime, timezone
import pathlib
import struct
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts.macosBiome import _mac2001_double, _unix_double  # pylint: disable=wrong-import-position

# 3001-01-01 00:00:00 UTC, the end of the documented range (the bound is documented, not measured).
# Microsoft Learn, "gmtime, _gmtime32, _gmtime64": _gmtime64 expresses dates
# "up through 23:59:59, December 31, 3000, UTC", and midnight, January 1, 1970, is the lower bound.
WINDOWS_GMTIME_END = 32535216000
DISTANT_FUTURE_COCOA = 63113904000.0  # NSDate.distantFuture, read from Foundation
DISTANT_FUTURE_UNIX = DISTANT_FUTURE_COCOA + 978307200
YEAR_4001 = datetime(4001, 1, 1, tzinfo=timezone.utc)
YEAR_3500 = datetime(3500, 7, 1, 12, 30, tzinfo=timezone.utc)  # after 3000, not a sentinel
COCOA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class WindowsGmtime(datetime):
    """datetime whose fromtimestamp accepts only the range Windows' gmtime accepts."""

    @classmethod
    def fromtimestamp(cls, timestamp, tz=None):
        if not 0 <= timestamp < WINDOWS_GMTIME_END:
            raise OSError(22, 'Invalid argument')
        return datetime.fromtimestamp(timestamp, tz)


def packed(seconds):
    return struct.pack('<d', seconds)


def on_windows_range():
    """Patch both places the converters can reach fromtimestamp."""
    return (mock.patch('scripts.artifacts.macosBiome.datetime', WindowsGmtime),
            mock.patch('scripts.ilapfuncs.datetime', WindowsGmtime))


class SameResultOnEveryPlatform(unittest.TestCase):
    cases = (
        ('cocoa', DISTANT_FUTURE_COCOA, YEAR_4001),
        ('unix', DISTANT_FUTURE_UNIX, YEAR_4001),
        ('cocoa', (YEAR_3500 - COCOA_EPOCH).total_seconds(), YEAR_3500),
        ('unix', (YEAR_3500 - UNIX_EPOCH).total_seconds(), YEAR_3500),
        ('cocoa', -1009843200.0, datetime(1969, 1, 1, tzinfo=timezone.utc)),
        ('unix', -86400.5, datetime(1969, 12, 30, 23, 59, 59, 500000, tzinfo=timezone.utc)),
        ('cocoa', 700000000.25, datetime(2023, 3, 8, 20, 26, 40, 250000, tzinfo=timezone.utc)),
        ('unix', 1678307200.0, datetime(2023, 3, 8, 20, 26, 40, tzinfo=timezone.utc)),
    )

    def convert(self, kind, seconds):
        return (_mac2001_double if kind == 'cocoa' else _unix_double)(packed(seconds))

    def test_native_platform(self):
        for kind, seconds, expected in self.cases:
            with self.subTest(kind=kind, seconds=seconds):
                self.assertEqual(self.convert(kind, seconds), expected)

    def test_windows_gmtime_range(self):
        first, second = on_windows_range()
        with first, second:
            for kind, seconds, expected in self.cases:
                with self.subTest(kind=kind, seconds=seconds):
                    self.assertEqual(self.convert(kind, seconds), expected)


class ErrorsStayBlank(unittest.TestCase):
    """The callers' contract: anything that cannot be converted is ''."""

    def test_unconvertible_values(self):
        first, second = on_windows_range()
        for patched in (False, True):
            for convert, value in ((_mac2001_double, packed(-63114076800.0)),  # NSDate.distantPast
                                   (_mac2001_double, packed(1e20)), (_unix_double, packed(-1e20)),
                                   (_unix_double, packed(float('nan'))), (_unix_double, packed(float('inf'))),
                                   (_unix_double, b'\x00' * 7), (_mac2001_double, None)):
                with self.subTest(patched=patched, convert=convert.__name__, value=value):
                    if patched:
                        with first, second:
                            self.assertEqual(convert(value), '')
                    else:
                        self.assertEqual(convert(value), '')


if __name__ == '__main__':
    unittest.main()
