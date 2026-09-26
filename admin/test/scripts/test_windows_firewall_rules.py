"""Pin the rule string reading in scripts/artifacts/windowsFirewallRules.py."""
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsFirewallRules as fw  # pylint: disable=wrong-import-position
from scripts.windows_registry import Registry  # pylint: disable=wrong-import-position

HEADERS = ('Rule Name', 'Action', 'Direction', 'Active', 'Protocol', 'Local Ports',
           'Remote Ports', 'Local Addresses', 'Remote Addresses', 'Application', 'Service',
           'Package ID', 'Profiles', 'Rule Group', 'Description', 'Other Fields', 'Rule ID',
           'Version', 'Registry Location')


def row_dict(row):
    return dict(zip(HEADERS, row))


class ParseRuleTest(unittest.TestCase):
    def test_version_columns_and_other_fields_keep_their_order(self):
        version, columns, other = fw.parse_rule(
            'v2.30|Action=Allow|Active=TRUE|Dir=In|Protocol=6|Profile=Domain|Profile=Private|'
            'LPort=445|App=System|Name=@FirewallAPI.dll,-28502|Edge=TRUE|'
            'LUAuth=O:LSD:(A;;CC;;;S-1-5-84-0-0-0-0-0)|')
        self.assertEqual(version, 'v2.30')
        self.assertEqual(columns[:4], [('Action', 'Allow'), ('Active', 'TRUE'),
                                       ('Direction', 'In'), ('Protocol', '6')])
        self.assertIn(('Profiles', 'Private'), columns)
        self.assertEqual(other, ['Edge=TRUE', 'LUAuth=O:LSD:(A;;CC;;;S-1-5-84-0-0-0-0-0)'])

    def test_a_part_without_a_value_and_an_unknown_token_are_kept_as_stored(self):
        version, columns, other = fw.parse_rule('v2.27|LPort2_24=Ply2Disc|stray|Desc|Name=x|')
        self.assertEqual(version, 'v2.27')
        self.assertEqual(columns, [('Rule Name', 'x')])
        self.assertEqual(other, ['LPort2_24=Ply2Disc', 'stray', 'Desc'])

    def test_a_string_without_a_version_is_still_read(self):
        version, columns, other = fw.parse_rule('Action=Block|Dir=Out|')
        self.assertEqual(version, '')
        self.assertEqual(columns, [('Action', 'Block'), ('Direction', 'Out')])
        self.assertEqual(other, [])


class RuleRowTest(unittest.TestCase):
    def test_repeated_tokens_are_joined_and_the_protocol_named(self):
        row = row_dict(fw.rule_row(
            'R1', 'v2.30|Action=Allow|Dir=In|Protocol=17|Profile=Domain|Profile=Private|'
            'LPort=5353|LPort=5355|RA4=LocalSubnet|RA6=LocalSubnet|EmbedCtxt=@g,-1|ICMP6=128:*|'
            'Edge=TRUE|',
            'SYSTEM\\ControlSet001\\x'))
        self.assertEqual(row['Protocol'], '17 (UDP)')
        self.assertEqual(row['Profiles'], 'Domain, Private')
        self.assertEqual(row['Local Ports'], '5353, 5355')
        self.assertEqual(row['Remote Addresses'], 'LocalSubnet, LocalSubnet')
        self.assertEqual(row['Rule Group'], '@g,-1')
        self.assertEqual(row['Other Fields'], 'ICMP6=128:*|Edge=TRUE')
        self.assertEqual((row['Rule ID'], row['Version'], row['Registry Location']),
                         ('R1', 'v2.30', 'SYSTEM\\ControlSet001\\x'))
        self.assertEqual(row['Application'], '')

    def test_protocol_numbers(self):
        self.assertEqual(fw.protocol_text('6'), '6 (TCP)')
        self.assertEqual(fw.protocol_text('58'), '58 (IPv6-ICMP)')
        self.assertEqual(fw.protocol_text('132'), '132')


class _Value:
    def __init__(self, data):
        self._data = data

    def value(self):
        return self._data


class _Key:
    def __init__(self, values=None):
        self._values = values or {}

    def value(self, name):
        if name not in self._values:
            raise Registry.RegistryValueNotFoundException(name)
        return _Value(self._values[name])


class _Hive:
    def __init__(self, keys):
        self._keys = keys

    def open(self, path):
        if path not in self._keys:
            raise Registry.RegistryKeyNotFoundException(path)
        return self._keys[path]


@unittest.skipIf(Registry is None, 'python-registry is not installed')
class RuleKeysTest(unittest.TestCase):
    def test_system_uses_the_current_control_set(self):
        rules = _Key()
        hive = _Hive({'Select': _Key({'Current': 2}),
                      'ControlSet002\\' + fw._SYSTEM_RULES: rules})  # pylint: disable=protected-access
        self.assertEqual(fw.rule_keys(hive, 'SYSTEM'),
                         [('SYSTEM\\ControlSet002\\Services\\SharedAccess\\Parameters\\'
                           'FirewallPolicy\\FirewallRules', rules)])

    def test_software_reads_the_group_policy_key_and_absent_keys_give_nothing(self):
        rules = _Key()
        hive = _Hive({'Policies\\Microsoft\\WindowsFirewall\\FirewallRules': rules})
        self.assertEqual(fw.rule_keys(hive, 'SOFTWARE'),
                         [('SOFTWARE\\Policies\\Microsoft\\WindowsFirewall\\FirewallRules', rules)])
        self.assertEqual(fw.rule_keys(_Hive({}), 'SOFTWARE'), [])
        self.assertEqual(fw.rule_keys(_Hive({}), 'SYSTEM'), [])


if __name__ == '__main__':
    unittest.main()
