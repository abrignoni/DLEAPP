"""DPAPI event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-Crypto-DPAPI record of the provider's Operational event log: master keys created or
deleted with their storage folder, credential keys found with the account's name and SID, password changes, failed
unprotect calls and the provider's other events of that log. The Event IDs, the message text and the field names
are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'DPAPI Events'
_LOG = 'Microsoft-Windows-Crypto-DPAPI%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-Crypto-DPAPI'

# The fields that have a column of their own, in column order; any other field goes to Other Fields.
_SHOWN = ('MasterKeyGUID', 'UserStorage', 'CredKeyIdentifier', 'UserName', 'UserSid')

# Event ID: the first sentence of the provider's message for it (see notes).
_EVENTS = {
    '1': 'DPAPI created Master key.',
    '2': 'DPAPI deleted Master key.',
    '3': 'Master key access failed.',
    '4': 'Password Change triggered.',
    '5': 'Synchronization of Master keys triggered.',
    '8196': 'Master key decryption in memory failed',
    '8198': 'DPAPI Unprotect failed .',
    '8199': 'Synchronization of Master keys failed.',
    '8200': "Master key's record successfully logged to Diagnostic file.",
    '8201': "Master key's record failed to log to Diagnostic file.",
    '8202': 'Master Key decryption failed but a record of this key can be found in the Diagnostic file.',
    '8203': 'Master Key decryption failed because no record of this key can be found in the Diagnostic file.',
    '8204': 'Master Key decryption failed because the encryption cred mismatches the decryption cred.',
    '8205': 'Master Key decryption failed but the encryption cred matches the decryption cred.',
    '8206': 'CredHist file decryption failed',
    '8207': 'Diagnostic File operation received a NULL credential key.',
    '12289': 'DPAPI found credential key.',
    '12290': 'Credential key does not exist.',
    '16386': 'DPAPI tried to backup its master key.',
    '16387': 'DPAPI tried to backup its master key.',
}


__artifacts_v2__ = {
    "dpapiEvents": {
        "name": "DPAPI Events",
        "description": "Microsoft-Windows-Crypto-DPAPI records of the provider's Operational event log, such as a "
                       "master key created with its GUID and storage folder and a credential key found with the "
                       "account's name and SID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Crypto-DPAPI%4Operational.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-Crypto-DPAPI, "
                 "whatever its Event ID. Microsoft's page for the CryptProtectData function (dpapi.h) says of the "
                 "data that function encrypts: 'Typically, only a user with the same logon credential as the user "
                 "who encrypted the data can decrypt the data.' "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/c12073e417d5780fe796278ada21b90cef1b0568/sdk-api-src/content/dpapi/nf-dpapi-cryptprotectdata.md?plain=1#L52). "
                 "The provider's manifest of Windows 11 build 26100.1742 sends 20 events to this log's channel, each "
                 "version 0: 1 to 5 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml#L150-L243), "
                 "8196 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml#L337-L348), "
                 "8198 to 8207, 12289 and 12290 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml#L369-L597) "
                 "and 16386 and 16387 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml#L622-L659). "
                 "The manifest of Windows 11 build 22621.819 holds the same 20, that of Windows 10 build 19041.208 "
                 "holds 10 of them (not 8200 to 8207, 16386 and 16387), that of build 17763.107 holds 9 (not 8196 "
                 "either, which it sends to the provider's Debug channel) and that of build 16299.15 holds 6 (not "
                 "8199, 12289 and 12290 either). Each entry an older manifest holds has the same message and fields; "
                 "8199 is level Information in the 17763.107 and 19041.208 manifests and Error in the two later ones "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-Crypto-DPAPI.xml). "
                 "These are the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for the "
                 "record's Event ID, the message's first sentence: the message with each run of white space made one "
                 "space, cut after the first period that a space or the end of the message follows. The messages of "
                 "16386 and 16387 share that sentence, 'DPAPI tried to backup its master key.', and go on 'Fallback "
                 "backup is enabled.' and 'Fallback backup is disabled.'. Event is blank for an Event ID outside the "
                 "20, which no tested record had. Five fields have a column, named after the label the messages give "
                 "the field: Master Key GUID is MasterKeyGUID ('GUID'; events 1, 2, 3 and 8200 to 8205), User "
                 "Storage Area is UserStorage (1 and 2), and Credential Key Identifier, Credential User Name and "
                 "Credential User SID are CredKeyIdentifier, UserName and UserSid ('User Name' and 'User Sid'; 8199 "
                 "and 12289). Other Fields lists any other named field that holds more than white space as 'name: "
                 "value', in the record's order, joined with ' | '. Each value is as python-evtx renders it with any "
                 "white space at either end removed, and no tested value had any. A data item that has no name is "
                 "not shown, and no tested record had one. If a record named a field twice the last would be read. "
                 "Tested on the logs of four public images (af_case2_win10, build 17763; lonewolf_win10, build "
                 "16299; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 70, 6, 383 and 103 "
                 "rows in that order; the two captures of a Windows 11 build 26200 machine hold no such log. The "
                 "rows are 24 of 1, 'DPAPI created Master key.' (8, 6, 0 and 10), 12 of 5, 'Synchronization of "
                 "Master keys triggered.' (szechuan_win10), 5 of 8198, 'DPAPI Unprotect failed .' and 11 of 8200, "
                 "\"Master key's record successfully logged to Diagnostic file.\" (pc_mus_001_win11), 236 of 12289, "
                 "'DPAPI found credential key.' (62, 0, 93 and 81) and 274 of 12290, 'Credential key does not "
                 "exist.' (pc_mus_001_win11). Every tested record carried the field names and the level the build "
                 "26100.1742 manifest gives its event. The other 14 events are unexercised. Each of the 24 rows of 1 "
                 "names a different key. For 21 of them (7 of 8, 5 of 6 and 9 of 10) the image holds a file named by "
                 "the GUID without its braces in the folder User Storage Area names, and the created time the image "
                 "records for that file is within 0.062 seconds of the row; the other 3 have no such file in the "
                 "image. In the other direction each of the 21 files with a GUID name in the Protect folders of "
                 "those three images has a row; pc_mus_001_win11 holds 5 such files and no row of 1. User Storage "
                 "Area is C:\\Windows\\system32\\Microsoft\\Protect\\S-1-5-18\\ on 7 rows, its User subfolder on 6 and a "
                 "folder named by a SID in AppData\\Roaming\\Microsoft\\Protect of a user profile on 11. The 236 rows "
                 "of 12289 name 17 accounts by Credential User SID (2, 1 and 14 on the three images that have such "
                 "rows). Credential Key Identifier is a binary field, which python-evtx renders as base64 text "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1359-L1360); "
                 "every one is 32 bytes, and each account has one identifier on all its rows; 3 accounts of "
                 "szechuan_win10 appear under two names. Credential User SID is S-1-5-18 on 6 rows of "
                 "szechuan_win10. What the identifier is computed from is not sourced here. The 11 rows of 8200 name "
                 "one key, which is a file with that GUID name in the image's Protect folders, and list "
                 "EncryptCredID and EncryptCredKey in Other Fields; those folders also hold a file named Diagnostic, "
                 "which no other tested image has. The 5 rows of 8198 list Status and ReasonForFailure in Other "
                 "Fields, and the rows of 5 and 12290 have no field. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Master Key GUID is the GUID as python-evtx renders it, lower case in braces "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1375-L1376). "
                 "User SID is the UserID of the record's Security element: S-1-5-18 on every row but the 12 rows of "
                 "5, which carry another SID. Record ID is the record's EventRecordID and Computer the machine name "
                 "the record stores, which held one value on lonewolf_win10 and pc_mus_001_win11, two on "
                 "af_case2_win10 and three on szechuan_win10. Other Fields is blank on every row of af_case2_win10, "
                 "lonewolf_win10 and szechuan_win10, whose events have no field outside the five columns. On "
                 "lonewolf_win10, whose rows are all 1, Event ID and Event held one value and Credential Key "
                 "Identifier, Credential User Name and Credential User SID are blank on every row. User Storage Area "
                 "is blank on every row of pc_mus_001_win11, which has no row of 1. User SID held one value, "
                 "S-1-5-18, on af_case2_win10, lonewolf_win10 and pc_mus_001_win11. Rows are in the order the file "
                 "holds them, which was rising Record ID on every tested log; in time order 1 row each of "
                 "af_case2_win10 and lonewolf_win10 is earlier than the row before it. Every record of the tested "
                 "logs rendered and is the provider's. A record python-evtx cannot render, or whose XML does not "
                 "parse, is counted in the run log and not reported. A log marked dirty is read past the chunks its "
                 "header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Not read: the events these manifests send to the "
                 "provider's BackUpKeySvc and Debug channels, and the files of the Protect folders.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 70 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 383 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 103 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-Crypto-DPAPI%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "key",
    },
}


def dpapi_row(record):
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields if name not in _SHOWN and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), *(record.get(name) for name in _SHOWN), other,
            record.user_sid, record.record_id, record.computer)


@artifact_processor
def dpapiEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Master Key GUID', 'User Storage Area',
                    'Credential Key Identifier', 'Credential User Name', 'Credential User SID', 'Other Fields', 'User SID',
                    'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [dpapi_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
