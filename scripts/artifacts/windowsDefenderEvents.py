"""Microsoft Defender Antivirus Operational event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Windows Defender/Operational: malware and suspicious
behavior detections and the actions taken on them, quarantine restores and
deletions (1006 to 1011, 1015, 1116 to 1119); protection and configuration
changes and detection history removal (5000, 5001, 5004, 5007, 5010, 5012, 5013,
1013); and antimalware scans (1000, 1001, 1002). Event IDs, messages and field
meanings are sourced in the notes. A field holding a parameter reference (%%n)
is given the text of that message from the English MpEvMsg.dll.mui of the same
volume, when one is there; see _ParameterText.
"""

import collections
import os

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records

_LOG = 'Microsoft-Windows-Windows Defender%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Windows Defender'

# Messages from Microsoft's Defender Antivirus event ID documentation (see notes).
_DETECTION_EVENTS = {
    '1006': 'The antimalware engine found malware or other potentially unwanted software',
    '1007': 'The antimalware platform performed an action to protect your system from '
            'malware or other potentially unwanted software',
    '1008': 'The antimalware platform attempted to perform an action to protect your '
            'system from malware or other potentially unwanted software, but the action failed',
    '1009': 'The antimalware platform restored an item from quarantine',
    '1011': 'The antimalware platform deleted an item from quarantine',
    '1015': 'The antimalware platform detected suspicious behavior',
    '1116': 'The antimalware platform detected malware or other potentially unwanted software',
    '1117': 'The antimalware platform performed an action to protect your system from '
            'malware or other potentially unwanted software',
    '1118': 'The antimalware platform attempted to perform an action to protect your '
            'system from malware or other potentially unwanted software, but the action failed',
    '1119': 'The antimalware platform encountered a critical error when trying to take '
            'action on malware or other potentially unwanted software',
}
_PROTECTION_EVENTS = {
    '5000': 'Real-time protection is enabled',
    '5001': 'Real-time protection is disabled',
    '5004': 'The real-time protection configuration changed',
    '5007': 'The antimalware platform configuration changed',
    '5010': 'Scanning for malware and other potentially unwanted software is disabled',
    '5012': 'Scanning for viruses is disabled',
    '5013': 'Tamper protection blocked a change to Microsoft Defender Antivirus',
    '1013': 'The antimalware platform deleted history of malware and other potentially '
            'unwanted software',
}
_SCAN_EVENTS = {
    '1000': 'An antimalware scan started',
    '1001': 'An antimalware scan finished',
    '1002': 'An antimalware scan was stopped before it finished',
}
# The 1116 to 1119 events carry these field names; 1006 to 1015 name theirs
# differently (see _first below).
_STATE_EVENTS = ('1116', '1117', '1118', '1119')
# Every field the cited manifest defines for 1000, 1001 and 1002. A field a scan
# record carries beyond these is reported in Other Fields, by name, as stored.
_SCAN_FIELDS = frozenset((
    'Product Name', 'Product Version', 'Scan ID', 'Scan Type Index', 'Scan Type',
    'Scan Parameters Index', 'Scan Parameters', 'Domain', 'User', 'SID', 'Scan Resources',
    'Scan Time Hours', 'Scan Time Minutes', 'Scan Time Seconds'))

