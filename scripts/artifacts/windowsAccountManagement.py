"""Windows account management event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The Event ID titles are Microsoft's, from the account-management audit
documentation (see the artifact notes).
"""

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import FastRenderer, log_records

# The Security event log records local account and group administration under
# the account-management audit subcategories: an account being created,
# enabled, disabled, changed, renamed, deleted, locked out or unlocked, a password
# change or reset, a computer account or security group being created, changed
# or deleted, and members being added to or removed from a group.

# Event ID titles as Microsoft documents them (account-management auditing).
_ACCOUNT_EVENTS = {
    '4720': 'A user account was created',
    '4722': 'A user account was enabled',
    '4723': "An attempt was made to change an account's password",
    '4724': "An attempt was made to reset an account's password",
    '4725': 'A user account was disabled',
    '4726': 'A user account was deleted',
    '4738': 'A user account was changed',
    '4740': 'A user account was locked out',
    '4767': 'A user account was unlocked',
    '4781': 'The name of an account was changed',
    '4741': 'A computer account was created',
    '4742': 'A computer account was changed',
    '4743': 'A computer account was deleted',
    '4731': 'A security-enabled local group was created',
    '4735': 'A security-enabled local group was changed',
    '4734': 'A security-enabled local group was deleted',
    '4727': 'A security-enabled global group was created',
    '4737': 'A security-enabled global group was changed',
    '4730': 'A security-enabled global group was deleted',
    '4754': 'A security-enabled universal group was created',
    '4755': 'A security-enabled universal group was changed',
    '4758': 'A security-enabled universal group was deleted',
    '4728': 'A member was added to a security-enabled global group',
    '4729': 'A member was removed from a security-enabled global group',
    '4732': 'A member was added to a security-enabled local group',
    '4733': 'A member was removed from a security-enabled local group',
    '4756': 'A member was added to a security-enabled universal group',
    '4757': 'A member was removed from a security-enabled universal group',
}

__artifacts_v2__ = {
    "accountManagement": {
        "name": "Windows Account Management",
        "description": "Account, computer account and group administration from the Security event log: "
                       "account creation, change, rename, deletion, lockout and password events, computer "
                       "account and security group creation, change and deletion, and group membership changes, "
                       "with the affected account, the member, and the account that requested it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line. Reported are the "
                 "account-lifecycle events (creation, enabling, disabling, "
                 "change, rename (4781), deletion, lockout, unlock, and password change or "
                 "reset), the computer account events (created 4741, changed 4742, deleted 4743), the "
                 "security-enabled group events (local group created 4731, changed 4735, deleted 4734; global "
                 "group 4727, 4737, 4730; universal group 4754, 4755, 4758) and the security-group membership "
                 "changes (a member added to or removed from a global, local or universal group); "
                 "the Event column is Microsoft's title for the Event ID. Event Time (UTC) is "
                 "the record's TimeCreated SystemTime, which scripts/windows_evtx.py renders from the FILETIME "
                 "the record stores with integer arithmetic, counted in UTC and cut to whole microseconds, in "
                 "place of python-evtx 0.8.1's conversion through a floating-point number, which can differ by "
                 "microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Target Account is TargetUserName as stored, which is the "
                 "account for the lifecycle events, the computer account for 4741 to 4743 and the group for the "
                 "group and membership events; for 4781, which stores no TargetUserName, it is NewTargetUserName "
                 "and Old Account Name is OldTargetUserName, the two names Microsoft labels New Account Name and "
                 "Old Account Name (Microsoft, '4781(S) The name of an account was changed.', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4781). "
                 "Old Account Name is blank on every other event, so it was blank on every row of "
                 "hexordia_mvs2025_win11, ou_ransomware_server2022 and pc_mus_001_win11, which hold no 4781. On "
                 "114 of the 115 tested 4781 rows Old Account Name equals Target Account; the other is on "
                 "szechuan_dc01_server2012r2. Member is the MemberName, or the MemberSid "
                 "when the name is not recorded, and is populated for the group "
                 "membership events (the account added or removed). Performed By is "
                 "SubjectUserName, which Microsoft describes as the account that requested the "
                 "operation (for example Microsoft, 'Event 4720', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4720). "
                 "The changed-attribute fields that 4735, 4737, 4738, 4742 and 4755 carry, the SAM account name "
                 "and attributes of the creation events and the target SIDs are not reported; read the record "
                 "for them. Microsoft documents that 4742 can record a change with every changed attribute shown "
                 "as -, and that for a local account 4738 fills the attribute fields that did not change with "
                 "their previous values instead of - "
                 "(https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4742, "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4738). "
                 "Computer is the machine that recorded the event. Computer held one value on "
                 "every row of lonewolf_win10 and pc_mus_001_win11, and two values on "
                 "af_case2_win10 and three on szechuan_win10. On af_case2_win10, lonewolf_win10 and "
                 "szechuan_win10 the account creation (4720), enabling (4722), disabling (4725), "
                 "change (4738), rename (4781), deletion (4726) and password-reset (4724) events, the local group "
                 "creation (4731) and change (4735) events, the global group change (4737) and the global "
                 "and local group membership changes (4728, 4729, 4732, 4733) were all present, and "
                 "on pc_mus_001_win11 only the change (4738) and a local group addition (4732). On "
                 "hexordia_mvs2025_win11 all 4 rows are changes (4738) of one account, with one Target Account, "
                 "Target Domain and Performed By. The computer "
                 "account events 4741 and 4742 were present only on szechuan_dc01_server2012r2 and "
                 "evtx_mitre_attack_4688_cc0, the global group creation event 4727 only on "
                 "szechuan_dc01_server2012r2 and evtx_baseline_nextron_085_win2022_ad, the universal group "
                 "creation event 4754 only on szechuan_dc01_server2012r2, and the universal group change "
                 "4755 on it and on ou_ransomware_server2022. The password-change (4723), lockout (4740) and unlock "
                 "(4767) events and the deletion events 4730, 4734, 4743 and 4758 are read and titled but were "
                 "not present on any tested image; the universal group membership events were present only on "
                 "szechuan_dc01_server2012r2 (4756) and ou_ransomware_server2022 (4757). "
                 "The Security logs of windows11_arm_4688_known and windows11_arm_known_20261001 hold none of "
                 "these events, and alihadi_threatsim_server2019's holds none either. "
                 "A record python-evtx cannot render is skipped and counted in the run log, and the records after "
                 "it are still read; no record of this log failed to render on the tested images. "
                 "Reading needs the python-evtx package (pip install "
                 "python-evtx). Event IDs and titles: Microsoft, 'Audit User Account Management', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/audit-user-account-management "
                 "(the account events), Microsoft, 'Audit Computer Account Management', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/audit-computer-account-management "
                 "(4741 to 4743), and Microsoft, 'Audit Security Group Management', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/audit-security-group-management "
                 "(the group events). The field names of 4781, 4741 to 4743 and the group events are those of the "
                 "provider manifest as registered on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository (https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Security-Auditing.xml#L4105-L4931, "
                 "#L5404-L5639 and #L6464-L6499); the manifests of Windows 10 builds 16299.125, 17763.107 and 19041.208 in that "
                 "repository give the same first message line and fields for each.",
        "paths": ("*/Windows/System32/winevt/Logs/Security.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "user-check",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 84 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 135 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 129 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 137 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the matched files held nothing this "
                                            "artifact reports)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 75 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (the matched files "
                                            "held nothing this artifact reports)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 102 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 4 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 22 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 263 rows",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name) | 80 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 131 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 131 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 79 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 130 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_mitre_attack_4688_cc0": "Public sample logs, Windows builds not recorded | 21 rows",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 0 rows (the matched logs hold no record this artifact reads)",
        },
    },
}


