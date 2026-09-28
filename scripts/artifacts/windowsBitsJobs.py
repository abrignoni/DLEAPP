"""Windows BITS job store (qmgr.db) for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Background Intelligent Transfer Service queue in
ProgramData\\Microsoft\\Network\\Downloader with scripts/bits_qmgr.py: the live records of
qmgr.db's Jobs and Files tables, and the job and file records still present in the
database file and its ESE log files, one row per distinct version of each.
"""

import os
from collections import OrderedDict

from scripts.bits_qmgr import QmgrDatabase, filetime, find_records, guid_text, parse_file, parse_job
from scripts.ilapfuncs import artifact_processor, logfunc

__artifacts_v2__ = {
    "bitsJobs": {
        "name": "BITS Jobs",
        "description": 'Jobs stored in the Windows BITS queue database (qmgr.db) and its ESE '
                        'log files, one row per distinct stored version.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-28",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": 'Reads the Background Intelligent Transfer Service queue in '
                  'ProgramData\\Microsoft\\Network\\Downloader: qmgr.db, an ESE database, and the '
                  '.log and .jrs files in the same folder, with scripts/bits_qmgr.py. Only this'
                  " ESE form is read; the qmgr0.dat and qmgr1.dat queue files ANSSI's README "
                  'describes '
                  '(https://github.com/ANSSI-FR/bits_parser/blob/bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357/README.rst?plain=1#L32-L35)'
                  " are not. Rows come from two places. Live rows are the records of qmgr.db's "
                  "Jobs table. A record carrying ESE's deleted node flag fNDDeleted "
                  '(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248),'
                  " which ESE's own code treats as not there unless its version store still "
                  'holds an update to it '
                  '(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079),'
                  ' is not a live row; it is counted in the run log instead. If qmgr.db is cut '
                  'short, such as a partial copy, and reading its Jobs or Files table reaches a '
                  'page that lies past the end of the file, neither table is read and the run '
                  'log names that page; the search below still covers the bytes the file holds. '
                  'A folder holding only a copy of PC-MUS-001\'s qmgr.db, which gives 25 rows '
                  'whole, cut to 90, 75, 50 and 25 percent of its length gave 25, 25, 8 and 0 '
                  'rows: the 25 percent copy\'s tables could not be read, and the search found '
                  'no record in the bytes it kept. Recovered rows are'
                  ' job records found by searching qmgr.db and every .db, .log and .jrs file in'
                  ' the folder for the job marker GUIDs BitsParser lists '
                  '(https://github.com/fireeye/BitsParser/blob/0a2b51eeec79c5e181d8fc526d5715552299c45f/BitsParser.py#L41-L47).'
                  ' They include jobs no longer in the table, and on AF-Case2 they included 15 '
                  'versions of the 2 live jobs, each with an earlier Modified time than the '
                  'live record. A row is one distinct version of a job record: copies whose '
                  'read fields are all the same are merged, Found In names the files they were '
                  "found in and Copies counts the copies the search found, so a Live row's "
                  "table record is not counted. The record layout is read from ANSSI's "
                  'MIT-licensed bits_parser, bits/structs.py at commit '
                  'bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357 '
                  '(https://github.com/ANSSI-FR/bits_parser/blob/bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357/bits/structs.py),'
                  ' cited below as structs.py; no code is copied. A job record holds the type, '
                  'priority and state (L79-L97), a 32-bit value not reported (L98), the job '
                  'GUID (L99), the name, the description and two strings structs.py calls cmd '
                  'and args (L120-L123), the owner SID (L104), a 32-bit value structs.py reads '
                  'as the notify flags (L105-L114), a block it calls the access token that runs'
                  ' to the transfer marker GUID (L125, and BitsParser.py L36, '
                  'https://github.com/fireeye/BitsParser/blob/0a2b51eeec79c5e181d8fc526d5715552299c45f/BitsParser.py#L36),'
                  ' the file GUIDs, the errors and five FILETIMEs (L161-L183). State, Type and '
                  'Priority are named as Microsoft lists BG_JOB_STATE '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/bits/ne-bits-bg_job_state.md?plain=1#L56-L97),'
                  ' BG_JOB_TYPE '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/bits/ne-bits-bg_job_type.md?plain=1#L56-L70)'
                  ' and BG_JOB_PRIORITY '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/bits/ne-bits-bg_job_priority.md?plain=1#L56-L70),'
                  ' numbered from 0 in that order as structs.py numbers them (L79-L97), with '
                  'the stored number in brackets. A match is not reported when its state, type '
                  'or priority is outside those lists, its job GUID is zero, its owner is not a'
                  ' SID, one of its strings is not terminated text, its file GUIDs are not '
                  "followed by the transfer marker again, or another record's marker comes "
                  'before its transfer marker (the rest of such a match would be read from '
                  "another record's bytes). Job Name equals the jobTitle of event 3 (job "
                  'created) in the Microsoft-Windows-Bits-Client/Operational log on all 342 '
                  'rows whose job has such an event on the four images tested. Owner SID: 7 of '
                  'those rows hold a well-known service SID, and event 3 names the same account'
                  ' on all 7; the other 335 hold account SIDs, which the event gives by name '
                  'and which were not compared. Created (UTC) and Modified (UTC) are the first '
                  'two FILETIMEs, which structs.py names ctime and mtime (L167-L168). Created '
                  "fell within a second of the job's event 3 on all 342 rows. Modified was not "
                  'earlier than Created on any row, and on 323 of the 342 it fell within a '
                  "second of one of that job's BITS-Client events. The other three FILETIMEs "
                  'are not reported; on every row tested the fifth was the fourth plus exactly '
                  '90 days. structs.py gives an error entry as 25 bytes (L151-L158). On the '
                  'Windows 10 1709 image tested (build 16299) only 25-byte entries left the '
                  'times in range, and on the builds 17763, 19041 and 22621 tested only 21-byte'
                  ' ones did, so both sizes are tried and the one that leaves the first two '
                  'FILETIMEs between 1970 and 2100 is kept. When both sizes do or neither does,'
                  ' the times and errors are left blank; no tested row needed that. Error Codes'
                  ' is the 32-bit value four bytes into each entry, the upper half of the '
                  '64-bit value structs.py calls code (L152), in hexadecimal. 83 rows carry '
                  'one; on 48 of the 61 whose job has a BITS-Client event with an hr value, it '
                  'equals one of those values. Notify Program and Notify Parameters are the '
                  'strings structs.py calls cmd and args (L122-L123), which BitsParser reports '
                  'as CommandExecuted and CommandArguments '
                  '(https://github.com/fireeye/BitsParser/blob/0a2b51eeec79c5e181d8fc526d5715552299c45f/BitsParser.py#L432-L433).'
                  ' The columns are named for the program and parameters that SetNotifyCmdLine '
                  'sets, which BITS runs when the job enters the error or transferred state '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/bits1_5/nf-bits1_5-ibackgroundcopyjob2-setnotifycmdline.md?plain=1#L53).'
                  ' Notify Program and Notify Parameters were empty on every row tested, so '
                  'that the two strings hold those values is not established here, and the two '
                  'columns are filled only in the unit tests. Notify Flags held 3 on every row '
                  'except 3 LoneWolf rows, which held 11. Both values are sums of the values '
                  'Microsoft lists for SetNotifyFlags '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/bits/nf-bits-ibackgroundcopyjob-setnotifyflags.md?plain=1#L68-L102).'
                  ' On the four images tested, Type was Download (0) on every row. File Count '
                  'was 1 on every row except 3 LoneWolf rows, which held 11. Description was '
                  'empty on every row of AF-Case2 and Szechuan, and filled on 26 of the 142 '
                  'LoneWolf rows and 70 of the 263 PC-MUS-001 rows. Owner SID held one value on'
                  ' every row of AF-Case2 and on every row of PC-MUS-001. Record Status was '
                  'Recovered on every row of LoneWolf, PC-MUS-001 and Szechuan. On the four '
                  'images tested, the Jobs table held 2 live records on AF-Case2 and none on '
                  'LoneWolf, PC-MUS-001 and Szechuan, each of which held one record flagged '
                  'deleted with no column data left. dissect.esedb 3.18 read the same Jobs and '
                  'Files table records from all four databases, with the same record IDs and '
                  "byte-identical blobs. Compared with FireEye's Apache-2.0 BitsParser at "
                  'commit 0a2b51eeec79c5e181d8fc526d5715552299c45f carving the same files: '
                  'apart from 4 matches with a zero job GUID, it reported the same job GUIDs '
                  'with the same job names. Every pair of Created and Modified times it '
                  'reported is reported here except 21 copies it reported with no times and 2 '
                  'with times in the year 7462; 22 of those 23 belong to jobs with errors on '
                  'the three images whose error entries are 21 bytes, which BitsParser reads as'
                  ' 25, the size in structs.py (L151-L158). Of the 4 zero-GUID matches, 3 have '
                  "a type, priority or state outside Microsoft's lists and 1 has times "
                  'BitsParser read from bytes further on in the file, and BitsParser also '
                  'reported one LoneWolf copy whose owner string stops partway through the SID.'
                  ' None of those is reported here.',
        "paths": ('*/ProgramData/Microsoft/Network/Downloader/*',),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 58 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 142 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 263 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 26 rows",
            "dleapp_macos_bigsur": ("macOS 11.2.1 build 20D74 | 0 rows (no member matches "
                                    "the declared paths)"),
        },
    },
    "bitsJobFiles": {
        "name": "BITS Job Files",
        "description": 'Files of Windows BITS jobs (remote URL, local path, sizes) stored in '
                        'the queue database (qmgr.db) and its ESE log files, one row per '
                        'distinct stored version.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-28",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": 'The files of the jobs in BITS Jobs, from the same folder and the same two '
                  "places: the records of qmgr.db's Files table, and the file records found by "
                  "searching qmgr.db and the folder's .db, .log and .jrs files for the file "
                  'marker GUID BitsParser lists '
                  '(https://github.com/fireeye/BitsParser/blob/0a2b51eeec79c5e181d8fc526d5715552299c45f/BitsParser.py#L40).'
                  ' Rows, Record Status, Found In and Copies work as in BITS Jobs. A qmgr.db '
                  'cut short is read as in BITS Jobs; the same copies gave 39, 39, 11 and 0 of '
                  'the 39 rows the whole file gives. The layout '
                  "is read from ANSSI's bits_parser (bits/structs.py at commit "
                  'bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357, '
                  'https://github.com/ANSSI-FR/bits_parser/blob/bd3c79b0ccc9191ecc8209e9f0b836a2b16e0357/bits/structs.py#L131-L148):'
                  ' the local file name, the remote name and a temporary file name, two 64-bit '
                  'numbers, one byte (not reported), and the drive and volume strings. A match '
                  'is not reported when its local or remote name is empty or one of its strings'
                  ' is not terminated text. structs.py names the two numbers download_size and '
                  'transfer_size (L132-L133). Which is the count transferred and which the '
                  'total was measured on the four images tested: of the 461 rows whose Remote '
                  'Name appears in events 59, 60 or 61 of the '
                  'Microsoft-Windows-Bits-Client/Operational log, the first number equals a '
                  'bytesTransferred value those events give for that URL on 445, and the second'
                  ' equals a bytesTotal value on 305 of the 310 where it is known, so they are '
                  'reported as Bytes Transferred and Bytes Total. Either number is left blank '
                  'where the record stores all bits set, the value the BITS headers define as '
                  'BG_SIZE_UNKNOWN (MinGW-w64 bits.h, '
                  'https://github.com/mingw-w64/mingw-w64/blob/4564ee4b5063097bf747af3a3f8270a28adff820/mingw-w64-headers/include/bits.h#L95)'
                  ' and Microsoft documents as the size when BITS cannot determine it '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/bits/ns-bits-bg_file_progress.md?plain=1#L59-L61);'
                  ' on the images tested only Bytes Total held it, on 217 of the 650 rows. File'
                  " ID is the Id of the file's record in the Files table. A live record has "
                  "one, and so does a copy found with the table record's bytes around its blob;"
                  ' other copies have none. 181 of the 650 rows carry one. Job ID and Job Name '
                  'name each job whose list of file GUIDs includes the File ID, so a row '
                  'without a File ID is linked to no job; 3 rows with a File ID had no job '
                  'listing it. Remote Name is the URL the record stores. Of the (job, URL) '
                  'pairs in events 59, 60 and 61 whose job has a linked row, the event URL '
                  "matched a linked row's Remote Name on 94 and differed on 2, both on "
                  'LoneWolf, where the event URL was on another host and carried a '
                  'cms_redirect=yes parameter. On the four images tested, Drive was C:\\ on '
                  'every row except 3 LoneWolf rows, which held \\\\?\\C:\\, and Volume held one '
                  'value on every row of each image. Record Status was Recovered on every row '
                  "of LoneWolf, PC-MUS-001 and Szechuan. Compared with FireEye's BitsParser at "
                  'commit 0a2b51eeec79c5e181d8fc526d5715552299c45f carving the same files, '
                  'every URL it reported is reported here; 15 URLs are reported here and not by'
                  ' BitsParser, 13 of which appear in the BITS-Client events.',
        "paths": ('*/ProgramData/Microsoft/Network/Downloader/*',),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 13 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 212 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 392 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 33 rows",
            "dleapp_macos_bigsur": ("macOS 11.2.1 build 20D74 | 0 rows (no member matches "
                                    "the declared paths)"),
        },
    },
}

