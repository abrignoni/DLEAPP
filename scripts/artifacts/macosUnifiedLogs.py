"""Apple Unified Log entries (tracev3), imported into the LAVA database, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Ported from iLEAPP's logarchive import. The tracev3 data is read with Mandiant's
unifiedlog_iterator through scripts/unifiedlogs.py; a 'log show' JSON export is read
directly when one is supplied instead.
"""

__artifacts_v2__ = {
    "macosUnifiedLogs": {
        "name": "Unified Logs",
        "description": "Apple Unified Log entries from the tracev3 data under db/diagnostics with "
                       "the uuidtext format strings, or from a 'log show' JSON export, imported "
                       "into the LAVA database: time, process, subsystem, category and message.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "Reading tracev3 data needs the unifiedlog_iterator binary from "
                        "Mandiant's macos-UnifiedLogs, found through the "
                        "DLEAPP_UNIFIEDLOG_ITERATOR environment variable, a bin folder beside "
                        "dleapp.py, or PATH",
        "category": "Unified Logs (macOS)",
        "notes": "Imports the Apple Unified Log entries the parser returns into the LAVA database "
                 "only, one row per entry. The tracev3 files under db/diagnostics, with the format "
                 "strings under db/uuidtext, are read by Mandiant's unifiedlog_iterator "
                 "(https://github.com/mandiant/macos-UnifiedLogs), which DLEAPP runs with --mode "
                 "log-archive and --format jsonl and finds through the DLEAPP_UNIFIEDLOG_ITERATOR "
                 "environment variable, a bin folder beside dleapp.py, or PATH; the run log records "
                 "the version it reports, unifiedlog_iterator 0.7.0 on the tested images. When no "
                 "binary is found the tracev3 data is not read and the run log says so. A log show "
                 "--style json export named logarchive*.json is read directly instead when one is "
                 "present; neither tested image carries one. Timestamp (UTC) is the time the parser "
                 "gives each entry, cut from nanoseconds to microseconds, or for a JSON export the "
                 "entry's timestamp with its stated offset converted to UTC. Row Number counts rows in"
                 " the order read. Process Image Path, Process ID, Subsystem, Category and Event "
                 "Message are the process, pid, subsystem, category and message values the parser "
                 "emits, or processImagePath, processID, subsystem, category and eventMessage from a "
                 "JSON export. Trace ID is traceID from a JSON export; the parser emits none, so Trace"
                 " ID has no value on any row read from tracev3 data, which is every row of both "
                 "tested images. A logical extraction of a Mac can hold both "
                 "private/var/db/diagnostics and System/Volumes/Data/private/var/db/diagnostics, and "
                 "the same for uuidtext; both copies are read together as one store, a file only one "
                 "copy holds from that copy and a file both hold from the copy whose bytes begin with "
                 "the other's, and the run log counts each case. On the MacBook Pro the two "
                 "diagnostics copies held 262 and 267 files: 19 tracev3 files only in "
                 "private/var/db/diagnostics, 24 files only in the other copy, 6 longer in the "
                 "System/Volumes/Data copy, each beginning with the other copy's bytes, and 237 "
                 "identical. Read alone, the System/Volumes/Data copy gives 22,102,026 entries; read "
                 "together the store gives 27,030,315, and the 19 files only "
                 "private/var/db/diagnostics holds give 4,928,289 when unifiedlog_iterator reads them "
                 "on their own. On dleapp_macos_bigsur the store gives 3,024,846 entries from "
                 "2021-02-15 15:25:46 to 2021-02-19 19:53:32 UTC, and on the MacBook Pro 27,030,315 "
                 "from 2025-11-26 15:51:30 to 2025-12-25 09:43:52 UTC. Warnings the parser writes are "
                 "copied to the run log: on dleapp_macos_bigsur one, that it failed to get a message "
                 "string from a UUIDText file, and on the MacBook Pro two, about an unsupported number"
                 " size of 16.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 3,024,846 rows",
                 },
        "paths": ('*/logarchive*.json', '*/db/diagnostics/*', '*/db/uuidtext/*', '*.logarchive/*'),
        "output_types": "lava_only",
        "artifact_icon": "database",
    }
}

import os
from datetime import datetime, timezone

import ijson

from scripts import unifiedlogs
from scripts.ilapfuncs import artifact_processor, get_file_path, logfunc

DATA_HEADERS = (('Timestamp (UTC)', 'datetime'), 'Row Number', 'Process Image Path', 'Process ID',
                'Subsystem', 'Category', 'Event Message', 'Trace ID')


def _json_timestamp(timestamp):
    """A 'log show' timestamp such as '2021-02-19 19:48:25.533606-0500' as aware UTC, or ''."""
    text = (timestamp or '').strip()
    if len(text) > 5 and text[-5] in '+-' and text[-4:].isdigit():
        text = f'{text[:-2]}:{text[-2:]}'
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return ''


