"""Windows Firewall rules from the SYSTEM and SOFTWARE hives, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each value under a FirewallRules key is one rule: the value name is the rule ID and the
data a rule string, a version followed by Token=value fields separated by '|'. The
grammar is Microsoft's MS-GPFAS section 2.2.2.19.
"""

__artifacts_v2__ = {
    "windowsFirewallRules": {
        "name": "Windows Firewall Rules",
        "description": "Windows Firewall rules from the SYSTEM hive's FirewallPolicy\\FirewallRules key "
                       "and the SOFTWARE hive's group policy FirewallRules key, one row per rule.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-27",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the rules under "
                 "Services\\SharedAccess\\Parameters\\FirewallPolicy\\FirewallRules in the SYSTEM "
                 "hive's control set named by the Select key's Current value (ControlSet001 when "
                 "there is none), and under Policies\\Microsoft\\WindowsFirewall\\FirewallRules in "
                 "the SOFTWARE hive, one row per string value. A hive that cannot be opened, and a "
                 "value that cannot be read or is not a string, is logged and skipped. A dirty hive, "
                 "one whose base block's two sequence numbers differ, is read after the entries in its "
                 ".LOG1 and .LOG2 transaction logs that continue its sequence are applied, following "
                 "Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a "
                 "replay that would give a key an earlier last-written time than the hive already "
                 "holds, a check added here beyond the specification; the run log names each hive "
                 "replayed, with the sequence numbers applied, and each dirty hive read as it is, with "
                 "the reason. Microsoft documents the values of "
                 "the SOFTWARE key: the value name is the rule ID and the data a rule string of "
                 "the letter v and a version, then Token=value fields, with '|' after the version "
                 "and after each field (MS-GPFAS section 2.2.2.19, last updated 2021-06-24, "
                 "https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpfas/2efe0b76-7b4a-41ff-9050-1023f8196d16). "
                 "No document was found describing the values of the SYSTEM key. On the tested "
                 "images every one of them began with a version, every field held a token and a "
                 "value, and every token but LPort2_24, on 1 rule of lonewolf_win10, is one that "
                 "section defines. Rule Name is read from Name, Action from Action, Direction from "
                 "Dir, Active from Active, Protocol from Protocol, Local Ports from LPort, "
                 "LPort2_10 and LPort2_20, Remote Ports from RPort and RPort2_10, Local Addresses "
                 "from LA4 and LA6, Remote Addresses from RA4, RA6, RA42 and RA62, Application "
                 "from App, Service from Svc, Package ID from AppPkgId, Profiles from Profile, "
                 "Rule Group from EmbedCtxt and Description from Desc, each value as stored apart "
                 "from the keyword added to Protocol, and a token that appears more than once "
                 "joined with ', '. Every other field, LPort2_24 included, is kept in Other Fields "
                 "as stored, joined with '|'. Rule ID is the value name, Version the rule string's "
                 "version and Registry Location the hive and key a row came from. The MS-GPFAS "
                 "section states that a rule with no Profile token has the profile value "
                 "FW_PROFILE_TYPE_ALL, which MS-FASP defines as all profiles (section 2.2.2, last "
                 "updated 2023-09-20, "
                 "https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fasp/7704e238-174d-4a5e-b809-5f3787dd8acc), "
                 "that the active flag is taken as false when there is no Active token, and that a "
                 "rule with no Protocol token has the protocol value 256, which MS-FASP defines as "
                 "matching any protocol (section 2.2.37, last updated 2022-04-27, "
                 "https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fasp/8c008258-166d-46d4-9090-f2ffaa01be4b). "
                 "MS-FASP also describes the rule ID as uniquely identifying the rule and the "
                 "group as a name other components use to enable or disable groups of rules (same "
                 "page). Protocol is the stored IP protocol number, with IANA's keyword added for "
                 "1, 2, 6, 17, 41, 47 and 58 "
                 "(https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml). A "
                 "Rule Name, Rule Group or Description that begins with '@' is an indirect string, "
                 "which names the file or package holding a text resource and the resource to take "
                 "from it "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/shlwapi/nf-shlwapi-shloadindirectstring.md#L94-L143). "
                 "It is reported as stored and not resolved. On the tested images most Rule Names "
                 "were indirect strings: 435 of 452 on af_case2_win10, 422 of 443 on lonewolf_win10, 437 "
                 "of 484 on pc_mus_001_win11 and 569 of 633 on szechuan_win10. A rule string records no "
                 "time, and no time is reported: Microsoft describes a key's last write time as "
                 "the last time the key or any of its values was modified "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/winreg/nf-winreg-regqueryinfokeyw.md#L140-L141), "
                 "so the rule key's time reflects a change to any rule in it. On pc_mus_001_win11, "
                 "8 Rule IDs are 'TCP Query User' or 'UDP Query User' followed by a GUID and an "
                 "application path, as TCP and UDP pairs for 4 application paths. The Windows "
                 "Firewall event log on that image (Microsoft-Windows-Windows Firewall With "
                 "Advanced Security%4Firewall.evtx) recorded each of them being added with action "
                 "Block by svchost.exe and then modified by dllhost.exe to action Allow, 2 to 51 "
                 "seconds later. What that sequence corresponds to is not established here. That "
                 "log records rule changes with the rule's ID. For the rules in the FirewallRules "
                 "key that it recorded being added or modified (83 on af_case2_win10, 59 on "
                 "lonewolf_win10, 58 on pc_mus_001_win11 and 129 on szechuan_win10), the latest such "
                 "record agreed with "
                 "the rule's Direction, Action and Active on every rule, and with its Rule Name on "
                 "all but 3 rules on af_case2_win10, where the key stores an indirect string and "
                 "the record the text (for example '@FirewallAPI.dll,-30253' and 'Windows Remote "
                 "Management (HTTP-In)'). Velociraptor's Windows.Sys.FirewallRules reads the "
                 "FirewallRules keys under FirewallPolicy, directly below it or deeper, since its "
                 "** glob also matches zero intermediate keys "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/glob/glob.go#L404-L406), "
                 "and extracts the Action, Active, Dir, Protocol, LPort, Name, Desc and App fields "
                 "with one regular expression each "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Sys/FirewallRules.yaml#L10-L11, "
                 "https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Sys/FirewallRules.yaml#L17-L26). "
                 "That glob also reaches FirewallPolicy\\RestrictedServices\\AppIso\\FirewallRules, "
                 "whose app isolation rules are not read here, and neither are the rules under "
                 "RestrictedServices\\Static\\System and RestrictedServices\\Configurable\\System. On "
                 "the tested images those three keys held 310, 195 and 5 values on af_case2_win10, "
                 "277, 186 and 5 on lonewolf_win10, 422, 182 and 3 on pc_mus_001_win11, and 989, 199 and 3 on szechuan_win10. Every "
                 "rule on the tested images was an Allow rule, so a Block rule has not been "
                 "exercised. Active was TRUE on 214 of 452 rules on af_case2_win10, 206 of 443 on lonewolf_win10, 255 of 484 on "
                 "pc_mus_001_win11 and 390 of 633 on szechuan_win10. No tested SOFTWARE hive held "
                 "Policies\\Microsoft\\WindowsFirewall, so reading that key is unexercised. On "
                 "szechuan_win10, the public DFIR Madness Szechuan Sauce desktop image, the SYSTEM hive "
                 "is dirty. Read as it is, its FirewallRules key held 628 rules and was last written at "
                 "03:40:45 UTC on 2020-09-19, and 26 of those rules are ones the Windows Firewall event "
                 "log records as deleted between 05:08:18 and 05:09:25 UTC. With the hive's logs "
                 "replayed the key holds 633 rules and was last written at 05:09:25 UTC: none of the 281 "
                 "rules whose latest record in that log is a deletion is among them, and the 31 rules "
                 "not in the hive as read are each ones whose latest record is an addition, between "
                 "05:08:19 and 05:09:25 UTC.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]',
                  '*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "firewall-check",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 452 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 443 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 484 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 633 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import Registry, current_control_set, found_hives, open_hive, open_key

_SYSTEM_RULES = 'Services\\SharedAccess\\Parameters\\FirewallPolicy\\FirewallRules'
_POLICY_RULES = 'Policies\\Microsoft\\WindowsFirewall\\FirewallRules'

# IANA protocol keywords for the numbers seen on the tested images.
_PROTOCOLS = {'1': 'ICMP', '2': 'IGMP', '6': 'TCP', '17': 'UDP', '41': 'IPv6', '47': 'GRE',
              '58': 'IPv6-ICMP'}

# Report column and the MS-GPFAS tokens it is read from. Every other field goes to Other Fields.
_COLUMNS = (
    ('Rule Name', ('Name',)),
    ('Action', ('Action',)),
    ('Direction', ('Dir',)),
    ('Active', ('Active',)),
    ('Protocol', ('Protocol',)),
    ('Local Ports', ('LPort', 'LPort2_10', 'LPort2_20')),
    ('Remote Ports', ('RPort', 'RPort2_10')),
    ('Local Addresses', ('LA4', 'LA6')),
    ('Remote Addresses', ('RA4', 'RA6', 'RA42', 'RA62')),
    ('Application', ('App',)),
    ('Service', ('Svc',)),
    ('Package ID', ('AppPkgId',)),
    ('Profiles', ('Profile',)),
    ('Rule Group', ('EmbedCtxt',)),
    ('Description', ('Desc',)),
)
_COLUMN_OF = {token: column for column, tokens in _COLUMNS for token in tokens}


def parse_rule(text):
    """The version, the (column, value) pairs and the other fields of a rule string.

    Fields keep the order they have in the string. A field whose token is not read into
    a column, or that has no '=', is kept in the other fields exactly as stored.
    """
    parts = text.split('|')
    version = ''
    if parts and parts[0][:1] in ('v', 'V') and '=' not in parts[0]:
        version = parts.pop(0)
    columns, other = [], []
    for part in parts:
        if not part:
            continue
        token, sep, value = part.partition('=')
        if sep and token in _COLUMN_OF:
            columns.append((_COLUMN_OF[token], value))
        else:
            other.append(part)
    return version, columns, other


def protocol_text(value):
    """A stored protocol number, with its IANA keyword when it is one of _PROTOCOLS."""
    keyword = _PROTOCOLS.get(value)
    return f'{value} ({keyword})' if keyword else value


def rule_row(rule_id, text, location):
    """One report row for a rule string."""
    version, columns, other = parse_rule(text)
    cells = {column: [] for column, _ in _COLUMNS}
    for column, value in columns:
        cells[column].append(protocol_text(value) if column == 'Protocol' else value)
    row = [', '.join(cells[column]) for column, _ in _COLUMNS]
    return tuple(row + ['|'.join(other), rule_id, version, location])


def rule_keys(reg, hive_name):
    """(registry location, key) for each firewall rule key the hive carries."""
    if hive_name == 'SYSTEM':
        path = f'{current_control_set(reg)}\\{_SYSTEM_RULES}'
    else:
        path = _POLICY_RULES
    key = open_key(reg, path)
    return [(f'{hive_name}\\{path}', key)] if key is not None else []


@artifact_processor
def windowsFirewallRules(context):
    data_headers = tuple(column for column, _ in _COLUMNS) + (
        'Other Fields', 'Rule ID', 'Version', 'Registry Location')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Windows Firewall Rules: the python-registry package is not installed')
        return data_headers, data_list, ''
    for hive in sorted(set(found_hives(context, 'SYSTEM', 'SOFTWARE'))):
        hive_name = os.path.basename(hive).upper()
        relative = context.get_relative_path(hive)
        try:
            reg = open_hive(hive, context)
            keys = rule_keys(reg, hive_name)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Firewall Rules: could not read {relative}: {exc}')
            continue
        for location, key in keys:
            for value in key.values():
                try:
                    text = value.value()
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logfunc(f'Windows Firewall Rules: could not read {value.name()} in '
                            f'{relative}: {exc}')
                    continue
                if not isinstance(text, str):
                    logfunc(f'Windows Firewall Rules: {value.name()} in {relative} is not a '
                            f'string ({value.value_type_str()})')
                    continue
                data_list.append(rule_row(value.name(), text, location))
            if hive not in sources:
                sources.append(hive)
    return data_headers, data_list, '\n'.join(sources)