# BG_JOB_STATE, BG_JOB_TYPE and BG_JOB_PRIORITY, in the order Microsoft's bits.h pages give
# them (see the notes).
_STATES = ('Queued', 'Connecting', 'Transferring', 'Suspended', 'Error', 'Transient Error',
           'Transferred', 'Acknowledged', 'Cancelled')
_TYPES = ('Download', 'Upload', 'Upload Reply')
_PRIORITIES = ('Foreground', 'High', 'Normal', 'Low')
_DATABASE = 'qmgr.db'
# BG_SIZE_UNKNOWN, defined as (UINT64)(-1) in bits.h (see the notes).
_SIZE_UNKNOWN = 0xFFFFFFFFFFFFFFFF
_SEARCHED = ('.db', '.log', '.jrs')
_JOB_FIELDS = ('marker', 'type', 'priority', 'state', 'unknown', 'job_id', 'name', 'description',
               'program', 'parameters', 'owner', 'flags')
_FILE_FIELDS = ('local_name', 'remote_name', 'temporary_name', 'size_1', 'size_2', 'drive',
                'volume')


def _named(value, names):
    return f'{names[value]} ({value})' if value < len(names) else str(value)


def _size(value):
    """A stored 64-bit size: '' for BG_SIZE_UNKNOWN, and text for any other value SQLite
    cannot hold as an integer."""
    if value == _SIZE_UNKNOWN:
        return ''
    return value if value < 1 << 63 else str(value)


