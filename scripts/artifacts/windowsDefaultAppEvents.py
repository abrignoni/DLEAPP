"""Default app event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-Shell-Core record of the provider's AppDefaults event log: the file extension or URL
scheme and the program ID of a default app that was set or reset for an account, and the log's other text entries.
The Event IDs, the message text and the field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Default App Events'
_LOG = 'Microsoft-Windows-Shell-Core%4AppDefaults.evtx'
_PROVIDER = 'Microsoft-Windows-Shell-Core'

# The fields that have a column of their own; any other field goes to Other Fields.
_ASSOCIATION = 'ExtOrUriScheme'
_PROGRAM = 'ProgId'
_INFO = 'Info'

# Event ID: the first sentence of the provider's message for it (see notes).
_EVENTS = {
    '62440': 'Hash mismatch detected for: %1.',
    '62441': 'User choice has been reset to prog id %1 for %2.',
    '62442': 'Upgraded to prog id %1 from prog id %2 for %3',
    '62443': 'AppDefault Info: %1',
    '62444': 'Missing Hash -- ProgId: %1 FileExtOrUriScheme: %2',
    '62445': 'Migration Info: %1',
}


__artifacts_v2__ = {
    "defaultAppEvents": {
        "name": "Default App Events",
        "description": "Microsoft-Windows-Shell-Core records of the provider's AppDefaults event log, such as a "
                       "default program set for a file extension or URI scheme with its program ID, with each "
                       "record's Info text and other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Shell-Core%4AppDefaults.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-Shell-Core, whatever "
                 "its Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 6 events to this log's "
                 "channel, each version 0 and level Information: 62440, 62441, 62442, 62443, 62444 and 62445 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L37447-L37546). "
                 "The manifest of Windows 11 build 22621.819 holds the first 5 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L37442-L37527) "
                 "and those of Windows 10 builds 16299.15, 17763.107 and 19041.208 the first 4 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L37504-L37563, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L37476-L37535 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L37491-L37550). "
                 "These are the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for the "
                 "record's Event ID, the first sentence of the build 26100 message: the message with each run of "
                 "white space made one space, cut after the first period that a space or the end of the message "
                 "follows, with its placeholders (such as %1) as the manifest writes them. A placeholder is an "
                 "insertion string for a data item of the event's template by its position (Microsoft's Defining "
                 "Events page: 'to include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. The three Windows 10 manifests word two events differently: the message of "
                 "62441 is 'User choice has been reset to prog id %1 for %2' with nothing after it, and that of "
                 "62440 begins 'User choice hash mismatch detected for: %1.'. They also give 62441 two fields "
                 "(ProgId and ExtOrUriScheme) where builds 22621 and 26100 give it four (adding CurrentDefaultProgId "
                 "and ShouldToast), and 62440 two fields where those builds give it eleven. Event is blank for an "
                 "Event ID outside the 6, which no tested record had. Association is the record's ExtOrUriScheme "
                 "field and Program ID its ProgId field when the record carries either of them (62440, 62441, 62442 "
                 "and 62444 in the manifests). Info is the record's Info field (62443 and 62445). For a record that "
                 "carries neither ExtOrUriScheme nor ProgId and whose Info begins 'SetDefault: Association=' or "
                 "'SetDefault-Info: Association=', Association is the text after that up to the first ', ProgId=' "
                 "and Program ID the text after it, which in a SetDefault-Info text ends before the last ', U=' it "
                 "holds; a text with no ', ProgId=' gives neither, and Info holds the whole text either way. Other "
                 "Fields lists every other named field that holds more than white space as 'name: value', in the "
                 "record's order, joined with ' | '. Other Fields held no value on any tested row: the tested 62441 "
                 "records carry only the two fields of the Windows 10 manifests. Each value is as python-evtx "
                 "renders it with any white space at either end removed, and no tested value had any. A data item "
                 "that has no name is not shown, and no tested record had one. If a record named a field twice the "
                 "last would be read. The tested records carried the field names their image's build manifest gives "
                 "the event. Tested on the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, "
                 "build 16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 221, 231, 199 "
                 "and 929 rows in that order; the two captures of a Windows 11 build 26200 machine hold no such log. "
                 "1,563 of the 1,580 rows are 62443 and 17 are 62441 (4, 9, 0 and 4). 62440, 62442, 62444 and 62445 "
                 "are unexercised, and so is the four-field form of 62441. On pc_mus_001_win11 Event ID held one "
                 "value, 62443, Event held one value and User SID held one value, one account, on all 199 rows. The "
                 "Info text of the 62443 rows, counted by the text before its first colon (the whole text when it "
                 "has none): 'SetDefault' 707, 'SetDefault-Info' 706, 'AppDefaults-Logon-UpgradeDefault' 55, "
                 "'AppDefaults-Logon-UserProfileLoaded' 45, 'File Association hash version is still the same' 18, "
                 "'Querying default browser info' 15, 'AppDefaults-Logon-UserProfileCreated' 6, 'File Association "
                 "hash version updated' 4, 'Update user choices before CDefaultAssociationsProfileHandler' 4, "
                 "'AppDefaults-Logon-ApplyDefaultsOnUpgrade' 1, and 2 that begin 'SetDefault-Error(' with a number. "
                 "No source that documents these texts was found; they are reported as stored. A SetDefault text has "
                 "the form 'SetDefault: Association=<association>, ProgId=<program ID>' and a SetDefault-Info text "
                 "adds ', U=<u>, T=<t>, H=<h>'. Each of the 706 SetDefault-Info rows comes directly after a "
                 "SetDefault row with the same Association, Program ID and User SID, at most 0.035 seconds later; "
                 "the one SetDefault row that has none (lonewolf_win10) is followed by the 2 SetDefault-Error rows. "
                 "On all 706, U equals the row's User SID and H is 12 characters of base64 that decode to 8 bytes. T "
                 "is six numbers joined by colons that equal the year, month, day of the week (Sunday as 0), day, "
                 "hour and minute of Event Time (UTC) on 705 rows and those of the minute before on 1; the 62440 "
                 "template of builds 22621 and 26100 names six date fields in that order (SystemDate.wYear, wMonth, "
                 "wDayOfWeek, wDay, wHour and wMinute). The four machines were set to Pacific or Eastern time (the "
                 "Time Zone row of Windows System Information), 4 to 8 hours from UTC, so T is not a local time. "
                 "Association begins with a period, as a file extension does, on 650 of the 707 SetDefault rows; on "
                 "the other 57 it is a name without one, such as http, https, mailto or ftp. The tested registry "
                 "hives agree with these rows. Taking the last SetDefault-Info row of each account and association "
                 "gives 700 pairs (6 rows are followed by a later one for the same pair). 684 pairs belong to an "
                 "account whose NTUSER.DAT the image holds, the account's SID matched to its profile folder through "
                 "the User Profile List artifact. For each of the 684 that hive holds a UserChoice key for the "
                 "association, under Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\<association> when "
                 "the association begins with a period and under "
                 "Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\<association> when it does not, "
                 "whose ProgId value equals Program ID, whose Hash value equals H and whose last written time falls "
                 "in the minute T gives. The other 16 pairs belong to accounts with no NTUSER.DAT in the image. This "
                 "artifact does not read the registry. The SetDefault and SetDefault-Info texts do not say what made "
                 "a change. 679 of the 707 SetDefault rows fall in a minute in which the same account has 20 or more "
                 "of them (111 at most), and 8 are the only one of their account in their minute. Each of the 17 "
                 "rows of 62441 has an Association (an extension on 13) and a Program ID, and a SetDefault row with "
                 "the same Association and Program ID lies within three rows of it; User SID is S-1-5-18 on 8 of "
                 "them and an S-1-5-21 account on 9. On pc_mus_001_win11 each of the 55 "
                 "'AppDefaults-Logon-UpgradeDefault: current=<current>, new=<new>' rows (17 with nothing after "
                 "'current=') comes directly before a SetDefault row whose Program ID is the text after 'new='. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element: an S-1-5-21 account on 1,556 tested rows "
                 "(2, 2, 1 and 5 accounts) and S-1-5-18 on 24. Record ID is the record's EventRecordID and Computer "
                 "the machine name the record stores, which held one value on af_case2_win10 and pc_mus_001_win11 "
                 "and two on lonewolf_win10 and szechuan_win10. Rows are in the order the file holds them, which was "
                 "rising Record ID on every tested log; in time order 1 row of lonewolf_win10 is earlier than the "
                 "row before it. Every record of the tested logs rendered and is the provider's. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. A log marked dirty is read past the chunks its header counts, and the run log says how "
                 "many records came from there. Reading needs the python-evtx package (pip install python-evtx). Not "
                 "read: the events these manifests send to the provider's other channels (Operational, Diagnostic, "
                 "LogonTasksChannel and ActionCenter).",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 221 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 231 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 199 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 929 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Shell-Core%4AppDefaults.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "settings",
    },
}


def set_default(info):
    """The association and the program ID a 'SetDefault: ' or 'SetDefault-Info: ' text names, else two empty strings."""
    head, _, rest = info.partition(': ')
    if head not in ('SetDefault', 'SetDefault-Info') or not rest.startswith('Association='):
        return '', ''
    association, found, rest = rest[len('Association='):].partition(', ProgId=')
    if not found:
        return '', ''
    if head == 'SetDefault-Info':
        before, cut, _ = rest.rpartition(', U=')
        if cut:
            rest = before
    return association, rest


def default_app_row(record):
    info = record.get(_INFO)
    if _ASSOCIATION in record.fields or _PROGRAM in record.fields:
        association, program = record.get(_ASSOCIATION), record.get(_PROGRAM)
    else:
        association, program = set_default(info)
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in (_ASSOCIATION, _PROGRAM, _INFO) and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), association, program, info, other,
            record.user_sid, record.record_id, record.computer)


@artifact_processor
def defaultAppEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Association', 'Program ID', 'Info',
                    'Other Fields', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [default_app_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
