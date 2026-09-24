"""Windows Security event log logon events parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The logon Event ID titles and the Logon Type code table are sourced from
Microsoft's audit documentation (see the artifact notes).
"""

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The Security event log (Security.evtx) records logon activity. This reads the
# logon family: a successful or failed logon, a logoff, and a logon attempted
# with explicit credentials, with the account, logon type, and the source
# network address and workstation where the log recorded them.

# Event ID titles as Microsoft documents them (learn.microsoft.com auditing).
_LOGON_EVENTS = {
    '4624': 'An account was successfully logged on',
    '4625': 'An account failed to log on',
    '4634': 'An account was logged off',
    '4647': 'User initiated logoff',
    '4648': 'A logon was attempted using explicit credentials',
}

# Logon Type codes, verbatim from Microsoft's Event 4624 documentation.
_LOGON_TYPES = {
    '0': 'System', '2': 'Interactive', '3': 'Network', '4': 'Batch',
    '5': 'Service', '7': 'Unlock', '8': 'NetworkCleartext', '9': 'NewCredentials',
    '10': 'RemoteInteractive', '11': 'CachedInteractive',
    '12': 'CachedRemoteInteractive', '13': 'CachedUnlock',
}

__artifacts_v2__ = {
    "securityLogons": {
        "name": "Windows Security Logons",
        "description": "Logon activity from the Security event log: successful "
                       "and failed logons, logoffs, and explicit-credential logon attempts, with the "
                       "account, logon type, and the source "
                       "network address and workstation as recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in the report's located-at line. Only the logon "
                 "family of events is reported: 4624 and 4625 (a logon that "
                 "succeeded or failed), 4634 and 4647 (a logoff), and 4648 (a "
                 "logon attempted with explicit credentials); the Event column "
                 "carries Microsoft's title for each Event ID. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Account Name and "
                 "Account Domain are the TargetUserName and TargetDomainName as "
                 "stored; for 4648 that is the account whose credentials were used (Microsoft, "
                 "'Event 4648', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4648). "
                 "Logon Type is the stored code with Microsoft's label for "
                 "it: 2 Interactive, 3 Network, 4 Batch, 5 Service, 7 Unlock, 8 "
                 "NetworkCleartext, 9 NewCredentials, 10 RemoteInteractive "
                 "(Terminal Services or Remote Desktop), 11 CachedInteractive, "
                 "12 CachedRemoteInteractive, 13 CachedUnlock, 0 System. Source "
                 "IP and Workstation are IpAddress and WorkstationName, which Microsoft notes "
                 "are populated depending on the authentication context and protocol used (for "
                 "example, 'network logons with Kerberos likely have no workstation "
                 "information'), and ::1 or 127.0.0.1 means localhost; on the registered images "
                 "most rows hold the '-' the event stores, both columns are blank for 4634 and "
                 "4647, which carry neither field, and Workstation is blank for 4648, which "
                 "carries no WorkstationName. Logon Process is LogonProcessName. Computer "
                 "is the machine that recorded the event. A successful logon (4624) records a "
                 "logon session created on this computer (Microsoft, 'Event 4624', cited below); "
                 "it does not by "
                 "itself establish the person at the keyboard. Reading needs the "
                 "python-evtx package (pip install python-evtx). Event IDs and the Logon Type "
                 "table: Microsoft, 'Event 4624', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4624; "
                 "the titles of the other events: Microsoft, 'Event 4625', 'Event 4634', 'Event "
                 "4647' and 'Event 4648', "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4625, "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4634, "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4647 "
                 "and "
                 "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4648",
        "paths": ("*/Windows/System32/winevt/Logs/Security.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "log-in",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1576 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1103 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 306 rows",
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


def _logon_type(code):
    code = (code or '').strip()
    if not code:
        return ''
    label = _LOGON_TYPES.get(code)
    return f"{code} ({label})" if label else code


def _system_field(system, name):
    element = system.find('{*}' + name) if system is not None else None
    return element.text if element is not None and element.text else ''


def _event_rows(xml_text):
    """Yield one row tuple from a logon event's XML, or nothing if not a logon."""
    root = ElementTree.fromstring(xml_text)
    system = root.find('{*}System')
    event_id = _system_field(system, 'EventID')
    if event_id not in _LOGON_EVENTS:
        return None
    time_created = system.find('{*}TimeCreated') if system is not None else None
    when = time_created.get('SystemTime') if time_created is not None else ''
    data = {}
    event_data = root.find('{*}EventData')
    if event_data is not None:
        for item in event_data.findall('{*}Data'):
            name = item.get('Name')
            if name:
                data[name] = item.text or ''
    return (
        _utc_from_iso(when), event_id, _LOGON_EVENTS[event_id],
        data.get('TargetUserName', ''), data.get('TargetDomainName', ''),
        _logon_type(data.get('LogonType', '')), data.get('IpAddress', ''),
        data.get('WorkstationName', ''), data.get('LogonProcessName', ''),
        _system_field(system, 'Computer'))


@artifact_processor
def securityLogons(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event',
                    'Account Name', 'Account Domain', 'Logon Type', 'Source IP',
                    'Workstation', 'Logon Process', 'Computer')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows Security Logons: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('security.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            with evtx.Evtx(source) as log:
                for record in log.records():
                    try:
                        row = _event_rows(record.xml())
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Security Logons: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