def _job_key(job):
    return (tuple(job[field] for field in _JOB_FIELDS)
            + (tuple(job['file_ids']), tuple(job['times']), tuple(job['errors'])))


def _file_key(record):
    return tuple(record[field] for field in _FILE_FIELDS)


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


class _Version:
    """One distinct job or file record, with where its copies were found."""

    def __init__(self, record):
        self.record = record
        self.live = False
        self.record_ids = []
        self.places = []
        self.copies = 0

    def add(self, place, copy=True):
        if place not in self.places:
            self.places.append(place)
        self.copies += copy

    def add_id(self, record_id):
        if record_id and record_id not in self.record_ids:
            self.record_ids.append(record_id)

    def status(self):
        return 'Live' if self.live else 'Recovered'


def _collect(context, label):
    """[(job versions, file versions)] for each Downloader folder found."""
    folders = OrderedDict()
    for path in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isfile(path):
            folders.setdefault(os.path.dirname(path), []).append(path)
    results = []
    for folder, paths in folders.items():
        jobs, files = OrderedDict(), OrderedDict()
        prefix = '' if len(folders) == 1 else context.get_relative_path(folder) + '/'
        database = next((p for p in paths if os.path.basename(p).lower() == _DATABASE), None)
        if database:
            _live(context, label, database, prefix, jobs, files)
        for path in paths:
            name = os.path.basename(path)
            if not name.lower().endswith(_SEARCHED):
                continue
            found_jobs = found_files = 0
            try:
                data = _read(path)
            except OSError as exc:
                logfunc(f'{label}: could not read {context.get_relative_path(path)}: {exc}')
                continue
            for _, kind, record in find_records(data):
                if kind == 'job':
                    jobs.setdefault(_job_key(record), _Version(record)).add(prefix + name)
                    found_jobs += 1
                else:
                    version = files.setdefault(_file_key(record), _Version(record))
                    version.add(prefix + name)
                    version.add_id(record['file_id'])
                    found_files += 1
            if found_jobs or found_files:
                logfunc(f'{label}: {context.get_relative_path(path)}: {found_jobs:,} job and '
                        f'{found_files:,} file records found')
        results.append((jobs, files))
    return results