__artifacts_v2__ = {
    "defenderDetections": {
        "name": "Microsoft Defender Detection Events",
        "description": "Microsoft Defender Antivirus detection, action and "
                       "quarantine events from the Defender Operational log, with "
                       "the threat name, severity, path, process, detection source "
                       "and action of each record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx; pefile to give parameter references their text",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Windows Defender%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Windows Defender "
                 "records with Event ID 1006, 1007, 1008, 1009, 1011, 1015, 1116, 1117, "
                 "1118 or 1119 are read. Event is the message Microsoft documents for the "
                 "Event ID, the first sentence of it for 1119 (Microsoft Learn, 'Review "
                 "event logs and error codes to troubleshoot issues with Microsoft "
                 "Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260908060019/https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). "
                 "Field names are those of the provider manifest (manifest as registered "
                 "on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L230-L437, "
                 "#L489-L537 and #L640-L989). On 1116 to 1119, Threat Name, Threat ID, "
                 "Severity, Category, Path, Process Name, Detection Source, Detection "
                 "Origin, Detection Type, Action and Status are Threat Name, Threat ID, "
                 "Severity Name, Category Name, Path, Process Name, Source Name, Origin "
                 "Name, Type Name, Action Name and Additional Actions String, the fields "
                 "the 1117 to 1119 messages print as Name, ID, Severity, Category, Path, "
                 "Process Name, Detection Source, Detection Origin, Detection Type, Action "
                 "and Action Status (the 1116 message prints all but the last two); User "
                 "is Detection User on 1116 and Remediation User on 1117 to 1119, the "
                 "field each message prints as User. On 1006 to 1015, User is Domain and "
                 "User joined with a backslash, as their messages print it, and User SID "
                 "is the SID field, which 1116 to 1119 do not carry; Path is Path Found on "
                 "1006 and 1015 and Path on the others; Action is Cleaning Action; Status "
                 "is Execution Status on 1006 and 1015 and Status Description on 1007 and "
                 "1008. Error Code, Error Description, Detection Time (as stored), "
                 "Detection ID and Engine Version are the fields of those names. Security "
                 "Intelligence Version is the Security intelligence Version field, also "
                 "read under the name Signature Version, which the same template position "
                 "carries in the published manifests of Windows 10 builds 10240, "
                 "14393.447, 16299.15, 17134.112 and 17763.107 (for example "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L769, "
                 "against #L769 of the Windows 11 manifest above; the two templates differ "
                 "in no other field this artifact reads) and in the records of the "
                 "defender_evtx_attack_samples log. A column whose field the manifest does "
                 "not give an event is blank on that event's rows. Every value is reported as "
                 "stored, except a parameter reference, as described below. Defender platform "
                 "4.18.1906.3, which wrote the records of the "
                 "defender_evtx_attack_samples log, stores Detection Source, Detection "
                 "Origin, Detection Type and Action as a reference of the form %%818 "
                 "rather than as text. Microsoft's documentation describes a parameter "
                 "string of the form %%n as the identifier of a message in the message "
                 "table of the provider's parameter file (Microsoft Learn, 'ProviderType "
                 "complex type', "
                 "https://learn.microsoft.com/en-us/windows/win32/wes/eventmanifestschema-providertype-complextype), "
                 "and the Defender provider's registration in the SOFTWARE hive names "
                 "MpEvMsg.dll as that file: the copy under Program Files/Windows Defender on "
                 "af_case2_win10 and lonewolf_win10, and the copy under "
                 "ProgramData/Microsoft/Windows Defender/Platform/4.18.2211.5-0 on "
                 "pc_mus_001_win11. A field that holds only such a reference is reported as the "
                 "text of that message followed by the reference, for example Real-Time "
                 "Protection (%%818), when an English (en-US) MpEvMsg.dll.mui on the volume the "
                 "log was read from holds the message: the copy under "
                 "ProgramData/Microsoft/Windows Defender/Platform in the folder named for the "
                 "record's Product Version, or else the copy under Program Files/Windows "
                 "Defender. The text is the message as FormatMessage prints it, without its "
                 "closing line break or a closing %0 escape, which ends a message without a new "
                 "line (Microsoft Learn, 'FormatMessage function', "
                 "https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-formatmessage); "
                 "every message referenced on the registered images and in the public samples "
                 "ends with one. A reference no such file resolves is reported as stored. The "
                 "run log counts the references given text from each file and those left as "
                 "stored, and the report's located-at line also names each MpEvMsg.dll.mui that "
                 "gave text. The copy for the record's own version comes first because a "
                 "message's wording can change between versions: of the 184 message ids in the "
                 "six English copies on the registered images, 43 read differently in at least "
                 "two of them, for example 827, which is Windows Defender Antivirus in the "
                 "copies on af_case2_win10 and lonewolf_win10 and Microsoft Defender Antivirus "
                 "in those on pc_mus_001_win11. The defender_evtx_attack_samples log comes "
                 "without an MpEvMsg.dll.mui, so its references are reported as stored, and no "
                 "detection record on the registered images or in the two public samples has had "
                 "a reference given text; the scan artifact's rows on af_case2_win10 and "
                 "lonewolf_win10 exercise the same code. The English MpEvMsg.dll.mui copies on "
                 "af_case2_win10, lonewolf_win10 and pc_mus_001_win11 all give %%818 as "
                 "Real-Time Protection, %%845 as Local machine, %%822 as Concrete, %%823 as "
                 "Generic, %%862 as FastPath, %%887 as Not Applicable, %%809 as Quarantine and "
                 "%%811 as Allow. No field of any record written by platform 4.18.2210.6 or "
                 "4.18.2211.5 on pc_mus_001_win11 holds such a reference; none of those "
                 "records is a detection event, so whether newer platforms store these "
                 "four fields as text is not established. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the "
                 "record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores. None of the three registered Windows disk images "
                 "carries a record with any of these Event IDs. The "
                 "defender_evtx_attack_samples log, a public research sample, carries 11 "
                 "(six 1116 and five 1117), and every value reported on those rows matched "
                 "the record field the mapping above names. On those 11 rows Process Name, "
                 "Detection Source, Detection Origin, Status and Computer each held one "
                 "value, and User SID was empty, since 1116 and 1117 carry no SID field. "
                 "The 1006 to 1015, 1118 and 1119 branches were run only on records "
                 "constructed for the purpose, not on a record Defender wrote. Not "
                 "reported: the product name and version, the ID and index fields beside "
                 "the names, the FWLink, the Status Code, Status Description, State, "
                 "Execution Name, Pre Execution Status and Post Clean Status fields of "
                 "1116 to 1119, and on 1015 the process ID, security intelligence ID, "
                 "fidelity, image hash and target file fields. A record python-evtx cannot "
                 "render, or whose XML does not parse, is counted in the run log and not "
                 "reported. python-evtx 0.8.1 rendered every record of this log on the "
                 "registered Windows disk images and in the defender_evtx_attack_samples "
                 "log, and none of the 6 records of the defender_evtx_to_mitre log, "
                 "another public sample whose file and chunk checksums all match, so that "
                 "log gives no rows. A detection row records what Defender logged; it does "
                 "not by itself establish who placed the file or ran the process. Reading needs "
                 "the python-evtx package (pip install python-evtx); giving references their "
                 "text needs the pefile package (pip install pefile), and without it they are "
                 "reported as stored.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx",
                  "*/Program Files/Windows Defender/en-US/MpEvMsg.dll.mui",
                  "*/ProgramData/Microsoft/Windows Defender/Platform/*/en-US/MpEvMsg.dll.mui"),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no detection or quarantine events in the Defender Operational log)",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no detection or quarantine events in the Defender Operational log)",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no detection or quarantine events in the Defender Operational log)",
                           "defender_evtx_attack_samples": "Defender Operational log only, Defender platform 4.18.1906.3 | 11 rows",
                           "defender_evtx_to_mitre": "Defender Operational log only | 0 rows (python-evtx 0.8.1 renders none of the log's 6 records)",
                       },
    },
    "defenderProtectionChanges": {
        "name": "Microsoft Defender Protection and Configuration Changes",
        "description": "Microsoft Defender Antivirus real-time protection, scanning "
                       "and configuration change events and detection history "
                       "removal events from the Defender Operational log, with the "
                       "old and new configuration values 5007 records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx; pefile to give parameter references their text",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Windows Defender%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Windows Defender "
                 "records with Event ID 5000, 5001, 5004, 5007, 5010, 5012, 5013 or 1013 "
                 "are read. Event is the message Microsoft documents for the Event ID "
                 "(Microsoft Learn, 'Review event logs and error codes to troubleshoot "
                 "issues with Microsoft Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260908060019/https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). "
                 "Old Value and New Value are the Old Value and New Value fields of 5007, "
                 "which that page describes as the old and new antivirus configuration "
                 "values. Detail is Feature Name and Configuration on 5004, Changed Type "
                 "and Value on 5013, and Timestamp, Domain and User joined with a "
                 "backslash, and SID on 1013, each as 'name: value'. Product Version is "
                 "the Product Version field. Field names are those of the provider "
                 "manifest (manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L589-L613 "
                 "and #L2221-L2380), which gives 5000, 5001, 5010 and 5012 no fields "
                 "beyond the product name and version, so their Old Value, New Value and "
                 "Detail are blank. Every value is reported as stored, except that an Old Value "
                 "or New Value holding only a parameter reference, %%n, the identifier of a "
                 "message in the provider's parameter file, MpEvMsg.dll (Microsoft Learn, "
                 "'ProviderType complex type', "
                 "https://learn.microsoft.com/en-us/windows/win32/wes/eventmanifestschema-providertype-complextype), "
                 "is reported as the text of that message followed by the reference, from an "
                 "English (en-US) MpEvMsg.dll.mui on the volume the log was read from: the copy "
                 "under ProgramData/Microsoft/Windows Defender/Platform in the folder named for "
                 "the record's Product Version, or else the copy under Program Files/Windows "
                 "Defender, and otherwise as stored. No row on the registered images holds a "
                 "reference, so no Old Value or New Value has been given text on real data; the "
                 "scan artifact's rows on af_case2_win10 and lonewolf_win10 exercise the same "
                 "code. 5007 was 18 of the "
                 "21 rows on af_case2_win10, 48 of 51 on pc_mus_001_win11 and 10 of 10 on "
                 "lonewolf_win10; Old Value was filled on 15 of the 18 5007 rows on "
                 "af_case2_win10 and 47 of 48 on pc_mus_001_win11, and New Value on 16 of "
                 "18 and 47 of 48. On lonewolf_win10 every row is 5007, so Event ID and "
                 "Event held one value and Detail is empty. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held two values on af_case2_win10 and one value on "
                 "every row of pc_mus_001_win11 and lonewolf_win10. Not reported: the "
                 "product name, the Feature ID of 5004, and the log's other events (1150, "
                 "1151, 2000, 2001, 2002, 2010, 2011 and 2014 on the registered images). A "
                 "record python-evtx cannot render, or whose XML does not parse, is "
                 "counted in the run log and not reported. python-evtx 0.8.1 rendered "
                 "every record of this log on the registered Windows disk images and in "
                 "the defender_evtx_attack_samples log, and none of the 6 records of the "
                 "defender_evtx_to_mitre log, another public sample whose file and chunk "
                 "checksums all match, so that log gives no rows. A 5007 row records a "
                 "configuration value Defender logged as changed; it does not by itself "
                 "establish which person or program changed it. Reading needs the python-evtx "
                 "package (pip install python-evtx); giving references their text needs the "
                 "pefile package (pip install pefile), and without it they are reported as "
                 "stored.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx",
                  "*/Program Files/Windows Defender/en-US/MpEvMsg.dll.mui",
                  "*/ProgramData/Microsoft/Windows Defender/Platform/*/en-US/MpEvMsg.dll.mui"),
        "output_types": ["standard"],
        "artifact_icon": "sliders",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 21 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 51 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 10 rows",
                           "defender_evtx_attack_samples": "Defender Operational log only, Defender platform 4.18.1906.3 | 0 rows (the log holds only 1116 and 1117 records)",
                           "defender_evtx_to_mitre": "Defender Operational log only | 0 rows (python-evtx 0.8.1 renders none of the log's 6 records)",
                       },
    },
    "defenderScans": {
        "name": "Microsoft Defender Scan Events",
        "description": "Microsoft Defender Antivirus scan started, finished and stopped "
                       "events from the Defender Operational log, with the scan type, "
                       "parameters, duration and account of each record.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "python-evtx; pefile to give parameter references their text",
        "category": "Windows",
        "notes": "Read from Microsoft-Windows-Windows Defender%4Operational.evtx, named in "
                 "the report's located-at line; only Microsoft-Windows-Windows Defender "
                 "records with Event ID 1000, 1001 or 1002 are read. Event is the message "
                 "Microsoft documents for the Event ID, and Scan ID, Scan Type, Scan "
                 "Parameters, Scan Resources and the scan time follow that page's "
                 "descriptions (Microsoft Learn, 'Review event logs and error codes to "
                 "troubleshoot issues with Microsoft Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260908060019/https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). "
                 "Field names are those of the provider manifest (manifest as registered "
                 "on Windows 11 build 22621.819, published in nasbench's "
                 "EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Windows%20Defender.xml#L64-L147). "
                 "Scan ID, Scan Type, Scan Parameters and Scan Resources are the fields of "
                 "those names; Scan Time (h:m:s) is Scan Time Hours, Scan Time Minutes and "
                 "Scan Time Seconds of 1001 joined with colons, as stored; User is Domain "
                 "and User joined with a backslash, as the messages print it; User SID is "
                 "the SID field; Product Version is the Product Version field. Other "
                 "Fields (as stored) lists, as 'name: value', any field a record carries "
                 "beyond those the cited manifest defines for 1000 to 1002, other than its "
                 "Unused fields. Other Fields (as stored) was empty on every row of the "
                 "registered images. Every value is reported as stored, except a parameter "
                 "reference, as described below. Scan Resources, "
                 "which only 1000 carries, was empty on every row of the registered "
                 "images. Scan Type, Scan Parameters, User and User SID each held one "
                 "value on every row of pc_mus_001_win11 and lonewolf_win10, and Product "
                 "Version on every row of lonewolf_win10; the two rows on af_case2_win10 "
                 "carry one Scan ID. Defender platforms 4.18.1902.2 and 4.12.17007.18022, "
                 "which wrote the scan records on af_case2_win10 and lonewolf_win10, store "
                 "Scan Type and Scan Parameters as a reference of the form %%802 rather than as "
                 "text: every record on those two images stores %%802 and %%806. "
                 "Microsoft's documentation describes a parameter string of the form %%n "
                 "as the identifier of a message in the message table of the provider's "
                 "parameter file (Microsoft Learn, 'ProviderType complex type', "
                 "https://learn.microsoft.com/en-us/windows/win32/wes/eventmanifestschema-providertype-complextype), "
                 "and the Defender provider's registration in the SOFTWARE hive names "
                 "MpEvMsg.dll as that file: the copy under Program Files/Windows Defender on "
                 "af_case2_win10 and lonewolf_win10, and the copy under "
                 "ProgramData/Microsoft/Windows Defender/Platform/4.18.2211.5-0 on "
                 "pc_mus_001_win11. A field that holds only such a reference is reported as the "
                 "text of that message followed by the reference, for example Antimalware "
                 "(%%802), when an English (en-US) MpEvMsg.dll.mui on the volume the log was "
                 "read from holds the message: the copy under ProgramData/Microsoft/Windows "
                 "Defender/Platform in the folder named for the record's Product Version, or "
                 "else the copy under Program Files/Windows Defender. The text is the message as "
                 "FormatMessage prints it, without its closing line break or a closing %0 "
                 "escape, which ends a message without a new line (Microsoft Learn, "
                 "'FormatMessage function', "
                 "https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-formatmessage); "
                 "every message referenced on the registered images and in the public samples "
                 "ends with one. A reference no such file resolves is reported as stored. The "
                 "run log counts the references given text from each file and those left as "
                 "stored, and the report's located-at line also names each MpEvMsg.dll.mui that "
                 "gave text. The copy for the record's own version comes first because a "
                 "message's wording can change between versions: of the 184 message ids in the "
                 "six English copies on the registered images, 43 read differently in at least "
                 "two of them, for example 827, which is Windows Defender Antivirus in the "
                 "copies on af_case2_win10 and lonewolf_win10 and Microsoft Defender Antivirus "
                 "in those on pc_mus_001_win11. On lonewolf_win10 the records name platform "
                 "4.12.17007.18022, whose folder under Platform holds the English file; the "
                 "folder for 4.18.1902.2, the version the records on af_case2_win10 name, holds "
                 "no MpEvMsg.dll or MpEvMsg.dll.mui, so those records take their text from the "
                 "Program Files copy. On both images that is the text the English copy of the "
                 "registered parameter file gives, since the Platform and Program Files copies "
                 "on lonewolf_win10 are byte-identical. Every row on the two images reads "
                 "Antimalware (%%802) and Quick Scan (%%806), and all six English copies give "
                 "those two references the same text; the records of platforms 4.18.2210.6 and "
                 "4.18.2211.5 on pc_mus_001_win11 store the text Antimalware and Quick Scan in "
                 "those fields. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, which python-evtx renders from the FILETIME the "
                 "record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name "
                 "the record stores: it held one value on every row of each registered "
                 "image. Not reported: the product name and the index field beside the "
                 "scan type and parameters. A record python-evtx cannot render, or whose "
                 "XML does not parse, is counted in the run log and not reported. "
                 "python-evtx 0.8.1 rendered every record of this log on the registered "
                 "Windows disk images and in the defender_evtx_attack_samples log, and "
                 "none of the 6 records of the defender_evtx_to_mitre log, another public "
                 "sample whose file and chunk checksums all match, so that log gives no "
                 "rows. A scan row records a scan Defender logged; the User the record "
                 "names does not by itself establish that a person started the scan. "
                 "Reading needs the python-evtx package (pip install python-evtx); giving "
                 "references their text needs the pefile package (pip install pefile), and "
                 "without it they are reported as stored.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Windows Defender%4Operational.evtx",
                  "*/Program Files/Windows Defender/en-US/MpEvMsg.dll.mui",
                  "*/ProgramData/Microsoft/Windows Defender/Platform/*/en-US/MpEvMsg.dll.mui"),
        "output_types": ["standard"],
        "artifact_icon": "search",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 10 rows",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
                           "defender_evtx_attack_samples": "Defender Operational log only, Defender platform 4.18.1906.3 | 0 rows (the log holds only 1116 and 1117 records)",
                           "defender_evtx_to_mitre": "Defender Operational log only | 0 rows (python-evtx 0.8.1 renders none of the log's 6 records)",
                       },
    },
}


