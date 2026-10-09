"""Pin how the Battery Center artifacts split a unified log entry into columns.

Battery Center writes a power source as an NSDictionary description, one 'key = value;' line
per key between braces, and a device as '<BCBatteryDevice: 0x...; key = value; ...>'. The
messages below are synthetic and follow those two shapes. The expected rows are written out,
never read back from the code.
"""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosUnifiedLogs as module  # pylint: disable=wrong-import-position

SOURCE = '''(<_BCPowerSourceController: 0x100000000>) Found power source: {
    "Accessory Category" = Keyboard;
    "Accessory Identifier" = "00-11-22-33-44-55";
    "Current Capacity" = 97;
    "Delayed Remove Power" = "-1";
    "Is Charging" = 0;
    "Is Present" = 1;
    "Max Capacity" = 100;
    Name = "Test\\U2019s \\"Keyboard\\"; one = two";
    "Power Source ID" = 1234;
    "Power Source State" = "Battery Power";
    "Product ID" = 620;
    "Transport Type" = Bluetooth;
    Type = "Accessory Source";
    "Vendor ID" = 76;
    BatteryHealthCondition = "";
}'''

DEVICE = ('(<_BCPowerSourceController: 0x100000000>) Found device: <BCBatteryDevice: 0x200000000; '
          'vendor = Apple; productIdentifier = 0; parts = (null); identifier = 1234; '
          'matchIdentifier = (null); name = Test; Computer; groupName =InternalBattery-0; '
          'percentCharge = 77; lowBattery = NO; connected = YES; charging = NO; internal = YES; '
          'powerSource = YES; poweredSoureState = Battery Power; transportType = Internal; '
          'accessoryIdentifier = (null); accessoryCategory = Unknown; modelNumber = (null); >')


class BatteryCenterSourceTests(unittest.TestCase):

    def test_shown_keys_fill_their_columns_and_the_rest_go_to_other(self):
        pairs, leftover = module._bc_source_pairs(SOURCE)  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
        self.assertEqual(row, (
            'Test’s "Keyboard"; one = two', 'Accessory Source', 'Bluetooth', 'Battery Power',
            '97', '100', '0', '1', '00-11-22-33-44-55', 'Keyboard', '', '76', '620', '1234',
            'Delayed Remove Power = -1; BatteryHealthCondition = '))

    def test_a_list_value_stays_one_value(self):
        message = 'Found power source: {\n    Name = One;\n    Parts = (\n        Left\n    );\n}'
        pairs, leftover = module._bc_source_pairs(message)  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
        self.assertEqual(row[0], 'One')
        self.assertEqual(row[-1], 'Parts = (Left)')

    def test_a_nested_value_stays_one_value(self):
        message = ('Found power source: {\n    Name = One;\n    Details = {\n        Name = Inner;\n'
                   '        Parts = (\n            Left\n        );\n    };\n    Type = Two;\n}')
        pairs, leftover = module._bc_source_pairs(message)  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
        self.assertEqual(row[:2], ('One', 'Two'))
        self.assertEqual(row[-1], 'Details = {Name = Inner; Parts = ( Left );}')

    def test_an_entry_cut_short_keeps_what_was_logged(self):
        for cut, other in (('    Type = Tw', 'Type = Tw'),
                           ('    Details = {\n        Inner = 1;', 'Details = {Inner = 1;'),
                           ('    Details = {\n        Inner = 1;\n    };', 'Details = {Inner = 1;}')):
            pairs, leftover = module._bc_source_pairs(  # pylint: disable=protected-access
                'Found power source: {\n    Name = One;\n' + cut)
            row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
            self.assertEqual((row[0], row[1], row[-1]), ('One', '', other))

    def test_a_line_that_is_not_a_pair_is_kept(self):
        message = 'Found power source: {\n    Name = One;\n    not a pair\n}'
        pairs, leftover = module._bc_source_pairs(message)  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
        self.assertEqual((row[0], row[-1]), ('One', 'not a pair'))

    def test_a_message_without_braces_is_kept_whole(self):
        pairs, leftover = module._bc_source_pairs('Found power source: <private>')  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
        self.assertEqual(row, ('',) * 14 + ('Found power source: <private>',))

    def test_a_repeated_key_keeps_the_first_in_its_column_and_the_next_in_other(self):
        message = 'Found power source: {\n    Name = One;\n    Name = Two;\n}'
        pairs, leftover = module._bc_source_pairs(message)  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_SOURCE_KEYS)  # pylint: disable=protected-access
        self.assertEqual((row[0], row[-1]), ('One', 'Name = Two'))


class BatteryCenterDeviceTests(unittest.TestCase):

    def test_device_values_fill_their_columns(self):
        pairs, leftover = module._bc_device_pairs(DEVICE)  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_DEVICE_KEYS)  # pylint: disable=protected-access
        self.assertEqual(row, (
            'Test; Computer', 'InternalBattery-0', 'Apple', '(null)', '77', 'NO', 'YES', 'YES',
            'Battery Power', 'Internal', '(null)', 'Unknown', '1234', '0',
            'parts = (null); matchIdentifier = (null); lowBattery = NO; powerSource = YES'))

    def test_a_message_of_another_shape_is_kept_whole(self):
        pairs, leftover = module._bc_device_pairs('Found device: <private>')  # pylint: disable=protected-access
        row = module._bc_row(pairs, leftover, module._BC_DEVICE_KEYS)  # pylint: disable=protected-access
        self.assertEqual(row, ('',) * 14 + ('Found device: <private>',))


if __name__ == '__main__':
    unittest.main()
