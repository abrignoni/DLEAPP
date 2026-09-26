"""Windows Firewall event log records for DLEAPP: rule changes, setting changes and blocked
applications.

Author: @AlexisBrignoni, Claude.

The records come from the Firewall channel of the Microsoft-Windows-Windows Firewall With
Advanced Security provider. A stored number the provider's manifest maps to a name is given
that name from MPSSVC.dll and its English .mui on the log's own volume (_Names).
"""

__artifacts_v2__ = {
    "windowsFirewallRuleChanges": {
        "name": "Windows Firewall Rule Changes",
        "description": "Firewall rule additions, changes and deletions recorded in the Windows "
                       "Firewall event log, with the rule's fields and the modifying user and "
                       "application as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx; pefile to give stored numbers their names",
        "category": "Windows",
        "notes": "Reads the Firewall channel log, Microsoft-Windows-Windows Firewall With Advanced "
                 "Security%4Firewall.evtx, and reports the records of the "
                 "Microsoft-Windows-Windows Firewall With Advanced Security provider with Event ID "
                 "2004, 2005, 2006, 2032, 2033, 2052, 2059, 2060, 2071 or 2073, one row per "
                 "record. A record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and skipped. Change names each Event ID by the first "
                 "sentence of the message the provider's manifest in MPSSVC.dll gives it, read "
                 "from the English mpssvc.dll.mui on the tested images: 2004 and 2071 'A rule has "
                 "been added to the Windows Defender Firewall exception list.', 2005 and 2073 'A "
                 "rule has been modified in the Windows Defender Firewall exception list.', 2006 "
                 "and 2052 'A rule has been deleted in the Windows Defender Firewall exception "
                 "list.', 2033 and 2059 'All rules have been deleted from the Windows Defender "
                 "Firewall configuration on this computer.', and 2032 and 2060 'Windows Defender "
                 "Firewall has been reset to its default configuration.' The DLLs of builds 16299, "
                 "17763 and 19041 define only the first ID of each pair and the build 22621 DLL "
                 "defines both. The Windows 10 logs held 2004 and 2006 records, af_case2_win10's "
                 "also 2005 records, and the Windows 11 log held 2071, 2073, 2052 and 2059 "
                 "records. Records 2007 and 2072, 'A rule has been listed when the Windows "
                 "Defender Firewall started.', are not reported, and no tested log held one. Time "
                 "(UTC) is the record's TimeCreated. Rule ID, Rule Name, Application Path, Service "
                 "Name, Direction, Protocol, Local Ports, Remote Ports, Local Addresses, Remote "
                 "Addresses, Action, Profiles, Active, Edge Traversal, Rule Group, Origin, Store "
                 "Type, Modifying User, Modifying Application and Error Code are the event data "
                 "fields RuleId, RuleName, ApplicationPath, ServiceName, Direction, Protocol, "
                 "LocalPorts, RemotePorts, LocalAddresses, RemoteAddresses, Action, Profiles, "
                 "Active, EdgeTraversal, EmbeddedContext, Origin, Store Type, ModifyingUser, "
                 "ModifyingApplication and ErrorCode, blank when a record has no such field. Every "
                 "other field that holds a value is kept in Other Fields as 'name: value', joined "
                 "with ' | '. A stored number that the manifest binds to a value map is shown as "
                 "'name (number)', with the name read from the MPSSVC.dll and en-US\\mpssvc.dll.mui "
                 "in the same Windows\\System32 folder as the log. A number the map does not list, "
                 "or a log with no such files beside it, keeps the number alone, and the run log "
                 "counts both. The value maps of the fields these three artifacts name were the "
                 "same in the DLLs of the four tested builds except Store Type, whose build 22621 "
                 "map adds 0 (Unknown) and 11 (MDM). On pc_mus_001_win11, Origin 0 on 12 rule "
                 "modified records and Store Type 12 on the 7 all rules deleted records are not in "
                 "their maps and are kept as numbers. Modifying User is a SID as stored. The "
                 "records are not limited to the FirewallRules key the Windows Firewall Rules "
                 "artifact reads. Of the added or modified records on af_case2_win10, "
                 "lonewolf_win10 and pc_mus_001_win11 (483, 538 and 473), 86, 59 and 85 named a "
                 "Rule ID in that key, 310, 182 and 146 one in "
                 "RestrictedServices\\AppIso\\FirewallRules, 3, 3 and 4 one in "
                 "RestrictedServices\\Configurable\\System, and 84, 294 and 238 one in none of them. "
                 "For the rules in the key with an added or modified record (83, 59 and 58 rules), "
                 "the latest record agreed with that artifact's Direction, Action and Active on "
                 "every rule. On pc_mus_001_win11 each of the 8 rules whose Rule ID begins 'TCP "
                 "Query User' or 'UDP Query User' was recorded as added with action Block by "
                 "svchost.exe and then modified three times by dllhost.exe, 2 to 51 seconds later, "
                 "ending with action Allow and edge traversal Defer to user. The log held 588 "
                 "records from 2019-03-19 12:59:30 to 2023-02-22 23:45:50 UTC on af_case2_win10, "
                 "902 from 2018-03-27 09:36:12 to 2018-04-06 12:26:14 UTC on lonewolf_win10 and "
                 "1,073 from 2022-12-08 02:57:51 to 2023-01-06 16:38:25 UTC on pc_mus_001_win11. "
                 "No tested log held a 2032, 2033 or 2060 record, so those are unexercised. Also "
                 "run on the Szechuan Sauce desktop image (not a registered corpus key), which "
                 "gave 894 rows.",
        "paths": (
            '*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Firewall With Advanced Security%4Firewall.evtx',
            '*/Windows/System32/[Mm][Pp][Ss][Ss][Vv][Cc].[Dd][Ll][Ll]',
            '*/Windows/System32/[Ee][Nn]-[Uu][Ss]/[Mm][Pp][Ss][Ss][Vv][Cc].[Dd][Ll][Ll].[Mm][Uu][Ii]',
        ),
        "output_types": ["standard"],
        "artifact_icon": "firewall-check",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 567 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 892 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 895 rows",
        },
    },
    "windowsFirewallSettingChanges": {
        "name": "Windows Firewall Setting Changes",
        "description": "Windows Firewall setting changes recorded in the Windows Firewall event "
                       "log, with the setting, its new value and the modifying user and "
                       "application as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx; pefile to give stored numbers their names",
        "category": "Windows",
        "notes": "Reads the same log as the Windows Firewall Rule Changes artifact for the "
                 "provider's records with Event ID 2002, 2003, 2082 or 2083, one row per record. "
                 "Change names 2002 and 2083 by the first sentence of their message, 'A Windows "
                 "Defender Firewall setting has changed.', and 2003 and 2082 by theirs, 'A Windows "
                 "Defender Firewall setting in the %1 profile has changed.', where %1 is the "
                 "Profiles field. Profiles, Setting Type, Origin, Modifying User, Modifying "
                 "Application and Error Code are the fields Profiles, SettingType, Origin, "
                 "ModifyingUser, ModifyingApplication and ErrorCode, blank when a record has no "
                 "such field, with mapped numbers named as in that artifact. Modifying User is a "
                 "SID as stored. Setting Value is the field each message prints as the value, "
                 "SettingValueDisplay for 2002 and 2083 and SettingValueString for 2003 and 2082. "
                 "Stored Setting Value (hex) is the SettingValue field, which python-evtx renders "
                 "in Base64 "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1339-L1344), "
                 "decoded to hex, and kept as rendered when it does not decode. Only 2002 records "
                 "were on the tested images: 2 on af_case2_win10, both with Setting Type Current "
                 "Profile (2) and Setting Value Private, and none on lonewolf_win10 or "
                 "pc_mus_001_win11. The Szechuan Sauce desktop image (not a registered corpus key) "
                 "held 4, with Setting Values Private, Domain, Public and Domain. Read as "
                 "little-endian 32-bit numbers their stored values were 2, 1 and 4, the values "
                 "MS-FASP gives the private, domain and public profiles (section 2.2.2, last "
                 "updated 2023-09-20, "
                 "https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fasp/7704e238-174d-4a5e-b809-5f3787dd8acc). "
                 "2003, 2082 and 2083 records are unexercised, and so is the Setting Type map of "
                 "2003 and 2082, which in the provider's manifest names 1 'Enable Windows Defender "
                 "Firewall'.",
        "paths": (
            '*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Firewall With Advanced Security%4Firewall.evtx',
            '*/Windows/System32/[Mm][Pp][Ss][Ss][Vv][Cc].[Dd][Ll][Ll]',
            '*/Windows/System32/[Ee][Nn]-[Uu][Ss]/[Mm][Pp][Ss][Ss][Vv][Cc].[Dd][Ll][Ll].[Mm][Uu][Ii]',
        ),
        "output_types": ["standard"],
        "artifact_icon": "firewall-check",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no 2002, 2003, 2082 or 2083 record in the log)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no 2002, 2003, 2082 or 2083 record in the log)",
        },
    },
    "windowsFirewallBlockedApps": {
        "name": "Windows Firewall Blocked Applications",
        "description": "Windows Firewall event log records of an application blocked from "
                       "accepting incoming connections without the user being notified, with its "
                       "path, port, process ID and reason.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx; pefile to give stored numbers their names",
        "category": "Windows",
        "notes": "Reads the same log as the Windows Firewall Rule Changes artifact for the "
                 "provider's records with Event ID 2011, one row per record. The message the "
                 "provider's manifest gives 2011 begins 'Windows Defender Firewall was unable to "
                 "notify the user that it blocked an application from accepting incoming "
                 "connections on the network.', and no other Event ID in the tested DLLs has that "
                 "message. Application Path, Port, Protocol, IP Version, Process ID and Reason are "
                 "the fields ApplicationPath, Port, Protocol, IPVersion, ProcessId and ReasonCode, "
                 "with mapped numbers named as in that artifact. User is the ModifyingUser field, "
                 "which the message prints as User, a SID as stored. Of the tested images only "
                 "lonewolf_win10 held a 2011 record: an application in Program Files\\WindowsApps "
                 "on TCP port 57122 over IPv4, with Reason 'The application is non interactive "
                 "(2)'.",
        "paths": (
            '*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Firewall With Advanced Security%4Firewall.evtx',
            '*/Windows/System32/[Mm][Pp][Ss][Ss][Vv][Cc].[Dd][Ll][Ll]',
            '*/Windows/System32/[Ee][Nn]-[Uu][Ss]/[Mm][Pp][Ss][Ss][Vv][Cc].[Dd][Ll][Ll].[Mm][Uu][Ii]',
        ),
        "output_types": ["standard"],
        "artifact_icon": "firewall-flame",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no 2011 record in the log)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no 2011 record in the log)",
        },
    },
}

