"""Print jobs and printers CUPS records on a Linux or macOS system, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "cupsJobs": {
        "name": "CUPS Print Jobs",
        "description": "Print jobs CUPS kept in its spool folder, one row per job control file: the times CUPS "
                       "recorded for the job's creation, processing and completion, its state, name, user, "
                       "originating host, printer, document name and size.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Printing (CUPS)",
        "notes": "Reads the job control files CUPS keeps in its request folder, /var/spool/cups, one file per job "
                 "named c and the job number in five digits (Reference: CUPS v2.4.16, commit "
                 "7523763f00d2063f88026d93bc5b29806240de2b, https://github.com/OpenPrinting/cups, 'scheduler/job.c' "
                 "line 2285). A control file is an IPP message holding the job's attributes and is read with the "
                 "encoding of RFC 8010, sections 3.1, 3.5 and 3.9 (https://www.rfc-editor.org/rfc/rfc8010): an "
                 "eight-byte header, then attributes, each a value tag, a name and a value, a further value of the "
                 "same attribute having an empty name, up to the end-of-attributes tag. One row is reported per "
                 "file. Created (UTC), Processing (UTC) and Completed (UTC) are the time-at-creation, "
                 "time-at-processing and time-at-completed attributes, which CUPS sets from the system clock as "
                 "seconds since 1970 ('scheduler/job.c' lines 4770 to 4790); an attribute with no value gives an "
                 "empty cell. Job ID is job-id. State is job-state named as RFC 8011 section 5.3.7 names its values "
                 "(https://www.rfc-editor.org/rfc/rfc8011): 3 pending, 4 pending-held, 5 processing, 6 "
                 "processing-stopped, 7 canceled, 8 aborted, 9 completed; another number is shown as stored. State "
                 "Reasons, Job Name, User, Originating Host, Printer URI, Document Name, Document Format, Size "
                 "(KiB), Copies, Sheets Completed and Job UUID are the attributes job-state-reasons, job-name, "
                 "job-originating-user-name, job-originating-host-name, job-printer-uri, document-name-supplied, "
                 "document-format, job-k-octets, copies, job-media-sheets-completed and job-uuid as stored, the "
                 "first value of each, and for State Reasons all values joined with ' | '. Other Attributes names "
                 "the attributes the row does not show; their values are in the file. A file that is not a complete "
                 "IPP message is counted in the run log and not reported, and the job's document files (d, the job "
                 "number and a file number, line 579) are not read. ubuntu2604_arm64_cups is known data from a VM "
                 "running CUPS 2.4.16 with the cups-pdf virtual printer: the desktop user printed two text files "
                 "with lp, 20 seconds apart, the second with two copies, then submitted a third on hold and "
                 "cancelled it 5 seconds later. The 3 rows are those jobs. Each Created (UTC) is the second the "
                 "script recorded after the lp command returned; the two printed jobs have State completed with "
                 "Processing and Completed in that same second, and the third has State canceled, an empty "
                 "Processing (UTC) and a Completed (UTC) in the second its cancel was recorded. Job Name is the "
                 "title given to lp, Document Name the file name, User the account that ran lp, Originating Host "
                 "localhost, Copies 1, 2 and 1, and Sheets Completed 1, 2 and 0. User, Originating Host, Printer "
                 "URI, Document Format and Size (KiB) each held one value on all 3 rows: the one account, localhost, "
                 "the one printer, text/plain and 1. The rows agree with what CUPS itself keeps elsewhere in the "
                 "capture: job.cache gives the same state number, completed time, user and size for each job, and "
                 "lpstat listed the same three jobs for the same user. The date-time-at attributes of the files give "
                 "the same instants as the three time columns. The cancelled job's State Reasons is "
                 "job-hold-until-specified, as stored. Not exercised on real data: a job from another host, a job "
                 "with more than one document, a collection value, which is shown as the text <collection>, and "
                 "other CUPS versions; the last two were tested with constructed input. A row shows that the job was "
                 "submitted to CUPS and what CUPS recorded about it, not the content printed. CUPS removes old jobs "
                 "and their files according to its settings, so the absence of a row is not evidence that nothing "
                 "was printed.",
        "paths": ("*/var/spool/cups/c[0-9]*",),
        "output_types": "standard",
        "artifact_icon": "printer",
        "sample_data": {
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS aarch64, CUPS 2.4.16 | 3 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "cupsPrinters": {
        "name": "CUPS Printers",
        "description": "Printers defined in CUPS's printers.conf, one row per printer: name, description, location, "
                       "make and model, device URI, state and the times of its last state and configuration change.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Printing (CUPS)",
        "notes": "Reads printers.conf of the CUPS configuration folder, which cupsd writes with one section per "
                 "printer (Reference: CUPS v2.4.16, commit 7523763f00d2063f88026d93bc5b29806240de2b, "
                 "https://github.com/OpenPrinting/cups, 'scheduler/printers.c' lines 857 to 881). One row is "
                 "reported per section. Printer is the name in the section's opening tag and Default is Yes for a "
                 "DefaultPrinter section. State Time (UTC) and Config Time (UTC) are the StateTime and ConfigTime "
                 "directives, the times of the printer's last state change and last configuration change as CUPS "
                 "wrote them, seconds since 1970 (lines 1125 to 1142 and 1534 to 1535). Info, Location, Make and "
                 "Model, Device URI, State, Accepting, Shared and UUID are the directives Info, Location, MakeModel, "
                 "DeviceURI, State, Accepting, Shared and UUID as stored; a directive that is absent gives an empty "
                 "cell, and when one is repeated the first is shown. Directive names are matched without case, as "
                 "cupsd matches them. On ubuntu2604_arm64_cups, from a VM running CUPS 2.4.16, the 1 row is the "
                 "cups-pdf virtual printer the test installed: Printer PDF, Default Yes, Device URI cups-pdf:/, "
                 "State Idle, Accepting Yes, Shared No and an empty Location. Its Config Time (UTC) is 8 seconds "
                 "before the second the script recorded after the package installation ended, and its State Time "
                 "(UTC) is the second the first test job was created and completed; the second job, 20 seconds "
                 "later, did not move it. Not exercised on real data: a network printer, a printer that is not the "
                 "default, and more than one printer, which were tested with constructed input. A Device URI can "
                 "hold a user name and password for the print server; it is shown as stored.",
        "paths": ("*/etc/cups/printers.conf",),
        "output_types": "standard",
        "artifact_icon": "printer",
        "sample_data": {
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS aarch64, CUPS 2.4.16 | 1 row",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import struct
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
JOB_STATES = {3: 'pending', 4: 'pending-held', 5: 'processing', 6: 'processing-stopped', 7: 'canceled', 8: 'aborted',
              9: 'completed'}
_INTEGER_TAGS = (0x21, 0x23)
_BEGIN_COLLECTION, _END_COLLECTION = 0x34, 0x37
# the attributes a row shows; every other attribute's name goes to Other Attributes
_SHOWN = ('time-at-creation', 'time-at-processing', 'time-at-completed', 'job-id', 'job-state', 'job-state-reasons',
          'job-name', 'job-originating-user-name', 'job-originating-host-name', 'job-printer-uri',
          'document-name-supplied', 'document-format', 'job-k-octets', 'copies', 'job-media-sheets-completed',
          'job-uuid')


def ipp_attributes(data):
    """{attribute name: [values]} for the bytes of an IPP message such as a CUPS job control file, in the order
    read: integers and enums as numbers, booleans as True or False, other values as text, and a collection as the
    text '<collection>'. None when the data ends before the end-of-attributes tag."""
    attributes, name, depth, at = {}, None, 0, 8
    while at < len(data):
        tag = data[at]
        at += 1
        if tag == 0x03:
            return attributes
        if tag < 0x10:
            name = None
            continue
        if at + 2 > len(data):
            return None
        length = struct.unpack_from('>H', data, at)[0]
        at += 2
        label = data[at:at + length]
        at += length
        if at + 2 > len(data):
            return None
        length = struct.unpack_from('>H', data, at)[0]
        at += 2
        value = data[at:at + length]
        at += length
        if depth:
            depth += {_BEGIN_COLLECTION: 1, _END_COLLECTION: -1}.get(tag, 0)
            continue
        if label:
            name = label.decode('utf-8', errors='backslashreplace')
            attributes.setdefault(name, [])
        if name is None:
            continue
        if tag == _BEGIN_COLLECTION:
            depth = 1
            attributes[name].append('<collection>')
        elif tag in _INTEGER_TAGS and length == 4:
            attributes[name].append(struct.unpack('>i', value)[0])
        elif tag == 0x22 and length == 1:
            attributes[name].append(bool(value[0]))
        else:
            attributes[name].append(value.decode('utf-8', errors='backslashreplace'))
    return None


def utc(seconds):
    """The UTC time of a positive whole count of seconds since 1970, or '' for anything else."""
    if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds <= 0:
        return ''
    try:
        return EPOCH + timedelta(seconds=seconds)
    except OverflowError:
        return ''


def _first(attributes, name):
    values = attributes.get(name) or ['']
    return values[0]


def _joined(attributes, name):
    return ' | '.join(str(value) for value in attributes.get(name, []))


def job_row(attributes):
    """The row for the attributes of a job control file, without the source file."""
    state = _first(attributes, 'job-state')
    others = sorted(name for name in attributes if name not in _SHOWN)
    return (utc(_first(attributes, 'time-at-creation')), utc(_first(attributes, 'time-at-processing')),
            utc(_first(attributes, 'time-at-completed')), _first(attributes, 'job-id'),
            JOB_STATES.get(state, state), _joined(attributes, 'job-state-reasons'), _first(attributes, 'job-name'),
            _first(attributes, 'job-originating-user-name'), _first(attributes, 'job-originating-host-name'),
            _first(attributes, 'job-printer-uri'), _first(attributes, 'document-name-supplied'),
            _first(attributes, 'document-format'), _first(attributes, 'job-k-octets'), _first(attributes, 'copies'),
            _first(attributes, 'job-media-sheets-completed'), _first(attributes, 'job-uuid'), ', '.join(others))


@artifact_processor
def cupsJobs(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Processing (UTC)', 'datetime'), ('Completed (UTC)', 'datetime'),
                    'Job ID', 'State', 'State Reasons', 'Job Name', 'User', 'Originating Host', 'Printer URI',
                    'Document Name', 'Document Format', 'Size (KiB)', 'Copies', 'Sheets Completed', 'Job UUID',
                    'Other Attributes', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        attributes = ipp_attributes(data)
        if not attributes:
            problems['files that are not a complete IPP message, not reported'] += 1
            continue
        data_list.append(job_row(attributes) + (context.get_relative_path(path),))
        read.append(path)
    if problems:
        logfunc('CUPS Print Jobs: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


def printer_rows(data):
    """The rows for the bytes of a printers.conf, in file order: (state time, config time, printer, default, info,
    location, make and model, device URI, state, accepting, shared, UUID). A printer is the lines between
    <Printer name> or <DefaultPrinter name> and the closing tag, each a directive name and its value."""
    rows, current = [], None
    for raw in data.split(b'\n'):
        line = raw.decode('utf-8', errors='backslashreplace').strip()
        if not line:
            continue
        word, _, rest = line.partition(' ')
        lowered = word.lower()
        if lowered in ('<printer', '<defaultprinter') and rest.endswith('>'):
            current = {'name': rest[:-1].strip(), 'default': 'Yes' if lowered == '<defaultprinter' else 'No'}
        elif lowered in ('</printer>', '</defaultprinter>'):
            if current is not None:
                rows.append(tuple(_stamp(current.get(key, '')) for key in ('statetime', 'configtime'))
                            + tuple(current.get(key, '') for key in ('name', 'default', 'info', 'location',
                                                                     'makemodel', 'deviceuri', 'state', 'accepting',
                                                                     'shared', 'uuid')))
            current = None
        elif current is not None:
            current.setdefault(lowered, rest.strip())
    return rows


def _stamp(text):
    return utc(int(text)) if text.isdigit() else ''


@artifact_processor
def cupsPrinters(context):
    data_headers = (('State Time (UTC)', 'datetime'), ('Config Time (UTC)', 'datetime'), 'Printer', 'Default',
                    'Info', 'Location', 'Make and Model', 'Device URI', 'State', 'Accepting', 'Shared', 'UUID',
                    'Source File')
    data_list, read, unreadable = [], [], 0
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            unreadable += 1
            continue
        rows = printer_rows(data)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if unreadable:
        logfunc(f'CUPS Printers: {unreadable} files that could not be read')
    return data_headers, data_list, '\n'.join(read)
