"""Windows advanced audit policy from the SECURITY hive (Policy\\PolAdtEv), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsAuditPolicy": {
        "name": "Audit Policy",
        "description": "The audit policy stored in the SECURITY hive, one row per audit subcategory: whether Windows "
                       "was set to record its success events, its failure events, both or neither in the Security "
                       "log.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the PolAdtEv value of the Policy key of the SECURITY hive, where Windows keeps the system "
                 "audit policy that auditpol.exe sets and queries (Microsoft, 'auditpol', "
                 "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/auditpol). No "
                 "published description of the value's layout was relied on: it was measured. The value has a "
                 "12-byte header, in which bytes 4 to 7 hold the number of categories and bytes 8 to 11 the offset "
                 "of a list of 16-bit counts, one per category; from byte 12 it holds 16-bit values, the first of "
                 "which, as many as the counts add up to, are the subcategory settings in category order. One more "
                 "16-bit value follows them and is not reported: it is 0 on build 26200 and holds other numbers on "
                 "the four public images. Value is the stored number and Setting its meaning: 0 No Auditing, 1 "
                 "Success, 2 Failure, 3 Success and Failure. Position is the place of the value, from 1. Category, "
                 "Subcategory and Subcategory GUID are given for the one layout whose positions were established, "
                 "the 60 subcategories in nine categories of Windows 11 build 26200, named as auditpol prints them "
                 "in English. windows11_arm_auditmap_20261010 is the known data that established it, made on a "
                 "build 26200 ARM64 virtual machine on 10 October 2026: the policy was backed up, each of the 60 "
                 "subcategories auditpol lists was set with auditpol, in three rounds, to the setting given by one "
                 "base-4 digit of its number, and the hive and auditpol's listing were saved after each round. In "
                 "every round auditpol's listing equals what was set, and the three values at a position identify "
                 "one subcategory for 59 positions; position 1, whose three values are 0 like those of the spare "
                 "value, is the remaining one, Security State Change. Each position's category is the one auditpol "
                 "lists its subcategory under. Within a category the positions follow the order of the GUIDs, "
                 "except that Special Logon is fifth in Logon/Logoff and Other Object Access Events is fifth in "
                 "Object Access. The policy was then restored, and auditpol's listing after the restore equals the "
                 "one before the test. On the hive saved after the restore and on windows11_arm_known_20261010, a "
                 "read-only capture of the same machine 47 minutes earlier, all 60 rows equal auditpol's listing "
                 "taken in the same second: 47 No Auditing, 9 Success and 4 Success and Failure. Key Last Written "
                 "(UTC) is the last-written time of the PolAdtEv key: in the three rounds it is within one second "
                 "before the time the script recorded after setting that round, so it is when the policy was last "
                 "written, one time for the whole policy and not one for each subcategory. Key Last Written (UTC) "
                 "held one value on all 60 rows of each build 26200 capture and on all 59 rows of each public "
                 "image, every row of a hive coming from the one key. A layout with other counts is reported by "
                 "Position and Value only, and the run log says so: pc_mus_001_win11, af_case2_win10, "
                 "lonewolf_win10 and szechuan_win10 each hold 59 values, with 11 in the second category where "
                 "build 26200 has 12, and Category, Subcategory, Setting and Subcategory GUID were empty on all 59 "
                 "rows of each, because which subcategory each position holds on those builds was not established. "
                 "A value that is not 0 to 3 has an empty Setting, and data without the header's shape gives no "
                 "row and a line in the run log, both tested with constructed input only. The rows show what "
                 "Windows was set to record when the hive was saved, not which events the Security log holds; the "
                 "policy can change, and Windows records event 4719 when it does (Microsoft, '4719(S): System "
                 "audit policy was changed', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4719). "
                 "Per-user audit policy and the other auditing options auditpol manages are not read. Source File "
                 "is the hive. Reading the hive requires the python-registry package; a dirty hive is read after "
                 "its transaction logs are applied, and the run log names each.",
        "paths": ('*/Windows/System32/config/SECURITY',
                  '*/Windows/System32/config/[Ss][Ee][Cc][Uu][Rr][Ii][Tt][Yy].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "clipboard",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 59 rows (positions and values only)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 59 rows (positions and values only)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 59 rows (positions and values only)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 59 rows (positions and values only)",
            "windows11_arm_auditmap_20261010": "Windows 11 build 26200 | 60 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 60 rows",
        },
    },
}

import struct

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, key_written_utc, open_hive, open_key

_GUID_TAIL = '-69AE-11D9-BED3-505054503030}'
_SETTINGS = {0: 'No Auditing', 1: 'Success', 2: 'Failure', 3: 'Success and Failure'}
# (category, subcategory, first eight digits of the subcategory GUID) for each position of the value, for the one
# layout whose positions were established with known data: Windows 11 build 26200, 60 subcategories.
_LAYOUT_60 = (
    ('System', 'Security State Change', '0CCE9210'),
    ('System', 'Security System Extension', '0CCE9211'),
    ('System', 'System Integrity', '0CCE9212'),
    ('System', 'IPsec Driver', '0CCE9213'),
    ('System', 'Other System Events', '0CCE9214'),
    ('Logon/Logoff', 'Logon', '0CCE9215'),
    ('Logon/Logoff', 'Logoff', '0CCE9216'),
    ('Logon/Logoff', 'Account Lockout', '0CCE9217'),
    ('Logon/Logoff', 'IPsec Main Mode', '0CCE9218'),
    ('Logon/Logoff', 'Special Logon', '0CCE921B'),
    ('Logon/Logoff', 'IPsec Quick Mode', '0CCE9219'),
    ('Logon/Logoff', 'IPsec Extended Mode', '0CCE921A'),
    ('Logon/Logoff', 'Other Logon/Logoff Events', '0CCE921C'),
    ('Logon/Logoff', 'Network Policy Server', '0CCE9243'),
    ('Logon/Logoff', 'User / Device Claims', '0CCE9247'),
    ('Logon/Logoff', 'Group Membership', '0CCE9249'),
    ('Logon/Logoff', 'Access Rights', '0CCE924B'),
    ('Object Access', 'File System', '0CCE921D'),
    ('Object Access', 'Registry', '0CCE921E'),
    ('Object Access', 'Kernel Object', '0CCE921F'),
    ('Object Access', 'SAM', '0CCE9220'),
    ('Object Access', 'Other Object Access Events', '0CCE9227'),
    ('Object Access', 'Certification Services', '0CCE9221'),
    ('Object Access', 'Application Generated', '0CCE9222'),
    ('Object Access', 'Handle Manipulation', '0CCE9223'),
    ('Object Access', 'File Share', '0CCE9224'),
    ('Object Access', 'Filtering Platform Packet Drop', '0CCE9225'),
    ('Object Access', 'Filtering Platform Connection', '0CCE9226'),
    ('Object Access', 'Detailed File Share', '0CCE9244'),
    ('Object Access', 'Removable Storage', '0CCE9245'),
    ('Object Access', 'Central Policy Staging', '0CCE9246'),
    ('Privilege Use', 'Sensitive Privilege Use', '0CCE9228'),
    ('Privilege Use', 'Non Sensitive Privilege Use', '0CCE9229'),
    ('Privilege Use', 'Other Privilege Use Events', '0CCE922A'),
    ('Detailed Tracking', 'Process Creation', '0CCE922B'),
    ('Detailed Tracking', 'Process Termination', '0CCE922C'),
    ('Detailed Tracking', 'DPAPI Activity', '0CCE922D'),
    ('Detailed Tracking', 'RPC Events', '0CCE922E'),
    ('Detailed Tracking', 'Plug and Play Events', '0CCE9248'),
    ('Detailed Tracking', 'Token Right Adjusted Events', '0CCE924A'),
    ('Policy Change', 'Audit Policy Change', '0CCE922F'),
    ('Policy Change', 'Authentication Policy Change', '0CCE9230'),
    ('Policy Change', 'Authorization Policy Change', '0CCE9231'),
    ('Policy Change', 'MPSSVC Rule-Level Policy Change', '0CCE9232'),
    ('Policy Change', 'Filtering Platform Policy Change', '0CCE9233'),
    ('Policy Change', 'Other Policy Change Events', '0CCE9234'),
    ('Account Management', 'User Account Management', '0CCE9235'),
    ('Account Management', 'Computer Account Management', '0CCE9236'),
    ('Account Management', 'Security Group Management', '0CCE9237'),
    ('Account Management', 'Distribution Group Management', '0CCE9238'),
    ('Account Management', 'Application Group Management', '0CCE9239'),
    ('Account Management', 'Other Account Management Events', '0CCE923A'),
    ('DS Access', 'Directory Service Access', '0CCE923B'),
    ('DS Access', 'Directory Service Changes', '0CCE923C'),
    ('DS Access', 'Directory Service Replication', '0CCE923D'),
    ('DS Access', 'Detailed Directory Service Replication', '0CCE923E'),
    ('Account Logon', 'Credential Validation', '0CCE923F'),
    ('Account Logon', 'Kerberos Service Ticket Operations', '0CCE9240'),
    ('Account Logon', 'Other Account Logon Events', '0CCE9241'),
    ('Account Logon', 'Kerberos Authentication Service', '0CCE9242'),
)
# the per-category counts the value ends with, for each layout whose positions are established
_LAYOUTS = {(5, 12, 14, 3, 6, 6, 6, 4, 4): _LAYOUT_60}


def policy_values(raw):
    """(values, per-category counts) for the bytes of a PolAdtEv value: a 12-byte header whose last four bytes are
    the offset of the per-category counts and whose four bytes before that are the number of categories, then
    16-bit values, of which the first sum(counts) are the subcategory settings. None when the data does not have
    that shape."""
    if len(raw) < 12:
        return None
    categories, offset = struct.unpack_from('<II', raw, 4)
    if offset < 12 or offset % 2 or categories == 0 or offset + 2 * categories > len(raw):
        return None
    counts = struct.unpack_from(f'<{categories}H', raw, offset)
    values = struct.unpack_from(f'<{(offset - 12) // 2}H', raw, 12)
    if sum(counts) > len(values):
        return None
    return values[:sum(counts)], counts


def policy_rows(raw):
    """The rows for a PolAdtEv value: (category, subcategory, setting, value, position, subcategory GUID), and
    whether the layout is one whose positions are established. None for data that is not an audit policy."""
    parsed = policy_values(raw)
    if parsed is None:
        return None
    values, counts = parsed
    layout = _LAYOUTS.get(counts)
    if layout is None:
        return [('', '', '', value, position, '') for position, value in enumerate(values, 1)], False
    return [(category, name, _SETTINGS.get(value, ''), value, position, '{' + guid + _GUID_TAIL)
            for position, (value, (category, name, guid)) in enumerate(zip(values, layout), 1)], True


@artifact_processor
def windowsAuditPolicy(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Category', 'Subcategory', 'Setting', 'Value',
                    'Position', 'Subcategory GUID', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Audit Policy: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SECURITY')):
        relative = context.get_relative_path(source)
        try:
            key = open_key(open_hive(source, context), 'Policy\\PolAdtEv')
            raw = key.values()[0].raw_data() if key is not None and key.values() else None
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Audit Policy: could not read {relative}: {exc}')
            continue
        if raw is None:
            logfunc(f'Audit Policy: {relative} holds no Policy\\PolAdtEv value')
            continue
        parsed = policy_rows(raw)
        if parsed is None:
            logfunc(f'Audit Policy: the PolAdtEv value of {relative} ({len(raw)} bytes) is not in a known shape')
            continue
        rows, named = parsed
        if not named:
            logfunc(f'Audit Policy: {relative} holds {len(rows)} subcategory values in a layout whose positions are '
                    'not established; they are reported by position, without names')
        written = key_written_utc(key)
        data_list.extend((written,) + row + (relative,) for row in rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