import base64
import binascii
import collections
import os

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-Windows Firewall With Advanced Security%4Firewall.evtx'
_PROVIDER = 'Microsoft-Windows-Windows Firewall With Advanced Security'
_GUID = 'd1bc9aff-2abf-4d71-9146-ecb2a986eb85'
_LOG_DIR = '/windows/system32/winevt/logs/'
_DLL = '/windows/system32/mpssvc.dll'
_MUI = '/windows/system32/en-us/mpssvc.dll.mui'

# Event ID -> the change it records, from the first sentence of the provider's message for
# that event (notes). Windows 11 22H2 writes the second ID of each pair.
_RULE_CHANGES = {
    '2004': 'Rule added', '2071': 'Rule added',
    '2005': 'Rule modified', '2073': 'Rule modified',
    '2006': 'Rule deleted', '2052': 'Rule deleted',
    '2033': 'All rules deleted', '2059': 'All rules deleted',
    '2032': 'Reset to default configuration', '2060': 'Reset to default configuration',
}
_SETTING_CHANGES = {
    '2002': 'Setting changed', '2083': 'Setting changed',
    '2003': 'Profile setting changed', '2082': 'Profile setting changed',
}
_BLOCKED = {'2011': 'Blocked application not notified'}

# Report column -> the event data field it is read from, for the rule change events.
_RULE_COLUMNS = (
    ('Rule ID', 'RuleId'),
    ('Rule Name', 'RuleName'),
    ('Application Path', 'ApplicationPath'),
    ('Service Name', 'ServiceName'),
    ('Direction', 'Direction'),
    ('Protocol', 'Protocol'),
    ('Local Ports', 'LocalPorts'),
    ('Remote Ports', 'RemotePorts'),
    ('Local Addresses', 'LocalAddresses'),
    ('Remote Addresses', 'RemoteAddresses'),
    ('Action', 'Action'),
    ('Profiles', 'Profiles'),
    ('Active', 'Active'),
    ('Edge Traversal', 'EdgeTraversal'),
    ('Rule Group', 'EmbeddedContext'),
    ('Origin', 'Origin'),
    ('Store Type', 'Store Type'),
    ('Modifying User', 'ModifyingUser'),
    ('Modifying Application', 'ModifyingApplication'),
    ('Error Code', 'ErrorCode'),
)
_RULE_FIELDS = {field for _column, field in _RULE_COLUMNS}


