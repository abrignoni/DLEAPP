"""Windows User Profile Service Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-User Profile Service/Operational: user logon (1) and
logoff (3) notifications with their session, user registry hives loaded (5)
and the logon type, local profile location and profile type of a logon (67).
Event IDs, field names and message text are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-User Profile Service%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-User Profiles Service'

# The provider's message for each event with its inserted values removed (see notes).
_EVENTS = {
    '1': 'Received user logon notification',
    '3': 'Received user logoff notification',
    '5': 'Registry file is loaded',
    '67': 'Logon type, local profile location and profile type',
}

__artifacts_v2__ = {
    "userProfileServiceEvents": {
        "name": "User Profile Service Events",
        "description": "User logon and logoff notifications, registry hive loads under HKU "
                       "and the logon type and local profile location of a logon, from the "
                       "User Profile Service Operational log, with the session, SID, hive "
                       "file and profile path each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-User Profile Service%4Operational.evtx, named in the "
                 "report's located-at line; only Microsoft-Windows-User Profiles Service records with "
                 "Event ID 1, 3, 5 or 67 are read. Event is the provider's message for the event with its "
                 "inserted values, and the clauses that hold them, removed: 1 'Received user logon "
                 "notification' and 3 'Received user logoff notification' (the provider's text spells it "
                 "'Recieved'), 5 'Registry file is loaded' (the message is 'Registry file %1 is loaded at "
                 "HKU\\%2.') and 67 'Logon type, local profile location and profile type' (manifest as "
                 "registered on Windows 11 build 22621.819, published in nasbench's EVTX-ETW-Resources "
                 "repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-User%20Profiles%20Service.xml#L81-L93, "
                 "#L107-L119, #L133-L146 and #L412-L428; the same messages and fields were read from "
                 "profsvc.dll and its en-US .mui on the tested images). Session is Session on 1 and 3. "
                 "Hive File and HKU Key are File and Key on 5: the file the message says was loaded, and "
                 "the key under HKU it was loaded at. Logon Type, Profile Location and Profile Type are "
                 "LogonType, LocalPath and ProfileType on 67, as stored; Logon Type and Profile Type held "
                 "'Regular' on every 67 row of the tested images, so the two columns are identical on "
                 "each. User SID is the SID the record's Security element stores: on every 1 and 3 row of "
                 "the tested images it was an account SID (S-1-5-21-...), and on every 5 and 67 row it was "
                 "S-1-5-18. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer "
                 "arithmetic, counted in UTC and cut to whole microseconds, in place of python-evtx "
                 "0.8.1's conversion through a floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the record stores: "
                 "it held one value on every row of af_case2_win10 and pc_mus_001_win11, and two on "
                 "lonewolf_win10 and szechuan_win10. A 1 or 3 row records a notification the service "
                 "received for the session; it does not record how the user logged on. Not reported: 2 and "
                 "4, which record the end of processing of the notification 1 and 3 record; on the tested "
                 "images each followed its 1 or 3, with the same session and SID, within 1.2 seconds. Also "
                 "not reported: the log's other events, of which the tested images carried one, a 59 on "
                 "szechuan_win10. A record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported; every record in this log rendered on the tested "
                 "images. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/"
                  "Microsoft-Windows-User Profile Service%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "log-in",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 93 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 25 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 54 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 60 rows",
        },
    },
}


def profile_row(record):
    """One User Profile Service record as a report row.

    Each field is defined on one of the events read (Session on 1 and 3, File and Key on
    5, LogonType, LocalPath and ProfileType on 67), so a field an event lacks is blank.
    """
    return (record.time, record.event_id, _EVENTS[record.event_id], record.user_sid,
            record.get('Session'), record.get('File'), record.get('Key'),
            record.get('LogonType'), record.get('LocalPath'), record.get('ProfileType'),
            record.record_id, record.computer)


@artifact_processor
def userProfileServiceEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'User SID', 'Session',
                    'Hive File', 'HKU Key', 'Logon Type', 'Profile Location', 'Profile Type',
                    'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'User Profile Service Events', event_ids=set(_EVENTS), provider=_PROVIDER)
    return data_headers, [profile_row(record) for record in records], '\n'.join(sources)
