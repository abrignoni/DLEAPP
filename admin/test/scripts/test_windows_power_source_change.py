"""Pin how Windows System Power Events reports Kernel-Power event 105, from a record written here in the shape
the provider's version 1 template gives (AcOnline, RemainingCapacity, FullChargeCapacity)."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsSystemPowerEvents as power  # pylint: disable=wrong-import-position

RECORD = '''<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Kernel-Power"/>
    <EventID>105</EventID>
    <Version>1</Version>
    <TimeCreated SystemTime="2026-10-01 12:00:00.000000+00:00"/>
    <EventRecordID>7</EventRecordID>
    <Computer>host</Computer>
  </System>
  <EventData>
    <Data Name="AcOnline">{ac}</Data>
    <Data Name="RemainingCapacity">{remaining}</Data>
    <Data Name="FullChargeCapacity">{full}</Data>
  </EventData>
</Event>'''


class PowerSourceChangeTest(unittest.TestCase):
    def row(self, **values):
        found = power._power_record(RECORD.format(**values))  # pylint: disable=protected-access
        return power._power_row(found, {})  # pylint: disable=protected-access

    def test_the_fields_are_shown_unchanged(self):
        row = self.row(ac='False', remaining='56293', full='62654')
        self.assertEqual((row[3], row[4], row[5]), ('Power source change', 'Microsoft-Windows-Kernel-Power', '105'))
        self.assertEqual(row[6], 'AC Online: False; Remaining Capacity (as stored): 56293; '
                                 'Full Charge Capacity (as stored): 62654')
        self.assertEqual((row[1], row[2]), ('', ''))

    def test_a_stored_zero_is_kept(self):
        self.assertEqual(self.row(ac='True', remaining='0', full='0')[6],
                         'AC Online: True; Remaining Capacity (as stored): 0; Full Charge Capacity (as stored): 0')


if __name__ == '__main__':
    unittest.main()
