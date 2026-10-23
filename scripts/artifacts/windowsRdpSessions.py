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
from scripts.windows_evtx import FastRenderer, log_records

# The TerminalServices-LocalSessionManager Operational log records interactive
# session activity for both local console and Remote Desktop sessions: a logon,
# the shell starting, a logoff, a disconnect, a reconnect and session arbitration. Each carries the
# user, the session id, and the source address (LOCAL for a console logon, or a
# network address for a remote session).

_SESSION_EVENTS = {
    '21': 'Session logon succeeded',
    '22': 'Shell start notification received',
    '23': 'Session logoff succeeded',
    '24': 'Session has been disconnected',
    '25': 'Session reconnection succeeded',
    '39': 'Session has been disconnected by session',
    '40': 'Session has been disconnected, reason code',
    '41': 'Begin session arbitration',
    '42': 'End session arbitration',
}

__artifacts_v2__ = {
    "rdpSessions": {
        "name": "Windows Terminal Services Sessions",
        "description": "Interactive and Remote Desktop session activity from the "
                       "TerminalServices-LocalSessionManager log: logon, shell "
                       "start, logoff, disconnect, reconnect and session arbitration, with the user, "
                       "session id, disconnect reason code and source address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-17",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Microsoft-Windows-TerminalServices-"
                 "LocalSessionManager%4Operational.evtx log, named in the report's located-at "
                 "line. These events are reported: 21 (Session "
                 "logon succeeded), 22 (Shell start notification received), 23 "
                 "(Session logoff succeeded), 24 (Session has been disconnected), "
                 "25 (Session reconnection succeeded), 39 (Session has been disconnected by session), 40 "
                 "(Session has been disconnected, reason code), 41 (Begin session arbitration) and 42 (End "
                 "session arbitration); the Event column is the first line of the provider message, with its "
                 "'Remote Desktop Services:' prefix and its inserted values left out. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with integer "
                 "arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion "
                 "through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User, Session "
                 "ID and Address are read from the event as stored. 39 and 40 store no user and no address, so "
                 "User and Address are blank on their rows. Session ID is the session the event names: SessionID "
                 "for 21 to 25, 41 and 42, TargetSession for 39 and Session for 40. Disconnected By Session is "
                 "39's Source, the session its message says disconnected the other; on all 11 tested 39 rows it "
                 "equals Session ID. Reason Code (as stored) is 40's Reason; this artifact gives no meaning for "
                 "its values, and the tested rows hold 0 (520), 5 (262), 11 (12), 12 (5), 16 (1), 25 (1) and "
                 "2147500036 (4). Disconnected By Session and Reason Code (as stored) are blank on every row of a "
                 "log with no 39 or 40, as on alihadi_threatsim_server2019 and cfreds_leakage_win7, and "
                 "Disconnected By Session on every row of ou_ransomware_server2022, whose log holds no 39. "
                 "Address is the value the "
                 "event's message labels Source Network Address, which logoff (23) records do "
                 "not carry; Psmths describes it as the source IP address of an RDP session "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/network/terminal-services-local-21.md#L38-L39), "
                 "and on af_case2_win10, lonewolf_win10 and pc_mus_001_win11, whose Security logs "
                 "hold no RemoteInteractive (type 10) logon, it was LOCAL on every row that "
                 "carries it; on szechuan_win10, whose Security log holds one, it was LOCAL on 24 "
                 "of the 27 rows that carry it and an IPv4 address on the other 3. On ou_ransomware_server2022 "
                 "it was an IPv4 address on all 523 rows that carry it, and on szechuan_dc01_server2012r2 LOCAL "
                 "on 23 of 29 and an IPv4 address on 6; the Security logs of those two were not compared. The "
                 "only row of alihadi_threatsim_server2019 is a logoff, so Address is blank there. Computer is "
                 "the "
                 "machine that recorded the event. Computer held one value on every row of "
                 "af_case2_win10 and pc_mus_001_win11, and two values on each of lonewolf_win10 and szechuan_win10. "
                 "Among the rows that carry it, User held one value on pc_mus_001_win11, two on each of "
                 "af_case2_win10 and lonewolf_win10, and five on szechuan_win10. Session ID held one value on all 27 rows of "
                 "alihadi_challenge3_win81. This log covers console sessions as well "
                 "as Remote Desktop, so an entry is not by itself proof of a "
                 "remote connection. On af_case2_win10, alihadi_challenge3_win81, hexordia_mvs2025_win11, "
                 "lonewolf_win10, pc_mus_001_win11, szechuan_dc01_server2012r2 and szechuan_win10 every disconnect "
                 "(24) was recorded less than a second after a logoff (23) for the same session, and on "
                 "cfreds_leakage_win7 3 of the 4; ou_ransomware_server2022 holds 261 disconnects and no logoff. "
                 "A record python-evtx cannot render "
                 "is skipped and counted in the run log, and the records after it are still read; no record of "
                 "this log failed to render on the tested images. Reading needs "
                 "the python-evtx package (pip install python-evtx). Event meanings: the "
                 "provider manifest's message for each (manifest as registered on Windows 11 "
                 "build 22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-TerminalServices-LocalSessionManager.xml#L294-L386 "
                 "and #L492-L553; the manifests of Windows 10 builds 16299.125, 17763.107 and 19041.208 in that "
                 "repository give the same messages and fields for all nine); "
                 "Remote Desktop use of 21 and 24: Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/network/terminal-services-local-21.md "
                 "and "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/network/terminal-services-local-24.md",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 62 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 93 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 22 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 68 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 27 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 1 row",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 35 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 43 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1832 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 77 rows",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the asset name) | 21 rows",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 client (per the asset name) | 37 rows",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 client (per the asset name) | 22 rows",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 client, 2023 capture (per the asset name) | 49 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 on Azure (per the asset name) | 34 rows",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 domain controller (per the asset name) | 19 rows",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the asset name) | 19 rows",
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
    # 39 stores its session as TargetSession and the session that disconnected it as Source; 40 stores its
    # session as Session and a Reason; the others store SessionID (provider manifest, see notes).
    session = (_user_data_field(inner, 'TargetSession') if event_id == '39'
               else _user_data_field(inner, 'Session') if event_id == '40'
               else _user_data_field(inner, 'SessionID'))
    return (
        _utc_from_iso(when), event_id, _SESSION_EVENTS[event_id],
        _user_data_field(inner, 'User'), session,
        _user_data_field(inner, 'Source') if event_id == '39' else '',
        _user_data_field(inner, 'Reason') if event_id == '40' else '',
        _user_data_field(inner, 'Address'),
        computer.text if computer is not None and computer.text else '')


@artifact_processor
def rdpSessions(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User',
                    'Session ID', 'Disconnected By Session', 'Reason Code (as stored)', 'Address',
                    'Computer')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows Terminal Services Sessions: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('localsessionmanager%4operational.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        unrendered = 0
        try:
            with evtx.Evtx(source) as log:
                renderer = FastRenderer()
                for record in log_records(log, 'Windows Terminal Services Sessions', relative_source):
                    try:
                        xml_text = renderer.xml(record)
                    except Exception:  # pylint: disable=broad-exception-caught
                        unrendered += 1
                        continue
                    try:
                        row = _session_row(xml_text)
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Terminal Services Sessions: could not read {relative_source}: {exc}')
        if unrendered:
            logfunc(f'Windows Terminal Services Sessions: {unrendered} record(s) in {relative_source} could not be '
                    'rendered by python-evtx and were skipped')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
