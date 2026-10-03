"""Windows Time service event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads seven Microsoft-Windows-Time-Service events of the System event log: the
service began synchronizing with a time source (35), is receiving valid time
data from one (37), set the time with an offset (52), found a change larger
than it will make (34), could not set a peer (129, 134), or a time provider
stopped (158). Event IDs, field names and message text are sourced in the
notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Windows Time Service Events'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-Time-Service'

# Event ID: the opening words of the provider's message for it (see notes).
_EVENTS = {
    '34': 'The time service has detected that the system time needs to be changed',
    '35': 'The time service is now synchronizing the system time with the time source',
    '37': 'The time provider NtpClient is currently receiving valid time data',
    '52': 'The time service has set the time with offset',
    '129': 'NtpClient was unable to set a domain peer to use as a time source because of discovery error',
    '134': 'NtpClient was unable to set a manual peer to use as a time source because of DNS resolution error',
    '158': 'The time provider has indicated that the current hardware and operating environment is not supported '
           'and has stopped',
}
# The field each event names its source, peer or provider in, and the field that holds its seconds.
_SOURCE_FIELD = {'34': 'TimeSource', '35': 'TimeSource', '37': 'TimeSource', '134': 'DomainPeer',
                 '158': 'TimeProvider'}
_SECONDS_FIELD = {'34': 'SystemTimeChangeSeconds', '52': 'TimeOffsetSeconds'}

__artifacts_v2__ = {
    "windowsTimeServiceEvents": {
        "name": "Windows Time Service Events",
        "description": "Microsoft-Windows-Time-Service events of the System event log: the service began "
                       "synchronizing with a time source (35), is receiving valid time data from one (37), set the "
                       "time with an offset (52), detected a needed change against its limit (34), could not set a "
                       "peer (129, 134) or a time provider stopped (158), with the source, peer or provider named "
                       "and the seconds, error and retry minutes the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-Time-Service and whose Event ID is 34, 35, 37, 52, "
                 "129, 134 or 158. Other providers use those Event IDs in the same log (1, 54, 13 and 0 records on "
                 "the four public images named below), so both are checked. The provider's manifest sends the seven "
                 "events to the System channel with the messages \"The time service has detected that the system time "
                 "needs to be changed by %1 seconds. The time service will not change the system time by more than "
                 "%2 seconds. Verify that your time and time zone are correct, and that the time source %3 is "
                 "working properly.\" (34, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L495-L509), "
                 "\"The time service is now synchronizing the system time with the time source %1 with reference id "
                 "%2. Current local stratum number is %3.\" (35, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L510-L524), "
                 "\"The time provider NtpClient is currently receiving valid time data from %1.\" (37, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L539-L551), "
                 "\"The time service has set the time with offset %1 seconds.\" (52, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L739-L751), "
                 "\"NtpClient was unable to set a domain peer to use as a time source because of discovery error. "
                 "NtpClient will try again in %2 minutes and double the reattempt interval thereafter. The error "
                 "was: %1\" (129, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L778-L791), "
                 "\"NtpClient was unable to set a manual peer to use as a time source because of DNS resolution error "
                 "on '%3'. NtpClient will try again in %2 minutes and double the reattempt interval thereafter. The "
                 "error was: %1\" (134, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L852-L866) "
                 "and \"The time provider '%1' has indicated that the current hardware and operating environment is "
                 "not supported and has stopped. This behavior is expected for VMICTimeProvider on non-HyperV-guest "
                 "environments. This may be the expected behavior for the current provider in the current operating "
                 "environment as well.\" (158, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1114-L1126). "
                 "These are the entries of the Microsoft-Windows-Time-Service manifest as registered on Windows 11 "
                 "build 22621.819, published in nasbench's EVTX-ETW-Resources repository; the manifests that "
                 "repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 hold the same seven "
                 "entries at the same lines "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Time-Service.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Time-Service.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Time-Service.xml). "
                 "Event is the opening words of that message; for 158 it is the first sentence without the quoted "
                 "provider name. Source, Peer or Provider is the field TimeSource on 34, 35 and 37, DomainPeer on "
                 "134 and TimeProvider on 158, and is blank on 52 and 129, to which the manifest gives none of the "
                 "three. Reference ID (as stored) and Stratum are TimeSourceRefId and CurrentStratumNumber, which "
                 "the manifest gives 35. Seconds is SystemTimeChangeSeconds on 34 and TimeOffsetSeconds on 52, and "
                 "Limit Seconds is MaxSystemTimeChangeSeconds, which the manifest gives 34. Error and Retry Minutes "
                 "are ErrorMessage and RetryMinutes, which it gives 129 and 134. Each is as python-evtx renders it "
                 "with any white space at either end removed (no tested value had any), and a column whose field the "
                 "record does not carry is blank. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of one Windows 11 "
                 "build 26200 ARM64 virtual machine (windows11_arm_4688_known and windows11_arm_known_20261001). The "
                 "four public images gave 15, 22, 76 and 16 rows in that order and the captures 124 and 126, every "
                 "row of the first capture being a row of the second. Counting the rows the captures share once, the "
                 "six logs hold 255 rows, every record version 0: 104 of 37, 35 of 35, 60 of 134, 45 of 158 (8 on "
                 "lonewolf_win10 and 37 on pc_mus_001_win11), 2 of 129 (on szechuan_win10), 6 of 34 and 3 of 52 "
                 "(both on the captures only). Seconds and Limit Seconds are therefore blank on every row of the "
                 "four public images. On all 145 rows of 34, 35 and 37 Source, Peer or Provider is a name, then in "
                 "brackets ntp.m (137 rows) or ntp.d (8 rows, all on szechuan_win10), a local address and port, an "
                 "arrow and a remote address and port; on the ntp.m rows a comma and a value beginning 0x follow the "
                 "name, and on the ntp.d rows they do not. The local address was 0.0.0.0 and both ports 123 on every "
                 "one. What ntp.m and ntp.d stand for is not sourced here. On all 35 rows of 35 Reference ID (as "
                 "stored) is a whole number equal to the four bytes of that remote address read least significant "
                 "byte first. On all 60 rows of 134 the column is a name, a comma and a value beginning 0x "
                 "(time.windows.com,0x9 on the 35 rows of the public images), and on all 45 rows of 158 it is "
                 "VMICTimeProvider. Retry Minutes held one value, 15, on every row that has one. On the public "
                 "images Error was 'No such host is known. (0x80072AF9)' on the 35 rows of 134 and 'The entry is not "
                 "found. (0x800706E1)' on the 2 rows of 129; Error held one value on every row that has one of each "
                 "capture. Limit Seconds held one value, 54000, on the 6 rows of 34, and Seconds was a smaller whole "
                 "number on each of them (0 on 4). Stratum held one value on af_case2_win10 (3, on its 1 row of 35) "
                 "and on pc_mus_001_win11 (4, on its 5 rows), and Reference ID (as stored) held one value on "
                 "af_case2_win10. Each of the 3 rows of 52 has a Windows System Time Changes row within a "
                 "millisecond of it, and that row's Previous Time (UTC) is later than its New Time (UTC) by the "
                 "Seconds value once the fraction of a second is dropped. No tested 52 row had a Seconds value below "
                 "zero, so what a negative offset looks like is unexercised. Rows are in the order the log file "
                 "holds its records, which was rising Record ID on every tested log. Event Time (UTC) rises with it "
                 "except for 1 row on af_case2_win10, 1 on lonewolf_win10, 1 on szechuan_win10 and 3 on each capture "
                 "that are earlier than the row before them. Computer held one value on every row of af_case2_win10, "
                 "pc_mus_001_win11 and each capture; lonewolf_win10 and szechuan_win10 hold two names. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. Every record of the tested logs rendered, among them the 72 TPM event 27 records of each "
                 "capture's log, which python-evtx renders only with the array value types scripts/windows_evtx.py "
                 "adds. A log marked dirty is read past the chunks its header "
                 "counts, and the run log says how many records came from there. Reading needs the python-evtx "
                 "package (pip install python-evtx). Not read: the provider's other events, 70 more of which the "
                 "build 22621 manifest sends to the System channel. No tested System log held one.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 124 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 126 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 76 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 15 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 22 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 16 rows",
        },
    },
}


def time_service_row(record):
    event_id = record.event_id
    source = record.get(_SOURCE_FIELD[event_id]) if event_id in _SOURCE_FIELD else ''
    seconds = record.get(_SECONDS_FIELD[event_id]) if event_id in _SECONDS_FIELD else ''
    return (record.time, event_id, _EVENTS[event_id], source,
            record.get('TimeSourceRefId'), record.get('CurrentStratumNumber'), seconds,
            record.get('MaxSystemTimeChangeSeconds'), record.get('ErrorMessage'),
            record.get('RetryMinutes'), record.record_id, record.computer)


@artifact_processor
def windowsTimeServiceEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Source, Peer or Provider',
                    'Reference ID (as stored)', 'Stratum', 'Seconds', 'Limit Seconds', 'Error',
                    'Retry Minutes', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids=set(_EVENTS),
                                          provider=_PROVIDER)
    data_list = [time_service_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
