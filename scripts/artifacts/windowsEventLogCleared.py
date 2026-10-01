"""Windows event log cleared records for DLEAPP.

Author: @AlexisBrignoni, Claude.

The event log service (provider Microsoft-Windows-Eventlog) records the clearing of
a log in two places: event 1102 in the Security log when the Security log itself is
cleared, and event 104 in the System log when another log is cleared. Both carry a
LogFileCleared block. The fields were measured on known data made on a Windows 11
lab machine (see the artifact notes).
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_EVENTLOG = 'Microsoft-Windows-Eventlog'
_LABEL = 'Event Logs Cleared'

__artifacts_v2__ = {
    "eventLogsCleared": {
        "name": "Event Logs Cleared",
        "description": "Records of an event log being cleared, from the Security log (event 1102) and the "
                       "System log (event 104): the time, the log cleared, the account the record names, "
                       "the backup path where one is stored, and the client process ID the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from the Security and System event logs, named in the report's located-at line. Each row is "
                 "one record the event log service (provider Microsoft-Windows-Eventlog) wrote when a log was "
                 "cleared: event 1102 in the Security log and event 104 in the System log, the two events "
                 "Velociraptor's Windows.EventLogs.Cleared artifact reads (Velociraptor, "
                 "'Windows.EventLogs.Cleared', "
                 "https://github.com/Velocidex/velociraptor/blob/74d2e0a9442f93f2ddedeca16436e7499209bcb6/artifacts/definitions/Windows/EventLogs/Cleared.yaml#L5-L6). "
                 "Microsoft documents 1102 as written every time the Security audit log is cleared, with the SID, "
                 "name, domain and logon ID of the account that cleared it (Microsoft, '1102(S): The audit log was "
                 "cleared.', as updated 27 April 2026, "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-1102). "
                 "No Microsoft description of event 104 was found, so its columns rest on the known data below. Rows "
                 "are in time order, and a record whose time does not parse is listed last. Log Cleared is the "
                 "record's Channel field, which a 104 record holds, and otherwise the channel the record itself is "
                 "in, the reading that artifact uses "
                 "(https://github.com/Velocidex/velociraptor/blob/74d2e0a9442f93f2ddedeca16436e7499209bcb6/artifacts/definitions/Windows/EventLogs/Cleared.yaml#L36). "
                 "Account Name, Account Domain, Logon ID, Backup Path and Client Process ID are the SubjectUserName, "
                 "SubjectDomainName, SubjectLogonId, BackupPath and ClientProcessId fields as stored, blank where "
                 "the record has none. Account SID is the SubjectUserSid field and, where the record has none, the "
                 "user ID in the record's header "
                 "(https://github.com/Velocidex/velociraptor/blob/74d2e0a9442f93f2ddedeca16436e7499209bcb6/artifacts/definitions/Windows/EventLogs/Cleared.yaml#L39). "
                 "On windows11_arm_known_20261001, known data made on a Windows 11 build 26200 VM on 1 October 2026, "
                 "wevtutil cleared the Internet Explorer log without a backup, the Key Management Service log with a "
                 "backup and the Security log with a backup, in that order, from one elevated session, and the 3 "
                 "rows are those three clears. The System log gained 2 event 104 records, for the first two, and "
                 "none for the Security log. The Security log exported after the clear holds 2 records, the first of "
                 "them the 1102, where the backup wevtutil took at the clear holds 22,524. Each row's Event Time is "
                 "30 to 46 ms after the time logged just before its command started and no more than 1 ms after the "
                 "time logged when the command returned. Account Name, Account Domain, Account SID and Computer each "
                 "held one value on all 3 rows: the name, domain and SID are those of the account that ran the "
                 "commands. Account SID came from SubjectUserSid on the 1102 row, whose header carries no user ID, "
                 "and from the header's user ID on the two 104 rows, which have no SubjectUserSid field. Logon ID is "
                 "filled on the 1102 row only. Backup Path is blank on the Internet Explorer row and holds the path "
                 "given to wevtutil on the Key Management Service row; it is blank on the Security row although that "
                 "log was also cleared with a backup, because the 1102 record has no BackupPath field. Client "
                 "Process ID on each row equals the New Process ID of the Security 4688 record for the wevtutil.exe "
                 "that ran that clear, timed 14 to 32 ms before the row, and all three 4688 records carry the "
                 "Subject Logon ID the 1102 row holds. The 4688 record for the Security clear is timed before the "
                 "1102 record and follows it in the cleared log. The ClientProcessStartKey field is not reported. "
                 "Microsoft's example 1102 record, from 2015, has no ClientProcessId field, so Client Process ID can "
                 "be blank on other versions of Windows; only build 26200 was tested. The Security and System logs "
                 "of af_case2_win10, lonewolf_win10, szechuan_win10, pc_mus_001_win11 and windows11_arm_4688_known "
                 "hold no 1102 or 104 record from this provider, so those images give no rows. A row is the event "
                 "log service's record that the named log was cleared under the named account; it does not show who "
                 "was using that account. Reading the logs needs the python-evtx package.",
        "paths": ("*/Windows/System32/winevt/Logs/Security.evtx",
                  "*/Windows/System32/winevt/Logs/System.evtx"),
        "output_types": ["standard"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 3 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def cleared_row(record):
    return (record.time, record.event_id, record.get('Channel') or record.channel,
            record.get('SubjectUserName'), record.get('SubjectDomainName'),
            record.get('SubjectUserSid') or record.user_sid, record.get('SubjectLogonId'),
            record.get('BackupPath'), record.get('ClientProcessId'), record.computer,
            record.record_id)


def _in_time_order(records):
    """Oldest first; a record whose time did not parse goes last, in the order read."""
    dated = [r for r in records if r.time != '']
    undated = [r for r in records if r.time == '']
    return sorted(dated, key=lambda r: r.time) + undated


@artifact_processor
def eventLogsCleared(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Log Cleared', 'Account Name',
                    'Account Domain', 'Account SID', 'Logon ID', 'Backup Path', 'Client Process ID',
                    'Computer', 'Event Record ID')
    records = []
    for file_name, event_id in (('security.evtx', '1102'), ('system.evtx', '104')):
        found, _sources = read_event_records(context, file_name, _LABEL, event_ids={event_id},
                                             provider=_EVENTLOG)
        records.extend(found)
    data_list = []
    sources = []
    for record in _in_time_order(records):
        data_list.append(cleared_row(record))
        if record.source not in sources:
            sources.append(record.source)
    return data_headers, data_list, '\n'.join(sources)