class _Names:
    """Names for stored numbers, from the provider's value maps and message table.

    The DLL and .mui used are the ones under the same root as the log, so a log is named
    with the files of the Windows installation that holds it.
    """

    _LABEL = 'Windows Firewall Events'

    def __init__(self, context):
        self.context = context
        self.files = {}      # (volume root, 'dll' or 'mui') -> staged path
        self.loaded = {}     # volume root -> (value maps, messages, DLL, .mui)
        self.named = collections.Counter()   # staged path -> numbers it named
        self.kept = collections.Counter()    # why a number was kept as stored
        for path in sorted(str(f) for f in context.get_files_found()):
            if os.path.isdir(path):
                continue
            relative = self._relative(path)
            for kind, suffix in (('dll', _DLL), ('mui', _MUI)):
                if relative.endswith(suffix):
                    self.files.setdefault((relative[:-len(suffix)], kind), path)

    def _relative(self, path):
        return '/' + self.context.get_relative_path(path).replace('\\', '/').lower()

    def _load(self, root):
        if root not in self.loaded:
            dll_path = self.files.get((root, 'dll'))
            mui_path = self.files.get((root, 'mui'))
            maps, messages = {}, {}
            if dll_path and mui_path:
                maps = windows_messages.read_event_value_maps(dll_path, _GUID)
                if maps:
                    messages = windows_messages.read_message_table(mui_path)
            self.loaded[root] = (maps, messages, dll_path, mui_path)
        return self.loaded[root]

    def text(self, record, field):
        """A stored field, as 'name (number)' when the provider's value map names it."""
        value = record.get(field)
        if not value.isdigit():
            return value
        relative = self._relative(record.source)
        at = relative.find(_LOG_DIR)
        maps, messages, dll_path, mui_path = (
            self._load(relative[:at]) if at >= 0 else ({}, {}, None, None))
        if not maps or not messages:
            self.kept['no value map'] += 1
            return value
        try:
            key = (int(record.event_id), int(record.version or 0))
        except ValueError:
            self.kept['not in the map'] += 1
            return value
        message_id = maps.get(key, {}).get(field, {}).get(int(value))
        name = messages.get(message_id, '').strip() if message_id is not None else ''
        if not name:
            if field in maps.get(key, {}):
                self.kept['not in the map'] += 1
            return value
        self.named[dll_path] += 1
        self.named[mui_path] += 1
        return f'{name} ({value})'

    def files_used(self):
        """The DLL and .mui files that named at least one number, for the source path."""
        return sorted(self.named)

    def log(self):
        for path, count in sorted(self.named.items()):
            logfunc(f'{self._LABEL}: {count} stored number(s) named with '
                    f'{self.context.get_relative_path(path)}')
        reasons = {
            'no value map': 'no MPSSVC.dll with an English .mui beside the log gave a value map'
                            + ('' if windows_messages.pefile else ' (pefile is not installed)'),
            'not in the map': "the field's value map has no entry for the number",
        }
        for reason, count in sorted(self.kept.items()):
            logfunc(f'{self._LABEL}: {count} stored number(s) kept as stored: {reasons[reason]}')


