"""Windows AppLocker events, for DLEAPP: files and packaged apps the provider logged as allowed, allowed in audit
mode or prevented, its Config CI events, and its policy and other notices.

Author: @AlexisBrignoni, Claude.
"""

import base64
import binascii
import re

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_PROVIDER = 'Microsoft-Windows-AppLocker'
_LOGS = ('microsoft-windows-applocker%4exe and dll.evtx', 'microsoft-windows-applocker%4msi and script.evtx',
         'microsoft-windows-applocker%4packaged app-deployment.evtx',
         'microsoft-windows-applocker%4packaged app-execution.evtx')

# Outcome: the provider's message for the Event ID without its leading insertion marker (%11 or %2) and 'was'
# (see notes).
_ALLOWED = 'Allowed to run'
_AUDITED = 'Allowed to run; would have been prevented from running if the AppLocker policy were enforced'
_PREVENTED = 'Prevented from running'
_RULE_EVENTS = {
    '8002': _ALLOWED, '8003': _AUDITED, '8004': _PREVENTED,
    '8005': _ALLOWED, '8006': _AUDITED, '8007': _PREVENTED,
    '8020': _ALLOWED, '8021': _AUDITED, '8022': _PREVENTED,
    '8023': 'Allowed to be installed', '8024': _AUDITED, '8025': _PREVENTED,
}
_CONFIG_CI_EVENTS = {
    '8028': 'Allowed to run; would have been prevented if the Config CI policy were enforced',
    '8029': 'Prevented from running due to Config CI policy',
    '8036': 'Prevented from running due to Config CI policy',
    '8037': 'Passed Config CI policy and was allowed to run',
    '8038': 'Publisher info',
    '8039': 'Allowed to install or update; would have been prevented if the Config CI policy were enforced',
    '8040': 'Prevented from installing or updating due to Config CI policy',
}
# Event: the provider's message, first line, with its insertion markers as the manifest has them (see notes).
_POLICY_EVENTS = {
    '8000': 'AppID policy conversion failed. Status %1.',
    '8001': 'The AppLocker policy was applied successfully to this computer.',
    '8008': '%2: AppLocker component not available on this SKU.',
    '8009': '%2: AppLocker component not available on this SKU.',
    '8026': 'No packaged apps can be executed while Exe rules are being enforced and no Packaged app rules have '
            'been configured.',
    '8027': 'No packaged apps can be executed while Exe rules are being enforced and no Packaged app rules have '
            'been configured.',
    '8041': "A %6 was allowed to %1 by system execution policy. The application provided this information: '%3'",
    '8042': "A %6 was not allowed to be executed by system execution policy. The application provided this "
            "information: '%3'",
    '8043': 'Process %6 attempted to register UninstallString %2, Status: %9.',
    '8044': 'Checking cmdline %2 against registered UninstallStrings %4, MatchFound: %5, Status:%6.',
}

