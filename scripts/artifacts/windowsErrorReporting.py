"""Windows Error Reporting reports and crash events parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Windows Error Reporting (WER) keeps a Report.wer text file for each report under a
WER folder of ProgramData or of a user profile, and logs events about crashes, hangs
and the reports it handles in the Application event log. This reads the Report.wer
files (their fields and the modules each lists as loaded) and the Application Error
(1000), Windows Error Reporting (1001) and Application Hang (1002) events. The field
meanings and time conversions are sourced or measured in the notes.
"""

import os
import re
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import classic_strings, read_event_records

_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
_INDEXED = re.compile(r'^(?P<name>[A-Za-z]+)\[(?P<index>\d+)\]\.?(?P<part>[A-Za-z.]*)$')
_TARGET_SHA1 = re.compile(r'^W:[^!]*!0000(?P<sha1>[0-9A-Fa-f]{40})(?:!|$)')
_HEX_FILETIME = re.compile(r'^(?:0x)?(?P<hex>[0-9A-Fa-f]{16})$')
_LOG = 'Application.evtx'
_REPORT = 'report.wer'

# Unnamed insertion strings of the events on builds whose providers are classic, in
# the order of the %n parameters of each event's message text in wer.dll.mui (1000,
# 1001) and wersvc.dll.mui (1002) on the tested images, which is also the order of
# the named fields the same events carry on build 22621 (see notes).
_CLASSIC_FIELDS = {
    ('Application Error', '1000'): (
        'AppName', 'AppVersion', 'AppTimeStamp', 'ModuleName', 'ModuleVersion',
        'ModuleTimeStamp', 'ExceptionCode', 'FaultingOffset', 'ProcessId',
        'ProcessCreationTime', 'AppPath', 'ModulePath', 'IntegratorReportId',
        'PackageFullName', 'PackageRelativeAppId'),
    ('Windows Error Reporting', '1001'): (
        'Bucket', 'BucketType', 'EventName', 'Response', 'CabId', 'P1', 'P2', 'P3', 'P4',
        'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'AttachedFiles', 'StorePath', 'AnalysisSymbol',
        'Rechecking', 'ReportId', 'ReportStatus', 'HashedBucket', 'CabGuid'),
    ('Application Hang', '1002'): (
        'AppName', 'AppVersion', 'ProcessId', 'StartTime', 'TerminationTime', 'ExeFileName',
        'ReportId', 'PackageFullName', 'PackageRelativeAppId', 'HangType'),
}
_EVENT_NAMES = {('Application Error', '1000'): 'Application Error (1000)',
                ('Application Hang', '1002'): 'Application Hang (1002)'}

