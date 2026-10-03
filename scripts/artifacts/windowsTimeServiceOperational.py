"""Time service operational event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-Time-Service record of the provider's Operational event log: the system time the
service set with the time it replaced, the time sources it reports, and the provider's other events of that log.
The Event IDs, the message text and the field names are sourced in the notes.
"""

import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Time Service Operational Events'
_LOG = 'Microsoft-Windows-Time-Service%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Time-Service'

# The fields shown as times when their text reads as one, and the fields with a text column of their own; any
# other field, and a time field whose text does not read as a time, goes to Other Fields.
_TIMES = ('NewTime', 'OldTime')
_SHOWN = ('TimeSource', 'AllNtpServers', 'ChosenReferenceNtpServer')
_STAMP = re.compile(r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?Z')

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '257': 'W32time service has started at %1 (UTC), System Tick Count %2.',
    '258': 'W32time service is stopping at %1 (UTC), System Tick Count %2 with return code: %3',
    '259': 'NTP Client provider periodic status:',
    '260': 'W32time Service periodic configuration and status message',
    '261': 'W32time service has set the system time to %1(UTC).',
    '262': 'W32time service has adjusted the system clock rate by %1 PPM and the new nominal clock rate is %2.',
    '263': 'W32time Service configuration parameters have been updated.',
    '264': 'NTP Client observed a change peer reachability.',
    '265': 'The time service is now synchronizing the system time with the reference time source %1 with '
           'reference id %2.',
    '266': 'W32time Service received notification to rediscover its time sources and/or resynchronize time.',
    '267': 'NTP provider is receiving timestamps from the network stack.',
    '268': 'NTP provider is not receiving any timestamps from the network stack, which may result in lowered '
           'time sync accuracy.',
    '272': 'Leap second configuration:',
    '273': 'A leap second will be %1 at %2 UTC (%3 local time).',
    '274': 'The time provider %4 has signaled a leap second should be %1 at %2 UTC (%3 local time).',
    '275': 'Per configuration, W32time service attempted to add a leap second %1 UTC to local settings.',
    '276': 'The local system data indicates that a leap second will be %1 at %2 UTC (%3 local time).',
    '279': 'W32time could not update the local system time data on leap seconds.',
    '281': 'The local system clock requires a frequency correction of approximately %1 parts per million (PPM).',
    '282': 'The local system clock required an average frequency correction of %1 parts per million (PPM) '
           'over the past %2 minutes.',
    '283': 'Inconsistent timekeeping or a time jump has been detected.',
    '284': 'Secure time message: %1',
}


