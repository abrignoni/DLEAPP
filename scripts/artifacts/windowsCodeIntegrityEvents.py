"""Code Integrity event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-CodeIntegrity record of the CodeIntegrity Operational event log: images that did not
meet a signing level, policy blocks and audits, the signature information Code Integrity records for another event,
policy activations and boot-session settings. The Event IDs, the message text and the field names are sourced in
the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Code Integrity Events'
_LOG = 'Microsoft-Windows-CodeIntegrity%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-CodeIntegrity'

# The spellings of the file, process and policy name fields (no manifest entry holds two spellings of one), and the
# two signer fields; each has a column of its own and every other field goes to Other Fields.
_FILE = ('FileNameBuffer', 'File Name')
_PROCESS = ('ProcessNameBuffer', 'Process Name')
_POLICY = ('PolicyNameBuffer', 'PolicyName')
_PUBLISHER = 'PublisherName'
_ISSUER = 'IssuerName'

# (Event ID, version): the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    ('3001', '0'): 'Code Integrity determined an unsigned kernel module %2 is loaded into the system.',
    ('3001', '1'): 'Code Integrity determined an unsigned kernel module %2 is loaded into the system.',
    ('3002', '0'): 'Code Integrity is unable to verify the image integrity of the file %2 because the set of '
                   'per-page image hashes could not be found on the system.',
    ('3002', '1'): 'Code Integrity is unable to verify the image integrity of the file %2 because the set of '
                   'per-page image hashes could not be found on the system.',
    ('3003', '0'): 'Code Integrity is unable to verify the image integrity of the file %2 because the set of '
                   'per-page image hashes could not be found on the system.',
    ('3003', '1'): 'Code Integrity is unable to verify the image integrity of the file %2 because the set of '
                   'per-page image hashes could not be found on the system.',
    ('3004', '0'): 'Windows is unable to verify the image integrity of the file %2 because file hash could '
                   'not be found on the system.',
    ('3004', '1'): 'Windows is unable to verify the image integrity of the file %2 because file hash could '
                   'not be found on the system.',
    ('3005', '0'): 'Code Integrity is unable to verify the image integrity of the file %2 because a file '
                   'hash could not be found on the system.',
    ('3005', '1'): 'Code Integrity is unable to verify the image integrity of the file %2 because a file '
                   'hash could not be found on the system.',
    ('3010', '0'): '',
    ('3010', '1'): 'Code Integrity was unable to load the %2 catalog.',
    ('3021', '0'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
    ('3021', '1'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
    ('3022', '0'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
    ('3022', '1'): 'Code Integrity determined a revoked kernel module %2 is loaded into the system.',
    ('3023', '0'): 'The driver %2 is blocked from loading as the driver has been revoked by Microsoft.',
    ('3023', '1'): 'The driver %2 is blocked from loading as the driver has been revoked by Microsoft.',
    ('3024', '0'): 'Windows was unable to update the boot catalog cache file.',
    ('3026', '0'): 'Code Integrity was unable to load the %2 catalog because the signing certificate for '
                   'this catalog has been revoked.',
    ('3032', '0'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
    ('3032', '1'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
    ('3033', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements.',
    ('3034', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3035', '0'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
    ('3035', '1'): 'Code Integrity determined a revoked image %2 is loaded into the system.',
    ('3036', '0'): 'Windows is unable to verify the integrity of the file %2 because the signing certificate '
                   'has been revoked.',
    ('3036', '1'): 'Windows is unable to verify the integrity of the file %2 because the signing certificate '
                   'has been revoked.',
    ('3037', '0'): 'Code Integrity determined an unsigned image %2 is loaded into the system.',
    ('3037', '1'): 'Code Integrity determined an unsigned image %2 is loaded into the system.',
    ('3050', '0'): 'Code Integrity completed retrieval of file cache.',
    ('3051', '0'): 'Code Integrity completed retrieval of file cache.',
    ('3052', '0'): 'Code Integrity completed retrieval of file cache.',
    ('3057', '0'): 'Code Integrity completed retrieval of file cache.',
    ('3058', '0'): 'Code Integrity completed retrieval of file cache.',
    ('3063', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   'security requirements for %5.',
    ('3065', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   'security requirements for %5.',
    ('3066', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3067', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3068', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3069', '0'): 'Code Integrity was unable to load the weak crypto policy value from registry.',
    ('3070', '0'): 'Code Integrity was unable to load the weak crypto policy from registry store.',
    ('3071', '0'): 'Code Integrity was unable to load the weak crypto policies.',
    ('3072', '0'): 'Code Integrity determined that the module %2 is not compatible with hypervisor '
                   'enforcement due to it having non-page aligned sections.',
    ('3073', '0'): 'Code Integrity determined that the module %2 is not compatible with strict mode '
                   'hypervisor enforcement due to it having an executable section that is also writable.',
    ('3074', '0'): 'Code Integrity was unable to verify a page for a module verified using hypervisor enforcement.',
    ('3076', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3076', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3076', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3076', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3076', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy (Policy ID:%29).',
    ('3076', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy (Policy ID:%33).',
    ('3077', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3077', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3077', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3077', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3077', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy (Policy ID:%29).',
    ('3077', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy (Policy ID:%33).',
    ('3078', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3078', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3078', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3078', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3079', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3079', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3079', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3079', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated Advanced Threat Protection policy.',
    ('3080', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated Driver policy.',
    ('3080', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '6'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '7'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated Advanced Threat Protection policy.',
    ('3080', '8'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated Driver policy.',
    ('3080', '9'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3080', '10'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet '
                    'the %5 signing level requirements or violated code integrity policy.',
    ('3080', '11'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet '
                    'the %5 signing level requirements or violated Advanced Threat Protection policy.',
    ('3080', '12'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated Driver policy.',
    ('3081', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3081', '1'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3081', '2'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3081', '3'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated Advanced Threat Protection policy.',
    ('3081', '4'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated Driver policy.',
    ('3081', '5'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3081', '6'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3081', '7'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated Advanced Threat Protection policy.',
    ('3081', '8'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated Driver policy.',
    ('3081', '9'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3081', '10'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet '
                    'the %5 signing level requirements or violated code integrity policy.',
    ('3081', '11'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet '
                    'the %5 signing level requirements or violated Advanced Threat Protection policy.',
    ('3081', '12'): 'Code Integrity determined that a process (%4) attempted to load %2 that violated Driver policy.',
    ('3082', '0'): 'Code Integrity determined kernel module %2 that did not meet the WHQL requirements is '
                   'loaded into the system.',
    ('3083', '0'): 'Code Integrity determined kernel module %2 that did not meet the WHQL requirements is '
                   'loaded into the system.',
    ('3084', '0'): 'Code Integrity will enable WHQL driver enforcement for this boot session.',
    ('3085', '0'): 'Code Integrity will disable WHQL driver enforcement for this boot session.',
    ('3086', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   'signing requirements for Isolated User Mode.',
    ('3087', '0'): 'Code Integrity determined that the kernel module %2 is not compatible with hypervisor '
                   'enforcement.',
    ('3087', '1'): 'Code Integrity determined that a process (%6) attempted to load %2 that is not '
                   'compatible with hypervisor enforcement.',
    ('3089', '0'): 'Signature information for another event.',
    ('3089', '1'): 'Signature information for another event.',
    ('3089', '2'): 'Signature information for another event.',
    ('3089', '3'): 'Signature information for another event.',
    ('3090', '0'): 'Code Integrity testing module %2 against policy %11.',
    ('3091', '0'): 'Code Integrity testing module %2 against policy %11.',
    ('3092', '0'): 'Code Integrity testing module %2 against policy %11.',
    ('3093', '0'): 'other (see event data)',
    ('3094', '0'): 'other (see event data)',
    ('3095', '0'): 'Code Integrity policy %5 %2 is set to unrefreshable.',
    ('3095', '1'): 'Code Integrity policy %5 %2 is set to unrefreshable.',
    ('3096', '0'): 'No change in active Code Integrity policy %5 %2 after refresh.',
    ('3096', '1'): 'No change in active Code Integrity policy %5 %2 after refresh.',
    ('3097', '0'): 'Not allowed to refresh Code Integrity policy %5 %2.',
    ('3097', '1'): 'Not allowed to refresh Code Integrity policy %5 %2.',
    ('3098', '0'): 'other (see event data)',
    ('3099', '0'): 'Refreshed and activated Code Integrity policy %5 %2.',
    ('3099', '1'): 'Refreshed and activated Code Integrity policy %5 %2.',
    ('3100', '0'): 'Refreshed but not activated Code Integrity policy %5 %2.',
    ('3100', '1'): 'Refreshed but not activated Code Integrity policy %5 %2.',
    ('3101', '0'): 'Code Integrity policy refresh started for %1 policies.',
    ('3102', '0'): 'Code Integrity policy refresh finished for %1 policies.',
    ('3103', '0'): 'Ignoring refresh for Code Integrity policy ID %1.',
    ('3103', '1'): 'Ignoring refresh for Code Integrity policy ID %1.',
    ('3104', '0'): 'Windows blocked file %2 which has been disallowed for protected processes.',
    ('3105', '0'): 'Trying to refresh Code Integrity policy with policy ID %1.',
    ('3108', '0'): 'Code Integrity successfully switched from %3 mode to %4 mode.',
    ('3109', '0'): 'Code Integrity already switched from %3 mode to %4 mode.',
    ('3110', '0'): 'Code Integrity failed to switch from %3 mode to %4 mode with error code %5.',
    ('3111', '0'): 'Code Integrity determined that a process (%6) attempted to load %2 that is not '
                   'compatible with hypervisor enforcement.',
    ('3112', '0'): 'Code Integrity determined that a process (%4) attempted to load %2 that did not meet the '
                   '%5 signing level requirements or violated code integrity policy.',
    ('3113', '0'): 'Code Integrity could not update the driver.stl revocation list.',
    ('3114', '0'): 'Code Integrity determined that %4 is trying to load %2 which failed the dynamic code '
                   'trust verification with error code of %5.',
    ('3115', '0'): 'Code Integrity determined that %4 is trying to load %2 which failed the dynamic code '
                   'trust verification with error code of %5.',
    ('3116', '0'): 'Signature information for Code Integrity policy ID %1.',
}


__artifacts_v2__ = {
    "codeIntegrityEvents": {
        "name": "Code Integrity Events",
        "description": "Microsoft-Windows-CodeIntegrity records of the CodeIntegrity Operational event log, such as "
                       "a process that attempted to load a file that did not meet a signing level, the signature "
                       "information recorded for another event, policy activations and boot-session settings, with "
                       "the file, process, policy, publisher and issuer names where a record carries them, its "
                       "Activity ID and its other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-CodeIntegrity%4Operational.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-CodeIntegrity, "
                 "whatever its Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 131 entries to "
                 "this log's channel, for 68 Event IDs of which 27 have more than one version; they sit among lines "
                 "394 to 4439 of the file, with 46 entries of other channels between them "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-CodeIntegrity.xml#L394-L4439). "
                 "The manifests of Windows 11 build 22621.819 and Windows 10 builds 19041.208, 17763.107 and "
                 "16299.15 send it 128, 126, 112 and 85 entries "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-CodeIntegrity.xml#L394-L4348, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-CodeIntegrity.xml#L383-L4203, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-CodeIntegrity.xml#L366-L3773 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-CodeIntegrity.xml#L366-L2924). "
                 "These are the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for the "
                 "record's Event ID and version, the first sentence of the first line of the build 26100 message: "
                 "the first line that holds more than white space, with each run of white space made one space, cut "
                 "after the first period that a space or the end of the line follows (whole when it has none), with "
                 "its placeholders (such as %1) as the manifest writes them. A placeholder is an insertion string "
                 "for a data item of the event's template by its position (Microsoft's Defining Events page: 'to "
                 "include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in; 113 of the 134 texts hold one. Version 0 of 3093, 3094 and 3098, which build "
                 "26100 does not hold, takes the build 17763 message, which the build 16299 one equals, and that "
                 "message is 'other (see event data)'. The build 26100 entry for version 0 of 3010 has no message "
                 "text, so Event is blank for it, as it is for an Event ID and version outside the table, which no "
                 "tested record had. The versions of 3010, 3076, 3077, 3080, 3081 and 3087 differ in their first "
                 "sentence. The manifests of builds 16299, 17763 and 19041 word 16, 12 and 2 entries differently "
                 "from the table with the same field names (9 and 8 of them 'other (see event data)' in 16299 and "
                 "17763); a record of such an entry is given the table text, and no tested record was of one. File "
                 "Name is the FileNameBuffer field, or 'File Name' (the spelling of 3076 to 3081); Process Name is "
                 "ProcessNameBuffer or 'Process Name'; Policy Name is PolicyNameBuffer or PolicyName; Publisher and "
                 "Issuer are PublisherName and IssuerName, which the manifests give 3089 and 3116. No entry holds "
                 "two spellings of one field, and if a record did, the first spelling named here would be shown and "
                 "the other listed in Other Fields. Activity ID is the ActivityID of the record's Correlation "
                 "element, blank when the record has none. On pc_mus_001_win11 each of the 115 rows of 3033 ('Code "
                 "Integrity determined that a process (%4) attempted to load %2 that did not meet the %5 signing "
                 "level requirements.') has the same File Name, ending igd10iumd64.dll, and a Process Name ending "
                 "MsMpEng.exe (2 distinct paths), each a \\Device\\HarddiskVolume path, with RequestedPolicy 7, "
                 "ValidatedPolicy 1 and Status 3221226536, as stored; what those numbers stand for is not "
                 "established here. Each of the 115 shares its Activity ID with exactly four rows of 3089 "
                 "('Signature information for another event.'), whose Signature is 0, 1, 2 and 3, and with no other "
                 "row. TotalSignatureCount is 6 on 356 of the 460 rows of 3089 and 9 on 104. Publisher held one "
                 "value on those 460 rows, Microsoft Windows Hardware Compatibility Publisher, and Issuer one value, "
                 "Microsoft Windows Third Party Component CA 2012. Hash, PublisherTBSHash and IssuerTBSHash are "
                 "win:Binary fields, which python-evtx renders as Base64 text "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1339-L1360); "
                 "decoded, each has the length its size field gives on all 460, and PageHash is False on all 460. "
                 "The 10 rows of 3099 ('Refreshed and activated Code Integrity policy %5 %2.') have Policy Name "
                 "Microsoft Windows Driver Policy and no Activity ID. The 40 rows of 3085 ('Code Integrity will "
                 "disable WHQL driver enforcement for this boot session.'), on all four images, carry Settings, 0x "
                 "followed by eight hexadecimal digits, and Exemption 1, listed in Other Fields. File Name, Process "
                 "Name, Policy Name, Publisher and Issuer are blank on every row of af_case2_win10, lonewolf_win10 "
                 "and szechuan_win10, whose logs hold only 3085 records, and there Event ID, Event, Other Fields and "
                 "User SID each held one value on every row. Other Fields lists every other named field that holds "
                 "more than white space as 'name: value', in the record's order, joined with ' | '. Each value, here "
                 "and in the five name columns, is as python-evtx renders it with any white space at either end "
                 "removed; no tested value had any. A data item that has no name is not shown, and no tested record "
                 "had one. If a record named a field twice the last would be read. The tested records carried the "
                 "field names their image's build manifest gives the event and version. Tested on the logs of four "
                 "public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, build "
                 "22621; szechuan_win10, build 19041), which gave 19, 4, 595 and 7 rows in that order; the two "
                 "captures of a Windows 11 build 26200 machine hold no such log. 4 of the 134 Event IDs and versions "
                 "in the table occur: version 0 of 3085 on all four images, and version 0 of 3033, version 2 of 3089 "
                 "and version 1 of 3099 on pc_mus_001_win11 alone. The other 130 are unexercised. Event Time (UTC) "
                 "is the record's TimeCreated SystemTime, which python-evtx renders from the FILETIME the record "
                 "stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element: S-1-5-18 on 615 tested rows and blank, "
                 "the record carrying none, on 10 (2 of 3033 and 8 of 3089). Record ID is the record's EventRecordID "
                 "and Computer the machine name the record stores, which held one value on pc_mus_001_win11, two on "
                 "af_case2_win10 and lonewolf_win10 and three on szechuan_win10. Rows are in the order the file "
                 "holds them, which was rising Record ID on every tested log; in time order 2 rows are earlier than "
                 "the row before them (1 each on af_case2_win10 and lonewolf_win10). Every record of the tested logs "
                 "rendered and is the provider's. A record python-evtx cannot render, or whose XML does not parse, "
                 "is counted in the run log and not reported. A log marked dirty is read past the chunks its header "
                 "counts, and the run log says how many records came from there. Reading needs the python-evtx "
                 "package (pip install python-evtx). Not read: the events these manifests send to the provider's "
                 "Verbose channel.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-CodeIntegrity%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 595 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 7 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


def first_present(record, names):
    return next((name for name in names if name in record.fields), '')


def code_integrity_row(record):
    shown = (first_present(record, _FILE), first_present(record, _PROCESS), first_present(record, _POLICY),
             _PUBLISHER, _ISSUER)
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in shown and record.get(name))
    return (record.time, record.event_id, _EVENTS.get((record.event_id, record.version), ''),
            *(record.get(name) for name in shown), record.activity_id, other, record.user_sid, record.record_id,
            record.computer)


@artifact_processor
def codeIntegrityEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'File Name', 'Process Name', 'Policy Name',
                    'Publisher', 'Issuer', 'Activity ID', 'Other Fields', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [code_integrity_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
