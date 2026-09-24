"""Windows system power (boot, shutdown, sleep, resume) event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The event meanings are sourced from public boot/shutdown event research and the
providers' manifests (notes). A stored number that a provider's manifest maps to a
name is given that name from the DLL and English .mui on the log's own volume
(_ValueNames).
"""

import collections
import os
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import utc_from_system_time

# The System event log records the machine's power timeline from several
# providers: the event log service starting and stopping (a proxy for boot and
# clean shutdown), the kernel starting and shutting down, dirty reboots, sleep
# and resume, the return from a low power state, and a process initiating a
# shutdown or restart. An Event ID means different things for different
# providers, so each event is matched on both.

_WAKE = ('Microsoft-Windows-Power-Troubleshooter', '1')
_SLEEP = ('Microsoft-Windows-Kernel-Power', '42')
_SHUTDOWN = ('Microsoft-Windows-Kernel-Power', '109')
_BOOT = ('Microsoft-Windows-Kernel-General', '12')

# (provider, event id) -> (the provider's DLL in System32, its GUID, the fields its
# manifest maps to names). The GUIDs are the providers' own, as their manifests
# record them.
_KERNEL_POWER = ('microsoft-windows-kernel-power-events.dll', '331c3b3a-2005-44c2-ac5e-77220c37d6b4')
_NAMED = {
    _SLEEP: _KERNEL_POWER + (('Reason',),),
    _SHUTDOWN: _KERNEL_POWER + (('ShutdownActionType', 'ShutdownReason'),),
    _WAKE: ('pots.dll', 'cdc05e28-c449-49c6-b9d2-88cf761644df', ('WakeSourceType',)),
}

# The Kernel-Power 109 fields shown in Detail, by the names its manifest gives them,
# in template order.
_SHUTDOWN_DETAIL = (
    ('ShutdownActionType', 'Shutdown Action Type'),
    ('ShutdownEventCode', 'Shutdown Event Code'),
    ('ShutdownReason', 'Shutdown Reason'),
)

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
                       "records, the sleep reason, shutdown action and reason, and "
                       "wake source, and a process "
                       "initiating a shutdown or restart.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx; pefile to give stored numbers their names",
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
                 "2 seconds after its Wake Time (that row 87 minutes after). Detail holds the process, "
                 "action, reason and user a 1074 event stores in its parameters; for a 42 event its "
                 "Reason, which the 42 message shows as Sleep Reason; for a 109 event its Shutdown "
                 "Action Type, Shutdown Event Code and Shutdown Reason, the ShutdownActionType, "
                 "ShutdownEventCode and ShutdownReason fields, all three on every build although the "
                 "109 message on builds 16299 and 17763 shows only the reason; and for a "
                 "Power-Troubleshooter 1 event its Wake Source Type, Wake Source Text, Wake Timer "
                 "Owner and Wake Timer Context, each left out when blank; it is blank for the others. "
                 "The providers' manifests bind the 42's Reason, the 109's ShutdownActionType and "
                 "ShutdownReason, and Wake Source Type to value maps of names, and the maps differ "
                 "between Windows builds: the manifests for build 10240 have no 'Predicted Presence "
                 "User Return' wake source, so there Wake Source Type 4 is 'Device -', 5 'Timer -', 6 "
                 "'Timer Set by Legacy Driver' and 7 'Unknown, but possibily due to timer -', and "
                 "their sleep reason map calls 6 'Hibernate from Sleep' where later builds say "
                 "'Hibernate from Sleep - Fixed Timeout'; and the power action map calls 5 'Power "
                 "Action Shutdown Reset' in the DLLs of builds 16299 and 17763 and 'Power Action "
                 "Reboot' in that of build 22621. So these fields are shown as the name followed by "
                 "the number, as in 'System Idle (7)', only when the provider's DLL in System32 on the "
                 "log's own volume (microsoft-windows-kernel-power-events.dll or pots.dll) maps that "
                 "field for the event's version, the English .mui beside the DLL gives the name, and "
                 "the boot record (Kernel-General 12) before the event names the same Windows build as "
                 "the last boot record in the log, so the event was written under the build running at "
                 "the log's last boot. That check does not show that the DLL on disk is the one that "
                 "build ran; on the registered images the file versions of both DLLs and both .mui "
                 "files carry the same build number as the boot records. Otherwise the number is kept "
                 "as stored, and the run log says how many numbers were named or kept and why. The DLL "
                 "and .mui files that named a number are listed in the located-at line. On each "
                 "registered image every boot record in the System log names one build (17763 on "
                 "af_case2_win10, 16299 on lonewolf_win10, 22621 on pc_mus_001_win11) and none of "
                 "these events comes before the first boot record, so every one of these fields was "
                 "named. Sleep Reason was System Idle (7) on both af_case2_win10 rows; System Idle (7) "
                 "on six and Button or Lid (0) on one lonewolf_win10 row; and System Idle (7) on 22, "
                 "Hibernate from Sleep - Fixed Timeout (6) on 14 and Button or Lid (0) on nine "
                 "pc_mus_001_win11 rows. Shutdown Reason was Kernel API (5) and Shutdown Event Code 0 "
                 "on every 109 row; Shutdown Action Type was Power Action Shutdown Reset (5) on 12, "
                 "Power Action Shutdown Off (6) on six and Power Action Shutdown (4) on three "
                 "af_case2_win10 rows; Power Action Shutdown Reset (5) on all three lonewolf_win10 "
                 "rows; and Power Action Reboot (5) on eight and Power Action Shutdown (4) on one "
                 "pc_mus_001_win11 row. Wake Source Type was Power Button (1) on both af_case2_win10 "
                 "rows; Timer - (6) on five and S4 Doze to Hibernate (3) on two lonewolf_win10 rows; "
                 "and Power Button (1) on 15, S4 Doze to Hibernate (3) on 15, Unknown (0) on 14 and "
                 "'Unknown, but possibily due to timer - (8)' (spelled so in the map) on one "
                 "pc_mus_001_win11 row. Wake Source Text, Wake Timer Owner and Wake Timer Context were "
                 "filled only on the six rows whose Wake Source Type is 6 or 8, where the text names a "
                 "scheduled task that requested waking the computer. The other fields of the 42, 107 "
                 "and Power-Troubleshooter 1 events are not reported, among them the target, effective "
                 "and wake-from states, the flags, the programmed wake times, the durations and the "
                 "hibernation counters: none of the three messages shows them, and the providers' DLLs "
                 "on the registered images bind no value map to any of them. Nor are the fields of a "
                 "41 event, among them the bugcheck code and parameters and, on build 22621, two "
                 "suppression states its manifest maps to names: its message shows none of them. "
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
                 "type in %5 and the user in %7). Value maps as published for builds 17134 "
                 "and 10240: repnz, 'etw-providers-docs', "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-17134/Microsoft-Windows-Kernel-Power.xml#L2366-L2371 "
                 "(Reason bound to Pop:MapSleepReason), "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-17134/Microsoft-Windows-Kernel-Power.xml#L580-L594 "
                 "and "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-10240/Microsoft-Windows-Kernel-Power.xml#L296-L305 "
                 "(the sleep reasons), "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-17134/Microsoft-Windows-Power-Troubleshooter.xml#L11-L21 "
                 "and "
                 "https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-10240/Microsoft-Windows-Power-Troubleshooter.xml#L11-L20 "
                 "(the wake sources). The value map layout in a DLL: libyal, 'Windows Event "
                 "manifest binary format', "
                 "https://github.com/libyal/libfwevt/blob/7bfd3403b1bd1476aefbaf2e94b5562cbf724997/documentation/Windows%20Event%20manifest%20binary%20format.asciidoc",
        "paths": ("*/Windows/System32/winevt/Logs/System.evtx",
                  "*/Windows/System32/pots.dll",
                  "*/Windows/System32/en-US/pots.dll.mui",
                  "*/Windows/System32/microsoft-windows-kernel-power-events.dll",
                  "*/Windows/System32/en-US/microsoft-windows-kernel-power-events.dll.mui"),
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


