"""Windows system power (boot, shutdown, sleep, resume) event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The event meanings are sourced from public boot/shutdown event research and the
providers' manifests (notes).
"""

from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import utc_from_system_time

# The System event log records the machine's power timeline from several
# providers: the event log service starting and stopping (a proxy for boot and
# clean shutdown), the kernel starting and shutting down, dirty reboots, sleep
# and resume, the return from a low power state, and a process initiating a
# shutdown or restart. An Event ID means different things for different
# providers, so each event is matched on both.

_WAKE = ('Microsoft-Windows-Power-Troubleshooter', '1')

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
    ('Microsoft-Windows-Kernel-Power', '107'): 'The system has resumed from sleep',
    ('Microsoft-Windows-Kernel-Power', '109'): 'The kernel power manager initiated a shutdown',
    _WAKE: 'The system has returned from a low power state',
    ('User32', '1074'): 'A process initiated a shutdown or restart',
}

# The Power-Troubleshooter 1 fields shown in Detail, by the names its manifest
# gives them, in template order.
_WAKE_DETAIL = (
    ('WakeSourceType', 'Wake Source Type'),
    ('WakeSourceText', 'Wake Source Text'),
    ('WakeTimerOwner', 'Wake Timer Owner'),
    ('WakeTimerContext', 'Wake Timer Context'),
)

