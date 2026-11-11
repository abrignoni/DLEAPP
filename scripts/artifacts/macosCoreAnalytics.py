__artifacts_v2__ = {
    "macosCoreAnalyticsFiles": {
        "name": "macOS CoreAnalytics Files",
        "description": "Header and metadata records of .core_analytics files in DiagnosticReports on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "CoreAnalytics (macOS)",
        "notes": (
            'One row per .core_analytics file under Library/Logs/DiagnosticReports, its Retired folder '
            'included. A .core_analytics file is lines of JSON: a header object, an object marked <metadata>, '
            'event records and an <end-of-file> marker. That layout is read from the files on the tested '
            "images, not from Apple documentation. Timestamp is the header's timestamp, stored with a UTC "
            "offset and shown as UTC. Start Timestamp is the metadata's startTimestamp, stored with a Z suffix "
            'and read as UTC. What the two times mark is not established. OS Version, Bug Type, Incident ID and'
            " Crash Reporter Key are the header's os_version, bug_type, incident_id and crashreporter_key as "
            'stored. Event Records is the number of event records in the file. Other Header Values and Other '
            'Metadata Values hold the other keys of the two objects as JSON. A line that is none of the four '
            'kinds is counted in the run log; no line was on the tested images. OS Version and Bug Type each '
            'held one value on every row of each image with rows. Crash Reporter Key held no value on any row '
            'of the macOS 14.6.1 and 15.4 images. Other Header Values held no value on any row of the two macOS'
            ' 11.2.1 images and held one value on every row of the macOS 14.6.1 and 15.4 images. Other Metadata'
            ' Values held one value on every row of the Magnet macOS 11.2.1 image. On the macOS 15.4 logical '
            'image one file sat in DiagnosticReports in one volume view and in Retired in another, '
            'byte-identical, and is reported at both paths. When a logical extraction holds the same file under'
            ' System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read '
            'again and the run log counts it. When the views hold different bytes but give the same row, the '
            'row is reported once and Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Logs/DiagnosticReports/*.core_analytics',),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 48 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 12 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 2 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 9 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (no .core_analytics file found)",
        },
    },
    "macosCoreAnalyticsEvents": {
        "name": "macOS CoreAnalytics Events",
        "description": "Event records of .core_analytics files in DiagnosticReports on macOS.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "CoreAnalytics (macOS)",
        "notes": (
            'One row per event record of the .core_analytics files under Library/Logs/DiagnosticReports, its '
            'Retired folder included. A .core_analytics file is lines of JSON: a header object, an object '
            'marked <metadata>, event records and an <end-of-file> marker. That layout is read from the files '
            "on the tested images, not from Apple documentation. File Timestamp is the timestamp of the file's "
            "header, stored with a UTC offset and shown as UTC: it is the file's time, not a time of the event."
            " Event Name is the record's name and Message its message object as JSON. Aggregation Period, Days "
            'Aggregated, Sampling, UUID and Device ID are aggregationPeriod, numDaysAggregated, sampling, uuid '
            'and deviceId as stored. Other Values holds any other key of the record as JSON. What an event name'
            ' or a message field means is set by the component that logged it and is not interpreted here. '
            'Aggregation Period and Days Aggregated each held no value on any row of the two macOS 11.2.1 '
            'images and the macOS 14.6.1 image. Device ID held no value on any row of the two macOS 11.2.1 '
            'images. Other Values held no value on any row of the Magnet macOS 11.2.1 and the macOS 14.6.1 '
            'images. On the macOS 15.4 image 5 rows held an aggregationPeriodStartTimestamp key there, a time '
            'that is not given a column, and on the Big Sur E01 image 4 rows held an eventCount key there. '
            'Sampling held one value on every row of the Magnet macOS 11.2.1 image. On the macOS 15.4 logical '
            'image one file sat in DiagnosticReports in one volume view and in Retired in another, so its 308 '
            'records are reported at both paths. When a logical extraction holds the same file under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ as well, a byte-identical copy is not read '
            'again and the run log counts it. When the views hold different bytes but give the same row, the '
            'row is reported once and Source File lists each file, one per line. '
        ),
        "paths": ('*/Library/Logs/DiagnosticReports/*.core_analytics',),
        "output_types": "standard",
        "artifact_icon": "bar-chart-2",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 37 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 33 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 363 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 2221 rows (308 of them reported twice, see notes)",
            "adams_macbookpro_macos26": "macOS 26.2 | 0 rows (no .core_analytics file found)",
        },
    },
}