def _shutdown_detail(values):
    """Render the notable 1074 parameters: process, action, reason, user."""
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


def _field_detail(fields, named, labels):
    """Render labelled fields as stored, named ones as given, leaving out blanks."""
    shown = dict(fields, **named)
    return '; '.join(f'{label}: {shown[name]}'
                     for name, label in labels if shown.get(name))


def _number(element):
    """An element's text as an int, or None when it is not a plain number."""
    text = (element.text or '').strip() if element is not None else ''
    return int(text) if text.isdigit() else None


def _power_record(xml_text):
    """The parts of a power event the rows are built from, or None for another event."""
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
    computer = system.find('{*}Computer')
    event_data = root.find('{*}EventData')
    return {
        'kind': (provider_name, event_id),
        'meaning': meaning,
        'time': utc_from_system_time(
            time_created.get('SystemTime') if time_created is not None else ''),
        'record_id': _number(system.find('{*}EventRecordID')),
        'version': _number(system.find('{*}Version')),
        'computer': computer.text if computer is not None and computer.text else '',
        'fields': _named_data(event_data),
        'values': _positional_data(event_data),
    }


def _written_under_last_build(record_id, boots):
    """Whether the boot record before this one names the same build as the log's last.

    `boots` holds (record id, BuildVersion) for every Kernel-General 12 record in the
    log. A record before the first of them, or in a log without one, returns False.
    """
    if record_id is None or not boots:
        return False
    ordered = sorted(boots)
    before = [build for boot_id, build in ordered if boot_id < record_id]
    return bool(before) and before[-1] == ordered[-1][1]


