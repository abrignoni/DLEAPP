"""Windows service installation event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

Event ID 7045 and its fields are sourced from public research (see the notes).
"""

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The System event log records a Service Control Manager event 7045, "A service
# was installed in the system", whenever a new service is registered. It carries
# the service name, the image path (the service binary or command line), the
# service and start types, and the account the service is configured to run
# under. It is a common record of service-based persistence.

_PROVIDER = 'Service Control Manager'
_EVENT_ID = '7045'

__artifacts_v2__ = {
    "serviceInstalls": {
        "name": "Windows Service Installations",
        "description": "Service installations recorded by Service Control Manager event 7045 in the "
                       "System event log: the service "
                       "name, image path, service and start types, and the "
                       "account the service runs under.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from System.evtx, named in the report's located-at line. Each row is a "
                 "Service Control Manager event 7045, which the provider's message records as 'A "
                 "service was installed in the system.' (Service Control Manager manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Service%20Control%20Manager.xml#L587-L607); "
                 "only that provider and "
                 "Event ID are read, because an Event ID means different things "
                 "for different providers. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, "
                 "counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Service Name, Image "
                 "Path, Service Type, Start Type and Account are the ServiceName, "
                 "ImagePath, ServiceType, StartType and AccountName fields as "
                 "stored; the type and start-type values are the text the event "
                 "carries. Image Path is the service binary or command line as stored. "
                 "Account is the value the event's message labels Service Account (manifest "
                 "cited above), "
                 "not necessarily the account that created the service, and is "
                 "blank when the event stored none. A 7045 event records an installation; "
                 "whether the service still exists is not established by this artifact. Computer "
                 "is the machine that recorded the event. "
                 "Reading needs the python-evtx package (pip install "
                 "python-evtx). Event 7045 and its forensic use: Psmths, "
                 "'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/persistence/evtx-7045-service-install.md",
        "paths": ("*/Windows/System32/winevt/Logs/System.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 44 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 28 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 38 rows",
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


def _service_row(xml_text):
    root = ElementTree.fromstring(xml_text)
    system = root.find('{*}System')
    if system is None:
        return None
    event_id = system.find('{*}EventID')
    provider = system.find('{*}Provider')
    if (event_id is None or event_id.text != _EVENT_ID
            or provider is None or provider.get('Name') != _PROVIDER):
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
    return (
        _utc_from_iso(when), data.get('ServiceName', ''), data.get('ImagePath', ''),
        data.get('ServiceType', ''), data.get('StartType', ''),
        data.get('AccountName', ''),
        computer.text if computer is not None and computer.text else '')


@artifact_processor
def serviceInstalls(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Service Name', 'Image Path',
                    'Service Type', 'Start Type', 'Account', 'Computer')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows Service Installations: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('system.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            with evtx.Evtx(source) as log:
                for record in log.records():
                    try:
                        row = _service_row(record.xml())
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Service Installations: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
