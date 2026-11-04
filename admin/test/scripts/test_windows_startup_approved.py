"""Pin the StartupApproved value reader and the Startup folder classifier of
scripts/artifacts/windowsStartupApproved.py. The byte shapes are the ones measured on the known-data VM; the
paths are made up and the time is one press time from the known-data log."""
import datetime
import pathlib
import struct
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsStartupApproved as sa
# pylint: enable=wrong-import-position

STAMP = 134382388931507012
WHEN = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(microseconds=STAMP // 10)


def value(flag, stamp=0):
    return bytes([flag, 0, 0, 0]) + struct.pack('<Q', stamp)


class ApprovedValueTest(unittest.TestCase):
    def test_every_measured_flag_maps_by_its_low_bit(self):
        for flag, state, stamp in ((0x00, 'Enabled', 0), (0x01, 'Disabled', STAMP), (0x02, 'Enabled', 0),
                                   (0x03, 'Disabled', STAMP), (0x04, 'Enabled', 0), (0x05, 'Disabled', STAMP),
                                   (0x06, 'Enabled', 0)):
            flags, got_state, got_stamp = sa.approved_value(value(flag, stamp))
            self.assertEqual((flags, got_state), (f'{flag:02x}', state))
            self.assertEqual(got_stamp, WHEN if stamp else '')

    def test_short_or_missing_values(self):
        self.assertEqual(sa.approved_value(b''), ('', '', ''))
        self.assertEqual(sa.approved_value(None), ('', '', ''))
        self.assertEqual(sa.approved_value(b'\x03\x00'), ('03', 'Disabled', ''))


class StartupLocationTest(unittest.TestCase):
    def test_the_three_folder_shapes(self):
        self.assertEqual(sa.startup_location(
            'C/Users/pat/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/a.lnk'), ('User', 'pat'))
        self.assertEqual(sa.startup_location(
            'C/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp/b.bat'), ('All users', ''))
        self.assertEqual(sa.startup_location(
            'C/Documents and Settings/pat/Start Menu/Programs/Startup/c.lnk'), ('User', 'pat'))
        self.assertEqual(sa.startup_location(
            'C/Documents and Settings/All Users/Start Menu/Programs/Startup/d.lnk'), ('All users', ''))

    def test_other_paths_are_not_startup_items(self):
        self.assertIsNone(sa.startup_location('C/Users/pat/AppData/Roaming/Microsoft/Windows/Start Menu/x.lnk'))
        self.assertIsNone(sa.startup_location('C/Users/pat/Desktop/Startup/e.lnk'))


if __name__ == '__main__':
    unittest.main()
