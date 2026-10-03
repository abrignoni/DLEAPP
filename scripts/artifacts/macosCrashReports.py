"""Crash reports macOS keeps in Library/Logs/DiagnosticReports, for DLEAPP: the .ips files whose
metadata names bug_type 309 and the text .crash reports.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosCrashReports": {
        "name": "Crash Reports",
        "description": "Crash reports in Library/Logs/DiagnosticReports folders: crash and launch "
                       "time in UTC, process, PID, path, bundle identifier, version, parent process, "
                       "user ID, exception, termination reason, OS version, incident ID and crash "
                       "reporter key.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Crash Reports (macOS)",
        "notes": "Reads the .ips and .crash files in a Library/Logs/DiagnosticReports folder and the "
                 "folders below it, such as Retired, one row per crash report. Apple's page 'Interpreting "
                 "the JSON format of a crash report' "
                 "(https://developer.apple.com/documentation/xcode/interpreting-the-json-format-of-a-crash-report) "
                 "describes an .ips file as a JSON metadata object on its first line followed by the "
                 "report, and names bug_type 309 as the type of the crash reports it describes. An .ips of "
                 "another bug_type, whose first line is not JSON, or whose report is JSON other than an "
                 "object is counted in the run log and not read; when the rest of a 309 file is not JSON "
                 "it is read as a text report, with the metadata line filling OS Version and Incident ID "
                 "where the text leaves them out. A text report is read by its field labels (Process, "
                 "Path, Identifier, Version, Parent Process, User ID, Date/Time, Launch Time, OS Version, "
                 "Exception Type, Termination Reason, Incident Identifier and CrashReporter Key), taking "
                 "the first line with each label, and a .crash file with none of them is counted and not "
                 "read. Crash Time (UTC) and Launch Time (UTC) come from captureTime and procLaunch, which "
                 "Apple defines as the date and time of the crash and of the process launch, or from the "
                 "text Date/Time and Launch Time fields, which Apple's page 'Examining the fields in a "
                 "crash report' "
                 "(https://developer.apple.com/documentation/xcode/examining-the-fields-in-a-crash-report) "
                 "defines the same way; each is converted with the offset it carries, and a time without "
                 "an offset is left blank. Process and PID are procName and pid (the text Process field, "
                 "split at the bracketed process ID), and Path is procPath, which Apple says macOS writes "
                 "with user-identifiable path components replaced by placeholder values. Bundle ID and "
                 "Version are CFBundleIdentifier and CFBundleShortVersionString with CFBundleVersion in "
                 "parentheses (the text Identifier and Version fields), Parent Process is parentProc with "
                 "parentPid in brackets, Exception Type is the exception type with its signal in "
                 "parentheses, and Termination Reason is built from the termination namespace, code and "
                 "indicator, with the terminating process when the report names one (the text fields as "
                 "written). OS Version and Incident ID come from the metadata line (the text OS Version "
                 "and Incident Identifier fields). Crash Reporter Key is crashReporterKey (the text "
                 "CrashReporter Key field), which Apple defines as an anonymized per-device identifier, "
                 "identical in reports from one device and reset when the device is erased. User ID (as "
                 "stored) is userID or the text User ID field; neither Apple page defines it. Apple "
                 "defines the incident identifier as unique to one report, so a report whose incident ID "
                 "was already read, such as a copy under Retired, is counted in the run log and not "
                 "reported again; a byte-identical copy under System/Volumes/Data is not read, and of two "
                 "copies of one report file the one outside Retired and System/Volumes/Data is the one "
                 "reported. On dleapp_macos_bigsur the one report is a text .crash with no Launch Time, "
                 "Incident Identifier or CrashReporter Key line, so Launch Time (UTC), Incident ID and "
                 "Crash Reporter Key are empty on its row. On the public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15) the 5 reports, all in the user's Retired "
                 "folder, are five crashes of Google Drive whose crash times fall within six seconds, so "
                 "Process, Path, Bundle ID, Version, Parent Process, User ID (as stored), Exception Type, "
                 "Termination Reason, OS Version and Crash Reporter Key each held one value on all 5 rows; "
                 "its 55 other .ips reports were of bug_type 298 and were not read. Bytes that are not "
                 "valid UTF-8 are shown as the Unicode replacement character; there were none in the "
                 "tested reports.",
        "paths": ('*/Library/Logs/DiagnosticReports/*.ips', '*/Library/Logs/DiagnosticReports/*.crash'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import unique_sources

# "2025-12-24 17:05:33.6811 -0500": local time, an optional fraction, and the offset from UTC.
_TIME = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.(\d+))? ([+-])(\d{2})(\d{2})$')
# The text report fields read here, as they are labelled in the report.
_TEXT_FIELDS = ('Process', 'Path', 'Identifier', 'Version', 'Parent Process', 'User ID', 'Date/Time',
                'Launch Time', 'OS Version', 'Exception Type', 'Termination Reason',
                'Incident Identifier', 'CrashReporter Key')
_TEXT_LINE = re.compile(r'^(' + '|'.join(re.escape(field) for field in _TEXT_FIELDS) + r'):\s+(.*)$')


def _utc(text):
    """The UTC datetime of a report time with its offset, or '' when it is not one."""
    match = _TIME.match(text.strip()) if isinstance(text, str) else None
    if not match:
        return ''
    stamp, fraction, sign, hours, minutes = match.groups()
    try:
        local = datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return ''
    local += timedelta(microseconds=int((fraction or '0')[:6].ljust(6, '0')))
    offset = timedelta(hours=int(hours), minutes=int(minutes))
    return (local + offset if sign == '-' else local - offset).replace(tzinfo=timezone.utc)


def _text(value):
    return '' if value is None else str(value)


def _named(name, pid):
    """'name [pid]' as a translated report writes it, or the part that is present."""
    if name in (None, '') and pid in (None, ''):
        return ''
    return f'{_text(name)} [{_text(pid)}]' if pid not in (None, '') else _text(name)


def _json_report(header, body):
    """(capture, launch, process, pid, path, bundle id, version, parent, user id, exception,
    termination, os version, incident id, crash reporter key) of a JSON crash report."""
    bundle = body.get('bundleInfo') if isinstance(body.get('bundleInfo'), dict) else {}
    short, build = bundle.get('CFBundleShortVersionString'), bundle.get('CFBundleVersion')
    version = _text(short) + (f' ({build})' if build not in (None, '') else '') if short not in (None, '') else _text(build)
    exception = body.get('exception') if isinstance(body.get('exception'), dict) else {}
    kind, signal = exception.get('type'), exception.get('signal')
    exception_text = _text(kind) + (f' ({signal})' if signal not in (None, '') else '') if kind else _text(signal)
    termination = body.get('termination') if isinstance(body.get('termination'), dict) else {}
    parts = []
    if termination.get('namespace') not in (None, ''):
        parts.append(f"Namespace {termination['namespace']}")
    if termination.get('code') not in (None, ''):
        parts.append(f"Code {termination['code']}")
    if termination.get('indicator') not in (None, ''):
        parts.append(_text(termination['indicator']))
    by = _named(termination.get('byProc'), termination.get('byPid'))
    if by:
        parts.append(f'by {by}')
    return (body.get('captureTime'), body.get('procLaunch'), body.get('procName'), body.get('pid'),
            body.get('procPath'), bundle.get('CFBundleIdentifier'), version,
            _named(body.get('parentProc'), body.get('parentPid')), body.get('userID'), exception_text,
            ', '.join(parts), header.get('os_version'), header.get('incident_id'),
            body.get('crashReporterKey'))


def _text_report(text, header=None):
    """The same fields read from a translated (text) crash report."""
    fields = {}
    for line in text.split('\n'):
        match = _TEXT_LINE.match(line)
        if match and match.group(1) not in fields:
            fields[match.group(1)] = match.group(2).strip()
    process = re.match(r'^(.*?)\s*\[(\d+)\]$', fields.get('Process', ''))
    header = header or {}
    return (fields.get('Date/Time'), fields.get('Launch Time'),
            process.group(1) if process else fields.get('Process'), process.group(2) if process else '',
            fields.get('Path'), fields.get('Identifier'), fields.get('Version'), fields.get('Parent Process'),
            fields.get('User ID'), fields.get('Exception Type'), fields.get('Termination Reason'),
            fields.get('OS Version') or header.get('os_version'),
            fields.get('Incident Identifier') or header.get('incident_id'), fields.get('CrashReporter Key'))


def _report(path, other_types):
    """The crash report fields of one file, None when it is not a crash report or cannot be read."""
    try:
        with open(path, 'rb') as handle:
            text = handle.read().decode('utf-8', errors='replace')
    except OSError:
        other_types['unreadable'] += 1
        return None
    if path.endswith('.crash'):
        report = _text_report(text)
        if not any(report):
            other_types['without crash report fields'] += 1
            return None
        return report
    first, _, rest = text.partition('\n')
    try:
        header = json.loads(first)
    except ValueError:
        header = None
    if not isinstance(header, dict):
        other_types['without a JSON metadata line'] += 1
        return None
    if str(header.get('bug_type')) != '309':
        other_types[f"of bug_type {header.get('bug_type')}"] += 1
        return None
    try:
        body = json.loads(rest)
    except ValueError:
        return _text_report(rest, header)
    if not isinstance(body, dict):
        other_types['of bug_type 309 whose report is not a JSON object'] += 1
        return None
    return _json_report(header, body)


@artifact_processor
def macosCrashReports(context):
    data_headers = (('Crash Time (UTC)', 'datetime'), ('Launch Time (UTC)', 'datetime'), 'Process', 'PID',
                    'Path', 'Bundle ID', 'Version', 'Parent Process', 'User ID (as stored)', 'Exception Type',
                    'Termination Reason', 'OS Version', 'Incident ID', 'Crash Reporter Key', 'Source File')
    data_list = []
    sources = []
    other_types = Counter()
    seen = set()
    repeated = 0
    paths, _skipped = unique_sources(context, context.get_files_found(), label='Crash Reports')
    # unique_sources orders the paths by length, so of two copies of one report file the one
    # outside Retired and System/Volumes/Data comes first.
    for path in paths:
        if os.path.isdir(path):
            continue
        report = _report(path, other_types)
        if report is None:
            continue
        # Apple documents the incident identifier as unique to one report, so a report that
        # reached the extraction twice (under System/Volumes/Data, or moved to Retired) is one report.
        incident = report[12]
        if incident:
            if incident in seen:
                repeated += 1
                continue
            seen.add(incident)
        capture, launch = report[0], report[1]
        data_list.append((_utc(capture), _utc(launch)) + tuple(_text(value) for value in report[2:])
                         + (context.get_relative_path(path),))
        sources.append(path)
    if other_types:
        summary = ', '.join(f'{count} {kind}' for kind, count in sorted(other_types.items()))
        logfunc(f'Crash Reports: files not read as crash reports: {summary}')
    if repeated:
        logfunc(f'Crash Reports: {repeated} report(s) with an incident ID already read not reported again')
    logfunc(f'Crash Reports: {len(data_list)} report(s).')
    return data_headers, data_list, '\n'.join(sources)