# Base64 in its padded form. Python versions differ on what b64decode accepts beyond this, so the form is tested.
_BASE64 = re.compile(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?')


def binary_hex(value):
    """A win:Binary field, which python-evtx renders in Base64, as uppercase hexadecimal; anything else as stored."""
    text = (value or '').strip()
    if not text or not _BASE64.fullmatch(text):
        return text
    try:
        return base64.b64decode(text, validate=True).hex().upper()
    except (binascii.Error, ValueError):
        return text


def signed_hex(value):
    """A stored 32-bit number as '0x........ (as stored)'; anything else as stored."""
    text = (value or '').strip()
    try:
        number = int(text)
    except ValueError:
        return text
    if not -0x80000000 <= number <= 0xFFFFFFFF:
        return text
    return f'0x{number & 0xFFFFFFFF:08X} ({text})'


__artifacts_v2__ = {
    "appLockerRuleEvents": {
        "name": "AppLocker Rule Events",
        "description": "Files and packaged apps that the Microsoft-Windows-AppLocker provider logged as allowed to "
                       "run or be installed, allowed although the policy would have prevented them had it been enforced, or "
                       "prevented from running, with the file path, hash, FQBN, rule and user SID each record "
                       "holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-AppLocker%4EXE and DLL.evtx, %4MSI and Script.evtx, %4Packaged "
                 "app-Deployment.evtx and %4Packaged app-Execution.evtx the paths match with python-evtx and "
                 "reports, one row per record, the records whose provider is Microsoft-Windows-AppLocker and whose "
                 "Event ID is 8002 to 8007 or 8020 to 8025. Event meanings and field names come from the "
                 "provider's manifest as registered on Windows 11 build 26100.1742 and published in nasbench's "
                 "EVTX-ETW-Resources repository "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-AppLocker.xml), "
                 "from Microsoft's 'Using Event Viewer with AppLocker' "
                 "(https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/using-event-viewer-with-applocker, "
                 "page source commit 891d26f03efb5988573898879b5b9c311a92e366, last updated 2024-10-01), and from "
                 "Microsoft's AaronLocker script Get-AppLockerEvents.ps1 "
                 "(https://github.com/microsoft/AaronLocker/blob/9d3c943b64f335ffd3c9fa3e6a748ae6f498c5b9/AaronLocker/Get-AppLockerEvents.ps1). "
                 "The repository holds 246 copies of the manifest at that commit, for Windows 7 SP1 to Windows 11 "
                 "24H2 and Windows Server 2008 R2 to 2022, and the messages of these twelve events are the same in "
                 "each copy that has them (8020 to 8025 are not in the Windows 7 SP1 and Server 2008 R2 copies). "
                 "Outcome is the event's message in that manifest without its leading insertion marker and 'was' "
                 "(lines 133 to 312 and 431 to 580): 'allowed to run' for 8002, 8005 and 8020; 'allowed to be "
                 "installed' for 8023; 'allowed to run but would have been prevented from running if the AppLocker "
                 "policy were enforced' for 8003, 8006, 8021 and 8024; 'prevented from running' for 8004, 8007, "
                 "8022 and 8025. Microsoft's page says 8003 and 8006 are shown only when the Audit only "
                 "enforcement mode is enabled and 8004 and 8007 only when Enforce rules is, and gives no other "
                 "description for 8020 to 8025 than the Windows version that added them. Outcome follows from the "
                 "Event ID alone, never from the record's data. Policy Name, Full File Path, File Path (as logged), "
                 "File Hash, FQBN, Rule Name, Rule ID, Rule SDDL, Target User (SID), Target Process ID and Target "
                 "Logon ID are the fields PolicyName, FullFilePath, FilePath, FileHash, Fqbn, RuleName, RuleId, "
                 "RuleSddl, TargetUser, TargetProcessId and TargetLogonId of the record's RuleAndFileData, as "
                 "stored, except File Hash. The manifest names the string fields PolicyNameBuffer, "
                 "FilePathBuffer and so on; the tested records carry them without 'Buffer', as AaronLocker reads "
                 "them (lines 556 to 571). Package is the field Package, which AaronLocker reads for 8020 to 8022 "
                 "(line 571), and which is read for 8023 to 8025 too, whose manifest template is the same; no "
                 "tested log holds a packaged app record, so the Package column is source-verified for 8020 to "
                 "8022 and unexercised for 8023 to 8025. AaronLocker comments that PolicyName holds EXE, DLL, MSI, SCRIPT or APPX (line 579). "
                 "File Hash is the binary FileHash, which python-evtx renders in Base64, shown in uppercase "
                 "hexadecimal, the manifest's output type for it; AaronLocker describes the hash it reports from "
                 "this field as the file's SHA256 hash (line 50). AaronLocker splits FQBN at backslashes into "
                 "publisher, product name, original file name and file version, and reads a '-' as unsigned "
                 "(lines 673 to 686). File Path (as logged) is the path as the provider stored it, which on the "
                 "tested rows uses tokens such as %SYSTEM32%. FullFilePath is in the manifest copies for Windows "
                 "10 1903 and later, Windows 11, Windows Server 2022 and Windows Server 2019 from build "
                 "17763.1637; TargetLogonId is in those and in the copies for Windows 10 1507 to 1809 and the "
                 "other Windows Server 2016 and 2019 copies; the Windows 7 SP1, 8, 8.1 and Server 2008 R2, 2012 "
                 "and 2012 R2 copies have neither. Target User (SID) is reported as stored: this artifact does "
                 "not resolve a SID to an account name; the User Profile List artifact shows the profile path "
                 "the SOFTWARE hive records for a SID. Every field is read by the name the record carries, never "
                 "by position, and a column whose field the record does not carry is blank; values have surrounding whitespace removed and are otherwise as stored. Event Time (UTC) is "
                 "the record's TimeCreated SystemTime, and Channel, Event Version, Record ID and Computer are its "
                 "Channel, Version, EventRecordID and Computer. Rows in the tested logs: on hexordia_mvs2025_win11 "
                 "238, all of 8003 version 0 from the EXE and DLL log, with Policy Name DLL on 230 and EXE on 8. On "
                 "those 238 rows Package and File Hash were empty; FQBN, Rule Name and Rule SDDL held one value, "
                 "'-'; Rule ID held one value, the all-zero GUID; and Event ID, Outcome, Channel, Event Version "
                 "and Computer each held one value. No other tested log holds any of these twelve events. For "
                 "every key whose logs were matched, the records per Event ID were also counted with a second "
                 "reader, the evtx crate's Python binding (pyevtx-rs, PyPI package evtx 0.13.1), and the rows "
                 "match it record for record by channel, Event ID, EventRecordID and time to the second, and field "
                 "for field on the columns named above (the crate prints TargetLogonId without leading zeros and "
                 "RuleId without braces). Not exercised on real data: 8002, 8004 to 8007, 8020 to 8025, and the "
                 "Package and File Hash columns. A row shows what the provider logged for a file or package; it "
                 "does not show that the file ran to completion. Not read here: 8030 to 8035, the provider's "
                 "ManagedInstaller and SmartlockerFilter checks, which no tested log holds; the Verbose channel "
                 "(9000 and 9001), whose log the paths do not match and which was on none of the 19 keys checked "
                 "for it; and the provider's other events, which the "
                 "AppLocker Config CI Events and AppLocker Policy Events artifacts report. The AppLocker policy "
                 "itself is not read: the SrpV2 key under SOFTWARE\\Policies\\Microsoft\\Windows was absent from "
                 "the SOFTWARE hive of each of the 12 tested keys probed for it, hexordia_mvs2025_win11 among them, "
                 "and on that key Windows\\System32\\AppLocker held AppCache.dat, a registry hive holding only its "
                 "root key, which is not read. For a log marked dirty, scripts/windows_evtx.py also reads the "
                 "records of intact chunks after the chunks its header counts, and the run log says how many "
                 "records came from there. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4EXE and DLL.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4MSI and Script.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4Packaged app-Deployment.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4Packaged app-Execution.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763.3046 | 0 rows (the matched logs hold no records)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "defender_evtx_attack_samples": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "defender_evtx_to_mitre": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "dhparser_detectionhistory_gpl": "Defender DetectionHistory samples | 0 rows (no member matches the declared paths)",
            "discord_win_ptb": "Synthetic Discord PTB layout (application folder only) | 0 rows (no member matches the declared paths)",
            "dleapp_slack_known": "Constructed Slack known-data fixture | 0 rows (no member matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "193 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 0 rows (the matched logs hold no record of these events)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_mitre_attack_4688_cc0": "74 public Security logs | 0 rows (no member matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "25 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 238 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, version 1709 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 0 rows (the matched logs hold no records)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "plaso_testdata_f951fc6": "12 plaso test files | 0 rows (no member matches the declared paths)",
            "roblox_windows": "Windows Roblox profile (application folder only) | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_parallels": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "wire_win": "Wire desktop profile (application folder only) | 0 rows (no member matches the declared paths)",
        },
    },
    "appLockerConfigCiEvents": {
        "name": "AppLocker Config CI Events",
        "description": "Files and packages that the Microsoft-Windows-AppLocker provider logged in its MSI and "
                       "Script log as passing a Config CI policy, prevented by one, or allowed although one would "
                       "have prevented them had it been enforced, with the file path, its SHA-1 and SHA-256 "
                       "hashes and version fields, and the publisher records logged beside them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-AppLocker%4EXE and DLL.evtx, %4MSI and Script.evtx, %4Packaged "
                 "app-Deployment.evtx and %4Packaged app-Execution.evtx the paths match with python-evtx and "
                 "reports, one row per record, the records whose provider is Microsoft-Windows-AppLocker and whose "
                 "Event ID is 8028, 8029, 8036, 8037, 8038, 8039 or 8040, which the provider's manifest logs to "
                 "the MSI and Script channel. Event meanings and field names come from that manifest as registered "
                 "on Windows 11 build 26100.1742 and published in nasbench's EVTX-ETW-Resources repository "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-AppLocker.xml), "
                 "and from Microsoft's 'Using Event Viewer with AppLocker' "
                 "(https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/using-event-viewer-with-applocker, "
                 "page source commit 891d26f03efb5988573898879b5b9c311a92e366, last updated 2024-10-01), which "
                 "lists these Event IDs with messages of the same wording (8039 and 8040 shortened), as added in Windows Server 2016 and "
                 "Windows 10. What "
                 "a Config CI policy is, is not described there and is not sourced here. Outcome is the event's "
                 "message in that manifest without its leading insertion marker and 'was' (lines 601 to 754 and "
                 "1006 to 1165): 'allowed to run but would have been prevented if the Config CI policy were "
                 "enforced' for 8028; 'prevented from running due to Config CI policy' for 8029 and 8036; 'passed "
                 "Config CI policy and was allowed to run' for 8037; 'allowed to install or update but would have "
                 "been prevented if the Config CI policy were enforced' for 8039; 'prevented from installing or "
                 "updating due to Config CI policy' for 8040. The message of 8038 is publisher information "
                 "('Publisher info: Subject: %4 Issuer: %6 Signature index %2 (%1 total)', lines 1097 to 1121), "
                 "so its Outcome is 'Publisher info'. Outcome follows from the Event ID alone, never from the "
                 "record's data. The repository holds 246 copies of the manifest at that commit, for Windows 7 SP1 "
                 "to Windows 11 24H2 and Windows Server 2008 R2 to 2022: 8028 and 8029 are in 240, 8037 and 8038 "
                 "in 216, 8039 and 8040 in 47 (Windows 11 and Windows Server 2022), and versions 1 and 2 of 8028, "
                 "8029 and 8037 only in Windows 11 24H2; 5 copies give 8037 and 89 give 8038 an empty message, and "
                 "the others give the messages above. File Path, Original File Name, Internal Name, File "
                 "Description, Product Name, File Version, User Writeable and USN are the fields FilePath, "
                 "OriginalFilename, InternalName, FileDescription, ProductName, FileVersion, UserWriteable and USN, "
                 "as stored. SHA-256, SHA-1, SHA-256 Catalog Hash and SHA-1 Catalog Hash are the binary fields "
                 "Sha256Hash, Sha1Hash, Sha256CatalogHash and Sha1CatalogHash, which python-evtx renders in "
                 "Base64, shown in uppercase hexadecimal, the manifest's output type for them. Result is Result, a "
                 "signed 32-bit number, shown in hexadecimal with the stored number in parentheses; what its values "
                 "mean is not sourced here. Publisher, Issuer, Signature Index and Signature Count are the "
                 "PublisherName, IssuerName, Signature and TotalSignatureCount of 8038. Package Family Name and "
                 "Package Version are PackageFamilyName and PackageVersion; Config CI Policy is "
                 "'Name:... ID:... Version:... GUID:...' from PolicyName, PolicyID, PolicyVersion and PolicyGuid, "
                 "as the messages of 8039 and 8040 print them; Status is Status, as stored; and CLSID is the CLSID "
                 "of 8036. Processing Error Code is the ErrorCode of a record that carries ProcessingErrorData in "
                 "place of its event data (see scripts/windows_evtx.py); such a row shows no event fields. Security "
                 "UserID and Execution ProcessID are the record's System Security UserID and Execution ProcessID, "
                 "which Microsoft's event schema describes as identifying the user that logged the event and the "
                 "process that logged it "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/eventschema-systempropertiestype-complextype.md?plain=1#L198-L203); "
                 "Security UserID is reported as stored; this artifact does not resolve a SID to an account name. "
                 "Not shown: the IsApproved field of 8036, the TBS hashes of 8038, DetachedSignatureFilePath, "
                 "and length fields. Every field is read by the name the record carries, never by position, and a "
                 "column whose field the record does not carry is blank; values have surrounding whitespace removed and are otherwise as stored. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, and Channel, Event Version, Record ID and Computer are its Channel, "
                 "Version, EventRecordID and Computer. Rows in the tested logs: on hexordia_mvs2025_win11 7, all "
                 "of 8037 version 2; on those 7 rows Event ID, Outcome, Channel, Event Version and Computer each "
                 "held one value, Original File Name, Internal Name, File Description and Product Name were empty, "
                 "File Version held one value, 0.0.0.0, User Writeable held one value, False, and Result held one "
                 "value, 0x00000000 (0); that key holds no 8038, so Signature Index, Signature Count and Processing Error "
                 "Code were empty on its 7 rows. On evtx_baseline_nextron_085_win11_client_2023 242: 234 of 8037 and 4 of "
                 "8028, both version 0, and 4 of 8038; version 0 has no version-resource fields, so Original File "
                 "Name, Internal Name, File Description, Product Name and File Version were empty on those 242 "
                 "rows, and Channel and Event Version each held one value. Result held 0x00000000 (0) on the 234 "
                 "rows of 8037 and 0xD0E90002 (-790036478) on the 4 of 8028. Of the 4 rows of 8038, 2 carry "
                 "ProcessingErrorData with Processing Error Code 15005 and 2 hold Signature Index 0 and Signature "
                 "Count 1; Publisher and Issuer were empty on every tested row. On that key each 8038 record's "
                 "EventRecordID is one more than that of an 8028 record in the same log; nothing in the records "
                 "links the two, and they are not joined here. SHA-1 Catalog Hash was identical to SHA-1 on all "
                 "245 tested rows of 8028 and 8037, and SHA-256 Catalog Hash differed from SHA-256 on all 245. "
                 "Package Family Name, Package Version, Config CI Policy, Status and CLSID were empty on every "
                 "tested row: no 8029, 8036, 8039 or 8040 record was found. For every key whose logs were matched, "
                 "the records per Event ID were also counted with a second reader, the evtx crate's Python binding "
                 "(pyevtx-rs, PyPI package evtx 0.13.1), and the rows match it record for record by channel, Event "
                 "ID, EventRecordID and time to the second, and field for field on File Path, the four hash "
                 "columns, File Version, User Writeable, USN, Publisher, Issuer, Signature Index, Signature Count, "
                 "Security UserID and Execution ProcessID. Not exercised on real data: 8029, 8036, 8039 and 8040, "
                 "8028 and 8029 versions 1 and 2, and 8037 version 1. For a log marked dirty, "
                 "scripts/windows_evtx.py also reads the records of intact chunks after the chunks its header "
                 "counts, and the run log says how many records came from there; on "
                 "evtx_baseline_nextron_085_win11_client_2023 the MSI and Script log is marked dirty and 11 of its "
                 "records come from such a chunk. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4EXE and DLL.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4MSI and Script.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4Packaged app-Deployment.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4Packaged app-Execution.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763.3046 | 0 rows (the matched logs hold no records)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "defender_evtx_attack_samples": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "defender_evtx_to_mitre": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "dhparser_detectionhistory_gpl": "Defender DetectionHistory samples | 0 rows (no member matches the declared paths)",
            "discord_win_ptb": "Synthetic Discord PTB layout (application folder only) | 0 rows (no member matches the declared paths)",
            "dleapp_slack_known": "Constructed Slack known-data fixture | 0 rows (no member matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "193 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 242 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_mitre_attack_4688_cc0": "74 public Security logs | 0 rows (no member matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "25 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 7 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, version 1709 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 0 rows (the matched logs hold no records)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "plaso_testdata_f951fc6": "12 plaso test files | 0 rows (no member matches the declared paths)",
            "roblox_windows": "Windows Roblox profile (application folder only) | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_parallels": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "wire_win": "Wire desktop profile (application folder only) | 0 rows (no member matches the declared paths)",
        },
    },
    "appLockerPolicyEvents": {
        "name": "AppLocker Policy Events",
        "description": "Microsoft-Windows-AppLocker events about the policy and the provider's other notices: the "
                       "policy applied or failed to convert, AppLocker not available on the edition, packaged apps "
                       "unable to run, system execution policy decisions, and processes registering or checking "
                       "uninstall strings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-AppLocker%4EXE and DLL.evtx, %4MSI and Script.evtx, %4Packaged "
                 "app-Deployment.evtx and %4Packaged app-Execution.evtx the paths match with python-evtx and "
                 "reports, one row per record, the records whose provider is Microsoft-Windows-AppLocker and whose "
                 "Event ID is 8000, 8001, 8008, 8009, 8026, 8027, 8041, 8042, 8043 or 8044. Event is the first "
                 "line of the event's message in the provider's manifest as registered on Windows 11 build "
                 "26100.1742 and published in nasbench's EVTX-ETW-Resources repository "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-AppLocker.xml; "
                 "lines 110 to 132, 313 to 340, 581 to 600 and 1166 to 1240), with insertion markers such as %2 "
                 "kept as the manifest has them. The repository holds 246 copies of the manifest at that commit, "
                 "for Windows 7 SP1 to Windows 11 24H2 and Windows Server 2008 R2 to 2022; the messages of these "
                 "events are the same in each copy that has them, 8026 and 8027 are not in the Windows 7 SP1 and "
                 "Server 2008 R2 copies, and 8041 to 8044 are only in the 8 copies for Windows 11 22H2 and 24H2. "
                 "Microsoft's 'Using Event Viewer with AppLocker' "
                 "(https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/using-event-viewer-with-applocker, "
                 "page source commit 891d26f03efb5988573898879b5b9c311a92e366, last updated 2024-10-01) says 8000 "
                 "indicates the policy was not applied correctly, 8001 that it was applied successfully, and 8008 "
                 "an edition of Windows that does not support AppLocker; it does not list 8009, 8026 or 8041 to "
                 "8044. Process Name and Uninstaller Path are the ProcessName and UninstallerPath of 8043; "
                 "Uninstall String is the UninstallString of 8043 and 8044; Command Line and Match Found are the Cmdline and MatchFound of 8044; "
                 "Audit Info is the AuditInfo of 8041 and 8042, which their message prints as the information the "
                 "application provided; Status is Status, of 8000, 8043 and 8044, as stored. File Path is the "
                 "path of 8008 and 8009, read as FilePath, the name the provider's records of 8003 carry for the "
                 "manifest's FilePathBuffer, or as FilePathBuffer; no tested log holds 8008 or 8009, so it is "
                 "unexercised. 8001, 8026 and 8027 have no fields: their rows show only that the record was "
                 "written. Security UserID and Execution ProcessID are the record's System Security UserID and "
                 "Execution ProcessID, which Microsoft's event schema describes as identifying the user that "
                 "logged the event and the process that logged it "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/eventschema-systempropertiestype-complextype.md?plain=1#L198-L203); "
                 "Security UserID is reported as stored; this artifact does not resolve a SID to an account name. "
                 "Not shown: the SessionId and SubSessionId GUIDs of 8043, and the "
                 "ExecutionDecision, ExecutionOptionFlags and Subject numbers and the Host GUID of 8041 and 8042. Every field "
                 "is read by the name the record carries, never by position, and a column whose field the record "
                 "does not carry is blank; values have surrounding whitespace removed and are otherwise as stored. Event Time (UTC) is the record's TimeCreated SystemTime, and Channel, "
                 "Event Version, Record ID and Computer are its Channel, Version, EventRecordID and Computer. Rows "
                 "in the tested logs: on hexordia_mvs2025_win11 5, all of 8001, on which Event ID, Event, Security "
                 "UserID, Channel and Event Version each held one value and Computer held three; on "
                 "evtx_baseline_nextron_085_win11_client_2023 43, 30 of 8001 and 13 of 8043, Channel and Event "
                 "Version each holding one value. The 13 rows of 8043 each have a Process Name, Uninstall String "
                 "and Uninstaller Path, and Status held one value, 0x00000000, on them. Command Line, Match Found, "
                 "Audit Info and File Path were empty on every tested row, and Process Name, Uninstall String, "
                 "Uninstaller Path and Status were empty on every row of 8001: no 8000, 8008, 8009, 8026, 8027, "
                 "8041, 8042 or 8044 record was found. For every key whose logs were matched, the records per "
                 "Event ID were also counted with a second reader, the evtx crate's Python binding (pyevtx-rs, "
                 "PyPI package evtx 0.13.1), and the rows match it record for record by channel, Event ID, "
                 "EventRecordID and time to the second, and field for field on Process Name, Uninstall String, "
                 "Uninstaller Path, Security UserID and Execution ProcessID (the crate prints Status 0x00000000 as "
                 "0x0). Not exercised on real data: 8000, 8008, 8009, 8026, 8027, 8041, 8042 and 8044. A row of "
                 "8043 shows that the provider logged the registration attempt with the status shown; it does not "
                 "show that anything was uninstalled. For a log marked dirty, scripts/windows_evtx.py also reads "
                 "the records of intact chunks after the chunks its header counts, and the run log says how many "
                 "records came from there. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4EXE and DLL.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4MSI and Script.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4Packaged app-Deployment.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-AppLocker%4Packaged app-Execution.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763.3046 | 0 rows (the matched logs hold no records)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "defender_evtx_attack_samples": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "defender_evtx_to_mitre": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "dhparser_detectionhistory_gpl": "Defender DetectionHistory samples | 0 rows (no member matches the declared paths)",
            "discord_win_ptb": "Synthetic Discord PTB layout (application folder only) | 0 rows (no member matches the declared paths)",
            "dleapp_slack_known": "Constructed Slack known-data fixture | 0 rows (no member matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "193 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 43 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_mitre_attack_4688_cc0": "74 public Security logs | 0 rows (no member matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "25 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 5 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, version 1709 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 0 rows (the matched logs hold no records)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "plaso_testdata_f951fc6": "12 plaso test files | 0 rows (no member matches the declared paths)",
            "roblox_windows": "Windows Roblox profile (application folder only) | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_parallels": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "wire_win": "Wire desktop profile (application folder only) | 0 rows (no member matches the declared paths)",
        },
    },
}


