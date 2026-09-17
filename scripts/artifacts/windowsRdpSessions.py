"""Windows Terminal Services local session event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The event meanings are sourced from public RDP event-log research (see notes).
"""

from datetime import datetime, timezone
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
        "last_update_date": "2026-09-15",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Microsoft-Windows-TerminalServices-"
                 "LocalSessionManager%4Operational.evtx log, named in Source "
                 "File. The session lifecycle events are reported: 21 (Session "
                 "logon succeeded), 22 (Shell start notification received), 23 "
                 "(Session logoff succeeded), 24 (Session has been disconnected) "
                 "and 25 (Session reconnection succeeded); the Event column is "
                 "the description for the Event ID. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, stored in UTC. User, Session "
                 "ID and Address are read from the event as stored. Address is "
                 "LOCAL for a local console logon and a network address for a "
                 "remote (Remote Desktop) session, so it is the field that "
                 "distinguishes the two. Computer is the machine that recorded "
                 "the event. This log covers console sessions as well "
                 "as Remote Desktop, so an entry is not by itself proof of a "
                 "remote connection. A disconnect (24) with no matching logoff "
                 "(23) is a session left running rather than ended. Reading needs "
                 "the python-evtx package (pip install python-evtx). Event "
                 "meanings: Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/tree/main/"
                 "lateral-movement",
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


def _utc_from_iso(value):
    """Parse an EVTX SystemTime (ISO 8601, UTC, variable fraction) to UTC."""
    if not value:
        return ''
    text = value.strip().rstrip('Z')
    fmt = "%Y-%m-%dT%H:%M:%S"
    if '.' in text:
        base, frac = text.split('.', 1)
        text = f"{base}.{(frac + '000000')[:6]}"
        fmt = "%Y-%m-%dT%H:%M:%S.%f"
    try:
        return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def _user_data_field(inner, name):
    if inner is None:
        return ''
    element = inner.find('{*}' + name)
    return element.text if element is not None and element.text else ''


def _session_row(xml_text, relative_source):
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
        computer.text if computer is not None and computer.text else '',
        relative_source)


@artifact_processor
def rdpSessions(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User',
                    'Session ID', 'Address', 'Computer', 'Source File')
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
                        row = _session_row(record.xml(), relative_source)
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
