"""Windows system power (boot, shutdown, sleep) event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The event meanings are sourced from public boot/shutdown event research (notes).
"""

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The System event log records the machine's power timeline from several
# providers: the event log service starting and stopping (a proxy for boot and
# clean shutdown), the kernel starting and shutting down, dirty reboots, sleep,
# and a process initiating a shutdown or restart. An Event ID means different
# things for different providers, so each event is matched on both.

# (provider, event id) -> description. Sourced from Microsoft event messages and
# boot/shutdown event-log research (see notes).
_POWER_EVENTS = {
    ('EventLog', '6005'): 'The event log service was started (system boot)',
    ('EventLog', '6006'): 'The event log service was stopped (clean shutdown)',
    ('EventLog', '6008'): 'The previous system shutdown was unexpected',
    ('Microsoft-Windows-Kernel-General', '12'): 'The operating system started',
    ('Microsoft-Windows-Kernel-General', '13'): 'The operating system is shutting down',
    ('Microsoft-Windows-Kernel-Power', '41'): 'The system rebooted without cleanly shutting down first',
    ('Microsoft-Windows-Kernel-Power', '42'): 'The system is entering sleep',
    ('Microsoft-Windows-Kernel-Power', '109'): 'The kernel power manager initiated a shutdown',
    ('User32', '1074'): 'A process initiated a shutdown or restart',
}

__artifacts_v2__ = {
    "systemPowerEvents": {
        "name": "Windows System Power Events",
        "description": "System power events from the System event log: "
                       "boot, clean and unexpected shutdown, operating system "
                       "start and stop, dirty reboot, sleep, and a process "
                       "initiating a shutdown or restart.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from System.evtx, named in the report's located-at line. Each row is one "
                 "power event, matched on both its provider and Event ID because "
                 "an Event ID means different things for different providers: "
                 "EventLog 6005 (service started, a proxy for boot), 6006 "
                 "(service stopped, a clean shutdown) and 6008 (the previous "
                 "shutdown was unexpected); Kernel-General 12 (operating system "
                 "started) and 13 (operating system shutting down); Kernel-Power "
                 "41 (rebooted without cleanly shutting down first, which its message says could "
                 "be caused if the system stopped responding, crashed, or lost power "
                 "unexpectedly), 42 (entering sleep) and 109 (kernel initiated a "
                 "shutdown); and User32 1074 (a process initiated a shutdown or "
                 "restart). The Event column is the description for that "
                 "provider and Event ID. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, stored in UTC. Detail is populated for "
                 "the 1074 event with the process, action, reason and user as "
                 "the event stores them in its parameters, and is blank for the "
                 "others. Computer is the machine that recorded the event. A 6008 records an "
                 "unexpected shutdown, and Kandi Brian notes that a gap between a 6006 and the "
                 "next 6005 may indicate the system was offline, powered off, or that the logs "
                 "were manipulated. On the registered images three 6005 events had no 6006 since "
                 "the previous 6005; a 6008 and a Kernel-Power 41 came between them only on "
                 "pc_mus_001_win11. Reading needs the python-evtx package "
                 "(pip install python-evtx). Event meanings: Kandi Brian, 'Windows Event Log "
                 "Forensics', https://kandibrian.com/articles/windows-event-log-forensics.html "
                 "(6005, 6006 and 6008); for the others, the provider manifests as registered on "
                 "Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources "
                 "repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-General.xml#L330-L365 "
                 "(12 and 13), "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-Power.xml#L2102-L2376 "
                 "(41 and 42) and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-Power.xml#L3708-L3728 "
                 "(109), and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/User32.xml#L53-L73 "
                 "(1074, whose message places the process in %1, the reason in %3, the shutdown "
                 "type in %5 and the user in %7)",
        "paths": ("*/Windows/System32/winevt/Logs/System.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 107 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 117 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 27 rows",
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


def _positional_data(event_data):
    """The <Data> values of an EventData block in order (User32 uses no names)."""
    if event_data is None:
        return []
    return [(item.text or '') for item in event_data.findall('{*}Data')]


def _shutdown_detail(event_data):
    """Render the notable 1074 parameters: process, action, reason, user."""
    values = _positional_data(event_data)
    labels = ((0, 'Process'), (4, 'Action'), (2, 'Reason'), (6, 'User'))
    parts = [f"{label}: {values[index]}"
             for index, label in labels
             if index < len(values) and values[index]]
    return '; '.join(parts)


def _power_row(xml_text):
    root = ElementTree.fromstring(xml_text)
    system = root.find('{*}System')
    if system is None:
        return None
    event_id = system.find('{*}EventID')
    provider = system.find('{*}Provider')
    event_id = event_id.text.strip() if event_id is not None and event_id.text else ''
    provider_name = provider.get('Name') if provider is not None else ''
    meaning = _POWER_EVENTS.get((provider_name, event_id))
    if meaning is None:
        return None
    time_created = system.find('{*}TimeCreated')
    when = time_created.get('SystemTime') if time_created is not None else ''
    computer = system.find('{*}Computer')
    detail = _shutdown_detail(root.find('{*}EventData')) if event_id == '1074' else ''
    return (
        _utc_from_iso(when), meaning, provider_name, event_id, detail,
        computer.text if computer is not None and computer.text else '')


@artifact_processor
def systemPowerEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event', 'Provider',
                    'Event ID', 'Detail', 'Computer')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows System Power Events: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('system.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            with evtx.Evtx(source) as log:
                for record in log.records():
                    try:
                        row = _power_row(record.xml())
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows System Power Events: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