def _records(context, label, event_ids):
    records = []
    sources = []
    for log in _LOGS:
        found, read = read_event_records(context, log, label, event_ids=set(event_ids), provider=_PROVIDER)
        records.extend(found)
        sources.extend(read)
    return records, sources


def rule_row(record):
    get = record.get
    return (record.time, record.event_id, _RULE_EVENTS.get(record.event_id, ''), get('PolicyName'),
            get('FullFilePath'), get('FilePath'), get('Package'), binary_hex(get('FileHash')), get('Fqbn'),
            get('RuleName'), get('RuleId'), get('RuleSddl'), get('TargetUser'), get('TargetProcessId'),
            get('TargetLogonId'), record.channel, record.version, record.record_id, record.computer)


def config_ci_policy(record):
    """The Config CI policy of 8039 and 8040 as their message prints it, or ''."""
    get = record.get
    if not any(get(name) for name in ('PolicyName', 'PolicyID', 'PolicyVersion', 'PolicyGuid')):
        return ''
    return (f"Name:{get('PolicyName')} ID:{get('PolicyID')} Version:{get('PolicyVersion')} "
            f"GUID:{get('PolicyGuid')}")


def config_ci_row(record):
    get = record.get
    return (record.time, record.event_id, _CONFIG_CI_EVENTS.get(record.event_id, ''), get('FilePath'),
            binary_hex(get('Sha256Hash')), binary_hex(get('Sha1Hash')), binary_hex(get('Sha256CatalogHash')),
            binary_hex(get('Sha1CatalogHash')), get('OriginalFilename'), get('InternalName'),
            get('FileDescription'), get('ProductName'), get('FileVersion'), get('UserWriteable'),
            signed_hex(get('Result')), get('USN'), get('PublisherName'), get('IssuerName'), get('Signature'),
            get('TotalSignatureCount'), get('PackageFamilyName'), get('PackageVersion'), config_ci_policy(record),
            get('Status'), get('CLSID'), record.processing_error.get('ErrorCode', ''), record.user_sid,
            record.process_id, record.channel, record.version, record.record_id, record.computer)