def _live(context, label, database, prefix, jobs, files):
    """Add the records of the Jobs and Files tables to the versions."""
    relative = context.get_relative_path(database)
    try:
        db = QmgrDatabase(database)
        tables = (('Jobs', db.records('Jobs'), parse_job, _job_key, jobs),
                  ('Files', db.records('Files'), parse_file, _file_key, files))
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # The vendored ESE reader raises bare Exception for pages it cannot read.
        logfunc(f'{label}: could not read the tables of {relative}: {exc}')
        return
    for table, records, parse, key, versions in tables:
        counts = {'live': 0, 'flagged deleted': 0, 'not read': 0}
        for record_id, blob, deleted in records:
            if deleted:
                # ESE does not show a record flagged deleted (see the notes). Any copy of its
                # bytes still in the file is found by the search like any other record.
                counts['flagged deleted'] += 1
                continue
            record = parse(blob) if blob else None
            if record is None:
                counts['not read'] += 1
                continue
            version = versions.setdefault(key(record), _Version(record))
            version.live = True
            counts['live'] += 1
            version.add_id(record_id)
            version.add(prefix + os.path.basename(database), copy=False)
        logfunc(f'{label}: {relative}: {table} table records: '
                + ', '.join(f'{count:,} {what}' for what, count in counts.items()))