__artifacts_v2__ = {
    "werReports": {
        "name": "Windows Error Reporting Reports",
        "description": "Report.wer files Windows Error Reporting kept for crashes, hangs "
                       "and other problem reports: when the event was recorded, the event "
                       "type, the program's name and path, its problem signature and the "
                       "report's identifier.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the Report.wer files in the report folders under Microsoft\\Windows\\WER in "
                 "ProgramData or in a user profile's AppData\\Local, the two locations Velociraptor's "
                 "Windows.System.WindowsErrorReporting artifact reads (Zach Stanford, "
                 "https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/Windows.System.WindowsErrorReporting.yaml#L24-L25); "
                 "Report Folder is the folder holding the file and identifies it, and every report on "
                 "the tested images sat under ProgramData's ReportArchive. No Microsoft documentation "
                 "of the file's fields was found. The file holds one Key=Value pair per line, which "
                 "that artifact also reads "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/Windows.System.WindowsErrorReporting.yaml#L32-L34), "
                 "and each column is the field of that name, as stored: Event Type is EventType, "
                 "Friendly Event Name is FriendlyEventName, App Name is AppName, App Path is AppPath, "
                 "Report Description is ReportDescription, which 5 of the 15 reports on lonewolf_win10 "
                 "and 2 of the 31 on pc_mus_001_win11 carry, Report ID is ReportIdentifier and "
                 "Integrator Report ID is IntegratorReportIdentifier. Problem Signature lists each "
                 "Sig[n] field's name and value in index order, as the file names them. Event Time "
                 "(UTC) and UploadTime (UTC) are EventTime and UploadTime read as FILETIMEs counted in "
                 "UTC. Both machines were set to Eastern time, and on the 7 reports on each image "
                 "whose ReportIdentifier a Windows Error Reporting event (1001) also names, the first "
                 "such event was logged 0.0 to 0.1 seconds (lonewolf_win10) and 0.7 to 2.0 seconds "
                 "(pc_mus_001_win11) after EventTime, where a local-time reading would put it hours "
                 "away; UploadTime fell within 1.1 seconds of one of those events on all 14. What "
                 "UploadTime records was not established, and this artifact does not treat it as proof "
                 "of an upload. Target SHA-1 (first 30 MiB) is the second !-separated part of "
                 "TargetAppId without its leading 0000, when TargetAppId begins W:, the part "
                 "Velociraptor's artifact reads as a SHA-1 "
                 "(https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/Windows.System.WindowsErrorReporting.yaml#L12, "
                 "https://github.com/Velocidex/velociraptor-docs/blob/d88489acae3045e7386f37de4fbce0afde1c146e/content/exchange/artifacts/Windows.System.WindowsErrorReporting.yaml#L46-L48). "
                 "On 26 reports (10 on lonewolf_win10, 16 on pc_mus_001_win11) it equalled the SHA-1 "
                 "of the first 31,457,280 bytes (30 MiB) of the file at App Path on the image, which "
                 "is the whole file when the file is smaller; 11 of those were for a 57,693,184-byte "
                 "program whose whole-file SHA-1 differs. On 8 more the file now at App Path hashed "
                 "differently (OneDrive.exe, Dropbox.exe, the Android emulator's "
                 "qemu-system-x86_64.exe and svchost.exe), so the value describes the file WER saw, "
                 "which need not be the file at that path now. On 5 pc_mus_001_win11 reports, all for "
                 "programs under D:\\Magnet AXIOM, a folder no partition of the image holds, it is "
                 "da39a3ee5e6b4b0d3255bfef95601890afd80709, the SHA-1 of no bytes, which identifies no "
                 "program; 4 pc_mus_001_win11 reports (MoAppCrash and MoAppHang) carry no W: "
                 "TargetAppId and leave it blank. For 14 of the 15 lonewolf_win10 reports, Amcache.hve "
                 "holds an entry for App Path whose FileId is 0000 followed by the same value, the "
                 "value the Amcache Application Files artifact reports as SHA-1. The Report ID of a "
                 "Windows Error Reporting Events or Application Crash and Hang Events row matched the "
                 "Report ID or Integrator Report ID of a report here on the tested images (counts in "
                 "those artifacts' notes). af_case2_win10 holds no Report.wer file. Not read: the "
                 "other files a report folder can hold, the WER Temp folder's WERInternalMetadata.xml, "
                 ".csv and .txt files (one set on lonewolf_win10), memory dumps, and the Windows Error "
                 "Reporting settings in the registry.",
        "paths": ('*/Microsoft/Windows/WER/*/*/Report.wer',),
        "output_types": ["standard"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Report.wer file)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 15 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 31 rows",
        },
    },
    "werLoadedModules": {
        "name": "Windows Error Reporting Loaded Modules",
        "description": "The modules each Windows Error Reporting Report.wer lists as loaded "
                       "in the reported program, one row per module.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per LoadedModule[n] field of each Report.wer (see Windows Error Reporting "
                 "Reports), in index order, with the report's EventTime, AppName and ReportIdentifier. "
                 "Module Path is the value as stored. That the module was loaded in the reported "
                 "program is what the field's name says, and no other record on the tested images was "
                 "compared with it. A report that lists no modules adds no rows: 4 of the 15 reports "
                 "on lonewolf_win10 gave 732 rows, and 22 of the 31 on pc_mus_001_win11 gave 2,272, "
                 "the most from one report being 233 and 229. Event Time (UTC) is EventTime read as a "
                 "FILETIME counted in UTC, as measured in the notes of Windows Error Reporting "
                 "Reports.",
        "paths": ('*/Microsoft/Windows/WER/*/*/Report.wer',),
        "output_types": ["standard"],
        "artifact_icon": "layers",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Report.wer file)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 732 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2272 rows",
        },
    },
    "werReportEvents": {
        "name": "Windows Error Reporting Events",
        "description": "Windows Error Reporting (Event ID 1001) records from the Application event log: the "
                       "event name, problem signature, attached files, the folder the record names for the "
                       "report's files and the report identifier.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Application.evtx, named in the report's located-at line; only records of "
                 "the Windows Error Reporting provider with Event ID 1001 are read. On "
                 "pc_mus_001_win11 (build 22621) the records name their fields: Bucket, BucketType, "
                 "EventName, Response, CabId, P1 to P10, AttachedFiles, StorePath, AnalysisSymbol, "
                 "Rechecking, ReportId, ReportStatus, HashedBucket and CabGuid. On lonewolf_win10 "
                 "(build 16299) they store unnamed strings, read here in the order of the parameters "
                 "of message 1001 in the wer.dll.mui of builds 16299 (lonewolf_win10), 17763 "
                 "(af_case2_win10) and 22621 (pc_mus_001_win11), which is the same order: Fault bucket "
                 "%1, type %2, Event Name %3, Response %4, Cab Id %5, P1 to P10 %6 to %15, Attached "
                 "files %16, 'These files may be available here' %17, Analysis symbol %18, Rechecking "
                 "for solution %19, Report Id %20, Report Status %21 and Hashed bucket %22, with Cab "
                 "Guid %23 from build 17763 (af_case2_win10) on. Event Name is EventName, Problem "
                 "Signature lists P1 to P10 where they hold a value, Attached Files is AttachedFiles, "
                 "Store Path is StorePath, Report ID is ReportId, Report Status is ReportStatus as "
                 "stored and Hashed Bucket is HashedBucket. On the 65 records whose report is on the "
                 "image (18 on lonewolf_win10, 47 on pc_mus_001_win11), P1 to P10 equalled that "
                 "Report.wer's Sig[0] to Sig[9] values, which its Problem Signature names. One report "
                 "can be logged more than once: 18 records named 8 report IDs on lonewolf_win10, and "
                 "53 named 31 on pc_mus_001_win11. Report ID matched a Report.wer's ReportIdentifier "
                 "for 7 of those IDs on each image and its IntegratorReportIdentifier for 1 "
                 "(lonewolf_win10) and 18 (pc_mus_001_win11). User SID is the SID in the record's "
                 "Security element, and it is blank on every lonewolf_win10 row, because those records "
                 "carry none. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113), "
                 "and Record ID is the record's EventRecordID. Not reported: Bucket, BucketType, "
                 "Response, CabId, AnalysisSymbol, Rechecking and CabGuid.",
        "paths": ('*/Windows/System32/winevt/Logs/Application.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Windows Error Reporting 1001 record)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 18 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 53 rows",
        },
    },
    "appCrashHangEvents": {
        "name": "Application Crash and Hang Events",
        "description": "Application Error (Event ID 1000) and Application Hang (Event ID "
                       "1002) records from the Application event log: the program, its "
                       "path, process ID and start time, the faulting module and the "
                       "report identifier.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Application.evtx, named in the report's located-at line; only Application "
                 "Error records with Event ID 1000 and Application Hang records with Event ID 1002 are "
                 "read. On pc_mus_001_win11 (build 22621) the records name their fields: AppName, "
                 "AppVersion, AppTimeStamp, ModuleName, ModuleVersion, ModuleTimeStamp, ExceptionCode, "
                 "FaultingOffset, ProcessId, ProcessCreationTime, AppPath, ModulePath, "
                 "IntegratorReportId, PackageFullName and PackageRelativeAppId for 1000, and AppName, "
                 "AppVersion, ProcessId, StartTime, TerminationTime, ExeFileName, ReportId, "
                 "PackageFullName, PackageRelativeAppId and HangType for 1002. Older builds store "
                 "unnamed strings, read here in the order of the parameters of message 1000 in the "
                 "wer.dll.mui of builds 16299, 17763 and 22621 and of message 1002 in the "
                 "wersvc.dll.mui of builds 16299 and 17763 (lonewolf_win10, af_case2_win10 and "
                 "pc_mus_001_win11), which is the same order: 'Faulting application name: %1, version: "
                 "%2, time stamp: 0x%3' through 'Faulting package-relative application ID: %15', and "
                 "'The program %1 version %2', Process ID %3, Start Time %4, Termination Time %5, "
                 "Application Path %6, Report Id %7, package %8 and %9, and Hang type %10, which "
                 "message 1002 on build 16299 lacks. lonewolf_win10 holds one such unnamed 1000 "
                 "record; no unnamed 1002 record was found, so that reading is unexercised. App Path "
                 "is AppPath (1000) or ExeFileName (1002). Process ID is ProcessId in decimal, with "
                 "its hexadecimal form: the named records store it with 0x, and message 1000 prints "
                 "the unnamed value after 0x, so that value is read as hexadecimal too; an unnamed "
                 "1002 value is shown as stored. Process Start Time (UTC) is ProcessCreationTime "
                 "(1000) or StartTime (1002) read as a hexadecimal FILETIME counted in UTC. Both "
                 "machines were set to Eastern time, and it fell 0 to 2,059 seconds before the "
                 "record's own time on all 18 pc_mus_001_win11 records and 1,585 seconds before it on "
                 "the lonewolf_win10 record, where a local-time reading would put each start after the "
                 "crash or hang it precedes. Exception Code and Fault Offset are ExceptionCode and "
                 "FaultingOffset with a 0x prefix, as message 1000 prints them; they and Module Name, "
                 "Module Version and Module Path are blank on 1002 rows, as Hang Type is on 1000 rows. "
                 "Report ID is IntegratorReportId (1000) or ReportId (1002); each of the 18 on "
                 "pc_mus_001_win11 and the one on lonewolf_win10 matched the "
                 "IntegratorReportIdentifier of a Report.wer and the Report ID of a Windows Error "
                 "Reporting Events row. Package Full Name is PackageFullName, blank on 14 of the 18 "
                 "pc_mus_001_win11 rows and on the lonewolf_win10 row. User SID is the SID in the "
                 "record's Security element, and it is blank on the lonewolf_win10 row, because that "
                 "record carries none. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113), "
                 "and Record ID is the record's EventRecordID. Not reported: AppTimeStamp, "
                 "ModuleTimeStamp, PackageRelativeAppId and TerminationTime.",
        "paths": ('*/Windows/System32/winevt/Logs/Application.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Application Error 1000 or Application Hang 1002 record)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 18 rows",
        },
    },
}