import json
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import fold_view_rows, unique_sources

_HEADER_SHOWN = ('timestamp', 'os_version', 'bug_type', 'incident_id', 'crashreporter_key')
_EVENT_SHOWN = ('name', 'message', 'aggregationPeriod', 'numDaysAggregated', 'sampling', 'uuid', 'deviceId')


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def _text(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (dict, list)):
        return _json(value)
    return str(value)


def _header_time(value):
    """'2021-03-29 20:01:16.38 -0400' as an aware UTC datetime, or '' when it is not in that form."""
    if not isinstance(value, str):
        return ''
    for form in ('%Y-%m-%d %H:%M:%S.%f %z', '%Y-%m-%d %H:%M:%S %z'):
        try:
            return datetime.strptime(value, form).astimezone(timezone.utc)
        except ValueError:
            continue
    return ''


def _start_time(value):
    """'2021-03-29T00:01:52Z' as an aware UTC datetime, or '' when it is not in that form."""
    if not isinstance(value, str):
        return ''
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def _records(path):
    """(header, metadata, events, unread): the JSON objects of one file, one per line.

    The header is the first object with no _marker, name or message key. The metadata is
    the object whose _marker is <metadata>. Events are the objects with a name or message
    key. unread counts lines that are not a JSON object or fit none of those.
    """
    header, metadata, events, unread = None, None, [], 0
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                unread += 1
                continue
            if not isinstance(record, dict):
                unread += 1
            elif '_marker' in record:
                if record['_marker'] == '<metadata>' and metadata is None:
                    metadata = record
                elif record['_marker'] != '<end-of-file>':
                    unread += 1
            elif 'name' in record or 'message' in record:
                events.append(record)
            elif header is None:
                header = record
            else:
                unread += 1
    return header or {}, metadata or {}, events, unread


def _files(context, label):
    found = [str(p) for p in context.get_files_found() if str(p).endswith('.core_analytics')]
    paths, _skipped = unique_sources(context, found, label=label)
    unread = 0
    for path in paths:
        header, metadata, events, bad = _records(path)
        unread += bad
        yield path, header, metadata, events
    if unread:
        logfunc(f'{label}: {unread} line(s) not read as a header, metadata, event or end-of-file record')


@artifact_processor
def macosCoreAnalyticsFiles(context):
    data_headers = (('Timestamp', 'datetime'), ('Start Timestamp', 'datetime'), 'OS Version', 'Bug Type',
                    'Incident ID', 'Crash Reporter Key', 'Event Records', 'Other Header Values',
                    'Other Metadata Values', 'Source File')
    rows, read = [], []
    for path, header, metadata, events in _files(context, 'macOS CoreAnalytics Files'):
        read.append(path)
        relative = context.get_relative_path(path)
        other_header = {key: value for key, value in header.items() if key not in _HEADER_SHOWN}
        other_metadata = {key: value for key, value in metadata.items()
                          if key not in ('_marker', 'startTimestamp')}
        rows.append((
            _header_time(header.get('timestamp')),
            _start_time(metadata.get('startTimestamp')),
            _text(header.get('os_version')),
            _text(header.get('bug_type')),
            _text(header.get('incident_id')),
            _text(header.get('crashreporter_key')),
            len(events),
            _json(other_header) if other_header else '',
            _json(other_metadata) if other_metadata else '',
            relative,
        ))
    return data_headers, fold_view_rows(rows), '\n'.join(read)


@artifact_processor
def macosCoreAnalyticsEvents(context):
    data_headers = (('File Timestamp', 'datetime'), 'Event Name', 'Message', 'Aggregation Period',
                    'Days Aggregated', 'Sampling', 'UUID', 'Device ID', 'Other Values', 'Source File')
    rows, read = [], []
    for path, header, _metadata, events in _files(context, 'macOS CoreAnalytics Events'):
        read.append(path)
        relative = context.get_relative_path(path)
        stamp = _header_time(header.get('timestamp'))
        for event in events:
            other = {key: value for key, value in event.items() if key not in _EVENT_SHOWN}
            rows.append((
                stamp,
                _text(event.get('name')),
                _text(event.get('message')),
                _text(event.get('aggregationPeriod')),
                _text(event.get('numDaysAggregated')),
                _text(event.get('sampling')),
                _text(event.get('uuid')),
                _text(event.get('deviceId')),
                _json(other) if other else '',
                relative,
            ))
    return data_headers, fold_view_rows(rows), '\n'.join(read)