@artifact_processor
def bitsJobs(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'Job Name',
                    'Job ID', 'State', 'Type', 'Priority', 'Owner SID', 'Description',
                    'Notify Program', 'Notify Parameters', 'Notify Flags', 'File Count',
                    'File IDs', 'Error Codes', 'Record Status', 'Found In', 'Copies')
    data_list = []
    for jobs, _ in _collect(context, 'BITS Jobs'):
        for version in jobs.values():
            job = version.record
            times = job['times']
            data_list.append((
                filetime(times[0]) if times else '', filetime(times[1]) if times else '',
                job['name'], guid_text(job['job_id']), _named(job['state'], _STATES),
                _named(job['type'], _TYPES), _named(job['priority'], _PRIORITIES), job['owner'],
                job['description'], job['program'], job['parameters'], job['flags'],
                len(job['file_ids']), '\n'.join(guid_text(i) for i in job['file_ids']),
                '\n'.join(f'0x{code:08X}' for code in job['errors']),
                version.status(), '\n'.join(version.places), version.copies))
    data_list.sort(key=lambda row: (str(row[0]), str(row[1]), row[3]))
    return data_headers, data_list, _sources(context)


@artifact_processor
def bitsJobFiles(context):
    data_headers = ('Remote Name', 'Local Name', 'Temporary Name', 'Bytes Transferred',
                    'Bytes Total', 'File ID', 'Job ID', 'Job Name', 'Drive', 'Volume',
                    'Record Status', 'Found In', 'Copies')
    data_list = []
    for jobs, files in _collect(context, 'BITS Job Files'):
        owners = {}
        for version in jobs.values():
            for file_id in version.record['file_ids']:
                owners.setdefault(file_id, OrderedDict())[
                    (guid_text(version.record['job_id']), version.record['name'])] = None
        for version in files.values():
            record = version.record
            linked = OrderedDict()
            for file_id in version.record_ids:
                linked.update(owners.get(file_id, {}))
            data_list.append((
                record['remote_name'], record['local_name'], record['temporary_name'],
                _size(record['size_1']), _size(record['size_2']),
                '\n'.join(guid_text(i) for i in version.record_ids),
                '\n'.join(job_id for job_id, _ in linked), '\n'.join(name for _, name in linked),
                record['drive'], record['volume'], version.status(),
                '\n'.join(version.places), version.copies))
    data_list.sort(key=lambda row: (row[0], row[1], row[5]))
    return data_headers, data_list, _sources(context)


def _sources(context):
    return '\n'.join(sorted(str(f) for f in context.get_files_found()
                            if os.path.isfile(str(f)) and str(f).lower().endswith(_SEARCHED)))