def _iterator_timestamp(timestamp):
    """The RFC 3339 time unifiedlog_iterator emits (nanoseconds, 'Z') as aware UTC, or ''."""
    if not timestamp:
        return ''
    normalized = timestamp[:-1] if timestamp.endswith('Z') else timestamp
    if '.' in normalized:
        whole, fraction = normalized.split('.', 1)
        normalized = f'{whole}.{fraction[:6]}'
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def _rows_from_json(source_path):
    """Rows from a 'log show --style json' export, which is one JSON array of entries."""
    progress = unifiedlogs.ImportProgress(os.path.getsize(source_path))
    count = 0
    with open(source_path, 'rb') as handle:
        try:
            for record in ijson.items(handle, 'item', multiple_values=True):
                if not isinstance(record, dict):
                    continue
                count += 1
                progress.add_record()
                if count % unifiedlogs.ImportProgress.CHECK_EVERY == 0:
                    progress.set_bytes_done(handle.tell())
                yield (_json_timestamp(record.get('timestamp', '')), count,
                       record.get('processImagePath', ''), record.get('processID', ''),
                       record.get('subsystem', ''), record.get('category', ''),
                       str(record.get('eventMessage', '')), str(record.get('traceID', '')))
        except ijson.JSONError as exc:
            logfunc(f'Unified Logs: the JSON export stopped parsing after {count:,} entries '
                    f'({type(exc).__name__}); the entries before that point were imported')
    progress.finish()


def _rows_from_tracev3(binary, archive_dir):
    """Rows as unifiedlog_iterator decodes them; it emits no trace ID, so that stays blank."""
    count = 0
    for record in unifiedlogs.stream_records(binary, archive_dir):
        count += 1
        yield (_iterator_timestamp(record.get('timestamp', '')), count, record.get('process', ''),
               record.get('pid', ''), record.get('subsystem', ''), record.get('category', ''),
               str(record.get('message', '')), '')


def _log_merge(context, copies, summary):
    """Record in the run log which copies of the log store were read and how they compared."""
    relative = [context.get_relative_path(copy) for copy in copies]
    logfunc(f'Unified Logs: the log store is held in more than one copy ({", ".join(relative)}); '
            f'they were read together as one store')
    for copy, count in summary['only_in'].items():
        noun = 'file is' if count == 1 else 'files are'
        logfunc(f'Unified Logs: {count:,} {noun} only in {context.get_relative_path(copy)}')
    logfunc(f"Unified Logs: comparing the copies of each file the copies share, "
            f"{summary['identical']:,} were identical, {summary['extended']:,} were longer in one "
            f"copy that begins with the other's bytes (the longer was read), and "
            f"{summary['disagreed']:,} differed otherwise (the first copy's file was read)")


@artifact_processor
def macosUnifiedLogs(context):
    files_found = context.get_files_found()
    results = context.create_artifact_result(headers=DATA_HEADERS)

    source_path = get_file_path(files_found, 'logarchive*.json')
    if source_path:
        results.set_source_path(source_path)
        return results.extend(_rows_from_json(source_path))

    logarchive_dir, diagnostics_dir, uuidtext_dir = unifiedlogs.find_archive_roots(files_found)
    if not logarchive_dir and not diagnostics_dir:
        return results

    binary = unifiedlogs.find_iterator()
    if not binary:
        logfunc('Unified Logs: tracev3 data was found but the unifiedlog_iterator binary is not '
                'available, so it was not read. Install the binary (see the artifact '
                'requirements) or supply a logarchive*.json export.')
        return results

    if logarchive_dir:
        archive_dir = source_path = logarchive_dir
    else:
        if not uuidtext_dir:
            logfunc('Unified Logs: tracev3 data was found but no uuidtext directory, so the '
                    'messages cannot be resolved; nothing was imported.')
            return results
        workdir = os.path.join(context.get_data_folder(), '_logarchive_native')
        diagnostics_dirs = unifiedlogs.store_copies(files_found, diagnostics_dir)
        uuidtext_dirs = unifiedlogs.store_copies(files_found, uuidtext_dir)
        if len(diagnostics_dirs) == 1 and len(uuidtext_dirs) == 1:
            archive_dir = unifiedlogs.assemble_archive(diagnostics_dir, uuidtext_dir, workdir)
        else:
            archive_dir, summary = unifiedlogs.assemble_merged_archive(
                diagnostics_dirs, uuidtext_dirs, workdir)
            _log_merge(context, diagnostics_dirs + uuidtext_dirs, summary)
        source_path = '\n'.join(diagnostics_dirs + uuidtext_dirs)

    parser = unifiedlogs.iterator_version(binary) or os.path.basename(binary)
    logfunc(f'Unified Logs: reading tracev3 data with {parser}')
    results.set_source_path(source_path)
    return results.extend(_rows_from_tracev3(binary, archive_dir))