def policy_row(record):
    get = record.get
    return (record.time, record.event_id, _POLICY_EVENTS.get(record.event_id, ''), get('ProcessName'),
            get('UninstallString'), get('UninstallerPath'), get('Cmdline'), get('MatchFound'), get('AuditInfo'),
            get('FilePath') or get('FilePathBuffer'), get('Status'), record.user_sid, record.process_id,
            record.channel, record.version, record.record_id, record.computer)


@artifact_processor
def appLockerRuleEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Outcome', 'Policy Name', 'Full File Path',
                    'File Path (as logged)', 'Package', 'File Hash', 'FQBN', 'Rule Name', 'Rule ID', 'Rule SDDL',
                    'Target User (SID)', 'Target Process ID', 'Target Logon ID', 'Channel', 'Event Version',
                    'Record ID', 'Computer')
    records, sources = _records(context, 'AppLocker Rule Events', _RULE_EVENTS)
    return data_headers, [rule_row(record) for record in records], '\n'.join(sources)


@artifact_processor
def appLockerConfigCiEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Outcome', 'File Path', 'SHA-256', 'SHA-1',
                    'SHA-256 Catalog Hash', 'SHA-1 Catalog Hash', 'Original File Name', 'Internal Name',
                    'File Description', 'Product Name', 'File Version', 'User Writeable', 'Result', 'USN',
                    'Publisher', 'Issuer', 'Signature Index', 'Signature Count', 'Package Family Name',
                    'Package Version', 'Config CI Policy', 'Status', 'CLSID', 'Processing Error Code',
                    'Security UserID', 'Execution ProcessID', 'Channel', 'Event Version', 'Record ID', 'Computer')
    records, sources = _records(context, 'AppLocker Config CI Events', _CONFIG_CI_EVENTS)
    return data_headers, [config_ci_row(record) for record in records], '\n'.join(sources)


@artifact_processor
def appLockerPolicyEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Process Name', 'Uninstall String',
                    'Uninstaller Path', 'Command Line', 'Match Found', 'Audit Info', 'File Path', 'Status',
                    'Security UserID', 'Execution ProcessID', 'Channel', 'Event Version', 'Record ID', 'Computer')
    records, sources = _records(context, 'AppLocker Policy Events', _POLICY_EVENTS)
    return data_headers, [policy_row(record) for record in records], '\n'.join(sources)
