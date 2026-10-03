"""Event log service event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Microsoft-Windows-Eventlog records of the Security and System event logs other than the two log cleared
events, which the Event Logs Cleared artifact reports: the event logging service shutting down, audit events being
dropped, a log being full or backed up, and the service's errors. The Event IDs, the message text and the field
names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Event Log Service Events'
_LOGS = ('security.evtx', 'system.evtx')
_PROVIDER = 'Microsoft-Windows-Eventlog'

# The log cleared events, which the Event Logs Cleared artifact reports.
_NOT_READ = ('1102', '104')

# (Event ID, version): the first sentence of the provider's message for it, placeholders as written (see notes).
_EVENTS = {
    ('20', '0'): ('The event logging service encountered an error %1 while obtaining or processing configuration '
                  'for channel %2.'),
    ('21', '0'): 'The event logging service encountered a configuration-related error (res=%1) for channel %2.',
    ('22', '0'): ('The event logging service encountered an error while initializing publishing resources for '
                  'channel %2.'),
    ('23', '0'): ('The event logging service encountered an error (res=%1) while initializing logging resources for '
                  'channel %2.'),
    ('25', '0'): 'The event logging service encountered a corrupt log file for channel %1.',
    ('26', '0'): 'The event logging service encountered a log file for channel %1 which is an unsupported version.',
    ('27', '0'): 'The event logging service encountered an error (res=%1) while opening log file for channel %2.',
    ('27', '1'): ('The event logging service encountered an error (res=%1) while opening log file for channel %2 at '
                  '%3.'),
    ('28', '0'): 'The event logging service encountered an error (res=%1) while parsing filter for channel %2.',
    ('29', '0'): ('The event logging service encountered a fatal error (res=%1) when applying settings to the %2 '
                  'channel.'),
    ('30', '0'): 'The event logging service encountered an error (%1) while enabling publisher %3 to channel %2.',
    ('31', '0'): ('The event logging service encountered an error (res=%1) while opening configuration for primary '
                  'channel %2.'),
    ('40', '0'): ('The event logging service encountered an error when attempting to apply one or more policy '
                  'settings.'),
    ('105', '0'): 'Event log automatic backup Log: %1 File: %2',
    ('106', '0'): 'Corruption was detected in the log for the %1 channel and some data was erased.',
    ('108', '0'): 'The previous system shutdown was unexpected.',
    ('1100', '0'): 'The event logging service has shut down.',
    ('1101', '0'): 'Audit events have been dropped by the transport.',
    ('1103', '0'): 'The security log is now %1 percent full.',
    ('1104', '0'): 'The security log is now full.',
    ('1105', '0'): 'Event log automatic backup Log: %1 File: %2',
    ('1106', '0'): 'Events have been dropped by the event logging service.',
    ('1107', '0'): ('The event logging service encountered an error while processing an incoming event from '
                    'publisher %3 and trying to process the metadata for it.'),
    ('1108', '0'): ('The event logging service encountered an error while processing an incoming event published '
                    'from %3.'),
    ('6000', '0'): 'The %1 log file is full.',
}

__artifacts_v2__ = {
    "eventLogServiceEvents": {
        "name": "Event Log Service Events",
        "description": "Microsoft-Windows-Eventlog records of the Security and System event logs other than the log "
                       "cleared events: the event logging service shutting down, audit events dropped, a log full or "
                       "backed up and the service's errors, with each record's named fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Security.evtx and System.evtx the paths match with python-evtx and reports, one row "
                 "per record, the records whose provider is Microsoft-Windows-Eventlog, whatever their Event ID, but "
                 "1102 and 104: those are the log cleared events, which the Event Logs Cleared artifact reports. "
                 "Apart from those two events, the provider's manifest sends 25 entries to the Security and System "
                 "channels. To Security: 'The event logging service has shut down.' (1100, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L704-L716), "
                 "'Audit events have been dropped by the transport. %1' (1101, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L717-L730), "
                 "1103 to 1107 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L777-L853) "
                 "and 'The event logging service encountered an error while processing an incoming event published "
                 "from %3.' (1108, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L854-L869). "
                 "To System: 20 to 23, 25 to 29, with 27 in versions 0 and 1 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L155-L315), "
                 "'The event logging service encountered an error (%1) while enabling publisher %3 to channel %2. "
                 "This does not affect channel operation, but does affect the ability of the publisher to raise "
                 "events to the channel. One common reason for this error is that the Provider is using ETW Provider "
                 "Security and has not granted enable permissions to the Event Log service identity.' (30, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L316-L332), "
                 "31 and 40 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L333-L363), "
                 "105 and 106 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L451-L482), "
                 "108 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L498-L520) "
                 "and 6000 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Eventlog.xml#L870-L882). "
                 "These are entries of the provider's manifest as registered on Windows 11 build 26100.1742, "
                 "published in nasbench's EVTX-ETW-Resources repository. Event is, for the record's Event ID and "
                 "version, the message's first sentence: the message with each run of white space made one space, "
                 "cut after the first period that a space or the end of the message follows, with its placeholders "
                 "(such as %1) as the manifest writes them. A placeholder is an insertion string for a data item of "
                 "the event's template by its position (Microsoft's Defining Events page: 'to include the third data "
                 "item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is blank for an Event ID and version outside the 25 entries, which no "
                 "tested record had. The manifests that repository publishes for Windows 10 builds 16299.15, "
                 "17763.107 and 19041.208 and Windows 11 build 22621.819 hold 24, 25, 25 and 25 of the 25 entries, "
                 "each with the same message, fields and channel; build 16299.15 lacks version 1 of 27 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Eventlog.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Eventlog.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Eventlog.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Eventlog.xml). "
                 "No manifest of build 26200, the captures' build, was read. Log is the record's Channel element. "
                 "Fields lists every named field that holds more than white space as 'name: value', by the names the "
                 "record carries, in the record's order, joined with ' | '; each value is as python-evtx renders it "
                 "with any white space at either end removed, and no tested value had any. A data item that has no "
                 "name is not shown, and no tested record had one. If a record named a field twice the last would be "
                 "read. The tested records carried the field names the manifest lists for their event, but for the "
                 "1108 record of szechuan_win10, which names its third field PublisherID where the manifests read "
                 "name it PubID. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a "
                 "floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element, blank when the record stores none. Record "
                 "ID is the record's EventRecordID and Computer the machine name the record stores. Tested on the "
                 "logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of a Windows 11 "
                 "build 26200 machine, which gave 19, 3, 8, 7, 9 and 2 rows in that order. The rows are 19, 3, 7, 6 "
                 "and 6 of 1100 on the first five logs, 1 of 1101 on pc_mus_001_win11 (Fields is Reason: 0) and 1 on "
                 "the first capture, 1 of 1108 on szechuan_win10 and 2 of 30 on each capture, each record version 0; "
                 "the 30 rows are the only ones from a System log. The second capture's Security log holds 2 "
                 "records, one of them the 1102 that the Event Logs Cleared artifact reports, and gives no Security "
                 "row. The other 21 entries are unexercised. Every one of the 41 rows of 1100 is within five seconds "
                 "(0.502 seconds at most) of an EventLog 6006 record in the System log of the same image or capture "
                 "(The event log service was stopped, which the Windows System Power Events artifact reports). In "
                 "the other direction 19 of 19, 3 of 3, 7 of 9, 6 of 6 and 6 of 75 such records have a 1100 row that "
                 "near, and every one of the 71 that has none is older than the oldest record of the Security log "
                 "beside it. Log held one value, Security, on each of the four public images. Event ID and Event "
                 "held one value on af_case2_win10 and lonewolf_win10, whose rows are all 1100, and Fields is blank "
                 "on every row of those two. User SID is blank on every row from a Security log and held one value, "
                 "S-1-5-19, on the 30 rows. Computer held one value on pc_mus_001_win11 and on each capture, two on "
                 "af_case2_win10 and lonewolf_win10 and three on szechuan_win10. Rows are the Security log's records "
                 "and then the System log's, each in the order the file holds them, which was rising Record ID "
                 "within every tested log; in time order 1 row each of af_case2_win10, lonewolf_win10, "
                 "szechuan_win10 and the first capture is earlier than the row before it. Every record of the tested "
                 "logs rendered, among them the 72 TPM event 27 records of each capture's System log, which "
                 "python-evtx renders only with the array value types scripts/windows_evtx.py adds. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted "
                 "in the run log and not reported. A log marked dirty is read past the chunks its header counts, and "
                 "the run log says how many records came from there. Reading needs the python-evtx package (pip "
                 "install python-evtx). Not read: 1102 and 104, and the provider's events in its other channels "
                 "(Setup, Microsoft-Windows-EventLog/Debug and Microsoft-Windows-EventLog/Analytic).",
        "paths": ('*/Windows/System32/winevt/Logs/Security.evtx', '*/Windows/System32/winevt/Logs/System.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 9 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 8 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 7 rows",
        },
    },
}


def service_row(record):
    fields = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields if record.get(name))
    return (record.time, record.channel, record.event_id, _EVENTS.get((record.event_id, record.version), ''), fields,
            record.user_sid, record.record_id, record.computer)


@artifact_processor
def eventLogServiceEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Log', 'Event ID', 'Event', 'Fields', 'User SID', 'Record ID',
                    'Computer')
    data_list = []
    sources = []
    for file_name in _LOGS:
        records, read = read_event_records(context, file_name, _LABEL, provider=_PROVIDER)
        data_list.extend(service_row(record) for record in records if record.event_id not in _NOT_READ)
        sources.extend(read)
    return data_headers, data_list, '\n'.join(sources)