__artifacts_v2__ = {
    "systemPowerEvents": {
        "name": "Windows System Power Events",
        "description": "System power events from the System event log: "
                       "boot, clean and unexpected shutdown, operating system "
                       "start and stop, dirty reboot, sleep and resume, return "
                       "from a low power state with the sleep and wake times it "
                       "records, and a process initiating a shutdown or restart.",
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
                 "unexpectedly), 42 (entering sleep), 107 (resumed from sleep) and 109 "
                 "(kernel initiated a shutdown); Power-Troubleshooter 1 (returned from a "
                 "low power state); and User32 1074 (a process initiated a shutdown or "
                 "restart). The Event column is the description for that "
                 "provider and Event ID. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, stored in UTC. On the registered images the time "
                 "of a 107 record was not the time the system resumed: each of the 54 was "
                 "logged 0.4 to 221 seconds after the 42 before it, and the earliest "
                 "Power-Troubleshooter Wake Time after that 42 came 4 seconds to 9.7 days "
                 "after the 107 was logged. Sleep Time (UTC) and Wake Time (UTC) are the "
                 "SleepTime and WakeTime fields of the Power-Troubleshooter 1 event, which "
                 "its message shows as Sleep Time and Wake Time; they are blank on the "
                 "other rows. "
                 "Sleep Time and Wake Time were the same, or 0.008 second apart, on 18 "
                 "rows: the 17 whose Wake Source Type is 3 (2 on lonewolf_win10 and 15 on "
                 "pc_mus_001_win11) and one lonewolf_win10 row whose Wake Source Type is 6. "
                 "The last 42 before each of those Wake Times was 3.0 hours earlier, so "
                 "equal times there do not mean the system slept for no time. Both fields "
                 "are UTC: on the registered images, whose SYSTEM hives name the Pacific "
                 "(af_case2_win10) and Eastern time zones, every Sleep Time was within 2 "
                 "seconds of the time of a 42 record, and every Power-Troubleshooter event "
                 "but that lonewolf_win10 row whose Wake Source Type is 6 was logged within "
                 "2 seconds after its Wake Time (that row 87 minutes after). Detail holds "
                 "the process, action, reason and user a 1074 event stores in its "
                 "parameters, and for a Power-Troubleshooter 1 event its Wake Source Type, "
                 "Wake Source Text, Wake Timer Owner and Wake Timer Context as stored, each "
                 "left out when blank; it is blank for the others. The Power-Troubleshooter "
                 "1 message shows the wake source as Wake Source Type followed by Wake "
                 "Source Text, and the provider binds Wake Source Type to a value map of "
                 "names. Detail keeps the number because the map differs between Windows "
                 "builds: in the pots.dll on each registered image (builds 16299, 17763 "
                 "and 22621) and in the manifest for build 17134, 0 is 'Unknown', "
                 "1 'Power Button', 2 'Sleep Button', 3 'S4 Doze to Hibernate', "
                 "4 'Predicted Presence User Return', 5 'Device -', 6 'Timer -', "
                 "7 'Timer Set by Legacy Driver' and 8 'Unknown, but possibily due to "
                 "timer -' (spelled so in the map), while the manifest for build 10240 "
                 "has no 'Predicted Presence User Return', so there 4 is 'Device -', "
                 "5 'Timer -', 6 'Timer Set by Legacy Driver' and 7 'Unknown, but "
                 "possibily due to timer -'. On the registered images Wake Source Type was "
                 "1 on both af_case2_win10 rows; 6 on five and 3 on two lonewolf_win10 "
                 "rows; and 1 on 15, 3 on 15, 0 on 14 and 8 on one pc_mus_001_win11 row. "
                 "Wake Source Text, Wake Timer Owner and Wake Timer Context were filled "
                 "only on the six rows whose Wake Source Type is 6 or 8, where the text "
                 "names a scheduled task that requested waking the computer. The other "
                 "fields of the 107 and Power-Troubleshooter 1 events are not reported, "
                 "among them the target, effective and wake-from states, the programmed "
                 "wake times, the durations and the hibernation counters: neither message "
                 "shows them, and the providers' resources on the registered images bind "
                 "no value map to any of them. "
                 "Computer is the machine that recorded the event. Computer held one "
                 "value on every row of pc_mus_001_win11, and two values on af_case2_win10 and "
                 "on lonewolf_win10. A 6008 records an "
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
                 "(41 and 42), "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-Power.xml#L3663-L3683 "
                 "(107), "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Kernel-Power.xml#L3708-L3728 "
                 "(109), "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Power-Troubleshooter.xml#L103-L177 "
                 "(Power-Troubleshooter 1, template versions 2 and 3, the ones on the "
                 "registered images) and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/User32.xml#L53-L73 "
                 "(1074, listed there as 2147484722, which is 1074 with 32768, the Qualifiers "
                 "value on the 1074 records, in the upper 16 bits; its message places the "
                 "process in %1, the reason in %3, the shutdown "
                 "type in %5 and the user in %7). Wake source value maps for builds 17134 "
                 "and 10240: repnz, 'etw-providers-docs', "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-17134/Microsoft-Windows-Power-Troubleshooter.xml#L11-L21 "
                 "and "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-10240/Microsoft-Windows-Power-Troubleshooter.xml#L11-L20",
        "paths": ("*/Windows/System32/winevt/Logs/System.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 197 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 121 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 41 rows",
        },
    },
}


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


def _named_data(event_data):
    """The named <Data> values of an EventData block, stripped, by name."""
    if event_data is None:
        return {}
    return {item.get('Name'): (item.text or '').strip()
            for item in event_data.findall('{*}Data') if item.get('Name')}


def _wake_detail(fields):
    """Render the wake source fields as stored, leaving out the blank ones."""
    return '; '.join(f'{label}: {fields[name]}'
                     for name, label in _WAKE_DETAIL if fields.get(name))


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
    sleep_time = wake_time = detail = ''
    if event_id == '1074':
        detail = _shutdown_detail(root.find('{*}EventData'))
    elif (provider_name, event_id) == _WAKE:
        fields = _named_data(root.find('{*}EventData'))
        sleep_time = utc_from_system_time(fields.get('SleepTime'))
        wake_time = utc_from_system_time(fields.get('WakeTime'))
        detail = _wake_detail(fields)
    return (
        utc_from_system_time(when), sleep_time, wake_time, meaning, provider_name,
        event_id, detail, computer.text if computer is not None and computer.text else '')


@artifact_processor
def systemPowerEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('Sleep Time (UTC)', 'datetime'),
                    ('Wake Time (UTC)', 'datetime'), 'Event', 'Provider', 'Event ID',
                    'Detail', 'Computer')
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