def binary_hex(value):
    """A binary event data item, which python-evtx renders in Base64, as hex."""
    try:
        return base64.b64decode(value, validate=True).hex()
    except (binascii.Error, ValueError):
        return value


def _read(context, event_ids):
    records, sources = read_event_records(context, _LOG, 'Windows Firewall Events',
                                          event_ids=set(event_ids), provider=_PROVIDER)
    return records, sources


def _sources(sources, names):
    return '\n'.join(list(sources) + names.files_used())


def rule_change_row(record, names):
    """The Windows Firewall Rule Changes row for one record."""
    cells = [names.text(record, field) for _column, field in _RULE_COLUMNS]
    other = [f'{field}: {names.text(record, field)}' for field in record.fields
             if field not in _RULE_FIELDS and record.get(field)]
    return (record.time, _RULE_CHANGES[record.event_id], *cells, ' | '.join(other),
            record.event_id, record.record_id)


def setting_change_row(record, names):
    """The Windows Firewall Setting Changes row for one record."""
    shown = record.get('SettingValueDisplay') or record.get('SettingValueString')
    return (record.time, _SETTING_CHANGES[record.event_id], names.text(record, 'Profiles'),
            names.text(record, 'SettingType'), shown, names.text(record, 'Origin'),
            record.get('ModifyingUser'), record.get('ModifyingApplication'),
            record.get('ErrorCode'), binary_hex(record.get('SettingValue')), record.event_id,
            record.record_id)