class _ParameterText:
    """Text for the parameter references (%%n) a Defender record stores.

    The text comes from the English (en-US) MpEvMsg.dll.mui on the volume the
    record's log was read from: the copy under ProgramData/Microsoft/Windows
    Defender/Platform in the folder named for the record's Product Version when
    there is one, else the copy under Program Files/Windows Defender. A resolved
    field reads 'text (%%n)'; a reference neither file resolves is kept as stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _INBOX = '/program files/windows defender/en-us/mpevmsg.dll.mui'
    _PLATFORM = '/programdata/microsoft/windows defender/platform/'
    _MESSAGE_FILE = '/en-us/mpevmsg.dll.mui'

    def __init__(self, context, label):
        self.context = context
        self.label = label
        self.inbox = {}        # volume root -> staged path
        self.platform = {}     # (volume root, platform version) -> staged path
        self.tables = {}       # staged path -> {message id: text}
        self.resolved = collections.Counter()
        self.kept = 0
        for path in sorted(str(f) for f in context.get_files_found()):
            relative = self._relative(path)
            if not relative.endswith(self._MESSAGE_FILE) or os.path.isdir(path):
                continue
            if relative.endswith(self._INBOX):
                self.inbox.setdefault(relative[:-len(self._INBOX)], path)
                continue
            at = relative.find(self._PLATFORM)
            if at >= 0:
                folder = relative[at + len(self._PLATFORM):].split('/')[0]
                self.platform.setdefault((relative[:at], folder.rsplit('-', 1)[0]), path)

    def _relative(self, path):
        return '/' + self.context.get_relative_path(path).replace('\\', '/').lower()

    def _message_file(self, record):
        relative = self._relative(record.source) if record.source else ''
        at = relative.find(self._LOG_DIR)
        if at < 0:
            return None
        root = relative[:at]
        version = record.get('Product Version').lower()
        return self.platform.get((root, version)) or self.inbox.get(root)

    def text(self, record, value):
        """The value, or 'text (%%n)' when it is a reference a message file resolves."""
        match = windows_messages.REFERENCE.fullmatch(value or '')
        if not match:
            return value
        path = self._message_file(record)
        if path and path not in self.tables:
            self.tables[path] = windows_messages.read_message_table(path)
        message = self.tables.get(path, {}).get(int(match.group(1))) if path else ''
        if not message:
            self.kept += 1
            return value
        self.resolved[path] += 1
        return f'{message} ({value})'

    def files(self):
        """The message files that gave text to at least one field, for the source path."""
        return sorted(self.resolved)

    def log(self):
        for path, count in sorted(self.resolved.items()):
            logfunc(f'{self.label}: {count} parameter reference(s) given their text from '
                    f'{self.context.get_relative_path(path)}')
        if self.kept:
            missing = '' if windows_messages.pefile else ' (pefile is not installed)'
            logfunc(f'{self.label}: {self.kept} parameter reference(s) reported as stored; '
                    f'no English MpEvMsg.dll.mui on the same volume gave their text{missing}')


def _first(record, *names):
    """The first non-empty named field, as stored."""
    for name in names:
        value = record.get(name)
        if value:
            return value
    return ''


def _domain_user(record):
    domain, user = record.get('Domain'), record.get('User')
    if domain and user:
        return f'{domain}\\{user}'
    return user or domain


def _labelled(record, names):
    """'Name: value' pairs, joined, for the named fields that hold a value."""
    return '; '.join(f'{name}: {record.get(name)}' for name in names if record.get(name))


@artifact_processor
def defenderDetections(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Threat Name',
                    'Threat ID', 'Severity', 'Category', 'Path', 'Process Name', 'User',
                    'User SID', 'Detection Source', 'Detection Origin', 'Detection Type', 'Action',
                    'Status', 'Error Code', 'Error Description',
                    'Detection Time (as stored)', 'Detection ID',
                    'Security Intelligence Version', 'Engine Version', 'Record ID', 'Computer')
    label = 'Microsoft Defender Detection Events'
    records, sources = read_event_records(
        context, _LOG, label, event_ids=set(_DETECTION_EVENTS), provider=_PROVIDER)
    parameters = _ParameterText(context, label)
    data_list = []
    for record in records:
        if record.event_id in _STATE_EVENTS:
            user = record.get('Detection User' if record.event_id == '1116'
                              else 'Remediation User')
            source, origin = record.get('Source Name'), record.get('Origin Name')
            detection_type, action = record.get('Type Name'), record.get('Action Name')
            status = record.get('Additional Actions String')
            path = record.get('Path')
        else:
            user = _domain_user(record)
            source, origin = record.get('Detection Source'), record.get('Detection Origin')
            detection_type, action = record.get('Detection Type'), record.get('Cleaning Action')
            status = _first(record, 'Execution Status', 'Status Description')
            path = _first(record, 'Path Found', 'Path')
        values = (
            record.get('Threat Name'), record.get('Threat ID'), record.get('Severity Name'),
            record.get('Category Name'), path, record.get('Process Name'), user,
            record.get('SID'), source,
            origin, detection_type, action, status, record.get('Error Code'),
            record.get('Error Description'), record.get('Detection Time'),
            record.get('Detection ID'),
            _first(record, 'Security intelligence Version', 'Signature Version'),
            record.get('Engine Version'))
        data_list.append((record.time, record.event_id, _DETECTION_EVENTS[record.event_id])
                         + tuple(parameters.text(record, value) for value in values)
                         + (record.record_id, record.computer))
    parameters.log()
    return data_headers, data_list, '\n'.join(sources + parameters.files())


@artifact_processor
def defenderProtectionChanges(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Old Value',
                    'New Value', 'Detail', 'Product Version', 'Record ID', 'Computer')
    label = 'Microsoft Defender Protection and Configuration Changes'
    records, sources = read_event_records(
        context, _LOG, label, event_ids=set(_PROTECTION_EVENTS), provider=_PROVIDER)
    parameters = _ParameterText(context, label)
    data_list = []
    for record in records:
        if record.event_id == '5004':
            detail = _labelled(record, ('Feature Name', 'Configuration'))
        elif record.event_id == '5013':
            detail = _labelled(record, ('Changed Type', 'Value'))
        elif record.event_id == '1013':
            detail = '; '.join(part for part in (
                f"Timestamp: {record.get('Timestamp')}" if record.get('Timestamp') else '',
                f"User: {_domain_user(record)}" if _domain_user(record) else '',
                f"SID: {record.get('SID')}" if record.get('SID') else '') if part)
        else:
            detail = ''
        data_list.append((
            record.time, record.event_id, _PROTECTION_EVENTS[record.event_id],
            parameters.text(record, record.get('Old Value')),
            parameters.text(record, record.get('New Value')), detail,
            record.get('Product Version'), record.record_id, record.computer))
    parameters.log()
    return data_headers, data_list, '\n'.join(sources + parameters.files())


@artifact_processor
def defenderScans(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Scan ID',
                    'Scan Type', 'Scan Parameters', 'Scan Resources', 'Scan Time (h:m:s)',
                    'User', 'User SID', 'Product Version', 'Other Fields (as stored)',
                    'Record ID', 'Computer')
    label = 'Microsoft Defender Scan Events'
    records, sources = read_event_records(
        context, _LOG, label, event_ids=set(_SCAN_EVENTS), provider=_PROVIDER)
    parameters = _ParameterText(context, label)
    data_list = []
    for record in records:
        hours, minutes = record.get('Scan Time Hours'), record.get('Scan Time Minutes')
        seconds = record.get('Scan Time Seconds')
        scan_time = f'{hours}:{minutes}:{seconds}' if hours or minutes or seconds else ''
        other = '; '.join(
            f'{name}: {value.strip()}' for name, value in record.fields.items()
            if name and name not in _SCAN_FIELDS and not name.startswith('Unused')
            and value and value.strip())
        data_list.append((
            record.time, record.event_id, _SCAN_EVENTS[record.event_id], record.get('Scan ID'),
            parameters.text(record, record.get('Scan Type')),
            parameters.text(record, record.get('Scan Parameters')),
            parameters.text(record, record.get('Scan Resources')), scan_time,
            _domain_user(record), record.get('SID'), record.get('Product Version'), other,
            record.record_id, record.computer))
    parameters.log()
    return data_headers, data_list, '\n'.join(sources + parameters.files())
