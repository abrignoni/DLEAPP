"""Windows BITS client Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Bits-Client/Operational: job created (3), job transfer
finished (4), job cancelled (5), transfer started and stopped (59, 60, 61) and
event 16403, whose fields name a job's remote and local file. Event IDs, field
names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import hex_status, read_event_records

_LOG = 'Microsoft-Windows-Bits-Client%4Operational.evtx'

# Message text from the Bits-Client provider manifest (see notes). The manifest
# gives 16403 no message text.
_EVENTS = {
    '3': 'The BITS service created a new job',
    '4': 'The transfer job is complete',
    '5': 'Job cancelled',
    '59': 'BITS started the transfer job',
    '60': 'BITS stopped transferring the transfer job',
    '61': 'BITS stopped transferring the transfer job (warning level)',
    '16403': '(no message text in the provider manifest)',
}

__artifacts_v2__ = {
    "bitsClientEvents": {
        "name": "BITS Client Transfer Events",
        "description": "Background Intelligent Transfer Service job and transfer "
                       "events from the Bits-Client Operational log: job title, "
                       "owner, URL, local file name, bytes and status code as each "
                       "record stores them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Bits-Client%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-Bits-Client records "
                 "with Event ID 3, 4, 5, 59, 60, 61 or 16403 are read. Event is a short "
                 "form of the provider manifest's message: 3 'The BITS service created a "
                 "new job', 4 'The transfer job is complete', 5 'Job cancelled', 59 'BITS "
                 "started the transfer job', and 60 and 61 'BITS stopped transferring the "
                 "transfer job', 61 at Warning level; the manifest dump gives 16403 no "
                 "message, only field names (manifest as registered on Windows 11 build "
                 "22621.819, published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Bits-Client.xml#L175-L334, "
                 "#L768-L920 and #L2001-L2019). Job Title is jobTitle, or name on 59 to "
                 "61; Job ID is jobId, or Id on 59 to 61; URL is url, or RemoteName on "
                 "16403; Local File is LocalName, which only 16403 carries; Job Owner, "
                 "User, Process Path, Process ID, Bytes Total, Bytes Transferred and File "
                 "Count are jobOwner, User, processPath, processId, bytesTotal, "
                 "bytesTransferred and fileCount; Status Code is hr, which the manifest "
                 "formats as hexadecimal, shown as hex with the stored decimal. Every "
                 "value is reported as stored. Local File was filled on the 173 16403 rows "
                 "of pc_mus_001_win11 and is empty on af_case2_win10 and lonewolf_win10, "
                 "which carry no 16403 records. Bytes Total held 18446744073709551615, the "
                 "largest unsigned 64-bit number, on 79 of 116 rows on af_case2_win10, 20 "
                 "of 871 on pc_mus_001_win11 and 43 of 156 on lonewolf_win10; the manifest "
                 "dump gives no description of that value. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. Not reported: the "
                 "transfer ID, peer, proxy, bandwidth and remote file time and length "
                 "fields, and the log's other events. A record python-evtx cannot render, "
                 "or whose XML does not parse, is counted in the run log and not reported; "
                 "every record in this log rendered on the registered images. On the job "
                 "created (3) rows, Job Owner was an NT AUTHORITY account on 10 of 18 on "
                 "af_case2_win10, 13 of 174 on pc_mus_001_win11 and 10 of 28 on "
                 "lonewolf_win10; a row does not by itself establish that a person started "
                 "the transfer. Reading needs the python-evtx package (pip install "
                 "python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Bits-Client%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 871 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 116 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 156 rows",
        },
    },
}


@artifact_processor
def bitsClientEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Job Title',
                    'Job ID', 'Job Owner', 'User', 'URL', 'Local File',
                    'Process Path', 'Process ID', 'Status Code', 'Bytes Total',
                    'Bytes Transferred', 'File Count', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'BITS Client Transfer Events', event_ids=set(_EVENTS),
        provider='Microsoft-Windows-Bits-Client')
    data_list = []
    for record in records:
        title = record.get('jobTitle') or record.get('name')
        job_id = record.get('jobId') or record.get('Id')
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id], title, job_id,
            record.get('jobOwner'), record.get('User'),
            record.get('url') or record.get('RemoteName'), record.get('LocalName'),
            record.get('processPath'), record.get('processId'), hex_status(record.get('hr')),
            record.get('bytesTotal'), record.get('bytesTransferred'),
            record.get('fileCount'), record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