def blocked_app_row(record, names):
    """The Windows Firewall Blocked Applications row for one record."""
    return (record.time, record.get('ApplicationPath'), record.get('Port'),
            names.text(record, 'Protocol'), names.text(record, 'IPVersion'),
            record.get('ProcessId'), names.text(record, 'ReasonCode'),
            record.get('ModifyingUser'), record.event_id, record.record_id)


@artifact_processor
def windowsFirewallRuleChanges(context):
    data_headers = ((('Time (UTC)', 'datetime'), 'Change')
                    + tuple(column for column, _field in _RULE_COLUMNS)
                    + ('Other Fields', 'Event ID', 'Record ID'))
    records, sources = _read(context, _RULE_CHANGES)
    names = _Names(context)
    data_list = [rule_change_row(record, names) for record in records]
    names.log()
    return data_headers, data_list, _sources(sources, names)


@artifact_processor
def windowsFirewallSettingChanges(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Change', 'Profiles', 'Setting Type',
                    'Setting Value', 'Origin', 'Modifying User', 'Modifying Application',
                    'Error Code', 'Stored Setting Value (hex)', 'Event ID', 'Record ID')
    records, sources = _read(context, _SETTING_CHANGES)
    names = _Names(context)
    data_list = [setting_change_row(record, names) for record in records]
    names.log()
    return data_headers, data_list, _sources(sources, names)


@artifact_processor
def windowsFirewallBlockedApps(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Application Path', 'Port', 'Protocol',
                    'IP Version', 'Process ID', 'Reason', 'User', 'Event ID', 'Record ID')
    records, sources = _read(context, _BLOCKED)
    names = _Names(context)
    data_list = [blocked_app_row(record, names) for record in records]
    names.log()
    return data_headers, data_list, _sources(sources, names)