_SYSTEM_TIME = re.compile(
    r'^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})?$')


def _utc_from_iso(value):
    """Parse an EVTX SystemTime to UTC.

    python-evtx renders it as '2018-03-27 09:35:33.595600' (0.7.4) or with a
    '+00:00' offset (0.8.x), and Windows' own rendering uses a T separator and a
    trailing Z. All three are accepted, and a value with no offset is UTC.
    """
    match = _SYSTEM_TIME.match((value or '').strip())
    if not match:
        return ''
    date_part, time_part, fraction, offset = match.groups()
    try:
        parsed = datetime.strptime(f'{date_part} {time_part}', '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return ''
    if fraction:
        parsed = parsed.replace(microsecond=int((fraction + '000000')[:6]))
    if offset and offset != 'Z':
        sign = -1 if offset[0] == '-' else 1
        parsed -= sign * timedelta(hours=int(offset[1:3]), minutes=int(offset[4:6]))
    return parsed.replace(tzinfo=timezone.utc)


def _member(data):
    name = (data.get('MemberName') or '').strip()
    if name and name != '-':
        return name
    return (data.get('MemberSid') or '').strip()


def _account_row(xml_text):
    root = ElementTree.fromstring(xml_text)
    system = root.find('{*}System')
    if system is None:
        return None
    event_id = system.find('{*}EventID')
    event_id = event_id.text.strip() if event_id is not None and event_id.text else ''
    if event_id not in _ACCOUNT_EVENTS:
        return None
    time_created = system.find('{*}TimeCreated')
    when = time_created.get('SystemTime') if time_created is not None else ''
    computer = system.find('{*}Computer')
    data = {}
    event_data = root.find('{*}EventData')
    if event_data is not None:
        for item in event_data.findall('{*}Data'):
            name = item.get('Name')
            if name:
                data[name] = item.text or ''
    # 4781 stores the account's name as OldTargetUserName and NewTargetUserName, not TargetUserName.
    target = data.get('NewTargetUserName', '') if event_id == '4781' else data.get('TargetUserName', '')
    return (
        _utc_from_iso(when), event_id, _ACCOUNT_EVENTS[event_id],
        target, data.get('OldTargetUserName', '') if event_id == '4781' else '',
        data.get('TargetDomainName', ''),
        _member(data), data.get('SubjectUserName', ''),
        computer.text if computer is not None and computer.text else '')


@artifact_processor
def accountManagement(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event',
                    'Target Account', 'Old Account Name', 'Target Domain', 'Member',
                    'Performed By', 'Computer')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows Account Management: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('security.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        unrendered = 0
        try:
            with evtx.Evtx(source) as log:
                renderer = FastRenderer()
                for record in log_records(log, 'Windows Account Management', relative_source):
                    try:
                        xml_text = renderer.xml(record)
                    except Exception:  # pylint: disable=broad-exception-caught
                        unrendered += 1
                        continue
                    try:
                        row = _account_row(xml_text)
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Account Management: could not read {relative_source}: {exc}')
        if unrendered:
            logfunc(f'Windows Account Management: {unrendered} record(s) in {relative_source} could not be '
                    'rendered by python-evtx and were skipped')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
