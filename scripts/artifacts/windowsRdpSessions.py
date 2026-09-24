"""Windows Terminal Services local session event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The event meanings are sourced from public RDP event-log research (see notes).
"""

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The TerminalServices-LocalSessionManager Operational log records interactive
# session activity for both local console and Remote Desktop sessions: a logon,
# the shell starting, a logoff, a disconnect and a reconnect. Each carries the
# user, the session id, and the source address (LOCAL for a console logon, or a
# network address for a remote session).

_SESSION_EVENTS = {
    '21': 'Session logon succeeded',
    '22': 'Shell start notification received',
    '23': 'Session logoff succeeded',
    '24': 'Session has been disconnected',
    '25': 'Session reconnection succeeded',
}

__artifacts_v2__ = {
    "rdpSessions": {
        "name": "Windows Terminal Services Sessions",
        "description": "Interactive and Remote Desktop session activity from the "
                       "TerminalServices-LocalSessionManager log: logon, shell "
                       "start, logoff, disconnect and reconnect, with the user, "
                       "session id, and source address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Microsoft-Windows-TerminalServices-"
                 "LocalSessionManager%4Operational.evtx log, named in the report's located-at "
                 "line. The session lifecycle events are reported: 21 (Session "
                 "logon succeeded), 22 (Shell start notification received), 23 "
                 "(Session logoff succeeded), 24 (Session has been disconnected) "
                 "and 25 (Session reconnection succeeded); the Event column is "
                 "the description for the Event ID. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, "
                 "counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User, Session "
                 "ID and Address are read from the event as stored. Address is the value the "
                 "event's message labels Source Network Address, which logoff (23) records do "
                 "not carry; Psmths describes it as the source IP address of an RDP session "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/network/terminal-services-local-21.md#L38-L39), "
                 "and on the registered images, whose Security logs hold no RemoteInteractive "
                 "(type 10) logon, it was LOCAL on every row that carries it. Computer is the "
                 "machine that recorded the event. Computer held one value on every row of "
                 "af_case2_win10 and pc_mus_001_win11, and two values on lonewolf_win10; User "
                 "held one value on every row of pc_mus_001_win11, and two values on each of the "
                 "other two images. This log covers console sessions as well "
                 "as Remote Desktop, so an entry is not by itself proof of a "
                 "remote connection. On the registered images every disconnect (24) was recorded "
                 "less than a second after a logoff (23) for the same session. Reading needs "
                 "the python-evtx package (pip install python-evtx). Event meanings: the "
                 "provider manifest's message for each (manifest as registered on Windows 11 "
                 "build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-TerminalServices-LocalSessionManager.xml#L294-L386); "
                 "Remote Desktop use of 21 and 24: Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/network/terminal-services-local-21.md "
                 "and "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/network/terminal-services-local-24.md",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 34 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 55 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 12 rows",
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


def _user_data_field(inner, name):
    if inner is None:
        return ''
    element = inner.find('{*}' + name)
    return element.text if element is not None and element.text else ''


def _session_row(xml_text):
    root = ElementTree.fromstring(xml_text)
    system = root.find('{*}System')
    if system is None:
        return None
    event_id = system.find('{*}EventID')
    event_id = event_id.text.strip() if event_id is not None and event_id.text else ''
    if event_id not in _SESSION_EVENTS:
        return None
    time_created = system.find('{*}TimeCreated')
    when = time_created.get('SystemTime') if time_created is not None else ''
    computer = system.find('{*}Computer')
    user_data = root.find('{*}UserData')
    inner = user_data[0] if user_data is not None and len(user_data) else None
    return (
        _utc_from_iso(when), event_id, _SESSION_EVENTS[event_id],
        _user_data_field(inner, 'User'), _user_data_field(inner, 'SessionID'),
        _user_data_field(inner, 'Address'),
        computer.text if computer is not None and computer.text else '')


@artifact_processor
def rdpSessions(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User',
                    'Session ID', 'Address', 'Computer')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows Terminal Services Sessions: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('localsessionmanager%4operational.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            with evtx.Evtx(source) as log:
                for record in log.records():
                    try:
                        row = _session_row(record.xml())
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Terminal Services Sessions: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