class _ValueNames:
    """Names for the numbers a power event stores, from the value maps on its volume.

    The number in a field that _NAMED lists is shown as 'name (number)' when three
    things hold: the DLL of that provider in the System32 folder beside the log carries
    an event manifest that binds a value map to the field for the event's version, the
    English (en-US) .mui beside that DLL gives the map entry's text, and the boot record
    (Kernel-General 12) before the event names the same Windows build as the last boot
    record in the log, so the event was written under the build that was running when
    the volume was acquired. Otherwise the number is kept as stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _SYSTEM32 = '/windows/system32/'
    _LABEL = 'Windows System Power Events'

    def __init__(self, context):
        self.context = context
        self.files = {}      # (volume root, file name) -> staged path
        self.loaded = {}     # (volume root, DLL) -> (value maps, messages, DLL, .mui)
        self.named = collections.Counter()   # staged path -> numbers it named
        self.kept = collections.Counter()    # why a number was kept as stored
        dlls = sorted({dll for dll, _guid, _fields in _NAMED.values()})
        for path in sorted(str(f) for f in context.get_files_found()):
            if os.path.isdir(path):
                continue
            relative = self._relative(path)
            for dll in dlls:
                for name, suffix in ((dll, self._SYSTEM32 + dll),
                                     (dll + '.mui', f'{self._SYSTEM32}en-us/{dll}.mui')):
                    if relative.endswith(suffix):
                        self.files.setdefault((relative[:-len(suffix)], name), path)

    def _relative(self, path):
        return '/' + self.context.get_relative_path(path).replace('\\', '/').lower()

    def _load(self, root, dll, guid):
        key = (root, dll)
        if key not in self.loaded:
            dll_path = self.files.get((root, dll))
            mui_path = self.files.get((root, dll + '.mui'))
            maps, messages = {}, {}
            if dll_path and mui_path:
                maps = windows_messages.read_event_value_maps(dll_path, guid)
                if maps:
                    messages = windows_messages.read_message_table(mui_path)
            self.loaded[key] = (maps, messages, dll_path, mui_path)
        return self.loaded[key]

    def text(self, source, found, boots, field):
        """The stored number of one of the event's named fields, as 'name (number)' when it can be."""
        dll, guid, _fields = _NAMED[found['kind']]
        value = found['fields'].get(field, '')
        if not value.isdigit():
            return value
        relative = self._relative(source)
        at = relative.find(self._LOG_DIR)
        maps, messages, dll_path, mui_path = (
            self._load(relative[:at], dll, guid) if at >= 0 else ({}, {}, None, None))
        if not maps or not messages:
            self.kept['no value map'] += 1
            return value
        if not _written_under_last_build(found['record_id'], boots):
            self.kept['build'] += 1
            return value
        message_id = maps.get((int(found['kind'][1]), found['version']), {}).get(field, {}) \
            .get(int(value))
        name = messages.get(message_id, '').strip() if message_id is not None else ''
        if not name:
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
            'no value map': 'no DLL with an English .mui beside the log gave a value map'
                            + ('' if windows_messages.pefile else ' (pefile is not installed)'),
            'build': 'the boot record before the event did not name the build of the '
                     "log's last boot record, or no boot record came before it",
            'not in the map': 'the value map has no entry for the number',
        }
        for reason, count in sorted(self.kept.items()):
            logfunc(f'{self._LABEL}: {count} stored number(s) kept as stored: {reasons[reason]}')


def _power_row(found, named):
    """The report row for a parsed power event; named maps its named fields to their text."""
    kind, fields = found['kind'], found['fields']
    sleep_time = wake_time = detail = ''
    if kind == ('User32', '1074'):
        detail = _shutdown_detail(found['values'])
    elif kind == _SLEEP and named.get('Reason'):
        detail = f"Sleep Reason: {named['Reason']}"  # the label the 42 message gives %3
    elif kind == _SHUTDOWN:
        detail = _field_detail(fields, named, _SHUTDOWN_DETAIL)
    elif kind == _WAKE:
        sleep_time = utc_from_system_time(fields.get('SleepTime'))
        wake_time = utc_from_system_time(fields.get('WakeTime'))
        detail = _field_detail(fields, named, _WAKE_DETAIL)
    return (found['time'], sleep_time, wake_time, found['meaning'], kind[0], kind[1], detail,
            found['computer'])


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

    names = _ValueNames(context)
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('system.evtx')]:
        relative_source = context.get_relative_path(source)
        found_here = []
        boots = []
        try:
            with evtx.Evtx(source) as log:
                for record in log.records():
                    try:
                        found = _power_record(record.xml())
                    except ElementTree.ParseError:
                        continue
                    if found is None:
                        continue
                    found_here.append(found)
                    build = found['fields'].get('BuildVersion')
                    if found['kind'] == _BOOT and build and found['record_id'] is not None:
                        boots.append((found['record_id'], build))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows System Power Events: could not read {relative_source}: {exc}')
        for found in found_here:
            named = {field: names.text(source, found, boots, field)
                     for field in _NAMED.get(found['kind'], (None, None, ()))[2]}
            data_list.append(_power_row(found, named))
        if found_here:
            sources.append(source)

    names.log()
    sources.extend(names.files_used())
    return data_headers, data_list, "\n".join(sources)