def read_report(data):
    """The key and value pairs of a Report.wer, first occurrence of each key kept."""
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        text = data.decode('utf-16', errors='replace')
    else:
        text = data.decode('utf-8-sig', errors='replace')
    fields = {}
    for line in re.split(r'\r\n|\r|\n', text):
        if '=' in line:
            key, value = line.split('=', 1)
            fields.setdefault(key, value)
    return fields


def filetime(value):
    """A FILETIME stored as decimal text, in UTC; '' for anything else or zero."""
    text = (value or '').strip()
    if not text.isdigit() or int(text) == 0:
        return ''
    try:
        return _FILETIME_EPOCH + timedelta(microseconds=int(text) // 10)
    except OverflowError:
        return ''


def hex_filetime(value):
    """A FILETIME stored as 16 hex digits, with or without 0x, in UTC; '' otherwise."""
    match = _HEX_FILETIME.match((value or '').strip())
    if not match:
        return ''
    number = int(match.group('hex'), 16)
    if number <= 0:
        return ''
    try:
        return _FILETIME_EPOCH + timedelta(microseconds=number // 10)
    except OverflowError:
        return ''


def indexed(fields, name):
    """{index: {part: value}} for the fields named <name>[n] or <name>[n].<part>."""
    found = {}
    for key, value in fields.items():
        match = _INDEXED.match(key)
        if match and match.group('name') == name:
            found.setdefault(int(match.group('index')), {})[match.group('part')] = value
    return found


def problem_signature(fields):
    """'Name: Value' lines of the Sig[n] fields, in index order."""
    lines = []
    for _, parts in sorted(indexed(fields, 'Sig').items()):
        name = parts.get('Name', '')
        if name:
            lines.append(f"{name}: {parts.get('Value', '')}")
    return '\n'.join(lines)


def loaded_modules(fields):
    """The LoadedModule[n] values, in index order."""
    return [parts.get('', '') for _, parts in sorted(indexed(fields, 'LoadedModule').items())]


def target_sha1(target_app_id):
    """The 40 hex digits after 0000 in the second part of a W: TargetAppId, or ''."""
    match = _TARGET_SHA1.match((target_app_id or '').strip())
    return match.group('sha1').lower() if match else ''


def process_id(value, hex_without_prefix):
    """'<decimal> (0x<hex>)' for a stored process ID; the stored text when unreadable."""
    text = (value or '').strip()
    try:
        if text.lower().startswith('0x'):
            number = int(text, 16)
        elif hex_without_prefix:
            number = int(text, 16)
        else:
            return text
    except ValueError:
        return text
    return f'{number} (0x{number:X})'


def hex_code(value):
    """A stored hexadecimal code with a 0x prefix, as stored otherwise."""
    text = (value or '').strip()
    if text and not text.lower().startswith('0x') and re.fullmatch(r'[0-9A-Fa-f]+', text):
        return '0x' + text.upper()
    return text


def event_fields(record):
    """The named fields of a record, or its classic strings labelled by position."""
    names = _CLASSIC_FIELDS.get((record.provider, record.event_id))
    if record.fields or names is None:
        return {key: (value or '').strip() for key, value in record.fields.items()}, False
    values = classic_strings(record.values)
    return {name: (values[i] if i < len(values) else '').strip()
            for i, name in enumerate(names)}, True


def _reports(context):
    """(source, fields) for every Report.wer found, in path order."""
    reports = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isdir(source) or os.path.basename(source).lower() != _REPORT:
            continue
        try:
            with open(source, 'rb') as handle:
                reports.append((source, read_report(handle.read())))
        except OSError as exc:
            logfunc(f'Windows Error Reporting: could not read '
                    f'{context.get_relative_path(source)}: {exc}')
    return reports


@artifact_processor
def werReports(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('UploadTime (UTC)', 'datetime'),
                    'Event Type', 'Friendly Event Name', 'App Name', 'App Path',
                    'Target SHA-1 (first 30 MiB)', 'Problem Signature', 'Report Description',
                    'Report ID', 'Integrator Report ID', 'Report Folder')
    data_list = []
    sources = []
    for source, fields in _reports(context):
        sources.append(source)
        data_list.append((
            filetime(fields.get('EventTime')), filetime(fields.get('UploadTime')),
            fields.get('EventType', ''), fields.get('FriendlyEventName', ''),
            fields.get('AppName', ''), fields.get('AppPath', ''),
            target_sha1(fields.get('TargetAppId')), problem_signature(fields),
            fields.get('ReportDescription', ''), fields.get('ReportIdentifier', ''),
            fields.get('IntegratorReportIdentifier', ''),
            context.get_relative_path(os.path.dirname(source))))
    logfunc(f'Windows Error Reporting Reports: {len(data_list)} Report.wer files read')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def werLoadedModules(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'App Name', 'Module Path', 'Report ID')
    data_list = []
    sources = []
    for source, fields in _reports(context):
        sources.append(source)
        for module in loaded_modules(fields):
            data_list.append((filetime(fields.get('EventTime')), fields.get('AppName', ''),
                              module, fields.get('ReportIdentifier', '')))
    logfunc(f'Windows Error Reporting Loaded Modules: {len(data_list)} modules from '
            f'{len(sources)} Report.wer files')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def werReportEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event Name', 'Problem Signature',
                    'Attached Files', 'Store Path', 'Report ID', 'Report Status',
                    'Hashed Bucket', 'User SID', 'Record ID')
    records, sources = read_event_records(context, _LOG, 'Windows Error Reporting Events',
                                          event_ids={'1001'},
                                          provider='Windows Error Reporting')
    data_list = []
    for record in records:
        fields, _ = event_fields(record)
        signature = '\n'.join(f'P{n}: {fields.get(f"P{n}", "")}' for n in range(1, 11)
                              if fields.get(f'P{n}', ''))
        data_list.append((record.time, fields.get('EventName', ''), signature,
                          fields.get('AttachedFiles', ''), fields.get('StorePath', ''),
                          fields.get('ReportId', ''), fields.get('ReportStatus', ''),
                          fields.get('HashedBucket', ''), record.user_sid, record.record_id))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def appCrashHangEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event', 'App Name', 'App Version',
                    'App Path', 'Process ID', ('Process Start Time (UTC)', 'datetime'),
                    'Module Name', 'Module Version', 'Module Path', 'Exception Code',
                    'Fault Offset', 'Hang Type', 'Report ID', 'Package Full Name',
                    'User SID', 'Record ID')
    records, sources = read_event_records(context, _LOG, 'Application Crash and Hang Events',
                                          event_ids={'1000', '1002'})
    data_list = []
    for record in records:
        key = (record.provider, record.event_id)
        if key not in _EVENT_NAMES:
            continue
        fields, classic = event_fields(record)
        crash = record.event_id == '1000'
        start = fields.get('ProcessCreationTime' if crash else 'StartTime', '')
        data_list.append((
            record.time, _EVENT_NAMES[key], fields.get('AppName', ''),
            fields.get('AppVersion', ''),
            fields.get('AppPath' if crash else 'ExeFileName', ''),
            process_id(fields.get('ProcessId', ''), classic and crash), hex_filetime(start),
            fields.get('ModuleName', ''), fields.get('ModuleVersion', ''),
            fields.get('ModulePath', ''), hex_code(fields.get('ExceptionCode', '')),
            hex_code(fields.get('FaultingOffset', '')), fields.get('HangType', ''),
            fields.get('IntegratorReportId' if crash else 'ReportId', ''),
            fields.get('PackageFullName', ''), record.user_sid, record.record_id))
    return data_headers, data_list, '\n'.join(sources)