__artifacts_v2__ = {
    "timeServiceOperationalEvents": {
        "name": "Time Service Operational Events",
        "description": "Microsoft-Windows-Time-Service records of the provider's Operational event log, such as the "
                       "system time the service set with the time it replaced and the time source it reports, with "
                       "each record's other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Time-Service%4Operational.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-Time-Service, "
                 "whatever its Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 22 events to "
                 "this log's channel, each version 0 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1140-L1504 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1518-L1581; "
                 "the entry between the two ranges, 280, goes to the System channel). The manifests of Windows 10 "
                 "builds 16299.15, 17763.107 and 19041.208 and Windows 11 build 22621.819 hold 10, 16, 18 and 21 of "
                 "them "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1140-L1355, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1140-L1474, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1140-L1504, "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1140-L1504 "
                 "with "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Time-Service.xml#L1518-L1568), "
                 "with the same message and fields except 259, whose message and fields on build 16299.15 have no "
                 "IFTSTMP. These are the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for "
                 "the record's Event ID, the first sentence of the first line of the build 26100 message: the first "
                 "line that holds more than white space, with each run of white space made one space, cut after the "
                 "first period that a space or the end of the line follows (whole when it has none), with its "
                 "placeholders (such as %1) as the manifest writes them. A placeholder is an insertion string for a "
                 "data item of the event's template by its position (Microsoft's Defining Events page: 'to include "
                 "the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is blank for an Event ID outside the 22, which no tested record had. "
                 "New Time (UTC) and Old Time (UTC) are the NewTime and OldTime fields of 261, whose message begins "
                 "'W32time service has set the system time to %1(UTC). Previous system time was %2(UTC).'. The "
                 "fields are text of the form YYYY-MM-DDTHH:MM:SS.mmmZ in which the one to three digits after the "
                 "period are a count of milliseconds written without leading zeros, so '.45' is 45 milliseconds: 11 "
                 "of the 98 tested values have two digits, and read as milliseconds each of the 98 is within a "
                 "millisecond of a time in Windows System Time Changes, while read as a decimal fraction none of the "
                 "11 is. A text with no period and digits would be read as a whole second, and a value of another "
                 "form (more than three digits after the period, or not such a time) leaves its column blank and is "
                 "listed in Other Fields; no tested value was either. Each of the 49 tested rows of 261 has a row in "
                 "Windows System Time Changes (Kernel-General event 1 of the System log) with the same two times to "
                 "the millisecond and the reason 'An application or system component changed the time (1)'. Event "
                 "Time (UTC) is within 0.015 seconds of New Time (UTC) on each, and the Time Zone row of Windows "
                 "System Information names Pacific or Eastern time on the four images, with an active bias of 4 to 8 "
                 "hours, so the texts are in UTC as the message says. New Time is later than Old Time on 28 rows, "
                 "earlier on 10 and the same to the millisecond on 11; the two differ by a second or more on 11 "
                 "rows, a minute or more on 4 and an hour or more on 2 (28,800.872 seconds at most, on "
                 "af_case2_win10). Time Source is the TimeSource field (265), NTP Servers the AllNtpServers field "
                 "(259 and 264) and Reference NTP Server the ChosenReferenceNtpServer field (259), as stored. Time "
                 "Source is time.windows.com,0x9 followed by ' (ntp.m|0x9|' on 13 tested rows and "
                 "CITADEL-DC01.C137.local followed by ' (ntp.d|' on 3 rows of szechuan_win10, each then holding two "
                 "IPv4 addresses with ports joined by '->' and a closing parenthesis; what ntp.m, ntp.d and 0x9 "
                 "stand for, and which address is which, is not established here. Each of the 16 rows of 265 has a "
                 "35 row in Windows Time Service Events within a second. On 28 of the 32 rows of 259 NTP Servers is "
                 "a semicolon alone and Reference NTP Server is blank. Other Fields lists every other named field "
                 "that holds more than white space as 'name: value', in the record's order, joined with ' | '. Each "
                 "value is as python-evtx renders it with any white space at either end removed; 207 tested values "
                 "had some (Configuration and TimeProviders on 95 records each and Source on 17). The Configuration "
                 "and TimeProviders values (257, 260 and 263) hold line breaks on each of the 95 tested records, and "
                 "the line breaks inside a value are kept. The CurrentTime(UTC) field of 257 and 258 stays in Other "
                 "Fields as text; it has the same form as NewTime, 3 of the 30 tested values with fewer than three "
                 "digits after the period, and read the same way each of the 30 is within a millisecond of Event "
                 "Time (UTC). ReasonCode of 266 held 0, 1, 2 or 3 (13, 89, 75 and 11 rows); what the numbers stand "
                 "for is not established here. A data item that has no name is not shown, and no tested record had "
                 "one. If a record named a field twice the last would be read. The tested records carried the field "
                 "names their image's build manifest gives the event. Tested on the logs of four public images "
                 "(af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; "
                 "szechuan_win10, build 19041), which gave 44, 57, 296 and 80 rows in that order; the two captures "
                 "of a Windows 11 build 26200 machine hold no such log. Of the 477 rows 188 are 266, 58 are 272, 49 "
                 "are 261, 42 are 263, 32 are 259, 31 are 264, 29 are 260, 24 are 257, 16 are 265, 6 are 258 and 2 "
                 "are 262. The other 11 events are unexercised, among them 283, whose message begins 'Inconsistent "
                 "timekeeping or a time jump has been detected.'. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which scripts/windows_evtx.py renders from the FILETIME the record stores with integer "
                 "arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's "
                 "conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element; User SID held one value, S-1-5-19, on "
                 "every tested row. Record ID is the record's EventRecordID and Computer the machine name the record "
                 "stores, which held one value on af_case2_win10 and pc_mus_001_win11 and two on lonewolf_win10 and "
                 "szechuan_win10. Rows are in the order the file holds them, which was rising Record ID on every "
                 "tested log; in time order 8 rows are earlier than the row before them (1 on af_case2_win10, 6 on "
                 "lonewolf_win10 and 1 on szechuan_win10), each a row of 261: 3 of them record a New Time 3,599.618 "
                 "seconds or more before Old Time, and the 5 others, on lonewolf_win10, are 0.001 seconds or less "
                 "before the row above. Every record of the tested logs rendered and is the provider's. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. A log marked dirty is read past the chunks its header counts, and the run log says how "
                 "many records came from there. Reading needs the python-evtx package (pip install python-evtx). Not "
                 "read: the provider's events in the System log; Windows Time Service Events reports seven of them.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 44 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 57 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 296 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 80 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Time-Service%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "clock",
    },
}


def utc_time(text):
    """A 'YYYY-MM-DDTHH:MM:SS.mmmZ' text as an aware UTC time, or None.

    The one to three digits after the period are a count of milliseconds, which the service writes without
    leading zeros (see notes): '.45' is 45 milliseconds.
    """
    found = _STAMP.fullmatch(text)
    if found is None:
        return None
    year, month, day, hour, minute, second = (int(part) for part in found.group(1, 2, 3, 4, 5, 6))
    micro = int(found.group(7) or '0') * 1000
    try:
        return datetime(year, month, day, hour, minute, second, micro, tzinfo=timezone.utc)
    except ValueError:
        return None


def time_service_row(record):
    times, unread = [], []
    for name in _TIMES:
        when = utc_time(record.get(name))
        times.append('' if when is None else when)
        if when is None:
            unread.append(name)
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if record.get(name) and (name in unread or name not in _TIMES + _SHOWN))
    return (record.time, *times, record.event_id, _EVENTS.get(record.event_id, ''),
            *(record.get(name) for name in _SHOWN), other, record.user_sid, record.record_id, record.computer)


@artifact_processor
def timeServiceOperationalEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), ('New Time (UTC)', 'datetime'), ('Old Time (UTC)', 'datetime'),
                    'Event ID', 'Event', 'Time Source', 'NTP Servers', 'Reference NTP Server', 'Other Fields', 'User SID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [time_service_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
