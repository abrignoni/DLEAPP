"""Microsoft Defender Antivirus Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Windows Defender/Operational: malware and suspicious
behavior detections and the actions taken on them, quarantine restores and
deletions (1006 to 1011, 1015, 1116 to 1119); protection and configuration
changes and detection history removal (5000, 5001, 5004, 5007, 5010, 5012, 5013,
1013); and antimalware scans (1000, 1001, 1002). Event IDs, messages and field
meanings are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-Windows Defender%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Windows Defender'

# Messages from Microsoft's Defender Antivirus event ID documentation (see notes).
_DETECTION_EVENTS = {
    '1006': 'The antimalware engine found malware or other potentially unwanted software',
    '1007': 'The antimalware platform performed an action to protect your system from '
            'malware or other potentially unwanted software',
    '1008': 'The antimalware platform attempted to perform an action to protect your '
            'system from malware or other potentially unwanted software, but the action failed',
    '1009': 'The antimalware platform restored an item from quarantine',
    '1011': 'The antimalware platform deleted an item from quarantine',
    '1015': 'The antimalware platform detected suspicious behavior',
    '1116': 'The antimalware platform detected malware or other potentially unwanted software',
    '1117': 'The antimalware platform performed an action to protect your system from '
            'malware or other potentially unwanted software',
    '1118': 'The antimalware platform attempted to perform an action to protect your '
            'system from malware or other potentially unwanted software, but the action failed',
    '1119': 'The antimalware platform encountered a critical error when trying to take '
            'action on malware or other potentially unwanted software',
}
_PROTECTION_EVENTS = {
    '5000': 'Real-time protection is enabled',
    '5001': 'Real-time protection is disabled',
    '5004': 'The real-time protection configuration changed',
    '5007': 'The antimalware platform configuration changed',
    '5010': 'Scanning for malware and other potentially unwanted software is disabled',
    '5012': 'Scanning for viruses is disabled',
    '5013': 'Tamper protection blocked a change to Microsoft Defender Antivirus',
    '1013': 'The antimalware platform deleted history of malware and other potentially '
            'unwanted software',
}
_SCAN_EVENTS = {
    '1000': 'An antimalware scan started',
    '1001': 'An antimalware scan finished',
    '1002': 'An antimalware scan was stopped before it finished',
}
# The 1116 to 1119 events carry these field names; 1006 to 1015 name theirs
# differently (see _first below).
_STATE_EVENTS = ('1116', '1117', '1118', '1119')
# Every field the cited manifest defines for 1000, 1001 and 1002. A field a scan
# record carries beyond these is reported in Other Fields, by name, as stored.
_SCAN_FIELDS = frozenset((
    'Product Name', 'Product Version', 'Scan ID', 'Scan Type Index', 'Scan Type',
    'Scan Parameters Index', 'Scan Parameters', 'Domain', 'User', 'SID', 'Scan Resources',
    'Scan Time Hours', 'Scan Time Minutes', 'Scan Time Seconds'))

__artifacts_v2__ = {
    "defenderDetections": {
        "name": "Microsoft Defender Detection Events",
        "description": "Microsoft Defender Antivirus detection, action and "
                       "quarantine events from the Defender Operational log, with "
                       "the threat name, severity, path, process, detection source "
                       "and action each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Windows Defender%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Windows Defender "
                 "records with Event ID 1006, 1007, 1008, 1009, 1011, 1015, 1116, 1117, "
                 "1118 or 1119 are read. Event is the message Microsoft documents for the "
                 "Event ID, the first sentence of it for 1119 (Microsoft Learn, 'Review "
                 "event logs and error codes to troubleshoot issues with Microsoft "
                 "Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260908060019/https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). "
                 "Field names are those of the provider manifest (manifest as registered "
                 "on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L230-L437, "
                 "#L489-L537 and #L640-L989). On 1116 to 1119, Threat Name, Threat ID, "
                 "Severity, Category, Path, Process Name, Detection Source, Detection "
                 "Origin, Detection Type, Action and Status are Threat Name, Threat ID, "
                 "Severity Name, Category Name, Path, Process Name, Source Name, Origin "
                 "Name, Type Name, Action Name and Additional Actions String, the fields "
                 "the 1117 to 1119 messages print as Name, ID, Severity, Category, Path, "
                 "Process Name, Detection Source, Detection Origin, Detection Type, Action "
                 "and Action Status (the 1116 message prints all but the last two); User "
                 "is Detection User on 1116 and Remediation User on 1117 to 1119, the "
                 "field each message prints as User. On 1006 to 1015, User is Domain and "
                 "User joined with a backslash, as their messages print it, and User SID "
                 "is the SID field, which 1116 to 1119 do not carry; Path is Path Found on "
                 "1006 and 1015 and Path on the others; Action is Cleaning Action; Status "
                 "is Execution Status on 1006 and 1015 and Status Description on 1007 and "
                 "1008. Error Code, Error Description, Detection Time (as stored), "
                 "Detection ID, Security Intelligence Version and Engine Version are the "
                 "fields of those names (Security intelligence Version in the manifest). A "
                 "column whose field the manifest does not give an event is blank on that "
                 "event's rows. Every value is reported as stored. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores. No registered image carries a record with any of "
                 "these Event IDs, so this artifact reported no rows on any tested image: "
                 "its field mapping is checked against the manifest and Microsoft's page "
                 "only, and the row building was run only on records constructed for the "
                 "purpose, not on a record Defender wrote. Not reported: the product name "
                 "and version, the ID and index fields beside the names, the FWLink, the "
                 "Status Code, Status Description, State, Execution Name, Pre Execution "
                 "Status and Post Clean Status fields of 1116 to 1119, and on 1015 the "
                 "process ID, security intelligence ID, fidelity, image hash and target "
                 "file fields. A record python-evtx cannot render, or whose XML does not "
                 "parse, is counted in the run log and not reported; every record in this "
                 "log rendered on the registered images. A detection row records what "
                 "Defender logged; it does not by itself establish who placed the file or "
                 "ran the process. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no detection or quarantine events in the Defender Operational log)",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no detection or quarantine events in the Defender Operational log)",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no detection or quarantine events in the Defender Operational log)",
                       },
    },
    "defenderProtectionChanges": {
        "name": "Microsoft Defender Protection and Configuration Changes",
        "description": "Microsoft Defender Antivirus real-time protection, scanning "
                       "and configuration change events and detection history "
                       "removal events from the Defender Operational log, with the "
                       "old and new configuration values 5007 records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Windows Defender%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Windows Defender "
                 "records with Event ID 5000, 5001, 5004, 5007, 5010, 5012, 5013 or 1013 "
                 "are read. Event is the message Microsoft documents for the Event ID "
                 "(Microsoft Learn, 'Review event logs and error codes to troubleshoot "
                 "issues with Microsoft Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260908060019/https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). "
                 "Old Value and New Value are the Old Value and New Value fields of 5007, "
                 "which that page describes as the old and new antivirus configuration "
                 "values. Detail is Feature Name and Configuration on 5004, Changed Type "
                 "and Value on 5013, and Timestamp, Domain and User joined with a "
                 "backslash, and SID on 1013, each as 'name: value'. Product Version is "
                 "the Product Version field. Field names are those of the provider "
                 "manifest (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L589-L613 "
                 "and #L2221-L2380), which gives 5000, 5001, 5010 and 5012 no fields "
                 "beyond the product name and version, so their Old Value, New Value and "
                 "Detail are blank. Every value is reported as stored. 5007 was 18 of the "
                 "21 rows on af_case2_win10, 48 of 51 on pc_mus_001_win11 and 10 of 10 on "
                 "lonewolf_win10; Old Value was filled on 15 of the 18 5007 rows on "
                 "af_case2_win10 and 47 of 48 on pc_mus_001_win11, and New Value on 16 of "
                 "18 and 47 of 48. On lonewolf_win10 every row is 5007, so Event ID and "
                 "Event held one value and Detail is empty. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held two values on af_case2_win10 and one value on "
                 "every row of pc_mus_001_win11 and lonewolf_win10. Not reported: the "
                 "product name, the Feature ID of 5004, and the log's other events (1150, "
                 "1151, 2000, 2001, 2002, 2010, 2011 and 2014 on the registered images). A "
                 "record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported; every record in this log "
                 "rendered on the registered images. A 5007 row records a configuration "
                 "value Defender logged as changed; it does not by itself establish which "
                 "person or program changed it. Reading needs the python-evtx package (pip "
                 "install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "sliders",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 21 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 51 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 10 rows",
                       },
    },
    "defenderScans": {
        "name": "Microsoft Defender Scan Events",
        "description": "Microsoft Defender Antivirus scan started, finished and stopped "
                       "events from the Defender Operational log, with the scan type, "
                       "parameters, duration and account each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Windows Defender%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Windows Defender "
                 "records with Event ID 1000, 1001 or 1002 are read. Event is the message "
                 "Microsoft documents for the Event ID, and Scan ID, Scan Type, Scan "
                 "Parameters, Scan Resources and the scan time follow that page's "
                 "descriptions (Microsoft Learn, 'Review event logs and error codes to "
                 "troubleshoot issues with Microsoft Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260908060019/https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). "
                 "Field names are those of the provider manifest (manifest as registered "
                 "on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L64-L147). "
                 "Scan ID, Scan Type, Scan Parameters and Scan Resources are the fields of "
                 "those names; Scan Time (h:m:s) is Scan Time Hours, Scan Time Minutes and "
                 "Scan Time Seconds of 1001 joined with colons, as stored; User is Domain "
                 "and User joined with a backslash, as the messages print it; User SID is "
                 "the SID field; Product Version is the Product Version field. Other "
                 "Fields (as stored) lists, as 'name: value', any field a record carries "
                 "beyond those the cited manifest defines for 1000 to 1002, other than its "
                 "Unused fields. Other Fields (as stored) was empty on every row of the "
                 "registered images. Every value is reported as stored. Scan Resources, "
                 "which only 1000 carries, was empty on every row of the registered "
                 "images. Scan Type, Scan Parameters, User and User SID each held one "
                 "value on every row of pc_mus_001_win11 and lonewolf_win10, and Product "
                 "Version on every row of lonewolf_win10; the two rows on af_case2_win10 "
                 "carry one Scan ID. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of each registered "
                 "image. Not reported: the product name and the index field beside the "
                 "scan type and parameters. A record python-evtx cannot render, or whose "
                 "XML does not parse, is counted in the run log and not reported; every "
                 "record in this log rendered on the registered images. A scan row records "
                 "a scan Defender logged; the User the record names does not by itself "
                 "establish that a person started the scan. Reading needs the python-evtx "
                 "package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 10 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
                       },
    },
}


def _first(record, *names):
    """The first non-empty named field, as stored."""
    for name in names:
        value = record.get(name)
        if value:
            return value
    return ''


def _domain_user(record):
    domain, user = record.get('Domain'), record.get('User')
    if domain and user:
        return f'{domain}\\{user}'
    return user or domain


def _labelled(record, names):
    """'Name: value' pairs, joined, for the named fields that hold a value."""
    return '; '.join(f'{name}: {record.get(name)}' for name in names if record.get(name))


@artifact_processor
def defenderDetections(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Threat Name',
                    'Threat ID', 'Severity', 'Category', 'Path', 'Process Name', 'User',
                    'User SID', 'Detection Source', 'Detection Origin', 'Detection Type', 'Action',
                    'Status', 'Error Code', 'Error Description',
                    'Detection Time (as stored)', 'Detection ID',
                    'Security Intelligence Version', 'Engine Version', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Microsoft Defender Detection Events',
        event_ids=set(_DETECTION_EVENTS), provider=_PROVIDER)
    data_list = []
    for record in records:
        if record.event_id in _STATE_EVENTS:
            user = record.get('Detection User' if record.event_id == '1116'
                              else 'Remediation User')
            source, origin = record.get('Source Name'), record.get('Origin Name')
            detection_type, action = record.get('Type Name'), record.get('Action Name')
            status = record.get('Additional Actions String')
            path = record.get('Path')
        else:
            user = _domain_user(record)
            source, origin = record.get('Detection Source'), record.get('Detection Origin')
            detection_type, action = record.get('Detection Type'), record.get('Cleaning Action')
            status = _first(record, 'Execution Status', 'Status Description')
            path = _first(record, 'Path Found', 'Path')
        data_list.append((
            record.time, record.event_id, _DETECTION_EVENTS[record.event_id],
            record.get('Threat Name'), record.get('Threat ID'), record.get('Severity Name'),
            record.get('Category Name'), path, record.get('Process Name'), user,
            record.get('SID'), source,
            origin, detection_type, action, status, record.get('Error Code'),
            record.get('Error Description'), record.get('Detection Time'),
            record.get('Detection ID'), record.get('Security intelligence Version'),
            record.get('Engine Version'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def defenderProtectionChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Old Value',
                    'New Value', 'Detail', 'Product Version', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Microsoft Defender Protection and Configuration Changes',
        event_ids=set(_PROTECTION_EVENTS), provider=_PROVIDER)
    data_list = []
    for record in records:
        if record.event_id == '5004':
            detail = _labelled(record, ('Feature Name', 'Configuration'))
        elif record.event_id == '5013':
            detail = _labelled(record, ('Changed Type', 'Value'))
        elif record.event_id == '1013':
            detail = '; '.join(part for part in (
                f"Timestamp: {record.get('Timestamp')}" if record.get('Timestamp') else '',
                f"User: {_domain_user(record)}" if _domain_user(record) else '',
                f"SID: {record.get('SID')}" if record.get('SID') else '') if part)
        else:
            detail = ''
        data_list.append((
            record.time, record.event_id, _PROTECTION_EVENTS[record.event_id],
            record.get('Old Value'), record.get('New Value'), detail,
            record.get('Product Version'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def defenderScans(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Scan ID',
                    'Scan Type', 'Scan Parameters', 'Scan Resources', 'Scan Time (h:m:s)',
                    'User', 'User SID', 'Product Version', 'Other Fields (as stored)',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Microsoft Defender Scan Events', event_ids=set(_SCAN_EVENTS),
        provider=_PROVIDER)
    data_list = []
    for record in records:
        hours, minutes = record.get('Scan Time Hours'), record.get('Scan Time Minutes')
        seconds = record.get('Scan Time Seconds')
        scan_time = f'{hours}:{minutes}:{seconds}' if hours or minutes or seconds else ''
        other = '; '.join(
            f'{name}: {value.strip()}' for name, value in record.fields.items()
            if name and name not in _SCAN_FIELDS and not name.startswith('Unused')
            and value and value.strip())
        data_list.append((
            record.time, record.event_id, _SCAN_EVENTS[record.event_id], record.get('Scan ID'),
            record.get('Scan Type'), record.get('Scan Parameters'),
            record.get('Scan Resources'), scan_time, _domain_user(record), record.get('SID'),
            record.get('Product Version'), other, record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
