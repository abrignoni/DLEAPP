"""Windows NTFS volume state event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Microsoft-Windows-Ntfs event 98 of the System event log, which names a
volume by its drive name and its device name and stores a corruption action
state number. The Event ID, field names and message text are sourced in the
notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'NTFS Volume State Events'
_LOG = 'system.evtx'
_PROVIDER = 'Microsoft-Windows-Ntfs'
_EVENT_ID = '98'

__artifacts_v2__ = {
    "ntfsVolumeStateEvents": {
        "name": "NTFS Volume State Events",
        "description": "Microsoft-Windows-Ntfs event 98 of the System event log, which names a volume and gives its "
                       "corruption action state: the drive name (a drive letter, a volume GUID name or two question "
                       "marks), the device name and the state number as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, the "
                 "records whose provider is Microsoft-Windows-Ntfs and whose Event ID is 98. No other provider wrote "
                 "a record with that Event ID in the tested logs. The provider's manifest sends 98 to the System "
                 "channel as information, with the keyword VolumeCorruptionActionStateChange, the message 'Volume %1 "
                 "(%2) %3' and the fields DriveName, DeviceName and CorruptionActionState, a 32-bit unsigned number "
                 "(Microsoft-Windows-Ntfs manifest as registered on Windows 11 build 22621.819, published in "
                 "nasbench's EVTX-ETW-Resources repository: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Ntfs.xml#L963-L978; "
                 "the manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold the same entry: "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Ntfs.xml#L317-L332, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Ntfs.xml#L317-L332 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Ntfs.xml#L385-L400). "
                 "Those manifests hold no text for the third parameter, so what a state number stands for is not "
                 "sourced here: Corruption Action State (as stored) is the number as python-evtx renders it. Drive "
                 "Name and Device Name are DriveName and DeviceName as python-evtx renders them, with any white "
                 "space at either end removed (no tested value had any). The message gives the two names and the "
                 "state and nothing else: a row does not say whether the volume was mounted, removed or checked. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. Tested on "
                 "the System logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041) and of two captures of one Windows 11 "
                 "build 26200 ARM64 virtual machine (windows11_arm_4688_known and windows11_arm_known_20261001). The "
                 "four public images gave 24, 10, 30 and 14 rows in that order and each capture gave 260, the same "
                 "260 records on both, every record version 0. Drive Name took three forms over the six logs: a "
                 "capital letter and a colon (211 rows), \\\\?\\Volume followed by a GUID in braces (380) and two "
                 "question marks (7). Device Name was \\Device\\HarddiskVolume followed by a number on 591 rows and "
                 "\\Device\\HarddiskVolumeShadowCopy followed by a number on 7, and those 7 are the rows whose Drive "
                 "Name is two question marks (2 on lonewolf_win10 and 5 on pc_mus_001_win11). Corruption Action "
                 "State (as stored) held one value, 0, on every row of the four public images; over the six logs it "
                 "was 0 on 596 rows and 3 on 1 row of each capture. The record's Level is 4 on every row with state "
                 "0 and 2 on the rows with state 3; Level is not reported. On the four public images every drive "
                 "letter in a row (6 over the four logs) is the name of a \\DosDevices value of the MountedDevices "
                 "key of the image's SYSTEM hive, and none of the 5 GUID names is among that key's value names; "
                 "where the GUID comes from was not established. The rows whose Drive Name is C: number 19, 4, 11 "
                 "and 7 on the public images and 77 on each capture, the same as the records of provider EventLog "
                 "with Event ID 6005 in each log, which Windows System Power Events reports. Neither name identifies "
                 "one volume across a log. A drive letter appears with more than one Device Name (E: with four on "
                 "af_case2_win10, D: with two on pc_mus_001_win11 and 1 letter on each capture), and a Device Name "
                 "with more than one Drive Name (1 on pc_mus_001_win11 and 2 on each capture). Rows are in the order "
                 "the log file holds its records, which was rising Record ID on every tested log. Event Time (UTC) "
                 "rises with it except for 1 row on af_case2_win10, 1 on lonewolf_win10 and 1 on each capture that "
                 "are earlier than the row before them. Computer held one value on every row of pc_mus_001_win11; "
                 "af_case2_win10, lonewolf_win10 and each capture hold two names and szechuan_win10 three. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. Every record of the tested logs rendered, among them the 72 TPM event 27 records of each "
                 "capture's log, which python-evtx renders only with the array value types scripts/windows_evtx.py "
                 "adds. A log marked dirty is read past the chunks its header "
                 "counts, and the run log says how many records came from there. Reading needs the python-evtx "
                 "package (pip install python-evtx). Not read: the provider's other events. No tested System log "
                 "held one.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 260 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 260 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 30 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 24 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 10 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 14 rows",
        },
    },
}


def volume_row(record):
    return (record.time, record.get('DriveName'), record.get('DeviceName'),
            record.get('CorruptionActionState'), record.record_id, record.computer)


@artifact_processor
def ntfsVolumeStateEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Drive Name', 'Device Name',
                    'Corruption Action State (as stored)', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, event_ids={_EVENT_ID},
                                          provider=_PROVIDER)
    data_list = [volume_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
